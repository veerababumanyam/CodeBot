"""Unit tests for BrainstormingAgent."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import yaml
from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.brainstorming import SYSTEM_PROMPT, BrainstormingAgent

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def agent() -> BrainstormingAgent:
    """Create a BrainstormingAgent instance."""
    return BrainstormingAgent()


@pytest.fixture
def agent_input() -> AgentInput:
    """Create a standard AgentInput with user_input in shared state."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={"user_input": {"content": "Build a social media app"}},
        context_tiers={},
    )


class TestBrainstormingAgentType:
    """BrainstormingAgent has correct type and inheritance."""

    def test_agent_type_is_brainstorm_facilitator(self, agent: BrainstormingAgent) -> None:
        """agent_type is BRAINSTORM_FACILITATOR."""
        assert agent.agent_type == AgentType.BRAINSTORM_FACILITATOR

    def test_agent_extends_base_agent(self, agent: BrainstormingAgent) -> None:
        """BrainstormingAgent is a subclass of BaseAgent."""
        assert isinstance(agent, BaseAgent)


class TestBrainstormingSystemPrompt:
    """SYSTEM_PROMPT contains required content."""

    def test_system_prompt_mentions_brainstorming(self) -> None:
        """SYSTEM_PROMPT contains 'brainstorming'."""
        assert "brainstorming" in SYSTEM_PROMPT.lower()

    def test_system_prompt_mentions_moscow(self) -> None:
        """SYSTEM_PROMPT contains 'MoSCoW'."""
        assert "MoSCoW" in SYSTEM_PROMPT


class TestBrainstormingPerceive:
    """BrainstormingAgent.perceive() extracts context."""

    async def test_perceive_extracts_user_input(
        self,
        agent: BrainstormingAgent,
        agent_input: AgentInput,
    ) -> None:
        """perceive() returns dict containing user_input."""
        result = await agent.perceive(agent_input)
        assert "user_input" in result
        assert result["user_input"] == {"content": "Build a social media app"}


class TestBrainstormingReview:
    """BrainstormingAgent.review() validates output."""

    async def test_review_passes_with_required_keys(
        self, agent: BrainstormingAgent
    ) -> None:
        """review() returns review_passed=True when required keys present."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "refined_requirements": "Build a social media platform",
                "alternatives": [{"name": "approach-1"}],
            },
        )
        output = await agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_review_fails_without_required_keys(
        self, agent: BrainstormingAgent
    ) -> None:
        """review() returns review_passed=False when required keys missing."""
        pra_result = PRAResult(
            is_complete=True,
            data={},
        )
        output = await agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False


class TestBrainstormingTools:
    """BrainstormingAgent has expected tools."""

    def test_tools_list_contains_web_search(self, agent: BrainstormingAgent) -> None:
        """tools list includes web_search."""
        assert "web_search" in agent.tools


class TestBrainstormingYAMLConfig:
    """brainstorming.yaml loads and validates."""

    def test_yaml_config_loads(self) -> None:
        """YAML config parses and has correct agent_type."""
        config_path = PROJECT_ROOT / "configs" / "agents" / "brainstorming.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["brainstorming"]["agent_type"] == "BRAINSTORM_FACILITATOR"


class TestBrainstormingStateUpdates:
    """review() stores output under brainstorming_output key."""

    async def test_state_updates_use_brainstorming_output_key(
        self, agent: BrainstormingAgent
    ) -> None:
        """state_updates contains brainstorming_output key."""
        pra_result = PRAResult(
            is_complete=True,
            data={
                "refined_requirements": "test",
                "alternatives": [],
            },
        )
        output = await agent.review(pra_result)
        assert "brainstorming_output" in output.state_updates
