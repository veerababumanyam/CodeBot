"""Token budget enforcement using tiktoken.

Provides accurate BPE-based token counting for context budget management.
For unknown or non-OpenAI models, falls back to cl100k_base encoding.
"""

from __future__ import annotations

import tiktoken


class TokenBudget:
    """Tracks and enforces token budgets using tiktoken-based counting.

    Attributes:
        max_tokens: The maximum token budget.
        used_tokens: Number of tokens consumed so far.
    """

    __slots__ = ("_encoder", "_max_tokens", "_used_tokens")

    def __init__(self, max_tokens: int, model: str = "gpt-4o") -> None:
        """Initialize a token budget.

        Args:
            max_tokens: Maximum number of tokens allowed.
            model: Model name for tokenizer selection. Falls back to
                cl100k_base for unknown models.
        """
        self._max_tokens = max_tokens
        self._used_tokens = 0
        try:
            self._encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            self._encoder = tiktoken.get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Args:
            text: The text to tokenize.

        Returns:
            Number of BPE tokens.
        """
        return len(self._encoder.encode(text))

    def has_budget(self, needed: int = 0) -> bool:
        """Check whether the budget can accommodate additional tokens.

        Args:
            needed: Number of additional tokens to check for.

        Returns:
            True if ``used_tokens + needed <= max_tokens``.
        """
        return (self._used_tokens + needed) <= self._max_tokens

    def consume(self, text: str) -> int:
        """Count tokens in *text* and add them to used_tokens.

        Args:
            text: The text whose tokens should be consumed.

        Returns:
            Number of tokens consumed.
        """
        tokens = self.count(text)
        self._used_tokens += tokens
        return tokens

    def release(self, tokens: int) -> None:
        """Release previously consumed tokens (floor at zero).

        Args:
            tokens: Number of tokens to release.
        """
        self._used_tokens = max(0, self._used_tokens - tokens)

    @property
    def used_tokens(self) -> int:
        """Number of tokens consumed so far."""
        return self._used_tokens

    @property
    def max_tokens(self) -> int:
        """Maximum token budget."""
        return self._max_tokens

    @property
    def remaining(self) -> int:
        """Remaining token budget (never negative)."""
        return max(0, self._max_tokens - self._used_tokens)
