---
phase: 07-vertical-slice
plan: 03
subsystem: testing-debugging
tags: [tester, debugger, experiment-loop, pytest, json-report, coverage, root-cause-analysis, fix-generation, circuit-breaker]

# Dependency graph
requires:
  - phase: 03-agent-framework
    provides: "BaseAgent, AgentInput, AgentOutput, PRAResult abstract base classes"
  - phase: 04-multi-llm
    provides: "LiteLLM abstraction for provider-agnostic LLM calls"
  - phase: 07-01
    provides: "OrchestratorAgent, ExtractedRequirements models"
  - phase: 07-02
    provides: "BackendDevAgent, CodeReviewerAgent, GeneratedFile models, SharedState keys"
provides:
  - "TesterAgent with test generation and execution via TestRunner + TestResultParser"
  - "DebuggerAgent with root cause analysis and iterative fix loop"
  - "ExperimentLoopController with 4 circuit breakers and KEEP/DISCARD semantics"
  - "FailureAnalyzer for LLM-powered root cause identification"
  - "FixGenerator for targeted code patch generation and application"
  - "ParsedTestResult and TestGenerationPlan structured output models"
  - "YAML configs for tester and debugger agents"
affects: [07-vertical-slice, 08-agent-roster, pipeline-graph, pipeline-composition]

# Tech tracking
tech-stack:
  added: []
  patterns: [experiment-loop-keep-discard, circuit-breaker-pattern, pytest-json-report-parsing, async-subprocess-test-execution]

key-files:
  created:
    - apps/server/src/codebot/agents/tester.py
    - apps/server/src/codebot/agents/debugger.py
    - apps/server/src/codebot/testing/__init__.py
    - apps/server/src/codebot/testing/runner.py
    - apps/server/src/codebot/testing/parser.py
    - apps/server/src/codebot/debug/__init__.py
    - apps/server/src/codebot/debug/analyzer.py
    - apps/server/src/codebot/debug/fixer.py
    - apps/server/src/codebot/debug/loop_controller.py
    - configs/agents/tester.yaml
    - configs/agents/debugger.yaml
    - tests/unit/agents/test_tester.py
    - tests/unit/agents/test_debugger.py
    - tests/unit/debug/__init__.py
    - tests/unit/debug/test_analyzer.py
    - tests/unit/debug/test_fixer.py
    - tests/unit/debug/test_loop_controller.py
  modified: []

key-decisions:
  - "instructor.from_litellm(litellm.completion) for sync structured output (consistent with BackendDevAgent/CodeReviewerAgent pattern)"
  - "ExperimentLoopController as dataclass with 4 circuit breakers: all-pass, max-experiments, time-budget, no-improvement-streak"
  - "KEEP/DISCARD semantics: delta > improvement_threshold (0.01) for KEEP, otherwise DISCARD"
  - "tempfile.gettempdir() as fallback workspace path (avoids ruff S108 hardcoded temp path warning)"
  - "DebuggerAgent reverts source_files dict on DISCARD to prevent cascading breakage"

patterns-established:
  - "ExperimentLoop pattern: baseline comparison with KEEP/DISCARD for iterative fix attempts"
  - "Circuit breaker pattern: 4 independent termination conditions preventing infinite loops"
  - "TestRunner+TestResultParser separation: execution and parsing are distinct concerns"
  - "Failure routing via SharedState: TesterAgent sets test_failures key for DebuggerAgent to consume"

requirements-completed: [TEST-01, TEST-02, TEST-05, DBUG-01, DBUG-02, DBUG-03]

# Metrics
duration: 8min
completed: 2026-03-20
---

# Phase 07 Plan 03: Tester and Debugger Agents Summary

**TesterAgent generates/executes pytest tests with JSON report parsing; DebuggerAgent performs LLM root cause analysis with ExperimentLoop KEEP/DISCARD semantics and 4 circuit breakers**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-20T05:46:17Z
- **Completed:** 2026-03-20T05:54:17Z
- **Tasks:** 2
- **Files modified:** 17

## Accomplishments
- TesterAgent generates unit tests (80% coverage target) and integration tests (httpx.AsyncClient) via instructor+LiteLLM structured output, executes via TestRunner with pytest-json-report, parses with TestResultParser
- DebuggerAgent performs LLM-powered root cause analysis via FailureAnalyzer, generates targeted fixes via FixGenerator, manages iterative fix cycle with ExperimentLoopController
- ExperimentLoopController implements 4 circuit breakers (all tests pass, max experiments, time budget, no-improvement streak) with KEEP/DISCARD semantics comparing against stable baseline
- Failed test results are structured and routable via SharedState (test_failures key) from TesterAgent to DebuggerAgent
- 42 unit tests passing across all new modules with mocked LLM and subprocess calls

## Task Commits

Each task was committed atomically:

