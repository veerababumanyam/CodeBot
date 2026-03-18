"""ExperimentLog ORM model — tracks autoresearch-style experiment loop results."""

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from codebot.db.models.base import Base


class ExperimentStatus(enum.Enum):
    """Outcome of an individual experiment iteration."""

    KEEP = "KEEP"
    DISCARD = "DISCARD"
    CRASH = "CRASH"
    TIMEOUT = "TIMEOUT"
    REGRESSION = "REGRESSION"


class ExperimentLog(Base):
    """Record of a single iteration in an ExperimentLoop.

    Inspired by the autoresearch ``results.tsv`` pattern — each row captures a
    hypothesis, its measured primary metric before/after, all secondary metric
    regression checks, and the keep/discard decision with reasoning.

    Used by the Debug, Performance, Security, and Improve pipeline stages.

    Attributes:
        id: Primary key UUID.
        project_id: FK to the owning Project.
        pipeline_id: FK to the Pipeline running the experiment loop.
        stage: Pipeline stage label (e.g. ``S8_DEBUG``, ``S6_PERF``, ``IMPROVE``).
        experiment_number: Sequential index within the current loop session.
        hypothesis: Natural language description of the proposed change.
        git_branch: Experiment branch name (e.g. ``experiment/7``).
        git_commit_sha: Commit hash of the applied change.
        metric_name: Primary metric being optimised (e.g. ``test_pass_rate``).
        metric_before: Baseline measurement before the change.
        metric_after: Post-experiment measurement.
        metric_delta: ``metric_after - metric_before``.
        regression_checks: JSON dict keyed by metric name, each with
            ``{before, after, passed}`` for secondary regression metrics.
        status: Whether the experiment was KEEP, DISCARD, CRASH, etc.
        decision_reason: Text explaining why the experiment was kept or discarded.
        diff_lines_added: Lines of code added by this experiment.
        diff_lines_removed: Lines of code removed by this experiment.
        complexity_delta: Change in cyclomatic complexity (nullable).
        duration_seconds: Wall-clock seconds for this experiment.
        token_cost: LLM tokens consumed by this experiment.
        created_at: When the experiment record was persisted.
    """

    __tablename__ = "experiment_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False
    )
    stage: Mapped[str] = mapped_column(sa.String(128), nullable=False, default="")
    experiment_number: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=1
    )
    hypothesis: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    git_branch: Mapped[str] = mapped_column(sa.String(255), nullable=False, default="")
    git_commit_sha: Mapped[str] = mapped_column(
        sa.String(64), nullable=False, default=""
    )
    metric_name: Mapped[str] = mapped_column(
        sa.String(255), nullable=False, default=""
    )
    metric_before: Mapped[float] = mapped_column(
        sa.Numeric(precision=12, scale=4), nullable=False, default=0
    )
    metric_after: Mapped[float] = mapped_column(
        sa.Numeric(precision=12, scale=4), nullable=False, default=0
    )
    metric_delta: Mapped[float] = mapped_column(
        sa.Numeric(precision=12, scale=4), nullable=False, default=0
    )
    regression_checks: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    status: Mapped[ExperimentStatus] = mapped_column(
        sa.Enum(ExperimentStatus, name="experimentstatus", create_constraint=True),
        nullable=False,
    )
    decision_reason: Mapped[str] = mapped_column(
        sa.Text, nullable=False, default=""
    )
    diff_lines_added: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0
    )
    diff_lines_removed: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0
    )
    complexity_delta: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, default=0
    )
    token_cost: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
