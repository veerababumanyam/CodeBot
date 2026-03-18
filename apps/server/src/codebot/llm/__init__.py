"""Multi-LLM abstraction layer for CodeBot.

Provides a provider-agnostic interface for all LLM calls with
task-based routing, fallback chains, cost tracking, and budget management.

Usage::

    from codebot.llm import LLMService, LLMRequest, TaskType

    service = LLMService.from_config(config)
    response = await service.complete(
        LLMRequest(messages=[LLMMessage(role="user", content="Hello")]),
        agent_id="my-agent",
        task_type=TaskType.CODE_GENERATION,
    )
"""

from codebot.llm.schemas import (
    BudgetDecision,
    LLMMessage,
    LLMRequest,
    LLMResponse,
    RoutingConstraints,
    RoutingRule,
    TaskType,
    TokenUsage,
)
from codebot.llm.service import LLMService, get_llm_service

__all__ = [
    "BudgetDecision",
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    "LLMService",
    "RoutingConstraints",
    "RoutingRule",
    "TaskType",
    "TokenUsage",
    "get_llm_service",
]
