"""Tests for SkillCreatorAgent -- full implementation (Phase 11).

Verifies the PRA cognitive cycle for extracting reusable code patterns
into skills, including SkillService integration and event bus publishing.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType


@pytest.fixture
def mock_skill_service() -> AsyncMock:
    """Mock SkillService with create_skill and activate_skill stubs."""
    service = AsyncMock()
    service.create_skill = AsyncMock(side_effect=lambda s: s)
    service.activate_skill = AsyncMock(side_effect=lambda sid: MagicMock(id=sid))
    return service


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    """Mock EventBus with publish stub."""
    return AsyncMock()


@pytest.fixture
def agent() -> Any:
    """Create a SkillCreatorAgent instance."""
    from codebot.agents.skill_creator_agent import SkillCreatorAgent

    return SkillCreatorAgent()


@pytest.fixture
def agent_input() -> AgentInput:
    """Create a standard AgentInput for testing."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={},
        context_tiers={},
    )


class TestSkillCreatorAgent:
    """Tests for SkillCreatorAgent conventions and PRA cycle."""

    def test_agent_type(self, agent: Any) -> None:
        """Agent type must be SKILL_MANAGER (existing enum value)."""
        assert agent.agent_type == AgentType.SKILL_MANAGER

    def test_dataclass_conventions(self, agent: Any) -> None:
        """Verify the agent follows @dataclass(slots=True, kw_only=True) conventions."""
        assert hasattr(agent, "__slots__")
        assert agent.agent_type == AgentType.SKILL_MANAGER

    def test_extends_base_agent(self, agent: Any) -> None:
        """Agent must extend BaseAgent."""
        assert isinstance(agent, BaseAgent)

    def test_has_name_field(self, agent: Any) -> None:
        """Agent must have a human-readable name."""
        assert agent.name == "skill_creator"

    async def test_perceive_extracts_code_context(
        self, agent: Any, agent_input: AgentInput
    ) -> None:
        """Perceive extracts code_files, execution_logs, existing_skills from shared_state."""
        agent_input.shared_state = {
            "code_files": ["a.py", "b.py"],
            "execution_logs": ["log1"],
            "existing_skills": ["existing-skill-1"],
        }
        result = await agent.perceive(agent_input)
        assert result["code_files"] == ["a.py", "b.py"]
        assert result["execution_logs"] == ["log1"]
        assert result["existing_skills"] == ["existing-skill-1"]

    async def test_perceive_handles_missing_keys(
        self, agent: Any, agent_input: AgentInput
    ) -> None:
        """Perceive returns empty defaults when keys are missing."""
        agent_input.shared_state = {}
        result = await agent.perceive(agent_input)
        assert result["code_files"] == []
        assert result["execution_logs"] == []
        assert result["existing_skills"] == []

    async def test_reason_builds_extraction_plan(self, agent: Any) -> None:
        """Reason builds an extraction plan from perceived context."""
        context = {
            "code_files": ["auth.py", "crud.py"],
            "existing_skills": [],
        }
        plan = await agent.reason(context)
        assert "patterns_to_extract" in plan
        assert "existing_skills" in plan

    async def test_act_creates_skills(
        self,
        agent: Any,
        mock_skill_service: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Act creates skills via SkillService and publishes events."""
        from codebot.agents.skill_creator_agent import ExtractedPattern

        agent.set_services(skill_service=mock_skill_service, event_bus=mock_event_bus)

        pattern = ExtractedPattern(
            name="auth-jwt",
            description="JWT authentication pattern",
            parameterized_code="def auth(): ...",
            applicable_agents=["backend_dev"],
            tags=["auth", "jwt"],
        )
        plan = {"extracted_patterns": [pattern]}
        result = await agent.act(plan)
        assert result.is_complete
        assert len(result.data["created_skills"]) == 1
        mock_skill_service.create_skill.assert_called_once()
        mock_skill_service.activate_skill.assert_called_once()
        mock_event_bus.publish.assert_called_once()

    async def test_act_handles_service_error(
        self,
        agent: Any,
        mock_skill_service: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Act handles SkillService errors gracefully."""
        from codebot.agents.skill_creator_agent import ExtractedPattern

        mock_skill_service.create_skill.side_effect = ValueError("Duplicate skill")
        agent.set_services(skill_service=mock_skill_service, event_bus=mock_event_bus)

        pattern = ExtractedPattern(
            name="bad",
            description="",
            parameterized_code="",
            applicable_agents=["x"],
        )
        plan = {"extracted_patterns": [pattern]}
        result = await agent.act(plan)
        assert result.is_complete
        assert len(result.data["errors"]) > 0
        assert "Duplicate skill" in result.data["errors"][0]

    async def test_act_with_empty_patterns(
        self,
        agent: Any,
        mock_skill_service: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Act with empty patterns returns success with no created skills."""
        agent.set_services(skill_service=mock_skill_service, event_bus=mock_event_bus)
        result = await agent.act({"extracted_patterns": []})
        assert result.is_complete
        assert result.data["created_skills"] == []
        assert result.data["errors"] == []

    async def test_review_validates_output(self, agent: Any) -> None:
        """Review validates and formats the PRA output."""
        pra_result = PRAResult(
            is_complete=True,
            data={"created_skills": ["id1"], "errors": []},
        )
        output = await agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed
        assert "skill_creator_output" in output.state_updates

    def test_build_system_prompt(self, agent: Any) -> None:
        """Agent has a system prompt."""
        prompt = agent.build_system_prompt()
        assert "Skill Creator" in prompt
        assert len(prompt) > 50
