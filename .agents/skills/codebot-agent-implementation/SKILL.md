---
name: CodeBot Agent Implementation
description: |
  USE THIS SKILL whenever the user wants to create a new AI agent, add an agent,
  implement an agent, extend the agent pipeline, add a new specialist, build a
  new bot, or modify existing agents in the CodeBot platform. This skill covers
  the full lifecycle of agent creation: defining the agent class, registering it
  in the enum, writing its system prompt, binding tools, wiring it into the
  LangGraph execution graph, and testing it. Apply this skill for ANY task
  involving CodeBot agents, the SDLC pipeline, agent types, BaseAgent, AgentNode,
  or the multi-agent orchestration system.
---

# How to Implement a New CodeBot Agent

CodeBot is an autonomous multi-agent software development platform with 30
specialized agents organized across an 11-stage SDLC pipeline. This skill
covers every step required to add a new agent to the platform.

## Architecture Overview

```
apps/server/src/codebot/
  agents/           # Agent implementations
    base.py         # BaseAgent abstract class
    orchestrator.py # Example: Orchestrator agent
    ...
  graph/
    node.py         # AgentNode wrapper for LangGraph
    edges.py        # Inter-agent communication edges
    pipeline.py     # Pipeline stage definitions
  llm/              # Multi-LLM abstraction layer
  context/          # 3-tier context management (L0/L1/L2)
  tools/            # Tool definitions and registries
  models/           # Data models, enums (AgentType, etc.)
```

## Step 1: Add the Agent Type to the Enum

File: `apps/server/src/codebot/models/agent_types.py`

Add a new member to the `AgentType` enum. The enum already contains 30 types
(ORCHESTRATOR, PLANNER, RESEARCHER, ARCHITECT, DESIGNER, FRONTEND_DEV,
BACKEND_DEV, MIDDLEWARE_DEV, INFRA_ENGINEER, SECURITY_AUDITOR, CODE_REVIEWER,
TESTER, DEBUGGER, DOC_WRITER, BRAINSTORM_FACILITATOR, TECH_STACK_ADVISOR,
TEMPLATE_CURATOR, DEPLOYER, COLLABORATION_MANAGER, MOBILE_DEV,
PERFORMANCE_TESTER, ACCESSIBILITY_AUDITOR, GITHUB_INTEGRATOR, SKILL_MANAGER,
HOOK_MANAGER, TOOL_BUILDER, INTEGRATION_ADAPTER, I18N_SPECIALIST,
API_DESIGNER, PROJECT_MANAGER).

```python
class AgentType(str, Enum):
    # ... existing members ...
    MY_NEW_AGENT = "my_new_agent"
```

Conventions:
- Use UPPER_SNAKE_CASE for the member name.
- The string value is the lower_snake_case equivalent.
- Keep the enum alphabetically sorted within its section if one exists.

## Step 2: Create the Agent File

File: `apps/server/src/codebot/agents/my_new_agent.py`

Every agent module follows a consistent structure:

