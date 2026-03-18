---
phase: 8
slug: security-pipeline-worktree-manager
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3+ with pytest-asyncio |
| **Config file** | `apps/server/pyproject.toml` |
| **Quick run command** | `uv run pytest tests/unit/ -x -q --timeout=30` |
| **Full suite command** | `uv run pytest --cov=codebot --cov-report=term-missing` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/unit/ -x -q --timeout=30`
- **After every plan wave:** Run `uv run pytest --cov=codebot --cov-report=term-missing`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | SECP-01 | unit | `uv run pytest tests/unit/test_security_semgrep.py -x` | Wave 0 | pending |
| 08-01-02 | 01 | 1 | SECP-02 | unit | `uv run pytest tests/unit/test_security_trivy.py -x` | Wave 0 | pending |
| 08-01-03 | 01 | 1 | SECP-03 | unit | `uv run pytest tests/unit/test_security_gitleaks.py -x` | Wave 0 | pending |
| 08-01-04 | 01 | 1 | SECP-04 | unit | `uv run pytest tests/unit/test_security_gate.py -x` | Wave 0 | pending |
| 08-01-05 | 01 | 1 | SECP-06 | unit | `uv run pytest tests/unit/test_allowlist.py -x` | Wave 0 | pending |
| 08-02-01 | 02 | 1 | WORK-01 | unit | `uv run pytest tests/unit/test_worktree_pool.py -x` | Wave 0 | pending |
| 08-02-02 | 02 | 1 | WORK-03 | unit | `uv run pytest tests/unit/test_port_allocator.py -x` | Wave 0 | pending |
| 08-02-03 | 02 | 1 | WORK-04 | unit | `uv run pytest tests/unit/test_branch_strategy.py -x` | Wave 0 | pending |
| 08-03-01 | 03 | 2 | SECP-05 | unit | `uv run pytest tests/unit/test_security_orchestrator.py -x` | Wave 0 | pending |
| 08-03-02 | 03 | 2 | SECP-05 | integration | `uv run pytest tests/integration/test_security_pipeline.py -x` | Wave 0 | pending |
| 08-04-01 | 04 | 2 | IMPL-06 | unit | `uv run pytest tests/unit/test_cli_agents.py -x` | Wave 0 | pending |
| 08-04-02 | 04 | 2 | IMPL-05, WORK-02 | integration | `uv run pytest tests/integration/test_parallel_worktrees.py tests/integration/test_worktree_docker.py -x` | Wave 0 | pending |

*Status: pending · green · red · flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_security_semgrep.py` — mock Semgrep CLI output, test JSON parsing and finding normalization
- [ ] `tests/unit/test_security_trivy.py` — mock Trivy CLI output, test vulnerability extraction
- [ ] `tests/unit/test_security_gitleaks.py` — mock Gitleaks CLI output, test secret finding creation
- [ ] `tests/unit/test_security_gate.py` — test threshold evaluation logic for pass/fail/warn
- [ ] `tests/unit/test_allowlist.py` — test allowlist validation for pip requirements and package.json
- [ ] `tests/unit/test_worktree_pool.py` — test pool acquire/release lifecycle with overflow
- [ ] `tests/unit/test_port_allocator.py` — test dynamic port allocation and release
- [ ] `tests/unit/test_branch_strategy.py` — test branch naming, merge strategies, conflict detection
- [ ] `tests/unit/test_cli_agents.py` — test adapter command building, env setup, output parsing
- [ ] `tests/integration/test_security_pipeline.py` — end-to-end SecurityOrchestrator scan with mocked CLIs
- [ ] `tests/integration/test_worktree_docker.py` — worktree + Docker profile integration
- [ ] `tests/integration/test_parallel_worktrees.py` — multiple agents in parallel worktrees
- [ ] `tests/conftest.py` — update with security fixtures (mock subprocess), worktree fixtures (temp git repos)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Trivy DB download on first run | SECP-02 | Requires network + real Trivy binary | Run `trivy filesystem --download-db-only` and verify cache created |
| CLI agent binary detection | IMPL-06 | Requires real CLI tools installed | Verify `which claude`, `which codex`, `which gemini` detection works |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
