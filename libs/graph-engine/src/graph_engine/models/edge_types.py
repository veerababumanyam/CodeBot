"""Edge type definitions for the graph engine."""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict


class EdgeType(enum.StrEnum):
    """Flow types for graph edges."""

    STATE_FLOW = "state_flow"
    MESSAGE_FLOW = "message_flow"
    CONTROL_FLOW = "control_flow"


class EdgeDefinition(BaseModel):
    """Immutable definition of a directed edge between two nodes."""

    model_config = ConfigDict(frozen=True)

    source: str
    target: str
    type: EdgeType = EdgeType.STATE_FLOW
    condition: str | None = None
    transform: str | None = None
