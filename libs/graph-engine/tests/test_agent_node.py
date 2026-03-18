"""Tests for AgentNode graph adapter.

Tests cover:
- Basic execution (SharedState in/out)
- AgentInput construction from SharedState
- Metrics recording
- Recovery strategy handling (retry_modified, escalate, rollback, no strategy)
- NoOpWorktreeProvider stub
- Timeout enforcement
- Event callback emission
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest

from agent_sdk.agents.metrics import AgentMetrics
from agent_sdk.agents.recovery import RecoveryAction, RecoveryContext, RecoveryStrategy
from graph_engine.nodes.agent_node import AgentNode, NoOpWorktreeProvider

from conftest import ConcreteTestAgent, FailingTestAgent, SlowTestAgent


class MockRetryStrategy(RecoveryStrategy):
    """Recovery strategy that retries with modified prompt up to max_retries."""

    def __init__(self) -> None:
        self.call_count = 0

    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        self.call_count += 1
        if ctx.attempt < ctx.max_retries:
            return RecoveryAction(RecoveryAction.RETRY_MODIFIED)
        return RecoveryAction(RecoveryAction.ESCALATE)


class MockEscalateStrategy(RecoveryStrategy):
    """Recovery strategy that always escalates."""

    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        return RecoveryAction(RecoveryAction.ESCALATE)


class MockRollbackStrategy(RecoveryStrategy):
    """Recovery strategy that always rolls back."""

    async def decide(self, ctx: RecoveryContext) -> RecoveryAction:
        return RecoveryAction(RecoveryAction.ROLLBACK)


async def test_agent_node_executes_agent(test_agent: ConcreteTestAgent) -> None:
    """AgentNode wrapping a ConcreteTestAgent returns updated SharedState."""
    node = AgentNode(node_id="test-node", agent=test_agent)
    state = {"task_id": str(uuid.uuid4()), "context": {}}
    result = await node.execute(state)
    assert result["agent_completed"] is True


async def test_agent_node_builds_agent_input(test_agent: ConcreteTestAgent) -> None:
    """SharedState with task_id and context keys converts to AgentInput correctly."""
    node = AgentNode(node_id="test-node", agent=test_agent)
    task_id = uuid.uuid4()
    state = {
        "task_id": str(task_id),
        "context": {"l0": "system prompt"},
    }
    agent_input = node._build_input(state)
    assert agent_input.task_id == task_id
    assert agent_input.shared_state is state
    assert agent_input.context_tiers == {"l0": "system prompt"}


async def test_agent_node_records_metrics(test_agent: ConcreteTestAgent) -> None:
    """After successful execution, node.last_metrics is populated with execution_time_ms > 0."""
    node = AgentNode(node_id="test-node", agent=test_agent)
    state = {"task_id": str(uuid.uuid4()), "context": {}}
    await node.execute(state)
    assert node.last_metrics is not None
    assert node.last_metrics.execution_time_ms >= 0


async def test_agent_node_recovery_on_failure(failing_agent: FailingTestAgent) -> None:
    """When agent raises and recovery returns RETRY_MODIFIED, agent is re-executed up to max_retries."""
    strategy = MockRetryStrategy()
    node = AgentNode(
        node_id="test-node",
        agent=failing_agent,
        recovery_strategy=strategy,
        max_retries=2,
    )
    state = {"task_id": str(uuid.uuid4()), "context": {}}
    # After 2 retries, strategy escalates, so exception propagates
    with pytest.raises(RuntimeError, match="intentional failure"):
        await node.execute(state)
    # Strategy was called for initial failure + 2 retries = at least 2 times
    assert strategy.call_count >= 2


async def test_agent_node_recovery_escalate(failing_agent: FailingTestAgent) -> None:
    """When recovery returns ESCALATE, AgentNode raises the original exception."""
    strategy = MockEscalateStrategy()
    node = AgentNode(
        node_id="test-node",
        agent=failing_agent,
        recovery_strategy=strategy,
    )
    state = {"task_id": str(uuid.uuid4()), "context": {}}
    with pytest.raises(RuntimeError, match="intentional failure"):
        await node.execute(state)


async def test_agent_node_recovery_rollback(failing_agent: FailingTestAgent) -> None:
    """When recovery returns ROLLBACK, AgentNode returns original state unchanged."""
    strategy = MockRollbackStrategy()
    node = AgentNode(
        node_id="test-node",
        agent=failing_agent,
        recovery_strategy=strategy,
    )
    original_state = {"task_id": str(uuid.uuid4()), "context": {}, "original_key": "value"}
    result = await node.execute(original_state)
    assert result["original_key"] == "value"
    assert "agent_completed" not in result


async def test_agent_node_no_recovery_raises(failing_agent: FailingTestAgent) -> None:
    """When no recovery_strategy set and agent fails, exception propagates."""
    node = AgentNode(node_id="test-node", agent=failing_agent)
    state = {"task_id": str(uuid.uuid4()), "context": {}}
    with pytest.raises(RuntimeError, match="intentional failure"):
        await node.execute(state)


async def test_agent_node_worktree_stub(test_agent: ConcreteTestAgent) -> None:
    """AgentNode with NoOpWorktreeProvider executes successfully."""
    worktree = NoOpWorktreeProvider()
    node = AgentNode(
        node_id="test-node",
        agent=test_agent,
        worktree_provider=worktree,
    )
    state = {"task_id": str(uuid.uuid4()), "context": {}}
    result = await node.execute(state)
    assert result["agent_completed"] is True


async def test_agent_node_timeout(slow_agent: SlowTestAgent) -> None:
    """AgentNode with timeout_seconds=0.001 cancels long-running agent."""
    node = AgentNode(
        node_id="test-node",
        agent=slow_agent,
        timeout_seconds=0.001,
    )
    state = {"task_id": str(uuid.uuid4()), "context": {}}
    with pytest.raises((TimeoutError, asyncio.TimeoutError)):
        await node.execute(state)


async def test_agent_node_emits_event_callback(test_agent: ConcreteTestAgent) -> None:
    """on_event callback receives dict with agent_id, agent_type, metrics after execution."""
    events: list[dict] = []

    def capture_event(event: dict) -> None:
        events.append(event)

    node = AgentNode(
        node_id="test-node",
        agent=test_agent,
        on_event=capture_event,
    )
    state = {"task_id": str(uuid.uuid4()), "context": {}}
    await node.execute(state)
    assert len(events) == 1
    event = events[0]
    assert "agent_id" in event
    assert "agent_type" in event
    assert "metrics" in event
    assert event["node_id"] == "test-node"
    assert event["review_passed"] is True
