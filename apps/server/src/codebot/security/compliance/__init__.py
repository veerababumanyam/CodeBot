"""SOC 2 compliance checking package.

Provides TSC-based compliance evaluation for generated code,
immutable audit logging with tamper-detection hashing, and
structured evidence collection for auditor export.
"""

from codebot.security.compliance.checker import SOC2ComplianceChecker
from codebot.security.compliance.evidence import ComplianceEvidenceCollector
from codebot.security.compliance.models import (
    ComplianceCheckResult,
    ComplianceFramework,
    ComplianceReport,
    TrustServiceCategory,
)

__all__ = [
    "ComplianceCheckResult",
    "ComplianceEvidenceCollector",
    "ComplianceFramework",
    "ComplianceReport",
    "SOC2ComplianceChecker",
    "TrustServiceCategory",
]
