"""GraphCompiler: translates GraphDefinition to LangGraph StateGraph."""

from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph  # noqa: TC002

from graph_engine.engine.fanout import FanOutConfig, build_fanout_node
from graph_engine.engine.validator import GraphValidator
from graph_engine.models.edge_types import EdgeDefinition  # noqa: TC001
from graph_engine.models.graph_def import GraphDefinition  # noqa: TC001
from graph_engine.models.node_types import NodeDefinition, NodeType
from graph_engine.models.state import SharedState
from graph_engine.tracing.tracer import ExecutionTracer  # noqa: TC001


class GateFailedError(Exception):
    """Raised when a GATE node's conditions are not met."""


class GraphCompiler:
    """Compiles a validated GraphDefinition into a LangGraph StateGraph."""

    def __init__(
        self,
        tracer: ExecutionTracer | None = None,
        node_functions: dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        self.tracer = tracer
        self.node_functions = node_functions or {}

    def compile(
        self,
        graph_def: GraphDefinition,
        checkpointer: Any = None,
        validate: bool = True,
    ) -> CompiledStateGraph:
        """Compile a GraphDefinition into a runnable LangGraph StateGraph.

        Args:
            graph_def: The validated graph definition.
            checkpointer: Optional LangGraph checkpointer for persistence.
            validate: Whether to run validation before compilation.

        Returns:
            A compiled LangGraph StateGraph ready for execution.

        Raises:
            ValueError: If validation fails.
        """
        if validate:
            result = GraphValidator().validate(graph_def)
            if not result.is_valid:
                msg = f"Invalid graph: {result.errors}"
                raise ValueError(msg)

        builder = StateGraph(SharedState)

        # Identify SWITCH nodes for conditional edge handling
        switch_ids = {n.id for n in graph_def.nodes if n.type == NodeType.SWITCH}

        # Identify fan-out nodes
        fanout_ids = {n.id for n in graph_def.nodes if "fanout" in n.config}

        # Add nodes
        for node in graph_def.nodes:
            node_fn = self._build_node_function(node)
            if self.tracer:
                node_fn = self.tracer.wrap_node(node.id, node_fn)
            builder.add_node(node.id, node_fn)

        # Build SWITCH conditional edges with path_map for LangGraph
        for switch_id in switch_ids:
            switch_node = next(n for n in graph_def.nodes if n.id == switch_id)
            cond_edges = [
                e for e in graph_def.edges if e.source == switch_id and e.condition
            ]
            router_fn, path_map = self._build_switch_router(switch_node, cond_edges)
            builder.add_conditional_edges(switch_id, router_fn, path_map)

        # Build fan-out conditional edges via Send API
        for fanout_id in fanout_ids:
            fanout_node = next(n for n in graph_def.nodes if n.id == fanout_id)
            fanout_cfg = fanout_node.config["fanout"]
            fo_config = FanOutConfig(
                source_node=fanout_id,
                worker_node=fanout_cfg["worker_node"],
                task_key=fanout_cfg["task_key"],
            )
            # Find fallback targets (non-worker edges from this fanout node)
            fallback_targets = [
                e.target
                for e in graph_def.edges
                if e.source == fanout_id and e.target != fo_config.worker_node
            ]
            dispatch_fn = build_fanout_node(fo_config)

            if fallback_targets:
                # Wrap dispatch to handle empty sends -> route to fallback
                fallback_target = fallback_targets[0]

                def _make_dispatch_with_fallback(
                    _dispatch: Any = dispatch_fn,
                    _fallback: str = fallback_target,
                    _worker: str = fo_config.worker_node,
                ) -> Any:
                    def dispatch_or_fallback(state: dict[str, Any]) -> Any:
                        sends = _dispatch(state)
                        if sends:
                            return sends
                        return _fallback

                    return dispatch_or_fallback

                builder.add_conditional_edges(
                    fanout_id,
                    _make_dispatch_with_fallback(),
                    {fallback_target: fallback_target},
                )
            else:
                builder.add_conditional_edges(fanout_id, dispatch_fn)

        # Add non-conditional edges (skip edges from SWITCH and fan-out nodes)
        skip_sources = switch_ids | fanout_ids
        for edge in graph_def.edges:
            if edge.source in skip_sources and edge.condition:
                continue
            if edge.source in fanout_ids:
                continue
            if edge.source not in switch_ids:
                builder.add_edge(edge.source, edge.target)

        # Wire entry/exit
        for entry_node in graph_def.entry_nodes:
            builder.add_edge(START, entry_node)
        for exit_node in graph_def.exit_nodes:
            builder.add_edge(exit_node, END)

        return builder.compile(checkpointer=checkpointer)

    def _build_node_function(
        self, node_def: NodeDefinition
    ) -> Callable[..., Any]:
        """Build an async node function for the given node type."""
        # Check for custom node functions first
        if node_def.id in self.node_functions:
            return self.node_functions[node_def.id]

        if node_def.type == NodeType.SWITCH:
            return self._build_switch_node(node_def)
        if node_def.type == NodeType.GATE:
            return self._build_gate_node(node_def)
        if node_def.type == NodeType.TRANSFORM:
            return self._build_transform_node(node_def)
        if node_def.type == NodeType.MERGE:
            return self._build_merge_node(node_def)
        return self._build_stub_node(node_def)

    def _build_switch_node(self, node_def: NodeDefinition) -> Callable[..., Any]:
        """SWITCH node: evaluate case conditions and store the matched route."""
        cases = node_def.config.get("cases", {})
        default_case = node_def.config.get("default")

        # Parse case conditions: "state.key == 'value'" -> (key_path, value)
        case_conditions: list[tuple[str, str, str]] = []
        for case_name, condition_str in cases.items():
            parts = condition_str.replace("state.", "").split("==")
            if len(parts) == 2:
                key_path = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                case_conditions.append((case_name, key_path, value))

        async def switch_fn(state: dict[str, Any]) -> dict[str, Any]:
            matched_route = default_case
            for case_name, key_path, expected_value in case_conditions:
                actual = _resolve_key_path(state, key_path)
                if actual == expected_value:
                    matched_route = case_name
                    break
            return {
                "node_outputs": {
                    node_def.id: {
                        "type": "switch",
                        "evaluated": True,
                        "route": matched_route,
                    }
                }
            }

        return switch_fn

    def _build_gate_node(self, node_def: NodeDefinition) -> Callable[..., Any]:
        """GATE node: evaluate conditions against state, raise on failure."""
        conditions = node_def.config.get("conditions", [])

        async def gate_fn(state: dict[str, Any]) -> dict[str, Any]:
            for condition in conditions:
                key_path = condition["key"]
                operator = condition["operator"]
                expected = condition.get("value")
                actual = _resolve_key_path(state, key_path)

                if not _evaluate_condition(actual, operator, expected):
                    msg = (
                        f"Gate '{node_def.id}' failed: condition on '{key_path}' "
                        f"not met (expected {operator} {expected!r}, got {actual!r})"
                    )
                    raise GateFailedError(msg)

            return {
                "node_outputs": {
                    node_def.id: {
                        "type": "gate",
                        "status": "passed",
                        "conditions_checked": len(conditions),
                    }
                }
            }

        return gate_fn

    def _build_transform_node(self, node_def: NodeDefinition) -> Callable[..., Any]:
        """TRANSFORM node: identity pass-through (real transforms in Phase 3)."""

        async def transform_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "node_outputs": {
                    node_def.id: {"type": "transform", "status": "executed"}
                }
            }

        return transform_fn

    def _build_merge_node(self, node_def: NodeDefinition) -> Callable[..., Any]:
        """MERGE node: collect upstream outputs into a combined dict."""

        async def merge_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "node_outputs": {
                    node_def.id: {
                        "type": "merge",
                        "status": "executed",
                        "merged_keys": list(state.get("node_outputs", {}).keys()),
                    }
                }
            }

        return merge_fn

    def _build_stub_node(self, node_def: NodeDefinition) -> Callable[..., Any]:
        """Stub for AGENT, SUBGRAPH, etc. -- replaced by real implementations later."""

        async def stub_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "node_outputs": {
                    node_def.id: {"status": "executed", "type": node_def.type.value}
                }
            }

        return stub_fn

    def _build_switch_router(
        self, switch_node: NodeDefinition, edges: list[EdgeDefinition]
    ) -> tuple[Callable[..., Any], dict[str, str]]:
        """Build a routing function and path_map for SWITCH node conditional edges.

        Returns:
            Tuple of (router_function, path_map) where path_map maps
            return values to target node IDs for LangGraph.
        """
        cases = switch_node.config.get("cases", {})
        default_case = switch_node.config.get("default")

        # Map case_name -> target_node_id from edge conditions
        case_to_target: dict[str, str] = {}
        for edge in edges:
            if edge.condition:
                # Parse condition like "case == 'simple'" -> extract case name
                for case_name in cases:
                    if case_name in (edge.condition or ""):
                        case_to_target[case_name] = edge.target
                        break

        # Parse case conditions: "state.key == 'value'" -> (key, value)
        case_conditions: dict[str, tuple[str, str]] = {}
        for case_name, condition_str in cases.items():
            parts = condition_str.replace("state.", "").split("==")
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip().strip("'\"")
                case_conditions[case_name] = (key, value)

        default_target = case_to_target.get(default_case, "") if default_case else ""

        # Build path_map: router return values -> target node ids
        path_map: dict[str, str] = dict(case_to_target)

        def router(state: dict[str, Any]) -> str:
            # Check for explicit route hint from the switch node output
            switch_output = state.get("node_outputs", {}).get(switch_node.id, {})
            if "route" in switch_output:
                route = switch_output["route"]
                if route in case_to_target:
                    return route

            # Evaluate case conditions against state
            for case_name, (key, value) in case_conditions.items():
                if case_name in case_to_target:
                    actual = state.get(key)
                    if actual == value:
                        return case_name

            return default_case or next(iter(case_to_target), default_target)

        return router, path_map


def _resolve_key_path(state: dict[str, Any], key_path: str) -> Any:
    """Resolve a dot-separated key path against a nested dict.

    E.g. "node_outputs.analyzer.status" resolves to
    state["node_outputs"]["analyzer"]["status"].
    """
    parts = key_path.split(".")
    current: Any = state
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _evaluate_condition(actual: Any, operator: str, expected: Any) -> bool:
    """Evaluate a single gate condition."""
    if operator == "exists":
        return actual is not None
    if operator == "eq":
        return actual == expected
    if operator == "neq":
        return actual != expected
    if operator == "in":
        return actual in (expected or [])
    return False
