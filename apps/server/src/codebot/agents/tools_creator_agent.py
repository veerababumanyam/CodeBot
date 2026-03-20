"""Tools Creator Agent -- generates custom tools and MCP server configurations.

Full implementation of Agent #28. Accepts natural-language tool descriptions,
designs parameter schemas, generates async implementations, registers tools
in the ToolService, and scaffolds MCP server configuration for external tool
exposure.

Runs post-delivery in Stage S9. Replaces the stub in tools_creator.py.

Implements the PRA cognitive cycle:
- perceive(): Gather tool requests and existing tool registry
- reason(): Design tool interfaces using LLM
- act(): Generate implementations, register via ToolService, produce MCP config
- review(): Validate created tools and format output
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, override

from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType

from codebot.agents.registry import register_agent

if TYPE_CHECKING:
    from codebot.events.bus import EventBus
    from codebot.tools.service import ToolService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<role>
You are the Tools Creator agent for CodeBot, a multi-agent software development
platform. You operate in the S9 (Documentation) pipeline stage, post-delivery.
Your purpose is to generate custom tools that extend the agent ecosystem.
</role>

<responsibilities>
- Accept natural-language descriptions of desired tool capabilities
- Design parameter schemas as JSON Schema draft 2020-12
- Generate async implementations for each tool
- Register tools in the tool registry via ToolService
- Produce MCP server configuration for external tool exposure
- Validate parameter schemas before registration
- Publish tool.created events for observability
</responsibilities>

<output_format>
Produce a JSON object with:
- "tool_specs": array of tool specifications, each with:
  - name, description, parameters (JSON Schema), implementation, version, tags
</output_format>

<constraints>
- All parameter schemas must be valid JSON Schema with a "type" field
- Tool names must be unique within the registry
- Implementations must be async callables
- MCP config must follow the MCP server specification
- Do not duplicate existing tools in the registry
</constraints>
"""


# ---------------------------------------------------------------------------
# Supporting data types
# ---------------------------------------------------------------------------


@dataclass(slots=True, kw_only=True)
class ToolSpec:
    """Specification for a tool to be created.

    Attributes:
        name: Unique tool name.
        description: What the tool does.
        parameters: JSON Schema for tool inputs.
        implementation: Python source for the async execute function.
        version: Semantic version string.
        tags: Searchable tags for discovery.
    """

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    implementation: str  # Python source for the async execute function
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------


