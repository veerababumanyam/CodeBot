# Architecture Research

**Domain:** Autonomous multi-agent software development platform (SDLC automation)
**Researched:** 2026-03-18
**Confidence:** HIGH — Extensively documented in existing project docs, cross-referenced with reference implementations (MASFactory, Automaker, Codebuff, Superset, OpenViking, OpenSandbox)

---

## Standard Architecture

### System Overview

The canonical architecture for autonomous multi-agent SDLC platforms follows a five-layer model. The execution substrate is a directed computation graph (DAG), with agents as nodes and data/control dependencies as edges. All major components ultimately connect to the graph engine, which governs scheduling and state flow.

```
+=========================================================================+
|  LAYER 5 -- INTERACTION LAYER                                           |
|  Web Dashboard (React/Vite)  |  CLI (TypeScript)  |  IDE Extensions    |
+=========================================================================+
          |                           |                     |
          v                           v                     v
+=========================================================================+
|  LAYER 4 -- PROTOCOL LAYER                                              |
|  FastAPI + Socket.IO Gateway  |  WebSocket Event Bus  |  REST API       |
|  Message Adapter              |  Context Adapter      |  NATS JetStream |
+=========================================================================+
          |                           |                     |
          v                           v                     v
+=========================================================================+
|  LAYER 3 -- COMPONENT LAYER                                             |
|  ~30 Specialized Agents  |  Composed Graphs  |  Node Templates          |
|  Loop / Switch / Parallel / Merge / HITL / Checkpoint / Transform nodes |
+=========================================================================+
          |                           |                     |
          v                           v                     v
+=========================================================================+
|  LAYER 2 -- ENGINE LAYER                                                |
|  Agent Graph Engine (DAG)     |  Task Scheduler (topo sort)            |
|  Pipeline Manager             |  Checkpoint Manager  |  Agent Pool Mgr |
|  Execution Runtime (asyncio)  |  Resource Governor   |  Event Bus       |
+=========================================================================+
          |                           |                     |
          v                           v                     v
+=========================================================================+
|  LAYER 1 -- FOUNDATION LAYER                                            |
|  Multi-LLM Abstraction  |  CLI Agent Bridge  |  Context Mgr (L0/L1/L2) |
|  Worktree Manager       |  Sandbox Manager   |  Security Pipeline       |
|  PostgreSQL + Redis     |  Vector Store      |  Object Store  |  NATS   |
+=========================================================================+
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Agent Graph Engine | DAG execution runtime: topological sort, parallel layer execution, conditional edges, loop/switch evaluation | LangGraph (primary), custom DirectedGraph class over it |
| Pipeline Manager | SDLC phase coordination, phase transition gates, multi-preset support (full/quick/review-only) | Python + YAML-declarative pipeline configs |
| Task Scheduler | Kahn's algorithm for topological ordering; selects ready nodes per layer | asyncio.TaskGroup for concurrent layer execution |
| Checkpoint Manager | State snapshots after each execution layer; enables pipeline resume on failure | PostgreSQL (checkpoint records) + Redis (live state cache) |
| Agent Pool Manager | Lifecycle management for all running agents; enforces concurrency limits | Bounded semaphore + process pool |
| Multi-LLM Abstraction | Provider-agnostic interface for OpenAI, Anthropic, Google, Ollama, LM Studio; routing, fallback chains, cost tracking | Custom LLMProvider Protocol; per-provider adapter classes |
| CLI Agent Bridge | Delegates coding to Claude Code (SDK), Codex CLI, Gemini CLI; manages subprocess lifecycle and output parsing | Claude Agent SDK (direct); subprocess + structured output parse (Codex, Gemini) |
| Context Manager | 3-tier hierarchical context assembly (L0 always-loaded, L1 on-demand, L2 deep retrieval) | Filesystem + ChromaDB + RAG pipeline |
| Worktree Manager | Git worktree isolation per coding agent; lifecycle (provision, execute, merge, cleanup) | git worktree commands; branch-per-agent strategy |
| Sandbox Manager | Docker container per agent for safe code execution; CPU/mem/network limits; gVisor or Kata isolation | Docker SDK (Python); seccomp + AppArmor profiles |
| Security Pipeline | Parallel SAST, DAST, secrets, SCA, IaC, license scanning; normalized finding schema; quality gate | Semgrep, SonarQube, Shannon, Trivy, Gitleaks, ORT, KICS (CLI subprocess + REST) |
| Web Dashboard | Real-time pipeline visualization, agent activity, code viewer, test results, cost tracker, architecture visualizer | React (Vite) + TypeScript 5.5 + Tailwind CSS + Zustand; React Flow for graph |
| CLI Interface | All user-facing commands (init, start, status, review, deploy, config); programmatic API | TypeScript (Node.js 22 LTS or Bun) |
| Event Bus | Asynchronous agent-to-agent messaging (TASK_HANDOFF, REVIEW_REQUEST, ESCALATION etc.); real-time dashboard streaming | NATS JetStream (at-least-once, persistent) |
| Data Layer | Durable state: projects, pipeline runs, agent tasks, LLM usage logs, security findings, memory | PostgreSQL 16 (relational) + Redis 7 (cache/pubsub) + ChromaDB (vectors) + MinIO/S3 (objects) |
| Knowledge Graph | Architecture decisions, code dependency graph, requirement traceability | Cognee |

---

## Recommended Project Structure

```
codebot/                          # Turborepo monorepo root
├── apps/
│   ├── server/                   # FastAPI backend (Python 3.12+)
│   │   └── src/codebot/
│   │       ├── main.py           # FastAPI entrypoint
│   │       ├── graph/            # Agent Graph Engine
│   │       │   ├── engine.py     # ExecutionEngine, DAG runtime
│   │       │   ├── nodes.py      # Node types (AGENT, LOOP, SWITCH, PARALLEL, MERGE, HITL, CHECKPOINT, TRANSFORM, GATE)
│   │       │   ├── edges.py      # Edge types (STATE_FLOW, MESSAGE_FLOW, CONTROL_FLOW)
│   │       │   ├── scheduler.py  # Topological sort, layer execution
│   │       │   └── templates.py  # NodeTemplate, ComposedGraph
│   │       ├── pipeline/         # SDLC Pipeline Manager
│   │       │   ├── manager.py    # Phase coordination, gate evaluation
│   │       │   ├── presets/      # full.yaml, quick.yaml, review-only.yaml
│   │       │   └── checkpoint.py # Snapshot + resume logic
│   │       ├── agents/           # ~30 specialized agent implementations
│   │       │   ├── base.py       # BaseAgent (shared lifecycle, tools, context)
│   │       │   ├── orchestrator.py
│   │       │   ├── brainstormer.py
│   │       │   ├── researcher.py
│   │       │   ├── architect.py
│   │       │   ├── designer.py
│   │       │   ├── planner.py
│   │       │   ├── frontend_dev.py
│   │       │   ├── backend_dev.py
│   │       │   ├── middleware_dev.py
│   │       │   ├── infra_engineer.py
│   │       │   ├── code_reviewer.py
│   │       │   ├── security_auditor.py
│   │       │   ├── tester.py
│   │       │   ├── debugger.py
│   │       │   ├── doc_writer.py
│   │       │   ├── delivery.py
│   │       │   └── project_manager.py
│   │       ├── llm/              # Multi-LLM Abstraction Layer
│   │       │   ├── router.py     # Routing rules + fallback chains
│   │       │   ├── providers/    # Per-provider adapters (anthropic, openai, google, ollama, lmstudio)
│   │       │   └── cost.py       # Token budget enforcement + usage tracking
│   │       ├── cli_agents/       # CLI Agent Integration Layer
│   │       │   ├── bridge.py     # Agent Bridge: task translate + output parse
│   │       │   ├── claude_code.py # Claude Agent SDK integration
│   │       │   ├── codex.py      # OpenAI Codex CLI subprocess
│   │       │   └── gemini.py     # Gemini CLI subprocess
│   │       ├── context/          # 3-Tier Context Management
│   │       │   ├── adapter.py    # Context assembly pipeline
│   │       │   ├── tiers.py      # L0/L1/L2 loaders
│   │       │   ├── indexer.py    # Tree-sitter code indexing
│   │       │   ├── retrieval.py  # Vector + BM25 hybrid retrieval
│   │       │   └── memory.py     # Episodic memory (cross-session, cross-project)
│   │       ├── worktree/         # Git Worktree Manager
│   │       │   └── manager.py    # Provision, execute, merge, cleanup lifecycle
│   │       ├── sandbox/          # Sandbox Execution Manager
│   │       │   ├── manager.py    # Docker container lifecycle
│   │       │   └── preview.py    # Live preview (hot-reload, VNC)
│   │       ├── security/         # Security & Quality Pipeline
│   │       │   ├── pipeline.py   # Orchestrates parallel scanner fan-out
│   │       │   ├── scanners/     # Per-tool runner (semgrep, trivy, gitleaks, etc.)
│   │       │   ├── aggregator.py # Normalize + deduplicate findings
│   │       │   └── gate.py       # Quality gate evaluation
│   │       ├── events/           # Event Bus (NATS JetStream)
│   │       │   └── bus.py        # Publish / subscribe / streaming to dashboard
│   │       └── api/              # FastAPI routers
│   │           ├── projects.py
│   │           ├── runs.py
│   │           ├── agents.py
│   │           └── ws.py         # WebSocket endpoint (Socket.IO)
│   ├── dashboard/                # React (Vite) + TypeScript dashboard
│   │   └── src/
│   │       ├── components/       # Pipeline view, agent cards, code viewer, etc.
│   │       ├── stores/           # Zustand state slices
│   │       └── api/              # REST + WebSocket client
│   └── cli/                      # TypeScript CLI (Node.js 22 LTS or Bun)
│       └── src/
│           └── commands/         # init, brainstorm, plan, start, status, review, deploy, config
├── libs/
│   ├── agent-sdk/                # Python agent base classes and tool bindings
│   ├── graph-engine/             # Core DAG primitives (importable by server)
│   └── shared-types/             # TypeScript types shared between dashboard and CLI
├── sdks/
│   ├── python/                   # Python client SDK (publish to PyPI)
│   └── typescript/               # TypeScript client SDK (publish to npm)
├── configs/                      # YAML-declarative pipeline + agent configs
│   ├── pipelines/                # full.yaml, quick.yaml, review-only.yaml
│   ├── agents/                   # Per-agent role templates
│   └── providers/                # LLM provider routing configs
├── docker-compose.yml            # Local dev: postgres, redis, chroma, minio, sonarqube, ragflow
├── Makefile                      # Common commands
├── pyproject.toml                # Python workspace root (uv)
├── package.json                  # Node.js workspace root (pnpm)
└── turbo.json                    # Turborepo build pipeline
```

### Structure Rationale

- **apps/server/src/codebot/graph/:** Core execution engine isolated from agents — graph engine can be tested and evolved independently of agent implementations
- **apps/server/src/codebot/agents/:** One file per agent role keeps concerns isolated; all inherit BaseAgent to enforce lifecycle contract
- **apps/server/src/codebot/llm/:** Provider adapters behind a Protocol interface — adding a new provider requires only a new adapter, no other changes
- **apps/server/src/codebot/cli_agents/:** Separate from `llm/` because CLI agents (Claude Code, Codex) are subprocess-based coding tools, not LLM API completions
- **libs/graph-engine/:** Extracted to a lib so it can be imported by both the server and potentially SDKs without circular imports
- **configs/:** YAML-declarative configurations drive the pipeline at runtime — changing a pipeline preset requires no code changes

---

## Architectural Patterns

### Pattern 1: Directed Computation Graph (DAG) with Topological Layer Execution

**What:** The entire SDLC pipeline is modeled as a DAG. Nodes are agents or control structures (loop, switch, parallel, merge). Edges are typed (STATE_FLOW, MESSAGE_FLOW, CONTROL_FLOW). A topological sort groups nodes into execution layers. Nodes within a layer have no dependencies on each other and execute concurrently via `asyncio.TaskGroup`. Each layer completes before the next begins.

**When to use:** Any multi-agent workflow where tasks have dependencies. The graph model makes dependencies explicit, enables automatic parallelism discovery, and allows the system to resume from checkpoints.

**Trade-offs:** Graph compilation adds startup latency. Loop nodes (debug-fix cycles) require explicit cycle handling (loops are explicit constructs, not graph cycles). Dynamic graph mutation at runtime is complex and should be avoided — route via SwitchNode instead.

**Example:**
```python
# Execution layer model — all nodes in a layer run concurrently
async def run_layer(layer: list[Node], state: SharedState) -> None:
    async with asyncio.TaskGroup() as tg:
        for node in layer:
            if all_conditions_met(node, state):
                tg.create_task(node.execute(state))
