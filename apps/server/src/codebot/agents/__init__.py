"""Agent package -- imports trigger registration via @register_agent decorators.

Re-exports the registry functions for convenient access::

    from codebot.agents import register_agent, create_agent, get_all_registered

Importing this package triggers all agent module imports, which execute
the ``@register_agent`` decorators and populate ``_REGISTRY`` with all
30 concrete agent classes.

Note: ``database_designer`` is imported but does NOT use ``@register_agent``
(it shares ``AgentType.ARCHITECT`` by design and is accessed directly).
"""

from codebot.agents.registry import create_agent, get_all_registered, register_agent  # noqa: F401

# Import all agent modules to trigger @register_agent decorators.
# Each module's @register_agent decorator adds the class to _REGISTRY.
from codebot.agents import (  # noqa: F401
    brainstorming,
    researcher,
    architect,
    designer,
    template_curator,
    database_designer,
    api_designer,
    planner,
    techstack_builder,
    frontend_dev,
    backend_dev,
    middleware_dev,
    mobile_dev,
    infra_engineer,
    integrations,
    code_reviewer,
    security_auditor,
    accessibility,
    performance,
    i18n_l10n,
    tester,
    debugger,
    doc_writer,
    devops,
    github_agent,
    orchestrator,
    project_manager,
    collaboration_manager,
    skill_creator,
    hooks_creator,
    tools_creator,
)

__all__ = [
    "create_agent",
    "get_all_registered",
    "register_agent",
]
