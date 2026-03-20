---
phase: 07-vertical-slice
plan: 01
subsystem: input-processing
tags: [pydantic, instructor, litellm, requirement-extraction, nlp, agents]

# Dependency graph
requires:
  - phase: 03-agent-framework
    provides: BaseAgent, AgentInput, AgentOutput, PRAResult, AgentType enums
provides:
  - ExtractedRequirements, FunctionalRequirement, AcceptanceCriterion Pydantic models
  - RequirementExtractor using instructor + LiteLLM for structured extraction
  - ClarificationLoop for ambiguity and low-confidence detection
  - OrchestratorAgent implementing PRA cycle for requirement extraction
  - YAML agent config at configs/agents/orchestrator.yaml
affects: [07-vertical-slice, input-processing, pipeline-composition]

# Tech tracking
tech-stack:
  added: [instructor 1.14.5]
  patterns: [instructor.from_litellm for structured LLM output, ClarificationLoop dataclass pattern, PRA cycle concrete implementation]

key-files:
  created:
    - apps/server/src/codebot/input/models.py
    - apps/server/src/codebot/input/extractor.py
    - apps/server/src/codebot/input/clarifier.py
    - apps/server/src/codebot/agents/orchestrator.py
    - tests/unit/input/test_extractor.py
    - tests/unit/input/test_clarifier.py
    - tests/unit/agents/test_orchestrator.py
  modified:
    - tests/conftest.py
    - configs/agents/orchestrator.yaml

key-decisions:
  - "instructor.from_litellm(litellm.acompletion) for async structured output -- matches research Pattern 2"
  - "ClarificationLoop as dataclass (not Pydantic) following CLAUDE.md slots=True kw_only=True convention"
  - "OrchestratorAgent logs ambiguities but proceeds with best-effort in vertical slice -- full HITL deferred to Phase 9"
  - "Updated orchestrator.yaml to vertical-slice config format (agent.type/model) from Phase 3 format"

patterns-established:
  - "Concrete BaseAgent subclass with PRA cycle: perceive->reason->act->review, each returning typed dicts"
  - "instructor + LiteLLM pattern for structured Pydantic extraction from LLM"
  - "ClarificationLoop triple-check: low_confidence + ambiguity + missing_criteria"
  - "mock_instructor_client fixture pattern for testing LLM-dependent code"

requirements-completed: [INPT-01, INPT-02, INPT-04, INPT-05]

# Metrics
duration: 6min
completed: 2026-03-20
---

# Phase 07 Plan 01: Input Processing and Orchestrator Summary

**Pydantic requirement extraction models with instructor+LiteLLM extractor, clarification loop, and OrchestratorAgent PRA cycle**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-20T05:33:57Z
- **Completed:** 2026-03-20T05:40:19Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- ExtractedRequirements, FunctionalRequirement, AcceptanceCriterion Pydantic v2 models with confidence validation (0.0-1.0)
- RequirementExtractor using instructor + LiteLLM async for structured NLP extraction with format detection (natural language, JSON, YAML, Markdown)
- ClarificationLoop detecting low-confidence requirements, explicit ambiguities, and missing acceptance criteria
- OrchestratorAgent extending BaseAgent with full PRA cognitive cycle
- 31 unit tests passing with mocked LLM calls

## Task Commits

Each task was committed atomically:

1. **Task 1: Input domain models and RequirementExtractor** - `53663f0` (test), `1f0e356` (feat)
2. **Task 2: ClarificationLoop and OrchestratorAgent** - `b90a403` (test), `1b9d4e6` (feat)

_TDD tasks have separate test (RED) and implementation (GREEN) commits._

## Files Created/Modified
- `apps/server/src/codebot/input/__init__.py` - Input domain package init
- `apps/server/src/codebot/input/models.py` - ExtractedRequirements, FunctionalRequirement, AcceptanceCriterion Pydantic models
- `apps/server/src/codebot/input/extractor.py` - RequirementExtractor with instructor+LiteLLM and format detection
- `apps/server/src/codebot/input/clarifier.py` - ClarificationLoop and ClarificationItem dataclasses
- `apps/server/src/codebot/agents/orchestrator.py` - OrchestratorAgent with PRA cycle and SYSTEM_PROMPT
- `configs/agents/orchestrator.yaml` - Orchestrator agent YAML config (vertical-slice format)
- `tests/conftest.py` - Added mock_extracted_requirements shared fixture
- `tests/unit/__init__.py` - Test package init
- `tests/unit/input/__init__.py` - Input test package init
- `tests/unit/input/test_extractor.py` - 16 tests for models and extractor
- `tests/unit/input/test_clarifier.py` - 8 tests for clarification loop
- `tests/unit/agents/__init__.py` - Agent test package init
- `tests/unit/agents/test_orchestrator.py` - 7 tests for orchestrator agent

## Decisions Made
- Used `instructor.from_litellm(litellm.acompletion)` for async structured output (matches research Pattern 2)
- ClarificationLoop as dataclass with `slots=True, kw_only=True` per CLAUDE.md convention (not Pydantic since it has mutable state)
- OrchestratorAgent logs ambiguities but proceeds in vertical slice -- full human-in-the-loop clarification deferred to Phase 9
- Updated `configs/agents/orchestrator.yaml` from Phase 3's flat format to the plan's `agent:` nested format

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Input domain models ready for downstream agents (BackendDev, CodeReviewer, Tester, Debugger)
- OrchestratorAgent can be composed into pipeline graph for Plan 07-04
- RequirementExtractor pattern established for other instructor+LiteLLM uses in Plans 07-02/03

## Self-Check: PASSED

All 10 files verified present. All 4 commits verified in git log.

---
*Phase: 07-vertical-slice*
*Completed: 2026-03-20*