```

### Pattern 2: 3-Tier Context Management (L0/L1/L2)

**What:** Agent context is assembled in three tiers before each invocation. L0 (~2K tokens) is always loaded: project summary, role instructions, current task. L1 (~10K tokens) is on-demand: relevant source files, architecture docs, upstream outputs, API specs. L2 (~20K tokens) is deep retrieval: full semantic search via vector store + keyword hybrid, external docs, ADRs. Agents pull L2 via MCP tool calls during execution.

**When to use:** Any system where multiple agents share a large codebase context. Without tiering, naive full-context injection wastes tokens on irrelevant content, inflates cost, and degrades response quality.

**Trade-offs:** Context assembly adds ~50-200ms per agent invocation. L1 selection requires per-role rules that must be maintained. L2 retrieval quality depends on indexing quality (Tree-sitter chunking + embedding freshness).

### Pattern 3: Git Worktree Isolation Per Coding Agent

**What:** Each coding agent (Frontend Dev, Backend Dev, Middleware Dev, Infra Engineer) works in a dedicated git worktree on a dedicated branch (`agent/<role>/<task-id>`). Agents cannot interfere with each other's filesystem changes. On task completion, branches are reviewed, rebased, and merged. Conflicts are auto-resolved or escalated.

**When to use:** Any system with multiple concurrent coding agents writing to the same repository. Direct shared filesystem access guarantees merge conflicts.

**Trade-offs:** Additional disk space proportional to active worktrees. Merge step adds latency after parallel coding completes. Conflict resolution logic is complex to implement correctly.

### Pattern 4: Experiment Loop (Keep/Discard Semantics)

**What:** For iterative improvement (debug-fix cycles, performance optimization, security hardening), the system runs experiments on isolated git branches. Each iteration: hypothesize → apply (branch) → measure metric → evaluate (delta vs baseline). If improved beyond threshold: merge. Otherwise: discard branch. Continues until time budget exhausted or N consecutive non-improvements. All attempts logged to `experiment_log.tsv`.

**When to use:** Debug & fix cycles (S8), performance optimization (S6), security hardening (S6), test coverage improvement (S7), and standalone Improve mode. Inspired by Karpathy's autoresearch pattern.

**Trade-offs:** Can be expensive in tokens and time. Requires a measurable metric function per use case. Must bound by time and iteration budgets to prevent runaway loops.

### Pattern 5: Provider-Agnostic LLM Routing

**What:** A Model Router selects the optimal (provider, model) tuple per agent invocation based on task type, complexity score, user overrides, provider health, and cost constraints. A fallback chain handles rate limits and provider outages. All providers implement a common `LLMProvider` Protocol.

**When to use:** Any system supporting multiple LLM providers. Prevents hard coupling between agent logic and specific models — allows swapping providers without agent code changes.

**Trade-offs:** Routing logic must be maintained as model capabilities change. Fallback to a weaker model may degrade output quality for complex tasks — quality gates downstream catch this.

---

## Data Flow

### Primary Request Flow (PRD to Deployed Application)

```
User submits PRD
    |
    v
