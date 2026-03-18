---
phase: 05-context-management
plan: 01
subsystem: context
tags: [tiktoken, pydantic, aiofiles, token-budget, three-tier-context, async-io]

# Dependency graph
requires:
  - phase: 01-foundation-and-scaffolding
    provides: "Server package structure, pyproject.toml, pytest config"
provides:
  - "Priority enum (CRITICAL/HIGH/MEDIUM/LOW) for context item ranking"
  - "ContextItem, CodeSymbol, L0Context, L1Context Pydantic models"
  - "AgentContext class with budget-aware add/remove/query"
  - "TokenBudget class with tiktoken BPE token counting"
  - "ThreeTierLoader with async L0/L1 loading from filesystem"
  - "Role-based file selection for L1 context (6 roles + DEFAULT)"
affects: [05-02, 05-03, context-adapter, agent-execution]

# Tech tracking
tech-stack:
  added: [tiktoken 0.12.0, aiofiles 25.1.0, types-aiofiles]
  patterns: [priority-based-context-assembly, token-budget-enforcement, async-file-io, three-tier-context-loading]

key-files:
  created:
    - apps/server/src/codebot/context/__init__.py
    - apps/server/src/codebot/context/models.py
    - apps/server/src/codebot/context/budget.py
    - apps/server/src/codebot/context/tiers.py
    - apps/server/tests/unit/context/conftest.py
    - apps/server/tests/unit/context/test_budget.py
    - apps/server/tests/unit/context/test_tiers.py
  modified:
    - apps/server/pyproject.toml

key-decisions:
  - "Used tiktoken cl100k_base as fallback for unknown model tokenizers"
  - "AgentContext is a regular class (not Pydantic BaseModel) for in-place mutation"
  - "L0 context capped at 2500 tokens with conventions truncated first"
  - "Role-to-file mapping uses glob patterns for flexible L1 file selection"
  - "Used uuid4 hex prefix for ContextItem IDs to avoid collisions"

patterns-established:
  - "Priority-based context assembly: CRITICAL > HIGH > MEDIUM > LOW"
  - "Token budget enforcement: count before add, never silently overflow"
  - "Async file I/O: all filesystem reads use aiofiles"
  - "Three-tier loading: L0 (always), L1 (phase+role), L2 (on-demand via vector store)"
  - "Graceful degradation: missing files return empty defaults, no exceptions"

requirements-completed: [CTXT-01, CTXT-02, CTXT-07]

# Metrics
duration: 8min
completed: 2026-03-18
---

# Phase 5 Plan 1: Context Core Types, Token Budget, and Three-Tier Loader Summary

**Priority-based context models with tiktoken token budget enforcement and async three-tier L0/L1 loading from filesystem**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-18T10:05:31Z
- **Completed:** 2026-03-18T10:13:50Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Built complete context type system with Priority enum, ContextItem, CodeSymbol, L0Context, L1Context, and AgentContext
- Implemented TokenBudget class using tiktoken for accurate BPE-based token counting with fallback for unknown models
- Created ThreeTierLoader with async L0/L1 loading, role-based file selection for 6 agent roles, and L0 token cap enforcement
- All 29 unit tests pass (19 for budget/models, 10 for tiers) with strict mypy type checking clean

## Task Commits

Each task was committed atomically:

1. **Task 1: Create context models, token budget, and unit tests** - `df19a26` (feat)
2. **Task 2: Create ThreeTierLoader for L0/L1 context loading with tests** - `16ce4f9` (feat)

_TDD tasks: tests written first (RED phase confirmed), then implementation (GREEN phase)._

## Files Created/Modified
- `apps/server/src/codebot/context/__init__.py` - Public API exports for context package (8 exports)
- `apps/server/src/codebot/context/models.py` - Priority, ContextItem, CodeSymbol, L0Context, L1Context, AgentContext
- `apps/server/src/codebot/context/budget.py` - TokenBudget with tiktoken encoding, consume/release/count
- `apps/server/src/codebot/context/tiers.py` - ThreeTierLoader with async L0/L1 loading and role-based file selection
- `apps/server/pyproject.toml` - Added tiktoken>=0.12.0, aiofiles>=25.1.0 to dependencies
- `apps/server/tests/unit/context/conftest.py` - Shared fixtures (sample_l0_context, sample_l1_context, sample_code_content)
- `apps/server/tests/unit/context/test_budget.py` - 19 tests for TokenBudget, AgentContext, Priority, ContextItem
- `apps/server/tests/unit/context/test_tiers.py` - 10 tests for ThreeTierLoader L0/L1 loading

## Decisions Made
- Used tiktoken cl100k_base as universal fallback for unknown model tokenizers (within ~10% accuracy for non-OpenAI models)
- Made AgentContext a regular class instead of Pydantic BaseModel to support in-place mutation (add/remove items)
- Set L0 token cap at 2500 tokens, truncating conventions first when over budget
- Used glob patterns in role-to-file mapping for flexible L1 file discovery
- Used uuid4 hex prefix for ContextItem IDs to prevent collisions in multi-add scenarios

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed types-aiofiles for mypy strict compliance**
- **Found during:** Task 2 (post-implementation verification)
- **Issue:** mypy --strict reported "Library stubs not installed for aiofiles"
- **Fix:** Ran `uv add --dev types-aiofiles` to install type stubs
- **Files modified:** apps/server/pyproject.toml (dev dependencies)
- **Verification:** `mypy src/codebot/context/ --strict` passes with 0 errors
- **Committed in:** Will be included in metadata commit

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor -- type stubs needed for strict mypy compliance. No scope creep.

## Issues Encountered
None -- both tasks executed cleanly with TDD flow (RED then GREEN).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Core context types and budget enforcement ready for Plans 02 (vector store, code indexer) and 03 (context adapter, compressor)
- ThreeTierLoader provides L0/L1 loading that the ContextAdapter will orchestrate
- TokenBudget provides the counting foundation that the ContextCompressor will use for compression decisions

## Self-Check: PASSED

- All 8 created files verified on disk
- Commit df19a26 (Task 1) verified in git log
- Commit 16ce4f9 (Task 2) verified in git log
- All 29 unit tests pass (48 total in context suite including pre-existing)
- mypy --strict passes on all 4 source files with 0 errors

---
*Phase: 05-context-management*
*Completed: 2026-03-18*
