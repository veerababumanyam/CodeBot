# Project Research Summary

**Project:** CodeBot
**Domain:** Autonomous multi-agent SDLC platform (idea-to-production code generation)
**Researched:** 2026-03-18
**Confidence:** MEDIUM-HIGH

## Executive Summary

CodeBot is a graph-centric multi-agent platform that orchestrates ~30 specialized AI agents across an 11-stage SDLC pipeline (S0-S10) to transform natural language ideas into fully tested, deployed applications. The canonical approach for this class of system is a directed computation graph (DAG) where agents are nodes, dependencies are edges, and a topological sort discovers automatic parallelism. All three research streams converge on LangGraph as the graph engine, Temporal for durable workflow execution, LiteLLM as the unified LLM gateway, and NATS JetStream for the event bus. The five-layer architecture (Foundation, Engine, Component, Protocol, Interaction) provides clean separation of concerns that maps directly to a phased build order.

The recommended approach is to build bottom-up: data layer and monorepo scaffolding first, then the graph engine and LLM abstraction, then agents and pipeline coordination, and finally the user-facing surfaces (dashboard, CLI). This order is dictated by hard dependency chains -- agents cannot function without the graph engine, the graph engine needs the data layer for checkpointing, and the dashboard needs API endpoints that only exist once the pipeline manager is built. The critical path to a first working end-to-end pipeline runs through: Data Layer -> Graph Engine -> Multi-LLM Layer -> Context Manager -> BaseAgent -> Core Agents -> Pipeline Manager -> FastAPI -> CLI.

The primary risks are: (1) LLM rate limits will be hit before any infrastructure bottleneck -- multi-provider routing with fallback chains is essential from day one; (2) the sheer scope of 30 agents across 11 stages creates a real risk of building too much before validating anything -- the build order must deliver a working vertical slice (single pipeline run, limited agent set) as early as possible; (3) git worktree merge conflicts from parallel coding agents are complex to resolve correctly and should be built with extensive test coverage; (4) context management quality directly determines code generation quality -- poor chunking or stale embeddings produce incoherent multi-file output.

## Key Findings

### Recommended Stack

The stack is a Python 3.12+ backend with FastAPI, a React/Vite/TypeScript dashboard, and a TypeScript CLI, all coordinated in a Turborepo monorepo. All three research files agree on the core choices. The stack prioritizes async-first Python (asyncio.TaskGroup for concurrent agent execution), self-hostable infrastructure (no mandatory cloud dependencies), and provider-agnostic LLM routing.

**Core technologies:**
- **Python 3.12+ / FastAPI / Pydantic v2**: Backend runtime -- async-first, auto-generated OpenAPI, Rust-backed validation
- **LangGraph >=0.2.x**: Agent graph engine -- native cyclical graph support (required for S8 debug loop), built-in Postgres checkpointing
- **Temporal (Python SDK)**: Durable workflow orchestration -- survives process crashes across hour-long pipeline runs
- **LiteLLM >=1.82.0**: Unified LLM gateway -- single interface for 100+ providers, built-in cost tracking, self-hosted proxy mode
- **NATS JetStream**: Event bus -- sub-millisecond pub/sub, at-least-once delivery, stream replay for agent fan-out
- **PostgreSQL 16**: Primary state store -- pipeline runs, agent tasks, checkpoints, LLM usage
- **Redis 7**: Cache, rate limiting, ephemeral pipeline state
- **LanceDB (dev) / Qdrant (prod)**: Vector store -- replaces ChromaDB (which has known scale issues); hybrid search for L2 context retrieval
- **React 18 / Vite 6 / TypeScript 5.5+**: Dashboard -- React Flow for DAG visualization, Monaco for code review, Zustand for state
- **Turborepo + uv + pnpm**: Monorepo tooling -- cached builds, fast installs, workspace-aware

