---
phase: 5
slug: context-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/unit/context/ -x -q` |
| **Full suite command** | `uv run pytest tests/unit/context/ tests/integration/context/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/context/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/unit/context/ tests/integration/context/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | CTXT-01 | unit | `uv run pytest tests/unit/context/test_l0_context.py -v` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | CTXT-02 | unit | `uv run pytest tests/unit/context/test_l1_context.py -v` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | CTXT-03 | unit | `uv run pytest tests/unit/context/test_context_adapter.py -v` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 1 | CTXT-04 | unit+int | `uv run pytest tests/unit/context/test_vector_store.py -v` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 1 | CTXT-05 | unit | `uv run pytest tests/unit/context/test_code_indexer.py -v` | ❌ W0 | ⬜ pending |
| 05-02-03 | 02 | 2 | CTXT-06 | unit | `uv run pytest tests/unit/context/test_compressor.py -v` | ❌ W0 | ⬜ pending |
| 05-02-04 | 02 | 2 | CTXT-07 | unit | `uv run pytest tests/unit/context/test_token_budget.py -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/context/` — directory structure for context tests
- [ ] `tests/unit/context/conftest.py` — shared fixtures (mock LLM responses, sample code files, test project configs)
- [ ] `tests/integration/context/conftest.py` — integration fixtures (LanceDB temp instance, sample embeddings)
- [ ] pytest + pytest-asyncio installed in dev dependencies

*Existing infrastructure from Phase 1-4 may already cover pytest installation.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Token budget enforcement accuracy | CTXT-07 | Exact token counts vary by model | Compare tiktoken count vs actual API token usage for 5 sample prompts |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
