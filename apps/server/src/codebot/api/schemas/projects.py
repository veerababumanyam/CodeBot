"""Pydantic v2 schemas for project CRUD endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    """Request body for creating a new project."""

    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    prd_source: str = "text"
    prd_content: str = ""
    tech_stack: dict | None = None
    settings: dict | None = None


class ProjectUpdate(BaseModel):
    """Request body for updating a project (partial)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ProjectResponse(BaseModel):
    """Project data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    status: str
    project_type: str
    prd_format: str
    tech_stack: dict | None
    created_at: datetime
    updated_at: datetime

    @field_validator("status", "project_type", mode="before")
    @classmethod
    def enum_to_string(cls, v: object) -> str:
        """Convert ORM enum to lowercase string."""
        if hasattr(v, "value"):
            return str(v.value).lower()
        return str(v).lower()


class ProjectDetailResponse(ProjectResponse):
    """Extended project data including PRD content and config."""

    prd_content: str
    config: dict | None
    repository_path: str
    repository_url: str | None
