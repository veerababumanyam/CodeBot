# Project Research Summary

**Project:** CodeBot -- Autonomous Multi-Agent SDLC Platform
**Domain:** Graph-centric multi-agent AI development platform
**Researched:** 2026-03-18
**Confidence:** HIGH

## Executive Summary

CodeBot is an autonomous software development platform that orchestrates ~30 specialized AI agents across an 11-stage SDLC pipeline (S0-S9, with optional S10 deployment). The dominant production pattern for systems of this scale in 2026 is **hierarchical orchestrator-worker with dual-engine execution**: LangGraph handles agent decision logic within pipeline stages, while Temporal provides durable workflow coordination across stages. This dual-engine approach is validated by production case studies (Grid Dynamics, LinkedIn, Klarna) and avoids the known limitations of either framework alone. The foundation layer -- NATS JetStream event bus, PostgreSQL state store, shared Pydantic models, and Docker services -- is already implemented and tested, giving the project a strong starting position.

The recommended approach is a **vertical-slice-first build strategy**: establish the graph engine and agent framework, wire up LLM access and context management, then prove the entire architecture end-to-end with a minimal 5-agent pipeline before building out the full 30-agent roster. This avoids the most dangerous pitfall in multi-agent systems -- building breadth on an unvalidated foundation. Feature research confirms that CodeBot's primary differentiator (full SDLC coverage with graph-based orchestration) has no direct competitor; Devin, OpenHands, MetaGPT, Claude Code, and Codex all cover subsets of the pipeline. Table-stakes features (NL-to-code, multi-file generation, security scanning, human-in-the-loop, Git integration) must ship in v1, while advanced capabilities (CRDT collaboration, multi-repo orchestration, automated deployment) belong in v2+.

The top risks are: (1) **error cascading** across the 30-agent chain where one bad output in S3 silently corrupts everything downstream -- mitigated by validation gates on every graph edge; (2) **dual orchestration complexity** from running LangGraph + Temporal -- mitigated by strict boundary definitions and prototyping the integration early; (3) **context window exhaustion** in multi-step workflows -- mitigated by rigorous L0/L1/L2 tiered context management; and (4) **AI-generated code security vulnerabilities** (48-62% of AI code has vulnerabilities) -- mitigated by scanning after every code generation step, not just at the S6 quality gate. All four risks have well-documented prevention strategies and should be addressed in the earliest build phases.

## Key Findings

### Recommended Stack

The stack is mature, well-validated, and largely already configured in the monorepo. Python 3.12+ with FastAPI powers the backend. LangGraph 1.0 (stable since October 2025, 24.6K stars) handles graph-based agent execution. Temporal (18.9K stars, MIT) provides durable workflow orchestration. LiteLLM (39K stars, 8ms P95 latency at 1K RPS) serves as the multi-LLM gateway supporting 100+ providers. The frontend uses React + Vite + Tailwind 4 + shadcn/ui with React Flow for pipeline visualization.

**Core technologies:**
- **LangGraph 1.0+**: Agent graph execution (StateGraph, Send API for dynamic fan-out, conditional routing) -- the only framework that natively supports CodeBot's DAG-based agent orchestration model
- **Temporal Python SDK 1.4+**: Durable workflow lifecycle, retry/checkpoint/resume for multi-hour pipeline runs -- complements LangGraph by handling crash recovery
- **LiteLLM 1.82+**: Unified multi-LLM gateway with cost tracking, load balancing, and fallback chains -- already running in Docker Compose
- **FastAPI 0.135+**: Async-native REST/WebSocket API with Pydantic v2 integration -- the standard Python API framework
- **NATS JetStream 2.x**: Inter-agent event bus with persistence and replay -- already implemented and tested
- **LanceDB 0.29+ / Qdrant 1.17+**: Vector store for dev (embedded, zero-config) and production (distributed, GPU-accelerated) respectively
- **LlamaIndex 0.14+**: RAG pipeline orchestration with 300+ integrations -- feeds curated context to agents
- **React + Vite + Tailwind 4 + shadcn/ui + React Flow**: Dashboard stack with real-time pipeline visualization
- **FastMCP 3.1+**: MCP server framework for exposing agent tools with streamable HTTP transport