[FastAPI Gateway] -- authenticate + validate
    |
    v
[PostgreSQL: Projects] -- create project record
    |
    v
[Pipeline Manager] -- load pipeline preset (full.yaml)
    |
    v
[Graph Engine] -- compile DAG, topological sort
    |
    v
[Execution Layer 0: Orchestrator Agent]
    | STATE_FLOW (project plan, agent assignments)
    v
[Execution Layer 1: Brainstormer Agent]
    | STATE_FLOW (brainstorm output)
    v
[Execution Layer 2: Researcher Agent]
    | STATE_FLOW (research report)
    v
[Execution Layer 3: Architect + Designer] (parallel)
    | STATE_FLOW (architecture doc + design specs)
    v
[Execution Layer 4: Planner Agent]
    | STATE_FLOW (task graph, assignments per agent)
    v
[Execution Layer 5: Frontend Dev | Backend Dev | Middleware Dev] (parallel, isolated worktrees)
    | STATE_FLOW (file manifests, git diffs)
    v
[Execution Layer 6: Code Reviewer | Security Auditor] (parallel)
    | STATE_FLOW + MESSAGE_FLOW (review comments, security findings)
    v
[Execution Layer 7: Tester] (parallel test suites)
    | STATE_FLOW (test results, coverage)
    v
