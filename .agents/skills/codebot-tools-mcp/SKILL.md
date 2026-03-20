---
skill: codebot-tools-mcp
title: CodeBot Custom Tools and MCP Integration
description: >
  How to work with CodeBot's custom tool system and Model Context Protocol (MCP)
  integration subsystem, including tool lifecycle, registry, MCP server/client,
  and agent bindings.
version: "1.0"
tags:
  - codebot
  - tools
  - mcp
  - agents
  - python
---

# CodeBot Custom Tools and MCP Integration

## Overview

CodeBot's tool subsystem allows agents to discover, register, and execute custom tools.
MCP (Model Context Protocol) is Anthropic's open standard for connecting LLMs to external
tools and data sources. CodeBot implements both an MCP server (exposing tools) and MCP
client (consuming external tools).

## Project Layout

```
apps/server/src/codebot/
  tools/
    service.py          # Tool lifecycle management
    registry.py         # Tool discovery and registration
    mcp_server.py       # MCP server exposing custom tools
  agents/
    tools_creator_agent.py  # Agent that creates custom tools and MCP integrations
  context/
    mcp.py              # MCP protocol integration and context management
```

## Tech Stack Requirements

- Python 3.12+
- Strict mypy type checking
- Linting with ruff
- Async-first design (all tool execution and MCP communication is async)

---

## 1. Tool Data Model

Every tool follows a consistent data model with four core components:

```python
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

@dataclass
class ToolDefinition:
    """Canonical representation of a CodeBot tool."""
    name: str                          # Unique identifier, e.g. "file_edit"
    description: str                   # Human-readable purpose
    parameters: dict[str, Any]         # JSON Schema for input parameters
    execute: Callable[..., Awaitable[Any]]  # Async execution function
    version: str = "1.0.0"            # Semver for capability matching
    tags: list[str] = field(default_factory=list)  # For discovery/filtering
```

### Parameter Schema Convention

Parameter schemas follow JSON Schema draft 2020-12:

```python
parameters = {
    "type": "object",
    "properties": {
        "file_path": {"type": "string", "description": "Absolute path to the file"},
        "content": {"type": "string", "description": "New file content"},
    },
    "required": ["file_path", "content"],
}
```

### Built-in Tool Categories

CodeBot ships with these tool families:
- **File editing** -- read, write, edit, glob, grep
- **Terminal** -- shell command execution
- **Browser** -- web navigation and interaction
- **Database access** -- query and schema inspection
- **Web search** -- internet search and page fetch
- **Documentation retrieval** -- project and library docs
- **Diagram generation** -- architecture and flow diagrams
- **Schema design** -- data model creation
- **Test runner** -- execute and report test results
- **Metric collector** -- gather runtime and code metrics
- **Git operations** -- commit, branch, diff, log

---

## 2. Tool Service Layer

`tools/service.py` manages the full tool lifecycle: creation, validation, execution,
and teardown.

### Key Patterns

```python
class ToolService:
    """Manages tool lifecycle: create, validate, execute, teardown."""

    def __init__(self, registry: "ToolRegistry") -> None:
        self._registry = registry

    async def create_tool(self, definition: ToolDefinition) -> None:
        """Validate and register a new tool."""
        self._validate_schema(definition.parameters)
        await self._registry.register(definition)

    async def execute_tool(self, name: str, params: dict[str, Any]) -> Any:
        """Look up a tool by name and execute it with validated params."""
        tool = await self._registry.get(name)
        validated = self._validate_params(tool.parameters, params)
        return await tool.execute(**validated)

    async def remove_tool(self, name: str) -> None:
        """Unregister and clean up a tool."""
        await self._registry.unregister(name)

    def _validate_schema(self, schema: dict[str, Any]) -> None:
        """Ensure the parameter schema is valid JSON Schema."""
        ...

    def _validate_params(
        self, schema: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate and coerce input params against the tool's schema."""
        ...
```

### Design Rules

- All public methods are **async**.
- Schema validation happens at registration time (fail fast).
- Parameter validation happens at execution time.
- Errors raise typed exceptions (`ToolNotFoundError`, `ToolValidationError`).

---

## 3. Tool Registry

`tools/registry.py` handles discovery, registration, capability matching, and version
management.

### Registry Patterns

