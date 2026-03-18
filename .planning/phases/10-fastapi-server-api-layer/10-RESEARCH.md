# Phase 10: FastAPI Server + API Layer - Research

**Researched:** 2026-03-18
**Domain:** FastAPI REST API, WebSocket real-time streaming, JWT/API Key auth, pipeline and agent management
**Confidence:** HIGH

## Summary

Phase 10 builds the HTTP/WebSocket interface that allows users, the dashboard, and the CLI to control the entire CodeBot platform. The codebase already has a solid foundation: FastAPI entrypoint (`main.py`), pydantic-settings config, SQLAlchemy 2.0 async engine with session factory, full ORM models (User, ApiKey, AuditLog, Project, Pipeline, PipelinePhase, Agent, AgentExecution, Task, etc.), Alembic migrations, and a NATS JetStream event bus. What is missing is everything between the database and the outside world: API routes, Pydantic request/response schemas, authentication/authorization middleware, dependency injection helpers, service layer business logic, WebSocket manager, and rate limiting.

The API specification (`docs/api/API_SPECIFICATION.md`) is exhaustive, defining 20+ endpoint groups with exact request/response JSON shapes, status codes, pagination format, error envelope, and WebSocket event contracts. The project's `codebot-api-endpoint` skill provides a clear, repeatable pattern for adding each endpoint domain: schema -> model (exists) -> service -> route -> register -> test.

**Primary recommendation:** Follow the layered architecture pattern from the skill: create `api/schemas/`, `api/routes/`, `api/deps.py`, `api/middleware.py`, and `websocket/manager.py` directories. Use PyJWT (not python-jose) for JWT, bcrypt for password hashing, python-socketio mounted as ASGI sub-app for WebSocket, and SlowAPI with Redis backend for rate limiting. Build auth first, then project CRUD, then pipeline control, then agent management, then WebSocket streaming.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SRVR-01 | REST API endpoints for project CRUD, pipeline control, and agent monitoring | FastAPI APIRouter pattern with versioned prefix `/api/v1`. Existing ORM models cover all entities. Standard 3-layer architecture: route -> service -> db. Pagination, filtering, and standard response envelope defined in API spec. |
| SRVR-02 | WebSocket endpoint for real-time pipeline status and agent output streaming | python-socketio as ASGI sub-app mounted on FastAPI. Room-based scoping per project. Bridge NATS events to Socket.IO rooms for real-time forwarding. Event contracts fully defined in API spec section 14. |
| SRVR-03 | Authentication and authorization for API access | Dual auth: JWT Bearer (RS256 per SYSTEM_DESIGN, HS256 acceptable for v1) + API Key (SHA-256 hash lookup). RBAC with admin/user/viewer roles. FastAPI `Depends()` chain for `get_current_user` and `require_role()`. Existing User and ApiKey ORM models ready. |
| SRVR-04 | Pipeline configuration endpoints accept YAML preset selection | Pipeline model and PipelinePhase model exist. API spec defines `POST /projects/{id}/pipelines` with `mode` field (full/incremental/phase_only). Preset YAML files loaded from `configs/pipelines/` directory. |
| SRVR-05 | Agent management endpoints (start, stop, restart, configure) | Agent and AgentExecution ORM models exist. API spec section 5 defines full CRUD + lifecycle control. Service layer coordinates with graph engine and event bus for agent lifecycle actions. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.x | HTTP + WebSocket framework | Already in pyproject.toml, auto OpenAPI docs, async-native, Pydantic v2 integration |
| Pydantic | 2.12.x | Request/response validation | Already in pyproject.toml, Rust-backed, `ConfigDict(from_attributes=True)` for ORM |
| SQLAlchemy | 2.0.48 | Async ORM | Already in pyproject.toml, `Mapped` columns already defined for all models |
| uvicorn | 0.42.x | ASGI server | Already in pyproject.toml, standard production server |
| pydantic-settings | 2.13.x | Configuration management | Already in pyproject.toml, existing `Settings` class |
| asyncpg | 0.31.x | PostgreSQL async driver | Already in pyproject.toml, required for SQLAlchemy async |
| alembic | 1.18.x | Database migrations | Already in pyproject.toml, migrations directory exists |

