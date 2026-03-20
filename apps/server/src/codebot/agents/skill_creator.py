"""SkillCreatorAgent -- stub for skill creation functionality.

Minimal implementation registered as AgentType.SKILL_MANAGER.
Full skill creation functionality will be implemented in Phase 11.

Implements the PRA cognitive cycle with placeholder outputs.
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
You are the Skill Creator agent. Full functionality will be implemented in Phase 11.
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.SKILL_MANAGER)
@dataclass(slots=True, kw_only=True)
class SkillCreatorAgent(BaseAgent):
    """Stub agent for skill creation -- full implementation in Phase 11.

    Attributes:
        agent_type: Always ``AgentType.SKILL_MANAGER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.SKILL_MANAGER, init=False)
    name: str = "skill_creator"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(default_factory=lambda: ["file_read", "file_write"])

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract context from shared state (stub).

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with shared_state reference.
        """
        return {"shared_state": agent_input.shared_state}

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build action plan (stub).

        Args:
            context: Dict from perceive().

        Returns:
            Dict with stub context.
        """
        return {"context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Return stub output indicating deferred implementation.

        Args:
            plan: Dict from reason().

        Returns:
            PRAResult with stub flag.
        """
        return PRAResult(
            is_complete=True,
            data={"message": "Skill creation deferred to Phase 11", "stub": True},
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate stub output.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed=True and state_updates.
        """
        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"skill_creator_output": result.data},
            review_passed=True,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Skill Creator agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
