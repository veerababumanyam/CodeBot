"""Security configuration loaders.

Functions to load YAML-based security configuration files into their
corresponding Pydantic models.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from codebot.security.models import AllowlistConfig, SecurityThresholds

THRESHOLDS_PATH = "configs/security/thresholds.yaml"
ALLOWLIST_PATH = "configs/security/allowlist.yaml"
GITLEAKS_CONFIG_PATH = "configs/security/gitleaks.toml"


def load_thresholds(
    path: str = THRESHOLDS_PATH,
) -> SecurityThresholds:
    """Load security gate thresholds from a YAML file.

    Args:
        path: Path to the thresholds YAML file.

    Returns:
        Parsed :class:`SecurityThresholds` model.
    """
    with Path(path).open() as f:
        data = yaml.safe_load(f) or {}
    return SecurityThresholds(**data)


def load_allowlist(
    path: str = ALLOWLIST_PATH,
) -> AllowlistConfig:
    """Load dependency allowlist from a YAML file.

    Args:
        path: Path to the allowlist YAML file.

    Returns:
        Parsed :class:`AllowlistConfig` model.
    """
    with Path(path).open() as f:
        data = yaml.safe_load(f) or {}
    return AllowlistConfig(**data)
