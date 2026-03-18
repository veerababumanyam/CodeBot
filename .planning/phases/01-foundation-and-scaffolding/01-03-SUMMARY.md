---
phase: 01-foundation-and-scaffolding
plan: "03"
subsystem: shared-types
tags: [pydantic, typescript, nats, jetstream, enums, event-bus, agent-sdk, shared-types]
dependency_graph:
  requires:
    - phase: "01-01"
      provides: "uv workspace with agent-sdk and shared-types packages registered"
    - phase: "01-02"
      provides: "NATS Docker service running with JetStream enabled"
  provides:
    - "17 StrEnum types in agent_sdk.models.enums (Python)"
    - "Matching 17 TypeScript string enums in @codebot/shared-types/enums"
    - "Pydantic v2 schemas: ProjectSchema, PipelineSchema, PipelinePhaseSchema, AgentSchema, AgentExecutionSchema, TaskSchema"
    - "Event payload models: AgentEvent, TaskEvent, PipelineEvent, EventEnvelope"
    - "API contract models: PipelineCreateRequest, PipelineStatusResponse"
    - "NATS JetStream EventBus with publish/subscribe/drain"
    - "publish_event() helper for EventEnvelope serialization"
    - "25 tests: 20 model tests + 5 JetStream integration tests"
    - "Cross-language enum parity test (Python vs TypeScript)"
  affects:
    - "02-graph-engine"
    - "03-agent-system"
    - "04-api-layer"
    - "05-dashboard"
tech_stack:
  added:
    - "nats-py 2.9+ (JetStream pub/sub)"
  patterns:
    - "StrEnum pattern: str + enum.Enum for JSON-native serialization"
    - "from_attributes=True on all Pydantic schemas for ORM compatibility"
    - "EventEnvelope: typed wrapper around raw bytes payload for NATS routing"
    - "publish_event() maps EventType enum values to dotted NATS subject suffixes"
    - "Cross-language enum parity verified by automated pytest test reading the TS file"
key_files:
  created:
    - "libs/agent-sdk/src/agent_sdk/models/enums.py — 17 StrEnum classes (complete domain coverage)"
    - "libs/agent-sdk/src/agent_sdk/models/project.py — ProjectSchema, PipelineSchema, PipelinePhaseSchema"
    - "libs/agent-sdk/src/agent_sdk/models/agent.py — AgentSchema, AgentExecutionSchema"
    - "libs/agent-sdk/src/agent_sdk/models/task.py — TaskSchema"
    - "libs/agent-sdk/src/agent_sdk/models/pipeline.py — PipelineCreateRequest, PipelineStatusResponse"
    - "libs/agent-sdk/src/agent_sdk/models/events.py — AgentEvent, TaskEvent, PipelineEvent, EventEnvelope"
    - "libs/agent-sdk/src/agent_sdk/models/__init__.py — barrel export all schemas and enums"
    - "libs/shared-types/src/enums.ts — 17 TypeScript string enums matching Python exactly"
    - "libs/shared-types/src/project.ts — Project, Pipeline, PipelinePhase interfaces"
    - "libs/shared-types/src/agent.ts — Agent, AgentExecution interfaces"
    - "libs/shared-types/src/task.ts — Task interface"
    - "libs/shared-types/src/events.ts — AgentEvent, TaskEvent, PipelineEvent, EventEnvelope interfaces"
    - "apps/server/src/codebot/events/bus.py — EventBus, create_event_bus, publish_event"
    - "apps/server/src/codebot/events/__init__.py — module exports"
    - "apps/server/tests/test_models.py — 20 model tests + cross-language parity test"
    - "apps/server/tests/test_events.py — 5 JetStream integration tests"
  modified:
    - "libs/agent-sdk/src/agent_sdk/__init__.py — re-export all models from package root"
    - "libs/shared-types/src/index.ts — barrel exports (enums as values, interfaces as types)"
