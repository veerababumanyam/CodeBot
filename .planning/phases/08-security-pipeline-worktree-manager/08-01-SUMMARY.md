---
phase: 08-security-pipeline-worktree-manager
plan: 01
subsystem: security
tags: [semgrep, trivy, gitleaks, pydantic, security-gate, allowlist, scanner-adapters]

requires:
  - phase: 01-foundation
    provides: SecurityFinding ORM model, Severity and FindingType enums

provides:
  - ScanFinding, ScanResult, SecurityReport Pydantic models for scanner output normalization
  - BaseScanner ABC with async _run_cli for CLI scanner wrapping
  - SASTRunner (Semgrep), DependencyScanner (Trivy), SecretScanner (Gitleaks) adapters
  - SecurityGate with threshold-based pass/fail evaluation
  - AllowlistValidator for pip/npm dependency checking
  - YAML configuration files for thresholds, allowlists, and gitleaks

affects: [08-03-security-orchestrator, 08-04-compliance, 07-vertical-slice]

tech-stack:
  added: []
  patterns: [scanner-adapter-pattern, threshold-based-gate, cli-subprocess-wrapping]

key-files:
  created:
    - apps/server/src/codebot/security/__init__.py
    - apps/server/src/codebot/security/models.py
    - apps/server/src/codebot/security/scanners/base.py
    - apps/server/src/codebot/security/scanners/semgrep.py
    - apps/server/src/codebot/security/scanners/trivy.py
    - apps/server/src/codebot/security/scanners/gitleaks.py
    - apps/server/src/codebot/security/scanners/allowlist.py
    - apps/server/src/codebot/security/gate.py
    - apps/server/src/codebot/security/config.py
    - configs/security/thresholds.yaml
    - configs/security/allowlist.yaml
    - configs/security/gitleaks.toml
    - apps/server/tests/unit/test_security_gate.py
    - apps/server/tests/unit/test_security_semgrep.py
    - apps/server/tests/unit/test_security_trivy.py
    - apps/server/tests/unit/test_security_gitleaks.py
    - apps/server/tests/unit/test_allowlist.py
  modified: []

key-decisions:
  - "Reuse Severity enum from codebot.db.models.security rather than redefining"
  - "ComplianceReport as placeholder model for later SOC 2 plan"
  - "Semgrep ERROR maps to HIGH (not CRITICAL) since Semgrep ERROR is rule-match severity"
  - "All Gitleaks secrets get Severity.CRITICAL regardless of rule"
  - "Trivy finding title includes PkgName for clearer identification"
  - "AllowlistValidator uses case-insensitive matching for Python packages"

patterns-established:
  - "Scanner adapter pattern: BaseScanner ABC with async scan() -> ScanResult and _run_cli helper"
  - "SecurityGate evaluates SecurityReport.summary against SecurityThresholds with pass/fail/warn"
  - "Config loading from YAML into Pydantic models via yaml.safe_load"

requirements-completed: [SECP-01, SECP-02, SECP-03, SECP-04, SECP-06, CMPL-04]

duration: 6min
completed: 2026-03-20
---

# Phase 8 Plan 01: Security Scanners and Gate Summary

**Semgrep/Trivy/Gitleaks scanner adapters with BaseScanner ABC, SecurityGate threshold evaluator, AllowlistValidator for pip/npm, and 48 unit tests**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-20T07:10:36Z
- **Completed:** 2026-03-20T07:16:51Z
- **Tasks:** 2
- **Files modified:** 17

## Accomplishments

- Security package with Pydantic v2 models (ScanFinding, ScanResult, SecurityReport, SecurityThresholds, GateResult, AllowlistConfig)
- BaseScanner ABC with async subprocess execution and timeout support via asyncio.create_subprocess_exec
- Three scanner adapters parsing JSON output: SASTRunner (Semgrep), DependencyScanner (Trivy), SecretScanner (Gitleaks)
- SecurityGate with configurable thresholds -- blocks on critical/high, warns on medium/low
- AllowlistValidator checking pip requirements.txt and npm package.json against curated allowlists
- YAML configuration files with sensible defaults for production use
- Full TDD with 48 passing unit tests across 5 test files

## Task Commits

Each task was committed atomically:

1. **Task 1: Security Pydantic models, BaseScanner ABC, SecurityGate, and config files** - `e305b60` (feat)
2. **Task 2: Semgrep, Trivy, Gitleaks scanner adapters and AllowlistValidator with unit tests** - `d76070e` (feat)

## Files Created/Modified

- `apps/server/src/codebot/security/__init__.py` - Package init exporting key classes
- `apps/server/src/codebot/security/models.py` - Pydantic v2 models for scan findings, results, reports, thresholds
- `apps/server/src/codebot/security/scanners/base.py` - BaseScanner ABC with async _run_cli helper
- `apps/server/src/codebot/security/scanners/semgrep.py` - SASTRunner wrapping Semgrep CLI
- `apps/server/src/codebot/security/scanners/trivy.py` - DependencyScanner wrapping Trivy CLI
- `apps/server/src/codebot/security/scanners/gitleaks.py` - SecretScanner wrapping Gitleaks CLI
- `apps/server/src/codebot/security/scanners/allowlist.py` - AllowlistValidator for pip/npm dependency checking
- `apps/server/src/codebot/security/gate.py` - SecurityGate with threshold-based evaluation
- `apps/server/src/codebot/security/config.py` - YAML config loaders and path constants
- `configs/security/thresholds.yaml` - Default gate thresholds (0 critical, 0 high, 5 medium, 20 low)
- `configs/security/allowlist.yaml` - Approved Python and npm packages
- `configs/security/gitleaks.toml` - Gitleaks allowlist for test fixtures and dev keys
- `apps/server/tests/unit/test_security_gate.py` - 13 tests for models and gate logic
- `apps/server/tests/unit/test_security_semgrep.py` - 5 tests for Semgrep adapter
- `apps/server/tests/unit/test_security_trivy.py` - 7 tests for Trivy adapter
- `apps/server/tests/unit/test_security_gitleaks.py` - 6 tests for Gitleaks adapter
- `apps/server/tests/unit/test_allowlist.py` - 17 tests for AllowlistValidator

## Decisions Made

- Reused Severity and FindingType enums from `codebot.db.models.security` to maintain consistency with the ORM layer
- ComplianceReport added as a placeholder model in models.py for later SOC 2 compliance plan (08-04)
- Semgrep ERROR severity maps to Severity.HIGH (not CRITICAL) since Semgrep's ERROR level indicates rule-match confidence, not vulnerability severity
- All Gitleaks findings are assigned Severity.CRITICAL since any hardcoded secret is a critical security issue
- Trivy finding titles prepend PkgName when available for clearer vulnerability identification
- AllowlistValidator uses case-insensitive matching for Python packages (pip is case-insensitive)
- Code snippet truncation at 200 chars for Gitleaks (secrets), 500 chars for Semgrep (code context)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Scanner adapters and gate are ready for SecurityOrchestrator (Plan 03) to coordinate parallel execution
- AllowlistValidator is ready for WorktreeManager (Plan 02) to validate dependencies before agent installs
- SecurityReport model supports the compliance_report field for SOC 2 integration (Plan 04)

## Self-Check: PASSED

- All 18 created files verified present on disk
- Commit e305b60 (Task 1) verified in git log
- Commit d76070e (Task 2) verified in git log
- All 48 tests pass across 5 test files

---
*Phase: 08-security-pipeline-worktree-manager*
*Completed: 2026-03-20*
