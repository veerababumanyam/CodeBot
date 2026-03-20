"""Socket.IO server with JWT auth and room management for real-time streaming."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from urllib.parse import parse_qs

import socketio
from agent_sdk.models.events import EventEnvelope, EventType

from codebot.auth.jwt import decode_token
from codebot.config import settings
from codebot.events.bus import EventBus, create_event_bus, publish_event
from codebot.input.extractor import RequirementExtractor

logger = logging.getLogger(__name__)

# Singletons for extractor and event bus (initialized on demand or in main)
_extractor = RequirementExtractor()
_event_bus: EventBus | None = None

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # Will be restricted per settings in production
    logger=False,
    engineio_logger=False,
)


async def get_event_bus() -> EventBus:
    """Lazy initialization of the EventBus."""
    global _event_bus
    if _event_bus is None:
        _event_bus = await create_event_bus(settings.nats_url)
    
    # After the check above, _event_bus should not be None
    # but we ensure the analyzer knows that.
    bus = _event_bus
    if bus is None:
        # Emergency re-initialization (satisfies analyzer)
        bus = await create_event_bus(settings.nats_url)
        _event_bus = bus
        
    if not bus.is_connected:
        await bus.connect()
    
    return bus



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
        if not settings.debug:
            raise ConnectionRefusedError("Authentication required")
        # Dev mode: allow unauthenticated connections
        payload = {"sub": "admin"}
    else:
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
    channels: list[str] = []
    if isinstance(data, dict):
        raw_channels = data.get("channels")
        if isinstance(raw_channels, list):
            channels.extend(
                channel for channel in raw_channels if isinstance(channel, str)
            )

        raw_channel = data.get("channel")
        if isinstance(raw_channel, str):
            channels.append(raw_channel)

        project_id = data.get("project_id")
        if isinstance(project_id, str):
            channels.append(f"project:{project_id}")

    for channel in channels:
        await sio.enter_room(sid, channel)


@sio.event  # type: ignore[misc]
async def unsubscribe(sid: str, data: dict | None = None) -> None:
    """Unsubscribe from channels.

    Args:
        sid: Socket.IO session ID.
        data: Dict with ``channels`` list.
    """
    channels: list[str] = []
    if isinstance(data, dict):
        raw_channels = data.get("channels")
        if isinstance(raw_channels, list):
            channels.extend(
                channel for channel in raw_channels if isinstance(channel, str)
            )

        raw_channel = data.get("channel")
        if isinstance(raw_channel, str):
            channels.append(raw_channel)

        project_id = data.get("project_id")
        if isinstance(project_id, str):
            channels.append(f"project:{project_id}")

    for channel in channels:
        await sio.leave_room(sid, channel)


@sio.on("chat.send")  # type: ignore[misc]
async def chat_send(sid: str, data: dict) -> None:
    """Handle chat.send event from client.

    Args:
        sid: Socket.IO session ID.
        data: Dict with ``project_id`` and ``content``.
    """
    session = await sio.get_session(sid)
    project_id = data.get("project_id") or session.get("project_id")
    content = data.get("content")
    attachments = data.get("attachments", [])

    if not project_id or (not content and not attachments):
        return

    room = f"project:{project_id}"
    message = {
        "id": f"msg_{int(datetime.now(UTC).timestamp() * 1000)}",
        "type": "user",
        "content": content,
        "attachments": attachments,
        "timestamp": datetime.now(UTC).isoformat(),
        "user_id": session.get("user_id"),
    }

    # 1. Echo back to the project room
    await sio.emit("chat.message", message, room=room)

    import json
    
    # 2. Publish to NATS for persistence and agent processing
    bus = await get_event_bus()
    payload_data = {
        "project_id": project_id,
        "content": content, 
        "attachments": attachments,
        "source": "chat", 
        "message_id": message["id"]
    }
    envelope = EventEnvelope(
        event_type=EventType.USER_INPUT_RECEIVED,
        payload=json.dumps(payload_data).encode("utf-8"),
    )
    await publish_event(bus, envelope)

    # 3. Trigger requirement extraction (non-blocking)
    # In a real system, this might be handled by an agent listening to NATS,
    # but for immediate feedback we can trigger it here or let the orchestrator do it.
    logger.info("Chat message processed: %s", message["id"])


@sio.on("chat.approve")  # type: ignore[misc]
async def chat_approve(sid: str, data: dict) -> None:
    """Handle chat.approve event for gate approvals.

    Args:
        sid: Socket.IO session ID.
        data: Dict with ``project_id``, ``gate_id``, and ``approved``.
    """
    project_id = data.get("project_id")
    gate_id = data.get("gate_id")
    approved = data.get("approved", False)

    if not project_id or not gate_id:
        return

    bus = await get_event_bus()
    envelope = EventEnvelope(
        event_type=EventType.GATE_APPROVAL_SUBMITTED,
        project_id=project_id,
        payload={"gate_id": gate_id, "approved": approved},
    )
    await publish_event(bus, envelope)
    logger.info(
        "Gate approval submitted: project=%s gate=%s approved=%s",
        project_id,
        gate_id,
        approved,
    )


@sio.event  # type: ignore[misc]
async def disconnect(sid: str) -> None:
    """Handle client disconnection.

    Args:
        sid: Socket.IO session ID.
    """
    logger.info("WebSocket client disconnected: sid=%s", sid)
