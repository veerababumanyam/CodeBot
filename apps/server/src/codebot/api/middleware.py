"""Middleware setup for the CodeBot FastAPI application.

Configures CORS, rate limiting, and request-ID injection.
"""

from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from codebot.config import settings


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware on the given FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[settings.rate_limit_default],
    )
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Request-ID injection
    @app.middleware("http")
    async def add_request_id(request: Request, call_next) -> Response:  # type: ignore[type-arg]
        """Add a unique X-Request-ID header to every response."""
        request_id = uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
