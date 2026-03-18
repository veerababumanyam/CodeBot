---
phase: 4
slug: multi-llm-abstraction
status: draft
nyquist_compliant: false
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
| 04-01-01 | 01 | 1 | LLM-01 | unit | `uv run pytest tests/unit/llm/test_provider_registry.py -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | LLM-01 | unit | `uv run pytest tests/unit/llm/test_litellm_adapter.py -x` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | LLM-03 | unit | `uv run pytest tests/unit/llm/test_fallback_chain.py -x` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | LLM-02 | unit | `uv run pytest tests/unit/llm/test_model_router.py -x` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 1 | LLM-04, LLM-05 | unit | `uv run pytest tests/unit/llm/test_cost_tracker.py -x` | ❌ W0 | ⬜ pending |
| 04-02-03 | 02 | 1 | LLM-06 | unit | `uv run pytest tests/unit/llm/test_budget_manager.py -x` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | LLM-07 | integration | `uv run pytest tests/integration/llm/test_streaming.py -x` | ❌ W0 | ⬜ pending |
| 04-03-02 | 03 | 2 | LLM-08 | integration | `uv run pytest tests/integration/llm/test_cli_agent_bridge.py -x` | ❌ W0 | ⬜ pending |

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

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
