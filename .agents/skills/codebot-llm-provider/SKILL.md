---
name: codebot-llm-provider
description: >
  How to work with CodeBot's LiteLLM proxy-first LLM abstraction layer. USE THIS SKILL
  whenever adding LLM providers, configuring model routing, implementing CLI agent bridges,
  setting up cost tracking, fallback chains, or offline mode. Covers the LiteLLM proxy
  architecture, RouteLLM cost-quality routing, Langfuse observability, provider strategy,
  CLI Agent Bridge (Codex SDK, Codex, Gemini), DuckDB cost analytics, token budgets,
  and testing patterns. Trigger for: LLM integration, provider config, model routing,
  cost tracking, CLI agents, offline mode, LiteLLM, RouteLLM, Langfuse.
globs:
  - "apps/server/src/codebot/llm/**/*.py"
  - "apps/server/src/codebot/cli_agents/**/*.py"
  - "configs/providers/**/*.yaml"
---

# CodeBot LLM Provider Integration

## Core Architecture: Two Execution Paths

CodeBot uses **two distinct paths** for LLM-powered work. This is the most
important architectural distinction in the LLM layer:

```
CodeBot Agent
    │
    ├── PATH 1: LLM Gateway (API models for reasoning)
    │   Agent -> LiteLLM Proxy -> Provider SDK -> Cloud/Local API
    │               |
    │               +-> RouteLLM (cost-quality routing)
    │               +-> Langfuse (observability callback)
    │               +-> DuckDB (cost analytics)
    │
    └── PATH 2: Direct CLI Agent Integration (autonomous coding)
        Agent -> Codex Agent SDK    (in-process, full agent)
        Agent -> OpenAI Codex CLI         (subprocess, autonomous coder)
        Agent -> Google Gemini CLI        (subprocess, long-context coder)
```

### Path 1: LLM Gateway (LiteLLM Proxy)

For **reasoning tasks** — planning, analysis, review, brainstorming. Agents that
think but don't directly edit files. Used in stages S0-S4, S6, S9.

- Unified API for 100+ providers (one interface, swap models freely)
- Cost tracking and budgets enforced at the proxy
- RouteLLM dynamically routes easy tasks to cheaper models (30-50% cost reduction)
- Langfuse callback provides LLM observability
- No vendor lock-in: change providers in config, not code

### Path 2: Direct CLI Agent Integration

For **autonomous coding tasks** — implementation, testing, debugging. Agents that
read, write, edit files and run shell commands. Used in stages S5, S7, S8.

- Codex, Codex CLI, and Gemini CLI are integrated **directly**, not through LiteLLM
- Each CLI agent manages its own LLM connection and authentication
- They bring built-in tools (file editing, shell execution, codebase search)
- CodeBot orchestrates them via the CLIAgentRunner interface
- Isolation via git worktrees — each CLI agent works in its own worktree

---

## Project Layout

```
apps/server/src/codebot/llm/
  proxy.py           # LiteLLM proxy client (all agents call this)
  config.py          # Proxy configuration loader
  router.py          # RouteLLM integration + task-based routing
  fallback.py        # Fallback chain with circuit breaker
  budget.py          # Token budget management per agent/project
  cost.py            # DuckDB-backed cost analytics
  observability.py   # Langfuse callback integration

apps/server/src/codebot/cli_agents/
  runner.py          # CLIAgentRunner base class
  Codex.py     # Codex agent (SDK integration)
  codex.py           # OpenAI Codex CLI agent (subprocess)
  gemini_cli.py      # Gemini CLI agent (subprocess)
  output_parser.py   # Unified output parsing
  session.py         # Agent session management

configs/providers/
  litellm_config.yaml  # LiteLLM proxy model definitions
  routing.yaml         # RouteLLM and task-based routing rules
  budgets.yaml         # Per-agent and per-project token budgets
```

---

## 1. LiteLLM Proxy Configuration

The LiteLLM proxy runs as a dedicated service (in docker-compose for dev, standalone
for production). All model definitions live in YAML config.

