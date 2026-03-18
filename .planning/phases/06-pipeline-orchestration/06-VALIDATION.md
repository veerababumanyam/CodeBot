---
phase: 6
slug: pipeline-orchestration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9+ with pytest-asyncio |
| **Config file** | `tests/conftest.py` (needs Temporal test fixtures) |
| **Quick run command** | `uv run pytest tests/unit/pipeline/ -x --timeout=30` |
| **Full suite command** | `uv run pytest tests/ -x --timeout=120` |
| **Estimated runtime** | ~30 seconds (unit), ~120 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/pipeline/ -x --timeout=30`
- **After every plan wave:** Run `uv run pytest tests/ -x --timeout=120`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | PIPE-04 | unit | `uv run pytest tests/unit/pipeline/test_preset_loader.py -x` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | PIPE-07 | unit | `uv run pytest tests/unit/pipeline/test_project_detector.py -x` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 2 | PIPE-03 | unit | `uv run pytest tests/unit/pipeline/test_gates.py -x` | ❌ W0 | ⬜ pending |
| 06-03-01 | 03 | 3 | PIPE-08 | unit | `uv run pytest tests/unit/pipeline/test_event_emission.py -x` | ❌ W0 | ⬜ pending |
| 06-04-01 | 04 | 3 | PIPE-01, PIPE-02 | unit | `uv run pytest tests/unit/pipeline/test_parallel_phases.py -x` | ❌ W0 | ⬜ pending |
| 06-04-02 | 04 | 3 | PIPE-01, PIPE-05 | integration | `uv run pytest tests/integration/test_pipeline_e2e.py -x` | ❌ W0 | ⬜ pending |
| 06-04-03 | 04 | 3 | PIPE-05 | integration | `uv run pytest tests/integration/test_temporal_durability.py -x` | ❌ W0 | ⬜ pending |
| 06-04-04 | 04 | 3 | PIPE-06 | integration | `uv run pytest tests/integration/test_pipeline_resume.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/pipeline/test_preset_loader.py` — stubs for PIPE-04
- [ ] `tests/unit/pipeline/test_project_detector.py` — stubs for PIPE-07
- [ ] `tests/unit/pipeline/test_parallel_phases.py` — stubs for PIPE-02
- [ ] `tests/unit/pipeline/test_gates.py` — stubs for PIPE-03
- [ ] `tests/unit/pipeline/test_event_emission.py` — stubs for PIPE-08
- [ ] `tests/integration/test_pipeline_e2e.py` — stubs for PIPE-01, PIPE-05
- [ ] `tests/integration/test_temporal_durability.py` — stubs for PIPE-05
- [ ] `tests/integration/test_pipeline_resume.py` — stubs for PIPE-06
- [ ] `tests/conftest.py` — shared Temporal WorkflowEnvironment fixtures
- [ ] `uv add --dev temporalio[testing]` — Temporal test dependency
- [ ] NATS test dependency: embedded nats-server or mock

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Temporal Web UI accessible at localhost:8233 | PIPE-05 | Requires visual inspection of UI | Start docker-compose, navigate to http://localhost:8233, verify pipeline workflow visible |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
