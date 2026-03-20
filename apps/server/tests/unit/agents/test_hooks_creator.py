"""Tests for HooksCreatorAgent -- full implementation (Phase 11).

Verifies the PRA cognitive cycle for generating lifecycle hooks,
including HookService integration and event bus publishing.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType


@pytest.fixture
def mock_hook_service() -> AsyncMock:
    """Mock HookService with register stub."""
    return AsyncMock()


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    """Mock EventBus with publish stub."""
    return AsyncMock()


@pytest.fixture
def agent() -> Any:
    """Create a HooksCreatorAgent instance."""
    from codebot.agents.hooks_creator_agent import HooksCreatorAgent

    return HooksCreatorAgent()


@pytest.fixture
def agent_input() -> AgentInput:
    """Create a standard AgentInput for testing."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={},
        context_tiers={},
    )


class TestHooksCreatorAgent:
    """Tests for HooksCreatorAgent conventions and PRA cycle."""

    def test_agent_type(self, agent: Any) -> None:
        """Agent type must be HOOK_MANAGER (existing enum value)."""
        assert agent.agent_type == AgentType.HOOK_MANAGER

    def test_dataclass_conventions(self, agent: Any) -> None:
        """Verify the agent follows @dataclass(slots=True, kw_only=True) conventions."""
        assert hasattr(agent, "__slots__")
        assert agent.agent_type == AgentType.HOOK_MANAGER

    def test_extends_base_agent(self, agent: Any) -> None:
        """Agent must extend BaseAgent."""
        assert isinstance(agent, BaseAgent)

    def test_has_name_field(self, agent: Any) -> None:
        """Agent must have a human-readable name."""
        assert agent.name == "hooks_creator"

    async def test_perceive_extracts_pipeline_context(
        self, agent: Any, agent_input: AgentInput
    ) -> None:
        """Perceive extracts pipeline_config, execution_history, existing_hooks."""
        agent_input.shared_state = {
            "pipeline_config": {"stages": 10},
            "execution_history": [{"phase": "S1", "status": "ok"}],
            "existing_hooks": ["hook-1"],
        }
        result = await agent.perceive(agent_input)
        assert result["pipeline_config"]["stages"] == 10
        assert len(result["execution_history"]) == 1
        assert result["existing_hooks"] == ["hook-1"]

    async def test_perceive_handles_missing_keys(
        self, agent: Any, agent_input: AgentInput
    ) -> None:
        """Perceive returns empty defaults when keys are missing."""
        agent_input.shared_state = {}
        result = await agent.perceive(agent_input)
        assert result["pipeline_config"] == {}
        assert result["execution_history"] == []
        assert result["existing_hooks"] == []

    async def test_reason_proposes_hooks(self, agent: Any) -> None:
        """Reason builds a hook proposal plan."""
        context = {
            "pipeline_config": {"stages": 10},
            "execution_history": [],
            "existing_hooks": [],
            "project_type": "greenfield",
        }
        plan = await agent.reason(context)
        assert "proposed_hooks" in plan
        assert "perception" in plan

    async def test_act_registers_hooks(
        self,
        agent: Any,
        mock_hook_service: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Act registers hooks via HookService and publishes events."""
        from codebot.agents.hooks_creator_agent import HookDefinition

        agent.set_services(hook_service=mock_hook_service, event_bus=mock_event_bus)

        defn = HookDefinition(
            name="pre-s5-lint",
            hook_type="PRE_PHASE",
            target="S5",
            priority=50,
            description="Lint check before implementation",
        )
        plan = {"proposed_hooks": [defn]}
        result = await agent.act(plan)
        assert result.is_complete
        assert len(result.data["registered_hooks"]) == 1
        mock_hook_service.register.assert_called_once()
        mock_event_bus.publish.assert_called_once()

    async def test_act_handles_registration_error(
        self,
        agent: Any,
        mock_hook_service: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Act handles registration errors gracefully."""
        from codebot.agents.hooks_creator_agent import HookDefinition

        mock_hook_service.register.side_effect = RuntimeError("Registry full")
        agent.set_services(hook_service=mock_hook_service, event_bus=mock_event_bus)

        defn = HookDefinition(name="bad", hook_type="ON_EVENT", target="*")
        plan = {"proposed_hooks": [defn]}
        result = await agent.act(plan)
        assert result.is_complete
        assert len(result.data["errors"]) > 0
        assert "Registry full" in result.data["errors"][0]

    async def test_act_with_empty_hooks(
        self,
        agent: Any,
        mock_hook_service: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Act with empty hook list returns success."""
        agent.set_services(hook_service=mock_hook_service, event_bus=mock_event_bus)
        result = await agent.act({"proposed_hooks": []})
        assert result.is_complete
        assert result.data["registered_hooks"] == []
        assert result.data["errors"] == []

    async def test_review_validates_output(self, agent: Any) -> None:
        """Review validates and formats the PRA output."""
        pra_result = PRAResult(
            is_complete=True,
            data={"registered_hooks": ["hook-1"], "errors": []},
        )
        output = await agent.review(pra_result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed
        assert "hooks_creator_output" in output.state_updates

    def test_build_system_prompt(self, agent: Any) -> None:
        """Agent has a system prompt."""
        prompt = agent.build_system_prompt()
        assert "Hooks Creator" in prompt
        assert len(prompt) > 50
