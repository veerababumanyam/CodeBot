---
skill: codebot-graph-engine
title: CodeBot Graph Engine
description: >
  How to work with the CodeBot graph engine — the core runtime that models
  the SDLC as a directed computation graph. Covers node types, edge types,
  graph composition, execution semantics, and testing.
tags:
  - codebot
  - graph-engine
  - sdlc
  - langgraph
  - directed-graph
version: "1.0"
---

# CodeBot Graph Engine

## Overview

The graph engine is CodeBot's core runtime. It models the entire software
development lifecycle (SDLC) as a directed computation graph where each
pipeline stage (S0 through S10) is expressed as a subgraph. The engine
uses LangGraph as its primary execution backend.

**Source location:** `apps/server/src/codebot/graph/`

**Key files:**

| File | Purpose |
|------|---------|
| `engine.py` | Top-level engine: build, validate, execute graphs |
| `graph.py` | `DirectedGraph` data structure and construction helpers |
| `node.py` | `Node` base class and all node type implementations |
| `edge.py` | `Edge` class and `EdgeType` enum |
| `loop.py` | `LoopNode` and `ExperimentLoopNode` |
| `switch.py` | `SwitchNode` conditional routing |
| `scheduler.py` | Kahn's algorithm topological sort and layer scheduling |
| `templates.py` | Pre-built graph templates (pipeline stages, common patterns) |

---

## 1. Core Data Structures

### DirectedGraph

```python
class DirectedGraph:
    id: str               # Unique graph identifier
    name: str             # Human-readable name
    nodes: dict[str, Node]  # node_id -> Node
    edges: list[Edge]     # Connections between nodes
    state: SharedState    # Thread-safe shared state
    metadata: dict        # Arbitrary metadata
```

`SharedState` is thread-safe — any node can read/write state safely during
parallel execution.

### Node

```python
class Node:
    id: str
    name: str
    node_type: NodeType
    inputs: list[str]
    outputs: list[str]
    config: dict
```

### Edge

```python
class Edge:
    source_id: str
    target_id: str
    edge_type: EdgeType
    condition: Optional[Callable]  # For conditional routing
```

---

## 2. Node Types

The `NodeType` enum defines all node categories:

```python
class NodeType(str, Enum):
    AGENT          = "agent"
    SUBGRAPH       = "subgraph"
    LOOP           = "loop"
    SWITCH         = "switch"
    HUMAN_IN_LOOP  = "human_in_loop"
    PARALLEL       = "parallel"
    MERGE          = "merge"
    CHECKPOINT     = "checkpoint"
    TRANSFORM      = "transform"
    GATE           = "gate"
```

### Class Hierarchy

```
Node (base)
 +-- AgentNode         wraps an LLM agent
 +-- SubGraphNode      embeds a full DirectedGraph
 +-- LoopNode          iterating sub-graph
 |    +-- ExperimentLoopNode  loop with keep/discard semantics
 +-- SwitchNode        conditional routing
 +-- HumanInLoopNode   pauses for human approval
```

### Creating New Node Types

To add a custom node type:

1. Add the type name to the `NodeType` enum in `node.py`.
2. Subclass `Node` and implement `execute(state: SharedState) -> SharedState`.
3. Register the type in the engine's node factory (`engine.py`).
4. Add YAML tag support in `templates.py` if needed.

```python
# node.py

class ValidationNode(Node):
    """Runs a validation suite and writes results to state."""

    node_type = NodeType.TRANSFORM  # or a new enum value

    def __init__(self, id: str, name: str, validator: Callable, **kwargs):
        super().__init__(id=id, name=name, node_type=self.node_type, **kwargs)
        self.validator = validator

    async def execute(self, state: SharedState) -> SharedState:
        result = await self.validator(state)
        state.set(f"{self.id}.result", result)
        return state
```

---

## 3. Defining Graph Structures

### Python API

