# Requirements: CodeBot

## Overview

**Total v1 requirements:** 39
**Categories:** 9 (INFRA, ENGINE, AGENT, LLM, CONTEXT, PIPELINE, SECURITY, SURFACE, PLATFORM)
**Priority levels:** P0 (must have for launch), P1 (should have, add when possible), P2 (nice to have, future)

## Requirements

### INFRA: Infrastructure and Foundation

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| REQ-001 | Turborepo monorepo with apps/ (server, dashboard, cli) and libs/ (agent-sdk, shared-types, graph-engine) | P0 | 1 |
| REQ-002 | Docker Compose dev stack (PostgreSQL, Redis, NATS, LanceDB/Qdrant) | P0 | 1 |
| REQ-003 | Database schemas (SQLAlchemy models, Alembic migrations) for pipeline state, agent tasks, LLM usage | P0 | 1 |
| REQ-004 | Shared type definitions (Python Pydantic models, TypeScript shared-types lib) | P0 | 1 |
| REQ-005 | Event bus (NATS JetStream) for async agent messaging and dashboard streaming | P0 | 1 |

### ENGINE: Graph Engine and Execution

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| REQ-006 | Graph-centric multi-agent orchestration engine (MASFactory-inspired DAG execution with topological sort, parallel layer execution) | P0 | 2 |
| REQ-007 | Node types: AGENT, SUBGRAPH, LOOP, EXPERIMENT_LOOP, SWITCH, HUMAN_IN_LOOP, PARALLEL, MERGE, CHECKPOINT, TRANSFORM | P0 | 2 |
| REQ-008 | Edge types: STATE_FLOW, MESSAGE_FLOW, CONTROL_FLOW with typed message passing | P0 | 2 |
| REQ-009 | Checkpoint-based pipeline resume (state snapshots after each execution layer, restart from failure point) | P0 | 2 |

### LLM: Multi-LLM Abstraction

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| REQ-010 | Multi-LLM support: Claude Code, OpenAI Codex, Google Gemini, Ollama, LM Studio via LiteLLM gateway | P0 | 2 |
| REQ-011 | Intelligent model routing (task-based, complexity-based, privacy-based, cost-based, latency-based) with fallback chains | P0 | 2 |
| REQ-012 | Cost intelligence: per-agent token tracking, per-stage costs, budget limits, cloud cost estimation | P0 | 2 |

### CONTEXT: Context Management

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| REQ-013 | 3-tier context management (L0 always-loaded, L1 on-demand, L2 deep retrieval via vector store) | P0 | 2 |
| REQ-014 | Vector store (LanceDB dev / Qdrant prod) with Tree-sitter code indexing for semantic code chunking | P0 | 2 |
| REQ-015 | Episodic memory with cross-session and cross-project learning | P1 | 8 |

### AGENT: Agent Framework and Implementations

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| REQ-016 | BaseAgent class with shared lifecycle, tool bindings, context assembly, and YAML-declarative config | P0 | 3 |
| REQ-017 | CLI agent integration (Claude Code SDK, Codex CLI subprocess, Gemini CLI subprocess) for code generation | P0 | 3 |
| REQ-018 | Git worktree isolation per coding agent (provision, execute, merge, cleanup lifecycle) | P0 | 3 |
| REQ-019 | Sandboxed code execution (Docker container per agent, resource limits, gVisor/Kata isolation) | P0 | 3 |
| REQ-020 | Critical-path agents: Orchestrator, Planner, Backend Dev, Tester, Debugger | P0 | 3 |
| REQ-021 | ~30 specialized AI agents with role-specific prompts and tool access covering all 11 SDLC stages | P0 | 4 |
| REQ-022 | Agent learning: skill creation, hook creation, tool creation, pattern library, anti-pattern registry | P1 | 8 |

