---
phase: 2
slug: graph-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio 0.24+ |
| **Config file** | `libs/graph-engine/pyproject.toml` (pytest section) |
| **Quick run command** | `cd libs/graph-engine && uv run pytest tests/ -x -q` |
| **Full suite command** | `cd libs/graph-engine && uv run pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd libs/graph-engine && uv run pytest tests/ -x -q`
- **After every plan wave:** Run `cd libs/graph-engine && uv run pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | GRPH-01,02,03 | unit | `cd libs/graph-engine && uv run pytest tests/test_models.py -x` | Wave 0 | pending |
| 02-01-02 | 01 | 1 | GRPH-04,05 | unit | `cd libs/graph-engine && uv run pytest tests/test_yaml_loader.py tests/test_validator.py -x` | Wave 0 | pending |
| 02-02-01 | 02 | 2 | GRPH-07,08,09 | unit | `cd libs/graph-engine && uv run pytest tests/test_compiler.py tests/test_tracer.py -x` | Wave 0 | pending |
| 02-02-02 | 02 | 2 | GRPH-07,08 | unit+int | `cd libs/graph-engine && uv run pytest tests/test_executor.py -x` | Wave 0 | pending |
| 02-03-01 | 03 | 3 | GRPH-06 | integration | `cd libs/graph-engine && uv run pytest tests/test_checkpoint.py -x` | Wave 0 | pending |
| 02-03-02 | 03 | 3 | GRPH-10 | unit+int | `cd libs/graph-engine && uv run pytest tests/test_fanout.py -x` | Wave 0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `libs/graph-engine/pyproject.toml` -- needs pytest, pytest-asyncio, langgraph, pydantic, pyyaml dependencies
- [ ] `libs/graph-engine/tests/conftest.py` -- shared fixtures (sample graph definitions, mock nodes)
- [ ] `libs/graph-engine/tests/test_models.py` -- covers GRPH-01, GRPH-02, GRPH-03
- [ ] `libs/graph-engine/tests/test_yaml_loader.py` -- covers GRPH-04
- [ ] `libs/graph-engine/tests/test_validator.py` -- covers GRPH-05
- [ ] `libs/graph-engine/tests/test_compiler.py` -- covers GRPH-07, GRPH-08, GRPH-09, GATE semantics
- [ ] `libs/graph-engine/tests/test_tracer.py` -- covers GRPH-07
- [ ] `libs/graph-engine/tests/test_executor.py` -- covers GRPH-01 (topological), GRPH-08 (parallel)
- [ ] `libs/graph-engine/tests/test_checkpoint.py` -- covers GRPH-06
- [ ] `libs/graph-engine/tests/test_fanout.py` -- covers GRPH-10, compiler integration
- [ ] `libs/graph-engine/tests/fixtures/` -- sample YAML graph definitions for tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Graph visualization renders in dashboard | GRPH-04 (partial) | Requires browser rendering | Load graph in React Flow, verify node/edge display |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
