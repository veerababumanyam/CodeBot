# CodeBot

## What This Is

CodeBot is an autonomous, end-to-end software development platform powered by a graph-centric multi-agent system of 30 specialized AI agents. It transforms natural language ideas/PRDs into fully tested, reviewed, secured applications across web, mobile, and backend platforms. The system covers the complete SDLC from brainstorming through documentation, with optional cloud deployment. Built on MASFactory-inspired directed computation graphs (arXiv:2603.06007) with LangGraph as the graph engine and Temporal for durable workflow orchestration.

## Core Value

A user can describe an idea in natural language and get working, tested, security-scanned code out the other end — autonomously, through a multi-agent pipeline that handles planning, architecture, implementation, QA, testing, debugging, and documentation without manual coding.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Monorepo foundation (Turborepo, uv, pnpm workspaces) — v1.0
- ✓ Shared Pydantic models + TypeScript types — v1.0
- ✓ NATS JetStream event bus — v1.0
- ✓ Docker stack (PostgreSQL, Redis, NATS) — v1.0
- ✓ Database schema (Alembic migrations) — v1.0
- ✓ Graph execution engine (LangGraph, 9 node types, parallel fan-out, checkpointing) — v1.0
- ✓ Agent framework (BaseAgent PRA cycle, 7-state FSM, YAML config, recovery strategies) — v1.0
- ✓ 30 specialized agents across 10 SDLC stages — v1.0
- ✓ Multi-LLM abstraction (task-based routing, fallback chains, cost tracking, streaming) — v1.0
- ✓ 3-tier context management (L0/L1/L2, Tree-sitter indexing, vector store, compression) — v1.0
- ✓ Pipeline orchestration (Temporal workflows, gates, presets, checkpoint/resume) — v1.0
- ✓ Vertical slice (5-agent NL-to-tested-code pipeline) — v1.0
- ✓ Security scanning cascade (Semgrep, Trivy, Gitleaks, quality gates) — v1.0
- ✓ Worktree isolation (WorktreePool, PortAllocator, BranchStrategy) — v1.0
- ✓ CLI agent adapters (Claude Code, Codex, Gemini) — v1.0
- ✓ SOC 2 compliance checker with immutable audit logging — v1.0
- ✓ FastAPI REST API with JWT auth, project/pipeline/agent endpoints — v1.0
- ✓ WebSocket real-time streaming (Socket.IO + NATS bridge) — v1.0
- ✓ React dashboard (React Flow pipeline graph, Monaco editor, xterm.js terminal) — v1.0
- ✓ TypeScript CLI (interactive project creation, pipeline control, log streaming) — v1.0
- ✓ Creator agents (Skill, Hooks, Tools) — v1.0

### Active

<!-- Next milestone scope -->

- [ ] Cross-phase integration wiring (agents→LLM, agents→context, API→Temporal, activities→registry, worktree→agent)
- [ ] Dashboard event name alignment with server-side emitter
- [ ] SonarQube integration for deeper static analysis
- [ ] S10 Cloud Deployment stage (optional, opt-in)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- S10 Cloud Deployment Automation — Deferred; users receive generated code with deployment docs. Can be triggered later on demand.
- Mobile app (native iOS/Android dashboard) — Web dashboard covers all use cases for v1
- Multi-repository orchestration — Focus on single-repo projects for v1
- Billing/payment system — Open-source, no monetization in v1
- Custom LLM fine-tuning — Use existing models via API/self-hosted

## Context

**Current state:** v1.0 shipped (2026-03-20). 44,509 LOC across Python and TypeScript. 12 phases, 36 plans executed. All subsystems built and individually tested. Cross-phase integration seams identified in audit — next milestone addresses runtime wiring.

**Codebase:**
- `apps/server/src/codebot/` — Full Python backend: agents (30), graph engine, LLM abstraction, context, pipeline, security, worktree, CLI agents, API, WebSocket
- `apps/dashboard/src/` — React dashboard with React Flow, Monaco, xterm.js, Socket.IO
- `apps/cli/src/` — TypeScript CLI with Commander.js
- `libs/agent-sdk/`, `libs/graph-engine/` — Shared agent and graph libraries
- `configs/` — YAML configs for agents, pipelines, stages, security

**Architecture paradigm:** MASFactory-inspired graph-centric multi-agent system. LangGraph for graph execution, Temporal for durable orchestration.

**Agent cognitive model:** All 30 agents follow Perception-Reasoning-Action (PRA) cycle with YAML configuration.

## Constraints

- **Open-source stack**: Prefer open-source (MIT/Apache-2) libraries and tools throughout. Avoid proprietary/vendor-locked dependencies where viable open alternatives exist.
- **Python version**: 3.12+ with strict mypy, ruff format/lint
- **TypeScript**: 5.5+ strict mode, ESM only, no CommonJS
- **Package managers**: uv (Python), pnpm (Node.js)
- **Agent isolation**: Each coding agent works in isolated git worktree
- **Communication**: Event bus (NATS) only — no direct inter-agent calls
- **LLM providers**: Must support Anthropic, OpenAI, Google, and self-hosted (Ollama) from day one
- **Testing**: Mock LLM providers in tests, never call real APIs. Coverage: line >= 80%, branch >= 70%, function >= 85%
- **Security**: All code passes Semgrep/Trivy/Gitleaks before advancing pipeline phases

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| LangGraph as graph engine | ~24.6K stars, MIT, native agent graph support, composable | ✓ Good |
| Temporal for durable workflows | ~18.9K stars, MIT, retry/checkpoint/resume built-in | ✓ Good |
| NATS JetStream for events | Lightweight, high-throughput, JetStream for persistence | ✓ Good |
| Turborepo for monorepo | Fast builds, good Python/Node hybrid support | ✓ Good |
| Defer S10 deployment | Reduces v1 scope significantly, deployment is opt-in anyway | ✓ Good |
| All 4 LLM providers in v1 | Core differentiator is provider flexibility | ✓ Good |
| Full React dashboard in v1 | Real-time visualization critical for monitoring 30 agents | ✓ Good |
| PRA cognitive cycle for agents | Structured perception-reasoning-action loop improves agent reliability | ✓ Good |
| Component-first build order | Foundation→vertical slice→breadth. Integration seams expected | ⚠️ Revisit |
| instructor + LiteLLM for structured output | Used in vertical slice agents; remaining agents need wiring | ⚠️ Revisit |

---
*Last updated: 2026-03-20 after v1.0 milestone completion*
