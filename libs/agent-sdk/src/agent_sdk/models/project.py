"""Pydantic v2 schemas for Project, Pipeline, and PipelinePhase.

These are API/event schemas (not ORM models). Use ``model_config =
ConfigDict(from_attributes=True)`` for ORM→schema conversion in API handlers.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from agent_sdk.models.enums import (
    PhaseStatus,
    PhaseType,
    PipelineStatus,
    ProjectStatus,
    ProjectType,
)


class ProjectSchema(BaseModel):
    """Public schema for a CodeBot Project.

    Attributes:
        id: Unique project identifier.
        name: Human-readable project name.
        description: Detailed project description.
        status: Current lifecycle state.
        project_type: Classification of the project's starting point.
        tech_stack: Arbitrary JSON mapping tech category to chosen stack.
        created_at: Timestamp of record creation.
        updated_at: Timestamp of last modification.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    status: ProjectStatus
    project_type: ProjectType
    tech_stack: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PipelineSchema(BaseModel):
    """Public schema for a Pipeline execution.

    Attributes:
        id: Unique pipeline identifier.
        project_id: Parent project reference.
        status: Current execution state.
        current_phase: Name of the actively running phase.
        total_tokens_used: Cumulative LLM token consumption.
        total_cost_usd: Cumulative cost in USD.
        started_at: When pipeline execution began.
        completed_at: When pipeline execution finished (nullable).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    status: PipelineStatus
    current_phase: str
    total_tokens_used: int
    total_cost_usd: float
    started_at: datetime
    completed_at: datetime | None = None


class PipelinePhaseSchema(BaseModel):
    """Public schema for a single PipelinePhase.

    Attributes:
        id: Unique phase identifier.
        pipeline_id: Parent pipeline reference.
        name: Human-readable phase name.
        phase_type: SDLC phase classification.
        status: Current execution state.
        order: Numeric ordering within the pipeline.
        requires_approval: Whether human approval is needed to proceed.
        started_at: When this phase began (nullable).
        completed_at: When this phase finished (nullable).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pipeline_id: uuid.UUID
    name: str
    phase_type: PhaseType
    status: PhaseStatus
    order: int
    requires_approval: bool
    started_at: datetime | None = None
    completed_at: datetime | None = None
