"""Tests for CostTracker budget tracking and enforcement."""

from __future__ import annotations

import asyncio

import pytest

from codebot.llm.budget import CostRecord, CostTracker
from codebot.llm.config import BudgetConfig
from codebot.llm.schemas import TokenUsage


@pytest.fixture
def budget_config() -> BudgetConfig:
    """Budget config with $50 global, agent_budgets for testing."""
    return BudgetConfig(
        global_budget_usd=50.0,
        warn_threshold=0.8,
        halt_threshold=0.95,
        agent_budgets={"agent-expensive": 10.0, "agent-cheap": 2.0},
    )


@pytest.fixture
def cost_tracker(budget_config: BudgetConfig) -> CostTracker:
    """Create a CostTracker from the budget config fixture."""
    return CostTracker(budget_config)


class TestCostTrackerRecord:
    """Tests for CostTracker.record() accumulation."""

    @pytest.mark.asyncio
    async def test_record_accumulates_cost_per_agent(
        self, cost_tracker: CostTracker
    ) -> None:
        usage = TokenUsage(
            prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.05
        )
        await cost_tracker.record(
            agent_id="agent-1", model="claude-sonnet", stage="S5", usage=usage
        )
        await cost_tracker.record(
            agent_id="agent-1", model="claude-sonnet", stage="S5", usage=usage
        )
        assert cost_tracker.get_agent_cost("agent-1") == pytest.approx(0.10)

    @pytest.mark.asyncio
    async def test_record_accumulates_cost_per_model(
        self, cost_tracker: CostTracker
    ) -> None:
        usage_a = TokenUsage(
            prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.05
        )
        usage_b = TokenUsage(
            prompt_tokens=200, completion_tokens=100, total_tokens=300, cost_usd=0.10
        )
        await cost_tracker.record(
            agent_id="agent-1", model="claude-sonnet", stage="S5", usage=usage_a
        )
        await cost_tracker.record(
            agent_id="agent-2", model="gpt-4o", stage="S6", usage=usage_b
        )
        report = cost_tracker.get_cost_report()
        assert report["by_model"]["claude-sonnet"] == pytest.approx(0.05)
        assert report["by_model"]["gpt-4o"] == pytest.approx(0.10)

    @pytest.mark.asyncio
    async def test_record_accumulates_cost_per_stage(
        self, cost_tracker: CostTracker
    ) -> None:
        usage = TokenUsage(
            prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.05
        )
        await cost_tracker.record(
            agent_id="agent-1", model="claude-sonnet", stage="S5", usage=usage
        )
        await cost_tracker.record(
            agent_id="agent-2", model="gpt-4o", stage="S6", usage=usage
        )
        report = cost_tracker.get_cost_report()
        assert report["by_stage"]["S5"] == pytest.approx(0.05)
        assert report["by_stage"]["S6"] == pytest.approx(0.05)


class TestCostTrackerTotals:
    """Tests for CostTracker total cost and reporting."""

    @pytest.mark.asyncio
    async def test_get_total_cost_returns_sum(
        self, cost_tracker: CostTracker
    ) -> None:
        usage = TokenUsage(
            prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.05
        )
        await cost_tracker.record(
            agent_id="agent-1", model="claude-sonnet", stage="S5", usage=usage
        )
        await cost_tracker.record(
            agent_id="agent-2", model="gpt-4o", stage="S6", usage=usage
        )
        assert cost_tracker.total_cost_usd == pytest.approx(0.10)

    @pytest.mark.asyncio
    async def test_get_agent_cost_returns_zero_for_unknown(
        self, cost_tracker: CostTracker
    ) -> None:
        assert cost_tracker.get_agent_cost("nonexistent") == 0.0

    @pytest.mark.asyncio
    async def test_get_cost_report_structure(
        self, cost_tracker: CostTracker
    ) -> None:
        usage = TokenUsage(
            prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.05
        )
        await cost_tracker.record(
            agent_id="agent-1", model="claude-sonnet", stage="S5", usage=usage
        )
        report = cost_tracker.get_cost_report()
        assert "total_cost_usd" in report
        assert "by_agent" in report
        assert "by_model" in report
        assert "by_stage" in report
        assert "record_count" in report
        assert report["record_count"] == 1
        assert report["total_cost_usd"] == pytest.approx(0.05)
        assert report["by_agent"]["agent-1"] == pytest.approx(0.05)


