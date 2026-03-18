# Architecture Patterns

**Domain:** Graph-centric multi-agent autonomous SDLC platform
**Researched:** 2026-03-18
**Overall Confidence:** HIGH

---

## Recommended Architecture

CodeBot's architecture aligns with the **hierarchical orchestrator-worker** pattern — the most validated multi-agent architecture pattern in production systems as of 2026 (confirmed by Google's ADK design patterns, LangChain's architecture recommendations, and Confluent's event-driven multi-agent guidance). This is layered on a **dual-engine orchestration** model: LangGraph for graph-based agent state machines and Temporal for durable workflow coordination.

### Why This Architecture

The core architectural decision — graph-centric multi-agent with hierarchical orchestration — is well-validated:

1. **Graph-based agent orchestration** is the dominant 2025-2026 pattern. LangGraph's StateGraph + Send API provides dynamic branching, conditional routing, and parallel execution natively. The alternative (linear chains) cannot express the fan-out/fan-in patterns CodeBot's pipeline requires (S5 Implementation and S6 QA both fan-out to parallel agents).

2. **Dual-engine (LangGraph + Temporal)** solves two distinct problems. LangGraph answers "given this state, what should the agent do next?" while Temporal answers "did this complete, and if not, what do we do about it?" Production systems that tried LangGraph alone hit state management and durability issues at scale (confirmed by Grid Dynamics case study migrating from LangGraph-only to Temporal). The Activity-StateGraph pattern — wrapping LangGraph graphs inside Temporal activities — is the proven integration approach.

3. **Event-driven communication via NATS JetStream** decouples agents cleanly. Confluent's 2025 guidance identifies event-driven multi-agent as the scaling pattern for systems beyond 10 agents. NATS provides subject-based routing for fine-grained agent targeting, queue groups for workload distribution, and KV store for shared agent state — all critical for 30-agent coordination.

4. **Tiered context management** is now industry standard. Google ADK, OpenDev's coding agent, and the "Codified Context" research (arXiv:2602.20478) all converge on three-tier architectures: hot memory (always loaded), domain context (per-task), and cold storage (on-demand retrieval). CodeBot's L0/L1/L2 model directly maps to this pattern.

### System Architecture Diagram

```
+=========================================================================+
|  LAYER 5: INTERACTION LAYER                                             |
|  React Dashboard (React Flow, Monaco, xterm.js, Socket.IO)             |
|  CLI (TypeScript)  |  Chat Interface                                    |
+=========================================================================+
        |  WebSocket/REST          |  CLI commands
        v                          v
+=========================================================================+
|  LAYER 4: API & PROTOCOL LAYER                                         |
|  FastAPI Gateway + Socket.IO Server                                     |
|  Authentication | Rate Limiting | Request Routing                      |
|  Message Adapter | Context Adapter | Interaction Handler                |
+=========================================================================+
        |
        v
+=========================================================================+
|  LAYER 3: ORCHESTRATION LAYER (Dual-Engine)                             |
|                                                                         |
|  +---------------------------+  +-----------------------------+         |
|  |  Temporal Workflows       |  |  LangGraph StateGraphs      |         |
|  |  - Pipeline lifecycle     |  |  - Agent decision logic     |         |
|  |  - Checkpoint/resume      |  |  - Conditional routing      |         |
|  |  - Retry/timeout          |  |  - Dynamic branching (Send) |         |
|  |  - Cross-phase gates      |  |  - Supervisor patterns      |         |
|  +---------------------------+  +-----------------------------+         |
|                                                                         |
|  Pipeline Manager | Phase Coordinator | Task Scheduler (topo sort)      |
|  Checkpoint Manager | Agent Pool Manager | Resource Governor            |
+=========================================================================+
        |                           |                    |
        v                           v                    v
+=========================================================================+
|  LAYER 2: AGENT & COMPONENT LAYER                                       |
|                                                                         |
|  30 Specialized Agents (BaseAgent + PRA cognitive cycle)                |
|  Node Types: AGENT | SUBGRAPH | LOOP | SWITCH | HUMAN_IN_LOOP          |
|              PARALLEL | MERGE | CHECKPOINT | TRANSFORM | GATE           |
|  Composed Graphs: CodingPipeline | ReviewGate | DebugFixLoop            |
|                   ExperimentLoop | FullSDLC                             |
+=========================================================================+
        |                           |                    |
        v                           v                    v
+=========================================================================+
|  LAYER 1: FOUNDATION LAYER                                              |
|                                                                         |
|  +----------------+ +----------------+ +-------------------+            |
|  | Multi-LLM      | | CLI Agent      | | Context           |            |
|  | Abstraction     | | Bridge         | | Management        |            |
|  | (LiteLLM +     | | (Claude Code,  | | (L0/L1/L2 +      |            |
|  |  RouteLLM)     | |  Codex, Gemini)| |  Vector Store +   |            |
|  +----------------+ +----------------+ |  Tree-sitter)     |            |
|                                        +-------------------+            |
|  +----------------+ +----------------+ +-------------------+            |
|  | Security       | | Worktree       | | Event Bus         |            |
|  | Pipeline       | | Manager        | | (NATS JetStream)  |            |
|  | (Semgrep,Trivy,| | (git worktree  | | Pub/Sub + KV      |            |
|  |  Gitleaks)     | |  isolation)    | |                   |            |
|  +----------------+ +----------------+ +-------------------+            |
|                                                                         |
|  +----------------+ +----------------+ +-------------------+            |
|  | PostgreSQL     | | Redis          | | ChromaDB/LanceDB  |            |
|  | (State, Config)| | (Cache, PubSub)| | (Vector Store)    |            |
|  +----------------+ +----------------+ +-------------------+            |
+=========================================================================+
```

