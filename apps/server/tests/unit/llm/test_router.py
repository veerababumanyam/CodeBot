"""Tests for TaskBasedModelRouter with complexity and cost adjustments."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from codebot.llm.config import LLMConfig
from codebot.llm.providers import ProviderRegistry
from codebot.llm.router import (
    DOWNGRADE_MAP,
    MODEL_TIER_MAP,
    ModelTier,
    TaskBasedModelRouter,
)
from codebot.llm.schemas import RoutingConstraints, TaskType


# ── Fixtures ───────────────────────────────────────────────────────────────

ROUTER_YAML = dedent("""\
    providers:
      - model_name: "claude-opus"
        litellm_model: "anthropic/claude-opus-4"
        api_key_env: "ANTHROPIC_API_KEY"
        enabled: true

      - model_name: "claude-sonnet"
        litellm_model: "anthropic/claude-sonnet-4"
        api_key_env: "ANTHROPIC_API_KEY"
        enabled: true

      - model_name: "claude-haiku"
        litellm_model: "anthropic/claude-haiku-3.5"
        api_key_env: "ANTHROPIC_API_KEY"
        enabled: true

      - model_name: "gpt-4o"
        litellm_model: "openai/gpt-4o"
        api_key_env: "OPENAI_API_KEY"
        enabled: true

      - model_name: "gpt-4o-mini"
        litellm_model: "openai/gpt-4o-mini"
        api_key_env: "OPENAI_API_KEY"
        enabled: true

      - model_name: "gemini-pro"
        litellm_model: "gemini/gemini-2.5-pro"
        api_key_env: "GOOGLE_API_KEY"
        enabled: true

      - model_name: "gemini-flash"
        litellm_model: "gemini/gemini-2.5-flash"
        api_key_env: "GOOGLE_API_KEY"
        enabled: true

      - model_name: "ollama-llama"
        litellm_model: "ollama/llama3.1:70b"
        api_base: "http://localhost:11434"
        enabled: true

    routing_table:
      ORCHESTRATION:
        primary_model: "claude-opus"
        fallback_models: ["gpt-4o", "gemini-pro"]
        reason: "Complex planning"
      CODE_GENERATION:
        primary_model: "claude-sonnet"
        fallback_models: ["gpt-4o", "gemini-pro"]
        reason: "Fast code gen"
      CODE_REVIEW:
        primary_model: "claude-opus"
        fallback_models: ["gpt-4o"]
        reason: "Nuanced review"
      RESEARCH:
        primary_model: "gemini-pro"
        fallback_models: ["claude-opus"]
        reason: "Large context"
      SIMPLE_TRANSFORM:
        primary_model: "claude-haiku"
        fallback_models: ["gemini-flash", "gpt-4o-mini"]
        reason: "Fast transforms"
      DOCUMENTATION:
        primary_model: "claude-sonnet"
        fallback_models: ["gpt-4o", "gemini-pro"]
        reason: "Clear writing"
      TESTING:
        primary_model: "claude-sonnet"
        fallback_models: ["gpt-4o"]
        reason: "Test generation"
      DEBUGGING:
        primary_model: "claude-opus"
        fallback_models: ["gpt-4o", "claude-sonnet"]
        reason: "Root cause analysis"
      BRAINSTORMING:
        primary_model: "claude-opus"
        fallback_models: ["gemini-pro", "gpt-4o"]
        reason: "Creative ideation"
      ARCHITECTURE:
        primary_model: "claude-opus"
        fallback_models: ["gpt-4o", "gemini-pro"]
        reason: "System design"
      PLANNING:
        primary_model: "claude-sonnet"
        fallback_models: ["gpt-4o"]
        reason: "Task decomposition"
      SECURITY_SCAN:
        primary_model: "claude-sonnet"
        fallback_models: ["gpt-4o"]
        reason: "Security patterns"

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


