# Phase 8: Security Pipeline + Worktree Manager - Research

**Researched:** 2026-03-18
**Domain:** Security scanning automation, git worktree isolation, dependency supply chain, CLI agent bridging
**Confidence:** HIGH

## Summary

Phase 8 adds two critical subsystems to CodeBot: (1) a security scanning pipeline that runs Semgrep, Trivy, and Gitleaks on every code generation output with quality gates that block pipeline advancement on critical/high findings, and (2) a worktree management system that gives each coding agent its own isolated git worktree with per-worktree Docker profiles and dynamic port allocation to prevent resource contention during parallel execution.

The security pipeline is architecturally straightforward -- it wraps three well-documented CLI tools (Semgrep, Trivy, Gitleaks) behind an async Python orchestrator that runs them in parallel via `asyncio.TaskGroup`, normalizes their JSON outputs into the existing `SecurityFinding` ORM model, and feeds results through a configurable `SecurityGate`. The project already has the `SecurityFinding` database model, `Severity` and `FindingStatus` enums, and a `worktree_path` field on the `Agent` ORM model -- these were built in Phase 1.

The worktree manager requires more custom engineering (flagged as a concern in STATE.md). GitPython 3.1.46 lacks a dedicated worktree API, so worktree operations must use `repo.git.worktree(...)` command passthrough or raw `asyncio.create_subprocess_exec` for async operations. The key challenge is full-stack isolation: worktrees share the same Docker daemon, database, and cache directories, so per-worktree Docker Compose profiles and the `ephemeral-port-reserve` library are needed for dynamic port allocation. The dependency allowlist requirement (SECP-06) is addressed by combining hash-pinned requirements files with a curated allowlist validated before `pip install` or `npm install` runs in agent worktrees.

**Primary recommendation:** Build security scanners as independent async adapters behind a `SecurityOrchestrator`, and build the worktree manager as a pooled resource with `asyncio.Queue` -- both patterns align with the existing codebase's async-first approach and the detailed designs in SYSTEM_DESIGN.md sections 7 and 8.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SECP-01 | Semgrep runs static analysis with custom rules for AI-generated code patterns | SASTRunner wrapping Semgrep CLI with `--json` output, parsed into SecurityFinding; rule packs p/security-audit, p/owasp-top-ten, p/cwe-top-25 plus custom .semgrep.yml |
| SECP-02 | Trivy scans container images and dependencies for known vulnerabilities | DependencyScanner wrapping `trivy filesystem --format json --scanners vuln,secret,misconfig`; parses Results[].Vulnerabilities array |
| SECP-03 | Gitleaks detects secrets, API keys, and credentials in generated code | SecretScanner wrapping `gitleaks detect --source <path> --report-format json --report-path /dev/stdout --no-git`; all secrets treated as CRITICAL severity |
| SECP-04 | Quality gates block advancement when critical/high vulnerabilities found | SecurityGate with configurable SecurityThresholds (max_critical=0, max_high=0); evaluates aggregated SecurityReport |
| SECP-05 | Security scanning runs after every code generation step, not just at S6 gate | SecurityOrchestrator.scan() callable from any pipeline stage; hook into agent task completion via EventBus |
| SECP-06 | Dependency allowlist prevents hallucinated/malicious package installation | AllowlistValidator with hash-pinned requirements + curated package name lists; runs before pip/npm install in worktrees |
| WORK-01 | Worktree lifecycle manager creates/cleans git worktrees per coding agent | WorktreePool with asyncio.Queue, acquire/release pattern, pool_size=5 default, overflow creation |
| WORK-02 | Per-worktree Docker Compose profiles for runtime isolation | docker-compose.worktree.yml template with profile per agent; env-file per worktree for service customization |
| WORK-03 | Dynamic port allocation prevents conflicts between parallel agents | ephemeral-port-reserve library for race-free port allocation; PortAllocator tracks assigned ports per worktree |
| WORK-04 | Sequential merge strategy with conflict detection for worktree results | BranchStrategy with sequential merge, AI-assisted conflict resolution via LLM, octopus and squash alternatives |
| IMPL-05 | S5 agents execute in parallel in isolated git worktrees | CLIAgentRunner uses WorktreePool.acquire() to provision worktrees before agent execution |
| IMPL-06 | CLI agent integration delegates coding to Claude Code, Codex CLI, or Gemini CLI | CLIAgentRunner with adapter pattern (ClaudeCodeAdapter, CodexAdapter, GeminiCLIAdapter); subprocess management via SessionManager |
| CMPL-01 | SOC 2 compliance checker evaluates generated code against Trust Service Criteria | SOC2ComplianceChecker with file-system + pattern-based TSC evaluation; produces ScanFinding with tool="soc2-compliance" |
| CMPL-02 | Immutable audit logging with tamper-detection content hashing | ImmutableAuditLogger wrapping AuditLog ORM; SHA-256 hashing; PostgreSQL rules prevent UPDATE/DELETE |
| CMPL-03 | Compliance evidence collection and export for auditor review | ComplianceEvidenceCollector exports structured JSON evidence packages per TSC category |
| CMPL-04 | COMPLIANCE_VIOLATION finding type in SecurityReport | New FindingType enum value; SecurityGate can evaluate compliance findings via require_compliance_pass flag |
</phase_requirements>

## SOC 2 Compliance Integration

### Trust Service Criteria Mapping to CodeBot Subsystems

