---
name: codebot-api-endpoint
description: How to add new API endpoints to the CodeBot FastAPI backend
tags:
  - codebot
  - fastapi
  - api
  - backend
  - python
globs:
  - "apps/server/src/codebot/**/*.py"
---

# Adding a New API Endpoint to CodeBot

## Project Layout

```
apps/server/src/codebot/
  main.py                    # FastAPI app entrypoint
  config.py                  # App configuration
  api/
    routes/                  # Route modules (one per domain)
    schemas/                 # Pydantic v2 request/response models
    deps.py                  # Dependency injection helpers
    middleware.py             # Auth, CORS, logging middleware
  db/
    models.py                # SQLAlchemy ORM models
    migrations/              # Alembic migration scripts
  auth/                      # JWT, API keys, RBAC, TOTP MFA
  websocket/
    manager.py               # Socket.IO WebSocket manager
  observability/             # Prometheus metrics, OpenTelemetry, health checks
```

Existing route modules include: `projects.py`, `pipeline.py`, `agents.py`, `code.py`,
`tests.py`, `security.py`, `reviews.py`, `config.py`, `metrics.py`, `brainstorm.py`,
`templates.py`, `techstack.py`, `deployment.py`, `collaboration.py`,
`github_integration.py`, `skills.py`, `hooks.py`, `auth.py`, `audit.py`,
`reports.py`, `health.py`, `retention.py`, `dlq.py`.

Each domain area typically also has its own service module (e.g., `brainstorm/service.py`).

## Step 1: Define Pydantic Schemas

Create a schema file at `api/schemas/<domain>.py`. Use Pydantic v2 (`BaseModel` from
`pydantic`). Define separate models for create, update, and response payloads.

```python
# apps/server/src/codebot/api/schemas/widgets.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WidgetCreate(BaseModel):
    """Request body for creating a widget."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    project_id: UUID


class WidgetUpdate(BaseModel):
    """Request body for updating a widget. All fields optional."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class WidgetResponse(BaseModel):
    """Response body returned to clients."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    project_id: UUID
    created_at: datetime
    updated_at: datetime


class WidgetListResponse(BaseModel):
    items: list[WidgetResponse]
    total: int
```

Conventions:
- Use `ConfigDict(from_attributes=True)` on response models so they can be built
  directly from SQLAlchemy model instances.
- Keep field constraints (min/max length, regex, ge/le) in the schema.
- Use `UUID` for all ID fields; use `datetime` for timestamps.

## Step 2: Create the Database Model

Add the SQLAlchemy model in `db/models.py`.

```python
# In apps/server/src/codebot/db/models.py
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Widget(Base):
    __tablename__ = "widgets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship(back_populates="widgets")
```

Then generate and apply an Alembic migration:

```bash
cd apps/server
alembic revision --autogenerate -m "add widgets table"
alembic upgrade head
```

## Step 3: Create the Service Layer

Create a service module for business logic. Keep route handlers thin; put logic here.

```python
# apps/server/src/codebot/<domain>/service.py  (or a standalone service file)
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.db.models import Widget
from codebot.api.schemas.widgets import WidgetCreate, WidgetUpdate


class WidgetService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, payload: WidgetCreate) -> Widget:
        widget = Widget(**payload.model_dump())
        self._db.add(widget)
        await self._db.commit()
        await self._db.refresh(widget)
        return widget

    async def get(self, widget_id: UUID) -> Widget | None:
        return await self._db.get(Widget, widget_id)

    async def list_for_project(
        self, project_id: UUID, *, offset: int = 0, limit: int = 50
    ) -> tuple[list[Widget], int]:
        query = select(Widget).where(Widget.project_id == project_id)
        count_result = await self._db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        results = await self._db.scalars(query.offset(offset).limit(limit))
        return list(results.all()), count_result or 0

    async def update(self, widget: Widget, payload: WidgetUpdate) -> Widget:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(widget, field, value)
        await self._db.commit()
        await self._db.refresh(widget)
        return widget

    async def delete(self, widget: Widget) -> None:
        await self._db.delete(widget)
        await self._db.commit()
```