1. **Task 1: TesterAgent with TestRunner and TestResultParser** - `b51f49c` (test: RED), `c105634` (feat: GREEN)
2. **Task 2: DebuggerAgent with FailureAnalyzer, FixGenerator, ExperimentLoopController** - `8a593f4` (test: RED), `d5c349d` (feat: GREEN)

_TDD tasks each have separate test (RED) and implementation (GREEN) commits._

## Files Created/Modified
- `apps/server/src/codebot/testing/__init__.py` - Testing package init
- `apps/server/src/codebot/testing/parser.py` - ParsedTestResult dataclass and TestResultParser extracting pass/fail/coverage from pytest-json-report
- `apps/server/src/codebot/testing/runner.py` - TestRunner executing pytest via asyncio.create_subprocess_exec with JSON report and coverage flags
- `apps/server/src/codebot/agents/tester.py` - TesterAgent PRA cycle with GeneratedTest/TestGenerationPlan Pydantic models, SYSTEM_PROMPT with anti-flakiness guidelines
- `apps/server/src/codebot/debug/__init__.py` - Debug package init
- `apps/server/src/codebot/debug/analyzer.py` - FailureAnalysis Pydantic model and FailureAnalyzer using instructor+LiteLLM for root cause identification
- `apps/server/src/codebot/debug/fixer.py` - FixProposal Pydantic model and FixGenerator for targeted patch generation and application
- `apps/server/src/codebot/debug/loop_controller.py` - ExperimentResult dataclass and ExperimentLoopController with 4 circuit breakers and KEEP/DISCARD semantics
- `apps/server/src/codebot/agents/debugger.py` - DebuggerAgent PRA cycle integrating analyzer, fixer, loop controller, and test runner; SYSTEM_PROMPT for senior debugger role
- `configs/agents/tester.yaml` - Tester agent YAML config (coverage_target: 80, run_twice_on_failure: true)
- `configs/agents/debugger.yaml` - Debugger agent YAML config (max_experiments: 5, time_budget: 600s, improvement_threshold: 0.01)
- `tests/unit/agents/test_tester.py` - 17 tests: ParsedTestResult model, parser extraction, runner subprocess, TesterAgent PRA cycle
- `tests/unit/agents/test_debugger.py` - 7 tests: DebuggerAgent type, perceive, reason, act experiment loop, review
- `tests/unit/debug/__init__.py` - Debug test package init
- `tests/unit/debug/test_analyzer.py` - 3 tests: FailureAnalysis model, root cause analysis, affected files
- `tests/unit/debug/test_fixer.py` - 4 tests: FixProposal model, fix generation, multiple fixes, file writing
- `tests/unit/debug/test_loop_controller.py` - 11 tests: all circuit breakers, KEEP/DISCARD logic, experiment recording

## Decisions Made
- Used `instructor.from_litellm(litellm.completion)` for sync structured output -- consistent with BackendDevAgent and CodeReviewerAgent patterns from Plan 07-02
- ExperimentLoopController uses dataclass with `slots=True, kw_only=True` per CLAUDE.md convention, with 4 independent circuit breakers
- KEEP/DISCARD threshold set at `delta > 0.01` (improvement_threshold) -- each fix compared against baseline, not previous attempt
- Used `tempfile.gettempdir()` as fallback workspace path instead of hardcoded `/tmp/` path to satisfy ruff S108
- DebuggerAgent reverts `source_files` dict on DISCARD to pre-fix state, preventing cascading breakage per research Pitfall 3

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed async/sync mismatch in TesterAgent.reason()**
- **Found during:** Task 1 (TesterAgent implementation)
- **Issue:** Plan specified `litellm.acompletion` (async) for TesterAgent.reason(), but test mocks returned sync values causing `TypeError: object can't be used in 'await' expression`
- **Fix:** Changed to `litellm.completion` (sync) matching the established pattern from BackendDevAgent and CodeReviewerAgent
- **Files modified:** apps/server/src/codebot/agents/tester.py
- **Verification:** All 17 tests pass
- **Committed in:** c105634 (part of Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug in async/sync pattern)
**Impact on plan:** Minor consistency fix to match established sync instructor+LiteLLM pattern. No scope creep.

## Issues Encountered
None -- both tasks executed cleanly after the async/sync pattern adjustment.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 5 vertical slice agents complete (Orchestrator, BackendDev, CodeReviewer, Tester, Debugger)
- Agents communicate via SharedState keys (backend_dev.generated_files -> test_results -> test_failures)
- ExperimentLoopController pattern validated with circuit breakers
- Ready for pipeline graph composition in Plan 07-04 (vertical-slice pipeline wiring)

## Self-Check: PASSED

All 17 files verified present. All 4 commits verified in git log. 42/42 tests pass.

---
*Phase: 07-vertical-slice*
*Completed: 2026-03-20*