| TSC | Criteria | CodeBot Subsystem | Check Method |
|-----|----------|-------------------|--------------|
| CC6 | Logical Access Controls | Auth middleware, RBAC enforcement | Pattern detection for auth decorators, RBAC checks |
| CC7 | System Operations | Health checks, structured logging | File/pattern inspection for logging and monitoring |
| CC8 | Change Management | DB migrations, version control | File existence checks for migration scripts, git history |
| CC9 | Risk Mitigation | Input validation, dependency pinning, rate limiting | Pattern + file detection |
| A1 | Availability | Health endpoints, error handling | Endpoint detection, error handler patterns |
| PI1 | Processing Integrity | Data validation, checksums | Input validation pattern detection |
| C1 | Confidentiality | Secrets externalized, TLS config | Delegates to Gitleaks results + TLS config inspection |
| P1 | Privacy | Data retention policies, PII handling | Pattern detection for PII types, retention configs |

### Dual-Level Compliance Architecture

1. **Platform level** (CodeBot itself): Immutable audit logs with SHA-256 content hashing, event-sourced pipeline execution records stored in PostgreSQL, compliance evidence collection and JSON export for auditor review. Database-level immutability enforced via PostgreSQL rules.

2. **Generated code level** (code agents produce): SOC2ComplianceChecker evaluates generated application code against TSC patterns. File-system and regex-based checks identify missing security controls. Findings flow into the standard SecurityReport pipeline as `COMPLIANCE_VIOLATION` type.

### SOC2ComplianceChecker Design

The checker is file-system + pattern-based (not an external CLI tool). It:
- Reads TSC rule definitions from `configs/security/compliance/soc2.yaml`
- Scans the project directory for files and patterns matching each TSC category
- Produces `ScanFinding` objects with `tool="soc2-compliance"` and `finding_type=COMPLIANCE_VIOLATION`
- Runs as an optional 4th scanner in the SecurityOrchestrator parallel fan-out

### Immutable Audit Logging

The `ImmutableAuditLogger` helper:
- Computes SHA-256 hash of the log entry payload before insertion
- Stores hash in `content_hash` column on `audit_logs`
- Tags entries with `compliance_framework` and `evidence_type`
- Sets `retention_until` based on framework requirements (SOC 2 = 1 year minimum)
- Provides `verify()` method to detect tampered entries by recomputing hashes

### Evidence Collection

The `ComplianceEvidenceCollector`:
- Gathers audit log entries, scan reports, and pipeline execution records
- Groups evidence by TSC category
- Exports structured JSON packages suitable for SOC 2 Type II auditor review
- Supports date range filtering for audit periods

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| semgrep | >=1.155.0 | SAST - static analysis with pattern matching | Industry standard for AI-generated code scanning; 3000+ community rules; JSON output; Python-native install |
| trivy | >=0.69.3 | SCA/container scanning for known CVEs | Aqua Security maintained; scans filesystem, containers, IaC; JSON/SARIF output; zero-config dependency detection |
| gitleaks | >=8.28.0 | Secret detection in source code | De facto standard; 25K+ GitHub stars; composite rules for reduced false positives; JSON output; pre-commit integration |
| GitPython | >=3.1.46 | Git operations including worktree management | Only mature Python git library; supports worktree via command passthrough; can open linked worktrees as Repo objects |
| ephemeral-port-reserve | >=1.1.4 | Race-free dynamic port allocation | Solves Docker port 0 race condition; TIME_WAIT trick ensures reserved ports stay available for subprocesses |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| safety | >=3.0 | Python dependency vulnerability checking | Complementary to Trivy for Python-specific vulnerability database |
| pip-audit | >=2.7.0 | Python package audit against PyPI advisory DB | Alternative/complement to Trivy for pip-specific packages |
| asyncio (stdlib) | Python 3.12+ | Async subprocess management for scanner CLIs | All scanner invocations use asyncio.create_subprocess_exec |
| pydantic | >=2.9.0 | Scanner config and finding schemas | Already in project; used for SecurityConfig, ScanResult, SecurityReport models |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Semgrep OSS | CodeQL | CodeQL is GitHub-specific, requires Actions; Semgrep runs locally with broader language support |
| Gitleaks | Betterleaks (by same author) | Betterleaks is brand new (March 2026), drop-in compatible but less battle-tested; monitor for maturity |
| GitPython + subprocess | pygit2 (libgit2 bindings) | pygit2 is faster but has no worktree API either; GitPython is already a project dependency |
| ephemeral-port-reserve | socket bind(0) trick | bind(0) has race conditions in parallel scenarios; ephemeral-port-reserve solves this explicitly |
| Custom allowlist | pip --require-hashes only | Hashes alone do not prevent typosquatting; need name-level allowlist + hash verification |

**Installation:**

```bash
# Python dependencies (add to pyproject.toml)
uv add semgrep gitpython ephemeral-port-reserve

# System tools (must be available on PATH)
brew install trivy gitleaks  # or via Docker images
```

## Architecture Patterns

### Recommended Project Structure

