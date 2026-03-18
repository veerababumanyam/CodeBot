"""Agent metrics collection.

Stub file -- implementation follows TDD GREEN phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, kw_only=True)
class AgentMetrics:
    """Collects execution metrics for a single agent run."""

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
        raise NotImplementedError("RED phase stub")

    def stop(self) -> None:
        raise NotImplementedError("RED phase stub")

    def record_llm_call(
        self, *, input_tokens: int, output_tokens: int, cost_usd: float, duration_ms: int
    ) -> None:
        raise NotImplementedError("RED phase stub")

    def record_retry(self) -> None:
        raise NotImplementedError("RED phase stub")

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError("RED phase stub")
