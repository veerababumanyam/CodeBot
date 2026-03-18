"""Tests for LLM YAML configuration loading and provider registry."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from codebot.llm.config import (
    BudgetConfig,
    FallbackConfig,
    LLMConfig,
    LLMSettings,
    ProviderConfig,
)
from codebot.llm.exceptions import ModelNotFoundError
from codebot.llm.providers import ProviderHealth, ProviderRegistry
from codebot.llm.schemas import RoutingRule


# ── Fixtures ───────────────────────────────────────────────────────────────

VALID_YAML = dedent("""\
    providers:
      - model_name: "claude-opus"
        litellm_model: "anthropic/claude-opus-4"
        api_key_env: "ANTHROPIC_API_KEY"
        enabled: true

      - model_name: "claude-sonnet"
        litellm_model: "anthropic/claude-sonnet-4"
        api_key_env: "ANTHROPIC_API_KEY"
        enabled: true

      - model_name: "gpt-4o"
        litellm_model: "openai/gpt-4o"
        api_key_env: "OPENAI_API_KEY"
        enabled: true

      - model_name: "ollama-llama"
        litellm_model: "ollama/llama3.1:70b"
        api_base: "http://localhost:11434"
        enabled: true

    routing_table:
      ORCHESTRATION:
        primary_model: "claude-opus"
        fallback_models: ["gpt-4o"]
        reason: "Complex planning"
      CODE_GENERATION:
        primary_model: "claude-sonnet"
        fallback_models: ["gpt-4o"]
        reason: "Fast code generation"
      SIMPLE_TRANSFORM:
        primary_model: "claude-sonnet"
        fallback_models: ["ollama-llama"]
        reason: "Fast transformations"

    budget:
      global_budget_usd: 50.0
      warn_threshold: 0.8
      halt_threshold: 0.95
      agent_budgets: {}

    fallback:
      num_retries: 3
      timeout_seconds: 60
      cooldown_seconds: 300

    settings:
      default_temperature: 0.7
      default_max_tokens: 4096
      enable_streaming: true
      enable_cost_tracking: true
""")


AIR_GAPPED_YAML = dedent("""\
    providers:
      - model_name: "claude-opus"
        litellm_model: "anthropic/claude-opus-4"
        api_key_env: "ANTHROPIC_API_KEY"
        enabled: false

      - model_name: "gpt-4o"
        litellm_model: "openai/gpt-4o"
        api_key_env: "OPENAI_API_KEY"
        enabled: false

      - model_name: "ollama-llama"
        litellm_model: "ollama/llama3.1:70b"
        api_base: "http://localhost:11434"
        enabled: true

    routing_table:
      ORCHESTRATION:
        primary_model: "ollama-llama"
        fallback_models: []
        reason: "Only self-hosted available"

    budget:
      global_budget_usd: 0.0
      warn_threshold: 0.8
      halt_threshold: 0.95
      agent_budgets: {}

    fallback:
      num_retries: 3
      timeout_seconds: 60
      cooldown_seconds: 300

    settings:
      default_temperature: 0.7
      default_max_tokens: 4096
      enable_streaming: false
      enable_cost_tracking: false
