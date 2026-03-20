"""Pydantic v2 schemas for agent management endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentResponse(BaseModel):
    """Agent data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    agent_type: str
    status: str
    llm_provider: str
    llm_model: str
    tokens_used: int
    cost_usd: float
    started_at: datetime | None
    completed_at: datetime | None
    error_count: int

    @field_validator("agent_type", "status", mode="before")
    @classmethod
    def enum_to_string(cls, v: object) -> str:
        """Convert AgentType/AgentStatus enums to lowercase string."""
        if hasattr(v, "value"):
            return str(v.value).lower()
        return str(v).lower()


class AgentDetailResponse(AgentResponse):
    """Extended agent data including worktree and prompt info."""

    worktree_path: str | None
    cli_agent_type: str | None
    system_prompt_hash: str


class AgentStopRequest(BaseModel):
    """Request body for stopping an agent."""

    reason: str | None = None
    force: bool = False


class AgentConfigUpdate(BaseModel):
    """Request body for updating agent configuration.

    All fields are optional -- only provided fields are applied.
    """

    llm_provider: str | None = None
    llm_model: str | None = None
    system_prompt: str | None = None
    max_retries: int | None = Field(default=None, ge=0, le=10)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)


class AgentMessageRequest(BaseModel):
    """Request body for sending a message to an agent."""

    message: str = Field(min_length=1)
    type: str = Field(default="instruction", pattern="^(instruction|question|correction)$")
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")


class AgentMessageResponse(BaseModel):
    """Response for agent message operations."""

    message_id: UUID
    agent_id: UUID
    acknowledged: bool
    acknowledged_at: datetime


class AgentLogEntry(BaseModel):
    """A single log entry from an agent."""

    timestamp: datetime
    level: str
    message: str
    metadata: dict | None = None


class AgentLogsResponse(BaseModel):
    """Response for agent log retrieval."""

    agent_id: UUID
    logs: list[AgentLogEntry]
    has_more: bool


class AgentTypeInfo(BaseModel):
    """Information about an available agent type."""

    type: str
    display_name: str
    description: str
    category: str
    capabilities: list[str]
