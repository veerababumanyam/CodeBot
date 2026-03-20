---
phase: 10-fastapi-server-api-layer
plan: 02
subsystem: api
tags: [fastapi, pipeline, agent, websocket, socketio, nats, jwt, pydantic]

# Dependency graph
requires:
  - phase: 10-fastapi-server-api-layer
    provides: Auth, response envelope, project CRUD, deps, middleware from Plan 01
provides:
  - Pipeline CRUD and lifecycle endpoints (create with YAML presets, start/pause/resume/cancel)
  - Agent management endpoints (list/get/types/start/stop/restart/configure)
  - Socket.IO WebSocket server with JWT auth and project room management
  - NATS-to-Socket.IO event bridge for real-time streaming
  - PipelineService with state machine transitions and YAML preset loading
  - AgentService with lifecycle management and agent type catalog
affects: [11-react-dashboard, 12-integration-testing]

# Tech tracking
tech-stack:
  added: [python-socketio]
  patterns: [service-layer-state-machine, yaml-preset-loading, nats-socketio-bridge, project-room-websocket]

key-files:
  created:
    - apps/server/src/codebot/api/schemas/pipelines.py
    - apps/server/src/codebot/api/schemas/agents.py
    - apps/server/src/codebot/services/pipeline_service.py
    - apps/server/src/codebot/services/agent_service.py
    - apps/server/src/codebot/api/routes/pipelines.py
    - apps/server/src/codebot/api/routes/agents.py
    - apps/server/src/codebot/websocket/manager.py
    - apps/server/src/codebot/websocket/bridge.py
    - apps/server/tests/api/test_pipelines.py
    - apps/server/tests/api/test_agents.py
    - apps/server/tests/websocket/test_manager.py
    - apps/server/tests/websocket/test_bridge.py
  modified:
    - apps/server/src/codebot/main.py
    - apps/server/pyproject.toml

key-decisions:
  - "PipelineCreate.mode pattern extended to include quick and review_only presets alongside full/incremental/phase_only"
  - "YAML preset loading uses module-level function called at class definition time (not classmethod) to avoid callable error"
  - "Pipeline model lacks created_at column -- removed from PipelineResponse schema to match ORM"
  - "Annotated[T, Query()] pattern for all Query defaults (ruff B008 compliance)"
  - "Bridge uses TimeoutError not asyncio.TimeoutError (ruff UP041)"

patterns-established:
  - "Service state machine: VALID_TRANSITIONS dict mapping current status to list of valid targets"
  - "YAML config loading with in-memory fallback: try YAML file, fall back to hardcoded defaults"
  - "Dual router pattern: project_pipelines_router for nested URLs, router for direct paths"
  - "Direct DB insertion in tests for entities without creation APIs (Agent records)"

requirements-completed: [SRVR-02, SRVR-04, SRVR-05]

# Metrics
duration: 12min
completed: 2026-03-20
---

# Phase 10 Plan 02: Pipeline & Agent Endpoints + WebSocket Streaming Summary

**Pipeline CRUD with YAML preset selection (full/quick/review_only), agent lifecycle management (start/stop/restart/configure), and Socket.IO real-time streaming with NATS event bridge**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-20T09:38:01Z
- **Completed:** 2026-03-20T09:50:01Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- Pipeline CRUD endpoints with 3 preset modes (full=10 phases, quick=3, review_only=2) loaded from YAML with in-memory fallback
- Pipeline lifecycle state machine (PENDING->RUNNING->PAUSED, with cancel from any active state)
- Agent management with full lifecycle (start, stop, restart, configure) and 30 agent type catalog
- Socket.IO WebSocket server with JWT authentication, project room management, and connection.established events
- NATS-to-Socket.IO bridge forwarding events to correct project rooms
- 31 tests passing: 11 pipeline, 12 agent, 8 websocket

## Task Commits

Each task was committed atomically:

1. **Task 1: Pipeline and agent schemas, services, and route endpoints** - `718eb75` (feat)
2. **Task 2: WebSocket manager, NATS bridge, main.py mounting, and full test suite** - `1634433` (feat)

