"""Node type definitions for the graph engine."""

from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class NodeType(enum.StrEnum):
    """All supported graph node types."""

    AGENT = "agent"
    SUBGRAPH = "subgraph"
    LOOP = "loop"
    SWITCH = "switch"
    HUMAN_IN_LOOP = "human"
    PARALLEL = "parallel"
    MERGE = "merge"
    CHECKPOINT = "checkpoint"
    TRANSFORM = "transform"
    GATE = "gate"


class RetryPolicy(BaseModel, frozen=True):
    """Retry configuration for node execution."""

    max_retries: int = 3
    backoff_factor: float = 2.0
    retry_on: list[str] = ["TimeoutError", "RateLimitError"]


class NodeDefinition(BaseModel):
    """Immutable definition of a single graph node."""

    model_config = ConfigDict(frozen=True)

    id: str
    type: NodeType
    config: dict[str, Any] = {}
    retry_policy: RetryPolicy = RetryPolicy()
    timeout_seconds: int = 600

    @field_validator("id")
    @classmethod
    def validate_node_id(cls, v: str) -> str:
        if not v.isidentifier():
            msg = f"Node ID must be a valid Python identifier: {v!r}"
            raise ValueError(msg)
        return v

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            msg = f"timeout_seconds must be > 0, got {v}"
            raise ValueError(msg)
        return v
