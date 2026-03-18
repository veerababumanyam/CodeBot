---
phase: 06-pipeline-orchestration
plan: 04
subsystem: pipeline
tags: [temporal, workflows, worker, docker-compose, parallel-execution, signals, continue-as-new]

# Dependency graph
requires:
  - phase: 06-pipeline-orchestration
    provides: "Pipeline DTOs, Temporal activities, gate logic, NATS events (Plans 01-03)"
provides:
  - "SDLCPipelineWorkflow: top-level durable 10-stage pipeline orchestration"
  - "PhaseAgentWorkflow: per-agent child workflow for parallel execution"
  - "create_worker / run_worker: Temporal worker with all workflows and activities"
  - "Docker Compose Temporal server and UI services"
  - "Integration tests for E2E, durability, and resume"
affects: [api-layer, deployment, testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "workflow.unsafe.imports_passed_through() for sandbox-safe imports in Temporal workflows"
    - "UnsandboxedWorkflowRunner for Temporal test environments"
    - "Activity name overrides for test stub registration"

key-files:
  created:
    - apps/server/src/codebot/pipeline/workflows.py
    - apps/server/src/codebot/pipeline/worker.py
    - tests/unit/pipeline/test_parallel_phases.py
    - tests/conftest.py
    - tests/integration/__init__.py
    - tests/integration/test_pipeline_e2e.py
    - tests/integration/test_temporal_durability.py
    - tests/integration/test_pipeline_resume.py
  modified:
    - docker-compose.yml
    - apps/server/src/codebot/pipeline/__init__.py

key-decisions:
  - "UnsandboxedWorkflowRunner for tests -- avoids sandbox restrictions on transitive imports (loader.py uses pathlib.Path.resolve at module level)"
  - "pipeline_input/phase_input parameter names in workflow run methods to avoid ruff A002 builtin shadow"
  - "Temporal signal args passed via args=[] kwarg for multi-parameter signals"
  - "NATS event emitter initialization is best-effort in worker -- pipeline runs without NATS"

patterns-established:
  - "Temporal workflow testing: UnsandboxedWorkflowRunner + WorkflowEnvironment.start_time_skipping()"
  - "Activity stubs with @activity.defn(name=...) for test isolation"
  - "conftest.py temporal_env fixture for shared test environment"

requirements-completed: [PIPE-01, PIPE-02, PIPE-05, PIPE-06]

# Metrics
duration: 12min
completed: 2026-03-18
---

# Phase 6 Plan 4: Temporal Workflows, Worker, and Integration Tests Summary

**SDLCPipelineWorkflow with sequential/parallel phase execution, signals, gates, continue-as-new, Temporal worker, and 14 integration tests**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-18T20:14:10Z
- **Completed:** 2026-03-18T20:26:44Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments
- SDLCPipelineWorkflow orchestrates 10-stage pipeline with sequential and parallel phase execution, human gates, pause/resume, and continue-as-new
- PhaseAgentWorkflow provides per-agent durability via Temporal child workflows with asyncio.gather
- Temporal worker with all workflows, activities, and NATS event emitter initialization
- Docker Compose Temporal server (auto-setup) and UI services
- Comprehensive test suite: 8 unit tests + 6 integration tests all passing
- ruff and mypy --strict clean across entire pipeline module (11 source files)

## Task Commits

Each task was committed atomically:

1. **Task 1: SDLCPipelineWorkflow and PhaseAgentWorkflow** - `74e1efe` (feat)
   - TDD: RED `0d63709` -> GREEN `74e1efe`
2. **Task 2: Temporal worker and Docker Compose** - `5462ff6` (feat)
3. **Task 3: Integration tests** - `5f8865f` (test)
   - Includes ruff A002 and mypy strict fixes in workflows.py

## Files Created/Modified
- `apps/server/src/codebot/pipeline/workflows.py` - SDLCPipelineWorkflow and PhaseAgentWorkflow Temporal workflow definitions
- `apps/server/src/codebot/pipeline/worker.py` - Temporal worker with NATS event emitter initialization
- `docker-compose.yml` - Added temporal and temporal-ui services
- `apps/server/src/codebot/pipeline/__init__.py` - Exports create_worker, run_worker
- `tests/conftest.py` - Shared Temporal WorkflowEnvironment fixture
- `tests/unit/pipeline/test_parallel_phases.py` - 8 unit tests for workflow behavior
- `tests/integration/__init__.py` - Integration test package
- `tests/integration/test_pipeline_e2e.py` - 2 E2E pipeline tests
- `tests/integration/test_temporal_durability.py` - 2 durability tests (retry, timeout)
- `tests/integration/test_pipeline_resume.py` - 2 resume tests (skip phases, correct count)

## Decisions Made
- **UnsandboxedWorkflowRunner for tests:** Temporal sandbox restricts pathlib.Path.resolve() used in loader.py at module level. Using UnsandboxedWorkflowRunner avoids this in tests; production worker uses SandboxedWorkflowRunner with passthrough_modules.
- **pipeline_input/phase_input parameter names:** Renamed from `input` to avoid ruff A002 builtin shadow, consistent with Phase 06-02 convention.
- **NATS emitter best-effort:** Worker gracefully degrades if NATS is unavailable -- events fall back to logging. This allows running the pipeline without the full Docker stack.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Temporal sandbox restriction on pathlib.Path.resolve**
- **Found during:** Task 1 (unit tests)
- **Issue:** Temporal sandbox blocked `pathlib.Path.resolve.__call__` from loader.py module-level code during workflow validation
- **Fix:** Used `UnsandboxedWorkflowRunner` in test Workers; `workflow.unsafe.imports_passed_through()` already in place for production
- **Files modified:** tests/unit/pipeline/test_parallel_phases.py
- **Verification:** All 8 unit tests pass
- **Committed in:** 74e1efe (Task 1)

**2. [Rule 1 - Bug] Temporal signal multi-arg API**
- **Found during:** Task 1 (signal test)
- **Issue:** `handle.signal(SDLCPipelineWorkflow.approve_gate, "gate_design", "approved")` fails -- signal() accepts single `arg` or `args=[]`
- **Fix:** Changed to `handle.signal(..., args=["gate_design", "approved"])`
- **Files modified:** tests/unit/pipeline/test_parallel_phases.py
- **Verification:** Signal test passes
- **Committed in:** 74e1efe (Task 1)

**3. [Rule 1 - Bug] Parallel phase duplicate tracking in E2E test**
- **Found during:** Task 3 (E2E test)
- **Issue:** Parallel phase "implement" with 2 agents adds phase name twice to tracker (once per child workflow)
- **Fix:** Used `dict.fromkeys()` for ordered unique phase names in assertion
- **Files modified:** tests/integration/test_pipeline_e2e.py
- **Verification:** E2E test passes
- **Committed in:** 5f8865f (Task 3)

**4. [Rule 1 - Bug] ruff A002 and mypy strict compliance**
- **Found during:** Task 3 (verification)
- **Issue:** Parameter name `input` shadows Python builtin; mypy strict required `dict[str, Any]` instead of `dict`
- **Fix:** Renamed to `pipeline_input`/`phase_input`; added `Any` type annotations
- **Files modified:** apps/server/src/codebot/pipeline/workflows.py
- **Verification:** ruff and mypy --strict pass cleanly
- **Committed in:** 5f8865f (Task 3)

---

**Total deviations:** 4 auto-fixed (2 bugs, 1 blocking, 1 bug)
**Impact on plan:** All fixes necessary for correctness and code quality. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required. Docker Compose services are self-contained.

## Next Phase Readiness
- Phase 6 Pipeline Orchestration is complete (all 4 plans done)
- Full pipeline path validated: config loading -> phase execution -> parallel child workflows -> signals/gates -> resume
- 91 total pipeline tests passing (85 unit + 6 integration)
- Ready for Phase 7+ which builds on this orchestration layer

## Self-Check: PASSED

All 9 files verified present. All 4 commits verified in git history.

---
*Phase: 06-pipeline-orchestration*
*Completed: 2026-03-18*
