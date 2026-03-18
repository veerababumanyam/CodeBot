"""Tests for GraphCompiler with GATE and SWITCH semantics."""

from __future__ import annotations

from typing import Any

import pytest

from graph_engine.engine.compiler import GateFailedError, GraphCompiler
from graph_engine.models.edge_types import EdgeDefinition, EdgeType
from graph_engine.models.graph_def import GraphDefinition
from graph_engine.models.node_types import NodeDefinition, NodeType
from graph_engine.tracing.tracer import ExecutionTracer


# --------------- fixtures ---------------


@pytest.fixture()
def simple_graph_def(sample_graph_def: dict) -> GraphDefinition:
    """Linear: analyzer -> builder -> reviewer."""
    return GraphDefinition.model_validate(sample_graph_def)


@pytest.fixture()
def switch_graph_def() -> GraphDefinition:
    """analyzer -> router(SWITCH) -> simple_builder / complex_builder -> merger.

    The analyzer outputs complexity level in node_outputs.analyzer.complexity.
    The router reads this to determine the branch.
    """
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


@pytest.fixture()
def parallel_graph_def() -> GraphDefinition:
    """analyzer -> (builder_a, builder_b) -> merger."""
    return GraphDefinition(
        name="parallel-pipeline",
        nodes=[
            NodeDefinition(id="analyzer", type=NodeType.AGENT, config={}),
            NodeDefinition(id="builder_a", type=NodeType.AGENT, config={}),
            NodeDefinition(id="builder_b", type=NodeType.AGENT, config={}),
            NodeDefinition(id="merger", type=NodeType.MERGE, config={}),
        ],
        edges=[
            EdgeDefinition(source="analyzer", target="builder_a"),
            EdgeDefinition(source="analyzer", target="builder_b"),
            EdgeDefinition(source="builder_a", target="merger"),
            EdgeDefinition(source="builder_b", target="merger"),
        ],
        entry_nodes=["analyzer"],
        exit_nodes=["merger"],
    )


@pytest.fixture()
def gate_graph_def() -> GraphDefinition:
    """analyzer -> quality_gate(GATE) -> builder."""
    return GraphDefinition(
        name="gate-pipeline",
        nodes=[
            NodeDefinition(id="analyzer", type=NodeType.AGENT, config={}),
            NodeDefinition(
                id="quality_gate",
                type=NodeType.GATE,
                config={
                    "conditions": [
                        {
                            "key": "node_outputs.analyzer.status",
                            "operator": "eq",
                            "value": "executed",
                        }
                    ]
                },
            ),
            NodeDefinition(id="builder", type=NodeType.AGENT, config={}),
        ],
        edges=[
            EdgeDefinition(source="analyzer", target="quality_gate"),
            EdgeDefinition(source="quality_gate", target="builder"),
        ],
        entry_nodes=["analyzer"],
        exit_nodes=["builder"],
    )


# --------------- compiler tests ---------------


async def test_compile_returns_invocable(simple_graph_def: GraphDefinition) -> None:
    compiler = GraphCompiler()
    compiled = compiler.compile(simple_graph_def)
    assert hasattr(compiled, "ainvoke")


async def test_compile_node_count(simple_graph_def: GraphDefinition) -> None:
    compiler = GraphCompiler()
    compiled = compiler.compile(simple_graph_def)
    # LangGraph compiled graph has a .nodes dict (internal)
    # 3 user nodes + __start__ + __end__
    node_names = {n for n in compiled.get_graph().nodes}
    for expected in ("analyzer", "builder", "reviewer"):
        assert expected in node_names


async def test_compile_invalid_graph_raises() -> None:
    bad_def = GraphDefinition(
        name="bad",
        nodes=[NodeDefinition(id="a", type=NodeType.AGENT)],
        edges=[EdgeDefinition(source="a", target="missing")],
        entry_nodes=["a"],
        exit_nodes=["a"],
    )
    compiler = GraphCompiler()
    with pytest.raises(ValueError, match="Invalid graph"):
        compiler.compile(bad_def)


async def test_switch_routes_to_simple(switch_graph_def: GraphDefinition) -> None:
    """Route to simple_builder when analyzer outputs complexity=low."""

    async def analyzer_low(state: dict[str, Any]) -> dict[str, Any]:
        return {"node_outputs": {"analyzer": {"status": "executed", "type": "agent", "complexity": "low"}}}

    compiler = GraphCompiler(node_functions={"analyzer": analyzer_low})
    compiled = compiler.compile(switch_graph_def)
    state: dict[str, Any] = {
        "node_outputs": {},
        "execution_trace": [],
        "errors": [],
    }
    result = await compiled.ainvoke(state, {"configurable": {"thread_id": "test-1"}})
    assert "simple_builder" in result["node_outputs"]
    assert "complex_builder" not in result["node_outputs"]


