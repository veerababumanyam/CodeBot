"""Unit tests for BackendDevAgent.

Tests cover:
- Agent type identification
- BaseAgent inheritance
- PRA cycle methods (perceive, reason, act, review)
- use_worktree attribute
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
def shared_state() -> dict[str, Any]:
    """Sample shared state with planning and architecture outputs."""
    return {
        "planner_output": {"task_graph": []},
        "architect_output": {"architecture": "microservices"},
        "api_designer_output": {"endpoints": [{"method": "POST", "path": "/todos"}]},
        "database_output": {"models": []},
        "techstack_output": {"language": "python", "framework": "fastapi"},
    }


@pytest.fixture
def agent_input(shared_state: dict[str, Any]) -> AgentInput:
    """Construct an AgentInput with sample data."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state=shared_state,
        context_tiers={
            "l0": {"conventions": "Use Pydantic v2, async/await, Google docstrings."},
        },
    )


@pytest.fixture
def backend_agent() -> Any:
    """Create a BackendDevAgent instance."""
    from codebot.agents.backend_dev import BackendDevAgent

    return BackendDevAgent()


# ---------------------------------------------------------------------------
# Agent type
# ---------------------------------------------------------------------------


class TestBackendDevAgentType:
    """BackendDevAgent has agent_type == AgentType.BACKEND_DEV."""

    def test_agent_type(self, backend_agent: Any) -> None:
        assert backend_agent.agent_type == AgentType.BACKEND_DEV

    def test_extends_base_agent(self, backend_agent: Any) -> None:
        assert isinstance(backend_agent, BaseAgent)


# ---------------------------------------------------------------------------
# perceive()
# ---------------------------------------------------------------------------


class TestPerceive:
    """BackendDevAgent.perceive() assembles upstream outputs."""

    async def test_perceive_returns_planner_output(
        self, backend_agent: Any, agent_input: AgentInput
    ) -> None:
        result = await backend_agent.perceive(agent_input)
        assert "planner_output" in result

    async def test_perceive_returns_architect_output(
        self, backend_agent: Any, agent_input: AgentInput
    ) -> None:
        result = await backend_agent.perceive(agent_input)
        assert "architect_output" in result
        assert result["architect_output"]["architecture"] == "microservices"

    async def test_perceive_returns_api_designer_output(
        self, backend_agent: Any, agent_input: AgentInput
    ) -> None:
        result = await backend_agent.perceive(agent_input)
        assert "api_designer_output" in result

    async def test_perceive_returns_database_output(
        self, backend_agent: Any, agent_input: AgentInput
    ) -> None:
        result = await backend_agent.perceive(agent_input)
        assert "database_output" in result

    async def test_perceive_returns_techstack_output(
        self, backend_agent: Any, agent_input: AgentInput
    ) -> None:
        result = await backend_agent.perceive(agent_input)
        assert "techstack_output" in result


# ---------------------------------------------------------------------------
# reason()
# ---------------------------------------------------------------------------


class TestReason:
    """BackendDevAgent.reason() builds LLM messages."""

    async def test_reason_returns_messages(self, backend_agent: Any) -> None:
        context = {
            "planner_output": {},
            "architect_output": {},
            "api_designer_output": {},
            "database_output": {},
            "techstack_output": {},
        }
        result = await backend_agent.reason(context)
        assert "messages" in result
        assert len(result["messages"]) == 2  # system + user


# ---------------------------------------------------------------------------
# act()
# ---------------------------------------------------------------------------


class TestAct:
    """BackendDevAgent.act() produces generated code output."""

    async def test_act_returns_pra_result(self, backend_agent: Any) -> None:
        plan = {"messages": [], "context": {}}
        result = await backend_agent.act(plan)
        assert isinstance(result, PRAResult)
        assert result.is_complete is True

    async def test_act_has_generated_files_key(self, backend_agent: Any) -> None:
        plan = {"messages": [], "context": {}}
        result = await backend_agent.act(plan)
        assert "generated_files" in result.data
        assert "api_endpoints" in result.data
        assert "db_models" in result.data
        assert "test_stubs" in result.data


# ---------------------------------------------------------------------------
# review()
# ---------------------------------------------------------------------------


class TestReview:
    """BackendDevAgent.review() validates generated output."""

    async def test_review_passes_with_generated_files(
        self, backend_agent: Any
    ) -> None:
        result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [{"path": "src/main.py", "content": "..."}],
                "api_endpoints": [],
                "db_models": [],
                "test_stubs": [],
            },
        )
        output = await backend_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True
        assert "backend_dev_output" in output.state_updates

    async def test_review_passes_with_empty_generated_files(
        self, backend_agent: Any
    ) -> None:
        """Review passes if generated_files key exists (even if list is empty)."""
        result = PRAResult(
            is_complete=True,
            data={
                "generated_files": [],
            },
        )
        output = await backend_agent.review(result)
        assert output.review_passed is True


# ---------------------------------------------------------------------------
# use_worktree
# ---------------------------------------------------------------------------


class TestWorktree:
    """BackendDevAgent has use_worktree=True for parallel execution."""

    def test_use_worktree(self, backend_agent: Any) -> None:
        assert backend_agent.use_worktree is True
