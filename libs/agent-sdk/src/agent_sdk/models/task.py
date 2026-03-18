"""Pydantic v2 schema for Task."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from agent_sdk.models.enums import TaskStatus


class TaskSchema(BaseModel):
    """Public schema for an agent Task.

    Attributes:
        id: Unique task identifier.
        project_id: Owning project reference.
        phase_id: Associated pipeline phase.
        parent_task_id: Parent task for sub-tasks (nullable).
        title: Short descriptive title.
        description: Detailed task description.
        status: Current lifecycle state.
        priority: Numeric priority (lower = higher priority).
        assigned_agent_type: Agent type responsible for this task.
        dependencies: UUIDs of tasks that must complete first.
        input_context: Arbitrary input context as JSON dict.
        output_artifacts: Produced artifacts as JSON (nullable).
        created_at: Record creation timestamp.
        started_at: When execution began (nullable).
        completed_at: When execution finished (nullable).
        error_message: Failure details (nullable).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    phase_id: uuid.UUID
    parent_task_id: uuid.UUID | None = None
    title: str
    description: str
    status: TaskStatus
    priority: int
    assigned_agent_type: str
    dependencies: list[uuid.UUID]
    input_context: dict
    output_artifacts: dict | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