**Version pinning note:** Core frameworks (FastAPI, LangGraph, Temporal) pin major+minor. Young/fast-moving libraries (Cognee, Letta, RouteLLM) pin exact versions due to API instability.

### Expected Features

**Must have (table stakes -- v1):**
- Natural language to multi-file code generation (core pipeline S0-S5)
- Automated test generation and self-healing debug loop (S7-S8)
- Git integration (branches, PRs, automated commits)
- Security scanning with quality gates (Semgrep + Trivy + Gitleaks at S6)
- Multi-LLM support (Anthropic + OpenAI + Google + self-hosted)
- Human-in-the-loop approval gates at phase boundaries
- Real-time progress visibility (React Flow dashboard + WebSocket)
- CLI interface for project creation and pipeline execution
- Sandbox execution (Docker containers per agent)
- 3-tier context management (L0/L1/L2) with vector store
- Checkpoint/resume via Temporal

**Should have (differentiators -- v1.x):**
- Full 11-stage SDLC pipeline with 30 specialized agents (primary differentiator -- no competitor has this)
- Intelligent LLM routing per task type (Claude for architecture, GPT for code gen, local models for boilerplate)
- Self-hosted / air-gapped operation (no competitor offers full offline mode)
- Pipeline presets (full, quick, review-only)
- Cost tracking per agent/stage/model
- Brownfield / legacy codebase support
- Agent extensibility (Skill/Hook/Tool creators)

**Defer (v2+):**
- Real-time CRDT collaboration (very high complexity, not needed for core pipeline)
- Multi-repository orchestration (enormous complexity, single-repo must be proven first)
- Automated cloud deployment (S10) -- generate configs in v1, automate in v2
- Plugin/extension marketplace (requires stable APIs first)
- IDE extensions (VS Code, JetBrains)
- Team features (multi-user, RBAC)

### Architecture Approach

