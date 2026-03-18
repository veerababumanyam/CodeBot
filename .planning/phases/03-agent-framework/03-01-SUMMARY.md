---
phase: 03-agent-framework
plan: 01
subsystem: agent-sdk
tags: [python, dataclass, pydantic, fsm, state-machine, pra-cycle, yaml-config, recovery-strategy, metrics]

# Dependency graph
requires:
  - phase: 01-foundation-and-scaffolding
    provides: "ORM models (AgentType, AgentStatus enums), Pydantic schemas, EventBus"
provides:
  - "BaseAgent abstract class with PRA cognitive cycle (perceive, reason, act, review)"
  - "AgentStateMachine with 7 states and 9 validated transition edges"
  - "4 recovery strategies (RetryWithModifiedPrompt, FallbackModel, Escalate, Rollback)"
  - "AgentMetrics collector for tokens, cost, timing, retries"
  - "AgentConfig Pydantic model for YAML validation with frozen=True, extra=forbid"
  - "Protocol stubs for LLMProvider, WorktreeProvider, ToolRegistry"
  - "AgentPhase runtime enum (higher resolution than ORM AgentStatus)"
affects: [04-multi-llm-abstraction, 05-context-management, 06-pipeline-orchestration, 08-agent-isolation, 09-agent-implementations]

# Tech tracking
tech-stack:
  added: [pyyaml, pytest-asyncio]
  patterns: [pra-cognitive-cycle, enum-based-fsm, strategy-pattern-recovery, fresh-per-execute-statelessness]

key-files:
  created:
    - libs/agent-sdk/src/agent_sdk/agents/__init__.py
    - libs/agent-sdk/src/agent_sdk/agents/base.py
    - libs/agent-sdk/src/agent_sdk/agents/state_machine.py
    - libs/agent-sdk/src/agent_sdk/agents/recovery.py
    - libs/agent-sdk/src/agent_sdk/agents/metrics.py
    - libs/agent-sdk/src/agent_sdk/agents/protocols.py
    - libs/agent-sdk/src/agent_sdk/models/agent_config.py
    - libs/agent-sdk/tests/__init__.py
    - libs/agent-sdk/tests/conftest.py
    - libs/agent-sdk/tests/test_state_machine.py
    - libs/agent-sdk/tests/test_recovery.py
    - libs/agent-sdk/tests/test_metrics.py
    - libs/agent-sdk/tests/test_base_agent.py
    - libs/agent-sdk/tests/test_agent_config.py
  modified:
    - libs/agent-sdk/src/agent_sdk/models/enums.py
    - libs/agent-sdk/src/agent_sdk/models/__init__.py
    - libs/agent-sdk/pyproject.toml

key-decisions:
  - "AgentPhase runtime enum separate from ORM AgentStatus -- higher resolution for EXECUTING/REVIEWING/RECOVERING states"
  - "State machine and metrics created fresh per execute() call -- enforces statelessness between executions"
  - "Hand-rolled FSM with dict transition table -- 7 states too simple for library overhead"
  - "RecoveryAction uses class-level constants (not enum) for extensibility"
  - "AgentConfig uses frozen=True and extra=forbid for strict YAML validation"

patterns-established:
  - "PRA cycle: perceive -> reason -> act (loop) -> review in BaseAgent.execute()"
  - "Fresh-per-execute: state_machine and metrics are local to execute(), not stored on self"
  - "TDD workflow: RED (failing tests) -> commit -> GREEN (implementation) -> commit"
  - "Protocol stubs for deferred dependencies (LLMProvider, WorktreeProvider, ToolRegistry)"
  - "YAML config: single top-level key pattern with agent name as key"

requirements-completed: [AGNT-01, AGNT-03, AGNT-05, AGNT-06, AGNT-07, AGNT-12]

# Metrics
duration: 8min
completed: 2026-03-18
---

# Phase 3 Plan 1: Agent Framework Core Summary

**BaseAgent with PRA cognitive cycle, 7-state FSM, 4 recovery strategies, metrics collector, YAML config validation, and LLM/worktree protocol stubs -- 45 unit tests passing**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-18T11:04:03Z
- **Completed:** 2026-03-18T11:12:04Z
- **Tasks:** 2
- **Files modified:** 17

