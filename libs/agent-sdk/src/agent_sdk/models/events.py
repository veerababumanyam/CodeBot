"""Pydantic v2 schemas for NATS event payloads.

All event models are designed for JSON serialization via
``model_dump_json()`` / ``model_validate_json()`` for use with the
NATS JetStream event bus.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from agent_sdk.models.enums import AgentStatus, AgentType, EventType, TaskStatus


class AgentEvent(BaseModel):
    """Payload for agent lifecycle events.

    Attributes:
        agent_id: Agent instance identifier.
        agent_type: Role of the agent.
        status: Agent's new status after the event.
        timestamp: UTC timestamp of the event.
        payload: Optional arbitrary metadata.
    """

    agent_id: uuid.UUID
    agent_type: AgentType
    status: AgentStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    payload: dict[str, Any] | None = None


class TaskEvent(BaseModel):
    """Payload for task lifecycle events.

    Attributes:
        task_id: Task identifier.
        agent_id: Agent that processed the task.
        status: Task's new status after the event.
        timestamp: UTC timestamp of the event.
    """

    task_id: uuid.UUID
    agent_id: uuid.UUID
    status: TaskStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class PipelineEvent(BaseModel):
    """Payload for pipeline/phase lifecycle events.

    Attributes:
        pipeline_id: Pipeline identifier.
        phase: Name of the current/affected phase.
        status: Pipeline's new status after the event.
        timestamp: UTC timestamp of the event.
    """

    pipeline_id: uuid.UUID
    phase: str
    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class EventEnvelope(BaseModel):
    """Top-level wrapper published on the NATS codebot-events stream.

    The ``payload`` field holds the JSON-serialized inner event model so
    consumers can route on ``event_type`` before deserializing the payload.

    Attributes:
        event_type: Routing key for this event.
        source_agent_id: Agent that emitted the event (nullable).
        payload: Raw JSON bytes of the inner event model.
        timestamp: UTC timestamp when the envelope was created.
    """

    event_type: EventType
    source_agent_id: uuid.UUID | None = None
    payload: bytes
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
