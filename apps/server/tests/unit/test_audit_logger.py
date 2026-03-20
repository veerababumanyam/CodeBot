"""Unit tests for ImmutableAuditLogger and ComplianceEvidenceCollector."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from codebot.security.compliance.models import (
    ComplianceFramework,
    TrustServiceCategory,
)


class TestImmutableAuditLogger:
    """ImmutableAuditLogger SHA-256 hashing, compliance tagging, and retention."""

    @pytest.fixture()
    def mock_session(self) -> AsyncMock:
        """Create a mock async database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()
        return session

    def test_log_computes_sha256_hash(self, mock_session: AsyncMock) -> None:
        """ImmutableAuditLogger.log() computes SHA-256 hash from entry details."""
        from codebot.security.audit import ImmutableAuditLogger

        logger = ImmutableAuditLogger(session=mock_session)
        entry = logger.log(
            action="create_project",
            resource_type="Project",
            resource_id="proj-123",
            details={"name": "test-project"},
        )

        assert entry.content_hash is not None
        assert len(entry.content_hash) == 64  # SHA-256 hex digest length

    def test_log_hash_is_deterministic(self, mock_session: AsyncMock) -> None:
        """Same inputs produce the same hash."""
        from codebot.security.audit import ImmutableAuditLogger

        logger = ImmutableAuditLogger(session=mock_session)
        entry1 = logger.log(
            action="create_project",
            resource_type="Project",
            resource_id="proj-123",
            details={"name": "test"},
        )
        entry2 = logger.log(
            action="create_project",
            resource_type="Project",
            resource_id="proj-123",
            details={"name": "test"},
        )

        assert entry1.content_hash == entry2.content_hash

    def test_log_sets_compliance_framework(self, mock_session: AsyncMock) -> None:
        """ImmutableAuditLogger.log() sets compliance_framework field."""
        from codebot.security.audit import ImmutableAuditLogger

        logger = ImmutableAuditLogger(
            session=mock_session,
            framework=ComplianceFramework.SOC2,
        )
        entry = logger.log(
            action="run_scan",
            resource_type="SecurityScan",
            resource_id="scan-456",
        )

        assert entry.compliance_framework == "SOC2"

    def test_log_sets_evidence_type(self, mock_session: AsyncMock) -> None:
        """ImmutableAuditLogger.log() sets evidence_type field."""
        from codebot.security.audit import ImmutableAuditLogger

        logger = ImmutableAuditLogger(
            session=mock_session,
            framework=ComplianceFramework.SOC2,
        )
        entry = logger.log(
            action="run_scan",
            resource_type="SecurityScan",
            resource_id="scan-456",
            evidence_type="CC7",
        )

        assert entry.evidence_type == "CC7"

    def test_log_sets_retention_soc2(self, mock_session: AsyncMock) -> None:
        """ImmutableAuditLogger.log() sets retention_until based on SOC2 (1 year)."""
        from codebot.security.audit import ImmutableAuditLogger

        logger = ImmutableAuditLogger(
            session=mock_session,
            framework=ComplianceFramework.SOC2,
        )
        before = datetime.now(UTC)
        entry = logger.log(
            action="access_data",
            resource_type="Data",
            resource_id="data-789",
        )

        assert entry.retention_until is not None
        # SOC 2 requires 1 year retention
        expected_min = before + timedelta(days=364)
        expected_max = before + timedelta(days=366)
        assert expected_min <= entry.retention_until <= expected_max

    def test_verify_detects_tampered_entry(self, mock_session: AsyncMock) -> None:
        """ImmutableAuditLogger.verify() detects tampered entries by recomputing hash."""
        from codebot.security.audit import ImmutableAuditLogger

        logger = ImmutableAuditLogger(session=mock_session)
        entry = logger.log(
            action="create_project",
            resource_type="Project",
            resource_id="proj-123",
            details={"name": "original"},
        )

        # Tamper with the entry
        entry.details = {"name": "tampered"}

        assert logger.verify(entry) is False

    def test_verify_passes_untampered_entry(self, mock_session: AsyncMock) -> None:
        """ImmutableAuditLogger.verify() passes for untampered entries."""
        from codebot.security.audit import ImmutableAuditLogger

        logger = ImmutableAuditLogger(session=mock_session)
        entry = logger.log(
            action="create_project",
            resource_type="Project",
            resource_id="proj-123",
            details={"name": "original"},
        )

        assert logger.verify(entry) is True

    def test_log_adds_to_session(self, mock_session: AsyncMock) -> None:
        """ImmutableAuditLogger.log() adds the entry to the database session."""
        from codebot.security.audit import ImmutableAuditLogger

        logger = ImmutableAuditLogger(session=mock_session)
        logger.log(
            action="create_project",
            resource_type="Project",
            resource_id="proj-123",
        )

        mock_session.add.assert_called_once()