### PIPELINE: SDLC Pipeline Stages

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| REQ-023 | 11-stage SDLC pipeline (S0 Project Init through S10 Deployment) with phase gates and YAML presets (full/quick/review-only) | P0 | 4 |
| REQ-024 | Brainstorming phase (S1): idea exploration, competitive analysis, feature prioritization, scope definition | P0 | 4 |
| REQ-025 | Research phase (S2): technology research, pattern discovery, dependency analysis, API discovery | P0 | 4 |
| REQ-026 | Architecture phase (S3, parallel): system architecture (C4), database design, API design, UI/UX design | P0 | 4 |
| REQ-027 | Planning phase (S4): task decomposition, dependency graphs, topological ordering, resource allocation | P0 | 4 |
| REQ-028 | Implementation phase (S5, parallel worktrees): frontend, backend, middleware, mobile, infrastructure, integrations | P0 | 4 |
| REQ-029 | Quality assurance phase (S6, parallel): code review, security audit, accessibility, i18n, performance analysis | P0 | 4 |
| REQ-030 | Testing phase (S7): unit, integration, E2E, and additional test types (performance, security, accessibility, contract, mutation) | P0 | 4 |
| REQ-031 | Debug and fix cycle (S8): root cause analysis, automated fix generation, regression testing, ExperimentLoop with keep/discard semantics (autoresearch-inspired: hypothesis → experiment branch → measure → keep if improved, discard otherwise; experiment log tracking) | P0 | 4 |
| REQ-032 | Documentation phase (S9): API docs, README, ADRs, deployment guides, runbooks | P0 | 4 |
| REQ-033 | Human-in-the-loop approval gates at configurable checkpoints | P0 | 4 |
| REQ-034 | Communication protocol: state flow, message flow, control flow, event flow, broadcast flow | P0 | 4 |
| REQ-035 | 4 project modes: greenfield, inflight, brownfield, improve (autonomous ExperimentLoop-based optimization with time/token budgets, inspired by autoresearch) | P1 | 7 |
| REQ-036 | Self-healing: automatic dependency resolution, config auto-fix, test flakiness detection, LLM fallback chains, pipeline resume from checkpoint | P0 | 4 |

### SECURITY: Security Pipeline

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| REQ-037 | SAST security scanning (Semgrep, Gitleaks) integrated into pipeline quality gates | P0 | 4 |
| REQ-038 | Agent safety guardrails: sandboxed creation, review before activation, capability boundaries | P0 | 3 |

### SURFACE: User-Facing Interfaces

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| REQ-039 | FastAPI REST API gateway with WebSocket streaming for all pipeline operations | P0 | 5 |
| REQ-040 | CLI interface (TypeScript): init, brainstorm, plan, start, status, review, deploy, config commands | P0 | 5 |
| REQ-041 | Web dashboard (React/Vite/TypeScript/Tailwind): pipeline view, agent activity, code viewer, test results, deployment status, brainstorming board, template gallery, tech stack configurator, cost tracker, knowledge base browser, architecture visualizer, git timeline | P0 | 6 |
| REQ-042 | Live preview (hot-reload, mobile viewport emulation, VNC for desktop apps) | P1 | 6 |
| REQ-043 | IDE extensions (VS Code, JetBrains, Neovim, Cursor) | P1 | 8 |