```python
"""My New Agent -- one-line description of its purpose."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, override

from codebot.agents.base import BaseAgent
from codebot.models.agent_types import AgentType

if TYPE_CHECKING:
    from codebot.context.manager import ContextManager
    from codebot.llm.provider import LLMProvider
    from codebot.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class MyNewAgent(BaseAgent):
    """Describe what this agent does in the pipeline."""

    agent_type: AgentType = field(default=AgentType.MY_NEW_AGENT, init=False)

    # Model preference -- pick the right tier for the agent's complexity.
    # Options: "tier1" (GPT-4/Codex Opus class), "tier2" (mid), "tier3" (fast)
    model_tier: str = "tier2"

    # Retry policy
    max_retries: int = 3
    retry_backoff_seconds: float = 1.0

    @override
    def build_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        return SYSTEM_PROMPT

    @override
    async def register_tools(self, registry: ToolRegistry) -> None:
        """Bind tools this agent is allowed to use."""
        await registry.bind(self, [
            "read_file",
            "write_file",
            "search_code",
            # Add tool names relevant to this agent's responsibilities.
        ])

    @override
    async def execute(
        self,
        *,
        context: ContextManager,
        llm: LLMProvider,
    ) -> None:
        """Core execution logic for this agent."""
        # 1. Pull context from the 3-tier system.
        project_ctx = await context.get_l0()  # L0: project-level
        task_ctx = await context.get_l1()      # L1: task-level
        turn_ctx = await context.get_l2()      # L2: turn-level

        # 2. Build messages for the LLM call.
        messages = self._build_messages(turn_ctx)

        # 3. Call the LLM through the abstraction layer.
        response = await llm.chat(
            messages=messages,
            model_tier=self.model_tier,
            tools=self.bound_tools,
        )

        # 4. Process the response and update shared state.
        await self._process_response(response, context)


SYSTEM_PROMPT = """\
You are the My New Agent for the CodeBot platform.

<role>
Describe the agent's role clearly.
</role>

<responsibilities>
- Responsibility 1
- Responsibility 2
</responsibilities>

<output_format>
Describe the expected output structure.
</output_format>

<constraints>
- Always follow the project's coding standards.
- Never modify files outside your designated scope.
</constraints>
"""
```

### Key Rules for Agent Classes

- Always use `@dataclass(slots=True, kw_only=True)`.
- The `agent_type` field MUST use `init=False` with a fixed default.
- Use `@override` decorator on all methods that override `BaseAgent`.
- All I/O methods must be `async`.
- Type hints are mandatory everywhere -- the project enforces strict mypy.
- Use `from __future__ import annotations` for PEP 604 style unions.

## Step 3: Write the System Prompt

System prompts live as module-level constants in the agent file (see
`SYSTEM_PROMPT` above). Follow these guidelines:

1. **Role definition** -- State who the agent is in one sentence.
2. **Responsibilities** -- Bullet list of what the agent does.
3. **Output format** -- Describe the structure of agent output so downstream
   agents can parse it.
4. **Constraints** -- Hard rules the agent must follow.
5. **Context references** -- Tell the agent what context keys it can read/write.

Keep prompts under 2000 tokens. Use XML-style tags for sections to help the
LLM parse structure.

## Step 4: Register Tools

Tools are defined in `apps/server/src/codebot/tools/` and registered via the
`ToolRegistry`. Each agent declares which tools it needs in `register_tools()`.

```python
@override
async def register_tools(self, registry: ToolRegistry) -> None:
    await registry.bind(self, [
        "read_file",
        "write_file",
        "search_code",
        "run_terminal_command",
        "git_diff",
        # Only bind what the agent actually needs.
    ])
```

To create a NEW tool specific to this agent:

```python
# apps/server/src/codebot/tools/my_custom_tool.py

from codebot.tools.base import BaseTool, tool_definition


@tool_definition(
    name="my_custom_tool",
    description="What this tool does.",
    parameters={
        "param1": {"type": "string", "description": "..."},
    },
)
class MyCustomTool(BaseTool):
    async def execute(self, param1: str) -> str:
        # Implementation
        ...
```

Then register it in the tool registry's discovery module so it can be bound by
name.

## Step 5: Wire Into the Graph as an AgentNode

File: `apps/server/src/codebot/graph/node.py`

The graph engine wraps every agent in an `AgentNode` for LangGraph execution.

```python
from codebot.agents.my_new_agent import MyNewAgent
from codebot.graph.node import AgentNode

my_node = AgentNode(
    agent=MyNewAgent(),
    # Optional: isolated git worktree for this agent's file operations
    use_worktree=True,
    # Optional: timeout in seconds
    timeout_seconds=300,
)
```

### AgentNode Responsibilities

- Manages the agent lifecycle (init, execute, cleanup).
- Provides an isolated git worktree if `use_worktree=True`.
- Handles retries according to the agent's retry policy.
- Captures agent output into `SharedState`.
- Emits `AgentMessage` objects on the graph edges for downstream consumers.

## Step 6: Add to the Pipeline Stage

File: `apps/server/src/codebot/graph/pipeline.py`

The 11-stage pipeline is defined here. Add your agent to the appropriate stage.

