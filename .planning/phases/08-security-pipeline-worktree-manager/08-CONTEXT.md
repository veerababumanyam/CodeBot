# Phase 8: Security Pipeline + Worktree Manager - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase adds two critical infrastructure layers: (1) a security scanning cascade that runs Semgrep, Trivy, and Gitleaks on every code generation output with quality gates that block pipeline advancement on critical/high findings, and (2) a worktree isolation system that gives each coding agent its own git worktree with dynamic port allocation to prevent conflicts. Also includes CLI agent adapters for delegating to Claude Code, Codex, and Gemini, plus SOC 2 compliance checking and immutable audit logging.

</domain>

<decisions>
## Implementation Decisions

### Security Scanner Configuration
- Semgrep + Gitleaks run always; Trivy runs only for Docker/dependency contexts (minimizes scan time)
- Unified SecurityFinding Pydantic model with severity, scanner source, location, description, and CWE ID
- YAML-based dependency allowlist per project type with packages.allow + packages.deny using glob patterns
- All scanners run in parallel via asyncio.TaskGroup, findings merged after completion

### Worktree Isolation & Port Management
- WorktreePool with max capacity — pre-creates N worktrees, agents check out/check in, auto-cleanup on completion
- Dynamic port allocation with range (10000-20000) — each worktree gets allocated ports tracked in pool
- Agent-scoped branch strategy: `codebot/{agent-type}/{task-id}` pattern, merged to main via PR
- Maximum 4 concurrent worktrees — balances parallelism vs resource pressure

### SOC 2 Compliance & Audit Logging
- TSC criteria enforcement: CC6.1 (access control), CC7.2 (change management), CC8.1 (infrastructure)
- SHA-256 content hashing per audit entry — each entry includes hash of previous entry for chain integrity
- SOC 2 compliance is opt-in per pipeline config: `compliance.soc2.enabled: true` in pipeline YAML
- CLIAgentRunner common interface — subprocess wrapper with stdout/stderr capture, timeout, exit code handling

### Claude's Discretion
- Internal scanner adapter implementation details
- Worktree directory naming and cleanup timing
- Audit log storage format (JSON lines vs structured DB records)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `apps/server/src/codebot/db/models/security.py` — existing security ORM model
- `apps/server/src/codebot/db/models/event.py` — event tracking with compliance fields
- `apps/server/src/codebot/db/models/user.py` — user auth with audit trail
- `apps/server/src/codebot/pipeline/` — pipeline module with gates, activities, workflows
- `apps/server/src/codebot/agents/` — 5 concrete agents from Phase 7

### Established Patterns
- Pydantic v2 with frozen=True ConfigDict for immutable models
- Dataclasses with slots=True and kw_only=True for DTOs
- asyncio.TaskGroup for parallel execution
- YAML configuration files in configs/
- Subprocess execution pattern in TestRunner from Phase 7

### Integration Points
- Security module: `apps/server/src/codebot/security/` (new directory)
- Worktree module: `apps/server/src/codebot/worktree/` (new directory)
- CLI agents: `apps/server/src/codebot/cli_agents/` (new directory)
- Pipeline gates integrate with SecurityOrchestrator findings
- SOC 2 checker runs as fan-out within SecurityOrchestrator

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches based on research and existing architecture.

</specifics>

<deferred>
## Deferred Ideas

- Full SAST/DAST pipeline with SonarQube integration — deferred to post-v1.0
- Container image scanning in CI/CD — deferred to deployment phase
- License compliance scanning with ScanCode/ORT — deferred to post-v1.0

</deferred>
