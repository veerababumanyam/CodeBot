"""Task-based model routing for the Multi-LLM abstraction layer.

Selects the optimal LLM model for each task type based on routing
rules, complexity scores, cost constraints, and local-preference flags.
The router uses a tier system (PREMIUM/STANDARD/ECONOMY) to enable
automatic downgrade of model selection for low-complexity tasks.
"""

from __future__ import annotations

import enum

from codebot.llm.config import LLMConfig
from codebot.llm.providers import ProviderRegistry
from codebot.llm.schemas import RoutingConstraints, RoutingRule, TaskType


class ModelTier(str, enum.Enum):
    """Classification of model quality/cost tiers.

    Used by the router to determine downgrade and cost-optimization
    paths between models of different capability levels.
    """

    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"


# Maps model names to their quality/cost tier.
MODEL_TIER_MAP: dict[str, ModelTier] = {
    # Premium tier: highest capability, highest cost
    "claude-opus": ModelTier.PREMIUM,
    "gpt-4o": ModelTier.PREMIUM,
    "gemini-pro": ModelTier.PREMIUM,
    # Standard tier: good capability, moderate cost
    "claude-sonnet": ModelTier.STANDARD,
    "gpt-4o-mini": ModelTier.STANDARD,
    "gemini-flash": ModelTier.STANDARD,
    # Economy tier: basic capability, lowest cost
    "claude-haiku": ModelTier.ECONOMY,
    "ollama-llama": ModelTier.ECONOMY,
}

# Maps premium models to their standard-tier equivalents for downgrade.
DOWNGRADE_MAP: dict[str, str] = {
    "claude-opus": "claude-sonnet",
    "gpt-4o": "gpt-4o-mini",
    "gemini-pro": "gemini-flash",
}

# Tier ordering for cost-based sorting (cheapest first).
_TIER_ORDER: dict[ModelTier, int] = {
    ModelTier.ECONOMY: 0,
    ModelTier.STANDARD: 1,
    ModelTier.PREMIUM: 2,
}


class TaskBasedModelRouter:
    """Routes LLM tasks to the optimal model based on task type and constraints.

    The router uses a configurable routing table to select models for each
    task type. It supports:

    - **Complexity-based downgrade**: Tasks with low complexity scores
      (< 0.3) are automatically routed to cheaper models.
    - **Cost constraints**: When a max cost per call is specified, the
      router selects the cheapest capable model.
    - **Local preference**: When ``prefer_local`` is True, routes to
      self-hosted models (e.g. Ollama).
    - **Fallback chains**: Provides ordered lists of fallback models
      for retry logic.

    Args:
        config: The LLMConfig containing routing table and provider info.
        provider_registry: The ProviderRegistry for health checks and provider lookup.
    """

    def __init__(self, config: LLMConfig, provider_registry: ProviderRegistry) -> None:
        self._config = config
        self._provider_registry = provider_registry
        self._routing_table = config.routing_table

    def route(
        self,
        task_type: TaskType,
        constraints: RoutingConstraints | None = None,
    ) -> str:
        """Select the best model for the given task type and constraints.

        Decision flow (in priority order):
        1. ``prefer_local`` -> return first self-hosted model
        2. ``complexity_score < 0.3`` -> downgrade to cheaper model
        3. ``complexity_score >= 0.7`` -> ensure premium model
        4. ``max_cost_per_call`` -> find cheapest capable model
        5. Default -> return primary model from routing rule

        Args:
            task_type: The category of task to route.
            constraints: Optional constraints influencing model selection.

        Returns:
            The model name to use for this task.
        """
        rule = self._config.get_routing_rule(task_type.value)

        if constraints is None:
            return rule.primary_model

        # Priority 1: prefer local models
        if constraints.prefer_local:
            local_models = self._get_local_models()
            if local_models:
                return local_models[0]

        # Priority 2: complexity-based downgrade (low complexity)
        if constraints.complexity_score is not None and constraints.complexity_score < 0.3:
            return self._downgrade_model(rule.primary_model)

        # Priority 3: ensure premium for high complexity
        if constraints.complexity_score is not None and constraints.complexity_score >= 0.7:
            return rule.primary_model

        # Priority 4: cost-constrained selection
        if constraints.max_cost_per_call is not None:
            return self._find_cheapest_capable(task_type, constraints.max_cost_per_call)

        return rule.primary_model

    def get_fallback_chain(self, task_type: TaskType) -> list[str]:
        """Get the ordered fallback chain for a task type.

        Returns the primary model followed by all fallback models
        from the routing rule.

        Args:
            task_type: The task type to get fallbacks for.

        Returns:
            Ordered list starting with the primary model.
        """
        rule = self._config.get_routing_rule(task_type.value)
        return [rule.primary_model, *rule.fallback_models]

    def _downgrade_model(self, model: str) -> str:
        """Downgrade a model to a cheaper equivalent.

        Looks up the model in the downgrade map and returns the
        cheaper alternative. If no downgrade path exists, returns
        the original model.

        Args:
            model: The model name to downgrade.

        Returns:
            The downgraded model name, or the original if no downgrade exists.
        """
        return DOWNGRADE_MAP.get(model, model)

    def _find_cheapest_capable(self, task_type: TaskType, max_cost: float) -> str:
        """Find the cheapest model that can handle the task.

        Sorts all enabled and healthy models by tier (ECONOMY first)
        and returns the first available one. Falls back to the
        primary model from the routing rule if no suitable model is found.

        Args:
            task_type: The task type for fallback rule lookup.
            max_cost: Maximum cost per call in USD (used as selection hint).

        Returns:
            The cheapest capable model name.
        """
        enabled = self._provider_registry.get_enabled_providers()

        # Sort by tier (cheapest first)
        sorted_models = sorted(
            enabled,
            key=lambda p: _TIER_ORDER.get(
                MODEL_TIER_MAP.get(p.model_name, ModelTier.PREMIUM),
                2,
            ),
        )

        for provider in sorted_models:
            if self._provider_registry.is_provider_healthy(provider.model_name):
                return provider.model_name

        # Fallback to primary model (best-effort)
        rule = self._config.get_routing_rule(task_type.value)
        return rule.primary_model

    def _get_local_models(self) -> list[str]:
        """Get model names for self-hosted providers.

        Returns models where the provider has an ``api_base`` set
        or the LiteLLM model identifier starts with ``ollama/``.

        Returns:
            List of local model names.
        """
        local: list[str] = []
        for provider in self._provider_registry.get_enabled_providers():
            if provider.api_base or provider.litellm_model.startswith("ollama/"):
                local.append(provider.model_name)
        return local
