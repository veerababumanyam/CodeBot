"""Pydantic v2 schemas for project CRUD endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ProjectCreate(BaseModel):
    """Request body for creating a new project."""

    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    prd_source: str = "text"
    prd_content: str = ""
    prd_url: str | None = None
    prd_file: str | None = None
    source_name: str | None = None
    source_media_type: str | None = None
    project_type: str | None = None
    repository_path: str | None = None
    repository_url: str | None = None
    tech_stack: dict | None = None
    settings: dict | None = None

    @field_validator("prd_source")
    @classmethod
    def validate_prd_source(cls, value: str) -> str:
        """Normalize and validate the PRD source selector."""
        normalized = value.strip().lower().replace("-", "_")
        allowed = {"text", "url", "file"}
        if normalized not in allowed:
            raise ValueError(f"prd_source must be one of {sorted(allowed)}")
        return normalized

    @field_validator("project_type")
    @classmethod
    def validate_project_type(cls, value: str | None) -> str | None:
        """Normalize optional project type values."""
        if value is None:
            return None
        normalized = value.strip().lower().replace("-", "_")
        allowed = {"greenfield", "inflight", "brownfield", "improve"}
        if normalized not in allowed:
            raise ValueError(f"project_type must be one of {sorted(allowed)}")
        return normalized

    @model_validator(mode="after")
    def validate_source_payload(self) -> "ProjectCreate":
        """Ensure the selected PRD source has the required payload."""
        if self.prd_source == "url" and not (self.prd_url or "").strip():
            raise ValueError("prd_url is required when prd_source is 'url'")
        if self.prd_source == "file" and not (self.prd_file or "").strip():
            raise ValueError("prd_file is required when prd_source is 'file'")
        return self


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