### Supporting (NEW dependencies needed for this phase)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyJWT | 2.12.x | JWT token creation/verification | Auth endpoints, token middleware |
| bcrypt | 5.0.x | Password hashing | User registration, login |
| python-socketio | 5.16.x | Socket.IO WebSocket server | Real-time event streaming to clients |
| slowapi | 0.1.9 | Rate limiting middleware | All API endpoints, configurable per-route |
| cryptography | latest | RS256 JWT key support (optional) | Only if RS256 signing is used over HS256 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyJWT | python-jose | python-jose is no longer maintained; PyJWT is actively maintained and recommended by FastAPI docs |
| python-socketio | FastAPI native WebSocket | Native WS lacks Socket.IO protocol features (rooms, auto-reconnect, binary) needed by dashboard |
| slowapi | Custom Redis middleware | SlowAPI is production-proven, decorator-based, and supports Redis backend; custom is unnecessary |
| bcrypt | passlib | passlib wraps bcrypt but adds complexity; direct bcrypt is simpler and actively maintained |

**Installation:**
```bash
cd apps/server
uv add pyjwt[crypto] bcrypt python-socketio slowapi
```

**Version verification:** All versions confirmed via `pip index versions` on 2026-03-18.

## Architecture Patterns

### Recommended Project Structure
```
apps/server/src/codebot/
  main.py                      # FastAPI app + lifespan + router registration
  config.py                    # Settings (exists)
  api/
    __init__.py
    deps.py                    # get_db, get_current_user, require_role, get_redis, get_event_bus
    middleware.py               # CORS, request ID, structured logging, rate limit setup
    envelope.py                 # Standard response envelope (SuccessResponse, ErrorResponse, PaginatedResponse)
    routes/
      __init__.py
      auth.py                  # register, login, refresh, logout, me, settings, api-keys
      projects.py              # CRUD + clone + stats + import
      pipelines.py             # create, list, get, start/pause/resume/cancel, graph, checkpoints, phases
      agents.py                # list, get, logs, stop/restart, types, context, message, artifacts
      health.py                # health check (move from main.py)
    schemas/
      __init__.py
      auth.py                  # RegisterRequest, LoginRequest, TokenResponse, UserResponse, etc.
      projects.py              # ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
      pipelines.py             # PipelineCreate, PipelineResponse, PipelinePhaseResponse
      agents.py                # AgentResponse, AgentLogsResponse, AgentStopRequest
      common.py                # PaginationMeta, ResponseEnvelope, ErrorDetail
  auth/
    __init__.py
    jwt.py                     # create_access_token, create_refresh_token, decode_token
    password.py                # hash_password, verify_password
    api_key.py                 # generate_api_key, hash_api_key, verify_api_key
  services/
    __init__.py
    project_service.py         # ProjectService class
    pipeline_service.py        # PipelineService class
    agent_service.py           # AgentService class
    auth_service.py            # AuthService class (register, login, refresh)
  websocket/
    __init__.py
    manager.py                 # SocketIO server, ASGI mount, room management
    bridge.py                  # NATS-to-SocketIO event bridge
  db/                          # (exists)
    engine.py                  # (exists)
    models/                    # (exists - all models already defined)
  events/                      # (exists)
    bus.py                     # (exists - EventBus with NATS JetStream)
```

