"""CodeReviewerAgent -- reviews generated code and enforces quality gate.

Implements the PRA cognitive cycle:
- perceive(): Reads generated source files from shared state
- reason(): Uses LLM to produce structured CodeReviewReport
- act(): Extracts quality gate result from the review report
- review(): Returns AgentOutput with gate_passed determining pipeline advancement

Uses instructor + LiteLLM for structured review output extraction.
Quality gate blocks advancement when critical or high severity issues exist.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import instructor
import litellm
from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<role>
You are an expert code reviewer specializing in Python/FastAPI applications.
You produce thorough, actionable code reviews with specific line references.
</role>

<responsibilities>
- Review code for bugs, logic errors, and incorrect behavior
- Check for style violations and inconsistencies
- Identify performance bottlenecks and inefficiencies
- Detect security vulnerabilities (injection, auth bypass, data exposure)
- Evaluate architecture conformance and design patterns
- Suggest improvements for maintainability and readability
</responsibilities>

<output_format>
Produce a structured review with:
- File-level comments with line numbers, severity, and category
- An overall quality assessment (excellent/good/acceptable/needs_work/poor)
- A gate_passed boolean: True ONLY if there are zero critical or high severity issues
- A concise summary of the review findings
</output_format>

<constraints>
- Set gate_passed=true ONLY when there are zero critical or high severity issues
- Every comment must reference a specific file_path and line range
- Severity must be one of: critical, high, medium, low, info
- Category must be one of: bug, style, performance, security, architecture, suggestion
- Be specific in messages -- explain WHY something is an issue
- Provide suggested_fix when possible
</constraints>
"""

# ---------------------------------------------------------------------------
# Pydantic models for structured review output
# ---------------------------------------------------------------------------


class ReviewComment(BaseModel):
    """A single review comment on generated code."""

    file_path: str
    line_start: int
    line_end: int
    severity: str = Field(description="critical/high/medium/low/info")
    category: str = Field(
        description="bug/style/performance/security/architecture/suggestion"
    )
    message: str
    suggested_fix: str | None = None


class CodeReviewReport(BaseModel):
    """Complete code review output with quality gate decision."""

    comments: list[ReviewComment]
    overall_quality: str = Field(description="excellent/good/acceptable/needs_work/poor")
    gate_passed: bool = Field(description="True if no critical or high severity issues")
    summary: str


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@dataclass(slots=True, kw_only=True)
class CodeReviewerAgent(BaseAgent):
    """Reviews generated code and enforces quality gate.

    Produces a structured CodeReviewReport with file-level comments,
    severity levels, and categories. The quality gate blocks pipeline
    advancement when critical or high severity issues are found.
    """

    agent_type: AgentType = field(default=AgentType.CODE_REVIEWER, init=False)

    async def _initialize(self, agent_input: AgentInput) -> None:
        """Prepare for code review execution.

        Args:
            agent_input: The task input for initialization context.
        """
        # No additional initialization needed

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Read generated source files from shared state.

        Args:
            agent_input: The task input with shared state containing generated files.

        Returns:
            Dict with source_files mapping (path -> content).
        """
        generated_files = agent_input.shared_state.get("backend_dev.generated_files", {})
        return {"source_files": generated_files}

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Call LLM to review code and produce CodeReviewReport.

        Formats source files as markdown code blocks and instructs the LLM
        to produce a structured review. The LLM is instructed to set
        gate_passed=True only if there are zero critical or high severity issues.

        Args:
            context: Dict with source_files from perceive().

        Returns:
            Dict with 'report' key containing the CodeReviewReport.
        """
        client = instructor.from_litellm(litellm.completion)
        source_files = context.get("source_files", {})

        file_contents = "\n\n".join(
            f"### {path}\n```python\n{content}\n```" for path, content in source_files.items()
        )

        user_msg = f"Review this code:\n\n{file_contents}"

        report: CodeReviewReport = client.chat.completions.create(
            model="anthropic/claude-sonnet-4",
            response_model=CodeReviewReport,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_retries=2,
        )

        return {"report": report}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Extract gate result from the CodeReviewReport.

        Args:
            plan: Dict with 'report' key from reason().

        Returns:
            PRAResult with gate_passed, report, and comments data.
        """
        report: CodeReviewReport = plan["report"]

        return PRAResult(
            is_complete=True,
            data={
                "gate_passed": report.gate_passed,
                "report": report.model_dump(),
                "comments": [c.model_dump() for c in report.comments],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Return AgentOutput with review_passed matching gate_passed.

        Stores the full review report, gate_passed boolean, and review
        comments in SharedState for downstream agents.

        Args:
            result: PRAResult from act() with gate decision.

        Returns:
            AgentOutput with review_passed=gate_passed and state_updates.
        """
        data = result.data
        gate_passed = bool(data.get("gate_passed", False))

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={
                "code_review.gate_passed": gate_passed,
                "code_review.report": data.get("report", {}),
                "code_review.comments": data.get("comments", []),
            },
            review_passed=gate_passed,
        )