```python
class ToolRegistry:
    """Central registry for tool discovery and management."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    async def register(self, tool: ToolDefinition) -> None:
        """Register a tool, rejecting duplicates unless version differs."""
        if tool.name in self._tools:
            existing = self._tools[tool.name]
            if existing.version == tool.version:
                raise ToolAlreadyRegisteredError(tool.name)
        self._tools[tool.name] = tool

    async def get(self, name: str) -> ToolDefinition:
        """Retrieve a tool by exact name."""
        if name not in self._tools:
            raise ToolNotFoundError(name)
        return self._tools[name]

    async def discover(
        self, *, tags: list[str] | None = None, query: str | None = None
    ) -> list[ToolDefinition]:
        """Find tools by tag filter or keyword search on name/description."""
        results = list(self._tools.values())
        if tags:
            results = [t for t in results if set(tags) & set(t.tags)]
        if query:
            q = query.lower()
            results = [
                t for t in results
                if q in t.name.lower() or q in t.description.lower()
            ]
        return results

    async def unregister(self, name: str) -> None:
        """Remove a tool from the registry."""
        self._tools.pop(name, None)
```

### Version Management

- Tools are keyed by `name`. Re-registering with a new `version` replaces the old one.
- Use semver. Breaking changes require a major version bump.
- Agents can request tools by name or by capability tags.

---

## 4. MCP Server Implementation

`tools/mcp_server.py` exposes registered tools over the MCP protocol so external
clients (other LLMs, IDE plugins, CLI tools) can call them.

### Server Setup

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

