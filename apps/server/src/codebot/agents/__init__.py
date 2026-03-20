"""Concrete agent implementations for the CodeBot pipeline.

Re-exports the registry functions for convenient access::

    from codebot.agents import register_agent, create_agent, get_all_registered
"""

from codebot.agents.registry import create_agent, get_all_registered, register_agent

__all__ = [
    "create_agent",
    "get_all_registered",
    "register_agent",
]