```python
from codebot.graph.graph import DirectedGraph
from codebot.graph.node import AgentNode, NodeType
from codebot.graph.edge import Edge, EdgeType

# Create graph
graph = DirectedGraph(id="my-pipeline", name="My Pipeline")

# Add nodes
planner = AgentNode(
    id="planner",
    name="Planning Agent",
    agent_id="planner-v1",
    tools=["file_search", "codebase_index"],
    model="Codex-sonnet-4-20250514",
)
graph.add_node(planner)

coder = AgentNode(
    id="coder",
    name="Coding Agent",
    agent_id="coder-v1",
    tools=["file_write", "terminal"],
    model="Codex-sonnet-4-20250514",
)
graph.add_node(coder)

# Connect them
graph.add_edge(Edge(
    source_id="planner",
    target_id="coder",
    edge_type=EdgeType.STATE_FLOW,
))
```

### YAML Definition

Graphs can be defined declaratively in YAML. The engine loads and validates
these at startup.

```yaml
graph:
  id: feature-pipeline
  name: Feature Implementation Pipeline

  nodes:
    planner:
      type: agent
      agent_id: planner-v1
      tools: [file_search, codebase_index]
      model: Codex-sonnet-4-20250514

    coder:
      type: agent
      agent_id: coder-v1
      tools: [file_write, terminal]
      model: Codex-sonnet-4-20250514

    reviewer:
      type: agent
      agent_id: reviewer-v1
      tools: [file_read, lint]
      model: Codex-sonnet-4-20250514

    approval:
      type: human_in_loop
      prompt: "Review changes before merge?"

  edges:
    - source: planner
      target: coder
      type: state_flow

    - source: coder
      target: reviewer
      type: state_flow

    - source: reviewer
      target: approval
      type: control_flow
```

---

## 4. Edge Types

| EdgeType | Purpose |
|----------|---------|
| `STATE_FLOW` | Passes shared state from source to target. The primary data channel. |
| `MESSAGE_FLOW` | Passes messages (e.g., agent outputs) between nodes. |
| `CONTROL_FLOW` | Determines execution order without data dependency. |

Use `STATE_FLOW` for most connections. Use `CONTROL_FLOW` when you need
ordering but the downstream node reads state independently.

```python
graph.add_edge(Edge(
    source_id="lint",
    target_id="test",
    edge_type=EdgeType.CONTROL_FLOW,  # test runs after lint, no data dep
))
```

---

## 5. Execution Flow and Layer-Based Parallelism

The scheduler uses **Kahn's algorithm** to produce a topological sort of the
graph, grouping nodes into execution layers.

```
Layer 0: [planner]           -- no dependencies
Layer 1: [coder, designer]   -- both depend only on planner
Layer 2: [reviewer]          -- depends on coder AND designer
Layer 3: [approval]          -- depends on reviewer
```

**Rules:**

- Nodes in the same layer execute in parallel.
- A layer completes before the next layer starts.
- Cycles are rejected at graph validation time (except inside `LoopNode`).

The scheduler is in `scheduler.py`:

```python
from codebot.graph.scheduler import topological_layers

layers = topological_layers(graph)
for layer in layers:
    await asyncio.gather(*[node.execute(state) for node in layer])
```

---

## 6. Loop and Switch Patterns

### LoopNode (debug-fix loop)

A `LoopNode` wraps a body sub-graph and re-executes it until a condition
is met or `max_iterations` is reached. The canonical use is the debug-fix
loop.

```python
from codebot.graph.loop import LoopNode

debug_fix = LoopNode(
    id="debug-fix",
    name="Debug-Fix Loop",
    body=debug_fix_subgraph,       # a DirectedGraph
    condition=lambda state: state.get("tests_passing") is True,
    max_iterations=5,
)
```

YAML:

```yaml
debug_fix:
  type: loop
  max_iterations: 5
  condition: tests_passing == true
  body:
    nodes:
      diagnose:
        type: agent
        agent_id: debugger-v1
      fix:
        type: agent
        agent_id: coder-v1
      test:
        type: agent
        agent_id: tester-v1
    edges:
      - { source: diagnose, target: fix, type: state_flow }
      - { source: fix, target: test, type: state_flow }
```

