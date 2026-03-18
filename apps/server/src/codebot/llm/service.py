"""LLMService -- unified entry point for all LLM calls in CodeBot.

Agents use this service, never litellm directly. Encapsulates routing,
fallback, budgeting, and cost tracking behind one async interface.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import litellm

from codebot.llm.budget import CostTracker
from codebot.llm.callbacks import CodeBotLLMLogger
from codebot.llm.config import LLMConfig
from codebot.llm.estimator import CostEstimator, PipelineCostEstimate
from codebot.llm.exceptions import BudgetExceededError
from codebot.llm.fallback import FallbackChainManager
from codebot.llm.providers import ProviderRegistry
from codebot.llm.router import TaskBasedModelRouter
from codebot.llm.schemas import (
    LLMRequest,
    LLMResponse,
    TaskType,
    TokenUsage,
)

if TYPE_CHECKING:
    from codebot.events.bus import EventBus

logger = logging.getLogger(__name__)


class LLMService:
    """Unified entry point for all LLM calls in CodeBot.

    Provides ``complete()`` for synchronous completions and ``stream()``
    for streaming responses. Handles routing, budget enforcement, and
    cost tracking transparently.

    Agents should use this service instead of calling LiteLLM directly.

    Args:
        config: The LLMConfig with all settings.
        litellm_router: Configured LiteLLM Router with fallback chains.
        router: TaskBasedModelRouter for model selection.
        cost_tracker: CostTracker for budget enforcement.
        estimator: CostEstimator for pre-execution predictions.
        llm_logger: CodeBotLLMLogger for callback integration.
    """

    def __init__(
        self,
        *,
        config: LLMConfig,
        litellm_router: Any,  # litellm.Router (untyped)
        router: TaskBasedModelRouter,
        cost_tracker: CostTracker,
        estimator: CostEstimator,
        llm_logger: CodeBotLLMLogger,
    ) -> None:
        self._config = config
        self._litellm_router = litellm_router
        self._router = router
        self._cost_tracker = cost_tracker
        self._estimator = estimator
        self._llm_logger = llm_logger

    async def complete(
        self,
        request: LLMRequest,
        *,
        agent_id: str,
        task_type: TaskType,
        stage: str = "unknown",
    ) -> LLMResponse:
        """Execute a non-streaming LLM completion.

        Routes the request to the optimal model, checks budget,
        executes via LiteLLM Router, and returns a structured response
        with usage and latency metrics.

        Args:
            request: The LLM request with messages, temperature, etc.
            agent_id: Identifier of the calling agent.
            task_type: Category of the task for routing.
            stage: Pipeline stage name (e.g. "S5").

        Returns:
            LLMResponse with content, usage, model, and latency.

        Raises:
            BudgetExceededError: If budget is exhausted.
        """
        # Route to optimal model
        model = self._router.route(task_type, request.constraints)

        # Budget check before API call
        decision = await self._cost_tracker.check_budget(agent_id)
        if not decision.allowed:
            raise BudgetExceededError(agent_id, decision)

        # Build messages as list of dicts for LiteLLM
        messages = [
            {"role": m.role, "content": m.content} for m in request.messages
        ]

        # Execute with timing
        start = time.monotonic()
        response = await self._litellm_router.acompletion(
            model=model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False,
            metadata={"agent_id": agent_id, "stage": stage},
        )
        latency_ms = (time.monotonic() - start) * 1000

        # Parse response
        content = response.choices[0].message.content or ""
        usage_data = response.usage
        response_cost = getattr(response, "_hidden_params", {}).get(
            "response_cost", 0.0
        )

        return LLMResponse(
            model=model,
            content=content,
            usage=TokenUsage(
                prompt_tokens=usage_data.prompt_tokens,
                completion_tokens=usage_data.completion_tokens,
                total_tokens=usage_data.total_tokens,
                cost_usd=response_cost,
            ),
            latency_ms=latency_ms,
        )

    async def stream(
        self,
        request: LLMRequest,
        *,
        agent_id: str,
        task_type: TaskType,
        stage: str = "unknown",
    ) -> AsyncIterator[str]:
        """Execute a streaming LLM completion.

        Routes the request, checks budget, and yields content chunks
        from the LiteLLM Router's streaming response.

        Args:
            request: The LLM request with messages, temperature, etc.
            agent_id: Identifier of the calling agent.
            task_type: Category of the task for routing.
            stage: Pipeline stage name (e.g. "S5").

        Yields:
            Content strings from each chunk of the streaming response.

        Raises:
            BudgetExceededError: If budget is exhausted.
        """
        # Route to optimal model
        model = self._router.route(task_type, request.constraints)

        # Budget check before streaming
        decision = await self._cost_tracker.check_budget(agent_id)
        if not decision.allowed:
            raise BudgetExceededError(agent_id, decision)

        # Build messages as list of dicts for LiteLLM
        messages = [
            {"role": m.role, "content": m.content} for m in request.messages
        ]

        # Execute with stream=True
        # LiteLLM Router may return an async generator directly (no await)
        # or a coroutine that resolves to one. Handle both patterns.
        response = self._litellm_router.acompletion(
            model=model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
            metadata={"agent_id": agent_id, "stage": stage},
        )

        # If it's a coroutine (awaitable), await it to get the async iterator
        if hasattr(response, "__await__"):
            response = await response

        async for chunk in response:
            content = chunk.choices[0].delta.content or ""
            yield content

    def get_cost_report(self) -> dict[str, Any]:
        """Return a cost breakdown report from the CostTracker.

        Returns:
            Dictionary with total_cost_usd, by_agent, by_model,
            by_stage, and record_count.
        """
        return self._cost_tracker.get_cost_report()

    def estimate_cost(
        self,
        tasks: list[tuple[TaskType, int, int]],
    ) -> PipelineCostEstimate:
        """Estimate the cost of a pipeline execution.

        Args:
            tasks: List of (task_type, estimated_input_tokens, max_output_tokens).

        Returns:
            PipelineCostEstimate with per-task breakdowns and total.
        """
        return self._estimator.estimate_pipeline_cost(tasks)

    @classmethod
    def from_config(
        cls,
        config: LLMConfig,
        event_bus: EventBus | None = None,
    ) -> LLMService:
        """Create a fully wired LLMService from configuration.

        Factory method that constructs all internal components
        (ProviderRegistry, Router, CostTracker, Estimator, Logger,
        FallbackChainManager) and wires them together.

        Args:
            config: The LLMConfig with all settings.
            event_bus: Optional EventBus for event emission.

        Returns:
            A fully configured LLMService instance.
        """
        provider_registry = ProviderRegistry(config)
        router = TaskBasedModelRouter(config, provider_registry)
        cost_tracker = CostTracker(config.budget)
        estimator = CostEstimator(config, router)
        llm_logger = CodeBotLLMLogger(cost_tracker, provider_registry, event_bus)

        # Register our custom logger with LiteLLM
        litellm.callbacks = [llm_logger]

        # Build LiteLLM Router with fallback chains
        fallback_mgr = FallbackChainManager(config, provider_registry)
        litellm_router = fallback_mgr.build_litellm_router()

        return cls(
            config=config,
            litellm_router=litellm_router,
            router=router,
            cost_tracker=cost_tracker,
            estimator=estimator,
            llm_logger=llm_logger,
        )


# Module-level singleton for get_llm_service
_llm_service: LLMService | None = None


def get_llm_service(
    config: LLMConfig | None = None,
    event_bus: EventBus | None = None,
) -> LLMService:
    """Get or create the singleton LLMService instance.

    On first call, creates the service from the provided config or
    from the application's default settings. Subsequent calls return
    the same instance.

    Args:
        config: Optional LLMConfig. If None on first call, loads from
            the default settings path.
        event_bus: Optional EventBus for event emission.

    Returns:
        The singleton LLMService instance.
    """
    global _llm_service  # noqa: PLW0603
    if _llm_service is None:
        if config is None:
            from codebot.config import settings

            config = LLMConfig.from_yaml(settings.llm_config_path)
        _llm_service = LLMService.from_config(config, event_bus)
    return _llm_service
