---
phase: 06-pipeline-orchestration
plan: 01
subsystem: pipeline
tags: [pydantic-v2, yaml, pipeline-config, project-detection, presets]

requires:
  - phase: 01-foundation
    provides: "Monorepo structure, pyproject.toml, agent-sdk with enums"
  - phase: 03-agent-framework
    provides: "agent-sdk models including ProjectType enum"
provides:
  - "PipelineConfig, PhaseConfig, GateConfig, PipelineSettings Pydantic v2 models"
  - "load_preset() YAML preset loader for full/quick/review-only"
  - "detect_project_type() greenfield/inflight/brownfield classifier"
  - "adapt_pipeline_for_project_type() phase filtering by project type"
  - "Three YAML pipeline presets: full.yaml, quick.yaml, review-only.yaml"
affects: [06-02, 06-03, 06-04, pipeline-workflows, temporal-activities]

tech-stack:
  added: []
  patterns:
    - "Frozen Pydantic v2 models with ConfigDict(frozen=True) for immutable config"
    - "YAML preset -> model_validate pipeline for typed config loading"
    - "skip_for_project_types field for adaptive phase filtering"
    - "Computed property (parallel) on frozen Pydantic model"

key-files:
  created:
    - apps/server/src/codebot/pipeline/__init__.py
    - apps/server/src/codebot/pipeline/models.py
    - apps/server/src/codebot/pipeline/loader.py
    - apps/server/src/codebot/pipeline/project_detector.py
    - configs/pipelines/full.yaml
    - configs/pipelines/quick.yaml
    - configs/pipelines/review-only.yaml
    - tests/unit/pipeline/test_preset_loader.py
    - tests/unit/pipeline/test_project_detector.py
    - tests/unit/__init__.py
    - tests/unit/pipeline/__init__.py
  modified: []

key-decisions:
  - "frozen=True ConfigDict on all pipeline config models for immutability"
  - "full.yaml has 11 phases (S0-S10) with human gates on design and deliver"
  - "Brownfield/improve project types skip brainstorm and research phases"
  - "Source file count threshold of 50 distinguishes inflight from brownfield"
  - "PRD content project_type hint overrides heuristic detection"

patterns-established:
  - "YAML preset loading: yaml.safe_load -> PipelineConfig.model_validate(raw['pipeline'])"
  - "Phase filtering: skip_for_project_types list on PhaseConfig controls adaptive pipelines"
  - "Config directory resolution: Path(__file__).resolve().parents[N] for repo-relative paths"

requirements-completed: [PIPE-04, PIPE-07]

duration: 5min
completed: 2026-03-18
---

# Phase 6 Plan 01: Pipeline Config Models & Preset Loader Summary

**Pydantic v2 pipeline config models with YAML preset loader (full/quick/review-only) and project type detection for adaptive phase filtering**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-18T19:57:01Z
- **Completed:** 2026-03-18T20:02:02Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 11

## Accomplishments
- Pipeline configuration data layer with 4 Pydantic v2 models (PipelineConfig, PhaseConfig, GateConfig, PipelineSettings)
- YAML preset loader supporting full (11-stage), quick (8-stage), and review-only (1-stage) presets
- Project type detector classifying greenfield/inflight/brownfield with adaptive pipeline filtering
- 19 unit tests all passing, ruff clean, mypy strict clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Pipeline config models and YAML preset loader**
   - `153edec` (test: add failing tests for pipeline config models and preset loader)
   - `f13c2dd` (feat: implement pipeline config models and YAML preset loader)
2. **Task 2: Project type detector and adaptive pipeline filtering**
   - `b7b2a23` (test: add failing tests for project type detector and pipeline adaptation)
   - `bf0817d` (feat: implement project type detector and adaptive pipeline filtering)

_Note: TDD tasks have two commits each (RED test -> GREEN implementation)_

## Files Created/Modified
- `apps/server/src/codebot/pipeline/__init__.py` - Package exports for all pipeline config public API
- `apps/server/src/codebot/pipeline/models.py` - PipelineConfig, PhaseConfig, GateConfig, PipelineSettings Pydantic v2 models
- `apps/server/src/codebot/pipeline/loader.py` - load_preset() reads YAML and validates through PipelineConfig.model_validate
- `apps/server/src/codebot/pipeline/project_detector.py` - detect_project_type() and adapt_pipeline_for_project_type()
- `configs/pipelines/full.yaml` - Full SDLC pipeline (11 phases, S0-S10, human gates on design/deliver)
- `configs/pipelines/quick.yaml` - Quick pipeline (8 phases, auto-approve gates, lower cost limit)
- `configs/pipelines/review-only.yaml` - Review-only pipeline (QA phase only)
- `tests/unit/pipeline/test_preset_loader.py` - 11 tests for models and loader
- `tests/unit/pipeline/test_project_detector.py` - 8 tests for detector and adaptation
- `tests/unit/__init__.py` - Test package init
- `tests/unit/pipeline/__init__.py` - Test package init

## Decisions Made
- **frozen=True on all config models**: Pipeline configs are immutable after loading. Use model_copy(update=...) for modifications (e.g., phase filtering). Consistent with Phase 4 pattern.
- **11 phases in full.yaml**: S0 initialize through S10 deliver, matching SYSTEM_DESIGN.md Section 6.2.
- **Brownfield/improve skip brainstorm+research**: These phases are unnecessary for existing codebases. Controlled via skip_for_project_types field on PhaseConfig.
- **Source file count threshold = 50**: Heuristic to distinguish inflight (1-50 files) from brownfield (>50 files). Simple but effective for v1.
- **PRD hint override**: Explicit project_type annotation in PRD content takes precedence over file-count heuristics.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Pipeline config models are ready for Temporal workflow integration (Plan 06-02)
- load_preset() provides typed config for workflow initialization
- adapt_pipeline_for_project_type() ready for use in pipeline startup activity
- All downstream plans (06-02 workflows, 06-03 gates, 06-04 events) can import from codebot.pipeline

## Self-Check: PASSED

All 11 created files verified present. All 4 task commits verified in git history.

---
*Phase: 06-pipeline-orchestration*
*Completed: 2026-03-18*