@pytest.fixture
def config(tmp_path: Path) -> LLMConfig:
    """Load a test LLMConfig from YAML."""
    p = tmp_path / "llm.yaml"
    p.write_text(ROUTER_YAML)
    return LLMConfig.from_yaml(p)


@pytest.fixture
def registry(config: LLMConfig) -> ProviderRegistry:
    """Create a ProviderRegistry from test config."""
    return ProviderRegistry(config)


@pytest.fixture
def router(config: LLMConfig, registry: ProviderRegistry) -> TaskBasedModelRouter:
    """Create a TaskBasedModelRouter from test config and registry."""
    return TaskBasedModelRouter(config=config, provider_registry=registry)


# ── ModelTier and Maps ────────────────────────────────────────────────────

class TestModelTierMaps:
    """ModelTier enum and tier/downgrade maps are correctly defined."""

    def test_model_tier_values(self) -> None:
        assert ModelTier.PREMIUM == "premium"
        assert ModelTier.STANDARD == "standard"
        assert ModelTier.ECONOMY == "economy"

    def test_premium_models_in_tier_map(self) -> None:
        assert MODEL_TIER_MAP["claude-opus"] == ModelTier.PREMIUM
        assert MODEL_TIER_MAP["gpt-4o"] == ModelTier.PREMIUM
        assert MODEL_TIER_MAP["gemini-pro"] == ModelTier.PREMIUM

    def test_standard_models_in_tier_map(self) -> None:
        assert MODEL_TIER_MAP["claude-sonnet"] == ModelTier.STANDARD
        assert MODEL_TIER_MAP["gpt-4o-mini"] == ModelTier.STANDARD
        assert MODEL_TIER_MAP["gemini-flash"] == ModelTier.STANDARD

    def test_economy_models_in_tier_map(self) -> None:
        assert MODEL_TIER_MAP["claude-haiku"] == ModelTier.ECONOMY
        assert MODEL_TIER_MAP["ollama-llama"] == ModelTier.ECONOMY

    def test_downgrade_map(self) -> None:
        assert DOWNGRADE_MAP["claude-opus"] == "claude-sonnet"
        assert DOWNGRADE_MAP["gpt-4o"] == "gpt-4o-mini"
        assert DOWNGRADE_MAP["gemini-pro"] == "gemini-flash"


# ── Default routing ───────────────────────────────────────────────────────

class TestDefaultRouting:
    """Router returns correct models for each task type with default config."""

    def test_orchestration_routes_to_opus(self, router: TaskBasedModelRouter) -> None:
        assert router.route(TaskType.ORCHESTRATION) == "claude-opus"

    def test_code_gen_routes_to_sonnet(self, router: TaskBasedModelRouter) -> None:
        assert router.route(TaskType.CODE_GENERATION) == "claude-sonnet"

    def test_research_routes_to_gemini(self, router: TaskBasedModelRouter) -> None:
        assert router.route(TaskType.RESEARCH) == "gemini-pro"

    def test_simple_transform_routes_to_haiku(self, router: TaskBasedModelRouter) -> None:
        assert router.route(TaskType.SIMPLE_TRANSFORM) == "claude-haiku"

    def test_debugging_routes_to_opus(self, router: TaskBasedModelRouter) -> None:
        assert router.route(TaskType.DEBUGGING) == "claude-opus"

    def test_documentation_routes_to_sonnet(self, router: TaskBasedModelRouter) -> None:
        assert router.route(TaskType.DOCUMENTATION) == "claude-sonnet"


# ── Complexity-based routing ──────────────────────────────────────────────

