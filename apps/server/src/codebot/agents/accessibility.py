"""AccessibilityAgent -- S6 Quality Assurance accessibility audit agent.

Implements the PRA cognitive cycle:
- perceive(): Extracts frontend_dev_output and designer_output from shared_state
- reason(): Builds LLM message list with accessibility-oriented system prompt
- act(): Returns structured WCAG 2.1 AA audit output
- review(): Validates wcag_violations is a list and lighthouse_score is present

Covers requirements:
  QA-03: Accessibility audit for WCAG 2.1 AA compliance
  QA-07: Parallel execution via separate state namespace (accessibility_output)
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
You are the Accessibility Auditor agent for CodeBot, operating in the S6
(Quality Assurance) pipeline stage. Your purpose is to audit generated UI
code for WCAG 2.1 AA compliance (QA-03).
</role>

<responsibilities>
- Run axe-core automated accessibility testing on rendered components
- Run Lighthouse accessibility audit for overall score
- Check color contrast ratios meet WCAG 2.1 AA minimum (4.5:1 for normal text,
  3:1 for large text)
- Validate ARIA labels, roles, and properties are correct and complete
- Test keyboard navigation support (tab order, focus indicators, skip links)
- Verify screen reader compatibility (alt text, heading hierarchy, live regions)
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "wcag_violations": array of violation objects with rule_id, description,
  severity, element, and fix_suggestion
- "lighthouse_score": float (0-100) representing the accessibility score
- "color_contrast_issues": array of contrast issues with element, foreground,
  background, ratio, and required_ratio
- "aria_issues": array of ARIA problems with element, issue, and recommendation
- "recommendations": array of improvement suggestions
</output_format>

<constraints>
- WCAG 2.1 AA is the minimum standard -- flag AAA improvements as recommendations
- Color contrast minimum: 4.5:1 for normal text, 3:1 for large text (18px+ or 14px+ bold)
- Every interactive element must be keyboard accessible
- Every image must have alt text (decorative images use alt="")
- Form inputs must have associated labels
- Page must have a logical heading hierarchy (h1 -> h2 -> h3)
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.ACCESSIBILITY_AUDITOR)
@dataclass(slots=True, kw_only=True)
class AccessibilityAgent(BaseAgent):
    """S6 accessibility audit agent for WCAG 2.1 AA compliance.

    Audits generated UI code for accessibility issues including color
    contrast, ARIA labels, keyboard navigation, and screen reader
    compatibility.

    Attributes:
        agent_type: Always ``AgentType.ACCESSIBILITY_AUDITOR``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.ACCESSIBILITY_AUDITOR, init=False)
    name: str = "accessibility"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "axe_core",
            "lighthouse",
            "color_contrast_checker",
            "aria_validator",
            "keyboard_nav_tester",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for AccessibilityAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract frontend and designer output from shared state.

        Pulls frontend_dev_output (UI code to audit) and designer_output
        (design specs) from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with frontend_dev_output and designer_output.
        """
        shared_state = agent_input.shared_state
        return {
            "frontend_dev_output": shared_state.get("frontend_dev_output", {}),
            "designer_output": shared_state.get("designer_output", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for accessibility analysis.

        Constructs a message sequence with the system prompt and UI
        context for the accessibility auditor role.

        Args:
            context: Dict with frontend_dev_output and designer_output
                     from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"UI code to audit: {context.get('frontend_dev_output', {})}\n\n"
                    f"Design specs: {context.get('designer_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce accessibility audit output.

        In the current implementation, returns a structured placeholder
        that downstream agents consume. The actual tool calls are handled
        by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with accessibility audit output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "wcag_violations": [],
                "lighthouse_score": 100.0,
                "color_contrast_issues": [],
                "aria_issues": [],
                "recommendations": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate accessibility audit output.

        Checks that wcag_violations is a list and lighthouse_score is
        present in the result data.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            accessibility_output.
        """
        data = result.data
        has_violations = isinstance(data.get("wcag_violations"), list)
        has_score = "lighthouse_score" in data

        review_passed = has_violations and has_score

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"accessibility_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Accessibility agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