[Execution Layer 8: Debugger] (ExperimentLoop -- iterates until tests pass)
    | STATE_FLOW (stable code, resolved failures)
    v
[Execution Layer 9: Doc Writer]
    | STATE_FLOW (documentation artifacts)
    v
[Execution Layer 10: Infra Engineer -> Project Manager -> Human Approval Gate]
    |
    v
[Object Store: Final Artifacts] -- application, docs, deployment manifests

Every layer:
  - Writes to [PostgreSQL: Agent Tasks] (status, result, tokens, cost)
  - Publishes to [NATS JetStream] -> [Dashboard WebSocket] (real-time events)
  - Updates [Vector Store] (new code indexed for L2 retrieval)
  - Writes to [PostgreSQL: LLM Usage] (token/cost accounting)
  - Checkpoints to [PostgreSQL: Pipeline Runs] (resume state)
```

### Agent-Level Data Flow (Single Agent Invocation)

```
[Graph Engine triggers node]
    |
    v
[Context Adapter]
    |-- Load L0 (project summary, role, task)  -- filesystem
    |-- Load L1 (relevant files, upstream outputs) -- PostgreSQL + filesystem
    |-- Register L2 MCP tools (semantic search hooks) -- ChromaDB
    |
    v
[LLM Router] -- select (provider, model) based on task_type + complexity
    |
    v
