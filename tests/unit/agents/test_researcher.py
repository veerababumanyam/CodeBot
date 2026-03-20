"""Unit tests for ResearcherAgent."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import yaml
from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.researcher import SYSTEM_PROMPT, ResearcherAgent

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def agent() -> ResearcherAgent:
    """Create a ResearcherAgent instance."""
    return ResearcherAgent()


@pytest.fixture
def agent_input() -> AgentInput:
    """Create a standard AgentInput with brainstorming_output in shared state."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={
            "brainstorming_output": {
                "alternatives": [{"name": "FastAPI monolith"}],
                "refined_requirements": "Build a REST API",
            }
        },
        context_tiers={},
    )


class TestResearcherAgentType:
    """ResearcherAgent has correct type and inheritance."""

    def test_agent_type_is_researcher(self, agent: ResearcherAgent) -> None:
        """agent_type is RESEARCHER."""
        assert agent.agent_type == AgentType.RESEARCHER

    def test_agent_extends_base_agent(self, agent: ResearcherAgent) -> None:
        """ResearcherAgent is a subclass of BaseAgent."""
        assert isinstance(agent, BaseAgent)


class TestResearcherSystemPrompt:
    """SYSTEM_PROMPT contains required content."""

    def test_system_prompt_mentions_research(self) -> None:
        """SYSTEM_PROMPT contains 'research'."""
        assert "research" in SYSTEM_PROMPT.lower()


class TestResearcherPerceive:
    """ResearcherAgent.perceive() extracts context."""

    async def test_perceive_extracts_brainstorming_output(
        self,
        agent: ResearcherAgent,
        agent_input: AgentInput,
    ) -> None:
        """perceive() returns dict containing brainstorming_output."""
        result = await agent.perceive(agent_input)
        assert "brainstorming_output" in result
        assert result["brainstorming_output"]["alternatives"][0]["name"] == "FastAPI monolith"


class TestResearcherReview:
    """ResearcherAgent.review() validates output."""

    async def test_review_passes_with_required_keys(
        self, agent: ResearcherAgent
    ) -> None:
        """review() returns review_passed=True when required keys present."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "library_evaluations": [
                    {"name": "FastAPI", "score": 0.9, "pros": ["fast"], "cons": ["async only"]},
                ],
                "research_report": "FastAPI is recommended for the REST API backend.",
            },
        )
        output = await agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_review_fails_without_research_report(
        self, agent: ResearcherAgent
    ) -> None:
        """review() returns review_passed=False when research_report missing."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "library_evaluations": [{"name": "FastAPI"}],
            },
        )
        output = await agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestResearcherTools:
    """ResearcherAgent has expected tools."""

    def test_tools_list_contains_github_search(self, agent: ResearcherAgent) -> None:
        """tools list includes github_search."""
        assert "github_search" in agent.tools


class TestResearcherStateUpdates:
    """review() stores output under research_output key."""

    async def test_state_updates_use_research_output_key(
        self, agent: ResearcherAgent
    ) -> None:
        """state_updates contains research_output key."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "library_evaluations": [],
                "research_report": "summary",
            },
        )
        output = await agent.review(pra_result)
        assert "research_output" in output.state_updates


class TestResearcherYAMLConfig:
    """researcher.yaml loads and validates."""

    def test_yaml_config_loads(self) -> None:
        """YAML config parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "researcher.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["researcher"]["agent_type"] == "RESEARCHER"
