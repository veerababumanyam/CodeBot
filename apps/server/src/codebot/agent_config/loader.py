"""YAML agent configuration discovery and loading.

Discovers all *.yaml files in a directory (skipping _ prefixed files),
validates each against AgentConfig, and returns a registry of configs.
"""

from __future__ import annotations

import logging
from pathlib import Path

from agent_sdk.models.agent_config import AgentConfig, load_agent_config

logger = logging.getLogger(__name__)


class AgentConfigLoader:
    """Discovers and loads agent YAML configs from a directory.

    Usage::

        loader = AgentConfigLoader(Path("configs/agents"))
        configs = loader.load_all()
        orchestrator_config = configs["ORCHESTRATOR"]

    Attributes:
        configs: Read-only copy of loaded configs indexed by uppercase agent_type.
    """

    def __init__(self, config_dir: Path) -> None:
        """Initialize the loader with a configuration directory.

        Args:
            config_dir: Path to the directory containing agent YAML configs.
        """
        self._config_dir = config_dir
        self._configs: dict[str, AgentConfig] = {}

    @property
    def configs(self) -> dict[str, AgentConfig]:
        """Return a copy of loaded configs indexed by uppercase agent_type."""
        return dict(self._configs)

    def load_all(self) -> dict[str, AgentConfig]:
        """Load all YAML configs from the directory.

        Discovers *.yaml files, skips files prefixed with ``_`` (templates),
        validates each against AgentConfig, and indexes by uppercase agent_type.

        Returns:
            Dict mapping uppercase agent_type to validated AgentConfig.

        Raises:
            Exception: Re-raised from load_agent_config on validation failure.
        """
        self._configs = {}
        if not self._config_dir.is_dir():
            logger.warning("Config directory does not exist: %s", self._config_dir)
            return self._configs

        for yaml_path in sorted(self._config_dir.glob("*.yaml")):
            if yaml_path.name.startswith("_"):
                logger.debug("Skipping template: %s", yaml_path.name)
                continue
            try:
                config = load_agent_config(yaml_path)
                key = config.agent_type.upper()
                self._configs[key] = config
                logger.info("Loaded agent config: %s from %s", key, yaml_path.name)
            except Exception:
                logger.exception("Failed to load agent config: %s", yaml_path)
                raise
        return self._configs

    def get(self, agent_type: str) -> AgentConfig | None:
        """Look up a config by agent type (case-insensitive).

        Args:
            agent_type: The agent type string to look up.

        Returns:
            The matching AgentConfig, or None if not found.
        """
        return self._configs.get(agent_type.upper())


def load_all_agent_configs(config_dir: Path) -> dict[str, AgentConfig]:
    """Convenience function: discover and load all agent configs.

    Args:
        config_dir: Path to the directory containing agent YAML configs.

    Returns:
        Dict mapping uppercase agent_type to validated AgentConfig.
    """
    loader = AgentConfigLoader(config_dir)
    return loader.load_all()
