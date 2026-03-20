"""CodeBot FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from codebot.api.middleware import setup_middleware
from codebot.api.routes.agents import router as agents_router
from codebot.api.routes.auth import router as auth_router
from codebot.api.routes.health import router as health_router
from codebot.api.routes.pipelines import (
    project_pipelines_router,
    router as pipelines_router,
)
from codebot.api.routes.projects import router as projects_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager.

    Placeholder for startup/shutdown hooks (NATS, Redis connections, etc.).
    """
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="CodeBot",
    description="Multi-agent autonomous software development platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure middleware (CORS, rate limiting, request-ID)
setup_middleware(app)

# Register routers
app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(pipelines_router, prefix="/api/v1")
app.include_router(project_pipelines_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
