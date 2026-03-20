"""Semgrep SAST scanner adapter.

Wraps the Semgrep CLI to run static analysis and normalizes JSON
output into :class:`ScanResult`.
"""

from __future__ import annotations

import json

from codebot.db.models.security import Severity
from codebot.security.models import ScanFinding, ScanResult
from codebot.security.scanners.base import BaseScanner


class SASTRunner(BaseScanner):
    """Static analysis via Semgrep CLI.

    Runs Semgrep with OWASP/CWE rule packs and optionally a custom
    rules directory.  Normalizes JSON output into ScanFindings.
    """

    DEFAULT_CONFIGS = [
        "p/security-audit",
        "p/owasp-top-ten",
        "p/cwe-top-25",
    ]

    def __init__(self, custom_rules_dir: str | None = None) -> None:
        self.custom_rules_dir = custom_rules_dir

    async def scan(self, project_path: str) -> ScanResult:
        """Run Semgrep against *project_path* and return normalized findings."""
        cmd = ["semgrep", "scan", "--json", "--no-git-ignore"]
        for config in self.DEFAULT_CONFIGS:
            cmd.extend(["--config", config])
        if self.custom_rules_dir:
            cmd.extend(["--config", self.custom_rules_dir])
        cmd.append(project_path)

        stdout, stderr, returncode = await self._run_cli(cmd, timeout=300)

        if returncode >= 2:
            return ScanResult(
                scanner="semgrep",
                errors=[f"Semgrep error (exit {returncode}): {stderr}"],
            )

        # returncode 0 = no findings, 1 = findings found (both valid JSON)
        data = json.loads(stdout)
        findings: list[ScanFinding] = []
        for result in data.get("results", []):
            extra = result.get("extra", {})
            metadata = extra.get("metadata", {})
            findings.append(
                ScanFinding(
                    tool="semgrep",
                    rule_id=result.get("check_id", ""),
                    severity=self._map_severity(extra.get("severity", "INFO")),
                    title=extra.get("message", ""),
                    file_path=result.get("path", ""),
                    line_start=result.get("start", {}).get("line", 0),
                    line_end=result.get("end", {}).get("line", 0),
                    code_snippet=str(extra.get("lines", ""))[:500],
                    cwe=metadata.get("cwe", []),
                    fix_recommendation=extra.get("fix", ""),
                )
            )
        return ScanResult(scanner="semgrep", findings=findings)

    def _map_severity(self, semgrep_severity: str) -> Severity:
        """Map Semgrep severity strings to the shared Severity enum."""
        mapping = {
            "ERROR": Severity.HIGH,
            "WARNING": Severity.MEDIUM,
            "INFO": Severity.LOW,
        }
        return mapping.get(semgrep_severity, Severity.INFO)