```yaml
# configs/providers/litellm_config.yaml
model_list:
  - model_name: "Codex-sonnet"
    litellm_params:
      model: "anthropic/Codex-sonnet-4-20250514"
      api_key: "os.environ/ANTHROPIC_API_KEY"
      max_tokens: 8192

  - model_name: "gpt-4.1"
    litellm_params:
      model: "openai/gpt-4.1"
      api_key: "os.environ/OPENAI_API_KEY"

  - model_name: "gemini-2.5-pro"
    litellm_params:
      model: "gemini/gemini-2.5-pro"
      api_key: "os.environ/GOOGLE_API_KEY"

  - model_name: "llama3-local"
    litellm_params:
      model: "ollama/llama3"
      api_base: "http://localhost:11434"

litellm_settings:
  callbacks: ["langfuse"]  # Automatic LLM observability
  success_callback: ["langfuse"]
  failure_callback: ["langfuse"]

general_settings:
  master_key: "os.environ/LITELLM_MASTER_KEY"
```

### Adding a New Provider

1. Add model entry to `configs/providers/litellm_config.yaml`
2. Set the API key environment variable
3. Restart the LiteLLM proxy
4. Update routing rules if needed

That's it. No code changes required for standard providers.

---

## 2. Model Routing Strategies

### Task-Based Routing

The router selects models based on the task type:

| Strategy | Description |
|----------|-------------|
| task-based | Match model to task type (code-gen, review, research) |
| complexity-based | Larger models for complex prompts, smaller for simple |
| privacy-based | Route sensitive data to self-hosted models only |
| cost-based | Prefer cheapest model meeting quality threshold |
| latency-based | Prefer fastest responding provider |
| fallback chains | Try providers in order until one succeeds |
| user override | Respect explicit model choice from user config |

```yaml
# configs/providers/routing.yaml
routing:
  default_strategy: task-based
  rules:
    - task: architecture
      model: Codex-sonnet
    - task: code_generation
      model: Codex-sonnet
    - task: code_review
      model: gpt-4.1
    - task: research
      model: gemini-2.5-pro  # 1M+ token context for research
    - task: quick_chat
      model: gemini-2.5-flash
    - task: sensitive_code
      strategy: privacy-based
      model: llama3-local
  fallback_order:
    - Codex-sonnet
    - gpt-4.1
    - gemini-2.5-pro
    - llama3-local
```

### RouteLLM Integration

RouteLLM sits between the agent and LiteLLM proxy, dynamically routing easy
tasks to cheaper models and hard tasks to capable models. This reduces LLM
spend by 30-50%.

```python
# apps/server/src/codebot/llm/router.py
from routellm import Controller

controller = Controller(
    routers=["mf"],  # Matrix factorization router
    strong_model="Codex-sonnet",
    weak_model="gemini-2.5-flash",
)

# RouteLLM decides which model to use based on prompt complexity
response = controller.chat.completions.create(
    model="router-mf-0.11593",  # Threshold for routing
    messages=[{"role": "user", "content": prompt}],
)
```

---

## 3. Provider Strategy

### Path 1 Providers (via LLM Gateway for reasoning)

| Provider | Best For | Models |
|----------|----------|--------|
| Anthropic | Architecture, planning, code review, complex reasoning | Opus 4.6, Sonnet 4, Haiku 3.5 |
| OpenAI | Structured output, summarization, analysis | GPT-4.1, o3, o4-mini |
| Google | Long-context analysis (1M+ tokens), research | Gemini 2.5 Pro, 2.5 Flash |
| Ollama | Privacy-sensitive, offline, development, cost-free | Llama 3, Mistral, Qwen, DeepSeek |
| LM Studio | Desktop local model testing | Various GGUF models |

These providers are accessed through the LiteLLM proxy for API-based reasoning.

### Path 2 Providers (direct integration for autonomous coding)

| CLI Agent | Package | Best For | Integration |
|-----------|---------|----------|-------------|
| Codex | `Codex-agent-sdk` | Complex coding, multi-file refactoring, debugging | SDK (in-process) |
| OpenAI Codex | `@openai/codex` CLI | Code generation, test writing, focused edits | Subprocess |
| Google Gemini CLI | `gemini` CLI | Large codebase analysis, long-context coding | Subprocess |

These agents are integrated **directly** — they bypass LiteLLM and manage their
own model connections and authentication.

---

## 4. CLI Agent Bridge

CLI agents are external coding tools that CodeBot orchestrates as autonomous
coding agents. They bypass the LiteLLM proxy because they manage their own LLM
connections. This is the **alternative to the Codex API** for tasks that need
autonomous file editing, shell execution, and codebase exploration.

