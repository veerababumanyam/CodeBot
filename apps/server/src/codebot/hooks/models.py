"""Hook domain models for the hook registry.

Defines the Hook dataclass used by HookService and HooksCreatorAgent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class HookType(StrEnum):
    """Types of lifecycle hooks in the pipeline."""

    PRE_PHASE = "PRE_PHASE"
    POST_PHASE = "POST_PHASE"
    PRE_AGENT = "PRE_AGENT"
    POST_AGENT = "POST_AGENT"
    ON_ERROR = "ON_ERROR"
    ON_APPROVAL = "ON_APPROVAL"
    ON_EVENT = "ON_EVENT"


class HookStatus(StrEnum):
    """Lifecycle status for a Hook."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    FAILED = "FAILED"


@dataclass(slots=True, kw_only=True)
class Hook:
    """A lifecycle hook registered in the pipeline.

    Attributes:
        id: Unique hook identifier.
        name: Human-readable hook name.
        hook_type: When this hook fires in the lifecycle.
        target: Target phase/agent/event for the hook.
        priority: Execution priority (lower = earlier).
        timeout_ms: Maximum execution time in milliseconds.
        enabled: Whether the hook is currently enabled.
        status: Current lifecycle status.
        metadata: Additional hook configuration.
    """

    id: str = ""
    name: str = ""
    hook_type: HookType = HookType.ON_EVENT
    target: str = ""
    priority: int = 100
    timeout_ms: int = 30000
    enabled: bool = True
    status: HookStatus = HookStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)
