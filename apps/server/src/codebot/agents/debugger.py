"""DebuggerAgent -- S8 debugger with security-specific debugging support.

Implements the PRA cognitive cycle:
- perceive(): Reads tester_output, security_auditor_output, qa_results from shared_state
- reason(): Uses root cause analysis to identify failures and security issues
- act(): Runs fix-test loop with patches, re-tests, and security fixes
- review(): Validates root_cause_analysis exists and retest_results.failed == 0 or
            iterations >= max_retries; review_passed is True when failed == 0

Covers requirements:
  DBUG-04: Security-specific debugging (parses SecurityAuditorAgent findings,
           generates input validation, SQL injection prevention, XSS mitigation,
           secret removal fixes)
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
You are the Debugger and Fixer agent for CodeBot, operating in the S8
(Debug & Fix) pipeline stage. You perform root cause analysis on test
failures and generate targeted fixes, including security-specific fixes.
</role>

<responsibilities>
- Perform root cause analysis on test failures from the TesterAgent
- Generate fix proposals as minimal, targeted patches
- Apply patches and re-run tests in a fix-test loop (max 3 iterations)
- Parse SecurityAuditorAgent findings for security-specific debugging (DBUG-04):
  * Input validation fixes
  * SQL injection prevention
  * XSS mitigation
  * Secret removal from source code
- Track experiment history with KEEP/DISCARD semantics
</responsibilities>

<output_format>
Produce a JSON object with the following top-level keys:
- "root_cause_analysis": description of the identified root cause
- "fix_patches": array of patch objects with file, original, fixed, and hypothesis
- "security_fixes": array of security-specific fix objects with vulnerability_type,
  file, fix_description, and severity
- "retest_results": object with "passed" and "failed" integer counts
- "iterations": integer count of fix-test loop iterations performed
</output_format>

<constraints>
- Change only what is necessary to fix the identified issue
- Do not refactor or reorganize code beyond the fix
- Ensure fixes don't introduce new issues
- Maximum 3 fix-test iterations before returning results
- Security fixes take priority over general bug fixes
- Preserve type annotations and docstrings
</constraints>
"""


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.DEBUGGER)
@dataclass(slots=True, kw_only=True)
class DebuggerAgent(BaseAgent):
    """S8 debugger with security-specific debugging and fix-test loop.

    Performs root cause analysis on test failures and security findings.
    Generates targeted patches, applies them, and re-runs tests in a
    loop until all pass or max iterations reached.

    Attributes:
        agent_type: Always ``AgentType.DEBUGGER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
        use_worktree: Whether to use git worktree for isolation.
        max_fix_iterations: Maximum fix-test loop iterations.
    """

    agent_type: AgentType = field(default=AgentType.DEBUGGER, init=False)
    name: str = "debugger"
    model_tier: str = "tier1"
    max_retries: int = 2
    use_worktree: bool = True
    max_fix_iterations: int = 3
    tools: list[str] = field(
        default_factory=lambda: [
            "file_read",
            "file_write",
            "file_edit",
            "bash",
            "test_runner",
            "stack_trace_analyzer",
            "root_cause_analyzer",
            "security_fix_generator",
        ]
    )

    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for DebuggerAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Extract tester output, security findings, and QA results from shared state.

        Pulls tester_output (failed tests), security_auditor_output
        (security findings for DBUG-04), and qa_results from the
        graph's shared state.

        Args:
            agent_input: The task input with shared_state.

        Returns:
            Dict with tester_output, security_auditor_output, and qa_results.
        """
        shared_state = agent_input.shared_state
        return {
            "tester_output": shared_state.get("tester_output", {}),
            "security_auditor_output": shared_state.get("security_auditor_output", {}),
            "qa_results": shared_state.get("qa_results", {}),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build LLM message list for root cause analysis.

        Constructs a message sequence with the system prompt and failure
        context for the debugger role.

        Args:
            context: Dict with tester_output, security_auditor_output,
                     qa_results from perceive().

        Returns:
            Dict with messages list and context for the act phase.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Test failures: {context.get('tester_output', {})}\n\n"
                    f"Security findings: {context.get('security_auditor_output', {})}\n\n"
                    f"QA results: {context.get('qa_results', {})}"
                ),
            },
        ]
        return {"messages": messages, "context": context}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Run fix-test loop with patches and re-tests.

        In the current implementation, returns a structured placeholder
        that downstream agents consume. The actual fix-test loop is
        handled by the AgentNode wrapper at graph execution time.

        Args:
            plan: Dict with messages and context from reason().

        Returns:
            PRAResult with fix-test loop results in data.
        """
        return PRAResult(
            is_complete=True,
            data={
                "root_cause_analysis": "Placeholder analysis",
                "fix_patches": [],
                "security_fixes": [],
                "retest_results": {
                    "passed": 0,
                    "failed": 0,
                },
                "iterations": 0,
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate debug output and fix-test loop results.

        Checks that root_cause_analysis exists and retest_results.failed == 0
        OR iterations >= max_fix_iterations. review_passed is True when
        retest_results.failed == 0.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            debugger_output.
        """
        data = result.data
        has_analysis = bool(data.get("root_cause_analysis"))

        retest_results = data.get("retest_results", {})
        failed_count = retest_results.get("failed", 0)
        iterations = data.get("iterations", 0)

        # Valid if analysis exists AND (all fixed OR max iterations reached)
        structurally_valid = has_analysis and (
            failed_count == 0 or iterations >= self.max_fix_iterations
        )

        # review_passed only when all tests actually pass
        review_passed = structurally_valid and failed_count == 0

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"debugger_output": data},
            review_passed=review_passed,
        )

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Debugger agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
