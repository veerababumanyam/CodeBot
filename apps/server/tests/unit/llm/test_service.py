"""Tests for LLMService facade -- complete(), stream(), from_config(), and public API."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codebot.llm.budget import CostTracker
from codebot.llm.callbacks import CodeBotLLMLogger
from codebot.llm.config import BudgetConfig, LLMConfig, ProviderConfig
from codebot.llm.estimator import CostEstimator, PipelineCostEstimate
from codebot.llm.exceptions import BudgetExceededError
from codebot.llm.fallback import FallbackChainManager
from codebot.llm.providers import ProviderRegistry
from codebot.llm.router import TaskBasedModelRouter
from codebot.llm.schemas import (
    LLMMessage,
    LLMRequest,
    LLMResponse,
    RoutingRule,
    TaskType,
    TokenUsage,
)
from codebot.llm.service import LLMService


@pytest.fixture
def service_config() -> LLMConfig:
    """Minimal config for service tests."""
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
        ],
        routing_table={
            "CODE_GENERATION": RoutingRule(
                primary_model="claude-sonnet",
                fallback_models=["gpt-4o"],
                reason="Code gen",
            ),
        },
        budget=BudgetConfig(global_budget_usd=50.0),
    )


@pytest.fixture
def mock_litellm_router() -> AsyncMock:
    """Mock LiteLLM Router with acompletion returning fake response."""
    router = AsyncMock()

    # Create a fake ModelResponse
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = "Test response"
    usage = MagicMock()
    usage.prompt_tokens = 100
    usage.completion_tokens = 50
    usage.total_tokens = 150
    response.usage = usage
    response._hidden_params = {"response_cost": 0.05}

    router.acompletion = AsyncMock(return_value=response)
    return router


@pytest.fixture
def llm_service(
    service_config: LLMConfig,
    mock_litellm_router: AsyncMock,
) -> LLMService:
    """Create an LLMService with mocked LiteLLM Router."""
    registry = ProviderRegistry(service_config)
    router = TaskBasedModelRouter(service_config, registry)
    cost_tracker = CostTracker(service_config.budget)
    estimator = CostEstimator(service_config, router)
    llm_logger = CodeBotLLMLogger(cost_tracker, registry, event_bus=None)

    return LLMService(
        config=service_config,
        litellm_router=mock_litellm_router,
        router=router,
        cost_tracker=cost_tracker,
        estimator=estimator,
        llm_logger=llm_logger,
    )


class TestLLMServiceComplete:
    """Tests for LLMService.complete()."""

    @pytest.mark.asyncio
    async def test_complete_returns_llm_response(
        self, llm_service: LLMService
    ) -> None:
        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
        )
        response = await llm_service.complete(
            request,
            agent_id="test-agent",
            task_type=TaskType.CODE_GENERATION,
            stage="S5",
        )
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "claude-sonnet"

    @pytest.mark.asyncio
    async def test_complete_returns_correct_usage(
        self, llm_service: LLMService
    ) -> None:
        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
        )
        response = await llm_service.complete(
            request,
            agent_id="test-agent",
            task_type=TaskType.CODE_GENERATION,
        )
        assert response.usage.prompt_tokens == 100
        assert response.usage.completion_tokens == 50
        assert response.usage.total_tokens == 150

    @pytest.mark.asyncio
    async def test_complete_measures_latency(
        self, llm_service: LLMService
    ) -> None:
        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
        )
        response = await llm_service.complete(
            request,
            agent_id="test-agent",
            task_type=TaskType.CODE_GENERATION,
        )
        assert response.latency_ms >= 0.0

    @pytest.mark.asyncio
    async def test_complete_raises_budget_exceeded(
        self,
        service_config: LLMConfig,
        mock_litellm_router: AsyncMock,
    ) -> None:
        """Budget exceeded should raise before making API call."""
        registry = ProviderRegistry(service_config)
        router = TaskBasedModelRouter(service_config, registry)
        cost_tracker = CostTracker(service_config.budget)
        estimator = CostEstimator(service_config, router)
        llm_logger = CodeBotLLMLogger(cost_tracker, registry, event_bus=None)

        # Pre-fill cost to exceed halt threshold
        usage = TokenUsage(
            prompt_tokens=1000, completion_tokens=500, total_tokens=1500, cost_usd=48.0
        )
        await cost_tracker.record(
            agent_id="other", model="claude-sonnet", stage="S5", usage=usage
        )

        service = LLMService(
            config=service_config,
            litellm_router=mock_litellm_router,
            router=router,
            cost_tracker=cost_tracker,
            estimator=estimator,
            llm_logger=llm_logger,
        )

        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
        )
        with pytest.raises(BudgetExceededError):
            await service.complete(
                request,
                agent_id="test-agent",
                task_type=TaskType.CODE_GENERATION,
            )

        # Should NOT have called the LLM
        mock_litellm_router.acompletion.assert_not_called()

    @pytest.mark.asyncio
    async def test_complete_passes_metadata(
        self, llm_service: LLMService, mock_litellm_router: AsyncMock
    ) -> None:
        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
        )
        await llm_service.complete(
            request,
            agent_id="agent-42",
            task_type=TaskType.CODE_GENERATION,
            stage="S5",
        )

        call_kwargs = mock_litellm_router.acompletion.call_args
        metadata = call_kwargs.kwargs.get("metadata", {})
        assert metadata["agent_id"] == "agent-42"
        assert metadata["stage"] == "S5"


class TestLLMServiceStream:
    """Tests for LLMService.stream()."""

    @pytest.mark.asyncio
    async def test_stream_returns_async_iterator(
        self, llm_service: LLMService, mock_litellm_router: AsyncMock
    ) -> None:
        # Set up mock to return an async iterator of chunks
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Hello"

        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = " world"

        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta.content = "!"

        async def mock_stream(*args: object, **kwargs: object) -> AsyncIterator[MagicMock]:
            for chunk in [chunk1, chunk2, chunk3]:
                yield chunk

        mock_litellm_router.acompletion = mock_stream

        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
        )
        chunks: list[str] = []
        async for content in llm_service.stream(
            request,
            agent_id="test-agent",
            task_type=TaskType.CODE_GENERATION,
        ):
            chunks.append(content)

        assert chunks == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_stream_checks_budget(
        self,
        service_config: LLMConfig,
        mock_litellm_router: AsyncMock,
    ) -> None:
        """Stream should check budget before streaming."""
        registry = ProviderRegistry(service_config)
        router = TaskBasedModelRouter(service_config, registry)
        cost_tracker = CostTracker(service_config.budget)
        estimator = CostEstimator(service_config, router)
        llm_logger = CodeBotLLMLogger(cost_tracker, registry, event_bus=None)

        # Pre-fill to exceed budget
        usage = TokenUsage(
            prompt_tokens=1000, completion_tokens=500, total_tokens=1500, cost_usd=48.0
        )
        await cost_tracker.record(
            agent_id="other", model="claude-sonnet", stage="S5", usage=usage
        )

        service = LLMService(
            config=service_config,
            litellm_router=mock_litellm_router,
            router=router,
            cost_tracker=cost_tracker,
            estimator=estimator,
            llm_logger=llm_logger,
        )

        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
        )
        with pytest.raises(BudgetExceededError):
            async for _ in service.stream(
                request,
                agent_id="test-agent",
                task_type=TaskType.CODE_GENERATION,
            ):
                pass

    @pytest.mark.asyncio
    async def test_stream_passes_stream_true(
        self, llm_service: LLMService, mock_litellm_router: AsyncMock
    ) -> None:
        async def mock_stream(*args: object, **kwargs: object) -> AsyncIterator[MagicMock]:
            assert kwargs.get("stream") is True
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = "ok"
            yield chunk

        mock_litellm_router.acompletion = mock_stream

        request = LLMRequest(
            messages=[LLMMessage(role="user", content="Hello")],
        )
        chunks = []
        async for content in llm_service.stream(
            request,
            agent_id="test-agent",
            task_type=TaskType.CODE_GENERATION,
        ):
            chunks.append(content)
        assert chunks == ["ok"]


class TestLLMServiceFactory:
    """Tests for LLMService.from_config() and factory function."""

    @patch("codebot.llm.service.litellm")
    @patch("codebot.llm.fallback.litellm")
    def test_from_config_creates_service(
        self,
        mock_fallback_litellm: MagicMock,
        mock_service_litellm: MagicMock,
        service_config: LLMConfig,
    ) -> None:
        mock_fallback_litellm.Router.return_value = MagicMock()

        service = LLMService.from_config(service_config)
        assert isinstance(service, LLMService)

    @patch("codebot.llm.service.litellm")
    @patch("codebot.llm.fallback.litellm")
    def test_from_config_with_event_bus(
        self,
        mock_fallback_litellm: MagicMock,
        mock_service_litellm: MagicMock,
        service_config: LLMConfig,
    ) -> None:
        mock_fallback_litellm.Router.return_value = MagicMock()
        mock_event_bus = AsyncMock()

        service = LLMService.from_config(service_config, event_bus=mock_event_bus)
        assert isinstance(service, LLMService)


class TestLLMServiceDelegation:
    """Tests for delegation methods."""

    @pytest.mark.asyncio
    async def test_get_cost_report_delegates(
        self, llm_service: LLMService
    ) -> None:
        report = llm_service.get_cost_report()
        assert isinstance(report, dict)
        assert "total_cost_usd" in report
        assert "by_agent" in report

    def test_estimate_cost_delegates(
        self, llm_service: LLMService
    ) -> None:
        tasks = [
            (TaskType.CODE_GENERATION, 1000, 4096),
        ]
        result = llm_service.estimate_cost(tasks)
        assert isinstance(result, PipelineCostEstimate)
        assert result.total_cost_usd > 0.0


class TestPublicAPI:
    """Tests for __init__.py exports."""

    def test_llm_service_importable(self) -> None:
        from codebot.llm import LLMService

        assert LLMService is not None

    def test_llm_request_importable(self) -> None:
        from codebot.llm import LLMRequest

        assert LLMRequest is not None

    def test_llm_response_importable(self) -> None:
        from codebot.llm import LLMResponse

        assert LLMResponse is not None

    def test_task_type_importable(self) -> None:
        from codebot.llm import TaskType

        assert TaskType is not None

    def test_get_llm_service_importable(self) -> None:
        from codebot.llm import get_llm_service

        assert callable(get_llm_service)

    def test_all_exports_present(self) -> None:
        from codebot.llm import __all__

        expected = {
            "BudgetDecision",
            "LLMMessage",
            "LLMRequest",
            "LLMResponse",
            "LLMService",
            "RoutingConstraints",
            "RoutingRule",
            "TaskType",
            "TokenUsage",
            "get_llm_service",
        }
        assert set(__all__) == expected
