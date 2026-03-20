"""SOC 2 compliance checker -- file-system + pattern-based TSC evaluation.

Scans a project directory for compliance with Trust Service Criteria
defined in a YAML configuration file.  Produces :class:`ScanResult`
objects compatible with the :class:`SecurityOrchestrator` pipeline.
"""

from __future__ import annotations

import fnmatch
import logging
from pathlib import Path

from codebot.db.models.security import Severity
from codebot.security.compliance.models import (
    ComplianceCheckResult,
    ComplianceFramework,
    ComplianceReport,
)
from codebot.security.compliance.tsc_rules import TSCRule, TSCRulesLoader
from codebot.security.models import ScanFinding, ScanResult
from codebot.security.scanners.base import BaseScanner

logger = logging.getLogger(__name__)

# Map YAML severity strings to ORM Severity enum
_SEVERITY_MAP: dict[str, Severity] = {
    "CRITICAL": Severity.CRITICAL,
    "HIGH": Severity.HIGH,
    "MEDIUM": Severity.MEDIUM,
    "LOW": Severity.LOW,
    "INFO": Severity.INFO,
}

# Skip these directories when walking project files
_SKIP_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".eggs",
    }
)

# Only scan text files with these extensions
_TEXT_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".java",
        ".go",
        ".rs",
        ".yaml",
        ".yml",
        ".toml",
        ".json",
        ".sql",
        ".sh",
        ".md",
        ".cfg",
        ".ini",
        ".env",
        ".html",
        ".css",
    }
)


class SOC2ComplianceChecker(BaseScanner):
    """Evaluate a project against SOC 2 Trust Service Criteria.

    Reads TSC rule definitions from a YAML config file and scans the
    project directory for files and patterns matching each category.
    Produces :class:`ScanFinding` objects with ``tool="soc2-compliance"``
    for any violations found.

    Args:
        config_path: Path to the SOC 2 rules YAML file.
    """

    def __init__(self, config_path: str) -> None:
        self.config_path = config_path
        loader = TSCRulesLoader(config_path)
        self.rules: list[TSCRule] = loader.load()

    async def scan(self, project_path: str) -> ScanResult:
        """Run all TSC rules against *project_path*.

        Args:
            project_path: Root directory of the project to evaluate.

        Returns:
            A :class:`ScanResult` with ``scanner="soc2-compliance"``.
            Each failed rule produces a :class:`ScanFinding`.
        """
        findings: list[ScanFinding] = []
        check_results: list[ComplianceCheckResult] = []

        # Collect all scannable text files once
        project = Path(project_path)
        text_files = self._collect_text_files(project)
        all_files = self._collect_all_files(project)

        for rule in self.rules:
            passed, evidence = self._evaluate_rule(rule, project, text_files, all_files)
            check_results.append(
                ComplianceCheckResult(
                    category=rule.category,
                    rule_id=rule.id,
                    description=rule.description,
                    passed=passed,
                    evidence=evidence,
                )
            )

            if not passed:
                findings.append(
                    ScanFinding(
                        tool="soc2-compliance",
                        rule_id=rule.id,
                        severity=_SEVERITY_MAP.get(rule.severity, Severity.MEDIUM),
                        title=f"Compliance violation: {rule.description}",
                        description=evidence,
                        fix_recommendation=(
                            f"Add {rule.description.lower()} to satisfy TSC {rule.category.value}"
                        ),
                    )
                )

        logger.info(
            "SOC 2 compliance check: %d rules, %d violations",
            len(self.rules),
            len(findings),
        )
        return ScanResult(
            scanner="soc2-compliance",
            findings=findings,
        )

    def get_compliance_report(self, scan_result: ScanResult) -> ComplianceReport:
        """Build a :class:`ComplianceReport` from a previous scan result.

        This is a convenience method for callers that need the structured
        compliance report rather than the raw :class:`ScanResult`.

        Args:
            scan_result: Result from a prior :meth:`scan` call.

        Returns:
            Structured compliance report with per-category results.
        """
        violated_rules = {f.rule_id for f in scan_result.findings}
        results: list[ComplianceCheckResult] = []
        for rule in self.rules:
            results.append(
                ComplianceCheckResult(
                    category=rule.category,
                    rule_id=rule.id,
                    description=rule.description,
                    passed=rule.id not in violated_rules,
                    evidence=""
                    if rule.id not in violated_rules
                    else (f"Missing: {rule.description}"),
                )
            )
        return ComplianceReport(
            framework=ComplianceFramework.SOC2,
            results=results,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_text_files(self, project: Path) -> list[Path]:
        """Walk *project* and return paths of scannable text files."""
        result: list[Path] = []
        for path in project.rglob("*"):
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path.is_file() and path.suffix in _TEXT_EXTENSIONS:
                result.append(path)
        return result

    def _collect_all_files(self, project: Path) -> list[Path]:
        """Walk *project* and return all file paths (for glob matching)."""
        result: list[Path] = []
        for path in project.rglob("*"):
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path.is_file():
                result.append(path)
        return result

    def _evaluate_rule(
        self,
        rule: TSCRule,
        project: Path,
        text_files: list[Path],
        all_files: list[Path],
    ) -> tuple[bool, str]:
        """Evaluate a single TSC rule.

        Returns:
            ``(passed, evidence)`` tuple.
        """
        if rule.check_type == "pattern":
            return self._check_patterns(rule, text_files)
        elif rule.check_type == "file_exists":
            return self._check_file_exists(rule, project, all_files)
        else:
            logger.warning("Unknown check_type '%s' for rule %s", rule.check_type, rule.id)
            return True, f"Skipped: unknown check_type '{rule.check_type}'"

    def _check_patterns(self, rule: TSCRule, text_files: list[Path]) -> tuple[bool, str]:
        """Check whether any pattern from *rule.patterns* appears in source files.

        Returns ``(True, evidence)`` if at least one pattern is found.
        """
        for fpath in text_files:
            try:
                content = fpath.read_text(errors="replace")
            except OSError:
                continue
            for pattern in rule.patterns:
                if pattern in content:
                    return True, f"Found '{pattern}' in {fpath.name}"
        return False, f"None of {rule.patterns} found in project source files"

    def _check_file_exists(
        self, rule: TSCRule, project: Path, all_files: list[Path]
    ) -> tuple[bool, str]:
        """Check whether files matching *rule.file_patterns* exist.

        Uses :func:`fnmatch.fnmatch` against relative paths.
        """
        for fpath in all_files:
            rel = str(fpath.relative_to(project))
            for glob_pattern in rule.file_patterns:
                # Support ** by checking both direct fnmatch and path parts
                if fnmatch.fnmatch(rel, glob_pattern):
                    return True, f"Found matching file: {rel}"
                # Handle **/name/** style patterns
                parts = glob_pattern.split("**")
                if len(parts) == 2:
                    # Simple ** at start: match if suffix matches
                    suffix = parts[1].lstrip("/")
                    if suffix and fnmatch.fnmatch(rel, f"*{suffix}"):
                        return True, f"Found matching file: {rel}"
                    # If just **/dirname/**, check if dirname appears in path
                    dirname = suffix.strip("/*")
                    if dirname and dirname in rel:
                        return True, f"Found matching path: {rel}"
        return False, f"No files matching {rule.file_patterns} found"
