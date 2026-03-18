"""Agent state machine with transition validation.

Stub file -- implementation follows TDD GREEN phase.
"""

from __future__ import annotations

from agent_sdk.models.enums import AgentPhase


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""


VALID_TRANSITIONS: dict[AgentPhase, set[AgentPhase]] = {}


class AgentStateMachine:
    """Manages agent lifecycle state with validated transitions."""

    def __init__(
        self,
        agent_id: str,
        on_transition: object = None,
    ) -> None:
        raise NotImplementedError("RED phase stub")
