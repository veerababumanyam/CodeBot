"""Unit tests for DebuggerAgent (Phase 9 extended implementation).

Tests cover:
- Agent type identification
- PRA cycle methods (perceive, reason, act, review)
- Security debugging support (DBUG-04)
- State updates key
- Max fix iterations default
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from agent_sdk.agents.base import AgentInput, AgentOutput, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.debugger import DebuggerAgent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def shared_state_for_debugger() -> dict[str, Any]:
    """Shared state from TesterAgent with failed test results."""
    return {
        "tester_output": {
            "test_files": ["tests/test_main.py"],
            "test_results": {"passed": 4, "failed": 1, "skipped": 0},
        },
        "security_auditor_output": {
            "semgrep_findings": [
                {"rule_id": "sql-injection", "severity": "high", "file": "src/db.py"}
            ],
            "severity_summary": {"critical": 0, "high": 1, "medium": 0, "low": 0},
        },
        "qa_results": {},
    }


@pytest.fixture
def agent_input_for_debugger(shared_state_for_debugger: dict[str, Any]) -> AgentInput:
    """AgentInput for DebuggerAgent."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state=shared_state_for_debugger,
        context_tiers={},
    )


@pytest.fixture
def debugger_agent() -> DebuggerAgent:
    """Create a DebuggerAgent instance."""
    return DebuggerAgent()


# ---------------------------------------------------------------------------
# Agent type
# ---------------------------------------------------------------------------


class TestDebuggerAgentType:
    """DebuggerAgent has agent_type == AgentType.DEBUGGER."""

    def test_agent_type(self, debugger_agent: DebuggerAgent) -> None:
        assert debugger_agent.agent_type == AgentType.DEBUGGER


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


class TestDebuggerTools:
    """DebuggerAgent has expected tools for security debugging."""

    def test_tools_include_security_fix_generator(self, debugger_agent: DebuggerAgent) -> None:
        """security_fix_generator tool for security-specific debugging (DBUG-04)."""
        assert "security_fix_generator" in debugger_agent.tools

    def test_tools_include_stack_trace_analyzer(self, debugger_agent: DebuggerAgent) -> None:
        """stack_trace_analyzer tool for root cause analysis."""
        assert "stack_trace_analyzer" in debugger_agent.tools

    def test_tools_include_root_cause_analyzer(self, debugger_agent: DebuggerAgent) -> None:
        """root_cause_analyzer tool for failure analysis."""
        assert "root_cause_analyzer" in debugger_agent.tools


# ---------------------------------------------------------------------------
# perceive()
# ---------------------------------------------------------------------------


class TestDebuggerPerceive:
    """DebuggerAgent.perceive() reads test failures and security findings."""

    async def test_perceive_reads_tester_output(
        self, debugger_agent: DebuggerAgent, agent_input_for_debugger: AgentInput
    ) -> None:
        result = await debugger_agent.perceive(agent_input_for_debugger)
        assert "tester_output" in result

    async def test_perceive_reads_security_auditor_output(
        self, debugger_agent: DebuggerAgent, agent_input_for_debugger: AgentInput
    ) -> None:
        """perceive() reads security_auditor_output for DBUG-04."""
        result = await debugger_agent.perceive(agent_input_for_debugger)
        assert "security_auditor_output" in result
        assert "semgrep_findings" in result["security_auditor_output"]


# ---------------------------------------------------------------------------
# review()
# ---------------------------------------------------------------------------


class TestDebuggerReview:
    """DebuggerAgent.review() returns AgentOutput with debug status."""

    async def test_review_returns_passing_status(self, debugger_agent: DebuggerAgent) -> None:
        result = PRAResult(
            is_complete=True,
            data={
                "root_cause_analysis": "KeyError in handler",
                "fix_patches": [{"file": "src/handlers.py"}],
                "security_fixes": [],
                "retest_results": {"passed": 10, "failed": 0},
                "iterations": 1,
            },
        )
        output = await debugger_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True
        assert "debugger_output" in output.state_updates

    async def test_review_returns_failing_status(self, debugger_agent: DebuggerAgent) -> None:
        result = PRAResult(
            is_complete=True,
            data={
                "root_cause_analysis": "Complex race condition",
                "fix_patches": [],
                "security_fixes": [],
                "retest_results": {"passed": 8, "failed": 2},
                "iterations": 1,
            },
        )
        output = await debugger_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


# ---------------------------------------------------------------------------
# Max iterations
# ---------------------------------------------------------------------------


class TestDebuggerConfig:
    """DebuggerAgent has correct configuration defaults."""

    def test_max_fix_iterations_default(self, debugger_agent: DebuggerAgent) -> None:
        """max_fix_iterations defaults to 3."""
        assert debugger_agent.max_fix_iterations == 3

    def test_use_worktree_default(self, debugger_agent: DebuggerAgent) -> None:
        """use_worktree defaults to True."""
        assert debugger_agent.use_worktree is True
