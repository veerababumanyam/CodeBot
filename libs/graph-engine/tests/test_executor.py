"""Tests for ExecutionEngine."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from graph_engine.engine.executor import ExecutionEngine
from graph_engine.models.edge_types import EdgeDefinition, EdgeType
from graph_engine.models.execution import GraphResult
from graph_engine.models.graph_def import GraphDefinition
from graph_engine.models.node_types import NodeDefinition, NodeType

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# --------------- fixtures ---------------


@pytest.fixture()
def linear_graph_def() -> GraphDefinition:
    """Simple linear: a -> b -> c."""
    return GraphDefinition(
        name="linear-pipeline",
        nodes=[
            NodeDefinition(id="a", type=NodeType.AGENT, config={}),
            NodeDefinition(id="b", type=NodeType.AGENT, config={}),
            NodeDefinition(id="c", type=NodeType.AGENT, config={}),
        ],
        edges=[
            EdgeDefinition(source="a", target="b"),
            EdgeDefinition(source="b", target="c"),
        ],
        entry_nodes=["a"],
        exit_nodes=["c"],
    )


@pytest.fixture()
def parallel_graph_def() -> GraphDefinition:
    """Diamond: a -> (b, c) -> d."""
    return GraphDefinition(
        name="parallel-pipeline",
        nodes=[
            NodeDefinition(id="a", type=NodeType.AGENT, config={}),
            NodeDefinition(id="b", type=NodeType.AGENT, config={}),
            NodeDefinition(id="c", type=NodeType.AGENT, config={}),
            NodeDefinition(id="d", type=NodeType.MERGE, config={}),
        ],
        edges=[
            EdgeDefinition(source="a", target="b"),
            EdgeDefinition(source="a", target="c"),
            EdgeDefinition(source="b", target="d"),
            EdgeDefinition(source="c", target="d"),
        ],
        entry_nodes=["a"],
        exit_nodes=["d"],
    )


@pytest.fixture()
def switch_graph_def() -> GraphDefinition:
    """analyzer -> router(SWITCH) -> simple_builder / complex_builder -> merger."""
    return GraphDefinition(
        name="switch-pipeline",
        nodes=[
            NodeDefinition(id="analyzer", type=NodeType.AGENT, config={}),
            NodeDefinition(
                id="router",
                type=NodeType.SWITCH,
                config={
                    "cases": {
                        "simple": "state.node_outputs.analyzer.complexity == 'low'",
                        "complex": "state.node_outputs.analyzer.complexity == 'high'",
                    },
                    "default": "simple",
                },
            ),
            NodeDefinition(id="simple_builder", type=NodeType.AGENT, config={}),
            NodeDefinition(id="complex_builder", type=NodeType.AGENT, config={}),
            NodeDefinition(id="merger", type=NodeType.MERGE, config={}),
        ],
        edges=[
            EdgeDefinition(source="analyzer", target="router"),
            EdgeDefinition(
                source="router",
                target="simple_builder",
                type=EdgeType.CONTROL_FLOW,
                condition="case == 'simple'",
            ),
            EdgeDefinition(
                source="router",
                target="complex_builder",
                type=EdgeType.CONTROL_FLOW,
                condition="case == 'complex'",
            ),
            EdgeDefinition(source="simple_builder", target="merger"),
            EdgeDefinition(source="complex_builder", target="merger"),
        ],
        entry_nodes=["analyzer"],
        exit_nodes=["merger"],
    )


# --------------- executor tests ---------------


async def test_execute_returns_graph_result(linear_graph_def: GraphDefinition) -> None:
    engine = ExecutionEngine()
    result = await engine.execute(linear_graph_def)
    assert isinstance(result, GraphResult)


async def test_execute_linear_has_3_records(linear_graph_def: GraphDefinition) -> None:
    engine = ExecutionEngine()
    result = await engine.execute(linear_graph_def)
    assert len(result.records) == 3
    node_ids = [r.node_id for r in result.records]
    assert set(node_ids) == {"a", "b", "c"}


async def test_execute_linear_topological_order(linear_graph_def: GraphDefinition) -> None:
    engine = ExecutionEngine()
    result = await engine.execute(linear_graph_def)
    records_by_id = {r.node_id: r for r in result.records}
    assert records_by_id["a"].started_at <= records_by_id["b"].started_at
    assert records_by_id["b"].started_at <= records_by_id["c"].started_at


async def test_execute_parallel_has_4_records(parallel_graph_def: GraphDefinition) -> None:
    engine = ExecutionEngine()
    result = await engine.execute(parallel_graph_def)
    assert len(result.records) == 4
    node_ids = {r.node_id for r in result.records}
    assert node_ids == {"a", "b", "c", "d"}


async def test_execute_parallel_overlapping_timestamps(
    parallel_graph_def: GraphDefinition,
) -> None:
    """Prove parallel branches execute concurrently with overlapping time windows."""

    async def slow_node(node_id: str) -> Any:
        async def fn(state: dict[str, Any]) -> dict[str, Any]:
            await asyncio.sleep(0.05)
            return {"node_outputs": {node_id: {"status": "executed", "type": "agent"}}}

        return fn

    engine = ExecutionEngine(
        node_functions={
            "b": await slow_node("b"),
            "c": await slow_node("c"),
        }
    )
    result = await engine.execute(parallel_graph_def)
    records_by_id = {r.node_id: r for r in result.records}
    b_rec = records_by_id["b"]
    c_rec = records_by_id["c"]
    # Overlapping: B started before C completed AND C started before B completed
    assert b_rec.started_at < c_rec.completed_at
    assert c_rec.started_at < b_rec.completed_at


async def test_execute_success_true(linear_graph_def: GraphDefinition) -> None:
    engine = ExecutionEngine()
    result = await engine.execute(linear_graph_def)
    assert result.success is True


async def test_execute_total_tokens(linear_graph_def: GraphDefinition) -> None:
    """Tokens are summed from all node records."""

    async def token_node(node_id: str) -> Any:
        async def fn(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "node_outputs": {node_id: {"status": "ok"}},
                "_metrics": {"input_tokens": 10, "output_tokens": 5, "cost_usd": 0.001},
            }

        return fn

    engine = ExecutionEngine(
        node_functions={
            "a": await token_node("a"),
            "b": await token_node("b"),
            "c": await token_node("c"),
        }
    )
    result = await engine.execute(linear_graph_def)
    assert result.total_tokens == 45  # (10+5)*3
    assert result.total_cost_usd == pytest.approx(0.003)


async def test_execute_total_duration(linear_graph_def: GraphDefinition) -> None:
    """Duration should be greater than 0."""

    async def slow_fn(state: dict[str, Any]) -> dict[str, Any]:
        await asyncio.sleep(0.01)
        return {"node_outputs": {"a": {"status": "ok"}}}

    engine = ExecutionEngine(node_functions={"a": slow_fn})
    result = await engine.execute(linear_graph_def)
    assert result.total_duration_ms > 0


async def test_execute_switch_routes_correctly(
    switch_graph_def: GraphDefinition,
) -> None:
    """SWITCH routes to complex_builder when analyzer outputs complexity=high."""

    async def analyzer_high(state: dict[str, Any]) -> dict[str, Any]:
        return {
            "node_outputs": {
                "analyzer": {"status": "executed", "type": "agent", "complexity": "high"}
            }
        }

    engine = ExecutionEngine(node_functions={"analyzer": analyzer_high})
    result = await engine.execute(switch_graph_def)
    node_ids = {r.node_id for r in result.records}
    assert "complex_builder" in node_ids
    assert "simple_builder" not in node_ids


async def test_execute_from_yaml() -> None:
    """Load and execute from a YAML fixture file."""
    yaml_path = str(FIXTURES_DIR / "simple_pipeline.yaml")
    engine = ExecutionEngine()
    result = await engine.execute_from_yaml(yaml_path)
    assert isinstance(result, GraphResult)
    assert result.success is True
    assert len(result.records) == 3


async def test_execute_custom_node_functions(linear_graph_def: GraphDefinition) -> None:
    """Custom node_functions override the default stub for specific nodes."""
    custom_output = {"special": "value", "was_custom": True}

    async def custom_fn(state: dict[str, Any]) -> dict[str, Any]:
        return {"node_outputs": {"b": custom_output}}

    engine = ExecutionEngine(node_functions={"b": custom_fn})
    result = await engine.execute(linear_graph_def)
    # Find the node_outputs for b in the final state -- check via records
    b_records = [r for r in result.records if r.node_id == "b"]
    assert len(b_records) == 1
    assert result.success is True