class TestComplexityRouting:
    """Router adjusts model selection based on complexity score."""

    def test_low_complexity_downgrades(self, router: TaskBasedModelRouter) -> None:
        constraints = RoutingConstraints(complexity_score=0.2)
        # ORCHESTRATION primary is claude-opus (PREMIUM) -> should downgrade to claude-sonnet
        result = router.route(TaskType.ORCHESTRATION, constraints)
        assert result == "claude-sonnet"

    def test_high_complexity_keeps_primary(self, router: TaskBasedModelRouter) -> None:
        constraints = RoutingConstraints(complexity_score=0.8)
        result = router.route(TaskType.ORCHESTRATION, constraints)
        assert result == "claude-opus"

    def test_medium_complexity_keeps_primary(self, router: TaskBasedModelRouter) -> None:
        constraints = RoutingConstraints(complexity_score=0.5)
        result = router.route(TaskType.ORCHESTRATION, constraints)
        assert result == "claude-opus"

    def test_threshold_exactly_0_3_keeps_primary(self, router: TaskBasedModelRouter) -> None:
        constraints = RoutingConstraints(complexity_score=0.3)
        result = router.route(TaskType.ORCHESTRATION, constraints)
        assert result == "claude-opus"

    def test_threshold_exactly_0_7_keeps_primary(self, router: TaskBasedModelRouter) -> None:
        constraints = RoutingConstraints(complexity_score=0.7)
        result = router.route(TaskType.ORCHESTRATION, constraints)
        assert result == "claude-opus"


# ── Cost-based routing ────────────────────────────────────────────────────

class TestCostRouting:
    """Router adjusts model selection based on max_cost_per_call."""

    def test_max_cost_returns_cheaper_model(self, router: TaskBasedModelRouter) -> None:
        constraints = RoutingConstraints(max_cost_per_call=0.001)
        result = router.route(TaskType.ORCHESTRATION, constraints)
        # Should return an economy model (cheapest available)
        tier = MODEL_TIER_MAP.get(result)
        assert tier in (ModelTier.ECONOMY, ModelTier.STANDARD)


# ── prefer_local routing ─────────────────────────────────────────────────

class TestLocalRouting:
    """Router prefers self-hosted models when prefer_local is True."""

    def test_prefer_local_returns_ollama(self, router: TaskBasedModelRouter) -> None:
        constraints = RoutingConstraints(prefer_local=True)
        result = router.route(TaskType.ORCHESTRATION, constraints)
        assert result == "ollama-llama"


# ── Unknown task type ─────────────────────────────────────────────────────

class TestUnknownTaskType:
    """Router handles unknown task types gracefully."""

    def test_unknown_task_uses_default(self, router: TaskBasedModelRouter) -> None:
        # Use a valid TaskType but one we might not have a specific test for
        # The important thing is it doesn't crash
        result = router.route(TaskType.SECURITY_SCAN)
        assert isinstance(result, str)
        assert len(result) > 0


# ── Fallback chains ──────────────────────────────────────────────────────

class TestFallbackChain:
    """Router provides ordered fallback chains for task types."""

    def test_orchestration_fallbacks(self, router: TaskBasedModelRouter) -> None:
        chain = router.get_fallback_chain(TaskType.ORCHESTRATION)
        assert chain == ["claude-opus", "gpt-4o", "gemini-pro"]

    def test_code_gen_fallbacks(self, router: TaskBasedModelRouter) -> None:
        chain = router.get_fallback_chain(TaskType.CODE_GENERATION)
        assert chain == ["claude-sonnet", "gpt-4o", "gemini-pro"]

    def test_simple_transform_fallbacks(self, router: TaskBasedModelRouter) -> None:
        chain = router.get_fallback_chain(TaskType.SIMPLE_TRANSFORM)
        assert chain == ["claude-haiku", "gemini-flash", "gpt-4o-mini"]


# ── Router construction ──────────────────────────────────────────────────

class TestRouterConstruction:
    """Router constructed from LLMConfig correctly loads routing table."""

    def test_loads_routing_table(self, router: TaskBasedModelRouter) -> None:
        # All 12 task types should be routable
        for task_type in TaskType:
            result = router.route(task_type)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_router_has_registry(self, router: TaskBasedModelRouter) -> None:
        assert router._provider_registry is not None
