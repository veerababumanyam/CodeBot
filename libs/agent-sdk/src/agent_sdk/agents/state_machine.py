"""Agent state machine with transition validation.

Implements a lightweight enum-based FSM for agent lifecycle management.
Validates transitions against a pre-defined transition table, maintains
history, and invokes an optional callback on every state change.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone

from agent_sdk.models.enums import AgentPhase

logger = logging.getLogger(__name__)


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


# Valid transitions: {from_state: {to_state, ...}}
VALID_TRANSITIONS: dict[AgentPhase, set[AgentPhase]] = {
    AgentPhase.IDLE: {AgentPhase.INITIALIZING},
    AgentPhase.INITIALIZING: {AgentPhase.EXECUTING, AgentPhase.FAILED},
    AgentPhase.EXECUTING: {AgentPhase.REVIEWING, AgentPhase.FAILED},
    AgentPhase.REVIEWING: {AgentPhase.COMPLETED, AgentPhase.FAILED},
    AgentPhase.COMPLETED: set(),  # terminal
    AgentPhase.FAILED: {AgentPhase.RECOVERING},
    AgentPhase.RECOVERING: {AgentPhase.EXECUTING, AgentPhase.FAILED},
}


class AgentStateMachine:
    """Manages agent lifecycle state with validated transitions.

    Args:
        agent_id: Identifier for logging and event correlation.
        on_transition: Optional callback invoked with (prev_state, new_state)
            on every successful transition.
    """

    __slots__ = ("_state", "_agent_id", "_on_transition", "_history")

    def __init__(
        self,
        agent_id: str,
        on_transition: Callable[[AgentPhase, AgentPhase], None] | None = None,
    ) -> None:
        self._state = AgentPhase.IDLE
        self._agent_id = agent_id
        self._on_transition = on_transition
        self._history: list[tuple[AgentPhase, datetime]] = [
            (AgentPhase.IDLE, datetime.now(tz=timezone.utc))
        ]

    @property
    def state(self) -> AgentPhase:
        """Current state of the agent."""
        return self._state

    @property
    def history(self) -> list[tuple[AgentPhase, datetime]]:
        """Full transition history as (state, timestamp) pairs."""
        return self._history

    def transition(self, target: AgentPhase) -> None:
        """Transition to a new state if valid, otherwise raise.

        Args:
            target: The desired target state.

        Raises:
            InvalidTransitionError: If the transition is not allowed.
        """
        allowed = VALID_TRANSITIONS.get(self._state, set())
        if target not in allowed:
            raise InvalidTransitionError(
                f"Cannot transition from {self._state.value} to {target.value}"
            )
        prev = self._state
        self._state = target
        now = datetime.now(tz=timezone.utc)
        self._history.append((target, now))
        logger.info(
            "Agent %s: %s -> %s", self._agent_id, prev.value, target.value
        )
        if self._on_transition is not None:
            self._on_transition(prev, target)