## Step 4: Create the Route Module

Add a new route file at `api/routes/<domain>.py`.

```python
# apps/server/src/codebot/api/routes/widgets.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from codebot.api.deps import get_current_user, get_db, get_redis
from codebot.api.schemas.widgets import (
    WidgetCreate,
    WidgetListResponse,
    WidgetResponse,
    WidgetUpdate,
)
from codebot.auth.models import User
from codebot.widgets.service import WidgetService
from codebot.websocket.manager import ws_manager

router = APIRouter(prefix="/widgets", tags=["widgets"])


def _get_service(db=Depends(get_db)) -> WidgetService:
    return WidgetService(db)


@router.post(
    "",
    response_model=WidgetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a widget",
)
async def create_widget(
    payload: WidgetCreate,
    service: WidgetService = Depends(_get_service),
    current_user: User = Depends(get_current_user),
) -> WidgetResponse:
    widget = await service.create(payload)
    # Broadcast real-time event (see Step 6)
    await ws_manager.emit(
        "widget:created",
        {"id": str(widget.id), "name": widget.name},
        room=f"project:{widget.project_id}",
    )
    return WidgetResponse.model_validate(widget)


@router.get("/{widget_id}", response_model=WidgetResponse, summary="Get a widget")
async def get_widget(
    widget_id: UUID,
    service: WidgetService = Depends(_get_service),
    current_user: User = Depends(get_current_user),
) -> WidgetResponse:
    widget = await service.get(widget_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    return WidgetResponse.model_validate(widget)


@router.get("", response_model=WidgetListResponse, summary="List widgets")
async def list_widgets(
    project_id: UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    service: WidgetService = Depends(_get_service),
    current_user: User = Depends(get_current_user),
) -> WidgetListResponse:
    items, total = await service.list_for_project(project_id, offset=offset, limit=limit)
    return WidgetListResponse(
        items=[WidgetResponse.model_validate(w) for w in items],
        total=total,
    )


@router.patch("/{widget_id}", response_model=WidgetResponse, summary="Update a widget")
async def update_widget(
    widget_id: UUID,
    payload: WidgetUpdate,
    service: WidgetService = Depends(_get_service),
    current_user: User = Depends(get_current_user),
) -> WidgetResponse:
    widget = await service.get(widget_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    updated = await service.update(widget, payload)
    await ws_manager.emit(
        "widget:updated",
        {"id": str(updated.id)},
        room=f"project:{updated.project_id}",
    )
    return WidgetResponse.model_validate(updated)


@router.delete(
    "/{widget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a widget",
)
async def delete_widget(
    widget_id: UUID,
    service: WidgetService = Depends(_get_service),
    current_user: User = Depends(get_current_user),
) -> None:
    widget = await service.get(widget_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    project_id = widget.project_id
    await service.delete(widget)
    await ws_manager.emit(
        "widget:deleted",
        {"id": str(widget_id)},
        room=f"project:{project_id}",
    )
```

## Step 5: Register the Router

In `main.py`, include the new router under the API version prefix.

```python
# In apps/server/src/codebot/main.py
from codebot.api.routes.widgets import router as widgets_router

app.include_router(widgets_router, prefix="/api/v1")
```

All routes are versioned under `/api/v1`. When introducing breaking changes, create
a `/api/v2` prefix and keep the old routes available during the deprecation window.

## Step 6: Dependency Injection Patterns

Common dependencies live in `api/deps.py`. Typical providers:

```python
# Illustrative patterns from api/deps.py
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db(request: Request) -> AsyncSession:
    """Yields a database session from the request-scoped pool."""
    ...

async def get_redis(request: Request):
    """Returns the Redis client attached to app state."""
    return request.app.state.redis

async def get_current_user(request: Request) -> User:
    """Extracts and validates JWT or API key from the Authorization header."""
    ...

def require_role(*roles: str):
    """Returns a dependency that enforces RBAC roles."""
    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return _check
```

Use `Depends(require_role("admin", "editor"))` on route parameters to enforce
role-based access control.

## Step 7: WebSocket Event Broadcasting

