"""ReviewComment ORM model — code review feedback from review agents."""

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from codebot.db.models.base import Base
from codebot.db.models.security import Severity


class CommentType(enum.Enum):
    """Category of a review comment."""

    BUG = "BUG"
    STYLE = "STYLE"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    ARCHITECTURE = "ARCHITECTURE"
    SUGGESTION = "SUGGESTION"


class CommentStatus(enum.Enum):
    """Resolution status of a review comment."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class ReviewComment(Base):
    """Code review feedback produced by a review agent.

    Attributes:
        id: Primary key UUID.
        project_id: FK to the owning Project.
        agent_id: FK to the reviewing Agent.
        file_path: Path to the reviewed file.
        line_number: Line number of the comment.
        comment_type: Category of the feedback.
        severity: Severity level (reuses Severity from security).
        content: Full comment text.
        suggestion: Optional suggested replacement code.
        status: Current resolution status.
        resolved_by_agent_id: Optional FK to the Agent that resolved it.
        created_at: When the comment was created.
        resolved_at: When the comment was resolved.
    """

    __tablename__ = "review_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    file_path: Mapped[str] = mapped_column(sa.String(1024), nullable=False, default="")
    line_number: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    comment_type: Mapped[CommentType] = mapped_column(
        sa.Enum(CommentType, name="commenttype", create_constraint=True),
        nullable=False,
    )
    severity: Mapped[Severity] = mapped_column(
        sa.Enum(Severity, name="severity", create_constraint=True),
        nullable=False,
        default=Severity.INFO,
    )
    content: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    suggestion: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    status: Mapped[CommentStatus] = mapped_column(
        sa.Enum(CommentStatus, name="commentstatus", create_constraint=True),
        nullable=False,
        default=CommentStatus.OPEN,
    )
    resolved_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
