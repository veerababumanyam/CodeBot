---
name: CodeBot Project Overview & Navigation
description: |
  Quick-reference skill for the CodeBot autonomous software development platform.
  Triggers when working on CodeBot, navigating its codebase, understanding its
  architecture, finding files, or consulting documentation. Covers project structure,
  documentation index, conventions, agent pipeline, and common workflows.
globs:
  - "apps/**"
  - "libs/**"
  - "sdks/**"
  - "configs/**"
  - "docs/**"
---

# CodeBot Project Overview & Navigation

## What Is CodeBot

CodeBot is an autonomous, end-to-end software development platform. It orchestrates
**30 AI agents** across an **11-stage pipeline** (S0-S10) to take a project from idea
to deployed code. Built on the MASFactory framework (arXiv:2603.06007): multi-agent
workflows modeled as directed computation graphs.

---

## Repository Layout

This is a **Turborepo monorepo** managed with `uv` (Python) and `pnpm` (Node.js).

```
codebot/
  apps/
    server/              # FastAPI Python backend (core platform)
      src/codebot/
        main.py          # FastAPI entrypoint
        graph/           # Agent Graph Engine (DAG runtime, nodes, edges, scheduler)
        pipeline/        # SDLC Pipeline Manager (phase coordination, presets, checkpoints)
        agents/          # ~30 specialized agent implementations (all extend BaseAgent)
        llm/             # Multi-LLM Abstraction (LiteLLM proxy, routing, cost tracking)
        cli_agents/      # CLI Agent Bridge (Codex SDK, Codex, Gemini subprocess)
        context/         # 3-Tier Context Management (L0/L1/L2, vector store, Tree-sitter)
        worktree/        # Git Worktree Manager (per-agent isolation)
        sandbox/         # Sandbox Manager (Docker containers, live preview)
        security/        # Security Pipeline (Semgrep, Trivy, Gitleaks, quality gate)
        events/          # Event Bus (NATS JetStream pub/sub)
        api/             # FastAPI routers (projects, runs, agents, WebSocket)
    dashboard/           # React TypeScript dashboard (operator UI)
      src/
        components/      # Pipeline view, agent cards, code viewer, etc.
        stores/          # Zustand state slices
        api/             # REST + WebSocket client
    cli/                 # TypeScript CLI (Node.js 22 LTS or Bun)
      src/commands/      # init, brainstorm, plan, start, status, review, deploy, config
  libs/
    agent-sdk/           # Python agent base classes and tool bindings
    graph-engine/        # Core DAG primitives (importable by server)
    shared-types/        # TypeScript types shared between dashboard and CLI
  sdks/
    python/              # Python client SDK (publish to PyPI)
    typescript/          # TypeScript client SDK (publish to npm)
  configs/               # YAML-declarative configs (pipelines, agents, providers)
    pipelines/           # full.yaml, quick.yaml, review-only.yaml
    agents/              # Per-agent role templates
    providers/           # LLM provider routing configs
  docker-compose.yml     # Local dev: PostgreSQL, Redis, NATS, LanceDB, LiteLLM, SigNoz
  Makefile               # Common commands
  pyproject.toml         # Python workspace root (uv)
  package.json           # Node.js workspace root (pnpm)
  turbo.json             # Turborepo build pipeline
```

---

## 5-Layer Architecture

```
Layer 5 — INTERACTION:   Dashboard (React/Vite) | CLI (TypeScript) | IDE Extensions
Layer 4 — PROTOCOL:      FastAPI + Socket.IO | WebSocket Event Bus | REST API | NATS
Layer 3 — COMPONENT:     ~30 Agents | Composed Graphs | Node Templates
Layer 2 — ENGINE:        Graph Engine (DAG) | Task Scheduler | Pipeline Manager | Checkpoint
Layer 1 — FOUNDATION:    LLM Abstraction (LiteLLM) | Context Mgr | Worktree | Sandbox | Security | Data
```

---

## Documentation Index