""")


@pytest.fixture
def valid_yaml_path(tmp_path: Path) -> Path:
    """Write a valid YAML config and return its path."""
    p = tmp_path / "llm.yaml"
    p.write_text(VALID_YAML)
    return p


@pytest.fixture
def air_gapped_yaml_path(tmp_path: Path) -> Path:
    """Write an air-gapped YAML config and return its path."""
    p = tmp_path / "llm-airgap.yaml"
    p.write_text(AIR_GAPPED_YAML)
    return p


@pytest.fixture
def config(valid_yaml_path: Path) -> LLMConfig:
    """Load a valid LLMConfig from YAML."""
    return LLMConfig.from_yaml(valid_yaml_path)


@pytest.fixture
def registry(config: LLMConfig) -> ProviderRegistry:
    """Create a ProviderRegistry from a valid config."""
    return ProviderRegistry(config)


# ── ProviderConfig ─────────────────────────────────────────────────────────

class TestProviderConfig:
    """ProviderConfig validates model definitions."""

    def test_basic_construction(self) -> None:
        pc = ProviderConfig(model_name="gpt-4o", litellm_model="openai/gpt-4o")
        assert pc.model_name == "gpt-4o"
        assert pc.litellm_model == "openai/gpt-4o"
        assert pc.api_key_env is None
        assert pc.api_base is None
        assert pc.enabled is True

    def test_with_api_key(self) -> None:
        pc = ProviderConfig(
            model_name="claude-opus",
            litellm_model="anthropic/claude-opus-4",
            api_key_env="ANTHROPIC_API_KEY",
        )
        assert pc.api_key_env == "ANTHROPIC_API_KEY"

    def test_with_api_base(self) -> None:
        pc = ProviderConfig(
            model_name="ollama-llama",
            litellm_model="ollama/llama3.1:70b",
            api_base="http://localhost:11434",
        )
        assert pc.api_base == "http://localhost:11434"


# ── BudgetConfig ───────────────────────────────────────────────────────────

class TestBudgetConfig:
    """BudgetConfig validates budget limits and thresholds."""

    def test_defaults(self) -> None:
        bc = BudgetConfig()
        assert bc.global_budget_usd == 50.0
        assert bc.warn_threshold == 0.8
        assert bc.halt_threshold == 0.95
        assert bc.agent_budgets == {}

    def test_custom_values(self) -> None:
        bc = BudgetConfig(global_budget_usd=100.0, warn_threshold=0.7, agent_budgets={"agent-1": 10.0})
        assert bc.global_budget_usd == 100.0
        assert bc.warn_threshold == 0.7
        assert bc.agent_budgets == {"agent-1": 10.0}


# ── LLMConfig loading ─────────────────────────────────────────────────────

class TestLLMConfigLoading:
    """LLMConfig.from_yaml() loads and validates YAML configuration."""

    def test_loads_valid_yaml(self, config: LLMConfig) -> None:
        assert len(config.providers) == 4
        assert config.providers[0].model_name == "claude-opus"

    def test_routing_table_populated(self, config: LLMConfig) -> None:
        assert "ORCHESTRATION" in config.routing_table
        assert "CODE_GENERATION" in config.routing_table
        rule = config.routing_table["ORCHESTRATION"]
        assert isinstance(rule, RoutingRule)
        assert rule.primary_model == "claude-opus"

    def test_budget_loaded(self, config: LLMConfig) -> None:
        assert config.budget.global_budget_usd == 50.0
        assert config.budget.warn_threshold == 0.8

    def test_fallback_loaded(self, config: LLMConfig) -> None:
        assert config.fallback.num_retries == 3
        assert config.fallback.timeout_seconds == 60
        assert config.fallback.cooldown_seconds == 300

    def test_settings_loaded(self, config: LLMConfig) -> None:
        assert config.settings.default_temperature == 0.7
        assert config.settings.default_max_tokens == 4096
        assert config.settings.enable_streaming is True

    def test_air_gapped_config(self, air_gapped_yaml_path: Path) -> None:
        cfg = LLMConfig.from_yaml(air_gapped_yaml_path)
        enabled = cfg.get_enabled_providers()
        assert len(enabled) == 1
        assert enabled[0].model_name == "ollama-llama"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            LLMConfig.from_yaml(tmp_path / "nonexistent.yaml")

    def test_invalid_yaml_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.yaml"
        p.write_text("not: [valid: yaml: {broken")
        with pytest.raises(ValueError, match="Invalid"):
            LLMConfig.from_yaml(p)

    def test_get_enabled_providers(self, config: LLMConfig) -> None:
        enabled = config.get_enabled_providers()
        assert all(p.enabled for p in enabled)
        assert len(enabled) == 4

    def test_get_routing_rule_known(self, config: LLMConfig) -> None:
        rule = config.get_routing_rule("ORCHESTRATION")
        assert rule.primary_model == "claude-opus"

    def test_get_routing_rule_unknown(self, config: LLMConfig) -> None:
        rule = config.get_routing_rule("NONEXISTENT_TASK")
        # Should return a default rule using first enabled provider
        assert rule.primary_model == config.get_enabled_providers()[0].model_name


# ── ProviderRegistry ───────────────────────────────────────────────────────

class TestProviderRegistry:
    """ProviderRegistry manages providers, health, and LiteLLM model list."""

    def test_get_enabled_providers(self, registry: ProviderRegistry) -> None:
        enabled = registry.get_enabled_providers()
        assert len(enabled) == 4
        assert all(p.enabled for p in enabled)

    def test_get_provider_exists(self, registry: ProviderRegistry) -> None:
        provider = registry.get_provider("claude-opus")
        assert provider.model_name == "claude-opus"
        assert provider.litellm_model == "anthropic/claude-opus-4"

    def test_get_provider_not_found(self, registry: ProviderRegistry) -> None:
        with pytest.raises(ModelNotFoundError):
            registry.get_provider("nonexistent-model")

    def test_is_provider_healthy_default(self, registry: ProviderRegistry) -> None:
        assert registry.is_provider_healthy("claude-opus") is True

    def test_record_failure(self, registry: ProviderRegistry) -> None:
        registry.record_failure("claude-opus", "timeout")
        health = registry._health["claude-opus"]
        assert health.consecutive_failures == 1
        assert health.last_error == "timeout"

    def test_record_success_resets_failures(self, registry: ProviderRegistry) -> None:
        registry.record_failure("claude-opus", "timeout")
        registry.record_failure("claude-opus", "timeout")
        registry.record_success("claude-opus")
        health = registry._health["claude-opus"]
        assert health.consecutive_failures == 0
        assert health.healthy is True

    def test_unhealthy_after_many_failures(self, registry: ProviderRegistry) -> None:
        for _ in range(5):
            registry.record_failure("claude-opus", "timeout")
        assert registry.is_provider_healthy("claude-opus") is False

    def test_build_litellm_model_list(self, registry: ProviderRegistry) -> None:
        model_list = registry.build_litellm_model_list()
        assert isinstance(model_list, list)
        assert len(model_list) == 4

        # Check structure of first entry
        entry = model_list[0]
        assert "model_name" in entry
        assert "litellm_params" in entry
        assert "model" in entry["litellm_params"]

    def test_build_litellm_model_list_has_api_base(self, registry: ProviderRegistry) -> None:
        model_list = registry.build_litellm_model_list()
        # ollama entry should have api_base
        ollama_entry = next(e for e in model_list if e["model_name"] == "ollama-llama")
        assert ollama_entry["litellm_params"]["api_base"] == "http://localhost:11434"


# ── Settings integration ──────────────────────────────────────────────────

class TestSettingsLLMConfigPath:
    """Settings class has llm_config_path field."""

    def test_has_llm_config_path(self) -> None:
        from codebot.config import Settings
        s = Settings()
        assert hasattr(s, "llm_config_path")
        assert s.llm_config_path == "configs/providers/llm.yaml"
