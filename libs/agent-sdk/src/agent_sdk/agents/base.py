"""BaseAgent abstract class with PRA cognitive cycle.

Implements the Perception-Reasoning-Action loop from MASFactory.
Every agent in CodeBot extends BaseAgent and overrides the abstract
methods: perceive(), reason(), act(), review(), _initialize().

Key design points:
- state_machine and metrics are created FRESH per execute() call
  (not stored on self), ensuring statelessness between executions.
- agent_type has no default -- subclasses MUST provide it via
  field(default=AgentType.XXX, init=False).
- PRAResult is the intermediate type between act() and review().
"""

from __future__ import annotations

import abc
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from agent_sdk.agents.metrics import AgentMetrics
from agent_sdk.agents.state_machine import AgentStateMachine, InvalidTransitionError
from agent_sdk.models.enums import AgentPhase, AgentType

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class AgentInput:
    """Typed input to an agent from the graph engine.

    Attributes:
        task_id: Unique identifier for this task execution.
        shared_state: Graph-level shared state dict.
        context_tiers: Context data keyed by tier ("l0", "l1", "l2").
    """

    task_id: uuid.UUID
    shared_state: dict[str, Any]
    context_tiers: dict[str, Any]


@dataclass(slots=True, kw_only=True)
class AgentOutput:
    """Typed output from an agent to the graph engine.

    Attributes:
        task_id: Identifier of the completed task.
        state_updates: Updates to merge into graph SharedState.
        artifacts: List of produced artifacts (files, code, etc.).
        review_passed: Whether self-review accepted the output.
        error: Error description if execution failed.
    """

    task_id: uuid.UUID
    state_updates: dict[str, Any]
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    review_passed: bool = True
    error: str | None = None


@dataclass(slots=True, kw_only=True)
class PRAResult:
    """Intermediate result from the act() phase.

    Attributes:
        is_complete: Whether the agent has finished its work.
        data: Arbitrary data produced during the action phase.
    """

    is_complete: bool = False
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, kw_only=True)
class BaseAgent(abc.ABC):
    """Abstract base for all CodeBot agents.

    Implements the PRA (Perception-Reasoning-Action) cognitive cycle.
    Concrete agents override perceive(), reason(), act(), and review().

    Attributes:
        agent_id: Unique identifier for this agent instance.
        agent_type: Specialization enum (set by subclass, no default).
        max_iterations: Maximum PRA loop iterations before forced review.
        token_budget: Token budget for the entire execution.
        timeout_seconds: Maximum execution time in seconds.
    """

    agent_id: uuid.UUID = field(default_factory=uuid.uuid4)
    agent_type: AgentType = field(init=False)
    max_iterations: int = 10
    token_budget: int = 100_000
    timeout_seconds: int = 1800

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """Run the full PRA cycle with state machine transitions and metrics.

        Creates fresh state_machine and metrics per call to ensure
        statelessness between executions (Pitfall 5 from research).

        Args:
            agent_input: Typed input containing task context.

        Returns:
            AgentOutput with results and review status.

        Raises:
            Exception: Re-raises any exception from PRA cycle after
                transitioning to FAILED state.
        """
        state_machine = AgentStateMachine(str(self.agent_id))
        metrics = AgentMetrics()
        metrics.start()

        try:
            state_machine.transition(AgentPhase.INITIALIZING)
            await self._initialize(agent_input)

            state_machine.transition(AgentPhase.EXECUTING)
            result = PRAResult()
            for _iteration in range(self.max_iterations):
                context = await self.perceive(agent_input)
                plan = await self.reason(context)
                result = await self.act(plan)
                if result.is_complete:
                    break

            state_machine.transition(AgentPhase.REVIEWING)
            output = await self.review(result)

            if output.review_passed:
                state_machine.transition(AgentPhase.COMPLETED)
            else:
                state_machine.transition(AgentPhase.FAILED)

            metrics.stop()
            return output

        except Exception as exc:
            try:
                state_machine.transition(AgentPhase.FAILED)
            except InvalidTransitionError:
                pass  # Already in a terminal or non-transitionable state
            metrics.stop()
            raise

    @abc.abstractmethod
    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Assemble context: L0/L1/L2 tiers, MCP resources, episodic memory.

        Args:
            agent_input: The task input with context tiers.

        Returns:
            Assembled context dict for the reasoning phase.
        """
        ...

    @abc.abstractmethod
    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Invoke LLM with assembled context; produce action plan.

        Args:
            context: Assembled context from perceive().

        Returns:
            Action plan dict for the act() phase.
        """
        ...

    @abc.abstractmethod
    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Execute chosen action: tool calls, delegation, state updates.

        Args:
            plan: Action plan from reason().

        Returns:
            PRAResult indicating completion status and produced data.
        """
        ...

    @abc.abstractmethod
    async def review(self, result: PRAResult) -> AgentOutput:
        """Self-review output against acceptance criteria.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed indicating acceptance.
        """
        ...

    @abc.abstractmethod
    async def _initialize(self, agent_input: AgentInput) -> None:
        """Load system prompt, tools, context. Called once per execution.

        Args:
            agent_input: The task input for initialization context.
        """
        ...
