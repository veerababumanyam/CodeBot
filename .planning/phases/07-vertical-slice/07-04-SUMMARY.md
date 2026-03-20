---
phase: 07-vertical-slice
plan: 04
subsystem: pipeline-composition
tags: [vertical-slice, pipeline-graph, event-emitter, nats, e2e-test, quality-gate, debug-routing]

# Dependency graph
requires:
  - phase: 07-01
    provides: "OrchestratorAgent with PRA cycle, ExtractedRequirements models"
  - phase: 07-02
    provides: "BackendDevAgent with code generation, CodeReviewerAgent with quality gate"
  - phase: 07-03
    provides: "TesterAgent with test execution, DebuggerAgent with experiment loop"
  - phase: 06-pipeline-orchestration
    provides: "EventBus with NATS JetStream pub/sub, publish_event helper"
provides:
  - "VerticalSlicePipeline composing 5 agents into executable sequential pipeline"
  - "build_vertical_slice_graph() factory function for pipeline construction"
  - "PipelineEventEmitter wrapping EventBus for structured agent/phase/pipeline NATS events"
  - "vertical-slice.yaml pipeline configuration with 5 phases, gates, and loop config"
  - "E2E integration test proving full pipeline execution with 7 tests"
affects: [08-agent-roster, pipeline-orchestration, observability]

# Tech tracking
tech-stack:
  added: []
  patterns: [pipeline-composition-dataclass, event-emitter-wrapper, patch-object-slots-testing, qa-reroute-loop, conditional-debug-phase]

key-files:
  created:
    - apps/server/src/codebot/pipeline/vertical_slice.py
    - apps/server/src/codebot/pipeline/event_emitter.py
    - configs/pipelines/vertical-slice.yaml
    - tests/integration/test_vertical_slice_e2e.py
  modified: []

key-decisions:
  - "PipelineEventEmitter wraps EventBus (Phase 6) using agent_sdk EventEnvelope/AgentEvent/PipelineEvent models -- complements Phase 6 PipelineEventEmitter which uses raw NATS client"
  - "VerticalSlicePipeline as dataclass with slots=True kw_only=True containing all 5 agent instances"
  - "QA gate reroute implemented as for loop with _MAX_QA_REROUTES=2 -- injects review_comments into shared_state for BackendDev"
  - "Conditional debug phase: only executes when shared_state tests_passing=False"
  - "patch.object() required for testing agents with slots=True dataclasses (direct attribute assignment blocked)"

patterns-established:
  - "Pipeline composition pattern: dataclass with agent instances + shared_state + _run_phase() helper"
  - "Event emitter wrapper: typed methods (agent_started, phase_started, etc.) wrapping EventBus.publish_event()"
  - "QA reroute loop: iterate implementation+QA phases, break on gate_passed=True or max_reroutes"
  - "Integration testing with slots=True: use patch.object(AgentClass, 'execute') instead of direct assignment"
  - "E2E pipeline testing: mock agent execute() at class level, assert on shared_state keys and event counts"

requirements-completed: [EVNT-01, TEST-05]

# Metrics
duration: 8min
completed: 2026-03-20
---

# Phase 07 Plan 04: Pipeline Composition and E2E Integration Summary

**5-agent vertical slice pipeline graph with NATS event emission, QA gate rerouting, test-failure-to-debugger routing, and 7 E2E integration tests proving full architecture**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-20T05:57:52Z
- **Completed:** 2026-03-20T06:05:52Z
- **Tasks:** 2 (auto) + 1 (checkpoint)
- **Files modified:** 4

## Accomplishments
- VerticalSlicePipeline composes all 5 agents (Orchestrator, BackendDev, CodeReviewer, Tester, Debugger) into executable sequential pipeline with SharedState data flow
- PipelineEventEmitter wraps EventBus for typed NATS JetStream events: agent_started/completed/failed, phase_started/completed, pipeline_started/completed
- QA gate enforcement with rerouting: CodeReviewer gate_passed=False triggers implementation reroute (max 2 cycles), injecting review comments into SharedState
- Conditional debug phase: only executes DebuggerAgent when tests_passing=False (TEST-05 requirement)
- vertical-slice.yaml defines complete pipeline configuration with 5 phases, human gates, reroute policy, and debug loop parameters
- 7 E2E integration tests proving: full pipeline execution, event emission, failure-to-debugger routing, debug phase skip, QA gate rerouting, event structure, no-emitter mode
- Full test suite: 232 tests passing (225 unit + 7 integration)

## Task Commits

Each task was committed atomically:

1. **Task 1: Pipeline graph builder, event emitter, and YAML config** - `f984656` (feat)
2. **Task 2: E2E integration test proving full pipeline execution** - `266377d` (test)

## Files Created/Modified
- `apps/server/src/codebot/pipeline/vertical_slice.py` - VerticalSlicePipeline dataclass and build_vertical_slice_graph() factory with 5-phase execution flow, QA reroute loop, conditional debug phase
- `apps/server/src/codebot/pipeline/event_emitter.py` - PipelineEventEmitter wrapping EventBus for typed agent/phase/pipeline event emission via EventEnvelope
- `configs/pipelines/vertical-slice.yaml` - Pipeline configuration: 5 phases (input_processing, implementation, quality_assurance, testing, debug_fix) with gates and loop config
- `tests/integration/test_vertical_slice_e2e.py` - 7 E2E tests: TestFullPipelineExecution (2), TestFailureRoutesToDebugger (2), TestQualityGateEnforcement (1), TestEventEmission (2)

## Decisions Made
- PipelineEventEmitter wraps the Phase 6 EventBus using agent_sdk typed models (EventEnvelope, AgentEvent, PipelineEvent) -- this is distinct from the Phase 6 PipelineEventEmitter which uses raw NATS client for Temporal workflow events
- VerticalSlicePipeline uses dataclass with `slots=True, kw_only=True` per CLAUDE.md convention
- QA gate reroute uses a simple for loop (max 2 reroutes) with review_comments injection into shared_state
- Debug phase is conditional on `tests_passing=False` in shared_state after TesterAgent execution
- E2E tests use `patch.object(AgentClass, 'execute')` instead of direct attribute assignment because `slots=True` on BaseAgent prevents attribute reassignment

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Used patch.object for slots=True dataclass testing**
- **Found during:** Task 2 (E2E integration test)
- **Issue:** `slots=True` on BaseAgent dataclass makes `execute` attribute read-only, preventing `pipeline.orchestrator.execute = AsyncMock(...)` direct assignment
- **Fix:** Changed all tests to use `patch.object(OrchestratorAgent, 'execute', new_callable=AsyncMock, side_effect=...)` context manager pattern
- **Files modified:** tests/integration/test_vertical_slice_e2e.py
- **Verification:** All 7 tests pass
- **Committed in:** 266377d (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor testing pattern adjustment for slots=True compatibility. No scope creep.

## Issues Encountered
- `pytest.mark.timeout(30)` mark caused PytestUnknownMarkWarning since pytest-timeout is not installed. The marks are harmless (ignored) but produce warnings. Left in place for documentation purposes.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Complete vertical slice architecture validated: 5 agents wired together, SharedState flows correctly, events emitted, quality gate enforces, debug routing works
- 232 tests passing across all Phase 7 modules
- All 5 agent YAML configs exist in configs/agents/
- Pipeline YAML config at configs/pipelines/vertical-slice.yaml
- Ready for Phase 8 (Agent Roster) to expand from 5 to 30 agents using the established patterns

## Self-Check: PASSED
