"""Event ORM model — tracks all system events from agents and pipelines."""

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from codebot.db.models.base import Base


class EventType(enum.Enum):
    """All event types that can be emitted across the CodeBot system."""

    AGENT_STARTED = "AGENT_STARTED"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    AGENT_FAILED = "AGENT_FAILED"
    TASK_CREATED = "TASK_CREATED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    PHASE_STARTED = "PHASE_STARTED"
    PHASE_COMPLETED = "PHASE_COMPLETED"
    PIPELINE_STARTED = "PIPELINE_STARTED"
    PIPELINE_COMPLETED = "PIPELINE_COMPLETED"
    BRAINSTORM_MESSAGE = "BRAINSTORM_MESSAGE"
    BRAINSTORM_FINALIZED = "BRAINSTORM_FINALIZED"
    DEPLOYMENT_STARTED = "DEPLOYMENT_STARTED"
    DEPLOYMENT_COMPLETED = "DEPLOYMENT_COMPLETED"
    DEPLOYMENT_FAILED = "DEPLOYMENT_FAILED"
    DEPLOYMENT_ROLLED_BACK = "DEPLOYMENT_ROLLED_BACK"
    COLLABORATION_JOINED = "COLLABORATION_JOINED"
    COLLABORATION_LEFT = "COLLABORATION_LEFT"
    COLLABORATION_CONFLICT = "COLLABORATION_CONFLICT"
    COLLABORATION_RESOLVED = "COLLABORATION_RESOLVED"
    GITHUB_PUSH = "GITHUB_PUSH"
    GITHUB_PR_CREATED = "GITHUB_PR_CREATED"
    GITHUB_PR_MERGED = "GITHUB_PR_MERGED"
    GITHUB_ISSUE_CREATED = "GITHUB_ISSUE_CREATED"
    GITHUB_ISSUE_CLOSED = "GITHUB_ISSUE_CLOSED"
    GITHUB_WEBHOOK_RECEIVED = "GITHUB_WEBHOOK_RECEIVED"
    SKILL_CREATED = "SKILL_CREATED"
    SKILL_EXECUTED = "SKILL_EXECUTED"
    HOOK_TRIGGERED = "HOOK_TRIGGERED"
    HOOK_COMPLETED = "HOOK_COMPLETED"
    TOOL_REGISTERED = "TOOL_REGISTERED"
    TOOL_INVOKED = "TOOL_INVOKED"
    PERFORMANCE_REPORT_GENERATED = "PERFORMANCE_REPORT_GENERATED"
    ACCESSIBILITY_REPORT_GENERATED = "ACCESSIBILITY_REPORT_GENERATED"


class Event(Base):
    """An immutable system event record emitted by agents and pipeline components.

    Events are published to NATS and also persisted here for audit, replay, and
    dashboard real-time streaming.

    Attributes:
        id: Primary key UUID.
        project_id: FK to the owning Project (nullable for system-level events).
        event_type: Enum identifying the event category.
        source_agent_id: Optional FK to the agent that emitted this event.
        target_agent_id: Optional FK to the agent that should receive this event.
        payload: JSON payload containing event-specific data.
        timestamp: When the event was emitted.
    """

    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    event_type: Mapped[EventType] = mapped_column(
        sa.Enum(EventType, name="eventtype", create_constraint=True),
        nullable=False,
    )
    source_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    target_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    payload: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
