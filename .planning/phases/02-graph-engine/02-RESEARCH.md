# Phase 2: Graph Engine - Research

**Researched:** 2026-03-18
**Domain:** Directed computation graph engine -- definition, validation, execution, checkpointing
**Confidence:** HIGH

## Summary

Phase 2 builds the core graph execution runtime for CodeBot. This is the foundational execution substrate upon which every agent, pipeline stage, and workflow depends. The engine must support YAML-based graph definition, topological-order execution, parallel branch execution via asyncio TaskGroup, conditional routing (SWITCH nodes), checkpoint/resume, and execution tracing.

The critical architectural decision is the relationship between LangGraph and CodeBot's custom graph engine. The project has chosen LangGraph as the primary graph execution engine. However, the design documents describe a custom `DirectedGraph` abstraction with domain-specific node types (AGENT, SUBGRAPH, LOOP, SWITCH, HUMAN_IN_LOOP, PARALLEL, MERGE, CHECKPOINT, TRANSFORM, GATE) and YAML-loadable graph definitions -- capabilities that LangGraph does not natively provide. The recommended approach is to build CodeBot's graph engine as a **thin orchestration layer on top of LangGraph's StateGraph**, where CodeBot's custom node types compile down to LangGraph nodes/subgraphs, CodeBot's YAML definitions compile to LangGraph StateGraph instances, and LangGraph handles the actual execution, checkpointing, and state management. This avoids hand-rolling a graph execution runtime while preserving the domain-specific abstractions the rest of CodeBot needs.

**Primary recommendation:** Build CodeBot's `DirectedGraph` as a compilation layer that loads YAML definitions, validates graph structure, and compiles to LangGraph `StateGraph` instances for execution. Use LangGraph's `AsyncPostgresSaver` for checkpointing and the `Send` API for dynamic parallel fan-out (GRPH-10).

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GRPH-01 | Execute directed graphs with typed nodes and edges in topological order | LangGraph StateGraph handles topological execution natively; CodeBot adds typed node/edge wrappers |
| GRPH-02 | Support node types: AGENT, SUBGRAPH, LOOP, SWITCH, HUMAN_IN_LOOP, PARALLEL, MERGE, CHECKPOINT, TRANSFORM | Each maps to LangGraph primitives: nodes, subgraphs, conditional edges, interrupt_before, Send API |
| GRPH-03 | SharedState for graph-level data flow between nodes | Maps directly to LangGraph's TypedDict state with Annotated reducers |
| GRPH-04 | Load and validate graph definitions from YAML | Custom YAML parser with Pydantic v2 models; compiles to LangGraph StateGraph |
| GRPH-05 | Detect cycles, missing dependencies, invalid edge types during validation | Custom validation pass before LangGraph compilation; Kahn's algorithm for cycle detection |
| GRPH-06 | Checkpoint graph state and resume from checkpoint | LangGraph's built-in checkpointing with AsyncPostgresSaver (Postgres already in Docker stack) |
| GRPH-07 | Trace execution with timing, token usage, output per node | Custom ExecutionTracer wrapping LangGraph node execution with timing/metrics collection |
| GRPH-08 | Execute parallel branches concurrently via asyncio TaskGroup | LangGraph's superstep parallelism (multiple outgoing edges) + Send API for dynamic fan-out |
| GRPH-09 | Conditional routing (SWITCH nodes) based on SharedState | LangGraph's conditional_edges with routing functions that read state |
| GRPH-10 | Dynamic fan-out via LangGraph Send API for parallel agent dispatch | Direct use of LangGraph's `Send` class from `langgraph.constants` |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langgraph | 1.1.2 | Primary graph execution engine -- StateGraph, checkpointing, Send API | Project decision (ADR-001); 24.6K stars, MIT, built-in persistence/parallelism |
| langgraph-checkpoint | 4.0.1 | Base checkpoint interfaces | Required by langgraph |
| langgraph-checkpoint-postgres | 3.0.4 | PostgreSQL checkpoint persistence | Project already runs PostgreSQL via Docker Compose; durable across restarts |
| pydantic | 2.12.5 | YAML schema validation, SharedState typing, node config models | Project standard (CLAUDE.md); v2 with ConfigDict |
| pyyaml | 6.0.3 | YAML parsing for graph definitions | Standard Python YAML library; already a transitive dependency |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncpg | >=0.30.0 | Async PostgreSQL driver for checkpoint saver | Already in server dependencies; needed by AsyncPostgresSaver |
| langchain-core | (transitive) | Base types for LangGraph (RunnableConfig, etc.) | Pulled in by langgraph; do not pin separately |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| LangGraph | Custom asyncio DAG engine | Full control but massive effort: must build checkpointing, parallel execution, state management from scratch. LangGraph gives this for free. |
| LangGraph | NetworkX + custom executor | NetworkX has great graph algorithms but zero execution runtime, no checkpointing, no state management |
| AsyncPostgresSaver | InMemorySaver | Simpler but state lost on restart; not suitable for GRPH-06 requirement |
| PyYAML | ruamel.yaml | Preserves comments and ordering but unnecessary for machine-parsed graph definitions |

