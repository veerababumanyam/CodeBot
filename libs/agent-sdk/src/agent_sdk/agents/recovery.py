"""Recovery strategy hierarchy for agent fault tolerance.

Stub file -- implementation follows TDD GREEN phase.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, kw_only=True)
class RecoveryContext:
    """Context passed to recovery strategies."""

    agent_id: str
    error: Exception
    attempt: int
    max_retries: int
    config: dict[str, Any]


class RecoveryAction:
    """Result of a recovery decision."""

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
    async def decide(self, ctx: RecoveryContext) -> RecoveryAction: ...


class RetryWithModifiedPrompt(RecoveryStrategy):
    """Retry with a modified prompt, escalate at limit."""

    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        raise NotImplementedError("RED phase stub")


class FallbackModelStrategy(RecoveryStrategy):
    """Retry with fallback model, escalate at limit."""

    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        raise NotImplementedError("RED phase stub")


class EscalateStrategy(RecoveryStrategy):
    """Always escalate to human."""

    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        raise NotImplementedError("RED phase stub")


class RollbackStrategy(RecoveryStrategy):
    """Always rollback."""

    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        raise NotImplementedError("RED phase stub")
