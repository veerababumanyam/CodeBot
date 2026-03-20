"""Integration test: verify agent events can be published for audit trail.

Tests EVNT-02/03/04: Agent events serialize to JSON, wrap in EventEnvelope,
and publish via EventBus for full audit trail reconstruction.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from agent_sdk.models.enums import AgentStatus, AgentType, EventType
from agent_sdk.models.events import AgentEvent, EventEnvelope


class TestEventAudit:
    """Integration tests for event sourcing audit trail."""

    def test_agent_event_serializes_to_json(self) -> None:
        """EVNT-03: Agent events serialize for persistence."""
        event = AgentEvent(
            agent_id=uuid.uuid4(),
            agent_type=AgentType.BRAINSTORM_FACILITATOR,
            status=AgentStatus.RUNNING,
        )
        json_bytes = event.model_dump_json().encode()
        assert b"BRAINSTORM_FACILITATOR" in json_bytes
        assert b"RUNNING" in json_bytes

    def test_event_envelope_wraps_agent_event(self) -> None:
        """EVNT-04: EventEnvelope wraps events for reconstruction."""
        agent_event = AgentEvent(
            agent_id=uuid.uuid4(),
            agent_type=AgentType.RESEARCHER,
            status=AgentStatus.COMPLETED,
        )
        envelope = EventEnvelope(
            event_type=EventType.AGENT_COMPLETED,
            source_agent_id=agent_event.agent_id,
            payload=agent_event.model_dump_json().encode(),
        )
        assert envelope.event_type == EventType.AGENT_COMPLETED
        assert envelope.payload is not None
        # Verify payload can be deserialized back (EVNT-02 replay)
        reconstructed = AgentEvent.model_validate_json(envelope.payload)
        assert reconstructed.agent_type == AgentType.RESEARCHER

    def test_envelope_payload_roundtrip(self) -> None:
        """EVNT-02: Events can be replayed from stored envelopes."""
        agent_id = uuid.uuid4()
        original_event = AgentEvent(
            agent_id=agent_id,
            agent_type=AgentType.TESTER,
            status=AgentStatus.RUNNING,
            payload={"test_count": 42},
        )
        envelope = EventEnvelope(
            event_type=EventType.AGENT_STARTED,
            source_agent_id=agent_id,
            payload=original_event.model_dump_json().encode(),
        )
        # Serialize envelope to JSON and back
        envelope_json = envelope.model_dump_json()
        restored_envelope = EventEnvelope.model_validate_json(envelope_json)
        restored_event = AgentEvent.model_validate_json(restored_envelope.payload)

        assert restored_event.agent_id == agent_id
        assert restored_event.agent_type == AgentType.TESTER
        assert restored_event.payload is not None
        assert restored_event.payload["test_count"] == 42

    @pytest.mark.asyncio
    async def test_agent_events_published(self) -> None:
        """EVNT-03: Events are published via EventBus."""
        from codebot.events.bus import publish_event

        mock_bus = AsyncMock()
        agent_event = AgentEvent(
            agent_id=uuid.uuid4(),
            agent_type=AgentType.TESTER,
            status=AgentStatus.RUNNING,
        )
        envelope = EventEnvelope(
            event_type=EventType.AGENT_STARTED,
            source_agent_id=agent_event.agent_id,
            payload=agent_event.model_dump_json().encode(),
        )
        await publish_event(mock_bus, envelope)
        mock_bus.publish.assert_awaited_once()
        call_args = mock_bus.publish.call_args
        assert "agent.started" in call_args[0][0]  # subject contains event type

    def test_all_agent_types_create_valid_events(self) -> None:
        """Every AgentType can produce a valid AgentEvent."""
        for agent_type in AgentType:
            event = AgentEvent(
                agent_id=uuid.uuid4(),
                agent_type=agent_type,
                status=AgentStatus.RUNNING,
            )
            json_bytes = event.model_dump_json().encode()
            assert agent_type.value.encode() in json_bytes
