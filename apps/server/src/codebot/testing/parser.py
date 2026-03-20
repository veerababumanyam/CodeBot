"""TestResultParser -- parses pytest-json-report and coverage.json output.

Provides structured ``ParsedTestResult`` for use by TesterAgent and
DebuggerAgent. Extracts pass/fail counts, coverage percentage, and
failure detail records from the raw JSON report dicts.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, kw_only=True)
class ParsedTestResult:
    """Structured test execution result.

    Attributes:
        total: Total number of tests discovered.
        passed: Number of tests that passed.
        failed: Number of tests that failed.
        errors: Number of tests that produced errors.
        skipped: Number of tests skipped.
        coverage_percent: Line coverage percentage from coverage.py.
        all_passed: True when failed == 0 and errors == 0.
        failure_details: List of dicts with nodeid, outcome, message, longrepr.
        duration_seconds: Total test suite execution time in seconds.
    """

    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    coverage_percent: float
    all_passed: bool
    failure_details: list[dict[str, str | float]] = field(default_factory=list)
    duration_seconds: float = 0.0


class TestResultParser:
    """Parses pytest-json-report and coverage.json into ParsedTestResult."""

    @staticmethod
    def parse(
        test_report: dict,  # noqa: ANN401
        coverage_data: dict,  # noqa: ANN401
    ) -> ParsedTestResult:
        """Parse pytest-json-report and coverage.json into ParsedTestResult.

        Args:
            test_report: Parsed JSON from pytest-json-report output.
            coverage_data: Parsed JSON from coverage.json output.

        Returns:
            ParsedTestResult with extracted counts, coverage, and failure details.
        """
        summary = test_report.get("summary", {})
        total = int(summary.get("total", 0))
        passed = int(summary.get("passed", 0))
        failed = int(summary.get("failed", 0))
        errors = int(summary.get("error", 0))
        skipped = int(summary.get("skipped", 0))

        # Extract coverage percentage
        totals = coverage_data.get("totals", {})
        coverage_percent = float(totals.get("percent_covered", 0.0))

        # Extract failure details from tests list
        failure_details: list[dict[str, str | float]] = []
        for test in test_report.get("tests", []):
            if test.get("outcome") not in ("passed", "skipped"):
                failure_details.append(
                    {
                        "nodeid": test.get("nodeid", ""),
                        "outcome": test.get("outcome", ""),
                        "longrepr": test.get("longrepr", ""),
                        "duration": test.get("duration", 0.0),
                    }
                )

        all_passed = failed == 0 and errors == 0

        duration_seconds = float(test_report.get("duration", 0.0))

        return ParsedTestResult(
            total=total,
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            coverage_percent=coverage_percent,
            all_passed=all_passed,
            failure_details=failure_details,
            duration_seconds=duration_seconds,
        )
