"""TemplateCuratorAgent -- template selection and scaffolding for S3 pipeline stage.

Implements the PRA cognitive cycle:
- perceive(): Extract designer_output, tech_stack, user_preferences
              from shared_state
- reason(): Build LLM message list with template-selection system prompt
- act(): Return structured template output with selected template,
         config, and scaffold files
- review(): Validate selected_template exists

Covers requirement INPT-06:
  INPT-06: Template selection supporting Shadcn/ui, Tailwind UI,
           Material Design, and custom templates
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
You are the Template Curator agent for CodeBot, a multi-agent software
development platform. You operate in the S3 (Architecture & Design) pipeline
stage. Your purpose is to select and configure the appropriate UI component
template/framework for the project, and generate initial scaffold files.
</role>

<responsibilities>
- INPT-06 Template Selection: Select the most appropriate UI component
  framework based on project requirements and user preferences. Supported
  frameworks include:
  * Shadcn/ui -- headless, accessible React components with Tailwind CSS
  * Tailwind UI -- commercial Tailwind component library
  * Material Design (MUI) -- Google's design system for React
  * Custom templates -- user-provided component libraries
  Evaluate each option against project needs (accessibility, bundle size,
  customization, design consistency).
- Template Configuration: Generate framework-specific configuration files
  including theme definitions, component overrides, and build integration
  settings.
- Scaffold Generation: Produce initial project scaffold files including
  directory structure, base components, layout templates, and configuration
  boilerplate specific to the selected framework.
- Compatibility Validation: Ensure the selected template is compatible with
  the chosen tech stack (React version, build tool, CSS strategy).
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "selected_template": object with "name" (e.g., "shadcn-ui"), "version",
  "rationale" (why selected), and "compatibility_score" (0.0-1.0)
- "template_config": object with framework-specific configuration including
  theme, variants, and build settings
- "scaffold_files": array of objects with "path", "content_type"
  (component|config|layout|style), and "description"
- "alternatives_considered": array of objects with "name", "pros", "cons",
  and "rejection_reason" for non-selected options
</output_format>

<constraints>
- Always evaluate at least 2 template options before selecting
- Justify template selection with concrete criteria (not preference)
- Ensure selected template supports the project's accessibility requirements
- Scaffold must include at minimum: layout component, theme config, and
  one example page component
- Do not hard-code framework versions -- use compatible version ranges
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.TEMPLATE_CURATOR)
@dataclass(slots=True, kw_only=True)
class TemplateCuratorAgent(BaseAgent):
    """Template curator for S3 pipeline stage.

    Selects and configures UI component templates (Shadcn/ui, Tailwind UI,
    Material Design, custom), generates scaffold files, and validates
    framework compatibility.

    Attributes:
        agent_type: Always ``AgentType.TEMPLATE_CURATOR``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier2 for template selection).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.TEMPLATE_CURATOR, init=False)
    name: str = "template_curator"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "template_registry",
            "scaffold_generator",
            "config_renderer",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for TemplateCuratorAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract template selection context from shared state.

        Pulls designer_output, tech_stack, and user_preferences from
        the graph's shared state for use in the reasoning phase.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with designer_output, tech_stack, and user_preferences.
        """
        shared_state = agent_input.shared_state
        return {
            "designer_output": shared_state.get("designer_output", {}),
            "tech_stack": shared_state.get("tech_stack", {}),
            "user_preferences": shared_state.get("user_preferences", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for template selection.

        Constructs a message sequence with the system prompt and context
        from the design phase for the template curator role.

        Args:
            context: Dict with designer_output, tech_stack,
                     user_preferences from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Design output: {context.get('designer_output', {})}\n\n"
                    f"Tech stack: {context.get('tech_stack', {})}\n\n"
                    f"User preferences: {context.get('user_preferences', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce template output with selection and scaffold.

        In the current implementation, returns a structured placeholder
        that downstream agents consume. The actual LLM call is handled
        by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with template output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "selected_template": {},
                "template_config": {},
                "scaffold_files": [],
                "alternatives_considered": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate template output contains required keys.

        Checks that selected_template is present in the result data.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            template_output.
        """
        data = result.data
        review_passed = bool("selected_template" in data)

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"template_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Template Curator agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