### Pattern 1: Layered Architecture (Route -> Service -> DB)
**What:** Routes are thin handlers that delegate to service classes. Services contain business logic and database operations. Routes handle HTTP concerns (status codes, response models).
**When to use:** Every endpoint.
**Example:**
```python
# api/routes/projects.py
@router.post("", response_model=ResponseEnvelope[ProjectResponse], status_code=201)
async def create_project(
    payload: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user),
) -> ResponseEnvelope[ProjectResponse]:
    project = await service.create(payload, owner=current_user)
    return ResponseEnvelope(status="success", data=ProjectResponse.model_validate(project))
```

### Pattern 2: Standard Response Envelope
**What:** All API responses wrapped in `{"status": "success"|"error", "data": ..., "meta": {...}}` as defined in API spec.
**When to use:** Every response.
**Example:**
```python
# api/envelope.py
from typing import Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

T = TypeVar("T")

class Meta(BaseModel):
    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex[:12]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int

class ResponseEnvelope(BaseModel, Generic[T]):
    status: str = "success"
    data: T
    meta: Meta = Field(default_factory=Meta)

class PaginatedEnvelope(BaseModel, Generic[T]):
    status: str = "success"
    data: list[T]
    meta: Meta = Field(default_factory=Meta)
    pagination: PaginationMeta | None = None

class ErrorResponse(BaseModel):
    status: str = "error"
    error: ErrorDetail
    meta: Meta = Field(default_factory=Meta)

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict] | None = None
```

### Pattern 3: Dependency Injection Chain
**What:** FastAPI `Depends()` for database sessions, auth, Redis, and event bus.
**When to use:** Every route handler.
**Example:**
```python
# api/deps.py
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from codebot.db.engine import async_session_factory
from codebot.db.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    api_key: str | None = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    if token:
        return await _resolve_jwt_user(token, db)
    if api_key:
        return await _resolve_api_key_user(api_key, db)
    raise HTTPException(status_code=401, detail="Not authenticated")

def require_role(*roles: str):
    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role.value.lower() not in [r.lower() for r in roles]:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return _check
```

### Pattern 4: NATS-to-WebSocket Bridge
**What:** A background task subscribes to NATS JetStream events and forwards them to Socket.IO rooms scoped by project_id.
**When to use:** Real-time pipeline and agent status updates.
**Example:**
```python
# websocket/bridge.py
import socketio
from codebot.events.bus import EventBus

async def start_nats_bridge(sio: socketio.AsyncServer, bus: EventBus) -> None:
    sub = await bus.subscribe("agent.>")
    async for msg in sub.messages:
        data = json.loads(msg.data)
        project_id = data.get("project_id")
        if project_id:
            await sio.emit(
                msg.subject.replace("codebot.events.", ""),
                data,
                room=f"project:{project_id}",
            )
```

### Pattern 5: FastAPI Lifespan for Resource Management
**What:** Use FastAPI `lifespan` context manager to connect/disconnect NATS, Redis, Socket.IO on startup/shutdown.
**When to use:** Application startup and shutdown.
**Example:**
```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.event_bus = await create_event_bus(settings.nats_url)
    app.state.redis = await create_redis_pool(settings.redis_url)
    await start_nats_bridge(sio, app.state.event_bus)
    yield
    # Shutdown
    await app.state.event_bus.disconnect()
    await app.state.redis.close()

app = FastAPI(title="CodeBot", lifespan=lifespan)
```

