"""TestRunner -- executes pytest with JSON report and coverage in a workspace.

Wraps ``pytest`` execution via ``asyncio.create_subprocess_exec``, reading
back the structured JSON report and coverage JSON for programmatic parsing
by ``TestResultParser``.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class TestRunner:
    """Executes pytest in a workspace directory with JSON report and coverage.

    Attributes:
        timeout_seconds: Maximum time for pytest execution.
    """

    timeout_seconds: int = 120

    async def run(
        self,
        workspace: str,
        test_dir: str = "tests",
    ) -> tuple[dict, dict]:
        """Execute pytest with JSON report and coverage in workspace directory.

        Runs ``uv run pytest`` with ``--json-report`` and ``--cov`` flags,
        then reads the generated report files from the workspace.

        Args:
            workspace: Path to the workspace directory containing the project.
            test_dir: Subdirectory containing tests (default ``tests``).

        Returns:
            Tuple of (test_report_dict, coverage_dict). Empty dicts if
            report files are not generated (e.g., on early crash).
        """
        report_file = "test-report.json"
        coverage_file = "coverage.json"

        cmd = [
            "uv",
            "run",
            "pytest",
            test_dir,
            "--json-report",
            f"--json-report-file={report_file}",
            "--cov=.",
            f"--cov-report=json:{coverage_file}",
            "-x",
        ]

        logger.info("Running tests in %s: %s", workspace, " ".join(cmd))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=workspace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout_seconds,
            )
        except TimeoutError:
            proc.kill()
            logger.warning("Test execution timed out after %ds", self.timeout_seconds)
            return {}, {}

        if stdout:
            logger.debug("pytest stdout: %s", stdout.decode()[:500])
        if stderr:
            logger.debug("pytest stderr: %s", stderr.decode()[:500])

        # Read test report
        report_path = Path(workspace) / report_file
        test_report: dict = {}
        if report_path.exists():
            test_report = json.loads(report_path.read_text())

        # Read coverage report
        coverage_path = Path(workspace) / coverage_file
        coverage_data: dict = {}
        if coverage_path.exists():
            coverage_data = json.loads(coverage_path.read_text())

        return test_report, coverage_data
