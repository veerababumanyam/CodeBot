"""Budget tracking and enforcement for the Multi-LLM abstraction layer.

Records per-agent, per-model, and per-stage token usage and cost.
Enforces global and per-agent budget limits with warn/halt thresholds.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from codebot.llm.config import BudgetConfig
from codebot.llm.schemas import BudgetDecision, TokenUsage


class CostRecord(BaseModel):
    """A single cost record for an LLM call.

    Attributes:
        agent_id: The agent that made the call.
        model: The model identifier used.
        stage: The pipeline stage (e.g. "S5").
        usage: Token usage and cost from the call.
        timestamp: When the call was recorded.
    """

    agent_id: str
    model: str
    stage: str
    usage: TokenUsage
    timestamp: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))


class CostTracker:
    """Tracks cumulative LLM costs and enforces budget limits.

    Records cost per agent, per model, and per pipeline stage.
    Provides warn/halt threshold checks for budget enforcement
    and per-agent budget limits.

    Uses an asyncio.Lock to ensure thread-safe concurrent access
    to cost accumulation state.

    Args:
        budget_config: Budget configuration with global limits and thresholds.
    """

    def __init__(self, budget_config: BudgetConfig) -> None:
        self._global_budget_usd = budget_config.global_budget_usd
        self._warn_threshold = budget_config.warn_threshold
        self._halt_threshold = budget_config.halt_threshold
        self._agent_budgets: dict[str, float] = dict(budget_config.agent_budgets)

        self._records: list[CostRecord] = []
        self._total_cost_usd: float = 0.0
        self._agent_costs: dict[str, float] = defaultdict(float)
        self._model_costs: dict[str, float] = defaultdict(float)
        self._stage_costs: dict[str, float] = defaultdict(float)
        self._lock = asyncio.Lock()

    async def record(
        self,
        *,
        agent_id: str,
        model: str,
        stage: str,
        usage: TokenUsage,
    ) -> None:
        """Record a cost entry from an LLM call.

        Acquires an asyncio lock to ensure concurrent safety when
        multiple agents record costs simultaneously.

        Args:
            agent_id: The agent that made the call.
            model: The model identifier used.
            stage: The pipeline stage (e.g. "S5").
            usage: Token usage and cost from the call.
        """
        async with self._lock:
            record = CostRecord(
                agent_id=agent_id,
                model=model,
                stage=stage,
                usage=usage,
            )
            self._records.append(record)
            self._total_cost_usd += usage.cost_usd
            self._agent_costs[agent_id] += usage.cost_usd
            self._model_costs[model] += usage.cost_usd
            self._stage_costs[stage] += usage.cost_usd

    @property
    def total_cost_usd(self) -> float:
        """Return the total accumulated cost in USD."""
        return self._total_cost_usd

    def get_agent_cost(self, agent_id: str) -> float:
        """Return the accumulated cost for a specific agent.

        Args:
            agent_id: The agent identifier to look up.

        Returns:
            Accumulated cost in USD, or 0.0 if no records exist.
        """
        return self._agent_costs.get(agent_id, 0.0)

    def get_cost_report(self) -> dict[str, Any]:
        """Return a cost breakdown report.

        Returns:
            Dictionary with keys: total_cost_usd, by_agent, by_model,
            by_stage, record_count.
        """
        return {
            "total_cost_usd": self._total_cost_usd,
            "by_agent": dict(self._agent_costs),
            "by_model": dict(self._model_costs),
            "by_stage": dict(self._stage_costs),
            "record_count": len(self._records),
        }

    def should_warn(self) -> bool:
        """Check if total cost has reached the warning threshold.

        Returns:
            True if total cost >= global_budget * warn_threshold.
        """
        return self._total_cost_usd >= self._global_budget_usd * self._warn_threshold

    def should_halt(self) -> bool:
        """Check if total cost has reached the halt threshold.

        Returns:
            True if total cost >= global_budget * halt_threshold.
        """
        return self._total_cost_usd >= self._global_budget_usd * self._halt_threshold

    async def check_budget(
        self,
        agent_id: str,
        estimated_cost_usd: float = 0.0,
    ) -> BudgetDecision:
        """Check whether a new LLM call is permitted within budget.

        Checks global halt threshold first, then per-agent budget limits.

        Args:
            agent_id: The agent requesting the call.
            estimated_cost_usd: Estimated cost of the upcoming call.

        Returns:
            BudgetDecision indicating whether the call is allowed
            and how much budget remains.
        """
        # Global halt check
        if self.should_halt():
            remaining = max(0.0, self._global_budget_usd - self._total_cost_usd)
            return BudgetDecision(allowed=False, remaining=remaining)

        # Per-agent budget check
        if agent_id in self._agent_budgets:
            agent_limit = self._agent_budgets[agent_id]
            agent_cost = self._agent_costs.get(agent_id, 0.0)
            if agent_cost + estimated_cost_usd > agent_limit:
                remaining = max(0.0, agent_limit - agent_cost)
                return BudgetDecision(allowed=False, remaining=remaining)

        # Under budget
        remaining = self._global_budget_usd - self._total_cost_usd
        return BudgetDecision(allowed=True, remaining=remaining)
