"""Shared fixtures for LLM unit tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from codebot.llm.config import (
    BudgetConfig,
    FallbackConfig,
    LLMConfig,
    LLMSettings,
    ProviderConfig,
)
from codebot.llm.providers import ProviderRegistry
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


@pytest.fixture
def sample_llm_config() -> LLMConfig:
    """Return a minimal LLMConfig for integration-style tests."""
    return LLMConfig(
        providers=[
            ProviderConfig(
                model_name="claude-sonnet",
                litellm_model="anthropic/claude-sonnet-4",
                api_key_env="ANTHROPIC_API_KEY",
            ),
            ProviderConfig(
                model_name="gpt-4o",
                litellm_model="openai/gpt-4o",
                api_key_env="OPENAI_API_KEY",
            ),
            ProviderConfig(
                model_name="claude-haiku",
                litellm_model="anthropic/claude-haiku-3.5",
                api_key_env="ANTHROPIC_API_KEY",
            ),
            ProviderConfig(
                model_name="ollama-llama",
                litellm_model="ollama/llama3.1:70b",
                api_base="http://localhost:11434",
            ),
        ],
        routing_table={
            "CODE_GENERATION": RoutingRule(
                primary_model="claude-sonnet",
                fallback_models=["gpt-4o"],
                reason="Code gen",
            ),
            "ORCHESTRATION": RoutingRule(
                primary_model="gpt-4o",
                fallback_models=["claude-sonnet"],
                reason="Orchestration",
            ),
            "SIMPLE_TRANSFORM": RoutingRule(
                primary_model="claude-haiku",
                fallback_models=["claude-sonnet"],
                reason="Simple tasks",
            ),
        },
        budget=BudgetConfig(
            global_budget_usd=50.0,
            warn_threshold=0.8,
            halt_threshold=0.95,
        ),
        fallback=FallbackConfig(
            num_retries=3,
            timeout_seconds=60,
            cooldown_seconds=300,
        ),
        settings=LLMSettings(),
    )


@pytest.fixture
def sample_provider_registry(sample_llm_config: LLMConfig) -> ProviderRegistry:
    """Return a ProviderRegistry built from the sample LLMConfig."""
    return ProviderRegistry(sample_llm_config)


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    """Return an AsyncMock of EventBus with publish as AsyncMock."""
    bus = AsyncMock()
    bus.publish = AsyncMock()
    return bus
