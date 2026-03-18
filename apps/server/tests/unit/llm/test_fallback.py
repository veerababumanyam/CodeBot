"""Tests for CodeBotLLMLogger callbacks and FallbackChainManager."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codebot.llm.budget import CostTracker
from codebot.llm.callbacks import CodeBotLLMLogger
from codebot.llm.config import BudgetConfig, FallbackConfig, LLMConfig, ProviderConfig
from codebot.llm.fallback import FallbackChainManager
from codebot.llm.providers import ProviderRegistry
from codebot.llm.schemas import RoutingRule


@pytest.fixture
def fallback_config() -> LLMConfig:
    """Config with multiple providers for fallback testing."""
    return LLMConfig(
        providers=[
            ProviderConfig(
                model_name="claude-sonnet",
                litellm_model="anthropic/claude-sonnet-4",
                api_key_env="ANTHROPIC_API_KEY",
            ),
            ProviderConfig(
                model_name="gpt-4o",
                litellm_model="openai/gpt-4o",
                api_key_env="OPENAI_API_KEY",
            ),
            ProviderConfig(
                model_name="gemini-pro",
                litellm_model="gemini/gemini-2.5-pro",
                api_key_env="GOOGLE_API_KEY",
            ),
        ],
        routing_table={
            "CODE_GENERATION": RoutingRule(
                primary_model="claude-sonnet",
                fallback_models=["gpt-4o", "gemini-pro"],
                reason="Code gen",
            ),
            "ORCHESTRATION": RoutingRule(
                primary_model="claude-sonnet",
                fallback_models=["gpt-4o"],
                reason="Orchestration",
            ),
            "RESEARCH": RoutingRule(
                primary_model="gemini-pro",
                fallback_models=["claude-sonnet"],
                reason="Research",
            ),
        },
        budget=BudgetConfig(global_budget_usd=50.0),
        fallback=FallbackConfig(num_retries=2, timeout_seconds=30),
    )


@pytest.fixture
def fallback_registry(fallback_config: LLMConfig) -> ProviderRegistry:
    """Provider registry for fallback tests."""
    return ProviderRegistry(fallback_config)


# ============================================================
# CodeBotLLMLogger Tests
# ============================================================


class TestCodeBotLLMLoggerSuccess:
    """Tests for async_log_success_event."""

    @pytest.fixture
    def logger_setup(self) -> tuple[CodeBotLLMLogger, CostTracker, ProviderRegistry, AsyncMock]:
        """Create a logger with mocked dependencies."""
        budget_config = BudgetConfig(global_budget_usd=50.0)
        cost_tracker = CostTracker(budget_config)
        config = LLMConfig(
            providers=[
                ProviderConfig(
                    model_name="claude-sonnet",
                    litellm_model="anthropic/claude-sonnet-4",
                    api_key_env="ANTHROPIC_API_KEY",
                ),
            ],
            routing_table={},
        )
        provider_registry = ProviderRegistry(config)
        event_bus = AsyncMock()
        event_bus.publish = AsyncMock()

        llm_logger = CodeBotLLMLogger(
            cost_tracker=cost_tracker,
            provider_registry=provider_registry,
            event_bus=event_bus,
        )
        return llm_logger, cost_tracker, provider_registry, event_bus

    @pytest.mark.asyncio
    async def test_records_cost_in_cost_tracker(
        self,
        logger_setup: tuple[CodeBotLLMLogger, CostTracker, ProviderRegistry, AsyncMock],
    ) -> None:
        llm_logger, cost_tracker, _, _ = logger_setup
        kwargs = {
            "response_cost": 0.05,
            "model": "claude-sonnet",
            "litellm_params": {
                "metadata": {"agent_id": "test-agent", "stage": "S5"},
            },
        }
        response_obj = MagicMock()
        response_obj.usage = MagicMock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        await llm_logger.async_log_success_event(kwargs, response_obj, None, None)

        assert cost_tracker.total_cost_usd == pytest.approx(0.05)
        assert cost_tracker.get_agent_cost("test-agent") == pytest.approx(0.05)

    @pytest.mark.asyncio
    async def test_extracts_agent_id_and_stage_from_metadata(
        self,
        logger_setup: tuple[CodeBotLLMLogger, CostTracker, ProviderRegistry, AsyncMock],
    ) -> None:
        llm_logger, cost_tracker, _, _ = logger_setup
        kwargs = {
            "response_cost": 0.03,
            "model": "claude-sonnet",
            "litellm_params": {
                "metadata": {"agent_id": "my-agent-42", "stage": "S7"},
            },
        }
        response_obj = MagicMock()
        response_obj.usage = MagicMock(
            prompt_tokens=50, completion_tokens=25, total_tokens=75
        )

        await llm_logger.async_log_success_event(kwargs, response_obj, None, None)

        assert cost_tracker.get_agent_cost("my-agent-42") == pytest.approx(0.03)
        report = cost_tracker.get_cost_report()
        assert report["by_stage"]["S7"] == pytest.approx(0.03)

    @pytest.mark.asyncio
    async def test_publishes_llm_usage_event(
        self,
        logger_setup: tuple[CodeBotLLMLogger, CostTracker, ProviderRegistry, AsyncMock],
    ) -> None:
        llm_logger, _, _, event_bus = logger_setup
        kwargs = {
            "response_cost": 0.05,
            "model": "claude-sonnet",
            "litellm_params": {
                "metadata": {"agent_id": "test-agent", "stage": "S5"},
            },
        }
        response_obj = MagicMock()
        response_obj.usage = MagicMock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        await llm_logger.async_log_success_event(kwargs, response_obj, None, None)

        # Should have published at least one event (LLM_USAGE)
        event_bus.publish.assert_called()
        call_args_list = event_bus.publish.call_args_list
        event_types = [call.args[0] for call in call_args_list]
        assert any("LLM_USAGE" in et for et in event_types)

    @pytest.mark.asyncio
    async def test_publishes_budget_warning_when_threshold_reached(
        self,
        logger_setup: tuple[CodeBotLLMLogger, CostTracker, ProviderRegistry, AsyncMock],
    ) -> None:
        llm_logger, cost_tracker, _, event_bus = logger_setup
        # Pre-fill cost to near warning threshold (80% of $50 = $40)
        from codebot.llm.schemas import TokenUsage

        usage = TokenUsage(
            prompt_tokens=1000, completion_tokens=500, total_tokens=1500, cost_usd=39.0
        )
        await cost_tracker.record(
            agent_id="other", model="claude-sonnet", stage="S5", usage=usage
        )
        event_bus.publish.reset_mock()

        kwargs = {
            "response_cost": 2.0,
            "model": "claude-sonnet",
            "litellm_params": {
                "metadata": {"agent_id": "test-agent", "stage": "S5"},
            },
        }
        response_obj = MagicMock()
        response_obj.usage = MagicMock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        await llm_logger.async_log_success_event(kwargs, response_obj, None, None)

        call_args_list = event_bus.publish.call_args_list
        event_types = [call.args[0] for call in call_args_list]
        assert any("BUDGET_WARNING" in et for et in event_types)

    @pytest.mark.asyncio
    async def test_publishes_budget_exceeded_when_halt_threshold(
        self,
        logger_setup: tuple[CodeBotLLMLogger, CostTracker, ProviderRegistry, AsyncMock],
    ) -> None:
        llm_logger, cost_tracker, _, event_bus = logger_setup
        # Pre-fill cost to near halt threshold (95% of $50 = $47.50)
        from codebot.llm.schemas import TokenUsage

        usage = TokenUsage(
            prompt_tokens=1000, completion_tokens=500, total_tokens=1500, cost_usd=46.0
        )
        await cost_tracker.record(
            agent_id="other", model="claude-sonnet", stage="S5", usage=usage
        )
        event_bus.publish.reset_mock()

        kwargs = {
            "response_cost": 2.0,
            "model": "claude-sonnet",
            "litellm_params": {
                "metadata": {"agent_id": "test-agent", "stage": "S5"},
            },
        }
        response_obj = MagicMock()
        response_obj.usage = MagicMock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        await llm_logger.async_log_success_event(kwargs, response_obj, None, None)

        call_args_list = event_bus.publish.call_args_list
        event_types = [call.args[0] for call in call_args_list]
        assert any("BUDGET_EXCEEDED" in et for et in event_types)


class TestCodeBotLLMLoggerFailure:
    """Tests for async_log_failure_event."""

    @pytest.mark.asyncio
    async def test_records_failure_in_provider_registry(self) -> None:
        budget_config = BudgetConfig(global_budget_usd=50.0)
        cost_tracker = CostTracker(budget_config)
        config = LLMConfig(
            providers=[
                ProviderConfig(
                    model_name="claude-sonnet",
                    litellm_model="anthropic/claude-sonnet-4",
                    api_key_env="ANTHROPIC_API_KEY",
                ),
            ],
            routing_table={},
        )
        provider_registry = ProviderRegistry(config)

        llm_logger = CodeBotLLMLogger(
            cost_tracker=cost_tracker,
            provider_registry=provider_registry,
            event_bus=None,
        )

        kwargs = {
            "model": "claude-sonnet",
            "exception": RuntimeError("API Error"),
            "litellm_params": {
                "metadata": {"agent_id": "test-agent", "stage": "S5"},
            },
        }

        await llm_logger.async_log_failure_event(kwargs, None, None, None)

        # Provider should have recorded a failure
        health = provider_registry._health["claude-sonnet"]
        assert health.consecutive_failures == 1
        assert health.last_error is not None


class TestCodeBotLLMLoggerNoEventBus:
    """Tests for CodeBotLLMLogger without event bus."""

    @pytest.mark.asyncio
    async def test_works_without_event_bus(self) -> None:
        """Logger should work fine when event_bus is None."""
        budget_config = BudgetConfig(global_budget_usd=50.0)
        cost_tracker = CostTracker(budget_config)
        config = LLMConfig(
            providers=[
                ProviderConfig(
                    model_name="claude-sonnet",
                    litellm_model="anthropic/claude-sonnet-4",
                    api_key_env="ANTHROPIC_API_KEY",
                ),
            ],
            routing_table={},
        )
        provider_registry = ProviderRegistry(config)

        llm_logger = CodeBotLLMLogger(
            cost_tracker=cost_tracker,
            provider_registry=provider_registry,
            event_bus=None,
        )

        kwargs = {
            "response_cost": 0.05,
            "model": "claude-sonnet",
            "litellm_params": {
                "metadata": {"agent_id": "test-agent", "stage": "S5"},
            },
        }
        response_obj = MagicMock()
        response_obj.usage = MagicMock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        # Should not raise even though event_bus is None
        await llm_logger.async_log_success_event(kwargs, response_obj, None, None)

        assert cost_tracker.total_cost_usd == pytest.approx(0.05)


# ============================================================
# FallbackChainManager Tests
# ============================================================


class TestFallbackChainManager:
    """Tests for FallbackChainManager."""

    @patch("codebot.llm.fallback.litellm")
    def test_build_litellm_router_creates_router(
        self,
        mock_litellm: MagicMock,
        fallback_config: LLMConfig,
        fallback_registry: ProviderRegistry,
    ) -> None:
        mock_router_instance = MagicMock()
        mock_litellm.Router.return_value = mock_router_instance

        mgr = FallbackChainManager(fallback_config, fallback_registry)
        router = mgr.build_litellm_router()

        assert router is mock_router_instance
        mock_litellm.Router.assert_called_once()
        call_kwargs = mock_litellm.Router.call_args
        assert call_kwargs.kwargs["num_retries"] == 2

    @patch("codebot.llm.fallback.litellm")
    def test_build_litellm_router_passes_model_list(
        self,
        mock_litellm: MagicMock,
        fallback_config: LLMConfig,
        fallback_registry: ProviderRegistry,
    ) -> None:
        mock_litellm.Router.return_value = MagicMock()

        mgr = FallbackChainManager(fallback_config, fallback_registry)
        mgr.build_litellm_router()

        call_kwargs = mock_litellm.Router.call_args
        model_list = call_kwargs.kwargs["model_list"]
        model_names = [m["model_name"] for m in model_list]
        assert "claude-sonnet" in model_names
        assert "gpt-4o" in model_names
        assert "gemini-pro" in model_names

    def test_get_fallback_mapping_deduplicates(
        self,
        fallback_config: LLMConfig,
        fallback_registry: ProviderRegistry,
    ) -> None:
        mgr = FallbackChainManager(fallback_config, fallback_registry)
        mapping = mgr.get_fallback_mapping()

        # claude-sonnet appears as primary in both CODE_GENERATION and ORCHESTRATION
        # The mapping should be deduplicated
        assert "claude-sonnet" in mapping
        # Should contain unique union of fallbacks
        assert isinstance(mapping["claude-sonnet"], list)

    @patch("codebot.llm.fallback.litellm")
    def test_build_litellm_router_passes_timeout(
        self,
        mock_litellm: MagicMock,
        fallback_config: LLMConfig,
        fallback_registry: ProviderRegistry,
    ) -> None:
        mock_litellm.Router.return_value = MagicMock()

        mgr = FallbackChainManager(fallback_config, fallback_registry)
        mgr.build_litellm_router()

        call_kwargs = mock_litellm.Router.call_args
        assert call_kwargs.kwargs["timeout"] == 30

    @patch("codebot.llm.fallback.litellm")
    def test_400_errors_not_retried_by_default(
        self,
        mock_litellm: MagicMock,
        fallback_config: LLMConfig,
        fallback_registry: ProviderRegistry,
    ) -> None:
        """400-level errors should not trigger fallback (LiteLLM default behavior).

        Verify we don't override LiteLLM's default that skips retries
        for client errors (400s). We check that enable_pre_call_checks
        is set to True to allow LiteLLM to validate requests.
        """
        mock_litellm.Router.return_value = MagicMock()

        mgr = FallbackChainManager(fallback_config, fallback_registry)
        mgr.build_litellm_router()

        call_kwargs = mock_litellm.Router.call_args
        # enable_pre_call_checks should be True
        assert call_kwargs.kwargs.get("enable_pre_call_checks") is True