```
apps/server/src/codebot/
  security/
    __init__.py
    orchestrator.py      # SecurityOrchestrator - coordinates all scanners
    scanners/
      __init__.py
      base.py            # BaseScanner ABC with scan() -> ScanResult
      semgrep.py         # SASTRunner - Semgrep integration
      trivy.py           # DependencyScanner - Trivy integration
      gitleaks.py        # SecretScanner - Gitleaks integration
      allowlist.py       # AllowlistValidator - dependency name/hash checking
    gate.py              # SecurityGate - pass/fail evaluation
    models.py            # Pydantic schemas: SecurityConfig, ScanResult, SecurityReport, SecurityThresholds
    config.py            # Default configs, rule set paths, threshold presets
  worktree/
    __init__.py
    pool.py              # WorktreePool - asyncio.Queue-based pool management
    manager.py           # WorktreeManager - lifecycle (provision, execute, merge, cleanup)
    branch_strategy.py   # BranchStrategy - naming, merge strategies, conflict resolution
    commit_manager.py    # CommitManager - structured commits with agent attribution
    port_allocator.py    # PortAllocator - dynamic port allocation via ephemeral-port-reserve
    models.py            # Pydantic schemas: WorktreeInfo, BranchConfig, MergeResult
  cli_agents/
    __init__.py
    runner.py            # CLIAgentRunner - unified interface for CLI agent execution
    adapters/
      __init__.py
      base.py            # BaseCLIAdapter ABC
      claude_code.py     # ClaudeCodeAdapter
      codex.py           # CodexAdapter
      gemini.py          # GeminiCLIAdapter
    session.py           # SessionManager - subprocess lifecycle
    output_parser.py     # OutputParser - extracts structured data from CLI output
    health.py            # HealthChecker - monitors subprocess health
configs/
  security/
    semgrep/
      ai-generated.yml   # Custom rules for AI code patterns
      codebot.yml        # CodeBot-specific rules
    gitleaks.toml        # Gitleaks configuration with project allowlist
    thresholds.yaml      # Security gate threshold presets
    allowlist.yaml       # Approved dependency names and hashes
```

### Pattern 1: Scanner Adapter Pattern

**What:** Each security scanner is wrapped in a `BaseScanner` adapter that normalizes its output to a common `ScanResult` containing `List[SecurityFinding]`.
**When to use:** For every scanner integration (Semgrep, Trivy, Gitleaks).
**Example:**

```python
# Source: SYSTEM_DESIGN.md Section 8 + verified Semgrep/Trivy/Gitleaks CLI docs
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import asyncio
import json

@dataclass(slots=True, kw_only=True)
class ScanResult:
    scanner: str
    findings: list[SecurityFinding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_ms: int = 0

class BaseScanner(ABC):
    """Abstract base for all security scanner adapters."""

    @abstractmethod
    async def scan(self, project_path: str) -> ScanResult:
        """Run the scanner and return normalized findings."""
        ...

    async def _run_cli(
        self, cmd: list[str], timeout: int = 300
    ) -> tuple[str, str, int]:
        """Run a CLI command asynchronously with timeout."""
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return stdout.decode(), stderr.decode(), proc.returncode or 0
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            raise
```

### Pattern 2: Worktree Pool with asyncio.Queue

**What:** Pre-created worktrees managed in an `asyncio.Queue` for quick acquisition; overflow worktrees created on demand when pool is exhausted.
**When to use:** Every time a coding agent needs an isolated working directory.
**Example:**

```python
# Source: SYSTEM_DESIGN.md Section 7.4 + GitPython docs
import asyncio
from uuid import uuid4

class WorktreePool:
    def __init__(self, repo_path: str, pool_size: int = 5):
        self.repo_path = repo_path
        self.pool_size = pool_size
        self.available: asyncio.Queue[WorktreeInfo] = asyncio.Queue()
        self.active: dict[str, WorktreeInfo] = {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Pre-create worktrees for the pool."""
        for i in range(self.pool_size):
            wt = await self._create_worktree(f"pool-{i}")
            await self.available.put(wt)

    async def acquire(self, agent_id: str, branch_name: str) -> WorktreeInfo:
        """Acquire a worktree, creating overflow if pool exhausted."""
        try:
            wt = self.available.get_nowait()
        except asyncio.QueueEmpty:
            wt = await self._create_worktree(f"overflow-{uuid4().hex[:6]}")

        # Checkout agent's branch
        await self._run_git(wt.path, f"checkout -b {branch_name}")
        wt.branch = branch_name
        wt.agent_id = agent_id

        async with self._lock:
            self.active[wt.id] = wt
        return wt

    async def release(self, worktree: WorktreeInfo) -> None:
        """Clean and return worktree to pool, or destroy if overflow."""
        async with self._lock:
            self.active.pop(worktree.id, None)

        await self._run_git(worktree.path, "checkout main")
        await self._run_git(worktree.path, "clean -fd")
        await self._run_git(worktree.path, "reset --hard HEAD")

        if self.available.qsize() < self.pool_size:
            await self.available.put(worktree)
        else:
            await self._destroy_worktree(worktree)
```

### Pattern 3: Security Orchestrator with Parallel Fan-Out

**What:** `SecurityOrchestrator` runs all scanners concurrently via `asyncio.TaskGroup`, aggregates and deduplicates findings, then evaluates the `SecurityGate`.
**When to use:** After every code generation step (SECP-05) and at S6 quality gate.
**Example:**

