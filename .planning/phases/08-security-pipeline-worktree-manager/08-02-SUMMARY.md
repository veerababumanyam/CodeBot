---
phase: 08-security-pipeline-worktree-manager
plan: 02
subsystem: worktree
tags: [git-worktree, asyncio-queue, port-allocation, branch-strategy, pydantic-v2]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Agent ORM model with worktree_path field
provides:
  - WorktreePool with asyncio.Queue-based lifecycle and overflow support
  - PortAllocator with race-free ephemeral port reservation
  - BranchStrategy with deterministic naming, sequential merge, conflict detection
  - CommitManager with agent attribution trailers
  - WorktreeInfo, BranchConfig, MergeResult, MergeStrategy Pydantic models
affects: [08-03-security-orchestrator, 08-04-cli-agent-runner, 08-05-integration]

# Tech tracking
tech-stack:
  added: [ephemeral-port-reserve]
  patterns: [asyncio.Queue pool, subprocess git commands, overflow worktree creation]

key-files:
  created:
    - apps/server/src/codebot/worktree/__init__.py
    - apps/server/src/codebot/worktree/models.py
    - apps/server/src/codebot/worktree/pool.py
    - apps/server/src/codebot/worktree/port_allocator.py
    - apps/server/src/codebot/worktree/branch_strategy.py
    - apps/server/src/codebot/worktree/commit_manager.py
    - apps/server/tests/unit/test_worktree_pool.py
    - apps/server/tests/unit/test_port_allocator.py
    - apps/server/tests/unit/test_branch_strategy.py
  modified: []

key-decisions:
  - "StrEnum for MergeStrategy (consistent with Phase 2 ruff UP042 decision)"
  - "Pydantic BaseModel with frozen=False for WorktreeInfo (mutable during acquire/release lifecycle)"
  - "asyncio.create_subprocess_exec for all git operations (avoids GitPython resource leaks per research Pitfall 3)"
  - "ephemeral-port-reserve for port allocation (race-free TIME_WAIT trick per research recommendation)"

patterns-established:
  - "Worktree pool acquire/release pattern: asyncio.Queue for available, dict for active, asyncio.Lock for thread safety"
  - "Overflow worktree creation: auto-scale beyond pool_size, auto-destroy on release"
  - "Branch naming convention: prefix/task_id-sanitized_agent_id with regex sanitization"
  - "Agent attribution: commit trailers with Agent and Refs fields for traceability"

requirements-completed: [WORK-01, WORK-03, WORK-04]

# Metrics
duration: 5min
completed: 2026-03-20
---

# Phase 8 Plan 02: Worktree Pool Manager Summary

**asyncio.Queue-based worktree pool with ephemeral port allocation, deterministic branch naming, and sequential merge with conflict detection**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-20T07:10:35Z
- **Completed:** 2026-03-20T07:16:02Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- WorktreePool manages git worktrees with asyncio.Queue lifecycle, overflow support, and automatic cleanup
- PortAllocator reserves race-free ports using ephemeral-port-reserve for parallel agent isolation
- BranchStrategy generates deterministic branch names and performs sequential merge with conflict detection
- CommitManager creates structured commits with agent attribution trailers
- All 18 unit tests pass across 3 test files

## Task Commits

Each task was committed atomically:

1. **Task 1: Worktree models, WorktreePool, PortAllocator** - `ff3ded8` (test: RED) + `91aab0e` (feat: GREEN)
2. **Task 2: BranchStrategy, CommitManager** - `b4e24fb` (test: RED) + `6ad617f` (feat: GREEN)
3. **Dependency addition** - `15305f0` (chore: ephemeral-port-reserve)

## Files Created/Modified
- `apps/server/src/codebot/worktree/__init__.py` - Package exports for all worktree components
- `apps/server/src/codebot/worktree/models.py` - WorktreeInfo, BranchConfig, MergeResult, MergeStrategy Pydantic models
- `apps/server/src/codebot/worktree/pool.py` - WorktreePool with asyncio.Queue, acquire/release, overflow, cleanup
- `apps/server/src/codebot/worktree/port_allocator.py` - PortAllocator with ephemeral-port-reserve integration
- `apps/server/src/codebot/worktree/branch_strategy.py` - BranchStrategy with naming, merge, conflict detection
- `apps/server/src/codebot/worktree/commit_manager.py` - CommitManager with agent attribution trailers
- `apps/server/tests/unit/test_worktree_pool.py` - 6 tests for pool lifecycle
- `apps/server/tests/unit/test_port_allocator.py` - 4 tests for port allocation
- `apps/server/tests/unit/test_branch_strategy.py` - 8 tests for branch strategy and commit manager

## Decisions Made
- Used StrEnum for MergeStrategy (consistent with Phase 2 ruff UP042 decision for Python 3.12+ target)
- WorktreeInfo uses frozen=False (mutable fields updated during acquire/release lifecycle)
- BranchConfig and MergeResult use frozen=True (immutable after creation)
- asyncio.create_subprocess_exec for all git operations (avoids GitPython resource leaks per research Pitfall 3)
- ephemeral-port-reserve for port allocation (race-free TIME_WAIT trick per research recommendation)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Worktree pool ready for consumption by CLI agent runner (Plan 04)
- BranchStrategy ready for SecurityOrchestrator merge operations (Plan 03)
- PortAllocator ready for per-worktree Docker profile port assignment

## Self-Check: PASSED

- All 9 source/test files verified present on disk
- All 5 commit hashes verified in git log

---
*Phase: 08-security-pipeline-worktree-manager*
*Completed: 2026-03-20*