| Question | Document |
|----------|----------|
| What does CodeBot do? Requirements? | `docs/prd/PRD.md` (v2.5) |
| How is the system structured? | `docs/architecture/ARCHITECTURE.md` (C4 model) |
| Graph engine, agent specs, pipeline orchestration? | `docs/design/SYSTEM_DESIGN.md` |
| Every file and directory? | `docs/design/PROJECT_STRUCTURE.md` |
| Data models and schemas? | `docs/design/DATA_MODELS.md` |
| What does each agent do? | `docs/design/AGENT_CATALOG.md` |
| REST API endpoints? | `docs/api/API_SPECIFICATION.md` |
| Agent coordination and handoffs? | `docs/workflows/AGENT_WORKFLOWS.md` |
| Versions, dependencies, tech requirements? | `docs/technical/TECHNICAL_REQUIREMENTS.md` |
| Technology research findings? | `docs/refernces/RESEARCH_SUMMARY.md` |

**Research documents** (implementation planning):
- `.planning/research/ARCHITECTURE.md` — 5-layer architecture, component boundaries, build order
- `.planning/research/FEATURES.md` — Feature landscape, MVP definition, competitor analysis
- `.planning/research/STACK.md` — Full tech stack with rationale and alternatives
- `.planning/research/SUMMARY.md` — Executive summary, 8-phase roadmap, risk areas

> **Tip**: Start with PRD → ARCHITECTURE → SYSTEM_DESIGN. For implementation planning,
> check the `.planning/research/` documents.

---

## Pipeline Stages

```
S0  Init             Set up project scaffold, git repo, config
S1  Brainstorm       Ideation, requirement extraction
S2  Research         Technology research, feasibility analysis
S3  Architecture     System design (parallel: 4 agents)
S4  Planning         Task decomposition, dependency graph
S5  Implementation   Code generation (parallel: 6 worktrees)
S6  QA               Code review, lint, security scan (parallel: 5 agents)
S7  Testing          Test generation and execution
S8  Debug            Failure analysis, auto-fix loop (ExperimentLoop)
S9  Docs             Documentation generation
S10 Deploy           Build, containerize, deploy (optional — user opts in)
```

**Parallel stages**: S3 (architecture sub-agents), S5 (worktree-per-module), S6 (QA checks).

---

## Tech Stack Summary

### Backend (Python 3.12+)
- **FastAPI** — HTTP + WebSocket API
- **LangGraph** — Agent graph orchestration (DAG with cycles)
- **Temporal** — Durable workflow execution (survives crashes)
- **LiteLLM** — LLM gateway for API-based reasoning (100+ providers, cost tracking)
- **Codex Agent SDK** — Direct integration for autonomous coding (in-process)
- **Codex CLI / Gemini CLI** — Direct subprocess integration for autonomous coding
- **NATS JetStream** — Event bus (sub-ms pub/sub, at-least-once delivery)
- **SQLAlchemy 2.0** — Async ORM
- **Pydantic v2** — Rust-backed validation
- **PostgreSQL 16** — Primary database
- **Redis 7** — Cache, rate limiting
- **LanceDB** (dev) / **Qdrant** (prod) — Vector store

### Frontend (TypeScript 5.5+)
- **React 18** + **Vite 6** — SPA dashboard
- **Tailwind CSS 4** + **Shadcn/ui** — Styling
- **React Flow** + **ELKjs** — DAG visualization
- **Monaco Editor** — Code review viewer
- **xterm.js** — Terminal output streaming
- **Zustand 5** — State management
- **TanStack Query** — Server state
- **Socket.IO** — Real-time WebSocket

### Tooling
- **uv** — Python package manager (10-100x faster than pip)
- **pnpm** — Node package manager (strict, workspace-aware)
- **ruff** — Python lint + format (replaces Black + Flake8 + isort)
- **mypy --strict** — Python type checking
- **Biome** — TS/JS lint + format (replaces ESLint + Prettier)

---

## Key Conventions & Patterns

### Python
- Strict mypy, full type annotations, `from __future__ import annotations`
- `ruff format` + `ruff check` before commit
- Pydantic v2 `BaseModel` for all request/response schemas
- Async-first: `asyncio.TaskGroup` for concurrency
- `@dataclass(slots=True, kw_only=True)` for agent classes
- Google-style docstrings

