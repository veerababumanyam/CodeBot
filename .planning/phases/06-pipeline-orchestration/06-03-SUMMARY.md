---
phase: 06-pipeline-orchestration
plan: 03
subsystem: pipeline
tags: [nats, jetstream, events, observability, temporal-activities]

# Dependency graph
requires:
  - phase: 06-pipeline-orchestration-02
    provides: "Temporal activities shell with emit_pipeline_event placeholder"
provides:
  - "PipelineEventEmitter class publishing typed events to NATS JetStream"
  - "PipelineEvent dataclass with JSON serialization and NATS subject formatting"
  - "Module-level singleton pattern for NATS connection reuse in Temporal activities"
  - "Graceful degradation to logging when NATS unavailable"
affects: [06-pipeline-orchestration-04, dashboard, cli, audit-trail]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Module-level singleton for shared NATS connection in Temporal activities", "Graceful degradation pattern: try emitter then fall back to logging"]

key-files:
  created:
    - apps/server/src/codebot/pipeline/events.py
    - tests/unit/pipeline/test_event_emission.py
  modified:
    - apps/server/src/codebot/pipeline/activities.py
    - apps/server/src/codebot/pipeline/__init__.py
    - tests/unit/pipeline/test_activities.py

key-decisions:
  - "NATSClient import from nats.aio.client.Client for mypy strict compatibility (nats.NATS alias not resolved by mypy)"
  - "RetentionPolicy.LIMITS enum instead of string 'limits' for type safety in StreamConfig"
  - "max_age as seconds float (7*24*3600.0) -- nats-py internally converts to nanoseconds"
  - "Module-level logger for fallback path instead of activity.logger for separation of concerns"

patterns-established:
  - "PipelineEventEmitter singleton: set_event_emitter() at worker startup, reuse across activity calls"
  - "Event subject format: pipeline.{type_with_dots_as_underscores}"

requirements-completed: [PIPE-08]

# Metrics
duration: 5min
completed: 2026-03-18
---

# Phase 6 Plan 3: NATS JetStream Event Emission Summary

**PipelineEventEmitter with NATS JetStream publishing, typed event helpers, and graceful fallback in Temporal activities**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-18T20:14:14Z
- **Completed:** 2026-03-18T20:19:26Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- PipelineEventEmitter publishes typed events to NATS JetStream PIPELINE_EVENTS stream with 7-day retention
- Typed helper methods for all pipeline lifecycle events (phase started/completed, gate waiting/decided)
- emit_pipeline_event Temporal activity wired to emitter with graceful degradation to logging
- 15 unit tests covering event format, subject naming, stream configuration, and all helpers

## Task Commits

Each task was committed atomically:

1. **Task 1: PipelineEventEmitter with NATS JetStream and typed events** - `b25b198` (test: RED) + `8017d4a` (feat: GREEN)
2. **Task 2: Wire PipelineEventEmitter into emit_pipeline_event activity** - `bf8810d` (feat)

_Note: Task 1 used TDD with RED/GREEN commits._

## Files Created/Modified
- `apps/server/src/codebot/pipeline/events.py` - PipelineEvent dataclass and PipelineEventEmitter with JetStream integration
- `apps/server/src/codebot/pipeline/activities.py` - Wired emit_pipeline_event to use PipelineEventEmitter singleton with fallback
- `apps/server/src/codebot/pipeline/__init__.py` - Added PipelineEvent and PipelineEventEmitter to public API
- `tests/unit/pipeline/test_event_emission.py` - 15 unit tests for event emission (all pass)
- `tests/unit/pipeline/test_activities.py` - Updated test_logs_event to match new fallback logging path

## Decisions Made
- Used `nats.aio.client.Client` import (aliased as NATSClient) instead of `nats.NATS` for mypy strict compatibility
- Used `RetentionPolicy.LIMITS` enum instead of string literal for type safety
- max_age specified as seconds float (7*24*3600.0) since nats-py converts internally to nanoseconds
- Module-level `logger` for fallback path instead of `activity.logger` for cleaner separation of concerns

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing test_logs_event to match new logging path**
- **Found during:** Task 2
- **Issue:** Existing test in test_activities.py expected `activity.logger.info` but the refactored code uses module-level `logger.info` for fallback
- **Fix:** Updated test to patch `codebot.pipeline.activities.logger` and explicitly set `_emitter = None`
- **Files modified:** tests/unit/pipeline/test_activities.py
- **Verification:** All 10 activity tests pass
- **Committed in:** bf8810d (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary to maintain test suite integrity after changing the logging implementation.

## Issues Encountered
- Pre-existing test failure in test_parallel_phases.py (SDLCPipelineWorkflow sandbox validation error) -- confirmed unrelated to this plan's changes, from Plan 06-04 RED phase tests. Not addressed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- NATS JetStream event emission layer complete and ready for consumption by dashboard, CLI, and audit trail
- Worker startup code in Plan 04 can use set_event_emitter() to inject the shared emitter
- All pipeline lifecycle events have typed helper methods

## Self-Check: PASSED

All 6 files verified present. All 3 commits (b25b198, 8017d4a, bf8810d) verified in git log.

---
*Phase: 06-pipeline-orchestration*
*Completed: 2026-03-18*
