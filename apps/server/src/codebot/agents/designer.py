"""DesignerAgent -- UI/UX designer for S3 pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract research_output, project_requirements, architect_output
              from shared_state
- reason(): Build LLM message list with design-oriented system prompt
- act(): Return structured design output with wireframes, component hierarchy,
         design tokens, and responsive specs
- review(): Validate wireframes and component_hierarchy exist

Covers requirement ARCH-04:
  ARCH-04: UI/UX wireframe generation and component hierarchy creation
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
You are the UI/UX Designer agent for CodeBot, a multi-agent software
development platform. You operate in the S3 (Architecture & Design) pipeline
stage, alongside other architecture agents. Your purpose is to design the
user interface, create wireframes, define the component hierarchy, establish
design tokens, and specify responsive behavior.
</role>

<responsibilities>
- ARCH-04 Wireframe Generation: Create low-to-medium fidelity wireframes
  for all primary user flows. Each wireframe includes layout structure,
  component placement, interaction annotations, and navigation flow.
- Component Hierarchy: Design the React component tree with clear
  parent-child relationships, prop interfaces, and state ownership.
  Identify shared/reusable components and layout components.
- Design Token System: Define a comprehensive design token set including
  colors (primary, secondary, accent, semantic), typography scale,
  spacing scale, border radii, shadows, and breakpoints. Tokens must
  support light and dark themes.
- Responsive Specifications: Define responsive behavior for mobile (< 768px),
  tablet (768px - 1024px), and desktop (> 1024px) breakpoints. Specify
  which components reflow, collapse, or hide at each breakpoint.
- Accessibility: Ensure designs meet WCAG 2.1 AA standards including
  color contrast ratios (4.5:1 for text), focus indicators, and
  semantic HTML structure recommendations.
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "wireframes": array of wireframe objects with page_name, layout,
  components (array), interactions (array), and navigation_targets
- "component_hierarchy": tree structure with component_name, children,
  props, state_ownership, and reusable (boolean) fields
- "design_tokens": object with colors, typography, spacing, borders,
  shadows, and breakpoints sub-keys
- "responsive_specs": object keyed by breakpoint (mobile, tablet, desktop)
  with layout_changes, hidden_components, and reflow_rules
- "accessibility_notes": array of accessibility considerations with
  wcag_criterion, component, and recommendation fields
</output_format>

<constraints>
- All wireframes must include navigation and error states
- Component hierarchy must identify reusable vs page-specific components
- Design tokens must support theming (at minimum light and dark)
- Responsive specs must cover at least 3 breakpoints
- Color choices must meet WCAG 2.1 AA contrast requirements (4.5:1)
- Do not prescribe specific CSS framework -- output framework-agnostic tokens
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.DESIGNER)
@dataclass(slots=True, kw_only=True)
class DesignerAgent(BaseAgent):
    """UI/UX designer for S3 pipeline stage.

    Creates wireframes, defines component hierarchy, establishes design
    tokens, and specifies responsive behavior for the application UI.

    Attributes:
        agent_type: Always ``AgentType.DESIGNER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for design reasoning).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.DESIGNER, init=False)
    name: str = "designer"
    model_tier: str = "tier1"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "wireframe_generator",
            "component_tree_builder",
            "color_palette",
            "layout_designer",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for DesignerAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract design context from shared state.

        Pulls research_output, project_requirements, and architect_output
        from the graph's shared state for use in the reasoning phase.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with research_output, project_requirements, and
            architect_output.
        """
        shared_state = agent_input.shared_state
        return {
            "research_output": shared_state.get("research_output", {}),
            "project_requirements": shared_state.get("project_requirements", {}),
            "architect_output": shared_state.get("architect_output", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for UI/UX design.

        Constructs a message sequence with the system prompt and context
        from the research and architecture phases for the designer role.

        Args:
            context: Dict with research_output, project_requirements,
                     architect_output from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Research output: {context.get('research_output', {})}\n\n"
                    f"Project requirements: {context.get('project_requirements', {})}\n\n"
                    f"Architecture output: {context.get('architect_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce design output with wireframes and component hierarchy.

        In the current implementation, returns a structured placeholder
        that downstream agents (TemplateCurator, Planner) consume. The
        actual LLM call is handled by the AgentNode wrapper at graph
        execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with design output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "wireframes": [],
                "component_hierarchy": {},
                "design_tokens": {},
                "responsive_specs": {},
                "accessibility_notes": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate design output contains required keys.

        Checks that wireframes and component_hierarchy are present
        in the result data.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            designer_output.
        """
        data = result.data
        review_passed = bool(
            "wireframes" in data
            and "component_hierarchy" in data
        )

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"designer_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Designer agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
