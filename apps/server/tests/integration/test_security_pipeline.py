"""Integration tests for SecurityOrchestrator end-to-end with mocked CLIs.

These tests run the full orchestrator -> scanner adapter -> CLI parsing
chain with mocked subprocess calls.  Each scanner adapter (Semgrep, Trivy,
Gitleaks) receives realistic JSON output and parses it into ScanFindings,
which the orchestrator aggregates.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codebot.security.orchestrator import SecurityOrchestrator


# ---- Realistic scanner JSON fixtures ----

SEMGREP_FINDINGS_JSON = json.dumps(
    {
        "results": [
            {
                "check_id": "python.lang.security.audit.dangerous-func",
                "path": "src/app.py",
                "start": {"line": 42, "col": 1},
                "end": {"line": 42, "col": 30},
                "extra": {
                    "severity": "WARNING",
                    "message": "Detected use of dangerous function.",
                    "lines": "dangerous(user_input)",
                    "metadata": {"cwe": ["CWE-78"]},
                },
            },
            {
                "check_id": "python.lang.security.injection.sql-injection",
                "path": "src/db.py",
                "start": {"line": 15, "col": 1},
                "end": {"line": 15, "col": 50},
                "extra": {
                    "severity": "ERROR",
                    "message": "SQL injection via string formatting",
                    "lines": "cursor.run(query_str)",
                    "metadata": {"cwe": ["CWE-89"]},
                },
            },
        ]
    }
)

TRIVY_FINDINGS_JSON = json.dumps(
    {
        "Results": [
            {
                "Target": "requirements.txt",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2024-0001",
                        "PkgName": "requests",
                        "Severity": "HIGH",
                        "Title": "HTTP request smuggling",
                        "Description": "A vulnerability in requests...",
                        "FixedVersion": "2.32.0",
                    }
                ],
            }
        ]
    }
)

GITLEAKS_FINDINGS_JSON = json.dumps(
    [
        {
            "RuleID": "aws-access-key-id",
            "Description": "AWS Access Key ID",
            "File": "config.py",
            "StartLine": 5,
            "EndLine": 5,
            "Match": "AKIAIOSFODNN7EXAMPLE",
        }
    ]
)

SEMGREP_EMPTY_JSON = json.dumps({"results": []})
TRIVY_EMPTY_JSON = json.dumps({"Results": []})


def _make_mock_process(
    stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0
) -> AsyncMock:
    """Create a mock subprocess process with given output."""
    proc = AsyncMock()
    proc.communicate = AsyncMock(return_value=(stdout, stderr))
    proc.returncode = returncode
    proc.kill = MagicMock()
    return proc


def _create_subprocess_router(
    *,
    semgrep_stdout: bytes = SEMGREP_EMPTY_JSON.encode(),
    semgrep_returncode: int = 0,
    trivy_stdout: bytes = TRIVY_EMPTY_JSON.encode(),
    trivy_returncode: int = 0,
    gitleaks_stdout: bytes = b"",
    gitleaks_returncode: int = 0,
    semgrep_side_effect: Exception | None = None,
) -> AsyncMock:
    """Create an AsyncMock that routes by command name.

    Inspects the first argument to determine which scanner is being
    called and returns the appropriate mock process.
    """

    async def _route(*args: str, **kwargs: object) -> AsyncMock:
        cmd = args[0] if args else ""
        if cmd == "semgrep":
            if semgrep_side_effect is not None:
                raise semgrep_side_effect
            return _make_mock_process(
                stdout=semgrep_stdout, returncode=semgrep_returncode
            )
        if cmd == "trivy":
            return _make_mock_process(
                stdout=trivy_stdout, returncode=trivy_returncode
            )
        if cmd == "gitleaks":
            return _make_mock_process(
                stdout=gitleaks_stdout, returncode=gitleaks_returncode
            )
        # Fallback for unexpected commands
        return _make_mock_process()

    mock = AsyncMock(side_effect=_route)
    return mock


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_scan_with_mocked_cli() -> None:
    """Full scan with all 3 scanners returning realistic JSON output."""
    router = _create_subprocess_router(
        semgrep_stdout=SEMGREP_FINDINGS_JSON.encode(),
        semgrep_returncode=1,  # semgrep exit 1 = findings found
        trivy_stdout=TRIVY_FINDINGS_JSON.encode(),
        trivy_returncode=0,
        gitleaks_stdout=GITLEAKS_FINDINGS_JSON.encode(),
        gitleaks_returncode=1,  # gitleaks exit 1 = leaks found
    )

    with patch("asyncio.create_subprocess_exec", router):
        orchestrator = SecurityOrchestrator()
        report = await orchestrator.scan("/fake/project")

    # 2 semgrep + 1 trivy + 1 gitleaks = 4 findings
    assert len(report.findings) == 4
    assert report.summary.total_findings == 4

    # Verify scanner-specific findings
    tools = {f.tool for f in report.findings}
    assert tools == {"semgrep", "trivy", "gitleaks"}

    # Verify severity counts:
    #   1 gitleaks CRITICAL, 1 trivy HIGH + 1 semgrep HIGH (ERROR->HIGH),
    #   1 semgrep MEDIUM (WARNING->MEDIUM)
    assert report.summary.critical_count == 1
    assert report.summary.high_count == 2
    assert report.summary.medium_count == 1
    assert report.summary.secrets_count == 1

    # Gate should fail (CRITICAL findings and secrets present)
    assert report.gate_result is not None
    assert report.gate_result.passed is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scan_with_one_scanner_timeout() -> None:
    """Semgrep raises TimeoutError -> deps and secrets results still present."""
    router = _create_subprocess_router(
        semgrep_side_effect=TimeoutError("semgrep timed out"),
        trivy_stdout=TRIVY_FINDINGS_JSON.encode(),
        trivy_returncode=0,
        gitleaks_stdout=b"",
        gitleaks_returncode=0,  # no leaks
    )

    with patch("asyncio.create_subprocess_exec", router):
        orchestrator = SecurityOrchestrator()
        report = await orchestrator.scan("/fake/project")

    # Should have 1 trivy finding, 0 gitleaks (clean), 0 semgrep (failed)
    assert len(report.findings) == 1
    assert report.findings[0].tool == "trivy"

    # Should have error entry for the failed sast scanner
    error_scanners = [e.scanner for e in report.errors]
    assert "sast" in error_scanners


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scan_gate_blocks_on_critical() -> None:
    """Gitleaks finding (CRITICAL) present -> gate blocks."""
    router = _create_subprocess_router(
        semgrep_stdout=SEMGREP_EMPTY_JSON.encode(),
        semgrep_returncode=0,
        trivy_stdout=TRIVY_EMPTY_JSON.encode(),
        trivy_returncode=0,
        gitleaks_stdout=GITLEAKS_FINDINGS_JSON.encode(),
        gitleaks_returncode=1,  # leaks found
    )

    with patch("asyncio.create_subprocess_exec", router):
        orchestrator = SecurityOrchestrator()
        report = await orchestrator.scan("/fake/project")

    # Gitleaks finding is CRITICAL
    assert report.summary.critical_count == 1
    assert report.summary.secrets_count == 1

    # Gate should fail due to secrets
    assert report.gate_result is not None
    assert report.gate_result.passed is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scan_gate_passes_clean_code() -> None:
    """All scanners return empty findings -> gate passes."""
    router = _create_subprocess_router(
        semgrep_stdout=SEMGREP_EMPTY_JSON.encode(),
        semgrep_returncode=0,
        trivy_stdout=TRIVY_EMPTY_JSON.encode(),
        trivy_returncode=0,
        gitleaks_stdout=b"",
        gitleaks_returncode=0,  # no leaks
    )

    with patch("asyncio.create_subprocess_exec", router):
        orchestrator = SecurityOrchestrator()
        report = await orchestrator.scan("/fake/project")

    assert len(report.findings) == 0
    assert report.summary.total_findings == 0
    assert report.gate_result is not None
    assert report.gate_result.passed is True
