"""Unit tests for SOC 2 compliance checker, models, and TSC rules loader."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from codebot.security.compliance.models import (
    ComplianceCheckResult,
    ComplianceFramework,
    ComplianceReport,
    TrustServiceCategory,
)
from codebot.security.compliance.tsc_rules import TSCRulesLoader


class TestComplianceFramework:
    """ComplianceFramework enum values."""

    def test_has_soc2(self) -> None:
        assert ComplianceFramework.SOC2 == "SOC2"

    def test_has_hipaa(self) -> None:
        assert ComplianceFramework.HIPAA == "HIPAA"

    def test_has_gdpr(self) -> None:
        assert ComplianceFramework.GDPR == "GDPR"

    def test_has_pci_dss(self) -> None:
        assert ComplianceFramework.PCI_DSS == "PCI_DSS"


class TestTrustServiceCategory:
    """TrustServiceCategory enum values."""

    def test_has_cc6(self) -> None:
        assert TrustServiceCategory.CC6 == "CC6"

    def test_has_cc7(self) -> None:
        assert TrustServiceCategory.CC7 == "CC7"

    def test_has_cc8(self) -> None:
        assert TrustServiceCategory.CC8 == "CC8"

    def test_has_cc9(self) -> None:
        assert TrustServiceCategory.CC9 == "CC9"

    def test_has_a1(self) -> None:
        assert TrustServiceCategory.A1 == "A1"

    def test_has_pi1(self) -> None:
        assert TrustServiceCategory.PI1 == "PI1"

    def test_has_c1(self) -> None:
        assert TrustServiceCategory.C1 == "C1"

    def test_has_p1(self) -> None:
        assert TrustServiceCategory.P1 == "P1"


class TestComplianceCheckResult:
    """ComplianceCheckResult Pydantic model."""

    def test_create_result(self) -> None:
        result = ComplianceCheckResult(
            category=TrustServiceCategory.CC6,
            rule_id="CC6-001",
            description="Auth middleware required",
            passed=False,
            evidence="No auth decorator found",
        )
        assert result.category == TrustServiceCategory.CC6
        assert result.rule_id == "CC6-001"
        assert result.passed is False
        assert result.evidence == "No auth decorator found"


class TestComplianceReport:
    """ComplianceReport Pydantic model (extended)."""

    def test_compliance_report_fields(self) -> None:
        report = ComplianceReport(
            framework=ComplianceFramework.SOC2,
            results=[
                ComplianceCheckResult(
                    category=TrustServiceCategory.CC6,
                    rule_id="CC6-001",
                    description="Auth middleware",
                    passed=True,
                    evidence="Found @require_auth",
                ),
                ComplianceCheckResult(
                    category=TrustServiceCategory.CC7,
                    rule_id="CC7-001",
                    description="Structured logging",
                    passed=False,
                    evidence="No logging import found",
                ),
            ],
        )
        assert report.framework == ComplianceFramework.SOC2
        assert len(report.results) == 2
        assert report.passed is False  # one failed check
        assert report.findings_count == 1  # count of failures


class TestTSCRulesLoader:
    """TSC rules loading from YAML configuration."""

    def test_load_rules_from_yaml(self, tmp_path: Path) -> None:
        yaml_content = textwrap.dedent("""\
            framework: SOC2
            rules:
              - id: CC6-001
                category: CC6
                description: "Authentication middleware required"
                check_type: pattern
                patterns:
                  - "@require_auth"
                  - "authenticate"
                severity: HIGH
              - id: CC7-001
                category: CC7
                description: "Structured logging required"
                check_type: pattern
                patterns:
                  - "import logging"
                  - "structlog"
                severity: MEDIUM
        """)
        yaml_file = tmp_path / "soc2.yaml"
        yaml_file.write_text(yaml_content)

        loader = TSCRulesLoader(str(yaml_file))
        rules = loader.load()

        assert len(rules) == 2
        assert rules[0].id == "CC6-001"
        assert rules[0].category == TrustServiceCategory.CC6
        assert rules[0].patterns == ["@require_auth", "authenticate"]
        assert rules[1].id == "CC7-001"


class TestSOC2ComplianceChecker:
    """SOC2ComplianceChecker integration tests with mocked filesystem."""

    @pytest.fixture()
    def project_with_auth(self, tmp_path: Path) -> Path:
        """Create a project directory with auth patterns present."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "auth.py").write_text(
            "from flask import request\n"
            "@require_auth\n"
            "def protected_route():\n"
            "    pass\n"
        )
        (src / "app.py").write_text(
            "import logging\n"
            "logger = logging.getLogger(__name__)\n"
            "from pydantic import BaseModel\n"
        )
        (src / "migrations").mkdir()
        (src / "migrations" / "001.sql").write_text("ALTER TABLE users ADD COLUMN role TEXT;")
        (src / "health.py").write_text(
            "from fastapi import APIRouter\n"
            "router = APIRouter()\n"
            "@router.get('/health')\n"
            "def health(): return {'status': 'ok'}\n"
        )
        return tmp_path

    @pytest.fixture()
    def project_without_auth(self, tmp_path: Path) -> Path:
        """Create a project directory with no security patterns."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text("print('hello world')\n")
        return tmp_path

    @pytest.fixture()
    def soc2_yaml(self, tmp_path: Path) -> Path:
        """Create a minimal SOC2 rules YAML file."""
        yaml_content = textwrap.dedent("""\
            framework: SOC2
            rules:
              - id: CC6-001
                category: CC6
                description: "Authentication middleware required"
                check_type: pattern
                patterns:
                  - "@require_auth"
                  - "authenticate"
                  - "Depends(get_current_user)"
                severity: HIGH
              - id: CC7-001
                category: CC7
                description: "Structured logging required"
                check_type: pattern
                patterns:
                  - "import logging"
                  - "import structlog"
                severity: MEDIUM
              - id: CC8-001
                category: CC8
                description: "Database migrations present"
                check_type: file_exists
                file_patterns:
                  - "**/migrations/**"
                  - "**/alembic/**"
                severity: MEDIUM
              - id: A1-001
                category: A1
                description: "Health check endpoint required"
                check_type: pattern
                patterns:
                  - "/health"
                  - "health_check"
                severity: HIGH
        """)
        rules_file = tmp_path / "soc2_rules.yaml"
        rules_file.write_text(yaml_content)
        return rules_file

    @pytest.mark.asyncio()
    async def test_check_returns_compliance_report(
        self, project_with_auth: Path, soc2_yaml: Path
    ) -> None:
        from codebot.security.compliance.checker import SOC2ComplianceChecker

        checker = SOC2ComplianceChecker(config_path=str(soc2_yaml))
        result = await checker.scan(str(project_with_auth))

        # Returns a ScanResult
        assert result.scanner == "soc2-compliance"

    @pytest.mark.asyncio()
    async def test_produces_scan_findings(
        self, project_with_auth: Path, soc2_yaml: Path
    ) -> None:
        from codebot.security.compliance.checker import SOC2ComplianceChecker

        checker = SOC2ComplianceChecker(config_path=str(soc2_yaml))
        result = await checker.scan(str(project_with_auth))

        for finding in result.findings:
            assert finding.tool == "soc2-compliance"

    @pytest.mark.asyncio()
    async def test_missing_patterns_produce_violations(
        self, project_without_auth: Path, soc2_yaml: Path
    ) -> None:
        from codebot.security.compliance.checker import SOC2ComplianceChecker

        checker = SOC2ComplianceChecker(config_path=str(soc2_yaml))
        result = await checker.scan(str(project_without_auth))

        # Should produce COMPLIANCE_VIOLATION findings for missing auth, logging,
        # migrations, and health endpoint
        assert len(result.findings) > 0
        violation_rule_ids = [f.rule_id for f in result.findings]
        assert "CC6-001" in violation_rule_ids  # No auth middleware
        assert "CC7-001" in violation_rule_ids  # No logging
        assert "CC8-001" in violation_rule_ids  # No migrations
        assert "A1-001" in violation_rule_ids  # No health endpoint

    @pytest.mark.asyncio()
    async def test_passing_project_no_violations(
        self, project_with_auth: Path, soc2_yaml: Path
    ) -> None:
        from codebot.security.compliance.checker import SOC2ComplianceChecker

        checker = SOC2ComplianceChecker(config_path=str(soc2_yaml))
        result = await checker.scan(str(project_with_auth))

        # Should have no findings -- all patterns present
        assert len(result.findings) == 0

    @pytest.mark.asyncio()
    async def test_tsc_rules_loaded_from_yaml(
        self, project_without_auth: Path, soc2_yaml: Path
    ) -> None:
        from codebot.security.compliance.checker import SOC2ComplianceChecker

        checker = SOC2ComplianceChecker(config_path=str(soc2_yaml))
        # Verify rules were loaded
        assert len(checker.rules) == 4
        assert checker.rules[0].id == "CC6-001"

    @pytest.mark.asyncio()
    async def test_findings_have_correct_severity(
        self, project_without_auth: Path, soc2_yaml: Path
    ) -> None:
        from codebot.security.compliance.checker import SOC2ComplianceChecker
        from codebot.db.models.security import Severity

        checker = SOC2ComplianceChecker(config_path=str(soc2_yaml))
        result = await checker.scan(str(project_without_auth))

        severity_map = {f.rule_id: f.severity for f in result.findings}
        assert severity_map["CC6-001"] == Severity.HIGH
        assert severity_map["CC7-001"] == Severity.MEDIUM