```
CodeBot Pipeline Agent (e.g., BackendDevAgent in S5)
    │
    ├── Reasoning path: LiteLLM Proxy → Codex/OpenAI/Google API
    │   (planning, analysis, review — agents that think)
    │
    └── Coding path: CLI Agent Bridge → Codex / Codex / Gemini CLI
        (autonomous coding — agents that read, write, and run code)
```

### When to Use CLI Agents vs LiteLLM Proxy

| Question | LiteLLM Proxy (API) | CLI Agent Bridge |
|----------|---------------------|-----------------|
| Needs to edit files autonomously? | No | **Yes** |
| Needs to run shell commands? | No | **Yes** |
| Needs to explore/search a codebase? | No | **Yes** |
| Reasoning/analysis/review only? | **Yes** | Overkill |
| Need unified cost tracking? | **Yes** (built-in) | Separate tracking |
| Pipeline stages | S1-S4, S6, S9 | **S5, S7, S8** |

### Base Class

```python
# apps/server/src/codebot/cli_agents/runner.py
from abc import ABC, abstractmethod

class CLIAgentRunner(ABC):
    @abstractmethod
    async def start_session(self, project_path: str, config: dict) -> str:
        """Start an agent session; return session ID."""

    @abstractmethod
    async def send_prompt(self, session_id: str, prompt: str) -> str:
        """Send a prompt to the running agent and return its response."""

    @abstractmethod
    async def stop_session(self, session_id: str) -> None:
        """Gracefully terminate the agent session."""
```

---

### 4a. Codex Integration (Agent SDK)

**Package:** `pip install Codex-agent-sdk`
**Integration type:** SDK (in-process, async iterator)
**Best for:** Complex coding tasks, multi-file refactoring, debugging

Codex is integrated via the `Codex-agent-sdk` Python package, which
communicates with the Codex CLI under the hood. It provides built-in
tools (Read, Write, Edit, Bash, Glob, Grep), permission controls, subagent
spawning, and MCP server support.

```python
# apps/server/src/codebot/cli_agents/Codex.py
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AgentDefinition,
    ResultMessage,
    SystemMessage,
    CLINotFoundError,
    CLIConnectionError,
)
from .runner import CLIAgentRunner


class ClaudeCodeAgent(CLIAgentRunner):
    """Codex as an autonomous coding agent via Agent SDK."""

    async def start_session(self, project_path: str, config: dict) -> str:
        self._project_path = project_path
        self._config = config
        self._session_id: str | None = None
        return "Codex-session"

    async def send_prompt(self, session_id: str, prompt: str) -> str:
        options = ClaudeAgentOptions(
            cwd=self._project_path,
            allowed_tools=["Read", "Edit", "Write", "Bash", "Glob", "Grep"],
            permission_mode="acceptEdits",  # Auto-accept in isolated worktree
            max_turns=self._config.get("max_turns", 25),
            max_budget_usd=self._config.get("max_budget_usd", 5.0),
            system_prompt=self._config.get("system_prompt", ""),
        )

        # Resume session to preserve conversation context
        if self._session_id:
            options = ClaudeAgentOptions(resume=self._session_id)

        result_text = ""
        try:
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, SystemMessage) and message.subtype == "init":
                    self._session_id = message.data.get("session_id")
                elif isinstance(message, ResultMessage):
                    result_text = message.result
        except CLINotFoundError:
            raise RuntimeError("Codex CLI not installed")
        except CLIConnectionError as e:
            raise RuntimeError(f"Codex connection failed: {e}")

        return result_text

    async def stop_session(self, session_id: str) -> None:
        self._session_id = None
```

**Exposing CodeBot tools to Codex via MCP:**

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeSDKClient

@tool("search_codebase", "Semantic search across the project", {"query": str, "top_k": int})
async def search_codebase(args):
    results = await vector_store.query(query=args["query"], top_k=args.get("top_k", 5))
    return {"content": [{"type": "text", "text": format_results(results)}]}

codebot_mcp = create_sdk_mcp_server("codebot-tools", tools=[search_codebase])

# Use with ClaudeSDKClient for full MCP control
options = ClaudeAgentOptions(
    cwd=worktree_path,
    allowed_tools=["Read", "Edit", "Write", "Bash", "Glob", "Grep"],
    permission_mode="acceptEdits",
    mcp_servers={"codebot": codebot_mcp},
)
async with ClaudeSDKClient(options=options) as client:
    await client.query("Implement the authentication module")
    async for message in client.receive_response():
        ...