decisions:
  - "StrEnum pattern (str, enum.Enum) used for all enums — values serialize directly to strings in JSON without custom serializers"
  - "Cross-language parity enforced by test_enum_parity_with_typescript which parses the TS enums.ts file at test time — any drift fails CI"
  - "EventEnvelope.payload is bytes — keeps inner event model opaque for JetStream routing; consumers route on event_type before deserializing"
  - "publish_event maps EventType value to dotted lowercase NATS subject (AGENT_COMPLETED -> agent.completed)"
  - "JetStream stream creation is idempotent — safe to call on every connect() without checking existence first"
  - "uv sync --all-packages --extra dev required for workspace-level pytest installation (not just per-package sync)"
  - "datetime.utcnow() replaced with datetime.now(tz=timezone.utc) to avoid Python 3.12 deprecation warning"
requirements-completed:
  - REQ-004
  - REQ-005
duration: 9min
completed: "2026-03-18"
---

# Phase 01 Plan 03: Shared Pydantic Models, TypeScript Types, and NATS JetStream Event Bus Summary

**17 StrEnum-based shared data contracts (Pydantic + TypeScript), NATS JetStream EventBus with durable stream, and 25 passing tests including automated cross-language enum parity verification.**

## Performance

- **Duration:** 9 minutes
- **Started:** 2026-03-18T07:20:17Z
- **Completed:** 2026-03-18T07:29:30Z
- **Tasks:** 2
- **Files created:** 16
- **Files modified:** 2

## Accomplishments

- 17 Python StrEnum classes covering full CodeBot domain (Projects, Pipelines, Phases, Tasks, Agents, Executions, Tests, Experiments, Security, Events)
- Matching TypeScript string enums with identical member names — cross-language parity verified by automated pytest test parsing the TS source
- 6 Pydantic v2 read schemas (ProjectSchema, PipelineSchema, PipelinePhaseSchema, AgentSchema, AgentExecutionSchema, TaskSchema) plus 4 event payload models and 2 API contract models
- TypeScript interfaces mirroring all Pydantic schemas (6 interface files, all strict-mode compliant)
- NATS JetStream EventBus with connect/disconnect/publish/subscribe/drain, `codebot-events` stream (100k message retention)
- 25 tests: 20 Pydantic model tests (instantiation, validation, enum serialization, JSON round-trips) + 5 JetStream integration tests (pub/sub within 1 second, envelope round-trip, filtered subscription, publish_event helper, create_event_bus factory)

## Task Commits

Each task was committed atomically:

1. **Task 1: Shared Pydantic models and TypeScript types** - `d83b791` (feat)
2. **Task 2: NATS JetStream event bus with pub/sub tests** - `fd0c93f` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `libs/agent-sdk/src/agent_sdk/models/enums.py` - 17 StrEnum classes covering all domain concepts
- `libs/agent-sdk/src/agent_sdk/models/project.py` - ProjectSchema, PipelineSchema, PipelinePhaseSchema with from_attributes=True
- `libs/agent-sdk/src/agent_sdk/models/agent.py` - AgentSchema, AgentExecutionSchema
- `libs/agent-sdk/src/agent_sdk/models/task.py` - TaskSchema with UUID dependency list
- `libs/agent-sdk/src/agent_sdk/models/pipeline.py` - PipelineCreateRequest, PipelineStatusResponse API contracts
- `libs/agent-sdk/src/agent_sdk/models/events.py` - Event payload models, EventEnvelope with bytes payload
- `libs/agent-sdk/src/agent_sdk/models/__init__.py` - Barrel exports for all schemas and enums
- `libs/agent-sdk/src/agent_sdk/__init__.py` - Re-exports from models subpackage (modified)
- `libs/shared-types/src/enums.ts` - 17 TypeScript string enums matching Python exactly
- `libs/shared-types/src/project.ts` - Project, Pipeline, PipelinePhase interfaces
- `libs/shared-types/src/agent.ts` - Agent, AgentExecution interfaces
- `libs/shared-types/src/task.ts` - Task interface
- `libs/shared-types/src/events.ts` - AgentEvent, TaskEvent, PipelineEvent, EventEnvelope interfaces
- `libs/shared-types/src/index.ts` - Barrel exports with verbatimModuleSyntax (modified)
- `apps/server/src/codebot/events/bus.py` - EventBus class, create_event_bus, publish_event
- `apps/server/src/codebot/events/__init__.py` - Module exports
- `apps/server/tests/test_models.py` - 20 model tests + cross-language parity test
- `apps/server/tests/test_events.py` - 5 NATS JetStream integration tests

