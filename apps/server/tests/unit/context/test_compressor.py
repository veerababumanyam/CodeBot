"""Unit tests for ContextCompressor with multi-strategy compression."""

from __future__ import annotations

from codebot.context.compressor import CompressionResult, ContextCompressor
from codebot.context.models import AgentContext, Priority


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def mock_summarizer(text: str) -> str:
    """Mock summarizer that returns a very short truncated version."""
    # Return just the first 20 characters -- this drastically reduces tokens.
    return text[:20]


def _make_over_budget_context() -> AgentContext:
    """Create an AgentContext that is well over budget.

    Budget: 50 tokens.
    Actual items total ~91 tokens, clearly over budget.
    """
    ctx = AgentContext(budget=50, model="gpt-4o")
    # ~4 tokens
    ctx.add("Critical system prompt data", Priority.CRITICAL, source="l0")
    # ~5 tokens
    ctx.add("High priority task data here", Priority.HIGH, source="task")
    # ~31 tokens
    ctx.add(
        "Medium architecture docs " * 10,
        Priority.MEDIUM,
        source="l1_arch",
    )
    # ~51 tokens
    ctx.add(
        "Low RAG retrieval result " * 10,
        Priority.LOW,
        source="l2_vector",
    )
    return ctx


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestContextCompressor:
    """Tests for ContextCompressor compression logic."""

    async def test_compress_evicts_low_first(self) -> None:
        """After compression, no LOW priority items should remain."""
        ctx = _make_over_budget_context()
        compressor = ContextCompressor(summarizer=mock_summarizer)

        await compressor.compress(ctx)

        low_items = [i for i in ctx.items if i.priority == Priority.LOW]
        assert low_items == [], "LOW priority items should be evicted first"

    async def test_compress_critical_never_dropped(self) -> None:
        """CRITICAL priority items must never be removed or modified."""
        ctx = _make_over_budget_context()
        original_critical = [
            i for i in ctx.items if i.priority == Priority.CRITICAL
        ]
        compressor = ContextCompressor(summarizer=mock_summarizer)

        await compressor.compress(ctx)

        remaining_critical = [
            i for i in ctx.items if i.priority == Priority.CRITICAL
        ]
        assert len(remaining_critical) == len(original_critical)
        assert remaining_critical[0].content == original_critical[0].content

    async def test_compress_within_budget_after(self) -> None:
        """Context should be within budget after compression."""
        ctx = _make_over_budget_context()
        compressor = ContextCompressor(summarizer=mock_summarizer)

        assert ctx.is_over_budget()
        await compressor.compress(ctx)

        assert not ctx.is_over_budget(), (
            f"Context should be within budget after compression. "
            f"Total: {ctx.total_tokens}, Budget: {ctx._budget.max_tokens}"
        )

    async def test_compress_without_summarizer_only_evicts(self) -> None:
        """Without a summarizer, only priority eviction should happen."""
        ctx = _make_over_budget_context()
        compressor = ContextCompressor()  # No summarizer

        result = await compressor.compress(ctx)

        # LOW items should be removed
        low_items = [i for i in ctx.items if i.priority == Priority.LOW]
        assert low_items == []
        # Summarization count should be 0
        assert result.items_summarized == 0

    async def test_compress_returns_compression_result(self) -> None:
        """Compress should return a CompressionResult with metrics."""
        ctx = _make_over_budget_context()
        compressor = ContextCompressor(summarizer=mock_summarizer)

        result = await compressor.compress(ctx)

        assert isinstance(result, CompressionResult)
        assert result.original_tokens > 0
        assert result.compressed_tokens > 0
        assert result.compressed_tokens <= result.original_tokens
        assert result.items_dropped > 0
        assert len(result.dropped_sources) > 0

    async def test_compress_summarizes_medium_when_needed(self) -> None:
        """When LOW eviction is insufficient, MEDIUM items should be summarized."""
        # Create a context where LOW eviction alone is not enough.
        # Budget is 20 tokens. CRITICAL ~4, HIGH ~5, MEDIUM ~31, LOW ~3.
        # After LOW eviction: total ~40 still > 20. Summarizer must compress MEDIUM.
        ctx = AgentContext(budget=20, model="gpt-4o")
        ctx.add("Critical system prompt data", Priority.CRITICAL, source="l0")
        ctx.add("High priority task data here", Priority.HIGH, source="task")
        ctx.add(
            "Medium architecture documentation content " * 8,
            Priority.MEDIUM,
            source="l1_arch",
        )
        ctx.add("Low result", Priority.LOW, source="l2_vector")

        compressor = ContextCompressor(summarizer=mock_summarizer)
        result = await compressor.compress(ctx)

        # The summarizer should have been called on MEDIUM items
        assert result.items_summarized > 0

    async def test_compress_noop_when_under_budget(self) -> None:
        """If context is already under budget, no compression should occur."""
        ctx = AgentContext(budget=10000, model="gpt-4o")
        ctx.add("Small content", Priority.CRITICAL, source="l0")

        assert not ctx.is_over_budget()

        compressor = ContextCompressor(summarizer=mock_summarizer)
        result = await compressor.compress(ctx)

        assert result.items_dropped == 0
        assert result.items_summarized == 0
        assert result.original_tokens == result.compressed_tokens

    async def test_compress_preserves_critical_item_ordering(self) -> None:
        """CRITICAL items should remain in order after compression."""
        ctx = AgentContext(budget=15, model="gpt-4o")
        ctx.add("First critical item", Priority.CRITICAL, source="l0_1")
        ctx.add("Second critical item", Priority.CRITICAL, source="l0_2")
        ctx.add("Low filler content " * 20, Priority.LOW, source="l2")

        compressor = ContextCompressor(summarizer=mock_summarizer)
        await compressor.compress(ctx)

        critical_items = [
            i for i in ctx.items if i.priority == Priority.CRITICAL
        ]
        assert len(critical_items) == 2
        assert "First critical" in critical_items[0].content
        assert "Second critical" in critical_items[1].content
