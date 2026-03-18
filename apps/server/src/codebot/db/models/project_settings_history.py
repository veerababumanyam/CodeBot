"""ProjectSettingsHistory ORM model — audit trail for settings changes."""

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from codebot.db.models.base import Base


class ProjectSettingsHistory(Base):
    """Versioned audit trail for project settings changes.

    Each row captures a full snapshot of the settings at a point in time,
    along with metadata about who/what triggered the change.

    Attributes:
        id: Primary key UUID.
        project_id: FK to the owning Project (cascading delete).
        version: Monotonically increasing version number per project.
        settings_snapshot: Full JSON snapshot of ProjectSettings at this version.
        changed_by: UUID of the user or agent that made the change (nullable).
        change_source: Origin of the change (e.g. "api", "agent:BRAINSTORM_FACILITATOR").
        change_summary: Human-readable description of what changed.
        created_at: Timestamp when this version was created.
    """

    __tablename__ = "project_settings_history"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    settings_snapshot: Mapped[dict] = mapped_column(sa.JSON, nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(sa.Uuid, nullable=True)
    change_source: Mapped[str] = mapped_column(
        sa.String(50), nullable=False, default="api"
    )
    change_summary: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
