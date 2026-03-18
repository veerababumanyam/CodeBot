"""Tests for dynamic fan-out via LangGraph Send API with compiler integration."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

import pytest
from langgraph.types import Send

from graph_engine.engine.compiler import GraphCompiler
from graph_engine.engine.executor import ExecutionEngine
from graph_engine.engine.fanout import FanOutConfig, build_fanout_node
from graph_engine.models.graph_def import GraphDefinition
from graph_engine.yaml.loader import load_graph_definition


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestFanOutConfig:
    """Tests for FanOutConfig validation."""

    def test_create_valid_config(self) -> None:
        config = FanOutConfig(
            source_node="planner",
            worker_node="agent_worker",
            task_key="pending_tasks",
        )
        assert config.source_node == "planner"
        assert config.worker_node == "agent_worker"
        assert config.task_key == "pending_tasks"

    def test_task_key_must_be_nonempty(self) -> None:
        with pytest.raises(ValueError, match="task_key must be a non-empty string"):
            FanOutConfig(
                source_node="planner",
                worker_node="agent_worker",
                task_key="   ",
            )

    def test_config_is_frozen(self) -> None:
        config = FanOutConfig(
            source_node="planner",
            worker_node="agent_worker",
            task_key="pending_tasks",
        )
        with pytest.raises(Exception):
            config.task_key = "other"  # type: ignore[misc]


class TestBuildFanoutNode:
    """Tests for the build_fanout_node dispatch function."""

    def test_returns_callable(self) -> None:
        config = FanOutConfig(
            source_node="planner",
            worker_node="agent_worker",
            task_key="pending_tasks",
        )
        dispatch_fn = build_fanout_node(config)
        assert callable(dispatch_fn)

    def test_dispatch_with_three_tasks(self) -> None:
        config = FanOutConfig(
            source_node="planner",
            worker_node="agent_worker",
            task_key="pending_tasks",
        )
        dispatch_fn = build_fanout_node(config)

        state = {
            "pending_tasks": [
                {"id": "task-1", "description": "Build auth"},
                {"id": "task-2", "description": "Build API"},
                {"id": "task-3", "description": "Build UI"},
            ],
            "node_outputs": {},
        }
        sends = dispatch_fn(state)

        assert len(sends) == 3
        assert all(isinstance(s, Send) for s in sends)

    def test_dispatch_targets_worker_node(self) -> None:
        config = FanOutConfig(
            source_node="planner",
            worker_node="agent_worker",
            task_key="pending_tasks",
        )
        dispatch_fn = build_fanout_node(config)

        state = {
            "pending_tasks": [{"id": "task-1", "description": "Build auth"}],
            "node_outputs": {},
        }
        sends = dispatch_fn(state)

        assert sends[0].node == "agent_worker"

    def test_dispatch_payload_has_task_and_task_id(self) -> None:
        config = FanOutConfig(
            source_node="planner",
            worker_node="agent_worker",
            task_key="pending_tasks",
        )
        dispatch_fn = build_fanout_node(config)

        state = {
            "pending_tasks": [{"id": "task-42", "description": "Build feature"}],
            "node_outputs": {},
        }
        sends = dispatch_fn(state)

        assert sends[0].arg["task"] == {"id": "task-42", "description": "Build feature"}
        assert sends[0].arg["task_id"] == "task-42"

    def test_dispatch_empty_tasks_returns_empty_list(self) -> None:
        config = FanOutConfig(
            source_node="planner",
            worker_node="agent_worker",
            task_key="pending_tasks",
        )
        dispatch_fn = build_fanout_node(config)

        state = {"pending_tasks": [], "node_outputs": {}}
        sends = dispatch_fn(state)

        assert sends == []

    def test_dispatch_uses_index_when_no_id(self) -> None:
        config = FanOutConfig(
            source_node="planner",
            worker_node="agent_worker",
            task_key="pending_tasks",
        )
        dispatch_fn = build_fanout_node(config)

        state = {
            "pending_tasks": [{"description": "no id field"}],
            "node_outputs": {},
        }
        sends = dispatch_fn(state)

        assert sends[0].arg["task_id"] == "0"


class TestFanOutCompilerIntegration:
    """Tests for fan-out integrated with GraphCompiler."""

    @pytest.mark.asyncio
    async def test_yaml_fanout_compiles_without_error(self) -> None:
        yaml_path = str(FIXTURES_DIR / "fanout_pipeline.yaml")
        graph_def = load_graph_definition(yaml_path)

        compiler = GraphCompiler()
        # Should not raise
        compiled = compiler.compile(graph_def)
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_fanout_execution_with_three_tasks(self) -> None:
        """Planner produces 3 tasks, fan-out dispatches 3 workers, merger collects."""
        yaml_path = str(FIXTURES_DIR / "fanout_pipeline.yaml")
        graph_def = load_graph_definition(yaml_path)

        async def planner_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "node_outputs": {
                    "planner": {
                        "status": "executed",
                        "type": "agent",
                        "tasks_dispatched": 3,
                    }
                },
                "pending_tasks": [
                    {"id": "t1", "description": "Auth module"},
                    {"id": "t2", "description": "API module"},
                    {"id": "t3", "description": "UI module"},
                ],
            }

        async def worker_fn(state: dict[str, Any]) -> dict[str, Any]:
            task_id = state.get("task_id", "unknown")
            await asyncio.sleep(0.01)  # Simulate work
            return {
                "node_outputs": {
                    f"agent_worker_{task_id}": {
                        "status": "executed",
                        "type": "agent",
                        "task_id": task_id,
                    }
                }
            }

        async def merger_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "node_outputs": {
                    "merger": {
                        "type": "merge",
                        "status": "executed",
                        "merged_keys": list(state.get("node_outputs", {}).keys()),
                    }
                }
            }

        engine = ExecutionEngine(
            node_functions={
                "planner": planner_fn,
                "agent_worker": worker_fn,
                "merger": merger_fn,
            }
        )
        result = await engine.execute(graph_def)

        assert result.success
        # Should have planner + 3 workers + merger = 5 records
        node_ids = [r.node_id for r in result.records]
        assert "planner" in node_ids
        assert "merger" in node_ids
        # Workers should have executed (at least 3 worker records)
        worker_records = [r for r in result.records if r.node_id == "agent_worker"]
        assert len(worker_records) >= 3

    @pytest.mark.asyncio
    async def test_fanout_zero_tasks_completes(self) -> None:
        """Planner produces 0 tasks -- graph should still complete via fallback edge."""
        yaml_path = str(FIXTURES_DIR / "fanout_pipeline.yaml")
        graph_def = load_graph_definition(yaml_path)

        async def planner_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "node_outputs": {
                    "planner": {"status": "executed", "type": "agent"}
                },
                "pending_tasks": [],
            }

        async def worker_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "node_outputs": {
                    "agent_worker": {"status": "executed", "type": "agent"}
                }
            }

        async def merger_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "node_outputs": {
                    "merger": {
                        "type": "merge",
                        "status": "executed",
                        "merged_keys": list(state.get("node_outputs", {}).keys()),
                    }
                }
            }

        engine = ExecutionEngine(
            node_functions={
                "planner": planner_fn,
                "agent_worker": worker_fn,
                "merger": merger_fn,
            }
        )
        result = await engine.execute(graph_def)
        assert result.success

    @pytest.mark.asyncio
    async def test_execute_from_yaml_end_to_end(self) -> None:
        """Full end-to-end: load YAML, compile, execute with dynamic fan-out."""
        yaml_path = str(FIXTURES_DIR / "fanout_pipeline.yaml")

        async def planner_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "node_outputs": {
                    "planner": {"status": "executed", "type": "agent"}
                },
                "pending_tasks": [
                    {"id": "t1", "description": "Task 1"},
                    {"id": "t2", "description": "Task 2"},
                ],
            }

        async def worker_fn(state: dict[str, Any]) -> dict[str, Any]:
            task_id = state.get("task_id", "unknown")
            return {
                "node_outputs": {
                    f"agent_worker_{task_id}": {
                        "status": "executed",
                        "type": "agent",
                    }
                }
            }

        async def merger_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {
                "node_outputs": {
                    "merger": {"type": "merge", "status": "executed"}
                }
            }

        engine = ExecutionEngine(
            node_functions={
                "planner": planner_fn,
                "agent_worker": worker_fn,
                "merger": merger_fn,
            }
        )
        result = await engine.execute_from_yaml(yaml_path)
        assert result.success
        assert result.graph_name == "fanout_pipeline"
