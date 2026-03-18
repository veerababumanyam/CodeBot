"""Tests for graph validator."""

from __future__ import annotations

from pathlib import Path

from graph_engine.engine.validator import GraphValidator, ValidationResult
from graph_engine.models.graph_def import GraphDefinition
from graph_engine.yaml.loader import load_graph_definition

FIXTURES = Path(__file__).parent / "fixtures"


def _make_graph(nodes_raw, edges_raw, entry, exit_) -> GraphDefinition:
    """Helper to build a GraphDefinition from raw dicts."""
    return GraphDefinition.model_validate(
        {
            "name": "test",
            "nodes": nodes_raw,
            "edges": edges_raw,
            "entry_nodes": entry,
            "exit_nodes": exit_,
        }
    )


class TestValidatorLinearGraph:
    """A -> B -> C linear graph."""

    def setup_method(self):
        self.gd = _make_graph(
            [
                {"id": "a", "type": "agent"},
                {"id": "b", "type": "agent"},
                {"id": "c", "type": "agent"},
            ],
            [
                {"source": "a", "target": "b"},
                {"source": "b", "target": "c"},
            ],
            ["a"],
            ["c"],
        )
        self.validator = GraphValidator()

    def test_valid(self):
        result = self.validator.validate(self.gd)
        assert result.is_valid is True
        assert result.errors == []

    def test_execution_layers(self):
        result = self.validator.validate(self.gd)
        assert result.execution_layers == [["a"], ["b"], ["c"]]


class TestValidatorDiamondGraph:
    """A -> B, A -> C, B -> D, C -> D."""

    def setup_method(self):
        self.gd = _make_graph(
            [
                {"id": "a", "type": "agent"},
                {"id": "b", "type": "agent"},
                {"id": "c", "type": "agent"},
                {"id": "d", "type": "agent"},
            ],
            [
                {"source": "a", "target": "b"},
                {"source": "a", "target": "c"},
                {"source": "b", "target": "d"},
                {"source": "c", "target": "d"},
            ],
            ["a"],
            ["d"],
        )
        self.validator = GraphValidator()

    def test_execution_layers(self):
        result = self.validator.validate(self.gd)
        assert result.is_valid is True
        # Layer 0: [a], Layer 1: [b, c] (order may vary), Layer 2: [d]
        assert len(result.execution_layers) == 3
        assert result.execution_layers[0] == ["a"]
        assert sorted(result.execution_layers[1]) == ["b", "c"]
        assert result.execution_layers[2] == ["d"]


class TestValidatorCycleDetection:
    def test_detects_cycle(self):
        gd = load_graph_definition(FIXTURES / "cyclic_graph.yaml")
        result = GraphValidator().validate(gd)
        assert result.is_valid is False
        assert any("cycle" in e.lower() for e in result.errors)


class TestValidatorMissingRefs:
    def test_detects_missing_edge_target(self):
        gd = load_graph_definition(FIXTURES / "invalid_refs.yaml")
        result = GraphValidator().validate(gd)
        assert result.is_valid is False
        assert any("not found" in e.lower() for e in result.errors)

    def test_detects_missing_edge_source(self):
        gd = _make_graph(
            [{"id": "a", "type": "agent"}],
            [{"source": "ghost", "target": "a"}],
            ["a"],
            ["a"],
        )
        result = GraphValidator().validate(gd)
        assert result.is_valid is False
        assert any("not found" in e.lower() for e in result.errors)

    def test_detects_entry_node_not_in_nodes(self):
        gd = _make_graph(
            [{"id": "a", "type": "agent"}],
            [],
            ["missing_entry"],
            ["a"],
        )
        result = GraphValidator().validate(gd)
        assert result.is_valid is False
        assert any("not found" in e.lower() for e in result.errors)

    def test_detects_exit_node_not_in_nodes(self):
        gd = _make_graph(
            [{"id": "a", "type": "agent"}],
            [],
            ["a"],
            ["missing_exit"],
        )
        result = GraphValidator().validate(gd)
        assert result.is_valid is False
        assert any("not found" in e.lower() for e in result.errors)


class TestValidatorLoopBackEdges:
    def test_excludes_loop_back_edges(self):
        """A LOOP node with a back-edge should not trigger cycle detection."""
        gd = _make_graph(
            [
                {"id": "start", "type": "agent"},
                {"id": "loop_node", "type": "loop", "config": {"max_iterations": 3}},
                {"id": "loop_body", "type": "agent"},
                {"id": "done", "type": "agent"},
            ],
            [
                {"source": "start", "target": "loop_node"},
                {"source": "loop_node", "target": "loop_body"},
                {"source": "loop_body", "target": "loop_node"},  # back-edge
                {"source": "loop_node", "target": "done"},
            ],
            ["start"],
            ["done"],
        )
        result = GraphValidator().validate(gd)
        assert result.is_valid is True


class TestValidatorNodeTypeWarnings:
    def test_warns_switch_no_conditional_edges(self):
        gd = _make_graph(
            [
                {"id": "a", "type": "agent"},
                {"id": "sw", "type": "switch"},
                {"id": "b", "type": "agent"},
            ],
            [
                {"source": "a", "target": "sw"},
                {"source": "sw", "target": "b"},  # no condition
            ],
            ["a"],
            ["b"],
        )
        result = GraphValidator().validate(gd)
        assert any("switch" in w.lower() for w in result.warnings)

    def test_warns_merge_fewer_than_2_incoming(self):
        gd = _make_graph(
            [
                {"id": "a", "type": "agent"},
                {"id": "m", "type": "merge"},
            ],
            [
                {"source": "a", "target": "m"},  # only 1 incoming
            ],
            ["a"],
            ["m"],
        )
        result = GraphValidator().validate(gd)
        assert any("merge" in w.lower() for w in result.warnings)


class TestValidatorParallelPipeline:
    def test_parallel_pipeline_valid(self):
        gd = load_graph_definition(FIXTURES / "parallel_pipeline.yaml")
        result = GraphValidator().validate(gd)
        assert result.is_valid is True
        assert len(result.execution_layers) == 3
