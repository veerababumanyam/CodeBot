---
phase: 7
slug: vertical-slice
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9+ with pytest-asyncio |
| **Config file** | `tests/conftest.py` (shared fixtures), `apps/server/tests/conftest.py` (server fixtures) |
| **Quick run command** | `uv run pytest tests/unit/agents/ tests/unit/input/ tests/unit/debug/ -x --timeout=30` |
| **Full suite command** | `uv run pytest tests/ -x --timeout=120` |
| **Estimated runtime** | ~30 seconds (quick), ~120 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/agents/ tests/unit/input/ tests/unit/debug/ -x --timeout=30`
- **After every plan wave:** Run `uv run pytest tests/ -x --timeout=120`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | INPT-01 | unit | `uv run pytest tests/unit/input/test_extractor.py::test_natural_language_input -x` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | INPT-02 | unit | `uv run pytest tests/unit/input/test_extractor.py::test_structured_input_formats -x` | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 1 | INPT-04 | unit | `uv run pytest tests/unit/input/test_extractor.py::test_extraction_completeness -x` | ❌ W0 | ⬜ pending |
| 07-01-04 | 01 | 1 | INPT-05 | unit | `uv run pytest tests/unit/input/test_clarifier.py::test_ambiguity_detection -x` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 1 | IMPL-02 | unit | `uv run pytest tests/unit/agents/test_backend_dev.py::test_code_generation -x` | ❌ W0 | ⬜ pending |
| 07-02-02 | 02 | 1 | IMPL-07 | unit | `uv run pytest tests/unit/agents/test_backend_dev.py::test_lint_typecheck -x` | ❌ W0 | ⬜ pending |
| 07-02-03 | 02 | 1 | QA-01 | unit | `uv run pytest tests/unit/agents/test_code_reviewer.py::test_review_output -x` | ❌ W0 | ⬜ pending |
| 07-02-04 | 02 | 1 | QA-06 | unit | `uv run pytest tests/unit/agents/test_code_reviewer.py::test_quality_gate -x` | ❌ W0 | ⬜ pending |
| 07-03-01 | 03 | 2 | TEST-01 | unit | `uv run pytest tests/unit/agents/test_tester.py::test_unit_test_generation -x` | ❌ W0 | ⬜ pending |
| 07-03-02 | 03 | 2 | TEST-02 | unit | `uv run pytest tests/unit/agents/test_tester.py::test_integration_test_generation -x` | ❌ W0 | ⬜ pending |
| 07-03-03 | 03 | 2 | TEST-05 | integration | `uv run pytest tests/integration/test_vertical_slice_e2e.py::test_failure_routes_to_debugger -x` | ❌ W0 | ⬜ pending |
| 07-03-04 | 03 | 2 | DBUG-01 | unit | `uv run pytest tests/unit/debug/test_analyzer.py::test_root_cause_analysis -x` | ❌ W0 | ⬜ pending |
| 07-03-05 | 03 | 2 | DBUG-02 | unit | `uv run pytest tests/unit/debug/test_fixer.py::test_fix_generation -x` | ❌ W0 | ⬜ pending |
| 07-03-06 | 03 | 2 | DBUG-03 | unit | `uv run pytest tests/unit/debug/test_loop_controller.py::test_experiment_loop -x` | ❌ W0 | ⬜ pending |
| 07-03-07 | 03 | 2 | EVNT-01 | integration | `uv run pytest tests/integration/test_vertical_slice_e2e.py::test_event_emission -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/input/test_extractor.py` — stubs for INPT-01, INPT-02, INPT-04
- [ ] `tests/unit/input/test_clarifier.py` — stubs for INPT-05
- [ ] `tests/unit/agents/test_backend_dev.py` — stubs for IMPL-02, IMPL-07
- [ ] `tests/unit/agents/test_code_reviewer.py` — stubs for QA-01, QA-06
- [ ] `tests/unit/agents/test_tester.py` — stubs for TEST-01, TEST-02
- [ ] `tests/unit/debug/test_analyzer.py` — stubs for DBUG-01
- [ ] `tests/unit/debug/test_fixer.py` — stubs for DBUG-02
- [ ] `tests/unit/debug/test_loop_controller.py` — stubs for DBUG-03
- [ ] `tests/integration/test_vertical_slice_e2e.py` — stubs for TEST-05, EVNT-01
- [ ] `tests/conftest.py` — LLM mock fixtures (instructor/litellm mocks)
- [ ] `uv add --dev pytest-json-report` — machine-parseable test results for Tester agent

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| LLM output quality assessment | INPT-04, IMPL-02, QA-01 | LLM outputs vary; mock tests verify structure not quality | Run with real LLM, inspect extracted requirements / generated code / review comments for coherence |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