---

## Component Boundaries

### Core Components and Their Responsibilities

| Component | Responsibility | Communicates With | Protocol |
|-----------|---------------|-------------------|----------|
| **FastAPI Gateway** | HTTP/WebSocket API, auth, rate limiting, request routing | Dashboard, CLI, Orchestration Layer | REST/WebSocket |
| **Temporal Workflows** | Pipeline lifecycle, durability, retry/timeout, cross-phase gates | LangGraph (activity wrapping), PostgreSQL (state), NATS (events) | Temporal SDK (gRPC) |
| **LangGraph StateGraphs** | Agent decision logic, conditional routing, dynamic branching, supervisor patterns | Agents (execution), SharedState (read/write), Temporal (wrapped as activities) | In-process Python calls |
| **Pipeline Manager** | Phase sequencing, entry/exit gates, pipeline presets (full/quick/review-only) | Temporal Workflows, Phase Coordinator, Dashboard (status) | Internal Python + NATS events |
| **Phase Coordinator** | Manages agents within a single phase, fan-out/fan-in, parallel execution | Agent Pool, Task Scheduler, NATS (agent events) | Internal Python + NATS |
| **Task Scheduler** | Topological sort, ready-node detection, resource constraint checking | Phase Coordinator, Agent Pool Manager | Internal Python |
| **Agent Pool Manager** | Agent lifecycle (create/destroy), concurrency limits, resource allocation | Worktree Manager, LLM Abstraction, NATS | Internal Python |
| **Checkpoint Manager** | State snapshots after each layer/phase, resume from failure | PostgreSQL (persistence), Temporal (integration) | Internal Python + SQL |
| **Multi-LLM Abstraction** | Provider-agnostic LLM access, intelligent routing, fallback chains, cost tracking | LLM APIs (Anthropic, OpenAI, Google, Ollama), Agents (via interface) | HTTP/SDK per provider |
| **CLI Agent Bridge** | Subprocess management for Claude Code, Codex CLI, Gemini CLI | Local filesystem (worktrees), Agents (delegation) | Subprocess/SDK |
| **Context Management** | 3-tier context assembly (L0/L1/L2), vector retrieval, Tree-sitter indexing, compression | Vector Store, PostgreSQL, Agent prompts | Internal Python |
| **Security Pipeline** | SAST/DAST/secret scanning, quality gate enforcement | Semgrep, Trivy, Gitleaks, SonarQube (external tools), Pipeline Manager (gate results) | CLI subprocess + NATS events |
| **Worktree Manager** | Git worktree creation/cleanup, branch isolation per agent | Git (local), Agent Pool Manager | Git CLI subprocess |
| **Event Bus (NATS)** | Inter-agent messaging, event streaming, audit trail, replay | All components (pub/sub), Dashboard (live updates) | NATS protocol |
| **React Dashboard** | Real-time pipeline visualization, agent monitoring, code editing, terminal | FastAPI (REST/WebSocket), Socket.IO (live updates) | HTTP + WebSocket |

### Component Boundary Rules

