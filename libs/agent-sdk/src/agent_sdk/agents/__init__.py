"""Agent framework: BaseAgent, state machine, recovery, metrics, and protocol stubs."""

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.agents.metrics import AgentMetrics
from agent_sdk.agents.protocols import LLMProvider, LLMResponse, ToolRegistry, WorktreeProvider
from agent_sdk.agents.recovery import (
    EscalateStrategy,
    FallbackModelStrategy,
    RecoveryAction,
    RecoveryContext,
    RecoveryStrategy,
    RetryWithModifiedPrompt,
    RollbackStrategy,
)
from agent_sdk.agents.state_machine import AgentStateMachine, InvalidTransitionError, VALID_TRANSITIONS

__all__ = [
    "AgentInput",
    "AgentMetrics",
    "AgentOutput",
    "AgentStateMachine",
    "BaseAgent",
    "EscalateStrategy",
    "FallbackModelStrategy",
    "InvalidTransitionError",
    "LLMProvider",
    "LLMResponse",
    "PRAResult",
    "RecoveryAction",
    "RecoveryContext",
    "RecoveryStrategy",
    "RetryWithModifiedPrompt",
    "RollbackStrategy",
    "ToolRegistry",
    "VALID_TRANSITIONS",
    "WorktreeProvider",
]