## Decisions Made

- StrEnum pattern (`str, enum.Enum`) chosen over `enum.StrEnum` (Python 3.11+) for maximum JSON serialization compatibility with Pydantic v2 without custom serializers
- Cross-language parity enforced by a pytest test that parses `enums.ts` using regex at test runtime — any future drift between Python and TypeScript enum members will fail the CI suite
- EventEnvelope wraps inner event model as raw `bytes` so NATS consumers can route on `event_type` before deserializing the payload — avoids tight coupling between the bus and specific event model types
- JetStream stream creation in `connect()` is idempotent — catches "already exists" errors gracefully so multiple service restarts do not fail
- `uv sync --all-packages --extra dev` (not just `uv sync`) required to install pytest into the workspace venv — documented as a deviation for operational awareness

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Fixed datetime.utcnow() deprecation**
- **Found during:** Task 1 (running model tests)
- **Issue:** `datetime.utcnow()` generates `DeprecationWarning` in Python 3.12 (scheduled for removal in 3.14)
- **Fix:** Changed to `datetime.now(tz=timezone.utc)` in `events.py` default factories
- **Files modified:** `libs/agent-sdk/src/agent_sdk/models/events.py`
- **Verification:** No deprecation warnings in test output after fix
- **Committed in:** d83b791 (Task 1 commit)

**2. [Rule 3 - Blocking] Fixed cross-language parity test path calculation**
- **Found during:** Task 1 (parity test was incorrectly skipping)
- **Issue:** `Path(__file__).parents[4]` for `apps/server/tests/test_models.py` computed wrong path (went above CodeBot root). Correct is `parents[3]`
- **Fix:** Changed `parents[4]` to `parents[3]` in `_TS_ENUMS_FILE` constant
- **Files modified:** `apps/server/tests/test_models.py`
- **Verification:** `test_enum_parity_with_typescript` now runs and passes (20/20 tests pass)
- **Committed in:** d83b791 (Task 1 commit, same commit)

**3. [Rule 3 - Blocking] Fixed JetStream test isolation issue**
- **Found during:** Task 2 (test_publish_event_helper received stale message from previous test)
- **Issue:** JetStream retains messages; test subscribing to `agent.completed` received a message published by an earlier test in the same suite run
- **Fix:** Changed test to drain messages and identify ours by `source_agent_id` UUID comparison rather than assuming first message is ours
- **Files modified:** `apps/server/tests/test_events.py`
- **Verification:** 5/5 event tests pass when run sequentially and in combination with model tests
- **Committed in:** fd0c93f (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (1 missing critical, 2 blocking)
**Impact on plan:** All auto-fixes necessary for correctness and test reliability. No scope creep.

## Issues Encountered

- `uv sync` (without `--all-packages`) does not install workspace member packages into the shared venv. Required `uv sync --all-packages --extra dev` to make `agent_sdk` and `pytest` importable in the same environment.

## User Setup Required

None - NATS was already running from Plan 01-02 Docker stack. No new external services needed.

## Next Phase Readiness

- All shared type contracts available — agent-sdk models are the canonical source of truth for inter-service communication
- TypeScript types ready for dashboard imports via `@codebot/shared-types`
- NATS JetStream event bus ready for graph engine integration (Phase 02)
- Cross-language parity test in CI prevents future enum drift

## Self-Check: PASSED

All 18 key files exist on disk. Both commits (d83b791, fd0c93f) verified in git log. 25 tests pass.

---
*Phase: 01-foundation-and-scaffolding*
*Completed: 2026-03-18*
