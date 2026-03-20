"""SecurityOrchestrator -- parallel fan-out of security scanners.

Coordinates :class:`SASTRunner`, :class:`DependencyScanner`, and
:class:`SecretScanner` via :func:`asyncio.TaskGroup`, aggregates
their findings, deduplicates, builds a summary, and evaluates
the :class:`SecurityGate`.

This is the central entry point for security scanning.  It is called
after every code generation step (SECP-05) -- not just at the S6
quality gate.  Agents and pipeline stages invoke
``orchestrator.scan(project_path)`` and receive a complete
:class:`SecurityReport` with gate pass/fail.
"""

from __future__ import annotations

import asyncio
import logging
import time

from codebot.db.models.security import Severity
from codebot.security.gate import SecurityGate
from codebot.security.models import (
    ScanError,
    ScanFinding,
    ScanResult,
    ScanSummary,
    SecurityReport,
    SecurityThresholds,
)
from codebot.security.scanners.base import BaseScanner
from codebot.security.scanners.gitleaks import SecretScanner
from codebot.security.scanners.semgrep import SASTRunner
from codebot.security.scanners.trivy import DependencyScanner

logger = logging.getLogger(__name__)


class SecurityOrchestrator:
    """Run all security scanners in parallel and produce a unified report.

    Args:
        thresholds: Custom gate thresholds.  Uses defaults if ``None``.
        sast: Override the SAST scanner (useful for testing).
        deps: Override the dependency scanner (useful for testing).
        secrets: Override the secret scanner (useful for testing).
        compliance: Optional SOC 2 compliance checker (wired in Plan 04).
    """

    def __init__(
        self,
        thresholds: SecurityThresholds | None = None,
        sast: BaseScanner | None = None,
        deps: BaseScanner | None = None,
        secrets: BaseScanner | None = None,
        compliance: BaseScanner | None = None,
    ) -> None:
        self.sast = sast or SASTRunner()
        self.deps = deps or DependencyScanner()
        self.secrets = secrets or SecretScanner()
        self.compliance = compliance  # Optional SOC2ComplianceChecker
        self.gate = SecurityGate(thresholds)

    async def scan(self, project_path: str) -> SecurityReport:
        """Run all scanners in parallel and return a complete security report.

        Args:
            project_path: Root path of the project to scan.

        Returns:
            A :class:`SecurityReport` with deduplicated findings,
            severity summary, and gate evaluation result.
        """
        start = time.monotonic()
        results: list[ScanResult] = []
        errors: list[ScanError] = []

        # Fan-out: run all scanners in parallel via TaskGroup
        async with asyncio.TaskGroup() as tg:
            sast_task = tg.create_task(
                self._safe_scan("sast", self.sast, project_path)
            )
            deps_task = tg.create_task(
                self._safe_scan("deps", self.deps, project_path)
            )
            secrets_task = tg.create_task(
                self._safe_scan("secrets", self.secrets, project_path)
            )
            compliance_task = (
                tg.create_task(
                    self._safe_scan("compliance", self.compliance, project_path)
                )
                if self.compliance
                else None
            )

        # Collect results from completed tasks
        scan_tasks: list[tuple[str, asyncio.Task[ScanResult | None]]] = [
            ("sast", sast_task),
            ("deps", deps_task),
            ("secrets", secrets_task),
        ]
        if compliance_task is not None:
            scan_tasks.append(("compliance", compliance_task))

        for name, task in scan_tasks:
            result = task.result()
            if result is not None:
                results.append(result)
                for err in result.errors:
                    errors.append(ScanError(scanner=name, error=err))

        # Aggregate all findings
        all_findings: list[ScanFinding] = []
        for r in results:
            all_findings.extend(r.findings)

        # Deduplicate and summarize
        deduplicated = self._deduplicate(all_findings)
        summary = self._build_summary(deduplicated)

        report = SecurityReport(
            findings=deduplicated,
            errors=errors,
            summary=summary,
        )

        # Evaluate quality gate
        report.gate_result = self.gate.evaluate(report)

        duration_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "Security scan completed in %dms: %d findings, gate=%s",
            duration_ms,
            summary.total_findings,
            "PASS" if report.gate_result.passed else "FAIL",
        )
        return report

    async def _safe_scan(
        self, name: str, scanner: BaseScanner, project_path: str
    ) -> ScanResult | None:
        """Run a single scanner, catching any exceptions.

        If the scanner raises, returns a :class:`ScanResult` with an error
        entry rather than propagating the exception (which would cancel
        sibling tasks in the TaskGroup).

        Args:
            name: Human-readable scanner name for error reporting.
            scanner: The scanner instance to invoke.
            project_path: Root path of the project to scan.

        Returns:
            The :class:`ScanResult`, or a result with error info on failure.
        """
        try:
            return await scanner.scan(project_path)
        except Exception:
            logger.exception("Scanner '%s' failed", name)
            return ScanResult(
                scanner=name,
                errors=[f"Scanner '{name}' raised an exception"],
            )

    def _deduplicate(self, findings: list[ScanFinding]) -> list[ScanFinding]:
        """Remove duplicate findings by (tool, rule_id, file_path, line_start).

        Preserves first occurrence order.
        """
        seen: set[tuple[str, str, str, int]] = set()
        unique: list[ScanFinding] = []
        for f in findings:
            key = (f.tool, f.rule_id, f.file_path, f.line_start)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _build_summary(self, findings: list[ScanFinding]) -> ScanSummary:
        """Count findings by severity and detect secrets.

        Secrets are identified by ``tool == "gitleaks"``.
        """
        counts: dict[Severity, int] = {s: 0 for s in Severity}
        secrets_count = 0

        for f in findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
            if f.tool == "gitleaks":
                secrets_count += 1

        return ScanSummary(
            total_findings=len(findings),
            critical_count=counts[Severity.CRITICAL],
            high_count=counts[Severity.HIGH],
            medium_count=counts[Severity.MEDIUM],
            low_count=counts[Severity.LOW],
            info_count=counts[Severity.INFO],
            secrets_count=secrets_count,
        )
