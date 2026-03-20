"""Schemas for project brainstorm session endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class BrainstormQuestion(BaseModel):
    """A guided clarification question for project intake."""

    id: str
    category: str
    prompt: str
    required: bool = True
    priority: str = "high"
    answer: str | None = None
    status: str = "open"


class BrainstormMessage(BaseModel):
    """A message in the brainstorm conversation."""

    id: str
    role: str
    content: str
    created_at: datetime


class BrainstormSummary(BaseModel):
    """Machine-usable summary of brainstorm readiness."""

    readiness_score: int = Field(ge=0, le=100)
    ready_for_pipeline: bool
    blockers: list[str]
    recommended_preset: str
    recommended_next_step: str
    open_questions: int = Field(ge=0)
    answered_questions: int = Field(ge=0)
    required_questions_remaining: int = Field(ge=0)


class BrainstormSessionResponse(BaseModel):
    """Current brainstorm session state for a project."""

    session_id: str
    project_id: UUID
    status: str
    started_at: datetime
    updated_at: datetime
    overview: str
    refined_brief: str
    questions: list[BrainstormQuestion]
    messages: list[BrainstormMessage]
    summary: BrainstormSummary
    source_context: dict[str, Any] | None = None
    agent_output: dict[str, Any] | None = None


class BrainstormRespondRequest(BaseModel):
    """Request body for answering a brainstorm question."""

    content: str = Field(min_length=1)
    question_id: str | None = None