1. **Agents never communicate directly.** All inter-agent messages flow through NATS JetStream or SharedState propagation via graph edges. This is a hard architectural constraint.
2. **Temporal owns durability.** LangGraph runs agent logic; Temporal ensures it survives crashes. LangGraph StateGraphs are wrapped as Temporal activities.
3. **The Gateway is the only external entry point.** Dashboard and CLI both go through FastAPI. No component accepts external traffic directly.
4. **Worktrees are agent-scoped.** Each coding agent (S5) gets its own git worktree. Worktrees are created by the Worktree Manager when the Agent Pool Manager allocates an agent, and cleaned up on completion.
5. **Context is assembled, not fetched ad-hoc.** The Context Management system pre-assembles context tiers before agent execution begins. Agents do not query vector stores or databases directly during their PRA cycle.

---

## Data Flow

### Primary Data Flow: PRD to Delivered Application

```
User PRD (natural language)
    |
    v
[FastAPI Gateway] -- validates, authenticates, creates Project record
    |
    v
[Temporal Workflow: FullSDLC] -- starts durable pipeline
    |
    v
[Phase S0: Orchestrator]
    | Reads PRD, creates project config, selects pipeline preset
    | Writes: project_config, pipeline_graph to SharedState
    v
[Phase S1: Brainstormer]
    | Reads: PRD + project_config
    | Writes: refined_requirements, feature_priorities, exploration_report
    v
[Phase S2: Researcher]
    | Reads: refined_requirements
    | Writes: research_findings, technology_recommendations
    v
[Phase S3: Architect + Designer] (parallel within phase)
    | Reads: research_findings + refined_requirements
    | Writes: system_architecture, api_design, database_schema, ui_wireframes
    v
[Phase S4: Planner]
    | Reads: architecture artifacts
    | Writes: task_graph (DAG of implementation tasks), tech_stack_config
    v
[Phase S5: Implementation] (fan-out to parallel agents)
    | Frontend Dev, Backend Dev, Middleware Dev, Infra Engineer
    | Each in isolated git worktree
    | Reads: assigned_tasks from task_graph
    | Writes: code files (in worktree), merge to integration branch
    v
[Phase S6: Quality Assurance] (fan-out to parallel agents)
    | Code Reviewer, Security Auditor, Accessibility, Performance, i18n
    | Reads: merged code from S5
    | Writes: review_findings, security_report, remediation_tasks
    v
[Phase S7: Tester]
    | Reads: code + review_findings
    | Writes: test_results, coverage_report
    v
[Phase S8: Debugger] (ExperimentLoop)
    | Reads: failing test results
    | Writes: fixes (keep/discard per experiment), updated code
    | Loops until: all tests pass OR max iterations hit
    v
[Phase S9: Doc Writer]
    | Reads: final code + architecture + API specs
    | Writes: API docs, user guides, architecture diagrams
    v
[Phase S10: Delivery] (optional)
    | Reads: code + docs + infra config
    | Writes: build artifacts, deployment manifests
    v
User receives: working application + handoff report
```

### Event Flow (NATS JetStream)

```
Subject Hierarchy:
  codebot.pipeline.{project_id}.phase.{stage}     -- phase lifecycle events
  codebot.agent.{agent_id}.status                  -- agent state transitions
  codebot.agent.{agent_id}.output                  -- agent output artifacts
  codebot.gate.{gate_id}.result                    -- quality gate pass/fail
  codebot.human.{project_id}.request               -- human-in-the-loop requests
  codebot.human.{project_id}.response              -- human responses
  codebot.metrics.{component}                      -- observability metrics

Consumers:
  - Dashboard: subscribes to all codebot.* for real-time visualization
  - Pipeline Manager: subscribes to phase.* and gate.* for coordination
  - Agents: subscribe to their own agent.{id}.* for task assignments
  - Audit Log: subscribes to all codebot.* for persistent audit trail
```

### State Flow Between Layers

```
SharedState (in-memory, thread-safe dict)
    |
    |-- Written by: Agent outputs, State transforms on edges
    |-- Read by: Downstream agents (via Context Adapter)
    |-- Checkpointed to: PostgreSQL (via Checkpoint Manager, after each layer)
    |-- Cached in: Redis (hot state for dashboard queries)
    |
    |-- Scoped per: Graph execution instance (one per pipeline run)
    |-- Thread safety: Controlled by Execution Engine (one writer per layer)
```

### Dashboard Real-Time Data Flow

```
Agent Event (NATS) --> FastAPI WebSocket handler --> Socket.IO --> React Dashboard

Specific channels:
  - Pipeline graph state (node colors, edge progress)
  - Agent logs and reasoning traces
  - Code diffs and file changes
  - Test results (pass/fail counts, coverage)
  - Security scan findings
  - Resource usage (tokens, cost, time)
```

