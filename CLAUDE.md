# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeBot is an autonomous, end-to-end software development platform powered by a graph-centric multi-agent system of ~30 specialized AI agents. It transforms natural language ideas/PRDs into fully tested, reviewed, secured, and optionally cloud-deployed applications across web, mobile, and backend platforms.

**Current state**: v1.0 complete — full implementation across 12 phases with ~280 source files and ~43K lines of code.

## Development Commands

### Python (Backend)
- `uv sync` — install all Python dependencies
- `uv run pytest` — run test suite
- `uv run ruff check .` — lint Python code
- `uv run ruff format .` — format Python code
- `uv run mypy --strict apps/server/` — strict type checking

### Node (Dashboard)
- `pnpm install` — install all Node dependencies
- `pnpm -F dashboard dev` — start dashboard in dev mode
- `pnpm -F dashboard build` — production build
- `pnpm -F dashboard test` — run dashboard tests

### Docker
- `docker-compose up -d` — start local stack (PostgreSQL, Redis, NATS)

### Database
- `uv run alembic upgrade head` — apply all pending migrations
- `uv run alembic revision --autogenerate -m "description"` — create a new migration

## Architecture Summary

### Core Paradigm
Built on the **MASFactory framework** (arXiv:2603.06007): multi-agent workflows modeled as directed computation graphs where nodes execute agents/sub-workflows and edges encode dependencies and message passing.

### 11-Stage SDLC Pipeline
Agents are organized into pipeline stages (S0–S10):
- **S0** Project Initialization → **S1** Brainstorming → **S2** Research → **S3** Architecture & Design → **S4** Planning → **S5** Implementation → **S6** Quality Assurance → **S7** Testing → **S8** Debug & Fix → **S9** Documentation → **S10** Deployment *(optional)*

Stages S3–S6 support parallel agent execution. S10 is opt-in.

### Tech Stack (Planned)
- **Backend/Orchestration**: Python 3.12+, FastAPI, SQLAlchemy, asyncio with TaskGroup
- **Dashboard**: React (Vite), TypeScript 5.5+, Tailwind CSS, Zustand state management
- **CLI**: TypeScript (Node.js 22 LTS or Bun)
- **Package managers**: `uv` (Python), `pnpm` (Node.js)
- **Monorepo**: Turborepo
- **Linting/Formatting**: `ruff` (Python), TypeScript strict mode
- **Type checking**: `mypy` strict (Python), `pyright` accepted
- **Database**: PostgreSQL (state/config), Redis (cache/pubsub), ChromaDB (vector store)
- **Optional Go**: Reserved for performance-critical components (context DB, vector ops)

### Planned Repository Layout
```
codebot/
├── apps/
│   ├── server/          # FastAPI backend (Python) — main.py entrypoint
│   ├── dashboard/       # React web dashboard (Vite + TypeScript)
│   └── cli/             # CLI application (TypeScript)
├── libs/
│   ├── agent-sdk/       # Agent base classes and tools (Python)
│   ├── shared-types/    # Shared TypeScript types
│   └── graph-engine/    # Graph execution engine (Python)
├── sdks/
│   ├── python/          # Python client SDK
│   └── typescript/      # TypeScript client SDK
├── configs/             # YAML configs for pipelines, providers, templates, security
├── docker-compose.yml   # Local development stack
├── Makefile             # Common commands
├── pyproject.toml       # Python workspace root
├── package.json         # Node.js workspace root
└── turbo.json           # Turborepo config
```

### Key Architectural Subsystems
- **Agent Graph Engine** (`server/src/codebot/graph/`): DAG execution with node types — AGENT, SUBGRAPH, LOOP, SWITCH, HUMAN_IN_LOOP, PARALLEL, MERGE, CHECKPOINT, TRANSFORM
- **Multi-LLM Abstraction** (`server/src/codebot/llm/`): Provider-agnostic layer supporting OpenAI, Anthropic, Google, Mistral, DeepSeek, plus self-hosted (Ollama, vLLM, LocalAI). Intelligent routing by task type, complexity, privacy, cost, and latency
- **CLI Agent Integration** (`server/src/codebot/cli_agents/`): Delegates coding to Claude Code, OpenAI Codex CLI, Gemini CLI via subprocess/SDK
- **Context Management** (`server/src/codebot/context/`): 3-tier system (L0/L1/L2), vector store, Tree-sitter code indexing, context compression
- **Security Pipeline** (`server/src/codebot/security/`): Semgrep, SonarQube, Trivy, Gitleaks, ScanCode/ORT
- **Collaboration** (`server/src/codebot/collaboration/`): CRDT-based real-time collaboration with conflict resolution
- **Agent implementations** (`server/src/codebot/agents/`): ~30 agents, all inheriting from `base.py` BaseAgent

### Agent Isolation Model
Each coding agent works in an isolated **git worktree** to prevent conflicts. Agents communicate through the graph engine's typed message passing, not direct file access.

## Code Style