**Installation:**
```bash
# Add to libs/graph-engine/pyproject.toml dependencies
uv add langgraph langgraph-checkpoint-postgres pyyaml
```

**Version verification:** All versions verified against PyPI on 2026-03-18.

## Architecture Patterns

### Recommended Project Structure

```
libs/graph-engine/src/graph_engine/
    __init__.py               # Public API exports
    models/
        __init__.py
        node_types.py         # NodeType enum, Node base, all node type classes
        edge_types.py         # EdgeType enum, Edge model
        state.py              # SharedState TypedDict, state reducers
        graph_def.py          # GraphDefinition Pydantic model (YAML schema)
        execution.py          # ExecutionContext, GraphResult, ExecutionRecord
    engine/
        __init__.py
        compiler.py           # YAML -> LangGraph StateGraph compilation
        validator.py          # Graph validation (cycles, missing deps, type checks)
        executor.py           # ExecutionEngine wrapper around compiled graph
        checkpoint.py         # Checkpoint manager (AsyncPostgresSaver setup)
    tracing/
        __init__.py
        tracer.py             # ExecutionTracer: timing, tokens, output per node
    yaml/
        __init__.py
        loader.py             # YAML loading + Pydantic validation
        schema.py             # YAML schema constants and examples
    templates/
        __init__.py
        composed.py           # Pre-built ComposedGraph patterns
        node_templates.py     # Reusable NodeTemplate definitions
```

### Pattern 1: Compilation Layer (YAML to LangGraph)

**What:** CodeBot's graph definitions (YAML or imperative Python) compile to LangGraph StateGraph instances. This decouples the domain model from the execution engine.

**When to use:** Always. This is the core architectural pattern for the entire graph engine.

**How it works:**
1. User writes YAML graph definition (or uses imperative API)
2. YAML is parsed into Pydantic `GraphDefinition` model
3. `GraphValidator` checks for cycles, missing deps, type mismatches
4. `GraphCompiler` walks the validated definition and builds a LangGraph `StateGraph`
5. Each CodeBot node type maps to a LangGraph node function or subgraph
6. StateGraph is compiled with checkpointer and returned as executable

```python
# Source: CodeBot design pattern derived from LangGraph StateGraph API
from typing import Any, Annotated
from typing_extensions import TypedDict
from operator import add as list_add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

class SharedState(TypedDict):
    """Graph-level shared state. Nodes read/write via typed keys."""
    node_outputs: Annotated[dict[str, Any], _merge_dicts]
    execution_trace: Annotated[list[dict], list_add]
    # Additional keys added per-graph from YAML definition

class GraphCompiler:
    """Compiles a validated GraphDefinition into a LangGraph StateGraph."""

    def compile(
        self,
        graph_def: GraphDefinition,
        checkpointer: AsyncPostgresSaver | None = None,
    ) -> CompiledStateGraph:
        builder = StateGraph(SharedState)

        for node in graph_def.nodes:
            node_fn = self._build_node_function(node)
            builder.add_node(node.id, node_fn)

        for edge in graph_def.edges:
            if edge.condition:
                builder.add_conditional_edges(
                    edge.source_id,
                    self._build_condition(edge),
                )
            else:
                builder.add_edge(edge.source_id, edge.target_id)

        # Wire entry/exit
        for entry_node in graph_def.entry_nodes:
            builder.add_edge(START, entry_node)
        for exit_node in graph_def.exit_nodes:
            builder.add_edge(exit_node, END)

        return builder.compile(checkpointer=checkpointer)
```

