"""TestResult ORM model — records outcomes from automated test runs."""

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from codebot.db.models.base import Base


class TestStatus(enum.Enum):
    """Outcome of a single test case."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class TestResult(Base):
    """Result record for a single test case execution.

    Attributes:
        id: Primary key UUID.
        project_id: FK to the owning Project.
        test_suite: Name of the test suite / file.
        test_name: Name of the individual test case.
        test_file: Path to the test file.
        status: Test outcome (PASSED / FAILED / SKIPPED / ERROR).
        duration_ms: Test execution duration in milliseconds.
        error_message: Error message if status is FAILED or ERROR.
        stack_trace: Full stack trace for debugging.
        framework: Testing framework used (e.g. ``pytest``, ``vitest``).
        coverage_percent: Optional code coverage percentage.
        run_number: Sequential run counter for trend analysis.
        created_at: When the test was executed.
    """

    __tablename__ = "test_results"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    test_suite: Mapped[str] = mapped_column(sa.String(512), nullable=False, default="")
    test_name: Mapped[str] = mapped_column(sa.String(512), nullable=False, default="")
    test_file: Mapped[str] = mapped_column(sa.String(1024), nullable=False, default="")
    status: Mapped[TestStatus] = mapped_column(
        sa.Enum(TestStatus, name="teststatus", create_constraint=True),
        nullable=False,
    )
    duration_ms: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    stack_trace: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    framework: Mapped[str] = mapped_column(sa.String(128), nullable=False, default="")
    coverage_percent: Mapped[float | None] = mapped_column(
        sa.Numeric(precision=5, scale=2), nullable=True
    )
    run_number: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