class TestCostTrackerThresholds:
    """Tests for should_warn() and should_halt() thresholds."""

    @pytest.mark.asyncio
    async def test_should_warn_false_when_under_threshold(
        self, cost_tracker: CostTracker
    ) -> None:
        """Under 80% of $50 = under $40."""
        usage = TokenUsage(
            prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=10.0
        )
        await cost_tracker.record(
            agent_id="agent-1", model="claude-sonnet", stage="S5", usage=usage
        )
        assert not cost_tracker.should_warn()

    @pytest.mark.asyncio
    async def test_should_warn_true_at_threshold(
        self, cost_tracker: CostTracker
    ) -> None:
        """At 80% of $50 = $40."""
        usage = TokenUsage(
            prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=40.0
        )
        await cost_tracker.record(
            agent_id="agent-1", model="claude-sonnet", stage="S5", usage=usage
        )
        assert cost_tracker.should_warn()

    @pytest.mark.asyncio
    async def test_should_halt_false_when_under_threshold(
        self, cost_tracker: CostTracker
    ) -> None:
        """Under 95% of $50 = under $47.50."""
        usage = TokenUsage(
            prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=40.0
        )
        await cost_tracker.record(
            agent_id="agent-1", model="claude-sonnet", stage="S5", usage=usage
        )
        assert not cost_tracker.should_halt()

    @pytest.mark.asyncio
    async def test_should_halt_true_at_threshold(
        self, cost_tracker: CostTracker
    ) -> None:
        """At 95% of $50 = $47.50."""
        usage = TokenUsage(
            prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=47.50
        )
        await cost_tracker.record(
            agent_id="agent-1", model="claude-sonnet", stage="S5", usage=usage
        )
        assert cost_tracker.should_halt()


class TestCostTrackerBudgetCheck:
    """Tests for CostTracker.check_budget() decisions."""

    @pytest.mark.asyncio
    async def test_check_budget_allowed_when_under_budget(
        self, cost_tracker: CostTracker
    ) -> None:
        decision = await cost_tracker.check_budget("agent-1")
        assert decision.allowed is True
        assert decision.remaining == pytest.approx(50.0)

    @pytest.mark.asyncio
    async def test_check_budget_denied_when_over_agent_budget(
        self, cost_tracker: CostTracker
    ) -> None:
        """agent-cheap has $2 budget."""
        usage = TokenUsage(
            prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=1.80
        )
        await cost_tracker.record(
            agent_id="agent-cheap", model="claude-haiku", stage="S5", usage=usage
        )
        decision = await cost_tracker.check_budget(
            "agent-cheap", estimated_cost_usd=0.50
        )
        assert decision.allowed is False
        assert decision.remaining == pytest.approx(0.20)

    @pytest.mark.asyncio
    async def test_check_budget_denied_when_over_global_halt(
        self, cost_tracker: CostTracker
    ) -> None:
        usage = TokenUsage(
            prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=48.0
        )
        await cost_tracker.record(
            agent_id="agent-1", model="claude-sonnet", stage="S5", usage=usage
        )
        decision = await cost_tracker.check_budget("agent-1")
        assert decision.allowed is False
        assert decision.remaining == pytest.approx(2.0)


class TestCostTrackerConcurrency:
    """Tests for CostTracker async-safety via asyncio.Lock."""

    @pytest.mark.asyncio
    async def test_concurrent_records_are_safe(
        self, cost_tracker: CostTracker
    ) -> None:
        """Multiple concurrent record() calls should not lose data."""
        usage = TokenUsage(
            prompt_tokens=10, completion_tokens=5, total_tokens=15, cost_usd=0.01
        )

        async def record_once(agent_id: str) -> None:
            await cost_tracker.record(
                agent_id=agent_id, model="claude-sonnet", stage="S5", usage=usage
            )

        # Run 100 concurrent records
        tasks = [record_once(f"agent-{i}") for i in range(100)]
        await asyncio.gather(*tasks)

        assert cost_tracker.total_cost_usd == pytest.approx(1.0)
        report = cost_tracker.get_cost_report()
        assert report["record_count"] == 100


class TestCostRecord:
    """Tests for the CostRecord model."""

    def test_cost_record_creation(self) -> None:
        usage = TokenUsage(
            prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.05
        )
        record = CostRecord(
            agent_id="agent-1",
            model="claude-sonnet",
            stage="S5",
            usage=usage,
        )
        assert record.agent_id == "agent-1"
        assert record.model == "claude-sonnet"
        assert record.stage == "S5"
        assert record.usage.cost_usd == 0.05
        assert record.timestamp is not None
