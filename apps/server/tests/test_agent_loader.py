"""Tests for agent configuration loading and discovery.

Tests cover:
- Loading the orchestrator reference config
- Skipping _schema.yaml template files
- load_all returns dict[str, AgentConfig]
- Nonexistent directory returns empty dict
- Invalid YAML raises validation error
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_sdk.models.agent_config import AgentConfig
from codebot.agent_config.loader import AgentConfigLoader, load_all_agent_configs

# Resolve the configs/agents/ directory relative to the repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]  # apps/server/tests/ -> repo root
_CONFIGS_DIR = _REPO_ROOT / "configs" / "agents"


def test_load_orchestrator_config() -> None:
    """Load configs/agents/, verify ORCHESTRATOR key, model, and recovery strategy."""
    loader = AgentConfigLoader(_CONFIGS_DIR)
    configs = loader.load_all()
    assert "ORCHESTRATOR" in configs
    config = configs["ORCHESTRATOR"]
    assert config.model == "claude-opus-4"
    assert config.retry_policy.recovery_strategy == "escalate"


def test_skip_schema_template() -> None:
    """_schema.yaml prefixed with _ is NOT loaded into configs dict."""
    loader = AgentConfigLoader(_CONFIGS_DIR)
    configs = loader.load_all()
    # _schema.yaml should be skipped; only orchestrator.yaml should be loaded
    for key in configs:
        assert key != "_TEMPLATE", "Template file should have been skipped"
    # Verify _schema.yaml exists on disk but was not loaded
    assert (_CONFIGS_DIR / "_schema.yaml").exists()


def test_load_all_returns_dict() -> None:
    """Result is dict[str, AgentConfig] with at least 1 entry."""
    configs = load_all_agent_configs(_CONFIGS_DIR)
    assert isinstance(configs, dict)
    assert len(configs) >= 1
    for key, val in configs.items():
        assert isinstance(key, str)
        assert isinstance(val, AgentConfig)


def test_nonexistent_dir_returns_empty() -> None:
    """Loader with nonexistent path returns empty dict."""
    loader = AgentConfigLoader(Path("/nonexistent/path/to/configs"))
    configs = loader.load_all()
    assert configs == {}


def test_invalid_yaml_raises(tmp_path: Path) -> None:
    """Create a tmp YAML with invalid agent_type, verify it raises."""
    invalid_yaml = tmp_path / "bad_agent.yaml"
    invalid_yaml.write_text(
        "bad_agent:\n"
        "  agent_type: NONEXISTENT_TYPE\n"
        "  model: some-model\n"
    )
    loader = AgentConfigLoader(tmp_path)
    with pytest.raises((ValueError, Exception)):
        loader.load_all()
