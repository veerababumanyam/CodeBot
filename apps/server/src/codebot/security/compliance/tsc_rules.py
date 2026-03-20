"""TSC rules loader -- reads compliance rules from YAML configuration.

Each rule defines a check type (``pattern`` for regex/string matching,
``file_exists`` for file-glob existence checks) and the TSC category it
maps to.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import yaml

from codebot.security.compliance.models import TrustServiceCategory


@dataclass(slots=True, kw_only=True)
class TSCRule:
    """A single Trust Service Criteria rule loaded from YAML.

    Attributes:
        id: Unique rule identifier (e.g. ``CC6-001``).
        category: TSC category the rule maps to.
        description: Human-readable description.
        check_type: ``"pattern"`` or ``"file_exists"``.
        patterns: String patterns to search for in source files (check_type=pattern).
        file_patterns: Glob patterns for file existence checks (check_type=file_exists).
        severity: Finding severity when rule is violated (``HIGH`` / ``MEDIUM`` / ``LOW``).
    """

    id: str
    category: TrustServiceCategory
    description: str
    check_type: str = "pattern"
    patterns: list[str] = field(default_factory=list)
    file_patterns: list[str] = field(default_factory=list)
    severity: str = "MEDIUM"


class TSCRulesLoader:
    """Load TSC rules from a YAML configuration file.

    Args:
        config_path: Absolute or relative path to the YAML file.
    """

    def __init__(self, config_path: str) -> None:
        self.config_path = config_path

    def load(self) -> list[TSCRule]:
        """Parse the YAML file and return a list of :class:`TSCRule`.

        Returns:
            Parsed rules ready for checker consumption.

        Raises:
            FileNotFoundError: If the config file does not exist.
            yaml.YAMLError: If the YAML is malformed.
        """
        with open(self.config_path) as f:
            data = yaml.safe_load(f)

        rules: list[TSCRule] = []
        for entry in data.get("rules", []):
            rules.append(
                TSCRule(
                    id=entry["id"],
                    category=TrustServiceCategory(entry["category"]),
                    description=entry.get("description", ""),
                    check_type=entry.get("check_type", "pattern"),
                    patterns=entry.get("patterns", []),
                    file_patterns=entry.get("file_patterns", []),
                    severity=entry.get("severity", "MEDIUM"),
                )
            )
        return rules
