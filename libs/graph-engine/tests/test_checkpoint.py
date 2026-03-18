"""Tests for CheckpointManager with checkpoint/resume functionality."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from langgraph.checkpoint.memory import MemorySaver

from graph_engine.engine.checkpoint import (
    CheckpointManager,
    create_checkpointer,
    resume_from_checkpoint,
)
from graph_engine.engine.compiler import GraphCompiler
from graph_engine.models.graph_def import GraphDefinition


def _make_linear_graph_def() -> GraphDefinition:
    """Create a simple 3-node linear graph: A -> B -> C."""
    return GraphDefinition(
        name="checkpoint-test",
        version="1.0",
        nodes=[
            {"id": "node_a", "type": "agent", "config": {}},
            {"id": "node_b", "type": "agent", "config": {}},
            {"id": "node_c", "type": "agent", "config": {}},
        ],
        edges=[
            {"source": "node_a", "target": "node_b", "type": "state_flow"},
            {"source": "node_b", "target": "node_c", "type": "state_flow"},
        ],
        entry_nodes=["node_a"],
        exit_nodes=["node_c"],
    )


@pytest.fixture()
def checkpoint_manager() -> CheckpointManager:
    """Create a CheckpointManager with in-memory storage."""
    return CheckpointManager.from_memory()


class TestCheckpointManagerCreation:
    """Tests for CheckpointManager construction."""

    def test_checkpoint_manager_from_memory(self) -> None:
        mgr = CheckpointManager.from_memory()
        assert isinstance(mgr, CheckpointManager)
        assert isinstance(mgr.checkpointer, MemorySaver)

    @pytest.mark.asyncio
    async def test_setup_with_memory_saver_is_noop(
        self, checkpoint_manager: CheckpointManager
    ) -> None:
        # setup() should complete without error for MemorySaver
        await checkpoint_manager.setup()


class TestCompileWithCheckpointer:
    """Tests for compiling graphs with a checkpointer attached."""

    @pytest.mark.asyncio
    async def test_compile_with_checkpointer(
        self, checkpoint_manager: CheckpointManager
    ) -> None:
        graph_def = _make_linear_graph_def()
        compiler = GraphCompiler()
        compiled = compiler.compile(
            graph_def, checkpointer=checkpoint_manager.checkpointer
        )

        state = {"node_outputs": {}, "execution_trace": [], "errors": []}
        config = {"configurable": {"thread_id": "compile-test-1"}}
        result = await compiled.ainvoke(state, config)

        assert "node_a" in result["node_outputs"]
        assert "node_b" in result["node_outputs"]
        assert "node_c" in result["node_outputs"]


class TestCheckpointPersistence:
    """Tests for checkpoint persistence and retrieval."""

    @pytest.mark.asyncio
    async def test_checkpoint_persists_after_execution(
        self, checkpoint_manager: CheckpointManager
    ) -> None:
        graph_def = _make_linear_graph_def()
        compiler = GraphCompiler()
        compiled = compiler.compile(
            graph_def, checkpointer=checkpoint_manager.checkpointer
        )

        state = {"node_outputs": {}, "execution_trace": [], "errors": []}
        config = {"configurable": {"thread_id": "persist-test-1"}}
        await compiled.ainvoke(state, config)

        checkpoint_id = await checkpoint_manager.get_latest_checkpoint_id("persist-test-1")
        assert checkpoint_id is not None
        assert isinstance(checkpoint_id, str)

    @pytest.mark.asyncio
    async def test_get_latest_checkpoint_id_no_thread(
        self, checkpoint_manager: CheckpointManager
    ) -> None:
        result = await checkpoint_manager.get_latest_checkpoint_id("nonexistent-thread")
        assert result is None


class TestCheckpointResume:
    """Tests for resuming execution from checkpoints."""

    @pytest.mark.asyncio
    async def test_resume_from_checkpoint(
        self, checkpoint_manager: CheckpointManager
    ) -> None:
        """Test that interrupted execution can be resumed from checkpoint.

        Uses a node_c function that raises on first call and succeeds on retry.
        First invoke fails at node_c, resume skips A and B, retries C successfully.
        """
        call_count = {"c": 0}

        async def failing_node_c(state: dict[str, Any]) -> dict[str, Any]:
            call_count["c"] += 1
            if call_count["c"] == 1:
                msg = "Simulated failure on first attempt"
                raise RuntimeError(msg)
            return {"node_outputs": {"node_c": {"status": "executed", "type": "agent"}}}

        graph_def = _make_linear_graph_def()
        compiler = GraphCompiler(node_functions={"node_c": failing_node_c})
        compiled = compiler.compile(
            graph_def, checkpointer=checkpoint_manager.checkpointer
        )

        state = {"node_outputs": {}, "execution_trace": [], "errors": []}
        thread_id = "resume-test-1"
        config = {"configurable": {"thread_id": thread_id}}

        # First invoke: should fail at node_c
        with pytest.raises(RuntimeError, match="Simulated failure"):
            await compiled.ainvoke(state, config)

        # Verify checkpoint exists (A and B completed)
        checkpoint_id = await checkpoint_manager.get_latest_checkpoint_id(thread_id)
        assert checkpoint_id is not None

        # Resume: node_c should succeed on second call
        result = await resume_from_checkpoint(compiled, thread_id)

        assert "node_a" in result["node_outputs"]
        assert "node_b" in result["node_outputs"]
        assert "node_c" in result["node_outputs"]

    @pytest.mark.asyncio
    async def test_checkpoint_resume_matches_full_run(
        self, checkpoint_manager: CheckpointManager
    ) -> None:
        """Full run and checkpoint-resume should produce the same node_outputs keys."""
        graph_def = _make_linear_graph_def()

        # Full uninterrupted run (no checkpointer)
        compiler_1 = GraphCompiler()
        compiled_1 = compiler_1.compile(graph_def)
        state_1 = {"node_outputs": {}, "execution_trace": [], "errors": []}
        result_1 = await compiled_1.ainvoke(
            state_1, {"configurable": {"thread_id": "full-run"}}
        )
        full_keys = set(result_1["node_outputs"].keys())

        # Run with checkpointing
        compiler_2 = GraphCompiler()
        compiled_2 = compiler_2.compile(
            graph_def, checkpointer=checkpoint_manager.checkpointer
        )
        state_2 = {"node_outputs": {}, "execution_trace": [], "errors": []}
        thread_id = "checkpoint-run"
        result_2 = await compiled_2.ainvoke(
            state_2, {"configurable": {"thread_id": thread_id}}
        )
        checkpoint_keys = set(result_2["node_outputs"].keys())

        assert full_keys == checkpoint_keys
        assert full_keys == {"node_a", "node_b", "node_c"}
