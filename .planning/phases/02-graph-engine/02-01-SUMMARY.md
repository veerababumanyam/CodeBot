---
phase: 02-graph-engine
plan: 01
subsystem: graph-engine
tags: [pydantic, yaml, dag, kahn-algorithm, strenum, typed-state]

requires:
  - phase: 01-foundation-and-scaffolding
    provides: monorepo structure, agent-sdk enums, pyproject.toml skeleton
provides:
  - NodeType enum (10 members), EdgeType enum (3 members)
  - NodeDefinition, EdgeDefinition, RetryPolicy Pydantic models
  - GraphDefinition Pydantic model for complete graph schema
  - SharedState TypedDict with Annotated reducers for parallel safety
  - ExecutionRecord and GraphResult dataclasses for execution tracing
  - YAML loader (load_graph_definition, load_graph_definition_from_string)
  - GraphValidator with Kahn's algorithm cycle detection and execution layers
  - ValidationResult with errors, warnings, and execution layers
affects: [02-02 compiler/executor, 02-03 checkpointing, 03-agent-sdk]

tech-stack:
  added: [pydantic>=2.10.0, pyyaml>=6.0, pytest>=8.0, pytest-asyncio>=0.24, ruff>=0.8.0]
  patterns: [StrEnum for typed enums, frozen Pydantic ConfigDict, slots+kw_only dataclasses, Annotated reducers for parallel state]

key-files:
  created:
    - libs/graph-engine/src/graph_engine/models/node_types.py
    - libs/graph-engine/src/graph_engine/models/edge_types.py
    - libs/graph-engine/src/graph_engine/models/state.py
    - libs/graph-engine/src/graph_engine/models/graph_def.py
    - libs/graph-engine/src/graph_engine/models/execution.py
    - libs/graph-engine/src/graph_engine/yaml/loader.py
    - libs/graph-engine/src/graph_engine/engine/validator.py
    - libs/graph-engine/tests/test_models.py
    - libs/graph-engine/tests/test_yaml_loader.py
    - libs/graph-engine/tests/test_validator.py
    - libs/graph-engine/tests/fixtures/simple_pipeline.yaml
    - libs/graph-engine/tests/fixtures/parallel_pipeline.yaml
    - libs/graph-engine/tests/fixtures/switch_pipeline.yaml
    - libs/graph-engine/tests/fixtures/cyclic_graph.yaml
    - libs/graph-engine/tests/fixtures/invalid_refs.yaml
  modified:
    - libs/graph-engine/pyproject.toml
    - libs/graph-engine/src/graph_engine/__init__.py

key-decisions:
  - "StrEnum instead of (str, Enum) per ruff UP042 for Python 3.12+ target"
  - "noqa TC001 for Pydantic model imports that must stay at runtime (not TYPE_CHECKING)"
  - "Kahn's algorithm with sorted initial queue for deterministic layer ordering"
  - "Loop back-edge detection via BFS descendant check from LOOP node"

patterns-established:
  - "Frozen Pydantic models with ConfigDict(frozen=True) for all domain definitions"
  - "StrEnum for all typed enums (NodeType, EdgeType)"
  - "Dataclass with slots=True, kw_only=True for execution tracking types"
  - "Annotated[dict, merge_dicts] and Annotated[list, operator.add] for parallel-safe SharedState"
  - "field_validator for business rules (identifier validation, positive timeout)"

requirements-completed: [GRPH-01, GRPH-02, GRPH-03, GRPH-04, GRPH-05]

duration: 5min
completed: 2026-03-18
---

# Phase 2 Plan 01: Graph Engine Domain Models Summary

**Pydantic domain models for 10 node types and 3 edge types, YAML loader with validation, and Kahn's algorithm graph validator with cycle detection and execution layer computation**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-18T10:25:59Z
- **Completed:** 2026-03-18T10:31:22Z
- **Tasks:** 2
- **Files modified:** 17

## Accomplishments
- All 10 node types (AGENT, SUBGRAPH, LOOP, SWITCH, HUMAN_IN_LOOP, PARALLEL, MERGE, CHECKPOINT, TRANSFORM, GATE) defined as StrEnum with frozen Pydantic models
- SharedState TypedDict with Annotated reducers (merge_dicts for dicts, operator.add for lists) enabling parallel-safe state management
- YAML loader that parses files and strings into validated GraphDefinition models
- Graph validator using Kahn's algorithm detecting cycles, missing node references, and invalid configurations with execution layer computation
- 40 tests passing across 3 test files with ruff lint clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Package setup, domain models, and model tests** - `18e3ff2` (feat)
2. **Task 2: YAML loader, graph validator, and tests** - `14a78af` (feat)

## Files Created/Modified
- `libs/graph-engine/pyproject.toml` - Added pydantic, pyyaml, pytest, ruff dependencies and tool config
- `libs/graph-engine/src/graph_engine/models/node_types.py` - NodeType enum (10 members), RetryPolicy, NodeDefinition
- `libs/graph-engine/src/graph_engine/models/edge_types.py` - EdgeType enum (3 members), EdgeDefinition
- `libs/graph-engine/src/graph_engine/models/state.py` - SharedState TypedDict with merge_dicts and list append reducers
- `libs/graph-engine/src/graph_engine/models/graph_def.py` - GraphDefinition with non-empty validation
- `libs/graph-engine/src/graph_engine/models/execution.py` - ExecutionRecord and GraphResult dataclasses
- `libs/graph-engine/src/graph_engine/yaml/loader.py` - YAML loading with Pydantic validation
- `libs/graph-engine/src/graph_engine/engine/validator.py` - GraphValidator with Kahn's algorithm
- `libs/graph-engine/tests/test_models.py` - 22 tests for all domain models
- `libs/graph-engine/tests/test_yaml_loader.py` - 6 tests for YAML loader
- `libs/graph-engine/tests/test_validator.py` - 12 tests for graph validator
- `libs/graph-engine/tests/fixtures/*.yaml` - 5 YAML fixture files

## Decisions Made
- Used StrEnum (Python 3.12+) instead of `(str, Enum)` per ruff UP042 -- cleaner, project targets 3.12+
- Used `# noqa: TC001` for Pydantic model imports that must remain at runtime (Pydantic needs them for model_validate)
- Sorted initial Kahn's queue for deterministic, reproducible execution layer ordering
- Loop back-edge detection uses BFS descendant check from LOOP node to confirm edge is truly a back-edge

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed ruff lint violations after initial implementation**
- **Found during:** Task 2 (after implementing validator)
- **Issue:** 8 ruff errors: UP042 (use StrEnum), TC001 (type-checking imports), SIM102 (nested ifs), F841 (unused variable)
- **Fix:** Changed to StrEnum, combined nested ifs, removed unused variable, added noqa for runtime Pydantic imports
- **Files modified:** node_types.py, edge_types.py, graph_def.py, validator.py
- **Verification:** `ruff check src/` passes, all 40 tests still green
- **Committed in:** 14a78af (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Lint fix was necessary for code quality. No scope creep.

## Issues Encountered
- Moving Pydantic model imports to TYPE_CHECKING block (per TC001) broke model_validate at runtime -- resolved with noqa annotation

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Domain models, YAML loader, and validator are complete and tested
- Plan 02-02 (compiler, executor, tracer) can now build on these types
- GraphDefinition models are the contract for all subsequent graph engine work

## Self-Check: PASSED

All 16 key files verified present. Both task commits (18e3ff2, 14a78af) confirmed in git log.

---
*Phase: 02-graph-engine*
*Completed: 2026-03-18*
