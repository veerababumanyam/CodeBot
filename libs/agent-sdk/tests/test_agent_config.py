"""Tests for AgentConfig YAML validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from agent_sdk.models.agent_config import (
    AgentConfig,
    ContextTiersConfig,
    RetryPolicyConfig,
    load_agent_config,
)


VALID_CONFIG_YAML = """\
orchestrator:
  model: claude-opus-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 8192
  temperature: 0.3
  tools:
    - graph_executor
    - task_scheduler
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 20000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 2.0
    max_delay_seconds: 60.0
    exponential_base: 2.0
    recovery_strategy: escalate
  timeout: 600
  system_prompt: "You are an orchestrator agent."
"""


class TestLoadValidYamlConfig:
    def test_load_valid_yaml_config(self) -> None:
        """Valid YAML with all fields loads to AgentConfig."""
        raw = yaml.safe_load(VALID_CONFIG_YAML)
        name = next(iter(raw))
        data = raw[name]
        data["agent_type"] = name.upper()
        config = AgentConfig.model_validate(data)
        assert config.agent_type == "ORCHESTRATOR"
        assert config.model == "claude-opus-4"
        assert config.fallback_model == "gpt-4.1"
        assert config.provider == "anthropic"
        assert config.max_tokens == 8192
        assert config.temperature == pytest.approx(0.3)
        assert "graph_executor" in config.tools
        assert config.context_tiers.l0 == 2000
        assert config.retry_policy.max_retries == 3
        assert config.retry_policy.recovery_strategy == "escalate"
        assert config.timeout == 600


class TestConfigValidation:
    def test_config_validates_agent_type(self) -> None:
        """Unknown agent type raises ValidationError."""
        with pytest.raises(ValidationError):
            AgentConfig(
                agent_type="NONEXISTENT_AGENT_TYPE",
                model="test-model",
            )

    def test_config_rejects_extra_keys(self) -> None:
        """YAML with unknown key raises ValidationError (extra='forbid')."""
        with pytest.raises(ValidationError):
            AgentConfig(
                agent_type="PLANNER",
                model="test-model",
                unknown_key="should_fail",  # type: ignore[call-arg]
            )

    def test_config_default_values(self) -> None:
        """Missing optional fields get defaults."""
        config = AgentConfig(agent_type="PLANNER", model="claude-opus-4")
        assert config.temperature == pytest.approx(0.7)
        assert config.max_tokens == 4096
        assert config.retry_policy.max_retries == 3
        assert config.retry_policy.recovery_strategy == "retry_with_modified_prompt"
        assert config.context_tiers.l0 == 2000
        assert config.timeout == 600
        assert config.fallback_model is None
        assert config.tools == []
        assert config.settings == {}


class TestRetryPolicyValidation:
    def test_max_retries_too_high(self) -> None:
        """max_retries > 10 raises ValidationError."""
        with pytest.raises(ValidationError):
            RetryPolicyConfig(max_retries=11)

    def test_recovery_strategy_invalid_pattern(self) -> None:
        """recovery_strategy must match allowed patterns."""
        with pytest.raises(ValidationError):
            RetryPolicyConfig(recovery_strategy="invalid_strategy")


class TestContextTiersValidation:
    def test_negative_token_values_rejected(self) -> None:
        """Negative token values raise ValidationError."""
        with pytest.raises(ValidationError):
            ContextTiersConfig(l0=-1)


class TestSystemPromptOptional:
    def test_system_prompt_and_file_both_optional(self) -> None:
        """Config with neither system_prompt nor system_prompt_file is valid."""
        config = AgentConfig(agent_type="PLANNER", model="test-model")
        assert config.system_prompt is None
        assert config.system_prompt_file is None


class TestLoadAgentConfigFromFile:
    def test_load_agent_config_from_file(self, tmp_path: Path) -> None:
        """load_agent_config(Path) reads YAML, returns AgentConfig."""
        config_file = tmp_path / "planner.yaml"
        config_file.write_text(
            """\
planner:
  model: claude-opus-4
  temperature: 0.5
  tools:
    - file_reader
    - code_writer
"""
        )
        config = load_agent_config(config_file)
        assert config.agent_type == "PLANNER"
        assert config.model == "claude-opus-4"
        assert config.temperature == pytest.approx(0.5)
        assert "file_reader" in config.tools


class TestFrozenConfig:
    def test_frozen_config(self) -> None:
        """Assigning to config field raises TypeError (frozen=True)."""
        config = AgentConfig(agent_type="PLANNER", model="test-model")
        with pytest.raises(ValidationError):
            config.model = "different-model"  # type: ignore[misc]
