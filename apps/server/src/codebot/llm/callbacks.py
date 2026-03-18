"""LiteLLM CustomLogger for CodeBot cost tracking and event emission.

Automatically intercepts every LiteLLM completion to record token usage
and cost in CostTracker, emit NATS events via EventBus, and track
provider health in ProviderRegistry.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from litellm.integrations.custom_logger import CustomLogger

from codebot.llm.schemas import TokenUsage

if TYPE_CHECKING:
    from codebot.events.bus import EventBus
    from codebot.llm.budget import CostTracker
    from codebot.llm.providers import ProviderRegistry

logger = logging.getLogger(__name__)


class CodeBotLLMLogger(CustomLogger):
    """LiteLLM callback that records costs and emits events on every completion.

    Hooks into LiteLLM's callback system to:
    - Record token usage and cost per agent/model/stage in CostTracker
    - Track provider health (success/failure) in ProviderRegistry
    - Emit LLM_USAGE, BUDGET_WARNING, and BUDGET_EXCEEDED events via EventBus

    Args:
        cost_tracker: The CostTracker for recording costs.
        provider_registry: The ProviderRegistry for health tracking.
        event_bus: Optional EventBus for NATS event emission. When None,
            events are logged but not published.
    """

    def __init__(
        self,
        cost_tracker: CostTracker,
        provider_registry: ProviderRegistry,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__()
        self._cost_tracker = cost_tracker
        self._provider_registry = provider_registry
        self._event_bus = event_bus

    async def async_log_success_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        """Called by LiteLLM after a successful completion.

        Extracts cost, model, agent_id, and stage from the call metadata,
        records usage in CostTracker, and emits events if an EventBus
        is available.

        Args:
            kwargs: LiteLLM call kwargs including response_cost and litellm_params.
            response_obj: The ModelResponse from LiteLLM.
            start_time: Call start timestamp.
            end_time: Call end timestamp.
        """
        cost = kwargs.get("response_cost", 0.0)
        model = kwargs.get("model", "unknown")

        # Extract metadata from litellm_params
        metadata = kwargs.get("litellm_params", {}).get("metadata", {})
        agent_id = metadata.get("agent_id", "unknown")
        stage = metadata.get("stage", "unknown")

        # Build TokenUsage from response
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        if response_obj and hasattr(response_obj, "usage") and response_obj.usage:
            prompt_tokens = getattr(response_obj.usage, "prompt_tokens", 0)
            completion_tokens = getattr(response_obj.usage, "completion_tokens", 0)
            total_tokens = getattr(response_obj.usage, "total_tokens", 0)

        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
        )

        # Record cost
        await self._cost_tracker.record(
            agent_id=agent_id,
            model=model,
            stage=stage,
            usage=usage,
        )

        # Record provider success
        self._provider_registry.record_success(model)

        # Emit events if event bus is available
        if self._event_bus is not None:
            # LLM_USAGE event
            usage_payload = json.dumps({
                "agent_id": agent_id,
                "model": model,
                "stage": stage,
                "cost_usd": cost,
                "tokens": total_tokens,
            }).encode()
            await self._event_bus.publish("LLM_USAGE", usage_payload)

            # BUDGET_WARNING event
            if self._cost_tracker.should_warn():
                warn_payload = json.dumps({
                    "total_cost": self._cost_tracker.total_cost_usd,
                    "threshold": "warn",
                    "budget": self._cost_tracker._global_budget_usd,
                }).encode()
                await self._event_bus.publish("BUDGET_WARNING", warn_payload)

            # BUDGET_EXCEEDED event
            if self._cost_tracker.should_halt():
                halt_payload = json.dumps({
                    "total_cost": self._cost_tracker.total_cost_usd,
                    "threshold": "halt",
                    "budget": self._cost_tracker._global_budget_usd,
                }).encode()
                await self._event_bus.publish("BUDGET_EXCEEDED", halt_payload)

        logger.debug(
            "LLM call: model=%s agent=%s cost=$%.4f tokens=%d",
            model,
            agent_id,
            cost,
            total_tokens,
        )

    async def async_log_failure_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        """Called by LiteLLM after a failed completion.

        Records the failure in ProviderRegistry for health tracking
        and optionally emits an LLM_FAILURE event.

        Args:
            kwargs: LiteLLM call kwargs including model and exception info.
            response_obj: The error response (may be None).
            start_time: Call start timestamp.
            end_time: Call end timestamp.
        """
        model = kwargs.get("model", "unknown")
        error = kwargs.get("exception", "Unknown error")

        # Record failure in provider registry
        self._provider_registry.record_failure(model, str(error))

        # Emit failure event if event bus is available
        if self._event_bus is not None:
            metadata = kwargs.get("litellm_params", {}).get("metadata", {})
            agent_id = metadata.get("agent_id", "unknown")
            stage = metadata.get("stage", "unknown")

            failure_payload = json.dumps({
                "agent_id": agent_id,
                "model": model,
                "stage": stage,
                "error": str(error),
            }).encode()
            await self._event_bus.publish("LLM_FAILURE", failure_payload)

        logger.warning(
            "LLM call failed: model=%s error=%s",
            model,
            str(error)[:200],
        )