```python
# Example: adding to the "Development" stage
PIPELINE_STAGES = {
    # ... earlier stages ...
    "development": PipelineStage(
        name="development",
        nodes=[
            frontend_dev_node,
            backend_dev_node,
            middleware_dev_node,
            my_new_node,          # <-- Add here
        ],
        # Agents within a stage run concurrently via asyncio TaskGroup
        parallel=True,
    ),
    # ... later stages ...
}
```

Then register the edges that connect your node to upstream/downstream nodes:

```python
from codebot.graph.edges import add_edge

# Your agent receives output from the Architect
add_edge(architect_node, my_node, channel="design_specs")

# Your agent sends output to the Code Reviewer
add_edge(my_node, code_reviewer_node, channel="code_artifacts")
```

### Choosing the Right Stage

| Stage | Purpose |
|---|---|
| 1. Intake | Requirements gathering |
| 2. Planning | Task decomposition |
| 3. Research | Codebase analysis, tech research |
| 4. Architecture | System design |
| 5. Design | UI/UX design |
| 6. Development | Code generation |
| 7. Review | Code review, security audit |
| 8. Testing | Unit, integration, performance tests |
| 9. Documentation | Docs, changelogs |
| 10. Deployment | CI/CD, infrastructure |
| 11. Management | Orchestration, collaboration |

## Step 7: Inter-Agent Communication

Agents communicate through `SharedState` and `AgentMessage`.

### SharedState

```python
# Writing to shared state (in your agent's execute method)
await context.shared_state.set(
    key="my_agent.output_key",
    value=result_data,
    scope="task",  # "project" | "task" | "turn"
)

# Reading from shared state
arch_design = await context.shared_state.get("architect.design_doc")
```

### AgentMessage

```python
from codebot.models.messages import AgentMessage

msg = AgentMessage(
    sender=self.agent_type,
    recipient=AgentType.CODE_REVIEWER,
    content=review_request,
    metadata={"priority": "high"},
)
await self.send_message(msg)
```

Namespace your shared state keys with the agent name prefix to avoid
collisions.

## Step 8: Context Management Integration

The 3-tier context system controls what information agents can access:

- **L0 (Project)** -- Repository structure, tech stack, conventions. Shared
  across all agents. Read-only for most agents.
- **L1 (Task)** -- Current task description, acceptance criteria, related
  files. Scoped to the current task being executed.
- **L2 (Turn)** -- Conversation history, intermediate results. Scoped to the
  current execution turn.

```python
async def execute(self, *, context: ContextManager, llm: LLMProvider) -> None:
    # Read project conventions (L0)
    conventions = await context.get_l0_entry("coding_conventions")

    # Read the current task (L1)
    task = await context.get_l1_entry("task_description")

    # Write turn-level output (L2)
    await context.set_l2_entry("my_agent.analysis", analysis_result)
```

When building the message list for the LLM, inject relevant context tiers:

```python
def _build_messages(self, turn_ctx: dict) -> list[dict]:
    return [
        {"role": "system", "content": self.build_system_prompt()},
        {"role": "user", "content": self._format_task(turn_ctx)},
    ]
```

## Step 9: Git Worktree Isolation

If your agent writes files, it should use an isolated git worktree so
concurrent agents do not conflict.

The `AgentNode` handles worktree creation when `use_worktree=True`. Inside the
agent, file paths are automatically resolved relative to the worktree root:

```python
# The agent does not need to manage worktrees directly.
# File tool operations are transparently scoped to the worktree.
await self.tools.write_file("src/module/new_file.py", content)
```

After execution, the graph engine merges the worktree back using a
conflict-resolution strategy configured at the pipeline level.

## Step 10: Testing

### Unit Tests

File: `apps/server/tests/agents/test_my_new_agent.py`

