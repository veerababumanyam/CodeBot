# Roadmap: CodeBot

## Overview

CodeBot is built foundation-first, then vertical-slice-validated, then breadth-expanded. The graph engine and agent framework form the critical path -- every pipeline stage, every agent execution, every workflow depends on them. Once the core infrastructure (graph engine, agents, LLM access, context, orchestration) is proven end-to-end with a minimal 5-agent pipeline (Phase 7), the remaining 25 agents are built on a validated foundation. The server, dashboard, and CLI come after the agent pipeline works, because there is nothing useful to visualize or control until agents can execute real workflows.

Phase 1 (Foundation) is already complete: monorepo scaffolding, Docker stack, NATS JetStream, shared models, and database schema are built and tested.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation Infrastructure** - Monorepo, Docker, NATS, shared models, DB schema
- [ ] **Phase 2: Graph Engine** - Directed graph runtime with all node types, parallel execution, validation, and checkpointing
- [ ] **Phase 3: Agent Framework** - BaseAgent with PRA cycle, AgentNode, state machine, YAML config, isolation, and metrics
- [ ] **Phase 4: Multi-LLM Abstraction** - Provider-agnostic LLM interface with routing, fallbacks, cost tracking, and streaming
- [ ] **Phase 5: Context Management** - 3-tier context system (L0/L1/L2), vector store, Tree-sitter indexing, and compression
- [ ] **Phase 6: Pipeline Orchestration** - Temporal durable workflows, pipeline lifecycle, gates, presets, and checkpoint/resume
- [ ] **Phase 7: Vertical Slice** - 5 agents end-to-end proving the full architecture (Orchestrator, Backend Dev, Code Reviewer, Tester, Debugger)
- [ ] **Phase 8: Security Pipeline + Worktree Manager** - Security scanning cascade, worktree isolation, CLI agent bridge, and dependency allowlists
- [ ] **Phase 9: Full Agent Roster** - All 30 agents across S0-S9 stages with parallel execution and composed graphs
- [ ] **Phase 10: FastAPI Server + API Layer** - REST API, WebSocket, authentication, and pipeline control endpoints
- [ ] **Phase 11: React Dashboard + CLI Application** - Real-time pipeline visualization, agent monitoring, code editor, terminal, and CLI interface

## Phase Details

### Phase 1: Foundation Infrastructure
**Goal**: Project infrastructure exists and all services run locally
**Depends on**: Nothing (first phase)
**Requirements**: (Validated -- see PROJECT.md)
**Success Criteria** (what must be TRUE):
  1. Docker Compose starts PostgreSQL, Redis, and NATS without errors
  2. Shared Pydantic models and TypeScript types exist with enum parity tests passing
  3. NATS JetStream event bus publishes and consumes messages with integration tests passing
  4. Alembic migrations apply cleanly to PostgreSQL
  5. Monorepo builds with Turborepo across Python and Node workspaces
**Plans**: 3 plans (COMPLETE)

Plans:
- [x] 01-01: Monorepo scaffolding (Turborepo, uv, pnpm workspaces)
- [x] 01-02: Docker stack and database schema
- [x] 01-03: Shared models and event bus

### Phase 2: Graph Engine
**Goal**: System can define, validate, and execute directed computation graphs with all required node types
**Depends on**: Phase 1
**Requirements**: GRPH-01, GRPH-02, GRPH-03, GRPH-04, GRPH-05, GRPH-06, GRPH-07, GRPH-08, GRPH-09, GRPH-10
**Success Criteria** (what must be TRUE):
  1. A graph defined in YAML loads, validates (cycle detection, missing dependencies), and executes nodes in correct topological order
  2. Parallel branches execute concurrently via asyncio TaskGroup and merge results correctly
  3. Conditional routing (SWITCH nodes) directs execution to different branches based on SharedState values
  4. Graph execution can checkpoint mid-run and resume from that checkpoint after restart
  5. Execution traces capture timing, token usage, and output per node for every graph run
**Plans**: 3 plans

