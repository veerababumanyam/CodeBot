# Roadmap: CodeBot

## Overview

CodeBot is built bottom-up following its architecture dependency tiers: foundation infrastructure first, then the graph engine and LLM abstraction, then agents with a first end-to-end vertical slice, then the full SDLC pipeline with all agents and stages, then user-facing surfaces (API, CLI, dashboard), and finally advanced features and ecosystem polish. The critical risk-reduction milestone is Phase 3, which validates one complete pipeline run (PRD in, tested code out) before investing in the remaining 25 agents. Phases are structured to maximize parallel agent execution within each phase wherever subsystems are independent.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation and Scaffolding** - Monorepo, Docker dev stack, database schemas, shared types, event bus
- [ ] **Phase 2: Graph Engine and Core Infrastructure** - DAG execution engine, multi-LLM routing, context management, checkpointing
- [ ] **Phase 3: Agent Framework and Vertical Slice** - BaseAgent, CLI agent bridge, worktree isolation, sandbox, 5 critical-path agents, first end-to-end run
- [ ] **Phase 4: Full Pipeline and All Agents** - 11-stage SDLC pipeline, all ~30 agents, YAML presets, SAST security, documentation generation
- [ ] **Phase 5: API Gateway and CLI** - FastAPI REST + WebSocket, TypeScript CLI with all commands
- [ ] **Phase 6: Web Dashboard** - React pipeline visualization, agent activity, code viewer, cost tracker, live preview
- [ ] **Phase 7: Advanced Features and Hardening** - Full security pipeline, expanded testing, React Native, cloud deployment (S10), brownfield mode
- [ ] **Phase 8: Ecosystem and Polish** - Plugin system, episodic memory, IDE extensions, multi-modal input, agent learning

## Phase Details

### Phase 1: Foundation and Scaffolding
**Goal**: A working monorepo with all infrastructure services running locally, database schemas migrated, shared types defined, and event bus operational -- so all downstream phases have stable infrastructure to build on
**Depends on**: Nothing (first phase)
**Requirements**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
**Success Criteria** (what must be TRUE):
  1. Running `docker-compose up` brings up PostgreSQL, Redis, NATS, and vector store with no manual configuration
  2. `uv sync` and `pnpm install` succeed from a clean clone, and `turbo build` completes for all workspaces
  3. Alembic migrations apply cleanly and create all pipeline state, agent task, and LLM usage tables
  4. A Python test can publish a message to NATS JetStream and a subscriber receives it within 1 second
  5. Shared Pydantic models and TypeScript types compile and are importable from their respective lib packages
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Monorepo scaffolding: root configs, workspace packages, build pipeline
- [ ] 01-02-PLAN.md — Docker Compose dev stack, SQLAlchemy models, Alembic migrations
- [ ] 01-03-PLAN.md — Shared Pydantic models, TypeScript types, NATS JetStream event bus

### Phase 2: Graph Engine and Core Infrastructure
**Goal**: A working DAG execution engine that can compile graphs, execute nodes in topological layers with parallel concurrency, route LLM calls across 5 providers with fallback chains, and assemble 3-tier context for agent invocations
**Depends on**: Phase 1
**Requirements**: REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012, REQ-013, REQ-014, REQ-053
**Success Criteria** (what must be TRUE):
  1. A test graph with 3 independent nodes executes them concurrently via asyncio.TaskGroup and completes in ~1x single-node time (not 3x)
  2. A LOOP node re-executes its subgraph until an exit condition is met, and an EXPERIMENT_LOOP node tracks baseline metrics, creates experiment branches, and implements keep/discard decisions (validates S8 debug cycle with autoresearch-inspired experiment semantics)
  3. LLM Router sends a request to a configured provider and falls back to a secondary provider when the primary returns an error
  4. Context assembly produces an L0+L1 payload under 12K tokens for a sample project, and L2 semantic search returns relevant code chunks from the vector store
  5. After simulating a failure mid-graph, resuming from checkpoint replays only the incomplete nodes (not the entire graph)
**Plans**: 3 plans

Plans:
- [ ] 02-01: Graph engine core (DirectedGraph, Node types incl. ExperimentLoopNode, Edge types, topological scheduler, ExecutionEngine with asyncio.TaskGroup, ExperimentLog data model)
- [ ] 02-02: Multi-LLM abstraction (LiteLLM gateway, provider adapters, model router, fallback chains, cost tracking)
- [ ] 02-03: Context management and checkpointing (L0/L1/L2 tiers, Tree-sitter indexer, vector store integration, checkpoint manager)