The architecture follows a **5-layer model**: Interaction (Dashboard + CLI), API & Protocol (FastAPI gateway), Orchestration (dual-engine: Temporal for pipeline lifecycle + LangGraph for agent logic), Agent & Component (30 agents with BaseAgent + PRA cognitive cycle), and Foundation (LLM abstraction, context management, security pipeline, event bus, databases). All inter-agent communication flows through NATS JetStream or SharedState -- agents never communicate directly. The Activity-StateGraph pattern (wrapping LangGraph graphs as Temporal activities) is the fundamental integration mechanism. The Supervisor-Worker pattern with dynamic fan-out (LangGraph's Send API) handles parallel execution in S3, S5, and S6.

**Major components:**
1. **Graph Engine (LangGraph StateGraphs)** -- Agent decision logic, conditional routing, dynamic fan-out via Send API, supervisor patterns
2. **Pipeline Orchestrator (Temporal Workflows)** -- Durable pipeline lifecycle, cross-phase gates, retry/timeout, checkpoint/resume
3. **Multi-LLM Abstraction (LiteLLM + RouteLLM)** -- Provider-agnostic LLM access, intelligent routing, fallback chains, cost tracking
4. **Context Management (L0/L1/L2)** -- Tiered context assembly, vector store retrieval, Tree-sitter code indexing, compression
5. **Agent Framework (BaseAgent + PRA cycle)** -- Standard contract for all 30 agents, perception-reasoning-action loop, self-review
6. **Security Pipeline (Semgrep/Trivy/Gitleaks)** -- Progressive validation cascade (4 levels), quality gates between phases
7. **Worktree Manager** -- Git worktree creation/cleanup per coding agent, branch isolation, sequential merge
8. **Event Bus (NATS JetStream)** -- Inter-agent messaging, event streaming, audit trail, replay (already implemented)
9. **React Dashboard** -- Pipeline visualization (React Flow), agent monitoring, code editing (Monaco), terminal (xterm.js)

### Critical Pitfalls

1. **Error cascading across agent chain** -- One bad output amplifies through 30 downstream agents; research shows 41-87% failure rates in multi-agent systems with cascading as the primary amplifier. Prevent with validation gates on every graph edge, Challenger verification agents, and rollback to last-known-good checkpoint.

2. **Dual orchestration complexity (LangGraph + Temporal)** -- State in two places, split observability, serialization overhead at activity boundaries. Prevent by defining strict boundaries (Temporal = cross-stage durability, LangGraph = intra-stage logic), unified trace IDs, and prototyping the integration before building the full pipeline.

3. **Context window exhaustion** -- 50-step workflows burn through context windows; agents continue with partial context and produce confident but incorrect results. Prevent with rigorous L0/L1/L2 implementation, hard token budgets per agent call, tool output compression, and context observability metrics.

4. **AI-generated code security vulnerabilities** -- 48-62% of AI code has vulnerabilities; ~20% of code samples hallucinate non-existent packages (slopsquatting). Prevent by scanning after every code generation step, dependency allowlists, and security-specific debugging in S8.

5. **Git worktree isolation gaps** -- Worktrees isolate filesystems but NOT runtime environments (shared ports, databases, Docker daemon). Prevent with per-worktree Docker Compose profiles, dynamic port allocation, worktree lifecycle management, and disk quotas.

## Implications for Roadmap

Based on combined research, the suggested build order follows a **foundation-first, vertical-slice-validation, then breadth** strategy. The ordering is driven by dependency analysis from ARCHITECTURE.md, validated against pitfall warnings from PITFALLS.md, and aligned with feature priorities from FEATURES.md.

### Phase 1: Foundation Infrastructure
**Rationale:** Everything depends on the database, event bus, shared models, and Docker stack. Cannot run agents without state storage, cannot communicate without the event bus, cannot validate types without shared models.
**Delivers:** Monorepo scaffolding, Docker Compose stack, PostgreSQL schema (all 16 ORM models), shared Pydantic/TypeScript models, NATS JetStream event bus, Alembic migrations.
**Status:** LARGELY COMPLETE per existing commits (01-01 through 01-03). Validate and move forward.
**Addresses:** Infrastructure prerequisites for all pipeline stages.
**Avoids:** Pitfall #7 (NATS ordering) -- validate ordering guarantees under concurrent load now.

### Phase 2: Graph Engine + Agent Framework
**Rationale:** This is the CRITICAL PATH. The graph engine is the execution substrate for all 30 agents. Without it, nothing above can run. Building agents against an unvalidated engine guarantees rework.
**Delivers:** DirectedGraph with Node/Edge primitives, Execution Engine (topological sort, parallel execution via asyncio TaskGroup), BaseAgent with PRA cognitive cycle, AgentNode wrapper, SharedState for inter-node data flow, validation gates on graph edges.
**Uses:** LangGraph 1.0 StateGraph, Send API, conditional edges; asyncio TaskGroup for concurrency.
**Implements:** Layer 2 (Agent & Component Layer) foundation and Layer 3 (Orchestration Layer) graph execution.
**Avoids:** Pitfall #1 (error cascading -- build validation gates into graph edges), Pitfall #13 (agent role drift -- build role enforcement into BaseAgent), Pitfall #14 (LangGraph API instability -- pin version, create wrapper layer).

### Phase 3: Multi-LLM Abstraction + Context Management
**Rationale:** Agents need LLM access to reason and context to perceive. A crashing agent that reasons correctly is easier to fix than a durable agent that reasons poorly. These are the "senses" of every agent.
**Delivers:** Provider-agnostic LLM interface (LiteLLM wrapper), intelligent routing (RouteLLM), fallback chains, token/cost tracking, L0/L1/L2 context tiers, vector store integration (LanceDB), Tree-sitter code indexing, context compression.
**Uses:** LiteLLM 1.82+, RouteLLM, LanceDB 0.29+, LlamaIndex 0.14+, tree-sitter, ast-grep.
**Implements:** Layer 1 (Foundation Layer) LLM and context subsystems.
**Avoids:** Pitfall #3 (context window exhaustion -- implement L0/L1/L2 rigorously with token budgets), Pitfall #6 (LLM gateway bottleneck -- benchmark under load, build bypass mechanism), Pitfall #10 (poor code retrieval -- use Tree-sitter AST chunking + dependency graph hybrid).

### Phase 4: Temporal Integration + Pipeline Orchestration
**Rationale:** Once agents can execute within a graph, the next need is durability and lifecycle management for long-running pipelines. Temporal provides retry, timeout, and checkpoint/resume.
**Delivers:** Temporal workflow definitions, Activity-StateGraph integration pattern, Pipeline Manager, Phase Coordinator, Checkpoint Manager, quality gates, human-in-the-loop approval flows.
**Uses:** Temporal Python SDK 1.4+, Pydantic v2 for serializable state boundaries.
**Implements:** Layer 3 (Orchestration Layer) durability and lifecycle management.
**Avoids:** Pitfall #2 (dual orchestration complexity -- strict boundary: Temporal = cross-stage, LangGraph = intra-stage), Pitfall #9 (Temporal determinism violations -- all business logic in Activities, never in Workflows).

### Phase 5: Vertical Slice (First Agents End-to-End)
**Rationale:** VALIDATION CHECKPOINT. Prove the entire architecture works with a minimal 5-agent pipeline before building breadth. Exercises every layer: graph engine, LLM abstraction, context management, Temporal durability, event bus, and quality gates.
**Delivers:** 5 working agents (Orchestrator, Backend Dev, Code Reviewer, Tester, Debugger) in a complete mini-pipeline, end-to-end proof of architecture.
**Addresses:** NL-to-code, test generation, self-healing debug loop, security scanning, human-in-the-loop.
**Avoids:** Building 30 agents on an unvalidated foundation. Validates error cascading prevention actually works before scaling.

### Phase 6: Worktree Manager + CLI Agent Bridge + Security Pipeline
**Rationale:** Full worktree isolation and CLI agent delegation are prerequisites for parallel implementation agents. Security scanning must be wired in before building the full agent roster that will generate code at volume.
**Delivers:** Git worktree creation/cleanup, branch management, Claude Code/Codex CLI/Gemini CLI subprocess integration, Semgrep/Trivy/Gitleaks integration, Progressive Validation Cascade (4-level quality gates), dependency allowlist.
**Uses:** GitPython, Semgrep, Trivy, Gitleaks, SonarQube.
**Avoids:** Pitfall #5 (worktree isolation gaps -- per-worktree Docker profiles, dynamic ports), Pitfall #4 (security vulnerabilities -- scan after every generation step), Pitfall #11 (false positive fatigue -- start with minimal high-confidence rules).

### Phase 7: Remaining Agents (Full Breadth)
**Rationale:** With infrastructure proven by the vertical slice, build out the full 30-agent roster. Each agent follows the validated BaseAgent interface and PRA cycle.
**Delivers:** All 30 agents across 10 categories (S0-S9), YAML-declarative agent configurations, ComposedGraphs (CodingPipeline, ReviewGate, DebugFixLoop, ExperimentLoop), parallel execution in S3/S5/S6.
**Addresses:** Full 11-stage SDLC pipeline (primary differentiator), structured brainstorming (S1), dedicated research phase (S2), comprehensive QA (security, code review, accessibility, performance, i18n).
**Avoids:** Pitfall #13 (agent role drift -- structured output schemas, role enforcement per agent).

### Phase 8: FastAPI Server + React Dashboard
**Rationale:** The backend must be working before building the UI. Agents can run headless via Temporal's built-in UI during earlier phases. The dashboard is critical for monitoring 30 agents but is not on the critical path for agent execution.
**Delivers:** REST API, WebSocket server, Socket.IO integration, React dashboard with React Flow pipeline visualization, Monaco editor, xterm.js terminal, real-time agent status updates, cost dashboard.
**Uses:** FastAPI, Socket.IO, React, Vite, Tailwind 4, shadcn/ui, React Flow, Monaco Editor, xterm.js, Zustand, TanStack Query.
**Avoids:** Pitfall #8 (dashboard re-render storms -- event batching at 100ms intervals, back-pressure, virtualization, Web Workers for aggregation).

### Phase 9: CLI Application + Git Integration + Polish
**Rationale:** CLI is the primary developer interface. Build after the API exists for it to call.
**Delivers:** TypeScript CLI for project creation/pipeline execution/agent monitoring, automated branching/commits/PR creation, pipeline presets (full/quick/review-only), cost tracking, brownfield codebase import.
**Addresses:** CLI interface, git integration, pipeline presets, cost tracking -- the v1.x differentiators.

### Phase 10: Advanced Features + Hardening
**Rationale:** Post-validation features that differentiate CodeBot but are not required for MVP. Production hardening based on real usage.
**Delivers:** Self-hosted/air-gapped mode, brownfield codebase support, live preview during build, agent extensibility framework, additional language support.
**Addresses:** v1.x differentiators that push CodeBot beyond competitors without blocking core v1 launch.

### Phase Ordering Rationale

- **Foundation before everything:** Database, event bus, and shared models are dependencies of every other component. Already done.
- **Graph engine is the critical path:** Every agent, every pipeline stage, every execution pattern depends on the graph engine. If the graph engine is wrong, everything built on top is wrong.
- **LLM + Context before Temporal:** Agents need to reason (LLM) and perceive (context) before they need durability (Temporal). Correct reasoning is a harder problem than crash recovery.
- **Vertical slice before breadth:** Building 5 agents end-to-end proves the architecture faster than building 30 agents against an unvalidated foundation. This is the research's strongest recommendation.
- **Security pipeline before full agent roster:** Security tools must be integrated and tested before 30 agents start generating potentially vulnerable code at volume.
- **Dashboard after agents:** The dashboard visualizes agent activity. Without running agents, there is nothing useful to visualize. Temporal's built-in UI serves for early development.
- **CLI after API:** The CLI calls the API. The API must exist first.

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 2 (Graph Engine):** LangGraph 1.0 API patterns for CodeBot's specific node types (LOOP, SWITCH, HUMAN_IN_LOOP, PARALLEL, MERGE) may require creative patterns beyond standard documentation. Research the Send API for dynamic fan-out and supervisor patterns in depth.
- **Phase 4 (Temporal Integration):** The Activity-StateGraph pattern has limited production documentation beyond a single POC. The serialization boundary design is critical and easy to get wrong. Research Temporal's versioning APIs for workflow evolution.
- **Phase 6 (Worktree Manager):** Full runtime isolation beyond filesystem (ports, databases, Docker) has sparse documentation. The ccswarm and Pochi projects are the best references but are small-scale.
- **Phase 7 (Remaining Agents):** Agent prompt engineering for 30 distinct roles requires domain-specific research. The MAST taxonomy (NeurIPS 2025) provides failure mode guidance.

**Phases with standard patterns (can skip deep research):**
- **Phase 1 (Foundation):** Already complete. Standard Docker/PostgreSQL/NATS patterns.
- **Phase 3 (LLM + Context):** LiteLLM, LlamaIndex, and Tree-sitter are well-documented with extensive examples.
- **Phase 8 (Dashboard):** React + WebSocket + React Flow is a well-documented pattern with production examples.
- **Phase 9 (CLI):** Standard TypeScript CLI development.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All core technologies verified via official docs, release notes, and GitHub. Only Cognee, Letta, and RouteLLM carry MEDIUM confidence due to younger ecosystems. |
| Features | HIGH | Comprehensive competitor analysis across 6 platforms (Devin, OpenHands, MetaGPT, Claude Code, Codex, MGX). Backed by 2026 industry reports (Anthropic, Deloitte), academic perspectives (MIT), and user feedback analysis. |
| Architecture | HIGH | Hierarchical orchestrator-worker validated against Google ADK patterns, LangChain guidance, Confluent event-driven patterns, Grid Dynamics case study, and MAST taxonomy. Dual-engine and tiered context are converged best practices. |
| Pitfalls | HIGH | Based on NeurIPS 2025 research (150 failure traces across 7 systems), production reports, OWASP Agentic AI Top 10, official documentation, and peer-reviewed security studies. 14 pitfalls with specific prevention strategies. |

**Overall confidence:** HIGH

### Gaps to Address

- **Activity-StateGraph pattern in practice:** The Temporal + LangGraph integration has limited production documentation beyond a single POC. Build a prototype of this boundary in Phase 2/4 before committing to the full pattern. If LangGraph 1.0's built-in durable execution proves sufficient, Temporal may be unnecessary for some phases.
- **30-agent coordination at scale:** No public reference for a system with exactly this topology (30 agents, 11 stages, parallel fan-out). The vertical slice in Phase 5 must validate coordination patterns before scaling. Monitor NATS consumer counts against the ~100K limit.
- **RouteLLM production readiness:** Published at ICLR 2025 with promising results (85% cost reduction) but production deployment reports are sparse. Validate routing quality with CodeBot's specific task mix before relying on it for cost optimization.
- **Cognee and Letta API stability:** Both are younger projects (MEDIUM confidence). APIs may shift between minor versions. Pin exact versions and evaluate whether the value justifies the integration risk, or whether simpler alternatives (direct LanceDB + manual memory tiers) suffice for v1.
- **Git worktree full-stack isolation:** No turnkey solution exists for per-worktree runtime isolation (ports, databases, Docker). This will require custom engineering in Phase 6. Plan for more implementation time than typical infrastructure work.

## Sources

### Primary (HIGH confidence)
- LangGraph 1.0 Announcement and Documentation (blog.langchain.com)
- Temporal Python SDK and Production Guidance (temporal.io, pypi.org)
- FastAPI Release Notes and Documentation (fastapi.tiangolo.com)
- LiteLLM v1.82 Release Notes and GitHub (docs.litellm.ai, github.com/BerriAI/litellm)
- NATS JetStream Architecture and Anti-Patterns (docs.nats.io, synadia.com)
- Anthropic Context Engineering Guide (anthropic.com/engineering)
- MAST Taxonomy -- NeurIPS 2025 (arXiv:2503.13657) -- multi-agent failure analysis
- Codified Context Paper (arXiv:2602.20478) -- tiered context patterns
- Google Multi-Agent Design Patterns (InfoQ, Jan 2026)
- OWASP Agentic AI Top 10 (legitsecurity.com) -- security vulnerability data
- Anthropic 2026 Agentic Coding Trends Report -- AI code security statistics
- Tailwind CSS v4, shadcn/ui, React Flow, Zustand, TanStack Query (official docs)

### Secondary (MEDIUM confidence)
- Temporal + LangGraph Integration POC (DeepWiki, anup.io)
- Grid Dynamics LangGraph Migration Case Study
- RouteLLM (GitHub, ICLR 2025 paper)
- Cognee and Letta (GitHub repositories, community reports)
- Confluent Event-Driven Multi-Agent Guidance
- Dagger, Taskiq, Pulumi, OpenTofu (GitHub, comparison articles)
- Competitor analysis (Devin, OpenHands, MetaGPT, Claude Code, Codex, MGX)
- Industry reports (Deloitte AI Agent Orchestration, State of AI Coding Agents 2026)
- Git worktree isolation community reports (ccswarm, Pochi, Nx Blog, Upsun)

### Tertiary (LOW confidence)
- Git worktree full-stack isolation patterns (community blogs, small OSS projects)
- 30-agent-scale coordination (inferred from smaller-scale production reports)
- Taskiq NATS broker integration (limited production reports)
- ExperimentLoop pattern at scale (inspired by autoresearch, limited validation)

---
*Research completed: 2026-03-18*
*Ready for roadmap: yes*