### Pattern 2: Node Type Dispatch

**What:** Each CodeBot node type (AGENT, SWITCH, LOOP, PARALLEL, etc.) compiles to a different LangGraph construct.

**When to use:** In the GraphCompiler when translating node types.

**Mapping:**

| CodeBot Node Type | LangGraph Construct |
|-------------------|---------------------|
| AGENT | Regular node function (async callable) |
| SUBGRAPH | Compiled subgraph added as node |
| LOOP | Subgraph with conditional edge back to start |
| SWITCH | Node + conditional_edges with routing function |
| HUMAN_IN_LOOP | Node with `interrupt_before` on compile |
| PARALLEL | Multiple outgoing edges from predecessor (native superstep) |
| MERGE | Node that reads from multiple state keys (fan-in) |
| CHECKPOINT | Automatic (LangGraph checkpoints every superstep) |
| TRANSFORM | Pure function node that transforms state |
| GATE | Node that checks conditions and raises on failure |

### Pattern 3: SharedState with Reducers

**What:** LangGraph requires explicit reducer functions for state keys that receive concurrent writes from parallel nodes. Without reducers, concurrent writes conflict.

**When to use:** Any state key that parallel nodes write to.

```python
# Source: LangGraph state management pattern
from typing import Any, Annotated
from typing_extensions import TypedDict
from operator import add

def merge_dicts(existing: dict, update: dict) -> dict:
    """Reducer: merge dicts from parallel nodes."""
    return {**existing, **update}

class SharedState(TypedDict):
    """Thread-safe shared state with reducers for parallel writes."""
    # Dict-based outputs keyed by node_id -- parallel-safe via merge
    node_outputs: Annotated[dict[str, Any], merge_dicts]
    # Trace records appended by each node -- parallel-safe via list concat
    execution_trace: Annotated[list[dict[str, Any]], add]
    # Error accumulator
    errors: Annotated[list[dict[str, Any]], add]
```

### Pattern 4: Send API for Dynamic Fan-Out (GRPH-10)

**What:** LangGraph's `Send` API enables creating parallel branches at runtime based on state content. This is how CodeBot dispatches multiple agents in parallel when the exact count/config is determined at runtime.

**When to use:** When the number of parallel branches is not known at graph definition time (e.g., "run N coding agents based on the task decomposition").

```python
# Source: LangGraph Send API documentation
from langgraph.constants import Send

def dispatch_parallel_agents(state: SharedState) -> list[Send]:
    """Dynamic fan-out: create one execution per task."""
    tasks = state["pending_tasks"]
    return [
        Send("agent_worker", {"task": task, "task_id": task["id"]})
        for task in tasks
    ]

# In graph construction:
builder.add_conditional_edges("planner", dispatch_parallel_agents)
```

### Anti-Patterns to Avoid

- **Hand-rolling asyncio.gather for graph execution:** LangGraph manages parallel execution via supersteps. Do not bypass this with raw asyncio.gather -- it breaks checkpointing and state management.
- **Mutable shared state without reducers:** Parallel nodes writing to the same state key without a reducer causes data loss. Always annotate shared keys with reducers.
- **Putting LangGraph types in the public API:** CodeBot's graph engine should expose its own types (NodeType, EdgeType, GraphDefinition). LangGraph is an implementation detail that downstream code should not depend on directly.
- **Skipping validation before compilation:** LangGraph's compile() does minimal structural checks. CodeBot's validator must catch domain-specific issues (invalid node type combinations, missing required ports, edge type mismatches) before compilation.
- **Storing raw LLM conversation in SharedState:** Per design doc (SYSTEM_DESIGN.md line 6452-6454), SharedState carries typed data, not conversation history. Raw LLM messages go to AgentExecution records, not state.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Graph execution runtime | Custom asyncio DAG scheduler | LangGraph StateGraph | Handles superstep parallelism, state management, interrupt/resume, error propagation |
| Checkpoint/resume | Custom serialization + DB persistence | LangGraph AsyncPostgresSaver | Battle-tested checkpoint format (v4), handles pending writes from failed supersteps, thread isolation |
| Cycle detection | Custom DFS/Kahn's from scratch | Custom validator using Kahn's algorithm (simple) | Kahn's is ~20 lines; no library needed, but also validates topological ordering |
| YAML parsing | Custom parser | PyYAML + Pydantic v2 model_validate | Pydantic validates types, defaults, constraints automatically |
| Parallel fan-out | asyncio.TaskGroup with manual coordination | LangGraph Send API | Send handles state isolation per branch, automatic result merging, checkpoint integration |
| State merging from parallel branches | Custom locking/merge logic | LangGraph Annotated reducers | Reducers run atomically within superstep boundaries |