### Phase 3: Agent Framework and Vertical Slice
**Goal**: A working agent lifecycle from BaseAgent through CLI agent bridge to sandboxed execution in isolated git worktrees -- validated by one complete end-to-end pipeline run from PRD input to tested, passing code using 5 critical-path agents
**Depends on**: Phase 2
**Requirements**: REQ-016, REQ-017, REQ-018, REQ-019, REQ-020, REQ-038
**Success Criteria** (what must be TRUE):
  1. A PRD text input triggers the Orchestrator agent, which delegates to Planner, Backend Dev, Tester, and Debugger in sequence -- producing a working Python application with passing tests
  2. Backend Dev agent operates in an isolated git worktree (not the main working tree) and its changes are merged back after completion
  3. Code generated by Backend Dev runs inside a sandboxed Docker container with CPU/memory limits enforced
  4. When Tester finds failures, Debugger automatically generates fixes and re-runs tests until they pass (or exhausts iteration budget)
  5. Agent safety guardrails prevent an agent from executing outside its declared capability boundaries
**Plans**: 3 plans

Plans:
- [ ] 03-01: BaseAgent framework (lifecycle, tool bindings, YAML config, AgentNode wrapper, agent safety guardrails)
- [ ] 03-02: Worktree manager and sandbox execution (git worktree lifecycle, Docker container per agent, resource limits)
- [ ] 03-03: CLI agent bridge and critical-path agents (Claude Code SDK, Codex/Gemini subprocess, Orchestrator, Planner, Backend Dev, Tester, Debugger)

### Phase 4: Full Pipeline and All Agents
**Goal**: The complete 11-stage SDLC pipeline runs end-to-end with all ~30 agents, YAML preset configurations, SAST security gates, and documentation generation -- producing fully tested, scanned, documented applications from natural language input
**Depends on**: Phase 3
**Requirements**: REQ-021, REQ-023, REQ-024, REQ-025, REQ-026, REQ-027, REQ-028, REQ-029, REQ-030, REQ-031, REQ-032, REQ-033, REQ-034, REQ-036, REQ-037, REQ-048
**Success Criteria** (what must be TRUE):
  1. A full pipeline run from PRD input executes all 11 stages (S0-S9, S10 opt-in) with stage transitions gated by quality checks
  2. Parallel stages (S3 Architecture+Design, S5 Implementation with multiple coding agents, S6 QA with review+security in parallel) execute concurrently and complete faster than sequential execution
  3. Human-in-the-loop gates pause execution at configured checkpoints and resume after approval
  4. Semgrep and Gitleaks scan generated code and block progression if critical/high findings are detected
  5. Running `codebot --preset quick` executes a reduced pipeline (skip brainstorm, research, and some test types) that completes significantly faster than the full preset
**Plans**: 3 plans

Plans:
- [ ] 04-01: Pipeline manager and SDLC stages (phase coordination, gate evaluation, YAML presets, Temporal integration, S0-S4 agents)
- [ ] 04-02: Implementation and QA agents (S5 frontend/backend/middleware/infra agents, S6 code reviewer/security auditor, parallel worktree execution)
- [ ] 04-03: Testing, debug, documentation agents and security gates (S7 tester, S8 debugger ExperimentLoop with keep/discard experiment branches, S9 doc writer, Semgrep/Gitleaks integration, HITL gates)

### Phase 5: API Gateway and CLI
**Goal**: Users can operate CodeBot through a REST API and TypeScript CLI -- starting pipelines, monitoring progress in real-time via WebSocket, approving human-in-the-loop gates, and viewing cost/status information
**Depends on**: Phase 4
**Requirements**: REQ-039, REQ-040
**Success Criteria** (what must be TRUE):
  1. `codebot init` creates a new project and `codebot start` triggers a full pipeline run from the command line
  2. WebSocket connection streams real-time agent events (started, progress, completed, failed) to a connected client as the pipeline runs
  3. REST API returns current pipeline status, per-stage cost breakdown, and agent task history for any active or completed run
  4. CLI `codebot review` surfaces human-in-the-loop approval prompts and `codebot approve` / `codebot reject` advance or block the pipeline
**Plans**: 3 plans

Plans:
- [ ] 05-01: FastAPI gateway (REST endpoints for projects, runs, agents, cost; WebSocket/Socket.IO streaming; auth middleware)
- [ ] 05-02: TypeScript CLI (all core commands: init, brainstorm, plan, start, status, review, approve, deploy, config)