[CLI Agent Bridge or Direct LLM call]
    |-- Claude Code (SDK): operates in git worktree, reads/writes files, runs commands
    |-- Codex/Gemini CLI (subprocess): same, via temp prompt file
    |-- Direct completion: planning, review, doc writing (no filesystem ops)
    |
    v
[Output Parser] -- extract structured result (files changed, test output, recommendations)
    |
    v
[State Update] -- write outputs to SharedState (Redis)
    |
    v
[Event Emission] -- publish AgentCompleted event to NATS -> Dashboard
    |
    v
[Checkpoint] -- persist state snapshot to PostgreSQL
    |
    v
[Edge Evaluation] -- check downstream edge conditions, activate next layer
```

### Event / Real-Time Dashboard Flow

```
[Any Agent Action]
    |
    v
[NATS JetStream: codebot.events.*]
    |
    v
[FastAPI WebSocket handler]
    |
    v
[Socket.IO broadcast to dashboard clients]
    |
    v
[Dashboard: Zustand store update -> React re-render]
```

---

## Component Boundaries (What Talks to What)

| Boundary | Direction | Communication | Notes |
|----------|-----------|---------------|-------|
| Dashboard / CLI -> API Gateway | Bidirectional | REST + WebSocket (Socket.IO) | Auth token required |
| API Gateway -> Graph Engine | Internal call | Direct Python (same process) | No network hop |
| Graph Engine -> Agent Pool | Internal call | Direct Python; async Task | Agent runs in same process or subprocess |
| Agent -> LLM Router | Internal call | Direct Python | Router selects provider |
| LLM Router -> Provider (API) | External HTTP | HTTPS (Anthropic/OpenAI/Google) or local (Ollama/LM Studio) | Rate limited, cost tracked |
| Agent -> CLI Agent Bridge | Internal call | Direct Python | Bridge manages subprocess |
| CLI Agent Bridge -> Claude Code | External subprocess | Claude Agent SDK over stdio | Streaming |
| CLI Agent Bridge -> Codex/Gemini CLI | External subprocess | stdin/stdout | Structured output |
| Agent -> Context Adapter | Internal call | Direct Python | Assembles L0/L1/L2 |
| Context Adapter -> ChromaDB | Internal | HTTP (ChromaDB REST) | Semantic search |
| Agent -> Worktree Manager | Internal call | Direct Python | Provisions git worktree |
| Security Pipeline -> Scanners | External subprocess | CLI (Semgrep, Trivy, Gitleaks etc.) or REST (SonarQube) | Parallel fan-out |
| Agent -> NATS (events) | One-way publish | NATS JetStream | Fire-and-forget |
| NATS -> Dashboard | One-way subscribe | WebSocket bridged via FastAPI | Real-time streaming |
| Graph Engine -> PostgreSQL | Read/Write | SQLAlchemy async | State persistence |
| Graph Engine -> Redis | Read/Write | aioredis | Live state cache, pubsub |
| Delivery Agent -> Object Store | Write | MinIO SDK / S3 boto3 | Build artifacts |

---

## Build Order (Component Dependencies)

The implementation must respect these dependency chains. A component cannot be built until all components it depends on are buildable (even in stub/mock form for testing).

```
TIER 1 — No dependencies, build first:
  - Data Layer (PostgreSQL schemas, Redis setup, ChromaDB, MinIO)
  - Monorepo scaffolding (Turborepo, pyproject.toml, package.json, docker-compose.yml)
  - BaseAgent class (stub — no real LLM calls)
  - Core type definitions (shared-types lib: Node, Edge, Agent, Message schemas)

