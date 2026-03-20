"""Pydantic v2 schemas for pipeline CRUD and lifecycle endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PipelineCreate(BaseModel):
    """Request body for creating a new pipeline."""

    name: str | None = Field(default=None, max_length=255)
    mode: str = Field(
        default="full",
        pattern="^(full|quick|review_only|incremental|phase_only)$",
    )
    phases: list[str] | None = None
    config: dict | None = None


class PipelineResponse(BaseModel):
    """Pipeline data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    status: str
    current_phase: str
    started_at: datetime | None
    completed_at: datetime | None
    total_tokens_used: int
    total_cost_usd: float

    @field_validator("status", mode="before")
    @classmethod
    def enum_to_string(cls, v: object) -> str:
        """Convert PipelineStatus enum to lowercase string."""
        if hasattr(v, "value"):
            return str(v.value).lower()
        return str(v).lower()


class PipelineDetailResponse(PipelineResponse):
    """Extended pipeline data including graph definition and error info."""

    graph_definition: dict | None
    error_message: str | None
    name: str | None = None
    mode: str | None = None
    config: dict | None = None


class PipelinePhaseResponse(BaseModel):
    """Pipeline phase data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phase_type: str
    status: str
    order: int
    requires_approval: bool
    approved_by: str | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None = None

    @field_validator("phase_type", "status", mode="before")
    @classmethod
    def enum_to_string(cls, v: object) -> str:
        """Convert PhaseType/PhaseStatus enums to lowercase string."""
        if hasattr(v, "value"):
            return str(v.value).lower()
        return str(v).lower()


class PipelineActionResponse(BaseModel):
    """Response for pipeline lifecycle actions (start, pause, resume, cancel)."""

    id: UUID
    status: str
    timestamp: datetime


class PhaseApprovalRequest(BaseModel):
    """Request body for approving or rejecting a pipeline phase."""

    approved: bool
    comment: str | None = None
