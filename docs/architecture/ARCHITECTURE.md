# CodeBot -- System Architecture Document

**Version:** 2.5
**Date:** 2026-03-18
**Status:** Draft
**Author:** Architecture Team
**Related:** [PRD v2.5](../prd/PRD.md) | [References](../refernces/ref.md)

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Agent Graph Engine](#3-agent-graph-engine)
4. [Multi-LLM Abstraction Layer](#4-multi-llm-abstraction-layer)
5. [CLI Agent Integration Layer](#5-cli-agent-integration-layer)
6. [Context Management System](#6-context-management-system)
7. [Security and Quality Pipeline](#7-security-and-quality-pipeline)
8. [Data Architecture](#8-data-architecture)
9. [Infrastructure Architecture](#9-infrastructure-architecture)
10. [Communication Architecture](#10-communication-architecture)
11. [Deployment Architecture](#11-deployment-architecture)
12. [Technology Stack Summary](#12-technology-stack-summary)
13. [Cross-Cutting Concerns](#13-cross-cutting-concerns)
14. [Agent Lifecycle Management](#14-agent-lifecycle-management)
15. [Error Handling Architecture](#15-error-handling-architecture)
16. [Communication Protocol](#16-communication-protocol)
17. [Platform Observability](#17-platform-observability)
18. [Data Retention Architecture](#18-data-retention-architecture)
19. [Authentication Architecture](#19-authentication-architecture)
20. [Agent Safety Guardrails](#20-agent-safety-guardrails)
21. [Prompt Engineering Standards](#21-prompt-engineering-standards)

---

## 1. System Overview

CodeBot is an autonomous, end-to-end software development platform powered by a
graph-centric multi-agent system. It accepts a Product Requirements Document (PRD)
or natural language requirements and orchestrates a fleet of specialized AI agents
to plan, research, architect, design, implement, review, test, debug, and deliver
a fully working application.

The system uses LangGraph (~24.6K stars, MIT) as the primary agent graph engine,
with Temporal (~18.9K stars, MIT) for durable workflow orchestration. The architecture
follows graph-centric multi-agent patterns (originally inspired by MASFactory,
arXiv:2603.06007) where workflows are expressed as directed computation graphs with
nodes executing agents or sub-workflows and edges encoding dependencies and message passing.

### 1.1 C4 Model -- Level 1: System Context

```
 +----------------------------------------------------------------+
 |                     External Systems                            |
 |  +----------+  +----------+  +----------+  +----------------+  |
 |  |  OpenAI  |  | Anthropic|  |  Google  |  | Git Hosting    |  |
 |  |  API     |  | API      |  |  API     |  | (GitHub/GitLab)|  |
 |  +----+-----+  +----+-----+  +----+-----+  +-------+--------+  |
 +-------|-------------|-------------|------------------|----------+
         |             |             |                  |
         +------+------+------+------+                  |
                |             |                         |
 +---------+   |             |   +-----------+          |
 |         |   v             v   |           |          v
 |  User   +---> +---------+  <--+ CLI       |   +-----------+
 | (Human) |     |         |     | Agents    |   | Package   |
 |         +---> | CODEBOT |  <--+ (Claude   |   | Registries|
 +---------+     |         |     |  Code,    |   | (npm,     |
   ^  |          |  Multi- |     |  Codex,   |   |  PyPI,    |
   |  |          |  Agent  |     |  Gemini)  |   |  crates)  |
   |  |          |  System |     +-----------+   +-----------+
   |  |          |         |
   |  |          +----+----+
   |  |               |
   |  |               v
   |  |     +-------------------+
   |  |     | Security Scanners |
   |  |     | (Trivy, Semgrep,  |
   |  |     |  SonarQube,       |
   |  |     |  Shannon,         |
   |  |     |  Gitleaks, ORT)   |
   |  |     +-------------------+
   |  |
   |  +----- Web Dashboard / CLI Interface
   +-------- Review feedback, approvals, overrides
```

**Key relationships:**

| From | To | Relationship |
|---|---|---|
| User | CodeBot | Submits PRD, reviews output, provides feedback |
| CodeBot | LLM APIs | Sends prompts, receives completions |
| CodeBot | CLI Agents | Delegates coding tasks via subprocess/SDK |
| CodeBot | Git Hosting | Pushes code, creates branches and PRs |
| CodeBot | Security Scanners | Submits code for analysis, receives reports |
| CodeBot | Package Registries | Resolves dependencies, checks versions |

### 1.2 C4 Model -- Level 2: Container Diagram

```
+------------------------------------------------------------------------+
|                            CODEBOT PLATFORM                            |
|                                                                        |
|  +---------------------+    +---------------------+                    |
|  |   Web Dashboard     |    |   CLI Interface     |                    |
|  |   (Next.js)         |    |   (Python/Click)    |                    |
|  |                     |    |                     |                    |
|  |  - Project Board    |    |  - codebot init     |                    |
|  |  - Agent Timeline   |    |  - codebot start    |                    |
|  |  - Code Viewer      |    |  - codebot status   |                    |
|  |  - Terminal         |    |  - codebot review   |                    |
|  |  - Chat Interface   |    |  - codebot deploy   |                    |
|  +----------+----------+    +----------+----------+                    |
|             |                          |                               |
|             +----------+  +-----------+                                |
|                        |  |                                            |
|                        v  v                                            |
|  +---------------------------------------------+                      |
|  |           API Gateway / WebSocket            |                      |
|  |           (FastAPI + Socket.IO)               |                      |
|  +---------------------+-----------------------+                      |
|                        |                                               |
|                        v                                               |
|  +---------------------------------------------+                      |
|  |         Orchestration Engine (Core)          |                      |
|  |                                              |                      |
|  |  +----------------+  +------------------+    |                      |
|  |  | Agent Graph    |  | Pipeline         |    |                      |
|  |  | Engine         |  | Manager          |    |                      |
|  |  +----------------+  +------------------+    |                      |
|  |  +----------------+  +------------------+    |                      |
|  |  | Task Scheduler |  | Checkpoint       |    |                      |
|  |  |                |  | Manager          |    |                      |
|  |  +----------------+  +------------------+    |                      |
|  +---------------------+-----------------------+                      |
|                        |                                               |
|          +-------------+-------------+                                 |
|          |             |             |                                  |
|          v             v             v                                  |
|  +-----------+  +------------+  +-----------+                          |
|  | Multi-LLM |  | CLI Agent  |  | Context   |                         |
|  | Abstraction|  | Integration|  | Management|                         |
|  | Layer     |  | Layer      |  | System    |                          |
|  +-----------+  +------------+  +-----------+                          |
|          |             |             |                                  |
|          v             v             v                                  |
|  +-----------+  +------------+  +-----------+  +------------------+    |
|  | Agent     |  | Worktree   |  | Vector    |  | Security &       |    |
|  | Pool      |  | Manager    |  | Store     |  | Quality Pipeline |    |
|  +-----------+  +------------+  +-----------+  +------------------+    |
|                                                                        |
|  +------------------+  +------------------+  +------------------+      |
|  | PostgreSQL       |  | Redis            |  | Object Store     |      |
|  | (State, Config)  |  | (Cache, PubSub)  |  | (Artifacts)      |      |
|  +------------------+  +------------------+  +------------------+      |
+------------------------------------------------------------------------+
```

### 1.3 C4 Model -- Level 3: Component Diagram (Orchestration Engine)

```
+-----------------------------------------------------------------------+
|                      Orchestration Engine                              |
|                                                                       |
|  +-------------------------------------------------------------------+
|  |                    Agent Graph Engine                              |
|  |                                                                   |
|  |  +--------------+   +--------------+   +------------------+       |
|  |  | Graph        |   | Node         |   | Edge             |       |
|  |  | Skeleton     |   | Registry     |   | Resolver         |       |
|  |  | (DAG)        |   | (Templates)  |   | (Dependencies)   |       |
|  |  +--------------+   +--------------+   +------------------+       |
|  |                                                                   |
|  |  +--------------+   +--------------+   +------------------+       |
|  |  | Loop         |   | Switch       |   | Composed         |       |
|  |  | Controller   |   | Controller   |   | Graph Manager    |       |
|  |  | (Fix cycles) |   | (Routing)    |   | (Reuse patterns) |       |
|  |  +--------------+   +--------------+   +------------------+       |
|  +-------------------------------------------------------------------+
|                                                                       |
|  +-------------------------------------------------------------------+
|  |                    Pipeline Manager                                |
|  |                                                                   |
|  |  +--------------+   +--------------+   +------------------+       |
|  |  | Phase        |   | Task         |   | Dependency       |       |
|  |  | Coordinator  |   | Decomposer   |   | Graph Builder    |       |
|  |  +--------------+   +--------------+   +------------------+       |
|  +-------------------------------------------------------------------+
|                                                                       |
|  +-------------------------------------------------------------------+
|  |                    Execution Runtime                               |
|  |                                                                   |
|  |  +--------------+   +--------------+   +------------------+       |
|  |  | Task         |   | Checkpoint   |   | Error            |       |
|  |  | Scheduler    |   | Manager      |   | Recovery         |       |
|  |  | (Topo sort)  |   | (Snapshots)  |   | (Retry/Fallback) |       |
|  |  +--------------+   +--------------+   +------------------+       |
|  |                                                                   |
|  |  +--------------+   +--------------+   +------------------+       |
|  |  | Agent        |   | Resource     |   | Metrics          |       |
|  |  | Pool         |   | Governor     |   | Collector        |       |
|  |  | Manager      |   | (Concurrency)|   |                  |       |
|  |  +--------------+   +--------------+   +------------------+       |
|  +-------------------------------------------------------------------+
|                                                                       |
|  +-------------------------------------------------------------------+
|  |                    Protocol Layer                                  |
|  |                                                                   |
|  |  +--------------+   +--------------+   +------------------+       |
|  |  | Message      |   | Context      |   | Interaction      |       |
|  |  | Adapter      |   | Adapter      |   | Handler          |       |
|  |  +--------------+   +--------------+   +------------------+       |
|  +-------------------------------------------------------------------+
+-----------------------------------------------------------------------+
```

---

## 2. High-Level Architecture

CodeBot is structured in five logical layers, following graph-centric multi-agent
patterns (inspired by MASFactory, now implemented via LangGraph + Temporal) and
extending them with infrastructure and security concerns specific to autonomous
software development.

### 2.1 Layer Model

```
+===================================================================+
|  LAYER 5 -- INTERACTION LAYER                                     |
|  Web Dashboard | CLI | Chat Interface | Vibe Graphing             |
+===================================================================+
         |                    |                    |
+===================================================================+
|  LAYER 4 -- PROTOCOL LAYER                                       |
|  Message Adapter | Context Adapter | Interaction Handler          |
+===================================================================+
         |                    |                    |
+===================================================================+
|  LAYER 3 -- COMPONENT LAYER                                      |
|  Agents | Graph | Loop | ExperimentLoop | Switch | ComposedGraph | NodeTemplate |
+===================================================================+
         |                    |                    |
+===================================================================+
|  LAYER 2 -- ENGINE LAYER                                         |
|  Graph Skeleton | Task Scheduler | Checkpoint Mgr | Agent Pool    |
+===================================================================+
         |                    |                    |
+===================================================================+
|  LAYER 1 -- FOUNDATION LAYER                                     |
|  Multi-LLM Abstraction | CLI Agent Bridge | Context Mgr |        |
|  Security Pipeline | Data Layer | Worktree Manager               |
+===================================================================+
```

### 2.2 Layer Responsibilities

**Layer 1 -- Foundation Layer**
Provides the low-level services that all higher layers depend on: LLM access,
filesystem isolation, persistent storage, vector retrieval, and security tooling.

**Layer 2 -- Engine Layer**
The execution runtime. Manages the directed acyclic graph (DAG) of agent tasks,
schedules execution respecting topological order, checkpoints state for resume,
and manages the pool of running agent processes.

**Layer 3 -- Component Layer**
The building blocks of workflows. Each agent is a component node. Graphs compose
agents into workflows. Loops enable iterative patterns (debug-fix cycles). Switches
enable conditional routing (model selection, error handling). NodeTemplates and
ComposedGraphs enable reuse.

**Layer 4 -- Protocol Layer**
Governs how components communicate. Message Adapters normalize inter-agent
messages. Context Adapters inject relevant context into agent prompts. Interaction
Handlers bridge the system to external interfaces (human-in-the-loop, tools).

**Layer 5 -- Interaction Layer**
User-facing surfaces. The Web Dashboard provides real-time visualization. The CLI
provides programmatic access. The Chat Interface enables conversational control.
Vibe Graphing allows natural language workflow definition.

### 2.3 Request Lifecycle

```
 1. User submits PRD
         |
         v
 2. API Gateway authenticates & validates
         |
         v
 3. Orchestrator Agent initializes project (S0: Project Initialization)
         |
         v
 4. Brainstorming Agent explores ideas and possibilities (S1: Discovery & Brainstorming)
         |
         v
 5. Researcher Agent investigates technologies and approaches (S2: Research & Analysis)
         |
         v
 6. Architect Agent designs system structure (S3: Architecture & Design)
         |
         v
 7. Planner Agent decomposes architecture into task graph (S4: Planning & Configuration)
         |
         v
 8. Graph Engine builds execution DAG, Task Scheduler computes topological order
         |
         v
 9. Phase Coordinator begins execution:
    a. Implementation phase -- S5 (full parallel coding in isolated worktrees)
    b. Quality Assurance phase -- S6 (full parallel security, quality, architecture checks)
    c. Testing & Validation phase -- S7 (unit, integration, E2E, UI component,
       smoke, regression, mutation testing)
    d. Debug & Stabilization phase -- S8 (iterative fix loop until convergence or escalation)
    e. Documentation & Knowledge phase -- S9 (API docs, architecture docs, handoff report)
    f. Deployment & Delivery phase -- S10 (build, package, optional deploy)
         |
         v
 8. Checkpoint Manager saves state after each phase
         |
         v
 9. Delivery Agent produces final artifacts
         |
         v
10. User receives working application + handoff report
```

---

## 3. Agent Graph Engine

The Agent Graph Engine is the core execution substrate. It implements the
graph-centric model (via LangGraph, replacing MASFactory as the primary engine)
where multi-agent workflows are expressed as directed computation graphs.
MASFactory patterns remain as architectural inspiration.

### 3.1 Graph Skeleton (Node/Edge Primitives)

The Graph Skeleton provides the fundamental data structures.

```
+--------------------------------------------------+
|               Graph Skeleton                      |
|                                                   |
|   Node                     Edge                   |
|   +------------------+     +-------------------+  |
|   | id: UUID         |     | id: UUID          |  |
|   | type: NodeType   |     | source: NodeID    |  |
|   | template: str?   |     | target: NodeID    |  |
|   | config: dict     |     | type: EdgeType    |  |
|   | state: NodeState |     | condition: Expr?  |  |
|   | retry_policy: .. |     | transform: Fn?    |  |
|   +------------------+     +-------------------+  |
|                                                   |
|   NodeType:                EdgeType:              |
|     AGENT                    DATA_DEPENDENCY      |
|     SUBGRAPH                 CONTROL_DEPENDENCY   |
|     LOOP                     MESSAGE_PASSING      |
|     SWITCH                   STATE_PROPAGATION    |
|     INTERACTION                                   |
|                                                   |
|   NodeState:                                      |
|     PENDING -> READY -> RUNNING -> COMPLETED      |
|                    \-> FAILED -> RETRYING          |
|                    \-> SKIPPED                     |
+--------------------------------------------------+
```

**Node**: Represents an executable unit. Can be a single agent, a subgraph
(composed workflow), a loop construct, a switch (conditional branch), or an
interaction point (human-in-the-loop gate).

**Edge**: Represents a relationship between nodes. Data dependency edges enforce
execution order and carry output data. Control dependency edges enforce order
without data transfer. Message passing edges enable asynchronous communication.
State propagation edges share mutable state.

### 3.2 Component Layer

Built on top of the Graph Skeleton, the Component Layer provides higher-level
constructs.

```
 Component Layer
 +---------------------------------------------------------------+
 |                                                               |
 |  Agent                       Graph                            |
 |  +-----------------------+   +----------------------------+   |
 |  | role: AgentRole       |   | nodes: List[Node]          |   |
 |  | llm_config: LLMConfig |   | edges: List[Edge]          |   |
 |  | tools: List[Tool]     |   | entry_nodes: List[NodeID]  |   |
 |  | system_prompt: str    |   | exit_nodes: List[NodeID]   |   |
 |  | context_tier: L0|L1|L2|   | state: GraphState          |   |
 |  | max_iterations: int   |   +----------------------------+   |
 |  +-----------------------+                                    |
 |                                                               |
 |  Loop                        Switch                           |
 |  +-----------------------+   +----------------------------+   |
 |  | body: Graph           |   | cases: Dict[str, NodeID]   |   |
 |  | condition: Expr       |   | condition: Expr            |   |
 |  | max_iterations: int   |   | default: NodeID            |   |
 |  | exit_on: str          |   +----------------------------+   |
 |  +-----------------------+                                    |
 |                                                               |
 |  NodeTemplate                ComposedGraph                    |
 |  +-----------------------+   +----------------------------+   |
 |  | base_config: dict     |   | template_id: str           |   |
 |  | overrides: dict       |   | parameter_map: dict        |   |
 |  | clone() -> Node       |   | instantiate() -> Graph     |   |
 |  +-----------------------+   +----------------------------+   |
 |                                                               |
 |  Interaction                                                  |
 |  +-----------------------+                                    |
 |  | type: APPROVAL|INPUT  |                                    |
 |  | |FEEDBACK|ESCALATION  |                                    |
 |  | prompt: str           |                                    |
 |  | timeout: Duration     |                                    |
 |  | default_action: str   |                                    |
 |  +-----------------------+                                    |
 +---------------------------------------------------------------+
```

**NodeTemplate**: A clone-able agent blueprint. Allows defining a base agent
configuration (role, tools, prompt structure) that can be instantiated multiple
times with different parameters. For example, a "Developer" template can be
cloned into Frontend, Backend, and Middleware developer agents.

**ComposedGraph**: A reusable workflow pattern. Captures a frequently used
subgraph (e.g., the Code-Review-Test-Fix cycle) as a template that can be
parameterized and embedded within larger graphs.

### 3.3 Execution Model

```
Graph Execution Lifecycle:

  1. GRAPH COMPILATION
     - Parse workflow definition (imperative, declarative, or vibe-graphed)
     - Resolve NodeTemplates into concrete Nodes
     - Expand ComposedGraphs into inline subgraphs
     - Validate DAG (detect cycles except in explicit Loop constructs)
     - Compute topological sort for scheduling

  2. SCHEDULING
     - Identify ready nodes (all dependencies satisfied)
     - Check resource constraints (max concurrency, token budgets)
     - Assign nodes to execution slots

  3. EXECUTION
     - For each ready node:
       a. Prepare context (Context Adapter injects L0/L1/L2 data)
       b. Prepare workspace (Worktree Manager provisions git worktree)
       c. Execute agent (LLM call or CLI agent subprocess)
       d. Collect output (Message Adapter normalizes response)
       e. Update node state (RUNNING -> COMPLETED | FAILED)
       f. Propagate results to downstream edges
       g. Checkpoint state

  4. CONTROL FLOW EVALUATION
     - Loop nodes: check exit condition, increment iteration, re-queue body
     - Switch nodes: evaluate condition, activate matching branch
     - Interaction nodes: pause execution, await human input, resume

  5. TERMINATION
     - All exit nodes completed: pipeline SUCCESS
     - Unrecoverable failure: pipeline FAILED with diagnostic report
     - Human escalation: pipeline PAUSED awaiting intervention
```

### 3.4 Pre-Built ComposedGraphs

| ComposedGraph | Pattern | Nodes Involved |
|---|---|---|
| `CodingPipeline` | Linear with fan-out | Architect -> [Frontend, Backend, Middleware, Infra] |
| `ReviewGate` | Fan-in with approval | [CodeReview, Security, Tester] -> Interaction(Approve) |
| `DebugFixLoop` | Loop with exit condition | Debugger -> Developer -> Tester -> [exit if pass] |
| `ResearchSpike` | Parallel fan-out, merge | [Researcher_1, ..., Researcher_N] -> Merge -> Architect |
| `FullSDLC` | End-to-end pipeline | Orchestrator -> Brainstormer -> Researcher -> Architect -> Planner -> CodingPipeline -> ReviewGate -> TestingGate -> DebugFixLoop -> DocWriter -> Delivery |
| `ExperimentLoop` | Autonomous keep/discard optimization | Baseline -> Hypothesize -> Apply(branch) -> Measure -> Evaluate -> [Keep(merge) \| Discard(delete)] -> loop back. Inspired by Karpathy's autoresearch. Used by: DebugFixLoop (S8), Performance optimization (S6), Security hardening (S6), Test coverage (S7), and standalone Improve mode |
| `ImproveModePipeline` | Bounded autonomous optimization | CodebaseAnalysis -> MetricBaseline -> ExperimentLoop(target_metrics) -> ResultsReport -> HumanReviewGate |

### 3.5 Agent Role Definitions

Agents are organized by pipeline stage (S0-S10). Dependencies flow top-to-bottom:
upstream agent outputs feed into downstream agents.

| Stage | Agent | Node Type | LLM Preference | Tools | Context Tier | Upstream | Downstream |
|---|---|---|---|---|---|---|---|
| S0 | Orchestrator | AGENT | Claude Opus / o3 | Task decomposition, graph builder | L0 | User PRD | Brainstormer |
| S1 | Brainstormer | AGENT | Claude Opus / o3 | Idea generation, possibility exploration, concept mapping | L0 + L1 | Orchestrator | Researcher |
| S2 | Researcher | AGENT | Gemini 2.5 Pro | Web search, documentation retrieval, MCP | L0 + L2 | Brainstormer | Architect |
| S3 | Architect | AGENT | Claude Opus / o3 | Diagram generation, schema design, MCP | L0 + L1 | Researcher | Planner, Designer |
| S3 | Designer | AGENT | Claude Sonnet / GPT-4.1 | Wireframing, component hierarchy | L0 + L1 | Architect | Planner |
| S4 | Planner | AGENT | Claude Opus / o3 | Scheduling, estimation, dependency analysis | L0 + L1 | Architect, Designer | Frontend Dev, Backend Dev, Middleware Dev, Infra Engineer |
| S5 | Frontend Dev | AGENT | Claude Code / Codex CLI | File editing, terminal, browser | L0 + L1 + L2 | Planner | Security Auditor, Code Reviewer |
| S5 | Backend Dev | AGENT | Claude Code / Codex CLI | File editing, terminal, database | L0 + L1 + L2 | Planner | Security Auditor, Code Reviewer |
| S5 | Middleware Dev | AGENT | Claude Code / Codex CLI | File editing, terminal | L0 + L1 + L2 | Planner | Security Auditor, Code Reviewer |
| S5 | Infra Engineer | AGENT | Claude Sonnet / GPT-4.1 | Docker, Terraform, K8s | L0 + L1 | Planner | Security Auditor, Code Reviewer |
| S6 | Security Auditor | AGENT | Claude Sonnet | Trivy, Semgrep, Shannon, Gitleaks | L0 + L1 | All S5 Dev agents | Tester |
| S6 | Code Reviewer | AGENT | Claude Opus / o3 | AST analysis, style checkers | L0 + L1 + L2 | All S5 Dev agents | Tester |
| S7 | Tester | AGENT | GPT-4.1 / Sonnet | Test runners, coverage tools, Playwright, Storybook | L0 + L1 | Security Auditor, Code Reviewer | Debugger |
| S8 | Debugger | AGENT | Claude Opus / o3 | Debugger, log analysis, stack traces | L0 + L1 + L2 | Tester | Doc Writer (on fix loop exit) |
| S9 | Doc Writer | AGENT | Gemini 2.5 Pro / Sonnet | Doc generators, diagram tools | L0 + L1 | Debugger | Delivery |
| S10 | Delivery | AGENT | Claude Sonnet / GPT-4.1 | Build tools, package managers, deploy scripts | L0 + L1 | Doc Writer | User |
| S0-S10 | Project Manager | AGENT | Claude Sonnet / GPT-4.1 | Progress tracking, status reports, timeline management, blocker detection, notifications | L0 + L1 | All agents (observes) | Dashboard, User |

**Pipeline dependency chain (critical path):**
```
S0: Orchestrator
  -> S1: Brainstormer
    -> S2: Researcher
      -> S3: Architect -> Designer
        -> S4: Planner
          -> S5: [Frontend Dev | Backend Dev | Middleware Dev | Infra Engineer] (parallel)
            -> S6: [Security Auditor | Code Reviewer] (parallel)
              -> S7: Tester (unit, integration, E2E, UI component, smoke, regression, mutation)
                -> S8: Debugger (loop until stable)
                  -> S9: Doc Writer
                    -> S10: Delivery
```

**Key ordering rationale:**
- Brainstorming (S1) BEFORE Research (S2): brainstorm outputs define what needs to be researched
- Research (S2) BEFORE Architecture (S3): research findings inform architectural decisions
- Architecture (S3) BEFORE Planning (S4): you must know the system design before decomposing into tasks

---

## 4. Multi-LLM Abstraction Layer

The Multi-LLM Abstraction Layer decouples agent logic from specific LLM providers,
enabling task-optimized model routing, fallback chains, and cost management.

### 4.1 Architecture

```
+-----------------------------------------------------------------------+
|                    Multi-LLM Abstraction Layer                        |
|                                                                       |
|  +---------------------------+                                        |
|  |      Model Router         |                                        |
|  |                           |                                        |
|  |  +---------------------+ |    +-----------------------------+      |
|  |  | Routing Rules       | |    | Provider Registry           |      |
|  |  | - Task-based        | |    |                             |      |
|  |  | - Complexity-based  | |--->| +----------+ +----------+  |      |
|  |  | - Cost-based        | |    | | Anthropic| | OpenAI   |  |      |
|  |  | - Latency-based     | |    | | Provider | | Provider |  |      |
|  |  | - User override     | |    | +----------+ +----------+  |      |
|  |  +---------------------+ |    | +----------+               |      |
|  |                           |    | | Google   |               |      |
|  |  +---------------------+ |    | | Provider |               |      |
|  |  | Fallback Chain      | |    | +----------+               |      |
|  |  | Manager             | |    +-----------------------------+      |
|  |  +---------------------+ |                                        |
|  +---------------------------+                                        |
|                                                                       |
|  +---------------------------+   +-----------------------------+      |
|  |   Unified Request/       |   | Rate Limiter & Cost         |      |
|  |   Response Interface     |   | Tracker                     |      |
|  |                           |   |                             |      |
|  |  - Prompt normalization  |   | - Per-provider rate limits  |      |
|  |  - Response parsing      |   | - Token budget enforcement  |      |
|  |  - Streaming support     |   | - Cost aggregation          |      |
|  |  - Tool call handling    |   | - Usage analytics           |      |
|  |  - Retry with backoff    |   |                             |      |
|  +---------------------------+   +-----------------------------+      |
+-----------------------------------------------------------------------+
```

### 4.2 Provider Adapters

Each LLM provider is wrapped in a uniform adapter interface.

```python
# Pseudocode -- Provider Adapter Interface

class LLMProvider(Protocol):
    """Uniform interface for all LLM providers."""

    async def complete(
        self,
        messages: list[Message],
        model: str,
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> CompletionResponse: ...

    async def stream_complete(
        self,
        messages: list[Message],
        model: str,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]: ...

    def get_token_count(self, messages: list[Message], model: str) -> int: ...
    def get_rate_limits(self, model: str) -> RateLimits: ...
    def get_pricing(self, model: str) -> Pricing: ...
```

### 4.3 Model Routing Strategy

```
Routing Decision Tree:

  Input: (task_type, complexity_score, user_overrides, provider_health)
         |
         v
  1. User override present?
     YES -> Use specified model (if healthy)
     NO  -> Continue
         |
         v
  2. Match task_type to routing table:
     +-------------------+------------------+--------------------+
     | Task Type         | Primary Model    | Fallback Model     |
     +-------------------+------------------+--------------------+
     | Architecture      | Claude Opus      | o3                 |
     | Complex reasoning | Claude Opus      | o3                 |
     | Code generation   | GPT-4.1          | Claude Sonnet      |
     | Code review       | Claude Opus      | Claude Sonnet      |
     | Research          | Gemini 2.5 Pro   | Claude Sonnet      |
     | Documentation     | Gemini 2.5 Pro   | Claude Sonnet      |
     | Simple tasks      | Claude Haiku     | Gemini Flash       |
     | Test generation   | GPT-4.1          | Claude Sonnet      |
     | Debugging         | Claude Opus      | o3                 |
     +-------------------+------------------+--------------------+
         |
         v
  3. Complexity adjustment:
     complexity < 0.3  -> Downgrade to cheaper model (Haiku/Flash/o4-mini)
     complexity >= 0.7 -> Ensure premium model (Opus/o3/Gemini Pro)
         |
         v
  4. Health check:
     Provider healthy?     -> Proceed
     Provider rate-limited? -> Use fallback
     Provider down?        -> Use fallback chain
         |
         v
  5. Return selected (provider, model) tuple
```

### 4.4 Cost Management

| Control | Implementation |
|---|---|
| Token budgets | Per-agent, per-phase, and per-project token limits |
| Cost tracking | Real-time cost accumulation per provider with dashboard display |
| Model downgrade | Automatic downgrade to cheaper model when budget threshold reached |
| Caching | Response caching for identical prompts (deterministic tasks) |
| Prompt optimization | Automatic context pruning when approaching token limits |

---

## 5. CLI Agent Integration Layer

CodeBot delegates hands-on coding tasks to CLI-based coding agents that operate
within isolated git worktrees. These agents have direct filesystem access, can
run terminal commands, and produce actual code changes.

### 5.1 Architecture

```
+-----------------------------------------------------------------------+
|                   CLI Agent Integration Layer                         |
|                                                                       |
|  +---------------------------+                                        |
|  |   Agent Bridge            |                                        |
|  |                           |                                        |
|  |  +---------------------+ |                                        |
|  |  | Task Translator     | | Converts CodeBot task spec into        |
|  |  | (Task -> Prompt)    | | agent-specific prompt format            |
|  |  +---------------------+ |                                        |
|  |  +---------------------+ |                                        |
|  |  | Output Parser       | | Parses agent output into structured    |
|  |  | (Response -> Result)| | result (files changed, tests run, etc) |
|  |  +---------------------+ |                                        |
|  |  +---------------------+ |                                        |
|  |  | Session Manager     | | Manages agent lifecycle & state        |
|  |  +---------------------+ |                                        |
|  +---------------------------+                                        |
|                                                                       |
|  +---------------------------+  +---------------------------+         |
|  | Claude Code Adapter      |  | Codex CLI Adapter         |         |
|  |                           |  |                           |         |
|  | - Claude Agent SDK        |  | - Subprocess invocation   |         |
|  | - Direct API integration  |  | - Structured output parse |         |
|  | - Streaming support       |  | - Sandbox mode            |         |
|  | - Tool use (MCP)          |  | - File diff extraction    |         |
|  +---------------------------+  +---------------------------+         |
|                                                                       |
|  +---------------------------+                                        |
|  | Gemini CLI Adapter        |                                        |
|  |                           |                                        |
|  | - Subprocess invocation   |                                        |
|  | - Structured output parse |                                        |
|  | - Sandbox mode            |                                        |
|  +---------------------------+                                        |
+-----------------------------------------------------------------------+
```

### 5.2 Claude Code Integration (Primary)

Claude Code is the primary CLI agent, integrated via the Claude Agent SDK for
deep control and streaming capabilities.

```
Claude Code Integration Flow:

  1. Worktree Manager provisions isolated git worktree
  2. Context Adapter prepares context:
     - L0: Project summary, agent role, current task
     - L1: Relevant source files, architecture docs
     - L2: On-demand retrieval via MCP tools
  3. Agent Bridge constructs Claude Agent SDK session:
     - System prompt with role instructions
     - Tools: file read/write, terminal, browser, MCP servers
     - Allowed commands whitelist
     - Max turns limit
  4. Claude Code executes in worktree:
     - Reads existing code
     - Writes new files / edits existing
     - Runs commands (build, test, lint)
     - Uses MCP tools for context retrieval
  5. Output Parser extracts:
     - Files created/modified/deleted (git diff)
     - Commands executed and their output
     - Test results
     - Agent reasoning/decisions
  6. Results propagated to downstream graph nodes
```

### 5.3 Codex CLI / Gemini CLI Integration

```
Subprocess-Based CLI Agent Flow:

  1. Prepare working directory (isolated worktree)
  2. Write task prompt to temporary file
  3. Invoke CLI agent as subprocess:
     - codex --quiet --model o3 --approval-mode full-auto < task.md
     - gemini --model gemini-2.5-pro < task.md
  4. Monitor stdout/stderr for progress
  5. On completion, parse structured output
  6. Extract file changes via git diff in worktree
  7. Return structured result to graph engine
```

### 5.4 Agent Selection Strategy

| Factor | Weight | Description |
|---|---|---|
| Task complexity | 30% | Complex tasks favor Claude Code (best reasoning) |
| Codebase familiarity | 25% | Agent that has prior context on the codebase preferred |
| Model routing | 20% | Aligns with Multi-LLM routing decisions |
| Availability | 15% | Rate limit and health status |
| Cost | 10% | Cost-optimized selection when quality is equivalent |

---

## 6. Context Management System

CodeBot's built-in hierarchical context system (inspired by OpenViking patterns) ensures
agents receive precisely the information they need, minimizing token waste while
maximizing relevance.

### 6.1 Three-Tier Architecture

```
+-----------------------------------------------------------------------+
|                    Context Management System                          |
|                                                                       |
|  +===================================================================+
|  | TIER L0 -- ALWAYS LOADED (~2K tokens)                             |
|  |                                                                   |
|  | - Project summary (name, tech stack, conventions)                 |
|  | - Current task specification                                      |
|  | - Agent role instructions and system prompt                       |
|  | - Active phase context (what has been completed, what is next)    |
|  | - Critical constraints and non-functional requirements            |
|  +===================================================================+
|                          |
|                          v
|  +===================================================================+
|  | TIER L1 -- ON-DEMAND (~10K tokens)                                |
|  |                                                                   |
|  | - Relevant source files (loaded by Context Adapter)               |
|  | - Architecture documents and design decisions                     |
|  | - API specifications (OpenAPI/GraphQL schemas)                    |
|  | - Database schemas and migration history                          |
|  | - Test results from upstream agents                               |
|  | - Security scan reports relevant to current task                  |
|  | - Upstream agent outputs (code review comments, etc.)             |
|  +===================================================================+
|                          |
|                          v
|  +===================================================================+
|  | TIER L2 -- DEEP RETRIEVAL (~20K tokens)                           |
|  |                                                                   |
|  | - Full codebase semantic search (vector + keyword hybrid)         |
|  | - External documentation and API references                      |
|  | - Research results and reference implementations                 |
|  | - Historical project decisions (ADRs)                            |
|  | - Stack Overflow / documentation snippets                        |
|  | - Dependency documentation and usage examples                    |
|  +===================================================================+
|                                                                       |
+-----------------------------------------------------------------------+
```

### 6.2 Context Sources and Technologies

```
+---------------------------+     +---------------------------+
|   Filesystem Paradigm     |     |   Vector Store            |
|   (Built-in, inspired by  |
|    OpenViking patterns)   |     |   (LanceDB / Qdrant)      |
|                           |     |                           |
| project/                  |     | - Code embeddings         |
|   .codebot/               |     |   (Tree-sitter + embed)   |
|     context/              |     | - Doc embeddings          |
|       L0/                 |     | - Semantic search         |
|         summary.md        |     | - Hybrid retrieval        |
|         conventions.md    |     |   (vector + BM25)         |
|       L1/                 |     +---------------------------+
|         architecture/     |
|         schemas/          |     +---------------------------+
|         api-specs/        |     |   Project Memory          |
|       L2/                 |     |   (Letta / MemGPT)        |
|         research/         |     |                           |
|         references/       |     | - Decision history        |
|     memory/               |     | - Agent learnings         |
|       decisions.json      |     | - Error patterns          |
|       learnings.json      |     | - Conversation summaries  |
|                           |     +---------------------------+
+---------------------------+
                              +---------------------------+
                              |   RAG Pipeline            |
                              |   (RAGFlow)               |
                              |                           |
                              | - Document chunking       |
                              | - Multi-strategy retrieval|
                              | - Re-ranking              |
                              | - Citation tracking       |
                              +---------------------------+
```

### 6.3 Context Adapter

The Context Adapter is the Protocol Layer component responsible for assembling
the context payload for each agent invocation.

```
Context Assembly Pipeline:

  1. LOAD L0 (mandatory)
     - Read project summary from .codebot/context/L0/
     - Inject current task specification
     - Inject agent role system prompt

  2. DETERMINE L1 NEEDS (rule-based)
     - Match task type to relevant context categories:
       Frontend Dev -> UI components, design specs, API specs
       Backend Dev  -> Database schemas, API specs, business logic
       Tester       -> Source under test, existing tests, coverage report
       Debugger     -> Failing tests, stack traces, recent changes

  3. LOAD L1 (on-demand)
     - Retrieve relevant files from filesystem or database
     - Apply token budget constraints
     - Prioritize by relevance score

  4. PREPARE L2 HOOKS (deferred)
     - Register MCP tools for semantic search
     - Configure RAG retrieval endpoints
     - Agent can pull L2 context as needed during execution

  5. ASSEMBLE AND OPTIMIZE
     - Concatenate L0 + L1 content
     - Check total token count against model context window
     - If over budget: summarize, truncate, or defer to L2
     - Return assembled context payload
```

### 6.4 Directory Recursive Retrieval

CodeBot's built-in hierarchical context system (inspired by OpenViking patterns)
supports recursive directory access patterns for context retrieval.

```
Retrieval Modes:

  FILE     - Load a single file by path
  DIR      - Load all files in a directory (non-recursive)
  TREE     - Load all files in a directory tree (recursive)
  GLOB     - Load files matching a glob pattern
  SEMANTIC - Vector similarity search across indexed content
  HYBRID   - Combine SEMANTIC + keyword (BM25) search
  GRAPH    - Traverse knowledge graph relationships (Cognee)
```

### 6.5 MCP Integration

The Model Context Protocol (MCP) provides a standardized interface for agents
to access tools and context sources at runtime.

| MCP Server | Purpose | Used By |
|---|---|---|
| Filesystem MCP | Read/write project files | All developer agents |
| Git MCP | Git operations (diff, log, branch) | All agents |
| Database MCP | Query project database | Backend Dev, Architect |
| Search MCP | Semantic code search | All agents (L2 retrieval) |
| Browser MCP | Web research | Researcher agent |
| Terminal MCP | Command execution | Developer agents |
| Documentation MCP | External API docs retrieval | Researcher, Developer agents |

### 6.6 Built-in Episodic Memory

CodeBot's built-in episodic memory (inspired by claude-mem patterns) provides
persistent learning across sessions and projects. Unlike external memory
integrations, this is a first-class built-in feature of the platform.

| Capability | Description |
|---|---|
| **Lifecycle hooks** | Memory capture at agent start, checkpoint, and completion events |
| **Semantic compression** | Automatic summarization of verbose agent interactions into compact memory entries |
| **Progressive disclosure** | Memories surfaced at increasing detail levels based on relevance scores |
| **Cross-session learning** | Agents retain learnings (error patterns, successful strategies) across project runs |
| **Cross-project learning** | Generalizable patterns (e.g., common framework pitfalls) shared across projects |
| **Observable retrieval** | Memory retrieval trajectories visible in the web dashboard for debugging and tuning |

Episodic memory entries are stored in the relational database (PostgreSQL) with
vector embeddings indexed in the vector store for semantic retrieval.

---

## 7. Security and Quality Pipeline

The Security and Quality Pipeline runs as a parallel fan-in stage after
implementation, providing comprehensive code analysis before delivery.

### 7.1 Pipeline Architecture

```
+-----------------------------------------------------------------------+
|                  Security & Quality Pipeline                          |
|                                                                       |
|  Implementation Output (from all developer agents)                    |
|         |                                                             |
|         v                                                             |
|  +------+------+------+------+------+------+                         |
|  |      |      |      |      |      |      |                         |
|  v      v      v      v      v      v      v                         |
| SAST  DAST  Secrets License SCA   IaC    Code                        |
|             Scan   Compliance     Scan   Quality                      |
|                                                                       |
| Semgrep Shannon Gitleaks ScanCode OpenSCA KICS  SonarQube             |
| +       +      +        FOSSology+       +     +                      |
| CodeQL         GitHub   ORT             Trivy  Linters                |
|                Secret                   (container)                    |
|                Scan                                                    |
|  |      |      |      |      |      |      |                         |
|  v      v      v      v      v      v      v                         |
|  +------+------+------+------+------+------+                         |
|         |                                                             |
|         v                                                             |
|  +-------------------+                                                |
|  | Report Aggregator |                                                |
|  |                   |                                                |
|  | - Normalize findings to common format                              |
|  | - Deduplicate across scanners                                      |
|  | - Classify severity (Critical/High/Medium/Low/Info)                |
|  | - Map findings to source locations                                 |
|  +-------------------+                                                |
|         |                                                             |
|         v                                                             |
|  +-------------------+                                                |
|  | Quality Gate      |                                                |
|  |                   |                                                |
|  | PASS conditions:                                                   |
|  |   - Zero critical vulnerabilities                                  |
|  |   - Zero high vulnerabilities                                      |
|  |   - Zero leaked secrets                                            |
|  |   - License compliance: all dependencies approved                  |
|  |   - Code coverage >= 80%                                           |
|  |   - SonarQube quality gate: passed                                 |
|  |                                                                    |
|  | FAIL -> Route to Debugger agent for remediation                    |
|  | PASS -> Proceed to Delivery                                        |
|  +-------------------+                                                |
+-----------------------------------------------------------------------+
```

### 7.2 Security Scanner Configuration

| Scanner | Category | Integration Method | Trigger |
|---|---|---|---|
| Semgrep | SAST | CLI subprocess | After code generation |
| SonarQube CE | SAST + Quality | REST API | After code generation |
| CodeQL | SAST (GitHub) | GitHub Actions | On PR creation |
| Shannon | DAST | CLI subprocess | After build/deploy to staging |
| Trivy | Container/SCA | CLI subprocess | After Dockerfile generation |
| Gitleaks | Secrets | CLI subprocess + pre-commit | Continuous |
| ScanCode | License | CLI subprocess | After dependency resolution |
| FOSSology | License | REST API | After dependency resolution |
| ORT | License + SCA | CLI subprocess | After dependency resolution |
| OpenSCA | SCA | CLI subprocess | After dependency resolution |
| KICS | IaC Security | CLI subprocess | After IaC generation |

### 7.3 Finding Schema

All scanner outputs are normalized to a common finding format:

```
Finding:
  id: UUID
  scanner: str                    # e.g., "semgrep", "trivy"
  category: SAST|DAST|SCA|SECRET|LICENSE|IAC|QUALITY
  severity: CRITICAL|HIGH|MEDIUM|LOW|INFO
  title: str                      # Short description
  description: str                # Detailed explanation
  file_path: str                  # Affected file
  line_start: int                 # Start line
  line_end: int                   # End line
  cwe_id: str?                    # CWE identifier if applicable
  cve_id: str?                    # CVE identifier if applicable
  remediation: str                # Suggested fix
  confidence: float               # Scanner confidence (0.0 - 1.0)
  false_positive: bool            # Marked by reviewer
  status: OPEN|FIXED|ACCEPTED|IGNORED
```

---

## 8. Data Architecture

### 8.1 Data Store Overview

```
+-----------------------------------------------------------------------+
|                       Data Architecture                               |
|                                                                       |
|  +---------------------------+     +---------------------------+      |
|  |     PostgreSQL            |     |     Redis                 |      |
|  |                           |     |                           |      |
|  |  Projects                 |     |  Session cache            |      |
|  |  +-----------------+      |     |  Agent state cache        |      |
|  |  | id              |      |     |  Rate limit counters      |      |
|  |  | name            |      |     |  LLM response cache       |      |
|  |  | prd_content     |      |     |                           |      |
|  |  | config          |      |                                        |
|  |  | status          |      |     +---------------------------+      |
|  |  | created_at      |      |     |     NATS + JetStream       |      |
|  |  +-----------------+      |     |                           |      |
|  |                           |     |  Event streaming          |      |
|  |                           |     |  Inter-agent messaging    |      |
|  |                           |     |  Task queue (Taskiq)      |      |
|  |                           |     +---------------------------+      |
|  |                           |                                        |
|  |  Pipeline Runs            |     |     Vector Store           |      |
|  |  +-----------------+      |     |     (LanceDB / Qdrant)     |      |
|  |  | id              |      |     |                           |      |
|  |  | project_id (FK) |      |     |  Code embeddings          |      |
|  |  | graph_snapshot  |      |     |  +-----------------+      |      |
|  |  | status          |      |     |  | file_path       |      |      |
|  |  | started_at      |      |     |  | chunk_content   |      |      |
|  |  | completed_at    |      |     |  | embedding       |      |      |
|  |  | checkpoints     |      |     |  | language        |      |      |
|  |  +-----------------+      |     |  | ast_type        |      |      |
|  |                           |     |  | project_id      |      |      |
|  |  Agent Tasks              |     |  +-----------------+      |      |
|  |  +-----------------+      |     |                           |      |
|  |  | id              |      |     |  Doc embeddings           |      |
|  |  | run_id (FK)     |      |     |  +-----------------+      |      |
|  |  | agent_role      |      |     |  | source          |      |      |
|  |  | node_id         |      |     |  | chunk_content   |      |      |
|  |  | status          |      |     |  | embedding       |      |      |
|  |  | input_context   |      |     |  | doc_type        |      |      |
|  |  | output_result   |      |     |  | project_id      |      |      |
|  |  | llm_model_used  |      |     |  +-----------------+      |      |
|  |  | tokens_used     |      |     +---------------------------+      |
|  |  | cost            |      |                                        |
|  |  | started_at      |      |     +---------------------------+      |
|  |  | completed_at    |      |     |     Object Store           |      |
|  |  | error_info      |      |     |     (MinIO / S3 / Local)   |      |
|  |  +-----------------+      |     |                           |      |
|  |                           |     |  Build artifacts          |      |
|  |  Security Findings        |     |  Generated documentation  |      |
|  |  +-----------------+      |     |  Screenshot captures      |      |
|  |  | (See Finding    |      |     |  Test reports (HTML)       |      |
|  |  |  Schema 7.3)    |      |     |  Security scan reports    |      |
|  |  +-----------------+      |     |  Checkpoint snapshots     |      |
|  |                           |     |  Agent conversation logs  |      |
|  |  Agent Messages           |     |                           |      |
|  |  +-----------------+      |     +---------------------------+      |
|  |  | id              |      |                                        |
|  |  | run_id (FK)     |      |     +---------------------------+      |
|  |  | from_agent      |      |     |     Knowledge Graph        |      |
|  |  | to_agent        |      |     |     (Cognee)               |      |
|  |  | message_type    |      |     |                           |      |
|  |  | payload         |      |     |  Architecture decisions   |      |
|  |  | timestamp       |      |     |  Code dependency graph    |      |
|  |  +-----------------+      |     |  Requirement traceability |      |
|  |                           |     |  Technology relationships |      |
|  |  LLM Usage Logs           |     +---------------------------+      |
|  |  +-----------------+      |                                        |
|  |  | id              |      |                                        |
|  |  | task_id (FK)    |      |                                        |
|  |  | provider        |      |                                        |
|  |  | model           |      |                                        |
|  |  | input_tokens    |      |                                        |
|  |  | output_tokens   |      |                                        |
|  |  | cost_usd        |      |                                        |
|  |  | latency_ms      |      |                                        |
|  |  | timestamp       |      |                                        |
|  |  +-----------------+      |                                        |
|  +---------------------------+                                        |
+-----------------------------------------------------------------------+
```

### 8.2 Data Flow Diagram

```
PRD Input
    |
    v
[PostgreSQL: Projects] ---- create project record
    |
    v
[PostgreSQL: Pipeline Runs] ---- create run record
    |
    v
[NATS: Task Queue] ---- enqueue agent tasks (via Taskiq + NATS broker)
    |
    +---> [Agent executes] ---> [PostgreSQL: Agent Tasks] (status, result)
    |         |
    |         +---> [Vector Store] (index new code)
    |         +---> [Object Store] (store artifacts)
    |         +---> [NATS: JetStream] (real-time events to dashboard)
    |         +---> [Knowledge Graph] (update decision/dependency graph)
    |         +---> [PostgreSQL: LLM Usage] (track tokens/cost)
    |
    v
[PostgreSQL: Security Findings] ---- store scan results
    |
    v
[Object Store: Final Artifacts] ---- build output, docs, reports
```

### 8.3 Backup and Retention

| Data Store | Backup Strategy | Retention |
|---|---|---|
| PostgreSQL | Daily automated backup, WAL archiving | 90 days for runs, indefinite for projects |
| Redis | RDB snapshots every 15 minutes | Session data: TTL-based (24h), PubSub: ephemeral |
| Vector Store | Snapshot on project completion | Lifetime of project |
| Object Store | Versioned storage | 30 days for intermediate, indefinite for final |
| Git Worktrees | Part of git repository | Cleaned after pipeline completion |
| Knowledge Graph | Export on project completion | Lifetime of project |

---

## 9. Infrastructure Architecture

### 9.1 Execution Environment

```
+-----------------------------------------------------------------------+
|                    Infrastructure Architecture                        |
|                                                                       |
|  Host Machine (Developer Workstation or Server)                       |
|  +-------------------------------------------------------------------+
|  |                                                                   |
|  |  Docker Compose / Podman Compose                                  |
|  |  +---------------------------------------------------------------+
|  |  |                                                               |
|  |  |  +------------------+  +------------------+                   |
|  |  |  | codebot-core     |  | codebot-web      |                   |
|  |  |  | (Python 3.12)    |  | (Next.js)        |                   |
|  |  |  |                  |  |                   |                   |
|  |  |  | - Orchestration  |  | - Dashboard UI   |                   |
|  |  |  | - Graph Engine   |  | - WebSocket      |                   |
|  |  |  | - Agent Pool     |  | - REST API       |                   |
|  |  |  | - CLI Agent Mgr  |  |                   |                   |
|  |  |  +------------------+  +------------------+                   |
|  |  |                                                               |
|  |  |  +------------------+  +------------------+                   |
|  |  |  | postgres         |  | redis            |                   |
|  |  |  | (PostgreSQL 16)  |  | (Redis 7)        |                   |
|  |  |  +------------------+  +------------------+                   |
|  |  |                                                               |
|  |  |  +------------------+  +------------------+                   |
|  |  |  | chroma           |  | minio            |                   |
|  |  |  | (Vector Store)   |  | (Object Store)   |                   |
|  |  |  +------------------+  +------------------+                   |
|  |  |                                                               |
|  |  |  +------------------+  +------------------+                   |
|  |  |  | sonarqube        |  | ragflow          |                   |
|  |  |  | (Code Quality)   |  | (RAG Pipeline)   |                   |
|  |  |  +------------------+  +------------------+                   |
|  |  |                                                               |
|  |  +---------------------------------------------------------------+
|  |                                                                   |
|  |  Git Worktree Area (Host Filesystem)                              |
|  |  +---------------------------------------------------------------+
|  |  |                                                               |
|  |  |  project-repo/                   (main repository)            |
|  |  |    +-- .git/                                                  |
|  |  |    +-- src/                                                   |
|  |  |                                                               |
|  |  |  .worktrees/                                                  |
|  |  |    +-- agent-frontend-dev-a1b2/  (isolated worktree)          |
|  |  |    +-- agent-backend-dev-c3d4/   (isolated worktree)          |
|  |  |    +-- agent-middleware-e5f6/    (isolated worktree)           |
|  |  |    +-- agent-infra-g7h8/        (isolated worktree)           |
|  |  |                                                               |
|  |  +---------------------------------------------------------------+
|  |                                                                   |
|  |  Sandbox Area (Docker-in-Docker or Sysbox)                       |
|  |  +---------------------------------------------------------------+
|  |  |                                                               |
|  |  |  +------------------+                                         |
|  |  |  | sandbox-runner   |  Executes generated code safely         |
|  |  |  | (Isolated Docker)|  - No network (optional)                |
|  |  |  | - CPU/mem limits |  - Ephemeral filesystem                 |
|  |  |  | - Timeout kill   |  - seccomp/AppArmor profiles            |
|  |  |  +------------------+                                         |
|  |  |                                                               |
|  |  +---------------------------------------------------------------+
|  +-------------------------------------------------------------------+
+-----------------------------------------------------------------------+
```

### 9.2 Git Worktree Management

Inspired by Superset's parallel agent execution model, each coding agent operates
in an isolated git worktree to prevent conflicts.

```
Worktree Lifecycle:

  1. PROVISION
     - Agent assigned a coding task
     - Worktree Manager creates new branch: agent/<role>/<task-id>
     - git worktree add .worktrees/agent-<role>-<id> agent/<role>/<task-id>
     - Working directory mounted/accessible to CLI agent

  2. EXECUTE
     - CLI agent operates exclusively within its worktree
     - Changes are committed to the agent's branch
     - Worktree isolated from other agents' changes

  3. MERGE
     - On task completion, agent's branch reviewed
     - If code review passes:
       a. Rebase onto main branch (resolve conflicts if any)
       b. Fast-forward merge
     - If conflicts detected:
       a. Conflict resolution agent attempts automatic resolution
       b. Escalate to human if automatic resolution fails

  4. CLEANUP
     - git worktree remove .worktrees/agent-<role>-<id>
     - Agent branch deleted after successful merge
     - Worktree directory cleaned up
```

### 9.3 Sandbox Execution

CodeBot's built-in sandbox execution system provides containerized per-agent
execution environments using Docker. Each coding agent gets its own sandbox
pre-configured with the project's tech stack.

| Sandbox Property | Configuration |
|---|---|
| Base image | `node:22-slim` or `python:3.12-slim` (task-dependent) |
| CPU limit | 2 cores |
| Memory limit | 2 GB |
| Execution timeout | 300 seconds (configurable) |
| Network | Disabled by default, enabled for DAST/integration tests |
| Filesystem | Ephemeral (tmpfs), project code mounted read-write |
| Security profile | seccomp default + AppArmor confinement |
| Capabilities | All dropped except minimal set |
| Isolation runtime | gVisor (runsc) or Kata Containers for enhanced isolation |

#### 9.3.1 Live Preview

The sandbox execution system supports live preview capabilities for generated
applications:

- **Web apps**: Hot-reload dev servers (e.g., Vite, Next.js dev) are started
  inside the sandbox with port forwarding to the host, enabling real-time
  preview of generated UIs in the dashboard.
- **Desktop apps**: VNC-based preview for desktop applications, streamed to
  the dashboard via noVNC.
- Preview URLs are surfaced in the web dashboard for human review during
  interactive checkpoints.

### 9.4 Resource Governance

```
Resource Governor:

  +-----------------------------+
  | Concurrency Limits          |
  |                             |
  | Max parallel agents: 15    |
  | Max CLI agent processes: 8 |
  | Max sandbox containers: 4  |
  | Max concurrent LLM calls:  |
  |   per provider: 10         |
  +-----------------------------+
          |
          v
  +-----------------------------+
  | Token Budget Enforcement    |
  |                             |
  | Per-agent budget: 100K tok  |
  | Per-phase budget: 500K tok  |
  | Per-project budget: 5M tok  |
  | Alert at: 80% consumption  |
  | Hard stop at: 100%         |
  +-----------------------------+
          |
          v
  +-----------------------------+
  | System Resource Monitoring  |
  |                             |
  | CPU utilization threshold   |
  | Memory pressure detection   |
  | Disk space monitoring       |
  | Docker resource tracking    |
  +-----------------------------+
```

---

## 10. Communication Architecture

### 10.1 Inter-Agent Messaging

Following the graph-centric three communication flows (inspired by MASFactory), CodeBot implements a layered
messaging system.

```
+-----------------------------------------------------------------------+
|                   Communication Architecture                          |
|                                                                       |
|  STATE FLOW (Shared Mutable State)                                    |
|  +-------------------------------------------------------------------+
|  |                                                                   |
|  |  Pipeline State Store (Redis)                                     |
|  |  +-------------------------------------------------------------+ |
|  |  | project_context:    Architecture decisions, tech stack       | |
|  |  | phase_state:        Current phase, completed phases          | |
|  |  | task_graph:         Node states, edge data                   | |
|  |  | shared_artifacts:   File manifests, schema definitions       | |
|  |  | quality_metrics:    Coverage, findings count, gate status    | |
|  |  +-------------------------------------------------------------+ |
|  |                                                                   |
|  |  Access pattern: Read-before-write with optimistic locking        |
|  |  Consistency: Eventually consistent with conflict detection       |
|  +-------------------------------------------------------------------+
|                                                                       |
|  MESSAGE FLOW (Agent-to-Agent Direct Messages)                        |
|  +-------------------------------------------------------------------+
|  |                                                                   |
|  |  Message Types:                                                   |
|  |  +-------------------+----------------------------------------+   |
|  |  | TASK_HANDOFF      | Transfer task output to downstream     |   |
|  |  | REVIEW_REQUEST    | Request code review from reviewer      |   |
|  |  | REVIEW_RESULT     | Return review findings                 |   |
|  |  | FIX_REQUEST       | Request fix from developer             |   |
|  |  | TEST_RESULT       | Report test execution results          |   |
|  |  | CONTEXT_REQUEST   | Request additional context             |   |
|  |  | CONTEXT_RESPONSE  | Provide requested context              |   |
|  |  | ESCALATION        | Escalate issue to orchestrator/human   |   |
|  |  +-------------------+----------------------------------------+   |
|  |                                                                   |
|  |  Transport: NATS JetStream (persistent, ordered, consumer groups)  |
|  |  Format: JSON with schema validation                              |
|  |  Delivery: At-least-once with idempotency keys                    |
|  +-------------------------------------------------------------------+
|                                                                       |
|  CONTROL FLOW (Orchestrator-Driven Signals)                           |
|  +-------------------------------------------------------------------+
|  |                                                                   |
|  |  Signal Types:                                                    |
|  |  +-------------------+----------------------------------------+   |
|  |  | PHASE_START       | Begin a new pipeline phase             |   |
|  |  | PHASE_COMPLETE    | Phase finished, proceed to next        |   |
|  |  | AGENT_START       | Activate an agent node                 |   |
|  |  | AGENT_CANCEL      | Cancel a running agent                 |   |
|  |  | PIPELINE_PAUSE    | Pause execution (human gate)           |   |
|  |  | PIPELINE_RESUME   | Resume after human approval            |   |
|  |  | PIPELINE_ABORT    | Terminate the pipeline                 |   |
|  |  | CHECKPOINT        | Save current state                     |   |
|  |  +-------------------+----------------------------------------+   |
|  |                                                                   |
|  |  Transport: Redis PubSub (fire-and-forget, real-time)             |
|  |  Reliability: Critical signals also persisted to PostgreSQL       |
|  +-------------------------------------------------------------------+
+-----------------------------------------------------------------------+
```

### 10.2 Event Bus

The Event Bus provides real-time observability and enables the Web Dashboard to
display live updates.

```
Event Bus (Redis PubSub + Socket.IO):

  Publishers (Agents, Engine, Pipeline Manager)
       |
       v
  +-------------------+
  |   Event Bus       |
  |   (Redis PubSub)  |
  +--------+----------+
           |
  +--------+----------+--------+--------+
  |        |          |        |        |
  v        v          v        v        v
 Web     CLI       Metrics  Logging  Webhook
 Dash    Output    Collector Sink    Dispatch
 (WS)
```

**Event Categories:**

| Category | Events | Consumers |
|---|---|---|
| Pipeline | `pipeline.started`, `pipeline.completed`, `pipeline.failed`, `pipeline.paused` | Dashboard, CLI, Webhooks |
| Agent | `agent.started`, `agent.completed`, `agent.failed`, `agent.output` | Dashboard, CLI, Metrics |
| Task | `task.queued`, `task.started`, `task.completed`, `task.failed` | Dashboard, Scheduler |
| Code | `code.file_created`, `code.file_modified`, `code.committed`, `code.merged` | Dashboard, Code Viewer |
| Security | `scan.started`, `scan.completed`, `finding.new`, `gate.passed`, `gate.failed` | Dashboard, Security Panel |
| Test | `test.started`, `test.passed`, `test.failed`, `coverage.updated` | Dashboard, Debugger |
| Cost | `tokens.consumed`, `budget.warning`, `budget.exceeded` | Dashboard, Resource Governor |
| System | `system.health`, `system.error`, `system.resource_warning` | Monitoring, Alerting |

### 10.3 Message Envelope

```
MessageEnvelope:
  id: UUID                        # Unique message ID
  correlation_id: UUID            # Links related messages (same task chain)
  run_id: UUID                    # Pipeline run this message belongs to
  from_agent: str                 # Source agent role + instance ID
  to_agent: str                   # Target agent role (or "*" for broadcast)
  message_type: MessageType       # See Message Types above
  payload: dict                   # Type-specific payload
  timestamp: datetime             # ISO 8601 timestamp
  ttl: int                        # Time-to-live in seconds (0 = no expiry)
  priority: int                   # 0 (lowest) to 9 (highest)
  idempotency_key: str            # For exactly-once processing
  metadata: dict                  # Tracing context, span IDs, etc.
```

---

## 11. Deployment Architecture

### 11.1 Deployment Modes

CodeBot supports three deployment modes to accommodate different use cases.

```
MODE 1: LOCAL DEVELOPMENT (Single Machine)
+--------------------------------------------------+
|  Developer Workstation                           |
|                                                  |
|  docker compose up                               |
|  +--------------------------------------------+ |
|  | codebot-core | web | postgres | redis |     | |
|  | chroma | minio | sonarqube | ragflow       | |
|  +--------------------------------------------+ |
|  |                                              | |
|  | CLI Agents run natively on host              | |
|  | Git worktrees on host filesystem             | |
|  +----------------------------------------------+|
+--------------------------------------------------+

MODE 2: TEAM SERVER (Shared Server)
+--------------------------------------------------+
|  Dedicated Server / VM                           |
|                                                  |
|  Docker Compose + Reverse Proxy (Caddy/Nginx)    |
|  +--------------------------------------------+ |
|  | Same containers as local + TLS termination  | |
|  | + Authentication (OAuth2 / OIDC)            | |
|  | + Multi-user project isolation              | |
|  +--------------------------------------------+ |
+--------------------------------------------------+

MODE 3: CLOUD-NATIVE (Kubernetes)
+--------------------------------------------------+
|  Kubernetes Cluster                              |
|                                                  |
|  +--------------------------------------------+ |
|  | Namespace: codebot-system                   | |
|  |                                              | |
|  | Deployments:                                 | |
|  |   codebot-core (HPA: 2-10 replicas)         | |
|  |   codebot-web  (HPA: 2-5 replicas)          | |
|  |   codebot-worker (HPA: 3-15 replicas)       | |
|  |                                              | |
|  | StatefulSets:                                | |
|  |   postgresql (1 primary + 1 replica)         | |
|  |   redis (3-node cluster)                     | |
|  |   chroma (1 replica)                         | |
|  |                                              | |
|  | Jobs:                                        | |
|  |   agent-tasks (dynamic, one per agent run)   | |
|  |   sandbox-runners (ephemeral pods)           | |
|  |                                              | |
|  | PersistentVolumes:                           | |
|  |   git-repos (shared NFS/EFS)                 | |
|  |   object-store (S3 / GCS)                    | |
|  +--------------------------------------------+ |
+--------------------------------------------------+
```

### 11.2 Container Image Architecture

```
Base Images:
  +-- codebot-base:latest (Python 3.12 + common deps)
       |
       +-- codebot-core:latest    (Orchestration engine)
       |     + Graph engine, agent pool, pipeline manager
       |     + CLI agent adapters (Claude Code, Codex, Gemini)
       |     + Security scanner CLIs (Semgrep, Trivy, Gitleaks)
       |
       +-- codebot-worker:latest  (Agent execution worker)
       |     + Isolated agent runtime
       |     + Git + worktree management tools
       |     + Language runtimes (Node.js, Python, Go, Rust)
       |
       +-- codebot-web:latest     (Web dashboard)
             + Next.js application
             + Socket.IO client
             + Static asset serving
```

### 11.3 Networking

```
External Access:
  HTTPS:443 -> Reverse Proxy -> codebot-web (UI + API)
  WSS:443   -> Reverse Proxy -> codebot-core (WebSocket events)

Internal Communication:
  codebot-core  <-> postgres    : TCP:5432
  codebot-core  <-> redis       : TCP:6379
  codebot-core  <-> chroma      : TCP:8000
  codebot-core  <-> minio       : TCP:9000
  codebot-core  <-> sonarqube   : TCP:9090
  codebot-core  <-> ragflow     : TCP:8080
  codebot-web   <-> codebot-core: TCP:8001 (internal API)
```

---

## 12. Technology Stack Summary

### 12.1 Core Platform

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Language** | Python | 3.12+ | Orchestration engine, agents, CLI |
| **Language** | TypeScript | 5.x | Web dashboard, CLI agent integrations |
| **Web Framework** | FastAPI | 0.115+ | REST API, WebSocket, async support |
| **Web Frontend** | Refine + React Flow + Shadcn/ui | latest | Dashboard UI with agent graph visualization |
| **Agent Orchestration** | LangGraph (~24.6K stars, MIT) | latest | Stateful agent graph execution with persistence |
| **Workflow Engine** | Temporal (~18.9K stars, MIT) | latest | Durable workflow orchestration, retry, and scheduling |
| **LLM Gateway** | LiteLLM Proxy (~39.2K stars, MIT) + RouteLLM | v1.82+ | Unified multi-provider LLM routing and proxy |
| **MCP** | FastMCP 2.0 (~21.9K stars, Apache-2.0) | 2.0 | Model Context Protocol server framework |
| **Event Bus** | NATS + JetStream (~19.4K stars, Apache-2.0) | latest | Inter-agent messaging, event streaming |
| **Task Queue** | Taskiq (~2K stars, MIT) with NATS broker | latest | Async task scheduling and execution |
| **CLI Framework** | Click | 8.x | CodeBot CLI interface |
| **Code Editor** | Monaco Editor + xterm.js | latest | In-browser code editing and terminal |
| **Real-time** | Socket.IO + Yjs | latest | WebSocket communication and collaborative editing |

### 12.2 Data Stores

| Store | Technology | Purpose |
|---|---|---|
| **Relational DB** | PostgreSQL 16+ | Projects, runs, tasks, findings, usage logs |
| **Cache** | Redis 7+ | State cache, rate limits, session state (note: Redis remains for caching; event bus moved to NATS) |
| **Vector Store (Dev)** | LanceDB | Embedded vector database for development (replaces ChromaDB, deprecated in favor of LanceDB for embedded use) |
| **Vector Store (Prod)** | Qdrant | Managed/self-hosted vector database for production |
| **Object Store** | MinIO (local) / S3 (cloud) | Artifacts, reports, build outputs |
| **Knowledge Graph** | Cognee | Architecture decisions, dependency graphs |
| **Memory** | Letta (MemGPT) | Agent memory hierarchy, learnings, decisions |

### 12.3 LLM Providers

| Provider | Models | SDK / Integration |
|---|---|---|
| **Anthropic** | Claude Opus, Sonnet 4, Haiku 3.5 | Anthropic Python SDK, Claude Agent SDK |
| **OpenAI** | GPT-4.1, o3, o4-mini | OpenAI Python SDK |
| **Google** | Gemini 2.5 Pro, Gemini 2.5 Flash | Google GenAI Python SDK |

### 12.4 CLI Agents (Mandatory Integrations)

CLI agents are mandatory external integrations that CodeBot orchestrates for
code generation tasks. These are third-party tools that must be installed and
configured separately.

| Agent | Integration | Sandbox |
|---|---|---|
| **Claude Code** | Claude Agent SDK (direct) | Git worktree isolation |
| **OpenAI Codex CLI** | Subprocess + output parsing | Git worktree + `--full-auto` mode |
| **Gemini CLI** | Subprocess + output parsing | Git worktree isolation |

### 12.5 Built-in Platform Features

The following capabilities are built-in features of the CodeBot platform, not
external integrations or dependencies. Some were inspired by open-source research
projects as design references.

| Feature | Description | Inspiration |
|---|---|---|
| **Hierarchical context management** | Three-tier (L0/L1/L2) context loading with filesystem paradigm | OpenViking patterns (research inspiration) |
| **Episodic memory** | Cross-session and cross-project agent learning with lifecycle hooks, semantic compression, and progressive disclosure | claude-mem patterns (research inspiration) |
| **Sandbox execution** | Containerized per-agent execution environments with gVisor/Kata isolation | Built-in |
| **Live preview** | Hot-reload for web apps, VNC for desktop apps, streamed to dashboard | Built-in |

### 12.6 Security and Quality Tools

| Category | Tool | Integration |
|---|---|---|
| **SAST** | Semgrep | CLI subprocess, rule packs |
| **SAST + Quality** | SonarQube Community | REST API, quality profiles |
| **SAST (GitHub)** | CodeQL | GitHub Actions integration |
| **DAST** | OWASP ZAP | CLI subprocess, API scanning |
| **Python Security** | Bandit | CLI subprocess, AST-based Python security linter |
| **Container Scanning** | Trivy | CLI subprocess |
| **SBOM + Vulnerability** | Syft + Grype | SBOM generation (Syft) and vulnerability matching (Grype) |
| **Secrets Detection** | Gitleaks | CLI subprocess + pre-commit hook |
| **License Compliance** | ORT (OSS Review Toolkit) | CLI subprocess, dependency analysis and license orchestration |
| **IaC Security** | KICS | CLI subprocess |
| **Code Formatting** | Prettier, Black, Ruff | CLI subprocess |
| **Linting** | ESLint, Ruff, Clippy | CLI subprocess |

### 12.7 Context and RAG

| Component | Technology | Purpose |
|---|---|---|
| **RAG Pipeline** | LlamaIndex (~47.7K stars, MIT) | Document chunking, retrieval, re-ranking, and RAG orchestration |
| **Code Parsing** | Tree-sitter (v0.26+) + ast-grep (v0.42+) | AST-aware code chunking, structural search, and semantic code analysis |
| **Embeddings** | OpenAI `text-embedding-3-large` / Cohere | Code and document embedding generation |
| **MCP Protocol** | FastMCP 2.0 (~21.9K stars, Apache-2.0) | Standardized tool interface for agents |

### 12.8 Infrastructure

| Component | Technology | Purpose |
|---|---|---|
| **Containerization** | Docker / Podman | Service isolation, reproducible environments |
| **Orchestration** | Docker Compose (local) / K8s (cloud) | Multi-container management |
| **IaC** | Pulumi + OpenTofu | Infrastructure as Code (Pulumi for programmatic, OpenTofu for Terraform-compatible) |
| **CI/CD Pipeline** | Dagger | Containerized CI/CD pipeline engine |
| **Configuration Mgmt** | Ansible | Server provisioning and configuration management |
| **Version Control** | Git 2.40+ | Source management, worktree isolation |
| **Reverse Proxy** | Caddy / Nginx | TLS termination, routing |
| **CI/CD** | GitHub Actions / GitLab CI | Pipeline automation |
| **Observability** | SigNoz / Prometheus + Grafana + Jaeger | Unified metrics, traces, and dashboards |
| **LLM Observability** | Langfuse | LLM-specific tracing, prompt management, and evaluation |
| **Tracing** | OpenTelemetry | Distributed tracing instrumentation |
| **Logging** | Structured JSON + Loki | Centralized log aggregation |
| **Sandbox** | E2B / Nsjail + code-server | Cloud sandboxes (E2B) and local sandbox isolation (Nsjail) with in-browser IDE (code-server) |

### 12.9 Testing

| Category | Technology | Purpose |
|---|---|---|
| **Unit Testing** | pytest v9+ (Python), Vitest v4+ (TS) | Component-level testing |
| **Integration Testing** | pytest + Testcontainers | Service integration testing with real dependencies |
| **E2E Testing** | Playwright v1.58+ | Browser-based end-to-end testing |
| **Accessibility Testing** | axe-core | Automated accessibility compliance checking |
| **Contract Testing** | Pact | Consumer-driven contract testing for API boundaries |
| **UI Component Testing** | Storybook + Chromatic | Visual regression and isolated UI component testing |
| **Smoke Testing** | Custom test suites (Playwright + pytest) | Quick post-deploy sanity checks for critical paths |
| **Regression Testing** | pytest + Playwright (tagged suites) | Verifying previously fixed bugs remain fixed |
| **Mutation Testing** | mutmut (Python), Stryker (TS/JS) | Evaluating test suite effectiveness by injecting faults |
| **Load Testing** | k6 | Performance and load benchmarking |
| **Coverage** | coverage.py, c8 | Code coverage measurement |

### 12.10 Plugins, Templates, and Utilities

| Category | Technology | Purpose |
|---|---|---|
| **Plugin System** | pluggy | Extensible plugin architecture for custom agent behaviors |
| **Project Templates** | Copier | Template-based project scaffolding and generation |
| **Notifications** | Apprise | Unified notification delivery (Slack, email, Discord, etc.) |
| **Diagrams** | Mermaid + D2 | Architecture and flow diagram generation from code |

---

## 13. Cross-Cutting Concerns

### 13.1 Logging

```
Logging Architecture:

  Agent / Service
       |
       v
  Structured JSON Logger (structlog / pino)
       |
       +-- Fields:
       |     timestamp: ISO 8601
       |     level: DEBUG | INFO | WARN | ERROR | FATAL
       |     service: str (e.g., "graph-engine", "agent-backend-dev")
       |     run_id: UUID
       |     task_id: UUID
       |     agent_role: str
       |     correlation_id: UUID
       |     message: str
       |     context: dict (additional structured data)
       |     duration_ms: int (for timed operations)
       |
       v
  Log Aggregator (Loki / ELK)
       |
       v
  Dashboard (Grafana / Kibana)
```

**Log Levels by Environment:**

| Environment | Default Level | Verbose Agents |
|---|---|---|
| Development | DEBUG | All agents |
| Staging | INFO | Orchestrator, Debugger |
| Production | WARN | None (INFO on request) |

**Agent Conversation Logging:**

All LLM interactions are logged to the object store for debugging and audit:
- Full prompt (system + user messages)
- Full response (assistant message + tool calls)
- Token counts (input, output)
- Model used
- Latency
- Cost

Sensitive data (API keys, credentials) is redacted before logging using pattern-based
scrubbing.

### 13.2 Monitoring and Observability

```
Observability Stack:

  +------------------+     +------------------+     +------------------+
  |   Metrics        |     |   Traces         |     |   Logs           |
  |   (Prometheus)   |     |   (OpenTelemetry)|     |   (Loki)         |
  +--------+---------+     +--------+---------+     +--------+---------+
           |                        |                        |
           +------------------------+------------------------+
                                    |
                                    v
                          +------------------+
                          |   Grafana        |
                          |   Dashboards     |
                          +------------------+
```

**Key Metrics:**

| Category | Metric | Type | Alert Threshold |
|---|---|---|---|
| **Pipeline** | `pipeline.duration_seconds` | Histogram | > 1800s (30 min) |
| **Pipeline** | `pipeline.success_rate` | Gauge | < 70% (rolling 24h) |
| **Agent** | `agent.execution_seconds` | Histogram | > 300s per agent |
| **Agent** | `agent.failure_rate` | Counter | > 3 consecutive failures |
| **LLM** | `llm.request_duration_seconds` | Histogram | > 60s |
| **LLM** | `llm.tokens_total` | Counter | Budget threshold |
| **LLM** | `llm.cost_usd_total` | Counter | Budget threshold |
| **LLM** | `llm.rate_limit_hits` | Counter | > 10/minute |
| **Security** | `scan.findings_total` | Gauge | Any CRITICAL |
| **System** | `system.cpu_usage_percent` | Gauge | > 85% |
| **System** | `system.memory_usage_percent` | Gauge | > 90% |
| **System** | `system.disk_usage_percent` | Gauge | > 85% |
| **Queue** | `queue.depth` | Gauge | > 50 pending tasks |
| **Queue** | `queue.processing_time_seconds` | Histogram | > 600s |

**Distributed Tracing:**

OpenTelemetry traces follow a request from PRD submission through the entire
pipeline, creating spans for:
- Each pipeline phase
- Each agent execution
- Each LLM API call
- Each security scan
- Each git operation
- Each context retrieval

Trace context is propagated through the Message Envelope `metadata.trace_context`
field, ensuring cross-agent trace continuity.

### 13.3 Error Handling

```
Error Handling Strategy:

  +--------------------+
  | Error Occurs       |
  +--------+-----------+
           |
           v
  +--------------------+
  | Classify Error     |
  +--------+-----------+
           |
  +--------+--------+--------+--------+
  |        |        |        |        |
  v        v        v        v        v
TRANSIENT RATE     MODEL    LOGIC   SYSTEM
(network, LIMITED  ERROR    ERROR   ERROR
 timeout)  |        |        |        |
  |        |        |        |        |
  v        v        v        v        v
RETRY    BACKOFF  FALLBACK ESCALATE ALERT
(exp.    +QUEUE   TO ALT   TO       +HALT
backoff) |        MODEL    HUMAN    |
3 tries) |        |        |        |
  |        |        |        |        |
  +--------+--------+--------+--------+
           |
           v
  +--------------------+
  | If all retries     |
  | exhausted:         |
  | 1. Log full context|
  | 2. Checkpoint state|
  | 3. Escalate        |
  | 4. Mark task FAILED|
  +--------------------+
```

**Error Categories:**

| Category | Examples | Strategy | Max Retries |
|---|---|---|---|
| Transient | Network timeout, connection reset | Exponential backoff retry | 3 |
| Rate Limited | LLM provider 429 | Backoff + queue, switch provider | 5 |
| Model Error | Invalid response, hallucination | Retry with different prompt/model | 2 |
| Logic Error | Test failure, build error | Route to Debugger agent | Via DebugFixLoop |
| System Error | OOM, disk full, Docker failure | Alert, halt pipeline, await human | 0 |
| Auth Error | Expired API key, invalid credentials | Alert user, pause pipeline | 0 |

**Circuit Breaker:**

Each LLM provider has a circuit breaker that opens after 5 consecutive failures
within a 60-second window. While open, all requests are routed to the fallback
provider. The circuit half-opens after 30 seconds, allowing a single probe request
to test recovery.

### 13.4 Configuration Management

```
Configuration Hierarchy (highest priority first):

  1. CLI flags / Environment variables
  2. Project-level .codebot/config.yaml
  3. User-level ~/.codebot/config.yaml
  4. System defaults (built-in)
```

**Configuration Schema:**

```yaml
# .codebot/config.yaml
project:
  name: "my-app"
  description: "E-commerce platform"

llm:
  providers:
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
      default_model: "claude-sonnet-4-20250514"
      max_tokens: 4096
    openai:
      api_key: "${OPENAI_API_KEY}"
      default_model: "gpt-4.1"
    google:
      api_key: "${GOOGLE_API_KEY}"
      default_model: "gemini-2.5-pro"

  routing:
    architecture: "claude-opus-4-20250514"
    code_generation: "gpt-4.1"
    research: "gemini-2.5-pro"
    simple_tasks: "claude-haiku-3-5"

  budgets:
    per_agent_tokens: 100000
    per_phase_tokens: 500000
    per_project_tokens: 5000000
    max_cost_usd: 50.00

agents:
  cli_preference: "claude-code"  # claude-code | codex | gemini
  max_parallel: 8
  max_iterations_per_loop: 5

security:
  scanners:
    sast: ["semgrep"]
    dast: ["shannon"]
    secrets: ["gitleaks"]
    license: ["scancode", "ort"]
    container: ["trivy"]
  quality_gate:
    max_critical: 0
    max_high: 0
    min_coverage: 80

context:
  vector_store: "chroma"
  embedding_model: "text-embedding-3-large"
  l1_token_budget: 10000
  l2_token_budget: 20000

infrastructure:
  docker:
    sandbox_image: "codebot-sandbox:latest"
    sandbox_timeout: 300
    sandbox_memory: "2g"
    sandbox_cpus: 2
  git:
    worktree_base: ".worktrees"
    auto_commit: true
    merge_strategy: "rebase"
```

### 13.5 Audit Trail

Every significant action in the system is recorded in an immutable audit log.

| Event | Data Captured |
|---|---|
| PRD submitted | User ID, PRD content hash, timestamp |
| Agent started | Agent role, model used, task ID, context summary |
| LLM call made | Provider, model, token count, cost, latency, prompt hash |
| File created/modified | File path, content hash, agent ID, commit SHA |
| Security finding | Finding details, scanner, severity, affected file |
| Human decision | User ID, decision type (approve/reject/override), context |
| Pipeline state change | Old state, new state, trigger, timestamp |
| Configuration change | Changed key, old value hash, new value hash, user ID |

### 13.6 Secret Management

| Concern | Implementation |
|---|---|
| API key storage | Environment variables or encrypted `.env` file (never in config YAML) |
| Runtime injection | Docker secrets / Kubernetes secrets mounted as env vars |
| Key rotation | Support for key rotation without pipeline restart |
| Exposure prevention | Gitleaks pre-commit hook, log redaction, prompt scrubbing |
| Agent isolation | Each agent receives only the credentials it needs |

### 13.7 Extensibility

The system is designed for extensibility at multiple points.

| Extension Point | Mechanism | Examples |
|---|---|---|
| New agent roles | NodeTemplate registration | Add a "Performance Engineer" agent |
| New LLM providers | Provider adapter interface | Add Mistral, Cohere, local Ollama |
| New security scanners | Scanner adapter interface | Add Snyk, Checkmarx |
| New CLI agents | CLI Agent Adapter interface | Add Aider, Cursor Agent |
| Custom workflows | ComposedGraph definitions | Domain-specific SDLC pipelines |
| Custom tools | MCP server registration | Project-specific tooling |
| Webhook integrations | Event bus subscription | Slack notifications, Jira updates |

### 13.8 Agent Visibility

All agent activity is observable in real-time through the dashboard and CLI. The
Agent Visibility system provides transparency into what each agent is doing,
why it is doing it, and what it plans to do next.

| Visibility Feature | Mechanism | Surface |
|---|---|---|
| **Live status** | Agent state machine events streamed via Event Bus | Dashboard timeline, CLI status |
| **Reasoning trace** | Chain-of-thought logging (opt-in per agent) | Dashboard detail panel |
| **Tool invocations** | MCP tool call/result events | Dashboard activity feed |
| **Token usage** | Per-turn token counters emitted to metrics | Cost center dashboard |
| **Progress indicators** | Stage completion percentage (S0-S10 progress) | Dashboard overview, CLI progress bar |
| **Decision audit** | Key decisions logged with rationale | Audit trail, dashboard |
| **Error context** | Failure context with stack traces and agent state | Dashboard alerts, CLI logs |

```
Agent Visibility Architecture:

  Agent Instance
       |
       +-- Emits: status_change, tool_call, llm_turn, decision, error
       |
       v
  Event Bus (Redis PubSub)
       |
       +----> WebSocket (Socket.IO) ----> Dashboard (real-time)
       +----> CLI Subscriber -----------> Terminal (polling/streaming)
       +----> Log Aggregator -----------> Audit Store (persistent)
       +----> Metrics Collector --------> Prometheus -> Grafana
```

### 13.9 Interactive User Input

The system supports interactive user input at configurable points in the pipeline.
Users can provide guidance, make decisions, and steer agent behavior without
halting the entire pipeline.

| Input Type | Trigger | Timeout Behavior | Use Case |
|---|---|---|---|
| **Approval Gate** | Stage transition (e.g., S3->S4, S6->S7) | Auto-approve after configurable timeout | Architecture sign-off, QA gate approval |
| **Feedback Request** | Agent requests clarification | Agent proceeds with best guess after timeout | Ambiguous requirements, design choices |
| **Override** | User initiates via dashboard/CLI | N/A (user-initiated) | Change agent parameters, skip stages, force retry |
| **Escalation** | Agent exhausts retries or detects blocking issue | Pipeline pauses until resolved | Unresolvable merge conflict, missing credentials |
| **Preference Selection** | Agent presents multiple options | First option selected after timeout | Technology choice, design alternative, naming conventions |

```
Interactive Input Flow:

  Agent encounters decision point
       |
       v
  Interaction Node created (type: APPROVAL | INPUT | FEEDBACK | ESCALATION)
       |
       v
  Notification sent to user (WebSocket + email/Slack optional)
       |
       +-- User responds within timeout --> Input captured, agent resumes
       |
       +-- Timeout expires --> Default action taken (configurable per gate)
       |
       v
  Decision logged to audit trail with source (user | timeout_default)
```

---

## 14. Agent Lifecycle Management

### 14.1 Agent States

Each agent instance follows a deterministic state machine throughout its lifecycle.

```
Agent State Machine:

  IDLE ──> INITIALIZING ──> RUNNING ──> COMPLETED
                              │              │
                              │              └──> TERMINATED
                              │
                              └──> WAITING ──> RUNNING (resumed)
                              │
                              └──> FAILED ──> TERMINATED
```

| State | Description |
|---|---|
| IDLE | Agent registered but not yet assigned a task |
| INITIALIZING | Loading context, provisioning worktree, preparing tools |
| RUNNING | Actively executing task (LLM calls, tool use, code generation) |
| WAITING | Blocked on external dependency (human input, upstream agent, resource) |
| COMPLETED | Task finished successfully, output available for downstream consumers |
| FAILED | Task terminated with error after exhausting retries |
| TERMINATED | Agent resources released, worktree cleaned up, final state persisted |

### 14.2 Lifecycle Phases

```
Agent Lifecycle:

  1. SPAWN
     - Agent Pool Manager creates agent instance from NodeTemplate
     - Assigns unique instance ID
     - Registers in Agent Registry

  2. INITIALIZE
     - Context Adapter assembles L0 + L1 context payload
     - Worktree Manager provisions isolated git worktree (if coding agent)
     - Tool registry configured with allowed tools
     - System prompt assembled from role template

  3. EXECUTE
     - Agent enters RUNNING state
     - LLM calls executed via Multi-LLM Abstraction Layer
     - Tool calls processed through MCP interface
     - Output streamed to Event Bus for real-time observation

  4. CHECKPOINT
     - State snapshot persisted to PostgreSQL after each significant action
     - Intermediate outputs stored in Object Store
     - Enables resume-from-checkpoint on failure or system restart

  5. TERMINATE
     - Output artifacts finalized and propagated to downstream edges
     - Worktree merged or cleaned up
     - Resources released (LLM sessions, tool connections)
     - Final metrics emitted (duration, tokens, cost)
     - Agent instance deregistered from Agent Registry
```

### 14.3 Health Checks

Agent health is monitored continuously by the Agent Pool Manager.

| Check | Interval | Action on Failure |
|---|---|---|
| Heartbeat | Every 30s | Mark agent as unresponsive after 3 missed beats |
| Progress | Every 60s | Detect stalled agents (no output for 60s) |
| Resource usage | Every 30s | Kill agent exceeding memory/CPU limits |
| Token budget | Per LLM call | Pause agent when approaching budget limit |

### 14.4 Graceful Degradation

On repeated failures, the system applies progressive degradation:

1. **First failure**: Retry with exponential backoff
2. **Second failure**: Switch to fallback LLM model
3. **Third failure**: Simplify task (reduce scope, request partial output)
4. **Fourth failure**: Pause agent, notify orchestrator for re-planning
5. **Fifth failure**: Mark task as FAILED, escalate to human, preserve all state for manual intervention

---

## 15. Error Handling Architecture

### 15.1 Error Taxonomy

All errors in CodeBot are classified into four categories with distinct handling strategies.

| Category | Description | Strategy | Example |
|---|---|---|---|
| **Transient** | Temporary failures likely to resolve on retry | Retry with exponential backoff (max 3 attempts) | Network timeout, API 503, connection reset |
| **Recoverable** | Errors that the system can auto-fix | Apply automated remediation, then retry | Malformed LLM output (re-prompt), minor merge conflict (auto-resolve) |
| **Blocking** | Errors requiring attention but not fatal | Pause pipeline + notify user/orchestrator | Security gate failure, missing API credentials, human approval required |
| **Fatal** | Unrecoverable errors requiring full stop | Stop pipeline + preserve full state for diagnosis | Data corruption, critical system failure, budget exhausted |

### 15.2 Dead Letter Queue

Failed messages that exhaust all retry attempts are routed to a Dead Letter Queue (DLQ) for post-mortem analysis.

```
Dead Letter Queue Flow:

  Message fails processing
       |
       v
  Retry policy exhausted? ──NO──> Re-enqueue with backoff
       |
      YES
       |
       v
  +-----------------------------+
  | Dead Letter Queue (Redis)   |
  |                             |
  | - Original message payload  |
  | - Error details + stack     |
  | - Retry history             |
  | - Source/target agent IDs   |
  | - Timestamp of final fail   |
  +-----------------------------+
       |
       v
  DLQ Monitor alerts operator
  Operator can: replay, discard, or manually resolve
```

### 15.3 Circuit Breaker Pattern

Each LLM provider has a circuit breaker to prevent cascading failures.

```
Circuit Breaker States:

  CLOSED (normal) ──> OPEN (after 5 consecutive failures)
       ^                    |
       |                    v
       +──── HALF-OPEN (after 30s cooldown, allow 1 probe request)
                    |
              probe succeeds? ──YES──> CLOSED
                    |
                   NO ──> OPEN (reset cooldown timer)
```

| Parameter | Value |
|---|---|
| Failure threshold | 5 consecutive failures |
| Cooldown window | 30 seconds |
| Probe request count | 1 |
| Scope | Per LLM provider |
| Fallback | Route to next provider in fallback chain |

### 15.4 Error Propagation Through the Agent Graph

```
Error Propagation Rules:

  1. CONTAINED errors (within a single agent):
     - Agent retries internally per its retry_policy
     - If resolved, downstream agents are unaffected

  2. PROPAGATED errors (agent fails completely):
     - Node marked as FAILED in the graph
     - Downstream dependent nodes marked as BLOCKED
     - Orchestrator evaluates: can the pipeline continue on alternate paths?
       YES -> Skip blocked branch, continue on other branches
       NO  -> Pause pipeline, escalate

  3. CASCADING errors (systemic failure):
     - Circuit breaker opens for affected provider
     - All agents using that provider are rerouted to fallback
     - If no fallback available, affected agents pause and alert

  4. POISON PILL detection:
     - If the same task fails across 3 different agents/models,
       mark the task as potentially malformed
     - Escalate to human with full diagnostic context
```

---

## 16. Communication Protocol

### 16.1 Standardized Message Format

All inter-agent messages conform to a standardized envelope format.

```
StandardMessage:
  id: UUID                        # Unique message identifier
  version: "1.0"                  # Protocol version
  type: MessageType               # TASK_HANDOFF | REVIEW_REQUEST | REVIEW_RESULT |
                                  # FIX_REQUEST | TEST_RESULT | CONTEXT_REQUEST |
                                  # CONTEXT_RESPONSE | ESCALATION | STATUS_UPDATE
  source: str                     # Source agent role + instance ID
  target: str                     # Target agent role (or "*" for broadcast)
  correlation_id: UUID            # Links related messages in the same task chain
  priority: int                   # 0 (lowest) to 9 (highest, reserved for ESCALATION)
  payload: dict                   # Type-specific structured payload
  metadata:
    run_id: UUID                  # Pipeline run context
    trace_context: dict           # OpenTelemetry trace/span IDs
    timestamp: datetime           # ISO 8601 creation timestamp
    ttl: int                      # Time-to-live in seconds (0 = no expiry)
    idempotency_key: str          # For exactly-once processing
    content_hash: str             # SHA-256 of payload for integrity verification
```

### 16.2 Delivery Guarantees

| Guarantee | Implementation |
|---|---|
| **At-least-once delivery** | NATS JetStream with consumer acknowledgment; unacknowledged messages are re-delivered after timeout |
| **Per-pair ordering** | Messages between any specific (source, target) pair are delivered in send order via dedicated stream partitions |
| **Idempotency** | Each message carries an `idempotency_key`; receivers track processed keys to skip duplicates |
| **Durability** | NATS JetStream persists messages to disk; critical messages also written to PostgreSQL |

### 16.3 Large Message Offloading

Messages with payloads exceeding 100KB are automatically offloaded to blob storage.

```
Large Message Flow:

  Sender creates message with large payload (>100KB)
       |
       v
  Message Adapter detects oversized payload
       |
       v
  Payload uploaded to Object Store (MinIO / S3)
       |
       v
  Message envelope updated:
    payload: { "$ref": "s3://codebot-messages/<run_id>/<message_id>.json" }
       |
       v
  Receiver retrieves payload from Object Store on consumption
```

---

## 17. Platform Observability

### 17.1 Observability Stack

| Pillar | Technology | Purpose |
|---|---|---|
| **Metrics** | Prometheus + Grafana | Time-series metrics collection, dashboarding, and alerting rules |
| **Logs** | Structured JSON (structlog/pino) + Loki | Centralized, queryable log aggregation with correlation IDs |
| **Traces** | OpenTelemetry -> Jaeger | Distributed tracing across agents, phases, and LLM calls |
| **Events** | Event Bus (NATS JetStream) + WebSocket (Socket.IO) | Real-time pipeline events streamed to dashboard and CLI |
| **Alerts** | Alertmanager (Prometheus) | Threshold-based alerts routed to Slack, email, or PagerDuty |

### 17.2 Observability Integration

```
Observability Data Flow:

  Agents / Services / Engine
       |          |          |
       v          v          v
  [Metrics]  [Traces]    [Logs]
  Prometheus  OTel SDK   structlog
       |          |          |
       v          v          v
  Prometheus  Jaeger     Loki
  Server     Collector   Stack
       |          |          |
       +----------+----------+
                  |
                  v
            +-----------+
            |  Grafana  |
            | Unified   |
            | Dashboard |
            +-----------+
                  |
                  v
           Alertmanager
           (thresholds)
                  |
           +------+------+
           |      |      |
           v      v      v
         Slack  Email  PagerDuty
```

### 17.3 Key Dashboards

| Dashboard | Content |
|---|---|
| Pipeline Overview | Active runs, phase progress, agent status, quality gate results |
| Agent Performance | Execution duration, success rate, token usage per agent role |
| LLM Analytics | Provider latency, cost breakdown, model usage distribution, error rates |
| Security Posture | Findings by severity, scanner coverage, gate pass/fail trends |
| System Health | CPU, memory, disk, container count, queue depth, Redis metrics |
| Cost Center | Running cost per project, per pipeline, per agent, budget utilization |

---

## 18. Data Retention Architecture

### 18.1 Retention Policies

| Data Category | Retention Period | Action After Expiry |
|---|---|---|
| Agent execution logs | 90 days | Auto-purge from PostgreSQL and Object Store |
| LLM request/response logs | 30 days | Auto-purge from Object Store |
| Event bus messages | 7 days | Auto-purge from NATS JetStream |
| Security scan results | 1 year | Auto-archive to cold storage (S3 Glacier / equivalent) |
| Build artifacts | 30 days after project completion | Auto-purge from Object Store |
| Project configuration | Indefinite | Retained as long as project exists |
| Audit trail | Indefinite | Immutable, append-only storage |
| Vector embeddings | Lifetime of project | Purged on project deletion |

### 18.2 Retention Enforcement

```
Retention Enforcement Pipeline:

  Daily cron job (02:00 UTC)
       |
       v
  For each data category:
    1. Query records older than retention threshold
    2. For ARCHIVE policies: move to cold storage
    3. For PURGE policies: delete from primary store
    4. Emit metrics: purged_records_count, freed_storage_bytes
    5. Log actions to audit trail
       |
       v
  Retention report published to Event Bus
```

---

## 19. Authentication Architecture

### 19.1 Authentication Methods

| Method | Use Case | Algorithm |
|---|---|---|
| **JWT tokens** | Interactive web dashboard and API sessions | RS256 (asymmetric) |
| **API Keys** | CI/CD pipelines and CLI programmatic access | HMAC-SHA256 |

### 19.2 JWT Token Flow

```
JWT Authentication Flow:

  User (browser / CLI)
       |
       v
  POST /auth/login  { email, password }
       |
       v
  Auth Service validates credentials
       |
       v
  Issue token pair:
    - Access token  (JWT RS256, 15 min TTL)
    - Refresh token (opaque, 7 day TTL, stored in HttpOnly cookie)
       |
       v
  Refresh token rotation:
    - Each refresh request issues a NEW refresh token
    - Previous refresh token is invalidated
    - Detects token reuse (potential theft) and revokes entire session
```

### 19.3 API Key Authentication

```
API Key Flow:

  CI/CD / CLI client
       |
       v
  Request with header: Authorization: Bearer <api_key>
       |
       v
  Auth middleware:
    1. Extract key prefix (first 8 chars) for lookup
    2. Retrieve hashed key from database
    3. Verify HMAC-SHA256 signature
    4. Check key scopes and expiry
    5. Rate limit per key (configurable)
```

### 19.4 Role-Based Access Control (RBAC)

| Role | Permissions |
|---|---|
| **admin** | Full system access: create/delete projects, manage users, configure agents, view audit logs, modify system settings |
| **user** | Create and manage own projects, start pipelines, review output, configure project-level settings |
| **viewer** | Read-only access to projects they are invited to, view pipeline status, download artifacts |

### 19.5 Multi-Factor Authentication (MFA)

- **Method**: TOTP (Time-based One-Time Password, RFC 6238)
- **Scope**: Optional for all accounts, mandatory for `admin` role accounts
- **Implementation**: Standard TOTP with 30-second window, SHA-1 algorithm, 6-digit codes
- **Recovery**: One-time backup codes generated at MFA enrollment

### 19.6 Auth Audit Logging

All authentication events are logged to the immutable audit trail:

| Event | Data Captured |
|---|---|
| Login success | User ID, IP address, user agent, MFA used (yes/no) |
| Login failure | Attempted user ID, IP address, failure reason |
| Token refresh | User ID, old token ID, new token ID |
| Token revocation | User ID, token ID, revocation reason |
| API key created | User ID, key prefix, scopes, expiry |
| API key revoked | User ID, key prefix, revocation reason |
| Role change | Admin user ID, target user ID, old role, new role |
| MFA enrollment | User ID, MFA method |

---

## 20. Agent Safety Guardrails

### 20.1 Sandboxed Execution

Agents that create executable artifacts (Skill Creator, Hook Creator, Tool Creator) run in isolated sandbox environments.

| Guardrail | Implementation |
|---|---|
| Execution isolation | Docker containers with seccomp + AppArmor profiles |
| Network restriction | No outbound network access from sandbox |
| Filesystem isolation | Ephemeral tmpfs, no access to host filesystem outside worktree |
| Resource limits | CPU: 2 cores, Memory: 2GB, Execution timeout: 300s |

### 20.2 Artifact Review Pipeline

All artifacts created by meta-agents (agents that generate new skills, hooks, or tools) must pass a mandatory review before activation.

```
Artifact Review Pipeline:

  Meta-Agent creates artifact (skill / hook / tool)
       |
       v
  Code Reviewer Agent (automated review)
    - Code quality check
    - Adherence to coding standards
    - Complexity analysis
       |
       v
  Security Auditor Agent (automated security review)
    - SAST scan (Semgrep)
    - Secrets detection (Gitleaks)
    - Dependency audit
    - Permission analysis
       |
       v
  Both PASS? ──NO──> Artifact REJECTED, feedback sent to creator
       |
      YES
       |
       v
  Artifact activated and registered in tool/skill/hook registry
```

### 20.3 Rate Limiting

| Limit | Value | Scope |
|---|---|---|
| Max new artifacts per pipeline run | 5 | Per pipeline execution |
| Max tool registrations per hour | 10 | System-wide |
| Max concurrent sandbox executions | 4 | System-wide |

### 20.4 Capability Boundaries

All agents operate within strict capability boundaries:

| Boundary | Rule |
|---|---|
| **No credential access** | Agents cannot read, modify, or exfiltrate API keys, passwords, or tokens outside their assigned scope |
| **No prompt modification** | Agents cannot modify the system prompts or role instructions of other agents |
| **No security bypass** | Agents cannot disable security scanners, skip quality gates, or modify finding severity |
| **No self-modification** | Agents cannot modify their own configuration, retry policies, or resource limits |
| **No escalation of privilege** | Agents cannot grant themselves additional tools, context tiers, or permissions |

---

## 21. Prompt Engineering Standards

### 21.1 Prompt Storage and Versioning

All agent prompts are stored as versioned templates in the project repository.

```
templates/prompts/
  ├── v1/
  │   ├── orchestrator.md
  │   ├── planner.md
  │   ├── researcher.md
  │   ├── architect.md
  │   ├── frontend-dev.md
  │   ├── backend-dev.md
  │   ├── middleware-dev.md
  │   ├── infra-engineer.md
  │   ├── security-auditor.md
  │   ├── code-reviewer.md
  │   ├── tester.md
  │   ├── debugger.md
  │   ├── doc-writer.md
  │   └── project-manager.md
  └── v2/
      └── ... (new versions)
```

- Prompts are version-controlled alongside application code
- Prompt changes require review (same as code changes)
- No hardcoded prompts in application source code
- Prompts loaded at runtime from template files with variable interpolation

### 21.2 Standard Prompt Structure

Every agent prompt follows a five-section structure:

```
+-------------------------------------------------------+
|  1. ROLE                                               |
|     Who the agent is, its expertise, and perspective   |
+-------------------------------------------------------+
|  2. CONTEXT                                            |
|     Project information, current phase, relevant       |
|     artifacts from upstream agents (injected by        |
|     Context Adapter from L0 + L1 tiers)                |
+-------------------------------------------------------+
|  3. INSTRUCTIONS                                       |
|     Specific task to perform, step-by-step guidance,   |
|     expected workflow and methodology                  |
+-------------------------------------------------------+
|  4. CONSTRAINTS                                        |
|     Boundaries: what NOT to do, quality standards,     |
|     security requirements, technology restrictions     |
+-------------------------------------------------------+
|  5. OUTPUT FORMAT                                      |
|     Expected response structure, required fields,      |
|     file format, JSON schema for structured output     |
+-------------------------------------------------------+
```

### 21.3 Token Budget

| Component | Budget |
|---|---|
| L0 context + system prompt | <= 4K tokens |
| L1 on-demand context | <= 10K tokens |
| L2 deep retrieval | <= 20K tokens |
| Total prompt (max) | Model context window minus reserved output tokens |

### 21.4 Prompt Governance Rules

| Rule | Description |
|---|---|
| No hardcoded prompts | All prompts must reside in `templates/prompts/`, never inline in source code |
| Variable interpolation | Use `{{variable}}` syntax for dynamic content injection |
| Version pinning | Agent configuration references a specific prompt version (e.g., `v1/backend-dev.md`) |
| A/B testing support | Multiple prompt versions can run concurrently with metric comparison |
| Prompt review | Prompt changes go through the same review process as code changes |

---

## Appendix A: Architecture Decision Records

### ADR-001: Graph-Centric Multi-Agent Architecture

**Status:** Accepted
**Context:** Need to orchestrate 15+ specialized agents with complex dependencies.
**Decision:** Adopt graph-centric model with DAG-based execution, implemented via
LangGraph (primary engine) + Temporal (durable workflows). MASFactory patterns
remain as architectural inspiration.
**Rationale:** LangGraph provides stateful, cyclical agent graph execution with
built-in persistence and human-in-the-loop support. Temporal adds durable workflow
guarantees with automatic retry and scheduling. Provides explicit dependency
modeling, parallel execution, reusable patterns, and formal scheduling guarantees
(topological sort). Alternatives considered: sequential pipeline (too rigid),
blackboard architecture (hard to reason about), market-based (unpredictable scheduling).

### ADR-002: Multi-LLM with Intelligent Routing

**Status:** Accepted
**Context:** Different LLMs excel at different tasks. Single-provider lock-in is a risk.
**Decision:** Implement a provider-agnostic abstraction with task-based routing.
**Rationale:** Enables best-model-for-task selection, cost optimization, and
provider fault tolerance. Adds complexity but provides significant quality and
reliability benefits.

### ADR-003: Git Worktree Isolation for Parallel Coding

**Status:** Accepted
**Context:** Multiple coding agents need to work on the same codebase simultaneously.
**Decision:** Each coding agent operates in an isolated git worktree on its own branch.
**Rationale:** Prevents merge conflicts during parallel execution. Worktrees share
the same git object database, minimizing disk overhead. Merge conflicts are deferred
to a controlled merge phase. Inspired by Superset's approach.

### ADR-004: Three-Tier Context Management

**Status:** Accepted
**Context:** LLM context windows are limited. Loading entire codebases is wasteful.
**Decision:** Implement L0/L1/L2 tiered context with filesystem paradigm.
**Rationale:** Minimizes token usage while ensuring agents have sufficient context.
L0 is always available (cheap), L1 is loaded on-demand (moderate cost), L2 is
deferred to agent-initiated retrieval (expensive but comprehensive). CodeBot's
built-in hierarchical context system was inspired by OpenViking patterns as
research inspiration, not as a direct integration or dependency.

### ADR-005: NATS + JetStream as Event Bus (Redis for Caching)

**Status:** Accepted (Updated)
**Context:** Need low-latency inter-agent communication and real-time event streaming.
**Decision:** Use NATS + JetStream (~19.4K stars, Apache-2.0) for event bus, messaging,
and streaming. Redis remains for caching, session state, and rate limiting.
**Rationale:** NATS provides sub-millisecond latency with JetStream adding persistence,
exactly-once delivery, and replay capabilities superior to Redis Streams. NATS
supports multiple messaging patterns (pub/sub, request/reply, queue groups) and
scales horizontally. Redis is retained for caching where its data structures
(sorted sets, hashes) excel. For persistence guarantees, critical state is also
written to PostgreSQL.

---

## Appendix B: Glossary

| Term | Definition |
|---|---|
| **Agent** | An autonomous LLM-powered worker with a specific role, tools, and context |
| **Agent Graph** | Directed computation graph where nodes are agents and edges are dependencies |
| **Agent Visibility** | Real-time observability into agent status, reasoning, tool use, and decisions |
| **Brainstormer** | Agent that explores ideas and possibilities during the Discovery phase (S1) |
| **CLI Agent** | Terminal-based coding agent (Claude Code, Codex CLI, Gemini CLI) |
| **ComposedGraph** | Reusable pre-built workflow pattern that can be parameterized and embedded |
| **Context Adapter** | Protocol layer component that assembles context payloads for agents |
| **Context Tier** | Hierarchical context loading strategy: L0 (always), L1 (on-demand), L2 (deep) |
| **Control Flow** | Orchestrator-driven signals for phase transitions and error handling |
| **DAST** | Dynamic Application Security Testing (testing running applications) |
| **Edge** | Connection between graph nodes encoding dependency or message channel |
| **ExperimentLoop** | Autonomous optimization loop with keep/discard semantics: hypothesize → apply to branch → measure → keep if improved, discard otherwise. Inspired by Karpathy's autoresearch |
| **ExperimentLoopNode** | Graph node type extending LoopNode with experiment tracking, metric comparison, and git branch management for keep/discard decisions |
| **Fix Loop** | Iterative debug-fix-test cycle (implemented as an ExperimentLoopNode in the graph with test_pass_rate as metric) |
| **Improve Mode** | Project type for autonomous codebase optimization via ExperimentLoop within a time/token budget |
| **Graph Skeleton** | Core DAG data structure with Node and Edge primitives |
| **MCP** | Model Context Protocol -- standardized interface for agent tools |
| **Message Adapter** | Protocol layer component that normalizes inter-agent messages |
| **Message Flow** | Direct agent-to-agent communication for task handoff and results |
| **Model Router** | Component that selects the optimal LLM for each task |
| **Node** | Executable unit in the agent graph (agent, subgraph, loop, switch, interaction) |
| **NodeTemplate** | Clone-able agent blueprint for instantiating agents with shared configuration |
| **Pipeline Stage** | A numbered execution phase (S0-S10) grouping related agents; stages execute sequentially, agents within a stage may run in parallel |
| **Project Manager** | Agent that tracks project progress, generates status reports, manages timelines, identifies blockers, and sends notifications |
| **Quality Gate** | Automated pass/fail checkpoint based on security, quality, and coverage metrics |
| **SAST** | Static Application Security Testing (analyzing source code without execution) |
| **SCA** | Software Composition Analysis (analyzing third-party dependencies) |
| **State Flow** | Shared mutable state propagated through the graph |
| **Vibe Graphing** | Natural language to workflow graph compilation (inspired by MASFactory concepts, implemented via LangGraph) |
| **Worktree** | Git worktree providing an isolated working directory per coding agent |

---

*Document generated for CodeBot v2.5 architecture planning. Subject to revision
as the system evolves through milestones M1-M8.*