---

## Patterns to Follow

### Pattern 1: Activity-StateGraph (Temporal + LangGraph Integration)

**What:** Wrap each LangGraph StateGraph as a Temporal activity. Temporal manages the workflow lifecycle (retry, timeout, checkpoint), while LangGraph manages the agent's decision logic within each activity.

**When:** Always. This is the fundamental integration pattern for CodeBot's dual-engine architecture.

**Why:** LangGraph excels at agent state machines but is single-process without built-in distribution. Temporal provides durable execution, automatic retry, and cross-process coordination. Together they address both the "what to do" and "how to survive failure" concerns.

**Confidence:** HIGH (confirmed by Grid Dynamics case study, Temporal + LangGraph integration POC on GitHub, and multiple 2026 production reports)

**Implementation sketch:**
```python
# Temporal activity wrapping a LangGraph StateGraph
@activity.defn
async def run_agent_graph(input: AgentGraphInput) -> AgentGraphOutput:
    """Each phase's agent graph runs as a Temporal activity."""
    graph = build_phase_graph(input.phase, input.agents)
    compiled = graph.compile(checkpointer=MemorySaver())
    result = await compiled.ainvoke(
        input.state,
        config={"configurable": {"thread_id": input.execution_id}}
    )
    return AgentGraphOutput(state=result, artifacts=extract_artifacts(result))

# Temporal workflow orchestrating the full pipeline
@workflow.defn
class SDLCPipelineWorkflow:
    @workflow.run
    async def run(self, input: PipelineInput) -> PipelineOutput:
        # Each phase is a Temporal activity with retry policy
        for phase in input.phases:
            result = await workflow.execute_activity(
                run_agent_graph,
                AgentGraphInput(phase=phase, state=current_state),
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            current_state = result.state
            await self.checkpoint(phase, current_state)
        return PipelineOutput(state=current_state)
```

**Key constraint:** Data must serialize/deserialize at every Temporal activity boundary. All SharedState objects must use Pydantic models (already planned) with JSON-serializable types only.

### Pattern 2: Supervisor-Worker with Dynamic Fan-Out

**What:** The Orchestrator agent acts as a hierarchical supervisor. It decomposes the pipeline into phases, and within phases that support parallelism (S3, S5, S6), uses LangGraph's Send API to dynamically spawn worker agents.

**When:** Phases S3 (Architecture & Design), S5 (Implementation), and S6 (Quality Assurance) where multiple agents work in parallel.

**Why:** Static fan-out requires knowing agent count at compile time. The Send API allows the Planner (S4) to determine how many implementation agents are needed based on the task graph, and the Phase Coordinator spawns them dynamically.