### ExperimentLoopNode

Extends `LoopNode` with experiment semantics: each iteration runs on a
separate git branch. After each iteration, metrics are compared and the
best result is kept.

```python
from codebot.graph.loop import ExperimentLoopNode

experiment = ExperimentLoopNode(
    id="optimization-experiment",
    name="Performance Optimization",
    body=optimization_subgraph,
    max_iterations=3,
    metric_key="benchmark_score",
    strategy="maximize",  # or "minimize"
)
```

- Creates a git branch per iteration (e.g., `experiment/optimization-experiment/iter-1`).
- Compares `metric_key` across iterations.
- Keeps the winning branch, discards the rest.

### SwitchNode

Routes execution to different branches based on predicates evaluated
against the current state.

```python
from codebot.graph.switch import SwitchNode

router = SwitchNode(
    id="complexity-router",
    name="Route by Complexity",
    cases={
        "simple": lambda state: state.get("complexity") == "low",
        "complex": lambda state: state.get("complexity") == "high",
    },
    default="simple",
)
```

YAML:

```yaml
complexity_router:
  type: switch
  cases:
    simple:
      condition: complexity == "low"
      target: quick_fix
    complex:
      condition: complexity == "high"
      target: full_pipeline
  default: quick_fix
```

---

## 7. Subgraph Composition

`SubGraphNode` embeds a complete `DirectedGraph` inside another graph.
This is how pipeline stages S0-S10 are composed into the top-level
pipeline.

```python
from codebot.graph.node import SubGraphNode

s3_design = SubGraphNode(
    id="s3-design",
    name="S3: Design",
    subgraph=design_stage_graph,   # a full DirectedGraph
)

# Embed in top-level pipeline
pipeline = DirectedGraph(id="pipeline", name="CodeBot Pipeline")
pipeline.add_node(s2_node)
pipeline.add_node(s3_design)
pipeline.add_edge(Edge(
    source_id="s2-planning",
    target_id="s3-design",
    edge_type=EdgeType.STATE_FLOW,
))
```

Subgraphs receive a copy of the parent's `SharedState` on entry and merge
their output state back on exit.

---

## 8. Quality Gates (GATE Nodes)

A `GATE` node enforces quality thresholds before allowing downstream
execution. If the gate fails, execution halts or reroutes.

```yaml
quality_gate:
  type: gate
  conditions:
    - metric: test_coverage
      operator: ">="
      threshold: 80
    - metric: lint_errors
      operator: "=="
      threshold: 0
  on_fail: reroute    # "halt" or "reroute"
  fail_target: fix_issues
```

Python equivalent:

```python
gate = Node(
    id="quality-gate",
    name="Pre-merge Quality Gate",
    node_type=NodeType.GATE,
    config={
        "conditions": [
            {"metric": "test_coverage", "operator": ">=", "threshold": 80},
            {"metric": "lint_errors", "operator": "==", "threshold": 0},
        ],
        "on_fail": "reroute",
        "fail_target": "fix_issues",
    },
)
```

---

## 9. Human-in-the-Loop Integration

`HumanInLoopNode` pauses graph execution and emits a
`HumanApprovalRequired` event. Execution resumes only when a human
provides input.

```python
from codebot.graph.node import HumanInLoopNode

approval = HumanInLoopNode(
    id="deploy-approval",
    name="Deploy Approval",
    prompt="Approve deployment to production?",
    timeout_seconds=3600,  # auto-reject after 1 hour
)
```

When the engine hits this node:

1. Execution suspends. A checkpoint is saved.
2. A `HumanApprovalRequired` event is emitted (WebSocket / webhook).
3. The UI presents the prompt and collected artifacts.
4. On approval, execution resumes from the checkpoint.
5. On rejection, the graph terminates or follows a rejection edge.

---

## 10. Checkpoint and State Management

