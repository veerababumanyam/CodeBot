"""Unit tests for the SecretScanner (Gitleaks scanner adapter)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from codebot.db.models.security import Severity
from codebot.security.models import ScanResult
from codebot.security.scanners.gitleaks import SecretScanner

GITLEAKS_JSON_OUTPUT = json.dumps(
    [
        {
            "RuleID": "aws-access-key",
            "Description": "AWS Access Key",
            "File": "app/config.py",
            "StartLine": 15,
            "EndLine": 15,
            "Match": "AKIAIOSFODNN7EXAMPLE",
        },
        {
            "RuleID": "generic-api-key",
            "Description": "Generic API Key",
            "File": "app/settings.py",
            "StartLine": 22,
            "EndLine": 22,
            "Match": "api_key = 'sk-1234567890abcdef'",
        },
    ]
)


class TestSecretScanner:
    @pytest.mark.asyncio
    async def test_parses_leaks_all_critical(self) -> None:
        """Exit code 1 with leaks maps to CRITICAL findings."""
        scanner = SecretScanner()
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = (GITLEAKS_JSON_OUTPUT, "", 1)
            result = await scanner.scan("/tmp/project")

        assert len(result.findings) == 2
        assert all(f.severity == Severity.CRITICAL for f in result.findings)
        assert result.findings[0].rule_id == "aws-access-key"
        assert result.findings[0].file_path == "app/config.py"
        assert result.findings[0].line_start == 15

    @pytest.mark.asyncio
    async def test_no_leaks_exit_0(self) -> None:
        """Exit code 0 means no secrets found."""
        scanner = SecretScanner()
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = ("", "", 0)
            result = await scanner.scan("/tmp/project")

        assert result.findings == []
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_error_exit_code(self) -> None:
        """Exit code > 1 returns errors."""
        scanner = SecretScanner()
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = ("", "gitleaks error: invalid config", 2)
            result = await scanner.scan("/tmp/project")

        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_truncates_code_snippet(self) -> None:
        """Match > 200 characters is truncated."""
        scanner = SecretScanner()
        long_match = "x" * 300
        leaks = json.dumps(
            [
                {
                    "RuleID": "long-secret",
                    "Description": "Long Secret",
                    "File": "app/main.py",
                    "StartLine": 1,
                    "EndLine": 1,
                    "Match": long_match,
                }
            ]
        )
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = (leaks, "", 1)
            result = await scanner.scan("/tmp/project")

        assert len(result.findings[0].code_snippet) == 200

    @pytest.mark.asyncio
    async def test_fix_recommendation(self) -> None:
        """All findings include the standard fix recommendation."""
        scanner = SecretScanner()
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = (GITLEAKS_JSON_OUTPUT, "", 1)
            result = await scanner.scan("/tmp/project")

        for finding in result.findings:
            assert "environment variables" in finding.fix_recommendation.lower()

    @pytest.mark.asyncio
    async def test_config_path_in_command(self) -> None:
        """Custom config path is included in the command."""
        scanner = SecretScanner(config_path="/custom/gitleaks.toml")
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = ("", "", 0)
            await scanner.scan("/tmp/project")
            cmd = mock_cli.call_args[0][0]
            assert "--config" in cmd
            assert "/custom/gitleaks.toml" in cmd
