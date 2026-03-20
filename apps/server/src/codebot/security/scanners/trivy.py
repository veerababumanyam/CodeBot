"""Trivy dependency/filesystem scanner adapter.

Wraps the Trivy CLI to scan for vulnerabilities, secrets, and
misconfigurations.  Normalizes JSON output into :class:`ScanResult`.
"""

from __future__ import annotations

import json

from codebot.db.models.security import Severity
from codebot.security.models import ScanFinding, ScanResult
from codebot.security.scanners.base import BaseScanner


class DependencyScanner(BaseScanner):
    """Dependency and filesystem vulnerability scanning via Trivy CLI.

    Scans for known CVEs in dependencies, embedded secrets, and
    infrastructure misconfigurations.
    """

    async def scan(self, project_path: str) -> ScanResult:
        """Run Trivy against *project_path* and return normalized findings."""
        cmd = [
            "trivy",
            "filesystem",
            "--format",
            "json",
            "--scanners",
            "vuln,secret,misconfig",
            "--severity",
            "CRITICAL,HIGH,MEDIUM",
            "--skip-dirs",
            "node_modules,.git,.worktrees",
            project_path,
        ]
        stdout, stderr, returncode = await self._run_cli(cmd, timeout=600)

        if returncode != 0 and not stdout:
            return ScanResult(
                scanner="trivy",
                errors=[f"Trivy error (exit {returncode}): {stderr}"],
            )

        data = json.loads(stdout)
        findings: list[ScanFinding] = []
        for target in data.get("Results", []):
            # Trivy returns null instead of [] when no vulns found
            vulns = target.get("Vulnerabilities") or []
            for vuln in vulns:
                pkg_name = vuln.get("PkgName", "")
                vuln_title = vuln.get("Title", vuln.get("VulnerabilityID", ""))
                title = f"{pkg_name}: {vuln_title}" if pkg_name else vuln_title

                fixed_version = vuln.get("FixedVersion", "")
                fix_rec = (
                    f"Update to {fixed_version}"
                    if fixed_version
                    else "No fix available yet"
                )

                findings.append(
                    ScanFinding(
                        tool="trivy",
                        rule_id=vuln.get("VulnerabilityID", ""),
                        severity=Severity(
                            vuln.get("Severity", "MEDIUM").upper()
                        ),
                        title=title,
                        description=vuln.get("Description", ""),
                        file_path=target.get("Target", ""),
                        cve_id=vuln.get("VulnerabilityID"),
                        fix_recommendation=fix_rec,
                    )
                )
        return ScanResult(scanner="trivy", findings=findings)
