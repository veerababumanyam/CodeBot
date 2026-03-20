"""Unit tests for the SASTRunner (Semgrep scanner adapter)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from codebot.db.models.security import Severity
from codebot.security.models import ScanResult
from codebot.security.scanners.semgrep import SASTRunner

SEMGREP_JSON_OUTPUT = json.dumps(
    {
        "results": [
            {
                "check_id": "python.lang.security.audit.sql-injection",
                "path": "app/main.py",
                "start": {"line": 42, "col": 1},
                "end": {"line": 42, "col": 30},
                "extra": {
                    "severity": "ERROR",
                    "message": "Detected SQL injection risk.",
                    "lines": "cursor.query(user_input)",
                    "metadata": {
                        "cwe": ["CWE-89"],
                    },
                    "fix": "Use parameterized queries instead.",
                },
            },
            {
                "check_id": "python.lang.security.audit.hardcoded-password",
                "path": "app/config.py",
                "start": {"line": 10, "col": 1},
                "end": {"line": 10, "col": 35},
                "extra": {
                    "severity": "WARNING",
                    "message": "Hardcoded password detected.",
                    "lines": "password = 'placeholder'",
                    "metadata": {
                        "cwe": ["CWE-798"],
                    },
                    "fix": "",
                },
            },
        ],
        "errors": [],
    }
)


class TestSASTRunner:
    @pytest.mark.asyncio
    async def test_parses_findings_with_severity_mapping(self) -> None:
        """Semgrep JSON with 2 results maps to 2 ScanFindings."""
        runner = SASTRunner()
        with patch.object(
            runner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = (SEMGREP_JSON_OUTPUT, "", 1)
            result = await runner.scan("/tmp/project")

        assert len(result.findings) == 2
        assert result.findings[0].severity == Severity.HIGH  # ERROR -> HIGH
        assert result.findings[1].severity == Severity.MEDIUM  # WARNING -> MEDIUM
        assert (
            result.findings[0].rule_id
            == "python.lang.security.audit.sql-injection"
        )
        assert result.findings[0].file_path == "app/main.py"
        assert result.findings[0].line_start == 42
        assert result.findings[0].cwe == ["CWE-89"]
        assert (
            result.findings[0].fix_recommendation
            == "Use parameterized queries instead."
        )

    @pytest.mark.asyncio
    async def test_no_findings_exit_code_0(self) -> None:
        """Exit code 0 with empty results returns empty findings."""
        runner = SASTRunner()
        empty_output = json.dumps({"results": [], "errors": []})
        with patch.object(
            runner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = (empty_output, "", 0)
            result = await runner.scan("/tmp/project")

        assert result.findings == []
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_error_exit_code(self) -> None:
        """Exit code >= 2 returns errors list."""
        runner = SASTRunner()
        with patch.object(
            runner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = ("", "Semgrep crashed", 2)
            result = await runner.scan("/tmp/project")

        assert len(result.errors) > 0
        assert result.findings == []

    def test_map_severity_all_cases(self) -> None:
        """_map_severity maps Semgrep levels to Severity enum."""
        runner = SASTRunner()
        assert runner._map_severity("ERROR") == Severity.HIGH
        assert runner._map_severity("WARNING") == Severity.MEDIUM
        assert runner._map_severity("INFO") == Severity.LOW
        assert runner._map_severity("UNKNOWN") == Severity.INFO

    @pytest.mark.asyncio
    async def test_custom_rules_dir(self) -> None:
        """Custom rules directory is included in the command."""
        runner = SASTRunner(custom_rules_dir="/custom/rules")
        with patch.object(
            runner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = (
                json.dumps({"results": [], "errors": []}),
                "",
                0,
            )
            await runner.scan("/tmp/project")
            cmd = mock_cli.call_args[0][0]
            assert "/custom/rules" in cmd
