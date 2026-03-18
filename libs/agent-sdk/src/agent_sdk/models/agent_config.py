"""Pydantic models for YAML agent configuration.

Stub file -- implementation follows TDD GREEN phase.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RetryPolicyConfig(BaseModel):
    """Retry policy for agent recovery. Stub."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    max_retries: int = 3


class ContextTiersConfig(BaseModel):
    """Token budget allocation per context tier. Stub."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    l0: int = 2000


class AgentConfig(BaseModel):
    """Full agent configuration loaded from YAML. Stub."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    agent_type: str
    model: str


def load_agent_config(path: Path) -> AgentConfig:
    """Load and validate a single agent YAML config file. Stub."""
    raise NotImplementedError("RED phase stub")
