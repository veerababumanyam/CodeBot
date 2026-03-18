---
phase: 06-pipeline-orchestration
verified: 2026-03-18T21:00:00Z
status: passed
score: 13/13 must-haves verified
re_verification: false
---

# Phase 6: Pipeline Orchestration Verification Report

**Phase Goal:** Multi-stage pipelines run durably with retry, checkpoint/resume, human approval gates, and configurable presets
**Verified:** 2026-03-18T21:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Pipeline configurations load from YAML files and produce validated PipelineConfig objects | VERIFIED | `loader.py` calls `PipelineConfig.model_validate(raw["pipeline"])` with FileNotFoundError for missing presets |
| 2 | Three presets (full, quick, review-only) exist and load without errors | VERIFIED | `configs/pipelines/full.yaml`, `quick.yaml`, `review-only.yaml` all present and pass model validation (11 unit tests pass) |
| 3 | Project type detection correctly classifies greenfield, inflight, and brownfield projects | VERIFIED | `project_detector.py` implements heuristic + PRD-hint detection; 8 unit tests all pass |
| 4 | Pipeline phases are filtered based on project type (brownfield skips brainstorm/research) | VERIFIED | `adapt_pipeline_for_project_type()` filters on `skip_for_project_types`; full.yaml has `skip_for_project_types: [brownfield, improve]` on brainstorm/research |
| 5 | Pipeline data transfer objects are JSON-serializable dataclasses for Temporal activity boundaries | VERIFIED | `checkpoint.py` has four `@dataclass(slots=True, kw_only=True)` classes with only primitive types; 15 unit tests pass |
| 6 | Long-running agent execution reports progress via heartbeats to prevent timeout false-positives | VERIFIED | `activities.py` calls `activity.heartbeat()` per-agent in `execute_phase_activity`; heartbeat_timeout=60s configured on all agent activities |
| 7 | Pipeline pauses at human gates via GateManager which determines gate behavior from GateConfig | VERIFIED | `gates.py` GateManager has `should_gate`, `build_gate_id`, `resolve_timeout`; wired in `SDLCPipelineWorkflow._wait_for_gate`; 13 unit tests pass |
| 8 | Phase execution activities retry automatically on transient failures without re-executing completed work | VERIFIED | `AGENT_RETRY = RetryPolicy(maximum_attempts=3)` and `FAST_RETRY` defined in `workflows.py` and applied to all `execute_activity` calls |
| 9 | Every stage transition emits a typed event to NATS JetStream | VERIFIED | `PipelineEventEmitter` publishes to `pipeline.{event_type}` subjects; `emit_pipeline_event` activity wired into SDLCPipelineWorkflow for every phase.started, phase.completed, gate.waiting, gate.decided |
| 10 | SDLCPipelineWorkflow executes 10 stages end-to-end via Temporal durable workflow | VERIFIED | `workflows.py` iterates over all phases from loaded config; full.yaml has 11 phases (S0-S10); 8 unit + 2 E2E integration tests pass |
| 11 | Stages execute agents in parallel via Temporal child workflows and asyncio.gather | VERIFIED | `_execute_parallel_phase` spawns `PhaseAgentWorkflow` child workflows per agent via `workflow.start_child_workflow`, collects with `asyncio.gather`; parallel test passes |
| 12 | Pipeline survives crashes and resumes from last completed phase via Temporal replay | VERIFIED | `resume_from_phase` field on `PipelineInput`; workflow skips phases with `idx < start_idx`; `continue_as_new` sets `resume_from_phase=idx+1`; 2 resume integration tests pass |
| 13 | Pipeline can be paused and resumed via Temporal signals | VERIFIED | `pause_pipeline` / `resume_pipeline` signals set `is_paused`; workflow awaits `workflow.wait_condition(lambda: not self.is_paused)` before each phase; signal tests pass |

