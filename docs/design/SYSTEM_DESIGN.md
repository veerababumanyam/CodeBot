# CodeBot System Design Document

> **Version:** 2.4
> **Date:** 2026-03-18
> **Status:** Draft
> **Related:** PRD v2.3
> **Architecture:** Graph-Centric Multi-Agent System (LangGraph engine, inspired by MASFactory, arXiv:2603.06007)

---

## Table of Contents

1. [Agent Graph Engine Design](#1-agent-graph-engine-design)
2. [Agent Design (16 Agent Types)](#2-agent-design)
3. [Multi-LLM Abstraction Layer Design](#3-multi-llm-abstraction-layer-design)
4. [CLI Agent Integration Design](#4-cli-agent-integration-design)
5. [Context Management System Design](#5-context-management-system-design)
6. [Pipeline Orchestration Design](#6-pipeline-orchestration-design)
7. [Git & Worktree Management Design](#7-git--worktree-management-design)
8. [Security Pipeline Design](#8-security-pipeline-design)
9. [Test Execution Design](#9-test-execution-design)
10. [Debug & Fix Loop Design](#10-debug--fix-loop-design)
11. [Event System Design](#11-event-system-design)
12. [Data Models](#12-data-models)
13. [Error Handling Strategy](#13-error-handling-strategy)
14. [Agent Lifecycle Management](#14-agent-lifecycle-management)
15. [Communication Protocol](#15-communication-protocol)
16. [Platform Observability](#16-platform-observability)
17. [Data Retention Policy](#17-data-retention-policy)
18. [Agent Safety Guardrails](#18-agent-safety-guardrails)
19. [Authentication & Authorization](#19-authentication--authorization)

---

## 1. Agent Graph Engine Design

### 1.1 Overview

The Agent Graph Engine is the foundational runtime of CodeBot. It models the entire software
development lifecycle as a directed graph where nodes represent computational units (agents,
sub-graphs, control structures) and edges represent data/control flow between them. This
design follows MASFactory's principle that multi-agent workflows are best expressed as
composable, reusable graph structures.

### 1.2 Core Data Structures

```
+------------------------------------------------------------------+
|                        DirectedGraph                             |
|------------------------------------------------------------------|
| - id: str                                                        |
| - name: str                                                      |
| - nodes: Dict[str, Node]                                         |
| - edges: List[Edge]                                              |
| - state: SharedState                                             |
| - metadata: GraphMetadata                                        |
|------------------------------------------------------------------|
| + add_node(node: Node) -> None                                   |
| + add_edge(edge: Edge) -> None                                   |
| + remove_node(node_id: str) -> None                              |
| + get_execution_order() -> List[List[Node]]                      |
| + validate() -> ValidationResult                                 |
| + execute(ctx: ExecutionContext) -> GraphResult                   |
| + to_yaml() -> str                                               |
| + from_yaml(yaml_str: str) -> DirectedGraph                      |
+------------------------------------------------------------------+
          |                                    |
          | contains                           | contains
          v                                    v
+------------------------+         +---------------------------+
|         Node           |         |          Edge             |
|------------------------|         |---------------------------|
| - id: str              |         | - id: str                 |
| - type: NodeType       |         | - source_id: str          |
| - config: NodeConfig   |         | - target_id: str          |
| - inputs: List[Port]   |         | - type: EdgeType          |
| - outputs: List[Port]  |         | - condition: Optional[    |
| - position: (int,int)  |         |     Callable]             |
| - retry_policy: Retry  |         | - transform: Optional[    |
| - timeout: int         |         |     Callable]             |
|------------------------|         | - priority: int           |
| + execute(ctx) -> Out  |         |---------------------------|
| + validate() -> bool   |         | + evaluate(state) -> bool |
| + clone() -> Node      |         | + apply_transform(data)   |
+------------------------+         +---------------------------+
```

### 1.3 Node Types

```python
class NodeType(Enum):
    AGENT = "agent"              # Wraps an AI agent with tools
    SUBGRAPH = "subgraph"        # Embeds another DirectedGraph
    LOOP = "loop"                # Iterates until condition met
    SWITCH = "switch"            # Conditional branching
    HUMAN_IN_LOOP = "human"      # Blocks for human input
    PARALLEL = "parallel"        # Runs children concurrently
    MERGE = "merge"              # Joins parallel branches
    CHECKPOINT = "checkpoint"    # Saves state for resume
    TRANSFORM = "transform"      # Pure data transformation
    GATE = "gate"                # Pass/fail quality gate
```

**Node Type Class Hierarchy:**

```
                        +------------+
                        |    Node    |
                        +-----+------+
                              |
          +--------+----------+----------+---------+
          |        |          |          |         |
    +-----+--+ +---+----+ +--+---+ +---+----+ +--+------+
    | Agent  | |SubGraph| | Loop | |Switch  | | Human   |
    | Node   | | Node   | | Node | | Node   | | Node    |
    +--------+ +--------+ +------+ +--------+ +---------+
    |agent_id| |graph   | |cond  | |cases   | |prompt   |
    |tools   | |io_map  | |max   | |default | |timeout  |
    |model   | |        | |body  | |        | |callback |
    +--------+ +--------+ +------+ +--------+ +---------+
```

**AgentNode** wraps one of the 16 agent types. It holds the agent's system prompt,
tool bindings, model preference, and retry policy.

**SubGraphNode** embeds a complete `DirectedGraph` instance, enabling hierarchical
composition. Input/output ports map to the sub-graph's entry/exit nodes.

**LoopNode** contains a body sub-graph that executes repeatedly until a condition
function returns `True` or `max_iterations` is reached. Used for the debug-fix loop.

**ExperimentLoopNode** extends LoopNode with keep/discard experiment semantics
(inspired by Karpathy's autoresearch). Each iteration: (1) agent proposes a
hypothesis and code change, (2) change is applied to an experiment git branch,
(3) metrics are measured and compared to baseline, (4) the change is merged if
improved or the branch is discarded if degraded. An experiment log (TSV) tracks
all attempts. The loop stops when the time budget is exhausted, the token budget
is exceeded, or N consecutive experiments show no improvement.

**SwitchNode** evaluates the shared state against a list of case predicates and routes
execution to the first matching branch. The `default` branch catches unmatched cases.

**HumanInLoopNode** pauses execution, emits a `HumanApprovalRequired` event, and waits
for input via the CLI, web UI, or API webhook. Configurable timeout with auto-escalation.

### 1.4 Edge Types

```python
class EdgeType(Enum):
    STATE_FLOW = "state_flow"      # Shared state propagation
    MESSAGE_FLOW = "message_flow"  # Direct inter-agent messages
    CONTROL_FLOW = "control_flow"  # Execution triggers / signals
```

| Edge Type      | Semantics | Data Carried | When Evaluated |
|---------------|-----------|-------------|----------------|
| STATE_FLOW    | Source writes to SharedState; target reads from it. Optional `transform` mutates data in transit. | Arbitrary state dict | After source completes |
| MESSAGE_FLOW  | Direct message from one agent to another, bypassing shared state. Useful for review feedback. | `AgentMessage` object | After source completes |
| CONTROL_FLOW  | Pure trigger: source completion (optionally with condition) triggers target start. No data. | None (signal only) | After source completes, condition evaluated |

### 1.5 Graph Execution Engine

```
                     EXECUTION FLOW
                     ==============

  +------------------+
  | Parse Graph YAML |
  +--------+---------+
           |
           v
  +--------+---------+
  | Validate Graph   |----> Error: cycle detection, missing edges
  +--------+---------+
           |
           v
  +--------+----------+
  | Topological Sort  |  Kahn's algorithm: produces execution layers
  +--------+----------+
           |
           v
  +--------+----------+
  | Layer 0: [A, B]   |  Independent nodes run in parallel
  | Layer 1: [C]      |  C depends on A and B
  | Layer 2: [D, E]   |  D and E depend on C
  | Layer 3: [F]      |  F depends on D and E
  +--------+----------+
           |
           v
  +--------+----------+       +------------------+
  | ExecutionEngine   |<----->| SharedState      |
  |   .run_layer()    |       | (thread-safe)    |
  +--------+----------+       +------------------+
           |
           |  For each layer:
           |    1. Collect ready nodes
           |    2. Evaluate edge conditions
           |    3. Submit to thread/process pool
           |    4. Await completion
           |    5. Apply state transforms
           |    6. Emit events
           |    7. Check gates / human approvals
           |    8. Advance to next layer
           |
           v
  +--------+----------+
  | GraphResult       |
  | - outputs         |
  | - execution_log   |
  | - metrics         |
  +-------------------+
```

```python
class ExecutionEngine:
    """Core graph execution runtime."""

    def __init__(self, graph: DirectedGraph, executor: ThreadPoolExecutor):
        self.graph = graph
        self.executor = executor
        self.state = SharedState()
        self.event_bus = EventBus()
        self.checkpoint_mgr = CheckpointManager()

    async def execute(self, ctx: ExecutionContext) -> GraphResult:
        layers = self.graph.get_execution_order()  # topological sort
        execution_log = []

        for layer_idx, layer in enumerate(layers):
            # Filter nodes whose incoming edge conditions are met
            ready_nodes = [
                node for node in layer
                if self._all_conditions_met(node)
            ]

            # Execute all ready nodes in parallel
            tasks = [
                self._execute_node(node, ctx)
                for node in ready_nodes
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results, update state, handle failures
            for node, result in zip(ready_nodes, results):
                if isinstance(result, Exception):
                    await self._handle_failure(node, result, ctx)
                else:
                    self._apply_state_updates(node, result)
                    execution_log.append(ExecutionRecord(node, result))

            # Checkpoint after each layer
            await self.checkpoint_mgr.save(self.state, layer_idx)

        return GraphResult(outputs=self.state.get_outputs(), log=execution_log)

    async def _execute_node(self, node: Node, ctx: ExecutionContext):
        self.event_bus.emit(AgentStarted(node_id=node.id))
        try:
            result = await node.execute(ctx.with_state(self.state))
            self.event_bus.emit(AgentCompleted(node_id=node.id, result=result))
            return result
        except Exception as e:
            self.event_bus.emit(AgentFailed(node_id=node.id, error=e))
            raise
```

### 1.6 Reusability: Templates and Composed Graphs

```python
class NodeTemplate:
    """Reusable agent configuration template."""

    def __init__(self, name: str, node_type: NodeType, config: NodeConfig):
        self.name = name
        self.node_type = node_type
        self.config = config

    def instantiate(self, node_id: str, overrides: dict = None) -> Node:
        """Clone this template into a concrete node with optional overrides."""
        cfg = self.config.copy()
        if overrides:
            cfg.update(overrides)
        return Node(id=node_id, type=self.node_type, config=cfg)


class ComposedGraph:
    """Pre-built workflow patterns that can be embedded as SubGraphNodes."""

    @staticmethod
    def code_review_loop() -> DirectedGraph:
        """Standard code -> review -> fix cycle."""
        g = DirectedGraph(name="code-review-loop")
        coder = NodeTemplate.BACKEND_DEV.instantiate("coder")
        reviewer = NodeTemplate.CODE_REVIEWER.instantiate("reviewer")
        fixer = NodeTemplate.DEBUGGER.instantiate("fixer")

        g.add_node(coder)
        g.add_node(reviewer)
        g.add_node(fixer)

        g.add_edge(Edge("coder", "reviewer", EdgeType.STATE_FLOW))
        g.add_edge(Edge("reviewer", "fixer",  EdgeType.MESSAGE_FLOW,
                        condition=lambda state: not state["review_approved"]))
        g.add_edge(Edge("fixer", "reviewer",  EdgeType.STATE_FLOW))
        return g

    @staticmethod
    def security_scan_pipeline() -> DirectedGraph:
        """Parallel security scanning sub-graph."""
        g = DirectedGraph(name="security-scan")
        sast = AgentNode("sast", tools=["semgrep", "sonarqube"])
        dast = AgentNode("dast", tools=["shannon"])
        deps = AgentNode("deps", tools=["trivy", "opensca"])
        secrets = AgentNode("secrets", tools=["gitleaks"])
        merge = MergeNode("sec-merge")

        for node in [sast, dast, deps, secrets]:
            g.add_node(node)
            g.add_edge(Edge(node.id, "sec-merge", EdgeType.STATE_FLOW))
        g.add_node(merge)
        return g

    @staticmethod
    def experiment_loop(
        agent_template: NodeTemplate,
        metric_fn: str,
        time_budget_seconds: int = 600,
        max_no_improvement: int = 5,
        improvement_threshold: float = 0.01,
    ) -> DirectedGraph:
        """
        Autonomous experiment loop with keep/discard semantics.
        Inspired by Karpathy's autoresearch framework.

        Each iteration:
          1. Agent proposes hypothesis + code change
          2. Change applied to experiment branch (git checkout -b experiment/N)
          3. Metric measured against baseline
          4. If improved beyond threshold: merge to working branch, update baseline
          5. If degraded or below threshold: discard branch
          6. Result logged to experiment_log.tsv
          7. Repeat until: time_budget exhausted, max_no_improvement consecutive
             non-improvements, or token budget exceeded

        Used for: Debug fix loops (S8), Performance optimization (S6),
                  Security hardening (S6), Test coverage improvement (S7),
                  and standalone Improve mode projects.
        """
        g = DirectedGraph(name="experiment-loop")

        baseline    = AgentNode("baseline_measure", tools=["test_runner", "metric_collector"])
        hypothesize = agent_template.instantiate("hypothesize")
        apply       = AgentNode("apply_experiment", tools=["code_writer", "git_branch_manager"])
        measure     = AgentNode("measure_experiment", tools=["test_runner", "metric_collector"])
        evaluate    = SwitchNode("evaluate", cases=[
            ("improved",   lambda s: s["metric_delta"] >= improvement_threshold),
            ("regressed",  lambda s: s["metric_delta"] < 0),
            ("no_change",  lambda s: True),  # default
        ])
        keep        = AgentNode("keep_experiment", tools=["git_merge", "experiment_logger"])
        discard     = AgentNode("discard_experiment", tools=["git_branch_delete", "experiment_logger"])

        for node in [baseline, hypothesize, apply, measure, evaluate, keep, discard]:
            g.add_node(node)

        g.add_edge(Edge("baseline_measure", "hypothesize",      EdgeType.STATE_FLOW))
        g.add_edge(Edge("hypothesize",      "apply_experiment", EdgeType.STATE_FLOW))
        g.add_edge(Edge("apply_experiment", "measure_experiment", EdgeType.STATE_FLOW))
        g.add_edge(Edge("measure_experiment", "evaluate",        EdgeType.STATE_FLOW))
        g.add_edge(Edge("evaluate",         "keep_experiment",   EdgeType.CONTROL_FLOW,
                        condition=lambda s: s["decision"] == "improved"))
        g.add_edge(Edge("evaluate",         "discard_experiment", EdgeType.CONTROL_FLOW,
                        condition=lambda s: s["decision"] != "improved"))
        # Loop back: both keep and discard feed back to hypothesize for next experiment
        g.add_edge(Edge("keep_experiment",    "hypothesize", EdgeType.STATE_FLOW))
        g.add_edge(Edge("discard_experiment", "hypothesize", EdgeType.STATE_FLOW))

        g.metadata = {
            "metric_fn": metric_fn,
            "time_budget_seconds": time_budget_seconds,
            "max_no_improvement": max_no_improvement,
            "improvement_threshold": improvement_threshold,
            "experiment_log_format": "commit_hash\thyp\tmetric_before\tmetric_after\tdelta\tstatus\tdiff_lines\tduration_s",
        }
        return g
```

### 1.7 SDLC Pipeline as a Graph

```python
def build_sdlc_pipeline() -> DirectedGraph:
    """
    Models the complete Software Development Lifecycle as a directed graph.

    Corrected 10-stage pipeline (v2.2):
      S0  - Project Initialization:  [orchestrator]
      S1  - Discovery & Brainstorm:  [brainstorm]
      S2  - Research & Analysis:     [researcher]            # AFTER brainstorm
      S3  - Architecture & Design:   [architect, designer]   # AFTER research, parallel agents
      S4  - Planning & Config:       [planner]               # AFTER architecture
      S5  - Implementation:          [frontend_dev, backend_dev, middleware_dev]  # full parallel
      S6  - Quality Assurance:       [code_reviewer, security_auditor]           # full parallel
      S7  - Testing & Validation:    [tester]                # parallel test suites (unit, integration,
                                                             #   e2e, UI, smoke, regression, mutation)
      S8  - Debug & Stabilization:   [debugger]              # loop
      S9  - Documentation & Knowledge: [doc_writer]
      S10 - Deployment & Delivery:   [infra_engineer, project_manager, human_approval]
    """
    g = DirectedGraph(name="sdlc-pipeline", version="2.2")

    # --- Nodes ---
    orchestrator   = AgentNode("orchestrator",   agent=OrchestratorAgent)
    brainstorm     = AgentNode("brainstorm",     agent=BrainstormAgent)
    researcher     = AgentNode("researcher",     agent=ResearcherAgent)      # AFTER brainstorm
    architect      = AgentNode("architect",      agent=ArchitectAgent)       # AFTER researcher
    designer       = AgentNode("designer",       agent=DesignerAgent)
    planner        = AgentNode("planner",        agent=PlannerAgent)         # AFTER architect (NOT before!)
    frontend_dev   = AgentNode("frontend_dev",   agent=FrontendDevAgent)
    backend_dev    = AgentNode("backend_dev",    agent=BackendDevAgent)
    middleware_dev = AgentNode("middleware_dev",  agent=MiddlewareDevAgent)
    reviewer       = AgentNode("reviewer",       agent=CodeReviewerAgent)
    security       = AgentNode("security",       agent=SecurityAuditorAgent)
    tester         = AgentNode("tester",         agent=TesterAgent)
    debugger       = ExperimentLoopNode("debugger", agent=DebuggerAgent,
                              condition=lambda s: s["all_tests_pass"],
                              max_iterations=5,
                              metric_fn="test_pass_rate",
                              time_budget_seconds=600,
                              max_no_improvement=3)
    doc_writer     = AgentNode("doc_writer",     agent=DocWriterAgent)
    infra_eng      = AgentNode("infra_eng",      agent=InfraEngineerAgent)
    project_mgr    = AgentNode("project_mgr",   agent=ProjectManagerAgent)
    human_gate     = HumanInLoopNode("human_approval",
                                     prompt="Review deliverables and approve?")

    for node in [orchestrator, brainstorm, researcher, architect, designer,
                 planner, frontend_dev, backend_dev, middleware_dev,
                 reviewer, security, tester, debugger, doc_writer,
                 infra_eng, project_mgr, human_gate]:
        g.add_node(node)

    # --- S0 -> S1: Initialization to Discovery ---
    g.add_edge(Edge("orchestrator",   "brainstorm",     EdgeType.STATE_FLOW))

    # --- S1 -> S2: Brainstorm to Research ---
    g.add_edge(Edge("brainstorm",     "researcher",     EdgeType.STATE_FLOW))

    # --- S2 -> S3: Research to Architecture & Design (parallel) ---
    g.add_edge(Edge("researcher",     "architect",      EdgeType.STATE_FLOW))
    g.add_edge(Edge("architect",      "designer",       EdgeType.STATE_FLOW))

    # --- S3 -> S4: Architecture to Planning ---
    g.add_edge(Edge("architect",      "planner",        EdgeType.STATE_FLOW))
    g.add_edge(Edge("designer",       "planner",        EdgeType.STATE_FLOW))

    # --- S4 -> S5: Planning to Implementation (full parallel) ---
    g.add_edge(Edge("planner",        "frontend_dev",   EdgeType.STATE_FLOW))
    g.add_edge(Edge("planner",        "backend_dev",    EdgeType.STATE_FLOW))
    g.add_edge(Edge("planner",        "middleware_dev",  EdgeType.STATE_FLOW))

    # --- S5 -> S6: Implementation to Quality Assurance (full parallel) ---
    g.add_edge(Edge("frontend_dev",   "reviewer",       EdgeType.STATE_FLOW))
    g.add_edge(Edge("backend_dev",    "reviewer",       EdgeType.STATE_FLOW))
    g.add_edge(Edge("middleware_dev",  "reviewer",       EdgeType.STATE_FLOW))
    g.add_edge(Edge("frontend_dev",   "security",       EdgeType.STATE_FLOW))
    g.add_edge(Edge("backend_dev",    "security",       EdgeType.STATE_FLOW))
    g.add_edge(Edge("middleware_dev",  "security",       EdgeType.STATE_FLOW))

    # --- S6 -> S7: QA to Testing & Validation (parallel test suites) ---
    g.add_edge(Edge("reviewer",       "tester",         EdgeType.STATE_FLOW))
    g.add_edge(Edge("security",       "tester",         EdgeType.MESSAGE_FLOW))

    # --- S7 -> S8: Testing to Debug & Stabilization (loop) ---
    g.add_edge(Edge("tester",         "debugger",       EdgeType.STATE_FLOW))

    # --- S8 -> S9: Debug to Documentation & Knowledge ---
    g.add_edge(Edge("debugger",       "doc_writer",     EdgeType.STATE_FLOW))

    # --- S9 -> S10: Documentation to Deployment & Delivery ---
    g.add_edge(Edge("doc_writer",     "infra_eng",      EdgeType.STATE_FLOW))
    g.add_edge(Edge("infra_eng",      "project_mgr",    EdgeType.STATE_FLOW))
    g.add_edge(Edge("project_mgr",    "human_approval",  EdgeType.STATE_FLOW))

    # --- Cross-cutting: Orchestrator monitors Project Manager ---
    g.add_edge(Edge("orchestrator",   "project_mgr",    EdgeType.STATE_FLOW))

    return g
```

**Visual Graph Representation (v2.2 -- corrected 10-stage pipeline):**

```
  S0              +----------------+
                  |  Orchestrator  |  (Project Initialization)
                  +-------+--------+
                          |
  S1              +-------+--------+
                  |  Brainstormer  |  (Discovery & Brainstorming)
                  +-------+--------+
                          |
  S2              +-------+--------+
                  |   Researcher   |  (Research & Analysis)
                  +-------+--------+
                          |
  S3              +-------+--------+
                  |   Architect    |  (Architecture & Design)
                  +---+--------+---+
                      |        |
                      v        v
              +-------+----+ +-+----------+
              |  Designer  | |  (feeds)   |
              +-------+----+ +--+---------+
                      |         |
  S4              +---+---------+--+
                  |     Planner    |  (Planning & Configuration)
                  +---+---+---+----+
                      |   |   |
        +-------------+   |   +--------------+
        |                 |                  |
  S5    v                 v                  v
  +-----+--------+ +-----+--------+ +-------+----------+
  | Frontend Dev | | Backend Dev  | | Middleware Dev    |  (Implementation)
  +-----+--------+ +-----+--------+ +-------+----------+
        |                 |                  |
        +--------+--------+------------------+
                 |
  S6    +--------+-------+--------+
        |                         |
        v                         v
  +-----+--------+  +-------------+-----+
  | Code Reviewer|  | Security Auditor  |  (Quality Assurance)
  +-----+--------+  +-------------+-----+
        |                         |
        +--------+-------+--------+
                 |
  S7    +--------+---------+
        |      Tester      |  (Testing & Validation)
        | [unit, integration, e2e,    |
        |  UI, smoke, regression,     |
        |  mutation testing]          |
        +--------+---------+
                 |
  S8    +--------+---------+
        |     Debugger     |<---+
        |   (Loop Node)    |    | (fix iteration)
        +--------+------+--+----+
                 |
  S9    +--------+---------+
        |    Doc Writer    |  (Documentation & Knowledge)
        +--------+---------+
                 |
  S10   +--------+---------+
        |  Infra Engineer  |  (Deployment & Delivery)
        +--------+---------+
                 |
                 v
        +--------+---------+
        | Project Manager  |
        +--------+---------+
                 |
                 v
        +--------+---------+
        |  Human Approval  |
        +------------------+
```

---

## 2. Agent Design

### 2.0 Agent Base Architecture

All 16 agents inherit from a common `BaseAgent` class that standardizes lifecycle
management, context injection, tool invocation, and observability.

```
+-------------------------------------------------------------------+
|                          BaseAgent                                |
|-------------------------------------------------------------------|
| - agent_id: str                                                   |
| - role: AgentRole                                                 |
| - system_prompt: str                                              |
| - model: ModelConfig                                              |
| - tools: List[Tool]                                               |
| - context_adapter: ContextAdapter                                 |
| - memory: MemoryManager                                           |
| - event_bus: EventBus                                             |
| - token_budget: TokenBudget                                       |
|-------------------------------------------------------------------|
| + execute(input: AgentInput) -> AgentOutput                       |
| + plan(task: Task) -> ActionPlan                                  |
| + invoke_tool(tool: str, args: dict) -> ToolResult                |
| + request_context(query: str) -> ContextChunk                     |
| + emit_event(event: Event) -> None                                |
| + escalate(reason: str) -> None                                   |
+-------------------------------------------------------------------+
```

### 2.1 Orchestrator Agent

**Role and Responsibilities:**
- Top-level coordinator for the entire SDLC pipeline
- Decomposes user requirements into a structured project plan
- Decides which agents to activate and in what order
- Monitors overall progress and handles escalations
- Makes go/no-go decisions at phase boundaries

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | User requirements (natural language) | `str` |
| Input | Project configuration | `ProjectConfig` |
| Input | Existing codebase context (if any) | `CodebaseContext` |
| Output | Project plan with phases and tasks | `ProjectPlan` |
| Output | Agent assignments | `Dict[str, AgentAssignment]` |
| Output | Pipeline configuration | `PipelineConfig` |

**Tools Available:**
- `project_analyzer` -- analyze existing codebase structure
- `task_decomposer` -- break requirements into atomic tasks
- `agent_selector` -- choose optimal agent for each task
- `progress_tracker` -- query pipeline execution status
- `escalation_handler` -- escalate to human when stuck

**LLM Model Preferences:**
- Primary: `claude-opus-4` (best for complex reasoning and planning)
- Fallback: `gpt-4o` (strong alternative for orchestration)
- Budget: High token budget (orchestration requires extensive context)

**System Prompt Design Principles:**
- Emphasize structured output (JSON project plans)
- Include SDLC phase definitions and transition criteria
- Provide examples of well-decomposed project plans
- Instruct on when to escalate vs. autonomously decide

**Interaction Patterns:**
- Sends `ProjectInit` to Brainstormer via STATE_FLOW (S0 -> S1)
- Receives `AgentFailed` events from any agent and decides retry/escalate
- Can dynamically re-route the graph (e.g., skip Designer for CLI-only projects)
- Monitors Project Manager via STATE_FLOW for overall pipeline status

---

### 2.1b Brainstormer Agent (S1: Discovery & Brainstorming)

**Role and Responsibilities:**
- Receives project initialization data from the Orchestrator
- Conducts creative exploration of requirements, constraints, and possibilities
- Generates ideas for features, approaches, and technical solutions
- Identifies edge cases, risks, and open questions early in the lifecycle
- Produces structured brainstorm output that feeds Research (S2)

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Project initialization data | `ProjectInit` |
| Input | User requirements (natural language) | `str` |
| Output | Brainstorm output (ideas, questions, risks) | `BrainstormOutput` |
| Output | Research questions for Researcher | `List[ResearchQuestion]` |

**Tools Available:**
- `idea_generator` -- generates creative feature/approach ideas
- `requirement_expander` -- expands vague requirements into specifics
- `risk_identifier` -- identifies risks and edge cases
- `constraint_analyzer` -- analyzes constraints and trade-offs

**LLM Model Preferences:**
- Primary: `claude-opus-4` (best for creative, divergent thinking)
- Fallback: `gpt-4o` (good alternative for brainstorming)

**System Prompt Design Principles:**
- Encourage creative, divergent thinking before convergence
- Instruct on structuring output for downstream research consumption
- Include templates for idea categorization and prioritization

**Interaction Patterns:**
- Receives `ProjectInit` from Orchestrator (STATE_FLOW) -- S0 -> S1
- Sends `BrainstormOutput` to Researcher (STATE_FLOW) -- S1 -> S2

---

### 2.2 Planner Agent (S4: Planning & Configuration)

**Role and Responsibilities:**
- Receives architecture and design output from Architect and Designer (S3)
- Creates detailed, actionable task breakdowns with acceptance criteria
- Estimates effort and assigns priorities
- Identifies dependencies between tasks
- Produces a DAG of tasks that maps onto the graph execution engine

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Architecture document (from Architect) | `ArchitectureDoc` |
| Input | Design specifications (from Designer) | `DesignSpecs` |
| Input | Technology constraints | `TechConstraints` |
| Output | Task DAG with dependencies | `TaskGraph` |
| Output | Effort estimates | `Dict[str, Estimate]` |
| Output | Risk assessment | `RiskReport` |

**Tools Available:**
- `task_graph_builder` -- creates dependency DAG
- `effort_estimator` -- estimates story points / time
- `tech_stack_resolver` -- resolves technology choices
- `requirement_validator` -- checks for ambiguous requirements

**LLM Model Preferences:**
- Primary: `claude-opus-4` (strong structured reasoning)
- Fallback: `gemini-2.5-pro` (good at detailed planning)

**System Prompt Design Principles:**
- Focus on SMART criteria for tasks (Specific, Measurable, Achievable, Relevant, Time-bound)
- Include templates for task definitions
- Emphasize dependency identification

**Interaction Patterns:**
- Receives `ArchitectureDoc` from Architect and `DesignSpecs` from Designer (STATE_FLOW)
- Sends `TaskGraph` to Implementation agents: Frontend Dev, Backend Dev, Middleware Dev (STATE_FLOW)
- May send clarification requests back to Orchestrator (MESSAGE_FLOW)

---

### 2.3 Researcher Agent

**Role and Responsibilities:**
- Investigates technical approaches, libraries, APIs, and best practices
- Analyzes existing codebases for patterns and conventions
- Gathers documentation for chosen technologies
- Produces research summaries that inform architectural decisions

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Task graph with research questions | `TaskGraph` |
| Input | Technology constraints | `TechConstraints` |
| Output | Research findings | `ResearchReport` |
| Output | Technology recommendations | `TechRecommendations` |
| Output | Reference documentation | `List[DocReference]` |

**Tools Available:**
- `web_search` -- search the web for documentation and articles
- `code_search` -- search code repositories for patterns
- `doc_reader` -- read and summarize documentation
- `api_explorer` -- explore API endpoints and schemas
- `package_analyzer` -- analyze npm/pip/cargo packages for suitability

**LLM Model Preferences:**
- Primary: `gemini-2.5-pro` (excellent at information synthesis, large context)
- Fallback: `claude-opus-4` (strong analysis)

**System Prompt Design Principles:**
- Emphasize citing sources and providing evidence
- Instruct to compare multiple approaches with pros/cons
- Focus on production-readiness and community support

**Interaction Patterns:**
- Receives `BrainstormOutput` from Brainstormer (STATE_FLOW) -- S1 -> S2
- Sends `ResearchReport` to Architect (STATE_FLOW) -- S2 -> S3

---

### 2.4 Architect Agent

**Role and Responsibilities:**
- Designs system architecture based on requirements and research
- Produces component diagrams, data flow diagrams, and API contracts
- Selects design patterns and architectural styles
- Defines module boundaries and interfaces
- Creates the technical specification that developers follow

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Research findings | `ResearchReport` |
| Input | Task graph | `TaskGraph` |
| Output | Architecture document | `ArchitectureDoc` |
| Output | API contracts | `List[APIContract]` |
| Output | Data models | `List[DataModel]` |
| Output | Component diagram | `ComponentDiagram` |

**Tools Available:**
- `diagram_generator` -- generates Mermaid/PlantUML diagrams
- `api_contract_builder` -- creates OpenAPI/GraphQL schemas
- `data_modeler` -- designs database schemas
- `pattern_selector` -- recommends design patterns
- `dependency_analyzer` -- analyzes component coupling

**LLM Model Preferences:**
- Primary: `claude-opus-4` (best for complex system design reasoning)
- Fallback: `gpt-4o`

**System Prompt Design Principles:**
- Include architectural pattern library (microservices, monolith, serverless)
- Emphasize SOLID principles and clean architecture
- Instruct on creating clear interface boundaries

**Interaction Patterns:**
- Receives `ResearchReport` from Researcher (STATE_FLOW) -- S2 -> S3
- Sends `ArchitectureDoc` to Designer (STATE_FLOW) -- within S3
- Sends `ArchitectureDoc` to Planner (STATE_FLOW) -- S3 -> S4

---

### 2.5 Designer Agent

**Role and Responsibilities:**
- Creates UI/UX designs based on architecture and requirements
- Produces wireframes, component hierarchies, and design tokens
- Defines responsive layouts and interaction patterns
- Generates design system specifications

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Architecture document | `ArchitectureDoc` |
| Input | UI requirements | `UIRequirements` |
| Output | Wireframes | `List[Wireframe]` |
| Output | Component tree | `ComponentTree` |
| Output | Design tokens | `DesignTokens` |
| Output | Interaction specs | `InteractionSpecs` |

**Tools Available:**
- `wireframe_generator` -- creates ASCII/SVG wireframes
- `component_designer` -- designs reusable UI components
- `color_palette_generator` -- generates accessible color schemes
- `layout_engine` -- designs responsive grid layouts
- `accessibility_checker` -- validates WCAG compliance

**LLM Model Preferences:**
- Primary: `claude-opus-4` (strong visual reasoning)
- Fallback: `gpt-4o`

**System Prompt Design Principles:**
- Include design system principles (atomic design methodology)
- Emphasize accessibility (WCAG 2.1 AA minimum)
- Provide responsive breakpoint standards

**Interaction Patterns:**
- Receives `ArchitectureDoc` from Architect (STATE_FLOW) -- within S3
- Sends `DesignSpecs` to Planner (STATE_FLOW) -- S3 -> S4

---

### 2.6 Frontend Dev Agent

**Role and Responsibilities:**
- Implements UI components based on designer output
- Writes frontend application code (React, Vue, Svelte, etc.)
- Implements client-side state management
- Handles API integration on the client side
- Writes component tests

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Component tree and design tokens | `ComponentTree`, `DesignTokens` |
| Input | API contracts | `List[APIContract]` |
| Input | Architecture document | `ArchitectureDoc` |
| Output | Frontend source code | `List[CodeArtifact]` |
| Output | Component tests | `List[TestArtifact]` |
| Output | Build configuration | `BuildConfig` |

**Tools Available:**
- `code_writer` -- writes code files to the worktree
- `file_reader` -- reads existing code for context
- `terminal` -- runs build tools, linters, formatters
- `package_manager` -- installs npm/yarn/pnpm dependencies
- `browser_preview` -- launches dev server and captures screenshots

**LLM Model Preferences:**
- Primary: `claude-sonnet-4` (excellent code generation, fast)
- CLI Agent: `claude-code` (via CLI Agent Runner for complex file operations)
- Fallback: `gpt-4o`

**System Prompt Design Principles:**
- Include framework-specific best practices
- Emphasize component reusability and separation of concerns
- Instruct on proper TypeScript typing

**Interaction Patterns:**
- Receives `TaskGraph` and design specs from Planner (STATE_FLOW) -- S4 -> S5
- Sends code artifacts to Code Reviewer and Security Auditor (STATE_FLOW) -- S5 -> S6
- Runs in parallel with Backend Dev and Middleware Dev

---

### 2.7 Backend Dev Agent

**Role and Responsibilities:**
- Implements server-side logic, APIs, and business rules
- Designs and implements database schemas and migrations
- Builds authentication/authorization systems
- Implements background jobs and event handlers
- Writes integration tests

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | API contracts | `List[APIContract]` |
| Input | Data models | `List[DataModel]` |
| Input | Architecture document | `ArchitectureDoc` |
| Output | Backend source code | `List[CodeArtifact]` |
| Output | Database migrations | `List[Migration]` |
| Output | Integration tests | `List[TestArtifact]` |

**Tools Available:**
- `code_writer` -- writes code files to the worktree
- `file_reader` -- reads existing code for context
- `terminal` -- runs servers, tests, database commands
- `database_client` -- executes SQL/NoSQL queries
- `api_tester` -- sends HTTP requests to test endpoints

**LLM Model Preferences:**
- Primary: `claude-sonnet-4` (strong code generation)
- CLI Agent: `claude-code` or `codex-cli`
- Fallback: `gemini-2.5-pro`

**System Prompt Design Principles:**
- Include API design best practices (RESTful, error handling)
- Emphasize input validation and security
- Instruct on database query optimization

**Interaction Patterns:**
- Receives API contracts from Architect (STATE_FLOW)
- Sends code artifacts to Code Reviewer (STATE_FLOW)
- Runs in parallel with Frontend Dev and Middleware Dev

---

### 2.8 Middleware Dev Agent

**Role and Responsibilities:**
- Implements middleware layers: API gateways, message queues, caching
- Builds service-to-service communication (gRPC, message brokers)
- Implements rate limiting, circuit breakers, and retry logic
- Handles data transformation and protocol translation

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Architecture document | `ArchitectureDoc` |
| Input | API contracts (inter-service) | `List[APIContract]` |
| Output | Middleware source code | `List[CodeArtifact]` |
| Output | Infrastructure configs | `List[InfraConfig]` |
| Output | Integration tests | `List[TestArtifact]` |

**Tools Available:**
- `code_writer` -- writes code files
- `file_reader` -- reads existing code
- `terminal` -- runs services and tests
- `message_queue_client` -- interacts with RabbitMQ/Kafka
- `cache_client` -- interacts with Redis/Memcached

**LLM Model Preferences:**
- Primary: `claude-sonnet-4`
- CLI Agent: `claude-code`
- Fallback: `gpt-4o`

**System Prompt Design Principles:**
- Include distributed systems patterns
- Emphasize fault tolerance and resilience
- Instruct on proper logging and observability

**Interaction Patterns:**
- Receives architecture specs from Designer/Architect (STATE_FLOW)
- Sends code artifacts to Code Reviewer (STATE_FLOW)
- Runs in parallel with Frontend Dev and Backend Dev

---

### 2.9 Infra Engineer Agent

**Role and Responsibilities:**
- Creates Infrastructure-as-Code (Terraform, Pulumi, CloudFormation)
- Configures CI/CD pipelines (GitHub Actions, GitLab CI)
- Sets up containerization (Dockerfile, docker-compose)
- Configures monitoring and alerting
- Manages deployment strategies (blue-green, canary)

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Architecture document | `ArchitectureDoc` |
| Input | Finalized code artifacts | `List[CodeArtifact]` |
| Output | IaC definitions | `List[InfraArtifact]` |
| Output | CI/CD pipeline configs | `List[PipelineConfig]` |
| Output | Dockerfiles and compose files | `List[ContainerConfig]` |
| Output | Monitoring configs | `MonitoringConfig` |

**Tools Available:**
- `code_writer` -- writes IaC files
- `terminal` -- runs terraform plan, docker build
- `cloud_api` -- queries cloud provider APIs
- `cost_estimator` -- estimates cloud infrastructure costs
- `security_scanner` -- scans IaC for misconfigurations

**LLM Model Preferences:**
- Primary: `claude-sonnet-4`
- CLI Agent: `claude-code`
- Fallback: `gpt-4o`

**System Prompt Design Principles:**
- Include cloud provider best practices (AWS/GCP/Azure)
- Emphasize cost optimization and right-sizing
- Instruct on security hardening

**Interaction Patterns:**
- Receives finalized code from Debugger (STATE_FLOW)
- Sends IaC artifacts to Doc Writer (STATE_FLOW)

---

### 2.10 Security Auditor Agent

**Role and Responsibilities:**
- Orchestrates automated security scanning (SAST, DAST, SCA)
- Reviews code for security vulnerabilities manually
- Checks for secrets, hardcoded credentials
- Validates authentication/authorization implementations
- Produces security findings with severity classifications

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Code artifacts from all dev agents | `List[CodeArtifact]` |
| Input | Architecture document | `ArchitectureDoc` |
| Output | Security findings | `List[SecurityFinding]` |
| Output | Security report | `SecurityReport` |
| Output | Remediation recommendations | `List[Remediation]` |

**Tools Available:**
- `semgrep` -- static analysis with custom rules
- `sonarqube_api` -- SonarQube scanning
- `trivy` -- container and dependency scanning
- `gitleaks` -- secret detection
- `shannon` -- dynamic application security testing
- `license_checker` -- OSS license compliance

**LLM Model Preferences:**
- Primary: `claude-opus-4` (best for security reasoning)
- Fallback: `gpt-4o`

**System Prompt Design Principles:**
- Include OWASP Top 10 reference
- Emphasize zero false-negative tolerance for critical findings
- Instruct on CVSS scoring methodology

**Interaction Patterns:**
- Receives code artifacts from Code Reviewer (STATE_FLOW)
- Sends security findings to Debugger (MESSAGE_FLOW)
- Runs in parallel with Tester

---

### 2.11 Code Reviewer Agent

**Role and Responsibilities:**
- Reviews code for quality, readability, and maintainability
- Checks adherence to project coding standards
- Identifies potential bugs and anti-patterns
- Suggests refactoring opportunities
- Approves or requests changes

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Code artifacts from dev agents | `List[CodeArtifact]` |
| Input | Architecture document | `ArchitectureDoc` |
| Input | Coding standards | `CodingStandards` |
| Output | Review comments | `List[ReviewComment]` |
| Output | Approval decision | `ReviewDecision` |
| Output | Suggested changes | `List[SuggestedChange]` |

**Tools Available:**
- `file_reader` -- reads code files for review
- `linter` -- runs language-specific linters
- `complexity_analyzer` -- measures cyclomatic complexity
- `diff_viewer` -- views git diffs
- `comment_writer` -- writes inline review comments

**LLM Model Preferences:**
- Primary: `claude-opus-4` (best for nuanced code understanding)
- Fallback: `claude-sonnet-4`

**System Prompt Design Principles:**
- Include code review checklist (naming, error handling, testing, etc.)
- Emphasize constructive feedback
- Instruct on severity classification of issues

**Interaction Patterns:**
- Receives code from Frontend, Backend, Middleware Devs (STATE_FLOW)
- Sends review results to Tester and Security Auditor (STATE_FLOW)
- Sends change requests back to Dev agents (MESSAGE_FLOW) in review loops

---

### 2.12 Tester Agent

**Role and Responsibilities:**
- Generates test cases based on requirements and code
- Writes unit tests, integration tests, and E2E tests
- Executes test suites and collects results
- Measures code coverage and enforces thresholds
- Identifies flaky tests and test gaps

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Code artifacts | `List[CodeArtifact]` |
| Input | API contracts | `List[APIContract]` |
| Input | Requirements | `TaskGraph` |
| Output | Test cases | `List[TestArtifact]` |
| Output | Test results | `TestResults` |
| Output | Coverage report | `CoverageReport` |

**Tools Available:**
- `code_writer` -- writes test files
- `test_runner` -- executes pytest/vitest/playwright
- `coverage_tool` -- collects coverage data
- `mock_generator` -- generates mocks and fixtures
- `terminal` -- runs arbitrary test commands

**LLM Model Preferences:**
- Primary: `claude-sonnet-4` (fast, good test generation)
- CLI Agent: `claude-code`
- Fallback: `gpt-4o`

**System Prompt Design Principles:**
- Include testing pyramid guidance (many unit, fewer integration, minimal E2E)
- Emphasize edge cases and boundary conditions
- Instruct on test isolation and determinism

**Interaction Patterns:**
- Receives code from Code Reviewer (STATE_FLOW)
- Sends test results to Debugger (STATE_FLOW)
- Runs in parallel with Security Auditor

---

### 2.13 Debugger Agent

**Role and Responsibilities:**
- Analyzes test failures and security findings to determine root causes
- Generates targeted fixes for identified issues
- Creates regression tests for each fix
- Verifies fixes by re-running relevant tests
- Manages the debug-fix iteration loop

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Test results with failures | `TestResults` |
| Input | Security findings | `List[SecurityFinding]` |
| Input | Source code context | `List[CodeArtifact]` |
| Output | Fix patches | `List[Patch]` |
| Output | Regression tests | `List[TestArtifact]` |
| Output | Fix verification results | `VerificationResults` |

**Tools Available:**
- `code_writer` -- writes fix patches
- `file_reader` -- reads code for context
- `test_runner` -- re-runs specific tests
- `debugger_tool` -- step-through debugging
- `stack_trace_analyzer` -- parses and analyzes stack traces
- `terminal` -- runs diagnostic commands

**LLM Model Preferences:**
- Primary: `claude-opus-4` (best for complex debugging reasoning)
- CLI Agent: `claude-code` (for interactive debugging sessions)
- Fallback: `claude-sonnet-4`

**System Prompt Design Principles:**
- Include systematic debugging methodology
- Emphasize minimal, targeted fixes (avoid unrelated changes)
- Instruct on root cause analysis over symptom treatment

**Interaction Patterns:**
- Receives test failures from Tester (STATE_FLOW)
- Receives security findings from Security Auditor (MESSAGE_FLOW)
- Loops back to self until all tests pass or max iterations reached
- Sends fixed code to Infra Engineer (STATE_FLOW)

---

### 2.14 Doc Writer Agent

**Role and Responsibilities:**
- Generates project documentation (README, API docs, guides)
- Creates inline code documentation and docstrings
- Produces architecture decision records (ADRs)
- Generates changelog entries
- Creates user-facing documentation

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | All code artifacts | `List[CodeArtifact]` |
| Input | Architecture document | `ArchitectureDoc` |
| Input | API contracts | `List[APIContract]` |
| Output | Documentation files | `List[DocArtifact]` |
| Output | API documentation | `APIDocumentation` |
| Output | Changelog | `Changelog` |

**Tools Available:**
- `code_writer` -- writes documentation files
- `file_reader` -- reads code for documentation
- `doc_generator` -- generates API docs from OpenAPI specs
- `markdown_formatter` -- formats Markdown documents
- `link_validator` -- checks documentation links

**LLM Model Preferences:**
- Primary: `claude-sonnet-4` (fast, clear writing)
- Fallback: `gpt-4o`

**System Prompt Design Principles:**
- Include documentation templates and standards
- Emphasize clarity and completeness
- Instruct on audience-appropriate language

**Interaction Patterns:**
- Receives all artifacts from Infra Engineer (STATE_FLOW)
- Sends documentation to Human Approval gate (STATE_FLOW)

---

### 2.15 Project Manager Agent (#30)

**Role and Responsibilities:**
- Tracks overall project progress across all pipeline phases
- Generates status reports (per-phase, per-agent, overall)
- Manages timelines and milestone tracking
- Identifies blockers and escalates proactively
- Sends notifications (pipeline stalls, budget warnings, completion)

**Input/Output Contract:**

| Direction | Data | Type |
|-----------|------|------|
| Input | Pipeline execution state | `PipelineState` |
| Input | Agent execution logs | `List[AgentExecution]` |
| Input | Project plan with milestones | `ProjectPlan` |
| Output | Status report | `StatusReport` |
| Output | Blocker alerts | `List[BlockerAlert]` |
| Output | Timeline updates | `TimelineUpdate` |
| Output | Notifications | `List[Notification]` |

**Tools Available:**
- `progress_tracker` -- queries pipeline and agent execution status
- `report_generator` -- generates structured status reports
- `timeline_manager` -- tracks milestones, deadlines, and slippage
- `blocker_detector` -- identifies stalled agents or failing phases
- `notification_sender` -- sends alerts via configured channels

**LLM Model Preferences:**
- Primary: `claude-sonnet-4` (fast summarization and reporting)
- Fallback: `gpt-4o`

**System Prompt Design Principles:**
- Include project management best practices and templates
- Emphasize concise, actionable reporting
- Instruct on proactive blocker identification

**Interaction Patterns:**
- Receives pipeline state from Orchestrator (STATE_FLOW)
- Broadcasts status reports to all agents (MESSAGE_FLOW)
- Sends blocker alerts to Orchestrator for escalation (STATE_FLOW)

---

### 2.16 Agent Interaction Matrix

```
                  Orch Brn  Res  Arch Des  Plan FDev BDev MDev Rev  Sec  Test Dbg  Doc  Infra PM
Orchestrator       --   SF   .    .    .    .    .    .    .    .    .    .    .    .    .    SF
Brainstormer       .    --   SF   .    .    .    .    .    .    .    .    .    .    .    .    .
Researcher         .    .    --   SF   .    .    .    .    .    .    .    .    .    .    .    .
Architect          .    .    .    --   SF   SF   .    .    .    .    .    .    .    .    .    .
Designer           .    .    .    .    --   SF   .    .    .    .    .    .    .    .    .    .
Planner            .    .    .    .    .    --   SF   SF   SF   .    .    .    .    .    .    .
Frontend Dev       .    .    .    .    .    .    --   .    .    SF   SF   .    .    .    .    .
Backend Dev        .    .    .    .    .    .    .    --   .    SF   SF   .    .    .    .    .
Middleware Dev     .    .    .    .    .    .    .    .    --   SF   SF   .    .    .    .    .
Code Reviewer      .    .    .    .    .    .    MF   MF   MF   --   .    SF   .    .    .    .
Security Auditor   .    .    .    .    .    .    .    .    .    .    --   MF   .    .    .    .
Tester             .    .    .    .    .    .    .    .    .    .    .    --   SF   .    .    .
Debugger           .    .    .    .    .    .    .    .    .    .    .    .    --   SF   .    .
Doc Writer         .    .    .    .    .    .    .    .    .    .    .    .    .    --   SF   .
Infra Engineer     .    .    .    .    .    .    .    .    .    .    .    .    .    .    --   SF
Project Manager    SF   .    .    .    .    .    .    .    .    .    .    .    .    .    .    --

Legend: SF = StateFlow, MF = MessageFlow, CF = ControlFlow, . = no direct edge

Corrected flow (v2.2):
  Orchestrator -> Brainstormer -> Researcher -> Architect -> Planner -> Implementation
  (Brainstorming feeds Research; Research feeds Architecture; Architecture feeds Planning)
```

---

## 3. Multi-LLM Abstraction Layer Design

### 3.1 Overview

The Multi-LLM Abstraction Layer provides a unified interface for interacting with
multiple LLM providers. It handles model routing, fallback chains, token budgeting,
cost tracking, and rate limiting -- all transparently to the agent layer above it.

### 3.2 Architecture

```
+------------------------------------------------------------------+
|                        Agent Layer                                |
|                  (16 Agent Types + BaseAgent)                     |
+---------------------------+--------------------------------------+
                            |
                            v
+---------------------------+--------------------------------------+
|                   LLMAbstractionLayer                            |
|------------------------------------------------------------------|
|  +-------------+  +--------------+  +------------------+        |
|  | ModelRouter  |  | FallbackChain|  | TokenBudgetMgr   |        |
|  +------+------+  +------+-------+  +--------+---------+        |
|         |                |                    |                  |
|  +------+------+  +------+-------+  +--------+---------+        |
|  | CostTracker |  | RateLimiter  |  | ResponseCache    |        |
|  +------+------+  +------+-------+  +--------+---------+        |
|         |                |                    |                  |
+---------|----------------|--------------------|---------+--------+
          |                |                    |         |
          v                v                    v         v
+----------------+ +----------------+ +-----------------+ +------+
| OpenAIProvider | | AnthropicProv  | | GoogleProvider  | | ...  |
+----------------+ +----------------+ +-----------------+ +------+
```

### 3.3 LLMProvider Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional

@dataclass
class LLMRequest:
    messages: List[Message]
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: Optional[List[ToolDefinition]] = None
    response_format: Optional[str] = None  # "json", "text"
    stream: bool = False

@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: TokenUsage
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: str = "stop"
    latency_ms: int = 0

@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class LLMProvider(ABC):
    """Unified interface for all LLM providers."""

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Send a completion request and return the response."""
        ...

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """Stream a completion response token by token."""
        ...

    @abstractmethod
    def supports_model(self, model: str) -> bool:
        """Check if this provider supports the given model."""
        ...

    @abstractmethod
    def get_rate_limits(self) -> RateLimitInfo:
        """Return current rate limit status."""
        ...

    @abstractmethod
    def get_pricing(self, model: str) -> PricingInfo:
        """Return pricing for the given model."""
        ...
```

### 3.4 Provider Implementations

```python
class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT-4o, GPT-4o-mini, o1, o3)."""

    SUPPORTED_MODELS = {
        "gpt-4o": {"input": 2.50, "output": 10.00},      # per 1M tokens
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "o1": {"input": 15.00, "output": 60.00},
        "o3-mini": {"input": 1.10, "output": 4.40},
    }

    async def complete(self, request: LLMRequest) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=request.model,
            messages=self._convert_messages(request.messages),
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tools=self._convert_tools(request.tools),
        )
        return self._parse_response(response)


class AnthropicProvider(LLMProvider):
    """Anthropic API provider (Claude Opus, Sonnet, Haiku)."""

    SUPPORTED_MODELS = {
        "claude-opus-4": {"input": 15.00, "output": 75.00},
        "claude-sonnet-4": {"input": 3.00, "output": 15.00},
        "claude-haiku-3.5": {"input": 0.80, "output": 4.00},
    }

    async def complete(self, request: LLMRequest) -> LLMResponse:
        response = await self.client.messages.create(
            model=request.model,
            messages=self._convert_messages(request.messages),
            max_tokens=request.max_tokens,
            tools=self._convert_tools(request.tools),
            system=self._extract_system(request.messages),
        )
        return self._parse_response(response)


class GoogleProvider(LLMProvider):
    """Google AI provider (Gemini 2.5 Pro, Flash)."""

    SUPPORTED_MODELS = {
        "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
        "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    }

    async def complete(self, request: LLMRequest) -> LLMResponse:
        response = await self.client.generate_content(
            model=request.model,
            contents=self._convert_messages(request.messages),
            generation_config=self._build_config(request),
            tools=self._convert_tools(request.tools),
        )
        return self._parse_response(response)
```

### 3.5 ModelRouter

```python
class ModelRouter:
    """Routes tasks to optimal models based on task characteristics."""

    # Task-to-model routing table
    ROUTING_TABLE = {
        # Task type            -> (primary_model, reason)
        "orchestration":        ("claude-opus-4",    "Complex planning/reasoning"),
        "planning":             ("claude-opus-4",    "Structured task decomposition"),
        "research":             ("gemini-2.5-pro",   "Large context, info synthesis"),
        "architecture":         ("claude-opus-4",    "System design reasoning"),
        "ui_design":            ("claude-opus-4",    "Visual/creative reasoning"),
        "code_generation":      ("claude-sonnet-4",  "Fast, high-quality code"),
        "code_review":          ("claude-opus-4",    "Nuanced code understanding"),
        "security_analysis":    ("claude-opus-4",    "Security reasoning"),
        "test_generation":      ("claude-sonnet-4",  "Fast test writing"),
        "debugging":            ("claude-opus-4",    "Root cause analysis"),
        "documentation":        ("claude-sonnet-4",  "Clear technical writing"),
        "simple_transform":     ("claude-haiku-3.5", "Fast, cheap data transforms"),
        "summarization":        ("gemini-2.5-flash", "Fast summarization"),
    }

    def route(self, task_type: str, constraints: RoutingConstraints) -> str:
        """Select the best model for a given task type and constraints."""
        primary, _ = self.ROUTING_TABLE.get(task_type, ("claude-sonnet-4", "default"))

        # Check budget constraints
        if constraints.max_cost_per_call:
            primary = self._find_cheapest_capable(task_type, constraints.max_cost_per_call)

        # Check latency constraints
        if constraints.max_latency_ms and constraints.max_latency_ms < 5000:
            primary = self._find_fastest(task_type)

        # Check rate limits
        if self.rate_limiter.is_throttled(primary):
            primary = self.fallback_chain.get_next(primary)

        return primary
```

### 3.6 FallbackChain

```python
class FallbackChain:
    """Automatic fallback when primary model fails or is unavailable."""

    CHAINS = {
        "claude-opus-4":     ["gpt-4o", "gemini-2.5-pro"],
        "claude-sonnet-4":   ["gpt-4o", "gemini-2.5-pro", "claude-haiku-3.5"],
        "gpt-4o":            ["claude-sonnet-4", "gemini-2.5-pro"],
        "gemini-2.5-pro":    ["claude-opus-4", "gpt-4o"],
        "claude-haiku-3.5":  ["gemini-2.5-flash", "gpt-4o-mini"],
    }

    async def execute_with_fallback(
        self,
        request: LLMRequest,
        providers: Dict[str, LLMProvider],
    ) -> LLMResponse:
        """Try primary model, then fall through the chain on failure."""
        chain = [request.model] + self.CHAINS.get(request.model, [])
        last_error = None

        for model in chain:
            provider = self._get_provider_for_model(model, providers)
            if provider is None:
                continue
            try:
                modified_request = request.copy(model=model)
                response = await provider.complete(modified_request)
                if model != request.model:
                    logger.warning(f"Fell back from {request.model} to {model}")
                return response
            except (RateLimitError, ServiceUnavailableError, TimeoutError) as e:
                last_error = e
                logger.warning(f"Model {model} failed: {e}, trying next")
                continue
            except InvalidRequestError:
                raise  # Don't fallback on bad requests

        raise AllModelsFailedError(f"All models in chain failed. Last: {last_error}")
```

### 3.7 TokenBudgetManager

```python
class TokenBudgetManager:
    """Per-agent token budgeting with real-time tracking."""

    def __init__(self, global_budget: int, agent_budgets: Dict[str, int]):
        self.global_budget = global_budget
        self.agent_budgets = agent_budgets       # max tokens per agent
        self.usage = defaultdict(int)             # actual usage per agent
        self._lock = asyncio.Lock()

    async def check_budget(self, agent_id: str, estimated_tokens: int) -> BudgetDecision:
        """Check if agent has sufficient budget for the request."""
        async with self._lock:
            current = self.usage[agent_id]
            limit = self.agent_budgets.get(agent_id, float('inf'))
            remaining = limit - current

            if estimated_tokens > remaining:
                return BudgetDecision(
                    allowed=False,
                    remaining=remaining,
                    suggestion=self._suggest_alternative(agent_id, estimated_tokens),
                )
            return BudgetDecision(allowed=True, remaining=remaining - estimated_tokens)

    async def record_usage(self, agent_id: str, usage: TokenUsage):
        """Record actual token usage after a completion."""
        async with self._lock:
            self.usage[agent_id] += usage.total_tokens
            self.global_usage += usage.total_tokens

            # Check alert thresholds
            if self.usage[agent_id] > self.agent_budgets.get(agent_id, 0) * 0.8:
                self.event_bus.emit(BudgetWarning(agent_id, usage_pct=80))

    # Default agent budgets (tokens)
    DEFAULT_BUDGETS = {
        "orchestrator":   500_000,
        "planner":        300_000,
        "researcher":     800_000,    # needs large context for research
        "architect":      400_000,
        "designer":       300_000,
        "frontend_dev":   1_000_000,  # code generation is token-heavy
        "backend_dev":    1_000_000,
        "middleware_dev":  500_000,
        "infra_eng":      300_000,
        "security":       400_000,
        "reviewer":       500_000,
        "tester":         600_000,
        "debugger":       800_000,    # may iterate multiple times
        "doc_writer":     400_000,
    }
```

### 3.8 CostTracker

```python
class CostTracker:
    """Real-time cost tracking and alerting."""

    def __init__(self, alert_thresholds: List[CostThreshold]):
        self.total_cost_usd = 0.0
        self.cost_by_agent: Dict[str, float] = defaultdict(float)
        self.cost_by_model: Dict[str, float] = defaultdict(float)
        self.cost_by_provider: Dict[str, float] = defaultdict(float)
        self.cost_history: List[CostEntry] = []
        self.alert_thresholds = alert_thresholds

    def record(self, agent_id: str, model: str, provider: str, usage: TokenUsage):
        """Record a cost entry and check thresholds."""
        cost = usage.cost_usd
        self.total_cost_usd += cost
        self.cost_by_agent[agent_id] += cost
        self.cost_by_model[model] += cost
        self.cost_by_provider[provider] += cost
        self.cost_history.append(CostEntry(
            timestamp=datetime.utcnow(),
            agent_id=agent_id,
            model=model,
            cost_usd=cost,
            tokens=usage.total_tokens,
        ))

        # Check thresholds
        for threshold in self.alert_thresholds:
            if self.total_cost_usd >= threshold.amount_usd and not threshold.triggered:
                threshold.triggered = True
                self.event_bus.emit(CostAlert(
                    total=self.total_cost_usd,
                    threshold=threshold.amount_usd,
                    action=threshold.action,  # "warn", "pause", "abort"
                ))

    def get_report(self) -> CostReport:
        """Generate a cost breakdown report."""
        return CostReport(
            total_cost_usd=self.total_cost_usd,
            by_agent=dict(self.cost_by_agent),
            by_model=dict(self.cost_by_model),
            by_provider=dict(self.cost_by_provider),
            history=self.cost_history,
        )
```

### 3.9 RateLimiter

```python
class RateLimiter:
    """Per-provider rate limit management using token bucket algorithm."""

    def __init__(self, provider_limits: Dict[str, ProviderRateLimit]):
        self.buckets: Dict[str, TokenBucket] = {}
        for provider, limits in provider_limits.items():
            self.buckets[provider] = TokenBucket(
                capacity=limits.requests_per_minute,
                refill_rate=limits.requests_per_minute / 60.0,  # per second
                tokens_capacity=limits.tokens_per_minute,
                tokens_refill_rate=limits.tokens_per_minute / 60.0,
            )

    async def acquire(self, provider: str, estimated_tokens: int) -> RateLimitResult:
        """Acquire rate limit tokens. Blocks if necessary."""
        bucket = self.buckets[provider]

        if bucket.try_consume(1, estimated_tokens):
            return RateLimitResult(allowed=True, wait_ms=0)

        # Calculate wait time
        wait_ms = bucket.time_until_available(1, estimated_tokens)
        if wait_ms < 5000:  # Wait up to 5 seconds
            await asyncio.sleep(wait_ms / 1000)
            bucket.consume(1, estimated_tokens)
            return RateLimitResult(allowed=True, wait_ms=wait_ms)

        return RateLimitResult(allowed=False, wait_ms=wait_ms)


class TokenBucket:
    """Token bucket rate limiter with dual tracking (requests + tokens)."""

    def __init__(self, capacity: int, refill_rate: float,
                 tokens_capacity: int, tokens_refill_rate: float):
        self.request_tokens = capacity
        self.request_capacity = capacity
        self.request_refill_rate = refill_rate
        self.token_tokens = tokens_capacity
        self.token_capacity = tokens_capacity
        self.token_refill_rate = tokens_refill_rate
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def try_consume(self, requests: int, tokens: int) -> bool:
        self._refill()
        if self.request_tokens >= requests and self.token_tokens >= tokens:
            self.request_tokens -= requests
            self.token_tokens -= tokens
            return True
        return False

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.request_tokens = min(
            self.request_capacity,
            self.request_tokens + elapsed * self.request_refill_rate
        )
        self.token_tokens = min(
            self.token_capacity,
            self.token_tokens + elapsed * self.token_refill_rate
        )
        self.last_refill = now
```

### 3.10 Multi-LLM Data Flow

```
  Agent requests completion
          |
          v
  +-------+--------+
  | ModelRouter     |  Selects optimal model based on task type
  +-------+--------+
          |
          v
  +-------+---------+
  | TokenBudgetMgr  |  Checks agent has sufficient budget
  +-------+---------+
          |
          v
  +-------+--------+
  | RateLimiter     |  Acquires rate limit tokens (may wait)
  +-------+--------+
          |
          v
  +-------+--------+
  | FallbackChain   |  Tries primary model, falls back on failure
  +-------+--------+
          |
          v
  +-------+--------+
  | LLMProvider     |  Sends request to provider API
  +-------+--------+
          |
          v
  +-------+--------+
  | CostTracker     |  Records cost, checks alert thresholds
  +-------+--------+
          |
          v
  +-------+---------+
  | TokenBudgetMgr  |  Records actual token usage
  +-------+---------+
          |
          v
  Return LLMResponse to Agent
```

---

## 4. CLI Agent Integration Design

### 4.1 Overview

CodeBot leverages existing CLI-based AI coding agents (Claude Code, Codex CLI, Gemini CLI)
as execution backends for development tasks. The CLI Agent Integration layer provides a
unified interface for spawning, managing, and collecting output from these CLI processes,
each running in an isolated git worktree.

### 4.2 Architecture

```
+-------------------------------------------------------------------+
|                      CLIAgentRunner                               |
|-------------------------------------------------------------------|
| - agent_type: CLIAgentType (claude_code | codex | gemini)         |
| - worktree_mgr: WorktreeManager                                  |
| - output_parser: OutputParser                                     |
| - session_mgr: SessionManager                                    |
| - health_checker: HealthChecker                                   |
|-------------------------------------------------------------------|
| + run(task: CLITask) -> CLIResult                                 |
| + run_interactive(task: CLITask) -> AsyncIterator[CLIEvent]       |
| + cancel(session_id: str) -> None                                 |
| + get_status(session_id: str) -> SessionStatus                    |
+-------------------------------------------------------------------+
         |               |               |
         v               v               v
+----------------+ +-------------+ +----------------+
| ClaudeCodeAdp  | | CodexAdapt  | | GeminiCLIAdapt |
+----------------+ +-------------+ +----------------+
| - binary: str  | | - binary    | | - binary       |
| - flags: []    | | - flags: [] | | - flags: []    |
+----------------+ +-------------+ +----------------+
```

### 4.3 CLIAgentRunner

```python
class CLIAgentType(Enum):
    CLAUDE_CODE = "claude-code"
    CODEX_CLI = "codex"
    GEMINI_CLI = "gemini"

@dataclass
class CLITask:
    prompt: str
    working_dir: str
    files_context: List[str]       # files to preload as context
    allowed_tools: List[str]       # tools the CLI agent can use
    timeout_seconds: int = 600
    max_tokens: int = 100_000
    environment: Dict[str, str] = field(default_factory=dict)

@dataclass
class CLIResult:
    session_id: str
    exit_code: int
    stdout: str
    stderr: str
    files_modified: List[str]
    files_created: List[str]
    duration_seconds: float
    token_usage: Optional[TokenUsage]
    structured_output: Optional[dict]  # parsed from output


class CLIAgentRunner:
    """Unified interface for running CLI-based AI coding agents."""

    def __init__(self, agent_type: CLIAgentType, config: CLIConfig):
        self.agent_type = agent_type
        self.adapter = self._create_adapter(agent_type)
        self.worktree_mgr = WorktreeManager(config.repo_path)
        self.output_parser = OutputParser()
        self.session_mgr = SessionManager()
        self.health_checker = HealthChecker()

    async def run(self, task: CLITask) -> CLIResult:
        """Execute a task using the CLI agent in an isolated worktree."""
        # 1. Create isolated worktree
        worktree = await self.worktree_mgr.acquire(task.branch_name)

        # 2. Build the command
        cmd = self.adapter.build_command(task, worktree.path)

        # 3. Start the process
        session = await self.session_mgr.create(cmd, worktree, task.timeout_seconds)

        # 4. Monitor execution
        self.health_checker.register(session)

        try:
            # 5. Wait for completion
            exit_code, stdout, stderr = await session.wait()

            # 6. Parse structured output
            structured = self.output_parser.parse(stdout, stderr)

            # 7. Collect file changes
            files_modified, files_created = await worktree.get_changes()

            return CLIResult(
                session_id=session.id,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                files_modified=files_modified,
                files_created=files_created,
                duration_seconds=session.duration,
                structured_output=structured,
            )
        finally:
            self.health_checker.unregister(session)
            await self.worktree_mgr.release(worktree)
```

### 4.4 WorktreeManager

```python
class WorktreeManager:
    """Manages git worktrees for isolated agent execution."""

    def __init__(self, repo_path: str, pool_size: int = 5):
        self.repo_path = repo_path
        self.pool_size = pool_size
        self.pool: List[Worktree] = []
        self.active: Dict[str, Worktree] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, branch_name: str) -> Worktree:
        """Acquire a worktree from the pool or create a new one."""
        async with self._lock:
            # Try to reuse from pool
            if self.pool:
                wt = self.pool.pop()
                await wt.checkout(branch_name)
                self.active[wt.id] = wt
                return wt

            # Create new worktree
            wt_path = os.path.join(self.repo_path, ".worktrees", f"agent-{uuid4().hex[:8]}")
            result = await run_cmd(
                f"git worktree add {wt_path} -b {branch_name}"
            )
            wt = Worktree(id=uuid4().hex, path=wt_path, branch=branch_name)
            self.active[wt.id] = wt
            return wt

    async def release(self, worktree: Worktree):
        """Return a worktree to the pool or destroy it."""
        async with self._lock:
            del self.active[worktree.id]
            if len(self.pool) < self.pool_size:
                await worktree.clean()  # git clean -fd && git checkout main
                self.pool.append(worktree)
            else:
                await self._destroy(worktree)

    async def _destroy(self, worktree: Worktree):
        """Remove a worktree completely."""
        await run_cmd(f"git worktree remove {worktree.path} --force")
```

### 4.5 OutputParser

```python
class OutputParser:
    """Extracts structured output from CLI agent stdout/stderr."""

    # Patterns for extracting structured data from CLI output
    PATTERNS = {
        "json_block": re.compile(r'```json\n(.*?)\n```', re.DOTALL),
        "file_created": re.compile(r'(?:Created|Wrote)\s+(?:file\s+)?[`"]?([^\s`"]+)[`"]?'),
        "file_modified": re.compile(r'(?:Modified|Updated|Edited)\s+[`"]?([^\s`"]+)[`"]?'),
        "error": re.compile(r'(?:Error|ERROR|FATAL):\s*(.+)'),
        "test_result": re.compile(r'(\d+)\s+passed.*?(\d+)\s+failed'),
        "token_usage": re.compile(r'Tokens?:\s*(\d+)\s*/\s*(\d+)'),
    }

    def parse(self, stdout: str, stderr: str) -> ParsedOutput:
        """Parse CLI output into structured data."""
        result = ParsedOutput()

        # Extract JSON blocks (agents often output structured JSON)
        json_matches = self.PATTERNS["json_block"].findall(stdout)
        for match in json_matches:
            try:
                result.json_outputs.append(json.loads(match))
            except json.JSONDecodeError:
                pass

        # Extract file operations
        result.files_created = self.PATTERNS["file_created"].findall(stdout)
        result.files_modified = self.PATTERNS["file_modified"].findall(stdout)

        # Extract errors
        result.errors = self.PATTERNS["error"].findall(stderr)

        # Extract test results
        test_match = self.PATTERNS["test_result"].search(stdout)
        if test_match:
            result.tests_passed = int(test_match.group(1))
            result.tests_failed = int(test_match.group(2))

        return result
```

### 4.6 SessionManager

```python
class SessionManager:
    """Manages long-running CLI agent sessions."""

    def __init__(self):
        self.sessions: Dict[str, CLISession] = {}

    async def create(
        self,
        cmd: List[str],
        worktree: Worktree,
        timeout: int,
    ) -> CLISession:
        """Create and start a new CLI session."""
        session = CLISession(
            id=uuid4().hex,
            process=None,
            worktree=worktree,
            started_at=datetime.utcnow(),
            timeout=timeout,
            status=SessionStatus.STARTING,
        )

        # Start the subprocess
        session.process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=worktree.path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._build_env(worktree),
        )
        session.status = SessionStatus.RUNNING
        self.sessions[session.id] = session

        return session

    async def cancel(self, session_id: str):
        """Gracefully cancel a running session."""
        session = self.sessions.get(session_id)
        if session and session.process:
            session.process.send_signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(session.process.wait(), timeout=10)
            except asyncio.TimeoutError:
                session.process.kill()
            session.status = SessionStatus.CANCELLED
```

### 4.7 HealthChecker

```python
class HealthChecker:
    """Monitors CLI agent process health."""

    def __init__(self, check_interval_seconds: int = 10):
        self.check_interval = check_interval_seconds
        self.monitored: Dict[str, CLISession] = {}
        self._task: Optional[asyncio.Task] = None

    def register(self, session: CLISession):
        """Start monitoring a session."""
        self.monitored[session.id] = session
        if self._task is None:
            self._task = asyncio.create_task(self._monitor_loop())

    def unregister(self, session: CLISession):
        """Stop monitoring a session."""
        self.monitored.pop(session.id, None)

    async def _monitor_loop(self):
        """Periodic health check loop."""
        while self.monitored:
            for session_id, session in list(self.monitored.items()):
                health = await self._check_health(session)
                if health.status == HealthStatus.UNHEALTHY:
                    self.event_bus.emit(SessionUnhealthy(session_id, health.reason))
                elif health.status == HealthStatus.TIMEOUT:
                    await self.session_mgr.cancel(session_id)
                    self.event_bus.emit(SessionTimeout(session_id))
            await asyncio.sleep(self.check_interval)

    async def _check_health(self, session: CLISession) -> HealthResult:
        """Check individual session health."""
        # Check if process is still alive
        if session.process.returncode is not None:
            return HealthResult(HealthStatus.COMPLETED)

        # Check timeout
        elapsed = (datetime.utcnow() - session.started_at).total_seconds()
        if elapsed > session.timeout:
            return HealthResult(HealthStatus.TIMEOUT, "Session exceeded timeout")

        # Check memory usage (platform-specific)
        try:
            proc = psutil.Process(session.process.pid)
            mem_mb = proc.memory_info().rss / (1024 * 1024)
            if mem_mb > 2048:  # 2GB limit
                return HealthResult(HealthStatus.UNHEALTHY, f"Memory: {mem_mb:.0f}MB")
        except psutil.NoSuchProcess:
            return HealthResult(HealthStatus.COMPLETED)

        return HealthResult(HealthStatus.HEALTHY)
```

### 4.8 CLI Agent Integration Sequence

```
  Agent Layer                 CLIAgentRunner         WorktreeManager       Process
      |                            |                       |                  |
      |-- run(CLITask) ----------->|                       |                  |
      |                            |-- acquire(branch) --->|                  |
      |                            |<-- Worktree ----------|                  |
      |                            |                       |                  |
      |                            |-- build_command() --->|                  |
      |                            |-- create_session() ---|-- spawn -------->|
      |                            |                       |                  |
      |                            |-- health_check -------|---- monitor ---->|
      |                            |          ...          |       ...        |
      |                            |<-- stdout/stderr -----|<-- output -------|
      |                            |                       |                  |
      |                            |-- parse_output() ---->|                  |
      |                            |-- get_changes() ----->|                  |
      |                            |-- release(worktree) ->|                  |
      |<-- CLIResult --------------|                       |                  |
      |                            |                       |                  |
```

---

## 5. Context Management System Design

### 5.1 Overview

The Context Management System implements MASFactory's Context Adapter pattern as a
**built-in feature** of CodeBot. It ensures each agent receives precisely the context it
needs -- no more, no less. This is critical for managing token budgets and ensuring agents
have relevant information without overwhelming their context windows.

**Key built-in capabilities:**

- **L0/L1/L2 hierarchical context** (inspired by OpenViking patterns): a built-in
  three-tier loading system that provides always-available project summaries (L0),
  on-demand code/doc retrieval (L1), and RAG-based semantic search (L2). Context sources
  are backed by **SQLite + file tree** (context store).
- **Episodic memory** (inspired by claude-mem patterns): a built-in persistent memory
  system with lifecycle hooks (on_task_start, on_task_complete, on_pipeline_end), semantic
  compression of stale memories, and progressive disclosure (summary -> full -> linked).
  Episodic memory is backed by **LanceDB (dev) / Qdrant (prod) + SQLite**.
- **CLI agent integrations** (Claude Code, Codex CLI, Gemini CLI) remain mandatory
  external integrations for code generation and development tasks.

### 5.2 Architecture

```
+-----------------------------------------------------------------------+
|                       ContextManagementSystem                        |
|-----------------------------------------------------------------------|
|                                                                       |
|  +------------------+    +------------------+    +-----------------+  |
|  | ContextAdapter   |    | MemoryManager    |    | VectorStore     |  |
|  | (unified iface)  |    | (persistent mem) |    | (embeddings)    |  |
|  +--------+---------+    +--------+---------+    +--------+--------+  |
|           |                       |                       |           |
|  +--------+---------+    +--------+---------+    +--------+--------+  |
|  | Three-Tier       |    | CodeIndexer      |    | ContextCompress |  |
|  | Loader           |    | (Tree-sitter)    |    | (summarization) |  |
|  +--------+---------+    +--------+---------+    +--------+--------+  |
|           |                       |                       |           |
|  +--------+---------+                                                 |
|  | MCPIntegration   |                                                 |
|  | (tool/resource)  |                                                 |
|  +------------------+                                                 |
+-----------------------------------------------------------------------+
```

### 5.3 ContextAdapter

```python
class ContextAdapter:
    """
    Unified context interface following MASFactory's Context Adapter pattern.

    Each agent receives a ContextAdapter instance that assembles the right
    context based on the agent's role, current task, and available budget.
    """

    def __init__(
        self,
        agent_role: AgentRole,
        token_budget: int,
        loader: ThreeTierLoader,
        memory: MemoryManager,
        vector_store: VectorStore,
        code_indexer: CodeIndexer,
        compressor: ContextCompressor,
    ):
        self.agent_role = agent_role
        self.token_budget = token_budget
        self.loader = loader
        self.memory = memory
        self.vector_store = vector_store
        self.code_indexer = code_indexer
        self.compressor = compressor

    async def build_context(self, task: Task) -> AgentContext:
        """
        Assemble context for an agent's task execution.

        Priority order:
        1. L0: Always-loaded project summary (always included)
        2. Task-specific data from shared state
        3. L1: On-demand code/docs relevant to the task
        4. L2: RAG-retrieved context from vector store
        5. Persistent memory from prior executions
        6. Compressed conversation history
        """
        context = AgentContext(budget=self.token_budget)

        # L0: Always loaded (small, essential project summary)
        l0 = await self.loader.load_l0()
        context.add(l0, priority=Priority.CRITICAL)

        # Task data from shared state
        task_data = self._extract_task_context(task)
        context.add(task_data, priority=Priority.HIGH)

        # L1: On-demand loading of relevant code files
        relevant_files = await self.code_indexer.find_relevant(task.description)
        for file_ctx in relevant_files:
            if context.has_budget():
                l1 = await self.loader.load_l1(file_ctx.path)
                context.add(l1, priority=Priority.MEDIUM)

        # L2: RAG retrieval for broader context
        if context.has_budget():
            rag_results = await self.vector_store.query(
                query=task.description,
                top_k=5,
                filter={"project_id": task.project_id},
            )
            for result in rag_results:
                context.add(result.content, priority=Priority.LOW)

        # Persistent memory
        if context.has_budget():
            memories = await self.memory.recall(
                agent_role=self.agent_role,
                task_type=task.type,
                limit=10,
            )
            context.add_memories(memories)

        # Compress if over budget
        if context.is_over_budget():
            context = await self.compressor.compress(context)

        return context
```

### 5.4 Three-Tier Context Loading

```
+---------------------------------------------------------------+
|                    Three-Tier Loading                          |
|---------------------------------------------------------------|
|                                                               |
|  Tier L0: Always Loaded (< 2K tokens)                        |
|  +----------------------------------------------------------+|
|  | - Project name, description, tech stack                   ||
|  | - Directory structure (top 2 levels)                      ||
|  | - Key configuration files (package.json, pyproject.toml)  ||
|  | - Coding conventions summary                              ||
|  | - Current pipeline phase and status                       ||
|  +----------------------------------------------------------+|
|                                                               |
|  Tier L1: On-Demand (loaded per-task, < 20K tokens)          |
|  +----------------------------------------------------------+|
|  | - Specific source files relevant to current task          ||
|  | - API contract definitions                                ||
|  | - Test files for modules being modified                   ||
|  | - Architecture decision records                           ||
|  | - Recent git diff context                                 ||
|  +----------------------------------------------------------+|
|                                                               |
|  Tier L2: RAG Retrieval (semantic search, < 10K tokens)      |
|  +----------------------------------------------------------+|
|  | - Similar code patterns from codebase                     ||
|  | - Relevant documentation chunks                           ||
|  | - Past conversation excerpts                              ||
|  | - External reference material                             ||
|  | - Stack Overflow / GitHub issues                          ||
|  +----------------------------------------------------------+|
+---------------------------------------------------------------+
```

```python
class ThreeTierLoader:
    """Three-tier context loading system."""

    async def load_l0(self) -> L0Context:
        """Load always-available project summary."""
        return L0Context(
            project_summary=await self._read_file(".codebot/project_summary.md"),
            directory_tree=await self._get_dir_tree(max_depth=2),
            tech_stack=await self._detect_tech_stack(),
            conventions=await self._read_file(".codebot/conventions.md"),
            pipeline_status=await self._get_pipeline_status(),
        )

    async def load_l1(self, file_path: str) -> L1Context:
        """Load specific file content on demand."""
        content = await self._read_file(file_path)
        # If file is too large, extract only relevant sections
        if self._estimate_tokens(content) > 5000:
            content = await self.code_indexer.extract_relevant_sections(
                file_path, self.current_task
            )
        return L1Context(path=file_path, content=content)
```

### 5.5 MemoryManager

```python
class MemoryManager:
    """
    CodeBot's built-in episodic memory system (inspired by claude-mem patterns).

    Provides persistent, semantically-searchable memory with lifecycle hooks,
    semantic compression, and progressive disclosure. Memory is backed by
    LanceDB/Qdrant + SQLite for fast hybrid retrieval (recency + semantic similarity).

    Memory is organized hierarchically:
      .codebot/memory/
        /{project_id}/
          /agents/{agent_role}/
            /decisions.jsonl      # architectural decisions made
            /learnings.jsonl      # lessons learned from failures
            /preferences.jsonl    # user preferences observed
          /shared/
            /project_knowledge.jsonl
            /code_patterns.jsonl

    Lifecycle hooks:
      - on_task_start: preload relevant memories for the agent's role
      - on_task_complete: auto-extract learnings and decisions
      - on_pipeline_end: run semantic compression on accumulated memories

    Semantic compression periodically consolidates redundant or low-value
    memories into summary entries, keeping the memory store lean.

    Progressive disclosure surfaces memories at increasing detail levels:
      - L0: one-line summary (always shown)
      - L1: full entry with context (loaded on demand)
      - L2: linked related memories and source artifacts (deep retrieval)
    """

    def __init__(self, base_path: str, db_path: str = ".codebot/memory.db"):
        self.base_path = base_path
        self.db = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self):
        """Initialize SQLite schema for memory metadata and fast lookups."""
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                agent_role TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                content TEXT NOT NULL,
                project_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                compressed INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_memories_role ON memories(agent_role);
            CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_id);
        """)

    async def remember(self, entry: MemoryEntry):
        """Store a new memory entry in SQLite + vector store."""
        # Persist to SQLite for fast structured queries
        self.db.execute(
            "INSERT OR REPLACE INTO memories VALUES (?,?,?,?,?,?,?,0,0)",
            (entry.id, entry.agent_role, entry.category,
             entry.summary, entry.content, entry.project_id,
             entry.timestamp.isoformat()),
        )
        self.db.commit()

        # Also persist to hierarchical file store
        path = self._get_path(entry.agent_role, entry.category)
        async with aiofiles.open(path, 'a') as f:
            await f.write(json.dumps(entry.to_dict()) + '\n')

        # Index in vector store (LanceDB/Qdrant) for semantic retrieval
        await self.vector_store.upsert(
            id=entry.id,
            content=entry.content,
            metadata={
                "agent_role": entry.agent_role,
                "category": entry.category,
                "timestamp": entry.timestamp.isoformat(),
                "project_id": entry.project_id,
            },
        )

    async def recall(
        self,
        agent_role: str,
        task_type: str,
        limit: int = 10,
    ) -> List[MemoryEntry]:
        """Retrieve relevant memories using hybrid retrieval (recency + semantic)."""
        # Recency-based from SQLite
        recent = await self._get_recent(agent_role, limit=5)
        # Semantic from LanceDB/Qdrant vector store
        semantic = await self.vector_store.query(
            query=task_type,
            filter={"agent_role": agent_role},
            top_k=limit,
        )
        # Deduplicate and rank
        combined = self._merge_and_rank(recent, semantic)
        return combined[:limit]

    async def compress(self, project_id: str):
        """Semantic compression: consolidate redundant memories into summaries."""
        stale = self.db.execute(
            "SELECT id, content FROM memories WHERE project_id=? AND compressed=0 "
            "ORDER BY created_at ASC LIMIT 50",
            (project_id,),
        ).fetchall()
        if len(stale) < 10:
            return  # not enough to compress
        # Group similar memories and produce summary entries
        clusters = await self._cluster_memories(stale)
        for cluster in clusters:
            summary = await self._summarize_cluster(cluster)
            await self.remember(summary)
            for mem_id in cluster.member_ids:
                self.db.execute(
                    "UPDATE memories SET compressed=1 WHERE id=?", (mem_id,)
                )
        self.db.commit()
```

### 5.6 VectorStore

```python
class VectorStore:
    """Embedding and retrieval via LanceDB (dev) or Qdrant (prod)."""

    def __init__(self, backend: str = "lancedb", persist_dir: str = ".codebot/vectors"):
        if backend == "lancedb":
            self.client = lancedb.connect(persist_dir)
        elif backend == "qdrant":
            self.client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    async def upsert(self, id: str, content: str, metadata: dict):
        """Insert or update a document in the vector store."""
        embedding = self.embedder.encode(content).tolist()
        collection = self.client.get_or_create_collection("codebot")
        collection.upsert(
            ids=[id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
        )

    async def query(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[dict] = None,
    ) -> List[VectorResult]:
        """Query the vector store for similar documents."""
        query_embedding = self.embedder.encode(query).tolist()
        collection = self.client.get_collection("codebot")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter,
        )
        return [
            VectorResult(
                id=results["ids"][0][i],
                content=results["documents"][0][i],
                metadata=results["metadatas"][0][i],
                distance=results["distances"][0][i],
            )
            for i in range(len(results["ids"][0]))
        ]
```

### 5.7 CodeIndexer

```python
class CodeIndexer:
    """Tree-sitter based code understanding and semantic indexing."""

    SUPPORTED_LANGUAGES = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "tsx", ".jsx": "javascript", ".rs": "rust",
        ".go": "go", ".java": "java", ".rb": "ruby",
        ".cpp": "cpp", ".c": "c", ".cs": "c_sharp",
    }

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.index: Dict[str, CodeSymbol] = {}
        self.parsers: Dict[str, Parser] = {}

    async def build_index(self):
        """Build a semantic index of the entire codebase."""
        for root, _, files in os.walk(self.project_path):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in self.SUPPORTED_LANGUAGES:
                    path = os.path.join(root, file)
                    symbols = await self._parse_file(path, ext)
                    for symbol in symbols:
                        self.index[symbol.qualified_name] = symbol

    async def _parse_file(self, path: str, ext: str) -> List[CodeSymbol]:
        """Parse a file and extract symbols using Tree-sitter."""
        lang = self.SUPPORTED_LANGUAGES[ext]
        parser = self._get_parser(lang)

        async with aiofiles.open(path, 'r') as f:
            source = await f.read()

        tree = parser.parse(bytes(source, 'utf-8'))
        symbols = []

        # Extract functions, classes, methods, imports
        query = self._get_symbol_query(lang)
        captures = query.captures(tree.root_node)

        for node, name in captures:
            symbols.append(CodeSymbol(
                name=self._extract_name(node),
                kind=self._node_to_kind(name),
                file_path=path,
                line_start=node.start_point[0],
                line_end=node.end_point[0],
                signature=self._extract_signature(node, source),
                docstring=self._extract_docstring(node, source),
                references=[],  # populated in a second pass
            ))

        return symbols

    async def find_relevant(self, query: str, top_k: int = 10) -> List[CodeSymbol]:
        """Find code symbols relevant to a natural language query."""
        # Combine keyword matching with semantic similarity
        keyword_matches = self._keyword_search(query)
        semantic_matches = await self.vector_store.query(
            query=query,
            filter={"type": "code_symbol"},
            top_k=top_k,
        )
        return self._merge_results(keyword_matches, semantic_matches)
```

### 5.8 ContextCompressor

```python
class ContextCompressor:
    """Automatic summarization of long conversations and context."""

    def __init__(self, llm: LLMProvider, target_ratio: float = 0.3):
        self.llm = llm
        self.target_ratio = target_ratio  # compress to 30% of original

    async def compress(self, context: AgentContext) -> AgentContext:
        """Compress context to fit within token budget."""
        if not context.is_over_budget():
            return context

        # Strategy 1: Remove low-priority items first
        context.remove_items_by_priority(Priority.LOW)
        if not context.is_over_budget():
            return context

        # Strategy 2: Summarize medium-priority items
        medium_items = context.get_items_by_priority(Priority.MEDIUM)
        for item in medium_items:
            summary = await self._summarize(item.content)
            context.replace_item(item.id, summary)
        if not context.is_over_budget():
            return context

        # Strategy 3: Aggressive summarization of all non-critical items
        non_critical = context.get_items_by_priority(
            Priority.MEDIUM, Priority.HIGH
        )
        combined = "\n---\n".join(item.content for item in non_critical)
        mega_summary = await self._summarize(combined, aggressive=True)
        context.replace_items(non_critical, mega_summary)

        return context

    async def _summarize(self, content: str, aggressive: bool = False) -> str:
        """Use a fast LLM to summarize content."""
        ratio = 0.1 if aggressive else self.target_ratio
        max_tokens = int(len(content.split()) * ratio)

        response = await self.llm.complete(LLMRequest(
            messages=[
                Message(role="system", content=(
                    "Summarize the following technical content. "
                    "Preserve all critical details: function signatures, "
                    "data structures, error conditions, and decisions made."
                )),
                Message(role="user", content=content),
            ],
            model="gemini-2.5-flash",  # fast and cheap for summarization
            max_tokens=max_tokens,
        ))
        return response.content
```

### 5.9 MCPIntegration

```python
class MCPIntegration:
    """Model Context Protocol integration for tool and resource injection."""

    def __init__(self, config: MCPConfig):
        self.servers: Dict[str, MCPServer] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}

    async def initialize(self, server_configs: List[MCPServerConfig]):
        """Connect to MCP servers and discover tools/resources."""
        for config in server_configs:
            server = await MCPServer.connect(
                name=config.name,
                command=config.command,
                args=config.args,
                env=config.env,
            )
            self.servers[config.name] = server

            # Discover available tools
            tools = await server.list_tools()
            for tool in tools:
                self.tools[f"{config.name}.{tool.name}"] = tool

            # Discover available resources
            resources = await server.list_resources()
            for resource in resources:
                self.resources[f"{config.name}.{resource.uri}"] = resource

    async def invoke_tool(self, tool_name: str, args: dict) -> ToolResult:
        """Invoke an MCP tool by name."""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ToolNotFoundError(f"MCP tool '{tool_name}' not found")
        server_name = tool_name.split(".")[0]
        return await self.servers[server_name].call_tool(tool.name, args)

    async def read_resource(self, uri: str) -> ResourceContent:
        """Read an MCP resource by URI."""
        resource = self.resources.get(uri)
        if not resource:
            raise ResourceNotFoundError(f"MCP resource '{uri}' not found")
        server_name = uri.split(".")[0]
        return await self.servers[server_name].read_resource(resource.uri)

    def get_tools_for_agent(self, agent_role: AgentRole) -> List[MCPTool]:
        """Return MCP tools available for a specific agent role."""
        role_tools = AGENT_MCP_TOOLS.get(agent_role, [])
        return [self.tools[t] for t in role_tools if t in self.tools]
```

### 5.10 Context Flow Diagram

```
  +------------------+
  |    Agent Task     |
  +--------+---------+
           |
           v
  +--------+---------+     +------------------+
  |  ContextAdapter   |---->|  L0: Project     |  Always loaded (~2K tokens)
  |                   |     |  Summary         |
  |  Assembles the    |     +------------------+
  |  right context    |
  |  for the agent    |---->|  L1: On-Demand   |  Loaded per-task (~20K tokens)
  |  based on role    |     |  Code/Docs       |
  |  and budget       |     +------------------+
  |                   |
  |                   |---->|  L2: RAG         |  Semantic search (~10K tokens)
  |                   |     |  Retrieval       |
  |                   |     +------------------+
  +--------+---------+
           |
           v
  +--------+---------+     +------------------+
  | ContextCompressor |---->| Summarization    |  If over budget
  +--------+---------+     +------------------+
           |
           v
  +--------+---------+
  |  Final Context    |  Fits within agent's token budget
  +------------------+
```

---

## 6. Pipeline Orchestration Design

### 6.1 Overview

The Pipeline Orchestration system manages the end-to-end execution of the SDLC pipeline,
handling phase transitions, parallel execution, checkpointing, human gates, and error
escalation. It bridges the high-level graph engine with the concrete agent executions.

### 6.2 Pipeline Definition

```yaml
# Example pipeline definition: sdlc-pipeline.yaml
pipeline:
  name: "full-sdlc"
  version: "1.0"
  description: "Complete software development lifecycle"

  settings:
    max_parallel_agents: 5
    checkpoint_after_each_phase: true
    cost_limit_usd: 50.00
    timeout_minutes: 120

  phases:
    # S0: Project Initialization
    - name: "initialize"
      agents: ["orchestrator"]
      sequential: true
      human_gate: false

    # S1: Discovery & Brainstorming
    - name: "brainstorm"
      agents: ["brainstorm"]
      sequential: true
      human_gate: false

    # S2: Research & Analysis (AFTER brainstorming)
    - name: "research"
      agents: ["researcher"]
      human_gate: false

    # S3: Architecture & Design (AFTER research, parallel agents)
    - name: "design"
      agents: ["architect", "designer"]
      sequential: true
      human_gate: true
      gate_prompt: "Review architecture and design. Approve to proceed?"

    # S4: Planning & Configuration (AFTER architecture)
    - name: "plan"
      agents: ["planner"]
      sequential: true
      human_gate: false

    # S5: Implementation (full parallel)
    - name: "implement"
      agents: ["frontend_dev", "backend_dev", "middleware_dev"]
      sequential: false  # parallel execution
      human_gate: false

    # S6: Quality Assurance (full parallel)
    - name: "qa"
      agents: ["code_reviewer", "security_auditor"]
      sequential: false  # parallel
      human_gate: false
      on_failure: "reroute_to_implement"

    # S7: Testing & Validation (parallel test suites)
    - name: "test"
      agents: ["tester"]
      test_suites:
        - "unit"
        - "integration"
        - "e2e"
        - "ui_component"
        - "smoke"
        - "regression"
        - "mutation"
      human_gate: false

    # S8: Debug & Stabilization
    - name: "fix"
      agents: ["debugger"]
      loop:
        condition: "all_tests_pass AND no_critical_security"
        max_iterations: 5
      on_max_iterations: "escalate_to_human"

    # S9: Documentation & Knowledge
    - name: "document"
      agents: ["doc_writer"]
      sequential: true
      human_gate: false

    # S10: Deployment & Delivery (LAST)
    - name: "deliver"
      agents: ["infra_engineer", "project_manager"]
      sequential: true
      human_gate: true
      gate_prompt: "Review final deliverables. Approve for delivery?"
```

### 6.3 PhaseExecutor

```python
class PhaseExecutor:
    """Manages phase transitions in the SDLC pipeline."""

    def __init__(
        self,
        pipeline: PipelineDefinition,
        graph_engine: ExecutionEngine,
        event_bus: EventBus,
    ):
        self.pipeline = pipeline
        self.graph_engine = graph_engine
        self.event_bus = event_bus
        self.current_phase_idx = 0
        self.checkpoint_mgr = CheckpointManager()

    async def execute_pipeline(self, project: Project) -> PipelineResult:
        """Execute the entire pipeline from start (or resume from checkpoint)."""
        # Check for existing checkpoint
        checkpoint = await self.checkpoint_mgr.load_latest(project.id)
        if checkpoint:
            self.current_phase_idx = checkpoint.phase_idx
            self.state = checkpoint.state
            logger.info(f"Resuming from phase {self.current_phase_idx}")

        results = []
        for idx in range(self.current_phase_idx, len(self.pipeline.phases)):
            phase = self.pipeline.phases[idx]
            self.current_phase_idx = idx
            self.event_bus.emit(PhaseTransition(
                phase_name=phase.name,
                phase_idx=idx,
                status="started",
            ))

            try:
                phase_result = await self._execute_phase(phase, project)
                results.append(phase_result)

                # Checkpoint after phase
                if self.pipeline.settings.checkpoint_after_each_phase:
                    await self.checkpoint_mgr.save(CheckpointData(
                        project_id=project.id,
                        phase_idx=idx + 1,
                        state=self.state,
                        results=results,
                    ))

                self.event_bus.emit(PhaseTransition(
                    phase_name=phase.name,
                    phase_idx=idx,
                    status="completed",
                ))

            except PhaseFailedError as e:
                return PipelineResult(
                    status="failed",
                    failed_phase=phase.name,
                    error=str(e),
                    results=results,
                )

        return PipelineResult(status="completed", results=results)

    async def _execute_phase(self, phase: PhaseConfig, project: Project) -> PhaseResult:
        """Execute a single pipeline phase."""
        if phase.loop:
            return await self._execute_loop_phase(phase, project)

        if phase.sequential:
            return await self._execute_sequential(phase.agents, project)
        else:
            return await self._execute_parallel(phase.agents, project)

    async def _execute_sequential(
        self, agent_names: List[str], project: Project
    ) -> PhaseResult:
        """Execute agents one after another."""
        results = []
        for name in agent_names:
            agent = self.agent_registry.get(name)
            result = await agent.execute(
                AgentInput(project=project, state=self.state)
            )
            self.state.update(result.state_updates)
            results.append(result)
        return PhaseResult(agent_results=results)

    async def _execute_parallel(
        self, agent_names: List[str], project: Project
    ) -> PhaseResult:
        """Execute independent agents concurrently."""
        tasks = []
        for name in agent_names:
            agent = self.agent_registry.get(name)
            tasks.append(agent.execute(
                AgentInput(project=project, state=self.state.snapshot())
            ))
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge state updates (with conflict resolution)
        for result in results:
            if not isinstance(result, Exception):
                self.state.merge(result.state_updates)
        return PhaseResult(agent_results=results)
```

### 6.4 CheckpointManager

```python
class CheckpointManager:
    """Saves and restores pipeline state for resume capability."""

    def __init__(self, storage_path: str = ".codebot/checkpoints"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    async def save(self, data: CheckpointData):
        """Save a checkpoint to disk."""
        filename = f"{data.project_id}_phase{data.phase_idx}_{datetime.utcnow().isoformat()}.json"
        path = os.path.join(self.storage_path, filename)
        async with aiofiles.open(path, 'w') as f:
            await f.write(json.dumps(data.to_dict(), default=str))
        logger.info(f"Checkpoint saved: {filename}")

    async def load_latest(self, project_id: str) -> Optional[CheckpointData]:
        """Load the most recent checkpoint for a project."""
        pattern = f"{project_id}_phase*.json"
        files = sorted(
            glob.glob(os.path.join(self.storage_path, pattern)),
            reverse=True,
        )
        if not files:
            return None
        async with aiofiles.open(files[0], 'r') as f:
            data = json.loads(await f.read())
        return CheckpointData.from_dict(data)
```

### 6.5 HumanGate

```python
class HumanGate:
    """Blocks pipeline for human approval at configurable points."""

    def __init__(self, notification_channels: List[NotificationChannel]):
        self.channels = notification_channels
        self.pending_approvals: Dict[str, ApprovalRequest] = {}

    async def request_approval(
        self,
        gate_id: str,
        prompt: str,
        context: dict,
        timeout_hours: float = 24,
    ) -> ApprovalResult:
        """Request human approval, blocking until received."""
        request = ApprovalRequest(
            id=gate_id,
            prompt=prompt,
            context=context,
            requested_at=datetime.utcnow(),
            timeout=timedelta(hours=timeout_hours),
        )
        self.pending_approvals[gate_id] = request

        # Notify all channels
        for channel in self.channels:
            await channel.notify(request)

        self.event_bus.emit(HumanApprovalRequired(gate_id=gate_id, prompt=prompt))

        # Block until approval, rejection, or timeout
        try:
            result = await asyncio.wait_for(
                self._wait_for_decision(gate_id),
                timeout=timeout_hours * 3600,
            )
            return result
        except asyncio.TimeoutError:
            return ApprovalResult(decision="timeout", gate_id=gate_id)

    async def submit_decision(
        self, gate_id: str, decision: str, feedback: str = ""
    ):
        """Submit a human decision (approve/reject)."""
        request = self.pending_approvals.get(gate_id)
        if request:
            request.decision = decision
            request.feedback = feedback
            request.decided_at = datetime.utcnow()
            request.event.set()  # unblock the waiting coroutine
```

### 6.6 ErrorEscalation

```python
class ErrorEscalation:
    """Escalation strategy when agents fail repeatedly."""

    STRATEGIES = {
        "retry": RetryStrategy,
        "fallback_model": FallbackModelStrategy,
        "simplify_task": SimplifyTaskStrategy,
        "escalate_to_human": HumanEscalationStrategy,
        "abort": AbortStrategy,
    }

    def __init__(self, config: EscalationConfig):
        self.config = config
        self.failure_counts: Dict[str, int] = defaultdict(int)

    async def handle_failure(
        self,
        agent_id: str,
        error: Exception,
        context: ExecutionContext,
    ) -> EscalationResult:
        """Handle an agent failure with progressive escalation."""
        self.failure_counts[agent_id] += 1
        count = self.failure_counts[agent_id]

        # Progressive escalation ladder
        if count <= 2:
            # Level 1: Retry with same configuration
            return await RetryStrategy().execute(agent_id, context)

        elif count <= 4:
            # Level 2: Retry with fallback model
            return await FallbackModelStrategy().execute(agent_id, context)

        elif count <= 5:
            # Level 3: Simplify the task
            return await SimplifyTaskStrategy().execute(agent_id, context)

        else:
            # Level 4: Escalate to human
            return await HumanEscalationStrategy().execute(agent_id, context, error)
```

### 6.7 Pipeline Execution Sequence (v2.2 -- 10-stage)

```
  User                Pipeline        PhaseExecutor     Agents         HumanGate
   |                     |                 |               |               |
   |-- start(req) ------>|                 |               |               |
   |                     |-- execute() --->|               |               |
   |                     |                 |               |               |
   |                     | S0: Initialize  |               |               |
   |                     |                 |-- run ------->| Orchestrator  |
   |                     |                 |<-- result ----|               |
   |                     |                 |-- checkpoint  |               |
   |                     |                 |               |               |
   |                     | S1: Brainstorm  |               |               |
   |                     |                 |-- run ------->| Brainstormer  |
   |                     |                 |<-- result ----|               |
   |                     |                 |-- checkpoint  |               |
   |                     |                 |               |               |
   |                     | S2: Research    |               |               |
   |                     |                 |-- run ------->| Researcher    |
   |                     |                 |<-- result ----|               |
   |                     |                 |-- checkpoint  |               |
   |                     |                 |               |               |
   |                     | S3: Design      |               |               |
   |                     |                 |-- run ------->| Architect     |
   |                     |                 |<-- result ----|               |
   |                     |                 |-- run ------->| Designer      |
   |                     |                 |<-- result ----|               |
   |                     |                 |-- gate -------|-------------->|
   |<--- approval req ---|-----------------|---------------|---------------|
   |--- approve -------->|-----------------|---------------|-------------->|
   |                     |                 |<-- approved --|---------------|
   |                     |                 |               |               |
   |                     | S4: Plan        |               |               |
   |                     |                 |-- run ------->| Planner       |
   |                     |                 |<-- result ----|               |
   |                     |                 |-- checkpoint  |               |
   |                     |                 |               |               |
   |                     | S5: Implement   |               |               |
   |                     |                 |== parallel ==>| FE, BE, MW   |
   |                     |                 |<== results ===|               |
   |                     |                 |               |               |
   |                     | S6: QA          |               |               |
   |                     |                 |== parallel ==>| Reviewer, Sec|
   |                     |                 |<== results ===|               |
   |                     |                 |               |               |
   |                     | S7: Test        |               |               |
   |                     |                 |-- run ------->| Tester        |
   |                     |                 |<-- result ----|  (all suites) |
   |                     |                 |               |               |
   |                     | S8: Debug       |               |               |
   |                     |                 |-- loop ------>| Debugger      |
   |                     |                 |   (iterate)   |   |           |
   |                     |                 |<-- fixed -----|<--+           |
   |                     |                 |               |               |
   |                     | S9: Docs        |               |               |
   |                     |                 |-- run ------->| Doc Writer    |
   |                     |                 |<-- result ----|               |
   |                     |                 |               |               |
   |                     | S10: Deploy     |               |               |
   |                     |                 |-- run ------->| Infra Eng     |
   |                     |                 |<-- result ----|               |
   |                     |                 |-- run ------->| Project Mgr   |
   |                     |                 |<-- result ----|               |
   |                     |                 |-- gate -------|-------------->|
   |<--- approval req ---|-----------------|---------------|---------------|
   |--- approve -------->|-----------------|---------------|-------------->|
   |                     |                 |<-- approved --|---------------|
   |                     |                 |               |               |
   |<-- result ----------|<-- done --------|               |               |
   |                     |                 |               |               |
```

---

## 7. Git & Worktree Management Design

### 7.1 Overview

Git and worktree management is critical infrastructure for CodeBot. Each agent operates
in an isolated git worktree to prevent conflicts when multiple agents write code
concurrently. The system manages branch naming, structured commits, merge strategies,
and automated PR creation.

### 7.2 Architecture

```
+--------------------------------------------------------------------+
|                     Git Management Layer                           |
|--------------------------------------------------------------------|
|                                                                    |
|  +-------------------+  +------------------+  +-----------------+  |
|  | ProjectRepository |  | WorktreePool     |  | BranchStrategy  |  |
|  | (main repo ops)   |  | (pooled worktrees|  | (naming/merge)  |  |
|  +--------+----------+  +--------+---------+  +--------+--------+  |
|           |                      |                      |          |
|  +--------+----------+  +-------+----------+                       |
|  | CommitManager     |  | PRManager        |                       |
|  | (structured cmts) |  | (automated PRs)  |                       |
|  +-------------------+  +------------------+                       |
+--------------------------------------------------------------------+
```

### 7.3 ProjectRepository

```python
class ProjectRepository:
    """Main repository management."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    async def initialize(self, project: Project):
        """Initialize repository for a CodeBot project."""
        # Ensure .codebot directory structure exists
        codebot_dirs = [
            ".codebot/memory", ".codebot/checkpoints",
            ".codebot/vectors", ".codebot/logs",
        ]
        for d in codebot_dirs:
            os.makedirs(os.path.join(self.repo_path, d), exist_ok=True)

        # Create .gitignore entries for CodeBot internals
        gitignore_entries = [
            ".codebot/vectors/", ".codebot/checkpoints/",
            ".codebot/logs/", ".worktrees/",
        ]
        await self._update_gitignore(gitignore_entries)

    async def get_status(self) -> RepoStatus:
        """Get comprehensive repository status."""
        return RepoStatus(
            branch=self.repo.active_branch.name,
            is_clean=not self.repo.is_dirty(),
            untracked_files=self.repo.untracked_files,
            modified_files=[item.a_path for item in self.repo.index.diff(None)],
            staged_files=[item.a_path for item in self.repo.index.diff("HEAD")],
            ahead_behind=self._get_ahead_behind(),
            worktrees=await self._list_worktrees(),
        )

    async def get_file_history(self, file_path: str, max_entries: int = 20) -> List[CommitInfo]:
        """Get commit history for a specific file."""
        commits = list(self.repo.iter_commits(paths=file_path, max_count=max_entries))
        return [
            CommitInfo(
                sha=c.hexsha[:8],
                message=c.message.strip(),
                author=str(c.author),
                date=c.authored_datetime,
                files_changed=list(c.stats.files.keys()),
            )
            for c in commits
        ]
```

### 7.4 WorktreePool

```python
class WorktreePool:
    """Pool of pre-created worktrees for quick agent assignment."""

    def __init__(
        self,
        repo_path: str,
        pool_size: int = 5,
        worktree_base: str = ".worktrees",
    ):
        self.repo_path = repo_path
        self.pool_size = pool_size
        self.worktree_base = os.path.join(repo_path, worktree_base)
        self.available: asyncio.Queue = asyncio.Queue()
        self.active: Dict[str, WorktreeInfo] = {}
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Pre-create worktrees for the pool."""
        os.makedirs(self.worktree_base, exist_ok=True)
        for i in range(self.pool_size):
            wt = await self._create_worktree(f"pool-{i}")
            await self.available.put(wt)
        logger.info(f"WorktreePool initialized with {self.pool_size} worktrees")

    async def acquire(self, agent_id: str, branch_name: str) -> WorktreeInfo:
        """Acquire a worktree for an agent, creating a new branch."""
        try:
            wt = self.available.get_nowait()
        except asyncio.QueueEmpty:
            wt = await self._create_worktree(f"overflow-{uuid4().hex[:6]}")

        # Create and checkout the agent's branch
        await self._run_git(wt.path, f"checkout -b {branch_name}")
        wt.branch = branch_name
        wt.agent_id = agent_id
        wt.acquired_at = datetime.utcnow()

        async with self._lock:
            self.active[wt.id] = wt

        return wt

    async def release(self, worktree: WorktreeInfo):
        """Return a worktree to the pool after cleanup."""
        async with self._lock:
            self.active.pop(worktree.id, None)

        # Clean up: discard changes, go back to main
        await self._run_git(worktree.path, "checkout main")
        await self._run_git(worktree.path, "clean -fd")
        await self._run_git(worktree.path, "reset --hard HEAD")

        worktree.branch = "main"
        worktree.agent_id = None

        if self.available.qsize() < self.pool_size:
            await self.available.put(worktree)
        else:
            await self._destroy_worktree(worktree)

    async def _create_worktree(self, name: str) -> WorktreeInfo:
        """Create a new git worktree."""
        wt_path = os.path.join(self.worktree_base, name)
        await self._run_git(
            self.repo_path,
            f"worktree add {wt_path} --detach"
        )
        return WorktreeInfo(
            id=uuid4().hex,
            path=wt_path,
            name=name,
            branch="HEAD",
        )
```

### 7.5 BranchStrategy

```python
class BranchStrategy:
    """Branch naming conventions, merge strategy, and conflict resolution."""

    # Branch naming convention:
    #   codebot/{project_id}/{phase}/{agent_role}/{short_description}
    #
    # Examples:
    #   codebot/proj-abc/implement/frontend-dev/user-auth-ui
    #   codebot/proj-abc/implement/backend-dev/user-auth-api
    #   codebot/proj-abc/fix/debugger/fix-login-validation

    BRANCH_TEMPLATE = "codebot/{project_id}/{phase}/{agent_role}/{description}"

    def generate_branch_name(
        self,
        project_id: str,
        phase: str,
        agent_role: str,
        description: str,
    ) -> str:
        """Generate a standardized branch name."""
        slug = re.sub(r'[^a-z0-9-]', '-', description.lower())[:40]
        return self.BRANCH_TEMPLATE.format(
            project_id=project_id[:8],
            phase=phase,
            agent_role=agent_role,
            description=slug,
        )

    async def merge_branches(
        self,
        repo: ProjectRepository,
        source_branches: List[str],
        target_branch: str,
        strategy: str = "sequential",
    ) -> MergeResult:
        """
        Merge multiple agent branches into a target branch.

        Strategies:
        - sequential: merge one by one, resolving conflicts between each
        - octopus: attempt octopus merge (all at once, fails on conflicts)
        - squash: squash-merge each branch
        """
        if strategy == "sequential":
            return await self._sequential_merge(repo, source_branches, target_branch)
        elif strategy == "octopus":
            return await self._octopus_merge(repo, source_branches, target_branch)
        elif strategy == "squash":
            return await self._squash_merge(repo, source_branches, target_branch)

    async def resolve_conflicts(
        self,
        repo: ProjectRepository,
        conflicts: List[ConflictInfo],
    ) -> List[Resolution]:
        """Use AI to resolve merge conflicts."""
        resolutions = []
        for conflict in conflicts:
            # Read both versions
            ours = conflict.ours_content
            theirs = conflict.theirs_content

            # Use LLM to intelligently merge
            resolution = await self.llm.complete(LLMRequest(
                messages=[
                    Message(role="system", content=(
                        "You are a code merge conflict resolver. Given two versions "
                        "of code, produce the correctly merged result that preserves "
                        "the intent of both changes."
                    )),
                    Message(role="user", content=(
                        f"File: {conflict.file_path}\n\n"
                        f"<<<< OURS (from {conflict.ours_branch}):\n{ours}\n\n"
                        f"==== THEIRS (from {conflict.theirs_branch}):\n{theirs}\n"
                        f">>>>\n\nProduce the merged result:"
                    )),
                ],
                model="claude-sonnet-4",
            ))
            resolutions.append(Resolution(
                file_path=conflict.file_path,
                content=resolution.content,
            ))
        return resolutions
```

### 7.6 CommitManager

```python
class CommitManager:
    """Structured commit messages with agent attribution."""

    # Commit message format:
    #
    #   [agent-role] type(scope): description
    #
    #   Body with details of changes.
    #
    #   Agent: backend-dev
    #   Phase: implement
    #   Task: TASK-042
    #   Co-Authored-By: CodeBot <codebot@example.com>

    COMMIT_TYPES = [
        "feat",      # new feature
        "fix",       # bug fix
        "refactor",  # code refactoring
        "test",      # adding/updating tests
        "docs",      # documentation
        "style",     # formatting, no code change
        "chore",     # maintenance tasks
        "security",  # security fixes
        "perf",      # performance improvements
        "ci",        # CI/CD changes
        "infra",     # infrastructure changes
    ]

    def create_commit(
        self,
        repo: git.Repo,
        agent_role: str,
        commit_type: str,
        scope: str,
        description: str,
        body: str = "",
        task_id: str = "",
        files: List[str] = None,
    ) -> str:
        """Create a structured commit with agent attribution."""
        # Stage files
        if files:
            repo.index.add(files)
        else:
            repo.git.add(A=True)

        # Build commit message
        header = f"[{agent_role}] {commit_type}({scope}): {description}"
        trailer = (
            f"\nAgent: {agent_role}\n"
            f"Phase: {self.current_phase}\n"
        )
        if task_id:
            trailer += f"Task: {task_id}\n"
        trailer += "Co-Authored-By: CodeBot <codebot@example.com>"

        full_message = header
        if body:
            full_message += f"\n\n{body}"
        full_message += f"\n\n{trailer}"

        commit = repo.index.commit(full_message)
        return commit.hexsha
```

### 7.7 PRManager

```python
class PRManager:
    """Automated PR creation with agent-generated descriptions."""

    def __init__(self, github_token: str, repo_owner: str, repo_name: str):
        self.gh = Github(github_token)
        self.repo = self.gh.get_repo(f"{repo_owner}/{repo_name}")

    async def create_pr(
        self,
        branch_name: str,
        target_branch: str,
        project: Project,
        phase_results: List[PhaseResult],
    ) -> PRInfo:
        """Create a PR with auto-generated description."""
        # Generate PR description from phase results
        description = await self._generate_description(project, phase_results)

        # Collect all file changes for the diff summary
        changed_files = await self._get_changed_files(branch_name, target_branch)

        pr = self.repo.create_pull(
            title=f"[CodeBot] {project.name}: {self._summarize_changes(phase_results)}",
            body=description,
            head=branch_name,
            base=target_branch,
        )

        # Add labels
        pr.add_to_labels("codebot", "automated")

        # Add reviewers if configured
        if project.config.reviewers:
            pr.create_review_request(reviewers=project.config.reviewers)

        return PRInfo(
            number=pr.number,
            url=pr.html_url,
            branch=branch_name,
            changed_files=len(changed_files),
        )

    async def _generate_description(
        self,
        project: Project,
        phase_results: List[PhaseResult],
    ) -> str:
        """Generate a comprehensive PR description."""
        template = """
## Summary
{summary}

## Changes Made

### Architecture
{architecture_changes}

### Implementation
{implementation_changes}

### Tests
{test_summary}

### Security
{security_summary}

## Agent Execution Log
{agent_log}

## How to Test
{test_instructions}

---
*This PR was automatically generated by CodeBot.*
"""
        # Fill template from phase results
        return template.format(
            summary=self._extract_summary(phase_results),
            architecture_changes=self._extract_arch_changes(phase_results),
            implementation_changes=self._extract_impl_changes(phase_results),
            test_summary=self._extract_test_summary(phase_results),
            security_summary=self._extract_security_summary(phase_results),
            agent_log=self._format_agent_log(phase_results),
            test_instructions=self._generate_test_instructions(phase_results),
        )
```

### 7.8 Git Workflow Diagram

```
  main --------+------------------------------------------+----> main
               |                                          |
               +-- codebot/proj/implement/frontend -------+
               |      |  commit  |  commit  |             |
               |                                          |
               +-- codebot/proj/implement/backend --------+  (merge via PR)
               |      |  commit  |  commit  |  commit  |  |
               |                                          |
               +-- codebot/proj/implement/middleware ------+
               |      |  commit  |                        |
               |                                          |
               +-- codebot/proj/fix/debugger-fix1 --------+
                      |  commit  |                        |
```

---

## 8. Security Pipeline Design

### 8.1 Overview

The Security Pipeline ensures all generated code meets security standards before delivery.
It orchestrates multiple security scanning tools in parallel, aggregates findings, and
enforces configurable pass/fail thresholds.

### 8.2 Architecture

```
+---------------------------------------------------------------------+
|                    SecurityOrchestrator                             |
|---------------------------------------------------------------------|
|                                                                     |
|  +-------------+  +-------------+  +------------------+            |
|  | SASTRunner  |  | DASTRunner  |  | DependencyScanner|            |
|  | (Semgrep +  |  | (Shannon)   |  | (Trivy + OpenSCA)|            |
|  |  SonarQube) |  |             |  |                  |            |
|  +------+------+  +------+------+  +--------+---------+            |
|         |                |                   |                     |
|  +------+------+  +------+-------+                                 |
|  | SecretScanner|  |LicenseChecker|                                 |
|  | (Gitleaks)  |  |(ScanCode/    |                                 |
|  |             |  | FOSSology)   |                                 |
|  +------+------+  +------+-------+                                 |
|         |                |                                         |
|         +-------+--------+                                         |
|                 |                                                  |
|         +-------+--------+         +-------------------+           |
|         | SecurityReport |-------->| SecurityGate      |           |
|         | (aggregated)   |         | (pass/fail)       |           |
|         +----------------+         +-------------------+           |
+---------------------------------------------------------------------+
```

### 8.3 SecurityOrchestrator

```python
class SecurityOrchestrator:
    """Coordinates all security scanning tools."""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.sast = SASTRunner(config.sast)
        self.dast = DASTRunner(config.dast)
        self.deps = DependencyScanner(config.deps)
        self.secrets = SecretScanner(config.secrets)
        self.license = LicenseChecker(config.license)
        self.gate = SecurityGate(config.thresholds)

    async def scan(self, project_path: str) -> SecurityReport:
        """Run all security scans in parallel and aggregate results."""
        # Run all scanners concurrently
        results = await asyncio.gather(
            self.sast.scan(project_path),
            self.dast.scan(project_path),
            self.deps.scan(project_path),
            self.secrets.scan(project_path),
            self.license.scan(project_path),
            return_exceptions=True,
        )

        # Aggregate findings
        all_findings = []
        scan_errors = []

        for scanner_name, result in zip(
            ["sast", "dast", "deps", "secrets", "license"], results
        ):
            if isinstance(result, Exception):
                scan_errors.append(ScanError(scanner=scanner_name, error=str(result)))
            else:
                all_findings.extend(result.findings)

        # Deduplicate findings (same vuln found by multiple tools)
        deduplicated = self._deduplicate(all_findings)

        # Classify by severity
        report = SecurityReport(
            findings=deduplicated,
            errors=scan_errors,
            summary=self._build_summary(deduplicated),
            scanned_at=datetime.utcnow(),
        )

        # Run gate check
        report.gate_result = self.gate.evaluate(report)

        return report
```

### 8.4 SASTRunner

```python
class SASTRunner:
    """Static Application Security Testing via Semgrep + SonarQube."""

    async def scan(self, project_path: str) -> ScanResult:
        """Run SAST tools and collect findings."""
        findings = []

        # Semgrep scan
        semgrep_result = await self._run_semgrep(project_path)
        findings.extend(self._parse_semgrep(semgrep_result))

        # SonarQube scan (if configured)
        if self.config.sonarqube_enabled:
            sonar_result = await self._run_sonarqube(project_path)
            findings.extend(self._parse_sonarqube(sonar_result))

        return ScanResult(scanner="sast", findings=findings)

    async def _run_semgrep(self, path: str) -> str:
        """Execute Semgrep with security-focused rulesets."""
        cmd = [
            "semgrep", "scan",
            "--config", "p/security-audit",
            "--config", "p/owasp-top-ten",
            "--config", "p/cwe-top-25",
            "--json",
            "--no-git-ignore",
            path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode()

    def _parse_semgrep(self, output: str) -> List[SecurityFinding]:
        """Parse Semgrep JSON output into SecurityFinding objects."""
        data = json.loads(output)
        findings = []
        for result in data.get("results", []):
            findings.append(SecurityFinding(
                id=uuid4().hex,
                tool="semgrep",
                rule_id=result["check_id"],
                severity=self._map_severity(result["extra"]["severity"]),
                title=result["extra"]["message"],
                file_path=result["path"],
                line_start=result["start"]["line"],
                line_end=result["end"]["line"],
                code_snippet=result["extra"].get("lines", ""),
                cwe=result["extra"].get("metadata", {}).get("cwe", []),
                fix_recommendation=result["extra"].get("fix", ""),
            ))
        return findings
```

### 8.5 DependencyScanner

```python
class DependencyScanner:
    """Dependency vulnerability scanning via Trivy + OpenSCA."""

    async def scan(self, project_path: str) -> ScanResult:
        """Scan dependencies for known vulnerabilities."""
        findings = []

        # Trivy scan
        trivy_result = await self._run_trivy(project_path)
        findings.extend(self._parse_trivy(trivy_result))

        # OpenSCA scan (if configured)
        if self.config.opensca_enabled:
            opensca_result = await self._run_opensca(project_path)
            findings.extend(self._parse_opensca(opensca_result))

        return ScanResult(scanner="dependency", findings=findings)

    async def _run_trivy(self, path: str) -> str:
        """Execute Trivy filesystem scan."""
        cmd = [
            "trivy", "filesystem",
            "--format", "json",
            "--severity", "CRITICAL,HIGH,MEDIUM",
            "--scanners", "vuln,secret,misconfig",
            path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode()
```

### 8.6 SecretScanner

```python
class SecretScanner:
    """Secret detection via Gitleaks."""

    async def scan(self, project_path: str) -> ScanResult:
        """Scan for hardcoded secrets and credentials."""
        cmd = [
            "gitleaks", "detect",
            "--source", project_path,
            "--report-format", "json",
            "--report-path", "/dev/stdout",
            "--no-git",
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        findings = []
        if stdout:
            leaks = json.loads(stdout.decode())
            for leak in leaks:
                findings.append(SecurityFinding(
                    id=uuid4().hex,
                    tool="gitleaks",
                    rule_id=leak["RuleID"],
                    severity=Severity.CRITICAL,  # secrets are always critical
                    title=f"Hardcoded secret detected: {leak['Description']}",
                    file_path=leak["File"],
                    line_start=leak["StartLine"],
                    line_end=leak["EndLine"],
                    code_snippet=leak["Match"],
                    fix_recommendation=(
                        "Remove hardcoded secret and use environment variables "
                        "or a secrets manager instead."
                    ),
                ))

        return ScanResult(scanner="secrets", findings=findings)
```

### 8.7 LicenseChecker

```python
class LicenseChecker:
    """OSS license compliance checking via ScanCode/FOSSology/ORT."""

    # License compatibility matrix
    ALLOWED_LICENSES = {
        "permissive": ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"],
        "weak_copyleft": ["LGPL-2.1", "LGPL-3.0", "MPL-2.0"],
        "copyleft": ["GPL-2.0", "GPL-3.0", "AGPL-3.0"],
    }

    BLOCKED_LICENSES = ["AGPL-3.0", "SSPL-1.0", "EUPL-1.1"]

    async def scan(self, project_path: str) -> ScanResult:
        """Check all dependencies for license compliance."""
        cmd = [
            "scancode",
            "--license", "--license-text",
            "--json-pp", "/dev/stdout",
            project_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        findings = []
        data = json.loads(stdout.decode())
        for file_info in data.get("files", []):
            for lic in file_info.get("licenses", []):
                if lic["spdx_license_key"] in self.BLOCKED_LICENSES:
                    findings.append(SecurityFinding(
                        id=uuid4().hex,
                        tool="license-checker",
                        rule_id=f"blocked-license-{lic['spdx_license_key']}",
                        severity=Severity.HIGH,
                        title=f"Blocked license detected: {lic['spdx_license_key']}",
                        file_path=file_info["path"],
                        fix_recommendation=(
                            f"Replace dependency using {lic['spdx_license_key']} "
                            f"license with a permissively-licensed alternative."
                        ),
                    ))

        return ScanResult(scanner="license", findings=findings)
```

### 8.8 SecurityGate

```python
class SecurityGate:
    """Pass/fail decision based on configurable security thresholds."""

    def __init__(self, thresholds: SecurityThresholds):
        self.thresholds = thresholds

    def evaluate(self, report: SecurityReport) -> GateResult:
        """Evaluate security findings against thresholds."""
        summary = report.summary

        # Hard fail conditions
        if summary.critical_count > self.thresholds.max_critical:
            return GateResult(
                passed=False,
                reason=(
                    f"CRITICAL findings ({summary.critical_count}) exceed "
                    f"threshold ({self.thresholds.max_critical})"
                ),
            )

        if summary.high_count > self.thresholds.max_high:
            return GateResult(
                passed=False,
                reason=(
                    f"HIGH findings ({summary.high_count}) exceed "
                    f"threshold ({self.thresholds.max_high})"
                ),
            )

        if summary.secrets_count > 0:
            return GateResult(
                passed=False,
                reason="Hardcoded secrets detected -- zero tolerance policy",
            )

        if summary.blocked_licenses_count > 0:
            return GateResult(
                passed=False,
                reason="Blocked OSS licenses detected",
            )

        # Warning conditions (pass with warnings)
        warnings = []
        if summary.medium_count > self.thresholds.max_medium:
            warnings.append(
                f"MEDIUM findings ({summary.medium_count}) exceed recommendation"
            )

        return GateResult(passed=True, warnings=warnings)


@dataclass
class SecurityThresholds:
    max_critical: int = 0     # zero tolerance for critical
    max_high: int = 0         # zero tolerance for high
    max_medium: int = 5       # allow some medium findings
    max_low: int = 20         # allow many low findings
    require_no_secrets: bool = True
    require_license_compliance: bool = True
```

### 8.9 Security Pipeline Sequence

```
  SecurityOrchestrator
         |
         +------ (parallel) ------+--------+--------+--------+
         |                        |        |        |        |
         v                        v        v        v        v
    SASTRunner              DASTRunner  DepScan  SecretScan LicChk
    (Semgrep +              (Shannon)   (Trivy+  (Gitleaks) (ScanCode)
     SonarQube)                         OpenSCA)
         |                        |        |        |        |
         +--------+-------+------+--------+--------+--------+
                  |
                  v
          Deduplicate & Classify
                  |
                  v
          SecurityReport
          {
            critical: 0,
            high: 2,
            medium: 5,
            low: 12,
            secrets: 0,
            licenses_ok: true
          }
                  |
                  v
           SecurityGate
                  |
            +-----+-----+
            |           |
         PASS         FAIL
            |           |
            v           v
       Continue     Debugger Agent
       Pipeline     (fix security issues)
```

---

## 9. Test Execution Design

### 9.1 Overview

The Test Execution system generates, runs, and analyzes tests across all code produced
by CodeBot's development agents. It supports multiple test frameworks, collects coverage
data, and identifies regressions.

### 9.2 Architecture

```
+---------------------------------------------------------------------+
|                      Test Execution System                          |
|---------------------------------------------------------------------|
|                                                                     |
|  +----------------+  +----------------+  +---------------------+    |
|  | TestGenerator  |  | TestRunner     |  | CoverageAnalyzer    |    |
|  | (AI-powered)   |  | (multi-fwk)    |  | (threshold enforce) |    |
|  +-------+--------+  +-------+--------+  +----------+----------+    |
|          |                    |                      |              |
|  +-------+--------+  +-------+--------+                             |
|  | TestResultParser|  |RegressionDetect|                             |
|  | (structured)   |  | (diff analysis)|                             |
|  +----------------+  +----------------+                             |
+---------------------------------------------------------------------+
```

### 9.3 TestGenerator

```python
class TestGenerator:
    """AI-powered test case generation per code module."""

    def __init__(self, llm: LLMProvider, code_indexer: CodeIndexer):
        self.llm = llm
        self.code_indexer = code_indexer

    async def generate_tests(
        self,
        code_artifact: CodeArtifact,
        test_type: TestType,
        coverage_target: float = 0.8,
    ) -> List[TestArtifact]:
        """Generate test cases for a code artifact."""
        # Get code structure via Tree-sitter
        symbols = await self.code_indexer.get_symbols(code_artifact.path)

        # Build test generation prompt
        tests = []
        for symbol in symbols:
            if symbol.kind in (SymbolKind.FUNCTION, SymbolKind.METHOD, SymbolKind.CLASS):
                test = await self._generate_test_for_symbol(
                    symbol, code_artifact, test_type
                )
                tests.append(test)

        return tests

    async def _generate_test_for_symbol(
        self,
        symbol: CodeSymbol,
        artifact: CodeArtifact,
        test_type: TestType,
    ) -> TestArtifact:
        """Generate tests for a single code symbol."""
        response = await self.llm.complete(LLMRequest(
            messages=[
                Message(role="system", content=self._get_test_system_prompt(test_type)),
                Message(role="user", content=(
                    f"Generate {test_type.value} tests for the following code:\n\n"
                    f"File: {artifact.path}\n"
                    f"Language: {artifact.language}\n"
                    f"Framework: {artifact.framework}\n\n"
                    f"```{artifact.language}\n{symbol.source}\n```\n\n"
                    f"Signature: {symbol.signature}\n"
                    f"Docstring: {symbol.docstring}\n\n"
                    f"Generate comprehensive tests covering:\n"
                    f"- Happy path scenarios\n"
                    f"- Edge cases and boundary conditions\n"
                    f"- Error handling paths\n"
                    f"- Input validation\n"
                )),
            ],
            model="claude-sonnet-4",
        ))

        return TestArtifact(
            path=self._test_path_for(artifact.path),
            content=self._extract_code(response.content),
            test_type=test_type,
            target_symbol=symbol.qualified_name,
        )

    def _get_test_system_prompt(self, test_type: TestType) -> str:
        """Return test-type-specific system prompt."""
        prompts = {
            TestType.UNIT: (
                "You are a test engineer writing unit tests. "
                "Use mocking for external dependencies. "
                "Each test should be independent and deterministic. "
                "Follow the Arrange-Act-Assert pattern."
            ),
            TestType.INTEGRATION: (
                "You are a test engineer writing integration tests. "
                "Test the interaction between multiple components. "
                "Use test databases and realistic fixtures. "
                "Verify end-to-end data flow."
            ),
            TestType.E2E: (
                "You are a test engineer writing end-to-end tests. "
                "Use Playwright for browser automation. "
                "Test complete user workflows. "
                "Include visual regression checks where appropriate."
            ),
            TestType.UI_COMPONENT: (
                "You are a test engineer writing UI component tests. "
                "Use React Testing Library or similar for component rendering. "
                "Test visual states, user interactions, accessibility, and responsive behavior. "
                "Verify props, events, and conditional rendering."
            ),
            TestType.SMOKE: (
                "You are a test engineer writing smoke tests. "
                "Focus on critical path verification only. "
                "Test that the most essential features are operational. "
                "Keep tests fast and lightweight for quick validation."
            ),
            TestType.REGRESSION: (
                "You are a test engineer writing regression tests. "
                "Target previously broken functionality. "
                "Each test should specifically guard against a known past bug. "
                "Include the bug context in test comments."
            ),
            TestType.MUTATION: (
                "You are a test engineer evaluating test quality via mutation testing. "
                "Generate mutants by modifying source code (flip operators, remove statements). "
                "Verify that existing tests detect (kill) each mutation. "
                "Report mutation score and surviving mutants."
            ),
        }
        return prompts.get(test_type, prompts[TestType.UNIT])
```

### 9.4 TestRunner

```python
class TestRunner:
    """Unified test execution across frameworks."""

    # Framework detection and configuration
    FRAMEWORK_CONFIGS = {
        "pytest": {
            "detect_files": ["pytest.ini", "setup.cfg", "conftest.py", "pyproject.toml"],
            "command": "python -m pytest",
            "coverage_flag": "--cov={source} --cov-report=json",
            "json_flag": "--json-report --json-report-file={output}",
            "patterns": ["test_*.py", "*_test.py"],
        },
        "vitest": {
            "detect_files": ["vitest.config.ts", "vitest.config.js"],
            "command": "npx vitest run",
            "coverage_flag": "--coverage --coverage.reporter=json",
            "json_flag": "--reporter=json --outputFile={output}",
            "patterns": ["*.test.ts", "*.test.tsx", "*.spec.ts"],
        },
        "playwright": {
            "detect_files": ["playwright.config.ts", "playwright.config.js"],
            "command": "npx playwright test",
            "json_flag": "--reporter=json",
            "patterns": ["*.spec.ts", "*.e2e.ts"],
        },
        "jest": {
            "detect_files": ["jest.config.js", "jest.config.ts"],
            "command": "npx jest",
            "coverage_flag": "--coverage --coverageReporters=json",
            "json_flag": "--json --outputFile={output}",
            "patterns": ["*.test.js", "*.test.tsx", "*.spec.js"],
        },
    }

    async def run(
        self,
        project_path: str,
        test_files: Optional[List[str]] = None,
        framework: Optional[str] = None,
    ) -> TestResults:
        """Run tests and collect results."""
        # Auto-detect framework if not specified
        if not framework:
            framework = self._detect_framework(project_path)

        config = self.FRAMEWORK_CONFIGS[framework]
        output_file = tempfile.mktemp(suffix=".json")

        # Build command
        cmd = config["command"]
        if test_files:
            cmd += " " + " ".join(test_files)
        cmd += " " + config["json_flag"].format(output=output_file)
        if "coverage_flag" in config:
            cmd += " " + config["coverage_flag"].format(source=project_path)

        # Execute
        proc = await asyncio.create_subprocess_shell(
            cmd,
            cwd=project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        # Parse results
        parser = TestResultParser()
        results = parser.parse(framework, output_file, stdout.decode(), stderr.decode())
        results.exit_code = proc.returncode

        return results
```

### 9.5 CoverageAnalyzer

```python
class CoverageAnalyzer:
    """Coverage collection and threshold enforcement."""

    def __init__(self, thresholds: CoverageThresholds):
        self.thresholds = thresholds

    def analyze(self, coverage_data: dict, test_results: TestResults) -> CoverageReport:
        """Analyze coverage data and enforce thresholds."""
        report = CoverageReport(
            overall_line_coverage=coverage_data.get("totals", {}).get("percent_covered", 0),
            overall_branch_coverage=coverage_data.get("totals", {}).get("branch_percent", 0),
            files=[],
            uncovered_lines={},
            threshold_met=True,
            threshold_failures=[],
        )

        # Per-file analysis
        for file_path, file_data in coverage_data.get("files", {}).items():
            file_coverage = FileCoverage(
                path=file_path,
                line_coverage=file_data.get("summary", {}).get("percent_covered", 0),
                branch_coverage=file_data.get("summary", {}).get("branch_percent", 0),
                uncovered_lines=file_data.get("missing_lines", []),
                total_lines=file_data.get("summary", {}).get("num_statements", 0),
            )
            report.files.append(file_coverage)

            if file_coverage.uncovered_lines:
                report.uncovered_lines[file_path] = file_coverage.uncovered_lines

        # Threshold enforcement
        if report.overall_line_coverage < self.thresholds.min_line_coverage:
            report.threshold_met = False
            report.threshold_failures.append(
                f"Line coverage {report.overall_line_coverage:.1f}% < "
                f"required {self.thresholds.min_line_coverage}%"
            )

        if report.overall_branch_coverage < self.thresholds.min_branch_coverage:
            report.threshold_met = False
            report.threshold_failures.append(
                f"Branch coverage {report.overall_branch_coverage:.1f}% < "
                f"required {self.thresholds.min_branch_coverage}%"
            )

        return report


@dataclass
class CoverageThresholds:
    min_line_coverage: float = 80.0      # 80% line coverage minimum
    min_branch_coverage: float = 70.0    # 70% branch coverage minimum
    min_per_file_coverage: float = 60.0  # no file below 60%
    new_code_coverage: float = 90.0      # 90% for new code
```

### 9.6 TestResultParser

```python
class TestResultParser:
    """Structured parsing of test outputs across frameworks."""

    def parse(
        self,
        framework: str,
        json_output_path: str,
        stdout: str,
        stderr: str,
    ) -> TestResults:
        """Parse test results from any supported framework."""
        parser_method = getattr(self, f"_parse_{framework}", None)
        if parser_method is None:
            return self._parse_generic(stdout, stderr)

        try:
            with open(json_output_path) as f:
                data = json.load(f)
            return parser_method(data, stdout, stderr)
        except (FileNotFoundError, json.JSONDecodeError):
            return self._parse_generic(stdout, stderr)

    def _parse_pytest(self, data: dict, stdout: str, stderr: str) -> TestResults:
        """Parse pytest JSON report."""
        tests = []
        for test in data.get("tests", []):
            tests.append(TestCase(
                name=test["nodeid"],
                status=self._map_status(test["outcome"]),
                duration_ms=test.get("duration", 0) * 1000,
                error_message=test.get("call", {}).get("longrepr", ""),
                file_path=test["nodeid"].split("::")[0],
            ))

        return TestResults(
            framework="pytest",
            total=data.get("summary", {}).get("total", 0),
            passed=data.get("summary", {}).get("passed", 0),
            failed=data.get("summary", {}).get("failed", 0),
            skipped=data.get("summary", {}).get("skipped", 0),
            errors=data.get("summary", {}).get("error", 0),
            duration_ms=data.get("duration", 0) * 1000,
            tests=tests,
        )

    def _parse_vitest(self, data: dict, stdout: str, stderr: str) -> TestResults:
        """Parse Vitest JSON report."""
        tests = []
        for suite in data.get("testResults", []):
            for test in suite.get("assertionResults", []):
                tests.append(TestCase(
                    name=f"{suite['name']}::{test['fullName']}",
                    status=self._map_status(test["status"]),
                    duration_ms=test.get("duration", 0),
                    error_message="\n".join(test.get("failureMessages", [])),
                    file_path=suite["name"],
                ))

        return TestResults(
            framework="vitest",
            total=data.get("numTotalTests", 0),
            passed=data.get("numPassedTests", 0),
            failed=data.get("numFailedTests", 0),
            skipped=data.get("numPendingTests", 0),
            tests=tests,
        )
```

### 9.7 RegressionDetector

```python
class RegressionDetector:
    """Identify which tests broke after changes."""

    async def detect(
        self,
        before_results: TestResults,
        after_results: TestResults,
        changed_files: List[str],
    ) -> RegressionReport:
        """Compare test results before and after changes."""
        regressions = []
        new_failures = []
        fixed_tests = []

        before_map = {t.name: t for t in before_results.tests}
        after_map = {t.name: t for t in after_results.tests}

        for name, after_test in after_map.items():
            before_test = before_map.get(name)

            if before_test is None and after_test.status == TestStatus.FAILED:
                new_failures.append(after_test)
            elif before_test and before_test.status == TestStatus.PASSED \
                    and after_test.status == TestStatus.FAILED:
                regressions.append(RegressionInfo(
                    test=after_test,
                    previous_status=before_test.status,
                    likely_cause=self._find_likely_cause(after_test, changed_files),
                ))

        for name, before_test in before_map.items():
            after_test = after_map.get(name)
            if after_test and before_test.status == TestStatus.FAILED \
                    and after_test.status == TestStatus.PASSED:
                fixed_tests.append(after_test)

        return RegressionReport(
            regressions=regressions,
            new_failures=new_failures,
            fixed_tests=fixed_tests,
            total_before=before_results.total,
            total_after=after_results.total,
        )

    def _find_likely_cause(
        self, failed_test: TestCase, changed_files: List[str]
    ) -> Optional[str]:
        """Heuristically determine which changed file likely caused the failure."""
        test_file = failed_test.file_path
        test_dir = os.path.dirname(test_file)
        test_name = os.path.basename(test_file).replace("test_", "").replace("_test", "")

        for changed_file in changed_files:
            # Check if the changed file matches the test's target
            if test_name in changed_file:
                return changed_file
            # Check if they're in the same module
            if os.path.dirname(changed_file) == test_dir.replace("tests", "src"):
                return changed_file

        return None
```

### 9.8 Test Execution Flow

```
  Code Artifacts
       |
       v
  +----+----------+
  | TestGenerator  |  AI generates test cases
  +----+----------+
       |
       v
  Test Files Written
       |
       v
  +----+----------+
  | TestRunner     |  Executes tests (pytest/vitest/playwright)
  +----+----------+
       |
       +----------------+------------------+
       |                |                  |
       v                v                  v
  TestResults     CoverageData       Test Stdout/Stderr
       |                |                  |
       v                v                  v
  +----+------+  +------+--------+  +------+--------+
  |ResultParser|  |CoverageAnalyzer|  |RegressionDtct|
  +----+------+  +------+--------+  +------+--------+
       |                |                  |
       +--------+-------+------------------+
                |
                v
        Unified TestReport
        {
          passed: 142,
          failed: 3,
          coverage: 84.2%,
          regressions: 1,
          threshold_met: true
        }
                |
          +-----+-----+
          |           |
       ALL PASS    FAILURES
          |           |
          v           v
       Continue    Debugger Agent
       Pipeline    (fix failures)
```

---

## 10. Debug & Fix Loop Design

### 10.1 Overview

The Debug & Fix Loop is a self-healing subsystem that automatically diagnoses test failures
and security findings, generates targeted fixes, verifies them, and iterates until all
issues are resolved or a maximum iteration count is reached.

### 10.2 Architecture

```
+---------------------------------------------------------------------+
|                       Debug & Fix Loop                              |
|---------------------------------------------------------------------|
|                                                                     |
|                  +-------------------+                              |
|                  | LoopController    |                              |
|                  | (iteration mgmt) |                              |
|                  +--------+----------+                              |
|                           |                                        |
|            +--------------+--------------+                         |
|            |                             |                         |
|            v                             v                         |
|  +---------+----------+    +-------------+-----------+             |
|  | FailureAnalyzer    |    | FixGenerator            |             |
|  | (root cause)       |    | (targeted patches)      |             |
|  +---------+----------+    +-------------+-----------+             |
|            |                             |                         |
|            v                             v                         |
|  +---------+----------+    +-------------+-----------+             |
|  | TestCaseGenerator  |    | FixVerifier             |             |
|  | (regression tests) |    | (run targeted tests)    |             |
|  +--------------------+    +-------------------------+             |
+---------------------------------------------------------------------+
```

### 10.3 FailureAnalyzer

```python
class FailureAnalyzer:
    """Root cause analysis from test failures and error logs."""

    def __init__(self, llm: LLMProvider, code_indexer: CodeIndexer):
        self.llm = llm
        self.code_indexer = code_indexer

    async def analyze(
        self,
        failures: List[TestCase],
        security_findings: List[SecurityFinding],
        code_artifacts: List[CodeArtifact],
    ) -> List[FailureAnalysis]:
        """Analyze failures and determine root causes."""
        analyses = []

        # Group related failures (same file, same module)
        failure_groups = self._group_failures(failures)

        for group in failure_groups:
            # Gather context for the failing code
            context = await self._gather_context(group)

            # Use LLM for root cause analysis
            analysis = await self.llm.complete(LLMRequest(
                messages=[
                    Message(role="system", content=(
                        "You are an expert debugger performing root cause analysis. "
                        "Given test failures, error messages, and source code, identify "
                        "the exact root cause. Be specific about which line(s) of code "
                        "are problematic and why."
                    )),
                    Message(role="user", content=(
                        f"## Failed Tests\n"
                        f"{self._format_failures(group.failures)}\n\n"
                        f"## Source Code\n"
                        f"```\n{context.source_code}\n```\n\n"
                        f"## Stack Traces\n"
                        f"{self._format_stack_traces(group.failures)}\n\n"
                        f"Provide root cause analysis in JSON format:\n"
                        f'{{"root_cause": "...", "affected_file": "...", '
                        f'"affected_lines": [start, end], '
                        f'"fix_strategy": "...", "confidence": 0.0-1.0}}'
                    )),
                ],
                model="claude-opus-4",
                response_format="json",
            ))

            parsed = json.loads(analysis.content)
            analyses.append(FailureAnalysis(
                failure_group=group,
                root_cause=parsed["root_cause"],
                affected_file=parsed["affected_file"],
                affected_lines=tuple(parsed["affected_lines"]),
                fix_strategy=parsed["fix_strategy"],
                confidence=parsed["confidence"],
            ))

        # Also analyze security findings
        for finding in security_findings:
            if finding.severity in (Severity.CRITICAL, Severity.HIGH):
                analyses.append(FailureAnalysis(
                    failure_group=None,
                    root_cause=finding.title,
                    affected_file=finding.file_path,
                    affected_lines=(finding.line_start, finding.line_end),
                    fix_strategy=finding.fix_recommendation,
                    confidence=0.9,
                    is_security=True,
                ))

        return analyses

    def _group_failures(self, failures: List[TestCase]) -> List[FailureGroup]:
        """Group related failures by module or root cause similarity."""
        groups: Dict[str, FailureGroup] = {}
        for failure in failures:
            module = self._extract_module(failure.file_path)
            if module not in groups:
                groups[module] = FailureGroup(module=module, failures=[])
            groups[module].failures.append(failure)
        return list(groups.values())
```

### 10.4 FixGenerator

```python
class FixGenerator:
    """Targeted fix generation with context from failure analysis."""

    def __init__(self, llm: LLMProvider, code_indexer: CodeIndexer):
        self.llm = llm
        self.code_indexer = code_indexer

    async def generate_fix(
        self,
        analysis: FailureAnalysis,
        code_artifacts: List[CodeArtifact],
    ) -> Patch:
        """Generate a targeted fix for a specific failure."""
        # Read the affected file
        affected_code = await self._read_file(analysis.affected_file)

        # Get surrounding context (imports, related functions)
        context = await self.code_indexer.get_context_around(
            analysis.affected_file,
            analysis.affected_lines,
            context_lines=50,
        )

        response = await self.llm.complete(LLMRequest(
            messages=[
                Message(role="system", content=(
                    "You are an expert software engineer fixing a bug. "
                    "Generate a minimal, targeted fix. Do NOT change unrelated code. "
                    "Output only the modified code section using unified diff format."
                )),
                Message(role="user", content=(
                    f"## Root Cause\n{analysis.root_cause}\n\n"
                    f"## Fix Strategy\n{analysis.fix_strategy}\n\n"
                    f"## Affected File: {analysis.affected_file}\n"
                    f"## Affected Lines: {analysis.affected_lines[0]}-{analysis.affected_lines[1]}\n\n"
                    f"## Full File Content\n```\n{affected_code}\n```\n\n"
                    f"## Context\n```\n{context}\n```\n\n"
                    f"Generate the fix as a unified diff (--- a/ +++ b/ format):"
                )),
            ],
            model="claude-opus-4",
        ))

        return Patch(
            file_path=analysis.affected_file,
            diff=response.content,
            analysis_id=analysis.id,
            description=f"Fix: {analysis.root_cause}",
        )

    async def apply_patch(self, patch: Patch, worktree_path: str) -> bool:
        """Apply a generated patch to the worktree."""
        patch_file = os.path.join(worktree_path, ".codebot", "fix.patch")
        async with aiofiles.open(patch_file, 'w') as f:
            await f.write(patch.diff)

        proc = await asyncio.create_subprocess_exec(
            "git", "apply", "--check", patch_file,
            cwd=worktree_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode == 0:
            # Patch applies cleanly
            await asyncio.create_subprocess_exec(
                "git", "apply", patch_file, cwd=worktree_path
            )
            return True
        else:
            # Fall back to direct file replacement
            return await self._apply_direct(patch, worktree_path)
```

### 10.5 TestCaseGenerator

```python
class BugTestCaseGenerator:
    """Create specific test case for the bug being fixed."""

    async def generate(
        self,
        analysis: FailureAnalysis,
        patch: Patch,
    ) -> TestArtifact:
        """Generate a regression test that catches this specific bug."""
        response = await self.llm.complete(LLMRequest(
            messages=[
                Message(role="system", content=(
                    "You are a test engineer writing a regression test. "
                    "This test must FAIL on the buggy code and PASS on the fixed code. "
                    "Make the test specific and deterministic."
                )),
                Message(role="user", content=(
                    f"## Bug Description\n{analysis.root_cause}\n\n"
                    f"## Fix Applied\n```diff\n{patch.diff}\n```\n\n"
                    f"Write a regression test that specifically catches this bug:"
                )),
            ],
            model="claude-sonnet-4",
        ))

        test_path = self._regression_test_path(analysis.affected_file)
        return TestArtifact(
            path=test_path,
            content=self._extract_code(response.content),
            test_type=TestType.REGRESSION,
            target_symbol=analysis.affected_file,
        )
```

### 10.6 FixVerifier

```python
class FixVerifier:
    """Run targeted tests to verify a fix."""

    def __init__(self, test_runner: TestRunner):
        self.test_runner = test_runner

    async def verify(
        self,
        patch: Patch,
        original_failures: List[TestCase],
        regression_test: TestArtifact,
        worktree_path: str,
    ) -> VerificationResult:
        """Verify that a fix resolves the original failures without regressions."""

        # 1. Run the originally failing tests
        original_test_files = list(set(t.file_path for t in original_failures))
        rerun_results = await self.test_runner.run(
            project_path=worktree_path,
            test_files=original_test_files,
        )

        # 2. Run the new regression test
        regression_results = await self.test_runner.run(
            project_path=worktree_path,
            test_files=[regression_test.path],
        )

        # 3. Run the full test suite to check for new regressions
        full_results = await self.test_runner.run(
            project_path=worktree_path,
        )

        # 4. Determine verdict
        originally_fixed = all(
            self._is_now_passing(f, rerun_results) for f in original_failures
        )
        regression_passes = regression_results.failed == 0
        no_new_regressions = full_results.failed <= len(original_failures)

        return VerificationResult(
            fix_applied=True,
            originally_failing_now_pass=originally_fixed,
            regression_test_passes=regression_passes,
            new_regressions=max(0, full_results.failed - len(original_failures)),
            verified=originally_fixed and regression_passes and no_new_regressions,
            full_results=full_results,
        )
```

### 10.7 LoopController

```python
class LoopController:
    """Manage debug-fix iterations with max retries and escalation."""

    def __init__(
        self,
        max_iterations: int = 5,
        escalation: ErrorEscalation = None,
    ):
        self.max_iterations = max_iterations
        self.escalation = escalation
        self.iteration_history: List[IterationRecord] = []

    async def run_loop(
        self,
        test_results: TestResults,
        security_findings: List[SecurityFinding],
        code_artifacts: List[CodeArtifact],
        worktree_path: str,
    ) -> LoopResult:
        """Run the debug-fix loop until all issues are resolved."""
        current_failures = [t for t in test_results.tests if t.status == TestStatus.FAILED]
        current_security = [f for f in security_findings
                           if f.severity in (Severity.CRITICAL, Severity.HIGH)]

        for iteration in range(self.max_iterations):
            if not current_failures and not current_security:
                return LoopResult(
                    status="all_resolved",
                    iterations=iteration,
                    history=self.iteration_history,
                )

            logger.info(
                f"Debug-fix iteration {iteration + 1}/{self.max_iterations}: "
                f"{len(current_failures)} failures, {len(current_security)} security issues"
            )

            # 1. Analyze failures
            analyses = await self.failure_analyzer.analyze(
                current_failures, current_security, code_artifacts
            )

            # 2. Generate and apply fixes
            patches = []
            for analysis in analyses:
                patch = await self.fix_generator.generate_fix(analysis, code_artifacts)
                success = await self.fix_generator.apply_patch(patch, worktree_path)
                if success:
                    patches.append(patch)

            # 3. Generate regression tests
            regression_tests = []
            for analysis, patch in zip(analyses, patches):
                test = await self.test_case_gen.generate(analysis, patch)
                await self._write_test(test, worktree_path)
                regression_tests.append(test)

            # 4. Verify fixes
            verification = await self.fix_verifier.verify(
                patches[-1] if patches else None,
                current_failures,
                regression_tests[-1] if regression_tests else None,
                worktree_path,
            )

            # Record iteration
            self.iteration_history.append(IterationRecord(
                iteration=iteration,
                failures_in=len(current_failures),
                fixes_applied=len(patches),
                verification=verification,
            ))

            if verification.verified:
                return LoopResult(
                    status="all_resolved",
                    iterations=iteration + 1,
                    history=self.iteration_history,
                )

            # Update remaining failures for next iteration
            current_failures = [
                t for t in verification.full_results.tests
                if t.status == TestStatus.FAILED
            ]
            current_security = []  # security fixes verified separately

        # Max iterations reached
        if self.escalation:
            await self.escalation.handle_failure(
                agent_id="debugger",
                error=MaxIterationsReached(self.max_iterations),
                context=ExecutionContext(
                    remaining_failures=current_failures,
                    history=self.iteration_history,
                ),
            )

        return LoopResult(
            status="max_iterations_reached",
            iterations=self.max_iterations,
            remaining_failures=current_failures,
            history=self.iteration_history,
        )
```

### 10.8 Debug-Fix Loop Sequence

```
  TestResults + SecurityFindings
          |
          v
  +-------+--------+
  | LoopController  |  iteration = 0
  +-------+--------+
          |
          v
  +-------+---------+
  | FailureAnalyzer |  Determine root causes via LLM
  +-------+---------+
          |
          v
  [FailureAnalysis, FailureAnalysis, ...]
          |
          v
  +-------+---------+
  | FixGenerator    |  Generate targeted patches via LLM
  +-------+---------+
          |
          v
  +-------+-------------+
  | TestCaseGenerator   |  Create regression test for each fix
  +-------+-------------+
          |
          v
  +-------+---------+
  | FixVerifier     |  Run originally failing + regression + full suite
  +-------+---------+
          |
     +----+----+
     |         |
  VERIFIED   STILL FAILING
     |         |
     v         v
  Return    iteration++
  Success   (back to LoopController)
             |
         iteration > max?
             |
        +----+----+
        |         |
       NO        YES
        |         |
        v         v
     Retry    Escalate to Human
```

---

## 11. Event System Design

### 11.1 Overview

The Event System provides a pub/sub mechanism for inter-agent communication, observability,
and audit logging. All significant actions in CodeBot emit events that can be consumed by
handlers for notifications, metrics, logging, and UI updates.

### 11.2 Architecture

```
+---------------------------------------------------------------------+
|                        Event System                                 |
|---------------------------------------------------------------------|
|                                                                     |
|  Producers                    EventBus                  Consumers   |
|  +----------+                +--------+              +-----------+  |
|  | Agent    |---emit()------>|        |---dispatch--->| Logger    |  |
|  +----------+                |        |              +-----------+  |
|  +----------+                | Topic  |              +-----------+  |
|  | Pipeline |---emit()------>| Router |---dispatch--->| Metrics   |  |
|  +----------+                |        |              +-----------+  |
|  +----------+                |        |              +-----------+  |
|  | Security |---emit()------>|        |---dispatch--->| Notifier  |  |
|  +----------+                +---+----+              +-----------+  |
|                                  |                   +-----------+  |
|                                  +---persist-------->| EventStore|  |
|                                                      +-----------+  |
+---------------------------------------------------------------------+
```

### 11.3 EventBus

```python
class EventBus:
    """Pub/sub system for inter-agent communication."""

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._global_handlers: List[EventHandler] = []
        self._event_store: Optional[EventStore] = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    def subscribe(self, event_type: str, handler: EventHandler):
        """Subscribe to a specific event type."""
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler):
        """Subscribe to all events."""
        self._global_handlers.append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler):
        """Unsubscribe from a specific event type."""
        self._handlers[event_type].remove(handler)

    async def emit(self, event: Event):
        """Emit an event to all subscribers."""
        event.timestamp = datetime.utcnow()
        event.id = uuid4().hex

        # Persist to event store
        if self._event_store:
            await self._event_store.append(event)

        # Dispatch to handlers
        await self._queue.put(event)

    async def start(self):
        """Start the event dispatch loop."""
        self._running = True
        while self._running:
            event = await self._queue.get()
            await self._dispatch(event)

    async def _dispatch(self, event: Event):
        """Dispatch event to matching handlers."""
        handlers = (
            self._handlers.get(event.type, []) +
            self._global_handlers
        )
        tasks = [handler.handle(event) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for handler, result in zip(handlers, results):
            if isinstance(result, Exception):
                logger.error(
                    f"Event handler {handler.__class__.__name__} failed "
                    f"for {event.type}: {result}"
                )
```

### 11.4 Event Types

```python
@dataclass
class Event:
    """Base event class."""
    id: str = ""
    type: str = ""
    timestamp: datetime = None
    source: str = ""          # agent or component that emitted the event
    project_id: str = ""
    metadata: dict = field(default_factory=dict)


# --- Agent Lifecycle Events ---

@dataclass
class AgentStarted(Event):
    type: str = "agent.started"
    agent_id: str = ""
    agent_role: str = ""
    task_id: str = ""
    model: str = ""

@dataclass
class AgentCompleted(Event):
    type: str = "agent.completed"
    agent_id: str = ""
    agent_role: str = ""
    task_id: str = ""
    duration_ms: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    output_summary: str = ""

@dataclass
class AgentFailed(Event):
    type: str = "agent.failed"
    agent_id: str = ""
    agent_role: str = ""
    task_id: str = ""
    error_type: str = ""
    error_message: str = ""
    retry_count: int = 0

@dataclass
class AgentEscalated(Event):
    type: str = "agent.escalated"
    agent_id: str = ""
    reason: str = ""
    escalation_level: int = 0


# --- Pipeline Events ---

@dataclass
class PhaseTransition(Event):
    type: str = "pipeline.phase_transition"
    phase_name: str = ""
    phase_idx: int = 0
    status: str = ""    # "started", "completed", "failed"
    duration_ms: int = 0

@dataclass
class PipelineCompleted(Event):
    type: str = "pipeline.completed"
    total_duration_ms: int = 0
    total_cost_usd: float = 0.0
    phases_completed: int = 0

@dataclass
class PipelineFailed(Event):
    type: str = "pipeline.failed"
    failed_phase: str = ""
    error_message: str = ""


# --- Approval Events ---

@dataclass
class HumanApprovalRequired(Event):
    type: str = "approval.required"
    gate_id: str = ""
    prompt: str = ""
    context_summary: str = ""
    timeout_hours: float = 24

@dataclass
class HumanApprovalReceived(Event):
    type: str = "approval.received"
    gate_id: str = ""
    decision: str = ""      # "approved", "rejected"
    feedback: str = ""
    reviewer: str = ""


# --- Code & Quality Events ---

@dataclass
class CodeGenerated(Event):
    type: str = "code.generated"
    agent_role: str = ""
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    lines_added: int = 0
    lines_removed: int = 0

@dataclass
class TestsCompleted(Event):
    type: str = "tests.completed"
    total: int = 0
    passed: int = 0
    failed: int = 0
    coverage_pct: float = 0.0
    framework: str = ""

@dataclass
class SecurityScanCompleted(Event):
    type: str = "security.scan_completed"
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    gate_passed: bool = False


# --- Cost Events ---

@dataclass
class BudgetWarning(Event):
    type: str = "cost.budget_warning"
    agent_id: str = ""
    usage_pct: float = 0.0
    remaining_tokens: int = 0

@dataclass
class CostAlert(Event):
    type: str = "cost.alert"
    total_cost_usd: float = 0.0
    threshold_usd: float = 0.0
    action: str = ""          # "warn", "pause", "abort"
```

### 11.5 EventStore

```python
class EventStore:
    """Persistent event log for audit trail."""

    def __init__(self, storage_path: str = ".codebot/events"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self._buffer: List[Event] = []
        self._flush_interval = 5  # seconds
        self._buffer_size = 100

    async def append(self, event: Event):
        """Append an event to the store."""
        self._buffer.append(event)
        if len(self._buffer) >= self._buffer_size:
            await self.flush()

    async def flush(self):
        """Write buffered events to disk."""
        if not self._buffer:
            return
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        path = os.path.join(self.storage_path, f"events-{date_str}.jsonl")
        async with aiofiles.open(path, 'a') as f:
            for event in self._buffer:
                await f.write(json.dumps(asdict(event), default=str) + '\n')
        self._buffer.clear()

    async def query(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Query events with filters."""
        results = []
        for event_file in sorted(glob.glob(
            os.path.join(self.storage_path, "events-*.jsonl")
        ), reverse=True):
            async with aiofiles.open(event_file, 'r') as f:
                async for line in f:
                    event_data = json.loads(line)
                    if self._matches_filter(event_data, event_type, source, since, until):
                        results.append(event_data)
                        if len(results) >= limit:
                            return results
        return results

    async def get_audit_trail(self, project_id: str) -> List[Event]:
        """Get complete audit trail for a project."""
        return await self.query(
            source=None,
            limit=10000,
        )
```

### 11.6 EventHandler

```python
class EventHandler(ABC):
    """Base class for event handlers."""

    @abstractmethod
    async def handle(self, event: Event) -> None:
        ...


class LoggingHandler(EventHandler):
    """Logs all events to structured logging."""

    async def handle(self, event: Event):
        logger.info(
            f"[{event.type}] source={event.source} "
            f"project={event.project_id} "
            f"data={event.metadata}"
        )


class MetricsHandler(EventHandler):
    """Collects metrics from events for dashboards."""

    def __init__(self):
        self.metrics = {
            "agents_started": Counter(),
            "agents_completed": Counter(),
            "agents_failed": Counter(),
            "tokens_used": Counter(),
            "cost_usd": Gauge(),
            "test_pass_rate": Gauge(),
            "phase_duration_ms": Histogram(),
        }

    async def handle(self, event: Event):
        if event.type == "agent.started":
            self.metrics["agents_started"].inc()
        elif event.type == "agent.completed":
            self.metrics["agents_completed"].inc()
            self.metrics["tokens_used"].inc(event.tokens_used)
            self.metrics["cost_usd"].set(event.cost_usd)
        elif event.type == "agent.failed":
            self.metrics["agents_failed"].inc()
        elif event.type == "pipeline.phase_transition" and event.status == "completed":
            self.metrics["phase_duration_ms"].observe(event.duration_ms)
        elif event.type == "tests.completed":
            rate = event.passed / max(event.total, 1) * 100
            self.metrics["test_pass_rate"].set(rate)


class NotificationHandler(EventHandler):
    """Sends notifications for important events."""

    NOTIFY_EVENTS = {
        "approval.required",
        "pipeline.completed",
        "pipeline.failed",
        "cost.alert",
        "agent.escalated",
    }

    def __init__(self, channels: List[NotificationChannel]):
        self.channels = channels

    async def handle(self, event: Event):
        if event.type in self.NOTIFY_EVENTS:
            message = self._format_notification(event)
            for channel in self.channels:
                await channel.send(message)

    def _format_notification(self, event: Event) -> str:
        formatters = {
            "approval.required": lambda e: (
                f"Human approval needed: {e.prompt}\n"
                f"Gate: {e.gate_id}"
            ),
            "pipeline.completed": lambda e: (
                f"Pipeline completed successfully!\n"
                f"Duration: {e.total_duration_ms/1000:.1f}s | "
                f"Cost: ${e.total_cost_usd:.2f}"
            ),
            "pipeline.failed": lambda e: (
                f"Pipeline FAILED at phase: {e.failed_phase}\n"
                f"Error: {e.error_message}"
            ),
            "cost.alert": lambda e: (
                f"Cost alert: ${e.total_cost_usd:.2f} "
                f"(threshold: ${e.threshold_usd:.2f})\n"
                f"Action: {e.action}"
            ),
        }
        formatter = formatters.get(event.type, lambda e: str(e))
        return formatter(event)
```

### 11.7 Event Flow Diagram

```
  +----------+    +----------+    +-----------+    +-----------+
  | Orchstr  |    | Planner  |    | FE Dev    |    | Tester    |
  +----+-----+    +----+-----+    +-----+-----+    +-----+-----+
       |               |               |               |
       |emit           |emit           |emit           |emit
       |               |               |               |
  +----v---------------v---------------v---------------v-----+
  |                        EventBus                          |
  |  +----------------------------------------------------+  |
  |  |              Topic Router                           |  |
  |  |  agent.*  --> [LoggingHandler, MetricsHandler]      |  |
  |  |  pipeline.* --> [LoggingHandler, NotificationHandler]|  |
  |  |  approval.* --> [NotificationHandler]               |  |
  |  |  cost.*    --> [MetricsHandler, NotificationHandler] |  |
  |  |  *         --> [EventStore] (all events persisted)  |  |
  |  +----------------------------------------------------+  |
  +-----------------------------------------------------------+
       |           |              |              |
       v           v              v              v
  +--------+ +----------+ +-----------+ +------------+
  | Logger | | Metrics  | | Notifier  | | EventStore |
  | (stdout| | (Prom/   | | (Slack/   | | (.jsonl    |
  |  /file)| |  Grafana)| |  email)   | |  on disk)  |
  +--------+ +----------+ +-----------+ +------------+
```

---

## 12. Data Models

### 12.1 Overview

This section defines the complete data models used throughout CodeBot. These models
represent the core domain entities and are used for persistence, inter-agent communication,
and API contracts.

### 12.2 Core Data Models

```
+-----------------------------------------------------------------------+
|                          Entity Relationship Diagram                  |
+-----------------------------------------------------------------------+

  +-------------+       +-------------+       +------------------+
  |   Project   |1----*>|    Task     |1----*>| AgentExecution   |
  +------+------+       +------+------+       +--------+---------+
         |                     |                       |
         |                     |1                      |1
         |                     |                       |
         |               +-----v------+          +-----v---------+
         |               |CodeArtifact|          |  TestResult   |
         |               +-----+------+          +-----+---------+
         |                     |                       |
         |1                    |*                      |*
         |               +-----v------+          +-----v---------+
  +------v------+        |ReviewComment|          |SecurityFinding|
  |  Pipeline   |        +------------+          +---------------+
  +------+------+
         |1
         |
  +------v--------+     +--------------+
  | PipelinePhase |*--->|  Checkpoint  |
  +---------------+     +--------------+
```

### 12.3 Project

```python
@dataclass
class Project:
    """Root entity representing a software project managed by CodeBot."""

    id: str                              # UUID
    name: str                            # Human-readable project name
    description: str                     # Project description
    repo_url: Optional[str]              # Git repository URL
    repo_path: str                       # Local filesystem path
    tech_stack: TechStack                # Detected/configured technology stack
    config: ProjectConfig                # CodeBot configuration
    status: ProjectStatus                # active, paused, completed, failed
    created_at: datetime
    updated_at: datetime
    owner: str                           # User who created the project
    tags: List[str]                      # Organizational tags
    metadata: Dict[str, Any]             # Extensible metadata


@dataclass
class TechStack:
    """Technology stack configuration."""

    languages: List[str]                 # ["python", "typescript"]
    frameworks: List[str]                # ["fastapi", "react"]
    databases: List[str]                 # ["postgresql", "redis"]
    infrastructure: List[str]            # ["docker", "kubernetes"]
    package_managers: List[str]          # ["pip", "npm"]
    test_frameworks: List[str]           # ["pytest", "vitest"]
    ci_cd: Optional[str]                # "github-actions"


@dataclass
class ProjectConfig:
    """CodeBot-specific project configuration."""

    pipeline_template: str               # Which pipeline to use
    model_preferences: Dict[str, str]    # Agent role -> model overrides
    token_budget: int                    # Global token budget
    cost_limit_usd: float               # Maximum cost allowed
    security_thresholds: SecurityThresholds
    coverage_thresholds: CoverageThresholds
    human_gates: List[str]              # Phases requiring human approval
    reviewers: List[str]                # GitHub users for PR review
    notification_channels: List[str]    # Where to send notifications


class ProjectStatus(Enum):
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"
```

### 12.4 Task

```python
@dataclass
class Task:
    """An atomic unit of work assigned to an agent."""

    id: str                              # UUID
    project_id: str                      # FK to Project
    parent_task_id: Optional[str]        # FK for sub-tasks
    title: str                           # Brief task description
    description: str                     # Detailed description with acceptance criteria
    type: TaskType                       # feature, bugfix, refactor, test, docs, etc.
    status: TaskStatus                   # pending, in_progress, completed, failed, blocked
    priority: int                        # 1 (highest) to 5 (lowest)
    assigned_agent: Optional[str]        # Agent role assigned to this task
    phase: str                           # Pipeline phase this task belongs to
    dependencies: List[str]              # Task IDs this depends on
    acceptance_criteria: List[str]       # Conditions for task completion
    estimated_tokens: int                # Estimated token usage
    actual_tokens: int                   # Actual token usage
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[TaskResult]         # Outcome data
    metadata: Dict[str, Any]


class TaskType(Enum):
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    TEST = "test"
    DOCUMENTATION = "documentation"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    RESEARCH = "research"
    DESIGN = "design"
    REVIEW = "review"


class TaskStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """Outcome of task execution."""

    success: bool
    outputs: Dict[str, Any]              # Task-specific output data
    artifacts: List[str]                 # IDs of created CodeArtifacts
    error: Optional[str]
    duration_ms: int
    tokens_used: int
    cost_usd: float
```

### 12.5 Agent & AgentExecution

```python
@dataclass
class Agent:
    """Configuration and state of an agent instance."""

    id: str                              # UUID
    role: AgentRole                      # One of the 14 agent types
    name: str                            # Human-readable name
    system_prompt: str                   # System prompt template
    model: str                           # Primary LLM model
    fallback_models: List[str]           # Fallback model chain
    tools: List[ToolConfig]              # Available tools
    token_budget: int                    # Maximum tokens for this agent
    retry_policy: RetryPolicy            # Retry configuration
    timeout_seconds: int                 # Execution timeout
    status: AgentStatus                  # idle, running, failed, disabled
    metadata: Dict[str, Any]


class AgentRole(Enum):
    ORCHESTRATOR = "orchestrator"
    PLANNER = "planner"
    RESEARCHER = "researcher"
    ARCHITECT = "architect"
    DESIGNER = "designer"
    FRONTEND_DEV = "frontend_dev"
    BACKEND_DEV = "backend_dev"
    MIDDLEWARE_DEV = "middleware_dev"
    INFRA_ENGINEER = "infra_engineer"
    SECURITY_AUDITOR = "security_auditor"
    CODE_REVIEWER = "code_reviewer"
    TESTER = "tester"
    DEBUGGER = "debugger"
    DOC_WRITER = "doc_writer"


@dataclass
class AgentExecution:
    """Record of a single agent execution."""

    id: str                              # UUID
    agent_id: str                        # FK to Agent
    task_id: str                         # FK to Task
    project_id: str                      # FK to Project
    phase: str                           # Pipeline phase
    model_used: str                      # Actual model used (may differ due to fallback)
    status: ExecutionStatus              # running, completed, failed, timeout
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    input_summary: str                   # Summarized input for audit
    output_summary: str                  # Summarized output for audit
    tool_calls: List[ToolCallRecord]     # Tools invoked during execution
    errors: List[ErrorRecord]            # Errors encountered
    retry_count: int                     # Number of retries
    worktree_path: Optional[str]         # Git worktree used
    files_modified: List[str]            # Files changed during execution


class ExecutionStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ToolCallRecord:
    """Record of a single tool invocation."""

    tool_name: str
    arguments: Dict[str, Any]
    result_summary: str
    duration_ms: int
    success: bool
    error: Optional[str]
    timestamp: datetime
```

### 12.6 CodeArtifact

```python
@dataclass
class CodeArtifact:
    """A code file or resource produced by an agent."""

    id: str                              # UUID
    project_id: str                      # FK to Project
    task_id: str                         # FK to Task
    agent_execution_id: str              # FK to AgentExecution
    path: str                            # File path relative to project root
    language: str                        # Programming language
    framework: Optional[str]             # Framework (react, fastapi, etc.)
    artifact_type: ArtifactType          # source, test, config, migration, docs
    content_hash: str                    # SHA-256 of file content
    lines_of_code: int                   # LOC count
    created_at: datetime
    updated_at: datetime
    version: int                         # Increments on each modification
    previous_version_id: Optional[str]   # FK to previous version
    metadata: Dict[str, Any]


class ArtifactType(Enum):
    SOURCE = "source"                    # Application source code
    TEST = "test"                        # Test files
    CONFIG = "config"                    # Configuration files
    MIGRATION = "migration"              # Database migrations
    DOCUMENTATION = "documentation"      # Documentation files
    INFRASTRUCTURE = "infrastructure"    # IaC files (Terraform, Dockerfile)
    SCHEMA = "schema"                    # API schemas (OpenAPI, GraphQL)
    ASSET = "asset"                      # Static assets (CSS, images)
```

### 12.7 TestResult

```python
@dataclass
class TestResult:
    """Results from test execution."""

    id: str                              # UUID
    project_id: str                      # FK to Project
    agent_execution_id: str              # FK to AgentExecution
    framework: str                       # pytest, vitest, playwright, jest
    test_type: TestType                  # unit, integration, e2e, regression
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration_ms: int
    coverage_line_pct: Optional[float]   # Line coverage percentage
    coverage_branch_pct: Optional[float] # Branch coverage percentage
    test_cases: List[TestCaseResult]     # Individual test case results
    created_at: datetime
    log_output: str                      # Raw test output
    metadata: Dict[str, Any]


@dataclass
class TestCaseResult:
    """Result for a single test case."""

    name: str                            # Full test name (including path)
    status: TestCaseStatus               # passed, failed, skipped, error
    duration_ms: float
    file_path: str                       # Test file path
    error_message: Optional[str]         # Error/failure message
    stack_trace: Optional[str]           # Full stack trace on failure
    assertions: int                      # Number of assertions
    stdout: Optional[str]               # Captured stdout
    stderr: Optional[str]               # Captured stderr


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    REGRESSION = "regression"
    PERFORMANCE = "performance"
    SECURITY = "security"
    UI_COMPONENT = "ui_component"    # UI Component Testing (visual + interaction)
    SMOKE = "smoke"                  # Smoke Testing (critical path verification)
    MUTATION = "mutation"            # Mutation Testing (test quality validation)


class TestCaseStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"
```

### 12.8 SecurityFinding

```python
@dataclass
class SecurityFinding:
    """A security issue found by scanning tools."""

    id: str                              # UUID
    project_id: str                      # FK to Project
    scan_id: str                         # FK to security scan execution
    tool: str                            # semgrep, trivy, gitleaks, etc.
    rule_id: str                         # Scanner-specific rule identifier
    severity: Severity                   # critical, high, medium, low, info
    title: str                           # Brief description
    description: str                     # Detailed explanation
    file_path: str                       # Affected file
    line_start: int                      # Start line number
    line_end: int                        # End line number
    code_snippet: str                    # Vulnerable code extract
    cwe: List[str]                       # CWE identifiers
    cvss_score: Optional[float]          # CVSS v3 score (0.0 - 10.0)
    fix_recommendation: str              # Suggested remediation
    is_false_positive: bool              # Marked as false positive
    status: FindingStatus                # open, fixed, false_positive, accepted
    fixed_in_execution_id: Optional[str] # FK to AgentExecution that fixed it
    created_at: datetime
    resolved_at: Optional[datetime]


class Severity(Enum):
    CRITICAL = "critical"                # CVSS 9.0-10.0
    HIGH = "high"                        # CVSS 7.0-8.9
    MEDIUM = "medium"                    # CVSS 4.0-6.9
    LOW = "low"                          # CVSS 0.1-3.9
    INFO = "info"                        # Informational

class FindingStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    FALSE_POSITIVE = "false_positive"
    RISK_ACCEPTED = "risk_accepted"
    WONT_FIX = "wont_fix"
```

### 12.9 ReviewComment

```python
@dataclass
class ReviewComment:
    """A code review comment from the Code Reviewer agent."""

    id: str                              # UUID
    project_id: str                      # FK to Project
    agent_execution_id: str              # FK to AgentExecution
    artifact_id: str                     # FK to CodeArtifact being reviewed
    file_path: str                       # File being commented on
    line_start: int                      # Start line of the comment
    line_end: int                        # End line of the comment
    comment_type: CommentType            # issue, suggestion, praise, question
    severity: CommentSeverity            # blocker, major, minor, trivial
    category: str                        # naming, logic, performance, security, style
    title: str                           # Brief comment title
    body: str                            # Detailed comment text
    suggested_change: Optional[str]      # Suggested code replacement
    resolved: bool                       # Whether the comment has been addressed
    resolution: Optional[str]            # How it was resolved
    created_at: datetime
    resolved_at: Optional[datetime]


class CommentType(Enum):
    ISSUE = "issue"                      # Something that must be fixed
    SUGGESTION = "suggestion"            # Improvement recommendation
    PRAISE = "praise"                    # Positive feedback
    QUESTION = "question"                # Needs clarification
    NITPICK = "nitpick"                  # Minor style issue


class CommentSeverity(Enum):
    BLOCKER = "blocker"                  # Must fix before merge
    MAJOR = "major"                      # Should fix before merge
    MINOR = "minor"                      # Nice to fix
    TRIVIAL = "trivial"                  # Optional
```

### 12.10 Pipeline & PipelinePhase

```python
@dataclass
class Pipeline:
    """A pipeline execution instance."""

    id: str                              # UUID
    project_id: str                      # FK to Project
    template_name: str                   # Pipeline template used
    status: PipelineStatus               # queued, running, completed, failed, paused
    current_phase: str                   # Current phase name
    current_phase_idx: int               # Current phase index
    total_phases: int                    # Total number of phases
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: int
    total_tokens_used: int
    total_cost_usd: float
    phases: List[PipelinePhaseRecord]    # Phase execution records
    config: PipelineConfig               # Pipeline configuration snapshot
    error: Optional[str]                 # Error message if failed
    triggered_by: str                    # "user", "api", "schedule"
    metadata: Dict[str, Any]


class PipelineStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"                    # Waiting for human approval
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelinePhaseRecord:
    """Record of a single phase execution within a pipeline."""

    id: str                              # UUID
    pipeline_id: str                     # FK to Pipeline
    phase_name: str                      # Phase name (plan, research, etc.)
    phase_idx: int                       # Phase index
    status: PhaseStatus                  # pending, running, completed, failed, skipped
    agents_executed: List[str]           # Agent execution IDs
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: int
    tokens_used: int
    cost_usd: float
    error: Optional[str]
    human_gate_result: Optional[str]     # approved, rejected, timeout
    metadata: Dict[str, Any]


class PhaseStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"
```

### 12.11 Checkpoint

```python
@dataclass
class Checkpoint:
    """Saved pipeline state for resume capability."""

    id: str                              # UUID
    pipeline_id: str                     # FK to Pipeline
    project_id: str                      # FK to Project
    phase_idx: int                       # Phase index at checkpoint time
    phase_name: str                      # Phase name
    state_snapshot: Dict[str, Any]       # Complete SharedState serialized
    agent_results: List[Dict[str, Any]]  # Results from completed agents
    created_at: datetime
    size_bytes: int                      # Size of serialized state
    is_valid: bool                       # Whether this checkpoint can be resumed
    resume_count: int                    # Times this checkpoint has been resumed
    metadata: Dict[str, Any]
```

### 12.12 Complete Data Model Relationship Diagram

```
+-------------------+
|     Project       |
|-------------------|
| id (PK)           |
| name              |         +--------------------+
| description       |         |      Pipeline      |
| repo_url          |1       *|--------------------+
| repo_path         +---------+ id (PK)            |
| tech_stack (JSON) |         | project_id (FK)    |      +-----------------+
| config (JSON)     |         | template_name      |      |   Checkpoint    |
| status            |         | status             |1    *|-----------------|
| created_at        |         | current_phase      +------+ id (PK)         |
| updated_at        |         | total_cost_usd     |      | pipeline_id (FK)|
| owner             |         | started_at         |      | phase_idx       |
+--------+----------+         | completed_at       |      | state_snapshot  |
         |                    +---------+----------+      | created_at      |
         |                              |                  +-----------------+
         |                              |1
         |1                             |
         |                    +---------v----------+
         |                    |  PipelinePhase     |
         |                    |--------------------|
         |                    | id (PK)            |
         |                    | pipeline_id (FK)   |
         |                    | phase_name         |
         |                    | status             |
         |                    | duration_ms        |
         |                    | cost_usd           |
         |                    +--------------------+
         |
         |*
+--------v----------+
|       Task        |
|-------------------|
| id (PK)           |
| project_id (FK)   |         +--------------------+
| parent_task_id    |1       *| AgentExecution     |
| title             +---------+--------------------+
| description       |         | id (PK)            |
| type              |         | agent_id (FK)      |
| status            |         | task_id (FK)       |
| priority          |         | model_used         |
| assigned_agent    |         | status             |
| phase             |         | duration_ms        |
| dependencies      |         | total_tokens       |
| created_at        |         | cost_usd           |
+--------+----------+         | tool_calls (JSON)  |
         |                    | files_modified     |
         |                    +---------+----------+
         |1                             |
         |                              |1
+--------v----------+                   |
|   CodeArtifact    |          +--------v-----------+
|-------------------|          |    TestResult       |
| id (PK)           |          |--------------------|
| project_id (FK)   |          | id (PK)            |
| task_id (FK)      |          | project_id (FK)    |
| agent_exec_id(FK) |          | agent_exec_id (FK) |
| path              |          | framework          |
| language          |          | total_tests        |
| artifact_type     |          | passed             |
| content_hash      |          | failed             |
| lines_of_code     |          | coverage_line_pct  |
| version           |          | test_cases (JSON)  |
+--------+----------+          +--------------------+
         |
         |1
         |                    +---------------------+
         |                    |  SecurityFinding     |
         +--------------------+---------------------|
         |*                   | id (PK)              |
+--------v----------+        | project_id (FK)      |
|  ReviewComment    |        | tool                  |
|-------------------|        | severity              |
| id (PK)           |        | file_path             |
| project_id (FK)   |        | cwe                   |
| artifact_id (FK)  |        | cvss_score            |
| file_path         |        | fix_recommendation    |
| comment_type      |        | status                |
| severity          |        +---------------------+
| body              |
| suggested_change  |
| resolved          |
+-------------------+
```

### 12.13 Data Persistence Strategy

| Entity | Primary Storage | Secondary Storage | Retention |
|--------|----------------|-------------------|-----------|
| Project | SQLite/PostgreSQL | -- | Indefinite |
| Task | SQLite/PostgreSQL | -- | Indefinite |
| Agent | In-memory + config YAML | -- | Session |
| AgentExecution | SQLite/PostgreSQL | Event log (JSONL) | 90 days |
| CodeArtifact | Git repository | SQLite metadata | Indefinite |
| TestResult | SQLite/PostgreSQL | -- | 90 days |
| SecurityFinding | SQLite/PostgreSQL | -- | Indefinite |
| ReviewComment | SQLite/PostgreSQL | -- | Indefinite |
| Pipeline | SQLite/PostgreSQL | -- | Indefinite |
| PipelinePhase | SQLite/PostgreSQL | -- | Indefinite |
| Checkpoint | Filesystem (JSON) | -- | 30 days |
| Events | JSONL files | -- | 90 days |
| Vector Embeddings | LanceDB (dev) / Qdrant (prod) | -- | Indefinite |
| Memory | JSONL files + vectors | -- | Indefinite |

---

## 13. Error Handling Strategy

### 13.1 Error Taxonomy

| Category | Examples | Strategy | Details |
|----------|----------|----------|---------|
| Transient | LLM rate limit, network timeout | Retry with exponential backoff | Max 3 retries, initial delay 1s, backoff factor 2x |
| Recoverable | Test failure, lint error | Route to Debugger | Automated fix via Debug & Fix Loop (Section 10) |
| Blocking | Missing dependency, invalid config | Pause pipeline, notify user | Human-in-the-loop resolution required |
| Fatal | Invalid credentials, disk full, OOM | Stop pipeline, preserve state, alert | Checkpoint state before termination; alert via configured channels |
| Quality Gate | Coverage below threshold, security findings above severity | Block phase transition | Route to appropriate fix agent (Tester, Security Auditor, etc.) |

### 13.2 Retry Policy

```python
class RetryPolicy:
    max_retries: int = 3
    initial_delay_seconds: float = 1.0
    backoff_factor: float = 2.0
    max_delay_seconds: float = 30.0
    retryable_exceptions: List[Type[Exception]] = [
        RateLimitError,
        NetworkTimeoutError,
        ProviderUnavailableError,
    ]
```

### 13.3 Dead Letter Queue (DLQ)

Messages that fail after all retry attempts are routed to a Dead Letter Queue for manual inspection:

- Failed messages are persisted with full context (agent, input, error trace)
- DLQ entries are surfaced in status reports by the Project Manager Agent
- Operators can replay, discard, or manually resolve DLQ entries

### 13.4 Circuit Breaker Pattern

Each LLM provider connection is wrapped in a circuit breaker:

- **Closed** (normal): Requests pass through; failures counted
- **Open** (tripped): After 5 consecutive failures, all requests short-circuit to fallback provider for 60s
- **Half-Open** (probe): After cooldown, a single probe request is sent; success resets to Closed, failure returns to Open

---

## 14. Agent Lifecycle Management

### 14.1 Agent States

```
  IDLE → INITIALIZING → RUNNING → WAITING → COMPLETED
                                      ↓          ↓
                                   FAILED    TERMINATED
```

| State | Description |
|-------|-------------|
| IDLE | Agent registered but not yet assigned a task |
| INITIALIZING | Loading context, tools, and system prompt |
| RUNNING | Actively executing task (LLM calls, tool invocations) |
| WAITING | Blocked on external input (human approval, dependency) |
| COMPLETED | Task finished successfully; results emitted |
| FAILED | Task failed after retries/escalation exhausted |
| TERMINATED | Agent forcefully stopped (timeout, resource limit, cancellation) |

### 14.2 Lifecycle Flow

```
Spawn → Initialize (load context, tools, prompt)
      → Execute (run task, invoke tools, call LLM)
      → Checkpoint (persist intermediate state)
      → Terminate (release resources, emit completion event)
```

### 14.3 Health Checks

- Health check heartbeat every **30 seconds**
- Unresponsive agents (2 missed heartbeats) are automatically restarted
- Restart preserves last checkpoint state for seamless resumption

### 14.4 Resource Limits

| Resource | Limit | Enforcement |
|----------|-------|-------------|
| Token budget | Per-agent configurable (default 100K tokens) | Hard cutoff; agent FAILED if exceeded |
| Execution timeout | Per-agent configurable (default 30 min) | Agent TERMINATED on timeout |
| Memory limit | Per-agent configurable (default 2 GB) | Agent TERMINATED on OOM |

---

## 15. Communication Protocol

### 15.1 Inter-Agent Message Format

All agent-to-agent communication uses a standardized JSON envelope:

```json
{
  "id": "msg-uuid-v4",
  "version": "1.0",
  "type": "task_handoff | result | error | clarification | approval_request | broadcast",
  "source_agent": "planner",
  "target_agent": "researcher",
  "correlation_id": "pipeline-run-uuid",
  "timestamp": "2026-03-18T12:00:00Z",
  "priority": "normal | high | critical",
  "payload": {
    "task": "...",
    "data": {}
  },
  "metadata": {
    "pipeline_id": "...",
    "phase": "...",
    "retry_count": 0
  }
}
```

### 15.2 Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `task_handoff` | Source → Target | Assign a task to the next agent in the pipeline |
| `result` | Target → Source | Return completed work product |
| `error` | Any → Orchestrator | Report an unrecoverable error |
| `clarification` | Agent → Human/Agent | Request additional information |
| `approval_request` | Agent → Human Gate | Request human approval to proceed |
| `broadcast` | Agent → All | Notify all agents (e.g., status updates from Project Manager) |

### 15.3 Delivery Guarantees

- **At-least-once delivery** via the event bus; consumers must be idempotent
- **Per source-target pair ordering** guarantee (messages between any two agents are delivered in send order)
- **Large messages** (payload > 100KB) are stored in blob storage; the message carries a reference URI instead of inline data

---

## 16. Platform Observability

### 16.1 Metrics

| Metric | Tool | Description |
|--------|------|-------------|
| Agent throughput | Prometheus + Grafana | Tasks completed per agent per unit time |
| Token usage | Prometheus + Grafana | Tokens consumed per agent, per model, per pipeline run |
| Cost tracking | Prometheus + Grafana | Dollar cost per agent, per pipeline run, cumulative |
| Latency | Prometheus + Grafana | P50/P95/P99 latency per agent execution, per LLM call |
| Error rates | Prometheus + Grafana | Errors per agent, per error category, over time |

### 16.2 Logging

- **Format:** Structured JSON to stdout
- **Fields:** timestamp, level, agent_id, pipeline_id, correlation_id, message, metadata
- **Levels:** DEBUG, INFO, WARN, ERROR, FATAL
- Log aggregation via standard container log drivers (e.g., Fluentd, Loki)

### 16.3 Distributed Tracing

- **Protocol:** OpenTelemetry SDK
- **Backend:** Jaeger
- **Scope:** End-to-end request tracing across all agents in a pipeline run
- Each agent execution creates a child span under the pipeline root span
- LLM calls, tool invocations, and event bus messages are traced as sub-spans

### 16.4 Alerting

| Alert | Condition | Channel |
|-------|-----------|---------|
| Budget exhaustion | Token or dollar budget > 90% consumed | Prometheus Alertmanager → configured notification channel |
| Agent failure | Agent in FAILED state after retries | Prometheus Alertmanager |
| Pipeline stall | No agent state change for > 10 minutes | Prometheus Alertmanager |
| Error rate spike | Error rate > 20% over 5-minute window | Prometheus Alertmanager |

---

## 17. Data Retention Policy

| Data Type | Retention | Cleanup Strategy |
|-----------|-----------|------------------|
| Project data | Indefinite | Manual delete |
| Agent execution logs | 90 days | Auto-purge |
| LLM request/response | 30 days | Auto-purge |
| Event bus messages | 7 days | Auto-purge |
| Pipeline checkpoints | Until archived | Cascade delete |
| Build artifacts | 30 days | Auto-purge |
| Security scan results | 1 year | Auto-archive |

Auto-purge jobs run daily at 02:00 UTC. Cascade delete removes checkpoints when their parent pipeline is archived or deleted. Auto-archive moves data to cold storage (compressed JSONL) before purging from primary storage.

---

## 18. Agent Safety Guardrails

### 18.1 Sandboxing

CodeBot includes a **built-in sandbox execution system** for agent isolation:

- **Docker containers per agent**: each agent execution runs in an isolated Docker
  container with a dedicated filesystem, ensuring no cross-contamination between agents
- **gVisor / Kata isolation**: production deployments use gVisor (default) or Kata
  Containers for defense-in-depth kernel-level isolation beyond standard container boundaries
- **Live preview with hot-reload**: sandbox containers expose a preview port for
  front-end agents, enabling real-time hot-reload of UI changes during development
- **Skill Creator**, **Hook Creator**, and **Tool Creator** agents execute in sandboxed environments
- Sandboxed agents have no access to host filesystem, network (except allowlisted endpoints), or other agent memory

### 18.2 Artifact Review

- All artifacts created by sandboxed agents (skills, hooks, tools) are held in a **staging area**
- Artifacts must pass automated validation and human review before activation in the pipeline
- Validation includes: syntax check, security scan (Semgrep), dependency audit

### 18.3 Rate Limiting

- Maximum **5 new artifacts** per pipeline run (skills + hooks + tools combined)
- Exceeding the limit triggers a blocking error routed to the Orchestrator

### 18.4 Restricted Capabilities

Sandboxed agents are explicitly denied the following:

- **No credential access:** Cannot read, write, or reference secrets, API keys, or tokens
- **No prompt modification:** Cannot alter system prompts of other agents
- **No security bypass:** Cannot disable or modify security gates, scanners, or audit rules

---

## 19. Authentication & Authorization

### 19.1 Authentication

CodeBot supports dual authentication mechanisms:

| Method | Algorithm | Use Case |
|--------|-----------|----------|
| JWT Bearer Token | RS256 (RSA + SHA-256) | Interactive user sessions (UI, CLI) |
| API Key | HMAC-SHA256 | Programmatic access (CI/CD, scripts) |

- **Session expiry:** 1 hour (access token TTL)
- **Refresh token rotation:** Each refresh issues a new refresh token and invalidates the previous one
- **Token storage:** Access tokens in memory; refresh tokens in HttpOnly secure cookies (UI) or encrypted local config (CLI)

### 19.2 Authorization (RBAC)

| Role | Permissions |
|------|-------------|
| `admin` | Full access: manage users, configure pipelines, view all projects, modify settings |
| `user` | Create/run pipelines, view own projects, manage own API keys |
| `viewer` | Read-only access to assigned projects, view reports and logs |

### 19.3 Multi-Factor Authentication (MFA)

- **Optional TOTP-based MFA** for admin accounts (RFC 6238)
- Enforced on first login after role elevation to admin
- Backup recovery codes (10 single-use codes) generated at MFA enrollment

---

## Appendix A: Technology Stack Summary

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Core Language | Python 3.12+ | Async support, AI ecosystem |
| Graph Engine | LangGraph (primary) | Agent orchestration as composable graphs |
| LLM Gateway | LiteLLM | Unified proxy for OpenAI, Anthropic, Google, self-hosted models |
| LLM Providers | OpenAI, Anthropic, Google APIs (via LiteLLM) | Multi-model strategy |
| CLI Agents (integration) | Claude Code, Codex CLI, Gemini CLI | Mandatory external integrations for coding tasks |
| Context Store (built-in) | SQLite + file tree | L0/L1/L2 hierarchical context (inspired by OpenViking patterns) |
| Episodic Memory (built-in) | LanceDB/Qdrant + SQLite | Persistent memory with lifecycle hooks, semantic compression, progressive disclosure (inspired by claude-mem patterns) |
| Sandbox Execution (built-in) | Docker + gVisor/Kata | Per-agent container isolation with live preview and hot-reload |
| Vector Store | LanceDB (dev), Qdrant (prod) | Embedding retrieval |
| Code Parsing | Tree-sitter | Multi-language AST parsing |
| Git Integration | GitPython + subprocess | Worktree management |
| Security: SAST | Semgrep + SonarQube | Comprehensive static analysis |
| Security: DAST | Shannon | Dynamic testing |
| Security: SCA | Trivy + OpenSCA | Dependency scanning |
| Security: Secrets | Gitleaks | Secret detection |
| Security: License | ScanCode / FOSSology / ORT | License compliance |
| Testing | pytest, vitest, Playwright | Multi-framework support |
| MCP Framework | FastMCP 2.0 | Model Context Protocol server/client framework |
| Event Bus | NATS | Pub/sub messaging for inter-agent communication |
| Task Queue | TaskIQ + TaskIQ-NATS | Distributed task queue over NATS |
| Durable Execution | Temporal (temporalio) | Durable workflow orchestration with retries and checkpoints |
| Observability | Langfuse | LLM observability, cost tracking, prompt analytics |
| Persistence | PostgreSQL (prod), SQLite (dev) | Flexible storage |
| Cache | Redis | Caching and session storage |
| Analytics DB | DuckDB | Analytical queries and reporting |
| Event Storage | JSONL files + NATS JetStream | Durable, auditable event log |
| Configuration | YAML | Human-readable pipeline defs |

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| Agent | An AI-powered component with a specific role in the SDLC pipeline |
| CodeBot | The autonomous end-to-end software development platform |
| Context Adapter | MASFactory pattern for assembling agent-specific context |
| DAG | Directed Acyclic Graph |
| DAST | Dynamic Application Security Testing |
| Edge | Connection between graph nodes carrying data or control signals |
| Gate | A checkpoint requiring pass/fail evaluation or human approval |
| Graph | The core data structure modeling agent workflows |
| Human-in-the-Loop | Pipeline pause requiring human decision before proceeding |
| Episodic Memory | Built-in persistent memory system with lifecycle hooks, semantic compression, and progressive disclosure (inspired by claude-mem patterns) |
| L0/L1/L2 | Three tiers of built-in hierarchical context loading (always/on-demand/RAG), inspired by OpenViking patterns |
| MASFactory | Multi-Agent System Factory (arXiv:2603.06007) |
| MCP | Model Context Protocol for tool and resource injection |
| Node | A computational unit in the agent graph |
| Phase | A stage in the SDLC pipeline (plan, research, code, test, etc.) |
| Pipeline | End-to-end execution sequence of SDLC phases |
| SAST | Static Application Security Testing |
| SCA | Software Composition Analysis |
| SDLC | Software Development Lifecycle |
| SharedState | Thread-safe state dictionary shared between graph nodes |
| Worktree | Isolated git working directory for parallel agent execution |

---

*Document generated for CodeBot v2.3 -- Last updated: 2026-03-18*
