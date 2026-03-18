"""Agent metrics collection.

Tracks execution time, token usage, cost, and retry counts for
a single agent execution. Designed to be created fresh per execute()
call to ensure statelessness between runs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, kw_only=True)
class AgentMetrics:
    """Collects execution metrics for a single agent run.

    Attributes:
        execution_time_ms: Total wall-clock execution time in milliseconds.
        input_tokens: Cumulative input tokens across all LLM calls.
        output_tokens: Cumulative output tokens across all LLM calls.
        total_tokens: Sum of input_tokens + output_tokens.
        cost_usd: Cumulative cost across all LLM calls.
        retry_count: Number of retries during execution.
        llm_calls: Number of LLM calls made.
    """

    execution_time_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    retry_count: int = 0
    llm_calls: int = 0
    _start_ns: int = field(default=0, repr=False)
    _stop_ns: int = field(default=0, repr=False)

    def start(self) -> None:
        """Mark the start of execution timing."""
        self._start_ns = time.monotonic_ns()

    def stop(self) -> None:
        """Mark the end of execution timing and compute elapsed time."""
        self._stop_ns = time.monotonic_ns()
        self.execution_time_ms = (self._stop_ns - self._start_ns) // 1_000_000

    def record_llm_call(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        duration_ms: int,
    ) -> None:
        """Record metrics from a single LLM call.

        Args:
            input_tokens: Number of input tokens in this call.
            output_tokens: Number of output tokens in this call.
            cost_usd: Cost of this call in USD.
            duration_ms: Duration of this call in milliseconds.
        """
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += input_tokens + output_tokens
        self.cost_usd += cost_usd
        self.llm_calls += 1

    def record_retry(self) -> None:
        """Increment the retry counter."""
        self.retry_count += 1

    def to_dict(self) -> dict[str, Any]:
        """Return all public metrics as a plain dict for event emission.

        Private fields (_start_ns, _stop_ns) are excluded.
        """
        return {
            "execution_time_ms": self.execution_time_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "retry_count": self.retry_count,
            "llm_calls": self.llm_calls,
        }
