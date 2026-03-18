"""Integration tests for the NATS JetStream event bus.

These tests require a live NATS server with JetStream enabled.
They are skipped automatically if NATS is not reachable.

Run with:
    cd apps/server && uv run pytest tests/test_events.py -v
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import pytest

from agent_sdk.models.enums import AgentStatus, AgentType, EventType
from agent_sdk.models.events import AgentEvent, EventEnvelope
from codebot.events.bus import EventBus, create_event_bus, publish_event

# ---------------------------------------------------------------------------
# NATS reachability check
# ---------------------------------------------------------------------------

NATS_URL = "nats://localhost:4222"


async def _nats_is_reachable() -> bool:
    """Return True if NATS server is reachable."""
    import nats

    try:
        nc = await nats.connect(NATS_URL, connect_timeout=1)
        await nc.drain()
        return True
    except Exception:
        return False


def _check_nats() -> bool:
    """Synchronously check NATS reachability (runs in a temporary event loop)."""
    return asyncio.run(_nats_is_reachable())


_NATS_UNAVAILABLE = not _check_nats()

nats_required = pytest.mark.skipif(
    _NATS_UNAVAILABLE,
    reason="NATS server not reachable at nats://localhost:4222 — skipping integration tests",
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def event_bus() -> EventBus:  # type: ignore[return]
    """Provide a connected EventBus that cleans up after each test."""
    bus = EventBus(nats_url=NATS_URL)
    await bus.connect()
    yield bus
    await bus.disconnect()


# ---------------------------------------------------------------------------
# Test 1: Basic JetStream pub/sub
# ---------------------------------------------------------------------------


@nats_required
@pytest.mark.asyncio
async def test_jetstream_pub_sub() -> None:
    """Publish a message and receive it within 1 second via JetStream."""
    bus = EventBus(nats_url=NATS_URL)
    await bus.connect()

    payload = b'{"test": "hello"}'
    event_type = f"agent.started.{uuid.uuid4().hex[:8]}"  # unique per run

    sub = await bus.subscribe(event_type)
    await bus.publish(event_type, payload)

    msg = await asyncio.wait_for(sub.next_msg(), timeout=1.0)
    assert msg.data == payload

    await sub.unsubscribe()
    await bus.disconnect()


# ---------------------------------------------------------------------------
# Test 2: EventEnvelope round-trip
# ---------------------------------------------------------------------------


@nats_required
@pytest.mark.asyncio
async def test_event_envelope_roundtrip() -> None:
    """Serialize an AgentEvent envelope, publish, subscribe, and deserialize."""
    bus = EventBus(nats_url=NATS_URL)
    await bus.connect()

    agent_id = uuid.uuid4()
    inner_event = AgentEvent(
        agent_id=agent_id,
        agent_type=AgentType.ORCHESTRATOR,
        status=AgentStatus.RUNNING,
        timestamp=datetime.now(tz=timezone.utc),
        payload={"detail": "starting up"},
    )
    inner_bytes = inner_event.model_dump_json().encode()

    envelope = EventEnvelope(
        event_type=EventType.AGENT_STARTED,
        source_agent_id=agent_id,
        payload=inner_bytes,
        timestamp=datetime.now(tz=timezone.utc),
    )

    # Use a unique event type suffix per test run to avoid cross-test contamination
    unique_suffix = uuid.uuid4().hex[:8]
    event_type = f"agent.started.rt.{unique_suffix}"

    sub = await bus.subscribe(event_type)
    envelope_bytes = envelope.model_dump_json().encode()
    await bus.publish(event_type, envelope_bytes)

    msg = await asyncio.wait_for(sub.next_msg(), timeout=1.0)

    restored_envelope = EventEnvelope.model_validate_json(msg.data)
    assert restored_envelope.event_type is EventType.AGENT_STARTED
    assert restored_envelope.source_agent_id == agent_id

    restored_inner = AgentEvent.model_validate_json(restored_envelope.payload)
    assert restored_inner.agent_id == agent_id
    assert restored_inner.agent_type is AgentType.ORCHESTRATOR
    assert restored_inner.status is AgentStatus.RUNNING
    assert restored_inner.payload == {"detail": "starting up"}

    await sub.unsubscribe()
    await bus.disconnect()


# ---------------------------------------------------------------------------
# Test 3: Filtered subscription
# ---------------------------------------------------------------------------


@nats_required
@pytest.mark.asyncio
async def test_subscribe_filtered() -> None:
    """Subscribe to 'agent.>' and verify only agent events are received."""
    bus = EventBus(nats_url=NATS_URL)
    await bus.connect()

    unique = uuid.uuid4().hex[:8]
    agent_event_type = f"agent.started.{unique}"
    task_event_type = f"task.completed.{unique}"

    agent_sub = await bus.subscribe(f"agent.started.{unique}")

    await bus.publish(task_event_type, b"task_payload")
    await bus.publish(agent_event_type, b"agent_payload")

    # Should receive agent message
    msg = await asyncio.wait_for(agent_sub.next_msg(), timeout=1.0)
    assert msg.data == b"agent_payload"

    # Should NOT receive the task message (different subject filter)
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(agent_sub.next_msg(), timeout=0.2)

    await agent_sub.unsubscribe()
    await bus.disconnect()


# ---------------------------------------------------------------------------
# Test 4: publish_event convenience helper
# ---------------------------------------------------------------------------


@nats_required
@pytest.mark.asyncio
async def test_publish_event_helper() -> None:
    """Test the publish_event helper with EventEnvelope.

    publish_event maps EventType enum values to dotted lowercase NATS subjects.
    Subscribe first, then call publish_event, then confirm the message received
    matches what was sent.
    """
    bus = EventBus(nats_url=NATS_URL)
    await bus.connect()

    agent_id = uuid.uuid4()
    inner = AgentEvent(
        agent_id=agent_id,
        agent_type=AgentType.PLANNER,
        status=AgentStatus.COMPLETED,
    )
    envelope = EventEnvelope(
        event_type=EventType.AGENT_COMPLETED,
        source_agent_id=agent_id,
        payload=inner.model_dump_json().encode(),
    )

    # publish_event maps AGENT_COMPLETED -> "agent.completed"
    # Subscribe before publishing to only receive our message.
    sub = await bus.subscribe("agent.completed")

    await publish_event(bus, envelope)

    # Drain messages until we find the one from this test (identified by agent_id)
    found = False
    deadline = asyncio.get_event_loop().time() + 1.0
    while asyncio.get_event_loop().time() < deadline and not found:
        try:
            msg = await asyncio.wait_for(sub.next_msg(), timeout=0.3)
            restored = EventEnvelope.model_validate_json(msg.data)
            if restored.source_agent_id == agent_id:
                assert restored.event_type is EventType.AGENT_COMPLETED
                found = True
        except asyncio.TimeoutError:
            break

    assert found, "Did not receive the expected EventEnvelope within 1 second"

    await sub.unsubscribe()
    await bus.disconnect()


# ---------------------------------------------------------------------------
# Test 5: create_event_bus convenience function
# ---------------------------------------------------------------------------


@nats_required
@pytest.mark.asyncio
async def test_create_event_bus() -> None:
    """Test the create_event_bus factory function."""
    bus = await create_event_bus(NATS_URL)
    assert bus.is_connected

    unique = uuid.uuid4().hex[:8]
    event_type = f"test.factory.{unique}"
    sub = await bus.subscribe(event_type)
    await bus.publish(event_type, b"factory_test")

    msg = await asyncio.wait_for(sub.next_msg(), timeout=1.0)
    assert msg.data == b"factory_test"

    await sub.unsubscribe()
    await bus.disconnect()
    assert not bus.is_connected