```

**Subagents for parallel S5 coding:**

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Write", "Bash", "Glob", "Grep", "Agent"],
    permission_mode="acceptEdits",
    agents={
        "frontend-dev": AgentDefinition(
            description="Frontend React/TypeScript developer",
            prompt="Implement React components with Tailwind and TypeScript strict.",
            tools=["Read", "Edit", "Write", "Glob", "Grep"],
        ),
        "test-writer": AgentDefinition(
            description="Test engineer writing pytest tests",
            prompt="Write comprehensive tests with pytest. Mock external services.",
            tools=["Read", "Edit", "Write", "Bash", "Glob", "Grep"],
        ),
    },
)
```

---

### 4b. OpenAI Codex CLI Integration (Subprocess)

**Package:** `npm install -g @openai/codex` (CLI binary)
**Integration type:** Subprocess (stdin/stdout pipe)
**Best for:** Code generation, test writing, structured output tasks

Codex CLI is integrated via subprocess. CodeBot spawns the `codex` binary,
pipes prompts via stdin, and parses structured output from stdout.

```python
# apps/server/src/codebot/cli_agents/codex.py
import asyncio
import json
from .runner import CLIAgentRunner
from .output_parser import parse_codex_output


class CodexCLIAgent(CLIAgentRunner):
    """OpenAI Codex CLI as an autonomous coding agent via subprocess."""

    BIN = "codex"

    async def start_session(self, project_path: str, config: dict) -> str:
        self._project_path = project_path
        self._config = config
        self._proc: asyncio.subprocess.Process | None = None
        return "codex-session"

    async def send_prompt(self, session_id: str, prompt: str) -> str:
        approval_mode = self._config.get("approval_mode", "auto-edit")
        model = self._config.get("model", "o4-mini")

        cmd = [
            self.BIN,
            "--approval-mode", approval_mode,  # full-auto | auto-edit | suggest
            "--model", model,
            "--quiet",                          # Suppress interactive UI
            prompt,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self._project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._build_env(),
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=self._config.get("timeout", 300),
        )

        if proc.returncode != 0:
            raise RuntimeError(
                f"Codex CLI exited with code {proc.returncode}: "
                f"{stderr.decode().strip()}"
            )

        return parse_codex_output(stdout.decode())

    async def stop_session(self, session_id: str) -> None:
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
            await self._proc.wait()
        self._proc = None

    def _build_env(self) -> dict[str, str]:
        import os
        env = os.environ.copy()
        # Codex uses OPENAI_API_KEY from environment
        # Can override model via config
        if "api_key" in self._config:
            env["OPENAI_API_KEY"] = self._config["api_key"]
        return env
```

**Codex approval modes for CodeBot:**

| Mode | Use in CodeBot | Description |
|------|---------------|-------------|
| `suggest` | S6 (QA review) | Read-only, suggests changes without applying |
| `auto-edit` | S5 (implementation) | Auto-applies file edits, asks before shell commands |
| `full-auto` | S5 (in worktree) | Full autonomy — safe inside isolated git worktree |

---

### 4c. Google Gemini CLI Integration (Subprocess)

**Package:** `npm install -g @anthropic-ai/gemini-cli` or `pip install gemini-cli`
**Integration type:** Subprocess (stdin/stdout pipe)
**Best for:** Long-context tasks (1M+ tokens), research, large codebase analysis

Gemini CLI is integrated via subprocess. Its 1M+ token context window makes it
ideal for tasks that need to ingest large portions of a codebase at once.

```python
# apps/server/src/codebot/cli_agents/gemini_cli.py
import asyncio
from .runner import CLIAgentRunner
from .output_parser import parse_gemini_output


class GeminiCLIAgent(CLIAgentRunner):
    """Google Gemini CLI as an autonomous coding agent via subprocess."""

    BIN = "gemini"

    async def start_session(self, project_path: str, config: dict) -> str:
        self._project_path = project_path
        self._config = config
        self._proc: asyncio.subprocess.Process | None = None
        return "gemini-session"

    async def send_prompt(self, session_id: str, prompt: str) -> str:
        model = self._config.get("model", "gemini-2.5-pro")
        sandbox = self._config.get("sandbox", "none")

        cmd = [
            self.BIN,
            "--model", model,
            "--sandbox", sandbox,  # none | docker | local
            "--non-interactive",   # Non-interactive mode for subprocess
            "--prompt", prompt,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self._project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._build_env(),
        )

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=self._config.get("timeout", 600),  # Longer for large context
        )

        if proc.returncode != 0:
            raise RuntimeError(
                f"Gemini CLI exited with code {proc.returncode}: "
                f"{stderr.decode().strip()}"
            )

        return parse_gemini_output(stdout.decode())

    async def stop_session(self, session_id: str) -> None:
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
            await self._proc.wait()
        self._proc = None

    def _build_env(self) -> dict[str, str]:
        import os
        env = os.environ.copy()
        if "api_key" in self._config:
            env["GOOGLE_API_KEY"] = self._config["api_key"]
        return env
```

