"""PerformanceAgent -- S6 Quality Assurance performance profiling agent.

Implements the PRA cognitive cycle:
- perceive(): Extracts all *_dev_output keys and architect_output from shared_state
- reason(): Builds LLM message list with performance-oriented system prompt
- act(): Returns structured performance analysis with bottlenecks and optimizations
- review(): Validates bottlenecks is a list and optimization_suggestions is non-empty

Covers requirements:
  QA-04: Performance profiling and bottleneck identification
  QA-07: Parallel execution via separate state namespace (performance_output)
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
You are the Performance Analyst agent for CodeBot, operating in the S6
(Quality Assurance) pipeline stage. Your purpose is to profile generated
code for bottlenecks and identify optimization opportunities (QA-04).
</role>

<responsibilities>
- Run Lighthouse performance audit for web metrics (LCP, FID, CLS, TTFB)
- Analyze webpack/Vite bundle sizes and identify oversized chunks
- Perform load testing to identify throughput limits and response time degradation
- Profile Python code for CPU and memory bottlenecks
- Check bundle sizes against budgets (initial load < 200KB gzipped)
- Run memory profiler to detect leaks and excessive allocation
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "lighthouse_metrics": object with lcp_ms, fid_ms, cls, ttfb_ms, performance_score
- "bundle_analysis": object with total_size_kb, chunk_details, tree_shaking_opportunities
- "bottlenecks": array of bottleneck objects with location, type (cpu/memory/io/network),
  severity, description, and suggested_fix
- "optimization_suggestions": array of suggestion objects with category, description,
  expected_impact, and effort_level
- "load_test_results": object with max_rps, p50_ms, p95_ms, p99_ms, error_rate
</output_format>

<constraints>
- Always identify at least one optimization suggestion (even if code is well-optimized)
- Prioritize suggestions by expected impact (high > medium > low)
- Include both frontend and backend bottlenecks when applicable
- Consider scalability implications, not just current performance
- Flag any O(n^2) or worse algorithmic complexity
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.PERFORMANCE_TESTER)
@dataclass(slots=True, kw_only=True)
class PerformanceAgent(BaseAgent):
    """S6 performance profiling agent for bottleneck identification.

    Profiles generated code for CPU, memory, and I/O bottlenecks.
    Analyzes bundle sizes, runs load tests, and identifies optimization
    opportunities.

    Attributes:
        agent_type: Always ``AgentType.PERFORMANCE_TESTER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.PERFORMANCE_TESTER, init=False)
    name: str = "performance"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "lighthouse",
            "webpack_analyzer",
            "load_tester",
            "profiler",
            "bundle_size_checker",
            "memory_profiler",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for PerformanceAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract all dev output keys and architect output from shared state.

        Pulls all ``*_dev_output`` keys (code to profile) and ``architect_output``
        (architecture specs) from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with dev_outputs and architect_output.
        """
        shared_state = agent_input.shared_state
        dev_outputs: dict[str, Any] = {}
        for key, value in shared_state.items():
            if key.endswith("_dev_output"):
                dev_outputs[key] = value

        return {
            "dev_outputs": dev_outputs,
            "architect_output": shared_state.get("architect_output", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for performance analysis.

        Constructs a message sequence with the system prompt and code
        context for the performance analyst role.

        Args:
            context: Dict with dev_outputs and architect_output from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Code to profile: {context.get('dev_outputs', {})}\n\n"
                    f"Architecture specs: {context.get('architect_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce performance analysis output.

        In the current implementation, returns a structured placeholder
        that downstream agents consume. The actual tool calls are handled
        by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with performance analysis output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "lighthouse_metrics": {},
                "bundle_analysis": {},
                "bottlenecks": [],
                "optimization_suggestions": [
                    {
                        "category": "general",
                        "description": "Review and optimize hot paths",
                        "expected_impact": "medium",
                        "effort_level": "low",
                    }
                ],
                "load_test_results": {},
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate performance analysis output.

        Checks that bottlenecks is a list and optimization_suggestions
        is non-empty.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            performance_output.
        """
        data = result.data
        has_bottlenecks = isinstance(data.get("bottlenecks"), list)
        has_suggestions = bool(data.get("optimization_suggestions"))

        review_passed = has_bottlenecks and has_suggestions

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"performance_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Performance agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
