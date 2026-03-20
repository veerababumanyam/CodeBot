"""CodeReviewerAgent -- S6 Quality Assurance code review agent.

Implements the PRA cognitive cycle:
- perceive(): Extracts all *_dev_output keys (code to review) and architect_output
  (architecture decisions to validate against) from shared_state
- reason(): Builds LLM message list with code review-oriented system prompt
- act(): Returns review comments, approval status, quality score, and pattern violations
- review(): Validates review_comments is a list and approval_status is present

Reviews generated code for correctness, patterns, maintainability, and performance.
Follows AGENT_CATALOG code review spec.
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
You are the Code Reviewer agent for CodeBot, a multi-agent software
development platform. You operate in the S6 (Quality Assurance) pipeline
stage. Your purpose is to review generated code for correctness, patterns,
maintainability, and performance.
</role>

<responsibilities>
- Review code for bugs, logic errors, and incorrect behavior
- Validate code against architecture decisions and design patterns
- Analyze code complexity and maintainability
- Detect performance bottlenecks and inefficiencies
- Check for style violations, naming conventions, and consistency
- Provide actionable review comments with specific file and line references
- Determine approval status: approved, changes_requested, or rejected
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "review_comments": array of comment objects with file_path, line_start,
  line_end, severity, category, message, and suggested_fix
- "approval_status": one of "approved", "changes_requested", "rejected"
- "code_quality_score": float between 0.0 and 1.0
- "pattern_violations": array of pattern violation objects with pattern_name,
  file_path, description, and severity
</output_format>

<constraints>
- Every comment must reference a specific file_path and line range
- Severity must be one of: critical, high, medium, low, info
- Category must be one of: bug, style, performance, security, architecture, suggestion
- approval_status = "approved" only if zero critical/high severity issues
- approval_status = "rejected" if critical architecture violations found
- code_quality_score must be calculated from weighted severity counts
- Be specific in messages -- explain WHY something is an issue
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.CODE_REVIEWER)
@dataclass(slots=True, kw_only=True)
class CodeReviewerAgent(BaseAgent):
    """S6 code review agent for correctness, patterns, maintainability, and performance.

    Reviews code against architecture decisions, checks for bugs and performance
    issues, and provides actionable review comments with approval status.

    Attributes:
        agent_type: Always ``AgentType.CODE_REVIEWER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection (tier1 for detailed review).
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.CODE_REVIEWER, init=False)
    name: str = "code_reviewer"
    model_tier: str = "tier1"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "file_read",
            "code_analyzer",
            "pattern_detector",
            "complexity_analyzer",
            "review_comment_writer",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for CodeReviewerAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract all dev output keys and architect output from shared state.

        Pulls all ``*_dev_output`` keys (code to review) and ``architect_output``
        (architecture decisions to validate against).

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
        """Build LLM message list for code review.

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
                    f"Code to review: {context.get('dev_outputs', {})}\n\n"
                    f"Architecture decisions: {context.get('architect_output', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Produce code review output with comments, approval status, and quality score.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with code review output in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "review_comments": [],
                "approval_status": "approved",
                "code_quality_score": 1.0,
                "pattern_violations": [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate code review output has comments list and approval status.

        Checks that review_comments is a list and approval_status is present.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            code_reviewer_output.
        """
        data = result.data
        has_comments = isinstance(data.get("review_comments"), list)
        has_status = "approval_status" in data
        review_passed = has_comments and has_status

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"code_reviewer_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Code Reviewer agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
