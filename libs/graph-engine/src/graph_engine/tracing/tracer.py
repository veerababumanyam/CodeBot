"""ExecutionTracer: wraps node functions to capture timing, tokens, and cost."""

from __future__ import annotations

import time
from collections.abc import Callable  # noqa: TC003
from typing import Any

from graph_engine.models.execution import ExecutionRecord, GraphResult


class ExecutionTracer:
    """Wraps node functions to capture per-node execution metrics."""

    def __init__(self) -> None:
        self.records: list[ExecutionRecord] = []

    def wrap_node(self, node_id: str, node_fn: Callable[..., Any]) -> Callable[..., Any]:
        """Return a traced version of a node function.

        The wrapped function records timing, token usage, and cost into an
        ExecutionRecord and appends trace data to the returned state dict.
        """

        async def traced_fn(state: dict[str, Any]) -> dict[str, Any]:
            record = ExecutionRecord(node_id=node_id, started_at=time.monotonic())
            try:
                result = await node_fn(state)
                record.completed_at = time.monotonic()
                record.duration_ms = int((record.completed_at - record.started_at) * 1000)

                if isinstance(result, dict):
                    metrics = result.get("_metrics", {})
                    record.input_tokens = metrics.get("input_tokens", 0)
                    record.output_tokens = metrics.get("output_tokens", 0)
                    record.total_tokens = record.input_tokens + record.output_tokens
                    record.cost_usd = metrics.get("cost_usd", 0.0)

                self.records.append(record)

                trace_entry = {
                    "node_id": node_id,
                    "duration_ms": record.duration_ms,
                    "tokens": record.total_tokens,
                    "cost_usd": record.cost_usd,
                }
                return {**result, "execution_trace": [trace_entry]}
            except Exception as e:
                record.completed_at = time.monotonic()
                record.duration_ms = int((record.completed_at - record.started_at) * 1000)
                record.error = str(e)
                self.records.append(record)
                raise

        return traced_fn

    def get_result(self, graph_name: str) -> GraphResult:
        """Aggregate all recorded execution data into a GraphResult."""
        total_tokens = sum(r.total_tokens for r in self.records)
        total_cost_usd = sum(r.cost_usd for r in self.records)
        success = all(r.error is None for r in self.records)
        started_at = min(r.started_at for r in self.records) if self.records else 0.0
        completed_at = max(r.completed_at for r in self.records) if self.records else 0.0
        total_duration_ms = int((completed_at - started_at) * 1000) if self.records else 0

        return GraphResult(
            graph_name=graph_name,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_ms=total_duration_ms,
            total_tokens=total_tokens,
            total_cost_usd=total_cost_usd,
            records=list(self.records),
            success=success,
        )