## Files Created/Modified
- `apps/server/src/codebot/api/schemas/pipelines.py` - Pipeline request/response schemas (PipelineCreate, PipelineResponse, PipelineDetailResponse, PipelinePhaseResponse, PipelineActionResponse, PhaseApprovalRequest)
- `apps/server/src/codebot/api/schemas/agents.py` - Agent request/response schemas (AgentResponse, AgentDetailResponse, AgentStopRequest, AgentConfigUpdate, AgentMessageRequest, AgentTypeInfo)
- `apps/server/src/codebot/services/pipeline_service.py` - Pipeline business logic with state machine, YAML preset loading, phase management
- `apps/server/src/codebot/services/agent_service.py` - Agent lifecycle service with start/stop/restart/configure and 30-type catalog
- `apps/server/src/codebot/api/routes/pipelines.py` - Pipeline CRUD and lifecycle endpoints (dual router pattern)
- `apps/server/src/codebot/api/routes/agents.py` - Agent management endpoints (list, types, get, start, stop, restart, configure)
- `apps/server/src/codebot/websocket/manager.py` - Socket.IO server with JWT auth and room management
- `apps/server/src/codebot/websocket/bridge.py` - NATS-to-Socket.IO event forwarding bridge
- `apps/server/src/codebot/main.py` - Register pipeline/agent routers, mount Socket.IO, NATS bridge lifespan
- `apps/server/pyproject.toml` - Added python-socketio dependency
- `apps/server/tests/api/test_pipelines.py` - 11 pipeline endpoint tests
- `apps/server/tests/api/test_agents.py` - 12 agent endpoint tests
- `apps/server/tests/websocket/test_manager.py` - 5 WebSocket auth tests
- `apps/server/tests/websocket/test_bridge.py` - 3 NATS bridge tests

## Decisions Made
- Extended PipelineCreate.mode pattern to include `quick` and `review_only` alongside `full|incremental|phase_only` -- required by success criteria for preset endpoint tests
- Used module-level `_load_preset_phases()` function instead of `@classmethod` for YAML loading at class definition time (classmethod descriptor not callable in class body)
- Removed `created_at` from PipelineResponse since Pipeline ORM model does not have a created_at column (it has started_at/completed_at)
- Used `Annotated[T, Query()]` pattern for all FastAPI Query parameters per ruff B008 rule (consistent with Phase 10-01 pattern)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed PipelineResponse missing created_at field**
- **Found during:** Task 2 (test_create_pipeline)
- **Issue:** PipelineResponse schema included `created_at: datetime` but Pipeline ORM model has no created_at column
- **Fix:** Removed created_at from PipelineResponse
- **Files modified:** apps/server/src/codebot/api/schemas/pipelines.py
- **Committed in:** 1634433

**2. [Rule 1 - Bug] Fixed load_preset_phases classmethod not callable in class body**
- **Found during:** Task 1 (import verification)
- **Issue:** `@classmethod` descriptor is not callable during class body execution, causing TypeError
- **Fix:** Moved YAML loading to module-level function `_load_preset_phases()`, called at class definition time
- **Files modified:** apps/server/src/codebot/services/pipeline_service.py
- **Committed in:** 718eb75

**3. [Rule 2 - Missing Critical] Added quick and review_only to PipelineCreate mode validation**
- **Found during:** Task 2 (test writing)
- **Issue:** Mode regex pattern only allowed full|incremental|phase_only, but quick and review_only presets need to be selectable via API
- **Fix:** Extended pattern to `^(full|quick|review_only|incremental|phase_only)$`
- **Files modified:** apps/server/src/codebot/api/schemas/pipelines.py
- **Committed in:** 1634433

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 missing critical)
**Impact on plan:** All fixes necessary for correctness. No scope creep.

## Issues Encountered
- pytest not installed in workspace venv -- used `uv pip install pytest pytest-asyncio httpx` to add test deps directly
- Global pytest on Python 3.11 cannot find socketio installed in 3.12 venv -- resolved by using venv pytest

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three SRVR requirements (SRVR-02, SRVR-04, SRVR-05) complete
- Phase 10 fully complete -- all API endpoints, auth, WebSocket, and tests in place
- Ready for Phase 11 (React Dashboard) which will consume these API endpoints
- WebSocket /ws endpoint ready for dashboard real-time features

## Self-Check: PASSED

All 15 created files verified present. Both task commits (718eb75, 1634433) verified in git log. 31/31 tests passing.

---
*Phase: 10-fastapi-server-api-layer*
*Completed: 2026-03-20*
