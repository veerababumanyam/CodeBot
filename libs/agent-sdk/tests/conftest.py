"""Shared test fixtures for agent-sdk tests."""

from __future__ import annotations

from typing import Any

import pytest

from agent_sdk.agents.metrics import AgentMetrics
from agent_sdk.agents.protocols import LLMProvider, LLMResponse
from agent_sdk.models.enums import AgentPhase


class MockLLMProvider:
    """Mock LLM provider that returns canned responses."""

    def __init__(self, content: str = "Mock LLM response") -> None:
        self._content = content
        self.call_count = 0

    async def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str = "",
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        self.call_count += 1
        return LLMResponse(
            content=self._content,
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.001,
            model=model or "mock-model",
        )


class MockEventCallback:
    """Records state transition events for testing."""

    def __init__(self) -> None:
        self.transitions: list[tuple[AgentPhase, AgentPhase]] = []

    def __call__(self, prev: AgentPhase, new: AgentPhase) -> None:
        self.transitions.append((prev, new))


@pytest.fixture
def mock_llm_provider() -> MockLLMProvider:
    """Return a MockLLMProvider instance."""
    return MockLLMProvider()


@pytest.fixture
def transition_recorder() -> MockEventCallback:
    """Return a MockEventCallback instance for recording transitions."""
    return MockEventCallback()
