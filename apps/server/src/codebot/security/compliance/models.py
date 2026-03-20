"""Compliance Pydantic models for SOC 2 Trust Service Criteria evaluation.

Defines frameworks, TSC categories, individual check results, and the
aggregate compliance report used by :class:`SOC2ComplianceChecker`.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, computed_field


class ComplianceFramework(StrEnum):
    """Supported compliance frameworks."""

    SOC2 = "SOC2"
    HIPAA = "HIPAA"
    GDPR = "GDPR"
    PCI_DSS = "PCI_DSS"


class TrustServiceCategory(StrEnum):
    """SOC 2 Trust Service Criteria categories.

    - CC6: Logical Access Controls
    - CC7: System Operations
    - CC8: Change Management
    - CC9: Risk Mitigation
    - A1: Availability
    - PI1: Processing Integrity
    - C1: Confidentiality
    - P1: Privacy
    """

    CC6 = "CC6"
    CC7 = "CC7"
    CC8 = "CC8"
    CC9 = "CC9"
    A1 = "A1"
    PI1 = "PI1"
    C1 = "C1"
    P1 = "P1"


class ComplianceCheckResult(BaseModel):
    """Result of a single TSC rule evaluation against a project.

    Attributes:
        category: Which TSC category this check belongs to.
        rule_id: Unique rule identifier (e.g. ``CC6-001``).
        description: Human-readable description of what was checked.
        passed: Whether the check passed.
        evidence: Supporting detail (pattern found / not found).
    """

    category: TrustServiceCategory
    rule_id: str
    description: str
    passed: bool
    evidence: str = ""


class ComplianceReport(BaseModel):
    """Aggregate compliance report for a single framework evaluation.

    Attributes:
        framework: Which compliance framework was evaluated.
        results: Individual check results.
        passed: Computed -- ``True`` only if all checks passed.
        findings_count: Computed -- number of failed checks.
    """

    framework: ComplianceFramework = ComplianceFramework.SOC2
    results: list[ComplianceCheckResult] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passed(self) -> bool:
        """Report passes only when every individual check passes."""
        return all(r.passed for r in self.results)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def findings_count(self) -> int:
        """Count of failed checks (compliance violations)."""
        return sum(1 for r in self.results if not r.passed)