**Key insight:** LangGraph already solves the hardest problems (parallel state management, checkpoint format, interrupt/resume, error propagation). CodeBot's value-add is the domain-specific layer: YAML definitions, custom node types, validation rules, and execution tracing.

## Common Pitfalls

### Pitfall 1: LangGraph Version Compatibility
**What goes wrong:** LangGraph has evolved rapidly (0.x to 1.x). APIs change between versions. The `config_schema` parameter was deprecated in v0.6.0, replaced by `context_schema`.
**Why it happens:** Fast-moving library with breaking changes.
**How to avoid:** Pin to langgraph>=1.1.0 (stable 1.x line). Always verify API signatures against the installed version, not training data. Use Context7 before implementing any LangGraph pattern.
**Warning signs:** Import errors, deprecation warnings, type mismatches.

### Pitfall 2: Checkpoint Schema Migration
**What goes wrong:** LangGraph's checkpoint format evolved from v3 to v4 to handle pending sends. If CodeBot stores checkpoints in Postgres and then LangGraph is upgraded, old checkpoints may need migration.
**Why it happens:** Checkpoint format is an internal detail that changes between versions.
**How to avoid:** Pin langgraph-checkpoint-postgres version. Use the library's built-in migration (it handles v3->v4 on-the-fly during get_tuple). Test checkpoint resume across version upgrades before deploying.
**Warning signs:** Deserialization errors when resuming from old checkpoints.

### Pitfall 3: Parallel State Writes Without Reducers
**What goes wrong:** Two parallel nodes write to the same state key. Without a reducer, one write silently overwrites the other. With the wrong reducer, data is corrupted.
**Why it happens:** Developers add state keys without considering parallel execution paths.
**How to avoid:** Every state key that can receive writes from parallel nodes MUST have an Annotated reducer. Use `operator.add` for lists, custom `merge_dicts` for dicts. The validator should check that all state keys written by parallel-eligible nodes have reducers defined.
**Warning signs:** Missing data after parallel execution, non-deterministic results.

### Pitfall 4: YAML Definitions with Cycles (Except Loops)
**What goes wrong:** A YAML graph definition accidentally creates a cycle (A -> B -> C -> A) that is not an intentional LOOP construct. LangGraph allows cycles, so it won't catch this.
**Why it happens:** Complex graphs with many edges make cycles hard to spot visually.
**How to avoid:** The validator must run Kahn's algorithm on the graph excluding intentional LOOP back-edges. Any remaining cycle is an error. LOOP nodes explicitly declare their back-edge, which is excluded from cycle detection.
**Warning signs:** Infinite execution, memory growth, timeout.

### Pitfall 5: Subgraph State Isolation
**What goes wrong:** A subgraph shares state keys with the parent graph, causing unintended data leakage or overwrites.
**Why it happens:** LangGraph subgraphs can share state with parent or be isolated. If keys overlap without explicit mapping, data flows incorrectly.
**How to avoid:** SubGraphNodes must have explicit input/output port mappings (defined in YAML). The compiler transforms parent state to subgraph state before invocation and transforms results back. Never share state keys implicitly.
**Warning signs:** Subgraph reads stale data, parent state corrupted after subgraph execution.

### Pitfall 6: Oversized Checkpoint State
**What goes wrong:** SharedState grows unbounded (e.g., storing full code artifacts) causing checkpoints to become multi-MB, slowing save/resume.
**Why it happens:** Nodes write large outputs directly to state instead of storing artifacts externally and referencing them.
**How to avoid:** SharedState should store references (artifact IDs, file paths) not large blobs. Large outputs go to the CodeArtifact table or filesystem. The TRANSFORM node type can strip large data and replace with references.
**Warning signs:** Checkpoint save taking >1s, Postgres storage growing rapidly.

