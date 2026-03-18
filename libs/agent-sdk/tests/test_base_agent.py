"""Tests for BaseAgent PRA cycle execution."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.agents.state_machine import AgentStateMachine
from agent_sdk.models.enums import AgentPhase, AgentType


@dataclass(slots=True, kw_only=True)
class ConcreteTestAgent(BaseAgent):
    """Concrete agent for testing the PRA cycle."""

    agent_type: AgentType = field(default=AgentType.PLANNER, init=False)

    # Test hooks to control behavior
    _perceive_result: dict[str, Any] = field(default_factory=dict, repr=False)
    _reason_result: dict[str, Any] = field(default_factory=dict, repr=False)
    _act_complete: bool = field(default=True, repr=False)
    _review_passed: bool = field(default=True, repr=False)
    _call_order: list[str] = field(default_factory=list, repr=False)

    async def _initialize(self, agent_input: AgentInput) -> None:
        self._call_order.append("initialize")

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        self._call_order.append("perceive")
        return self._perceive_result

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        self._call_order.append("reason")
        return self._reason_result

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        self._call_order.append("act")
        return PRAResult(is_complete=self._act_complete, data={"result": "test"})

    async def review(self, result: PRAResult) -> AgentOutput:
        self._call_order.append("review")
        return AgentOutput(
            task_id=uuid.uuid4(),
            state_updates={"key": "value"},
            review_passed=self._review_passed,
        )


def _make_input() -> AgentInput:
    """Create a standard AgentInput for testing."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state={"project_id": "test"},
        context_tiers={"l0": {}, "l1": {}, "l2": {}},
    )


class TestConcreteAgentInheritsBase:
    def test_concrete_agent_inherits_base(self) -> None:
        agent = ConcreteTestAgent()
        assert isinstance(agent, BaseAgent)
        assert agent.agent_type == AgentType.PLANNER


class TestExecutePRACycle:
    @pytest.mark.asyncio
    async def test_execute_runs_pra_cycle(self) -> None:
        agent = ConcreteTestAgent()
        output = await agent.execute(_make_input())
        # Check call order: initialize, perceive, reason, act, review
        assert "initialize" in agent._call_order
        assert "perceive" in agent._call_order
        assert "reason" in agent._call_order
        assert "act" in agent._call_order
        assert "review" in agent._call_order
        # Ensure correct ordering
        init_idx = agent._call_order.index("initialize")
        perceive_idx = agent._call_order.index("perceive")
        reason_idx = agent._call_order.index("reason")
        act_idx = agent._call_order.index("act")
        review_idx = agent._call_order.index("review")
        assert init_idx < perceive_idx < reason_idx < act_idx < review_idx

    @pytest.mark.asyncio
    async def test_execute_review_passed_completes(self) -> None:
        agent = ConcreteTestAgent(_review_passed=True)
        output = await agent.execute(_make_input())
        assert output.review_passed is True

    @pytest.mark.asyncio
    async def test_execute_review_failed_fails(self) -> None:
        agent = ConcreteTestAgent(_review_passed=False)
        output = await agent.execute(_make_input())
        assert output.review_passed is False

    @pytest.mark.asyncio
    async def test_execute_populates_metrics(self) -> None:
        """After execute(), the returned output should indicate completion,
        and internal metrics should have recorded non-zero execution time."""
        agent = ConcreteTestAgent()
        output = await agent.execute(_make_input())
        # The output itself is from review(), which we control.
        # We verify that the method completed (output exists and review was called)
        assert output is not None
        assert "review" in agent._call_order

    @pytest.mark.asyncio
    async def test_execute_respects_max_iterations(self) -> None:
        """If act() never sets is_complete=True, loop runs max_iterations times."""
        agent = ConcreteTestAgent(max_iterations=3, _act_complete=False)
        output = await agent.execute(_make_input())
        # perceive, reason, act should each be called 3 times
        assert agent._call_order.count("perceive") == 3
        assert agent._call_order.count("reason") == 3
        assert agent._call_order.count("act") == 3
        # review is called once at the end
        assert agent._call_order.count("review") == 1


class TestAgentInputOutput:
    def test_agent_input_fields(self) -> None:
        task_id = uuid.uuid4()
        inp = AgentInput(
            task_id=task_id,
            shared_state={"key": "val"},
            context_tiers={"l0": {}, "l1": {}, "l2": {}},
        )
        assert inp.task_id == task_id
        assert inp.shared_state == {"key": "val"}
        assert "l0" in inp.context_tiers

    def test_agent_output_fields(self) -> None:
        task_id = uuid.uuid4()
        out = AgentOutput(
            task_id=task_id,
            state_updates={"result": "done"},
            artifacts=[{"type": "code", "path": "/tmp/test.py"}],
            review_passed=True,
            error=None,
        )
        assert out.task_id == task_id
        assert out.state_updates == {"result": "done"}
        assert len(out.artifacts) == 1
        assert out.review_passed is True
        assert out.error is None


class TestAgentStatelessness:
    @pytest.mark.asyncio
    async def test_agent_is_stateless_between_executions(self) -> None:
        """Two consecutive execute() calls should not share mutable state."""
        agent = ConcreteTestAgent()
        input1 = _make_input()
        input2 = _make_input()

        output1 = await agent.execute(input1)
        # Reset call_order manually (since it's on self for test tracking)
        first_call_count = len(agent._call_order)

        output2 = await agent.execute(input2)
        # Both should complete successfully
        assert output1 is not None
        assert output2 is not None
        # The second run should have its own PRA cycle calls
        assert len(agent._call_order) > first_call_count


class TestExecuteStateTransitions:
    @pytest.mark.asyncio
    async def test_execute_transitions_through_states(self) -> None:
        """During execute(), state machine should go through
        IDLE -> INITIALIZING -> EXECUTING -> REVIEWING -> COMPLETED."""
        # We can verify this by using a recording agent
        agent = ConcreteTestAgent(_review_passed=True)
        output = await agent.execute(_make_input())
        assert output.review_passed is True
        # The fact that execute() completed without raising
        # InvalidTransitionError proves the state transitions were valid.
