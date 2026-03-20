"""Unit tests for the DependencyScanner (Trivy scanner adapter)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from codebot.db.models.security import Severity
from codebot.security.models import ScanResult
from codebot.security.scanners.trivy import DependencyScanner

TRIVY_JSON_OUTPUT = json.dumps(
    {
        "Results": [
            {
                "Target": "requirements.txt",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2023-1234",
                        "PkgName": "requests",
                        "InstalledVersion": "2.28.0",
                        "FixedVersion": "2.31.0",
                        "Severity": "CRITICAL",
                        "Title": "HTTP request smuggling in requests",
                        "Description": "A vulnerability in requests library.",
                    },
                    {
                        "VulnerabilityID": "CVE-2023-5678",
                        "PkgName": "flask",
                        "InstalledVersion": "2.2.0",
                        "FixedVersion": "",
                        "Severity": "HIGH",
                        "Title": "XSS in Flask debug mode",
                        "Description": "Flask debug mode is vulnerable to XSS.",
                    },
                ],
            },
        ],
    }
)


class TestDependencyScanner:
    @pytest.mark.asyncio
    async def test_parses_findings(self) -> None:
        """Trivy JSON with 2 vulns maps to 2 findings."""
        scanner = DependencyScanner()
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = (TRIVY_JSON_OUTPUT, "", 0)
            result = await scanner.scan("/tmp/project")

        assert len(result.findings) == 2
        assert result.findings[0].severity == Severity.CRITICAL
        assert result.findings[1].severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_severity_mapping(self) -> None:
        """Trivy severity strings map to Severity enum."""
        scanner = DependencyScanner()
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = (TRIVY_JSON_OUTPUT, "", 0)
            result = await scanner.scan("/tmp/project")

        assert result.findings[0].severity == Severity.CRITICAL
        assert result.findings[1].severity == Severity.HIGH

    @pytest.mark.asyncio
    async def test_fix_recommendation_includes_version(self) -> None:
        """fix_recommendation includes FixedVersion when available."""
        scanner = DependencyScanner()
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = (TRIVY_JSON_OUTPUT, "", 0)
            result = await scanner.scan("/tmp/project")

        assert "2.31.0" in result.findings[0].fix_recommendation

    @pytest.mark.asyncio
    async def test_empty_results(self) -> None:
        """Empty Results array returns no findings."""
        scanner = DependencyScanner()
        empty = json.dumps({"Results": []})
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = (empty, "", 0)
            result = await scanner.scan("/tmp/project")

        assert result.findings == []

    @pytest.mark.asyncio
    async def test_null_vulnerabilities(self) -> None:
        """Trivy returns null for Vulnerabilities when none found."""
        scanner = DependencyScanner()
        null_vulns = json.dumps(
            {"Results": [{"Target": "requirements.txt", "Vulnerabilities": None}]}
        )
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = (null_vulns, "", 0)
            result = await scanner.scan("/tmp/project")

        assert result.findings == []

    @pytest.mark.asyncio
    async def test_error_case(self) -> None:
        """Non-zero returncode with no stdout returns errors."""
        scanner = DependencyScanner()
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = ("", "Trivy error: db download failed", 1)
            result = await scanner.scan("/tmp/project")

        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_title_includes_pkg_name(self) -> None:
        """Finding title includes PkgName when present."""
        scanner = DependencyScanner()
        with patch.object(
            scanner, "_run_cli", new_callable=AsyncMock
        ) as mock_cli:
            mock_cli.return_value = (TRIVY_JSON_OUTPUT, "", 0)
            result = await scanner.scan("/tmp/project")

        assert "requests" in result.findings[0].title