```python
"""Tests for MyNewAgent."""

import pytest
from unittest.mock import AsyncMock

from codebot.agents.my_new_agent import MyNewAgent
from codebot.models.agent_types import AgentType


@pytest.fixture
def agent() -> MyNewAgent:
    return MyNewAgent()


@pytest.fixture
def mock_context() -> AsyncMock:
    ctx = AsyncMock()
    ctx.get_l0.return_value = {"tech_stack": "python"}
    ctx.get_l1.return_value = {"task": "implement feature X"}
    ctx.get_l2.return_value = {}
    return ctx


@pytest.fixture
def mock_llm() -> AsyncMock:
    llm = AsyncMock()
    llm.chat.return_value = AsyncMock(content="result")
    return llm


class TestMyNewAgent:
    def test_agent_type(self, agent: MyNewAgent) -> None:
        assert agent.agent_type == AgentType.MY_NEW_AGENT

    def test_system_prompt_is_nonempty(self, agent: MyNewAgent) -> None:
        prompt = agent.build_system_prompt()
        assert len(prompt) > 100

    @pytest.mark.asyncio
    async def test_execute(
        self,
        agent: MyNewAgent,
        mock_context: AsyncMock,
        mock_llm: AsyncMock,
    ) -> None:
        await agent.execute(context=mock_context, llm=mock_llm)
        mock_llm.chat.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_tools(self, agent: MyNewAgent) -> None:
        registry = AsyncMock()
        await agent.register_tools(registry)
        registry.bind.assert_awaited_once()
```

### Integration Tests

For integration tests that exercise the agent within the graph:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_in_pipeline(graph_fixture):
    result = await graph_fixture.run_single_node("my_new_agent")
    assert result.status == "success"
    assert "my_agent.output_key" in result.shared_state
```

### Running Tests

```bash
# Unit tests only
pytest apps/server/tests/agents/test_my_new_agent.py -v

# With type checking
mypy apps/server/src/codebot/agents/my_new_agent.py --strict

# With linting
ruff check apps/server/src/codebot/agents/my_new_agent.py
ruff format --check apps/server/src/codebot/agents/my_new_agent.py
```

## Complete Checklist

1. [ ] Add `AgentType.MY_NEW_AGENT` to the enum in `models/agent_types.py`
2. [ ] Create `agents/my_new_agent.py` extending `BaseAgent`
3. [ ] Implement `build_system_prompt()`, `register_tools()`, `execute()`
4. [ ] Write the system prompt with role, responsibilities, output format,
       constraints
5. [ ] Create any custom tools in `tools/` if needed
6. [ ] Create `AgentNode` wrapper in the graph configuration
7. [ ] Add the node to the correct pipeline stage in `graph/pipeline.py`
8. [ ] Add edges connecting the node to upstream/downstream agents
9. [ ] Write unit tests in `tests/agents/test_my_new_agent.py`
10. [ ] Run mypy strict, ruff check, ruff format
11. [ ] Run the full test suite to ensure no regressions

## Common Mistakes to Avoid

- **Forgetting `slots=True, kw_only=True`** on the dataclass decorator.
- **Mutable default fields** -- use `field(default_factory=list)` not `[]`.
- **Blocking I/O** -- all file/network operations must use async. Never call
  `open()` directly; use the tool abstractions.
- **Missing `@override`** -- the project enforces override decorators.
- **Overly broad tool bindings** -- only bind tools the agent actually needs.
  The principle of least privilege applies.
- **Unprefixed shared state keys** -- always prefix with agent name to avoid
  collisions (e.g., `"my_agent.result"` not `"result"`).
- **Giant system prompts** -- keep under 2000 tokens. Move reference material
  into L0 context instead.

## Documentation Lookup (Context7)

Before implementing agents, use Context7 to fetch current docs for key libraries:

```
mcp__plugin_context7_context7__resolve-library-id("LangGraph")
mcp__plugin_context7_context7__query-docs(id, "agent node state tool binding checkpointing")

mcp__plugin_context7_context7__resolve-library-id("Pydantic")
mcp__plugin_context7_context7__query-docs(id, "BaseModel field_validator model_validator v2")

mcp__plugin_context7_context7__resolve-library-id("GitPython")
mcp__plugin_context7_context7__query-docs(id, "Repo worktree checkout branch operations")
```

Agent implementations depend on LangGraph node APIs and Pydantic v2 validation — always verify current signatures.
