"""NATS JetStream event emission for pipeline observability.

Every stage transition, gate decision, and pipeline lifecycle event is
published to a JetStream stream (``PIPELINE_EVENTS``) with 7-day retention.
Events are consumed by the dashboard, CLI, and audit trail.

Public API:
    - :class:`PipelineEvent` -- immutable event dataclass
    - :class:`PipelineEventEmitter` -- JetStream publisher with typed helpers
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

from nats.aio.client import Client as NATSClient
from nats.js.api import RetentionPolicy, StreamConfig


@dataclass(slots=True, kw_only=True)
class PipelineEvent:
    """A single pipeline event destined for NATS JetStream.

    Attributes:
        type: Dot-delimited event type (e.g. ``"phase.started"``).
        data: Arbitrary event payload.
        timestamp: ISO 8601 UTC timestamp (auto-populated).
    """

    type: str
    data: dict[str, object] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_json_bytes(self) -> bytes:
        """Serialise the event as JSON bytes for JetStream publish.

        The ``data`` dict is spread into the top-level payload so
        consumers get a flat structure::

            {"type": "...", "timestamp": "...", ...data_fields}
        """
        payload: dict[str, object] = {
            "type": self.type,
            "timestamp": self.timestamp,
            **self.data,
        }
        return json.dumps(payload).encode()

    @property
    def subject(self) -> str:
        """NATS subject for this event.

        Follows ``pipeline.{event_type}`` with dots in the event type
        replaced by underscores so the subject remains a single NATS
        token after the ``pipeline.`` prefix.
        """
        return f"pipeline.{self.type.replace('.', '_')}"


class PipelineEventEmitter:
    """Publishes pipeline events to NATS JetStream.

    Events are published to subjects matching ``pipeline.{event_type}``.
    A JetStream stream named ``PIPELINE_EVENTS`` captures all
    ``pipeline.*`` subjects with 7-day retention.

    Args:
        nc: An open :class:`nats.aio.client.Client` connection.
    """

    STREAM_NAME: str = "PIPELINE_EVENTS"

    def __init__(self, nc: NATSClient) -> None:
        self._nc = nc
        self._js = nc.jetstream()

    async def ensure_stream(self) -> None:
        """Create or update the JetStream stream for pipeline events.

        Configures:
        - subjects: ``["pipeline.>"]`` (wildcard captures all pipeline events)
        - retention: limits-based
        - max_age: 7 days
        """
        await self._js.add_stream(
            StreamConfig(
                name=self.STREAM_NAME,
                subjects=["pipeline.>"],
                retention=RetentionPolicy.LIMITS,
                max_age=7 * 24 * 3600.0,  # 7 days in seconds
            )
        )

    async def emit(self, event_type: str, data: dict[str, object] | None = None) -> None:
        """Emit a pipeline event to JetStream.

        Args:
            event_type: Dot-delimited event type (e.g. ``"phase.started"``).
            data: Optional event payload dictionary.
        """
        event = PipelineEvent(type=event_type, data=data or {})
        await self._js.publish(event.subject, event.to_json_bytes())

    # ------------------------------------------------------------------
    # Typed helper methods
    # ------------------------------------------------------------------

    async def emit_phase_started(
        self,
        phase_name: str,
        phase_idx: int,
        project_id: str = "",
    ) -> None:
        """Emit a ``phase.started`` event."""
        await self.emit(
            "phase.started",
            {
                "phase": phase_name,
                "phase_idx": phase_idx,
                "project_id": project_id,
            },
        )

    async def emit_phase_completed(
        self,
        phase_name: str,
        phase_idx: int,
        project_id: str = "",
    ) -> None:
        """Emit a ``phase.completed`` event."""
        await self.emit(
            "phase.completed",
            {
                "phase": phase_name,
                "phase_idx": phase_idx,
                "project_id": project_id,
            },
        )

    async def emit_gate_waiting(self, gate_id: str) -> None:
        """Emit a ``gate.waiting`` event."""
        await self.emit("gate.waiting", {"gate_id": gate_id})

    async def emit_gate_decided(self, gate_id: str, decision: str) -> None:
        """Emit a ``gate.decided`` event."""
        await self.emit(
            "gate.decided",
            {
                "gate_id": gate_id,
                "decision": decision,
            },
        )
