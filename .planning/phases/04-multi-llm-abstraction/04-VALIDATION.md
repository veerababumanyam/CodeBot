---
phase: 4
slug: multi-llm-abstraction
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-18
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `uv run pytest tests/unit/llm/ -x -q` |
| **Full suite command** | `uv run pytest tests/unit/llm/ tests/integration/llm/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/llm/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/unit/llm/ tests/integration/llm/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-T1 | 01 | 1 | LLM-01, LLM-06 | unit | `uv run pytest tests/unit/llm/test_schemas.py -x -q` | ❌ W0 | ⬜ pending |
| 04-01-T2 | 01 | 1 | LLM-01, LLM-06 | unit | `uv run pytest tests/unit/llm/test_config.py -x -q` | ❌ W0 | ⬜ pending |
| 04-01-T3 | 01 | 1 | LLM-02 | unit | `uv run pytest tests/unit/llm/test_router.py -x -q` | ❌ W0 | ⬜ pending |
| 04-02-T1 | 02 | 2 | LLM-04, LLM-07, LLM-08 | unit | `uv run pytest tests/unit/llm/test_budget.py tests/unit/llm/test_estimator.py -x -q` | ❌ W0 | ⬜ pending |
| 04-02-T2 | 02 | 2 | LLM-03 | unit | `uv run pytest tests/unit/llm/test_fallback.py -x -q` | ❌ W0 | ⬜ pending |
| 04-02-T3 | 02 | 2 | LLM-01, LLM-05 | unit | `uv run pytest tests/unit/llm/test_service.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/llm/` — directory structure
- [ ] `tests/unit/llm/conftest.py` — shared fixtures (mock LiteLLM responses, mock provider configs)
- [ ] `tests/integration/llm/conftest.py` — integration fixtures (mock HTTP, mock subprocess)
- [ ] pytest + pytest-asyncio installed via `uv add --dev pytest pytest-asyncio`

*Wave 0 creates test stubs before any implementation begins.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Self-hosted Ollama connectivity | LLM-01 | Requires running Ollama instance | Start Ollama locally, run integration test with OLLAMA_HOST env |
| Real provider fallback latency | LLM-03 | Requires live API keys | Test with real providers, verify <5s switch time |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
