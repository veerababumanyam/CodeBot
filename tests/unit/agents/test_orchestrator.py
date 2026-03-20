"""Unit tests for OrchestratorAgent.

Tests cover:
- Agent type identification
- BaseAgent inheritance
- PRA cycle methods (perceive, reason, act, review)
- Multi-modal input tools (INPT-03)
- Codebase import tools (INPT-08)
- State updates key
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.orchestrator import SYSTEM_PROMPT, OrchestratorAgent


@pytest.fixture
def agent() -> OrchestratorAgent:
    """Create an OrchestratorAgent instance."""
    return OrchestratorAgent()


@pytest.fixture
def agent_input() -> AgentInput:
    """Create a standard AgentInput with user_input in shared state."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={
            "user_input": {"text": "Build me a todo list API", "images": [], "urls": []},
            "project_config": {"name": "Todo API"},
            "pipeline_state": {},
            "existing_codebase": None,
        },
        context_tiers={},
    )


class TestOrchestratorAgentType:
    """OrchestratorAgent has correct agent_type."""

    def test_agent_type_is_orchestrator(self, agent: OrchestratorAgent) -> None:
        assert agent.agent_type == AgentType.ORCHESTRATOR

    def test_extends_base_agent(self, agent: OrchestratorAgent) -> None:
        assert isinstance(agent, BaseAgent)


class TestOrchestratorPerceive:
    """OrchestratorAgent.perceive() returns context dict."""

    async def test_perceive_returns_user_input(
        self, agent: OrchestratorAgent, agent_input: AgentInput
    ) -> None:
        result = await agent.perceive(agent_input)
        assert "user_input" in result
        assert result["user_input"]["text"] == "Build me a todo list API"

    async def test_perceive_returns_project_config(
        self, agent: OrchestratorAgent, agent_input: AgentInput
    ) -> None:
        result = await agent.perceive(agent_input)
        assert "project_config" in result
        assert result["project_config"]["name"] == "Todo API"

    async def test_perceive_returns_pipeline_state(
        self, agent: OrchestratorAgent, agent_input: AgentInput
    ) -> None:
        result = await agent.perceive(agent_input)
        assert "pipeline_state" in result

    async def test_perceive_returns_existing_codebase(
        self, agent: OrchestratorAgent, agent_input: AgentInput
    ) -> None:
        result = await agent.perceive(agent_input)
        assert "existing_codebase" in result


class TestOrchestratorReason:
    """OrchestratorAgent.reason() builds LLM messages."""

    async def test_reason_returns_messages(self, agent: OrchestratorAgent) -> None:
        context = {
            "user_input": {},
            "project_config": {},
            "pipeline_state": {},
            "existing_codebase": None,
        }
        result = await agent.reason(context)
        assert "messages" in result
        assert len(result["messages"]) == 2  # system + user


class TestOrchestratorAct:
    """OrchestratorAgent.act() produces pipeline plan."""

    async def test_act_returns_pra_result(self, agent: OrchestratorAgent) -> None:
        plan = {"messages": [], "context": {}}
        result = await agent.act(plan)
        assert isinstance(result, PRAResult)
        assert result.is_complete is True

    async def test_act_has_pipeline_plan(self, agent: OrchestratorAgent) -> None:
        plan = {"messages": [], "context": {}}
        result = await agent.act(plan)
        assert "pipeline_plan" in result.data
        assert "stage_configs" in result.data
        assert "agent_assignments" in result.data
        assert "input_processed" in result.data
        assert "imported_codebase" in result.data


class TestOrchestratorReview:
    """OrchestratorAgent.review() validates output."""

    async def test_review_passes_with_pipeline_plan(
        self, agent: OrchestratorAgent
    ) -> None:
        result = PRAResult(
            is_complete=True,
            data={
                "pipeline_plan": {"stages": ["S0", "S1"]},
                "stage_configs": [],
                "agent_assignments": [],
                "input_processed": {},
                "imported_codebase": None,
            },
        )
        output = await agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True
        assert "orchestrator_output" in output.state_updates

    async def test_review_passes_with_empty_pipeline_plan(
        self, agent: OrchestratorAgent
    ) -> None:
        """Even an empty pipeline_plan dict counts as 'present'."""
        result = PRAResult(
            is_complete=True,
            data={"pipeline_plan": {}},
        )
        output = await agent.review(result)
        assert output.review_passed is True


class TestOrchestratorSystemPrompt:
    """OrchestratorAgent has SYSTEM_PROMPT and build_system_prompt()."""

    def test_system_prompt_exists(self, agent: OrchestratorAgent) -> None:
        prompt = agent.build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_system_prompt_mentions_multimodal(self) -> None:
        """INPT-03: System prompt mentions multi-modal input."""
        assert "multi-modal" in SYSTEM_PROMPT.lower() or "multimodal" in SYSTEM_PROMPT.lower()

    def test_system_prompt_mentions_codebase_import(self) -> None:
        """INPT-08: System prompt mentions codebase import."""
        assert "codebase" in SYSTEM_PROMPT.lower()


class TestOrchestratorTools:
    """OrchestratorAgent tools for INPT-03 and INPT-08."""

    def test_has_multimodal_input_processor(self, agent: OrchestratorAgent) -> None:
        assert "multimodal_input_processor" in agent.tools

    def test_has_git_importer(self, agent: OrchestratorAgent) -> None:
        assert "git_importer" in agent.tools

    def test_has_local_codebase_loader(self, agent: OrchestratorAgent) -> None:
        assert "local_codebase_loader" in agent.tools

    def test_has_pipeline_controller(self, agent: OrchestratorAgent) -> None:
        assert "pipeline_controller" in agent.tools