### Phase 6: Web Dashboard
**Goal**: Users can visually monitor and control CodeBot pipelines through a React dashboard with real-time DAG visualization, agent activity cards, code review, terminal output, test results, and cost tracking
**Depends on**: Phase 5
**Requirements**: REQ-041, REQ-042
**Success Criteria** (what must be TRUE):
  1. Dashboard displays a React Flow DAG of the pipeline with nodes changing color/state in real-time as agents execute
  2. Clicking an agent node shows its output log, generated files (with Monaco syntax highlighting), and token cost
  3. Test results panel shows pass/fail counts, coverage percentage, and individual test details with failure messages
  4. Cost tracker displays per-agent and per-stage token usage with running total and budget remaining
  5. Live preview iframe shows the generated application running with hot-reload as code changes are applied
**Plans**: 3 plans

Plans:
- [ ] 06-01: Dashboard shell and pipeline visualization (React/Vite/Tailwind scaffold, React Flow DAG, Zustand stores, Socket.IO integration)
- [ ] 06-02: Agent views and operational panels (agent activity cards, Monaco code viewer, xterm.js terminal, test results, cost tracker, live preview)

### Phase 7: Advanced Features and Hardening
**Goal**: CodeBot becomes production-grade with full security scanning (DAST+SCA), expanded test coverage (E2E, performance, accessibility), React Native mobile generation, multi-cloud deployment (S10), and brownfield/inflight project support
**Depends on**: Phase 6
**Requirements**: REQ-035, REQ-044, REQ-045, REQ-046, REQ-047, REQ-049, REQ-050
**Success Criteria** (what must be TRUE):
  1. A full pipeline run with the security preset runs DAST (ZAP against running app), SCA (Trivy), and license compliance (ORT) in addition to SAST, and blocks on critical findings
  2. Generated applications include E2E tests (Playwright), performance tests (k6), and accessibility tests (axe-core) that execute as part of S7
  3. Giving CodeBot a mobile-inclusive PRD produces a React Native application alongside the web app, sharing components where possible
  4. `codebot deploy --target aws` generates IaC (Pulumi/OpenTofu), provisions infrastructure, and deploys the generated application to the target cloud provider
  5. Running CodeBot in brownfield mode against an existing codebase analyzes the code, builds context, and generates improvements without breaking existing functionality
  6. Improve mode accepts a target metric (performance/security/coverage), time budget, and constraints, then runs ExperimentLoop producing atomic reviewable commits with measured deltas
**Plans**: 3 plans

Plans:
- [ ] 07-01: Full security pipeline and expanded testing (DAST/SCA/license scanning, Playwright E2E, k6 performance, axe-core accessibility, Pact contract tests)
- [ ] 07-02: React Native, deployment, and project modes (mobile generation agents, S10 deployment to 8+ providers, IaC generation, brownfield/inflight/improve modes with ExperimentLoop, template system, multi-repo support)

### Phase 8: Ecosystem and Polish
**Goal**: CodeBot is extensible, learning, and integrated into developer workflows -- with a plugin system for community extensions, episodic memory for cross-project improvement, IDE integrations, multi-modal input support, and agent self-improvement capabilities
**Depends on**: Phase 7
**Requirements**: REQ-015, REQ-022, REQ-043, REQ-051, REQ-052
**Success Criteria** (what must be TRUE):
  1. A third-party developer can create and register a custom agent plugin (via pluggy) that executes within the pipeline without modifying CodeBot core
  2. After completing 3+ projects, CodeBot's episodic memory surfaces relevant patterns and anti-patterns from past projects to improve current generation quality
  3. VS Code extension provides CodeBot pipeline status, agent output, and approval gates directly in the editor sidebar
  4. Submitting a wireframe image alongside a text PRD produces an application whose UI layout matches the wireframe
  5. Agents create reusable skills from successful patterns and these skills are available to all future pipeline runs after human review
**Plans**: 3 plans

Plans:
- [ ] 08-01: Plugin system and episodic memory (pluggy architecture, agent/tool/template/provider plugins, cross-session memory, pattern library, anti-pattern registry)
- [ ] 08-02: IDE extensions, multi-modal input, and agent learning (VS Code/JetBrains/Neovim extensions, image/voice/video input processing, skill/hook/tool creation)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Scaffolding | 1/3 | In Progress|  |
| 2. Graph Engine and Core Infrastructure | 0/3 | Not started | - |
| 3. Agent Framework and Vertical Slice | 0/3 | Not started | - |
| 4. Full Pipeline and All Agents | 0/3 | Not started | - |
| 5. API Gateway and CLI | 0/2 | Not started | - |
| 6. Web Dashboard | 0/2 | Not started | - |
| 7. Advanced Features and Hardening | 0/2 | Not started | - |
| 8. Ecosystem and Polish | 0/2 | Not started | - |

---
*Generated: 2026-03-18*
