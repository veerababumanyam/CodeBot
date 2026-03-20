"""Unit tests for S4 Planning agents (Planner, TechStack Builder)."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import yaml
from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.planner import SYSTEM_PROMPT as PLANNER_SYSTEM_PROMPT
from codebot.agents.planner import PlannerAgent
from codebot.agents.techstack_builder import SYSTEM_PROMPT as TECHSTACK_SYSTEM_PROMPT
from codebot.agents.techstack_builder import TechStackBuilderAgent

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def planner_agent() -> PlannerAgent:
    """Create a PlannerAgent instance."""
    return PlannerAgent()


@pytest.fixture
def techstack_agent() -> TechStackBuilderAgent:
    """Create a TechStackBuilderAgent instance."""
    return TechStackBuilderAgent()


@pytest.fixture
def planner_input() -> AgentInput:
    """Create a standard AgentInput for PlannerAgent."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={
            "architect_output": {"architecture_doc": "system arch doc"},
            "designer_output": {"wireframes": []},
            "database_output": {"database_schema": {}},
            "api_designer_output": {"api_spec": {}},
            "research_output": {"research_report": "summary"},
            "project_requirements": {"name": "test project"},
        },
        context_tiers={},
    )


@pytest.fixture
def techstack_input() -> AgentInput:
    """Create a standard AgentInput for TechStackBuilderAgent."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={
            "brainstorming_output": {"alternatives": []},
            "research_output": {"library_evaluations": []},
            "user_preferences": {"language": "python"},
        },
        context_tiers={},
    )


# ---------------------------------------------------------------------------
# PlannerAgent tests
# ---------------------------------------------------------------------------


class TestPlannerAgentType:
    """PlannerAgent has correct type and inheritance."""

    def test_agent_type(self, planner_agent: PlannerAgent) -> None:
        """agent_type is PLANNER."""
        assert planner_agent.agent_type == AgentType.PLANNER

    def test_extends_base_agent(self, planner_agent: PlannerAgent) -> None:
        """PlannerAgent is a subclass of BaseAgent."""
        assert isinstance(planner_agent, BaseAgent)

    def test_system_prompt_not_empty(self) -> None:
        """SYSTEM_PROMPT is non-empty and mentions planning."""
        assert len(PLANNER_SYSTEM_PROMPT) > 0
        assert "planner" in PLANNER_SYSTEM_PROMPT.lower()


class TestPlannerPerceive:
    """PlannerAgent.perceive() extracts context."""

    async def test_perceive_reads_architecture_outputs(
        self, planner_agent: PlannerAgent, planner_input: AgentInput
    ) -> None:
        """perceive() returns dict with all architecture outputs."""
        result = await planner_agent.perceive(planner_input)
        assert "architect_output" in result
        assert "designer_output" in result
        assert "database_output" in result
        assert "api_designer_output" in result
        assert "research_output" in result
        assert "project_requirements" in result


class TestPlannerReview:
    """PlannerAgent.review() validates output."""

    async def test_review_passes_with_valid_task_graph(
        self, planner_agent: PlannerAgent
    ) -> None:
        """review() returns review_passed=True when task_graph is valid."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "task_graph": [
                    {
                        "id": "TASK-001",
                        "title": "Create database schema",
                        "description": "Design and create the PostgreSQL schema",
                        "target_files": ["apps/server/src/models.py"],
                        "acceptance_criteria": ["Schema creates successfully"],
                        "estimated_complexity": "medium",
                        "dependencies": [],
                        "parallel_group": None,
                    }
                ],
                "execution_order": [["TASK-001"]],
            },
        )
        output = await planner_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_review_passes_with_empty_task_graph(
        self, planner_agent: PlannerAgent
    ) -> None:
        """review() returns review_passed=True for empty task_graph (placeholder)."""
        pra_result = PRAResult(
            is_complete=True,
            data={"task_graph": []},
        )
        output = await planner_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_review_fails_with_invalid_task_structure(
        self, planner_agent: PlannerAgent
    ) -> None:
        """review() returns review_passed=False when task missing required keys."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "task_graph": [
                    {
                        "id": "TASK-001",
                        "title": "Incomplete task",
                        # Missing: target_files, acceptance_criteria, estimated_complexity
                    }
                ],
            },
        )
        output = await planner_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False

    async def test_review_validates_task_structure(
        self, planner_agent: PlannerAgent
    ) -> None:
        """review() validates each task has title, target_files, acceptance_criteria, estimated_complexity."""
        # Valid task with all required keys
        valid_task = {
            "id": "TASK-001",
            "title": "Setup database",
            "target_files": ["models.py"],
            "acceptance_criteria": ["Tables exist"],
            "estimated_complexity": "low",
        }
        pra_result = PRAResult(
            is_complete=True,
            data={"task_graph": [valid_task]},
        )
        output = await planner_agent.review(pra_result)
        assert output.review_passed is True

        # Invalid task missing acceptance_criteria
        invalid_task = {
            "id": "TASK-002",
            "title": "Build API",
            "target_files": ["api.py"],
            "estimated_complexity": "high",
            # Missing: acceptance_criteria
        }
        pra_result_invalid = PRAResult(
            is_complete=True,
            data={"task_graph": [invalid_task]},
        )
        output_invalid = await planner_agent.review(pra_result_invalid)
        assert output_invalid.review_passed is False


class TestPlannerStateUpdates:
    """review() stores output under planner_output key."""

    async def test_state_updates_use_planner_output_key(
        self, planner_agent: PlannerAgent
    ) -> None:
        """state_updates contains planner_output key."""
        pra_result = PRAResult(
            is_complete=True,
            data={"task_graph": []},
        )
        output = await planner_agent.review(pra_result)
        assert "planner_output" in output.state_updates


# ---------------------------------------------------------------------------
# TechStackBuilderAgent tests
# ---------------------------------------------------------------------------


class TestTechStackAgentType:
    """TechStackBuilderAgent has correct type and inheritance."""

    def test_agent_type(self, techstack_agent: TechStackBuilderAgent) -> None:
        """agent_type is TECH_STACK_ADVISOR."""
        assert techstack_agent.agent_type == AgentType.TECH_STACK_ADVISOR

    def test_extends_base_agent(self, techstack_agent: TechStackBuilderAgent) -> None:
        """TechStackBuilderAgent is a subclass of BaseAgent."""
        assert isinstance(techstack_agent, BaseAgent)

    def test_system_prompt_not_empty(self) -> None:
        """SYSTEM_PROMPT is non-empty and mentions technology."""
        assert len(TECHSTACK_SYSTEM_PROMPT) > 0
        assert "technology" in TECHSTACK_SYSTEM_PROMPT.lower()


class TestTechStackPerceive:
    """TechStackBuilderAgent.perceive() extracts context."""

    async def test_perceive_reads_user_preferences(
        self, techstack_agent: TechStackBuilderAgent, techstack_input: AgentInput
    ) -> None:
        """perceive() returns dict containing user_preferences."""
        result = await techstack_agent.perceive(techstack_input)
        assert "user_preferences" in result
        assert result["user_preferences"]["language"] == "python"
        assert "brainstorming_output" in result
        assert "research_output" in result


class TestTechStackReview:
    """TechStackBuilderAgent.review() validates output."""

    async def test_review_passes_with_valid_stack(
        self, techstack_agent: TechStackBuilderAgent
    ) -> None:
        """review() returns review_passed=True when recommended_stack has required keys."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "recommended_stack": {
                    "language": {"name": "Python", "version": "3.12"},
                    "framework": {"name": "FastAPI", "version": "0.115"},
                    "database": {"name": "PostgreSQL", "version": "16"},
                    "hosting": {"name": "AWS", "service": "ECS"},
                },
            },
        )
        output = await techstack_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_review_fails_without_framework_key(
        self, techstack_agent: TechStackBuilderAgent
    ) -> None:
        """review() returns review_passed=False when framework key missing."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "recommended_stack": {
                    "language": "Python",
                    # Missing: framework, database, hosting
                },
            },
        )
        output = await techstack_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False

    async def test_review_fails_with_empty_stack(
        self, techstack_agent: TechStackBuilderAgent
    ) -> None:
        """review() returns review_passed=False when recommended_stack is empty."""
        pra_result = PRAResult(
            is_complete=True,
            data={"recommended_stack": {}},
        )
        output = await techstack_agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestTechStackStateUpdates:
    """review() stores output under techstack_output key."""

    async def test_state_updates_use_techstack_output_key(
        self, techstack_agent: TechStackBuilderAgent
    ) -> None:
        """state_updates contains techstack_output key."""
        pra_result = PRAResult(
            is_complete=True,
            data={"recommended_stack": {}},
        )
        output = await techstack_agent.review(pra_result)
        assert "techstack_output" in output.state_updates


# ---------------------------------------------------------------------------
# YAML config tests
# ---------------------------------------------------------------------------


class TestPlannerYAMLConfig:
    """planner.yaml loads and validates."""

    def test_yaml_config_loads(self) -> None:
        """YAML config parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "planner.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["planner"]["agent_type"] == "PLANNER"


class TestTechStackYAMLConfig:
    """techstack_builder.yaml loads and validates."""

    def test_yaml_config_loads(self) -> None:
        """YAML config parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "techstack_builder.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["techstack_builder"]["agent_type"] == "TECH_STACK_ADVISOR"
