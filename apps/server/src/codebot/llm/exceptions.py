"""Custom exception types for the Multi-LLM abstraction layer.

All LLM-specific exceptions inherit from ``LLMError`` so callers
can catch the entire family with a single ``except LLMError`` clause.
"""

from __future__ import annotations

from codebot.llm.schemas import BudgetDecision


class LLMError(Exception):
    """Base exception for all LLM subsystem errors."""


class BudgetExceededError(LLMError):
    """Raised when an LLM call would exceed the configured budget.

    Attributes:
        agent_id: The agent that attempted the call.
        budget_decision: The budget check result with remaining amount.
    """

    def __init__(self, agent_id: str, budget_decision: BudgetDecision) -> None:
        self.agent_id = agent_id
        self.budget_decision = budget_decision
        super().__init__(
            f"Budget exceeded for agent {agent_id}: "
            f"remaining=${budget_decision.remaining:.4f}"
        )


class AllProvidersFailedError(LLMError):
    """Raised when all providers in a fallback chain have failed.

    Attributes:
        model: The originally requested model name.
        errors: List of exceptions from each failed provider attempt.
    """

    def __init__(self, model: str, errors: list[Exception]) -> None:
        self.model = model
        self.errors = errors
        super().__init__(
            f"All providers failed for model '{model}': "
            f"{len(errors)} error(s)"
        )


class ModelNotFoundError(LLMError):
    """Raised when a requested model is not found in the provider registry.

    Attributes:
        model: The model name that was not found.
    """

    def __init__(self, model: str) -> None:
        self.model = model
        super().__init__(f"Model not found: '{model}'")


class ProviderUnavailableError(LLMError):
    """Raised when a specific provider is temporarily unavailable.

    Attributes:
        provider: The provider name (e.g. "anthropic", "openai").
        reason: Human-readable explanation of why the provider is unavailable.
    """

    def __init__(self, provider: str, reason: str) -> None:
        self.provider = provider
        self.reason = reason
        super().__init__(f"Provider '{provider}' unavailable: {reason}")