### PLATFORM: Cross-Cutting Platform Features

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| REQ-044 | Deployment phase (S10): CI/CD generation, multi-cloud (AWS, GCP, Azure, Vercel, Railway, Netlify, Fly.io, DigitalOcean), multi-environment management, rollback automation, monitoring setup | P1 | 7 |
| REQ-045 | React Native cross-platform mobile development | P1 | 7 |
| REQ-046 | Full security pipeline: DAST (OWASP ZAP), SCA (Trivy), license compliance (ORT/ScanCode) | P1 | 7 |
| REQ-047 | Full test suite expansion: E2E (Playwright), performance (k6), accessibility (axe-core), visual regression, contract (Pact), mutation (Stryker), chaos (optional) | P1 | 7 |
| REQ-048 | Responsive web design across all generated applications | P0 | 4 |
| REQ-049 | Multi-repo support with cross-repo dependency management | P1 | 7 |
| REQ-050 | Template system: Material Design, Ant Design, Tailwind UI, Shadcn/ui, Chakra UI, Bootstrap, custom | P1 | 7 |
| REQ-051 | Multi-modal input: text, images, diagrams, voice (transcribed), video walkthroughs, reference URLs | P1 | 8 |
| REQ-052 | Plugin system (pluggy-based): agent plugins, LLM provider plugins, template plugins | P1 | 8 |
| REQ-053 | ExperimentLog data model: tracks hypothesis, git branch, metrics before/after, delta, keep/discard decision, duration, token cost for every experiment in debug (S8), QA optimization (S6), and Improve mode | P0 | 2 |

## Priority Summary

| Priority | Count | Description |
|----------|-------|-------------|
| P0 | 35 | Must have for v1 launch |
| P1 | 18 | Should have, add when possible |
| P2 | 0 | Future (tracked in PROJECT.md Out of Scope) |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-001 | Phase 1 | Complete |
| REQ-002 | Phase 1 | Complete |
| REQ-003 | Phase 1 | Complete |
| REQ-004 | Phase 1 | Pending |
| REQ-005 | Phase 1 | Pending |
| REQ-006 | Phase 2 | Pending |
| REQ-007 | Phase 2 | Pending |
| REQ-008 | Phase 2 | Pending |
| REQ-009 | Phase 2 | Pending |
| REQ-010 | Phase 2 | Pending |
| REQ-011 | Phase 2 | Pending |
| REQ-012 | Phase 2 | Pending |
| REQ-013 | Phase 2 | Pending |
| REQ-014 | Phase 2 | Pending |
| REQ-015 | Phase 8 | Pending |
| REQ-016 | Phase 3 | Pending |
| REQ-017 | Phase 3 | Pending |
| REQ-018 | Phase 3 | Pending |
| REQ-019 | Phase 3 | Pending |
| REQ-020 | Phase 3 | Pending |
| REQ-021 | Phase 4 | Pending |
| REQ-022 | Phase 8 | Pending |
| REQ-023 | Phase 4 | Pending |
| REQ-024 | Phase 4 | Pending |
| REQ-025 | Phase 4 | Pending |
| REQ-026 | Phase 4 | Pending |
| REQ-027 | Phase 4 | Pending |
| REQ-028 | Phase 4 | Pending |
| REQ-029 | Phase 4 | Pending |
| REQ-030 | Phase 4 | Pending |
| REQ-031 | Phase 4 | Pending |
| REQ-032 | Phase 4 | Pending |
| REQ-033 | Phase 4 | Pending |
| REQ-034 | Phase 4 | Pending |
| REQ-035 | Phase 7 | Pending |
| REQ-036 | Phase 4 | Pending |
| REQ-037 | Phase 4 | Pending |
| REQ-038 | Phase 3 | Pending |
| REQ-039 | Phase 5 | Pending |
| REQ-040 | Phase 5 | Pending |
| REQ-041 | Phase 6 | Pending |
| REQ-042 | Phase 6 | Pending |
| REQ-043 | Phase 8 | Pending |
| REQ-044 | Phase 7 | Pending |
| REQ-045 | Phase 7 | Pending |
| REQ-046 | Phase 7 | Pending |
| REQ-047 | Phase 7 | Pending |
| REQ-048 | Phase 4 | Pending |
| REQ-049 | Phase 7 | Pending |
| REQ-050 | Phase 7 | Pending |
| REQ-051 | Phase 8 | Pending |
| REQ-052 | Phase 8 | Pending |

| REQ-053 | Phase 2 | Pending |

**Coverage:** 53/53 requirements mapped. No orphans.

---
*Generated: 2026-03-18*
