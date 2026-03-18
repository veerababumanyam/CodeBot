"""Tests for CostEstimator pre-execution cost predictions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from codebot.llm.config import BudgetConfig, LLMConfig, ProviderConfig
from codebot.llm.estimator import CostEstimator, PipelineCostEstimate, TaskCostEstimate
from codebot.llm.providers import ProviderRegistry
from codebot.llm.router import TaskBasedModelRouter
from codebot.llm.schemas import RoutingRule, TaskType


@pytest.fixture
def estimator_config() -> LLMConfig:
    """Create a minimal LLMConfig for estimator tests."""
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
                model_name="claude-haiku",
                litellm_model="anthropic/claude-haiku-3.5",
                api_key_env="ANTHROPIC_API_KEY",
            ),
        ],
        routing_table={
            "CODE_GENERATION": RoutingRule(
                primary_model="claude-sonnet",
                fallback_models=["gpt-4o"],
                reason="Code gen",
            ),
            "SIMPLE_TRANSFORM": RoutingRule(
                primary_model="claude-haiku",
                fallback_models=["claude-sonnet"],
                reason="Simple tasks",
            ),
        },
        budget=BudgetConfig(global_budget_usd=50.0),
    )


@pytest.fixture
def estimator(estimator_config: LLMConfig) -> CostEstimator:
    """Create a CostEstimator from config."""
    registry = ProviderRegistry(estimator_config)
    router = TaskBasedModelRouter(estimator_config, registry)
    return CostEstimator(estimator_config, router)


class TestCostEstimatorSingleCall:
    """Tests for CostEstimator.estimate_single_call()."""

    def test_estimate_single_call_returns_task_cost_estimate(
        self, estimator: CostEstimator
    ) -> None:
        result = estimator.estimate_single_call(
            TaskType.CODE_GENERATION,
            estimated_input_tokens=1000,
            max_output_tokens=4096,
        )
        assert isinstance(result, TaskCostEstimate)
        assert result.task_type == "CODE_GENERATION"
        assert result.model == "claude-sonnet"
        assert result.estimated_input_tokens == 1000
        assert result.estimated_output_tokens == 4096
        assert result.estimated_cost_usd > 0.0

    def test_estimate_single_call_uses_hardcoded_defaults(
        self, estimator: CostEstimator
    ) -> None:
        """When litellm.model_cost is empty, use DEFAULT_COSTS."""
        with patch("codebot.llm.estimator.litellm") as mock_litellm:
            mock_litellm.model_cost = {}
            result = estimator.estimate_single_call(
                TaskType.CODE_GENERATION,
                estimated_input_tokens=1000,
                max_output_tokens=1000,
            )
            # claude-sonnet: input=0.003/1k, output=0.015/1k
            # cost = (1000/1000 * 0.003) + (1000/1000 * 0.015) = 0.018
            assert result.estimated_cost_usd == pytest.approx(0.018)

    def test_estimate_uses_litellm_model_cost_when_available(
        self, estimator: CostEstimator
    ) -> None:
        """Prefer litellm.model_cost over hardcoded defaults."""
        with patch("codebot.llm.estimator.litellm") as mock_litellm:
            mock_litellm.model_cost = {
                "anthropic/claude-sonnet-4": {
                    "input_cost_per_token": 0.000005,  # $5/1M = $0.005/1k
                    "output_cost_per_token": 0.000025,  # $25/1M = $0.025/1k
                }
            }
            result = estimator.estimate_single_call(
                TaskType.CODE_GENERATION,
                estimated_input_tokens=1000,
                max_output_tokens=1000,
            )
            # cost = (1000 * 0.000005) + (1000 * 0.000025) = 0.005 + 0.025 = 0.030
            assert result.estimated_cost_usd == pytest.approx(0.030)


class TestCostEstimatorPipeline:
    """Tests for CostEstimator.estimate_pipeline_cost()."""

    def test_estimate_pipeline_cost_sums_tasks(
        self, estimator: CostEstimator
    ) -> None:
        tasks = [
            (TaskType.CODE_GENERATION, 1000, 4096),
            (TaskType.SIMPLE_TRANSFORM, 500, 2048),
        ]
        result = estimator.estimate_pipeline_cost(tasks)
        assert isinstance(result, PipelineCostEstimate)
        assert len(result.estimates) == 2
        assert result.total_cost_usd > 0.0
        assert result.total_cost_usd == pytest.approx(
            sum(e.estimated_cost_usd for e in result.estimates)
        )
        assert "upper-bound" in result.note.lower() or "Upper" in result.note

    def test_estimate_pipeline_cost_empty_tasks(
        self, estimator: CostEstimator
    ) -> None:
        result = estimator.estimate_pipeline_cost([])
        assert isinstance(result, PipelineCostEstimate)
        assert result.total_cost_usd == 0.0
        assert len(result.estimates) == 0


class TestCostEstimatorFallbackPricing:
    """Tests for fallback pricing when model is unknown."""

    def test_unknown_model_uses_conservative_default(
        self, estimator: CostEstimator
    ) -> None:
        """Unknown model should use conservative default pricing."""
        with patch("codebot.llm.estimator.litellm") as mock_litellm:
            mock_litellm.model_cost = {}
            # Mock the router to return an unknown model
            estimator._router = MagicMock()
            estimator._router.route.return_value = "unknown-model-xyz"

            result = estimator.estimate_single_call(
                TaskType.CODE_GENERATION,
                estimated_input_tokens=1000,
                max_output_tokens=1000,
            )
            # Conservative default: input=0.01/1k, output=0.03/1k
            # cost = (1000/1000 * 0.01) + (1000/1000 * 0.03) = 0.04
            assert result.estimated_cost_usd == pytest.approx(0.04)


class TestPipelineCostEstimate:
    """Tests for PipelineCostEstimate and TaskCostEstimate models."""

    def test_task_cost_estimate_fields(self) -> None:
        estimate = TaskCostEstimate(
            task_type="CODE_GENERATION",
            model="claude-sonnet",
            estimated_input_tokens=1000,
            estimated_output_tokens=4096,
            estimated_cost_usd=0.065,
        )
        assert estimate.task_type == "CODE_GENERATION"
        assert estimate.model == "claude-sonnet"
        assert estimate.estimated_cost_usd == 0.065

    def test_pipeline_cost_estimate_fields(self) -> None:
        estimates = [
            TaskCostEstimate(
                task_type="CODE_GENERATION",
                model="claude-sonnet",
                estimated_input_tokens=1000,
                estimated_output_tokens=4096,
                estimated_cost_usd=0.065,
            ),
        ]
        pipeline = PipelineCostEstimate(
            estimates=estimates,
            total_cost_usd=0.065,
            note="Upper-bound estimate",
        )
        assert pipeline.total_cost_usd == 0.065
        assert len(pipeline.estimates) == 1
