"""Tests for recovery strategies."""

from __future__ import annotations

import pytest

from agent_sdk.agents.recovery import (
    EscalateStrategy,
    FallbackModelStrategy,
    RecoveryAction,
    RecoveryContext,
    RetryWithModifiedPrompt,
    RollbackStrategy,
)


def _make_ctx(attempt: int = 0, max_retries: int = 3) -> RecoveryContext:
    """Helper to build a RecoveryContext with defaults."""
    return RecoveryContext(
        agent_id="agent-1",
        error=RuntimeError("test error"),
        attempt=attempt,
        max_retries=max_retries,
        config={},
    )


class TestRetryWithModifiedPrompt:
    @pytest.mark.asyncio
    async def test_returns_retry_when_under_limit(self) -> None:
        strategy = RetryWithModifiedPrompt()
        action = await strategy.decide(_make_ctx(attempt=0, max_retries=3))
        assert action.action == RecoveryAction.RETRY_MODIFIED
        assert action.modified_prompt is not None
        assert len(action.modified_prompt) > 0

    @pytest.mark.asyncio
    async def test_escalates_at_limit(self) -> None:
        strategy = RetryWithModifiedPrompt()
        action = await strategy.decide(_make_ctx(attempt=3, max_retries=3))
        assert action.action == RecoveryAction.ESCALATE


class TestFallbackModelStrategy:
    @pytest.mark.asyncio
    async def test_returns_retry_under_limit(self) -> None:
        strategy = FallbackModelStrategy()
        action = await strategy.decide(_make_ctx(attempt=0, max_retries=3))
        assert action.action == RecoveryAction.RETRY

    @pytest.mark.asyncio
    async def test_escalates_at_limit(self) -> None:
        strategy = FallbackModelStrategy()
        action = await strategy.decide(_make_ctx(attempt=3, max_retries=3))
        assert action.action == RecoveryAction.ESCALATE


class TestEscalateStrategy:
    @pytest.mark.asyncio
    async def test_always_escalates(self) -> None:
        strategy = EscalateStrategy()
        for attempt in [0, 1, 5, 100]:
            action = await strategy.decide(_make_ctx(attempt=attempt))
            assert action.action == RecoveryAction.ESCALATE


class TestRollbackStrategy:
    @pytest.mark.asyncio
    async def test_always_rolls_back(self) -> None:
        strategy = RollbackStrategy()
        for attempt in [0, 1, 5, 100]:
            action = await strategy.decide(_make_ctx(attempt=attempt))
            assert action.action == RecoveryAction.ROLLBACK


class TestRecoveryContext:
    def test_recovery_context_fields(self) -> None:
        error = ValueError("some error")
        ctx = RecoveryContext(
            agent_id="agent-42",
            error=error,
            attempt=2,
            max_retries=5,
            config={"key": "value"},
        )
        assert ctx.agent_id == "agent-42"
        assert ctx.error is error
        assert ctx.attempt == 2
        assert ctx.max_retries == 5
        assert ctx.config == {"key": "value"}
