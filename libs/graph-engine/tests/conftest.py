"""Shared fixtures for graph-engine tests."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType


@dataclass(slots=True, kw_only=True)
class ConcreteTestAgent(BaseAgent):
    """Simple agent that returns state_updates with a marker."""

    agent_type: AgentType = field(default=AgentType.RESEARCHER, init=False)

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        return {}

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        return {}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        return PRAResult(is_complete=True, data={"result": "done"})

    async def review(self, result: PRAResult) -> AgentOutput:
        return AgentOutput(
            task_id=uuid.uuid4(),
            state_updates={"agent_completed": True},
            review_passed=True,
        )

    async def _initialize(self, agent_input: AgentInput) -> None:
        pass


@dataclass(slots=True, kw_only=True)
class FailingTestAgent(BaseAgent):
    """Agent whose execute() always raises RuntimeError."""

    agent_type: AgentType = field(default=AgentType.RESEARCHER, init=False)

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        raise RuntimeError("intentional failure")

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        return {}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        return PRAResult(is_complete=True)

    async def review(self, result: PRAResult) -> AgentOutput:
        return AgentOutput(
            task_id=uuid.uuid4(),
            state_updates={},
            review_passed=True,
        )

    async def _initialize(self, agent_input: AgentInput) -> None:
        pass


@dataclass(slots=True, kw_only=True)
class SlowTestAgent(BaseAgent):
    """Agent whose execute() sleeps for 10 seconds (for timeout testing)."""

    agent_type: AgentType = field(default=AgentType.RESEARCHER, init=False)

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        await asyncio.sleep(10)
        return {}

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        return {}

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        return PRAResult(is_complete=True)

    async def review(self, result: PRAResult) -> AgentOutput:
        return AgentOutput(
            task_id=uuid.uuid4(),
            state_updates={},
            review_passed=True,
        )

    async def _initialize(self, agent_input: AgentInput) -> None:
        pass


@pytest.fixture()
def test_agent() -> ConcreteTestAgent:
    """Return a ConcreteTestAgent instance."""
    return ConcreteTestAgent()


@pytest.fixture()
def failing_agent() -> FailingTestAgent:
    """Return a FailingTestAgent instance."""
    return FailingTestAgent()


@pytest.fixture()
def slow_agent() -> SlowTestAgent:
    """Return a SlowTestAgent instance."""
    return SlowTestAgent()


# Keep existing fixtures for other tests
@pytest.fixture()
def sample_node_def() -> dict:
    """A valid NodeDefinition as a raw dict."""
    return {
        "id": "analyzer",
        "type": "agent",
        "config": {"agent_type": "RESEARCHER"},
        "timeout_seconds": 300,
    }


@pytest.fixture()
def sample_edge_def() -> dict:
    """A valid EdgeDefinition as a raw dict."""
    return {
        "source": "analyzer",
        "target": "builder",
        "type": "state_flow",
    }


@pytest.fixture()
def sample_graph_def() -> dict:
    """A complete valid GraphDefinition as a raw dict."""
    return {
        "name": "test-pipeline",
        "version": "1.0",
        "description": "Test pipeline",
        "nodes": [
            {
                "id": "analyzer",
                "type": "agent",
                "config": {"agent_type": "RESEARCHER"},
                "timeout_seconds": 300,
            },
            {
                "id": "builder",
                "type": "agent",
                "config": {"agent_type": "BACKEND_DEV"},
                "timeout_seconds": 600,
            },
            {
                "id": "reviewer",
                "type": "agent",
                "config": {"agent_type": "CODE_REVIEWER"},
                "timeout_seconds": 300,
            },
        ],
        "edges": [
            {"source": "analyzer", "target": "builder", "type": "state_flow"},
            {"source": "builder", "target": "reviewer", "type": "state_flow"},
        ],
        "entry_nodes": ["analyzer"],
        "exit_nodes": ["reviewer"],
    }
