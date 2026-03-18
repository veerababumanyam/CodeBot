"""SharedState definition with parallel-safe reducers."""

from __future__ import annotations

from operator import add
from typing import Annotated, Any

from typing_extensions import TypedDict


def merge_dicts(existing: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Reducer: merge dicts from parallel nodes, later values win."""
    return {**existing, **update}


class SharedState(TypedDict):
    """Graph-level shared state with Annotated reducers for parallel safety."""

    node_outputs: Annotated[dict[str, Any], merge_dicts]
    execution_trace: Annotated[list[dict[str, Any]], add]
    errors: Annotated[list[dict[str, Any]], add]
