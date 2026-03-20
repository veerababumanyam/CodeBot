---
phase: 08-security-pipeline-worktree-manager
plan: 04
subsystem: cli-agents
tags: [cli, claude-code, codex, gemini, worktree, security-scanning, docker, subprocess]

# Dependency graph
requires:
  - phase: 08-02
    provides: WorktreePool, PortAllocator, BranchStrategy for worktree lifecycle
  - phase: 08-03
    provides: SecurityOrchestrator.scan() for post-generation security scanning
provides:
  - BaseCLIAdapter ABC with build_command, build_env, check_available
  - ClaudeCodeAdapter, CodexAdapter, GeminiCLIAdapter adapters
  - CLIAgentRunner integrating worktree pool, port allocator, adapters, and SecurityOrchestrator
  - SessionManager for async subprocess execution with timeout
  - OutputParser for JSON extraction from CLI output
  - HealthChecker for process and binary availability detection
  - CLITask/CLIResult/AdapterInfo Pydantic v2 models
  - Docker Compose worktree template with profile-based isolation
affects: [pipeline-orchestration, agent-framework, vertical-slice]

# Tech tracking
tech-stack:
  added: []
  patterns: [adapter-pattern-for-cli-tools, try-finally-resource-cleanup, non-fatal-security-scanning]

key-files:
  created:
    - apps/server/src/codebot/cli_agents/__init__.py
    - apps/server/src/codebot/cli_agents/models.py
    - apps/server/src/codebot/cli_agents/adapters/__init__.py
    - apps/server/src/codebot/cli_agents/adapters/base.py
    - apps/server/src/codebot/cli_agents/adapters/claude_code.py
    - apps/server/src/codebot/cli_agents/adapters/codex.py
    - apps/server/src/codebot/cli_agents/adapters/gemini.py
    - apps/server/src/codebot/cli_agents/session.py
    - apps/server/src/codebot/cli_agents/output_parser.py
    - apps/server/src/codebot/cli_agents/health.py
    - apps/server/src/codebot/cli_agents/runner.py
    - configs/worktree/docker-compose.worktree.yml
    - apps/server/tests/unit/test_cli_agents.py
    - apps/server/tests/integration/test_parallel_worktrees.py
    - apps/server/tests/integration/test_worktree_docker.py
  modified: []

key-decisions:
  - "Runtime import of SecurityReport in models.py (not TYPE_CHECKING) so Pydantic v2 can resolve forward reference with from __future__ import annotations"
  - "noqa TC001 on SecurityReport import consistent with Phase 2 convention for Pydantic model type imports"

patterns-established:
  - "Adapter pattern: BaseCLIAdapter ABC with build_command/build_env/check_available for uniform CLI tool integration"
  - "Non-fatal security scanning: SecurityOrchestrator.scan() failures logged but not propagated from CLIAgentRunner"
  - "try/finally resource cleanup: worktree and ports always released even on adapter failure"

requirements-completed: [IMPL-05, IMPL-06, WORK-02, SECP-05]

# Metrics
duration: 5min
completed: 2026-03-20
---

# Phase 8 Plan 04: CLI Agent Adapters with SecurityOrchestrator Wiring Summary

**Three CLI adapters (Claude Code, Codex, Gemini) with CLIAgentRunner orchestrating worktree isolation, port allocation, and automatic post-generation security scanning (SECP-05)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-20T07:32:04Z
- **Completed:** 2026-03-20T07:37:57Z
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments
- Three CLI adapters building correct commands for Claude Code (--print --output-format json), Codex (--quiet --json), and Gemini (--json --cwd)
- CLIAgentRunner integrating WorktreePool + PortAllocator + BranchStrategy + CLI adapters + SecurityOrchestrator in a single execute() flow
- Automatic SecurityOrchestrator.scan() after every code generation step with SecurityReport attached to CLIResult (SECP-05)
- Docker Compose template with profile-based per-worktree service isolation and dynamic PORT_* variables

## Task Commits

Each task was committed atomically:

1. **Task 1: CLI agent models, adapters, session, parser** - `6b3e98c` (test) + `4646bc0` (feat)
2. **Task 2: CLIAgentRunner, Docker template, integration tests** - `4dd5b9f` (test) + `fd7badf` (feat)

_TDD tasks have separate test and implementation commits._

## Files Created/Modified
- `apps/server/src/codebot/cli_agents/__init__.py` - Package init exporting all adapters and CLIAgentRunner
- `apps/server/src/codebot/cli_agents/models.py` - CLITask, CLIResult (with security_report), AdapterInfo models
- `apps/server/src/codebot/cli_agents/adapters/base.py` - BaseCLIAdapter ABC with build_command, build_env, check_available
- `apps/server/src/codebot/cli_agents/adapters/claude_code.py` - ClaudeCodeAdapter for Claude Code CLI
- `apps/server/src/codebot/cli_agents/adapters/codex.py` - CodexAdapter for OpenAI Codex CLI
- `apps/server/src/codebot/cli_agents/adapters/gemini.py` - GeminiCLIAdapter for Google Gemini CLI
- `apps/server/src/codebot/cli_agents/session.py` - SessionManager for async subprocess execution with timeout
- `apps/server/src/codebot/cli_agents/output_parser.py` - OutputParser for JSON extraction from mixed CLI output
- `apps/server/src/codebot/cli_agents/health.py` - HealthChecker for process/binary availability
- `apps/server/src/codebot/cli_agents/runner.py` - CLIAgentRunner with SecurityOrchestrator wiring
- `configs/worktree/docker-compose.worktree.yml` - Per-worktree Docker Compose template with profiles
- `apps/server/tests/unit/test_cli_agents.py` - 14 unit tests for adapters, session, parser, models
- `apps/server/tests/integration/test_parallel_worktrees.py` - 6 integration tests for parallel execution and security wiring
- `apps/server/tests/integration/test_worktree_docker.py` - 3 integration tests for Docker template validation

## Decisions Made
- Runtime import of SecurityReport in models.py (not TYPE_CHECKING only) -- Pydantic v2 needs runtime access to resolve forward references even with `from __future__ import annotations`; noqa TC001 consistent with Phase 2 convention
- Non-fatal security scanning pattern -- SecurityOrchestrator.scan() exceptions caught and logged but never crash CLIAgentRunner, allowing code generation to succeed even if scanner infrastructure is unavailable

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Pydantic forward reference resolution for SecurityReport**
- **Found during:** Task 1 (CLIResult model)
- **Issue:** Using TYPE_CHECKING-only import for SecurityReport caused PydanticUserError at runtime -- Pydantic v2 cannot resolve forward references from TYPE_CHECKING blocks even with `from __future__ import annotations`
- **Fix:** Changed to runtime import with `noqa: TC001` annotation
- **Files modified:** apps/server/src/codebot/cli_agents/models.py
- **Verification:** All 14 unit tests pass including CLIResult instantiation
- **Committed in:** 4646bc0 (Task 1 feat commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary fix for Pydantic model correctness. No scope creep.

## Issues Encountered
None beyond the forward reference fix documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CLI agent adapters ready for integration with agent graph engine
- SecurityOrchestrator wiring enables automatic security scanning for all code generation tasks
- Docker Compose template available for per-worktree runtime isolation
- Phase 8 Plan 05 (final plan) can build on this foundation

## Self-Check: PASSED

All 15 created files verified present. All 4 task commits (6b3e98c, 4646bc0, 4dd5b9f, fd7badf) verified in git log.

---
*Phase: 08-security-pipeline-worktree-manager*
*Completed: 2026-03-20*
