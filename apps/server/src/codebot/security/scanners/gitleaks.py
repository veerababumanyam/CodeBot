"""Gitleaks secret detection scanner adapter.

Wraps the Gitleaks CLI to detect hardcoded secrets and normalizes
JSON output into :class:`ScanResult`.  All secrets are treated as
CRITICAL severity.
"""

from __future__ import annotations

import json

from codebot.db.models.security import Severity
from codebot.security.models import ScanFinding, ScanResult
from codebot.security.scanners.base import BaseScanner


class SecretScanner(BaseScanner):
    """Secret detection via Gitleaks CLI.

    All detected secrets are assigned :attr:`Severity.CRITICAL`.

    Args:
        config_path: Optional path to a custom gitleaks.toml config.
    """

    def __init__(self, config_path: str | None = None) -> None:
        self.config_path = config_path

    async def scan(self, project_path: str) -> ScanResult:
        """Run Gitleaks against *project_path* and return normalized findings."""
        cmd = [
            "gitleaks",
            "detect",
            "--source",
            project_path,
            "--report-format",
            "json",
            "--report-path",
            "/dev/stdout",
            "--no-git",
            "--no-banner",
        ]
        if self.config_path:
            cmd.extend(["--config", self.config_path])

        stdout, stderr, returncode = await self._run_cli(cmd, timeout=120)

        # returncode 0 = no leaks found
        if returncode == 0:
            return ScanResult(scanner="gitleaks")

        # returncode 1 = leaks found (parse JSON array)
        findings: list[ScanFinding] = []
        if returncode == 1 and stdout:
            leaks = json.loads(stdout)
            for leak in leaks:
                findings.append(
                    ScanFinding(
                        tool="gitleaks",
                        rule_id=leak.get("RuleID", ""),
                        severity=Severity.CRITICAL,
                        title=f"Secret detected: {leak.get('Description', '')}",
                        file_path=leak.get("File", ""),
                        line_start=leak.get("StartLine", 0),
                        line_end=leak.get("EndLine", 0),
                        code_snippet=leak.get("Match", "")[:200],
                        fix_recommendation=(
                            "Remove hardcoded secret. Use environment variables "
                            "or a secrets manager instead."
                        ),
                    )
                )
            return ScanResult(scanner="gitleaks", findings=findings)

        # returncode > 1 = actual error
        return ScanResult(
            scanner="gitleaks",
            errors=[f"Gitleaks error (exit {returncode}): {stderr}"],
        )
