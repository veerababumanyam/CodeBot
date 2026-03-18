"""BaseAgent abstract class with PRA cognitive cycle.

Stub file -- implementation follows TDD GREEN phase.
"""

from __future__ import annotations

import abc
import uuid
from dataclasses import dataclass, field
from typing import Any

from agent_sdk.models.enums import AgentType


@dataclass(slots=True, kw_only=True)
class AgentInput:
    """Typed input to an agent from the graph engine."""

    task_id: uuid.UUID
    shared_state: dict[str, Any]
    context_tiers: dict[str, Any]


@dataclass(slots=True, kw_only=True)
class AgentOutput:
    """Typed output from an agent to the graph engine."""

    task_id: uuid.UUID
    state_updates: dict[str, Any]
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    review_passed: bool = True
    error: str | None = None


@dataclass(slots=True, kw_only=True)
class PRAResult:
    """Intermediate result from the act() phase."""

    is_complete: bool = False
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, kw_only=True)
class BaseAgent(abc.ABC):
    """Abstract base for all CodeBot agents. Stub -- not yet implemented."""

    agent_id: uuid.UUID = field(default_factory=uuid.uuid4)
    agent_type: AgentType = field(init=False)
    max_iterations: int = 10
    token_budget: int = 100_000
    timeout_seconds: int = 1800

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError("RED phase stub")

    @abc.abstractmethod
    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]: ...

    @abc.abstractmethod
    async def reason(self, context: dict[str, Any]) -> dict[str, Any]: ...

    @abc.abstractmethod
    async def act(self, plan: dict[str, Any]) -> PRAResult: ...

    @abc.abstractmethod
    async def review(self, result: PRAResult) -> AgentOutput: ...

    @abc.abstractmethod
    async def _initialize(self, agent_input: AgentInput) -> None: ...
