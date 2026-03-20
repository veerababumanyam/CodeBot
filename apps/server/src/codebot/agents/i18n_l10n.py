"""I18nL10nAgent -- S6 Quality Assurance internationalization verification agent.

Implements the PRA cognitive cycle:
- perceive(): Extracts frontend_dev_output and mobile_dev_output from shared_state
- reason(): Builds LLM message list with i18n-oriented system prompt
- act(): Returns structured i18n analysis with hardcoded strings and completeness
- review(): Validates hardcoded_strings is a list and completeness_score is present

Covers requirements:
  QA-05: Internationalization and localization verification
  QA-07: Parallel execution via separate state namespace (i18n_output)
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
You are the i18n/L10n Specialist agent for CodeBot, operating in the S6
(Quality Assurance) pipeline stage. Your purpose is to verify
internationalization completeness and localization readiness (QA-05).
</role>

<responsibilities>
- Extract hardcoded user-facing strings from source code that should be
  externalized to translation files
- Configure i18n framework setup (react-intl, i18next, gettext, etc.)
- Run pseudo-localization to detect layout issues with longer translations
- Validate RTL (right-to-left) language support for Arabic, Hebrew, etc.
- Check translation file completeness across supported locales
- Verify date/time, number, and currency formatting uses locale-aware APIs
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "hardcoded_strings": array of objects with file, line, string, and context
  describing user-facing strings that should be externalized
- "i18n_config": object describing the i18n framework configuration and setup status
- "missing_translations": array of objects with key, locale, and context for
  translation keys missing in specific locales
- "rtl_issues": array of objects with file, element, issue, and fix_suggestion
  for RTL layout problems
- "completeness_score": float (0-100) representing overall i18n readiness
</output_format>

<constraints>
- Only flag genuinely user-facing strings (not log messages, error codes, etc.)
- Consider pluralization rules for different languages
- Verify that string concatenation is not used for translated strings
- Check that format strings use named parameters (not positional)
- RTL validation is required for any app supporting Arabic, Hebrew, Farsi, or Urdu
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.I18N_SPECIALIST)
@dataclass(slots=True, kw_only=True)
class I18nL10nAgent(BaseAgent):
    """S6 internationalization verification agent.

    Extracts hardcoded strings, configures i18n framework, validates
    RTL support, and checks translation completeness.

    Attributes:
        agent_type: Always ``AgentType.I18N_SPECIALIST``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.I18N_SPECIALIST, init=False)
    name: str = "i18n_l10n"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "string_extractor",
            "i18n_configurator",
            "pseudo_localizer",
            "rtl_validator",
            "translation_validator",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for I18nL10nAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract frontend and mobile dev output from shared state.

        Pulls frontend_dev_output and mobile_dev_output (code with
        user-facing strings) from the graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with frontend_dev_output and mobile_dev_output.
        """
        shared_state = agent_input.shared_state
        return {
            "frontend_dev_output": shared_state.get("frontend_dev_output", {}),
            "mobile_dev_output": shared_state.get("mobile_dev_output", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for i18n analysis.

        Constructs a message sequence with the system prompt and code
        context for the i18n specialist role.

        Args:
            context: Dict with frontend_dev_output and mobile_dev_output
                     from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Frontend code: {context.get('frontend_dev_output', {})}\n\n"
                    f"Mobile code: {context.get('mobile_dev_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce i18n analysis output.

        In the current implementation, returns a structured placeholder
        that downstream agents consume. The actual tool calls are handled
        by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with i18n analysis output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "hardcoded_strings": [],
                "i18n_config": {},
                "missing_translations": [],
                "rtl_issues": [],
                "completeness_score": 100.0,
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate i18n analysis output.

        Checks that hardcoded_strings is a list and completeness_score
        is present in the result data.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            i18n_output.
        """
        data = result.data
        has_strings = isinstance(data.get("hardcoded_strings"), list)
        has_score = "completeness_score" in data

        review_passed = has_strings and has_score

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"i18n_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the i18n/L10n agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