`CHECKPOINT` nodes persist the full `SharedState` so execution can be
resumed after interruption.

```python
checkpoint = Node(
    id="post-build-checkpoint",
    name="Post-Build Checkpoint",
    node_type=NodeType.CHECKPOINT,
    config={"storage": "redis"},  # or "filesystem", "gcs"
)
```

State management patterns:

```python
# Reading state inside a node
value = state.get("s3.design_doc")

# Writing state
state.set("s4.implementation.files", ["src/main.py", "src/utils.py"])

# Scoped reads (get all keys under a prefix)
s4_state = state.get_scope("s4")
```

Checkpoints are created automatically:
- Before and after every `HUMAN_IN_LOOP` node.
- At the start of each pipeline stage subgraph.
- Manually via `CHECKPOINT` nodes.

---

## 11. Testing Graph Definitions

### Validating Graph Structure

```python
from codebot.graph.engine import GraphEngine

engine = GraphEngine()
graph = engine.load_yaml("path/to/graph.yaml")

# Validates: no cycles, all edge targets exist, required fields present
errors = engine.validate(graph)
assert not errors, f"Graph validation failed: {errors}"
```

### Unit Testing Individual Nodes

```python
import pytest
from codebot.graph.node import AgentNode
from codebot.graph.graph import SharedState

@pytest.mark.asyncio
async def test_agent_node_execution():
    state = SharedState()
    state.set("input.task", "Write a hello world function")

    node = AgentNode(
        id="test-coder",
        name="Test Coder",
        agent_id="coder-v1",
        tools=["file_write"],
        model="Codex-sonnet-4-20250514",
    )

    result_state = await node.execute(state)
    assert result_state.get("test-coder.result") is not None
```

### Integration Testing Full Graphs

```python
@pytest.mark.asyncio
async def test_debug_fix_loop_terminates():
    graph = build_debug_fix_graph()
    engine = GraphEngine()

    state = SharedState()
    state.set("source_code", "def add(a, b): return a - b")
    state.set("test_spec", "assert add(1, 2) == 3")

    final_state = await engine.run(graph, state)

    assert final_state.get("tests_passing") is True
    assert final_state.get("debug-fix.iterations") <= 5
```

### Testing YAML Definitions

```python
def test_yaml_graph_loads():
    engine = GraphEngine()
    graph = engine.load_yaml("graphs/feature-pipeline.yaml")

    assert len(graph.nodes) == 4
    assert "planner" in graph.nodes
    assert len(graph.edges) == 3

    layers = topological_layers(graph)
    assert layers[0][0].id == "planner"  # planner has no deps
```

---

## Quick Reference

| Task | Approach |
|------|----------|
| Add a new agent step | Create `AgentNode`, add to graph, connect with `STATE_FLOW` edge |
| Run steps in parallel | Ensure nodes have no edges between them; scheduler auto-parallelizes |
| Retry on failure | Wrap in `LoopNode` with condition checking success state |
| A/B test approaches | Use `ExperimentLoopNode` with metric comparison |
| Conditional branching | Use `SwitchNode` with case predicates |
| Require human review | Insert `HumanInLoopNode` before critical steps |
| Enforce quality bar | Place `GATE` node before downstream steps |
| Compose pipeline stages | Wrap each stage as `SubGraphNode` in the top-level graph |
| Save progress | Add `CHECKPOINT` node at critical boundaries |
| Load from YAML | `engine.load_yaml("path.yaml")` — auto-validates on load |

## Documentation Lookup (Context7)

Before implementing graph engine features, use Context7 to fetch current LangGraph docs:

```
mcp__plugin_context7_context7__resolve-library-id("LangGraph")
mcp__plugin_context7_context7__query-docs(id, "StateGraph nodes edges conditional branching checkpointing")
mcp__plugin_context7_context7__query-docs(id, "subgraph composition parallel execution state channels")
```

LangGraph's API has evolved significantly. Always verify node/edge APIs and state management patterns against Context7.
