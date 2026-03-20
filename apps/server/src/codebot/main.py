"""CodeBot FastAPI application entrypoint."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from codebot.api.middleware import setup_middleware
from codebot.api.routes.agents import router as agents_router
from codebot.api.routes.auth import router as auth_router
from codebot.api.routes.brainstorm import router as brainstorm_router
from codebot.api.routes.health import router as health_router
from codebot.api.routes.pipelines import (
    project_pipelines_router,
    router as pipelines_router,
)
from codebot.api.routes.projects import router as projects_router
from codebot.config import settings
from codebot.events.bus import create_event_bus
from codebot.websocket.bridge import start_nats_bridge
from codebot.websocket.manager import sio

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager.

    Connects to NATS event bus and starts the WebSocket bridge on startup.
    Gracefully shuts down the bridge and disconnects from NATS on shutdown.
    """
    # Startup
    try:
        app.state.event_bus = await create_event_bus(settings.nats_url)
        logger.info("Event bus connected to %s", settings.nats_url)
    except Exception:
        logger.warning(
            "Failed to connect to NATS at %s -- WebSocket bridge disabled",
            settings.nats_url,
            exc_info=True,
        )
        app.state.event_bus = None

    if app.state.event_bus is not None:
        app.state.bridge_task = await start_nats_bridge(sio, app.state.event_bus)
    else:
        app.state.bridge_task = None

    yield

    # Shutdown
    if app.state.bridge_task is not None:
        app.state.bridge_task.cancel()
    if app.state.event_bus is not None:
        await app.state.event_bus.disconnect()


fastapi_app = FastAPI(
    title="CodeBot",
    description="Multi-agent autonomous software development platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure middleware (CORS, rate limiting, request-ID)
setup_middleware(fastapi_app)

# Register routers
fastapi_app.include_router(health_router)
fastapi_app.include_router(auth_router, prefix="/api/v1")
fastapi_app.include_router(projects_router, prefix="/api/v1")
fastapi_app.include_router(brainstorm_router, prefix="/api/v1")
fastapi_app.include_router(pipelines_router, prefix="/api/v1")
fastapi_app.include_router(project_pipelines_router, prefix="/api/v1")
fastapi_app.include_router(agents_router, prefix="/api/v1")

# Wrap FastAPI with Socket.IO ASGI app so both share the same server.
# Socket.IO handles /socket.io/ path; everything else falls through to FastAPI.
import socketio as _socketio

app = _socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
