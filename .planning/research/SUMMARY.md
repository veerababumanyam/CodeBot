# Project Research Summary

**Project:** CodeBot -- Autonomous Multi-Agent SDLC Platform
**Domain:** Graph-centric multi-agent autonomous software development
**Researched:** 2026-03-18
**Confidence:** HIGH

## Executive Summary

CodeBot is an autonomous, end-to-end software development platform that transforms natural language ideas into fully tested, reviewed, secured, and documented applications using ~30 specialized AI agents organized across an 11-stage SDLC pipeline (S0-S9, with S10 optional). Research confirms that the **hierarchical orchestrator-worker pattern with graph-based agent orchestration** is the dominant and most validated multi-agent architecture as of 2026 (confirmed by Google ADK, LangChain, and Confluent guidance). The recommended approach uses a dual-engine model -- LangGraph for agent state machines and Temporal for durable workflow coordination -- layered on top of NATS JetStream for event-driven inter-agent communication, FastAPI for the API gateway, and a React dashboard for real-time visualization. The technology stack is mature, with most core dependencies at v1.0+ stability (LangGraph 1.0, Temporal 1.4+, FastAPI 0.135+, Tailwind 4, React 18+). Supporting components for knowledge graphs (Cognee) and agent memory (Letta) are newer and carry MEDIUM confidence.

The primary competitive advantage is the **full 11-stage SDLC pipeline** -- no competitor covers brainstorming through documentation as a structured, graph-orchestrated pipeline. Devin does implementation, MetaGPT does planning-to-code, and Claude Code is a single coding agent. CodeBot's graph-centric architecture with parallel agent execution (S3, S5, S6), intelligent multi-LLM routing, and integrated security scanning is unique in the market. Table stakes features (NL-to-code, multi-file generation, self-healing debug loops, git integration, sandbox execution) are well-understood and achievable with the recommended stack.

The top risks are: (1) **error cascading across the agent chain** -- one bad agent output amplified through 30 downstream agents, requiring validation gates at every phase boundary; (2) **dual orchestration complexity** -- managing state across both LangGraph and Temporal demands strict boundary discipline from day one; (3) **context window exhaustion** -- long-running pipelines burn through context fast, making the 3-tier context system (L0/L1/L2) load-bearing architecture, not optional; (4) **AI-generated code security vulnerabilities** -- 48-62% of AI code contains vulnerabilities, requiring security scanning after every generation step; and (5) **incomplete git worktree isolation** -- worktrees isolate files but not ports, databases, or Docker daemons, requiring per-worktree environment management.

## Key Findings

### Recommended Stack

The stack is anchored on Python 3.12+ for backend/agents/orchestration and TypeScript 5.5+ for the dashboard and CLI. Both are industry-standard choices with the deepest ecosystem support for AI tooling and web development respectively. Most dependencies are already configured in the monorepo (Turborepo, uv, pnpm, Docker Compose with PostgreSQL/Redis/NATS running).

**Core technologies:**
- **LangGraph 1.0+**: Stateful agent graph execution -- v1.0 stability commitment, 24.6K stars, MIT, native DAG execution with Send API for dynamic fan-out
- **Temporal (Python SDK 1.4+)**: Durable workflow orchestration -- retry/checkpoint/resume for multi-hour pipeline runs, complementary to LangGraph
- **FastAPI 0.135+**: REST/WebSocket API -- async-native, Pydantic v2 integration, automatic OpenAPI docs, 96K stars
- **LiteLLM 1.82+**: Unified multi-LLM gateway -- 100+ providers, 8ms P95 latency at 1K RPS, cost tracking, fallback chains
- **NATS JetStream**: Inter-agent event bus -- already implemented and tested, lightweight pub/sub with persistence
- **LanceDB / Qdrant**: Vector storage -- LanceDB for embedded dev use, Qdrant for production horizontal scaling
- **LlamaIndex 0.14+**: RAG pipeline orchestration -- document chunking, retrieval, re-ranking for context management
- **React 18+ / Vite 6+ / Tailwind 4 / shadcn/ui**: Dashboard -- React Flow for graph visualization, Monaco for code editing, xterm.js for terminal
- **Yjs 13.6+**: CRDT collaborative editing -- defer to v2, but architecture should accommodate it

