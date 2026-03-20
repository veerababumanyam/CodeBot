"""Dependency allowlist validator.

Validates pip and npm dependency lists against a curated allowlist
to prevent hallucinated or malicious packages from being installed
in agent worktrees.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from codebot.security.models import AllowlistConfig

# Characters that start a version specifier or extras section
_VERSION_SPLIT_RE = re.compile(r"[=<>~!;\[\s]")


class AllowlistValidator:
    """Checks dependency lists against an approved package allowlist.

    Args:
        config: The allowlist configuration with approved package sets.
    """

    def __init__(self, config: AllowlistConfig) -> None:
        self.config = config

    async def validate_requirements(
        self, requirements_path: str
    ) -> list[str]:
        """Check requirements.txt packages against the Python allowlist.

        Args:
            requirements_path: Path to a requirements.txt file.

        Returns:
            List of violation description strings. Empty if all pass.
        """
        violations: list[str] = []
        allowed = {p.lower() for p in self.config.python_packages}
        text = Path(requirements_path).read_text()
        for line in text.splitlines():
            pkg_name = self._extract_package_name(line)
            if pkg_name is not None and pkg_name.lower() not in allowed:
                violations.append(
                    f"Package '{pkg_name}' not in Python allowlist"
                )
        return violations

    async def validate_package_json(
        self, pkg_json_path: str
    ) -> list[str]:
        """Check package.json dependencies against the npm allowlist.

        Args:
            pkg_json_path: Path to a package.json file.

        Returns:
            List of violation description strings. Empty if all pass.
        """
        violations: list[str] = []
        with Path(pkg_json_path).open() as f:
            data = json.load(f)
        for section in ("dependencies", "devDependencies"):
            for pkg_name in data.get(section, {}):
                if pkg_name not in self.config.npm_packages:
                    violations.append(
                        f"NPM package '{pkg_name}' not in allowlist"
                    )
        return violations

    def _extract_package_name(self, line: str) -> str | None:
        """Extract package name from a requirements.txt line.

        Handles version specifiers, extras, environment markers,
        comments, blank lines, and pip flags.

        Returns:
            The package name, or ``None`` if the line should be skipped.
        """
        stripped = line.strip()
        if not stripped:
            return None
        if stripped.startswith("#"):
            return None
        if stripped.startswith("-r") or stripped.startswith("--"):
            return None

        # Split on the first version/extras delimiter
        match = _VERSION_SPLIT_RE.search(stripped)
        if match:
            name = stripped[: match.start()].strip()
        else:
            name = stripped

        return name if name else None