### TypeScript
- ESM only — no CommonJS
- Strict mode: `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`
- Zustand stores per domain, normalized as `Record<string, T>`
- Tailwind utility classes (no CSS modules or styled-components)
- Socket.IO events: `domain:action` naming

### Architecture Rules
- All agents extend `BaseAgent` from `agents/base.py`
- Agents wrapped in `AgentNode` for graph execution
- Agent isolation via git worktrees — never share working directories
- API-based LLM calls go through LiteLLM proxy (reasoning, planning, review)
- CLI agents (Codex, Codex, Gemini CLI) integrate directly — they bypass the gateway
- Inter-agent messaging via NATS event bus — no direct calls between agents
- `SharedState` for graph-level data flow between nodes
- Pipeline configs are YAML-declarative in `configs/`
- Security scans run in S6 (parallel with code review), not after delivery

---

## Common Workflows

### Understanding a specific agent
1. Check `docs/design/AGENT_CATALOG.md` for the agent's specification
2. Look in `apps/server/src/codebot/agents/` for the implementation
3. See `docs/workflows/AGENT_WORKFLOWS.md` for inter-agent interactions

### Understanding the pipeline flow
1. Read `docs/design/SYSTEM_DESIGN.md` — graph engine section
2. Check orchestration code in `apps/server/src/codebot/pipeline/`
3. See `docs/workflows/AGENT_WORKFLOWS.md` for sequencing

### Working on the dashboard
1. Code in `apps/dashboard/src/`
2. State: find relevant Zustand store in `stores/`
3. Real-time: trace Socket.IO event names between dashboard and server
4. API: reference `docs/api/API_SPECIFICATION.md`

### Planning what to build next
1. Check `.planning/research/SUMMARY.md` for the 8-phase roadmap
2. Check `.planning/research/ARCHITECTURE.md` for the 6-tier dependency chain
3. Use the `codebot-build-order` skill for detailed sequencing

### Choosing a technology
1. Check `.planning/research/STACK.md` for the recommended stack with rationale
2. Use the `codebot-stack-decisions` skill for "what NOT to use" guidance
3. Check version compatibility matrix before pinning versions

---

## Quick Lookup

| Looking for... | Go to... |
|----------------|----------|
| Agent implementations | `apps/server/src/codebot/agents/` |
| Graph engine / orchestration | `apps/server/src/codebot/graph/` |
| Pipeline manager / phases | `apps/server/src/codebot/pipeline/` |
| LLM gateway (API reasoning) | `apps/server/src/codebot/llm/` |
| CLI agent bridge (coding) | `apps/server/src/codebot/cli_agents/` |
| Context engine / RAG | `apps/server/src/codebot/context/` |
| Security scanners | `apps/server/src/codebot/security/` |
| REST API routes | `apps/server/src/codebot/api/` |
| Dashboard components | `apps/dashboard/src/components/` |
| Zustand stores | `apps/dashboard/src/stores/` |
| Shared TypeScript types | `libs/shared-types/` |
| CLI tool | `apps/cli/src/commands/` |
| Pipeline YAML presets | `configs/pipelines/` |
| Agent YAML configs | `configs/agents/` |
| Docker setup | `docker-compose.yml` |
| All documentation | `docs/` |
| Research & planning | `.planning/research/` |

---

## Notes

- The documentation suite is comprehensive. Check the doc index before exploring code.
- `docs/design/PROJECT_STRUCTURE.md` has the most detailed file-by-file breakdown.
- Note the typo in the repo: `docs/refernces/` (not `references`).
- Deployment (S10) is optional — users opt in during project init.
- All LLM calls route through LiteLLM proxy for unified cost tracking.

## Documentation Lookup (Context7)

When implementing any CodeBot component, use Context7 MCP to fetch current library documentation:

```
mcp__plugin_context7_context7__resolve-library-id("<library-name>")
mcp__plugin_context7_context7__query-docs(id, "<your question>")
```

Always look up docs before using: FastAPI, Pydantic v2, SQLAlchemy 2.0, LangGraph, LiteLLM, Temporal, React, Zustand, TanStack Query, Tailwind CSS 4, Shadcn/ui, Vite, LanceDB, Qdrant, DuckDB, Semgrep, Trivy, NATS.
