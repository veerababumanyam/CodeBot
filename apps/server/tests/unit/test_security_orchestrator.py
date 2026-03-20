"""Unit tests for SecurityOrchestrator parallel fan-out, deduplication, and summary."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from codebot.db.models.security import Severity
from codebot.security.models import (
    ScanFinding,
    ScanResult,
    SecurityReport,
    SecurityThresholds,
)
from codebot.security.orchestrator import SecurityOrchestrator


def _make_finding(
    *,
    tool: str = "semgrep",
    rule_id: str = "rule-1",
    severity: Severity = Severity.MEDIUM,
    file_path: str = "src/app.py",
    line_start: int = 10,
    title: str = "test finding",
) -> ScanFinding:
    """Create a ScanFinding with sensible defaults."""
    return ScanFinding(
        tool=tool,
        rule_id=rule_id,
        severity=severity,
        title=title,
        file_path=file_path,
        line_start=line_start,
    )


@pytest.mark.asyncio
async def test_scan_runs_all_scanners() -> None:
    """Verify orchestrator invokes all 3 scanner scan() methods."""
    sast = AsyncMock()
    sast.scan = AsyncMock(return_value=ScanResult(scanner="semgrep"))
    deps = AsyncMock()
    deps.scan = AsyncMock(return_value=ScanResult(scanner="trivy"))
    secrets = AsyncMock()
    secrets.scan = AsyncMock(return_value=ScanResult(scanner="gitleaks"))

    orchestrator = SecurityOrchestrator(sast=sast, deps=deps, secrets=secrets)
    report = await orchestrator.scan("/fake")

    sast.scan.assert_awaited_once_with("/fake")
    deps.scan.assert_awaited_once_with("/fake")
    secrets.scan.assert_awaited_once_with("/fake")
    assert isinstance(report, SecurityReport)


@pytest.mark.asyncio
async def test_scan_aggregates_findings() -> None:
    """sast returns 2, deps returns 1, secrets returns 1 -> total 4."""
    sast = AsyncMock()
    sast.scan = AsyncMock(
        return_value=ScanResult(
            scanner="semgrep",
            findings=[
                _make_finding(tool="semgrep", rule_id="r1"),
                _make_finding(tool="semgrep", rule_id="r2", line_start=20),
            ],
        )
    )
    deps = AsyncMock()
    deps.scan = AsyncMock(
        return_value=ScanResult(
            scanner="trivy",
            findings=[_make_finding(tool="trivy", rule_id="CVE-2024-001")],
        )
    )
    secrets = AsyncMock()
    secrets.scan = AsyncMock(
        return_value=ScanResult(
            scanner="gitleaks",
            findings=[
                _make_finding(
                    tool="gitleaks",
                    rule_id="aws-key",
                    severity=Severity.CRITICAL,
                )
            ],
        )
    )

    orchestrator = SecurityOrchestrator(sast=sast, deps=deps, secrets=secrets)
    report = await orchestrator.scan("/fake")

    assert len(report.findings) == 4
    assert report.summary.total_findings == 4


@pytest.mark.asyncio
async def test_scan_deduplicates() -> None:
    """Two scanners return a finding with same key -> only 1 in report."""
    dup = _make_finding(tool="semgrep", rule_id="dup-1", file_path="a.py", line_start=5)
    sast = AsyncMock()
    sast.scan = AsyncMock(
        return_value=ScanResult(scanner="semgrep", findings=[dup])
    )
    deps = AsyncMock()
    deps.scan = AsyncMock(
        return_value=ScanResult(scanner="trivy", findings=[])
    )
    secrets = AsyncMock()
    # Same (tool, rule_id, file_path, line_start) as dup above
    dup2 = _make_finding(tool="semgrep", rule_id="dup-1", file_path="a.py", line_start=5)
    secrets.scan = AsyncMock(
        return_value=ScanResult(scanner="gitleaks", findings=[dup2])
    )

    orchestrator = SecurityOrchestrator(sast=sast, deps=deps, secrets=secrets)
    report = await orchestrator.scan("/fake")

    assert len(report.findings) == 1


@pytest.mark.asyncio
async def test_build_summary_counts_correctly() -> None:
    """1 CRITICAL, 2 HIGH, 1 gitleaks finding -> correct summary counts."""
    findings = [
        _make_finding(tool="semgrep", rule_id="r1", severity=Severity.CRITICAL, line_start=1),
        _make_finding(tool="trivy", rule_id="r2", severity=Severity.HIGH, line_start=2),
        _make_finding(tool="trivy", rule_id="r3", severity=Severity.HIGH, line_start=3),
        _make_finding(
            tool="gitleaks",
            rule_id="r4",
            severity=Severity.CRITICAL,
            line_start=4,
        ),
    ]
    sast = AsyncMock()
    sast.scan = AsyncMock(
        return_value=ScanResult(scanner="semgrep", findings=[findings[0]])
    )
    deps = AsyncMock()
    deps.scan = AsyncMock(
        return_value=ScanResult(scanner="trivy", findings=[findings[1], findings[2]])
    )
    secrets = AsyncMock()
    secrets.scan = AsyncMock(
        return_value=ScanResult(scanner="gitleaks", findings=[findings[3]])
    )

    orchestrator = SecurityOrchestrator(sast=sast, deps=deps, secrets=secrets)
    report = await orchestrator.scan("/fake")

    assert report.summary.critical_count == 2
    assert report.summary.high_count == 2
    assert report.summary.secrets_count == 1
    assert report.summary.total_findings == 4


@pytest.mark.asyncio
async def test_scan_attaches_gate_result() -> None:
    """Default thresholds, 1 CRITICAL finding -> gate_result.passed==False."""
    sast = AsyncMock()
    sast.scan = AsyncMock(
        return_value=ScanResult(
            scanner="semgrep",
            findings=[_make_finding(severity=Severity.CRITICAL)],
        )
    )
    deps = AsyncMock()
    deps.scan = AsyncMock(return_value=ScanResult(scanner="trivy"))
    secrets = AsyncMock()
    secrets.scan = AsyncMock(return_value=ScanResult(scanner="gitleaks"))

    orchestrator = SecurityOrchestrator(sast=sast, deps=deps, secrets=secrets)
    report = await orchestrator.scan("/fake")

    assert report.gate_result is not None
    assert report.gate_result.passed is False


@pytest.mark.asyncio
async def test_scan_handles_scanner_failure() -> None:
    """One scanner raises Exception -> report has results from other 2 + error entry."""
    sast = AsyncMock()
    sast.scan = AsyncMock(side_effect=RuntimeError("semgrep crashed"))
    deps = AsyncMock()
    deps.scan = AsyncMock(
        return_value=ScanResult(
            scanner="trivy",
            findings=[_make_finding(tool="trivy", rule_id="v1")],
        )
    )
    secrets = AsyncMock()
    secrets.scan = AsyncMock(
        return_value=ScanResult(
            scanner="gitleaks",
            findings=[
                _make_finding(
                    tool="gitleaks",
                    rule_id="s1",
                    severity=Severity.CRITICAL,
                )
            ],
        )
    )

    orchestrator = SecurityOrchestrator(sast=sast, deps=deps, secrets=secrets)
    report = await orchestrator.scan("/fake")

    # Should have findings from deps and secrets
    assert len(report.findings) == 2
    # Should have at least one error entry for the failed scanner
    error_scanners = [e.scanner for e in report.errors]
    assert "sast" in error_scanners


@pytest.mark.asyncio
async def test_custom_thresholds_passed_to_gate() -> None:
    """SecurityThresholds(max_critical=5), 1 CRITICAL -> gate passes."""
    thresholds = SecurityThresholds(max_critical=5)
    sast = AsyncMock()
    sast.scan = AsyncMock(
        return_value=ScanResult(
            scanner="semgrep",
            findings=[_make_finding(severity=Severity.CRITICAL)],
        )
    )
    deps = AsyncMock()
    deps.scan = AsyncMock(return_value=ScanResult(scanner="trivy"))
    secrets = AsyncMock()
    secrets.scan = AsyncMock(return_value=ScanResult(scanner="gitleaks"))

    orchestrator = SecurityOrchestrator(
        thresholds=thresholds, sast=sast, deps=deps, secrets=secrets
    )
    report = await orchestrator.scan("/fake")

    assert report.gate_result is not None
    assert report.gate_result.passed is True
