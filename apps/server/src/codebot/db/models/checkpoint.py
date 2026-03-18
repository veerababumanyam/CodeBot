"""Checkpoint ORM model — saves graph execution state for resume-from-checkpoint."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codebot.db.models.base import Base


class Checkpoint(Base):
    """Snapshot of pipeline graph state enabling resume after interruption.

    Checkpoints capture the full serialised graph state at a named point in the
    pipeline execution so that a run can be resumed from that point without
    replaying earlier phases.

    Attributes:
        id: Primary key UUID.
        pipeline_id: FK to the owning Pipeline.
        phase_name: Human-readable name of the phase where the checkpoint was taken.
        state_data: Full JSON serialisation of the graph node states and edges.
        git_commit_sha: Git commit SHA of the worktree at checkpoint time.
        created_at: When the checkpoint was saved.
    """

    __tablename__ = "checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=False
    )
    phase_name: Mapped[str] = mapped_column(sa.String(255), nullable=False, default="")
    state_data: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    git_commit_sha: Mapped[str] = mapped_column(
        sa.String(64), nullable=False, default=""
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    # Relationships
    pipeline: Mapped["Pipeline"] = relationship(  # type: ignore[name-defined]
        "Pipeline", back_populates="checkpoints"
    )


from codebot.db.models.project import Pipeline  # noqa: E402, F401
