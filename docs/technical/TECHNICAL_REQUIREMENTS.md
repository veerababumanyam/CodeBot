# CodeBot Technical Requirements Document

**Version:** 2.1
**Last Updated:** 2026-03-18
**Status:** Draft
**Authors:** CodeBot Core Team

---

## Table of Contents

1. [Overview](#1-overview)
2. [Runtime & Language Requirements](#2-runtime--language-requirements)
3. [Core Dependencies & Frameworks](#3-core-dependencies--frameworks)
4. [LLM Provider Requirements](#4-llm-provider-requirements)
5. [CLI Agent Integration Requirements](#5-cli-agent-integration-requirements)
6. [Security Tool Requirements](#6-security-tool-requirements)
7. [Testing Framework Requirements](#7-testing-framework-requirements)
8. [Infrastructure Requirements](#8-infrastructure-requirements)
9. [Data Storage Requirements](#9-data-storage-requirements)
10. [API Requirements](#10-api-requirements)
11. [Security Requirements](#11-security-requirements)
12. [Monitoring & Observability](#12-monitoring--observability)
13. [Compatibility Matrix](#13-compatibility-matrix)
14. [Platform Observability Requirements](#14-platform-observability-requirements)
15. [Authentication & Authorization](#15-authentication--authorization)
16. [Error Handling Requirements](#16-error-handling-requirements)
17. [Data Retention Requirements](#17-data-retention-requirements)
18. [Prompt Engineering Requirements](#18-prompt-engineering-requirements)
19. [Agent Safety Requirements](#19-agent-safety-requirements)
20. [Offline Mode Requirements](#20-offline-mode-requirements)
21. [Appendix](#21-appendix)

---

## 1. Overview

CodeBot is an autonomous end-to-end software development platform powered by a graph-centric multi-agent system. It accepts PRDs (Product Requirements Documents) and natural-language requirements as input and autonomously plans, researches, architects, designs, codes, reviews, tests, debugs, manages project progress, and delivers working applications.

### 1.1 Architecture Summary

CodeBot operates as a directed acyclic graph (DAG) of specialized agents, each responsible for a discrete phase of the software development lifecycle. The orchestration engine manages agent scheduling, inter-agent communication, context propagation, and failure recovery. A web dashboard provides real-time visibility into agent activity, and a CLI interface supports headless operation for CI/CD integration.

### 1.2 Document Purpose

This document defines the complete set of technical requirements for building, deploying, and operating CodeBot. It serves as the authoritative reference for:

- Development environment setup
- Dependency management and version pinning
- Infrastructure provisioning
- Security posture and compliance
- Integration contracts between subsystems

### 1.3 Terminology

| Term | Definition |
|------|------------|
| **Agent** | An autonomous unit of execution within the CodeBot graph that performs a specific SDLC task (e.g., planning, coding, testing). |
| **Orchestrator** | The central engine that schedules agents, manages the execution graph, and propagates context. |
| **Worktree** | An isolated Git working tree used to sandbox agent code generation and prevent conflicts. |
| **Context Window** | The token budget available to an LLM for a single inference call; managed via chunking and summarization. |
| **MCP** | Model Context Protocol -- Anthropic's open standard for connecting LLMs to external tools and data sources. |
| **PRD** | Product Requirements Document -- the primary input artifact that CodeBot consumes to begin autonomous development. |

---

## 2. Runtime & Language Requirements

### 2.1 Python (Primary -- Orchestration Engine)

| Property | Requirement |
|----------|-------------|
| **Minimum Version** | 3.12.0 |
| **Recommended Version** | 3.12.x (latest patch) |
| **Maximum Tested Version** | 3.13.x |
| **Package Manager** | `uv` (preferred), `pip` with `pip-tools` (fallback) |
| **Virtual Environment** | Required; managed via `uv venv` or `python -m venv` |
| **Type Checking** | `mypy` in strict mode; `pyright` accepted as alternative |
| **Formatter** | `ruff format` (Black-compatible) |
| **Linter** | `ruff check` with comprehensive rule set |

**Rationale:** Python 3.12 introduces performance improvements via the specializing adaptive interpreter, improved error messages, and `type` statement support. The orchestration engine, all agent logic, the FastAPI backend, and LLM integration layers are implemented in Python.

**Required Python Features:**
- `asyncio` with `TaskGroup` for concurrent agent execution
- `typing` module with `TypeVar`, `ParamSpec`, and `TypeAlias` for strict type annotations
- `tomllib` (stdlib in 3.11+) for configuration parsing
- `dataclasses` with `slots=True` and `kw_only=True` for performance-critical data models
- `ExceptionGroup` for structured multi-agent error handling

### 2.2 Node.js (Web Dashboard & CLI Integrations)

| Property | Requirement |
|----------|-------------|
| **Minimum Version** | 22.0.0 (LTS) |
| **Recommended Version** | 22.x (latest LTS patch) |
| **Package Manager** | `pnpm` 9.x (preferred), `npm` 10.x (fallback) |
| **Module System** | ESM (ECMAScript Modules) exclusively |
| **Runtime for CLI Tools** | Node.js or Bun 1.1+ (for performance-sensitive CLI operations) |

**Rationale:** Node.js 22 LTS provides native ESM support, improved `fetch` API stability, the `--watch` mode for development, and long-term support through April 2027. It powers the React-based web dashboard, the CLI tool layer, and SDK distribution.

### 2.3 TypeScript (Frontend & SDK)

| Property | Requirement |
|----------|-------------|
| **Minimum Version** | 5.5.0 |
| **Recommended Version** | 5.x (latest stable) |
| **Strict Mode** | Required (`"strict": true` in `tsconfig.json`) |
| **Target** | `ES2023` |
| **Module Resolution** | `bundler` (for Vite projects), `node16` (for SDK/CLI) |

**TypeScript Compiler Options (Mandatory):**

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true,
    "verbatimModuleSyntax": true
  }
}
```

### 2.4 Go (Optional -- High-Performance Components)

| Property | Requirement |
|----------|-------------|
| **Minimum Version** | 1.22.0 |
| **Recommended Version** | 1.22.x (latest patch) |
| **Use Cases** | Context database engine, high-throughput vector operations, embedding pipeline workers |
| **Build** | Static binaries via `CGO_ENABLED=0` for container deployment |

**Rationale:** Go is optional and reserved for performance-critical components where Python's throughput is insufficient. Primary candidates include a custom context database for sub-millisecond retrieval, a high-throughput embedding ingestion pipeline, and a gRPC inter-service communication layer.

---

## 3. Core Dependencies & Frameworks

### 3.1 Agent Orchestration

| Dependency | Version | Purpose | Install |
|------------|---------|---------|---------|
| **MASFactory** | >=0.1.0 | Graph-centric multi-agent orchestration framework; defines agent DAGs, manages execution order, handles inter-agent messaging and context propagation | `pip install masfactory` |
| **LangChain** | >=0.3.0 | LLM chain composition, prompt management, output parsing, and tool integration | `pip install langchain` |
| **LangGraph** | >=0.2.0 | Stateful, cyclical agent graph execution with built-in persistence and human-in-the-loop support | `pip install langgraph` |
| **LangSmith** | >=0.1.0 | Observability, tracing, and evaluation for LLM chains (optional but recommended) | `pip install langsmith` |

**MASFactory Integration Details:**

MASFactory serves as the primary orchestration layer. Each CodeBot agent (Planner, Researcher, Architect, Designer, Coder, Reviewer, Tester, Debugger, Deployer, Project Manager) is registered as a node in a MASFactory execution graph. The framework provides:

- **Graph Definition:** Declarative YAML or Python-based DAG specification for agent execution order and conditional branching.
- **Context Bus:** Typed message passing between agents with schema validation.
- **Checkpoint/Resume:** Serializable execution state for long-running development workflows.
- **Parallel Execution:** Automatic parallelization of independent agent subgraphs.
- **Error Recovery:** Configurable retry policies, fallback agents, and graceful degradation.

### 3.2 Backend API

| Dependency | Version | Purpose | Install |
|------------|---------|---------|---------|
| **FastAPI** | >=0.115.0 | Async HTTP API framework for the backend server | `pip install fastapi` |
| **Uvicorn** | >=0.30.0 | ASGI server for FastAPI | `pip install uvicorn[standard]` |
| **Pydantic** | >=2.9.0 | Data validation, serialization, and settings management | `pip install pydantic` |
| **python-multipart** | >=0.0.9 | File upload handling | `pip install python-multipart` |
| **python-jose** | >=3.3.0 | JWT token creation and verification | `pip install python-jose[cryptography]` |
| **passlib** | >=1.7.4 | Password hashing (bcrypt) | `pip install passlib[bcrypt]` |
| **httpx** | >=0.27.0 | Async HTTP client for external API calls | `pip install httpx` |
| **websockets** | >=13.0 | WebSocket support for real-time streaming | `pip install websockets` |

### 3.3 Frontend (Web Dashboard)

| Dependency | Version | Purpose | Install |
|------------|---------|---------|---------|
| **React** | >=18.3.0 | UI component framework | `pnpm add react react-dom` |
| **Vite** | >=6.0.0 | Build tool and dev server | `pnpm add -D vite` |
| **TailwindCSS** | >=4.0.0 | Utility-first CSS framework | `pnpm add -D tailwindcss` |
| **Zustand** | >=5.0.0 | Lightweight state management | `pnpm add zustand` |
| **React Router** | >=7.0.0 | Client-side routing | `pnpm add react-router` |
| **TanStack Query** | >=5.60.0 | Server state management and data fetching | `pnpm add @tanstack/react-query` |
| **Recharts** | >=2.13.0 | Charting library for metrics dashboards | `pnpm add recharts` |
| **shadcn/ui** | latest | Pre-built accessible UI components (copy-paste pattern) | `pnpm dlx shadcn@latest init` |
| **Lucide React** | >=0.460.0 | Icon set | `pnpm add lucide-react` |

### 3.4 Desktop Application (Optional)

| Dependency | Version | Purpose | Install |
|------------|---------|---------|---------|
| **Electron** | >=33.0.0 | Cross-platform desktop app shell | `pnpm add -D electron` |
| **Electron Forge** | >=7.0.0 | Build, package, and distribute Electron apps | `pnpm add -D @electron-forge/cli` |

**Note:** The desktop app is an optional distribution target. The web dashboard is the primary interface and must function independently.

### 3.5 Data Storage

| Dependency | Version | Purpose | Install |
|------------|---------|---------|---------|
| **SQLAlchemy** | >=2.0.35 | ORM and database toolkit for relational data | `pip install sqlalchemy` |
| **Alembic** | >=1.14.0 | Database migration management | `pip install alembic` |
| **aiosqlite** | >=0.20.0 | Async SQLite driver (development) | `pip install aiosqlite` |
| **asyncpg** | >=0.30.0 | Async PostgreSQL driver (production) | `pip install asyncpg` |
| **ChromaDB** | >=0.5.0 | Embedded vector database (development) | `pip install chromadb` |
| **Weaviate Client** | >=4.9.0 | Managed vector database client (production) | `pip install weaviate-client` |
| **Redis** (via `redis-py`) | >=5.2.0 | Caching, pub/sub, session state | `pip install redis[hiredis]` |

### 3.6 DevOps & Tooling

| Dependency | Version | Purpose | Install |
|------------|---------|---------|---------|
| **Docker SDK for Python** | >=7.1.0 | Programmatic container management for sandboxing | `pip install docker` |
| **GitPython** | >=3.1.43 | Git operations (clone, commit, branch, worktree) | `pip install gitpython` |
| **Click** | >=8.1.0 | CLI framework for the `codebot` command | `pip install click` |
| **Rich** | >=13.9.0 | Terminal formatting, progress bars, and tables | `pip install rich` |
| **Typer** | >=0.12.0 | Alternative CLI framework (for subcommands) | `pip install typer` |

---

## 4. LLM Provider Requirements

### 4.1 Provider Overview

CodeBot operates with a multi-provider LLM strategy. No single provider is a hard dependency; the system must gracefully degrade when a provider is unavailable and route requests to an available alternative.

### 4.2 OpenAI API

| Property | Requirement |
|----------|-------------|
| **SDK** | `openai` >= 1.55.0 (`pip install openai`) |
| **Models Required** | `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano` |
| **Reasoning Models** | `o3`, `o4-mini` |
| **Code Models** | Codex CLI (via subprocess) |
| **API Version** | Latest stable |
| **Authentication** | API key via `OPENAI_API_KEY` environment variable |
| **Organization** | Optional via `OPENAI_ORG_ID` |

**Model Routing Strategy:**

| Use Case | Primary Model | Fallback Model |
|----------|---------------|----------------|
| Complex architecture decisions | `o3` | `gpt-4.1` |
| Code generation | `gpt-4.1` | `o4-mini` |
| Code review | `gpt-4.1` | `gpt-4.1-mini` |
| Quick completions / boilerplate | `gpt-4.1-mini` | `gpt-4.1-nano` |
| Reasoning-heavy debugging | `o3` | `o4-mini` |

### 4.3 Anthropic API

| Property | Requirement |
|----------|-------------|
| **SDK** | `anthropic` >= 0.39.0 (`pip install anthropic`) |
| **Models Required** | `claude-opus-4-20250514`, `claude-sonnet-4-20250514` |
| **Fast Models** | `claude-haiku-3-5-20241022` |
| **Agent SDK** | Claude Code SDK (via `claude-code-sdk` package or subprocess) |
| **API Version** | `2023-06-01` (latest stable) |
| **Authentication** | API key via `ANTHROPIC_API_KEY` environment variable |
| **Extended Thinking** | Required for Opus and Sonnet on complex tasks; budget tokens configurable |

**Model Routing Strategy:**

| Use Case | Primary Model | Fallback Model |
|----------|---------------|----------------|
| Complex architecture and planning | Claude Opus 4 | Claude Sonnet 4 |
| Code generation and review | Claude Sonnet 4 | Claude Haiku 3.5 |
| Quick edits and simple tasks | Claude Haiku 3.5 | Claude Sonnet 4 |
| Agentic coding (tool use) | Claude Code SDK | Claude Sonnet 4 (direct API) |

### 4.4 Google Generative AI

| Property | Requirement |
|----------|-------------|
| **SDK** | `google-genai` >= 1.0.0 (`pip install google-genai`) |
| **Models Required** | `gemini-2.5-pro`, `gemini-2.5-flash` |
| **CLI Tool** | Gemini CLI (via subprocess) |
| **Authentication** | API key via `GOOGLE_API_KEY` or Application Default Credentials |

**Model Routing Strategy:**

| Use Case | Primary Model | Fallback Model |
|----------|---------------|----------------|
| Long-context analysis (1M+ tokens) | Gemini 2.5 Pro | Gemini 2.5 Flash |
| Code generation | Gemini 2.5 Pro | Gemini 2.5 Flash |
| Fast completions | Gemini 2.5 Flash | Gemini 2.5 Pro |

### 4.5 Unified LLM Interface

| Property | Requirement |
|----------|-------------|
| **Abstraction Layer** | LiteLLM >= 1.50.0 (`pip install litellm`) or custom `LLMRouter` class |
| **Fallback Strategy** | Ordered provider list per use case; automatic failover on error |
| **Rate Limiting** | Token bucket algorithm; per-provider and per-model limits |
| **Retry Policy** | Exponential backoff with jitter: base 1s, max 60s, max retries 5 |
| **Timeout** | 120s default per request; 300s for reasoning models |
| **Streaming** | Required for all code generation and chat-style interactions |
| **Token Tracking** | Per-request token counting for cost attribution |

**Rate Limiting Configuration:**

```yaml
rate_limits:
  openai:
    gpt-4.1:
      requests_per_minute: 500
      tokens_per_minute: 300000
    o3:
      requests_per_minute: 100
      tokens_per_minute: 200000
  anthropic:
    claude-opus-4:
      requests_per_minute: 100
      tokens_per_minute: 200000
    claude-sonnet-4:
      requests_per_minute: 500
      tokens_per_minute: 400000
  google:
    gemini-2.5-pro:
      requests_per_minute: 200
      tokens_per_minute: 500000
```

**Retry Policy Implementation:**

```python
retry_config:
  max_retries: 5
  base_delay_seconds: 1.0
  max_delay_seconds: 60.0
  exponential_base: 2
  jitter: true  # adds random 0-1s to prevent thundering herd
  retryable_status_codes: [429, 500, 502, 503, 504]
  retryable_exceptions:
    - ConnectionError
    - TimeoutError
    - APIConnectionError
```

---

## 5. CLI Agent Integration Requirements

### 5.1 Claude Code

| Property | Requirement |
|----------|-------------|
| **Integration Method** | Claude Agent SDK (`claude-code-sdk` Python package) |
| **Fallback Method** | Subprocess execution of `claude` CLI binary |
| **Output Format** | Structured JSON via SDK; parsed stdout/stderr via subprocess |
| **Isolation** | Git worktree per agent session |
| **Permissions** | File read/write, shell command execution (sandboxed) |
| **Session Management** | Persistent sessions with checkpoint/resume support |

**SDK Integration Pattern:**

```python
from claude_code_sdk import ClaudeAgent, AgentConfig

config = AgentConfig(
    model="claude-sonnet-4-20250514",
    max_turns=50,
    allowed_tools=["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
    working_directory="/path/to/worktree",
    system_prompt="You are a code generation agent..."
)

agent = ClaudeAgent(config)
result = await agent.run(prompt="Implement the user authentication module...")
```

**Subprocess Fallback Pattern:**

```python
import subprocess
import json

proc = subprocess.run(
    ["claude", "--output-format", "json", "--max-turns", "50",
     "--allowedTools", "Read,Write,Edit,Bash",
     "-p", prompt],
    capture_output=True, text=True, timeout=600,
    cwd=worktree_path
)
result = json.loads(proc.stdout)
```

### 5.2 OpenAI Codex CLI

| Property | Requirement |
|----------|-------------|
| **Integration Method** | Subprocess execution of `codex` CLI binary |
| **Output Format** | Parsed stdout/stderr with structured extraction |
| **Isolation** | Git worktree per agent session |
| **Approval Mode** | `--full-auto` for autonomous operation |
| **Model Override** | Configurable via `--model` flag |

**Subprocess Pattern:**

```python
proc = subprocess.run(
    ["codex", "--full-auto", "--model", "o4-mini",
     prompt],
    capture_output=True, text=True, timeout=600,
    cwd=worktree_path,
    env={**os.environ, "OPENAI_API_KEY": api_key}
)
```

### 5.3 Gemini CLI

| Property | Requirement |
|----------|-------------|
| **Integration Method** | Subprocess execution of `gemini` CLI binary |
| **Output Format** | Parsed stdout/stderr with structured extraction |
| **Isolation** | Git worktree per agent session |
| **Model Override** | Configurable via `--model` flag |

**Subprocess Pattern:**

```python
proc = subprocess.run(
    ["gemini", "--model", "gemini-2.5-pro",
     "-p", prompt],
    capture_output=True, text=True, timeout=600,
    cwd=worktree_path,
    env={**os.environ, "GOOGLE_API_KEY": api_key}
)
```

### 5.4 Common CLI Agent Requirements

All CLI agent integrations must satisfy the following:

| Requirement | Description |
|-------------|-------------|
| **Worktree Isolation** | Each CLI agent session operates in a dedicated Git worktree created from the project repository. Worktrees are created via `git worktree add` and cleaned up after session completion. |
| **Timeout Management** | Configurable per-agent timeout (default 600s). Hard kill after timeout + 30s grace period. |
| **Output Parsing** | Structured extraction of: files created/modified, commands run, errors encountered, and final summary. |
| **Error Classification** | Parse exit codes, stderr, and output to classify failures as: transient (retry), permanent (escalate), or partial (merge partial results). |
| **Resource Limits** | CPU and memory limits enforced via Docker cgroup constraints when running in containerized mode. |
| **Logging** | All stdin/stdout/stderr captured and stored for audit and debugging. Sensitive content (API keys) redacted before storage. |

---

## 6. Security Tool Requirements

### 6.1 Static Application Security Testing (SAST)

#### 6.1.1 Semgrep

| Property | Requirement |
|----------|-------------|
| **Version** | >= 1.90.0 |
| **Install** | `pip install semgrep` or `brew install semgrep` |
| **Rule Sets** | `p/default`, `p/owasp-top-ten`, `p/security-audit`, `p/python`, `p/javascript`, `p/typescript` |
| **Integration Point** | Post-code-generation, pre-commit, and CI pipeline |
| **Output Format** | JSON (`--json`) for programmatic consumption |
| **Severity Threshold** | Block on `ERROR`; warn on `WARNING`; info on `INFO` |

**Execution Pattern:**

```bash
semgrep scan --config=auto --json --output=results.json \
  --severity=ERROR --severity=WARNING \
  /path/to/generated/code
```

#### 6.1.2 CodeQL (GitHub-Native SAST)

| Property | Requirement |
|----------|-------------|
| **Version** | >= 2.19.0 |
| **Install** | GitHub CLI extension or standalone binary |
| **Languages** | Python, JavaScript, TypeScript, Go |
| **Integration Point** | GitHub Actions CI pipeline; post-push analysis |
| **Query Suites** | `security-extended`, `security-and-quality` |
| **Output Format** | SARIF (Static Analysis Results Interchange Format) |

### 6.2 Code Quality

#### 6.2.1 SonarQube Community Edition

| Property | Requirement |
|----------|-------------|
| **Version** | >= 10.7 (Community Edition) |
| **Deployment** | Docker container (`sonarqube:community`) |
| **Scanner** | `sonar-scanner` CLI >= 6.2.0 |
| **Languages** | Python, JavaScript, TypeScript, HTML, CSS |
| **Quality Gates** | Configurable; default: no new bugs, no new vulnerabilities, 80%+ coverage on new code |
| **Integration Point** | Post-test-execution; results fed back to Reviewer agent |

### 6.3 Container & Dependency Scanning

#### 6.3.1 Trivy

| Property | Requirement |
|----------|-------------|
| **Version** | >= 0.57.0 |
| **Install** | `brew install trivy` or Docker image `aquasec/trivy` |
| **Scan Targets** | Container images, filesystem (for dependency vulnerabilities), IaC files |
| **Output Format** | JSON (`--format json`) and SARIF |
| **Severity Threshold** | Block on `CRITICAL` and `HIGH`; warn on `MEDIUM` |

**Execution Pattern:**

```bash
# Dependency scan
trivy fs --format json --output trivy-fs.json --severity HIGH,CRITICAL /path/to/project

# Container image scan
trivy image --format json --output trivy-image.json --severity HIGH,CRITICAL codebot:latest
```

### 6.4 Secret Detection

#### 6.4.1 Gitleaks

| Property | Requirement |
|----------|-------------|
| **Version** | >= 8.21.0 |
| **Install** | `brew install gitleaks` or Go binary |
| **Integration Point** | Pre-commit hook, post-code-generation scan, CI pipeline |
| **Output Format** | JSON (`--report-format json`) |
| **Configuration** | Custom `.gitleaks.toml` with project-specific allowlist |

**Execution Pattern:**

```bash
# Pre-commit scan
gitleaks protect --staged --report-format json --report-path gitleaks-report.json

# Full repository scan
gitleaks detect --report-format json --report-path gitleaks-report.json
```

### 6.5 Dynamic Application Security Testing (DAST)

#### 6.5.1 Shannon

| Property | Requirement |
|----------|-------------|
| **Purpose** | Autonomous DAST for web applications generated by CodeBot |
| **Integration Point** | Post-deployment to staging environment |
| **Target** | HTTP endpoints of generated applications |
| **Output Format** | Structured findings report (JSON) |
| **Scope Control** | Restrict scanning to the generated application domain only |

### 6.6 License Compliance

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| **ScanCode Toolkit** | >= 32.3.0 | License detection in source code and dependencies | `pip install scancode-toolkit` |
| **FOSSology** | >= 4.4.0 | Open-source license compliance (server-based) | Docker image `fossology/fossology` |
| **ORT (OSS Review Toolkit)** | >= 27.0.0 | Dependency analysis and license compliance orchestration | Docker image or standalone |

**License Policy:**

| License Category | Action |
|------------------|--------|
| Permissive (MIT, BSD, Apache 2.0) | Allow |
| Weak Copyleft (LGPL, MPL) | Warn; require review |
| Strong Copyleft (GPL, AGPL) | Block; require explicit approval |
| Unknown | Block; require manual classification |

---

## 7. Testing Framework Requirements

### 7.1 Python Testing

| Dependency | Version | Purpose | Install |
|------------|---------|---------|---------|
| **pytest** | >= 8.3.0 | Test runner and framework | `pip install pytest` |
| **pytest-asyncio** | >= 0.24.0 | Async test support | `pip install pytest-asyncio` |
| **pytest-cov** | >= 6.0.0 | Coverage reporting plugin | `pip install pytest-cov` |
| **pytest-mock** | >= 3.14.0 | Mock/patch utilities | `pip install pytest-mock` |
| **pytest-xdist** | >= 3.5.0 | Parallel test execution | `pip install pytest-xdist` |
| **pytest-timeout** | >= 2.3.0 | Test timeout enforcement | `pip install pytest-timeout` |
| **Coverage.py** | >= 7.6.0 | Code coverage measurement | `pip install coverage` |
| **hypothesis** | >= 6.115.0 | Property-based testing | `pip install hypothesis` |
| **factory-boy** | >= 3.3.0 | Test fixture factories | `pip install factory-boy` |
| **respx** | >= 0.21.0 | HTTP request mocking for `httpx` | `pip install respx` |

**Coverage Requirements:**

| Metric | Minimum Threshold | Target |
|--------|-------------------|--------|
| Line coverage | 80% | 90% |
| Branch coverage | 70% | 85% |
| Function coverage | 85% | 95% |
| New code coverage | 90% | 95% |

**pytest Configuration (`pyproject.toml`):**

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",
    "--timeout=30",
    "--cov=codebot",
    "--cov-report=term-missing",
    "--cov-report=html:reports/coverage",
    "--cov-fail-under=80",
]
markers = [
    "unit: Unit tests (fast, no I/O)",
    "integration: Integration tests (may require external services)",
    "e2e: End-to-end tests (full system)",
    "slow: Tests that take more than 10 seconds",
]
```

### 7.2 JavaScript/TypeScript Testing

| Dependency | Version | Purpose | Install |
|------------|---------|---------|---------|
| **Vitest** | >= 2.1.0 | Primary test runner (Vite-native) | `pnpm add -D vitest` |
| **Jest** | >= 29.7.0 | Alternative test runner (for non-Vite projects) | `pnpm add -D jest` |
| **Testing Library** | >= 16.0.0 | React component testing utilities | `pnpm add -D @testing-library/react` |
| **MSW** | >= 2.6.0 | API mocking (Mock Service Worker) | `pnpm add -D msw` |
| **istanbul** (via `c8`) | >= 10.1.0 | Code coverage for JS/TS | `pnpm add -D c8` or via Vitest built-in |

### 7.3 End-to-End Testing

| Dependency | Version | Purpose | Install |
|------------|---------|---------|---------|
| **Playwright** | >= 1.49.0 | Cross-browser E2E testing | `pnpm add -D @playwright/test` or `pip install playwright` |
| **Browsers** | Chromium, Firefox, WebKit | Multi-browser verification | `npx playwright install` |

**Playwright Configuration:**

```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html'], ['json', { outputFile: 'reports/e2e-results.json' }]],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
});
```

### 7.4 Test Categories and Execution Strategy

| Category | Scope | Execution Time | Trigger |
|----------|-------|----------------|---------|
| **Unit** | Individual functions, classes | < 100ms per test | Pre-commit, every agent cycle |
| **Integration** | Module interactions, API endpoints | < 5s per test | Post-commit, CI pipeline |
| **E2E** | Full user workflows | < 60s per test | Pre-merge, nightly |
| **Security** | SAST, DAST, dependency scan | < 300s total | Pre-merge, nightly |
| **Performance** | Load, latency, throughput | < 600s total | Weekly, pre-release |

---

## 8. Infrastructure Requirements

### 8.1 Docker

| Property | Requirement |
|----------|-------------|
| **Minimum Version** | 24.0.0 |
| **Recommended Version** | 27.x (latest stable) |
| **Docker Compose** | >= 2.29.0 (v2 plugin, not standalone) |
| **BuildKit** | Required (`DOCKER_BUILDKIT=1`) |
| **Rootless Mode** | Recommended for production deployments |

**Docker Use Cases in CodeBot:**

| Use Case | Description |
|----------|-------------|
| **Code Execution Sandbox** | Generated code runs inside ephemeral containers with restricted networking, filesystem, and syscall access. |
| **Tool Isolation** | Security scanners (Semgrep, Trivy, SonarQube) run in dedicated containers to prevent tool conflicts. |
| **Development Environment** | `docker compose` for local development with all services (API, dashboard, databases, Redis). |
| **Build Pipeline** | Multi-stage Docker builds for production images. |

**Sandbox Container Constraints:**

```yaml
sandbox_container:
  memory_limit: "2g"
  cpu_limit: "2.0"
  pids_limit: 256
  network_mode: "none"  # No network access for untrusted code
  read_only_rootfs: true
  no_new_privileges: true
  security_opt:
    - "no-new-privileges:true"
    - "seccomp=seccomp-profile.json"
  tmpfs:
    /tmp: "size=512m"
  timeout: 300  # seconds
```

### 8.2 Git

| Property | Requirement |
|----------|-------------|
| **Minimum Version** | 2.40.0 |
| **Recommended Version** | 2.47.x (latest stable) |
| **Worktree Support** | Required for parallel agent execution |
| **Sparse Checkout** | Required for large repository handling |
| **LFS** | Required for binary artifact management |

**Git Worktree Strategy:**

Each coding agent receives its own Git worktree to prevent merge conflicts during parallel code generation:

```
project-repo/
  .git/                      # Shared Git database
  main/                      # Main working tree (protected)
  .worktrees/
    agent-planner-abc123/    # Planner agent worktree
    agent-coder-def456/      # Coder agent worktree
    agent-tester-ghi789/     # Tester agent worktree
```

**Worktree Lifecycle:**

1. **Create:** `git worktree add .worktrees/agent-{name}-{id} -b agent/{name}/{id} main`
2. **Execute:** Agent performs work inside the worktree
3. **Commit:** Agent commits changes to the worktree branch
4. **Merge:** Orchestrator merges the branch back to main after review
5. **Cleanup:** `git worktree remove .worktrees/agent-{name}-{id}`

### 8.3 Hardware Requirements

#### 8.3.1 Development Environment (Single Developer)

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **CPU** | 4 cores | 8+ cores (Apple M-series or modern x86) |
| **RAM** | 16 GB | 32 GB |
| **Disk** | 50 GB free | 100 GB+ SSD (NVMe preferred) |
| **Network** | 10 Mbps | 50+ Mbps (for LLM API latency) |

#### 8.3.2 Production Environment (Team/CI)

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **CPU** | 8 cores | 16+ cores |
| **RAM** | 32 GB | 64 GB |
| **Disk** | 200 GB SSD | 500 GB+ NVMe SSD |
| **Network** | 100 Mbps | 1 Gbps |
| **GPU** | None required | Optional: for local embedding models |

### 8.4 Network Requirements

| Endpoint | Protocol | Port | Purpose |
|----------|----------|------|---------|
| `api.openai.com` | HTTPS | 443 | OpenAI API access |
| `api.anthropic.com` | HTTPS | 443 | Anthropic API access |
| `generativelanguage.googleapis.com` | HTTPS | 443 | Google AI API access |
| `pypi.org` | HTTPS | 443 | Python package installation |
| `registry.npmjs.org` | HTTPS | 443 | Node.js package installation |
| `ghcr.io`, `docker.io` | HTTPS | 443 | Container image registry |
| `github.com` | HTTPS/SSH | 443/22 | Git operations |

**Firewall Rules for Sandbox Containers:**

- Default: deny all outbound traffic
- Allow: DNS resolution (port 53) during build phase only
- Allow: package registry access during dependency install phase only
- Deny: all network access during code execution phase

---

## 9. Data Storage Requirements

### 9.1 Project Metadata

| Environment | Backend | Configuration |
|-------------|---------|---------------|
| **Development** | SQLite 3.45+ | File-based; `~/.codebot/metadata.db` |
| **Production** | PostgreSQL 16+ | Connection pool via `asyncpg`; max 20 connections |

**Schema Overview (Key Tables):**

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `projects` | Project registry | `id`, `name`, `description`, `created_at`, `status` |
| `tasks` | Development tasks derived from PRD | `id`, `project_id`, `title`, `status`, `agent_id`, `priority` |
| `agent_runs` | Individual agent execution records | `id`, `task_id`, `agent_type`, `started_at`, `completed_at`, `status`, `tokens_used`, `cost` |
| `artifacts` | Generated files and outputs | `id`, `agent_run_id`, `file_path`, `file_hash`, `artifact_type` |
| `audit_log` | Security and compliance audit trail | `id`, `timestamp`, `actor`, `action`, `resource`, `details` |
| `api_keys` | Encrypted LLM provider API keys | `id`, `provider`, `encrypted_key`, `created_at`, `last_used` |

**Migration Strategy:**

- All schema changes managed via Alembic
- Migrations must be backwards-compatible (expand-then-contract pattern)
- Migration scripts stored in `codebot/db/migrations/`
- Automated migration on application startup (with opt-out flag)

### 9.2 Vector Embeddings

| Environment | Backend | Configuration |
|-------------|---------|---------------|
| **Development** | ChromaDB (embedded mode) | Persistent storage at `~/.codebot/chroma/` |
| **Production** | Weaviate (managed or self-hosted) | gRPC connection; batch import enabled |

**Vector Storage Use Cases:**

| Collection | Content | Embedding Model | Dimensions |
|------------|---------|-----------------|------------|
| `codebase_chunks` | Source code chunks (function/class level) | `text-embedding-3-small` | 1536 |
| `documentation` | Project docs, READMEs, comments | `text-embedding-3-small` | 1536 |
| `agent_memories` | Agent execution summaries and learnings | `text-embedding-3-small` | 1536 |
| `error_patterns` | Known error patterns and resolutions | `text-embedding-3-small` | 1536 |
| `prd_requirements` | Parsed PRD requirements and user stories | `text-embedding-3-small` | 1536 |

**Chunking Strategy:**

| Content Type | Chunk Size | Overlap | Splitter |
|--------------|------------|---------|----------|
| Source code | 1500 tokens | 200 tokens | AST-aware (tree-sitter) |
| Documentation | 1000 tokens | 150 tokens | Recursive character |
| Conversations | 800 tokens | 100 tokens | Sentence-boundary |

### 9.3 Agent Memory

CodeBot implements a hybrid memory system inspired by hierarchical episodic memory:

| Memory Tier | Storage | Persistence | Access Pattern |
|-------------|---------|-------------|----------------|
| **Working Memory** | In-process Python objects | Session-scoped | Direct attribute access |
| **Short-Term Memory** | Redis (key-value + streams) | TTL-based (1 hour default) | Key lookup, stream read |
| **Long-Term Memory** | Vector DB + filesystem | Permanent | Semantic search, file read |
| **Episodic Memory** | Filesystem (structured JSON) | Permanent | Timeline-based retrieval |

**Filesystem Layout for Agent Memory:**

```
~/.codebot/memory/
  projects/{project_id}/
    episodes/
      {timestamp}-{agent}-{task}.json    # Episodic records
    summaries/
      {agent}-cumulative.json            # Running summaries
    context/
      codebase-map.json                  # Repository structure
      dependency-graph.json              # Dependency relationships
      architecture-decisions.json         # ADRs from Architect agent
```

### 9.4 File Artifacts

| Artifact Type | Storage Location | Versioning | Retention |
|---------------|------------------|------------|-----------|
| Generated source code | Git repository (worktree) | Git commits | Permanent |
| Build outputs | `{project}/dist/` | Not versioned | Until next build |
| Test reports | `{project}/reports/` | Git commits | Permanent |
| Security scan results | `{project}/reports/security/` | Git commits | Permanent |
| Agent logs | `~/.codebot/logs/` | Rotated | 30 days |
| Temporary files | `/tmp/codebot/` | Not versioned | Session-scoped |

### 9.5 Cache (Redis)

| Property | Requirement |
|----------|-------------|
| **Version** | Redis 7.4+ |
| **Deployment** | Standalone (dev), Sentinel or Cluster (prod) |
| **Max Memory** | 2 GB (dev), 8 GB (prod) |
| **Eviction Policy** | `allkeys-lru` |
| **Persistence** | RDB snapshots every 60s (optional; cache is non-authoritative) |

**Redis Key Namespaces:**

| Namespace | Pattern | Purpose | TTL |
|-----------|---------|---------|-----|
| `cache:llm` | `cache:llm:{hash}` | LLM response caching (deterministic prompts) | 1 hour |
| `cache:embed` | `cache:embed:{hash}` | Embedding vector caching | 24 hours |
| `pubsub:agents` | `pubsub:agents:{project_id}` | Real-time agent status events | N/A (pub/sub) |
| `stream:logs` | `stream:logs:{project_id}` | Agent log streaming | 4 hours |
| `session` | `session:{session_id}` | User session state | 24 hours |
| `lock` | `lock:{resource}` | Distributed locks for resource contention | 30 seconds |
| `ratelimit` | `ratelimit:{provider}:{model}` | Token bucket rate limiting state | 60 seconds |

### 9.6 Session State

| Environment | Backend | Configuration |
|-------------|---------|---------------|
| **Development** | Filesystem checkpoints | `~/.codebot/sessions/{session_id}/` |
| **Production** | Redis + filesystem hybrid | Redis for active sessions; filesystem for hibernated sessions |

**Checkpoint Schema:**

```json
{
  "session_id": "uuid",
  "project_id": "uuid",
  "created_at": "ISO-8601",
  "graph_state": {
    "completed_nodes": ["planner", "researcher"],
    "active_nodes": ["architect"],
    "pending_nodes": ["coder", "reviewer", "tester"],
    "node_outputs": {}
  },
  "context": {
    "prd_summary": "...",
    "architecture_decisions": [],
    "generated_files": []
  },
  "token_usage": {
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "cost_usd": 0.0
  }
}
```

---

## 10. API Requirements

### 10.1 RESTful API

| Property | Requirement |
|----------|-------------|
| **Framework** | FastAPI (see Section 3.2) |
| **Base URL** | `/api/v1` |
| **Authentication** | Bearer token (JWT) with RS256 signing |
| **Content Type** | `application/json` (request and response) |
| **Versioning** | URL path versioning (`/api/v1`, `/api/v2`) |
| **Rate Limiting** | 100 requests/minute per user (configurable) |
| **CORS** | Configurable allowed origins; default `localhost:*` in dev |

**Core API Endpoints:**

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/projects` | Create a new project from PRD |
| `GET` | `/api/v1/projects` | List all projects |
| `GET` | `/api/v1/projects/{id}` | Get project details |
| `POST` | `/api/v1/projects/{id}/start` | Start autonomous development |
| `POST` | `/api/v1/projects/{id}/pause` | Pause execution |
| `POST` | `/api/v1/projects/{id}/resume` | Resume from checkpoint |
| `GET` | `/api/v1/projects/{id}/status` | Get current execution status |
| `GET` | `/api/v1/projects/{id}/agents` | List agent runs for project |
| `GET` | `/api/v1/projects/{id}/agents/{agent_id}/logs` | Get agent logs |
| `GET` | `/api/v1/projects/{id}/artifacts` | List generated artifacts |
| `GET` | `/api/v1/projects/{id}/artifacts/{artifact_id}` | Download artifact |
| `GET` | `/api/v1/projects/{id}/costs` | Get token usage and cost breakdown |
| `POST` | `/api/v1/auth/login` | Authenticate user |
| `POST` | `/api/v1/auth/refresh` | Refresh JWT token |
| `GET` | `/api/v1/settings` | Get system settings |
| `PUT` | `/api/v1/settings` | Update system settings |
| `GET` | `/api/v1/health` | Health check |

**API Response Format (Standard Envelope):**

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO-8601",
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

**Error Response Format:**

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable error message",
    "details": [
      {
        "field": "name",
        "message": "Field is required"
      }
    ]
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO-8601"
  }
}
```

### 10.2 WebSocket API

| Property | Requirement |
|----------|-------------|
| **Endpoint** | `ws://localhost:8000/ws/{project_id}` |
| **Authentication** | JWT token as query parameter or first message |
| **Heartbeat** | Ping/pong every 30 seconds; disconnect after 3 missed pongs |
| **Reconnection** | Client must implement exponential backoff reconnection |
| **Message Format** | JSON with `type` discriminator field |

**WebSocket Message Types:**

| Type | Direction | Purpose |
|------|-----------|---------|
| `agent.started` | Server -> Client | Agent began execution |
| `agent.progress` | Server -> Client | Agent progress update (streaming) |
| `agent.completed` | Server -> Client | Agent finished execution |
| `agent.error` | Server -> Client | Agent encountered an error |
| `graph.updated` | Server -> Client | Execution graph state changed |
| `file.created` | Server -> Client | New file generated |
| `file.modified` | Server -> Client | Existing file modified |
| `log.entry` | Server -> Client | Log line from agent |
| `user.input` | Client -> Server | Human-in-the-loop response |
| `user.command` | Client -> Server | User command (pause, resume, abort) |

**WebSocket Message Schema:**

```json
{
  "type": "agent.progress",
  "timestamp": "ISO-8601",
  "project_id": "uuid",
  "payload": {
    "agent_id": "uuid",
    "agent_type": "coder",
    "message": "Implementing authentication module...",
    "progress_pct": 45,
    "tokens_used": 12500,
    "files_modified": ["src/auth/handler.py"]
  }
}
```

### 10.3 MCP (Model Context Protocol) Integration

| Property | Requirement |
|----------|-------------|
| **Purpose** | Expose CodeBot tools and data sources to LLM agents via standardized protocol |
| **Transport** | stdio (for CLI agents), SSE (for web-based agents) |
| **SDK** | `mcp` Python SDK >= 1.0.0 (`pip install mcp`) |

**MCP Servers Provided by CodeBot:**

| Server Name | Tools Exposed |
|-------------|---------------|
| `codebot-project` | `get_project_structure`, `read_file`, `write_file`, `search_codebase` |
| `codebot-git` | `git_status`, `git_diff`, `git_commit`, `git_branch`, `git_log` |
| `codebot-test` | `run_tests`, `get_coverage`, `get_test_results` |
| `codebot-security` | `run_semgrep`, `run_trivy`, `run_gitleaks`, `get_scan_results` |
| `codebot-memory` | `search_memory`, `save_memory`, `get_context` |

### 10.4 gRPC (Optional -- High-Performance Inter-Service)

| Property | Requirement |
|----------|-------------|
| **Version** | gRPC 1.68+ |
| **Language** | Go (server), Python (client) |
| **Use Cases** | Vector similarity search, high-throughput embedding ingestion, inter-service agent communication |
| **Protocol** | Protocol Buffers v3 |
| **TLS** | Required for production; optional for local development |

---

## 11. Security Requirements

### 11.1 API Key Management

| Property | Requirement |
|----------|-------------|
| **Encryption at Rest** | AES-256-GCM |
| **Key Derivation** | PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP 2023 recommendation) or Argon2id |
| **Master Key Storage** | Environment variable (`CODEBOT_MASTER_KEY`) or system keychain (macOS Keychain, Linux Secret Service) |
| **Key Rotation** | Support for manual rotation without downtime; old keys remain valid for a configurable grace period (default 24 hours) |
| **Access Pattern** | Decrypted keys held in memory only during active use; zeroed after use |

**Key Storage Schema:**

```json
{
  "provider": "openai",
  "encrypted_key": "base64-encoded-ciphertext",
  "iv": "base64-encoded-iv",
  "tag": "base64-encoded-auth-tag",
  "algorithm": "AES-256-GCM",
  "kdf": "PBKDF2-HMAC-SHA256",
  "kdf_iterations": 600000,
  "created_at": "ISO-8601",
  "rotated_at": "ISO-8601",
  "last_used_at": "ISO-8601"
}
```

### 11.2 Transport Security

| Property | Requirement |
|----------|-------------|
| **TLS Version** | TLS 1.3 (minimum TLS 1.2) |
| **Certificate** | Let's Encrypt (production) or self-signed (development) |
| **HSTS** | Enabled with `max-age=31536000; includeSubDomains` |
| **Cipher Suites** | TLS 1.3: `TLS_AES_256_GCM_SHA384`, `TLS_CHACHA20_POLY1305_SHA256` |

### 11.3 Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| **Admin** | Full system access; manage users, API keys, settings; view audit logs |
| **Developer** | Create/manage projects; start/pause/resume execution; view logs and artifacts |
| **Viewer** | Read-only access to projects, logs, and artifacts |
| **Service Account** | API access only; scoped to specific projects; no UI access |

**Permission Matrix:**

| Resource | Admin | Developer | Viewer | Service |
|----------|-------|-----------|--------|---------|
| Create project | Yes | Yes | No | Yes (scoped) |
| Start execution | Yes | Yes | No | Yes (scoped) |
| View logs | Yes | Yes | Yes | Yes (scoped) |
| Download artifacts | Yes | Yes | Yes | Yes (scoped) |
| Manage API keys | Yes | No | No | No |
| Manage users | Yes | No | No | No |
| View audit logs | Yes | No | No | No |
| System settings | Yes | No | No | No |

### 11.4 Sandbox Execution

All generated code must execute within a sandboxed environment:

| Property | Requirement |
|----------|-------------|
| **Isolation** | Docker container with `--network=none` (default) |
| **Filesystem** | Read-only root filesystem; writable `/tmp` (tmpfs, 512 MB max) |
| **Syscall Filter** | seccomp profile restricting dangerous syscalls (`ptrace`, `mount`, `reboot`, etc.) |
| **Resource Limits** | 2 GB RAM, 2 CPU cores, 256 PIDs, 300s timeout |
| **User** | Non-root user (UID 1000) inside container |
| **Capabilities** | All Linux capabilities dropped; none added |

### 11.5 Audit Logging

| Event Category | Examples | Retention |
|----------------|----------|-----------|
| **Authentication** | Login, logout, token refresh, failed login | 90 days |
| **Authorization** | Permission denied, role change | 90 days |
| **Agent Execution** | Agent start, complete, error, file write | 365 days |
| **Data Access** | API key decryption, artifact download | 365 days |
| **Configuration** | Settings change, user management | 365 days |
| **Security** | Secret detected, vulnerability found, scan results | 365 days |

**Audit Log Entry Schema:**

```json
{
  "id": "uuid",
  "timestamp": "ISO-8601",
  "level": "INFO",
  "category": "agent_execution",
  "actor": {
    "type": "agent",
    "id": "coder-agent-abc123",
    "user_id": "user-uuid"
  },
  "action": "file.write",
  "resource": {
    "type": "file",
    "path": "src/auth/handler.py",
    "project_id": "project-uuid"
  },
  "details": {
    "bytes_written": 2048,
    "file_hash": "sha256:..."
  },
  "request_id": "uuid",
  "ip_address": "127.0.0.1"
}
```

### 11.6 Pre-Commit Secret Scanning

| Property | Requirement |
|----------|-------------|
| **Tool** | Gitleaks (see Section 6.4.1) |
| **Hook** | `pre-commit` framework hook |
| **Scope** | All staged files |
| **Action on Detection** | Block commit; display detected secret location; prompt for remediation |
| **Custom Rules** | Detect CodeBot-specific patterns (e.g., `CODEBOT_MASTER_KEY`, internal API tokens) |

**Pre-Commit Configuration (`.pre-commit-config.yaml`):**

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.0
    hooks:
      - id: gitleaks
        name: gitleaks
        description: Detect secrets in staged changes
        entry: gitleaks protect --staged --verbose
        language: golang
        pass_filenames: false
```

---

## 12. Monitoring & Observability

### 12.1 Distributed Tracing (OpenTelemetry)

| Property | Requirement |
|----------|-------------|
| **SDK** | `opentelemetry-sdk` >= 1.28.0, `opentelemetry-api` >= 1.28.0 |
| **Exporter** | OTLP (gRPC or HTTP) to Jaeger, Grafana Tempo, or Datadog |
| **Auto-Instrumentation** | FastAPI, httpx, SQLAlchemy, Redis |
| **Custom Spans** | Agent execution, LLM API calls, tool invocations, file operations |
| **Sampling** | Configurable; default 100% in dev, 10% in prod (always sample errors) |
| **Install** | `pip install opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-fastapi` |

**Tracing Hierarchy:**

```
Project Run (root span)
  |-- Planner Agent (span)
  |     |-- LLM Call: Claude Opus (span)
  |     |-- Tool: Read PRD (span)
  |     +-- Output: Task Breakdown (span)
  |-- Architect Agent (span)
  |     |-- LLM Call: GPT-4.1 (span)
  |     |-- Tool: Search Codebase (span)
  |     +-- Output: Architecture Doc (span)
  |-- Coder Agent (span)
  |     |-- Claude Code Session (span)
  |     |     |-- Tool: Write File (span)
  |     |     |-- Tool: Run Tests (span)
  |     |     +-- Tool: Fix Errors (span)
  |     +-- Output: Generated Files (span)
  |-- Tester Agent (span)
  |     |-- pytest Execution (span)
  |     +-- Coverage Report (span)
  +-- Project Manager Agent (span)
        |-- Status Report Generation (span)
        |-- Timeline Tracking (span)
        +-- Blocker Identification (span)
```

**Required Span Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `codebot.project_id` | string | Project identifier |
| `codebot.agent.type` | string | Agent type (planner, coder, tester, etc.) |
| `codebot.agent.id` | string | Agent instance identifier |
| `codebot.llm.provider` | string | LLM provider (openai, anthropic, google) |
| `codebot.llm.model` | string | Model identifier |
| `codebot.llm.input_tokens` | int | Input token count |
| `codebot.llm.output_tokens` | int | Output token count |
| `codebot.llm.cost_usd` | float | Estimated cost in USD |
| `codebot.llm.latency_ms` | int | LLM response latency in milliseconds |

### 12.2 Metrics (Prometheus)

| Property | Requirement |
|----------|-------------|
| **Client Library** | `prometheus-client` >= 0.21.0 (`pip install prometheus-client`) |
| **Endpoint** | `/metrics` on the FastAPI server |
| **Format** | Prometheus text exposition format |
| **Scrape Interval** | 15 seconds (recommended) |

**Core Metrics:**

| Metric Name | Type | Description |
|-------------|------|-------------|
| `codebot_agent_executions_total` | Counter | Total agent executions by type and status |
| `codebot_agent_execution_duration_seconds` | Histogram | Agent execution duration distribution |
| `codebot_llm_requests_total` | Counter | LLM API requests by provider, model, and status |
| `codebot_llm_request_duration_seconds` | Histogram | LLM API latency distribution |
| `codebot_llm_tokens_total` | Counter | Tokens consumed by provider, model, and direction (input/output) |
| `codebot_llm_cost_usd_total` | Counter | Cumulative LLM cost in USD by provider and model |
| `codebot_llm_rate_limit_hits_total` | Counter | Rate limit rejections by provider |
| `codebot_projects_active` | Gauge | Currently active projects |
| `codebot_sandbox_containers_active` | Gauge | Currently running sandbox containers |
| `codebot_files_generated_total` | Counter | Total files generated by language |
| `codebot_test_results_total` | Counter | Test results by status (pass/fail/skip) |
| `codebot_security_findings_total` | Counter | Security findings by severity |
| `codebot_cache_hits_total` | Counter | Cache hit/miss by namespace |
| `codebot_cache_hit_ratio` | Gauge | Cache hit ratio over sliding window |

### 12.3 Structured Logging

| Property | Requirement |
|----------|-------------|
| **Library** | `structlog` >= 24.4.0 (`pip install structlog`) |
| **Format** | JSON lines (production), colored human-readable (development) |
| **Output** | stdout (containerized), file rotation (standalone) |
| **Log Levels** | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| **Default Level** | `INFO` (production), `DEBUG` (development) |
| **Correlation** | Every log entry includes `request_id`, `project_id`, `agent_id` where applicable |

**Log Entry Schema:**

```json
{
  "timestamp": "2026-03-18T10:30:00.000Z",
  "level": "info",
  "event": "agent.execution.started",
  "logger": "codebot.agents.coder",
  "project_id": "proj-abc123",
  "agent_id": "agent-def456",
  "agent_type": "coder",
  "task_id": "task-ghi789",
  "request_id": "req-jkl012",
  "message": "Starting code generation for authentication module",
  "context": {
    "model": "claude-sonnet-4-20250514",
    "worktree": "/tmp/codebot/worktrees/agent-coder-def456",
    "files_in_scope": 12
  }
}
```

### 12.4 Token Usage & Cost Tracking

| Property | Requirement |
|----------|-------------|
| **Granularity** | Per-request, per-agent, per-task, per-project |
| **Storage** | Relational database (`agent_runs` table) |
| **Dashboard** | Real-time cost widget in web dashboard |
| **Alerts** | Configurable budget thresholds per project and per billing period |
| **Reporting** | Daily and monthly cost summaries; CSV export |

**Cost Calculation Model:**

```python
cost_per_1k_tokens = {
    "openai": {
        "gpt-4.1":       {"input": 0.002, "output": 0.008},
        "gpt-4.1-mini":  {"input": 0.0004, "output": 0.0016},
        "gpt-4.1-nano":  {"input": 0.0001, "output": 0.0004},
        "o3":            {"input": 0.002, "output": 0.008},
        "o4-mini":       {"input": 0.00011, "output": 0.00044},
    },
    "anthropic": {
        "claude-opus-4":   {"input": 0.015, "output": 0.075},
        "claude-sonnet-4": {"input": 0.003, "output": 0.015},
        "claude-haiku-3.5": {"input": 0.0008, "output": 0.004},
    },
    "google": {
        "gemini-2.5-pro":   {"input": 0.00125, "output": 0.01},
        "gemini-2.5-flash": {"input": 0.00015, "output": 0.0006},
    },
}
```

**Budget Alert Configuration:**

```yaml
cost_alerts:
  project_budget:
    warning_threshold_usd: 50.00
    critical_threshold_usd: 100.00
    action_on_critical: "pause"  # pause, warn, or continue
  monthly_budget:
    warning_threshold_usd: 500.00
    critical_threshold_usd: 1000.00
    action_on_critical: "warn"
  per_agent_run:
    max_cost_usd: 10.00
    action_on_exceeded: "terminate"
```

---

## 13. Compatibility Matrix

### 13.1 Operating System Support

| OS | Version | Architecture | Support Level | Notes |
|----|---------|--------------|---------------|-------|
| **macOS** | 14.0+ (Sonoma) | ARM64 (Apple Silicon) | Tier 1 (Full) | Primary development platform |
| **macOS** | 14.0+ (Sonoma) | x86_64 (Intel) | Tier 1 (Full) | Rosetta 2 compatible |
| **Ubuntu** | 22.04 LTS, 24.04 LTS | x86_64, ARM64 | Tier 1 (Full) | Primary production platform |
| **Debian** | 12 (Bookworm) | x86_64, ARM64 | Tier 1 (Full) | |
| **Fedora** | 40, 41 | x86_64 | Tier 2 (Supported) | Community tested |
| **Windows** | 11 23H2+ | x86_64 | Tier 2 (Supported) | Requires WSL2 for Docker sandbox features |
| **Windows** | 11 23H2+ (WSL2) | x86_64 | Tier 1 (Full) | Ubuntu 24.04 WSL2 recommended |
| **Alpine Linux** | 3.20+ | x86_64, ARM64 | Tier 3 (Container Only) | For Docker images only; not for development |

**Support Level Definitions:**

| Level | Definition |
|-------|------------|
| **Tier 1 (Full)** | Actively tested in CI; all features supported; bugs treated as high priority |
| **Tier 2 (Supported)** | Periodically tested; core features supported; bugs treated as normal priority |
| **Tier 3 (Container Only)** | Supported only as a Docker container base image; no native development support |

### 13.2 Python Version Matrix

| Python Version | Support Status | Notes |
|----------------|----------------|-------|
| 3.10 | Not Supported | Missing required stdlib features (`tomllib`, `ExceptionGroup`) |
| 3.11 | Not Supported | Missing performance improvements from 3.12 specializing interpreter |
| **3.12** | **Supported (Minimum)** | All features available; primary test target |
| **3.13** | **Supported** | Tested; experimental free-threading support available |
| 3.14 | Experimental | May work; not tested in CI |

### 13.3 Node.js Version Matrix

| Node.js Version | Support Status | Notes |
|-----------------|----------------|-------|
| 18.x | Not Supported | EOL April 2025 |
| 20.x | Not Supported | Lacks required ESM and fetch stability |
| **22.x LTS** | **Supported (Minimum)** | Primary test target; LTS through April 2027 |
| 23.x | Experimental | May work; not tested in CI |

### 13.4 Docker Version Matrix

| Docker Version | Support Status | Notes |
|----------------|----------------|-------|
| 23.x | Not Supported | Missing required BuildKit features |
| **24.x** | **Supported (Minimum)** | All features available |
| **25.x** | **Supported** | Tested |
| **26.x** | **Supported** | Tested |
| **27.x** | **Supported (Recommended)** | Primary test target |

### 13.5 Git Version Matrix

| Git Version | Support Status | Notes |
|-------------|----------------|-------|
| 2.39 | Not Supported | Missing worktree improvements |
| **2.40** | **Supported (Minimum)** | Worktree management improvements |
| **2.41 - 2.46** | **Supported** | All features available |
| **2.47** | **Supported (Recommended)** | Primary test target |

### 13.6 Database Compatibility

| Database | Minimum Version | Recommended Version | Use Case |
|----------|-----------------|---------------------|----------|
| SQLite | 3.45.0 | 3.47.x | Development metadata |
| PostgreSQL | 16.0 | 16.x (latest) | Production metadata |
| Redis | 7.4.0 | 7.4.x (latest) | Caching, pub/sub |
| ChromaDB | 0.5.0 | 0.5.x (latest) | Development vector store |
| Weaviate | 1.27.0 | 1.27.x (latest) | Production vector store |

---

## 14. Platform Observability Requirements

CodeBot requires comprehensive observability across all platform components to ensure operational visibility, debugging capability, and performance monitoring.

| Signal | Technology | Purpose |
|--------|------------|---------|
| Metrics | Prometheus + Grafana | Agent throughput, token usage, cost, latency, error rates |
| Logs | Structured JSON → stdout | Agent actions, LLM calls, tool invocations |
| Traces | OpenTelemetry → Jaeger | End-to-end request tracing across agents |
| Events | Event bus + WebSocket | Real-time pipeline state to dashboard |
| Alerts | Prometheus Alertmanager | Budget exhaustion, agent failures, pipeline stalls |

---

## 15. Authentication & Authorization

CodeBot itself requires robust authentication and authorization for all interactive and programmatic access.

### 15.1 Authentication Methods

| Method | Algorithm | Use Case |
|--------|-----------|----------|
| **JWT** | RS256 | Interactive sessions (web dashboard, desktop app) |
| **API Keys** | HMAC-SHA256 | CI/CD pipelines and CLI access |

### 15.2 Token Management

| Property | Requirement |
|----------|-------------|
| **Access Token Expiry** | 1 hour |
| **Refresh Token** | Rotation on each use; previous token invalidated |
| **Token Storage** | HttpOnly secure cookies (web); OS keychain (CLI/desktop) |

### 15.3 Authorization

| Property | Requirement |
|----------|-------------|
| **Model** | Role-Based Access Control (RBAC) |
| **Roles** | `admin`, `user`, `viewer` |
| **MFA** | Optional TOTP-based MFA for admin accounts |
| **Audit** | All authentication and authorization events logged to the audit log |

---

## 16. Error Handling Requirements

### 16.1 Error Taxonomy

| Error Class | Description | Handling Strategy |
|-------------|-------------|-------------------|
| **Transient** | Temporary failures (network timeouts, rate limits) | Retry with exponential backoff (max 3 retries) |
| **Recoverable** | Failures that can be resolved with alternative approaches | Fallback to alternative provider/model or agent re-run |
| **Blocking** | Failures that prevent a single agent from proceeding | Escalate to orchestrator; skip or reassign task |
| **Fatal** | Unrecoverable system-level failures | Halt pipeline; notify user; persist state for resume |
| **Quality Gate** | Output fails quality or security checks | Route back to originating agent with feedback |

### 16.2 Resilience Patterns

| Pattern | Configuration |
|---------|---------------|
| **Dead Letter Queue** | Unprocessable messages routed to DLQ for manual inspection and replay |
| **Circuit Breaker** | Per LLM provider; opens after 5 consecutive failures; half-open probe after 60 seconds |
| **Retry Policy** | Max 3 retries with exponential backoff (base 1s, max 30s, jitter enabled) for transient errors |

---

## 17. Data Retention Requirements

| Data Category | Retention Period | Notes |
|---------------|------------------|-------|
| Agent logs | 90 days | Rotated and compressed after 7 days |
| LLM request/response | 30 days | Includes prompt, completion, token counts, and cost |
| Event bus messages | 7 days | Real-time pipeline events |
| Security scan results | 1 year | SAST, DAST, dependency, and license scan outputs |
| Build artifacts | 30 days post-completion | Generated binaries, Docker images, and deployment bundles |

---

## 18. Prompt Engineering Requirements

### 18.1 Prompt Storage and Versioning

| Property | Requirement |
|----------|-------------|
| **Location** | `templates/prompts/` directory in the CodeBot repository |
| **Versioning** | All prompts version-controlled in Git; semantic versioning for major prompt changes |
| **Format** | Jinja2 or Mustache templates with variable interpolation |

### 18.2 Prompt Structure

All agent prompts must follow the standard structure:

1. **Role** -- Define the agent's persona and expertise
2. **Context** -- Provide relevant project and task context
3. **Instructions** -- Step-by-step task instructions
4. **Constraints** -- Boundaries, limitations, and guardrails
5. **Output Format** -- Expected response structure and schema

### 18.3 Token Budget

| Property | Requirement |
|----------|-------------|
| **L0 system prompt** | L0 prompt + system prompt combined must not exceed 4,096 tokens |
| **Measurement** | Token count validated at prompt build time using `tiktoken` or provider tokenizer |

### 18.4 Prompt Testing

| Property | Requirement |
|----------|-------------|
| **Test Suites** | Each prompt must have an associated test suite validating expected outputs |
| **Regression Testing** | Prompt changes trigger regression tests before merge |
| **Evaluation Metrics** | Accuracy, format compliance, and safety checks |

---

## 19. Agent Safety Requirements

### 19.1 Creator Sandboxing

Skill, Hook, and Tool creators (agents that produce new executable artifacts) must operate within a sandboxed environment:

| Property | Requirement |
|----------|-------------|
| **Execution Sandbox** | All creator agents run inside restricted containers (see Section 11.4) |
| **Artifact Review** | Created artifacts must be reviewed (automated + optional human) before activation |
| **Artifact Limit** | Maximum 5 new artifacts (skills, hooks, or tools) per pipeline run |

### 19.2 Prohibited Actions

Creator agents must NOT be allowed to:

| Prohibition | Enforcement |
|-------------|-------------|
| **Access credentials** | No environment variable access to API keys or secrets; credential store inaccessible |
| **Modify prompts** | System and agent prompts are read-only to creator agents |
| **Bypass security** | Security scanning and review gates cannot be skipped or disabled by any agent |

---

## 20. Offline Mode Requirements

CodeBot must support an offline mode for air-gapped environments, local development without internet, and privacy-sensitive deployments.

### 20.1 Local LLM Requirements

| Property | Requirement |
|----------|-------------|
| **Minimum Model Size** | 13B+ parameters (self-hosted via Ollama, vLLM, or llama.cpp) |
| **Recommended Models** | CodeLlama 34B, DeepSeek Coder 33B, or equivalent |
| **Inference Backend** | Ollama (preferred), vLLM, or llama.cpp with OpenAI-compatible API |

### 20.2 Auto-Disabled Features

The following features must be automatically disabled when offline mode is active:

| Feature | Reason |
|---------|--------|
| GitHub integration | Requires network access to GitHub API |
| Cloud deployment | Requires network access to cloud providers |
| Remote template registry | Cannot fetch remote templates without network |
| External research agent | Web search and URL fetching unavailable |

### 20.3 Offline Infrastructure

| Property | Requirement |
|----------|-------------|
| **Dependencies** | Pre-cached; all Python and Node.js packages available locally |
| **Vector Store** | Local ChromaDB instance (embedded mode) |
| **UI/CLI Indicator** | Offline mode clearly indicated in both web dashboard and CLI output |

---

## 21. Appendix

### 21.1 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CODEBOT_MASTER_KEY` | Yes | None | Master encryption key for API key storage |
| `CODEBOT_ENV` | No | `development` | Environment: `development`, `staging`, `production` |
| `CODEBOT_LOG_LEVEL` | No | `INFO` | Logging level |
| `CODEBOT_DATA_DIR` | No | `~/.codebot` | Base directory for CodeBot data |
| `OPENAI_API_KEY` | Conditional | None | OpenAI API key (required if using OpenAI models) |
| `ANTHROPIC_API_KEY` | Conditional | None | Anthropic API key (required if using Anthropic models) |
| `GOOGLE_API_KEY` | Conditional | None | Google AI API key (required if using Google models) |
| `DATABASE_URL` | No | `sqlite:///~/.codebot/metadata.db` | Database connection string |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection URL |
| `VECTOR_DB_URL` | No | None (embedded ChromaDB) | Vector database connection URL |
| `CODEBOT_API_HOST` | No | `0.0.0.0` | API server bind host |
| `CODEBOT_API_PORT` | No | `8000` | API server bind port |
| `CODEBOT_SANDBOX_IMAGE` | No | `codebot-sandbox:latest` | Docker image for code execution sandbox |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | `http://localhost:4317` | OpenTelemetry collector endpoint |

### 21.2 Configuration File Structure

CodeBot uses a layered configuration system with the following precedence (highest to lowest):

1. Command-line arguments
2. Environment variables
3. Project-level config (`{project}/.codebot/config.toml`)
4. User-level config (`~/.codebot/config.toml`)
5. System defaults

**Example `config.toml`:**

```toml
[general]
environment = "development"
log_level = "DEBUG"
data_dir = "~/.codebot"

[api]
host = "0.0.0.0"
port = 8000
cors_origins = ["http://localhost:5173"]

[llm]
default_provider = "anthropic"
default_model = "claude-sonnet-4-20250514"
max_retries = 5
timeout_seconds = 120
streaming = true

[llm.providers.openai]
api_key_env = "OPENAI_API_KEY"
models = ["gpt-4.1", "gpt-4.1-mini", "o3", "o4-mini"]

[llm.providers.anthropic]
api_key_env = "ANTHROPIC_API_KEY"
models = ["claude-opus-4-20250514", "claude-sonnet-4-20250514", "claude-haiku-3-5-20241022"]

[llm.providers.google]
api_key_env = "GOOGLE_API_KEY"
models = ["gemini-2.5-pro", "gemini-2.5-flash"]

[database]
url = "sqlite:///~/.codebot/metadata.db"

[redis]
url = "redis://localhost:6379/0"

[vector_db]
backend = "chroma"
persist_dir = "~/.codebot/chroma"

[sandbox]
enabled = true
image = "codebot-sandbox:latest"
memory_limit = "2g"
cpu_limit = "2.0"
timeout_seconds = 300
network = "none"

[security]
secret_scanning = true
sast_on_generate = true
dependency_scan = true
license_check = true

[monitoring]
tracing_enabled = true
metrics_enabled = true
otel_endpoint = "http://localhost:4317"
```

### 21.3 Dependency Installation Quick Reference

**Python Environment Setup:**

```bash
# Install uv (package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv --python 3.12
source .venv/bin/activate

# Install all Python dependencies
uv pip install -r requirements.txt

# Or install individual groups
uv pip install -r requirements/core.txt      # Orchestration + API
uv pip install -r requirements/llm.txt       # LLM provider SDKs
uv pip install -r requirements/security.txt  # Security scanning tools
uv pip install -r requirements/dev.txt       # Development/testing tools
```

**Node.js Environment Setup:**

```bash
# Install pnpm
corepack enable && corepack prepare pnpm@latest --activate

# Install dashboard dependencies
cd dashboard && pnpm install

# Install CLI dependencies
cd cli && pnpm install
```

**Infrastructure Setup:**

```bash
# Start all services (development)
docker compose up -d

# Services started: PostgreSQL, Redis, ChromaDB, SonarQube
```

### 21.4 Version Pinning Policy

| Dependency Category | Pinning Strategy | Update Frequency |
|---------------------|------------------|------------------|
| **Runtime (Python, Node)** | Minor version pinned (e.g., `3.12.x`) | Quarterly evaluation |
| **Core Frameworks** | Compatible release (`>=X.Y.0, <X+1.0.0`) | Monthly evaluation |
| **LLM SDKs** | Compatible release | Weekly evaluation (fast-moving) |
| **Security Tools** | Latest stable | Monthly update |
| **Dev Tools** | Latest stable | As needed |

**Lock File Requirements:**

- Python: `uv.lock` (preferred) or `requirements.txt` with exact hashes
- Node.js: `pnpm-lock.yaml` committed to repository
- Docker: Pinned base image digests in production Dockerfiles

---

*End of Technical Requirements Document*