## Code Examples

### YAML Graph Definition Schema

```yaml
# Source: Derived from SYSTEM_DESIGN.md Section 1.8.2
# configs/pipelines/example.yaml
name: example-pipeline
version: "1.0"
description: "Example graph definition"

state_schema:
  node_outputs:
    type: dict
    reducer: merge_dicts
  execution_trace:
    type: list
    reducer: append

nodes:
  - id: analyzer
    type: agent
    config:
      agent_type: RESEARCHER
      llm_model: claude-sonnet-4
      timeout_seconds: 300
    retry_policy:
      max_retries: 2
      backoff_factor: 2.0

  - id: router
    type: switch
    config:
      cases:
        simple: "state.complexity == 'low'"
        complex: "state.complexity == 'high'"
      default: simple

  - id: simple_builder
    type: agent
    config:
      agent_type: BACKEND_DEV
      llm_model: claude-sonnet-4

  - id: complex_builder
    type: agent
    config:
      agent_type: BACKEND_DEV
      llm_model: claude-opus-4

  - id: merger
    type: merge
    config:
      strategy: combine_outputs

edges:
  - source: analyzer
    target: router
    type: state_flow

  - source: router
    target: simple_builder
    type: control_flow
    condition: "case == 'simple'"

  - source: router
    target: complex_builder
    type: control_flow
    condition: "case == 'complex'"

  - source: simple_builder
    target: merger
    type: state_flow

  - source: complex_builder
    target: merger
    type: state_flow

entry_nodes: [analyzer]
exit_nodes: [merger]
```

### Pydantic Model for YAML Validation

```python
# Source: Pydantic v2 patterns from CLAUDE.md conventions
from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class NodeType(str, enum.Enum):
    AGENT = "agent"
    SUBGRAPH = "subgraph"
    LOOP = "loop"
    SWITCH = "switch"
    HUMAN_IN_LOOP = "human"
    PARALLEL = "parallel"
    MERGE = "merge"
    CHECKPOINT = "checkpoint"
    TRANSFORM = "transform"
    GATE = "gate"


class EdgeType(str, enum.Enum):
    STATE_FLOW = "state_flow"
    MESSAGE_FLOW = "message_flow"
    CONTROL_FLOW = "control_flow"


class RetryPolicy(BaseModel, frozen=True):
    max_retries: int = 3
    backoff_factor: float = 2.0
    retry_on: list[str] = ["TimeoutError", "RateLimitError"]


class NodeDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    type: NodeType
    config: dict[str, Any] = {}
    retry_policy: RetryPolicy = RetryPolicy()
    timeout_seconds: int = 600

    @field_validator("id")
    @classmethod
    def validate_node_id(cls, v: str) -> str:
        if not v.isidentifier():
            raise ValueError(f"Node ID must be a valid identifier: {v}")
        return v


class EdgeDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str
    target: str
    type: EdgeType = EdgeType.STATE_FLOW
    condition: str | None = None
    transform: str | None = None


class GraphDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    version: str = "1.0"
    description: str = ""
    state_schema: dict[str, Any] = {}
    nodes: list[NodeDefinition]
    edges: list[EdgeDefinition]
    entry_nodes: list[str]
    exit_nodes: list[str]
```

### Graph Validator (Kahn's Algorithm)