```python
# Source: SYSTEM_DESIGN.md Section 8.3
async def scan(self, project_path: str) -> SecurityReport:
    findings: list[SecurityFinding] = []
    errors: list[ScanError] = []

    async with asyncio.TaskGroup() as tg:
        sast_task = tg.create_task(self.sast.scan(project_path))
        deps_task = tg.create_task(self.deps.scan(project_path))
        secrets_task = tg.create_task(self.secrets.scan(project_path))

    for name, task in [("sast", sast_task), ("deps", deps_task), ("secrets", secrets_task)]:
        result = task.result()
        findings.extend(result.findings)
        errors.extend(ScanError(scanner=name, error=e) for e in result.errors)

    deduplicated = self._deduplicate(findings)
    report = SecurityReport(
        findings=deduplicated,
        errors=errors,
        summary=self._build_summary(deduplicated),
    )
    report.gate_result = self.gate.evaluate(report)
    return report
```

### Pattern 4: CLI Agent Adapter with Worktree Integration

**What:** Each CLI coding tool (Claude Code, Codex, Gemini) gets an adapter that builds the correct command and environment for execution within a worktree.
**When to use:** When delegating coding tasks to external CLI agents (IMPL-06).
**Example:**

```python
# Source: SYSTEM_DESIGN.md Section 4
class ClaudeCodeAdapter(BaseCLIAdapter):
    binary = "claude"

    def build_command(self, task: CLITask, worktree_path: str) -> list[str]:
        cmd = [
            self.binary,
            "--print",  # non-interactive mode
            "--output-format", "json",
            "--allowedTools", ",".join(task.allowed_tools),
            "--max-tokens", str(task.max_tokens),
        ]
        if task.files_context:
            for f in task.files_context:
                cmd.extend(["--file", f])
        cmd.append(task.prompt)
        return cmd

    def build_env(
        self, worktree_path: str, ports: dict[str, int]
    ) -> dict[str, str]:
        import os
        env = os.environ.copy()
        env["HOME"] = worktree_path  # isolate config
        env["CODEBOT_WORKTREE"] = worktree_path
        for service, port in ports.items():
            env[f"PORT_{service.upper()}"] = str(port)
        return env
```

### Pattern 5: Dependency Allowlist Validation

**What:** Before any `pip install` or `npm install` runs in an agent worktree, the `AllowlistValidator` checks package names against a curated allowlist and verifies hashes.
**When to use:** Whenever an agent attempts to install dependencies (SECP-06).
**Example:**

```python
# Source: pip secure installs docs + safety CLI patterns
@dataclass(slots=True, kw_only=True)
class AllowlistConfig:
    python_packages: set[str]       # approved package names
    npm_packages: set[str]          # approved npm package names
    require_hashes: bool = True     # enforce --require-hashes
    block_unknown: bool = True      # block packages not in allowlist

class AllowlistValidator:
    def __init__(self, config: AllowlistConfig):
        self.config = config

    async def validate_requirements(self, requirements_path: str) -> list[str]:
        """Check requirements.txt against allowlist. Returns violations."""
        violations = []
        with open(requirements_path) as f:
            for line in f:
                pkg_name = self._extract_package_name(line.strip())
                if pkg_name and pkg_name.lower() not in self.config.python_packages:
                    violations.append(f"Package '{pkg_name}' not in allowlist")
        return violations

    async def validate_package_json(self, pkg_json_path: str) -> list[str]:
        """Check package.json dependencies against allowlist."""
        violations = []
        import json as json_mod
        with open(pkg_json_path) as f:
            data = json_mod.load(f)
        for section in ("dependencies", "devDependencies"):
            for pkg_name in data.get(section, {}):
                if pkg_name not in self.config.npm_packages:
                    violations.append(f"NPM package '{pkg_name}' not in allowlist")
        return violations
```

### Anti-Patterns to Avoid

- **Running scanners sequentially:** All three scanners (Semgrep, Trivy, Gitleaks) are I/O-bound CLI subprocesses. Always run them in parallel via `asyncio.TaskGroup`. Sequential execution wastes 2-3x the time.
- **Sharing worktrees between agents:** Never let two agents use the same worktree. The entire point is isolation. Even "read-only" sharing creates race conditions with git index operations.
- **Using GitPython for async operations:** GitPython is synchronous and leaks resources in long-running processes. Use `asyncio.create_subprocess_exec` for all git worktree operations, reserving GitPython only for high-level Repo inspection.
- **Hardcoding port numbers:** Never assign fixed ports to agent worktrees. Use `ephemeral-port-reserve` or `socket.bind(('', 0))` for every service port.
- **Parsing scanner text output:** Always use `--json` or `--format json` flags. Text output parsing is fragile and breaks across versions.
- **Ignoring scanner exit codes:** Semgrep exits 1 when findings exist (not an error). Trivy exits 0 even with findings when using `--exit-code 0`. Gitleaks exits 1 when leaks found. Handle exit codes per-scanner, not generically.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Static analysis | Custom AST analysis | Semgrep with rule packs | 3000+ rules, OWASP Top 10 coverage, CWE mapping, active maintenance |
| Dependency CVE scanning | Custom CVE database lookup | Trivy filesystem scan | Continuously updated vuln DB, multi-language lockfile parsing |
| Secret detection | Regex pattern matching | Gitleaks with composite rules | 100+ built-in patterns, entropy detection, low false positive rate |
| Port allocation | Random port + retry | ephemeral-port-reserve | Race-free TIME_WAIT trick specifically designed for parallel subprocess scenarios |
| Git worktree CLI | Raw subprocess calls everywhere | Thin wrapper using asyncio.create_subprocess_exec | Testable, consistent error handling, timeout management |
| JSON output parsing | Ad-hoc field extraction | Pydantic model validation | Type-safe, version-resilient, automatic deserialization |
| Dependency allowlisting | Manual review | Allowlist YAML + hash verification | Prevents typosquatting, hallucinated packages, supply chain attacks |