async def test_switch_routes_to_complex(switch_graph_def: GraphDefinition) -> None:
    """Route to complex_builder when analyzer outputs complexity=high."""

    async def analyzer_high(state: dict[str, Any]) -> dict[str, Any]:
        return {"node_outputs": {"analyzer": {"status": "executed", "type": "agent", "complexity": "high"}}}

    compiler = GraphCompiler(node_functions={"analyzer": analyzer_high})
    compiled = compiler.compile(switch_graph_def)
    state: dict[str, Any] = {
        "node_outputs": {},
        "execution_trace": [],
        "errors": [],
    }
    result = await compiled.ainvoke(state, {"configurable": {"thread_id": "test-2"}})
    assert "complex_builder" in result["node_outputs"]
    assert "simple_builder" not in result["node_outputs"]


async def test_parallel_branches_execute(parallel_graph_def: GraphDefinition) -> None:
    compiler = GraphCompiler()
    compiled = compiler.compile(parallel_graph_def)
    state: dict[str, Any] = {
        "node_outputs": {},
        "execution_trace": [],
        "errors": [],
    }
    result = await compiled.ainvoke(state, {"configurable": {"thread_id": "test-3"}})
    assert "builder_a" in result["node_outputs"]
    assert "builder_b" in result["node_outputs"]


async def test_build_node_function_returns_dict(simple_graph_def: GraphDefinition) -> None:
    compiler = GraphCompiler()
    node_def = simple_graph_def.nodes[0]
    fn = compiler._build_node_function(node_def)
    result = await fn({"node_outputs": {}, "execution_trace": [], "errors": []})
    assert isinstance(result, dict)
    assert "node_outputs" in result


async def test_build_switch_router_returns_callable(switch_graph_def: GraphDefinition) -> None:
    compiler = GraphCompiler()
    switch_node = next(n for n in switch_graph_def.nodes if n.type == NodeType.SWITCH)
    cond_edges = [e for e in switch_graph_def.edges if e.source == switch_node.id and e.condition]
    router, path_map = compiler._build_switch_router(switch_node, cond_edges)
    assert callable(router)
    assert isinstance(path_map, dict)
    assert len(path_map) >= 2


async def test_gate_passes_when_conditions_met(gate_graph_def: GraphDefinition) -> None:
    """GATE passes when analyzer has already run and conditions are satisfied."""
    compiler = GraphCompiler()
    compiled = compiler.compile(gate_graph_def)
    state: dict[str, Any] = {
        "node_outputs": {},
        "execution_trace": [],
        "errors": [],
    }
    # analyzer stub will set node_outputs.analyzer.status = "executed"
    # gate should then check and pass
    result = await compiled.ainvoke(state, {"configurable": {"thread_id": "test-gate-pass"}})
    assert "quality_gate" in result["node_outputs"]
    assert result["node_outputs"]["quality_gate"]["status"] == "passed"
    assert "builder" in result["node_outputs"]


async def test_gate_raises_on_failed_condition() -> None:
    """GATE raises GateFailedError when condition is not met."""
    gate_def = GraphDefinition(
        name="gate-fail",
        nodes=[
            NodeDefinition(
                id="quality_gate",
                type=NodeType.GATE,
                config={
                    "conditions": [
                        {
                            "key": "node_outputs.analyzer.status",
                            "operator": "eq",
                            "value": "passed",
                        }
                    ]
                },
            ),
        ],
        edges=[],
        entry_nodes=["quality_gate"],
        exit_nodes=["quality_gate"],
    )
    compiler = GraphCompiler()
    compiled = compiler.compile(gate_def)
    state: dict[str, Any] = {
        "node_outputs": {},
        "execution_trace": [],
        "errors": [],
    }
    with pytest.raises(GateFailedError, match="quality_gate"):
        await compiled.ainvoke(state, {"configurable": {"thread_id": "test-gate-fail"}})


async def test_gate_error_includes_condition_details() -> None:
    """GateFailedError message includes the failed condition details."""
    compiler = GraphCompiler()
    node_def = NodeDefinition(
        id="my_gate",
        type=NodeType.GATE,
        config={
            "conditions": [
                {"key": "node_outputs.check.value", "operator": "eq", "value": "ready"}
            ]
        },
    )
    gate_fn = compiler._build_node_function(node_def)
    with pytest.raises(GateFailedError) as exc_info:
        await gate_fn({"node_outputs": {}, "execution_trace": [], "errors": []})
    assert "node_outputs.check.value" in str(exc_info.value)
    assert "eq" in str(exc_info.value)


async def test_compile_with_tracer(simple_graph_def: GraphDefinition) -> None:
    tracer = ExecutionTracer()
    compiler = GraphCompiler(tracer=tracer)
    compiled = compiler.compile(simple_graph_def)
    state: dict[str, Any] = {
        "node_outputs": {},
        "execution_trace": [],
        "errors": [],
    }
    await compiled.ainvoke(state, {"configurable": {"thread_id": "test-traced"}})
    assert len(tracer.records) == 3  # analyzer, builder, reviewer
    result = tracer.get_result("test-pipeline")
    assert result.success is True