```python
# Source: Standard Kahn's algorithm for DAG validation
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    execution_layers: list[list[str]]  # Topological layers for parallel execution


class GraphValidator:
    """Validates a GraphDefinition before compilation."""

    def validate(self, graph_def: GraphDefinition) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        # 1. Check all edge endpoints reference existing nodes
        node_ids = {n.id for n in graph_def.nodes}
        for edge in graph_def.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge source '{edge.source}' not found in nodes")
            if edge.target not in node_ids:
                errors.append(f"Edge target '{edge.target}' not found in nodes")

        # 2. Check entry/exit nodes exist
        for entry in graph_def.entry_nodes:
            if entry not in node_ids:
                errors.append(f"Entry node '{entry}' not found")
        for exit_node in graph_def.exit_nodes:
            if exit_node not in node_ids:
                errors.append(f"Exit node '{exit_node}' not found")

        # 3. Cycle detection via Kahn's algorithm
        #    (exclude back-edges from LOOP nodes)
        layers = self._topological_sort(graph_def, errors)

        # 4. Node-type-specific validation
        self._validate_node_types(graph_def, errors, warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            execution_layers=layers,
        )

    def _topological_sort(
        self, graph_def: GraphDefinition, errors: list[str]
    ) -> list[list[str]]:
        """Kahn's algorithm: returns execution layers (parallel groups)."""
        loop_back_edges = self._identify_loop_back_edges(graph_def)

        # Build adjacency and in-degree (excluding loop back-edges)
        in_degree: dict[str, int] = defaultdict(int)
        adjacency: dict[str, list[str]] = defaultdict(list)
        node_ids = {n.id for n in graph_def.nodes}

        for nid in node_ids:
            in_degree[nid] = 0

        for edge in graph_def.edges:
            if (edge.source, edge.target) in loop_back_edges:
                continue
            adjacency[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        # Kahn's: collect nodes layer by layer
        queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
        layers: list[list[str]] = []
        visited = 0

        while queue:
            layer = list(queue)
            layers.append(layer)
            next_queue: deque[str] = deque()
            for nid in layer:
                visited += 1
                for neighbor in adjacency[nid]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_queue.append(neighbor)
            queue = next_queue

        if visited != len(node_ids):
            errors.append(
                "Graph contains a cycle (excluding declared loop back-edges)"
            )
        return layers
```

### ExecutionTracer (GRPH-07)

```python
# Source: Design pattern for execution tracing
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(slots=True, kw_only=True)
class ExecutionRecord:
    """Single node execution record for tracing."""
    node_id: str
    started_at: float
    completed_at: float = 0.0
    duration_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    output_summary: str = ""
    error: str | None = None
    trace_id: UUID = field(default_factory=uuid4)


class ExecutionTracer:
    """Wraps node functions to capture execution metrics."""

    def __init__(self) -> None:
        self.records: list[ExecutionRecord] = []

    def wrap_node(self, node_id: str, node_fn):
        """Returns a traced version of a node function."""
        async def traced_fn(state: dict[str, Any]) -> dict[str, Any]:
            record = ExecutionRecord(
                node_id=node_id,
                started_at=time.monotonic(),
            )
            try:
                result = await node_fn(state)
                record.completed_at = time.monotonic()
                record.duration_ms = int(
                    (record.completed_at - record.started_at) * 1000
                )
                # Extract token metrics if present
                if isinstance(result, dict):
                    metrics = result.get("_metrics", {})
                    record.input_tokens = metrics.get("input_tokens", 0)
                    record.output_tokens = metrics.get("output_tokens", 0)
                    record.total_tokens = (
                        record.input_tokens + record.output_tokens
                    )
                    record.cost_usd = metrics.get("cost_usd", 0.0)
                self.records.append(record)
                # Add trace to state for downstream visibility
                trace_entry = {
                    "node_id": node_id,
                    "duration_ms": record.duration_ms,
                    "tokens": record.total_tokens,
                    "cost_usd": record.cost_usd,
                }
                return {
                    **result,
                    "execution_trace": [trace_entry],
                }
            except Exception as e:
                record.completed_at = time.monotonic()
                record.duration_ms = int(
                    (record.completed_at - record.started_at) * 1000
                )
                record.error = str(e)
                self.records.append(record)
                raise

        return traced_fn
```

### Checkpoint Manager Setup (GRPH-06)

