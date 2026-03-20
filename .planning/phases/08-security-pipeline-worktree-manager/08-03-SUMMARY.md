---
phase: 08-security-pipeline-worktree-manager
plan: 03
subsystem: security
tags: [security-orchestrator, parallel-scanning, taskgroup, deduplication, gate-evaluation, integration-tests]

requires:
  - phase: 08-security-pipeline-worktree-manager
    provides: Scanner adapters (SASTRunner, DependencyScanner, SecretScanner), SecurityGate, Pydantic models

provides:
  - SecurityOrchestrator with parallel fan-out via asyncio.TaskGroup
  - Finding deduplication by (tool, rule_id, file_path, line_start)
  - Severity summary builder with secrets detection
  - Gate evaluation attached to every scan report
  - Integration test scaffold with mocked CLI subprocesses
  - Shared conftest fixtures (mock_subprocess, tmp_git_repo, security_fixtures_dir)

affects: [08-04-compliance, 08-05-worktree-integration, 07-vertical-slice]

tech-stack:
  added: []
  patterns: [parallel-fan-out-with-taskgroup, safe-scan-error-isolation, subprocess-routing-mock]

key-files:
  created:
    - apps/server/src/codebot/security/orchestrator.py
    - apps/server/tests/unit/test_security_orchestrator.py
    - apps/server/tests/integration/test_security_pipeline.py
  modified:
    - apps/server/src/codebot/security/__init__.py
    - apps/server/tests/conftest.py
    - apps/server/pyproject.toml

key-decisions:
  - "asyncio.TaskGroup for parallel scanner execution with _safe_scan error isolation"
  - "Deduplication key is (tool, rule_id, file_path, line_start) tuple"
  - "Secrets identified by tool=='gitleaks' in _build_summary"
  - "Subprocess routing mock pattern for integration tests (inspect cmd[0] to dispatch)"
  - "Registered integration pytest marker in pyproject.toml to suppress warnings"

patterns-established:
  - "Parallel fan-out pattern: asyncio.TaskGroup with _safe_scan wrappers that catch exceptions per-task"
  - "Subprocess routing mock: AsyncMock with side_effect that dispatches by command name"
  - "Conftest factory fixture pattern: mock_subprocess returns (patcher, proc) tuple for flexible test setup"

requirements-completed: [SECP-05]

duration: 6min
completed: 2026-03-20
---

# Phase 8 Plan 03: Security Orchestrator Summary

**SecurityOrchestrator with parallel asyncio.TaskGroup fan-out, finding deduplication, severity summary, gate evaluation, and integration test scaffold with mocked CLI subprocesses**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-20T07:20:39Z
- **Completed:** 2026-03-20T07:27:22Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- SecurityOrchestrator coordinating 3 scanners in parallel via asyncio.TaskGroup with graceful failure isolation
- Finding deduplication by (tool, rule_id, file_path, line_start) preserving first-occurrence order
- Severity summary builder counting CRITICAL/HIGH/MEDIUM/LOW/INFO with separate secrets detection
- SecurityGate evaluation automatically attached to every scan report
- 4 integration tests exercising the full orchestrator -> scanner adapter -> CLI parsing chain
- 3 shared conftest fixtures (mock_subprocess, tmp_git_repo, security_fixtures_dir) for security and worktree testing

## Task Commits

Each task was committed atomically:

1. **Task 1: SecurityOrchestrator with parallel fan-out, deduplication, and summary builder** - `6586dc9` (test, TDD RED), `750aba3` (feat, TDD GREEN)
2. **Task 2: Integration test scaffold and conftest fixtures** - `6554342` (feat)

## Files Created/Modified

- `apps/server/src/codebot/security/orchestrator.py` - SecurityOrchestrator with parallel scan, dedup, summary, gate
- `apps/server/src/codebot/security/__init__.py` - Added SecurityOrchestrator to package exports
- `apps/server/tests/unit/test_security_orchestrator.py` - 7 unit tests for orchestrator logic
- `apps/server/tests/integration/test_security_pipeline.py` - 4 integration tests with mocked CLI subprocesses
- `apps/server/tests/conftest.py` - Added mock_subprocess, tmp_git_repo, security_fixtures_dir fixtures
- `apps/server/pyproject.toml` - Registered integration pytest marker

## Decisions Made

- asyncio.TaskGroup chosen for parallel scanner execution with _safe_scan wrappers to catch individual scanner exceptions without cancelling siblings
- Deduplication key is (tool, rule_id, file_path, line_start) tuple -- identifies same finding across scanner runs
- Secrets identified by checking tool=="gitleaks" rather than severity, since other tools can also produce CRITICAL findings
- Integration tests use subprocess routing mock pattern: AsyncMock with side_effect that inspects cmd[0] to dispatch appropriate response per scanner
- Registered "integration" as a custom pytest marker to suppress PytestUnknownMarkWarning

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- SecurityOrchestrator is the central entry point for all security scanning operations
- Integration test infrastructure ready for Plan 04 (SOC 2 compliance) to extend with compliance checker
- Conftest fixtures (tmp_git_repo, mock_subprocess) ready for Plan 05 (worktree integration) tests
- Optional compliance scanner slot available via constructor parameter

## Self-Check: PASSED

- All 4 created/modified source files verified present on disk
- Commit 6586dc9 (Task 1 RED) verified in git log
- Commit 750aba3 (Task 1 GREEN) verified in git log
- Commit 6554342 (Task 2) verified in git log
- All 11 tests pass (7 unit + 4 integration)

---
*Phase: 08-security-pipeline-worktree-manager*
*Completed: 2026-03-20*
