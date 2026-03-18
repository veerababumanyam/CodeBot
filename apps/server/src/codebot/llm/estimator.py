"""Pre-execution cost estimation for the Multi-LLM abstraction layer.

Provides upper-bound cost predictions for individual LLM calls and
full pipeline executions, using LiteLLM's maintained pricing data
with hardcoded fallbacks for offline/unknown models.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import litellm
from pydantic import BaseModel

from codebot.llm.schemas import TaskType

if TYPE_CHECKING:
    from codebot.llm.config import LLMConfig
    from codebot.llm.router import TaskBasedModelRouter

logger = logging.getLogger(__name__)


class TaskCostEstimate(BaseModel):
    """Cost estimate for a single LLM call.

    Attributes:
        task_type: The task type being estimated.
        model: The model that would be selected by the router.
        estimated_input_tokens: Number of input tokens estimated.
        estimated_output_tokens: Number of output tokens (max).
        estimated_cost_usd: Upper-bound cost estimate in USD.
    """

    task_type: str
    model: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float


class PipelineCostEstimate(BaseModel):
    """Aggregated cost estimate for a full pipeline execution.

    Attributes:
        estimates: Per-task cost estimates.
        total_cost_usd: Sum of all task estimates.
        note: Explanation of estimate methodology.
    """

    estimates: list[TaskCostEstimate]
    total_cost_usd: float
    note: str = "Upper-bound estimate using max_tokens for output"


class CostEstimator:
    """Estimates LLM costs before execution.

    Uses LiteLLM's maintained ``model_cost`` map for pricing when
    available, falling back to hardcoded defaults for offline or
    unknown models.

    Args:
        config: The LLMConfig for provider lookups.
        router: The TaskBasedModelRouter for model selection.
    """

    # Hardcoded fallback pricing (per 1k tokens) for when LiteLLM
    # model_cost is unavailable or the model is not listed.
    DEFAULT_COSTS: dict[str, dict[str, float]] = {
        "claude-opus": {"input_per_1k": 0.015, "output_per_1k": 0.075},
        "claude-sonnet": {"input_per_1k": 0.003, "output_per_1k": 0.015},
        "claude-haiku": {"input_per_1k": 0.001, "output_per_1k": 0.005},
        "gpt-4o": {"input_per_1k": 0.005, "output_per_1k": 0.015},
        "gpt-4o-mini": {"input_per_1k": 0.00015, "output_per_1k": 0.0006},
        "gemini-pro": {"input_per_1k": 0.00125, "output_per_1k": 0.005},
        "gemini-flash": {"input_per_1k": 0.000075, "output_per_1k": 0.0003},
        "ollama-llama": {"input_per_1k": 0.0, "output_per_1k": 0.0},
    }

    # Conservative fallback when model is completely unknown.
    _UNKNOWN_COST: dict[str, float] = {
        "input_per_1k": 0.01,
        "output_per_1k": 0.03,
    }

    def __init__(self, config: LLMConfig, router: TaskBasedModelRouter) -> None:
        self._config = config
        self._router = router
        # Build a reverse map from model_name to litellm_model for pricing lookup
        self._model_name_to_litellm: dict[str, str] = {
            p.model_name: p.litellm_model for p in config.providers
        }

    def _get_model_cost(self, model_name: str) -> dict[str, float]:
        """Look up pricing for a model.

        Tries LiteLLM's maintained ``model_cost`` dict first (keyed by
        litellm_model identifier), then falls back to ``DEFAULT_COSTS``
        (keyed by short model name). If neither has the model, returns
        a conservative default.

        Args:
            model_name: The short model name (e.g. "claude-sonnet").

        Returns:
            Dict with ``input_per_1k`` and ``output_per_1k`` keys.
        """
        # Try LiteLLM's maintained pricing first
        litellm_model = self._model_name_to_litellm.get(model_name)
        if litellm_model and hasattr(litellm, "model_cost"):
            litellm_costs = litellm.model_cost
            if isinstance(litellm_costs, dict) and litellm_model in litellm_costs:
                cost_info = litellm_costs[litellm_model]
                input_cost = cost_info.get("input_cost_per_token", 0.0)
                output_cost = cost_info.get("output_cost_per_token", 0.0)
                return {
                    "input_per_1k": input_cost * 1000,
                    "output_per_1k": output_cost * 1000,
                }

        # Fall back to hardcoded defaults
        if model_name in self.DEFAULT_COSTS:
            return self.DEFAULT_COSTS[model_name]

        logger.warning(
            "No pricing data for model '%s', using conservative default",
            model_name,
        )
        return dict(self._UNKNOWN_COST)

    def estimate_single_call(
        self,
        task_type: TaskType,
        estimated_input_tokens: int = 1000,
        max_output_tokens: int = 4096,
    ) -> TaskCostEstimate:
        """Estimate the cost of a single LLM call.

        Routes the task type to determine which model would be used,
        then calculates cost based on token counts and model pricing.

        Args:
            task_type: The type of task being performed.
            estimated_input_tokens: Expected number of input tokens.
            max_output_tokens: Maximum output tokens (upper bound).

        Returns:
            A TaskCostEstimate with the cost prediction.
        """
        model = self._router.route(task_type)
        costs = self._get_model_cost(model)

        estimated_cost = (
            estimated_input_tokens / 1000 * costs["input_per_1k"]
        ) + (max_output_tokens / 1000 * costs["output_per_1k"])

        return TaskCostEstimate(
            task_type=task_type.value,
            model=model,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=max_output_tokens,
            estimated_cost_usd=estimated_cost,
        )

    def estimate_pipeline_cost(
        self,
        tasks: list[tuple[TaskType, int, int]],
    ) -> PipelineCostEstimate:
        """Estimate the total cost of a pipeline execution.

        Args:
            tasks: List of (task_type, estimated_input_tokens, max_output_tokens)
                tuples representing each LLM call in the pipeline.

        Returns:
            A PipelineCostEstimate with per-task breakdowns and total.
        """
        estimates: list[TaskCostEstimate] = []
        total_cost = 0.0

        for task_type, input_tokens, max_output in tasks:
            estimate = self.estimate_single_call(task_type, input_tokens, max_output)
            estimates.append(estimate)
            total_cost += estimate.estimated_cost_usd

        return PipelineCostEstimate(
            estimates=estimates,
            total_cost_usd=total_cost,
            note="Upper-bound estimate using max_tokens for output",
        )
