"""Unit tests for TokenBudget and context models.

Tests cover:
- TokenBudget token counting via tiktoken
- TokenBudget budget tracking (consume, release, has_budget)
- AgentContext add/remove/query operations
- Priority enum values
- ContextItem validation
"""

from __future__ import annotations

import pytest

from codebot.context.budget import TokenBudget
from codebot.context.models import AgentContext, ContextItem, Priority


class TestTokenBudget:
    """Tests for the TokenBudget class."""

    def test_token_budget_count_returns_positive_int(self) -> None:
        """TokenBudget.count() should return a positive integer for non-empty text."""
        budget = TokenBudget(max_tokens=1000, model="gpt-4o")
        count = budget.count("hello world")
        assert isinstance(count, int)
        assert count > 0

    def test_token_budget_has_budget_under_limit(self) -> None:
        """has_budget() returns True when usage is under the limit."""
        budget = TokenBudget(max_tokens=1000, model="gpt-4o")
        assert budget.has_budget() is True
        assert budget.has_budget(needed=500) is True

    def test_token_budget_has_budget_over_limit(self) -> None:
        """has_budget() returns False when usage would exceed the limit."""
        budget = TokenBudget(max_tokens=10, model="gpt-4o")
        # Consume some tokens to get near the limit
        budget.consume("This is a test sentence with several words in it.")
        assert budget.has_budget() is False

    def test_token_budget_consume_increments_used(self) -> None:
        """consume() should increment used_tokens by the token count of the text."""
        budget = TokenBudget(max_tokens=1000, model="gpt-4o")
        assert budget.used_tokens == 0
        tokens = budget.consume("hello world")
        assert tokens > 0
        assert budget.used_tokens == tokens
        # Consume more
        tokens2 = budget.consume("another phrase")
        assert budget.used_tokens == tokens + tokens2

    def test_token_budget_release_decrements_used(self) -> None:
        """release() should decrement used_tokens."""
        budget = TokenBudget(max_tokens=1000, model="gpt-4o")
        consumed = budget.consume("hello world")
        budget.release(consumed)
        assert budget.used_tokens == 0

    def test_token_budget_release_floors_at_zero(self) -> None:
        """release() should not go below zero."""
        budget = TokenBudget(max_tokens=1000, model="gpt-4o")
        budget.release(500)  # Release more than consumed
        assert budget.used_tokens == 0

    def test_token_budget_unknown_model_falls_back(self) -> None:
        """Unknown model names should fall back to cl100k_base encoding."""
        budget = TokenBudget(max_tokens=1000, model="unknown-model-xyz")
        count = budget.count("hello world")
        assert isinstance(count, int)
        assert count > 0

    def test_token_budget_remaining_property(self) -> None:
        """remaining property should return max_tokens - used_tokens."""
        budget = TokenBudget(max_tokens=1000, model="gpt-4o")
        assert budget.remaining == 1000
        budget.consume("hello")
        assert budget.remaining < 1000
        assert budget.remaining == budget.max_tokens - budget.used_tokens


class TestAgentContext:
    """Tests for the AgentContext class."""

    def test_agent_context_add_tracks_tokens(self) -> None:
        """Adding content to AgentContext should track token usage."""
        ctx = AgentContext(budget=500, model="gpt-4o")
        result = ctx.add("hello world", Priority.HIGH, source="test")
        assert result is True
        assert ctx.total_tokens > 0

    def test_agent_context_add_returns_false_over_budget(self) -> None:
        """add() returns False when adding content exceeds the budget."""
        ctx = AgentContext(budget=5, model="gpt-4o")
        # Add content that will exceed the tiny budget
        result = ctx.add(
            "This is a much longer sentence that will definitely exceed five tokens.",
            Priority.LOW,
            source="test",
        )
        assert result is False

    def test_agent_context_is_over_budget(self) -> None:
        """is_over_budget() returns True when used tokens exceed budget."""
        ctx = AgentContext(budget=5, model="gpt-4o")
        ctx.add(
            "This sentence has more than five tokens for sure.",
            Priority.LOW,
            source="test",
        )
        assert ctx.is_over_budget() is True

    def test_agent_context_remove_by_priority(self) -> None:
        """remove_items_by_priority() removes items and reclaims tokens."""
        ctx = AgentContext(budget=5000, model="gpt-4o")
        ctx.add("critical item", Priority.CRITICAL, source="l0")
        ctx.add("low priority item one", Priority.LOW, source="l2")
        ctx.add("low priority item two", Priority.LOW, source="l2")

        tokens_before = ctx.total_tokens
        reclaimed = ctx.remove_items_by_priority(Priority.LOW)

        assert reclaimed > 0
        assert ctx.total_tokens == tokens_before - reclaimed
        # Only the CRITICAL item should remain
        assert len(ctx.items) == 1
        assert ctx.items[0].priority == Priority.CRITICAL

    def test_agent_context_to_text_joins_items(self) -> None:
        """to_text() joins all item contents with '---' separator."""
        ctx = AgentContext(budget=5000, model="gpt-4o")
        ctx.add("first item", Priority.HIGH, source="test")
        ctx.add("second item", Priority.MEDIUM, source="test")
        text = ctx.to_text()
        assert "first item" in text
        assert "second item" in text
        assert "\n---\n" in text

    def test_agent_context_remaining_budget(self) -> None:
        """remaining_budget property tracks remaining token budget."""
        ctx = AgentContext(budget=5000, model="gpt-4o")
        assert ctx.remaining_budget == 5000
        ctx.add("some content", Priority.HIGH, source="test")
        assert ctx.remaining_budget < 5000
        assert ctx.remaining_budget >= 0

    def test_agent_context_has_budget(self) -> None:
        """has_budget() checks if there is room for more tokens."""
        ctx = AgentContext(budget=5000, model="gpt-4o")
        assert ctx.has_budget() is True
        assert ctx.has_budget(reserve=4999) is True
        assert ctx.has_budget(reserve=5001) is False


class TestPriorityEnum:
    """Tests for the Priority enum."""

    def test_priority_enum_values(self) -> None:
        """Priority enum should have exactly 4 values."""
        values = list(Priority)
        assert len(values) == 4
        assert Priority.CRITICAL in values
        assert Priority.HIGH in values
        assert Priority.MEDIUM in values
        assert Priority.LOW in values

    def test_priority_enum_is_str(self) -> None:
        """Priority values should be strings (str, Enum pattern)."""
        assert isinstance(Priority.CRITICAL, str)
        assert Priority.CRITICAL == "CRITICAL"


class TestContextItem:
    """Tests for the ContextItem model."""

    def test_context_item_validation(self) -> None:
        """ContextItem should validate with all required fields."""
        item = ContextItem(
            id="test-1",
            content="some content",
            priority=Priority.HIGH,
            token_count=10,
            source="l0",
        )
        assert item.id == "test-1"
        assert item.content == "some content"
        assert item.priority == Priority.HIGH
        assert item.token_count == 10
        assert item.source == "l0"

    def test_context_item_rejects_missing_fields(self) -> None:
        """ContextItem should reject creation with missing required fields."""
        with pytest.raises(Exception):  # noqa: B017
            ContextItem(id="test-1", content="x")  # type: ignore[call-arg]
