"""Tests for LLM Pydantic schemas, enums, and exception types."""

from __future__ import annotations

import pytest

from codebot.llm.schemas import (
    BudgetDecision,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    RoutingConstraints,
    RoutingRule,
    TaskType,
    TokenUsage,
)
from codebot.llm.exceptions import (
    AllProvidersFailedError,
    BudgetExceededError,
    LLMError,
    ModelNotFoundError,
    ProviderUnavailableError,
)
from agent_sdk.models.enums import EventType


# ── TaskType enum ──────────────────────────────────────────────────────────

class TestTaskType:
    """TaskType enum covers all CodeBot task categories."""

    EXPECTED_VALUES = [
        "ORCHESTRATION",
        "CODE_GENERATION",
        "CODE_REVIEW",
        "RESEARCH",
        "SIMPLE_TRANSFORM",
        "DOCUMENTATION",
        "TESTING",
        "DEBUGGING",
        "BRAINSTORMING",
        "ARCHITECTURE",
        "PLANNING",
        "SECURITY_SCAN",
    ]

    @pytest.mark.parametrize("value", EXPECTED_VALUES)
    def test_has_value(self, value: str) -> None:
        assert TaskType(value) == value

    def test_is_str_enum(self) -> None:
        assert isinstance(TaskType.ORCHESTRATION, str)

    def test_at_least_12_values(self) -> None:
        assert len(TaskType) >= 12


# ── LLMRequest ─────────────────────────────────────────────────────────────

class TestLLMRequest:
    """LLMRequest validates messages, temperature, max_tokens, and stream."""

    def test_with_messages(self, sample_messages: list[LLMMessage]) -> None:
        req = LLMRequest(messages=sample_messages)
        assert len(req.messages) == 2
        assert req.messages[0].role == "system"

    def test_defaults(self, sample_messages: list[LLMMessage]) -> None:
        req = LLMRequest(messages=sample_messages)
        assert req.temperature == 0.7
        assert req.max_tokens == 4096
        assert req.stream is False

    def test_custom_values(self, sample_messages: list[LLMMessage]) -> None:
        req = LLMRequest(messages=sample_messages, temperature=0.2, max_tokens=8192, stream=True)
        assert req.temperature == 0.2
        assert req.max_tokens == 8192
        assert req.stream is True

    def test_constraints_optional(self, sample_messages: list[LLMMessage]) -> None:
        req = LLMRequest(messages=sample_messages)
        assert req.constraints is None

    def test_with_constraints(self, sample_messages: list[LLMMessage]) -> None:
        constraints = RoutingConstraints(complexity_score=0.5, max_cost_per_call=0.01)
        req = LLMRequest(messages=sample_messages, constraints=constraints)
        assert req.constraints is not None
        assert req.constraints.complexity_score == 0.5


# ── LLMResponse ────────────────────────────────────────────────────────────

class TestLLMResponse:
    """LLMResponse contains model, content, usage, and latency."""

    def test_construction(self) -> None:
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30, cost_usd=0.001)
        resp = LLMResponse(model="claude-sonnet", content="Hello!", usage=usage, latency_ms=120.5)
        assert resp.model == "claude-sonnet"
        assert resp.content == "Hello!"
        assert resp.latency_ms == 120.5

    def test_frozen(self) -> None:
        usage = TokenUsage()
        resp = LLMResponse(model="test", content="ok", usage=usage)
        with pytest.raises(Exception):
            resp.model = "changed"  # type: ignore[misc]

    def test_serialization(self) -> None:
        usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30, cost_usd=0.001)
        resp = LLMResponse(model="claude-sonnet", content="Hello!", usage=usage)
        data = resp.model_dump()
        assert data["model"] == "claude-sonnet"
        assert data["usage"]["prompt_tokens"] == 10


# ── TokenUsage ─────────────────────────────────────────────────────────────

class TestTokenUsage:
    """TokenUsage tracks prompt, completion, total tokens, and cost."""

    def test_defaults(self) -> None:
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0
        assert usage.cost_usd == 0.0

    def test_with_values(self) -> None:
        usage = TokenUsage(prompt_tokens=100, completion_tokens=200, total_tokens=300, cost_usd=0.05)
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 200
        assert usage.total_tokens == 300
        assert usage.cost_usd == 0.05

    def test_frozen(self) -> None:
        usage = TokenUsage()
        with pytest.raises(Exception):
            usage.prompt_tokens = 99  # type: ignore[misc]


# ── RoutingRule ────────────────────────────────────────────────────────────

