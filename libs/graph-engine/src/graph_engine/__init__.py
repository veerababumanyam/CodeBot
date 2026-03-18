"""Graph execution engine for CodeBot multi-agent pipelines."""

from __future__ import annotations

from graph_engine.engine.compiler import GateFailedError, GraphCompiler
from graph_engine.engine.executor import ExecutionEngine
from graph_engine.engine.validator import GraphValidator, ValidationResult
from graph_engine.models.edge_types import EdgeDefinition, EdgeType
from graph_engine.models.execution import ExecutionRecord, GraphResult
from graph_engine.models.graph_def import GraphDefinition
from graph_engine.models.node_types import NodeDefinition, NodeType, RetryPolicy
from graph_engine.models.state import SharedState, merge_dicts
from graph_engine.tracing.tracer import ExecutionTracer
from graph_engine.yaml.loader import load_graph_definition, load_graph_definition_from_string

__version__ = "0.1.0"

__all__ = [
    "EdgeDefinition",
    "EdgeType",
    "ExecutionEngine",
    "ExecutionRecord",
    "ExecutionTracer",
    "GateFailedError",
    "GraphCompiler",
    "GraphDefinition",
    "GraphResult",
    "GraphValidator",
    "NodeDefinition",
    "NodeType",
    "RetryPolicy",
    "SharedState",
    "ValidationResult",
    "load_graph_definition",
    "load_graph_definition_from_string",
    "merge_dicts",
]