### Python
- Format with `ruff format`, lint with `ruff check`
- Type check with `mypy --strict`
- Use dataclasses with `slots=True` and `kw_only=True`
- Async-first: use `asyncio.TaskGroup` for concurrency
- Use `ExceptionGroup` for structured error handling
- Use Pydantic v2 for all API request/response schemas
- Docstrings: Google style

### TypeScript
- Strict mode with `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`
- ESM only — no CommonJS
- Tailwind CSS utilities for styling (no custom CSS unless necessary)
- Zustand for client state management
- TanStack Query for server state and data fetching

### Naming Conventions
- **Python**: `snake_case` for functions, variables, modules; `PascalCase` for classes
- **TypeScript**: `camelCase` for functions and variables; `PascalCase` for React components, types, and interfaces
- **Python files**: lowercase with underscores (e.g., `agent_runner.py`)
- **TypeScript component files**: lowercase with hyphens (e.g., `pipeline-view.tsx`)

## Architecture Rules

- All agents must extend `BaseAgent` from `apps/server/src/codebot/agents/base.py`
- All agents are wrapped in `AgentNode` for graph execution
- Context management uses 3 tiers: **L0** (always in context), **L1** (phase-scoped), **L2** (on-demand retrieval)
- Agent isolation via git worktrees — never share working directories between agents
- Pipeline phases use entry/exit gates with human approval support
- Event bus (NATS) for inter-agent messaging — no direct calls between agents
- `SharedState` for graph-level data flow between nodes
- Security scans must pass quality gates before code moves to the next pipeline phase
- Agent configurations are YAML-declarative (in `configs/`)
- Pipeline configs support three presets: `full.yaml`, `quick.yaml`, `review-only.yaml`
- SOC 2 compliance checks run as part of SecurityOrchestrator fan-out when enabled

## Testing Conventions

### Test Organization
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- End-to-end tests: `tests/e2e/`

### Frameworks and Tools
- **Python**: pytest + `httpx.AsyncClient` for API tests
- **Dashboard**: Vitest + React Testing Library

### Rules
- Mock LLM providers in tests — never call real APIs
- Minimum coverage thresholds: line >= 80%, branch >= 70%, function >= 85%

## Key Dependencies

### Backend
FastAPI, LangGraph, Temporal, SQLAlchemy 2.0, Pydantic v2, NATS, Redis, LanceDB/Qdrant

### Frontend
React, Vite, Tailwind 4, Shadcn/ui, Zustand 5, TanStack Query, React Flow, Monaco Editor, xterm.js, Socket.IO, Yjs

### Tooling and Security
Semgrep, Trivy, Gitleaks, SonarQube, GitPython

## Documentation Lookup (Context7)

Use the **Context7 MCP server** to fetch up-to-date documentation and code examples for any library before implementing. This ensures you use current APIs, not stale training data.

### Workflow
1. **Resolve the library**: `mcp__plugin_context7_context7__resolve-library-id` with the library name
2. **Query docs**: `mcp__plugin_context7_context7__query-docs` with the resolved ID and your question

### When to Use Context7
- Before implementing with any library from the tech stack (FastAPI, Pydantic v2, SQLAlchemy 2.0, LangGraph, etc.)
- When unsure about API signatures, configuration options, or migration patterns
- When a library has had recent breaking changes (Pydantic v1→v2, SQLAlchemy 1.x→2.0, Tailwind 3→4)
- When implementing patterns with libraries you haven't used recently

### Key Libraries to Look Up
| Domain | Libraries |
|--------|-----------|
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, NATS |
| Graph/Orchestration | LangGraph, Temporal |
| LLM | LiteLLM, Claude Agent SDK, RouteLLM, Langfuse |
| Frontend | React, Vite, Tailwind CSS 4, Zustand, TanStack Query, Shadcn/ui, React Flow |
| Data | LanceDB, Qdrant, DuckDB, LlamaIndex |
| Security | Semgrep, Trivy, Gitleaks |
| Testing | pytest, Vitest, httpx |

## Documentation Map

| Document | Purpose |
|---|---|
| `docs/prd/PRD.md` | Product requirements (v2.4) — capabilities, user personas, pipeline stages |
| `docs/architecture/ARCHITECTURE.md` | C4 model diagrams, 5-layer architecture, all subsystem designs |
| `docs/design/SYSTEM_DESIGN.md` | Agent graph engine, agent specifications, pipeline orchestration |
| `docs/design/PROJECT_STRUCTURE.md` | Complete planned file/directory layout |
| `docs/design/DATA_MODELS.md` | Pydantic/SQLAlchemy data model schemas |
| `docs/design/AGENT_CATALOG.md` | Detailed specs for all ~30 agents |
| `docs/api/API_SPECIFICATION.md` | REST API endpoint definitions |
| `docs/workflows/AGENT_WORKFLOWS.md` | Agent workflow orchestration per pipeline stage |
| `docs/technical/TECHNICAL_REQUIREMENTS.md` | Runtime versions, dependencies, security, infra requirements |
| `docs/refernces/RESEARCH_SUMMARY.md` | Technology research findings |
