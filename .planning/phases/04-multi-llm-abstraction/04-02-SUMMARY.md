---
phase: 04-multi-llm-abstraction
plan: 02
subsystem: llm
tags: [litellm, budget, cost-tracking, fallback, streaming, callbacks, facade]

# Dependency graph
requires:
  - phase: 04-multi-llm-abstraction
    plan: 01
    provides: "TaskType enum, LLMRequest/LLMResponse schemas, LLMConfig YAML loader, ProviderRegistry, TaskBasedModelRouter, exceptions"
  - phase: 01-foundation
    provides: "EventBus, Settings, EventType enum"
provides:
  - "LLMService facade with complete() and stream() methods"
  - "CostTracker with per-agent/model/stage cost recording and budget enforcement"
  - "CostEstimator for pre-execution upper-bound cost predictions"
  - "CodeBotLLMLogger LiteLLM callback for automatic cost tracking and NATS event emission"
  - "FallbackChainManager wrapping LiteLLM Router with deduplicated fallback chains"
  - "get_llm_service() singleton factory for application-wide access"
  - "Complete public API exports from codebot.llm package"
affects: [06-pipeline-orchestration, 08-security-pipeline-worktree-manager]

# Tech tracking
tech-stack:
  added: [types-pyyaml]
  patterns: [asyncio.Lock for concurrent cost tracking, LiteLLM CustomLogger callbacks, singleton factory pattern, async generator streaming]

key-files:
  created:
    - apps/server/src/codebot/llm/budget.py
    - apps/server/src/codebot/llm/estimator.py
    - apps/server/src/codebot/llm/callbacks.py
    - apps/server/src/codebot/llm/fallback.py
    - apps/server/src/codebot/llm/service.py
    - apps/server/tests/unit/llm/test_budget.py
    - apps/server/tests/unit/llm/test_estimator.py
    - apps/server/tests/unit/llm/test_fallback.py
    - apps/server/tests/unit/llm/test_service.py
  modified:
    - apps/server/src/codebot/llm/__init__.py
    - apps/server/tests/unit/llm/conftest.py
    - apps/server/pyproject.toml

key-decisions:
  - "asyncio.Lock in CostTracker for concurrent agent cost recording safety"
  - "LiteLLM Router stream returns async generator directly (not coroutine) -- handle both patterns"
  - "litellm.Router typed as Any due to missing py.typed in litellm package"
  - "Conservative fallback pricing ($0.01/1k input, $0.03/1k output) for unknown models"
  - "Budget warning at 80%, halt at 95% -- configurable via BudgetConfig YAML"
  - "Deduplicated fallback mappings when same primary model appears in multiple task types"

patterns-established:
  - "LiteLLM CustomLogger callback pattern for transparent cost tracking"
  - "Budget check before every LLM call via CostTracker.check_budget()"
  - "Singleton factory pattern (get_llm_service) for application-wide LLM access"
  - "TDD red-green-refactor with separate commits per phase"

requirements-completed: [LLM-01, LLM-03, LLM-04, LLM-05, LLM-07, LLM-08]

# Metrics
duration: 12min
completed: 2026-03-18
---

# Phase 4 Plan 02: LLM Service Runtime Summary

**LLMService facade with complete/stream, CostTracker budget enforcement, LiteLLM callbacks for automatic cost tracking, and fallback chain management**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-18T18:43:22Z
- **Completed:** 2026-03-18T18:56:15Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments
- LLMService facade providing complete() and stream() for all agent LLM calls
- CostTracker with asyncio.Lock-protected per-agent/model/stage cost accumulation and budget enforcement (warn at 80%, halt at 95%)
- CodeBotLLMLogger extending LiteLLM CustomLogger for automatic cost recording and NATS event emission (LLM_USAGE, BUDGET_WARNING, BUDGET_EXCEEDED)
- FallbackChainManager building LiteLLM Router with deduplicated fallback chains from YAML config
- CostEstimator providing upper-bound USD estimates using LiteLLM model_cost with hardcoded fallbacks
- Full public API exports from codebot.llm package (10 symbols in __all__)
- 148 total LLM tests passing (95 from Plan 01 + 53 new), mypy strict clean

## Task Commits

Each task was committed atomically (TDD red-green pattern):

1. **Task 1: CostTracker and CostEstimator** - `e4d904a` (test), `fd239b0` (feat)
2. **Task 2: CodeBotLLMLogger and FallbackChainManager** - `7b83e39` (test), `6fed79a` (feat)
3. **Task 3: LLMService facade and public API** - `a56f5d1` (test), `802879d` (feat)

_Note: TDD tasks have separate test and feat commits per red-green cycle._

## Files Created/Modified
- `apps/server/src/codebot/llm/budget.py` - CostTracker with record/warn/halt/check_budget, CostRecord model
- `apps/server/src/codebot/llm/estimator.py` - CostEstimator with LiteLLM pricing lookup and pipeline estimation
- `apps/server/src/codebot/llm/callbacks.py` - CodeBotLLMLogger extending LiteLLM CustomLogger for cost/event tracking
- `apps/server/src/codebot/llm/fallback.py` - FallbackChainManager building LiteLLM Router with fallback chains
- `apps/server/src/codebot/llm/service.py` - LLMService facade with complete(), stream(), from_config(), get_llm_service()
- `apps/server/src/codebot/llm/__init__.py` - Updated with full public API exports (10 symbols)
- `apps/server/tests/unit/llm/conftest.py` - Added sample_llm_config, sample_provider_registry, mock_event_bus fixtures
- `apps/server/tests/unit/llm/test_budget.py` - 15 tests for CostTracker
- `apps/server/tests/unit/llm/test_estimator.py` - 8 tests for CostEstimator
- `apps/server/tests/unit/llm/test_fallback.py` - 12 tests for callbacks and fallback
- `apps/server/tests/unit/llm/test_service.py` - 18 tests for LLMService
- `apps/server/pyproject.toml` - Added types-pyyaml dev dependency

## Decisions Made
- asyncio.Lock in CostTracker protects concurrent cost recording from multiple agents
- LiteLLM Router streaming returns async generators directly -- service handles both awaitable and generator patterns
- litellm.Router typed as Any with targeted type: ignore due to missing py.typed in litellm
- Conservative fallback pricing ($0.01/1k input, $0.03/1k output) for unknown models ensures overestimation
- Fallback mappings deduplicated when same primary model appears across multiple task type routing rules

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed stream() TypeError with async generators**
- **Found during:** Task 3 (LLMService stream implementation)
- **Issue:** LiteLLM Router's acompletion with stream=True returns an async generator directly, not a coroutine wrapping one. Using `await` caused TypeError.
- **Fix:** Added hasattr check for `__await__` to handle both coroutine and async generator patterns
- **Files modified:** apps/server/src/codebot/llm/service.py
- **Verification:** All stream tests pass
- **Committed in:** 802879d (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential for stream() correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed streaming issue.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Complete Multi-LLM Abstraction layer ready for agent consumption
- LLMService.complete() and stream() ready for BaseAgent integration
- Budget enforcement active for pipeline cost control
- Cost estimation ready for pre-execution budget planning
- All 148 LLM tests passing, mypy strict clean

## Self-Check: PASSED

All 11 created/modified files verified present. All 6 task commits (e4d904a, fd239b0, 7b83e39, 6fed79a, a56f5d1, 802879d) verified in git log.

---
*Phase: 04-multi-llm-abstraction*
*Completed: 2026-03-18*
