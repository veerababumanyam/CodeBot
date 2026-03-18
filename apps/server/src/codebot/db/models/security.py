"""SecurityFinding ORM model — tracks security scan results."""

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from codebot.db.models.base import Base


class FindingType(enum.Enum):
    """Category of a security finding."""

    VULNERABILITY = "VULNERABILITY"
    SECRET = "SECRET"
    LICENSE_VIOLATION = "LICENSE_VIOLATION"
    CODE_SMELL = "CODE_SMELL"
    DEPENDENCY_RISK = "DEPENDENCY_RISK"
    CONFIG_ISSUE = "CONFIG_ISSUE"
    COMPLIANCE_VIOLATION = "COMPLIANCE_VIOLATION"


class Severity(enum.Enum):
    """Severity level shared by SecurityFinding and ReviewComment."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FindingStatus(enum.Enum):
    """Remediation status of a security finding."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    FIXED = "FIXED"
    ACCEPTED_RISK = "ACCEPTED_RISK"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class SecurityFinding(Base):
    """A security issue discovered by an automated scanner.

    Attributes:
        id: Primary key UUID.
        project_id: FK to the owning Project.
        scanner: Name of the scanner (e.g. ``semgrep``, ``trivy``, ``gitleaks``).
        finding_type: Category of the finding.
        severity: Severity level.
        title: Short finding title.
        description: Full description of the issue.
        file_path: Path to the affected file.
        line_number: Line number of the issue.
        code_snippet: Relevant code excerpt.
        cwe_id: CWE identifier (e.g. ``CWE-89``).
        cve_id: CVE identifier if applicable.
        recommendation: Suggested fix.
        status: Current remediation status.
        fixed_by_agent_id: Optional FK to the Agent that fixed the issue.
        fixed_at: When the fix was applied.
        created_at: When the finding was recorded.
    """

    __tablename__ = "security_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    scanner: Mapped[str] = mapped_column(sa.String(128), nullable=False, default="")
    finding_type: Mapped[FindingType] = mapped_column(
        sa.Enum(FindingType, name="findingtype", create_constraint=True),
        nullable=False,
    )
    severity: Mapped[Severity] = mapped_column(
        sa.Enum(Severity, name="severity", create_constraint=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    file_path: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    line_number: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    code_snippet: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    cwe_id: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    cve_id: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    recommendation: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    status: Mapped[FindingStatus] = mapped_column(
        sa.Enum(FindingStatus, name="findingstatus", create_constraint=True),
        nullable=False,
        default=FindingStatus.OPEN,
    )
    fixed_by_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    fixed_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