### Anti-Patterns to Avoid
- **Fat routes:** Do NOT put business logic in route handlers. Routes should be 5-10 lines max: parse input, call service, return response.
- **Mixing sync and async:** ALL database operations MUST use `async` session. Never use `psycopg2` or synchronous SQLAlchemy.
- **Direct NATS from routes:** Routes should not publish to NATS directly. Services emit events; the WebSocket bridge forwards them. This keeps routes testable without NATS.
- **Global mutable state:** Do NOT store state in module-level variables. Use `app.state` or dependency injection.
- **Hardcoded secrets:** JWT secrets, database passwords MUST come from `Settings` (env vars), never hardcoded.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT token management | Custom JWT implementation | PyJWT `encode`/`decode` with `HS256` or `RS256` | Edge cases: expiry, clock skew, refresh rotation, revocation |
| Password hashing | Custom hash function | `bcrypt.hashpw` / `bcrypt.checkpw` | Bcrypt handles salting, cost factor, timing-safe comparison |
| Rate limiting | Custom counter middleware | SlowAPI with Redis backend | Token bucket, distributed counting, per-route config, retry-after headers |
| WebSocket room management | Custom connection registry | python-socketio rooms | Auto-cleanup on disconnect, Redis adapter for multi-process |
| Response validation | Manual dict construction | Pydantic `response_model` on routes | Auto-validation, serialization, OpenAPI schema generation |
| CORS handling | Custom headers middleware | `fastapi.middleware.cors.CORSMiddleware` | Handles preflight, credentials, allowed origins correctly |
| API key generation | `uuid4()` as API key | `secrets.token_urlsafe(32)` + SHA-256 hash storage | Cryptographically secure, prefix-based display, hash-only storage |

**Key insight:** The API spec defines exact response shapes, status codes, and error formats. Using Pydantic response models + FastAPI response_model validation eliminates entire classes of bugs where responses don't match the spec.

## Common Pitfalls

### Pitfall 1: Async Session Lifecycle
**What goes wrong:** Database sessions leak when exceptions occur or sessions are not properly scoped.
**Why it happens:** Using `async_session_factory()` without `async with` or failing to close sessions in error paths.
**How to avoid:** Always use `async with async_session_factory() as session:` in the `get_db` dependency. FastAPI's DI automatically calls cleanup on generator dependencies.
**Warning signs:** "too many connections" errors, connection pool exhaustion.

### Pitfall 2: JWT Refresh Token Rotation
**What goes wrong:** Refresh tokens are reused after rotation, enabling token replay attacks.
**Why it happens:** Not invalidating old refresh tokens when new ones are issued.
**How to avoid:** Store refresh tokens in Redis with a TTL. On refresh, delete the old token and issue a new one. If a deleted token is presented, revoke ALL tokens for that user (compromise detected).
**Warning signs:** Same refresh token working after a successful refresh call.

### Pitfall 3: Socket.IO ASGI Mount Path Collision
**What goes wrong:** Socket.IO requests get intercepted by FastAPI routes, or Socket.IO fails to connect.
**Why it happens:** Mounting Socket.IO ASGI app at the wrong path, or CORS mismatch between FastAPI and Socket.IO.
**How to avoid:** Mount Socket.IO at a dedicated path (e.g., `/ws`) using `socketio.ASGIApp(sio, socketio_path="/ws")` and mount it as a sub-application on the FastAPI app. Ensure CORS settings match.
**Warning signs:** WebSocket connection failures, 404 on Socket.IO handshake.

