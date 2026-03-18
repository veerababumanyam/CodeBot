"""Task ORM model."""

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codebot.db.models.base import Base


class TaskStatus(enum.Enum):
    """Lifecycle status of a Task."""

    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Task(Base):
    """A unit of work assigned to an agent within a pipeline phase.

    Attributes:
        id: Primary key UUID.
        project_id: FK to the owning Project.
        phase_id: FK to the containing PipelinePhase.
        parent_task_id: Optional self-referential FK for sub-tasks.
        title: Short task title.
        description: Full task description.
        status: Current execution status.
        priority: Numeric priority (lower = higher priority).
        assigned_agent_type: AgentType string of the responsible agent.
        dependencies: JSON list of Task UUIDs that must complete first.
        input_context: JSON context provided as input to the task.
        output_artifacts: JSON list of artifact references produced.
        created_at: Row creation timestamp.
        started_at: When the task was picked up by an agent.
        completed_at: When the task finished.
        error_message: Error detail if the task failed.
    """

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    phase_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("pipeline_phases.id", ondelete="CASCADE"), nullable=False
    )
    parent_task_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    status: Mapped[TaskStatus] = mapped_column(
        sa.Enum(TaskStatus, name="taskstatus", create_constraint=True),
        nullable=False,
        default=TaskStatus.PENDING,
    )
    priority: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    assigned_agent_type: Mapped[str] = mapped_column(
        sa.String(255), nullable=False, default=""
    )
    dependencies: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    input_context: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    output_artifacts: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Relationships
    phase: Mapped["PipelinePhase"] = relationship(  # type: ignore[name-defined]
        "PipelinePhase", back_populates="tasks"
    )
    subtasks: Mapped[list["Task"]] = relationship(
        "Task", foreign_keys=[parent_task_id], back_populates="parent_task"
    )
    parent_task: Mapped["Task | None"] = relationship(
        "Task", foreign_keys=[parent_task_id], back_populates="subtasks", remote_side=[id]
    )


from codebot.db.models.project import PipelinePhase  # noqa: E402, F401
