---
phase: 03-agent-framework
plan: 02
subsystem: graph-engine
tags: [python, dataclass, agent-node, recovery-strategy, yaml-config, metrics, worktree, graph-adapter]

# Dependency graph
requires:
  - phase: 03-agent-framework
    plan: 01
    provides: "BaseAgent, AgentInput, AgentOutput, RecoveryStrategy, AgentMetrics, WorktreeProvider protocol, AgentConfig"
  - phase: 02-graph-engine
    provides: "Graph execution engine, SharedState, NodeDefinition"
provides:
  - "AgentNode graph adapter wrapping BaseAgent for execution within graph engine"
  - "NoOpWorktreeProvider stub satisfying AGNT-04 WorktreeProvider protocol"
  - "AgentConfigLoader for YAML agent config discovery and validation"
  - "Reference orchestrator.yaml config with escalate recovery strategy"
  - "_schema.yaml documenting all agent config fields"
affects: [04-multi-llm-abstraction, 06-pipeline-orchestration, 08-agent-isolation, 09-agent-implementations]

# Tech tracking
tech-stack:
  added: []
  patterns: [agent-node-adapter, yaml-config-discovery, noop-stub-pattern, on-event-callback]

key-files:
  created:
    - libs/graph-engine/src/graph_engine/nodes/__init__.py
    - libs/graph-engine/src/graph_engine/nodes/agent_node.py
    - libs/graph-engine/tests/test_agent_node.py
    - configs/agents/_schema.yaml
    - configs/agents/orchestrator.yaml
    - apps/server/src/codebot/agent_config/__init__.py
    - apps/server/src/codebot/agent_config/loader.py
    - apps/server/tests/test_agent_loader.py
  modified:
    - libs/graph-engine/pyproject.toml
    - libs/graph-engine/tests/conftest.py
    - apps/server/pyproject.toml

key-decisions:
  - "agent-sdk added as workspace dependency to both graph-engine and codebot-server via tool.uv.sources"
  - "NoOpWorktreeProvider returns '.' (cwd) -- real worktree isolation deferred to Phase 8"
  - "AgentNode.worktree_provider typed as Any to avoid circular import with agent_sdk protocols"
  - "on_event callback is synchronous Callable (not async) -- keeps event emission non-blocking"
  - "AgentConfigLoader skips _-prefixed YAML files for schema/template documentation"

patterns-established:
  - "AgentNode adapter: wraps any BaseAgent for graph execution with SharedState I/O"
  - "Recovery loop: attempt counter + strategy.decide() with action dispatch (retry/escalate/rollback)"
  - "_-prefixed YAML files as skippable documentation templates"
  - "Workspace cross-dependency: tool.uv.sources = { workspace = true }"

requirements-completed: [AGNT-02, AGNT-04, AGNT-05, AGNT-12]

# Metrics
duration: 6min
completed: 2026-03-18
---

# Phase 3 Plan 2: AgentNode Graph Adapter and YAML Config Loading Summary

**AgentNode wraps BaseAgent for graph execution with recovery strategies, timeout enforcement, metrics recording, and worktree stub -- YAML config loader discovers and validates agent configs from configs/agents/ -- 15 tests passing**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-18T11:16:01Z
- **Completed:** 2026-03-18T11:22:17Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- AgentNode converts SharedState dict to AgentInput, runs BaseAgent.execute() with asyncio.timeout, handles recovery strategies (retry, retry_modified, escalate, rollback), records AgentMetrics, and emits events via callback
- NoOpWorktreeProvider stub satisfies WorktreeProvider protocol for agent isolation (real implementation deferred to Phase 8)
- AgentConfigLoader discovers YAML files in configs/agents/, skips _-prefixed templates, validates against AgentConfig with Pydantic, and indexes by uppercase agent_type
- orchestrator.yaml serves as reference config with 7 tools, escalate recovery, and 8192 max tokens

## Task Commits

Each task was committed atomically (TDD for Task 1):