**Confidence:** HIGH (LangGraph's Send API is documented and stable since LangGraph 1.0, October 2025)

### Pattern 3: ExperimentLoop (Keep/Discard Optimization)

**What:** An autonomous loop where each iteration proposes a hypothesis, applies it to an experiment git branch, measures against a baseline metric, and either keeps (merges) or discards (deletes branch) the change. Tracks all experiments in a TSV log.

**When:** Debug/Fix loops (S8), performance optimization (S6), security hardening (S6), test coverage improvement (S7), and standalone Improve mode.

**Why:** This pattern, inspired by Karpathy's autoresearch framework, provides structured experimentation with rollback safety. Each experiment is isolated in its own git branch, so failures are free.

**Confidence:** MEDIUM (the pattern is well-described in CodeBot's own design docs and draws from autoresearch, but large-scale production validation is limited)

### Pattern 4: Progressive Validation Cascade

**What:** Quality gates organized into 4 levels of increasing cost: (1) Syntax & Style checks, (2) Unit Tests, (3) Integration Tests, (4) Acceptance Checklist (security + architecture conformance). Each level must pass before the next executes.

**When:** At every phase transition, particularly gates G5-G9.

**Why:** Fast feedback. Cheap static checks (seconds) catch errors before expensive integration tests (minutes) run. Agents auto-fix Level 1 failures without human intervention.

**Confidence:** HIGH (standard CI/CD pattern, well-proven in traditional software development)

### Pattern 5: Git Worktree Isolation for Parallel Agents

**What:** Each coding agent (S5) operates in an isolated git worktree. The Worktree Manager creates a worktree + branch per agent, agents work independently, and branches are merged sequentially after completion.

**When:** Phase S5 (Implementation) where Frontend Dev, Backend Dev, Middleware Dev, and Infra Engineer work in parallel.

**Why:** Without isolation, parallel agents would create file conflicts and corrupt each other's work. Worktrees provide complete filesystem isolation while sharing the same git history. This is the standard pattern adopted by Claude Code, Cursor, ccswarm, and Pochi as of 2026.

**Known challenges:**
- Port conflicts: Multiple dev servers on the same ports. Mitigation: assign unique port ranges per worktree.
- Database isolation: Shared database state creates race conditions. Mitigation: use per-agent test databases or schema prefixes.
- Disk space: Each worktree is a full checkout. Mitigation: sparse checkouts, aggressive cleanup after merge.

**Confidence:** HIGH (widely adopted in production AI coding workflows, documented by Anthropic, confirmed by multiple independent teams)

### Pattern 6: Tiered Context Assembly

**What:** Pre-assemble agent context in three tiers before execution:
- **L0 (Hot):** Always loaded — project config, pipeline state, agent system prompt, CLAUDE.md-style constitution
- **L1 (Warm):** Phase-scoped — current phase artifacts, relevant upstream outputs, tool schemas
- **L2 (Cold):** On-demand retrieval — vector store queries, Tree-sitter code index lookups, historical experiment logs

**When:** Before every agent execution in the PRA cycle's Perception phase.

**Why:** Context engineering is the single most important factor in agent reliability (confirmed by Anthropic's context engineering guide, Google ADK's tiered context design, and the Codified Context paper). Pre-assembly ensures agents receive curated, relevant context rather than raw data dumps.

**Confidence:** HIGH (converged best practice across Google ADK, Anthropic, and academic research)

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Direct Agent-to-Agent Communication

**What:** Agents calling each other directly via function calls or shared memory without going through the event bus or graph edges.

**Why bad:** Creates tight coupling, makes the system impossible to debug, breaks agent isolation, and prevents replay/audit. When agent A calls agent B directly, you lose visibility into what happened and cannot retry or checkpoint the interaction.

**Instead:** All inter-agent communication flows through NATS JetStream events or SharedState propagation via typed graph edges. This is a hard constraint in CodeBot's architecture.

### Anti-Pattern 2: Single-Engine Orchestration

**What:** Using only LangGraph (or only Temporal) for everything — both the agent logic and the pipeline durability.

**Why bad:** LangGraph is single-process and lacks distributed durability. Teams that used LangGraph alone hit state management and debugging issues at scale (Grid Dynamics case study). Temporal alone lacks the rich agent-specific primitives (conditional routing, Send API, supervisor patterns) that LangGraph provides.

**Instead:** Dual-engine: LangGraph for agent decision logic (within-phase), Temporal for pipeline lifecycle (cross-phase). Wrap LangGraph graphs as Temporal activities.

### Anti-Pattern 3: Flat Context / No Context Engineering

**What:** Dumping all available information into the agent's prompt without curation or tiering.

**Why bad:** Exceeds context windows, dilutes relevant information, increases token costs, and degrades agent performance. Research shows that agents with curated context consistently outperform those with raw data dumps.

**Instead:** Tiered context assembly (L0/L1/L2). The Context Management system pre-assembles relevant context before the agent's PRA cycle begins. Agents do not query data stores directly.

### Anti-Pattern 4: Shared Worktree for Parallel Agents

**What:** Multiple coding agents writing to the same git working directory simultaneously.

**Why bad:** File conflicts, race conditions, corrupted state. One agent's intermediate file writes can break another agent's compilation or test runs.

**Instead:** Isolated git worktrees per agent. Merge sequentially after all agents complete.

### Anti-Pattern 5: Monolithic Agent Design

**What:** Building one large, general-purpose agent that handles everything instead of specialized agents.

**Why bad:** Large tool sets decrease agent reliability. An agent with 50 tools performs worse than 5 agents with 10 tools each. LangChain's 2026 guidance explicitly recommends focusing tasks per agent.

**Instead:** 30 specialized agents, each with a focused role and limited tool set. The Orchestrator coordinates them via the graph.

---

## Scalability Considerations

| Concern | At 1 user (dev) | At 10 users (team) | At 100+ users (enterprise) |
|---------|-----------------|---------------------|---------------------------|
| **Agent concurrency** | Single pipeline, 5-8 parallel agents max | Multiple pipelines, Temporal worker scaling | Temporal cluster, agent pool with backpressure |
| **LLM API throughput** | Direct API calls, single provider | Load balancing across providers, rate limit management | RouteLLM intelligent routing, cost optimization, provider failover |
| **Event bus** | Single NATS server | NATS cluster (3 nodes) | NATS super-cluster with leaf nodes |
| **State storage** | Single PostgreSQL | Read replicas, connection pooling | Partitioned by project, archival policy |
| **Dashboard updates** | Direct WebSocket | Socket.IO with Redis adapter | Socket.IO cluster with Redis pub/sub fan-out |
| **Git worktrees** | Local filesystem | Shared NFS or distributed filesystem | Object storage-backed worktrees, sparse checkouts |
| **Vector store** | ChromaDB (local) | ChromaDB/LanceDB (single instance) | Qdrant cluster (distributed, sharded) |

---

## Suggested Build Order

The build order reflects component dependencies — each phase builds on the previous one's outputs. This directly informs the milestone/phase structure for the roadmap.

### Phase 1: Foundation (No agents yet)

**Build:** Monorepo scaffolding, Docker stack, database schema, shared models, NATS event bus

**Rationale:** Everything else depends on these. You cannot run agents without a database to store state, an event bus for communication, or shared types for data flow. This is already partially complete (monorepo, Docker, NATS, shared models).

**Status:** Largely done per PROJECT.md.

### Phase 2: Graph Engine + Agent Framework

**Build:** Graph Skeleton (Node, Edge, DirectedGraph), Execution Engine (topological sort, parallel execution), BaseAgent with PRA cycle, AgentNode wrapper, SharedState

**Rationale:** The graph engine is the core execution substrate. Without it, agents have no way to be scheduled, executed, or coordinated. BaseAgent defines the contract all 30 agents must implement. SharedState is the data flow mechanism between nodes.

**Depends on:** Phase 1 (shared models, database for checkpoints, NATS for events)

**This is the critical path.** If the graph engine is wrong, everything built on top is wrong.

### Phase 3: Multi-LLM Abstraction + Context Management

**Build:** Provider-agnostic LLM interface (LiteLLM wrapper), intelligent routing (RouteLLM), fallback chains, token tracking, context tiers (L0/L1/L2), vector store integration, Tree-sitter indexing

**Rationale:** Agents need LLM access and context to function. The LLM abstraction must exist before any agent can reason. Context management must exist before agents can perceive their environment (the "P" in PRA).

**Depends on:** Phase 2 (agents need the BaseAgent interface to consume LLM and context services)

### Phase 4: Temporal Integration + Pipeline Orchestration

**Build:** Temporal workflow definitions, Activity-StateGraph pattern, Pipeline Manager, Phase Coordinator, Checkpoint Manager, quality gates

**Rationale:** Once agents can execute within a graph, the next need is durability and lifecycle management. Temporal provides retry, timeout, and checkpoint/resume for long-running pipelines. Quality gates enforce phase transitions.

**Depends on:** Phase 2 (graph engine), Phase 3 (LLM + context — needed for gate evaluation)

### Phase 5: First Agents (Vertical Slice)

**Build:** Orchestrator agent, one implementation agent (e.g., Backend Dev), Code Reviewer, Tester, Debugger. Wire them into a minimal pipeline: Orchestrator -> Backend Dev -> Code Reviewer -> Tester -> Debugger.

**Rationale:** Validate the entire architecture end-to-end with a minimal vertical slice before building all 30 agents. This proves the graph engine, LLM abstraction, context management, Temporal integration, event bus, worktree isolation, and quality gates all work together.

**Depends on:** Phases 2, 3, 4

### Phase 6: Worktree Manager + CLI Agent Bridge

**Build:** Git worktree creation/cleanup, branch management, Claude Code/Codex CLI/Gemini CLI subprocess integration

**Rationale:** The vertical slice in Phase 5 can use a simple working directory. Full worktree isolation and CLI agent delegation are needed for parallel implementation agents in Phase 7.

**Depends on:** Phase 5 (validated agent execution)

### Phase 7: Remaining Agents (Breadth)

**Build:** All 30 agents across 10 categories, YAML-declarative agent configurations, ComposedGraphs (CodingPipeline, ReviewGate, DebugFixLoop, ExperimentLoop)

**Rationale:** With the infrastructure proven by the vertical slice, build out the full agent roster. Each agent follows the same BaseAgent interface and PRA cycle.

**Depends on:** Phases 5, 6

### Phase 8: Security Pipeline + Quality Gates

**Build:** Semgrep, Trivy, Gitleaks integration, Progressive Validation Cascade (4-level), security quality gates, SonarQube integration

**Rationale:** Security scanning and quality gates need working code to scan. They sit between Implementation (S5) and Testing (S7) in the pipeline.

**Depends on:** Phase 7 (agents produce code to scan)

### Phase 9: FastAPI Server + Dashboard

**Build:** REST API, WebSocket server, Socket.IO integration, React dashboard with React Flow pipeline visualization, Monaco editor, xterm.js terminal, real-time updates

**Rationale:** The backend must be working before building the UI. The dashboard is critical for monitoring 30 agents but is not on the critical path for agent execution — agents can run headless via CLI.

**Depends on:** Phase 7 (agents to monitor), Phase 4 (Temporal to query pipeline state)

### Phase 10: CLI Application + Polish

**Build:** TypeScript CLI, pipeline execution commands, agent interaction interface, CRDT-based collaboration (Yjs), pipeline presets (full/quick/review-only)

**Depends on:** Phase 9 (API to interact with)

### Build Order Dependency Graph

```
Phase 1: Foundation
    |
    v
Phase 2: Graph Engine + Agent Framework  <-- CRITICAL PATH
    |
    +---> Phase 3: Multi-LLM + Context Management
    |         |
    |         v
    +---> Phase 4: Temporal + Pipeline Orchestration
              |
              v
          Phase 5: First Agents (Vertical Slice)  <-- VALIDATION CHECKPOINT
              |
              +---> Phase 6: Worktree Manager + CLI Agent Bridge
              |         |
              |         v
              +---> Phase 7: Remaining Agents (Breadth)
                        |
                        +---> Phase 8: Security Pipeline
                        |
                        +---> Phase 9: FastAPI + Dashboard
                                  |
                                  v
                              Phase 10: CLI + Polish
```

### Key Ordering Rationale

1. **Graph Engine before Agents:** The execution substrate must exist before any agent can run. Building agents without the graph engine is like writing microservices without a container runtime.

2. **Vertical Slice before Breadth:** Building 5 agents end-to-end proves the architecture faster than building 30 agents against an unvalidated foundation. The vertical slice (Phase 5) is the first point where the system can be tested as a whole.

3. **LLM + Context before Temporal:** Agents need to reason (LLM) and perceive (context) before they need durability (Temporal). A crashing agent that reasons correctly is easier to fix than a durable agent that reasons poorly.

4. **Dashboard after Agents:** The dashboard visualizes agent activity. Without running agents, there is nothing to visualize. Agents can execute headlessly via Temporal's built-in UI for early development.

5. **Security Pipeline after Implementation Agents:** Security tools scan code. Code must exist first. Wiring Semgrep/Trivy integration before any agent produces code is premature.

---

## Technology Validation Notes

### LangGraph

- **Status:** Stable, production-ready (v1.0 released October 2025, MIT license)
- **Stars:** ~24.6K GitHub stars
- **Key features used:** StateGraph, Send API (dynamic branching), conditional edges, supervisor pattern, MemorySaver checkpointing
- **Risk:** LangGraph 1.0 includes built-in durable execution which overlaps with Temporal. Monitor whether the dual-engine approach becomes redundant as LangGraph matures.
- **Confidence:** HIGH

### Temporal

- **Status:** Production-proven, widely adopted (~18.9K stars, MIT)
- **Key features used:** Workflow durability, activity retry, timeout, cross-process coordination
- **Integration pattern:** Activity-StateGraph (wrap LangGraph as Temporal activities)
- **Risk:** Serialization boundary overhead. All state passed between activities must be JSON-serializable.
- **Confidence:** HIGH

### NATS JetStream

- **Status:** Production-proven, already integrated in CodeBot (Phase 01-03)
- **Key features used:** Pub/sub with persistence, subject-based routing, queue groups, KV store
- **Scaling concern:** Keep total consumers below ~100K (Synadia anti-patterns guide). At 30 agents with per-project streams, this is well within limits.
- **Confidence:** HIGH

### Git Worktree Isolation

- **Status:** Well-validated pattern, adopted by Claude Code, Cursor, ccswarm, Pochi
- **Key features used:** Per-agent isolated worktrees, branch-per-worktree, sequential merge
- **Challenges:** Port conflicts, database isolation, disk space
- **Confidence:** HIGH

### Tiered Context (L0/L1/L2)

- **Status:** Industry standard as of 2025-2026, converged across Google ADK, Anthropic, and academic research
- **Validation:** Confirmed by "Codified Context" paper (arXiv:2602.20478), Google ADK's tiered architecture, OpenDev's 5-tier prompt system
- **Confidence:** HIGH

---

## Sources

### Architecture & Multi-Agent Patterns
- [Google's Eight Essential Multi-Agent Design Patterns (InfoQ, Jan 2026)](https://www.infoq.com/news/2026/01/multi-agent-design-patterns/)
- [Choosing the Right Multi-Agent Architecture (LangChain Blog)](https://blog.langchain.com/choosing-the-right-multi-agent-architecture/)
- [Four Design Patterns for Event-Driven Multi-Agent Systems (Confluent)](https://www.confluent.io/blog/event-driven-multi-agent-systems/)
- [Designing Effective Multi-Agent Architectures (O'Reilly Radar)](https://www.oreilly.com/radar/designing-effective-multi-agent-architectures/)
- [How to Build Multi-Agent Systems: Complete 2026 Guide (DEV Community)](https://dev.to/eira-wexford/how-to-build-multi-agent-systems-complete-2026-guide-1io6)

### Temporal + LangGraph Integration
- [Temporal + LangGraph: A Two-Layer Architecture (anup.io)](https://www.anup.io/temporal-langgraph-a-two-layer-architecture-for-multi-agent-coordination/)
- [Agentic AI Workflows: Why Orchestration with Temporal is Key (IntuitionLabs)](https://intuitionlabs.ai/articles/agentic-ai-temporal-orchestration)
- [Temporal and LangGraph Integration POC (DeepWiki)](https://deepwiki.com/domainio/temporal-langgraph-poc/2.1-temporal-and-langgraph-integration)
- [Orchestrating Multi-Step Agents: Temporal/Dagster/LangGraph Patterns (Kinde)](https://www.kinde.com/learn/ai-for-software-engineering/ai-devops/orchestrating-multi-step-agents-temporal-dagster-langgraph-patterns-for-long-running-work/)

### LangGraph Specifics
- [LangGraph Multi-Agent Workflows (LangChain Blog)](https://blog.langchain.com/langgraph-multi-agent-workflows/)
- [Production-Grade Multi-Agent Communication Using LangGraph (MarkTechPost, Mar 2026)](https://www.marktechpost.com/2026/03/01/how-to-design-a-production-grade-multi-agent-communication-system-using-langgraph-structured-message-bus-acp-logging-and-persistent-shared-state-architecture/)
- [LangGraph Supervisor Reference (LangChain)](https://reference.langchain.com/python/langgraph/supervisor/)

### NATS JetStream
- [JetStream Architecture (NATS Docs)](https://docs.nats.io/nats-concepts/jetstream)
- [JetStream Anti-Patterns: Avoid These Pitfalls (Synadia)](https://www.synadia.com/blog/jetstream-design-patterns-for-scale)
- [NATS JetStream Event-Driven Architecture on Kubernetes](https://oneuptime.com/blog/post/2026-02-09-nats-jetstream-event-driven-kubernetes/view)
- [Why NATS JetStream is Well Suited to AI at the Edge (Synadia)](https://www.synadia.com/blog/ai-at-the-edge-with-nats-jetstream)

### Git Worktree Isolation
- [Git Worktrees: The Secret Weapon for Running Multiple AI Coding Agents in Parallel](https://medium.com/@mabd.dev/git-worktrees-the-secret-weapon-for-running-multiple-ai-coding-agents-in-parallel-e9046451eb96)
- [Git Worktree Isolation in Claude Code (Towards AI, Mar 2026)](https://medium.com/@richardhightower/git-worktree-isolation-in-claude-code-parallel-development-without-the-chaos-262e12b85cc5)
- [ccswarm: Multi-agent orchestration with Git worktree isolation (GitHub)](https://github.com/nwiizo/ccswarm)
- [How We Built True Parallel Agents With Git Worktrees (DEV Community)](https://dev.to/getpochi/how-we-built-true-parallel-agents-with-git-worktrees-2580)

### Context Management
- [Effective Context Engineering for AI Agents (Anthropic)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Codified Context: Infrastructure for AI Agents in a Complex Codebase (arXiv:2602.20478)](https://arxiv.org/html/2602.20478v1)
- [Architecting Efficient Context-Aware Multi-Agent Framework (Google Developers Blog)](https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/)
- [Context Management: The Missing Piece for Agentic AI (DataHub)](https://datahub.com/blog/context-management/)

### Dashboard & Real-Time
- [Building Real-Time Dashboards with React and WebSockets](https://www.wildnetedge.com/blogs/building-real-time-dashboards-with-react-and-websockets)
- [How to Use WebSockets in React for Real-Time Applications](https://oneuptime.com/blog/post/2026-01-15-websockets-react-real-time-applications/view)
