"""Tests for pipeline event emission via NATS JetStream.

Validates PipelineEvent dataclass structure, PipelineEventEmitter behaviour
including stream creation, event publishing, subject formatting, and typed
helper methods.  All NATS interaction is mocked -- no live server required.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codebot.pipeline.events import PipelineEvent, PipelineEventEmitter


# ---------------------------------------------------------------------------
# Test 1: PipelineEvent dataclass fields
# ---------------------------------------------------------------------------


class TestPipelineEvent:
    """PipelineEvent has correct fields and serialisation."""

    def test_has_required_fields(self) -> None:
        """PipelineEvent has type (str), timestamp (str), and data (dict)."""
        event = PipelineEvent(type="phase.started", data={"phase": "s0"})
        assert isinstance(event.type, str)
        assert isinstance(event.timestamp, str)
        assert isinstance(event.data, dict)

    def test_default_timestamp_is_iso8601(self) -> None:
        """Default timestamp is a valid ISO 8601 string."""
        event = PipelineEvent(type="test")
        # Should parse without error
        parsed = datetime.fromisoformat(event.timestamp)
        assert parsed.tzinfo is not None  # timezone-aware

    def test_default_data_is_empty_dict(self) -> None:
        """data defaults to an empty dict when omitted."""
        event = PipelineEvent(type="test")
        assert event.data == {}

    def test_to_json_bytes_includes_type_and_timestamp(self) -> None:
        """to_json_bytes encodes type, timestamp, and data fields."""
        event = PipelineEvent(
            type="gate.decided",
            data={"gate_id": "g1", "decision": "approved"},
            timestamp="2026-01-01T00:00:00+00:00",
        )
        payload = json.loads(event.to_json_bytes())
        assert payload["type"] == "gate.decided"
        assert payload["timestamp"] == "2026-01-01T00:00:00+00:00"
        assert payload["gate_id"] == "g1"
        assert payload["decision"] == "approved"

    def test_subject_replaces_dots_with_underscores(self) -> None:
        """Event subject follows pipeline.{event_type} with dots replaced."""
        event = PipelineEvent(type="phase.started")
        assert event.subject == "pipeline.phase_started"

        event2 = PipelineEvent(type="gate.decided")
        assert event2.subject == "pipeline.gate_decided"


# ---------------------------------------------------------------------------
# Test 2-7: PipelineEventEmitter
# ---------------------------------------------------------------------------


def _make_emitter() -> tuple[PipelineEventEmitter, AsyncMock]:
    """Create an emitter with a mocked NATS connection."""
    nc = MagicMock()
    js_mock = AsyncMock()
    nc.jetstream.return_value = js_mock
    emitter = PipelineEventEmitter(nc)
    return emitter, js_mock


class TestPipelineEventEmitter:
    """PipelineEventEmitter publishes events to NATS JetStream."""

    @pytest.mark.asyncio
    async def test_emit_publishes_to_correct_subject(self) -> None:
        """emit() publishes JSON-encoded event to pipeline.{event_type} subject."""
        emitter, js_mock = _make_emitter()

        await emitter.emit("phase.started", {"phase": "s0"})

        js_mock.publish.assert_awaited_once()
        call_args = js_mock.publish.call_args
        subject = call_args[0][0]
        assert subject == "pipeline.phase_started"

    @pytest.mark.asyncio
    async def test_emit_publishes_json_encoded_payload(self) -> None:
        """emit() publishes a JSON-encoded bytes payload."""
        emitter, js_mock = _make_emitter()

        await emitter.emit("phase.started", {"phase": "s0"})

        raw_bytes = js_mock.publish.call_args[0][1]
        payload = json.loads(raw_bytes)
        assert payload["type"] == "phase.started"
        assert payload["phase"] == "s0"

    @pytest.mark.asyncio
    async def test_emit_adds_iso8601_timestamp(self) -> None:
        """emit() adds an ISO 8601 timestamp to every event payload."""
        emitter, js_mock = _make_emitter()

        await emitter.emit("test.event")

        raw_bytes = js_mock.publish.call_args[0][1]
        payload = json.loads(raw_bytes)
        assert "timestamp" in payload
        # Should parse without error
        dt = datetime.fromisoformat(payload["timestamp"])
        assert dt.tzinfo is not None

    @pytest.mark.asyncio
    async def test_ensure_stream_creates_pipeline_events_stream(self) -> None:
        """ensure_stream() creates JetStream stream named PIPELINE_EVENTS."""
        emitter, js_mock = _make_emitter()

        await emitter.ensure_stream()

        js_mock.add_stream.assert_awaited_once()
        config = js_mock.add_stream.call_args[0][0]
        assert config.name == "PIPELINE_EVENTS"

    @pytest.mark.asyncio
    async def test_ensure_stream_configures_subjects_and_retention(self) -> None:
        """ensure_stream() configures subjects=['pipeline.>'] and 7-day retention."""
        emitter, js_mock = _make_emitter()

        await emitter.ensure_stream()

        config = js_mock.add_stream.call_args[0][0]
        assert config.subjects == ["pipeline.>"]
        # max_age should be 7 days; the StreamConfig stores seconds as float
        seven_days_seconds = 7 * 24 * 3600.0
        assert config.max_age == seven_days_seconds

    @pytest.mark.asyncio
    async def test_emit_phase_started_helper(self) -> None:
        """emit_phase_started() emits a phase.started event."""
        emitter, js_mock = _make_emitter()

        await emitter.emit_phase_started("s0_init", 0, "proj-1")

        raw_bytes = js_mock.publish.call_args[0][1]
        payload = json.loads(raw_bytes)
        assert payload["type"] == "phase.started"
        assert payload["phase"] == "s0_init"
        assert payload["phase_idx"] == 0
        assert payload["project_id"] == "proj-1"

    @pytest.mark.asyncio
    async def test_emit_phase_completed_helper(self) -> None:
        """emit_phase_completed() emits a phase.completed event."""
        emitter, js_mock = _make_emitter()

        await emitter.emit_phase_completed("s0_init", 0, "proj-1")

        raw_bytes = js_mock.publish.call_args[0][1]
        payload = json.loads(raw_bytes)
        assert payload["type"] == "phase.completed"
        assert payload["phase"] == "s0_init"

    @pytest.mark.asyncio
    async def test_emit_gate_waiting_helper(self) -> None:
        """emit_gate_waiting() emits a gate.waiting event."""
        emitter, js_mock = _make_emitter()

        await emitter.emit_gate_waiting("gate_design")

        raw_bytes = js_mock.publish.call_args[0][1]
        payload = json.loads(raw_bytes)
        assert payload["type"] == "gate.waiting"
        assert payload["gate_id"] == "gate_design"

    @pytest.mark.asyncio
    async def test_emit_gate_decided_helper(self) -> None:
        """emit_gate_decided() emits a gate.decided event."""
        emitter, js_mock = _make_emitter()

        await emitter.emit_gate_decided("gate_design", "approved")

        raw_bytes = js_mock.publish.call_args[0][1]
        payload = json.loads(raw_bytes)
        assert payload["type"] == "gate.decided"
        assert payload["gate_id"] == "gate_design"
        assert payload["decision"] == "approved"

    def test_stream_name_constant(self) -> None:
        """STREAM_NAME class attribute is 'PIPELINE_EVENTS'."""
        assert PipelineEventEmitter.STREAM_NAME == "PIPELINE_EVENTS"