1. **Task 1: AgentNode graph adapter** - `61eda6d` (test) + `6f8917d` (feat)
2. **Task 2: YAML agent configs and config loader** - `b2a3525` (feat)

## Files Created/Modified
- `libs/graph-engine/src/graph_engine/nodes/agent_node.py` - AgentNode dataclass wrapping BaseAgent with recovery, timeout, metrics, events
- `libs/graph-engine/src/graph_engine/nodes/__init__.py` - Barrel exports for AgentNode, NoOpWorktreeProvider
- `libs/graph-engine/pyproject.toml` - Added agent-sdk workspace dependency, asyncio fixture scope
- `libs/graph-engine/tests/conftest.py` - ConcreteTestAgent, FailingTestAgent, SlowTestAgent fixtures
- `libs/graph-engine/tests/test_agent_node.py` - 10 tests for AgentNode execution, recovery, timeout, events
- `configs/agents/_schema.yaml` - Documented template with all AgentConfig fields and comments
- `configs/agents/orchestrator.yaml` - Reference config for orchestrator agent
- `apps/server/src/codebot/agent_config/__init__.py` - Package init with barrel exports
- `apps/server/src/codebot/agent_config/loader.py` - AgentConfigLoader class and load_all_agent_configs function
- `apps/server/tests/test_agent_loader.py` - 5 tests for config loading, skipping, validation
- `apps/server/pyproject.toml` - Added agent-sdk workspace dependency

## Decisions Made
- **Workspace cross-dependency via tool.uv.sources**: Both graph-engine and codebot-server now depend on agent-sdk through uv workspace resolution (`agent-sdk = { workspace = true }`). This avoids pip path dependencies.
- **NoOpWorktreeProvider returns cwd**: Returns "." as worktree path. Phase 8 (Agent Isolation) will implement real git worktree management.
- **worktree_provider typed as Any**: Using `Any` instead of `WorktreeProvider` protocol to avoid adding a type: ignore or complex conditional import. The protocol is checked at runtime via duck typing.
- **Synchronous on_event callback**: Event emission is a synchronous `Callable[[dict], None]` rather than async, keeping the hot path simple. EventBus integration (async publish) is the responsibility of the caller.
- **_-prefixed YAML files skipped**: _schema.yaml uses the _ prefix convention so the loader automatically skips documentation/template files.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added tool.uv.sources for workspace dependency resolution**
- **Found during:** Task 1 (AgentNode implementation)
- **Issue:** Adding `agent-sdk` to graph-engine dependencies failed -- uv requires explicit `tool.uv.sources` for workspace members
- **Fix:** Added `[tool.uv.sources] agent-sdk = { workspace = true }` to graph-engine and server pyproject.toml
- **Files modified:** libs/graph-engine/pyproject.toml, apps/server/pyproject.toml
- **Verification:** `uv run pytest` resolves agent-sdk correctly
- **Committed in:** 6f8917d, b2a3525

**2. [Rule 3 - Blocking] Fixed conftest import in test file**
- **Found during:** Task 1 (AgentNode tests)
- **Issue:** `from conftest import ConcreteTestAgent` fails -- pytest conftest is auto-discovered, not importable as module
- **Fix:** Removed direct conftest import; used BaseAgent type hints with pytest fixture injection
- **Files modified:** libs/graph-engine/tests/test_agent_node.py
- **Verification:** All 10 tests collect and pass
- **Committed in:** 6f8917d

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes necessary for dependency resolution and test collection. No scope creep.

## Issues Encountered
None beyond the auto-fixed blocking issues above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- AgentNode is ready for pipeline orchestration (Phase 6) -- any BaseAgent can be wrapped and executed in a graph
- YAML config infrastructure supports adding new agent configs by dropping YAML files into configs/agents/
- Phase 4 (Multi-LLM Abstraction) can proceed -- AgentNode's on_event callback provides the integration point
- Phase 8 (Agent Isolation) has a clean stub (NoOpWorktreeProvider) to replace with real worktree management
- Phase 9 (Agent Implementations) has the config loading pattern established for declarative agent definition

## Self-Check: PASSED
