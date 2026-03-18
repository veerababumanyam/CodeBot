"""AgentNode graph adapter wrapping BaseAgent for execution within the graph engine.

AgentNode is the bridge between the agent framework (Phase 3) and the graph
engine (Phase 2). It manages the agent lifecycle within graph execution:

- Converting SharedState dict to AgentInput
- Running BaseAgent.execute() with asyncio.timeout
- Handling recovery on failure via RecoveryStrategy
- Recording AgentMetrics per execution
- Calling on_event callback with execution results
- Optionally creating/cleaning up a git worktree via WorktreeProvider
"""

from __future__ import annotations

import asyncio
import logging
import uuid as _uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent
from agent_sdk.agents.metrics import AgentMetrics
from agent_sdk.agents.recovery import RecoveryAction, RecoveryContext, RecoveryStrategy

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class NoOpWorktreeProvider:
    """Stub worktree provider that returns the current working directory.

    Phase 8 (Agent Isolation) implements real git worktree management.
    This stub satisfies the WorktreeProvider protocol interface (AGNT-04).
    """

    async def create_worktree(self, agent_id: str, branch_name: str) -> str:
        """Return current directory as worktree path (no-op)."""
        return "."

    async def cleanup_worktree(self, worktree_path: str) -> None:
        """No-op cleanup."""
        pass


@dataclass(slots=True, kw_only=True)
class AgentNode:
    """Graph node that wraps a BaseAgent for execution within the graph engine.

    Responsibilities:
    - Convert SharedState dict to AgentInput
    - Run BaseAgent.execute() with asyncio.timeout
    - Handle recovery on failure via RecoveryStrategy
    - Record AgentMetrics per execution
    - Call on_event callback with execution results

    Attributes:
        node_id: Unique identifier for this node in the graph.
        agent: The BaseAgent instance to wrap.
        timeout_seconds: Maximum execution time before cancellation.
        max_retries: Maximum retry attempts on failure.
        recovery_strategy: Optional strategy for handling agent failures.
        worktree_provider: Optional provider for git worktree isolation.
        on_event: Optional callback invoked after execution with event dict.
        last_metrics: Metrics from the most recent execution (read-only).
    """

    node_id: str
    agent: BaseAgent
    timeout_seconds: float = 1800.0
    max_retries: int = 3
    recovery_strategy: RecoveryStrategy | None = None
    worktree_provider: Any = None  # WorktreeProvider protocol
    on_event: Callable[[dict[str, Any]], None] | None = None
    last_metrics: AgentMetrics | None = field(default=None, init=False)

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the wrapped agent within the graph.

        Args:
            state: SharedState dict from the graph engine.

        Returns:
            Updated SharedState dict with agent outputs merged.

        Raises:
            TimeoutError: If execution exceeds timeout_seconds.
            Exception: Re-raised from agent if recovery escalates or aborts.
        """
        worktree_path: str | None = None
        if self.worktree_provider is not None:
            worktree_path = await self.worktree_provider.create_worktree(
                str(self.agent.agent_id), f"agent-{self.node_id}"
            )

        metrics = AgentMetrics()
        metrics.start()
        attempt = 0

        try:
            while True:
                try:
                    agent_input = self._build_input(state)
                    async with asyncio.timeout(self.timeout_seconds):
                        output = await self.agent.execute(agent_input)
                    state.update(output.state_updates)
                    metrics.stop()
                    self.last_metrics = metrics
                    self._emit_event(output, metrics)
                    return state
                except Exception as exc:
                    attempt += 1
                    if self.recovery_strategy is None:
                        metrics.stop()
                        self.last_metrics = metrics
                        raise

                    ctx = RecoveryContext(
                        agent_id=str(self.agent.agent_id),
                        error=exc,
                        attempt=attempt,
                        max_retries=self.max_retries,
                        config={},
                    )
                    action = await self.recovery_strategy.decide(ctx)

                    if action.action in (RecoveryAction.RETRY, RecoveryAction.RETRY_MODIFIED):
                        metrics.record_retry()
                        logger.info(
                            "AgentNode %s: retrying (attempt %d/%d)",
                            self.node_id,
                            attempt,
                            self.max_retries,
                        )
                        continue
                    elif action.action == RecoveryAction.ROLLBACK:
                        metrics.stop()
                        self.last_metrics = metrics
                        logger.info("AgentNode %s: rolling back to original state", self.node_id)
                        return state  # Return unmodified state
                    else:
                        # ESCALATE, ABORT, or unknown action
                        metrics.stop()
                        self.last_metrics = metrics
                        raise
        finally:
            if self.worktree_provider is not None and worktree_path is not None:
                await self.worktree_provider.cleanup_worktree(worktree_path)

    def _build_input(self, state: dict[str, Any]) -> AgentInput:
        """Convert SharedState dict to typed AgentInput.

        Extracts task_id (as UUID) and context tiers from the state dict.
        Generates a new task_id if none is present.

        Args:
            state: SharedState dict from the graph engine.

        Returns:
            AgentInput with task_id, shared_state reference, and context tiers.
        """
        task_id = state.get("task_id")
        if isinstance(task_id, str):
            task_id = _uuid.UUID(task_id)
        elif task_id is None:
            task_id = _uuid.uuid4()
        return AgentInput(
            task_id=task_id,
            shared_state=state,
            context_tiers=state.get("context", {}),
        )

    def _emit_event(self, output: AgentOutput, metrics: AgentMetrics) -> None:
        """Invoke the on_event callback with execution results.

        Args:
            output: The AgentOutput from successful execution.
            metrics: The AgentMetrics recorded during execution.
        """
        if self.on_event is not None:
            self.on_event(
                {
                    "node_id": self.node_id,
                    "agent_id": str(self.agent.agent_id),
                    "agent_type": self.agent.agent_type.value,
                    "review_passed": output.review_passed,
                    "metrics": metrics.to_dict(),
                }
            )