**Gemini sandbox modes for CodeBot:**

| Mode | Use in CodeBot | Description |
|------|---------------|-------------|
| `none` | S2 (research) | No file access, analysis/research only |
| `local` | S5 (implementation) | Direct file access in worktree |
| `docker` | S5 (untrusted code) | Sandboxed execution in Docker container |

---

### 4d. Session Manager (CLI Agent Routing)

The session manager routes coding tasks to the appropriate CLI agent based
on task type, model preference, and availability:

```python
# apps/server/src/codebot/cli_agents/session.py
from .Codex import ClaudeCodeAgent
from .codex import CodexCLIAgent
from .gemini_cli import GeminiCLIAgent


CLI_AGENTS = {
    "Codex": ClaudeCodeAgent,
    "codex": CodexCLIAgent,
    "gemini": GeminiCLIAgent,
}

# Default agent selection by pipeline stage
STAGE_DEFAULTS = {
    "S2_research": "gemini",       # 1M+ context for research
    "S5_implementation": "Codex",  # Best autonomous coding
    "S5_tests": "codex",           # Strong test generation
    "S7_testing": "codex",         # Test execution and fixing
    "S8_debug": "Codex",     # Complex debugging
}
```

### Adding a New CLI Agent

1. Create `apps/server/src/codebot/cli_agents/<name>.py`
2. Subclass `CLIAgentRunner`, implement `start_session`, `send_prompt`, `stop_session`
3. Choose integration: SDK (like Codex) or subprocess (like Codex/Gemini)
4. Add output parsing rules in `output_parser.py`
5. Register in `session.py` `CLI_AGENTS` dict and `STAGE_DEFAULTS`
6. Configure token budget limits in `budget.py`

---

## 5. Observability: Langfuse Integration

Langfuse provides LLM observability automatically via LiteLLM's callback system.
No per-agent instrumentation needed.

What Langfuse tracks:
- Every LLM call (prompt, response, tokens, latency, cost)
- Per-agent and per-pipeline-run traces
- Model performance comparison
- Cost breakdown by agent, model, and task type
- Error rates and retry patterns

Configuration is in the LiteLLM config (see section 1). Langfuse runs as a
self-hosted service to avoid sending generated code to third parties.

---

## 6. Cost Tracking and Analytics

### DuckDB Cost Aggregation

After every LLM call, token usage is recorded. DuckDB provides in-process
OLAP analytics for cost dashboards.

```python
# apps/server/src/codebot/llm/cost.py
import duckdb

class CostTracker:
    def __init__(self, db_path: str = "costs.duckdb"):
        self.conn = duckdb.connect(db_path)

    async def record_usage(
        self,
        agent: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        project_id: str,
    ) -> None:
        ...

    async def get_project_cost(self, project_id: str) -> float:
        """Aggregate cost for a project across all agents and models."""
        ...

    async def get_agent_cost_breakdown(self, project_id: str) -> dict:
        """Cost per agent for a project."""
        ...
```

### Token Budget Management

Budgets are enforced per agent and per project:

- Before each request, check remaining tokens
- If over budget: reject or downgrade to a cheaper model
- Budgets reset on configurable schedule

```python
from codebot.llm.budget import BudgetManager

budget = BudgetManager()
budget.set_limit(agent="backend_dev", project="myapp", max_tokens=1_000_000)

if not budget.can_spend(agent="backend_dev", project="myapp", estimated_tokens=4000):
    # Switch to cheaper model or reject
    ...
```

---

## 7. Fallback Chain with Circuit Breaker

`fallback.py` manages ordered provider lists with automatic failover.

Key behaviors:
- On provider error (rate limit, timeout, auth failure), advance to next
- Circuit breaker: after N consecutive failures, skip provider for cooldown period
- Offline mode: cloud providers automatically excluded
- Each provider in chain can have a different model

