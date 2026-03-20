"""ProjectManagerAgent -- pipeline progress tracking and risk management.

Implements the PRA cognitive cycle:
- perceive(): Extracts all *_output keys and pipeline metrics from shared_state
- reason(): Builds LLM message list with project management-oriented system prompt
- act(): Returns structured status report, timeline, risks, and recommendations
- review(): Validates status_report exists

Tracks pipeline progress, reports status, identifies risks, recommends resource
allocation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.registry import register_agent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<role>
You are the Project Manager agent for CodeBot, a multi-agent software
development platform. Your purpose is to track pipeline progress, report
status, identify risks, and recommend resource allocation.
</role>

<responsibilities>
- Track progress across all pipeline stages (S0-S10)
- Generate status reports with completion percentages and timelines
- Identify risks: stuck agents, slow phases, resource contention, quality issues
- Recommend resource allocation: which agents need more compute, which can be
  deprioritized
- Monitor quality metrics across the pipeline
- Provide timeline estimates based on historical execution data
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "status_report": object with overall_progress, phase_status, blocked_items,
  and quality_metrics
- "timeline": object with estimated_completion, phase_durations, and milestones
- "risks": array of risk objects with description, likelihood (high/medium/low),
  impact (high/medium/low), and mitigation strategy
- "recommendations": array of recommendation strings for improving pipeline
  execution
</output_format>

<constraints>
- Status report must include all active pipeline phases
- Timeline estimates must be based on actual execution metrics, not guesses
- Risks must include concrete mitigation strategies
- Recommendations must be actionable (not vague platitudes)
- Never report false progress -- be accurate about stuck or failed phases
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.PROJECT_MANAGER)
@dataclass(slots=True, kw_only=True)
class ProjectManagerAgent(BaseAgent):
    """Pipeline progress tracker, status reporter, and risk monitor.

    Consumes outputs from all upstream agents and pipeline metrics to
    generate status reports, identify risks, and recommend resource
    allocation.

    Attributes:
        agent_type: Always ``AgentType.PROJECT_MANAGER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.PROJECT_MANAGER, init=False)
    name: str = "project_manager"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "status_reporter",
            "timeline_tracker",
            "risk_monitor",
            "resource_allocator",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for ProjectManagerAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract all output keys and pipeline metrics from shared state.

        Pulls all ``*_output`` keys and pipeline_metrics from the graph's
        shared state for comprehensive status reporting.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with all_outputs and pipeline_metrics.
        """
        shared_state = agent_input.shared_state
        all_outputs: dict[str, Any] = {}
        for key, value in shared_state.items():
            if key.endswith("_output"):
                all_outputs[key] = value

        return {
            "all_outputs": all_outputs,
            "pipeline_metrics": shared_state.get("pipeline_metrics", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for status reporting and risk analysis.

        Args:
            context: Dict with all_outputs and pipeline_metrics from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Agent outputs: {context.get('all_outputs', {})}\n\n"
                    f"Pipeline metrics: {context.get('pipeline_metrics', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce status report, timeline, risks, and recommendations.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with project management output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "status_report": {},
                "timeline": {},
                "risks": [],
                "recommendations": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate project management output contains status report.

        Checks that status_report is present in the result data.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            project_manager_output.
        """
        data = result.data
        review_passed = bool("status_report" in data)

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"project_manager_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Project Manager agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
