"""ExecutionEngine: runs compiled graphs and collects results."""

from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
from typing import Any

from graph_engine.engine.compiler import GraphCompiler
from graph_engine.models.execution import GraphResult  # noqa: TC001
from graph_engine.models.graph_def import GraphDefinition  # noqa: TC001
from graph_engine.tracing.tracer import ExecutionTracer
from graph_engine.yaml.loader import load_graph_definition


class ExecutionEngine:
    """Orchestrates graph execution: compile, run, and collect results."""

    def __init__(
        self,
        node_functions: dict[str, Callable[..., Any]] | None = None,
    ) -> None:
        self.node_functions = node_functions or {}

    async def execute(
        self,
        graph_def: GraphDefinition,
        initial_state: dict[str, Any] | None = None,
        checkpointer: Any = None,
        thread_id: str | None = None,
    ) -> GraphResult:
        """Execute a graph definition and return aggregated results.

        Args:
            graph_def: The graph definition to execute.
            initial_state: Optional initial state values.
            checkpointer: Optional LangGraph checkpointer for persistence.
            thread_id: Optional thread ID for checkpointing.

        Returns:
            GraphResult with ExecutionRecords for each node.
        """
        tracer = ExecutionTracer()
        compiler = GraphCompiler(tracer=tracer, node_functions=self.node_functions)
        compiled = compiler.compile(graph_def, checkpointer=checkpointer)

        state: dict[str, Any] = {
            "node_outputs": {},
            "execution_trace": [],
            "errors": [],
            **(initial_state or {}),
        }
        config = {"configurable": {"thread_id": thread_id or graph_def.name}}

        await compiled.ainvoke(state, config)

        return tracer.get_result(graph_def.name)

    async def execute_from_yaml(
        self,
        yaml_path: str,
        initial_state: dict[str, Any] | None = None,
        checkpointer: Any = None,
    ) -> GraphResult:
        """Load a YAML graph definition and execute it.

        Args:
            yaml_path: Path to the YAML graph definition file.
            initial_state: Optional initial state values.
            checkpointer: Optional LangGraph checkpointer for persistence.

        Returns:
            GraphResult with ExecutionRecords for each node.
        """
        graph_def = load_graph_definition(yaml_path)
        return await self.execute(graph_def, initial_state, checkpointer)
