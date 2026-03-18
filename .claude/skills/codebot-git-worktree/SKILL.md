---
skill: codebot-git-worktree
title: "CodeBot Git Operations & Worktree Isolation"
description: >
  How to work with CodeBot's git operations layer — repository management,
  worktree pool isolation for agents, branch strategy, commit conventions,
  PR creation, experiment branches, and multi-repo coordination.
tags:
  - git
  - worktree
  - branching
  - pull-requests
  - agent-isolation
  - multi-repo
version: "1.0"
project: CodeBot
---

# CodeBot Git Operations & Worktree Isolation

## Overview

CodeBot isolates every coding agent in its own git worktree so multiple agents
can work on the same repository simultaneously without conflicts. The git
subsystem lives at:

```
apps/server/src/codebot/git/
  __init__.py
  repository.py      # Repository management (init, clone, import)
  worktree.py         # Worktree pool management
  branch.py           # Branch naming & protection strategy
  commit.py           # Commit creation & message conventions
  pr.py               # Pull request creation & management
```

Supporting modules:

- `apps/server/src/codebot/agents/github_agent.py` — high-level GitHub
  operations (repo creation/import, branch protection, CI/CD scaffold,
  project board setup).
- `apps/server/src/codebot/api/routes/github_integration.py` — REST
  endpoints exposing GitHub operations to the dashboard and CLI.
- Dashboard components: `apps/dashboard/src/components/github/`
  (`GitHubPanel.tsx`, `PRViewer.tsx`, `ActionsStatus.tsx`).

Runtime workspace (gitignored):

```
workspace/
  projects/       # Generated project directories
  worktrees/      # Git worktree pool
  checkpoints/    # Pipeline checkpoints
  artifacts/      # Build artifacts
  logs/           # Agent execution logs
```

Key dependency: **GitPython >= 3.1.43** (`gitpython` in `pyproject.toml`).

Tech requirements: Python 3.12+, strict mypy, ruff linting, async-first.

---

## 1. Repository Management

`repository.py` handles init, clone, and import operations.

### Patterns

```python
from codebot.git.repository import RepositoryManager

repo_mgr = RepositoryManager(workspace_root="workspace/projects")

# Initialize a new repository
repo = await repo_mgr.init(project_id="proj-abc", name="my-app")

# Clone an existing repository
repo = await repo_mgr.clone(
    url="https://github.com/org/repo.git",
    project_id="proj-abc",
    branch="main",
)

# Import from local path (brownfield / inflight projects)
repo = await repo_mgr.import_local(
    path="/path/to/existing",
    project_id="proj-abc",
)
```

### GitHub Agent Repository Operations

The `github_agent.py` provides higher-level orchestration:

- **Repository creation** — creates the remote repo on GitHub, sets
  description, topics, visibility.
- **Repository import** — forks or mirrors an existing repo.
- **Branch protection** — applies rulesets to `main` (require PR, status
  checks, no force push).
- **CI/CD scaffold** — generates `.github/workflows/ci.yml` and
  `release.yml`.
- **Project board setup** — creates a GitHub Project board linked to the repo.

---

## 2. Worktree Pool Management

`worktree.py` manages a pool of pre-provisioned git worktrees so agents
get an isolated working directory instantly.

### Lifecycle

1. **Provision** — at project start, the pool creates N worktrees under
   `workspace/worktrees/<project_id>/`.
2. **Allocate** — when an agent needs to write code, it requests a worktree.
   The pool assigns one, checking it out to the agent's feature branch.
3. **Release** — when the agent finishes (commit + PR or discard), the
   worktree is cleaned and returned to the pool.
4. **Cleanup** — on project completion or timeout, all worktrees are pruned.

### Patterns

```python
from codebot.git.worktree import WorktreePool

pool = WorktreePool(repo=repo, pool_dir="workspace/worktrees/proj-abc")

# Pre-provision worktrees (called once per project)
await pool.provision(count=6)

# Allocate a worktree for an agent
wt = await pool.allocate(
    agent_id="frontend-dev-01",
    branch="feature/PROJ-42-user-auth",
)
# wt.path  -> absolute filesystem path for the agent to work in
# wt.branch -> the checked-out branch

# Release when done
await pool.release(wt)

# Full cleanup
await pool.cleanup()
```

### Why Worktrees

- Each agent gets its own filesystem — no lock contention on index/HEAD.
- Agents can run builds, tests, linters inside their worktree independently.
- Merges happen via PRs, not direct pushes to shared branches.

---

## 3. Branch Strategy

