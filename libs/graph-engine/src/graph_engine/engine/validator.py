"""Graph validation with Kahn's algorithm for cycle detection and layer computation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from graph_engine.models.graph_def import GraphDefinition  # noqa: TC001
from graph_engine.models.node_types import NodeType


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of graph validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    execution_layers: list[list[str]] = field(default_factory=list)


class GraphValidator:
    """Validates a GraphDefinition for structural correctness."""

    def validate(self, graph_def: GraphDefinition) -> ValidationResult:
        """Validate the graph and compute execution layers.

        Checks:
            1. All edge endpoints reference existing nodes.
            2. Entry/exit nodes exist in the node set.
            3. No cycles (excluding LOOP back-edges) via Kahn's algorithm.
            4. Node-type-specific warnings (SWITCH, MERGE).

        Returns:
            ValidationResult with errors, warnings, and execution layers.
        """
        errors: list[str] = []
        warnings: list[str] = []

        node_ids = {n.id for n in graph_def.nodes}

        # 1. Check edge endpoints
        for edge in graph_def.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge source '{edge.source}' not found in nodes")
            if edge.target not in node_ids:
                errors.append(f"Edge target '{edge.target}' not found in nodes")

        # 2. Check entry/exit nodes
        for entry in graph_def.entry_nodes:
            if entry not in node_ids:
                errors.append(f"Entry node '{entry}' not found in nodes")
        for exit_node in graph_def.exit_nodes:
            if exit_node not in node_ids:
                errors.append(f"Exit node '{exit_node}' not found in nodes")

        # 3. Cycle detection and topological sort
        layers = self._topological_sort(graph_def, errors)

        # 4. Node-type-specific validation
        self._validate_node_types(graph_def, errors, warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            execution_layers=layers,
        )

    def _identify_loop_back_edges(
        self, graph_def: GraphDefinition
    ) -> set[tuple[str, str]]:
        """Identify edges that are LOOP back-edges (target is a LOOP node
        and edge goes from a downstream node back to the LOOP node)."""
        loop_node_ids = {
            n.id for n in graph_def.nodes if n.type == NodeType.LOOP
        }
        back_edges: set[tuple[str, str]] = set()

        for edge in graph_def.edges:
            if (
                edge.target in loop_node_ids
                and edge.source != edge.target
                and self._is_descendant(graph_def, edge.target, edge.source, loop_node_ids)
            ):
                back_edges.add((edge.source, edge.target))

        return back_edges

    def _is_descendant(
        self,
        graph_def: GraphDefinition,
        ancestor: str,
        candidate: str,
        loop_node_ids: set[str],
    ) -> bool:
        """Check if candidate is reachable from ancestor via forward edges only."""
        visited: set[str] = set()
        queue = deque([ancestor])

        while queue:
            current = queue.popleft()
            if current == candidate:
                return True
            if current in visited:
                continue
            visited.add(current)
            for edge in graph_def.edges:
                if (
                    edge.source == current
                    and edge.target not in visited
                    and (edge.target not in loop_node_ids or edge.target == candidate)
                ):
                    queue.append(edge.target)

        return False

    def _topological_sort(
        self, graph_def: GraphDefinition, errors: list[str]
    ) -> list[list[str]]:
        """Kahn's algorithm returning execution layers (parallel groups)."""
        loop_back_edges = self._identify_loop_back_edges(graph_def)

        in_degree: dict[str, int] = {}
        adjacency: dict[str, list[str]] = defaultdict(list)
        node_ids = {n.id for n in graph_def.nodes}

        for nid in node_ids:
            in_degree[nid] = 0

        for edge in graph_def.edges:
            if (edge.source, edge.target) in loop_back_edges:
                continue
            if edge.source in node_ids and edge.target in node_ids:
                adjacency[edge.source].append(edge.target)
                in_degree[edge.target] += 1

        queue = deque(sorted(nid for nid in node_ids if in_degree[nid] == 0))
        layers: list[list[str]] = []
        visited = 0

        while queue:
            layer = list(queue)
            layers.append(layer)
            next_queue: deque[str] = deque()
            for nid in layer:
                visited += 1
                for neighbor in adjacency[nid]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_queue.append(neighbor)
            queue = next_queue

        if visited != len(node_ids):
            errors.append(
                "Graph contains a cycle (excluding declared loop back-edges)"
            )

        return layers

    def _validate_node_types(
        self,
        graph_def: GraphDefinition,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Node-type-specific validation rules."""
        for node in graph_def.nodes:
            if node.type == NodeType.SWITCH:
                # SWITCH should have at least one outgoing edge with a condition
                outgoing = [e for e in graph_def.edges if e.source == node.id]
                has_conditional = any(e.condition is not None for e in outgoing)
                if not has_conditional:
                    warnings.append(
                        f"SWITCH node '{node.id}' has no conditional outgoing edges"
                    )

            if node.type == NodeType.MERGE:
                # MERGE should have at least 2 incoming edges
                incoming = [e for e in graph_def.edges if e.target == node.id]
                if len(incoming) < 2:
                    warnings.append(
                        f"MERGE node '{node.id}' has fewer than 2 incoming edges "
                        f"({len(incoming)} found)"
                    )
