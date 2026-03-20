"""Agent-level event emitter wrapping EventBus for structured NATS emission.

Provides a :class:`VerticalSliceEventEmitter` that emits typed
:class:`~agent_sdk.models.events.AgentEvent` and
:class:`~agent_sdk.models.events.PipelineEvent` payloads through the
:func:`~codebot.events.bus.publish_event` helper.

This complements the Phase 6 :class:`~codebot.pipeline.events.PipelineEventEmitter`
(Temporal workflow-level events) by providing agent-level event emission
for the vertical slice pipeline execution.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from agent_sdk.models.enums import AgentStatus, AgentType, EventType
from agent_sdk.models.events import (
    AgentEvent,
    EventEnvelope,
    PipelineEvent,
)

from codebot.events.bus import EventBus, publish_event

logger = logging.getLogger(__name__)


class PipelineEventEmitter:
    """Wraps EventBus to emit structured pipeline and agent events.

    Emits typed :class:`AgentEvent` and :class:`PipelineEvent` payloads
    wrapped in :class:`EventEnvelope` via :func:`publish_event`. Each
    method corresponds to a specific :class:`EventType`.

    Usage::

        emitter = PipelineEventEmitter(bus=event_bus, pipeline_id=uuid)
        await emitter.agent_started(agent_type=AgentType.ORCHESTRATOR, agent_id=uuid)
        await emitter.agent_completed(agent_type=AgentType.ORCHESTRATOR, agent_id=uuid)
        await emitter.phase_started(phase_name="input_processing")
        await emitter.phase_completed(phase_name="input_processing")
        await emitter.pipeline_started()
        await emitter.pipeline_completed()

    Args:
        bus: A connected :class:`EventBus` instance.
        pipeline_id: Unique identifier for the pipeline run.
    """

    def __init__(self, bus: EventBus, pipeline_id: uuid.UUID) -> None:
        self._bus = bus
        self._pipeline_id = pipeline_id

    async def agent_started(self, agent_type: AgentType, agent_id: uuid.UUID) -> None:
        """Emit AGENT_STARTED event.

        Args:
            agent_type: The type/role of the agent.
            agent_id: Unique identifier of the agent instance.
        """
        event = AgentEvent(
            agent_id=agent_id,
            agent_type=agent_type,
            status=AgentStatus.RUNNING,
            timestamp=datetime.now(tz=UTC),
        )
        envelope = EventEnvelope(
            event_type=EventType.AGENT_STARTED,
            source_agent_id=agent_id,
            payload=event.model_dump_json().encode(),
            timestamp=datetime.now(tz=UTC),
        )
        await publish_event(self._bus, envelope)

    async def agent_completed(self, agent_type: AgentType, agent_id: uuid.UUID) -> None:
        """Emit AGENT_COMPLETED event.

        Args:
            agent_type: The type/role of the agent.
            agent_id: Unique identifier of the agent instance.
        """
        event = AgentEvent(
            agent_id=agent_id,
            agent_type=agent_type,
            status=AgentStatus.COMPLETED,
            timestamp=datetime.now(tz=UTC),
        )
        envelope = EventEnvelope(
            event_type=EventType.AGENT_COMPLETED,
            source_agent_id=agent_id,
            payload=event.model_dump_json().encode(),
            timestamp=datetime.now(tz=UTC),
        )
        await publish_event(self._bus, envelope)

    async def agent_failed(
        self, agent_type: AgentType, agent_id: uuid.UUID, error: str = ""
    ) -> None:
        """Emit AGENT_FAILED event.

        Args:
            agent_type: The type/role of the agent.
            agent_id: Unique identifier of the agent instance.
            error: Error description, included in the payload.
        """
        event = AgentEvent(
            agent_id=agent_id,
            agent_type=agent_type,
            status=AgentStatus.FAILED,
            timestamp=datetime.now(tz=UTC),
            payload={"error": error} if error else None,
        )
        envelope = EventEnvelope(
            event_type=EventType.AGENT_FAILED,
            source_agent_id=agent_id,
            payload=event.model_dump_json().encode(),
            timestamp=datetime.now(tz=UTC),
        )
        await publish_event(self._bus, envelope)

    async def phase_started(self, phase_name: str) -> None:
        """Emit PHASE_STARTED event.

        Args:
            phase_name: Name of the pipeline phase (e.g. ``"input_processing"``).
        """
        event = PipelineEvent(
            pipeline_id=self._pipeline_id,
            phase=phase_name,
            status="RUNNING",
            timestamp=datetime.now(tz=UTC),
        )
        envelope = EventEnvelope(
            event_type=EventType.PHASE_STARTED,
            payload=event.model_dump_json().encode(),
            timestamp=datetime.now(tz=UTC),
        )
        await publish_event(self._bus, envelope)

    async def phase_completed(self, phase_name: str) -> None:
        """Emit PHASE_COMPLETED event.

        Args:
            phase_name: Name of the pipeline phase.
        """
        event = PipelineEvent(
            pipeline_id=self._pipeline_id,
            phase=phase_name,
            status="COMPLETED",
            timestamp=datetime.now(tz=UTC),
        )
        envelope = EventEnvelope(
            event_type=EventType.PHASE_COMPLETED,
            payload=event.model_dump_json().encode(),
            timestamp=datetime.now(tz=UTC),
        )
        await publish_event(self._bus, envelope)

    async def pipeline_started(self) -> None:
        """Emit PIPELINE_STARTED event."""
        event = PipelineEvent(
            pipeline_id=self._pipeline_id,
            phase="pipeline",
            status="STARTED",
            timestamp=datetime.now(tz=UTC),
        )
        envelope = EventEnvelope(
            event_type=EventType.PIPELINE_STARTED,
            payload=event.model_dump_json().encode(),
            timestamp=datetime.now(tz=UTC),
        )
        await publish_event(self._bus, envelope)

    async def pipeline_completed(self) -> None:
        """Emit PIPELINE_COMPLETED event."""
        event = PipelineEvent(
            pipeline_id=self._pipeline_id,
            phase="pipeline",
            status="COMPLETED",
            timestamp=datetime.now(tz=UTC),
        )
        envelope = EventEnvelope(
            event_type=EventType.PIPELINE_COMPLETED,
            payload=event.model_dump_json().encode(),
            timestamp=datetime.now(tz=UTC),
        )
        await publish_event(self._bus, envelope)