### Pitfall 4: N+1 Query on List Endpoints
**What goes wrong:** Listing projects with pipelines generates one query per project for eager-loaded relationships.
**Why it happens:** SQLAlchemy lazy loading is the default. List endpoints that access relationships trigger N+1 queries.
**How to avoid:** Use `selectinload()` or `joinedload()` options on list queries. Keep list endpoint response schemas lean (don't include nested relationships unless explicitly needed).
**Warning signs:** Slow list endpoints, many SQL queries per request in debug logs.

### Pitfall 5: Missing Request Validation on Pipeline State Transitions
**What goes wrong:** A pipeline that is already `CANCELLED` gets started, or a `RUNNING` pipeline gets started again.
**Why it happens:** Route handlers don't validate the current state before performing the transition.
**How to avoid:** Add state transition validation in the service layer. Define valid transitions: `PENDING -> RUNNING`, `RUNNING -> PAUSED`, `PAUSED -> RUNNING`, `RUNNING/PAUSED -> CANCELLED`. Return 400/409 for invalid transitions.
**Warning signs:** Duplicate running pipelines, orphaned agent processes.

### Pitfall 6: Rate Limiter Key Function with Proxies
**What goes wrong:** All users share the same rate limit because `get_remote_address` returns the proxy IP.
**Why it happens:** Behind a reverse proxy (nginx, cloudflare), the client IP is in `X-Forwarded-For`, not the TCP source.
**How to avoid:** Use a custom `key_func` that reads `X-Forwarded-For` header, or better yet, use the authenticated user ID as the rate limit key for authenticated endpoints.
**Warning signs:** One user hitting rate limits blocks all users.

## Code Examples

Verified patterns from existing codebase and official docs:

### JWT Token Creation
```python
# auth/jwt.py
import jwt
from datetime import datetime, timedelta, timezone
from uuid import UUID

from codebot.config import settings

def create_access_token(user_id: UUID, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def create_refresh_token(user_id: UUID) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
```

### Password Hashing
```python
# auth/password.py
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
```

### Socket.IO Server Setup
```python
# websocket/manager.py
import socketio

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # Restrict in production
    logger=False,
    engineio_logger=False,
)

@sio.event
async def connect(sid, environ, auth):
    # Validate JWT from auth dict or query params
    token = auth.get("token") if auth else None
    if not token:
        raise ConnectionRefusedError("Authentication required")
    # Decode and validate
    user = await validate_ws_token(token)
    # Join project room if specified
    project_id = environ.get("HTTP_X_PROJECT_ID") or auth.get("project_id")
    if project_id:
        await sio.enter_room(sid, f"project:{project_id}")

@sio.event
async def subscribe(sid, data):
    channels = data.get("channels", [])
    for channel in channels:
        await sio.enter_room(sid, channel)

@sio.event
async def disconnect(sid):
    pass  # Rooms auto-cleaned by python-socketio
```

### Service Layer Pattern
```python
# services/project_service.py
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from codebot.db.models.project import Project, ProjectStatus
from codebot.db.models.user import User
from codebot.api.schemas.projects import ProjectCreate, ProjectUpdate

class ProjectService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, payload: ProjectCreate, owner: User) -> Project:
        project = Project(
            user_id=owner.id,
            name=payload.name,
            description=payload.description or "",
            prd_content=payload.prd_content or "",
            prd_format=payload.prd_format or "markdown",
            tech_stack=payload.tech_stack,
            config=payload.settings,
        )
        self._db.add(project)
        await self._db.commit()
        await self._db.refresh(project)
        return project

    async def list_for_user(
        self, user_id: UUID, *, page: int = 1, per_page: int = 20,
        status: str | None = None, search: str | None = None,
    ) -> tuple[list[Project], int]:
        query = select(Project).where(Project.user_id == user_id)
        if status:
            query = query.where(Project.status == ProjectStatus(status.upper()))
        if search:
            query = query.where(Project.name.ilike(f"%{search}%"))
        count = await self._db.scalar(
            select(func.count()).select_from(query.subquery())
        )
        results = await self._db.scalars(
            query.order_by(Project.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(results.all()), count or 0
```

### Testing API Endpoints
```python
# tests/api/test_projects.py
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
async def test_create_project(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Test Project", "prd_source": "text", "prd_content": "Build something"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["name"] == "Test Project"

@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient) -> None:
    response = await client.get("/api/v1/projects")
    assert response.status_code == 401
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-jose for JWT | PyJWT | 2024-2025 | python-jose unmaintained; FastAPI docs now recommend PyJWT |
| passlib[bcrypt] wrapper | Direct bcrypt | 2024 | passlib adds unnecessary abstraction; bcrypt 5.0 is cleaner |
| FastAPI native WebSocket | python-socketio ASGI mount | Stable since 2023 | Socket.IO protocol provides rooms, reconnection, fallbacks needed for dashboard |
| In-memory rate limiting | SlowAPI + Redis | Production standard | Redis-backed rate limiting scales across multiple server instances |
| `@app.on_event("startup")` | `lifespan` context manager | FastAPI 0.109+ (2024) | `on_event` deprecated; `lifespan` is the official approach |
| `OAuth2PasswordBearer` only | Dual auth (JWT + API Key) | N/A | API keys needed for CI/CD, CLI, server-to-server; JWT for interactive |
| fastapi-slim | fastapi[standard] | FastAPI 0.130+ | fastapi-slim dropped; use `fastapi` or `fastapi[standard]` |

**Deprecated/outdated:**
- `@app.on_event("startup"/"shutdown")`: Use `lifespan` async context manager instead.
- `fastapi-slim`: No longer published. Use `fastapi` directly.
- `python-jose`: No longer maintained. Use `PyJWT`.
- Pydantic v1 `Config` class: Use `model_config = ConfigDict(...)` (already done in project).
- Strict Content-Type checking is now default in FastAPI 0.135+ -- can disable with `strict_content_type=False` if needed for non-JSON endpoints.

## Open Questions

1. **HS256 vs RS256 for JWT signing**
   - What we know: SYSTEM_DESIGN.md specifies RS256 (RSA). API spec just says "JWT Bearer Token". HS256 is simpler (single secret), RS256 allows public key verification by clients.
   - What's unclear: Whether clients (dashboard, CLI) need to verify tokens independently or only the server verifies.
   - Recommendation: Start with HS256 (symmetric) for simplicity. Add RS256 support later if needed for distributed verification. The existing `Settings` class would need a `jwt_secret` field added either way.

2. **Socket.IO vs native WebSocket for the WebSocket endpoint**
   - What we know: API spec section 14 defines a WebSocket protocol with `type` envelopes and `subscribe`/`unsubscribe` actions. The dashboard skill specifies Socket.IO. The `codebot-api-endpoint` skill uses Socket.IO.
   - What's unclear: Whether the API spec's WebSocket protocol maps 1:1 to Socket.IO event semantics or requires adaptation.
   - Recommendation: Use python-socketio. The `type` field in the API spec maps to Socket.IO event names. Subscribe/unsubscribe maps to Socket.IO rooms. This is the clearest path.

3. **Refresh token storage: Redis vs PostgreSQL**
   - What we know: Refresh tokens need to be revocable. Redis provides TTL-based expiry. PostgreSQL provides durability.
   - What's unclear: Whether server restarts should invalidate all refresh tokens (Redis) or preserve them (PostgreSQL).
   - Recommendation: Redis with TTL. Refresh tokens are short-lived (7 days). Server restart forcing re-login is acceptable for v1. Simpler than a DB table with cleanup jobs.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.24+ |
| Config file | `apps/server/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `cd apps/server && uv run pytest tests/ -x -q` |
| Full suite command | `cd apps/server && uv run pytest tests/ -v --strict-markers` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SRVR-01 | Project CRUD endpoints return correct responses | integration | `cd apps/server && uv run pytest tests/api/test_projects.py -x` | No -- Wave 0 |
| SRVR-01 | Pipeline start/stop/pause/resume endpoints | integration | `cd apps/server && uv run pytest tests/api/test_pipelines.py -x` | No -- Wave 0 |
| SRVR-01 | Agent status query endpoints | integration | `cd apps/server && uv run pytest tests/api/test_agents.py -x` | No -- Wave 0 |
| SRVR-02 | WebSocket connects with valid JWT | integration | `cd apps/server && uv run pytest tests/websocket/test_manager.py -x` | No -- Wave 0 |
| SRVR-02 | Events broadcast to correct project rooms | unit | `cd apps/server && uv run pytest tests/websocket/test_bridge.py -x` | No -- Wave 0 |
| SRVR-03 | Unauthorized requests rejected with 401 | integration | `cd apps/server && uv run pytest tests/api/test_auth.py::test_unauthorized -x` | No -- Wave 0 |
| SRVR-03 | JWT login returns valid tokens | integration | `cd apps/server && uv run pytest tests/api/test_auth.py::test_login -x` | No -- Wave 0 |
| SRVR-03 | API key authentication works | integration | `cd apps/server && uv run pytest tests/api/test_auth.py::test_api_key -x` | No -- Wave 0 |
| SRVR-03 | Role-based access control enforced | integration | `cd apps/server && uv run pytest tests/api/test_auth.py::test_rbac -x` | No -- Wave 0 |
| SRVR-04 | Pipeline preset selection accepted | integration | `cd apps/server && uv run pytest tests/api/test_pipelines.py::test_preset_selection -x` | No -- Wave 0 |
| SRVR-05 | Agent start/stop/restart endpoints | integration | `cd apps/server && uv run pytest tests/api/test_agents.py::test_agent_lifecycle -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd apps/server && uv run pytest tests/ -x -q`
- **Per wave merge:** `cd apps/server && uv run pytest tests/ -v --strict-markers`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/api/__init__.py` -- test package
- [ ] `tests/api/conftest.py` -- shared fixtures (async client, auth headers, test user factory)
- [ ] `tests/api/test_auth.py` -- covers SRVR-03
- [ ] `tests/api/test_projects.py` -- covers SRVR-01 (projects)
- [ ] `tests/api/test_pipelines.py` -- covers SRVR-01 (pipelines), SRVR-04
- [ ] `tests/api/test_agents.py` -- covers SRVR-01 (agents), SRVR-05
- [ ] `tests/websocket/__init__.py` -- test package
- [ ] `tests/websocket/test_manager.py` -- covers SRVR-02 (connection)
- [ ] `tests/websocket/test_bridge.py` -- covers SRVR-02 (event forwarding)
- [ ] `tests/auth/__init__.py` -- test package
- [ ] `tests/auth/test_jwt.py` -- unit tests for JWT creation/verification
- [ ] `tests/auth/test_password.py` -- unit tests for password hashing

## Sources

### Primary (HIGH confidence)
- PyPI package index -- verified current versions for all dependencies (FastAPI 0.135.1, Pydantic 2.12.5, SQLAlchemy 2.0.48, PyJWT 2.12.1, bcrypt 5.0.0, python-socketio 5.16.1, slowapi 0.1.9, uvicorn 0.42.0, pydantic-settings 2.13.1)
- Existing codebase -- `apps/server/src/codebot/` (main.py, config.py, db/, events/)
- Project skills -- `codebot-api-endpoint`, `codebot-stack-decisions` SKILL.md files
- `docs/api/API_SPECIFICATION.md` -- full endpoint definitions with request/response schemas
- `docs/design/SYSTEM_DESIGN.md` section 19 -- auth/authorization design
- `docs/design/DATA_MODELS.md` -- ORM model specifications

### Secondary (MEDIUM confidence)
- [FastAPI official docs - JWT tutorial](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) -- PyJWT recommendation, OAuth2 patterns
- [FastAPI GitHub Discussions #14807](https://github.com/fastapi/fastapi/discussions/14807) -- WebSocket library recommendations for 2026
- [SlowAPI documentation](https://slowapi.readthedocs.io/) -- Rate limiting setup with Redis

### Tertiary (LOW confidence)
- WebSearch results on python-socketio + FastAPI integration patterns -- multiple sources agree on ASGI mount approach
- WebSearch results on SlowAPI + Redis production patterns -- benchmarks and case studies

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries verified via PyPI, existing pyproject.toml already defines core deps, only 4 new deps needed
- Architecture: HIGH -- existing codebase provides clear patterns, skill files define exact structure, API spec is comprehensive
- Pitfalls: HIGH -- well-documented FastAPI/SQLAlchemy async gotchas, verified against official docs
- WebSocket integration: MEDIUM -- python-socketio ASGI mount is standard but exact bridge pattern with NATS is project-specific

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable libraries, 30-day window)