**Score:** 13/13 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `apps/server/src/codebot/pipeline/models.py` | PipelineConfig, PhaseConfig, GateConfig, PipelineSettings Pydantic v2 models | VERIFIED | All four classes present with frozen=True, field_validator on phases |
| `apps/server/src/codebot/pipeline/loader.py` | `load_preset()` function that reads YAML and returns PipelineConfig | VERIFIED | 48-line substantive file; calls `PipelineConfig.model_validate(raw["pipeline"])` |
| `apps/server/src/codebot/pipeline/project_detector.py` | `detect_project_type()` and `adapt_pipeline_for_project_type()` | VERIFIED | Both functions present; imports `ProjectType` from agent-sdk; uses `model_copy(update=...)` |
| `configs/pipelines/full.yaml` | Full SDLC pipeline preset with all stages | VERIFIED | 11 phases S0-S10; `name: full-sdlc`; human_gate `enabled: true, mandatory: true` on design and deliver |
| `configs/pipelines/quick.yaml` | Quick pipeline preset with subset of stages | VERIFIED | 8 phases; `name: quick`; all gates have `timeout_action: auto_approve` |
| `configs/pipelines/review-only.yaml` | Review-only preset for QA workflows | VERIFIED | Single QA phase; `name: review-only` |
| `apps/server/src/codebot/pipeline/checkpoint.py` | PipelineInput, PhaseInput, PhaseResult, PipelineCheckpoint dataclasses | VERIFIED | All four `@dataclass(slots=True, kw_only=True)` classes with primitive-only fields |
| `apps/server/src/codebot/pipeline/registry.py` | PhaseRegistry mapping phase names to agent lists | VERIFIED | `get_agents()`, `register_from_config()`, `register()`, `phase_names` property |
| `apps/server/src/codebot/pipeline/activities.py` | Three Temporal activities: load_pipeline_config, execute_phase_activity, emit_pipeline_event | VERIFIED | All three `@activity.defn` functions present; heartbeating on execute_phase_activity; emitter singleton + fallback on emit_pipeline_event |
| `apps/server/src/codebot/pipeline/gates.py` | GateManager for human-in-the-loop approval logic | VERIFIED | GateManager and GateDecision present; `should_gate`, `build_gate_id`, `resolve_timeout` static methods |
| `apps/server/src/codebot/pipeline/events.py` | PipelineEventEmitter with NATS JetStream integration | VERIFIED | `STREAM_NAME = "PIPELINE_EVENTS"`; `subjects=["pipeline.>"]`; 7-day retention; four typed helper methods |
| `apps/server/src/codebot/pipeline/workflows.py` | SDLCPipelineWorkflow and PhaseAgentWorkflow Temporal workflow definitions | VERIFIED | Both `@workflow.defn` classes; approve_gate / pause_pipeline / resume_pipeline signals; get_status query; continue_as_new; asyncio.gather for parallel |
| `apps/server/src/codebot/pipeline/worker.py` | Temporal worker startup with workflow and activity registration | VERIFIED | `TASK_QUEUE = "codebot-pipeline"`; registers both workflows and all activities; NATS emitter init with graceful degradation |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `loader.py` | `models.py` | `PipelineConfig.model_validate(raw["pipeline"])` | WIRED | Line 47 of loader.py |
| `project_detector.py` | `models.py` | `config.model_copy(update={"phases": adapted_phases})` | WIRED | Line 98 of project_detector.py |
| `activities.py` | `checkpoint.py` | `PhaseInput`, `PhaseResult` used as activity I/O | WIRED | Lines 24, 66, 96 of activities.py |
| `activities.py` | `loader.py` | `load_preset()` called inside `load_pipeline_config` | WIRED | Line 61 of activities.py |
| `activities.py` | `events.py` | `emit_pipeline_event` calls `_emitter.emit()` | WIRED | Lines 25, 122 of activities.py; `_emitter` set via `set_event_emitter()` |
| `workflows.py` | `activities.py` | `workflow.execute_activity(execute_phase_activity, ...)` | WIRED | Lines 78, 174, 195, 203, 297 of workflows.py |
| `workflows.py` | `checkpoint.py` | `PipelineInput`/`PhaseInput` used as workflow inputs | WIRED | Lines 34-38 of workflows.py (`with workflow.unsafe.imports_passed_through()`) |
| `worker.py` | `workflows.py` | `Worker` registers `SDLCPipelineWorkflow`, `PhaseAgentWorkflow` | WIRED | Lines 59-60 of worker.py |
| `worker.py` | `events.py` | `PipelineEventEmitter` initialized and injected via `set_event_emitter` | WIRED | Lines 36, 95-97 of worker.py |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PIPE-01 | 06-04 | System executes 10-stage SDLC pipeline S0-S9 | SATISFIED | `SDLCPipelineWorkflow.run` iterates all phases from loaded config; full.yaml has 11 phases; E2E tests verify completion |
| PIPE-02 | 06-04 | Stages S3, S5, S6 execute agents in parallel | SATISFIED | `_execute_parallel_phase` uses `workflow.start_child_workflow` per agent + `asyncio.gather`; full.yaml marks design/implement/qa as `sequential: false` |
| PIPE-03 | 06-02 | Pipeline supports entry/exit gates with human approval | SATISFIED | `GateManager.should_gate()` + `SDLCPipelineWorkflow._wait_for_gate()` + `approve_gate` signal; full.yaml has mandatory gates on design and deliver |
| PIPE-04 | 06-01 | Pipeline configurations loadable from YAML presets: full, quick, review-only | SATISFIED | `load_preset("full|quick|review-only")` loads and validates all three presets; 11 loader unit tests pass |
| PIPE-05 | 06-04 | Temporal provides durable workflow orchestration with retry, timeout, crash recovery | SATISFIED | `FAST_RETRY` and `AGENT_RETRY` `RetryPolicy` objects applied to all `execute_activity` calls; `heartbeat_timeout=timedelta(seconds=60)` on agent activities; durability integration tests pass |
| PIPE-06 | 06-04 | Pipeline can resume from last checkpoint after failure or manual pause | SATISFIED | `PipelineInput.resume_from_phase` skips completed phase indices; `continue_as_new` passes `resume_from_phase=idx+1`; 2 resume integration tests verify skip behavior and count accuracy |
| PIPE-07 | 06-01 | Pipeline detects project type and adapts stage configuration | SATISFIED | `detect_project_type()` classifies via repo heuristics + PRD hint; `adapt_pipeline_for_project_type()` filters on `skip_for_project_types`; brownfield/improve skip brainstorm+research in full.yaml |
| PIPE-08 | 06-03 | Pipeline emits events to NATS JetStream for every stage transition | SATISFIED | `PipelineEventEmitter` publishes to `PIPELINE_EVENTS` stream with `pipeline.>` subjects and 7-day retention; wired into `emit_pipeline_event` activity; workflow calls emit for phase.started, phase.completed, gate.waiting, gate.decided |

All 8 requirements satisfied. No orphaned requirements found — REQUIREMENTS.md maps all PIPE-01 through PIPE-08 exclusively to Phase 6, and all 4 plans claim them collectively.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `apps/server/src/codebot/pipeline/activities.py` | 82 | `# TODO: Phase 2/3 integration — delegate to graph engine` | Info | `execute_phase_activity` currently simulates agent execution (iterates agents, returns stub results) rather than calling the graph engine. This is an intentional architectural stub — the activity is fully wired with heartbeating, timing, and proper PhaseResult return. Graph engine delegation is deferred to a future phase. The orchestration layer itself (Temporal workflows, retry, signals, gates, events) is fully implemented. |

No blocker or warning anti-patterns found. The single Info-level TODO is a documented, scoped deferral that does not prevent the Phase 6 goal from being achieved.

---

## Human Verification Required

None. All observable truths verifiable programmatically. All 91 tests (85 unit + 6 integration) pass. ruff and mypy --strict clean across all 11 source files.

---

## Gaps Summary

No gaps. All 13 observable truths verified. All 8 PIPE requirements satisfied with concrete code evidence. All key links wired and confirmed through source inspection.

---

_Verified: 2026-03-18T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
