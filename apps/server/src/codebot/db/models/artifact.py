"""CodeArtifact ORM model — tracks files created/modified by agents."""

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from codebot.db.models.base import Base


class ArtifactOperation(enum.Enum):
    """Operation performed on a code artifact."""

    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"


class CodeArtifact(Base):
    """A versioned record of a file touched by a coding agent.

    Attributes:
        id: Primary key UUID.
        project_id: FK to the owning Project.
        agent_id: FK to the Agent that produced this artifact.
        file_path: Relative path to the file within the repository.
        file_type: MIME type or extension category (e.g. ``python``, ``typescript``).
        language: Programming language (e.g. ``Python``, ``TypeScript``).
        content_hash: SHA-256 of the file content for deduplication.
        line_count: Number of lines in the file.
        operation: CREATE / MODIFY / DELETE.
        git_commit_sha: Git commit SHA where this change was recorded.
        git_branch: Branch name where the change was committed.
        created_at: Timestamp of artifact creation.
    """

    __tablename__ = "code_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    file_path: Mapped[str] = mapped_column(sa.String(1024), nullable=False)
    file_type: Mapped[str] = mapped_column(sa.String(128), nullable=False, default="")
    language: Mapped[str] = mapped_column(sa.String(128), nullable=False, default="")
    content_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False, default="")
    line_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    operation: Mapped[ArtifactOperation] = mapped_column(
        sa.Enum(
            ArtifactOperation, name="artifactoperation", create_constraint=True
        ),
        nullable=False,
        default=ArtifactOperation.CREATE,
    )
    git_commit_sha: Mapped[str] = mapped_column(
        sa.String(64), nullable=False, default=""
    )
    git_branch: Mapped[str] = mapped_column(sa.String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )

    # Relationships
    agent: Mapped["Agent | None"] = relationship("Agent")  # type: ignore[name-defined]


from codebot.db.models.agent import Agent  # noqa: E402, F401