class TestRoutingRule:
    """RoutingRule specifies primary model, fallbacks, and reason."""

    def test_construction(self, sample_routing_rule: RoutingRule) -> None:
        assert sample_routing_rule.primary_model == "claude-sonnet"
        assert sample_routing_rule.fallback_models == ["gpt-4o", "gemini-pro"]
        assert sample_routing_rule.reason == "Fast code generation"

    def test_defaults(self) -> None:
        rule = RoutingRule(primary_model="gpt-4o")
        assert rule.fallback_models == []
        assert rule.reason == ""

    def test_frozen(self) -> None:
        rule = RoutingRule(primary_model="gpt-4o")
        with pytest.raises(Exception):
            rule.primary_model = "changed"  # type: ignore[misc]


# ── RoutingConstraints ────────────────────────────────────────────────────

class TestRoutingConstraints:
    """RoutingConstraints control model selection preferences."""

    def test_defaults(self) -> None:
        constraints = RoutingConstraints()
        assert constraints.complexity_score is None
        assert constraints.max_cost_per_call is None
        assert constraints.prefer_local is False

    def test_with_values(self) -> None:
        constraints = RoutingConstraints(complexity_score=0.8, max_cost_per_call=0.05, prefer_local=True)
        assert constraints.complexity_score == 0.8
        assert constraints.max_cost_per_call == 0.05
        assert constraints.prefer_local is True


# ── BudgetDecision ─────────────────────────────────────────────────────────

class TestBudgetDecision:
    """BudgetDecision indicates whether a call is allowed and remaining budget."""

    def test_allowed(self) -> None:
        decision = BudgetDecision(allowed=True, remaining=42.50)
        assert decision.allowed is True
        assert decision.remaining == 42.50

    def test_denied(self) -> None:
        decision = BudgetDecision(allowed=False, remaining=0.0)
        assert decision.allowed is False

    def test_frozen(self) -> None:
        decision = BudgetDecision(allowed=True, remaining=10.0)
        with pytest.raises(Exception):
            decision.allowed = False  # type: ignore[misc]


# ── Exceptions ─────────────────────────────────────────────────────────────

class TestBudgetExceededError:
    """BudgetExceededError stores agent_id and budget_decision."""

    def test_attributes(self) -> None:
        decision = BudgetDecision(allowed=False, remaining=0.0)
        err = BudgetExceededError(agent_id="agent-123", budget_decision=decision)
        assert err.agent_id == "agent-123"
        assert err.budget_decision.allowed is False
        assert err.budget_decision.remaining == 0.0

    def test_is_llm_error(self) -> None:
        decision = BudgetDecision(allowed=False, remaining=0.0)
        err = BudgetExceededError(agent_id="test", budget_decision=decision)
        assert isinstance(err, LLMError)


class TestAllProvidersFailedError:
    """AllProvidersFailedError stores model name and list of errors."""

    def test_attributes(self) -> None:
        errors = [RuntimeError("timeout"), ValueError("bad response")]
        err = AllProvidersFailedError(model="claude-sonnet", errors=errors)
        assert err.model == "claude-sonnet"
        assert len(err.errors) == 2

    def test_is_llm_error(self) -> None:
        err = AllProvidersFailedError(model="test", errors=[])
        assert isinstance(err, LLMError)


class TestModelNotFoundError:
    """ModelNotFoundError stores model name."""

    def test_attributes(self) -> None:
        err = ModelNotFoundError(model="nonexistent-model")
        assert err.model == "nonexistent-model"

    def test_is_llm_error(self) -> None:
        err = ModelNotFoundError(model="test")
        assert isinstance(err, LLMError)


class TestProviderUnavailableError:
    """ProviderUnavailableError stores provider and reason."""

    def test_attributes(self) -> None:
        err = ProviderUnavailableError(provider="openai", reason="rate limited")
        assert err.provider == "openai"
        assert err.reason == "rate limited"

    def test_is_llm_error(self) -> None:
        err = ProviderUnavailableError(provider="test", reason="down")
        assert isinstance(err, LLMError)


# ── EventType LLM events ──────────────────────────────────────────────────

class TestEventTypeLLMEvents:
    """EventType enum in agent_sdk includes LLM-specific events."""

    @pytest.mark.parametrize("event", ["LLM_USAGE", "LLM_FAILURE", "BUDGET_WARNING", "BUDGET_EXCEEDED"])
    def test_has_llm_event(self, event: str) -> None:
        assert EventType(event) == event
