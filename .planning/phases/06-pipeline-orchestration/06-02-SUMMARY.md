---
phase: 06-pipeline-orchestration
plan: 02
subsystem: pipeline
tags: [temporal, dataclass, dto, activity, heartbeat, gate, human-in-the-loop]

# Dependency graph
requires:
  - phase: 06-pipeline-orchestration/01
    provides: PipelineConfig, PhaseConfig, GateConfig, PipelineSettings, load_preset, detect_project_type
provides:
  - PipelineInput, PhaseInput, PhaseResult, PipelineCheckpoint dataclasses for Temporal boundaries
  - PhaseRegistry mapping phase names to agent lists
  - load_pipeline_config, execute_phase_activity, emit_pipeline_event Temporal activities
  - GateManager and GateDecision for human approval gate logic
affects: [06-pipeline-orchestration/03, 06-pipeline-orchestration/04]

# Tech tracking
tech-stack:
  added: [temporalio>=1.23.0]
  patterns: [Temporal activity boundary DTOs, heartbeating per agent, static gate logic]

key-files:
  created:
    - apps/server/src/codebot/pipeline/checkpoint.py
    - apps/server/src/codebot/pipeline/registry.py
    - apps/server/src/codebot/pipeline/activities.py
    - apps/server/src/codebot/pipeline/gates.py
    - tests/unit/pipeline/test_checkpoint.py
    - tests/unit/pipeline/test_registry.py
    - tests/unit/pipeline/test_activities.py
    - tests/unit/pipeline/test_gates.py
  modified:
    - apps/server/src/codebot/pipeline/__init__.py
    - apps/server/pyproject.toml

key-decisions:
  - "dataclasses with slots=True and kw_only=True for all DTOs (per CLAUDE.md convention)"
  - "Renamed execute_phase_activity parameter from 'input' to 'phase_input' to avoid ruff A002 builtin shadowing"
  - "GateDecision uses field(default_factory=lambda: datetime.now(UTC).isoformat()) for auto-timestamping"
  - "PhaseRegistry uses list(phase.agents) in register_from_config to decouple from frozen Pydantic model"

patterns-established:
  - "Temporal activity DTO pattern: dataclasses with only primitive types (str, int, float, bool, list[dict], dict) for JSON serialization at activity boundaries"
  - "Heartbeat-per-agent pattern: each agent execution sends a heartbeat to prevent timeout false-positives"
  - "Static gate logic: GateManager uses static methods (no instance state) -- workflow handles signal waiting"

requirements-completed: [PIPE-03, PIPE-05]

# Metrics
duration: 5min
completed: 2026-03-18
---

# Phase 6 Plan 02: Pipeline Data Layer and Activities Summary

**Temporal activity DTOs, PhaseRegistry, three @activity.defn activities with heartbeating, and GateManager for human approval gate logic**

## Performance

- **Duration:** 5min
- **Started:** 2026-03-18T20:05:28Z
- **Completed:** 2026-03-18T20:11:15Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments
- Four JSON-serializable dataclasses (PipelineInput, PhaseInput, PhaseResult, PipelineCheckpoint) for Temporal activity boundaries
- PhaseRegistry with manual registration and bulk-load from PhaseConfig objects
- Three Temporal activities with @activity.defn, heartbeating, and proper serialization
- GateManager with should_gate/build_gate_id/resolve_timeout static methods plus GateDecision dataclass
- 43 new unit tests (62 total pipeline tests), all passing
- ruff and mypy --strict clean on entire pipeline module

## Task Commits

Each task was committed atomically:

1. **Task 1: Pipeline DTOs and PhaseRegistry** - `63ace15` (feat)
2. **Task 2: Temporal activities** - `c65b821` (feat)
3. **Task 3: Human approval gates** - `0e998d3` (feat)

## Files Created/Modified
- `apps/server/src/codebot/pipeline/checkpoint.py` - PipelineInput, PhaseInput, PhaseResult, PipelineCheckpoint dataclasses
- `apps/server/src/codebot/pipeline/registry.py` - PhaseRegistry mapping phase names to agent lists
- `apps/server/src/codebot/pipeline/activities.py` - Three Temporal activities with heartbeating
- `apps/server/src/codebot/pipeline/gates.py` - GateManager and GateDecision for human approval logic
- `apps/server/src/codebot/pipeline/__init__.py` - Updated exports for new modules
- `apps/server/pyproject.toml` - Added temporalio>=1.23.0 dependency
- `tests/unit/pipeline/test_checkpoint.py` - 15 tests for DTOs
- `tests/unit/pipeline/test_registry.py` - 5 tests for PhaseRegistry
- `tests/unit/pipeline/test_activities.py` - 10 tests for activities
- `tests/unit/pipeline/test_gates.py` - 13 tests for GateManager/GateDecision

## Decisions Made
- **dataclasses with slots=True and kw_only=True**: Follows CLAUDE.md convention for all pipeline DTOs; ensures keyword-only construction prevents positional argument errors
- **Renamed input to phase_input**: ruff A002 flags `input` as Python builtin shadowing; renamed to `phase_input` for clarity
- **Static GateManager methods**: Gate logic is pure function of GateConfig -- no instance state needed; workflow (Plan 04) handles the actual Temporal signal waiting
- **PhaseRegistry copies agent lists**: Uses `list(phase.agents)` to decouple from frozen Pydantic model tuples

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ruff A002 builtin shadowing in execute_phase_activity**
- **Found during:** Task 3 (final ruff verification)
- **Issue:** Parameter named `input` shadows Python builtin
- **Fix:** Renamed to `phase_input` in function signature and all references
- **Files modified:** apps/server/src/codebot/pipeline/activities.py
- **Verification:** `uv run ruff check apps/server/src/codebot/pipeline/` -- All checks passed
- **Committed in:** 0e998d3 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Trivial rename for lint compliance. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- DTOs and activities are ready for SDLCPipelineWorkflow composition in Plan 04
- GateManager gate logic ready for Temporal signal integration in Plan 04
- NATS JetStream wiring for emit_pipeline_event deferred to Plan 03
- PhaseRegistry ready for pipeline config bootstrap

---
*Phase: 06-pipeline-orchestration*
*Completed: 2026-03-18*
