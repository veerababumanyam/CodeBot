"""Agent and AgentExecution ORM models."""

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codebot.db.models.base import Base


class AgentType(enum.Enum):
    """Enumeration of all specialized agent types in the CodeBot system."""

    ORCHESTRATOR = "ORCHESTRATOR"
    PLANNER = "PLANNER"
    RESEARCHER = "RESEARCHER"
    ARCHITECT = "ARCHITECT"
    DESIGNER = "DESIGNER"
    FRONTEND_DEV = "FRONTEND_DEV"
    BACKEND_DEV = "BACKEND_DEV"
    MIDDLEWARE_DEV = "MIDDLEWARE_DEV"
    INFRA_ENGINEER = "INFRA_ENGINEER"
    SECURITY_AUDITOR = "SECURITY_AUDITOR"
    CODE_REVIEWER = "CODE_REVIEWER"
    TESTER = "TESTER"
    DEBUGGER = "DEBUGGER"
    DOC_WRITER = "DOC_WRITER"
    BRAINSTORM_FACILITATOR = "BRAINSTORM_FACILITATOR"
    TECH_STACK_ADVISOR = "TECH_STACK_ADVISOR"
    TEMPLATE_CURATOR = "TEMPLATE_CURATOR"
    DEPLOYER = "DEPLOYER"
    COLLABORATION_MANAGER = "COLLABORATION_MANAGER"
    MOBILE_DEV = "MOBILE_DEV"
    PERFORMANCE_TESTER = "PERFORMANCE_TESTER"
    ACCESSIBILITY_AUDITOR = "ACCESSIBILITY_AUDITOR"
    GITHUB_INTEGRATOR = "GITHUB_INTEGRATOR"
    SKILL_MANAGER = "SKILL_MANAGER"
    HOOK_MANAGER = "HOOK_MANAGER"
    TOOL_BUILDER = "TOOL_BUILDER"
    INTEGRATION_ADAPTER = "INTEGRATION_ADAPTER"
    I18N_SPECIALIST = "I18N_SPECIALIST"
    API_DESIGNER = "API_DESIGNER"
    PROJECT_MANAGER = "PROJECT_MANAGER"


class AgentStatus(enum.Enum):
    """Runtime status of an agent instance."""

    IDLE = "IDLE"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"


class ExecutionStatus(enum.Enum):
    """Final status of a single AgentExecution (one LLM call sequence)."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"
    RATE_LIMITED = "RATE_LIMITED"
    CANCELLED = "CANCELLED"


class Agent(Base):
    """An agent instance active within a pipeline run.

    Attributes:
        id: Primary key UUID.
        project_id: FK to the owning Project.
        agent_type: Specialized role of this agent.
        status: Current runtime status.
        llm_provider: Name of the LLM provider (e.g. ``anthropic``).
        llm_model: Model identifier (e.g. ``claude-opus-4-5``).
        worktree_path: Path to the agent's isolated git worktree.
        cli_agent_type: Optional CLI agent delegation type.
        system_prompt_hash: SHA-256 of the system prompt for traceability.
        tokens_used: Total tokens consumed by this agent.
        cost_usd: Total cost in USD.
        started_at: When the agent was initialized.
        completed_at: When the agent finished (success or failure).
        error_count: Number of errors encountered.
    """

    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    agent_type: Mapped[AgentType] = mapped_column(
        sa.Enum(AgentType, name="agenttype", create_constraint=True),
        nullable=False,
    )
    status: Mapped[AgentStatus] = mapped_column(
        sa.Enum(AgentStatus, name="agentstatus", create_constraint=True),
        nullable=False,
        default=AgentStatus.IDLE,
    )
    llm_provider: Mapped[str] = mapped_column(sa.String(128), nullable=False, default="")
    llm_model: Mapped[str] = mapped_column(sa.String(128), nullable=False, default="")
    worktree_path: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    cli_agent_type: Mapped[str | None] = mapped_column(sa.String(128), nullable=True)
    system_prompt_hash: Mapped[str] = mapped_column(
        sa.String(64), nullable=False, default=""
    )
    tokens_used: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(
        sa.Numeric(precision=10, scale=6), nullable=False, default=0
    )
    started_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    error_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

    # Relationships
    executions: Mapped[list["AgentExecution"]] = relationship(
        "AgentExecution", back_populates="agent", cascade="all, delete-orphan"
    )


class AgentExecution(Base):
    """A single LLM call sequence (one turn) by an agent.

    Attributes:
        id: Primary key UUID.
        agent_id: FK to the parent Agent.
        task_id: FK to the Task being worked on.
        llm_provider: LLM provider used for this execution.
        llm_model: Specific model used.
        input_tokens: Tokens in the prompt.
        output_tokens: Tokens in the completion.
        total_tokens: Sum of input + output tokens.
        cost_usd: Cost for this execution.
        duration_ms: Wall-clock duration in milliseconds.
        status: Final status of the execution.
        input_messages: JSON list of input messages.
        output_messages: JSON list of output messages.
        tool_calls: JSON list of tool call records.
        error_message: Error detail if execution failed.
        created_at: Timestamp of the execution.
    """

    __tablename__ = "agent_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    llm_provider: Mapped[str] = mapped_column(sa.String(128), nullable=False, default="")
    llm_model: Mapped[str] = mapped_column(sa.String(128), nullable=False, default="")
    input_tokens: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(
        sa.Numeric(precision=10, scale=6), nullable=False, default=0
    )
    duration_ms: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    status: Mapped[ExecutionStatus] = mapped_column(
        sa.Enum(ExecutionStatus, name="executionstatus", create_constraint=True),
        nullable=False,
    )
    input_messages: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    output_messages: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    tool_calls: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="executions")
