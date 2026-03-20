"""Unit tests for extended TesterAgent and DebuggerAgent.

Tests cover:
- Agent type identification and BaseAgent inheritance
- TesterAgent tools include playwright (TEST-03) and docker_sandbox (TEST-04)
- TesterAgent review logic (pass when no failures, fail when tests fail)
- DebuggerAgent tools include security_fix_generator (DBUG-04)
- DebuggerAgent perceive reads security_auditor_output (DBUG-04)
- DebuggerAgent review logic (pass when all fixed, fail when unfixed)
- DebuggerAgent max_fix_iterations default is 3
- YAML config loading for both agents
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml
from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.debugger import DebuggerAgent
from codebot.agents.tester import TesterAgent

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tester_agent() -> TesterAgent:
    """Create a TesterAgent instance."""
    return TesterAgent()


@pytest.fixture
def debugger_agent() -> DebuggerAgent:
    """Create a DebuggerAgent instance."""
    return DebuggerAgent()


@pytest.fixture
def agent_input_with_security() -> AgentInput:
    """Create AgentInput with security_auditor_output in shared state."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={
            "tester_output": {
                "test_files": ["tests/test_main.py"],
                "test_results": {"passed": 8, "failed": 2, "skipped": 0},
            },
            "security_auditor_output": {
                "semgrep_findings": [
                    {"rule_id": "sql-injection", "severity": "high", "file": "src/db.py"}
                ],
                "severity_summary": {"critical": 0, "high": 1, "medium": 0, "low": 0},
                "gate_passed": False,
            },
            "qa_results": {},
        },
        context_tiers={},
    )


# ---------------------------------------------------------------------------
# TesterAgent
# ---------------------------------------------------------------------------


class TestTesterAgentType:
    """TesterAgent has correct type and inheritance."""

    def test_agent_type_is_tester(self, tester_agent: TesterAgent) -> None:
        """agent_type is TESTER."""
        assert tester_agent.agent_type == AgentType.TESTER

    def test_extends_base_agent(self, tester_agent: TesterAgent) -> None:
        """TesterAgent is a subclass of BaseAgent."""
        assert isinstance(tester_agent, BaseAgent)


class TestTesterTools:
    """TesterAgent has expected tools for E2E and sandbox."""

    def test_tools_include_playwright(self, tester_agent: TesterAgent) -> None:
        """tools list includes playwright (TEST-03)."""
        assert "playwright" in tester_agent.tools

    def test_tools_include_docker_sandbox(self, tester_agent: TesterAgent) -> None:
        """tools list includes docker_sandbox (TEST-04)."""
        assert "docker_sandbox" in tester_agent.tools


class TestTesterReview:
    """TesterAgent.review() validates test execution output."""

    async def test_review_passes_when_no_failures(self, tester_agent: TesterAgent) -> None:
        """review() returns review_passed=True when failed == 0."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "test_files": ["tests/test_main.py", "tests/test_api.py"],
                "test_results": {"passed": 10, "failed": 0, "skipped": 0},
                "coverage_report": {},
                "e2e_results": {},
                "sandbox_used": True,
            },
        )
        output = await tester_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_review_fails_when_tests_fail(self, tester_agent: TesterAgent) -> None:
        """review() returns review_passed=False when failed > 0."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "test_files": ["tests/test_main.py"],
                "test_results": {"passed": 8, "failed": 2, "skipped": 0},
                "coverage_report": {},
                "e2e_results": {},
                "sandbox_used": True,
            },
        )
        output = await tester_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestTesterStateUpdates:
    """TesterAgent.review() stores output under tester_output key."""

    async def test_state_updates_use_tester_output_key(
        self, tester_agent: TesterAgent
    ) -> None:
        """state_updates contains tester_output key."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "test_files": ["tests/test_main.py"],
                "test_results": {"passed": 10, "failed": 0, "skipped": 0},
            },
        )
        output = await tester_agent.review(pra_result)
        assert "tester_output" in output.state_updates


# ---------------------------------------------------------------------------
# DebuggerAgent
# ---------------------------------------------------------------------------


class TestDebuggerAgentType:
    """DebuggerAgent has correct type and inheritance."""

    def test_agent_type_is_debugger(self, debugger_agent: DebuggerAgent) -> None:
        """agent_type is DEBUGGER."""
        assert debugger_agent.agent_type == AgentType.DEBUGGER

    def test_extends_base_agent(self, debugger_agent: DebuggerAgent) -> None:
        """DebuggerAgent is a subclass of BaseAgent."""
        assert isinstance(debugger_agent, BaseAgent)


class TestDebuggerTools:
    """DebuggerAgent has expected tools for security debugging."""

    def test_tools_include_security_fix_generator(self, debugger_agent: DebuggerAgent) -> None:
        """tools list includes security_fix_generator (DBUG-04)."""
        assert "security_fix_generator" in debugger_agent.tools


class TestDebuggerPerceive:
    """DebuggerAgent.perceive() reads security findings for DBUG-04."""

    async def test_perceive_reads_security_findings(
        self, debugger_agent: DebuggerAgent, agent_input_with_security: AgentInput
    ) -> None:
        """perceive() includes security_auditor_output key (DBUG-04)."""
        result = await debugger_agent.perceive(agent_input_with_security)
        assert "security_auditor_output" in result
        assert "semgrep_findings" in result["security_auditor_output"]


class TestDebuggerReview:
    """DebuggerAgent.review() validates fix-test loop results."""

    async def test_review_passes_when_all_fixed(self, debugger_agent: DebuggerAgent) -> None:
        """review() returns review_passed=True when retest_results.failed == 0."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "root_cause_analysis": "KeyError in handler due to missing key",
                "fix_patches": [{"file": "src/handlers.py", "hypothesis": "Use .get()"}],
                "security_fixes": [],
                "retest_results": {"passed": 10, "failed": 0},
                "iterations": 1,
            },
        )
        output = await debugger_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_review_fails_when_unfixed(self, debugger_agent: DebuggerAgent) -> None:
        """review() returns review_passed=False when retest_results.failed > 0."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "root_cause_analysis": "Complex race condition",
                "fix_patches": [],
                "security_fixes": [],
                "retest_results": {"passed": 8, "failed": 2},
                "iterations": 1,
            },
        )
        output = await debugger_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestDebuggerMaxIterations:
    """DebuggerAgent has correct max_fix_iterations default."""

    def test_max_fix_iterations_default(self, debugger_agent: DebuggerAgent) -> None:
        """max_fix_iterations defaults to 3."""
        assert debugger_agent.max_fix_iterations == 3


class TestDebuggerStateUpdates:
    """DebuggerAgent.review() stores output under debugger_output key."""

    async def test_state_updates_use_debugger_output_key(
        self, debugger_agent: DebuggerAgent
    ) -> None:
        """state_updates contains debugger_output key."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "root_cause_analysis": "test analysis",
                "retest_results": {"passed": 10, "failed": 0},
                "iterations": 1,
            },
        )
        output = await debugger_agent.review(pra_result)
        assert "debugger_output" in output.state_updates


# ---------------------------------------------------------------------------
# YAML config loading
# ---------------------------------------------------------------------------


class TestYAMLConfigsLoad:
    """YAML configs load and validate for both agents."""

    def test_tester_yaml_loads(self) -> None:
        """tester.yaml parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "tester.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["tester"]["agent_type"] == "TESTER"

    def test_debugger_yaml_loads(self) -> None:
        """debugger.yaml parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "debugger.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["debugger"]["agent_type"] == "DEBUGGER"