```python
from codebot.llm.fallback import FallbackChain

chain = FallbackChain([
    ("Codex-sonnet", {"timeout": 30}),
    ("gpt-4.1", {"timeout": 30}),
    ("llama3-local", {"timeout": 60}),
])
result = await chain.complete(prompt)
```

---

## 8. Offline Mode

When CodeBot operates without internet:

- Only Ollama/LM Studio models are available
- LiteLLM proxy routes 100% to local providers
- CLI agents requiring cloud APIs are disabled
- RouteLLM is bypassed (single local model)
- GPU/CPU detection suggests appropriate quantized models

---

## 9. Testing LLM Integrations

### Mock at the LiteLLM Proxy Boundary

Since all calls go through LiteLLM, mock at that level:

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_litellm():
    with patch("litellm.acompletion") as mock:
        mock.return_value = MockResponse(content="mocked response")
        yield mock

async def test_agent_uses_proxy(mock_litellm):
    # Agent calls go through litellm.acompletion, which is mocked
    result = await agent.execute(task)
    mock_litellm.assert_called_once()
```

### CLI Agent Tests (Mock Subprocess)

```python
async def test_codex_agent_send_prompt():
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.stdout.read.return_value = b"agent output"
        mock_exec.return_value = mock_proc

        agent = CodexAgent()
        await agent.start_session("/tmp/project", {})
        result = await agent.send_prompt("sid", "fix the bug")
        assert result == "agent output"
```

### Integration Tests (Recorded Fixtures)

Record real API responses once, replay in CI:

```python
@pytest.mark.vcr("fixtures/litellm_complete.yaml")
async def test_litellm_proxy_complete():
    result = await litellm.acompletion(
        model="Codex-sonnet",
        messages=[{"role": "user", "content": "Say hello"}],
    )
    assert "hello" in result.choices[0].message.content.lower()
```

---

## Quick Reference

### Path 1: LLM Gateway (API reasoning)

| Task | Where |
|------|-------|
| Add a new API provider | `configs/providers/litellm_config.yaml` |
| Change routing rules | `configs/providers/routing.yaml` |
| Adjust token budgets | `configs/providers/budgets.yaml` + `llm/budget.py` |
| View cost analytics | `llm/cost.py` (DuckDB queries) |
| Configure Langfuse | LiteLLM config `callbacks: ["langfuse"]` |
| Enable offline mode | Set `CODEBOT_OFFLINE=1`, ensure Ollama running |
| Debug API calls | Check Langfuse traces or `LITELLM_LOG=DEBUG` |
| Mock API in tests | Mock `litellm.acompletion` (single mock point) |

### Path 2: Direct CLI Agent Integration (autonomous coding)

| Task | Where |
|------|-------|
| Add Codex agent | `cli_agents/Codex.py` (Agent SDK) |
| Add Codex CLI agent | `cli_agents/codex.py` (subprocess) |
| Add Gemini CLI agent | `cli_agents/gemini_cli.py` (subprocess) |
| Add a new CLI agent | `cli_agents/<name>.py` subclassing `CLIAgentRunner` |
| Expose CodeBot tools to CLI agents | MCP server via `create_sdk_mcp_server()` |
| Configure stage defaults | `cli_agents/session.py` `STAGE_DEFAULTS` |
| Mock CLI agents in tests | Mock `asyncio.create_subprocess_exec` or `claude_agent_sdk.query` |

## Documentation Lookup (Context7)

Before implementing LLM provider features, use Context7 to fetch current docs:

```
# LLM Gateway
mcp__plugin_context7_context7__resolve-library-id("LiteLLM")
mcp__plugin_context7_context7__query-docs(id, "proxy completion embedding router fallback")

# Cost-quality routing
mcp__plugin_context7_context7__resolve-library-id("RouteLLM")
mcp__plugin_context7_context7__query-docs(id, "router configuration cost quality threshold")

# Observability
mcp__plugin_context7_context7__resolve-library-id("Langfuse")
mcp__plugin_context7_context7__query-docs(id, "Python SDK trace generation span decorator")

# CLI Agent SDK
mcp__plugin_context7_context7__resolve-library-id("Codex Agent SDK")
mcp__plugin_context7_context7__query-docs(id, "query tool_use session subprocess")

# Analytics
mcp__plugin_context7_context7__resolve-library-id("DuckDB")
mcp__plugin_context7_context7__query-docs(id, "Python API aggregate window functions")
```

LiteLLM and Codex Agent SDK APIs evolve rapidly. Always check Context7 for current method signatures.
