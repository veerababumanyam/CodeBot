"""Project, Pipeline, and PipelinePhase ORM models."""

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codebot.db.models.base import Base


class ProjectStatus(enum.Enum):
    """Lifecycle status of a CodeBot project."""

    CREATED = "CREATED"
    PLANNING = "PLANNING"
    BRAINSTORMING = "BRAINSTORMING"
    RESEARCHING = "RESEARCHING"
    ARCHITECTING = "ARCHITECTING"
    DESIGNING = "DESIGNING"
    IMPLEMENTING = "IMPLEMENTING"
    REVIEWING = "REVIEWING"
    TESTING = "TESTING"
    DEBUGGING = "DEBUGGING"
    DOCUMENTING = "DOCUMENTING"
    DEPLOYING = "DEPLOYING"
    DELIVERING = "DELIVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class ProjectType(enum.Enum):
    """Classification of a CodeBot project."""

    GREENFIELD = "GREENFIELD"
    INFLIGHT = "INFLIGHT"
    BROWNFIELD = "BROWNFIELD"
    IMPROVE = "IMPROVE"


class PipelineStatus(enum.Enum):
    """Execution status of a Pipeline run."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PhaseType(enum.Enum):
    """Type of pipeline phase corresponding to an SDLC stage."""

    BRAINSTORMING = "BRAINSTORMING"
    TECH_STACK_SELECTION = "TECH_STACK_SELECTION"
    TEMPLATE_SELECTION = "TEMPLATE_SELECTION"
    PLANNING = "PLANNING"
    RESEARCH = "RESEARCH"
    ARCHITECTURE = "ARCHITECTURE"
    DESIGN = "DESIGN"
    IMPLEMENTATION = "IMPLEMENTATION"
    REVIEW = "REVIEW"
    TESTING = "TESTING"
    DEBUG_FIX = "DEBUG_FIX"
    DOCUMENTATION = "DOCUMENTATION"
    DEPLOYMENT = "DEPLOYMENT"
    DELIVERY = "DELIVERY"


class PhaseStatus(enum.Enum):
    """Status of an individual pipeline phase."""

    PENDING = "PENDING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class Project(Base):
    """Top-level entity representing a software project being built by CodeBot.

    Attributes:
        id: Primary key UUID.
        user_id: FK to the owning User.
        name: Human-readable project name.
        description: Short description.
        status: Current lifecycle status.
        project_type: Classification of the project.
        prd_content: Full PRD text provided by the user.
        prd_format: Encoding of prd_content (markdown / json / yaml).
        tech_stack: JSON blob describing the chosen tech stack.
        tech_stack_config_id: Optional FK to TechStackConfig.
        template_id: Optional FK to a Template.
        repository_path: Local path to the git worktree.
        repository_url: Optional remote git URL.
        config: Arbitrary pipeline configuration JSON.
        created_at: Row creation timestamp.
        updated_at: Last modification timestamp.
        completed_at: When the project was completed or failed.
    """

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    status: Mapped[ProjectStatus] = mapped_column(
        sa.Enum(ProjectStatus, name="projectstatus", create_constraint=True),
        nullable=False,
        default=ProjectStatus.CREATED,
    )
    project_type: Mapped[ProjectType] = mapped_column(
        sa.Enum(ProjectType, name="projecttype", create_constraint=True),
        nullable=False,
        default=ProjectType.GREENFIELD,
    )
    prd_content: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    prd_format: Mapped[str] = mapped_column(
        sa.Enum("markdown", "json", "yaml", name="prdformat", create_constraint=True),
        nullable=False,
        default="markdown",
    )
    tech_stack: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    tech_stack_config_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, nullable=True
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(sa.Uuid, nullable=True)
    repository_path: Mapped[str] = mapped_column(sa.String(1024), nullable=False, default="")
    repository_url: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    config: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )

    # Relationships
    pipelines: Mapped[list["Pipeline"]] = relationship(
        "Pipeline", back_populates="project", cascade="all, delete-orphan"
    )


class Pipeline(Base):
    """A single execution run of the CodeBot SDLC pipeline for a project.

    Attributes:
        id: Primary key UUID.
        project_id: FK to the owning Project.
        status: Current execution status.
        current_phase: Name of the phase currently executing.
        graph_definition: JSON serialization of the agent graph.
        checkpoint_data: Saved graph state for resume-from-checkpoint.
        started_at: When the pipeline started executing.
        completed_at: When the pipeline finished (success or failure).
        total_tokens_used: Cumulative LLM tokens across all agents.
        total_cost_usd: Cumulative LLM cost in USD.
        error_message: Error detail if the pipeline failed.
    """

    __tablename__ = "pipelines"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[PipelineStatus] = mapped_column(
        sa.Enum(PipelineStatus, name="pipelinestatus", create_constraint=True),
        nullable=False,
        default=PipelineStatus.PENDING,
    )
    current_phase: Mapped[str] = mapped_column(
        sa.String(255), nullable=False, default=""
    )
    graph_definition: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    checkpoint_data: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    total_tokens_used: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    total_cost_usd: Mapped[float] = mapped_column(
        sa.Numeric(precision=10, scale=6), default=0, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="pipelines")
    phases: Mapped[list["PipelinePhase"]] = relationship(
        "PipelinePhase", back_populates="pipeline", cascade="all, delete-orphan"
    )
    checkpoints: Mapped[list["Checkpoint"]] = relationship(  # type: ignore[name-defined]
        "Checkpoint", back_populates="pipeline", cascade="all, delete-orphan"
    )


class PipelinePhase(Base):
    """An individual phase within a Pipeline execution.

    Attributes:
        id: Primary key UUID.
        pipeline_id: FK to the parent Pipeline.
        name: Human-readable phase name.
        phase_type: Enum identifying the SDLC stage.
        status: Current execution status of this phase.
        order: Numeric ordering within the pipeline (0-based).
        requires_approval: Whether a human must approve before proceeding.
        approved_by: Name/email of the approver.
        started_at: Phase start timestamp.
        completed_at: Phase completion timestamp.
        input_data: JSON input passed into this phase.
        output_data: JSON output produced by this phase.
        error_message: Error detail if the phase failed.
    """

    __tablename__ = "pipeline_phases"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    phase_type: Mapped[PhaseType] = mapped_column(
        sa.Enum(PhaseType, name="phasetype", create_constraint=True),
        nullable=False,
    )
    status: Mapped[PhaseStatus] = mapped_column(
        sa.Enum(PhaseStatus, name="phasestatus", create_constraint=True),
        nullable=False,
        default=PhaseStatus.PENDING,
    )
    order: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    requires_approval: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False
    )
    approved_by: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    input_data: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # Relationships
    pipeline: Mapped["Pipeline"] = relationship("Pipeline", back_populates="phases")
    tasks: Mapped[list["Task"]] = relationship(  # type: ignore[name-defined]
        "Task", back_populates="phase", cascade="all, delete-orphan"
    )


# Avoid circular import — Checkpoint is defined in checkpoint.py and added there.
from codebot.db.models.checkpoint import Checkpoint  # noqa: E402, F401
from codebot.db.models.task import Task  # noqa: E402, F401