Plans:
- [ ] 02-01-PLAN.md — Domain models, YAML loader, and graph validator (NodeType, EdgeType, SharedState, GraphDefinition, Kahn's cycle detection)
- [ ] 02-02-PLAN.md — Graph compiler and execution engine (YAML-to-LangGraph compilation, SWITCH routing, parallel execution, execution tracing)
- [ ] 02-03-PLAN.md — Checkpointing and dynamic fan-out (AsyncPostgresSaver checkpoint/resume, LangGraph Send API for runtime parallelism)

### Phase 3: Agent Framework
**Goal**: Agents can be defined, configured, and executed within the graph engine following a structured cognitive cycle
**Depends on**: Phase 2
**Requirements**: AGNT-01, AGNT-02, AGNT-03, AGNT-04, AGNT-05, AGNT-06, AGNT-07, AGNT-12
**Success Criteria** (what must be TRUE):
  1. A BaseAgent subclass executes the full PRA cycle (perceive context, reason about approach, act on decision, self-review output)
  2. AgentNode wraps any BaseAgent instance and executes it within a graph with typed inputs and outputs
  3. Agent state machine transitions are observable (IDLE through COMPLETED/FAILED/RECOVERING) and logged
  4. A YAML configuration file fully specifies an agent (system prompt, tools, model, context tiers, retry policy) without code changes
  5. Failed agents automatically attempt recovery (retry with modified prompt, escalate, or rollback) based on configured strategy
**Plans**: 2 plans

Plans:
- [ ] 03-01-PLAN.md — BaseAgent with PRA cycle, state machine, recovery strategies, metrics, config models, and protocol stubs
- [ ] 03-02-PLAN.md — AgentNode graph adapter, YAML agent configs, config loader, and integration tests

### Phase 4: Multi-LLM Abstraction
**Goal**: Any agent can call any supported LLM provider through a unified interface with intelligent routing and cost awareness
**Depends on**: Phase 3
**Requirements**: LLM-01, LLM-02, LLM-03, LLM-04, LLM-05, LLM-06, LLM-07, LLM-08
**Success Criteria** (what must be TRUE):
  1. An agent can send a prompt and receive a response through a single interface regardless of whether the backing provider is Anthropic, OpenAI, Google, or self-hosted Ollama
  2. System routes tasks to different models based on task type and cost constraints without agent awareness
  3. When a primary model fails, the system automatically falls back to the next model in the fallback chain and completes the request
  4. Token usage and cost are tracked per agent, per stage, and per model, queryable at any time
  5. Pipeline execution can be halted automatically when cumulative cost exceeds a configured budget threshold
**Plans**: 2 plans

Plans:
- [ ] 04-01-PLAN.md -- LLM schemas, YAML config, provider registry, and task-based model router
- [ ] 04-02-PLAN.md -- LLMService facade, fallback chains, cost tracking, budget enforcement, and streaming

### Phase 5: Context Management
**Goal**: Agents receive precisely the right context for their task -- always-present essentials, phase-scoped materials, and on-demand retrieval -- within token budgets
**Depends on**: Phase 4
**Requirements**: CTXT-01, CTXT-02, CTXT-03, CTXT-04, CTXT-05, CTXT-06, CTXT-07
**Success Criteria** (what must be TRUE):
  1. L0 context (project config, current task, agent system prompt) is automatically included in every agent call without explicit request
  2. L1 context (phase requirements, related code files, architecture decisions) is assembled per-phase and available to all agents in that phase
  3. L2 context retrieval returns semantically relevant code snippets and documentation from the vector store given a natural language query
  4. Tree-sitter parses source files and indexes functions, classes, and imports for structural code search
  5. Hard token budgets are enforced per agent call -- oversized context is compressed or truncated, never silently exceeding limits
**Plans**: 3 plans

Plans:
- [ ] 05-01-PLAN.md -- Context models, token budget enforcement, and three-tier loader (L0/L1)
- [ ] 05-02-PLAN.md -- Vector store backends (LanceDB/Qdrant) and Tree-sitter code indexer
- [ ] 05-03-PLAN.md -- Context compressor and ContextAdapter (full assembly pipeline)

### Phase 6: Pipeline Orchestration
**Goal**: Multi-stage pipelines run durably with retry, checkpoint/resume, human approval gates, and configurable presets
**Depends on**: Phase 5
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06, PIPE-07, PIPE-08
**Success Criteria** (what must be TRUE):
  1. A 10-stage SDLC pipeline (S0-S9) executes end-to-end with Temporal providing durable workflow orchestration
  2. Stages S3, S5, and S6 execute their agents in parallel via DAG topology and merge results before advancing
  3. Pipeline pauses at configured checkpoints for human approval and resumes only after approval is granted
  4. A pipeline that crashes mid-execution resumes from its last checkpoint without re-executing completed stages
  5. Pipeline presets (full, quick, review-only) load from YAML and configure which stages execute
**Plans**: TBD

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD
- [ ] 06-03: TBD

### Phase 7: Vertical Slice
**Goal**: A minimal 5-agent pipeline proves the entire architecture end-to-end by accepting a natural language description and producing tested, reviewed code
**Depends on**: Phase 6
**Requirements**: INPT-01, INPT-02, INPT-04, INPT-05, IMPL-02, IMPL-07, QA-01, QA-06, TEST-01, TEST-02, TEST-05, DBUG-01, DBUG-02, DBUG-03, EVNT-01
**Success Criteria** (what must be TRUE):
  1. User describes a project idea in natural language and the system extracts functional requirements and acceptance criteria
  2. Backend Dev agent generates Python/FastAPI code from the extracted requirements that passes linting and type checks
  3. Code Reviewer agent reviews the generated code and produces actionable feedback that the system can act on
  4. Tester agent generates unit and integration tests that execute against the generated code
  5. When tests fail, Debugger agent performs root cause analysis, generates fixes, and re-runs tests until they pass or max retries are exhausted
**Plans**: 4 plans

Plans:
- [ ] 07-01-PLAN.md — Input processing domain and Orchestrator agent (RequirementExtractor, ClarificationLoop, OrchestratorAgent)
- [ ] 07-02-PLAN.md — Backend Dev and Code Reviewer agents (code generation with lint/typecheck, structured review with quality gate)
- [ ] 07-03-PLAN.md — Tester and Debugger agents (test generation/execution, root cause analysis, ExperimentLoop with keep/discard)
- [ ] 07-04-PLAN.md — Pipeline wiring and E2E validation (vertical-slice graph builder, NATS event emission, integration tests)

### Phase 8: Security Pipeline + Worktree Manager
**Goal**: Generated code is security-scanned at every step with quality gates, and coding agents operate in fully isolated git worktrees
**Depends on**: Phase 7
**Requirements**: SECP-01, SECP-02, SECP-03, SECP-04, SECP-05, SECP-06, WORK-01, WORK-02, WORK-03, WORK-04, IMPL-05, IMPL-06
**Success Criteria** (what must be TRUE):
  1. Semgrep, Trivy, and Gitleaks run automatically on every code generation output and produce structured findings
  2. Quality gates block pipeline advancement when critical or high severity vulnerabilities are found
  3. Dependency allowlist prevents installation of hallucinated or malicious packages
  4. Each coding agent runs in its own git worktree with isolated filesystem, and worktrees are created and cleaned up automatically
  5. Parallel coding agents operate without port conflicts or shared-resource contention via per-worktree Docker profiles and dynamic port allocation
**Plans**: TBD

Plans:
- [ ] 08-01: TBD
- [ ] 08-02: TBD
- [ ] 08-03: TBD

### Phase 9: Full Agent Roster
**Goal**: All 30 specialized agents are implemented across all 10 SDLC stages, completing the full pipeline from brainstorming through documentation
**Depends on**: Phase 8
**Requirements**: AGNT-08, INPT-03, INPT-06, INPT-07, INPT-08, BRST-01, BRST-02, BRST-03, BRST-04, BRST-05, BRST-06, BRST-07, RSRC-01, RSRC-02, RSRC-03, RSRC-04, ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-05, ARCH-06, PLAN-01, PLAN-02, PLAN-03, IMPL-01, IMPL-03, IMPL-04, QA-02, QA-03, QA-04, QA-05, QA-07, TEST-03, TEST-04, DBUG-04, DOCS-01, DOCS-02, DOCS-03, DOCS-04, EVNT-02, EVNT-03, EVNT-04
**Success Criteria** (what must be TRUE):
  1. All 30 agents are registered in the system, each with a YAML configuration specifying its role, tools, model, and context requirements
  2. S1 Brainstorming agents explore ideas, perform competitive analysis, prioritize features, and define MVP scope from a user's project description
  3. S3 Architecture agents (Architect, API Designer, DB Designer, UI/UX Designer) execute in parallel and produce architecture, API specs, schemas, and wireframes
  4. S5 Implementation agents (Frontend, Backend, Mobile, Infrastructure) execute in parallel in isolated worktrees and produce code for their respective platforms
  5. S6 QA agents (Security Scanner, Accessibility, Performance, i18n) execute in parallel and all quality gates pass before advancing to Testing
**Plans**: 5 plans

Plans:
- [ ] 09-01-PLAN.md — Agent registry, S1 Brainstorming agent, S2 Researcher agent, test scaffolding with mock fixtures
- [ ] 09-02-PLAN.md — S3 Architecture agents (Architect, Designer, Template, Database, API Gateway) and S4 Planning agents (Planner, TechStack Builder)
- [ ] 09-03-PLAN.md — S5 Implementation agents (Frontend Dev, Mobile Dev, Infrastructure Engineer, Middleware Dev, Integrations)
- [ ] 09-04-PLAN.md — S6 QA agents (Security Auditor, Accessibility, Performance, i18n) and S7/S8 extensions (Tester with E2E, Debugger with security debugging)
- [ ] 09-05-PLAN.md — Remaining agents (Documentation, Operations, Cross-cutting, Tooling stubs), stage subgraph configs, full registry integration test

### Phase 10: FastAPI Server + API Layer
**Goal**: Users and frontends can control the entire CodeBot system through a REST API with real-time updates via WebSocket
**Depends on**: Phase 9
**Requirements**: SRVR-01, SRVR-02, SRVR-03, SRVR-04, SRVR-05
**Success Criteria** (what must be TRUE):
  1. REST API endpoints exist for project CRUD, pipeline start/stop/pause/resume, and agent status queries
  2. WebSocket endpoint streams real-time pipeline progress and agent output to connected clients
  3. API access requires authentication and enforces authorization (unauthorized requests are rejected)
  4. Pipeline configuration endpoints accept preset selection (full, quick, review-only) and return the configured pipeline
  5. Agent management endpoints allow starting, stopping, restarting, and reconfiguring individual agents
**Plans**: 2 plans

Plans:
- [ ] 10-01-PLAN.md — Auth foundation, response envelope, deps, middleware, project CRUD endpoints (SRVR-01, SRVR-03)
- [ ] 10-02-PLAN.md — Pipeline config/lifecycle, agent management, WebSocket real-time streaming (SRVR-02, SRVR-04, SRVR-05)

### Phase 11: React Dashboard + CLI Application
**Goal**: Users can monitor, control, and interact with CodeBot through a real-time web dashboard and a command-line interface
**Depends on**: Phase 10
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, DASH-07, DASH-08, CLI-01, CLI-02, CLI-03, CLI-04, AGNT-09, AGNT-10, AGNT-11
**Success Criteria** (what must be TRUE):
  1. Dashboard displays the full pipeline as an interactive graph (React Flow) with real-time node status updates via Socket.IO
  2. Agent monitoring panel shows live status, logs, metrics, and cost breakdown per agent, per stage, and per model
  3. Code editor (Monaco) and terminal (xterm.js) are embedded in the dashboard for viewing generated code and running commands
  4. CLI can create projects with interactive prompts, start/pause/resume pipelines, and stream agent logs from the terminal
  5. Skill Creator, Hooks Creator, and Tools Creator agents allow extending the agent ecosystem without code changes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation Infrastructure | 3/3 | Complete | 2026-03-18 |
| 2. Graph Engine | 0/3 | Not started | - |
| 3. Agent Framework | 0/2 | Not started | - |
| 4. Multi-LLM Abstraction | 0/2 | Not started | - |
| 5. Context Management | 0/3 | Not started | - |
| 6. Pipeline Orchestration | 0/3 | Not started | - |
| 7. Vertical Slice | 0/4 | Not started | - |
| 8. Security Pipeline + Worktree Manager | 0/3 | Not started | - |
| 9. Full Agent Roster | 0/5 | Not started | - |
| 10. FastAPI Server + API Layer | 0/2 | Not started | - |
| 11. React Dashboard + CLI Application | 0/3 | Not started | - |