**Critical version requirements:**
- FastAPI >=0.115.0 requires Pydantic v2 only (no v1 compat)
- LangGraph >=0.2.x requires langchain-core >=0.3.0
- SQLAlchemy 2.0 async requires asyncpg (not psycopg2)
- Vite 6 requires Node >=18 (use Node 22 LTS)

### Expected Features

The feature research identified 18 table-stakes features, 18 differentiators, and 11 anti-features to avoid. The MVP definition is aggressive but clearly structured.

**Must have (table stakes -- P1 for launch):**
- Natural language / PRD input to working code
- Multi-file, multi-module code generation
- Git integration with branch-per-feature and PR creation
- Automated test generation and execution (unit + integration minimum)
- Error detection and auto-fix loop (S8 debug cycle)
- Multi-LLM routing (Claude, OpenAI, Gemini, Ollama, LM Studio)
- Sandbox execution per agent (containerized, resource-limited)
- Human-in-the-loop approval gates
- Checkpoint-based pipeline resume
- CLI interface and web dashboard
- Cost tracking (per-agent, per-stage, budget enforcement)
- SAST security scanning (Semgrep + Gitleaks minimum)

**Should have (differentiators -- P2):**
- Full security pipeline (DAST + SCA + license compliance)
- Full test suite (E2E, performance, accessibility, mutation, contract)
- React Native mobile generation
- Cloud deployment to 8+ providers (S10)
- Brownfield / inflight project modes
- Episodic memory / cross-session learning
- Plugin system (pluggy-based)

**Defer (v2+):**
- Real-time CRDT collaboration (conflicts with worktree isolation model)
- Self-improving agent ecosystem (requires mature episodic memory)
- Native iOS/Android (React Native covers v1)
- Autonomous improve mode (requires proven pipeline safety)
- App Store / Play Store submission automation

**Anti-features to actively avoid:**
- Per-file streaming output (incomplete files create confusion)
- Monolithic agent (context window overflow, no parallelism)
- In-browser code editor as primary interface (blurs autonomous pipeline identity)
- Built-in LLM hosting (CodeBot orchestrates, not hosts)

### Architecture Approach

The architecture follows MASFactory's four-layer model extended to five layers: Foundation (data, LLM, sandboxing), Engine (graph execution, scheduling, checkpointing), Component (30 specialized agents, node templates), Protocol (FastAPI gateway, WebSocket, event bus), and Interaction (dashboard, CLI, IDE extensions). All inter-agent communication flows through the graph engine's typed message passing or the NATS event bus -- no direct agent-to-agent calls.

**Major components (build-order priority):**
1. **Agent Graph Engine** -- DAG runtime with topological layer execution, asyncio.TaskGroup concurrency, LangGraph-backed
2. **Pipeline Manager** -- SDLC phase coordination, gate evaluation, YAML-declarative presets
3. **Multi-LLM Abstraction** -- Provider-agnostic interface with routing, fallback chains, cost tracking via LiteLLM
4. **3-Tier Context Manager** -- L0 always-loaded (~2K tokens), L1 on-demand (~10K), L2 deep retrieval (~20K) via vector store
5. **CLI Agent Bridge** -- Delegates coding to Claude Code (SDK), Codex CLI, Gemini CLI via subprocess
6. **Worktree Manager** -- Git worktree isolation per coding agent with merge coordination
7. **Sandbox Manager** -- Docker container per agent with resource limits
8. **Security Pipeline** -- Parallel scanner fan-out (Semgrep, Trivy, Gitleaks), normalized findings, quality gate
9. **Event Bus** -- NATS JetStream for async agent events and real-time dashboard streaming
10. **Web Dashboard** -- React Flow pipeline visualization, Monaco code viewer, agent activity, cost tracker

### Critical Pitfalls

Note: No dedicated PITFALLS.md was produced by the research agents. The following pitfalls are synthesized from warnings embedded across ARCHITECTURE.md, FEATURES.md, and STACK.md.

