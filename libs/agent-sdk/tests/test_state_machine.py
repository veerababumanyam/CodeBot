"""Tests for AgentStateMachine transition validation and history tracking."""

from __future__ import annotations

import pytest

from agent_sdk.agents.state_machine import (
    AgentStateMachine,
    InvalidTransitionError,
    VALID_TRANSITIONS,
)
from agent_sdk.models.enums import AgentPhase


class TestAgentStateMachine:
    """State machine transition validation tests."""

    def test_initial_state_is_idle(self) -> None:
        sm = AgentStateMachine("agent-1")
        assert sm.state == AgentPhase.IDLE

    def test_valid_transition_idle_to_initializing(self) -> None:
        sm = AgentStateMachine("agent-1")
        sm.transition(AgentPhase.INITIALIZING)
        assert sm.state == AgentPhase.INITIALIZING

    def test_valid_transition_initializing_to_executing(self) -> None:
        sm = AgentStateMachine("agent-1")
        sm.transition(AgentPhase.INITIALIZING)
        sm.transition(AgentPhase.EXECUTING)
        assert sm.state == AgentPhase.EXECUTING

    def test_valid_transition_executing_to_reviewing(self) -> None:
        sm = AgentStateMachine("agent-1")
        sm.transition(AgentPhase.INITIALIZING)
        sm.transition(AgentPhase.EXECUTING)
        sm.transition(AgentPhase.REVIEWING)
        assert sm.state == AgentPhase.REVIEWING

    def test_valid_transition_reviewing_to_completed(self) -> None:
        sm = AgentStateMachine("agent-1")
        sm.transition(AgentPhase.INITIALIZING)
        sm.transition(AgentPhase.EXECUTING)
        sm.transition(AgentPhase.REVIEWING)
        sm.transition(AgentPhase.COMPLETED)
        assert sm.state == AgentPhase.COMPLETED

    def test_valid_transition_reviewing_to_failed(self) -> None:
        sm = AgentStateMachine("agent-1")
        sm.transition(AgentPhase.INITIALIZING)
        sm.transition(AgentPhase.EXECUTING)
        sm.transition(AgentPhase.REVIEWING)
        sm.transition(AgentPhase.FAILED)
        assert sm.state == AgentPhase.FAILED

    def test_valid_transition_failed_to_recovering(self) -> None:
        sm = AgentStateMachine("agent-1")
        sm.transition(AgentPhase.INITIALIZING)
        sm.transition(AgentPhase.EXECUTING)
        sm.transition(AgentPhase.REVIEWING)
        sm.transition(AgentPhase.FAILED)
        sm.transition(AgentPhase.RECOVERING)
        assert sm.state == AgentPhase.RECOVERING

    def test_valid_transition_recovering_to_executing(self) -> None:
        sm = AgentStateMachine("agent-1")
        sm.transition(AgentPhase.INITIALIZING)
        sm.transition(AgentPhase.EXECUTING)
        sm.transition(AgentPhase.REVIEWING)
        sm.transition(AgentPhase.FAILED)
        sm.transition(AgentPhase.RECOVERING)
        sm.transition(AgentPhase.EXECUTING)
        assert sm.state == AgentPhase.EXECUTING

    def test_invalid_transition_idle_to_completed(self) -> None:
        sm = AgentStateMachine("agent-1")
        with pytest.raises(InvalidTransitionError):
            sm.transition(AgentPhase.COMPLETED)

    def test_invalid_transition_completed_is_terminal(self) -> None:
        sm = AgentStateMachine("agent-1")
        sm.transition(AgentPhase.INITIALIZING)
        sm.transition(AgentPhase.EXECUTING)
        sm.transition(AgentPhase.REVIEWING)
        sm.transition(AgentPhase.COMPLETED)
        # Try every possible target from COMPLETED -- all should fail
        for target in AgentPhase:
            if target == AgentPhase.COMPLETED:
                continue
            with pytest.raises(InvalidTransitionError):
                sm.transition(target)

    def test_invalid_transition_idle_to_executing(self) -> None:
        sm = AgentStateMachine("agent-1")
        with pytest.raises(InvalidTransitionError):
            sm.transition(AgentPhase.EXECUTING)

    def test_transition_history_recorded(self) -> None:
        sm = AgentStateMachine("agent-1")
        sm.transition(AgentPhase.INITIALIZING)
        sm.transition(AgentPhase.EXECUTING)
        sm.transition(AgentPhase.REVIEWING)
        # Initial state + 3 transitions = 4 entries
        assert len(sm.history) == 4
        assert sm.history[0][0] == AgentPhase.IDLE
        assert sm.history[1][0] == AgentPhase.INITIALIZING
        assert sm.history[2][0] == AgentPhase.EXECUTING
        assert sm.history[3][0] == AgentPhase.REVIEWING

    def test_on_transition_callback_called(self, transition_recorder) -> None:
        sm = AgentStateMachine("agent-1", on_transition=transition_recorder)
        sm.transition(AgentPhase.INITIALIZING)
        sm.transition(AgentPhase.EXECUTING)
        assert len(transition_recorder.transitions) == 2
        assert transition_recorder.transitions[0] == (AgentPhase.IDLE, AgentPhase.INITIALIZING)
        assert transition_recorder.transitions[1] == (AgentPhase.INITIALIZING, AgentPhase.EXECUTING)
