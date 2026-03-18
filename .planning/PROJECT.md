# CodeBot

## What This Is

CodeBot is an autonomous, end-to-end software development platform powered by a graph-centric multi-agent system of 30 specialized AI agents. It transforms natural language ideas/PRDs into fully tested, reviewed, secured applications across web, mobile, and backend platforms. The system covers the complete SDLC from brainstorming through documentation, with optional cloud deployment. Built on MASFactory-inspired directed computation graphs (arXiv:2603.06007) with LangGraph as the graph engine and Temporal for durable workflow orchestration.

## Core Value

A user can describe an idea in natural language and get working, tested, security-scanned code out the other end — autonomously, through a multi-agent pipeline that handles planning, architecture, implementation, QA, testing, debugging, and documentation without manual coding.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Monorepo foundation (Turborepo, uv, pnpm workspaces) — Phase 01-01
- ✓ Shared Pydantic models + TypeScript types (agent-sdk, shared-types) — Phase 01-03
- ✓ NATS JetStream event bus with integration tests — Phase 01-03
- ✓ Docker stack configuration (PostgreSQL, Redis, NATS) — Phase 01-02
- ✓ Database schema (Alembic migrations) — Phase 01-02

### Active

<!-- Current scope. Building toward these. -->

**Agent Graph Engine**
- [ ] Directed graph runtime (nodes, edges, execution order, parallel execution)
- [ ] Node types: AGENT, SUBGRAPH, LOOP, SWITCH, HUMAN_IN_LOOP, PARALLEL, MERGE, CHECKPOINT, TRANSFORM
- [ ] SharedState for graph-level data flow between nodes
- [ ] YAML-declarative graph definitions
- [ ] Graph validation, cycle detection, and execution tracing
- [ ] Checkpoint/resume for long-running workflows

**Agent Framework**
- [ ] BaseAgent with Perception-Reasoning-Action (PRA) cognitive cycle
- [ ] AgentNode wrapper for graph execution
- [ ] Agent state machine (IDLE → INITIALIZING → EXECUTING → REVIEWING → COMPLETED/FAILED → RECOVERING)
- [ ] Agent isolation via git worktrees
- [ ] 30 specialized agents across 10 categories (Orchestration, Ideation, Planning, Research, Design, Implementation, Quality, Testing, Operations, Tooling)
- [ ] Agent configuration via YAML
- [ ] Agent skill/hook/tool creation (extensible ecosystem)

**Multi-LLM Abstraction Layer**
- [ ] Provider-agnostic interface for Anthropic (Claude), OpenAI (GPT-4o+), Google (Gemini), self-hosted (Ollama/vLLM/LocalAI)
- [ ] Intelligent routing by task type, complexity, privacy, cost, and latency
- [ ] Fallback chains and retry logic
- [ ] Token tracking and cost management
- [ ] Streaming support

**CLI Agent Integration**
- [ ] Claude Code subprocess/SDK integration
- [ ] OpenAI Codex CLI integration
- [ ] Gemini CLI integration
- [ ] Unified tool interface across CLI agents

**11-Stage SDLC Pipeline (S0–S9)**
- [ ] S0: Project initialization (PRD ingestion, multi-modal input, tech stack selection)
- [ ] S1: Brainstorming (idea exploration, competitive analysis, feature prioritization)
- [ ] S2: Research (technology research, best practices, pattern discovery)
- [ ] S3: Architecture & Design (system architecture, API design, database schema, UI/UX) — parallel
- [ ] S4: Planning (task decomposition, dependency graph, sprint planning)
- [ ] S5: Implementation (code generation across web/mobile/backend) — parallel
- [ ] S6: Quality Assurance (code review, security scanning, accessibility audit) — parallel
- [ ] S7: Testing (unit, integration, E2E test generation and execution)
- [ ] S8: Debug & Fix (automated debugging loop with root cause analysis)
- [ ] S9: Documentation (API docs, user guides, architecture docs)