**Key insight:** The security tools are mature, well-documented CLIs with JSON output. The value is in orchestration, normalization, and gate logic -- not in building scanning capabilities.

## Common Pitfalls

### Pitfall 1: Semgrep Exit Code Misinterpretation
**What goes wrong:** Treating Semgrep exit code 1 as a fatal error when it actually means "findings found."
**Why it happens:** Most CLI tools use exit code 1 for errors. Semgrep uses it to signal results.
**How to avoid:** Check `proc.returncode`: 0 = no findings, 1 = findings found (parse JSON), 2+ = actual error.
**Warning signs:** Scanner "fails" every time it runs, but JSON output is valid.

### Pitfall 2: Trivy Database Download on First Run
**What goes wrong:** First Trivy scan takes 2-5 minutes downloading the vulnerability database, causing timeouts.
**Why it happens:** Trivy needs to download its vuln DB before scanning. Subsequent runs use cache.
**How to avoid:** Run `trivy filesystem --download-db-only` during system initialization/startup. Set `--skip-db-update` on subsequent scans for speed. Or use `--cache-dir` to persist across runs.
**Warning signs:** First scan per fresh environment always times out.

### Pitfall 3: GitPython Resource Leaks in Long-Running Processes
**What goes wrong:** Memory and file descriptor leaks accumulate over time.
**Why it happens:** GitPython documentation explicitly warns it "is not suited for long-running processes (like daemons) as it tends to leak system resources."
**How to avoid:** Use `asyncio.create_subprocess_exec` for worktree operations instead of GitPython's API. Reserve GitPython for brief, bounded operations like reading repo status. Periodically call `gc.collect()` and `repo.close()`.
**Warning signs:** Increasing memory usage over time, "too many open files" errors.

### Pitfall 4: Worktree Lock Contention
**What goes wrong:** Git operations on worktrees block each other because they share the same `.git` directory.
**Why it happens:** Git uses file locks in `.git/` for index operations. Parallel worktree checkouts, commits, or branch operations can contend on these locks.
**How to avoid:** Serialize git operations that touch shared state (branch creation, fetch, gc). Only parallelize operations within individual worktrees (file reads/writes, local commits). Use `asyncio.Lock` around shared-repo operations.
**Warning signs:** "fatal: Unable to create '.git/index.lock'" errors during parallel agent execution.

### Pitfall 5: Docker Port Allocation Race
**What goes wrong:** Two agents try to bind the same port simultaneously; one fails to start its dev server.
**Why it happens:** Docker's built-in port 0 allocation has race conditions under parallel bind attempts.
**How to avoid:** Use `ephemeral-port-reserve` to reserve ports before Docker Compose starts. Pass reserved ports as environment variables to the compose profile.
**Warning signs:** "Address already in use" errors that appear intermittently during parallel agent runs.

### Pitfall 6: Gitleaks False Positives on Generated Code
**What goes wrong:** Gitleaks flags test fixtures, example configs, or base64-encoded content as secrets.
**Why it happens:** AI-generated code often contains realistic-looking test data, mock credentials, and sample configs.
**How to avoid:** Use a `.gitleaks.toml` config with path-based allowlists for test directories. Add `[allowlist]` entries for known patterns like `codebot_dev_key`. Use the `--redact` flag in reports.
**Warning signs:** High false positive rate in scan reports, especially in test files and fixture data.

### Pitfall 7: Worktree Cleanup Failures Leave Stale State
**What goes wrong:** Abruptly terminated agents leave worktrees in dirty state; subsequent pool acquisitions get contaminated worktrees.
**Why it happens:** Process crashes, timeouts, or OOM kills skip the `finally` cleanup block.
**How to avoid:** Implement a startup-time cleanup sweep that runs `git worktree prune` and force-removes any worktrees not tracked in the active pool. Add a periodic garbage collector.
**Warning signs:** "fatal: '<path>' is already checked out" errors when creating new worktrees.

## Code Examples

### Semgrep Scanner Implementation

```python
# Verified against Semgrep CLI docs and JSON output schema
class SASTRunner(BaseScanner):
    """Static analysis via Semgrep."""

    DEFAULT_CONFIGS = [
        "p/security-audit",
        "p/owasp-top-ten",
        "p/cwe-top-25",
    ]

    def __init__(self, custom_rules_dir: str | None = None):
        self.custom_rules_dir = custom_rules_dir

    async def scan(self, project_path: str) -> ScanResult:
        cmd = ["semgrep", "scan", "--json", "--no-git-ignore"]
        for config in self.DEFAULT_CONFIGS:
            cmd.extend(["--config", config])
        if self.custom_rules_dir:
            cmd.extend(["--config", self.custom_rules_dir])
        cmd.append(project_path)

        stdout, stderr, returncode = await self._run_cli(cmd, timeout=300)

        if returncode >= 2:
            return ScanResult(scanner="semgrep", errors=[f"Semgrep error: {stderr}"])

        # returncode 0 = no findings, 1 = findings found (both have valid JSON)
        data = json.loads(stdout)
        findings = []
        for result in data.get("results", []):
            findings.append(SecurityFinding(
                tool="semgrep",
                rule_id=result["check_id"],
                severity=self._map_severity(result["extra"]["severity"]),
                title=result["extra"]["message"],
                file_path=result["path"],
                line_start=result["start"]["line"],
                line_end=result["end"]["line"],
                code_snippet=result["extra"].get("lines", ""),
                cwe=result["extra"].get("metadata", {}).get("cwe", []),
                fix_recommendation=result["extra"].get("fix", ""),
            ))
        return ScanResult(scanner="semgrep", findings=findings)

    def _map_severity(self, semgrep_severity: str) -> Severity:
        mapping = {
            "ERROR": Severity.HIGH,
            "WARNING": Severity.MEDIUM,
            "INFO": Severity.LOW,
        }
        return mapping.get(semgrep_severity, Severity.INFO)
```