## Accomplishments
- BaseAgent abstract class executes the full PRA cycle (perceive, reason, act, review) with observable state transitions through IDLE -> INITIALIZING -> EXECUTING -> REVIEWING -> COMPLETED
- AgentStateMachine validates 9 transition edges and rejects all invalid transitions with clear error messages
- 4 composable recovery strategies return correct actions based on attempt count and configured limits
- AgentConfig loads from YAML, validates against AgentType enum, rejects unknown keys, and prevents post-creation mutation
- Protocol stubs define clean interfaces for LLM, worktree, and tool dependencies that downstream phases will implement

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1: State machine, recovery, metrics, protocols** - `fc2e355` (test) + `5c91104` (feat)
2. **Task 2: BaseAgent PRA cycle, AgentConfig** - `f806bf2` (test) + `3ce8b3f` (feat)

## Files Created/Modified
- `libs/agent-sdk/src/agent_sdk/agents/base.py` - BaseAgent abstract class with PRA cycle, AgentInput, AgentOutput, PRAResult
- `libs/agent-sdk/src/agent_sdk/agents/state_machine.py` - AgentStateMachine with VALID_TRANSITIONS dict and InvalidTransitionError
- `libs/agent-sdk/src/agent_sdk/agents/recovery.py` - RecoveryStrategy hierarchy with 4 concrete strategies
- `libs/agent-sdk/src/agent_sdk/agents/metrics.py` - AgentMetrics with token/cost/timing tracking
- `libs/agent-sdk/src/agent_sdk/agents/protocols.py` - LLMProvider, WorktreeProvider, ToolRegistry protocol stubs
- `libs/agent-sdk/src/agent_sdk/agents/__init__.py` - Barrel exports for all 16 public types
- `libs/agent-sdk/src/agent_sdk/models/agent_config.py` - AgentConfig, RetryPolicyConfig, ContextTiersConfig, load_agent_config
- `libs/agent-sdk/src/agent_sdk/models/enums.py` - Added AgentPhase enum (7 runtime states)
- `libs/agent-sdk/src/agent_sdk/models/__init__.py` - Added AgentPhase, AgentConfig, RetryPolicyConfig, ContextTiersConfig exports
- `libs/agent-sdk/pyproject.toml` - Added pyyaml, pytest, pytest-asyncio dependencies
- `libs/agent-sdk/tests/conftest.py` - MockLLMProvider, MockEventCallback fixtures
- `libs/agent-sdk/tests/test_state_machine.py` - 13 tests for transitions and history
- `libs/agent-sdk/tests/test_recovery.py` - 7 tests for all 4 strategies
- `libs/agent-sdk/tests/test_metrics.py` - 5 tests for token/cost/timing tracking
- `libs/agent-sdk/tests/test_base_agent.py` - 10 tests for PRA cycle and statelessness
- `libs/agent-sdk/tests/test_agent_config.py` - 10 tests for YAML validation

## Decisions Made
- **AgentPhase separate from AgentStatus**: The ORM AgentStatus (7 states) lacks EXECUTING/REVIEWING/RECOVERING. Created a higher-resolution runtime AgentPhase enum. Maps to ORM for persistence: EXECUTING/REVIEWING -> RUNNING, RECOVERING -> RUNNING.
- **Fresh-per-execute pattern**: state_machine and metrics are local variables inside execute(), not stored on self. This prevents context pollution between task executions (per SYSTEM_DESIGN Section 14.5).
- **Hand-rolled FSM**: Only 7 states and 9 transitions -- python-statemachine library would add unnecessary dependency and complexity.
- **RecoveryAction as class with constants (not enum)**: Allows easy extensibility for custom actions without modifying the enum.
- **AgentConfig frozen + extra=forbid**: Strictest Pydantic validation -- rejects typos in YAML keys and prevents accidental mutation.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- BaseAgent contract is ready for all downstream consumers (LLM abstraction, context management, pipeline orchestration, agent implementations)
- Protocol stubs (LLMProvider, WorktreeProvider, ToolRegistry) define clean interfaces for Phase 4, 8, and tool registry implementations
- AgentConfig YAML pattern established for configs/agents/ directory population
- Plan 03-02 (AgentNode adapter) can proceed -- it wraps BaseAgent for graph execution

## Self-Check: PASSED

All 14 created files verified present. All 4 commits (fc2e355, 5c91104, f806bf2, 3ce8b3f) verified in git log. 45/45 tests passing.

---
*Phase: 03-agent-framework*
*Completed: 2026-03-18*
