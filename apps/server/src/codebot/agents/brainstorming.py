"""BrainstormingAgent -- creative brainstorming facilitator for S1 pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract user_input, preferences, similar_projects from shared_state
- reason(): Build LLM message list with brainstorming-oriented system prompt
- act(): Return structured brainstorming output with alternatives, risks, personas
- review(): Validate required keys (refined_requirements, alternatives) are present

Covers requirements BRST-01 through BRST-07:
  BRST-01: Idea exploration
  BRST-02: Solution mapping
  BRST-03: Competitive analysis
  BRST-04: Feature prioritization (MoSCoW/RICE)
  BRST-05: Trade-off analysis
  BRST-06: User persona generation
  BRST-07: MVP scoping
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
You are the Brainstorming Facilitator agent for CodeBot, a multi-agent software
development platform. You operate in the S1 (Brainstorming) pipeline stage,
immediately after the Orchestrator parses the user's project description. Your
purpose is to creatively explore the solution space before formal planning begins.
</role>

<responsibilities>
- BRST-01 Idea Exploration: Generate multiple distinct approaches to the user's
  requirements, including unconventional solutions that the user may not have
  considered. Always produce at least 3 alternatives.
- BRST-02 Solution Mapping: Map each approach to concrete technology choices,
  architectural patterns, and implementation strategies.
- BRST-03 Competitive Analysis: Identify comparable products, open-source
  references, and prior art to inform decision-making.
- BRST-04 Feature Prioritization: Apply MoSCoW (Must/Should/Could/Won't) and
  RICE (Reach, Impact, Confidence, Effort) frameworks to rank features.
- BRST-05 Trade-off Analysis: Evaluate trade-offs across dimensions including
  performance, cost, time-to-market, scalability, and maintainability. Produce
  at least 3 identified risks with mitigation strategies.
- BRST-06 User Persona Generation: Create 2-4 user personas that represent the
  target audience, including their goals, pain points, and usage patterns.
- BRST-07 MVP Scoping: Define the minimum viable product boundary, separating
  essential features from nice-to-haves for iterative delivery.
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "refined_requirements": refined and clarified version of the user's original input
- "alternatives": array of 3-5 solution approaches, each with name, description,
  pros, cons, and recommended_for fields
- "risk_assessment": array of 3+ risks with description, likelihood, impact,
  and mitigation fields
- "feature_priorities": object with "moscow" (categorized features) and
  "rice_scores" (scored feature list) sub-keys
- "user_personas": array of 2-4 persona objects with name, role, goals,
  pain_points, and usage_patterns
- "mvp_scope": object with "included_features", "deferred_features", and
  "rationale" fields
</output_format>

<constraints>
- Always generate at least 3 alternative approaches
- Always identify at least 3 risks with mitigation strategies
- Always use MoSCoW framework for feature prioritization
- Do not assume technical choices -- explore the space first
- Flag implicit assumptions and make them explicit
- If the PRD is too vague, document assumptions rather than guessing silently
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.BRAINSTORM_FACILITATOR)
@dataclass(slots=True, kw_only=True)
class BrainstormingAgent(BaseAgent):
    """Creative brainstorming facilitator for S1 pipeline stage.

    Explores the solution space, generates alternatives, identifies risks,
    prioritizes features, creates user personas, and scopes the MVP.

    Attributes:
        agent_type: Always ``AgentType.BRAINSTORM_FACILITATOR``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for creative tasks).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.BRAINSTORM_FACILITATOR, init=False)
    name: str = "brainstorming"
    model_tier: str = "tier1"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: ["web_search", "idea_matrix", "user_dialog", "reference_finder"]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for BrainstormingAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract brainstorming context from shared state.

        Pulls user_input, preferences, and similar_projects from the
        graph's shared state for use in the reasoning phase.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with user_input, preferences, and similar_projects.
        """
        shared_state = agent_input.shared_state
        return {
            "user_input": shared_state.get("user_input", {}),
            "preferences": shared_state.get("preferences", {}),
            "similar_projects": shared_state.get("similar_projects", []),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for brainstorming.

        Constructs a message sequence with the system prompt and user
        context for the brainstorming facilitator role.

        Args:
            context: Dict with user_input, preferences, similar_projects
                     from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Project input: {context.get('user_input', '')}\n\n"
                    f"User preferences: {context.get('preferences', {})}\n\n"
                    f"Similar projects found: {context.get('similar_projects', [])}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce brainstorming output with alternatives, risks, and personas.

        In the current implementation, returns a structured placeholder
        that downstream agents (Planner, Architect) consume. The actual
        LLM call is handled by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with brainstorming output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "refined_requirements": plan.get("context", {}).get("user_input", ""),
                "alternatives": [],
                "risk_assessment": [],
                "feature_priorities": {},
                "user_personas": [],
                "mvp_scope": {},
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate brainstorming output contains required keys.

        Checks that refined_requirements and alternatives are present
        in the result data.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            brainstorming_output.
        """
        data = result.data
        review_passed = bool(
            "refined_requirements" in data
            and "alternatives" in data
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"brainstorming_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Brainstorming agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