### Trivy Scanner Implementation

```python
# Verified against Trivy CLI docs and JSON output format
class DependencyScanner(BaseScanner):
    """Dependency and filesystem vulnerability scanning via Trivy."""

    async def scan(self, project_path: str) -> ScanResult:
        cmd = [
            "trivy", "filesystem",
            "--format", "json",
            "--scanners", "vuln,secret,misconfig",
            "--severity", "CRITICAL,HIGH,MEDIUM",
            "--skip-dirs", "node_modules,.git,.worktrees",
            project_path,
        ]
        stdout, stderr, returncode = await self._run_cli(cmd, timeout=600)

        if returncode != 0 and not stdout:
            return ScanResult(scanner="trivy", errors=[f"Trivy error: {stderr}"])

        data = json.loads(stdout)
        findings = []
        for target in data.get("Results", []):
            for vuln in target.get("Vulnerabilities", []):
                findings.append(SecurityFinding(
                    tool="trivy",
                    rule_id=vuln.get("VulnerabilityID", ""),
                    severity=Severity(vuln.get("Severity", "MEDIUM").upper()),
                    title=vuln.get("Title", vuln.get("VulnerabilityID", "")),
                    description=vuln.get("Description", ""),
                    file_path=target.get("Target", ""),
                    cve_id=vuln.get("VulnerabilityID"),
                    fix_recommendation=f"Update to {vuln.get('FixedVersion', 'N/A')}",
                ))
        return ScanResult(scanner="trivy", findings=findings)
```

### Gitleaks Scanner Implementation

```python
# Verified against Gitleaks v8.28.0 JSON output format
class SecretScanner(BaseScanner):
    """Secret detection via Gitleaks."""

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path

    async def scan(self, project_path: str) -> ScanResult:
        cmd = [
            "gitleaks", "detect",
            "--source", project_path,
            "--report-format", "json",
            "--report-path", "/dev/stdout",
            "--no-git",
            "--no-banner",
        ]
        if self.config_path:
            cmd.extend(["--config", self.config_path])

        stdout, stderr, returncode = await self._run_cli(cmd, timeout=120)

        findings = []
        # returncode 1 = leaks found; 0 = no leaks
        if returncode == 1 and stdout:
            leaks = json.loads(stdout)
            for leak in leaks:
                findings.append(SecurityFinding(
                    tool="gitleaks",
                    rule_id=leak["RuleID"],
                    severity=Severity.CRITICAL,  # secrets are always critical
                    title=f"Secret detected: {leak['Description']}",
                    file_path=leak["File"],
                    line_start=leak.get("StartLine", 0),
                    line_end=leak.get("EndLine", 0),
                    code_snippet=leak.get("Match", "")[:200],  # truncate
                    fix_recommendation=(
                        "Remove hardcoded secret. Use environment variables "
                        "or a secrets manager instead."
                    ),
                ))
        elif returncode > 1:
            return ScanResult(
                scanner="gitleaks", errors=[f"Gitleaks error: {stderr}"]
            )

        return ScanResult(scanner="gitleaks", findings=findings)
```

### Security Gate Implementation

```python
# Source: SYSTEM_DESIGN.md Section 8.8
@dataclass(slots=True, kw_only=True)
class SecurityThresholds:
    max_critical: int = 0      # zero tolerance
    max_high: int = 0          # zero tolerance
    max_medium: int = 5        # allow some
    max_low: int = 20          # allow many
    require_no_secrets: bool = True

@dataclass(slots=True, kw_only=True)
class GateResult:
    passed: bool
    reason: str = ""
    warnings: list[str] = field(default_factory=list)

class SecurityGate:
    def __init__(self, thresholds: SecurityThresholds):
        self.thresholds = thresholds

    def evaluate(self, report: SecurityReport) -> GateResult:
        summary = report.summary

        if summary.secrets_count > 0 and self.thresholds.require_no_secrets:
            return GateResult(passed=False, reason="Hardcoded secrets detected")

        if summary.critical_count > self.thresholds.max_critical:
            return GateResult(
                passed=False,
                reason=(
                    f"CRITICAL findings ({summary.critical_count}) "
                    f"exceed threshold ({self.thresholds.max_critical})"
                ),
            )

        if summary.high_count > self.thresholds.max_high:
            return GateResult(
                passed=False,
                reason=(
                    f"HIGH findings ({summary.high_count}) "
                    f"exceed threshold ({self.thresholds.max_high})"
                ),
            )

        warnings = []
        if summary.medium_count > self.thresholds.max_medium:
            warnings.append(
                f"MEDIUM findings ({summary.medium_count}) exceed recommendation"
            )

        return GateResult(passed=True, warnings=warnings)
```

### Dynamic Port Allocation

