"""Dynamic fan-out helpers using LangGraph Send API."""

from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
from typing import Any

from langgraph.types import Send
from pydantic import BaseModel, ConfigDict, field_validator


class FanOutConfig(BaseModel):
    """Configuration for dynamic fan-out dispatch."""

    model_config = ConfigDict(frozen=True)

    source_node: str
    worker_node: str
    task_key: str  # Key in SharedState containing list of tasks to dispatch

    @field_validator("task_key")
    @classmethod
    def validate_task_key(cls, v: str) -> str:
        if not v.strip():
            msg = "task_key must be a non-empty string"
            raise ValueError(msg)
        return v


def build_fanout_node(config: FanOutConfig) -> Callable[..., list[Send]]:
    """Build a dispatch function that uses LangGraph's Send API for dynamic fan-out.

    The returned function reads state[config.task_key] (a list of task dicts)
    and returns a list[Send], one per task, each targeting config.worker_node.

    Each Send payload is: {"task": task_dict, "task_id": task_dict["id"]}
    If a task dict has no "id" key, uses the list index as task_id.
    """

    def dispatch(state: dict[str, Any]) -> list[Send]:
        tasks = state.get(config.task_key, [])
        if not tasks:
            return []
        sends = []
        for idx, task in enumerate(tasks):
            task_id = task.get("id", str(idx)) if isinstance(task, dict) else str(idx)
            sends.append(Send(config.worker_node, {"task": task, "task_id": task_id}))
        return sends

    return dispatch
