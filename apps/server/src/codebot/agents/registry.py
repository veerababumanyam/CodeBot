"""Agent registry -- class-level registration and factory for CodeBot agents.

Provides a decorator-based registration pattern so agent classes self-register
when their module is imported, and a factory function to instantiate agents
by AgentType enum.

Usage::

    from codebot.agents.registry import register_agent, create_agent
    from agent_sdk.models.enums import AgentType

    @register_agent(AgentType.BRAINSTORM_FACILITATOR)
    @dataclass(slots=True, kw_only=True)
    class BrainstormingAgent(BaseAgent):
        ...

    agent = create_agent(AgentType.BRAINSTORM_FACILITATOR)
"""

from __future__ import annotations

import logging
from typing import Any

from agent_sdk.models.enums import AgentType

logger = logging.getLogger(__name__)

_REGISTRY: dict[AgentType, type] = {}


def register_agent(agent_type: AgentType):
    """Class decorator that registers an agent class in the global registry.

    Args:
        agent_type: The AgentType enum value to register this class under.

    Returns:
        A decorator that adds the class to ``_REGISTRY`` and returns it unchanged.

    Raises:
        ValueError: If ``agent_type`` is already registered (prevents silent overwrites).
    """

    def decorator(cls: type) -> type:
        if agent_type in _REGISTRY:
            logger.warning(
                "Overwriting registry entry for %s: %s -> %s",
                agent_type,
                _REGISTRY[agent_type].__name__,
                cls.__name__,
            )
        _REGISTRY[agent_type] = cls
        logger.debug("Registered agent %s -> %s", agent_type, cls.__name__)
        return cls

    return decorator


def create_agent(agent_type: AgentType, **kwargs: Any) -> object:
    """Instantiate a registered agent by its AgentType.

    Args:
        agent_type: The AgentType to look up.
        **kwargs: Keyword arguments forwarded to the agent constructor.

    Returns:
        An instance of the registered agent class.

    Raises:
        ValueError: If no agent is registered for the given type.
    """
    cls = _REGISTRY.get(agent_type)
    if cls is None:
        raise ValueError(f"No agent registered for type {agent_type}")
    return cls(**kwargs)


def get_all_registered() -> dict[AgentType, type]:
    """Return a shallow copy of the agent registry.

    Returns:
        Dict mapping AgentType to the registered agent class.
        Modifying the returned dict does not affect the internal registry.
    """
    return dict(_REGISTRY)