`branch.py` defines naming conventions, protection rules, and branch
lifecycle.

### Naming Conventions

| Pattern | Usage |
|---|---|
| `main` | Protected production branch |
| `develop` | Integration branch (optional) |
| `feature/<TASK-ID>-<slug>` | Agent feature work |
| `fix/<TASK-ID>-<slug>` | Bug fixes |
| `experiment/<N>` | ExperimentLoopNode branches |
| `release/<semver>` | Release branches |
| `agent/<agent-id>/<task-id>` | Alternative per-agent namespace |

### Protection Rules

Applied by the GitHub Agent:

- `main`: require PR with at least 1 approval, require status checks
  (CI green), no force push, no direct commits.
- `develop` (if used): require PR, require CI.
- Feature branches: no restrictions (agents push freely).

### Branch Lifecycle

1. Agent receives task assignment.
2. `branch.py` creates feature branch from `main` (or `develop`).
3. Agent works in its worktree on that branch.
4. On completion, a PR is created targeting `main`.
5. After merge, the feature branch is deleted.

---

## 4. Commit Management

`commit.py` handles atomic commits with conventional messages.

### Message Convention

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `ci`,
`style`, `build`.

Example:
```
feat(auth): add JWT refresh token rotation

Implements automatic token rotation on refresh. Tokens are
single-use and invalidated after exchange.

Refs: PROJ-42
Agent: backend-dev-01
```

### Patterns

```python
from codebot.git.commit import CommitManager

cm = CommitManager(worktree=wt)

# Stage and commit atomically
await cm.commit(
    message="feat(auth): add JWT refresh token rotation",
    paths=["src/auth/tokens.py", "tests/test_tokens.py"],
    agent_id="backend-dev-01",
    task_id="PROJ-42",
)
```

### Commit Signing

When configured, commits are signed with GPG or SSH keys to provide
provenance. Agent-authored commits include an `Agent:` trailer for
traceability.

---

## 5. PR Creation and Management

`pr.py` creates and manages pull requests via the GitHub API.

### Patterns

```python
from codebot.git.pr import PRManager

pr_mgr = PRManager(repo=repo, github_token=token)

pr = await pr_mgr.create(
    branch="feature/PROJ-42-user-auth",
    target="main",
    title="feat(auth): add JWT refresh token rotation",
    body="## Changes\n- Refresh token rotation\n- Single-use tokens\n\nCloses PROJ-42",
    labels=["feature", "auth"],
    reviewers=["code-reviewer-agent"],
    draft=False,
)

# Check PR status
status = await pr_mgr.get_status(pr.number)

# Merge when checks pass
await pr_mgr.merge(pr.number, strategy="squash")
```

### PR Body

Auto-generated PR descriptions include:

- Summary of changes (from commit messages).
- Files changed with categorization.
- Test results summary.
- Security scan results (if available).
- Link to the originating task.

### Dashboard Integration

`apps/dashboard/src/components/github/PRViewer.tsx` renders PR details,
diff, review comments, and merge status in the web UI.

---

## 6. Agent-to-Worktree Assignment

The orchestrator assigns agents to worktrees through the pool:

1. **Task scheduler** (`core/task_scheduler.py`) assigns a task to an agent.
2. **Orchestrator** calls `pool.allocate(agent_id, branch)`.
3. The agent receives `wt.path` as its working directory.
4. All file reads/writes by the agent are scoped to that path.
5. On task completion, the agent commits, creates a PR, and the orchestrator
   calls `pool.release(wt)`.

Multiple agents can work on the same repo simultaneously because each has
its own worktree with an independent branch.

---

## 7. Experiment Branch Management

The `ExperimentLoopNode` (in `graph/loop.py`) uses git branches for
keep/discard experiment semantics.

### Flow

1. **Start experiment** — create branch `experiment/<N>` from current state.
2. **Run experiment** — agent implements the experimental approach in the
   worktree checked out to `experiment/<N>`.
3. **Evaluate** — run tests, benchmarks, or quality checks.
4. **Keep** — if metrics improved, merge `experiment/<N>` back into the
   source branch.
5. **Discard** — if metrics did not improve, delete `experiment/<N>` and
   restore the worktree to the source branch.

```python
# Pseudocode inside ExperimentLoopNode
branch = f"experiment/{iteration}"
await git.checkout_new_branch(branch, from_ref=source_branch)

# ... agent performs work ...

if metrics_improved:
    await git.merge(branch, into=source_branch)
else:
    await git.checkout(source_branch)
    await git.delete_branch(branch)
```

