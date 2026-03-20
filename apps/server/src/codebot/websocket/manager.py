"""Socket.IO server with JWT auth and room management for real-time streaming."""

from __future__ import annotations

import logging
from urllib.parse import parse_qs

import socketio

from codebot.auth.jwt import decode_token

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # Will be restricted per settings in production
    logger=False,
    engineio_logger=False,
)

# ASGI app to mount on FastAPI at path "/ws"
socket_app = socketio.ASGIApp(sio, socketio_path="/ws")


@sio.event  # type: ignore[misc]
async def connect(
    sid: str,
    environ: dict,
    auth: dict | None = None,
) -> None:
    """Handle new WebSocket connections with JWT authentication.

    Extracts token from auth dict or query string, validates it,
    joins project rooms if specified, and emits connection.established.

    Args:
        sid: Socket.IO session ID.
        environ: ASGI/WSGI environ dict.
        auth: Optional auth dict from client (contains token, project_id).

    Raises:
        ConnectionRefusedError: If authentication fails.
    """
    token = None
    project_id = None

    # Try auth dict first
    if isinstance(auth, dict):
        token = auth.get("token")
        project_id = auth.get("project_id")

    # Fallback to query string
    if token is None:
        query_string = environ.get("QUERY_STRING", "")
        if isinstance(query_string, bytes):
            query_string = query_string.decode()
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]
        if project_id is None:
            project_id = params.get("project_id", [None])[0]

    if not token:
        raise ConnectionRefusedError("Authentication required")

    try:
        payload = decode_token(token)
    except Exception:
        raise ConnectionRefusedError("Authentication required") from None

    # Join project room if specified
    subscriptions: list[str] = []
    if project_id:
        room = f"project:{project_id}"
        await sio.enter_room(sid, room)
        subscriptions.append(f"project.{project_id}")

    # Store session data
    await sio.save_session(
        sid, {"user_id": payload["sub"], "project_id": project_id}
    )

    # Emit connection established event
    await sio.emit(
        "connection.established",
        {"connection_id": sid, "subscriptions": subscriptions},
        to=sid,
    )

    logger.info("WebSocket client connected: sid=%s user=%s", sid, payload["sub"])


@sio.event  # type: ignore[misc]
async def subscribe(sid: str, data: dict | None = None) -> None:
    """Subscribe to additional channels.

    Args:
        sid: Socket.IO session ID.
        data: Dict with ``channels`` list.
    """
    channels = data.get("channels", []) if isinstance(data, dict) else []
    for channel in channels:
        await sio.enter_room(sid, channel)


@sio.event  # type: ignore[misc]
async def unsubscribe(sid: str, data: dict | None = None) -> None:
    """Unsubscribe from channels.

    Args:
        sid: Socket.IO session ID.
        data: Dict with ``channels`` list.
    """
    channels = data.get("channels", []) if isinstance(data, dict) else []
    for channel in channels:
        await sio.leave_room(sid, channel)


@sio.event  # type: ignore[misc]
async def disconnect(sid: str) -> None:
    """Handle client disconnection.

    Args:
        sid: Socket.IO session ID.
    """
    logger.info("WebSocket client disconnected: sid=%s", sid)
