"""Tests for graph-engine domain models."""

from __future__ import annotations

import time

import pytest
from pydantic import ValidationError

from graph_engine.models.node_types import NodeDefinition, NodeType, RetryPolicy
from graph_engine.models.edge_types import EdgeDefinition, EdgeType
from graph_engine.models.graph_def import GraphDefinition
from graph_engine.models.state import SharedState, merge_dicts
from graph_engine.models.execution import ExecutionRecord, GraphResult


# --- NodeType ---


class TestNodeType:
    def test_has_exactly_10_members(self):
        assert len(NodeType) == 10

    def test_values_are_lowercase(self):
        assert NodeType.AGENT == "agent"
        assert NodeType.SUBGRAPH == "subgraph"
        assert NodeType.LOOP == "loop"
        assert NodeType.SWITCH == "switch"
        assert NodeType.HUMAN_IN_LOOP == "human"
        assert NodeType.PARALLEL == "parallel"
        assert NodeType.MERGE == "merge"
        assert NodeType.CHECKPOINT == "checkpoint"
        assert NodeType.TRANSFORM == "transform"
        assert NodeType.GATE == "gate"


# --- EdgeType ---


class TestEdgeType:
    def test_has_exactly_3_members(self):
        assert len(EdgeType) == 3

    def test_values(self):
        assert EdgeType.STATE_FLOW == "state_flow"
        assert EdgeType.MESSAGE_FLOW == "message_flow"
        assert EdgeType.CONTROL_FLOW == "control_flow"


# --- NodeDefinition ---


class TestNodeDefinition:
    def test_validates_id_as_identifier(self):
        with pytest.raises(ValidationError, match="identifier"):
            NodeDefinition(id="my node", type=NodeType.AGENT)

    def test_accepts_valid_identifier(self):
        node = NodeDefinition(id="my_node", type=NodeType.AGENT)
        assert node.id == "my_node"

    def test_enforces_positive_timeout(self):
        with pytest.raises(ValidationError, match="timeout"):
            NodeDefinition(id="n", type=NodeType.AGENT, timeout_seconds=0)

    def test_frozen(self):
        node = NodeDefinition(id="n", type=NodeType.AGENT)
        with pytest.raises(ValidationError):
            node.id = "other"

    def test_defaults(self):
        node = NodeDefinition(id="n", type=NodeType.AGENT)
        assert node.timeout_seconds == 600
        assert node.config == {}
        assert node.retry_policy == RetryPolicy()


# --- EdgeDefinition ---


class TestEdgeDefinition:
    def test_condition_default_none(self):
        edge = EdgeDefinition(source="a", target="b")
        assert edge.condition is None

    def test_accepts_condition(self):
        edge = EdgeDefinition(source="a", target="b", condition="x > 1")
        assert edge.condition == "x > 1"

    def test_default_type_is_state_flow(self):
        edge = EdgeDefinition(source="a", target="b")
        assert edge.type == EdgeType.STATE_FLOW


# --- RetryPolicy ---


class TestRetryPolicy:
    def test_defaults(self):
        rp = RetryPolicy()
        assert rp.max_retries == 3
        assert rp.backoff_factor == 2.0
        assert rp.retry_on == ["TimeoutError", "RateLimitError"]


# --- GraphDefinition ---


class TestGraphDefinition:
    def test_requires_non_empty_nodes(self):
        with pytest.raises(ValidationError):
            GraphDefinition(
                name="t", nodes=[], edges=[], entry_nodes=["a"], exit_nodes=["b"]
            )

    def test_requires_non_empty_entry_nodes(self):
        with pytest.raises(ValidationError):
            GraphDefinition(
                name="t",
                nodes=[{"id": "a", "type": "agent"}],
                edges=[],
                entry_nodes=[],
                exit_nodes=["a"],
            )

    def test_model_validate_from_dict(self, sample_graph_def):
        gd = GraphDefinition.model_validate(sample_graph_def)
        assert gd.name == "test-pipeline"
        assert len(gd.nodes) == 3
        assert len(gd.edges) == 2
        assert gd.entry_nodes == ["analyzer"]
        assert gd.exit_nodes == ["reviewer"]


# --- SharedState ---


class TestSharedState:
    def test_merge_dicts_preserves_all_keys(self):
        a = {"x": 1, "y": 2}
        b = {"y": 3, "z": 4}
        result = merge_dicts(a, b)
        assert result == {"x": 1, "y": 3, "z": 4}

    def test_list_reducer_concatenates(self):
        from operator import add

        a = [{"node": "a"}]
        b = [{"node": "b"}]
        result = add(a, b)
        assert result == [{"node": "a"}, {"node": "b"}]

    def test_shared_state_annotations(self):
        """SharedState has the expected annotated keys."""
        hints = SharedState.__annotations__
        assert "node_outputs" in hints
        assert "execution_trace" in hints
        assert "errors" in hints


# --- ExecutionRecord ---


class TestExecutionRecord:
    def test_has_all_fields(self):
        rec = ExecutionRecord(node_id="n1", started_at=time.monotonic())
        assert rec.node_id == "n1"
        assert rec.completed_at == 0.0
        assert rec.duration_ms == 0
        assert rec.input_tokens == 0
        assert rec.output_tokens == 0
        assert rec.total_tokens == 0
        assert rec.cost_usd == 0.0
        assert rec.error is None

    def test_slots_and_kw_only(self):
        assert ExecutionRecord.__dataclass_params__.slots is True
        assert ExecutionRecord.__dataclass_params__.kw_only is True


# --- GraphResult ---


class TestGraphResult:
    def test_has_all_fields(self):
        gr = GraphResult(graph_name="g", started_at=time.monotonic())
        assert gr.graph_name == "g"
        assert gr.completed_at == 0.0
        assert gr.records == []
        assert gr.total_duration_ms == 0
        assert gr.total_tokens == 0
        assert gr.total_cost_usd == 0.0
        assert gr.success is False
