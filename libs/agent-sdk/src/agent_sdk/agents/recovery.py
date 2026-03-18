"""Recovery strategy hierarchy for agent fault tolerance.

Implements the Strategy pattern for configurable agent recovery.
Each strategy decides the next action based on the current attempt
count and configured limits.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, kw_only=True)
class RecoveryContext:
    """Context passed to recovery strategies.

    Attributes:
        agent_id: Identifier of the failing agent.
        error: The exception that triggered recovery.
        attempt: Current retry attempt number (0-based).
        max_retries: Maximum allowed retry attempts.
        config: Additional configuration from AgentConfig.retry_policy.
    """

    agent_id: str
    error: Exception
    attempt: int
    max_retries: int
    config: dict[str, Any]


class RecoveryAction:
    """Result of a recovery decision.

    Attributes:
        action: One of the class-level constants (RETRY, RETRY_MODIFIED, etc.).
        modified_prompt: Optional modified prompt for RETRY_MODIFIED actions.
    """

    RETRY = "retry"
    RETRY_MODIFIED = "retry_modified"
    ESCALATE = "escalate"
    ROLLBACK = "rollback"
    ABORT = "abort"

    def __init__(self, action: str, *, modified_prompt: str | None = None) -> None:
        self.action = action
        self.modified_prompt = modified_prompt


class RecoveryStrategy(abc.ABC):
    """Abstract base for recovery strategies."""

    @abc.abstractmethod
    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        """Decide the next recovery action based on context.

        Args:
            ctx: Current recovery context with error and attempt info.

        Returns:
            A RecoveryAction indicating what to do next.
        """
        ...


class RetryWithModifiedPrompt(RecoveryStrategy):
    """Retry with a modified prompt that includes the error, escalate at limit."""

    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        if ctx.attempt < ctx.max_retries:
            return RecoveryAction(
                RecoveryAction.RETRY_MODIFIED,
                modified_prompt=(
                    f"Previous attempt failed with: {ctx.error}. "
                    "Please try a different approach."
                ),
            )
        return RecoveryAction(RecoveryAction.ESCALATE)


class FallbackModelStrategy(RecoveryStrategy):
    """Retry with a fallback model, escalate at limit."""

    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        if ctx.attempt < ctx.max_retries:
            return RecoveryAction(RecoveryAction.RETRY)
        return RecoveryAction(RecoveryAction.ESCALATE)


class EscalateStrategy(RecoveryStrategy):
    """Always escalate to human intervention."""

    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        return RecoveryAction(RecoveryAction.ESCALATE)


class RollbackStrategy(RecoveryStrategy):
    """Always rollback to the previous known-good state."""

    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        return RecoveryAction(RecoveryAction.ROLLBACK)
