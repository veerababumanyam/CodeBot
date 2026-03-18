"""Pydantic models for YAML agent configuration.

Validates agent configuration files with strict typing, frozen
immutability, and extra key rejection. Supports loading from YAML
files with a single top-level key pattern (agent name -> config dict).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RetryPolicyConfig(BaseModel):
    """Retry policy for agent recovery.

    Attributes:
        max_retries: Maximum retry attempts (0-10).
        base_delay_seconds: Initial backoff delay.
        max_delay_seconds: Maximum backoff delay cap.
        exponential_base: Base for exponential backoff calculation.
        recovery_strategy: Strategy name (must match allowed pattern).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_retries: int = Field(default=3, ge=0, le=10)
    base_delay_seconds: float = Field(default=2.0, gt=0)
    max_delay_seconds: float = Field(default=60.0, gt=0)
    exponential_base: float = Field(default=2.0, ge=1.0)
    recovery_strategy: str = Field(
        default="retry_with_modified_prompt",
        pattern=r"^(retry_with_modified_prompt|escalate|rollback|fallback_model)$",
    )


class ContextTiersConfig(BaseModel):
    """Token budget allocation per context tier.

    Attributes:
        l0: L0 (always-in-context) token budget.
        l1: L1 (phase-scoped) token budget.
        l2: L2 (on-demand retrieval) token budget.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    l0: int = Field(default=2000, ge=0)
    l1: int = Field(default=10000, ge=0)
    l2: int = Field(default=20000, ge=0)


class AgentConfig(BaseModel):
    """Full agent configuration loaded from YAML.

    Uses frozen=True to prevent mutation after creation and
    extra='forbid' to reject unknown keys in YAML configs.

    Attributes:
        agent_type: Agent specialization (validated against AgentType enum).
        model: Primary LLM model identifier.
        fallback_model: Optional fallback model for recovery.
        provider: LLM provider name.
        max_tokens: Maximum output tokens per LLM call.
        temperature: LLM sampling temperature.
        tools: List of tool names this agent can use.
        context_tiers: Token budget per context tier.
        retry_policy: Retry and recovery configuration.
        timeout: Maximum execution time in seconds.
        system_prompt: Inline system prompt text.
        system_prompt_file: Path to system prompt file (relative).
        settings: Additional agent-specific settings.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    agent_type: str
    model: str
    fallback_model: str | None = None
    provider: str = "anthropic"
    max_tokens: int = Field(default=4096, ge=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    tools: list[str] = Field(default_factory=list)
    context_tiers: ContextTiersConfig = Field(default_factory=ContextTiersConfig)
    retry_policy: RetryPolicyConfig = Field(default_factory=RetryPolicyConfig)
    timeout: int = Field(default=600, ge=1)
    system_prompt: str | None = None
    system_prompt_file: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)

    @field_validator("agent_type")
    @classmethod
    def validate_agent_type(cls, v: str) -> str:
        """Validate agent_type against the AgentType enum (case-insensitive)."""
        from agent_sdk.models.enums import AgentType

        try:
            AgentType(v.upper())
        except ValueError:
            msg = f"Unknown agent type: {v}"
            raise ValueError(msg) from None
        return v


def load_agent_config(path: Path) -> AgentConfig:
    """Load and validate a single agent YAML config file.

    Supports the single top-level key pattern where the key name
    is the agent type and the value is the config dict.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        Validated AgentConfig instance.
    """
    with open(path) as f:
        raw = yaml.safe_load(f)
    # YAML has the agent name as the top-level key
    if isinstance(raw, dict) and len(raw) == 1:
        name = next(iter(raw))
        data = raw[name]
        if isinstance(data, dict):
            data.setdefault("agent_type", name.upper())
        else:
            data = raw
    else:
        data = raw
    return AgentConfig.model_validate(data)
