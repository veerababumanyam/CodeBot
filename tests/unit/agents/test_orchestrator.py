"""Unit tests for OrchestratorAgent."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from agent_sdk.agents.base import AgentInput, AgentOutput, PRAResult
from agent_sdk.models.enums import AgentType
from codebot.agents.orchestrator import OrchestratorAgent
from codebot.input.models import (
    AcceptanceCriterion,
    ExtractedRequirements,
    FunctionalRequirement,
)


@pytest.fixture
def agent() -> OrchestratorAgent:
    """Create an OrchestratorAgent instance."""
    return OrchestratorAgent()


@pytest.fixture
def agent_input() -> AgentInput:
    """Create a standard AgentInput with user_input in shared state."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={"user_input": "Build me a todo list API"},
        context_tiers={},
    )


@pytest.fixture
def valid_requirements() -> ExtractedRequirements:
    """Valid ExtractedRequirements with acceptance criteria."""
    return ExtractedRequirements(
        project_name="Todo API",
        project_description="A simple todo list API",
        functional_requirements=[
            FunctionalRequirement(
                id="FR-01",
                title="Create todo",
                description="User can create a new todo item",
                priority="Must",
                acceptance_criteria=[
                    AcceptanceCriterion(
                        description="POST /todos returns 201",
                        test_strategy="integration_test",
                    )
                ],
                confidence=0.95,
            ),
        ],
        non_functional_requirements=["Response time < 200ms"],
        constraints=["Python 3.12+"],
        ambiguities=[],
    )


@pytest.fixture
def empty_requirements() -> ExtractedRequirements:
    """ExtractedRequirements with no functional requirements."""
    return ExtractedRequirements(
        project_name="Empty",
        project_description="Nothing extracted",
        functional_requirements=[],
        non_functional_requirements=[],
        constraints=[],
        ambiguities=[],
    )


class TestOrchestratorAgentType:
    """OrchestratorAgent has correct agent_type."""

    def test_agent_type_is_orchestrator(self, agent: OrchestratorAgent) -> None:
        assert agent.agent_type == AgentType.ORCHESTRATOR


class TestOrchestratorPerceive:
    """OrchestratorAgent.perceive() returns context dict."""

    async def test_perceive_returns_user_input_and_format(
        self,
        agent: OrchestratorAgent,
        agent_input: AgentInput,
    ) -> None:
        """perceive() returns dict with user_input and input_format keys."""
        result = await agent.perceive(agent_input)
        assert "user_input" in result
        assert "input_format" in result
        assert result["user_input"] == "Build me a todo list API"
        assert result["input_format"] == "natural_language"


class TestOrchestratorReason:
    """OrchestratorAgent.reason() calls RequirementExtractor.extract()."""

    async def test_reason_calls_extractor(
        self,
        agent: OrchestratorAgent,
        valid_requirements: ExtractedRequirements,
    ) -> None:
        """reason() calls RequirementExtractor.extract() and returns requirements dict."""
        with patch(
            "codebot.agents.orchestrator.RequirementExtractor"
        ) as mock_cls:
            mock_instance = mock_cls.return_value
            mock_instance.extract = AsyncMock(return_value=valid_requirements)

            context = {
                "user_input": "Build me a todo API",
                "input_format": "natural_language",
            }
            result = await agent.reason(context)

            assert "requirements" in result
            assert "needs_clarification" in result
            assert isinstance(result["requirements"], ExtractedRequirements)
            mock_instance.extract.assert_awaited_once_with("Build me a todo API")


class TestOrchestratorAct:
    """OrchestratorAgent.act() stores requirements."""

    async def test_act_returns_requirements(
        self,
        agent: OrchestratorAgent,
        valid_requirements: ExtractedRequirements,
    ) -> None:
        """act() returns PRAResult with requirements."""
        plan = {
            "requirements": valid_requirements,
            "needs_clarification": False,
        }
        result = await agent.act(plan)
        assert isinstance(result, PRAResult)
        assert result.is_complete is True
        assert result.data["requirements"] is valid_requirements


class TestOrchestratorReview:
    """OrchestratorAgent.review() validates output."""

    async def test_review_passed_with_valid_requirements(
        self,
        agent: OrchestratorAgent,
        valid_requirements: ExtractedRequirements,
    ) -> None:
        """review() returns AgentOutput with review_passed=True when requirements are valid."""
        pra_result = PRAResult(
            is_complete=True,
            data={"requirements": valid_requirements},
        )
        output = await agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_review_failed_with_empty_requirements(
        self,
        agent: OrchestratorAgent,
        empty_requirements: ExtractedRequirements,
    ) -> None:
        """review() returns AgentOutput with review_passed=False when no FRs extracted."""
        pra_result = PRAResult(
            is_complete=True,
            data={"requirements": empty_requirements},
        )
        output = await agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestOrchestratorSystemPrompt:
    """OrchestratorAgent has SYSTEM_PROMPT and build_system_prompt()."""

    def test_system_prompt_exists(self, agent: OrchestratorAgent) -> None:
        """build_system_prompt() returns a non-empty string."""
        prompt = agent.build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
