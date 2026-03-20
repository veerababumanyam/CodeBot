"""Security scanning pipeline package.

Provides scanner adapters, quality gate, and configuration for the
CodeBot security pipeline.
"""

from codebot.security.gate import SecurityGate
from codebot.security.models import (
    AllowlistConfig,
    GateResult,
    ScanResult,
    SecurityReport,
    SecurityThresholds,
)
from codebot.security.scanners.base import BaseScanner

__all__ = [
    "AllowlistConfig",
    "BaseScanner",
    "GateResult",
    "ScanResult",
    "SecurityGate",
    "SecurityReport",
    "SecurityThresholds",
]
