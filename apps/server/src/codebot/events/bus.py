"""NATS JetStream event bus for inter-agent messaging.

Implements Pattern 4 from research: durable JetStream consumers with
subject-based routing on the ``codebot.events.>`` subject hierarchy.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import nats
from nats.js import JetStreamContext
from nats.js.api import StreamConfig

from agent_sdk.models.events import EventEnvelope

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_STREAM_NAME = "codebot-events"
_SUBJECT_PREFIX = "codebot.events"


class EventBus:
    """NATS JetStream event bus for inter-agent messaging.

    Usage::

        bus = EventBus()
        await bus.connect()
        await bus.publish("agent.started", payload_bytes)
        sub = await bus.subscribe("agent.>")
        msg = await sub.next_msg()
        await bus.disconnect()
    """

    def __init__(self, nats_url: str = "nats://localhost:4222") -> None:
        """Initialise the EventBus.

        Args:
            nats_url: NATS server URL (default: nats://localhost:4222).
        """
        self._nats_url = nats_url
        self._nc: nats.NATS | None = None
        self._js: JetStreamContext | None = None

    @property
    def is_connected(self) -> bool:
        """Return True if the underlying NATS connection is open."""
        return self._nc is not None and not self._nc.is_closed

    async def connect(self) -> None:
        """Connect to NATS and initialize JetStream context.

        Creates the ``codebot-events`` stream (idempotent — safe to call
        if the stream already exists).

        Raises:
            nats.errors.NoServersError: If NATS is not reachable.
        """
        self._nc = await nats.connect(self._nats_url)
        self._js = self._nc.jetstream()
        await self._ensure_stream()
        logger.info("EventBus connected to %s", self._nats_url)

    async def _ensure_stream(self) -> None:
        """Create the JetStream stream if it does not already exist."""
        assert self._js is not None, "JetStream context not initialised"
        try:
            await self._js.add_stream(
                StreamConfig(
                    name=_STREAM_NAME,
                    subjects=[f"{_SUBJECT_PREFIX}.>"],
                    retention="limits",
                    max_msgs=100_000,
                )
            )
            logger.debug("Stream '%s' created", _STREAM_NAME)
        except Exception as exc:
            # Stream already exists — that is fine.
            if "stream name already in use" in str(exc).lower() or "already exists" in str(exc).lower():
                logger.debug("Stream '%s' already exists, skipping creation", _STREAM_NAME)
            else:
                raise

    async def disconnect(self) -> None:
        """Drain and close the NATS connection.

        Draining allows in-flight messages to be delivered before closing.
        Safe to call multiple times.
        """
        if self._nc is not None and not self._nc.is_closed:
            await self._nc.drain()
            self._nc = None
            self._js = None
            logger.info("EventBus disconnected")

    async def publish(self, event_type: str, payload: bytes) -> None:
        """Publish a raw byte payload to the JetStream for ``event_type``.

        Args:
            event_type: Dotted event type string (e.g. ``agent.started``).
                        Appended to ``codebot.events.`` to form the NATS subject.
            payload: Raw bytes (typically JSON-serialized Pydantic model).

        Raises:
            RuntimeError: If not connected.
        """
        if self._js is None:
            raise RuntimeError("EventBus is not connected. Call connect() first.")
        subject = f"{_SUBJECT_PREFIX}.{event_type}"
        await self._js.publish(subject, payload)
        logger.debug("Published to %s (%d bytes)", subject, len(payload))

    async def subscribe(
        self,
        event_type: str = ">",
        durable: str | None = None,
    ) -> nats.js.api.PushSubscription:  # type: ignore[name-defined]
        """Subscribe to events on a subject filter.

        Args:
            event_type: Subject suffix filter. Use ``>`` for all events,
                        ``agent.>`` for all agent events, or a specific
                        event type like ``agent.started``.
            durable: Optional durable consumer name for persistent delivery.

        Returns:
            A NATS JetStream push subscription.

        Raises:
            RuntimeError: If not connected.
        """
        if self._js is None:
            raise RuntimeError("EventBus is not connected. Call connect() first.")
        subject = f"{_SUBJECT_PREFIX}.{event_type}"
        if durable:
            return await self._js.subscribe(subject, durable=durable)
        return await self._js.subscribe(subject)


async def create_event_bus(nats_url: str = "nats://localhost:4222") -> EventBus:
    """Create, connect, and return an EventBus instance.

    Args:
        nats_url: NATS server URL.

    Returns:
        A connected EventBus ready for use.
    """
    bus = EventBus(nats_url=nats_url)
    await bus.connect()
    return bus


async def publish_event(bus: EventBus, envelope: EventEnvelope) -> None:
    """Serialize an EventEnvelope and publish it via the event bus.

    Args:
        bus: A connected EventBus instance.
        envelope: The EventEnvelope Pydantic model to publish.
    """
    # Use the dotted lowercase form of the event_type as the subject suffix
    event_type_slug = envelope.event_type.value.lower().replace("_", ".")
    payload = envelope.model_dump_json().encode()
    await bus.publish(event_type_slug, payload)