**Version pinning strategy:** Core frameworks pin major+minor (allow patch). LLM SDKs pin minor (allow patch). Young/fast-moving libraries (Cognee, Letta, RouteLLM) pin exact version.

### Expected Features

**Must have (table stakes -- P1):**
- Natural language to multi-file code generation (core pipeline S0-S5)
- Automated test generation and self-healing debug loop (S7-S8)
- Git integration (branches, PRs, automated commits)
- Security scanning with quality gates (Semgrep, Trivy, Gitleaks at S6)
- Multi-LLM support (Anthropic + OpenAI + Google + self-hosted)
- Human-in-the-loop approval gates at phase boundaries
- Real-time progress visibility (React Flow pipeline visualization)
- CLI interface for project creation and pipeline execution
- Sandbox execution (Docker containers per agent)
- Context management (L0/L1/L2 tiered system)
- Checkpoint/resume via Temporal

**Should have (differentiators -- P2):**
- Full 11-stage SDLC pipeline (unique -- no competitor has this)
- Graph-centric agent orchestration with parallel execution
- Intelligent LLM routing per task type/complexity/cost
- Self-hosted / air-gapped operation with local models
- Agent extensibility (skill/hook/tool creators)
- Brownfield / legacy codebase support
- Pipeline presets (full, quick, review-only)
- Cost tracking per agent/model/stage

**Defer (v2+):**
- Real-time CRDT collaboration (complex, not required for core pipeline)
- Multi-repository orchestration (cross-repo adds enormous complexity)
- Automated cloud deployment (S10) -- generate configs in v1, automate in v2
- Plugin marketplace (requires stable APIs first)
- IDE extensions (VS Code, JetBrains)
- Team features (multi-user, RBAC)

### Architecture Approach