```python
# Source: ephemeral-port-reserve PyPI docs
from ephemeral_port_reserve import reserve

class PortAllocator:
    """Allocates unique ports for parallel agent worktrees."""

    def __init__(self) -> None:
        self._allocated: dict[str, dict[str, int]] = {}
        self._lock = asyncio.Lock()

    async def allocate(
        self, worktree_id: str, services: list[str]
    ) -> dict[str, int]:
        """Reserve ports for all services needed by a worktree."""
        ports = {}
        async with self._lock:
            for service in services:
                port = reserve()  # race-free port reservation
                ports[service] = port
            self._allocated[worktree_id] = ports
        return ports

    async def release(self, worktree_id: str) -> None:
        """Release port reservations for a worktree."""
        async with self._lock:
            self._allocated.pop(worktree_id, None)
        # Ports return to OS pool after TIME_WAIT expires (~60s on Linux)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Gitleaks regex-only rules | Gitleaks v8.28.0 composite rules | Late 2025 | Reduced false positives via proximity-based rule matching |
| Manual worktree management | Worktrunk / Superset IDE tooling | Jan-Mar 2026 | Ecosystem recognizes worktree isolation as standard pattern for parallel AI agents |
| Semgrep OSS standalone | Semgrep Community Edition 1.155+ | Ongoing | 3000+ rules, MCP server integration, broader language support |
| Single-tool scanning | Multi-tool orchestrated scanning | 2024-2025 | Industry standard is running SAST + SCA + secret detection in parallel |
| Docker port 0 allocation | ephemeral-port-reserve | Stable since 2020 | Eliminates race conditions that Docker's built-in allocation suffers from |
| Gitleaks by original maintainer | Betterleaks announced March 2026 | March 2026 | Original author lost control of gitleaks repo; Betterleaks is drop-in replacement but too new to adopt |

**Deprecated/outdated:**
- Bandit for Python security linting: Still useful but overlaps significantly with Semgrep's Python rules. Use Semgrep as primary, Bandit as optional complement.
- GitPython for async operations: Use subprocess-based approach instead. GitPython is synchronous and leaks resources.
- Docker Compose v1 syntax: Project already uses Compose Specification format. No `version:` key needed in new compose files.

## Open Questions

1. **Gitleaks vs Betterleaks stability**
   - What we know: Gitleaks original author launched Betterleaks (March 2026) as a drop-in replacement after losing admin control of the gitleaks repo. Gitleaks v8.28.0 is stable and widely used.
   - What's unclear: Whether Betterleaks will supersede Gitleaks and whether gitleaks maintenance will continue.
   - Recommendation: Use Gitleaks v8.28.0 for now. Design the `SecretScanner` adapter so it can swap implementations trivially. Monitor Betterleaks maturity.

2. **SonarQube integration scope for Phase 8**
   - What we know: The architecture docs mention SonarQube CE alongside Semgrep for SAST. Phase 8 requirements (SECP-01 through SECP-06) focus on Semgrep, Trivy, and Gitleaks specifically.
   - What's unclear: Whether SonarQube should be integrated in Phase 8 or deferred to Phase 9.
   - Recommendation: Defer SonarQube to Phase 9. Phase 8 requirements explicitly name Semgrep/Trivy/Gitleaks. Design the scanner adapter pattern to accommodate SonarQube later.

3. **Worktree disk space management for large codebases**
   - What we know: Each worktree is a full checkout. With 5+ parallel agents, disk usage multiplies.
   - What's unclear: Exact disk impact for typical CodeBot-generated projects.
   - Recommendation: Implement disk space monitoring in the WorktreePool. Set a configurable disk threshold. Use shallow worktrees (`--depth 1`) where possible.

4. **CLI agent binary availability detection**
   - What we know: IMPL-06 requires Claude Code, Codex CLI, and Gemini CLI adapters. Not all may be installed on every system.
   - What's unclear: How to gracefully handle missing CLI tools.
   - Recommendation: Each adapter should check binary availability at startup (`which claude`, `which codex`, etc.). Report available agents to the pipeline. Skip unavailable agents rather than failing.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio |
| Config file | `apps/server/pyproject.toml` (exists) |
| Quick run command | `uv run pytest tests/unit/ -x -q` |
| Full suite command | `uv run pytest --cov=codebot --cov-report=term-missing` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SECP-01 | Semgrep produces structured findings | unit + integration | `uv run pytest tests/unit/test_security_semgrep.py -x` | Wave 0 |
| SECP-02 | Trivy scans dependencies for CVEs | unit + integration | `uv run pytest tests/unit/test_security_trivy.py -x` | Wave 0 |
| SECP-03 | Gitleaks detects secrets | unit + integration | `uv run pytest tests/unit/test_security_gitleaks.py -x` | Wave 0 |
| SECP-04 | Quality gate blocks on critical/high | unit | `uv run pytest tests/unit/test_security_gate.py -x` | Wave 0 |
| SECP-05 | Security scanning after every code gen | integration | `uv run pytest tests/integration/test_security_pipeline.py -x` | Wave 0 |
| SECP-06 | Dependency allowlist validation | unit | `uv run pytest tests/unit/test_allowlist.py -x` | Wave 0 |
| WORK-01 | Worktree lifecycle (create/clean) | unit + integration | `uv run pytest tests/unit/test_worktree_pool.py -x` | Wave 0 |
| WORK-02 | Per-worktree Docker profiles | integration | `uv run pytest tests/integration/test_worktree_docker.py -x` | Wave 0 |
| WORK-03 | Dynamic port allocation | unit | `uv run pytest tests/unit/test_port_allocator.py -x` | Wave 0 |
| WORK-04 | Sequential merge with conflict detection | unit | `uv run pytest tests/unit/test_branch_strategy.py -x` | Wave 0 |
| IMPL-05 | Parallel agents in isolated worktrees | integration | `uv run pytest tests/integration/test_parallel_worktrees.py -x` | Wave 0 |
| IMPL-06 | CLI agent adapters (Claude/Codex/Gemini) | unit | `uv run pytest tests/unit/test_cli_agents.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/unit/ -x -q --timeout=30`
- **Per wave merge:** `uv run pytest --cov=codebot --cov-report=term-missing`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_security_semgrep.py` -- mock Semgrep CLI output, test JSON parsing
- [ ] `tests/unit/test_security_trivy.py` -- mock Trivy CLI output, test finding extraction
- [ ] `tests/unit/test_security_gitleaks.py` -- mock Gitleaks CLI output, test secret finding
- [ ] `tests/unit/test_security_gate.py` -- test threshold evaluation logic
- [ ] `tests/unit/test_allowlist.py` -- test allowlist validation for pip/npm
- [ ] `tests/unit/test_worktree_pool.py` -- test pool acquire/release lifecycle
- [ ] `tests/unit/test_port_allocator.py` -- test dynamic port allocation
- [ ] `tests/unit/test_branch_strategy.py` -- test branch naming, merge strategies
- [ ] `tests/unit/test_cli_agents.py` -- test adapter command building, output parsing
- [ ] `tests/integration/test_security_pipeline.py` -- end-to-end scan with real tools (optional, requires tools installed)
- [ ] `tests/integration/test_worktree_docker.py` -- worktree + Docker profile integration
- [ ] `tests/integration/test_parallel_worktrees.py` -- multiple agents in parallel worktrees
- [ ] `tests/conftest.py` -- update with security and worktree fixtures (mock subprocess, temp git repos)