**Context Management**
- [ ] 3-tier system: L0 (always in context), L1 (phase-scoped), L2 (on-demand retrieval)
- [ ] Vector store integration (ChromaDB/LanceDB/Qdrant)
- [ ] Tree-sitter code indexing
- [ ] Context compression and summarization

**Security Pipeline**
- [ ] Semgrep static analysis
- [ ] Trivy container/dependency scanning
- [ ] Gitleaks secret detection
- [ ] SonarQube integration
- [ ] Quality gates between pipeline phases

**FastAPI Server**
- [ ] REST API for project management, pipeline control, agent monitoring
- [ ] WebSocket for real-time updates
- [ ] Authentication & authorization
- [ ] Pipeline configuration endpoints (full, quick, review-only presets)

**React Dashboard**
- [ ] Real-time pipeline visualization (React Flow)
- [ ] Agent monitoring and status
- [ ] Code editor integration (Monaco Editor)
- [ ] Terminal emulator (xterm.js)
- [ ] CRDT-based real-time collaboration (Yjs)
- [ ] Socket.IO live updates

**CLI Application**
- [ ] TypeScript CLI for project management
- [ ] Pipeline execution and monitoring
- [ ] Agent interaction interface

**Event System**
- [ ] NATS JetStream pub/sub for inter-agent messaging
- [ ] Event-driven architecture (no direct agent-to-agent calls)
- [ ] Event replay and audit trail

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- S10 Cloud Deployment Automation — Deferred; users receive generated code with deployment docs. Can be triggered later on demand.
- Mobile app (native iOS/Android dashboard) — Web dashboard covers all use cases for v1
- Multi-repository orchestration — Focus on single-repo projects for v1
- Billing/payment system — Open-source, no monetization in v1
- Custom LLM fine-tuning — Use existing models via API/self-hosted

## Context

**Documentation state:** Comprehensive PRD v2.5, Architecture v2.5, System Design v2.5, Agent Catalog v2.5, and Agent Workflows documentation exists in `docs/`. These describe the complete system design and serve as the implementation blueprint.

**Existing code:**
- Monorepo scaffolding with Turborepo (`apps/server`, `apps/dashboard`, `apps/cli`, `libs/agent-sdk`, `libs/shared-types`, `libs/graph-engine`)
- Shared Pydantic models in `libs/agent-sdk/src/agent_sdk/models/` (agent, task, events, enums, pipeline, project)
- TypeScript type definitions in `libs/shared-types/src/` (mirroring Python models)
- Docker Compose stack for local development
- NATS JetStream event bus with integration tests
- Python virtual environment configured with uv

**Architecture paradigm:** MASFactory-inspired graph-centric multi-agent system. Workflows modeled as directed computation graphs. LangGraph for graph execution, Temporal for durable orchestration.

**Agent cognitive model:** All agents follow Perception-Reasoning-Action (PRA) cycle — perceive context, reason about approach, act on decisions, then self-review.

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
| LangGraph as graph engine | ~24.6K stars, MIT, native agent graph support, composable | — Pending |
| Temporal for durable workflows | ~18.9K stars, MIT, retry/checkpoint/resume built-in | — Pending |
| NATS JetStream for events | Lightweight, high-throughput, JetStream for persistence | ✓ Good |
| Turborepo for monorepo | Fast builds, good Python/Node hybrid support | ✓ Good |
| Defer S10 deployment | Reduces v1 scope significantly, deployment is opt-in anyway | — Pending |
| All 4 LLM providers in v1 | Core differentiator is provider flexibility | — Pending |
| Full React dashboard in v1 | Real-time visualization critical for monitoring 30 agents | — Pending |
| PRA cognitive cycle for agents | Structured perception-reasoning-action loop improves agent reliability | — Pending |

---
*Last updated: 2026-03-18 after reinitialization from updated docs v2.5*