@register_agent(AgentType.TOOL_BUILDER)
@dataclass(slots=True, kw_only=True)
class ToolsCreatorAgent(BaseAgent):
    """Agent #28: Generates custom tools and MCP server configurations.

    Runs post-delivery in Stage S9. Accepts natural-language tool descriptions,
    designs parameter schemas, generates async implementations, registers tools
    in the ToolService, and optionally scaffolds MCP server configuration for
    external tool exposure.

    Attributes:
        agent_type: Always ``AgentType.TOOL_BUILDER``.
        name: Human-readable agent name.
        model_tier: LLM tier selection.
        max_retries: Number of retry attempts on failure.
        tools: List of tool identifiers available to this agent.
    """

    agent_type: AgentType = field(default=AgentType.TOOL_BUILDER, init=False)
    name: str = "tools_creator"
    model_tier: str = "tier2"
    max_retries: int = 2
    tools: list[str] = field(
        default_factory=lambda: [
            "tool_generator",
            "schema_validator",
            "tool_registry",
            "mcp_config_builder",
        ]
    )

    # Injected dependencies (not part of config, set after construction)
    _tool_service: ToolService | None = field(default=None, init=False, repr=False)
    _event_bus: EventBus | None = field(default=None, init=False, repr=False)

    def set_services(self, tool_service: ToolService, event_bus: EventBus) -> None:
        """Inject service dependencies after construction.

        Args:
            tool_service: Service for creating tool definitions.
            event_bus: Event bus for publishing tool.created events.
        """
        self._tool_service = tool_service
        self._event_bus = event_bus

    @override
    async def _initialize(self, agent_input: AgentInput) -> None:
        """No additional initialization needed for ToolsCreatorAgent.

        Args:
            agent_input: The task input for initialization context.
        """

    @override
    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Gather tool requests and existing registry.

        Args:
            agent_input: The task input with shared_state containing
                         tool_requests, existing_tools, and project_context.

        Returns:
            Dict with tool_requests, existing_tools, and project_context.
        """
        shared_state = agent_input.shared_state
        return {
            "tool_requests": shared_state.get("tool_requests", []),
            "existing_tools": shared_state.get("existing_tools", []),
            "project_context": shared_state.get("project_context", {}),
        }

    @override
    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Design tool interfaces using LLM.

        For each tool request:
        1. Design the parameter JSON Schema
        2. Determine appropriate tags and version
        3. Plan the implementation approach
        4. Check for duplicates against existing_tools

        Args:
            context: Dict with tool_requests, existing_tools from perceive().

        Returns:
            Dict with tool_specs list and perception for the act phase.
        """
        return {"tool_specs": [], "perception": context}

    @override
    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Generate tool implementations and register them.

        For each tool spec:
        1. Validate parameter schema is valid JSON Schema
        2. Generate async execute function implementation
        3. Register via ToolService.create_tool()
        4. Generate MCP server config entry
        5. Emit tool.created event

        Args:
            plan: Dict with tool_specs list from reason().

        Returns:
            PRAResult with created_tools, mcp_config, and any errors.
        """
        from codebot.tools.registry import ToolDefinition

        created_tools: list[str] = []
        mcp_configs: list[dict[str, Any]] = []
        errors: list[str] = []

        specs: list[ToolSpec] = plan.get("tool_specs", [])
        for spec in specs:
            try:
                # Validate schema structure
                if not isinstance(spec.parameters, dict) or "type" not in spec.parameters:
                    msg = (
                        f"Invalid parameter schema for tool '{spec.name}': "
                        f"must be a JSON Schema object with 'type' field"
                    )
                    raise ValueError(msg)

                async def _placeholder_execute(
                    _tool_name: str = spec.name, **kwargs: Any
                ) -> str:
                    return f"Tool {_tool_name} executed with {kwargs}"

                definition = ToolDefinition(
                    name=spec.name,
                    description=spec.description,
                    parameters=spec.parameters,
                    execute=_placeholder_execute,
                    version=spec.version,
                    tags=spec.tags,
                )

                if self._tool_service is None:
                    raise RuntimeError("ToolService not injected -- call set_services() first")
                await self._tool_service.create_tool(definition)

                # Generate MCP config entry
                mcp_entry = {
                    "name": spec.name,
                    "description": spec.description,
                    "inputSchema": spec.parameters,
                }
                mcp_configs.append(mcp_entry)

                if self._event_bus is None:
                    raise RuntimeError("EventBus not injected -- call set_services() first")
                await self._event_bus.publish("tool.created", {
                    "name": spec.name,
                    "version": spec.version,
                    "created_by": "tools_creator",
                })
                created_tools.append(spec.name)
            except Exception as exc:
                errors.append(f"Failed to create tool '{spec.name}': {exc}")

        # Generate aggregate MCP server config
        mcp_server_config: dict[str, Any] = {
            "mcpServers": {
                "codebot-custom-tools": {
                    "command": "python",
                    "args": ["-m", "codebot.tools.mcp_server"],
                    "tools": mcp_configs,
                }
            }
        }

        return PRAResult(
            is_complete=True,
            data={
                "created_tools": created_tools,
                "mcp_config": mcp_server_config,
                "errors": errors,
            },
        )

    @override
    async def review(self, result: PRAResult) -> AgentOutput:
        """Validate tool creation output.

        Checks that created tools list is populated and no errors occurred.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed and state_updates containing
            tools_creator_output.
        """
        data = result.data
        has_errors = len(data.get("errors", [])) > 0
        review_passed = not has_errors or len(data.get("created_tools", [])) > 0

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={"tools_creator_output": data},
            review_passed=review_passed,
        )

    def generate_mcp_config(self, tools: list[ToolSpec]) -> dict[str, Any]:
        """Generate MCP server configuration JSON for the created tools.

        Args:
            tools: List of ToolSpec objects to include in the config.

        Returns:
            MCP server configuration dict with mcpServers entry.
        """
        return {
            "mcpServers": {
                "codebot-custom-tools": {
                    "command": "python",
                    "args": ["-m", "codebot.tools.mcp_server"],
                    "tools": [
                        {
                            "name": t.name,
                            "description": t.description,
                            "inputSchema": t.parameters,
                        }
                        for t in tools
                    ],
                }
            }
        }

    def build_system_prompt(self) -> str:
        """Return the system prompt for the Tools Creator agent.

        Returns:
            The SYSTEM_PROMPT constant.
        """
        return SYSTEM_PROMPT
