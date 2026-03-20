"""Security quality gate with threshold-based pass/fail evaluation.

The :class:`SecurityGate` evaluates a :class:`SecurityReport` against
configurable :class:`SecurityThresholds` and returns a :class:`GateResult`.
"""

from __future__ import annotations

from codebot.security.models import GateResult, SecurityReport, SecurityThresholds


class SecurityGate:
    """Evaluates security scan reports against severity thresholds.

    Args:
        thresholds: Custom thresholds. Uses defaults if ``None``.
    """

    def __init__(self, thresholds: SecurityThresholds | None = None) -> None:
        self.thresholds = thresholds or SecurityThresholds()

    def evaluate(self, report: SecurityReport) -> GateResult:
        """Evaluate *report* summary against configured thresholds.

        Returns:
            A :class:`GateResult` indicating pass/fail with reason and
            optional warnings for medium/low threshold exceedances.
        """
        summary = report.summary

        # Secrets check (hard fail)
        if summary.secrets_count > 0 and self.thresholds.require_no_secrets:
            return GateResult(
                passed=False, reason="Hardcoded secrets detected"
            )

        # Critical findings check
        if summary.critical_count > self.thresholds.max_critical:
            return GateResult(
                passed=False,
                reason=(
                    f"CRITICAL findings ({summary.critical_count}) "
                    f"exceed threshold ({self.thresholds.max_critical})"
                ),
            )

        # High findings check
        if summary.high_count > self.thresholds.max_high:
            return GateResult(
                passed=False,
                reason=(
                    f"HIGH findings ({summary.high_count}) "
                    f"exceed threshold ({self.thresholds.max_high})"
                ),
            )

        # Warnings for medium/low (still passes)
        warnings: list[str] = []
        if summary.medium_count > self.thresholds.max_medium:
            warnings.append(
                f"MEDIUM findings ({summary.medium_count}) "
                f"exceed recommendation ({self.thresholds.max_medium})"
            )

        if summary.low_count > self.thresholds.max_low:
            warnings.append(
                f"LOW findings ({summary.low_count}) "
                f"exceed recommendation ({self.thresholds.max_low})"
            )

        return GateResult(passed=True, warnings=warnings)
