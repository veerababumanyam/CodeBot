---
name: codebot-build-order
description: |
  Implementation build order and phased roadmap for the CodeBot autonomous multi-agent
  SDLC platform. USE THIS SKILL whenever planning implementation work, deciding what to
  build next, understanding component dependencies, or sequencing development phases.
  Covers the 6-tier dependency chain, 8-phase roadmap, critical path, and risk areas.
  Trigger for ANY task involving: build order, implementation planning, "what to build
  first", dependency tiers, phase sequencing, or roadmap questions.
---

# CodeBot Build Order & Implementation Roadmap

## Why Build Order Matters

CodeBot has ~30 agents across 11 pipeline stages with deep interdependencies. Building
components out of order creates stub-heavy code with unclear contracts, wasted rework,
and delayed validation. The build order below is derived from hard dependency chains —
a component cannot function (even in test) until its dependencies exist.

---

## 6-Tier Dependency Chain

Components must be built in tier order. A component cannot be built until all
components it depends on are at least stubbed.

```
TIER 1 — No dependencies, build first:
  - Data Layer (PostgreSQL schemas, Redis setup, LanceDB, MinIO)
  - Monorepo scaffolding (Turborepo, pyproject.toml, package.json, docker-compose.yml)
  - BaseAgent class (stub — no real LLM calls)
  - Core type definitions (shared-types lib: Node, Edge, Agent, Message schemas)

TIER 2 — Depends on Tier 1:
  - Graph Engine (DirectedGraph, Node, Edge, Scheduler, ExecutionEngine)
    [depends on: BaseAgent stub, shared types, data layer for checkpoints]
  - LLM Gateway (LiteLLM proxy, RouteLLM routing, per-provider adapters — API reasoning only)
    [depends on: shared types only]
  - Context Manager (L0/L1/L2 tiers, LanceDB/Qdrant integration)
    [depends on: data layer, Tree-sitter indexer]
  - Event Bus (NATS JetStream integration)
    [depends on: NATS broker running in docker-compose]

TIER 3 — Depends on Tier 2:
  - CLI Agent Bridge (Codex Agent SDK, Codex CLI subprocess, Gemini CLI subprocess)
    [depends on: Worktree Manager — direct integration, does NOT go through LLM Gateway]
  - Worktree Manager
    [depends on: data layer (task IDs for branch naming)]
  - Sandbox Manager
    [depends on: Docker available in environment]
  - Security Pipeline (scanner wrappers, aggregator, quality gate)
    [depends on: data layer for finding storage]

TIER 4 — Depends on Tier 3:
  - Agent implementations (~30 agents, starting with critical path)
    [depends on: BaseAgent, Graph Engine, LLM Layer, CLI Bridge, Context Mgr]
  - Pipeline Manager (phase coordination, preset loading)
    [depends on: Graph Engine, Agent Pool, Checkpoint Manager]
  - FastAPI API Gateway + WebSocket
    [depends on: Pipeline Manager, Event Bus]

TIER 5 — Depends on Tier 4:
  - Web Dashboard (React)
    [depends on: FastAPI endpoints + WebSocket streaming functional]
  - CLI Interface (TypeScript)
    [depends on: FastAPI REST API functional]
  - IDE Extensions
    [depends on: CLI Interface]

TIER 6 — Integration and polish:
  - End-to-end pipeline runs (all stages connected)
  - Deployment agent (S10) + CI/CD generation
  - SDK publishing (Python + TypeScript)
```

---

## Critical Path

The shortest path to a first working end-to-end pipeline:

```
Data Layer → Graph Engine → LLM Gateway + CLI Agent Bridge → Context Manager →
BaseAgent → Core Agents (Orchestrator, Planner, Backend Dev, Tester, Debugger) →
Pipeline Manager → FastAPI → CLI → first end-to-end run
```

This path delivers a working vertical slice before investing in the remaining 25 agents.

---

## 8-Phase Implementation Roadmap

### Phase 1: Foundation and Scaffolding
**Delivers:** Working monorepo with Docker Compose dev stack, database schemas,
BaseAgent stub, shared type definitions.

**Stack:** Turborepo, pyproject.toml, package.json, docker-compose.yml (PostgreSQL,
Redis, NATS, LanceDB), SQLAlchemy models, Alembic migrations.

**Research needed:** None — standard patterns.

### Phase 2: Graph Engine and Core Infrastructure
**Delivers:** Working DAG execution engine, LLM routing with fallback chains,
L0/L1/L2 context assembly, NATS event bus.