```python
# Source: LangGraph checkpoint-postgres documentation
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


async def create_checkpointer(db_uri: str) -> AsyncPostgresSaver:
    """Create and initialize the PostgreSQL checkpointer.

    Must be called once at startup. The setup() call creates required
    tables if they do not already exist (idempotent).
    """
    checkpointer = AsyncPostgresSaver.from_conn_string(db_uri)
    await checkpointer.setup()
    return checkpointer


async def resume_from_checkpoint(
    compiled_graph,
    thread_id: str,
    checkpoint_id: str | None = None,
) -> dict:
    """Resume graph execution from a specific checkpoint.

    If checkpoint_id is None, resumes from the latest checkpoint
    for the given thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    if checkpoint_id:
        config["configurable"]["checkpoint_id"] = checkpoint_id

    # Invoke with None input to resume from checkpoint state
    return await compiled_graph.ainvoke(None, config)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LangGraph 0.x API | LangGraph 1.x stable API | 2025 Q3-Q4 | config_schema deprecated, context_schema introduced; stable API guarantees |
| Checkpoint format v3 | Checkpoint format v4 | langgraph-checkpoint 4.x | Better handling of pending sends from failed supersteps; on-the-fly migration |
| asyncio.gather for parallel nodes | LangGraph supersteps + Send API | LangGraph 0.3+ | Automatic checkpoint integration, state isolation per branch |
| MASFactory patterns (original design) | LangGraph implementation | Project ADR-001 | MASFactory remains as conceptual inspiration; LangGraph provides production implementation |

**Deprecated/outdated:**
- `config_schema` parameter on StateGraph: Use `context_schema` instead (deprecated in v0.6.0)
- Direct `asyncio.gather()` for parallel graph nodes: Use LangGraph's built-in superstep parallelism
- MASFactory as runtime: Replaced by LangGraph; patterns retained as architectural inspiration

## Open Questions

1. **LangGraph version pinning strategy**
   - What we know: langgraph 1.1.2 is current stable. The API has stabilized in 1.x.
   - What's unclear: Whether to pin exact versions or use compatible release specifiers (>=1.1.0,<2.0).
   - Recommendation: Use `>=1.1.0,<2.0` for langgraph; exact pin for checkpoint-postgres since checkpoint format is sensitive to version changes.

2. **Condition expression handling in YAML**
   - What we know: YAML definitions contain condition strings like `"state.complexity == 'low'"`. These need safe interpretation.
   - What's unclear: Whether to use a restricted expression evaluator, AST-based parser, or compile conditions as named Python functions.
   - Recommendation: Use a registry of named condition functions. YAML references function names (e.g., `condition: is_simple_project`), and the compiler looks them up in a conditions registry. This avoids any form of dynamic code execution from YAML strings. For built-in conditions, provide a small DSL parsed via Python's `ast` module that only allows attribute access, comparisons, and boolean logic.

3. **AsyncPostgresSaver connection pooling**
   - What we know: AsyncPostgresSaver can use a connection string or a connection pool.
   - What's unclear: Whether it should share the server's asyncpg pool or use its own.
   - Recommendation: Use a dedicated connection pool for the checkpointer to avoid contention with the application's database operations. The server already has asyncpg configured.

4. **LOOP node back-edge handling in LangGraph**
   - What we know: LangGraph natively supports cycles. CodeBot's design requires explicit LOOP constructs with max_iterations and exit conditions.
   - What's unclear: Best way to enforce max_iterations within LangGraph's cycle support.
   - Recommendation: Implement LOOP as a subgraph with a counter in state and a conditional edge that checks `iteration_count < max_iterations AND NOT exit_condition`. The counter increments each iteration.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.24+ |
| Config file | `libs/graph-engine/pyproject.toml` (needs [tool.pytest.ini_options] section) |
| Quick run command | `uv run pytest libs/graph-engine/tests/ -x -q` |
| Full suite command | `uv run pytest libs/graph-engine/tests/ -v --tb=short` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GRPH-01 | Topological order execution | unit | `uv run pytest libs/graph-engine/tests/test_executor.py::test_topological_order -x` | Wave 0 |
| GRPH-02 | All node types execute correctly | unit | `uv run pytest libs/graph-engine/tests/test_node_types.py -x` | Wave 0 |
| GRPH-03 | SharedState read/write between nodes | unit | `uv run pytest libs/graph-engine/tests/test_state.py -x` | Wave 0 |
| GRPH-04 | YAML loads and validates into GraphDefinition | unit | `uv run pytest libs/graph-engine/tests/test_yaml_loader.py -x` | Wave 0 |
| GRPH-05 | Cycle detection, missing deps, invalid types | unit | `uv run pytest libs/graph-engine/tests/test_validator.py -x` | Wave 0 |
| GRPH-06 | Checkpoint save and resume | integration | `uv run pytest libs/graph-engine/tests/test_checkpoint.py -x` | Wave 0 |
| GRPH-07 | Execution traces with timing/tokens | unit | `uv run pytest libs/graph-engine/tests/test_tracer.py -x` | Wave 0 |
| GRPH-08 | Parallel branches via asyncio | integration | `uv run pytest libs/graph-engine/tests/test_parallel.py -x` | Wave 0 |
| GRPH-09 | SWITCH conditional routing | unit | `uv run pytest libs/graph-engine/tests/test_switch.py -x` | Wave 0 |
| GRPH-10 | Dynamic fan-out via Send API | integration | `uv run pytest libs/graph-engine/tests/test_send_api.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest libs/graph-engine/tests/ -x -q`
- **Per wave merge:** `uv run pytest libs/graph-engine/tests/ -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `libs/graph-engine/pyproject.toml` -- needs pytest, pytest-asyncio, langgraph dependencies
- [ ] `libs/graph-engine/tests/conftest.py` -- shared fixtures (mock nodes, sample graph definitions, test DB connection)
- [ ] `libs/graph-engine/tests/test_validator.py` -- covers GRPH-05
- [ ] `libs/graph-engine/tests/test_yaml_loader.py` -- covers GRPH-04
- [ ] `libs/graph-engine/tests/test_executor.py` -- covers GRPH-01, GRPH-08
- [ ] `libs/graph-engine/tests/test_node_types.py` -- covers GRPH-02
- [ ] `libs/graph-engine/tests/test_state.py` -- covers GRPH-03
- [ ] `libs/graph-engine/tests/test_checkpoint.py` -- covers GRPH-06 (needs Postgres)
- [ ] `libs/graph-engine/tests/test_tracer.py` -- covers GRPH-07
- [ ] `libs/graph-engine/tests/test_switch.py` -- covers GRPH-09
- [ ] `libs/graph-engine/tests/test_send_api.py` -- covers GRPH-10
- [ ] `libs/graph-engine/tests/fixtures/` -- sample YAML graph definitions for tests

