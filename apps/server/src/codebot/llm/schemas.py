"""Pydantic v2 schemas and enums for the Multi-LLM abstraction layer.

Defines all data contracts used by the LLM subsystem: request/response
models, routing rules, budget decisions, and the TaskType enum that
maps every CodeBot task category to a model selection strategy.
"""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict


class TaskType(str, enum.Enum):
    """Maps each CodeBot task category to a model selection strategy.

    Used by the TaskBasedModelRouter to determine which LLM model
    should handle a given task based on its type and routing rules.
    """

    ORCHESTRATION = "ORCHESTRATION"
    CODE_GENERATION = "CODE_GENERATION"
    CODE_REVIEW = "CODE_REVIEW"
    RESEARCH = "RESEARCH"
    SIMPLE_TRANSFORM = "SIMPLE_TRANSFORM"
    DOCUMENTATION = "DOCUMENTATION"
    TESTING = "TESTING"
    DEBUGGING = "DEBUGGING"
    BRAINSTORMING = "BRAINSTORMING"
    ARCHITECTURE = "ARCHITECTURE"
    PLANNING = "PLANNING"
    SECURITY_SCAN = "SECURITY_SCAN"


class RoutingConstraints(BaseModel):
    """Constraints that influence model selection during routing.

    Attributes:
        complexity_score: Task complexity from 0.0 (trivial) to 1.0 (very complex).
            When < 0.3, the router downgrades to a cheaper model.
        max_cost_per_call: Maximum allowed cost in USD for a single LLM call.
        prefer_local: When True, router prefers self-hosted models (e.g. Ollama).
    """

    complexity_score: float | None = None
    max_cost_per_call: float | None = None
    prefer_local: bool = False


class RoutingRule(BaseModel):
    """Defines which model to use for a given task type.

    Attributes:
        primary_model: The preferred model name for this task type.
        fallback_models: Ordered list of fallback model names if the primary fails.
        reason: Human-readable explanation for this routing choice.
    """

    model_config = ConfigDict(frozen=True)

    primary_model: str
    fallback_models: list[str] = []
    reason: str = ""


class LLMMessage(BaseModel):
    """A single message in an LLM conversation.

    Attributes:
        role: Message role (e.g. "system", "user", "assistant").
        content: The message text content.
    """

    role: str
    content: str


class LLMRequest(BaseModel):
    """Request payload for an LLM call.

    Attributes:
        messages: Ordered list of conversation messages.
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
        max_tokens: Maximum number of tokens in the response.
        stream: Whether to stream the response.
        constraints: Optional routing constraints for model selection.
    """

    messages: list[LLMMessage]
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False
    constraints: RoutingConstraints | None = None


class TokenUsage(BaseModel):
    """Token usage statistics from an LLM call.

    Attributes:
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        total_tokens: Total tokens (prompt + completion).
        cost_usd: Estimated cost of the call in USD.
    """

    model_config = ConfigDict(frozen=True)

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0


class LLMResponse(BaseModel):
    """Response from an LLM call.

    Attributes:
        model: The model identifier that served the request.
        content: The generated text content.
        usage: Token usage statistics.
        latency_ms: End-to-end latency in milliseconds.
    """

    model_config = ConfigDict(frozen=True)

    model: str
    content: str
    usage: TokenUsage
    latency_ms: float = 0.0


class BudgetDecision(BaseModel):
    """Result of a budget check before making an LLM call.

    Attributes:
        allowed: Whether the call is permitted within budget.
        remaining: Remaining budget in USD after this decision.
    """

    model_config = ConfigDict(frozen=True)

    allowed: bool
    remaining: float