1. **Shared filesystem without worktrees** -- Multiple coding agents writing to the same directory causes race conditions and non-deterministic output. Prevention: git worktree isolation is non-negotiable for parallel implementation (S5). Build and test the worktree manager before enabling parallel agents.

2. **Full codebase in every agent's context** -- Injecting the entire codebase wastes tokens, exceeds context windows, and degrades quality. Prevention: implement 3-tier context management (L0/L1/L2) early; agents should never see more than ~32K tokens of context.

3. **No checkpointing (restart from zero on failure)** -- Full pipeline runs take hours and cost significant tokens. A failure at S7 should not restart from S0. Prevention: checkpoint state after every execution layer using LangGraph's built-in Postgres checkpointing.

4. **ChromaDB at scale** -- Research explicitly flags ChromaDB performance degradation above ~1M vectors and lack of native hybrid search. Prevention: use LanceDB for development and Qdrant for production from the start; do not build on ChromaDB despite it appearing in earlier project docs.

5. **Synchronous security scanning after delivery** -- Running security scans as a final step means findings require rewrites of already-complete code. Prevention: security pipeline runs in parallel with code review (S6), immediately after implementation (S5), feeding back into the debug loop.

6. **Scope explosion before validation** -- Building all 30 agents and 11 stages before testing a single end-to-end run. Prevention: implement the critical-path agent subset first (Orchestrator, Planner, Backend Dev, Tester, Debugger), validate one full pipeline run, then expand.

## Implications for Roadmap

Based on the architecture dependency tiers and feature priorities, the following phase structure is recommended. Each phase delivers a testable increment.

### Phase 1: Foundation and Scaffolding
**Rationale:** Everything depends on the data layer, monorepo structure, and shared types. No agent or engine code can be written without these.
**Delivers:** Working monorepo with Docker Compose dev stack, database schemas, BaseAgent stub, shared type definitions.
**Addresses:** Project scaffolding, dependency management, data layer setup.
**Avoids:** Building on unstable foundations; ensures all downstream phases have infrastructure.
**Stack:** Turborepo, pyproject.toml, package.json, docker-compose.yml (PostgreSQL, Redis, NATS, LanceDB), SQLAlchemy models, Alembic migrations.

### Phase 2: Graph Engine and Core Infrastructure
**Rationale:** The graph engine is the execution substrate for everything. Multi-LLM routing and context management are the two services every agent invocation depends on. These three must be built before any agent can run.
**Delivers:** Working DAG execution engine, LLM routing with fallback chains, L0/L1/L2 context assembly, NATS event bus.
**Addresses:** Graph-centric orchestration, multi-LLM support, context management, event-driven architecture.
**Avoids:** Building agents before the infrastructure they depend on exists.
**Stack:** LangGraph, LiteLLM, NATS JetStream, LanceDB/Qdrant, Tree-sitter, asyncio.TaskGroup.

### Phase 3: Agent Framework and Critical-Path Agents
**Rationale:** With the engine running, build the agent framework (BaseAgent lifecycle, tool bindings) and the minimum set of agents needed for a first end-to-end pipeline run: Orchestrator, Planner, Backend Dev, Tester, Debugger.
**Delivers:** Working agent lifecycle, git worktree isolation, CLI agent bridge (Claude Code SDK), sandbox execution, first end-to-end pipeline from PRD input to tested code.
**Addresses:** Natural language input, code generation, automated testing, debug-fix cycle, git integration, sandbox execution.
**Avoids:** Building all 30 agents before validating the pipeline works end-to-end.
**Stack:** BaseAgent, GitPython, Docker SDK, Claude Agent SDK, Codex CLI, pytest.