## Sources

### Primary (HIGH confidence)
- LangGraph PyPI registry -- verified version 1.1.2, checkpoint 4.0.1, checkpoint-postgres 3.0.4
- [LangGraph Official Docs](https://docs.langchain.com/oss/python/langgraph/) -- StateGraph API, Send API, checkpointing
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph) -- source of truth for API
- [LangGraph Persistence Docs](https://docs.langchain.com/oss/python/langgraph/persistence) -- checkpoint resume patterns
- CodeBot design docs: `docs/design/SYSTEM_DESIGN.md` Section 1 -- Graph Engine Design
- CodeBot architecture: `docs/architecture/ARCHITECTURE.md` Section 3 -- Agent Graph Engine
- CodeBot existing code: `libs/graph-engine/`, `libs/agent-sdk/src/agent_sdk/models/`, `apps/server/src/codebot/`

### Secondary (MEDIUM confidence)
- [LangGraph Graph API Overview](https://docs.langchain.com/oss/python/langgraph/graph-api) -- verified graph API patterns
- [LangGraph Send API Reference](https://reference.langchain.com/python/langgraph/types/Send) -- Send class for dynamic parallelism
- [LangGraph PostgresSaver](https://pypi.org/project/langgraph-checkpoint-postgres/) -- PostgreSQL checkpoint setup
- [LangGraph Subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs) -- subgraph isolation patterns

### Tertiary (LOW confidence)
- WebSearch results on custom DAG execution engines -- general patterns, not CodeBot-specific
- Medium articles on LangGraph async patterns -- community examples, may not reflect latest API

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- LangGraph is a locked project decision, versions verified against PyPI
- Architecture: HIGH -- Compilation-layer pattern is well-established; design docs are thorough and internally consistent
- Pitfalls: HIGH -- Based on LangGraph documentation and known async/parallel programming issues
- YAML schema: MEDIUM -- Custom design derived from design docs; no existing implementation to validate against
- Condition evaluation: MEDIUM -- Open question on safe expression evaluation approach

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (LangGraph is stable 1.x; unlikely to break within 30 days)