Use the Socket.IO manager at `websocket/manager.py` to push real-time updates.

```python
await ws_manager.emit(
    "widget:created",          # event name — use <entity>:<action> convention
    {"id": str(widget.id)},    # JSON-serializable payload
    room=f"project:{pid}",     # room scoping — clients join project rooms
)
```

Clients subscribe to rooms on connect. Keep payloads small (IDs + changed fields);
let the client re-fetch full data if needed.

## Step 8: Authentication and Authorization

The middleware stack in `api/middleware.py` applies globally:
- **Auth middleware**: validates JWT tokens / API keys on every request.
- **CORS middleware**: configured for allowed origins.
- **Logging middleware**: structured request/response logging.

For route-level authorization:
- Use `Depends(get_current_user)` for any authenticated route.
- Use `Depends(require_role("admin"))` for admin-only routes.
- The auth system supports JWT, API keys, RBAC, and TOTP MFA (see `auth/`).

## Step 9: Error Handling Patterns

Raise `HTTPException` with appropriate status codes. For domain errors, define
custom exception classes and register handlers in `main.py`.

```python
from fastapi import HTTPException, status

# Simple 404
raise HTTPException(status_code=404, detail="Widget not found")

# Validation / business rule error
raise HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Widget name must be unique within the project",
)

# For custom exceptions, register a handler:
class WidgetLimitExceeded(Exception):
    pass

@app.exception_handler(WidgetLimitExceeded)
async def handle_widget_limit(request, exc):
    return JSONResponse(status_code=429, content={"detail": str(exc)})
```

Always return a JSON body with a `detail` field for error responses.

## Step 10: Testing API Endpoints

Write tests using `pytest` with `httpx.AsyncClient`. Place tests alongside or under
a `tests/` directory mirroring the source structure.

```python
# tests/api/routes/test_widgets.py
import pytest
from httpx import AsyncClient, ASGITransport

from codebot.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers(test_user_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.mark.asyncio
async def test_create_widget(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/api/v1/widgets",
        json={"name": "My Widget", "project_id": "...uuid..."},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Widget"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_widget_not_found(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get(
        "/api/v1/widgets/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_widgets_pagination(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get(
        "/api/v1/widgets",
        params={"project_id": "...uuid...", "offset": 0, "limit": 10},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
```

Run with: `pytest tests/ -x -q --strict-markers`

Enforce code quality before committing:
- `ruff check .` and `ruff format .` for linting/formatting.
- `mypy --strict .` for type checking (Python 3.12+).

## Quick Checklist

1. [ ] Schema file created at `api/schemas/<domain>.py`
2. [ ] SQLAlchemy model added to `db/models.py`
3. [ ] Alembic migration generated and applied
4. [ ] Service class created with business logic
5. [ ] Route module created at `api/routes/<domain>.py`
6. [ ] Router registered in `main.py` under `/api/v1`
7. [ ] Auth dependencies applied to all route handlers
8. [ ] WebSocket events emitted for create/update/delete
9. [ ] Error handling with proper HTTP status codes
10. [ ] Tests written with `pytest` + `httpx.AsyncClient`
11. [ ] `ruff` and `mypy --strict` pass cleanly

## Documentation Lookup (Context7)

Before implementing, use Context7 to fetch current docs for the libraries used in this skill:

```
# Resolve library IDs first, then query specific topics:
mcp__plugin_context7_context7__resolve-library-id("FastAPI")
mcp__plugin_context7_context7__query-docs(id, "dependency injection and APIRouter")

mcp__plugin_context7_context7__resolve-library-id("Pydantic")
mcp__plugin_context7_context7__query-docs(id, "model_validator field_validator v2 migration")

mcp__plugin_context7_context7__resolve-library-id("SQLAlchemy")
mcp__plugin_context7_context7__query-docs(id, "async session declarative_base 2.0 style")

mcp__plugin_context7_context7__resolve-library-id("Alembic")
mcp__plugin_context7_context7__query-docs(id, "autogenerate migration async")
```

Always verify API signatures against Context7 docs — Pydantic v2 and SQLAlchemy 2.0 have significant breaking changes from v1.
