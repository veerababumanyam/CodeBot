"""Execution tracking dataclasses for graph runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(slots=True, kw_only=True)
class ExecutionRecord:
    """Single node execution record for tracing."""

    node_id: str
    started_at: float
    completed_at: float = 0.0
    duration_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    output_summary: str = ""
    error: str | None = None
    trace_id: UUID = field(default_factory=uuid4)


@dataclass(slots=True, kw_only=True)
class GraphResult:
    """Aggregate result of a full graph execution."""

    graph_name: str
    started_at: float
    completed_at: float = 0.0
    total_duration_ms: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    records: list[ExecutionRecord] = field(default_factory=list)
    success: bool = False