class TestComplianceEvidenceCollector:
    """ComplianceEvidenceCollector groups and exports evidence as JSON."""

    def test_export_groups_by_tsc_category(self) -> None:
        """ComplianceEvidenceCollector.export() groups evidence by TSC category."""
        from codebot.security.compliance.evidence import ComplianceEvidenceCollector

        collector = ComplianceEvidenceCollector()

        # Add evidence entries
        collector.add_evidence(
            category=TrustServiceCategory.CC6,
            evidence_type="scan_result",
            data={"finding": "auth check passed"},
        )
        collector.add_evidence(
            category=TrustServiceCategory.CC6,
            evidence_type="audit_log",
            data={"action": "login"},
        )
        collector.add_evidence(
            category=TrustServiceCategory.CC7,
            evidence_type="scan_result",
            data={"finding": "logging present"},
        )

        package = collector.export()

        assert "CC6" in package
        assert "CC7" in package
        assert len(package["CC6"]) == 2
        assert len(package["CC7"]) == 1

    def test_export_produces_structured_json(self) -> None:
        """ComplianceEvidenceCollector.export() produces structured JSON output."""
        from codebot.security.compliance.evidence import ComplianceEvidenceCollector

        collector = ComplianceEvidenceCollector()
        collector.add_evidence(
            category=TrustServiceCategory.CC6,
            evidence_type="scan_result",
            data={"passed": True},
        )

        package = collector.export()

        # Should be JSON-serializable
        json_str = json.dumps(package)
        parsed = json.loads(json_str)
        assert "CC6" in parsed
        assert parsed["CC6"][0]["evidence_type"] == "scan_result"
        assert parsed["CC6"][0]["data"]["passed"] is True

    def test_export_empty_collector(self) -> None:
        """Empty collector produces empty dict."""
        from codebot.security.compliance.evidence import ComplianceEvidenceCollector

        collector = ComplianceEvidenceCollector()
        package = collector.export()
        assert package == {}

    def test_export_includes_metadata(self) -> None:
        """Each evidence entry includes timestamp and type metadata."""
        from codebot.security.compliance.evidence import ComplianceEvidenceCollector

        collector = ComplianceEvidenceCollector()
        collector.add_evidence(
            category=TrustServiceCategory.A1,
            evidence_type="health_check",
            data={"endpoint": "/health", "status": 200},
        )

        package = collector.export()
        entry = package["A1"][0]

        assert "evidence_type" in entry
        assert "data" in entry
        assert "collected_at" in entry
        assert entry["evidence_type"] == "health_check"

    def test_export_json_string(self) -> None:
        """export_json() returns a JSON string."""
        from codebot.security.compliance.evidence import ComplianceEvidenceCollector

        collector = ComplianceEvidenceCollector()
        collector.add_evidence(
            category=TrustServiceCategory.CC9,
            evidence_type="config",
            data={"rate_limiting": True},
        )

        json_output = collector.export_json()
        assert isinstance(json_output, str)
        parsed = json.loads(json_output)
        assert "CC9" in parsed
