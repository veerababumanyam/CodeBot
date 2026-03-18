"""Shared fixtures for LLM unit tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from codebot.llm.schemas import LLMMessage, RoutingRule


@pytest.fixture
def sample_messages() -> list[LLMMessage]:
    """Return a list of LLMMessage objects for testing."""
    return [
        LLMMessage(role="system", content="You are a coding assistant."),
        LLMMessage(role="user", content="Write a hello world function."),
    ]


@pytest.fixture
def sample_routing_rule() -> RoutingRule:
    """Return a sample RoutingRule for testing."""
    return RoutingRule(
        primary_model="claude-sonnet",
        fallback_models=["gpt-4o", "gemini-pro"],
        reason="Fast code generation",
    )


@pytest.fixture
def mock_litellm_response() -> MagicMock:
    """Return a mock LiteLLM ModelResponse with usage fields."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = "Hello, world!"
    response.model = "anthropic/claude-sonnet-4"

    usage = MagicMock()
    usage.prompt_tokens = 50
    usage.completion_tokens = 100
    usage.total_tokens = 150
    response.usage = usage

    return response
