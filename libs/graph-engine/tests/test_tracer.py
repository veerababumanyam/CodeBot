"""Tests for ExecutionTracer."""

from __future__ import annotations

import asyncio

import pytest

from graph_engine.models.execution import ExecutionRecord, GraphResult
from graph_engine.tracing.tracer import ExecutionTracer


@pytest.fixture()
def tracer() -> ExecutionTracer:
    return ExecutionTracer()


async def test_wrap_node_returns_async_callable(tracer: ExecutionTracer) -> None:
    async def node_fn(state: dict) -> dict:
        return {"node_outputs": {"a": {"status": "ok"}}}

    wrapped = tracer.wrap_node("a", node_fn)
    assert asyncio.iscoroutinefunction(wrapped)


async def test_wrapped_fn_records_duration(tracer: ExecutionTracer) -> None:
    async def node_fn(state: dict) -> dict:
        await asyncio.sleep(0.01)
        return {"node_outputs": {"a": {"status": "ok"}}}

    wrapped = tracer.wrap_node("a", node_fn)
    result = await wrapped({"node_outputs": {}, "execution_trace": [], "errors": []})
    assert len(tracer.records) == 1
    assert tracer.records[0].duration_ms > 0
    assert "execution_trace" in result
    assert result["execution_trace"][0]["duration_ms"] > 0


async def test_wrapped_fn_extracts_metrics(tracer: ExecutionTracer) -> None:
    async def node_fn(state: dict) -> dict:
        return {
            "node_outputs": {"a": {"status": "ok"}},
            "_metrics": {"input_tokens": 100, "output_tokens": 50, "cost_usd": 0.005},
        }

    wrapped = tracer.wrap_node("a", node_fn)
    result = await wrapped({"node_outputs": {}, "execution_trace": [], "errors": []})
    record = tracer.records[0]
    assert record.input_tokens == 100
    assert record.output_tokens == 50
    assert record.total_tokens == 150
    assert record.cost_usd == 0.005
    assert result["execution_trace"][0]["tokens"] == 150


async def test_wrapped_fn_on_error_records_and_reraises(tracer: ExecutionTracer) -> None:
    async def failing_fn(state: dict) -> dict:
        msg = "node failed"
        raise RuntimeError(msg)

    wrapped = tracer.wrap_node("failing", failing_fn)
    with pytest.raises(RuntimeError, match="node failed"):
        await wrapped({"node_outputs": {}, "execution_trace": [], "errors": []})

    assert len(tracer.records) == 1
    assert tracer.records[0].error == "node failed"
    assert tracer.records[0].duration_ms >= 0


async def test_records_accumulate(tracer: ExecutionTracer) -> None:
    async def node_fn(state: dict) -> dict:
        return {"node_outputs": {"x": {}}}

    for name in ("a", "b", "c"):
        wrapped = tracer.wrap_node(name, node_fn)
        await wrapped({"node_outputs": {}, "execution_trace": [], "errors": []})

    assert len(tracer.records) == 3
    assert [r.node_id for r in tracer.records] == ["a", "b", "c"]


async def test_get_result_aggregates(tracer: ExecutionTracer) -> None:
    async def node_fn(state: dict) -> dict:
        await asyncio.sleep(0.005)
        return {
            "node_outputs": {"x": {}},
            "_metrics": {"input_tokens": 10, "output_tokens": 20, "cost_usd": 0.001},
        }

    for name in ("a", "b"):
        wrapped = tracer.wrap_node(name, node_fn)
        await wrapped({"node_outputs": {}, "execution_trace": [], "errors": []})

    result = tracer.get_result("test-graph")
    assert isinstance(result, GraphResult)
    assert result.graph_name == "test-graph"
    assert result.total_tokens == 60  # (10+20)*2
    assert result.total_cost_usd == pytest.approx(0.002)
    assert result.success is True
    assert result.total_duration_ms > 0
    assert len(result.records) == 2


async def test_get_result_with_error_sets_success_false(tracer: ExecutionTracer) -> None:
    async def ok_fn(state: dict) -> dict:
        return {"node_outputs": {"a": {}}}

    async def fail_fn(state: dict) -> dict:
        msg = "boom"
        raise ValueError(msg)

    wrapped_ok = tracer.wrap_node("a", ok_fn)
    await wrapped_ok({"node_outputs": {}, "execution_trace": [], "errors": []})

    wrapped_fail = tracer.wrap_node("b", fail_fn)
    with pytest.raises(ValueError):
        await wrapped_fail({"node_outputs": {}, "execution_trace": [], "errors": []})

    result = tracer.get_result("test-graph")
    assert result.success is False
