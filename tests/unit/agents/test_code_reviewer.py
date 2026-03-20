"""Unit tests for CodeReviewerAgent.

Tests cover:
- Agent type identification
- BaseAgent inheritance
- PRA cycle methods (perceive, reason, act, review)
- Review logic: approval_status and review_comments validation
- State updates key
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def shared_state_with_files() -> dict[str, Any]:
    """Shared state containing generated files from dev agents."""
    return {
        "backend_dev_output": {
            "generated_files": [
                {"path": "src/main.py", "content": "from fastapi import FastAPI\napp = FastAPI()\n"},
            ]
        },
        "frontend_dev_output": {
            "generated_files": [
                {"path": "src/App.tsx", "content": "export default function App() {}"},
            ]
        },
        "architect_output": {"architecture": "microservices", "patterns": ["repository"]},
    }


@pytest.fixture
def agent_input(shared_state_with_files: dict[str, Any]) -> AgentInput:
    """Construct an AgentInput with generated files."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state=shared_state_with_files,
        context_tiers={"l0": {}, "l1": {}},
    )


@pytest.fixture
def reviewer_agent() -> Any:
    """Create a CodeReviewerAgent instance."""
    from codebot.agents.code_reviewer import CodeReviewerAgent

    return CodeReviewerAgent()


# ---------------------------------------------------------------------------
# Agent type
# ---------------------------------------------------------------------------


class TestCodeReviewerAgentType:
    """CodeReviewerAgent has agent_type == AgentType.CODE_REVIEWER."""

    def test_agent_type(self, reviewer_agent: Any) -> None:
        assert reviewer_agent.agent_type == AgentType.CODE_REVIEWER

    def test_extends_base_agent(self, reviewer_agent: Any) -> None:
        assert isinstance(reviewer_agent, BaseAgent)


# ---------------------------------------------------------------------------
# perceive()
# ---------------------------------------------------------------------------


class TestPerceive:
    """CodeReviewerAgent.perceive() reads dev outputs and architect output."""

    async def test_perceive_reads_dev_outputs(
        self, reviewer_agent: Any, agent_input: AgentInput
    ) -> None:
        result = await reviewer_agent.perceive(agent_input)
        assert "dev_outputs" in result
        # Both *_dev_output keys should be captured
        # (Note: only keys ending in _dev_output are captured)

    async def test_perceive_reads_architect_output(
        self, reviewer_agent: Any, agent_input: AgentInput
    ) -> None:
        result = await reviewer_agent.perceive(agent_input)
        assert "architect_output" in result
        assert result["architect_output"]["architecture"] == "microservices"


# ---------------------------------------------------------------------------
# reason()
# ---------------------------------------------------------------------------


class TestReason:
    """CodeReviewerAgent.reason() builds messages for LLM."""

    async def test_reason_returns_messages(self, reviewer_agent: Any) -> None:
        context = {
            "dev_outputs": {"backend_dev_output": {}},
            "architect_output": {},
        }
        result = await reviewer_agent.reason(context)
        assert "messages" in result
        assert len(result["messages"]) == 2  # system + user


# ---------------------------------------------------------------------------
# act()
# ---------------------------------------------------------------------------


class TestAct:
    """CodeReviewerAgent.act() produces review output."""

    async def test_act_returns_pra_result(self, reviewer_agent: Any) -> None:
        plan = {"messages": [], "context": {}}
        result = await reviewer_agent.act(plan)
        assert isinstance(result, PRAResult)
        assert result.is_complete is True

    async def test_act_has_review_keys(self, reviewer_agent: Any) -> None:
        plan = {"messages": [], "context": {}}
        result = await reviewer_agent.act(plan)
        assert "review_comments" in result.data
        assert "approval_status" in result.data
        assert "code_quality_score" in result.data
        assert "pattern_violations" in result.data


# ---------------------------------------------------------------------------
# review()
# ---------------------------------------------------------------------------


class TestReview:
    """CodeReviewerAgent.review() validates output structure."""

    async def test_review_passes_with_valid_output(self, reviewer_agent: Any) -> None:
        result = PRAResult(
            is_complete=True,
            data={
                "review_comments": [],
                "approval_status": "approved",
                "code_quality_score": 1.0,
                "pattern_violations": [],
            },
        )
        output = await reviewer_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True
        assert "code_reviewer_output" in output.state_updates

    async def test_review_fails_without_approval_status(self, reviewer_agent: Any) -> None:
        result = PRAResult(
            is_complete=True,
            data={
                "review_comments": [],
            },
        )
        output = await reviewer_agent.review(result)
        assert output.review_passed is False

    async def test_review_fails_with_non_list_comments(self, reviewer_agent: Any) -> None:
        result = PRAResult(
            is_complete=True,
            data={
                "review_comments": "not a list",
                "approval_status": "approved",
            },
        )
        output = await reviewer_agent.review(result)
        assert output.review_passed is False


# ---------------------------------------------------------------------------
# tools
# ---------------------------------------------------------------------------


class TestTools:
    """CodeReviewerAgent has expected tools."""

    def test_tools_include_code_analyzer(self, reviewer_agent: Any) -> None:
        assert "code_analyzer" in reviewer_agent.tools

    def test_tools_include_pattern_detector(self, reviewer_agent: Any) -> None:
        assert "pattern_detector" in reviewer_agent.tools