**Stack:** LangGraph, LiteLLM, NATS JetStream, LanceDB/Qdrant, Tree-sitter,
asyncio.TaskGroup.

**Research needed:** LangGraph cyclical graph support for S8 debug loop.

### Phase 3: Agent Framework and Critical-Path Agents
**Delivers:** Working agent lifecycle, git worktree isolation, CLI agent bridge
(Codex SDK), sandbox execution, first end-to-end pipeline from PRD to tested code.

**Agents built:** Orchestrator, Planner, Backend Dev, Tester, Debugger (5 of 30).

**Stack:** BaseAgent, GitPython, Docker SDK, Codex Agent SDK, Codex CLI, pytest.

**Research needed:** Codex SDK integration, Codex CLI subprocess management.

### Phase 4: Pipeline Manager and SDLC Stages
**Delivers:** Full SDLC pipeline (S0-S10), checkpoint-based resume, YAML presets
(full/quick/review-only), SAST security scanning, documentation generation.

**Agents built:** Remaining ~25 agents added incrementally.

**Stack:** Temporal, Semgrep, Gitleaks, pipeline YAML configs.

**Research needed:** LangGraph + Temporal boundary (graph execution vs durable orchestration).

### Phase 5: API Gateway and CLI
**Delivers:** REST API for all pipeline operations, WebSocket streaming, CLI with
all core commands.

**Stack:** FastAPI, Socket.IO, Node.js 22 LTS, TypeScript CLI.

**Research needed:** None — standard FastAPI patterns.

### Phase 6: Web Dashboard
**Delivers:** Pipeline DAG visualization (React Flow), agent activity cards,
code review viewer (Monaco), terminal output (xterm.js), cost tracker.

**Stack:** React, Vite, TypeScript, Tailwind, Shadcn/ui, React Flow, Monaco,
Zustand, TanStack Query.

**Research needed:** None — standard React patterns.

### Phase 7: Advanced Features and Hardening
**Delivers:** Full security pipeline (DAST + SCA), expanded test types, React
Native mobile generation, multi-cloud deployment (S10).

**Stack:** OWASP ZAP, Playwright, k6, axe-core, Pact, Pulumi, OpenTofu.

**Research needed:** Multi-cloud IaC generation across 8+ providers.

### Phase 8: Ecosystem and Polish
**Delivers:** Plugin architecture, cross-project learning, full observability,
IDE integrations, published SDKs.

**Stack:** pluggy, Langfuse, OpenTelemetry, SigNoz, VS Code extension API.

---

## Phase Ordering Rationale

- **Bottom-up mirrors architecture tiers:** Foundation → Engine → Agents → Pipeline →
  Surfaces → Integration. Building out of order creates stub-heavy code.
- **First end-to-end run in Phase 3:** By focusing on just 5 critical-path agents,
  the team validates the entire execution pipeline before building the remaining 25.
  This is the single most important risk-reduction decision.
- **Security shifts left:** SAST in Phase 4, not deferred to a late hardening phase.
- **Dashboard after API:** Building the dashboard after the API is stable avoids
  wasted frontend effort on moving API contracts.

---

## Risk Areas Requiring Deep Research

| Phase | Risk | Why |
|-------|------|-----|
| Phase 2 | LangGraph cyclical graphs | S8 debug loop needs cycles; docs cover basic cases, not experiment-loop pattern |
| Phase 3 | Codex SDK integration | Relatively new SDK; error handling and subprocess lifecycle need validation |
| Phase 4 | LangGraph + Temporal boundary | Both handle workflow state; division of responsibility needs prototyping |
| Phase 7 | Multi-cloud deployment | 8+ providers with different deployment models and API surfaces |

## Phases With Standard Patterns (Skip Research)

- **Phase 1:** Monorepo setup, Docker Compose, SQLAlchemy — well-documented
- **Phase 5:** FastAPI REST + WebSocket — extensive docs, mature ecosystem
- **Phase 6:** React + Vite + React Flow — rich community examples

---

## Quick Decision Guide

| Question | Answer |
|----------|--------|
| What do I build first? | Phase 1: monorepo + data layer + docker-compose |
| When can I run a pipeline end-to-end? | Phase 3 (after 5 critical-path agents) |
| When should I build the dashboard? | Phase 6 (after API is stable in Phase 5) |
| When do I add security scanning? | Phase 4 (SAST with pipeline stages, not deferred) |
| When do I add deployment (S10)? | Phase 7 (after pipeline produces quality code) |
| When do I add the plugin system? | Phase 8 (after internal agent API stabilizes) |