class CodeBotMCPServer:
    """Exposes CodeBot tools via MCP protocol."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry
        self._server = Server("codebot-tools")
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self._server.list_tools()
        async def list_tools() -> list[Tool]:
            definitions = await self._registry.discover()
            return [
                Tool(
                    name=d.name,
                    description=d.description,
                    inputSchema=d.parameters,
                )
                for d in definitions
            ]

        @self._server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            result = await self._service.execute_tool(name, arguments)
            return [TextContent(type="text", text=str(result))]

    async def start(self, transport: str = "stdio") -> None:
        """Start the MCP server on the given transport (stdio or sse)."""
        ...
```

### Transport Options

- **stdio** -- default for CLI integrations (Codex, Codex CLI, Gemini CLI)
- **SSE** -- for web-based clients and remote connections

### Configuration

MCP server config is typically declared in a JSON config file:

```json
{
  "mcpServers": {
    "codebot-tools": {
      "command": "python",
      "args": ["-m", "codebot.tools.mcp_server"],
      "env": {}
    }
  }
}
```

---

## 5. MCP Client Integration

`context/mcp.py` handles consuming tools from external MCP servers.

### Client Pattern

```python
from mcp.client import ClientSession

class MCPClientManager:
    """Manages connections to external MCP servers."""

    def __init__(self) -> None:
        self._sessions: dict[str, ClientSession] = {}

    async def connect(self, server_name: str, config: dict) -> None:
        """Establish a session with an external MCP server."""
        session = await self._create_session(config)
        self._sessions[server_name] = session

    async def list_remote_tools(self, server_name: str) -> list[Tool]:
        """Discover tools available on a remote MCP server."""
        session = self._sessions[server_name]
        return await session.list_tools()

    async def call_remote_tool(
        self, server_name: str, tool_name: str, arguments: dict
    ) -> Any:
        """Invoke a tool on a remote MCP server."""
        session = self._sessions[server_name]
        return await session.call_tool(tool_name, arguments)

    async def disconnect(self, server_name: str) -> None:
        """Close an MCP session."""
        session = self._sessions.pop(server_name, None)
        if session:
            await session.close()
```

### Context Bridging

MCP context is merged into the agent's context window. The `mcp.py` module handles:
- Fetching tool lists from connected MCP servers
- Converting MCP tool schemas to CodeBot's `ToolDefinition` format
- Forwarding tool calls from the agent to the correct MCP server
- Collecting results and feeding them back into the agent context

---

## 6. Tools Creator Agent

`agents/tools_creator_agent.py` is a specialized agent that generates new custom tools
and MCP integrations programmatically.

### Responsibilities

- Accept a natural-language description of a desired tool
- Generate the tool implementation (async execute function)
- Produce a valid JSON Schema for parameters
- Register the tool via `ToolService.create_tool()`
- Optionally scaffold an MCP server wrapper for the new tool

### Integration Flow

```
User request
  -> tools_creator_agent interprets intent
  -> generates ToolDefinition (name, schema, execute fn)
  -> calls ToolService.create_tool()
  -> tool appears in ToolRegistry
  -> MCP server exposes it automatically
```

### Usage from Other Agents

Any agent can request tool creation by delegating to the tools creator agent:

```python
await orchestrator.delegate(
    agent="tools_creator",
    task="Create a tool that queries the GitHub API for open PRs",
)
```

---

## 7. Binding Tools to Agents

Every agent extends `BaseAgent`, which provides the `register_tools()` method for
declaring which tools the agent can use.

### Pattern

```python
class MyAgent(BaseAgent):
    async def setup(self) -> None:
        # Bind specific tools by name
        await self.register_tools(["file_edit", "terminal", "git_operations"])

        # Or bind by tags (all tools tagged "code")
        await self.register_tools_by_tags(["code", "testing"])

        # Or bind remote MCP tools
        await self.register_mcp_tools(server_name="external-api")
```

### How Binding Works

1. `register_tools()` queries the `ToolRegistry` for matching tools.
2. Tool schemas are converted to the LLM's function-calling format.
3. Schemas are injected into the agent's system prompt / tool list.
4. When the LLM emits a tool call, the agent runtime routes it to `ToolService.execute_tool()`.

### CLI Agent Layer

CLI agents (Codex, Codex CLI, Gemini CLI) are integrated via a separate CLI agent
layer, not directly through the tools system. The CLI layer:
- Wraps tool calls in CLI-specific protocols
- Handles streaming output
- Manages CLI session state

---

## 8. API Endpoints for Tool Management

The server exposes REST endpoints for managing tools at runtime.

### Endpoint Reference

| Method | Path                     | Purpose                          |
|--------|--------------------------|----------------------------------|
| GET    | /api/tools               | List all registered tools        |
| GET    | /api/tools/{name}        | Get tool details and schema      |
| POST   | /api/tools               | Register a new custom tool       |
| DELETE | /api/tools/{name}        | Unregister a tool                |
| POST   | /api/tools/{name}/execute| Execute a tool with parameters   |
| GET    | /api/mcp/servers         | List connected MCP servers       |
| POST   | /api/mcp/servers         | Connect to an external MCP server|
| DELETE | /api/mcp/servers/{name}  | Disconnect an MCP server         |

### Example: Register a Tool via API

```bash
curl -X POST http://localhost:8000/api/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_custom_tool",
    "description": "Does something useful",
    "parameters": {
      "type": "object",
      "properties": {
        "input": {"type": "string"}
      },
      "required": ["input"]
    },
    "version": "1.0.0",
    "tags": ["custom"]
  }'
```

---

## 9. Testing Custom Tools

### Unit Testing a Tool

```python
import pytest
from codebot.tools.service import ToolService
from codebot.tools.registry import ToolRegistry

@pytest.fixture
async def tool_service() -> ToolService:
    registry = ToolRegistry()
    return ToolService(registry)

async def test_register_and_execute(tool_service: ToolService) -> None:
    async def my_execute(input: str) -> str:
        return f"processed: {input}"

    definition = ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters={
            "type": "object",
            "properties": {"input": {"type": "string"}},
            "required": ["input"],
        },
        execute=my_execute,
    )

    await tool_service.create_tool(definition)
    result = await tool_service.execute_tool("test_tool", {"input": "hello"})
    assert result == "processed: hello"
```

### Testing MCP Server Exposure

```python
async def test_tool_exposed_via_mcp(
    tool_service: ToolService, mcp_server: CodeBotMCPServer
) -> None:
    # Register a tool
    await tool_service.create_tool(some_tool_definition)

    # Verify it appears in MCP tool listing
    tools = await mcp_server._server.list_tools()
    names = [t.name for t in tools]
    assert "some_tool" in names
```

### Testing MCP Client Integration

```python
async def test_remote_tool_call(mcp_client: MCPClientManager) -> None:
    await mcp_client.connect("test-server", {"command": "...", "args": [...]})
    tools = await mcp_client.list_remote_tools("test-server")
    assert len(tools) > 0

    result = await mcp_client.call_remote_tool(
        "test-server", tools[0].name, {"input": "test"}
    )
    assert result is not None
```

### Test Conventions

- All test functions are `async` (use `pytest-asyncio`).
- Use fixtures for `ToolService`, `ToolRegistry`, and MCP server/client instances.
- Mock external MCP servers in integration tests.
- Validate both success paths and error cases (`ToolNotFoundError`, schema violations).
- Run with: `pytest apps/server/tests/tools/ -v --strict-markers`

## Documentation Lookup (Context7)

When implementing MCP features, use Context7 to fetch the latest MCP protocol docs:

```
mcp__plugin_context7_context7__resolve-library-id("MCP")
mcp__plugin_context7_context7__query-docs(id, "server client tool resource protocol specification")
```

The MCP specification is actively evolving. Always verify protocol messages, transport options, and tool schema formats against Context7 before implementing server/client features.
