"""GraphDefinition model -- the complete schema for a graph pipeline."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from graph_engine.models.edge_types import EdgeDefinition  # noqa: TC001
from graph_engine.models.node_types import NodeDefinition  # noqa: TC001


class GraphDefinition(BaseModel):
    """Immutable, validated definition of a complete computation graph."""

    model_config = ConfigDict(frozen=True)

    name: str
    version: str = "1.0"
    description: str = ""
    state_schema: dict[str, Any] = {}
    nodes: list[NodeDefinition]
    edges: list[EdgeDefinition]
    entry_nodes: list[str]
    exit_nodes: list[str]

    @field_validator("nodes")
    @classmethod
    def validate_nodes_non_empty(cls, v: list[NodeDefinition]) -> list[NodeDefinition]:
        if not v:
            msg = "nodes must not be empty"
            raise ValueError(msg)
        return v

    @field_validator("entry_nodes")
    @classmethod
    def validate_entry_nodes_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            msg = "entry_nodes must not be empty"
            raise ValueError(msg)
        return v
