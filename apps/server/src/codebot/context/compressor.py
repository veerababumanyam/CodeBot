"""Context compression with priority-based eviction and LLM summarization.

Implements a three-stage compression strategy for reducing oversized
context to fit within a token budget:

1. **Stage 1 -- Evict LOW priority items:** removes all LOW items and
   reclaims their tokens.
2. **Stage 2 -- Summarize MEDIUM priority items:** uses an injected
   summarizer callable to compress MEDIUM items into shorter versions.
3. **Stage 3 -- Summarize HIGH priority items:** same as Stage 2 but
   for HIGH priority items.

CRITICAL priority items are **never** removed or modified.

The summarizer callable is intentionally decoupled from any specific
LLM library -- any ``async (str) -> str`` function works, making the
compressor testable with simple mocks and flexible in production.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from pydantic import BaseModel

from codebot.context.models import AgentContext, Priority

logger = logging.getLogger(__name__)

# Type alias for the summarizer callable.  Accepts a text string and
# returns a (shorter) summarized version asynchronously.
SummarizerFn = Callable[[str], Awaitable[str]]


class CompressionResult(BaseModel):
    """Metrics from a compression run.

    Attributes:
        original_tokens: Token count before compression.
        compressed_tokens: Token count after compression.
        items_dropped: Number of items removed entirely.
        items_summarized: Number of items whose content was summarized.
        dropped_sources: Source identifiers of dropped items.
    """

    original_tokens: int
    compressed_tokens: int
    items_dropped: int
    items_summarized: int
    dropped_sources: list[str]


class ContextCompressor:
    """Multi-strategy context compressor with priority-based eviction.

    Compression proceeds in three stages, stopping as soon as the
    context fits within its budget:

    1. Evict all LOW priority items.
    2. Summarize MEDIUM priority items via the injected summarizer.
    3. Summarize HIGH priority items via the injected summarizer.

    CRITICAL items are never touched.

    Args:
        summarizer: An async callable ``(str) -> str`` that produces
            a shorter version of the input text.  When ``None``,
            only priority eviction is performed (no summarization).
    """

    __slots__ = ("_summarizer",)

    def __init__(self, summarizer: SummarizerFn | None = None) -> None:
        self._summarizer = summarizer

    async def compress(self, context: AgentContext) -> CompressionResult:
        """Compress *context* to fit within its token budget.

        Applies stages in order, returning early if the budget is
        satisfied.  CRITICAL items are never removed or modified.

        Args:
            context: The mutable ``AgentContext`` to compress in-place.

        Returns:
            A ``CompressionResult`` describing what was done.
        """
        original_tokens = context.total_tokens
        items_dropped = 0
        items_summarized = 0
        dropped_sources: list[str] = []

        # Short-circuit: already within budget
        if not context.is_over_budget():
            return CompressionResult(
                original_tokens=original_tokens,
                compressed_tokens=context.total_tokens,
                items_dropped=0,
                items_summarized=0,
                dropped_sources=[],
            )

        # ------------------------------------------------------------------
        # Stage 1: Evict LOW priority items
        # ------------------------------------------------------------------
        low_items = [
            item for item in context.items if item.priority == Priority.LOW
        ]
        if low_items:
            dropped_sources.extend(item.source for item in low_items)
            items_dropped += len(low_items)
            context.remove_items_by_priority(Priority.LOW)
            logger.debug(
                "Stage 1: evicted %d LOW items, reclaimed tokens",
                len(low_items),
            )

        if not context.is_over_budget():
            return CompressionResult(
                original_tokens=original_tokens,
                compressed_tokens=context.total_tokens,
                items_dropped=items_dropped,
                items_summarized=items_summarized,
                dropped_sources=dropped_sources,
            )

        # ------------------------------------------------------------------
        # Stage 2: Summarize MEDIUM priority items
        # ------------------------------------------------------------------
        if self._summarizer is not None:
            summarized_count = await self._summarize_priority(
                context, Priority.MEDIUM
            )
            items_summarized += summarized_count

        if not context.is_over_budget():
            return CompressionResult(
                original_tokens=original_tokens,
                compressed_tokens=context.total_tokens,
                items_dropped=items_dropped,
                items_summarized=items_summarized,
                dropped_sources=dropped_sources,
            )

        # ------------------------------------------------------------------
        # Stage 3: Summarize HIGH priority items
        # ------------------------------------------------------------------
        if self._summarizer is not None:
            summarized_count = await self._summarize_priority(
                context, Priority.HIGH
            )
            items_summarized += summarized_count

        if context.is_over_budget():
            logger.warning(
                "Context still over budget after all compression stages. "
                "Total: %d tokens (CRITICAL items preserved).",
                context.total_tokens,
            )

        return CompressionResult(
            original_tokens=original_tokens,
            compressed_tokens=context.total_tokens,
            items_dropped=items_dropped,
            items_summarized=items_summarized,
            dropped_sources=dropped_sources,
        )

    async def _summarize_priority(
        self, context: AgentContext, priority: Priority
    ) -> int:
        """Summarize all items at the given priority level.

        Args:
            context: The mutable context to modify in-place.
            priority: Which priority level to summarize.

        Returns:
            Number of items summarized.
        """
        assert self._summarizer is not None  # noqa: S101
        count = 0
        # Snapshot items to avoid mutation during iteration
        target_items = [
            item for item in context.items if item.priority == priority
        ]
        for item in target_items:
            summarized = await self._summarizer(item.content)
            if summarized != item.content:
                context.replace_item_content(item.id, summarized)
                count += 1
        return count