This pattern allows safe experimentation — the source branch is never
modified until an experiment is proven.

---

## 8. Multi-Repo Coordination

CodeBot supports multi-repository architectures (monorepo, polyrepo,
microservices). The git layer coordinates operations across repos.

### Patterns

- **Cross-repo dependency tracking** — when Agent A modifies a shared
  library in repo X, the system identifies downstream repos Y and Z that
  depend on it and schedules update tasks.
- **Coordinated branching** — feature branches with the same task ID are
  created across all affected repos.
- **Coordinated PRs** — PRs in downstream repos reference the upstream PR.
- **Merge ordering** — upstream repos are merged first; downstream repos
  merge only after upstream CI passes.

### Configuration

Multi-repo structure is defined during the Planning phase:

```yaml
repositories:
  - name: api-service
    url: https://github.com/org/api-service
    role: backend
  - name: web-app
    url: https://github.com/org/web-app
    role: frontend
    depends_on: [api-service]
  - name: shared-lib
    url: https://github.com/org/shared-lib
    role: library
```

Each repo gets its own `RepositoryManager`, `WorktreePool`, and set of
feature branches.

---

## 9. Conflict Detection and Resolution

### Prevention (Primary Strategy)

- Worktree isolation ensures agents never touch the same index.
- Task scheduler avoids assigning overlapping file scopes to parallel agents.
- Feature branches are short-lived to minimize drift.

### Detection

- Before PR creation, `branch.py` checks for merge conflicts with the
  target branch.
- The collaboration module (`collaboration/conflict_resolver.py`) detects
  real-time conflicts when humans edit files an agent is also modifying.

### Resolution

- **Automatic** — for non-overlapping changes, standard git merge resolves.
- **Agent-assisted** — when conflicts involve generated code, the Debugger
  agent is assigned to resolve them.
- **Human-in-the-loop** — the dashboard `ConflictResolver.tsx` component
  presents conflicts for manual resolution at phase gates.

---

## 10. Testing Git Operations

Tests live in `apps/server/tests/` with the standard project layout:

```
apps/server/tests/
  unit/          # Unit tests (mocked git)
  integration/   # Integration tests (real git repos)
  e2e/           # End-to-end tests
```

### Unit Testing

Mock `gitpython` objects to test branch naming, commit message formatting,
PR body generation, and pool allocation logic without touching the
filesystem.

```python
import pytest
from unittest.mock import AsyncMock
from codebot.git.worktree import WorktreePool

@pytest.mark.asyncio
async def test_allocate_assigns_unique_worktree():
    pool = WorktreePool(repo=mock_repo, pool_dir="/tmp/wt")
    await pool.provision(count=3)
    wt1 = await pool.allocate(agent_id="a1", branch="feature/x")
    wt2 = await pool.allocate(agent_id="a2", branch="feature/y")
    assert wt1.path != wt2.path
```

### Integration Testing

Use temporary directories with real `git init` to verify worktree
creation, branch checkout, commit, and merge operations end-to-end.

### Key Test Scenarios

- Pool exhaustion (all worktrees allocated) raises or blocks.
- Double-release of a worktree is idempotent.
- Experiment branch cleanup removes all `experiment/*` branches.
- Multi-repo coordinated branch creation across 2+ repos.
- Conflict detection returns correct file list.
- Commit trailers (`Agent:`, `Refs:`) are present in commit metadata.
- PR body includes test results and security scan summary.

---

## Quick Reference

| Operation | Module | Entry Point |
|---|---|---|
| Init / clone / import repo | `git/repository.py` | `RepositoryManager` |
| Provision worktree pool | `git/worktree.py` | `WorktreePool.provision()` |
| Allocate worktree to agent | `git/worktree.py` | `WorktreePool.allocate()` |
| Release worktree | `git/worktree.py` | `WorktreePool.release()` |
| Create feature branch | `git/branch.py` | `BranchManager.create()` |
| Commit changes | `git/commit.py` | `CommitManager.commit()` |
| Create PR | `git/pr.py` | `PRManager.create()` |
| Merge PR | `git/pr.py` | `PRManager.merge()` |
| Experiment branch | `graph/loop.py` | `ExperimentLoopNode` |
| GitHub repo setup | `agents/github_agent.py` | `GitHubAgent` |
| GitHub REST routes | `api/routes/github_integration.py` | FastAPI router |
| Dashboard PR view | `dashboard/src/components/github/PRViewer.tsx` | React component |

All paths above are relative to `apps/server/src/codebot/` unless otherwise
noted.
