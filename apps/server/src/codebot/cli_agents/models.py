"""Pydantic v2 models for CLI agent integration.

Defines data transfer objects for CLI tasks, results, and adapter metadata
used across the cli_agents subsystem.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from codebot.security.models import SecurityReport  # noqa: TC001


class CLITask(BaseModel):
    """A task to be executed by a CLI agent adapter.

    Attributes:
        prompt: The natural language prompt describing the task.
        allowed_tools: List of tool names the agent is allowed to use.
        max_tokens: Maximum tokens for the agent's response.
        files_context: List of file paths to include as context.
        timeout: Maximum execution time in seconds.
    """

    prompt: str
    allowed_tools: list[str] = Field(default_factory=list)
    max_tokens: int = 4096
    files_context: list[str] = Field(default_factory=list)
    timeout: int = 300


class CLIResult(BaseModel):
    """Result from a CLI agent execution.

    Attributes:
        stdout: Standard output captured from the process.
        stderr: Standard error captured from the process.
        returncode: Process exit code (0 = success, -1 = timeout/error).
        duration_ms: Execution duration in milliseconds.
        parsed_output: Parsed JSON output from the CLI tool.
        security_report: Security scan report attached after code generation
            (set by CLIAgentRunner when SecurityOrchestrator is provided).
    """

    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    duration_ms: int = 0
    parsed_output: dict[str, Any] = Field(default_factory=dict)
    security_report: SecurityReport | None = None


class AdapterInfo(BaseModel):
    """Metadata about a CLI agent adapter and its availability.

    Attributes:
        name: Human-readable adapter class name.
        binary: Name of the CLI binary the adapter wraps.
        available: Whether the binary was found on PATH.
        version: Detected version string of the binary.
    """

    name: str
    binary: str
    available: bool = False
    version: str = "unknown"