TIER 2 — Depends on Tier 1:
  - Graph Engine (DirectedGraph, Node, Edge, Scheduler, ExecutionEngine)
    [depends on: BaseAgent stub, shared types, data layer for checkpoints]
  - Multi-LLM Abstraction Layer (LLMProvider Protocol, per-provider adapters)
    [depends on: shared types only]
  - Context Manager (L0/L1/L2 tiers, ChromaDB integration)
    [depends on: data layer, Tree-sitter indexer]
  - Event Bus (NATS JetStream integration)
    [depends on: NATS broker running in docker-compose]

TIER 3 — Depends on Tier 2:
  - CLI Agent Bridge (Claude Code SDK, Codex/Gemini subprocess)
    [depends on: LLM Abstraction, Worktree Manager]
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

**Critical path for first working pipeline:**
Data Layer → Graph Engine → Multi-LLM Layer → Context Manager → BaseAgent → Core agents (Orchestrator, Planner, Backend Dev, Tester, Debugger) → Pipeline Manager → FastAPI → CLI → first end-to-end run.

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single developer (local) | Docker Compose, all services on one machine, SQLite acceptable for context store, Ollama for local LLMs |
| Small team (2-10 projects concurrent) | Current architecture works; Redis + PostgreSQL handle the load; scale agent concurrency limit to 15+ |
| Production SaaS (100+ concurrent pipelines) | Extract Graph Engine to dedicated worker pool; NATS cluster; PostgreSQL read replicas; horizontal agent workers; container orchestration (Kubernetes or Fly.io) |

### Scaling Priorities

1. **First bottleneck: LLM rate limits.** The system will hit API rate limits before any infrastructure limit. Mitigation: multi-provider routing, response caching for deterministic tasks, token budget enforcement.
2. **Second bottleneck: Sandbox containers.** Each coding agent needs a Docker container. At 4 active coding agents concurrently, this is manageable. Beyond that, a dedicated container runtime host is needed.
3. **Third bottleneck: Worktree disk space.** Each worktree is a full copy of the project. For large repos, this becomes significant. Mitigation: sparse checkout, cleanup on completion.

---

## Anti-Patterns

### Anti-Pattern 1: Shared Filesystem Without Worktrees

**What people do:** Multiple coding agents write directly to the project's main working tree simultaneously.
**Why it's wrong:** Concurrent writes cause merge conflicts, race conditions on config files, and non-deterministic output. One agent's partial state corrupts another's context.
**Do this instead:** Provision one git worktree per coding agent. Merge after individual tasks complete.

### Anti-Pattern 2: Monolithic Agent (One Agent for Everything)

**What people do:** A single agent handles the entire SDLC: brainstorm, design, code, test, deploy.
**Why it's wrong:** Context window overflows on any real project. Role confusion degrades output quality. Cannot parallelize. Debugging failures is impossible.
**Do this instead:** Specialized agents per role with typed input/output contracts. Graph engine coordinates handoffs.

### Anti-Pattern 3: Direct Agent-to-Agent Calling (No Message Bus)

**What people do:** Agent A directly calls Agent B's function/API to get a result.
**Why it's wrong:** Creates tight coupling. If Agent B fails, Agent A is stuck. No replay, no observability, no fan-out.
**Do this instead:** All inter-agent communication via the event bus (NATS) for async messages or via SharedState for output propagation. Graph engine manages execution order.

### Anti-Pattern 4: Full Codebase in Every Agent's Context

**What people do:** Inject the entire codebase as context for every agent invocation.
**Why it's wrong:** Exceeds context windows on any real project. Dramatically increases token cost. Most content is irrelevant to the specific task, degrading focus.
**Do this instead:** 3-tier context management. L0 always, L1 role-relevant on demand, L2 via semantic retrieval only when needed.

### Anti-Pattern 5: Synchronous Security Scanning (After Delivery)

**What people do:** Run security scans as a final step before releasing the build.
**Why it's wrong:** Late-stage findings require rewrites of already-"complete" code. Debugging context is cold. Developer agents have already moved on.
**Do this instead:** Security pipeline runs in parallel with code review (S6) immediately after implementation (S5). Findings feed back into the debug loop before documentation or deployment.

