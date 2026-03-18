"""API contract models for Pipeline operations.

These Pydantic models define the request/response shapes for the Pipeline
REST endpoints — separate from the full PipelineSchema read model.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel

from agent_sdk.models.enums import PipelineStatus


class PipelineCreateRequest(BaseModel):
    """Request body for creating a new pipeline.

    Attributes:
        project_id: The project to attach the pipeline to.
        config: Optional pipeline configuration overrides.
    """

    project_id: uuid.UUID
    config: dict[str, Any] | None = None


class PipelineStatusResponse(BaseModel):
    """Lightweight status response for a pipeline.

    Attributes:
        id: Pipeline identifier.
        project_id: Owning project.
        status: Current execution state.
        current_phase: Name of the active phase.
        total_tokens_used: Cumulative token consumption.
        total_cost_usd: Cumulative cost in USD.
    """

    id: uuid.UUID
    project_id: uuid.UUID
    status: PipelineStatus
    current_phase: str
    total_tokens_used: int
    total_cost_usd: float
