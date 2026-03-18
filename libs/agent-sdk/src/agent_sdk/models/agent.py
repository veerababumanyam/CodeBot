"""Pydantic v2 schemas for Agent and AgentExecution."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from agent_sdk.models.enums import AgentStatus, AgentType, ExecutionStatus


class AgentSchema(BaseModel):
    """Public schema for an Agent instance.

    Attributes:
        id: Unique agent identifier.
        project_id: Owning project reference.
        agent_type: Role specialization.
        status: Current runtime state.
        llm_provider: LLM provider name (e.g., ``openai``, ``anthropic``).
        llm_model: Model identifier (e.g., ``gpt-4o``, ``claude-3-5-sonnet``).
        worktree_path: Isolated git worktree directory (nullable).
        cli_agent_type: Delegate CLI agent type (nullable).
        system_prompt_hash: SHA-256 of the agent's system prompt.
        tokens_used: Total tokens consumed.
        cost_usd: Total cost in USD.
        started_at: When this agent instance was initialized.
        completed_at: When execution finished (nullable).
        error_count: Number of retried errors encountered.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    agent_type: AgentType
    status: AgentStatus
    llm_provider: str
    llm_model: str
    worktree_path: str | None = None
    cli_agent_type: str | None = None
    system_prompt_hash: str
    tokens_used: int
    cost_usd: float
    started_at: datetime
    completed_at: datetime | None = None
    error_count: int


class AgentExecutionSchema(BaseModel):
    """Public schema for a single LLM execution by an Agent.

    Attributes:
        id: Unique execution identifier.
        agent_id: Owning agent reference.
        task_id: Associated task reference.
        llm_provider: Provider used for this execution.
        llm_model: Model used for this execution.
        input_tokens: Tokens in the prompt.
        output_tokens: Tokens in the completion.
        total_tokens: Sum of input + output tokens.
        cost_usd: Cost for this specific execution.
        duration_ms: Wall-clock duration in milliseconds.
        status: Execution outcome.
        input_messages: Raw input messages as JSON-serializable list.
        output_messages: Raw output messages as JSON-serializable list.
        tool_calls: Tool invocations made during this execution.
        error_message: Error details on failure (nullable).
        created_at: Timestamp of execution start.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_id: uuid.UUID
    task_id: uuid.UUID
    llm_provider: str
    llm_model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    duration_ms: int
    status: ExecutionStatus
    input_messages: list[dict]
    output_messages: list[dict]
    tool_calls: list[dict]
    error_message: str | None = None
    created_at: datetime