### Phase 4: Pipeline Manager and SDLC Stages
**Rationale:** With core agents proven, build the full pipeline coordinator (phase gates, presets, checkpointing) and expand agent coverage to all 11 stages. Add the remaining ~25 agents incrementally.
**Delivers:** Full SDLC pipeline (S0-S10), checkpoint-based resume, YAML presets (full/quick/review-only), SAST security scanning, documentation generation.
**Addresses:** Pipeline execution, checkpointing, security pipeline (SAST), documentation generation, brainstorming, research, architecture phases.
**Avoids:** Late-stage security scanning; pipeline resume failures.
**Stack:** Temporal, Semgrep, Gitleaks, pipeline YAML configs.

### Phase 5: API Gateway and CLI
**Rationale:** The pipeline needs a user-facing entry point. The FastAPI gateway exposes REST + WebSocket endpoints; the CLI provides headless operation. These are the primary user interfaces.
**Delivers:** REST API for all pipeline operations, WebSocket streaming for real-time events, CLI with all core commands (init, plan, start, status, review, deploy).
**Addresses:** CLI interface, human-in-the-loop gates, cost tracking API, progress visibility.
**Avoids:** Building the dashboard before the API it depends on exists.
**Stack:** FastAPI, Socket.IO, Node.js 22 LTS, TypeScript CLI.

### Phase 6: Web Dashboard
**Rationale:** With a functioning API, build the dashboard for visual pipeline management. This is the last major component before the platform is usable by non-CLI users.
**Delivers:** Pipeline DAG visualization (React Flow), agent activity cards, code review viewer (Monaco), terminal output (xterm.js), cost tracker, test results.
**Addresses:** Web dashboard, pipeline visualization, cost intelligence, progress visibility.
**Avoids:** Building UI before the API is stable.
**Stack:** React, Vite, TypeScript, Tailwind, Shadcn/ui, React Flow, Monaco, Zustand, TanStack Query.

### Phase 7: Advanced Features and Hardening
**Rationale:** Once the core platform works end-to-end with all stages, add the differentiating features: full security pipeline (DAST + SCA), expanded test types, React Native, cloud deployment.
**Delivers:** Full security pipeline, E2E/performance/accessibility testing, mobile code generation, multi-cloud deployment (S10), brownfield mode.
**Addresses:** P2 features from the prioritization matrix.
**Stack:** OWASP ZAP, Playwright, k6, axe-core, Pact, Pulumi, OpenTofu, React Native.

### Phase 8: Ecosystem and Polish
**Rationale:** Final phase -- plugin system, episodic memory, observability, IDE extensions, SDK publishing.
**Delivers:** Plugin architecture, cross-project learning, full observability stack, IDE integrations, published SDKs.
**Addresses:** Plugin system, episodic memory, IDE extensions, SDK publishing.
**Stack:** pluggy, Langfuse, OpenTelemetry, SigNoz, VS Code extension API.

### Phase Ordering Rationale

