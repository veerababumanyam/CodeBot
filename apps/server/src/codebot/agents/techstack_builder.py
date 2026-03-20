"""TechStackBuilderAgent -- technology stack advisor for S4 pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract brainstorming_output, research_output, user_preferences
              from shared_state
- reason(): Build LLM message list with tech stack advisory system prompt
- act(): Return structured tech stack output with recommendations,
         alternatives, compatibility matrix, and version pins
- review(): Validate recommended_stack has language, framework, database, hosting

Covers requirement INPT-07:
  INPT-07: User can select or auto-recommend technology stack
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
You are the Technology Stack Advisor agent for CodeBot, a multi-agent
software development platform. You operate in the S4 (Planning) pipeline
stage. Your purpose is to recommend and validate technology choices for the
project, considering performance, ecosystem maturity, team familiarity,
and long-term maintainability.
</role>

<responsibilities>
- INPT-07 Technology Recommendation: When the user has not specified a
  technology stack, analyze project requirements and recommend an optimal
  stack covering language, framework, database, hosting, and key libraries.
  When the user has specified preferences, validate their choices and
  suggest improvements or flag potential issues.
- Stack Validation: Verify compatibility between all chosen technologies.
  Check version compatibility, identify known conflicts, and validate
  that the stack supports all project requirements (e.g., real-time
  features require WebSocket support).
- Alternative Analysis: For each technology choice, provide at least one
  alternative with pros, cons, and migration difficulty. This enables
  informed decision-making and reduces lock-in risk.
- Version Pinning: Recommend specific version ranges for all dependencies,
  considering stability (prefer LTS/stable releases), security patches,
  and feature requirements. Flag any dependencies with known CVEs.
- Performance Profiling: Provide performance characteristics for the
  recommended stack including expected throughput, memory footprint,
  cold start time, and scalability limits. Base estimates on published
  benchmarks where available.
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "recommended_stack": object with "language", "framework", "database",
  "hosting", "frontend_framework", "css_framework", "orm", "testing",
  and "ci_cd" keys, each with name and version
- "alternatives": array of objects with "category" (language|framework|etc.),
  "current_choice", "alternative", "pros", "cons", "migration_difficulty"
- "compatibility_matrix": object mapping technology pairs to compatibility
  status ("compatible", "partial", "incompatible") with notes
- "version_pins": object mapping package names to version ranges with
  rationale for each pin
- "performance_profile": object with "throughput_estimate", "memory_estimate",
  "cold_start_estimate", and "scalability_notes"
</output_format>

<constraints>
- Always provide at least one alternative for each major technology choice
- Never recommend deprecated or end-of-life versions
- Flag any technology with fewer than 1000 GitHub stars (adoption risk)
- Validate that all recommended technologies have active maintainers
- Include license compatibility check (no GPL in proprietary projects)
- Performance estimates must cite sources when available
- Stack must support the project's deployment target (cloud, on-prem, edge)
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.TECH_STACK_ADVISOR)
@dataclass(slots=True, kw_only=True)
class TechStackBuilderAgent(BaseAgent):
    """Technology stack advisor for S4 pipeline stage.

    Recommends and validates technology choices, analyzes alternatives,
    checks compatibility, and provides version pinning recommendations.

    Attributes:
        agent_type: Always ``AgentType.TECH_STACK_ADVISOR``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier2 for tech stack evaluation).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.TECH_STACK_ADVISOR, init=False)
    name: str = "techstack_builder"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "stack_analyzer",
            "compatibility_checker",
            "version_resolver",
            "benchmark_lookup",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for TechStackBuilderAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract tech stack context from shared state.

        Pulls brainstorming_output, research_output, and user_preferences
        from the graph's shared state for use in the reasoning phase.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with brainstorming_output, research_output, and
            user_preferences.
        """
        shared_state = agent_input.shared_state
        return {
            "brainstorming_output": shared_state.get("brainstorming_output", {}),
            "research_output": shared_state.get("research_output", {}),
            "user_preferences": shared_state.get("user_preferences", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for tech stack evaluation.

        Constructs a message sequence with the system prompt and context
        from the brainstorming and research phases for the tech stack
        advisor role.

        Args:
            context: Dict with brainstorming_output, research_output,
                     user_preferences from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Brainstorming output: {context.get('brainstorming_output', {})}\n\n"
                    f"Research output: {context.get('research_output', {})}\n\n"
                    f"User preferences: {context.get('user_preferences', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce tech stack output with recommendations and alternatives.

        In the current implementation, returns a structured placeholder
        that downstream agents consume. The actual LLM call is handled
        by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with tech stack output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "recommended_stack": {},
                "alternatives": [],
                "compatibility_matrix": {},
                "version_pins": {},
                "performance_profile": {},
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate tech stack output contains required keys.

        Checks that recommended_stack has language, framework, database,
        and hosting keys.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            techstack_output.
        """
        data = result.data
        recommended_stack = data.get("recommended_stack", {})

        required_keys = {"language", "framework", "database", "hosting"}
        review_passed = bool(
            isinstance(recommended_stack, dict)
            and required_keys.issubset(recommended_stack.keys())
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"techstack_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the TechStack Builder agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
