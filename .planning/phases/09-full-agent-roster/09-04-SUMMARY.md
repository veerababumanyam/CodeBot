---
phase: 09-full-agent-roster
plan: 04
subsystem: agents
tags: [security-auditor, accessibility, performance, i18n, tester, debugger, playwright, docker-sandbox, wcag, semgrep, trivy, gitleaks]

# Dependency graph
requires:
  - phase: 09-01
    provides: "Agent registry, BaseAgent pattern, brainstorming/researcher agents"
provides:
  - "SecurityAuditorAgent with Semgrep/Trivy/Gitleaks integration (QA-02)"
  - "AccessibilityAgent for WCAG 2.1 AA compliance (QA-03)"
  - "PerformanceAgent for bottleneck profiling (QA-04)"
  - "I18nL10nAgent for internationalization verification (QA-05)"
  - "TesterAgent with Playwright E2E and Docker sandbox (TEST-03, TEST-04)"
  - "DebuggerAgent with security-specific debugging (DBUG-04)"
affects: [09-05, pipeline-orchestration, qa-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [parallel-qa-agents-with-separate-state-namespaces, security-quality-gate-pattern, sandbox-config-dataclass]

key-files:
  created:
    - apps/server/src/codebot/agents/security_auditor.py
    - apps/server/src/codebot/agents/accessibility.py
    - apps/server/src/codebot/agents/performance.py
    - apps/server/src/codebot/agents/i18n_l10n.py
    - configs/agents/security_auditor.yaml
    - configs/agents/accessibility.yaml
    - configs/agents/performance.yaml
    - configs/agents/i18n_l10n.yaml
    - tests/unit/agents/test_qa_agents.py
    - tests/unit/agents/test_testing_agents.py
  modified:
    - apps/server/src/codebot/agents/tester.py
    - apps/server/src/codebot/agents/debugger.py
    - configs/agents/tester.yaml
    - configs/agents/debugger.yaml
    - tests/unit/agents/test_tester.py
    - tests/unit/agents/test_debugger.py

key-decisions:
  - "All S6 QA agents use separate state_updates keys for parallel execution safety (QA-07)"
  - "SecurityAuditor quality gate blocks on critical OR high severity findings"
  - "TesterAgent and DebuggerAgent fully reimplemented with extended capabilities (not patched)"
  - "DebuggerAgent reads security_auditor_output for security-specific debugging (DBUG-04)"

patterns-established:
  - "Parallel QA agents: each writes to a distinct state namespace (security_auditor_output, accessibility_output, performance_output, i18n_output)"
  - "Quality gate pattern: SecurityAuditor.review() enforces gate_passed boolean based on severity thresholds"
  - "Sandbox config: dict field with use_docker, image, timeout defaults for test isolation"

requirements-completed: [QA-02, QA-03, QA-04, QA-05, QA-07, TEST-03, TEST-04, DBUG-04]

# Metrics
duration: 8min
completed: 2026-03-20
---

# Phase 09 Plan 04: QA, Tester, and Debugger Agents Summary

**4 S6 QA agents (SecurityAuditor/Accessibility/Performance/I18n) with parallel-safe state namespaces, plus extended TesterAgent with Playwright E2E/Docker sandbox and DebuggerAgent with security debugging**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-20T08:39:29Z
- **Completed:** 2026-03-20T08:47:57Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- Implemented 4 S6 QA agents extending BaseAgent with parallel-safe state namespaces for QA-07
- SecurityAuditorAgent integrates Semgrep, Trivy, and Gitleaks with quality gate enforcement (QA-02)
- AccessibilityAgent audits WCAG 2.1 AA compliance with axe-core and Lighthouse tools (QA-03)
- PerformanceAgent profiles bottlenecks with load testing and bundle analysis (QA-04)
- I18nL10nAgent verifies internationalization completeness with RTL validation (QA-05)
- Extended TesterAgent with Playwright E2E testing (TEST-03) and Docker sandbox execution (TEST-04)
- Extended DebuggerAgent with security-specific debugging from SecurityAuditor findings (DBUG-04)
- 44 passing tests across test_qa_agents.py and test_testing_agents.py

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement 4 S6 QA agents** - `f734999` (feat)
2. **Task 2: Implement extended Tester and Debugger agents** - `66a480c` (feat)

## Files Created/Modified
- `apps/server/src/codebot/agents/security_auditor.py` - SecurityAuditorAgent with Semgrep/Trivy/Gitleaks quality gate
- `apps/server/src/codebot/agents/accessibility.py` - AccessibilityAgent for WCAG 2.1 AA audit
- `apps/server/src/codebot/agents/performance.py` - PerformanceAgent for bottleneck profiling
- `apps/server/src/codebot/agents/i18n_l10n.py` - I18nL10nAgent for internationalization verification
- `apps/server/src/codebot/agents/tester.py` - Extended TesterAgent with Playwright and Docker sandbox
- `apps/server/src/codebot/agents/debugger.py` - Extended DebuggerAgent with security debugging
- `configs/agents/security_auditor.yaml` - SecurityAuditor agent config
- `configs/agents/accessibility.yaml` - Accessibility agent config
- `configs/agents/performance.yaml` - Performance agent config
- `configs/agents/i18n_l10n.yaml` - I18n agent config
- `configs/agents/tester.yaml` - Updated Tester config with Playwright/sandbox settings
- `configs/agents/debugger.yaml` - Updated Debugger config with security debugging settings
- `tests/unit/agents/test_qa_agents.py` - 27 tests for 4 QA agents
- `tests/unit/agents/test_testing_agents.py` - 17 tests for Tester/Debugger
- `tests/unit/agents/test_tester.py` - Updated tests for extended TesterAgent
- `tests/unit/agents/test_debugger.py` - Updated tests for extended DebuggerAgent

## Decisions Made
- All S6 QA agents use separate state_updates keys (security_auditor_output, accessibility_output, performance_output, i18n_output) for parallel execution safety (QA-07)
- SecurityAuditor quality gate requires gate_passed=True AND all 4 severity keys present -- blocks on critical OR high findings
- TesterAgent and DebuggerAgent fully reimplemented (not patched from Phase 7) since the plan specifies new implementations with extended capabilities from the start
- DebuggerAgent.perceive() explicitly reads security_auditor_output from shared_state for DBUG-04 security debugging

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated existing test_tester.py and test_debugger.py for new agent API**
- **Found during:** Task 2 (Extended Tester/Debugger implementation)
- **Issue:** Old Phase 7 test files (test_tester.py, test_debugger.py) imported from old API (source_files, instructor, TestRunner) incompatible with new implementations
- **Fix:** Rewrote test files to test the new agent API (dev_outputs, tester_output, sandbox_config, etc.)
- **Files modified:** tests/unit/agents/test_tester.py, tests/unit/agents/test_debugger.py
- **Verification:** All 37 tests pass across test_testing_agents.py, test_tester.py, test_debugger.py
- **Committed in:** 66a480c (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary to maintain test suite consistency after agent reimplementation. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All S6 QA agents ready for pipeline orchestration integration
- TesterAgent and DebuggerAgent ready for S7/S8 pipeline stages
- 6 agents total from this plan join the agent roster (now at ~15 agents implemented)
- Remaining Plan 05 covers deployment, documentation, and extensibility agents

## Self-Check: PASSED

All 16 files verified present on disk. Both task commits (f734999, 66a480c) verified in git log. 44 tests passing.

---
*Phase: 09-full-agent-roster*
*Completed: 2026-03-20*