### Anti-Pattern 6: No Checkpointing (Restart from Zero on Failure)

**What people do:** Run the full pipeline as a single transaction — if it fails at S7, restart from S0.
**Why it's wrong:** Full pipeline runs can take hours and cost significant LLM tokens. A failure deep in the pipeline should not require re-running brainstorming and architecture.
**Do this instead:** Checkpoint state after every execution layer. On restart, load the latest checkpoint and resume from the failed node.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Anthropic API | HTTPS REST via Claude Agent SDK (for Claude Code) or direct completion API | Primary provider for reasoning + code review |
| OpenAI API | HTTPS REST; Codex CLI via subprocess | Code generation + test writing |
| Google Gemini API | HTTPS REST; Gemini CLI via subprocess | Research + documentation |
| Ollama | Local HTTP REST (localhost:11434) | Self-hosted LLMs; no latency budget for reasoning tasks |
| LM Studio | Local HTTP REST (OpenAI-compatible endpoint) | Self-hosted alternative |
| GitHub / GitLab | git CLI + REST API (PR creation, webhook triggers) | Push generated code, create PRs for human review |
| Semgrep | CLI subprocess | SAST; run in sandbox container |
| SonarQube CE | REST API (self-hosted Docker) | Code quality gate |
| Trivy | CLI subprocess | Container + SCA scanning |
| Gitleaks | CLI subprocess + pre-commit hook | Secrets detection |
| npm / PyPI / crates.io | CLI (npm install, pip install) inside sandbox | Dependency resolution |
| Cloud providers (AWS/GCP/Azure/Vercel/Railway) | Provider SDKs + CLI tools inside sandbox | Deployment (S10) |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Graph Engine <-> Pipeline Manager | Direct Python call | Both in same process; Pipeline Manager drives top-level graph |
| Graph Engine <-> Agent implementations | Direct Python async call | Nodes are agent wrappers; graph calls node.execute() |
| Agent <-> LLM Router | Direct Python call | Router is called per agent invocation, not per message |
| Agent <-> Context Adapter | Direct Python call | Adapter called before each invocation to assemble context payload |
| Context Adapter <-> ChromaDB | HTTP REST | ChromaDB runs as a Docker container; accessed via client library |
| CLI Agent Bridge <-> Worktree Manager | Direct Python call | Bridge requests worktree path before spawning subprocess |
| Pipeline Manager <-> Checkpoint Manager | Direct Python call | Checkpoint saved after each layer completes |
| Graph Engine <-> Event Bus | Direct Python call (publish only) | Events flow one direction: engine -> bus -> dashboard |
| FastAPI <-> Graph Engine | Direct Python call (in-process) | No queue needed for single-machine deployment |
| FastAPI <-> NATS | async subscribe | Dashboard streaming uses NATS as the pub/sub bridge |

---

## Sources

- Project documentation: `docs/architecture/ARCHITECTURE.md` (v2.5, 2026-03-18) — C4 model diagrams, 5-layer architecture, all subsystem designs. HIGH confidence.
- Project documentation: `docs/design/SYSTEM_DESIGN.md` (v2.5, 2026-03-18) — Graph engine design, agent specs, pipeline orchestration. HIGH confidence.
- Project documentation: `docs/refernces/RESEARCH_SUMMARY.md` (v2.5, 2026-03-18) — Reference implementations: MASFactory, Automaker, Codebuff, Superset, OpenViking, OpenSandbox, claude-mem. HIGH confidence.
- MASFactory (arXiv:2603.06007, Apache 2.0): Foundational four-layer architecture (Graph Skeleton, Component, Protocol, Interaction layers). HIGH confidence (cited in project docs).
- Automaker, Codebuff, Superset, cmux: Git worktree isolation, subprocess-based CLI agent orchestration, parallel agent dashboards. MEDIUM confidence (cited in research summary).
- OpenViking: Hierarchical context (L0/L1/L2) and filesystem-paradigm context organization. MEDIUM confidence (cited in research summary).
- OpenSandbox (Alibaba): Docker-per-agent sandbox with gVisor/Kata isolation, live preview patterns. MEDIUM confidence (cited in research summary).
- claude-mem: Episodic memory with lifecycle hooks, semantic compression, progressive disclosure, cross-project learning. MEDIUM confidence (cited in research summary).

---

*Architecture research for: Autonomous multi-agent SDLC platform (CodeBot)*
*Researched: 2026-03-18*