## Sources

### Primary (HIGH confidence)
- [Semgrep CLI Reference](https://semgrep.dev/docs/cli-reference) - command flags, exit codes, JSON output format
- [Semgrep JSON/SARIF Fields](https://semgrep.dev/docs/semgrep-appsec-platform/json-and-sarif) - output schema documentation
- [Semgrep Output JSON Schema](https://github.com/semgrep/semgrep-interfaces/blob/main/semgrep_output_v1.jsonschema) - canonical JSON schema
- [Trivy Reporting Docs](https://trivy.dev/docs/latest/configuration/reporting/) - output formats and configuration
- [Trivy CLI Reference](https://trivy.dev/docs/latest/guide/references/configuration/cli/trivy/) - command flags and options
- [Gitleaks GitHub](https://github.com/gitleaks/gitleaks) - usage, JSON output structure, composite rules
- [GitPython API Reference v3.1.46](https://gitpython.readthedocs.io/en/stable/reference.html) - worktree support via command passthrough
- [ephemeral-port-reserve PyPI](https://pypi.org/project/ephemeral-port-reserve/) - race-free port allocation
- [pip Secure Installs](https://pip.pypa.io/en/stable/topics/secure-installs/) - hash-pinned requirements
- [Docker Compose Profiles](https://docs.docker.com/compose/how-tos/profiles/) - service profile management
- CodeBot SYSTEM_DESIGN.md Sections 4, 7, 8 - SecurityOrchestrator, WorktreePool, CLIAgentRunner designs
- CodeBot ARCHITECTURE.md Sections 7, 9 - Security pipeline architecture, worktree management

### Secondary (MEDIUM confidence)
- [Agentic Coding: Git Worktrees and Agent Skills](https://blog.shanelee.name/2026/02/03/agentic-coding-git-worktrees-and-agent-skills-for-parallel-workflows/) - community patterns for parallel AI agent worktrees
- [Git Worktrees for Parallel AI Coding Agents](https://devcenter.upsun.com/posts/git-worktrees-for-parallel-ai-coding-agents/) - isolation challenges and solutions
- [Superset IDE: Parallel AI Coding Agents](https://byteiota.com/superset-ide-run-10-parallel-ai-coding-agents-2026/) - industry tooling reference
- [Container Security with Trivy: Python Integration](https://johal.in/container-security-scanning-with-trivy-python-integration-for-ci-pipelines-2025/) - Python subprocess patterns
- [GitPython Worktree Issues #719, #344](https://github.com/gitpython-developers/GitPython/issues/719) - worktree support limitations

### Tertiary (LOW confidence)
- [Betterleaks Announcement](https://cybersecuritynews.com/betterleaks-tool/) - March 2026, too new to assess stability
- [Gitleaks v8.28.0 Composite Rules](https://appsecsanta.com/gitleaks) - feature description, needs hands-on validation
- [safety PyPI](https://pypi.org/project/safety/) - complementary tool, not primary recommendation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Tools are mature, well-documented, versions verified against PyPI/GitHub releases
- Architecture: HIGH - Patterns directly from SYSTEM_DESIGN.md with verified tool APIs
- Pitfalls: HIGH - Documented in official tool docs, community reports, and project STATE.md concern about worktree engineering
- Worktree isolation: MEDIUM - Custom engineering required; patterns exist in community but limited production Python implementations
- Dependency allowlist: MEDIUM - Multiple approaches exist; no single standard solution

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (30 days - tools are stable, Betterleaks situation may evolve)