The architecture follows a **5-layer model**: Interaction (dashboard/CLI) -> API & Protocol (FastAPI gateway) -> Orchestration (dual-engine: Temporal for pipeline lifecycle, LangGraph for agent logic) -> Agent & Component (30 specialized agents with BaseAgent + PRA cognitive cycle) -> Foundation (LLM abstraction, context management, event bus, storage). Communication flows through NATS JetStream -- agents never communicate directly. The orchestrator-worker pattern with dynamic fan-out (LangGraph's Send API) handles parallel execution in S3, S5, and S6.

**Major components:**
1. **FastAPI Gateway** -- single external entry point for dashboard and CLI, auth, rate limiting
2. **Temporal Workflows** -- pipeline lifecycle durability, retry/timeout, cross-phase gates
3. **LangGraph StateGraphs** -- agent decision logic, conditional routing, dynamic branching within phases
4. **Pipeline Manager + Phase Coordinator** -- phase sequencing, fan-out/fan-in, topological sort scheduling
5. **Multi-LLM Abstraction (LiteLLM + RouteLLM)** -- provider-agnostic access, intelligent routing, fallback chains
6. **Context Management (L0/L1/L2)** -- tiered context assembly with vector store and Tree-sitter indexing
7. **Event Bus (NATS JetStream)** -- inter-agent messaging, audit trail, replay, dashboard live updates
8. **Worktree Manager** -- git worktree creation/cleanup for agent isolation during parallel execution
9. **Security Pipeline** -- Semgrep, Trivy, Gitleaks, SonarQube with progressive validation cascade

### Critical Pitfalls

1. **Error cascading across agent chain** -- One bad agent output amplifies through 30 downstream agents. Prevent with validation gates at every phase boundary, Challenger verification agents, and rollback to last-known-good checkpoint.
2. **Dual orchestration complexity (LangGraph + Temporal)** -- State in two places, split observability, serialization overhead. Prevent by defining clear boundary: Temporal owns durability/retry, LangGraph owns intra-phase agent logic. Use unified trace IDs. Consider starting LangGraph-only.
3. **Context window exhaustion** -- 50-step workflows burn through context fast with silent quality degradation. Prevent with rigorous L0/L1/L2 implementation, explicit token budgets per agent call, and context observability.
4. **AI-generated code security vulnerabilities** -- 48-62% of AI code is insecure; hallucinated dependencies create supply chain risks. Prevent with security scanning after every code generation step, dependency allowlists, and property-based security testing.
5. **Incomplete git worktree isolation** -- Worktrees isolate files but not ports/databases/Docker. Prevent with per-worktree Docker Compose profiles, dynamic port allocation, and a worktree lifecycle manager.

## Implications for Roadmap

Based on the combined research, the following 10-phase structure is recommended. The ordering is driven by dependency analysis from ARCHITECTURE.md, validated against pitfall warnings from PITFALLS.md.

### Phase 1: Foundation Infrastructure
**Rationale:** Everything depends on this. Database for state, event bus for communication, shared types for data flow. Already partially complete (monorepo, Docker, NATS, shared models from Phase 01-03).
**Delivers:** Monorepo scaffolding, Docker stack, database schema, shared Pydantic/TypeScript models, NATS event bus (done), Alembic migrations
**Addresses:** Infrastructure prerequisites for all features
**Avoids:** Building on sand -- no agent can run without storage, events, and shared types

### Phase 2: Graph Engine + Agent Framework
**Rationale:** The graph engine is the core execution substrate. Without it, agents cannot be scheduled, executed, or coordinated. This is the **critical path** -- if the graph engine is wrong, everything built on top is wrong.
**Delivers:** Graph skeleton (Node, Edge, DirectedGraph), execution engine (topological sort, parallel execution), BaseAgent with PRA cycle, AgentNode wrapper, SharedState, validation gates on edges
**Addresses:** Graph-centric orchestration (primary differentiator), agent framework (foundation for all 30 agents)
**Avoids:** Error cascading (validation gates), agent role drift (role enforcement in BaseAgent), monolithic agent design

### Phase 3: Multi-LLM Abstraction + Context Management
**Rationale:** Agents need LLM access to reason and context to perceive. A crashing agent that reasons correctly is easier to fix than a durable agent that reasons poorly. LLM and context must exist before agents can function.
**Delivers:** Provider-agnostic LLM interface (LiteLLM wrapper), intelligent routing (RouteLLM), fallback chains, token tracking, context tiers (L0/L1/L2), vector store integration (LanceDB), Tree-sitter AST-based indexing
**Uses:** LiteLLM, RouteLLM, LanceDB, LlamaIndex, tree-sitter
**Avoids:** Context window exhaustion (L0/L1/L2 with token budgets), poor code retrieval (AST chunking + dependency graph), LLM gateway bottleneck (bypass mechanism)

### Phase 4: Temporal Integration + Pipeline Orchestration
**Rationale:** Once agents can execute within a graph, the next need is durability and lifecycle management for multi-hour pipeline runs. Quality gates enforce phase transitions.
**Delivers:** Temporal workflow definitions, Activity-StateGraph pattern, Pipeline Manager, Phase Coordinator, Checkpoint Manager, quality gates, pipeline presets (full/quick/review-only)
**Uses:** Temporal Python SDK, LangGraph (wrapped as activities)
**Avoids:** Dual orchestration complexity (clear boundary definition), Temporal determinism violations (strict workflow/activity separation)

### Phase 5: First Agents -- Vertical Slice
**Rationale:** Validate the entire architecture end-to-end with a minimal agent set before building all 30. This is the **validation checkpoint** -- it proves graph engine, LLM abstraction, context management, Temporal, event bus, and quality gates work together.
**Delivers:** Orchestrator agent, Backend Dev agent, Code Reviewer agent, Tester agent, Debugger agent. Minimal pipeline: Orchestrator -> Backend Dev -> Code Reviewer -> Tester -> Debugger.
**Addresses:** NL-to-code, test generation, self-healing debug loop, code review, human-in-the-loop (all on a single vertical path)
**Avoids:** Building 30 agents on an unvalidated foundation

### Phase 6: Worktree Manager + Sandbox Execution + CLI Agent Bridge
**Rationale:** The vertical slice validates single-agent execution. Full worktree isolation and sandbox execution are needed for parallel implementation agents. CLI agent bridge enables delegation to Claude Code / Codex CLI / Gemini CLI.
**Delivers:** Git worktree lifecycle management, Docker sandbox per agent, dynamic port allocation, per-worktree database isolation, CLI agent subprocess integration
**Addresses:** Agent isolation, sandbox execution, multi-agent parallelism
**Avoids:** Incomplete worktree isolation (per-worktree Docker profiles, port management), build artifact pollution

### Phase 7: Remaining Agents -- Full Breadth
**Rationale:** With infrastructure proven by the vertical slice, build the full 30-agent roster across all 10 SDLC categories. Each agent follows the validated BaseAgent interface and PRA cycle.
**Delivers:** All 30 agents across S0-S9, YAML-declarative agent configurations, composed graphs (CodingPipeline, ReviewGate, DebugFixLoop, ExperimentLoop), parallel execution in S3/S5/S6
**Addresses:** Full 11-stage SDLC pipeline (primary differentiator), all table stakes features, agent extensibility framework
**Avoids:** Agent role drift (structured output schemas, role enforcement), specification ambiguity

### Phase 8: Security Pipeline + Quality Gates
**Rationale:** Security tools scan code -- code must exist first. With agents producing code, integrate the full security pipeline with progressive validation cascade.
**Delivers:** Semgrep/Trivy/Gitleaks/SonarQube integration, 4-level progressive validation cascade, security quality gates, dependency allowlist, finding triage workflow
**Addresses:** Security scanning (table stakes), quality gates, supply chain protection
**Avoids:** AI-generated security vulnerabilities (scan after every generation step), false positive fatigue (start minimal, tune thresholds)

### Phase 9: FastAPI Server + React Dashboard
**Rationale:** Agents must be working before building the UI. The dashboard is critical for monitoring 30 agents but not on the critical path for execution -- agents run headlessly during development.
**Delivers:** REST API, WebSocket server, Socket.IO, React Flow pipeline visualization, Monaco editor, xterm.js terminal, real-time agent status, pipeline progress, cost dashboard
**Uses:** FastAPI, Socket.IO, React, Vite, Tailwind 4, shadcn/ui, React Flow, Monaco, xterm.js
**Avoids:** Dashboard re-render storms (event batching at 100ms, back-pressure, virtualization, Web Workers)

### Phase 10: CLI Application + Git Integration + Polish
**Rationale:** CLI is the primary developer interface. Git integration automates the developer workflow. Polish includes pipeline presets, cost tracking, and brownfield support.
**Delivers:** TypeScript CLI (project creation, pipeline execution, monitoring), automated branching/commits/PR creation, pipeline presets, cost tracking dashboard, brownfield codebase import
**Addresses:** CLI interface, git integration, pipeline presets, cost tracking

### Phase Ordering Rationale

- **Foundation before Engine:** You cannot run agents without storage, events, and shared types.
- **Graph Engine before LLM/Context:** The execution substrate must exist before agents can be scheduled. Building agents without the graph engine is like writing microservices without a container runtime.
- **LLM + Context before Temporal:** Agents need to reason and perceive before they need durability. Get the agent logic right first, then make it durable.
- **Vertical Slice before Breadth (Phase 5 before Phase 7):** Building 5 agents end-to-end proves the architecture faster than building 30 agents on an unvalidated foundation. The vertical slice is where "does this actually work?" gets answered.
- **Worktree + Sandbox before Full Agents:** Parallel execution requires isolation infrastructure. Build it between the vertical slice and the full agent roster.
- **Security after Implementation Agents:** Security tools scan code. Code must exist first. Wiring Semgrep before any agent produces code is premature.
- **Dashboard after Agents:** The dashboard visualizes agent activity. Without running agents, there is nothing to visualize. Agents run headlessly via Temporal's built-in UI during early development.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Graph Engine):** LangGraph 1.0 API patterns, StateGraph composition, Send API for dynamic fan-out. Complex integration with potential API evolution.
- **Phase 3 (Context Management):** Tree-sitter AST chunking strategies, hybrid vector + graph retrieval, token budget enforcement. Niche domain with limited production references.
- **Phase 4 (Temporal Integration):** Activity-StateGraph pattern implementation, serialization boundaries, determinism constraints. Dual-engine integration is novel.
- **Phase 6 (Worktree + Sandbox):** Per-worktree environment isolation, Docker Compose profiles, dynamic port allocation. Limited production references for AI agent-specific worktree management.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Standard monorepo, Docker, PostgreSQL, NATS -- well-documented, established patterns. Already partially complete.
- **Phase 8 (Security Pipeline):** Semgrep/Trivy/Gitleaks are standard DevSecOps tools with extensive documentation.
- **Phase 9 (Dashboard):** React + Vite + Tailwind + React Flow is a well-trodden path. WebSocket patterns are established.
- **Phase 10 (CLI + Polish):** Standard CLI development with Click/TypeScript. Git integration is well-documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All core technologies verified via official docs, release notes, and GitHub. Only Cognee, Letta, and RouteLLM carry MEDIUM confidence. |
| Features | HIGH | Extensive competitor analysis (6 products), market research (5+ reports), user feedback analysis. Clear consensus on table stakes vs. differentiators. |
| Architecture | HIGH | Validated against Google ADK patterns, LangChain architecture guidance, Confluent event-driven patterns, Grid Dynamics production case study, academic research (MAST taxonomy). |
| Pitfalls | HIGH | Based on NeurIPS 2025 research (150 failure traces), production reports, official documentation, and peer-reviewed security studies. |

**Overall confidence:** HIGH

### Gaps to Address

- **Cognee + Letta integration**: Both are fast-moving projects with potentially unstable APIs. Pin exact versions and test thoroughly before committing to them. Consider deferring to Phase 7+ if integration proves difficult.
- **LangGraph 1.0 durable execution overlap with Temporal**: LangGraph 1.0 added built-in durable execution. Monitor whether the dual-engine approach becomes redundant. May simplify to LangGraph-only if its durability proves sufficient.
- **RouteLLM production validation**: Published at ICLR 2025 with strong benchmarks (85% cost reduction, 95% quality retention) but limited production reports at CodeBot's scale. Validate with real routing decisions.
- **ExperimentLoop pattern at scale**: The keep/discard optimization loop is well-described in CodeBot's design docs and inspired by autoresearch, but large-scale production validation is limited. Needs careful testing in Phase 5 vertical slice.
- **Taskiq maturity**: ~1.8K stars, small community. The async-native NATS broker integration is ideal but less battle-tested than Celery. Have a fallback plan.

## Sources

### Primary (HIGH confidence)
- LangGraph 1.0 official announcement and documentation -- agent graph execution, StateGraph, Send API
- Temporal Python SDK documentation and production guidance -- durable workflows, activity patterns
- FastAPI release notes and documentation -- API framework, async patterns
- NATS JetStream documentation and anti-patterns guide -- event bus, ordering, scaling
- Anthropic context engineering guide -- tiered context management
- MAST taxonomy (arXiv:2503.13657, NeurIPS 2025) -- multi-agent failure analysis
- Google ADK multi-agent design patterns (InfoQ, Jan 2026) -- architecture validation
- Anthropic 2026 Agentic Coding Trends Report -- security vulnerability data
- Grid Dynamics case study -- LangGraph + Temporal integration validation

### Secondary (MEDIUM confidence)
- Confluent event-driven multi-agent guidance -- NATS architecture patterns
- RouteLLM paper (ICLR 2025) -- intelligent LLM routing
- Cognee and Letta GitHub repositories -- knowledge graph and agent memory
- Dagger, Pulumi, OpenTofu documentation -- CI/CD and IaC options
- Competitor product analyses (Devin, OpenHands, MetaGPT, Claude Code, Codex)
- Community production reports (Git worktrees, LiteLLM, JetStream ordering)

### Tertiary (LOW confidence)
- Taskiq NATS broker integration -- limited production reports
- ExperimentLoop pattern at scale -- inspired by autoresearch, limited validation
- LangGraph 1.0 durable execution as Temporal replacement -- too early to assess

---
*Research completed: 2026-03-18*
*Ready for roadmap: yes*
