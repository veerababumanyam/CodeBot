"""Security scanning Pydantic models.

Defines the shared data structures used across all scanner adapters,
the security gate, and the orchestrator.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from codebot.db.models.security import Severity


class ScanFinding(BaseModel):
    """A single finding produced by a security scanner."""

    tool: str
    rule_id: str = ""
    severity: Severity
    title: str
    description: str = ""
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    code_snippet: str = ""
    cwe: list[str] = Field(default_factory=list)
    cve_id: str | None = None
    fix_recommendation: str = ""


class ScanResult(BaseModel):
    """Aggregated output from a single scanner run."""

    scanner: str
    findings: list[ScanFinding] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    duration_ms: int = 0


class ScanSummary(BaseModel):
    """Counts of findings by severity level."""

    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    secrets_count: int = 0


class GateResult(BaseModel):
    """Outcome of a security gate evaluation."""

    passed: bool
    reason: str = ""
    warnings: list[str] = Field(default_factory=list)


class SecurityThresholds(BaseModel):
    """Configurable thresholds for the security quality gate."""

    max_critical: int = 0
    max_high: int = 0
    max_medium: int = 5
    max_low: int = 20
    require_no_secrets: bool = True
    require_compliance_pass: bool = False


class ScanError(BaseModel):
    """Error reported by a scanner."""

    scanner: str
    error: str


class ComplianceReport(BaseModel):
    """Placeholder for SOC 2 compliance report (built in later plan)."""

    passed: bool = True
    findings_count: int = 0


class SecurityReport(BaseModel):
    """Complete security scan report combining all scanner outputs."""

    findings: list[ScanFinding] = Field(default_factory=list)
    errors: list[ScanError] = Field(default_factory=list)
    summary: ScanSummary = Field(default_factory=ScanSummary)
    gate_result: GateResult | None = None
    compliance_report: ComplianceReport | None = None


class AllowlistConfig(BaseModel):
    """Approved dependency packages for pip and npm."""

    python_packages: set[str] = Field(default_factory=set)
    npm_packages: set[str] = Field(default_factory=set)
    require_hashes: bool = True
    block_unknown: bool = True
