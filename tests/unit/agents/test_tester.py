"""Unit tests for TesterAgent (Phase 9 extended implementation).

Tests cover:
- Agent type identification
- PRA cycle methods (perceive, reason, act, review)
- Playwright E2E support (TEST-03)
- Docker sandbox support (TEST-04)
- State updates key
- Sandbox config defaults
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from agent_sdk.agents.base import AgentInput, AgentOutput, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.tester import TesterAgent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def shared_state_for_tester() -> dict[str, Any]:
    """Shared state with dev outputs for TesterAgent."""
    return {
        "backend_dev_output": {
            "files": {"src/main.py": "from fastapi import FastAPI\napp = FastAPI()"},
        },
        "frontend_dev_output": {
            "files": {"App.tsx": "export default function App() { return <div /> }"},
        },
        "planner_output": {
            "acceptance_criteria": ["Health endpoint returns 200"],
        },
    }


@pytest.fixture
def agent_input_for_tester(shared_state_for_tester: dict[str, Any]) -> AgentInput:
    """AgentInput with shared state for TesterAgent."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state=shared_state_for_tester,
        context_tiers={},
    )


@pytest.fixture
def tester_agent() -> TesterAgent:
    """Create a TesterAgent instance."""
    return TesterAgent()


# ---------------------------------------------------------------------------
# TesterAgent type and tools
# ---------------------------------------------------------------------------


class TestTesterAgentType:
    """TesterAgent has agent_type == AgentType.TESTER."""

    def test_agent_type(self, tester_agent: TesterAgent) -> None:
        assert tester_agent.agent_type == AgentType.TESTER


class TestTesterTools:
    """TesterAgent has expected tools including Playwright and Docker."""

    def test_tools_include_playwright(self, tester_agent: TesterAgent) -> None:
        """Playwright tool for E2E testing (TEST-03)."""
        assert "playwright" in tester_agent.tools

    def test_tools_include_docker_sandbox(self, tester_agent: TesterAgent) -> None:
        """Docker sandbox tool for isolated test execution (TEST-04)."""
        assert "docker_sandbox" in tester_agent.tools

    def test_tools_include_test_runner(self, tester_agent: TesterAgent) -> None:
        """test_runner tool for executing tests."""
        assert "test_runner" in tester_agent.tools


# ---------------------------------------------------------------------------
# TesterAgent perceive
# ---------------------------------------------------------------------------


class TestTesterPerceive:
    """TesterAgent.perceive() reads dev outputs from shared state."""

    async def test_perceive_reads_dev_outputs(
        self, tester_agent: TesterAgent, agent_input_for_tester: AgentInput
    ) -> None:
        result = await tester_agent.perceive(agent_input_for_tester)
        assert "dev_outputs" in result
        assert "backend_dev_output" in result["dev_outputs"]

    async def test_perceive_reads_planner_output(
        self, tester_agent: TesterAgent, agent_input_for_tester: AgentInput
    ) -> None:
        result = await tester_agent.perceive(agent_input_for_tester)
        assert "planner_output" in result


# ---------------------------------------------------------------------------
# TesterAgent review
# ---------------------------------------------------------------------------


class TestTesterReview:
    """TesterAgent.review() sets tester_output in state_updates."""

    async def test_review_sets_review_passed_true(self, tester_agent: TesterAgent) -> None:
        result = PRAResult(
            is_complete=True,
            data={
                "test_files": ["tests/test_main.py"],
                "test_results": {"passed": 5, "failed": 0, "skipped": 0},
            },
        )
        output = await tester_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True
        assert "tester_output" in output.state_updates

    async def test_review_sets_review_passed_false_on_failure(
        self, tester_agent: TesterAgent
    ) -> None:
        result = PRAResult(
            is_complete=True,
            data={
                "test_files": ["tests/test_main.py"],
                "test_results": {"passed": 3, "failed": 2, "skipped": 0},
            },
        )
        output = await tester_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


# ---------------------------------------------------------------------------
# TesterAgent sandbox config
# ---------------------------------------------------------------------------


class TestTesterSandboxConfig:
    """TesterAgent has sandbox configuration defaults."""

    def test_sandbox_config_defaults(self, tester_agent: TesterAgent) -> None:
        """sandbox_config has Docker defaults."""
        assert tester_agent.sandbox_config["use_docker"] is True
        assert tester_agent.sandbox_config["image"] == "python:3.12-slim"
        assert tester_agent.sandbox_config["timeout"] == 120

    def test_use_worktree_default(self, tester_agent: TesterAgent) -> None:
        """use_worktree defaults to True."""
        assert tester_agent.use_worktree is True
