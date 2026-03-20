"""Unit tests for security Pydantic models and SecurityGate."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from codebot.db.models.security import Severity
from codebot.security.models import (
    AllowlistConfig,
    GateResult,
    ScanFinding,
    ScanResult,
    ScanSummary,
    SecurityReport,
    SecurityThresholds,
)
from codebot.security.gate import SecurityGate
from codebot.security.scanners.base import BaseScanner


# ---------------------------------------------------------------------------
# ScanResult model tests
# ---------------------------------------------------------------------------


class TestScanResult:
    def test_instantiation_with_fields(self) -> None:
        result = ScanResult(
            scanner="semgrep",
            findings=[],
            errors=["some error"],
            duration_ms=1234,
        )
        assert result.scanner == "semgrep"
        assert result.findings == []
        assert result.errors == ["some error"]
        assert result.duration_ms == 1234

    def test_defaults(self) -> None:
        result = ScanResult(scanner="trivy")
        assert result.findings == []
        assert result.errors == []
        assert result.duration_ms == 0


# ---------------------------------------------------------------------------
# SecurityThresholds model tests
# ---------------------------------------------------------------------------


class TestSecurityThresholds:
    def test_defaults(self) -> None:
        t = SecurityThresholds()
        assert t.max_critical == 0
        assert t.max_high == 0
        assert t.max_medium == 5
        assert t.max_low == 20
        assert t.require_no_secrets is True


# ---------------------------------------------------------------------------
# AllowlistConfig model tests
# ---------------------------------------------------------------------------


class TestAllowlistConfig:
    def test_holds_package_sets(self) -> None:
        config = AllowlistConfig(
            python_packages={"fastapi", "pydantic"},
            npm_packages={"react", "vite"},
        )
        assert "fastapi" in config.python_packages
        assert "react" in config.npm_packages
        assert config.require_hashes is True
        assert config.block_unknown is True


# ---------------------------------------------------------------------------
# SecurityGate tests
# ---------------------------------------------------------------------------


def _make_report(
    *,
    critical: int = 0,
    high: int = 0,
    medium: int = 0,
    low: int = 0,
    secrets: int = 0,
) -> SecurityReport:
    """Helper to build a SecurityReport with a pre-populated summary."""
    return SecurityReport(
        summary=ScanSummary(
            total_findings=critical + high + medium + low,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            secrets_count=secrets,
        ),
    )


class TestSecurityGate:
    def test_gate_passes_no_findings(self) -> None:
        gate = SecurityGate()
        report = _make_report()
        result = gate.evaluate(report)
        assert result.passed is True
        assert result.warnings == []

    def test_gate_fails_critical(self) -> None:
        gate = SecurityGate()
        report = _make_report(critical=1)
        result = gate.evaluate(report)
        assert result.passed is False
        assert "CRITICAL" in result.reason

    def test_gate_fails_high(self) -> None:
        gate = SecurityGate()
        report = _make_report(high=1)
        result = gate.evaluate(report)
        assert result.passed is False
        assert "HIGH" in result.reason

    def test_gate_fails_secrets(self) -> None:
        gate = SecurityGate()
        report = _make_report(secrets=3)
        result = gate.evaluate(report)
        assert result.passed is False
        assert "secrets" in result.reason.lower()

    def test_gate_passes_medium_within_threshold(self) -> None:
        gate = SecurityGate()
        report = _make_report(medium=3)
        result = gate.evaluate(report)
        assert result.passed is True

    def test_gate_warns_medium_above_threshold(self) -> None:
        gate = SecurityGate()
        report = _make_report(medium=10)
        result = gate.evaluate(report)
        assert result.passed is True
        assert len(result.warnings) > 0
        assert "MEDIUM" in result.warnings[0]

    def test_gate_warns_low_above_threshold(self) -> None:
        gate = SecurityGate()
        report = _make_report(low=25)
        result = gate.evaluate(report)
        assert result.passed is True
        assert any("LOW" in w for w in result.warnings)

    def test_custom_thresholds(self) -> None:
        thresholds = SecurityThresholds(max_critical=2, max_high=5)
        gate = SecurityGate(thresholds=thresholds)
        # 2 critical is within threshold (max_critical=2 means > 2 fails)
        report = _make_report(critical=2)
        result = gate.evaluate(report)
        assert result.passed is True

        # 3 critical exceeds threshold
        report = _make_report(critical=3)
        result = gate.evaluate(report)
        assert result.passed is False


# ---------------------------------------------------------------------------
# BaseScanner._run_cli timeout test
# ---------------------------------------------------------------------------


class TestBaseScanner:
    @pytest.mark.asyncio
    async def test_run_cli_timeout(self) -> None:
        """BaseScanner._run_cli raises TimeoutError after timeout."""

        class DummyScanner(BaseScanner):
            async def scan(self, project_path: str) -> ScanResult:
                return ScanResult(scanner="dummy")

        scanner = DummyScanner()
        with pytest.raises(asyncio.TimeoutError):
            await scanner._run_cli(["sleep", "30"], timeout=1)