- **Bottom-up build order mirrors the architecture dependency tiers:** Foundation (Tier 1) -> Engine (Tier 2) -> Agents (Tier 3) -> Pipeline (Tier 4) -> Surfaces (Tier 5) -> Integration (Tier 6). Attempting to build out of order creates stub-heavy code with unclear contracts.
- **First end-to-end run in Phase 3:** By focusing Phase 3 on just 5 critical-path agents, the team validates the entire execution pipeline before investing in the remaining 25 agents. This is the single most important risk-reduction decision.
- **Security shifts left:** SAST scanning is introduced in Phase 4 alongside pipeline stages, not deferred to a late hardening phase. This prevents the anti-pattern of late-stage security findings.
- **Dashboard after API:** Building the dashboard (Phase 6) after the API is stable (Phase 5) avoids the common trap of building a UI against a moving API, which wastes frontend effort on repeated API contract changes.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Graph Engine):** LangGraph's cyclical graph support for the S8 debug loop needs hands-on prototyping; the documentation covers basic cycles but not the experiment-loop pattern CodeBot requires.
- **Phase 3 (CLI Agent Bridge):** Claude Code SDK integration patterns, Codex CLI subprocess management, and structured output parsing from CLI agents are not well-documented publicly; expect discovery work.
- **Phase 4 (Temporal integration):** The boundary between LangGraph (graph execution) and Temporal (durable orchestration) needs careful design to avoid overlapping responsibilities.
- **Phase 7 (Cloud Deployment):** Multi-cloud IaC generation across 8+ providers is complex; each provider has different deployment models and API surfaces.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Monorepo setup, Docker Compose, SQLAlchemy models -- all well-documented, established patterns.
- **Phase 5 (API Gateway):** FastAPI REST + WebSocket -- extensive documentation, mature ecosystem.
- **Phase 6 (Dashboard):** React + Vite + React Flow -- standard patterns with rich community examples.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Versions from project docs (v2.5); external verification unavailable in research session; core choices (LangGraph, FastAPI, LiteLLM) well-established |
| Features | HIGH | Grounded in PRD v2.5 and competitive analysis; clear MVP/v1.x/v2 boundaries defined |
| Architecture | HIGH | Extensive project documentation with C4 diagrams; cross-referenced with MASFactory, Automaker, OpenSandbox reference implementations |
| Pitfalls | MEDIUM | No dedicated pitfalls research was conducted; pitfalls synthesized from anti-patterns documented in ARCHITECTURE.md and "What NOT to Use" in STACK.md |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **PITFALLS.md not produced:** Dedicated pitfall research was not completed. The pitfalls section above is synthesized from other research files. A focused pitfall analysis (especially around LangGraph cycle handling, worktree merge conflict resolution, and token budget enforcement) would strengthen planning.
- **External version verification:** Stack versions were sourced from project documentation, not verified against live package registries. Pin exact versions during Phase 1 scaffolding.
- **LangGraph + Temporal boundary:** Both tools handle workflow state and execution. The exact division of responsibility (LangGraph for intra-stage graph execution, Temporal for inter-stage durability) needs prototyping in Phase 2.
- **ChromaDB to LanceDB/Qdrant migration:** Project docs reference ChromaDB extensively, but stack research recommends LanceDB/Qdrant. All documentation and code references to ChromaDB need updating.
- **Claude Code SDK stability:** The Claude Agent SDK is relatively new; API stability and error handling patterns need validation during Phase 3.
- **Cost estimation accuracy:** Token cost tracking via LiteLLM + Langfuse is well-supported, but accurate cost prediction before a pipeline run (a user expectation) requires historical data that won't exist until after multiple runs.

## Sources

### Primary (HIGH confidence)
- `docs/architecture/ARCHITECTURE.md` v2.5 -- C4 model, 5-layer architecture, subsystem designs
- `docs/prd/PRD.md` v2.5 -- Product requirements, feature definitions, competitive landscape
- `docs/design/SYSTEM_DESIGN.md` v2.5 -- Graph engine design, agent specifications, pipeline orchestration
- `docs/technical/TECHNICAL_REQUIREMENTS.md` v2.5 -- Version pins, integration patterns
- `docs/refernces/RESEARCH_SUMMARY.md` v2.5 -- Technology evaluations, reference implementations
- `.planning/PROJECT.md` -- In-scope vs deferred decisions, constraints

### Secondary (MEDIUM confidence)
- MASFactory (arXiv:2603.06007) -- Graph-centric multi-agent architecture pattern
- Automaker, Codebuff, Superset -- Git worktree isolation, subprocess CLI agent orchestration
- OpenViking -- Hierarchical context management (L0/L1/L2)
- OpenSandbox (Alibaba) -- Docker-per-agent sandbox with gVisor/Kata isolation

### Tertiary (needs validation)
- Stack version numbers beyond August 2025 training data cutoff -- verify against live registries
- LangGraph >=0.2.x API for cyclical graphs -- validate with hands-on prototyping
- Claude Agent SDK subprocess lifecycle management -- validate integration patterns

---
*Research completed: 2026-03-18*
*Ready for roadmap: yes*
