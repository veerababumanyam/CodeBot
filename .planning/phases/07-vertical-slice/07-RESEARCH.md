# Phase 7: Vertical Slice - Research

**Researched:** 2026-03-18
**Domain:** End-to-end multi-agent pipeline integration -- NLP requirement extraction, LLM-driven code generation, automated code review, test generation/execution, debug-fix loop with experiment semantics
**Confidence:** HIGH

## Summary

Phase 7 is the architectural validation phase for CodeBot. It wires together a minimal 5-agent pipeline (Orchestrator, Backend Dev, Code Reviewer, Tester, Debugger) that proves the full stack end-to-end: graph engine (Phase 2), agent framework (Phase 3), LLM abstraction (Phase 4), context management (Phase 5), and pipeline orchestration (Phase 6). A user describes a project idea in natural language, and the system extracts requirements, generates Python/FastAPI code, reviews it, tests it, and iteratively fixes failures -- all without human intervention beyond the initial input.

The core technical challenges in this phase are: (1) building the NLP requirement extraction pipeline that turns natural language into structured functional requirements and acceptance criteria (INPT-01, INPT-02, INPT-04, INPT-05), (2) implementing 5 concrete BaseAgent subclasses that exercise the PRA cognitive cycle with real LLM calls via LiteLLM, (3) composing these agents into a pipeline graph that executes through the Temporal workflow orchestration, (4) implementing the experiment-based debug-fix loop (ExperimentLoop) with keep/discard semantics, and (5) emitting events to NATS JetStream throughout the pipeline for observability. This phase does NOT build the full set of 30 agents, security pipeline, worktree isolation, or UI -- those come in Phases 8-11.

The key insight is that this phase is an integration phase, not a greenfield build. All the foundational infrastructure (graph engine, agent framework, LLM abstraction, context management, pipeline orchestration) should exist from Phases 2-6. Phase 7's job is to implement 5 concrete agent classes, compose them into a working pipeline graph, and validate that the entire architecture holds together. The "vertical slice" must be narrow (single project type: greenfield Python/FastAPI) but deep (requirement extraction through tested code).

**Primary recommendation:** Implement the 5 agents as concrete BaseAgent subclasses in `apps/server/src/codebot/agents/`, compose them in a pipeline graph definition in `configs/pipelines/vertical-slice.yaml`, and drive execution through the Temporal SDLC workflow. Use LiteLLM + instructor for structured output extraction. Use the project's own pytest infrastructure for the Tester agent's test execution (recursive but controlled). The Debugger agent implements the ExperimentLoop from SYSTEM_DESIGN.md Section 10 with experiment branches, baseline comparison, and circuit breakers.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INPT-01 | User can describe project idea in natural language | Orchestrator agent accepts natural language input, passes to NLP extraction pipeline using LiteLLM + Pydantic structured output |
| INPT-02 | System accepts structured PRDs in Markdown, JSON, or YAML | Orchestrator agent detects input format (plain text vs structured), parses accordingly using format detection heuristic + Pydantic validators |
| INPT-04 | System extracts functional requirements, NFRs, constraints, and acceptance criteria via NLP | LLM-powered extraction with instructor/Pydantic models defining the output schema; multi-pass extraction for completeness |
| INPT-05 | System initiates clarification loop when requirements are ambiguous or incomplete | Orchestrator agent evaluates extraction confidence scores; low-confidence items trigger a clarification request via HumanInLoopNode or auto-inference with disclaimer |
| IMPL-02 | Backend agent generates Python/FastAPI server code from API specs | Backend Dev agent (BaseAgent subclass) uses LLM to generate FastAPI endpoints, models, and business logic; validates against ruff + mypy |
| IMPL-07 | Generated code follows project style conventions and linting rules | Backend Dev agent runs `ruff check` and `ruff format` as post-generation validation; re-prompts LLM with lint errors on failure |
| QA-01 | Code Review agent reviews generated code for correctness, patterns, and maintainability | Code Reviewer agent (BaseAgent subclass) analyzes code with LLM for patterns, correctness, architecture conformance; outputs structured review comments |
| QA-06 | Quality gates must pass before code advances to Testing phase | Pipeline orchestration enforces gate between QA and Testing phases; Code Reviewer's quality gate result (pass/fail) determines advancement |
| TEST-01 | Test Generator creates unit tests with >= 80% line coverage target | Tester agent generates pytest unit tests using LLM, executes them, measures coverage with coverage.py, iterates if below threshold |
| TEST-02 | Test Generator creates integration tests for API endpoints and data flows | Tester agent generates httpx.AsyncClient integration tests for FastAPI endpoints, executes with pytest |
| TEST-05 | Test results feed back to Debug phase when failures detected | Pipeline graph routes failed test results to Debugger agent via SharedState; gate G7 auto-passes test results to debug phase |
| DBUG-01 | Debugger performs root cause analysis on test failures | Debugger agent parses stack traces, reads affected source code, uses LLM for root cause identification with structured FailureAnalysis output |
| DBUG-02 | Debugger generates fix proposals and applies them | Debugger generates targeted patches via LLM, applies to experiment branch, commits with hypothesis as message |
| DBUG-03 | Fix-test loop iterates until all tests pass or max retries exceeded | ExperimentLoop (LoopNode in graph) iterates: hypothesize -> branch -> fix -> measure -> keep/discard; circuit breakers on time/token/no-improvement |
| EVNT-01 | NATS JetStream pub/sub for all inter-agent messaging | All agent state transitions, pipeline phase transitions, and gate decisions emit events to NATS JetStream via PipelineEventEmitter from Phase 6 |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| litellm | 1.82.4 | Provider-agnostic LLM interface | Already chosen for Phase 4 (LLM-01); supports 100+ providers, structured output, cost tracking |
| instructor | 1.14.5 | Structured output extraction from LLMs | Top library for validated Pydantic output from LLMs; integrates with LiteLLM; automatic retry on validation failure |
| pydantic | >=2.9.0 | Schema definitions for extracted requirements, agent I/O | Already project standard; all API/config schemas use Pydantic v2 |
| temporalio | 1.23.0 | Pipeline workflow orchestration | Phase 6 deliverable; provides durable execution for the vertical slice pipeline |
| nats-py | 2.14.0 | Event emission for inter-agent messaging | Phase 6 deliverable; EVNT-01 requires NATS JetStream |
| ruff | (already in project) | Lint and format validation for generated code | IMPL-07 requires style enforcement; `ruff check` + `ruff format` |
| mypy | (already in project) | Type checking for generated code | IMPL-07 requires type checking; `mypy --strict` |
| pytest | (already in project) | Test execution for generated tests | TEST-01/02 require test execution; project standard test framework |
| coverage | (already in project) | Code coverage measurement | TEST-01 requires >= 80% line coverage measurement |
| httpx | (already in project) | Async HTTP client for integration tests | TEST-02 requires API endpoint testing; `httpx.AsyncClient` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-json-report | 1.6.0 | Structured JSON test output for parsing | When Tester agent needs to parse test results programmatically |
| pytest-cov | (already in project) | Coverage integration with pytest | When running coverage alongside test execution |
| gitpython | >=3.1.0 | Git operations for experiment branches | When Debugger creates/merges/deletes experiment branches |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| instructor for structured output | Raw LiteLLM JSON mode | instructor handles validation retries automatically, catches malformed JSON; raw JSON mode requires manual retry logic |
| pytest-json-report | Custom stdout parsing | JSON report is machine-parseable, deterministic; stdout parsing is fragile across pytest versions |
| GitPython for experiment branches | subprocess git calls | GitPython provides typed API; subprocess is simpler but requires manual error parsing. Either works for Phase 7 -- GitPython preferred for consistency with Phase 8 worktree manager |

**Installation:**
```bash
uv add instructor pytest-json-report
# litellm, temporalio, nats-py, ruff, mypy, pytest, coverage, httpx, gitpython already installed from prior phases
```

**Version verification:** instructor 1.14.5 confirmed on PyPI (2026-01-29). litellm 1.82.4 confirmed on PyPI (2026-03-16). pytest-json-report 1.6.0 confirmed stable. All other libraries already in project from Phases 1-6.

## Architecture Patterns

### Recommended Project Structure

```
apps/server/src/codebot/
    agents/
        __init__.py
        orchestrator.py           # Orchestrator agent -- requirement extraction, task graph
        backend_dev.py            # Backend Dev agent -- FastAPI code generation
        code_reviewer.py          # Code Reviewer agent -- code quality review
        tester.py                 # Tester agent -- test generation + execution
        debugger.py               # Debugger agent -- root cause analysis + fix loop
    pipeline/
        vertical_slice.py         # Vertical slice graph builder function
    input/
        __init__.py
        extractor.py              # RequirementExtractor -- NLP extraction with instructor
        models.py                 # Pydantic models: ExtractedRequirements, FunctionalRequirement, AcceptanceCriterion
        clarifier.py              # ClarificationLoop -- ambiguity detection
    testing/
        __init__.py
        runner.py                 # TestRunner wrapper for agent use
        parser.py                 # TestResultParser for JSON report parsing
    debug/
        __init__.py
        analyzer.py               # FailureAnalyzer -- root cause analysis
        fixer.py                  # FixGenerator -- targeted patch generation
        loop_controller.py        # ExperimentLoop controller with circuit breakers
        experiment_logger.py      # TSV experiment log writer

configs/
    pipelines/
        vertical-slice.yaml       # Pipeline config for the 5-agent vertical slice
    agents/
        orchestrator.yaml         # Orchestrator agent YAML config
        backend_dev.yaml          # Backend Dev agent YAML config
        code_reviewer.yaml        # Code Reviewer agent YAML config
        tester.yaml               # Tester agent YAML config
        debugger.yaml             # Debugger agent YAML config

tests/
    unit/
        agents/
            test_orchestrator.py
            test_backend_dev.py
            test_code_reviewer.py
            test_tester.py
            test_debugger.py
        input/
            test_extractor.py
            test_clarifier.py
        debug/
            test_analyzer.py
            test_fixer.py
            test_loop_controller.py
    integration/
        test_vertical_slice_e2e.py    # End-to-end pipeline test with mocked LLM
```

### Pattern 1: Concrete Agent Implementation (BaseAgent Subclass)

**What:** Each of the 5 agents extends BaseAgent from Phase 3, implementing the `perceive()`, `reason()`, `act()`, and `review()` methods of the PRA cognitive cycle.

**When to use:** Every concrete agent in Phase 7.

**Example:**
```python
# apps/server/src/codebot/agents/backend_dev.py
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from agent_sdk.agents.base import BaseAgent, AgentInput, AgentOutput
from agent_sdk.models.enums import AgentType


@dataclass(slots=True, kw_only=True)
class BackendDevAgent(BaseAgent):
    """Generates Python/FastAPI code from extracted requirements."""

    agent_type: AgentType = field(default=AgentType.BACKEND_DEV, init=False)

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Assemble context: requirements, API spec, coding conventions."""
        return {
            "requirements": agent_input.shared_state.get("requirements"),
            "api_spec": agent_input.shared_state.get("api_spec"),
            "conventions": agent_input.context_tiers.get("l0", {}).get("conventions"),
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Use LLM to plan code structure from requirements."""
        # Calls self.llm_provider.complete() with structured prompt
        # Returns: file list, function signatures, data models
        ...

    async def act(self, plan: dict[str, Any]) -> Any:
        """Generate code files, run ruff check + mypy validation."""
        # 1. Generate code via LLM
        # 2. Write to workspace
        # 3. Run ruff check --fix
        # 4. Run mypy --strict
        # 5. If lint/type errors, re-prompt LLM with errors
        ...

    async def review(self, result: Any) -> AgentOutput:
        """Self-review: does generated code compile, lint, and satisfy requirements?"""
        ...
```

### Pattern 2: Structured Requirement Extraction with instructor

**What:** Use instructor + LiteLLM to extract structured requirements from natural language input into validated Pydantic models.

**When to use:** INPT-01, INPT-04 -- the Orchestrator agent's requirement extraction pipeline.

**Example:**
```python
# apps/server/src/codebot/input/extractor.py
from pydantic import BaseModel, Field
import instructor
import litellm


class AcceptanceCriterion(BaseModel):
    """A single testable acceptance criterion."""
    description: str = Field(description="What must be true for this criterion to pass")
    test_strategy: str = Field(description="How to verify: unit test, integration test, or manual")


class FunctionalRequirement(BaseModel):
    """A single functional requirement extracted from user input."""
    id: str = Field(description="Short identifier like FR-01")
    title: str = Field(description="Brief requirement title")
    description: str = Field(description="Detailed requirement description")
    priority: str = Field(description="Must/Should/Could/Won't (MoSCoW)")
    acceptance_criteria: list[AcceptanceCriterion]
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence 0-1")


class ExtractedRequirements(BaseModel):
    """Complete structured output from requirement extraction."""
    project_name: str
    project_description: str
    functional_requirements: list[FunctionalRequirement]
    non_functional_requirements: list[str]
    constraints: list[str]
    ambiguities: list[str] = Field(
        default_factory=list,
        description="Items that are unclear and may need clarification"
    )


class RequirementExtractor:
    """Extract structured requirements from natural language using LLM."""

    def __init__(self, model: str = "anthropic/claude-sonnet-4") -> None:
        self.client = instructor.from_litellm(litellm.completion)
        self.model = model

    async def extract(self, user_input: str) -> ExtractedRequirements:
        """Extract requirements from natural language description."""
        return self.client.chat.completions.create(
            model=self.model,
            response_model=ExtractedRequirements,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior requirements analyst. Extract structured "
                        "software requirements from the user's project description. "
                        "Be thorough: identify functional requirements, non-functional "
                        "requirements, constraints, and testable acceptance criteria. "
                        "Flag any ambiguities that need clarification. "
                        "Assign confidence scores (0-1) to each requirement."
                    ),
                },
                {"role": "user", "content": user_input},
            ],
            max_retries=3,  # instructor auto-retries on validation failure
        )
```

### Pattern 3: ExperimentLoop (Debug-Fix Loop with Keep/Discard)

**What:** The Debugger agent uses experiment semantics: each fix attempt is an isolated git branch. The fix is measured against a baseline. If improved, the branch is merged (KEEP); if degraded, the branch is deleted (DISCARD). This prevents cascading breakage.

**When to use:** DBUG-01, DBUG-02, DBUG-03 -- the debug-fix loop.

**Example:**
```python
# apps/server/src/codebot/debug/loop_controller.py
from dataclasses import dataclass, field


@dataclass(slots=True, kw_only=True)
class ExperimentResult:
    """Result of a single fix experiment."""
    experiment_id: int
    hypothesis: str
    commit_hash: str
    metric_before: float  # test pass rate before fix
    metric_after: float   # test pass rate after fix
    delta: float
    status: str  # "KEEP", "DISCARD", "CRASH", "TIMEOUT"
    diff_lines: int
    duration_seconds: float


@dataclass(slots=True, kw_only=True)
class ExperimentLoopController:
    """Manages the debug-fix experiment loop with circuit breakers."""

    max_experiments: int = 5
    time_budget_seconds: float = 600.0
    max_no_improvement: int = 3
    improvement_threshold: float = 0.01

    experiments: list[ExperimentResult] = field(default_factory=list)

    def should_continue(self, baseline_pass_rate: float, current_pass_rate: float) -> bool:
        """Check circuit breakers."""
        # All tests pass
        if current_pass_rate >= 1.0:
            return False
        # Max experiments reached
        if len(self.experiments) >= self.max_experiments:
            return False
        # Time budget exhausted
        total_time = sum(e.duration_seconds for e in self.experiments)
        if total_time >= self.time_budget_seconds:
            return False
        # Consecutive non-improvements
        recent = self.experiments[-self.max_no_improvement:]
        if len(recent) >= self.max_no_improvement and all(
            e.status == "DISCARD" for e in recent
        ):
            return False
        return True
```

### Pattern 4: Vertical Slice Pipeline Graph

**What:** A pipeline graph definition that chains the 5 agents through the SDLC phases: S0 (Input) -> S5 (Implementation) -> S6 (QA) -> S7 (Testing) -> S8 (Debug/Fix).

**When to use:** The `vertical-slice.yaml` pipeline preset.

**Example:**
```yaml
# configs/pipelines/vertical-slice.yaml
pipeline:
  name: vertical-slice
  version: "1.0"
  description: "Minimal 5-agent pipeline proving end-to-end architecture"
  settings:
    max_parallel_agents: 1  # Sequential for vertical slice
    checkpoint_after_each_phase: true
    cost_limit_usd: 10.0
    timeout_minutes: 30
  phases:
    - name: input_processing
      agents: [orchestrator]
      sequential: true
      human_gate:
        enabled: true
        prompt: "Review extracted requirements before proceeding"
        timeout_minutes: 5
        timeout_action: auto_approve
    - name: implementation
      agents: [backend_dev]
      sequential: true
      human_gate:
        enabled: false
    - name: quality_assurance
      agents: [code_reviewer]
      sequential: true
      on_failure: reroute_to_implement
      human_gate:
        enabled: false
    - name: testing
      agents: [tester]
      sequential: true
      human_gate:
        enabled: false
    - name: debug_fix
      agents: [debugger]
      sequential: true
      loop:
        max_iterations: 5
        exit_condition: all_tests_pass
      on_failure: escalate
      human_gate:
        enabled: false
```

### Pattern 5: Agent YAML Configuration

**What:** Each agent is fully configured via YAML (AGNT-05 from Phase 3), specifying model, tools, context budgets, retry policy, and agent-specific settings.

**When to use:** All 5 agents in the vertical slice.

**Example:**
```yaml
# configs/agents/backend_dev.yaml
agent:
  type: BACKEND_DEV
  model: anthropic/claude-sonnet-4
  fallback_model: openai/gpt-4.1
  max_tokens: 8192
  temperature: 0.1
  system_prompt: |
    You are a senior Python backend developer. Generate clean, well-structured
    FastAPI code following these conventions:
    - Use Pydantic v2 for all request/response models
    - Use async/await for all endpoint handlers
    - Use Google-style docstrings
    - Include comprehensive error handling
    - Follow the repository pattern for data access
  tools:
    - file_read
    - file_write
    - file_edit
    - bash
  context_tiers:
    l0: 2000
    l1: 12000
    l2: 20000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 2
    max_delay_seconds: 60
    exponential_base: 2
  timeout: 600
  settings:
    framework: fastapi
    language: python
    lint_command: "ruff check --fix"
    format_command: "ruff format"
    typecheck_command: "mypy --strict"
    enable_self_test: true
```

### Anti-Patterns to Avoid

- **Implementing all 30 agents in Phase 7:** The vertical slice is explicitly 5 agents. Resist scope creep. The remaining 25 agents come in Phase 9.
- **Skipping the experiment loop for Debugger:** The ExperimentLoop with keep/discard semantics is a core architectural pattern that must be validated here. A simple retry loop does not satisfy DBUG-03.
- **Calling real LLM APIs in unit tests:** CLAUDE.md explicitly requires mocking LLM providers in tests. Use mock responses that return pre-canned structured output.
- **Generating code into the main repository:** Generated code goes into an isolated workspace directory (or git worktree in Phase 8). For Phase 7, use a temporary directory as the workspace.
- **Hardcoding LLM model names in agent code:** Model names come from YAML config (AGNT-05). Agent code references `self.config.model`, never hardcoded strings.
- **Tight coupling between agents:** Agents communicate only through SharedState and the event bus (NATS). No direct method calls between agent instances.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Structured output from LLMs | Custom JSON parsing with regex | instructor + Pydantic models | instructor handles validation retries, malformed JSON recovery, and multi-provider support automatically |
| Test result parsing | Custom stdout regex parser | pytest-json-report + TestResultParser | JSON reports are deterministic, machine-parseable, and pytest-version-independent |
| Git experiment branches | Manual subprocess chains | GitPython Repo API | GitPython provides typed error handling, branch management, and merge operations without shell escaping issues |
| Pipeline durability | Custom checkpoint files | Temporal workflows (Phase 6) | Temporal provides crash recovery, retry, and resume -- already built in Phase 6 |
| LLM cost tracking | Custom token counter | LiteLLM response_cost attribute | LiteLLM tracks cost per-call across all providers; no need for manual price tables |
| Retry with backoff | Custom sleep loops | instructor max_retries (for LLM) + Temporal RetryPolicy (for pipeline) | Both handle structured retry with backoff; instructor specifically retries on Pydantic validation failure |

**Key insight:** Phase 7 is an integration phase. The infrastructure is built (Phases 2-6). The vertical slice should integrate existing infrastructure, not rebuild it. Every "don't hand-roll" item has already been addressed in a prior phase or by a purpose-built library.

## Common Pitfalls

### Pitfall 1: LLM Output Not Matching Pydantic Schema

**What goes wrong:** The LLM generates JSON that doesn't match the expected Pydantic model (missing fields, wrong types, extra fields).
**Why it happens:** LLMs are probabilistic; they don't reliably produce exact schema matches, especially with complex nested models.
**How to avoid:** Use instructor with `max_retries=3`. instructor catches Pydantic ValidationError, sends the error message back to the LLM, and re-requests. Keep Pydantic models flat where possible; deeply nested models increase failure rate.
**Warning signs:** Frequent `ValidationError` exceptions even with retries; overly complex Pydantic models with many nested levels.

### Pitfall 2: Generated Code That Doesn't Import Correctly

**What goes wrong:** Backend Dev agent generates code that imports non-existent modules or uses wrong package names.
**Why it happens:** LLMs hallucinate import paths. They may reference packages that don't exist or use wrong submodule paths.
**How to avoid:** Include a "known imports" section in the L0 context for the Backend Dev agent. Post-generation, run the generated code through `ruff check` to catch import errors before proceeding. Re-prompt with the specific error.
**Warning signs:** Persistent `ModuleNotFoundError` or `ImportError` in generated code; ruff reporting undefined names.

### Pitfall 3: Debugger Fix Loop That Never Converges

**What goes wrong:** The Debugger agent enters an infinite loop where each fix introduces new failures that the next fix tries to resolve.
**Why it happens:** Without experiment semantics, fixes cascade: fix A breaks test B, fix B breaks test C. The system oscillates.
**How to avoid:** The ExperimentLoop pattern prevents this by design. Each fix is measured against the stable baseline (not the previous attempt). If a fix does not improve the pass rate vs. baseline, it is DISCARDED (branch deleted), and the next attempt starts fresh from baseline. Circuit breakers halt the loop after `max_no_improvement` consecutive discards.
**Warning signs:** All experiments being DISCARDED; baseline not updating; token budget exhausting quickly.

### Pitfall 4: Flaky Tests From Generated Code

**What goes wrong:** The Tester agent generates tests that pass sometimes and fail other times (flaky tests), causing the Debugger to chase phantom failures.
**Why it happens:** LLM-generated tests may have timing dependencies, shared state between tests, or non-deterministic assertions.
**How to avoid:** Include anti-flakiness guidelines in the Tester agent's system prompt: "Each test must be independent and deterministic. Use fixtures for setup/teardown. Never depend on execution order. Mock all external dependencies." Run tests 2x on failure to detect flakiness before sending to Debugger.
**Warning signs:** Tests that pass on re-run without code changes; test pass rate fluctuating between runs.

### Pitfall 5: Oversized Context Exhausting Token Budget

**What goes wrong:** Agents receive too much context (full source files, entire requirement docs) and exceed their token budgets, causing truncation or failed LLM calls.
**Why it happens:** Phase 7 agents generate code that grows over the pipeline execution. By the time the Debugger runs, the accumulated context (requirements + generated code + test files + stack traces) may exceed limits.
**How to avoid:** Enforce L0/L1/L2 context tiers strictly. Each agent's YAML config specifies token budgets per tier. The context management system (Phase 5) should compress or truncate. For Phase 7, keep the vertical slice scope small (a single FastAPI application with 3-5 endpoints) to stay within budgets.
**Warning signs:** LLM API calls returning errors about context length; agents producing lower-quality output as context grows.

### Pitfall 6: Event Emission Blocking Agent Execution

**What goes wrong:** NATS JetStream publish calls inside agent execution paths slow down or block the agent, especially if NATS is temporarily unreachable.
**Why it happens:** Synchronous or awaited event emission in the hot path of agent execution.
**How to avoid:** Use fire-and-forget event emission with a background queue (the EventBus from Phase 1 already has an asyncio.Queue dispatch loop). If NATS is unreachable, buffer events locally and retry. Never let event emission failure block agent progress.
**Warning signs:** Agent execution times increasing; NATS connection timeouts appearing in agent logs.

### Pitfall 7: Test Generation Without Adequate Source Context

**What goes wrong:** The Tester agent generates tests that don't align with the actual generated code (wrong function names, wrong argument signatures, wrong import paths).
**Why it happens:** The Tester agent doesn't receive the latest generated code in its context, or the code is truncated.
**How to avoid:** The Tester agent's `perceive()` phase must read the actual generated source files from the workspace (via file_read tool), not rely on a stale SharedState snapshot. Include the complete generated file contents in the L1 context.
**Warning signs:** Tests failing with `NameError` or `AttributeError` on import; test imports not matching generated module paths.

## Code Examples

### Orchestrator Agent -- Requirement Extraction Flow

```python
# apps/server/src/codebot/agents/orchestrator.py
# Source: CodeBot design docs (AGENT_CATALOG.md Section 1) + instructor docs

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from agent_sdk.agents.base import BaseAgent, AgentInput, AgentOutput
from agent_sdk.models.enums import AgentType
from codebot.input.extractor import RequirementExtractor
from codebot.input.models import ExtractedRequirements


@dataclass(slots=True, kw_only=True)
class OrchestratorAgent(BaseAgent):
    """Master coordinator: parses input, extracts requirements, orchestrates pipeline."""

    agent_type: AgentType = field(default=AgentType.ORCHESTRATOR, init=False)

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Load user input and detect format."""
        user_input = agent_input.shared_state.get("user_input", "")
        input_format = self._detect_format(user_input)
        return {"user_input": user_input, "input_format": input_format}

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Extract structured requirements from input."""
        extractor = RequirementExtractor(model=self.config.model)
        requirements = await extractor.extract(context["user_input"])
        return {
            "requirements": requirements,
            "needs_clarification": len(requirements.ambiguities) > 0,
        }

    async def act(self, plan: dict[str, Any]) -> Any:
        """Store requirements in SharedState, request clarification if needed."""
        requirements: ExtractedRequirements = plan["requirements"]
        if plan["needs_clarification"] and requirements.ambiguities:
            # In vertical slice: log ambiguities but proceed with best-effort
            # Full clarification loop deferred to Phase 9
            pass
        return requirements

    async def review(self, result: Any) -> AgentOutput:
        """Verify extracted requirements are non-empty and well-formed."""
        requirements: ExtractedRequirements = result
        review_passed = (
            len(requirements.functional_requirements) > 0
            and all(
                fr.acceptance_criteria
                for fr in requirements.functional_requirements
            )
        )
        return AgentOutput(
            task_id=self.current_task_id,
            state_updates={"requirements": requirements.model_dump()},
            review_passed=review_passed,
        )

    @staticmethod
    def _detect_format(input_text: str) -> str:
        """Detect whether input is plain text, markdown, JSON, or YAML."""
        stripped = input_text.strip()
        if stripped.startswith("{"):
            return "json"
        if stripped.startswith("---") or ":\n" in stripped[:200]:
            return "yaml"
        if stripped.startswith("#") or "## " in stripped[:200]:
            return "markdown"
        return "natural_language"
```

### Code Reviewer Agent -- Structured Review Output

```python
# apps/server/src/codebot/agents/code_reviewer.py
from pydantic import BaseModel, Field
import instructor
import litellm


class ReviewComment(BaseModel):
    """A single review comment on generated code."""
    file_path: str
    line_start: int
    line_end: int
    severity: str = Field(description="critical/high/medium/low/info")
    category: str = Field(
        description="bug/style/performance/security/architecture/suggestion"
    )
    message: str
    suggested_fix: str | None = None


class CodeReviewReport(BaseModel):
    """Complete code review output."""
    comments: list[ReviewComment]
    overall_quality: str = Field(
        description="excellent/good/acceptable/needs_work/poor"
    )
    gate_passed: bool = Field(
        description="True if code is acceptable for testing"
    )
    summary: str


# Inside CodeReviewerAgent.reason():
async def _review_code(
    self, source_files: dict[str, str]
) -> CodeReviewReport:
    """Review generated code using LLM with structured output."""
    client = instructor.from_litellm(litellm.completion)
    file_contents = "\n\n".join(
        f"### {path}\n```python\n{content}\n```"
        for path, content in source_files.items()
    )
    return client.chat.completions.create(
        model=self.config.model,
        response_model=CodeReviewReport,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert code reviewer. Review the following "
                    "Python/FastAPI code. Check for: bugs, style violations, "
                    "performance issues, security vulnerabilities, architecture "
                    "conformance, and maintainability. Set gate_passed=true only "
                    "if there are no critical or high severity issues."
                ),
            },
            {
                "role": "user",
                "content": f"Review this code:\n\n{file_contents}",
            },
        ],
        max_retries=2,
    )
```

### Tester Agent -- Test Generation and Execution

```python
# apps/server/src/codebot/agents/tester.py (partial)
import asyncio
import json
from pathlib import Path
from typing import Any

from agent_sdk.agents.base import BaseAgent, AgentInput, AgentOutput


class TesterAgent(BaseAgent):
    """Generates and executes tests against generated code."""

    async def act(self, plan: dict[str, Any]) -> Any:
        """Generate tests, write to workspace, execute, collect results."""
        workspace = plan["workspace_path"]
        source_files = plan["source_files"]

        # 1. Generate test code via LLM
        test_code = await self._generate_tests(source_files)

        # 2. Write test files
        for test_path, test_content in test_code.items():
            full_path = Path(workspace) / test_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(test_content)

        # 3. Execute tests with JSON reporting and coverage
        result = await self._run_tests(workspace)
        return result

    async def _run_tests(self, workspace: str) -> dict:
        """Run pytest with JSON report and coverage."""
        proc = await asyncio.create_subprocess_exec(
            "uv", "run", "pytest",
            "--json-report",
            "--json-report-file=test-report.json",
            "--cov=.",
            "--cov-report=json:coverage.json",
            "-x",  # Stop on first failure for faster feedback
            cwd=workspace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        # Parse results
        report_path = Path(workspace) / "test-report.json"
        coverage_path = Path(workspace) / "coverage.json"

        test_results = {}
        if report_path.exists():
            test_results = json.loads(report_path.read_text())

        coverage_data = {}
        if coverage_path.exists():
            coverage_data = json.loads(coverage_path.read_text())

        return {
            "exit_code": proc.returncode,
            "test_results": test_results,
            "coverage": coverage_data,
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
        }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Regex-based requirement parsing | LLM + Pydantic structured extraction (instructor) | 2024-2025 | Orders of magnitude better at handling natural language ambiguity; schema-validated output |
| Simple retry loop for debug | ExperimentLoop with keep/discard semantics | 2025 (Karpathy autoresearch) | Prevents cascading breakage; each fix independently reversible against baseline |
| Manual JSON mode with custom retry | instructor library with automatic validation retry | 2024-2025 | Reduces boilerplate; handles malformed JSON recovery across all providers |
| Custom LLM cost tracking per provider | LiteLLM unified cost tracking (`response_cost`) | 2024-2025 | Single interface for cost across 100+ providers; no manual price tables |
| Stdout parsing for test results | JSON reporter plugins (pytest-json-report) | Established | Machine-parseable, stable across pytest versions |

**Deprecated/outdated:**
- **instructor < 1.0**: Older versions used `openai.patch()` pattern. Current version (1.14.5) uses `instructor.from_litellm()` factory pattern.
- **LiteLLM < 1.0**: Pre-1.0 had different JSON mode configuration. Current (1.82.4) uses standardized `response_format` parameter.
- **pytest < 7**: Older pytest versions have different exit code semantics. Current pytest (9+) is project standard.

## Open Questions

1. **Workspace Directory Strategy for Phase 7 (Before Worktrees)**
   - What we know: Phase 8 introduces full git worktree isolation. Phase 7 doesn't have that yet.
   - What's unclear: Should Phase 7 use a temp directory for the generated code workspace, or a fixed subdirectory within the project?
   - Recommendation: Use `tempfile.mkdtemp()` for isolation. Create a `WorkspaceManager` interface that Phase 8 can later implement with real git worktrees. Phase 7 uses a `TempWorkspaceManager` implementation.

2. **Clarification Loop Depth for INPT-05**
   - What we know: INPT-05 requires the system to initiate a clarification loop when requirements are ambiguous.
   - What's unclear: In the vertical slice, should clarification block the pipeline (requiring human input), or should the system auto-infer and proceed with disclaimers?
   - Recommendation: For the vertical slice, auto-infer with disclaimers. Log ambiguities as warnings and proceed. The full human-in-the-loop clarification loop comes with the full agent roster in Phase 9. The vertical slice pipeline YAML has `human_gate.enabled: true` on the input phase as a demonstration, with `timeout_action: auto_approve` to not block automated testing.

3. **Code Reviewer Feedback Loop (Reroute to Implementation)**
   - What we know: QA-06 requires quality gates. The vertical slice config has `on_failure: reroute_to_implement` for the QA phase.
   - What's unclear: Should the Code Reviewer's feedback be automatically applied by re-running the Backend Dev agent, or should it be a separate remediation step?
   - Recommendation: On QA failure, re-route to Backend Dev agent with the review comments injected into SharedState as additional context. The Backend Dev agent's `perceive()` checks for review comments and adjusts its generation accordingly. Limit to 2 QA-implementation cycles to prevent infinite loops.

4. **Scope of Generated Application**
   - What we know: The vertical slice generates Python/FastAPI code.
   - What's unclear: How complex should the generated application be? A single-endpoint CRUD app, or something with multiple endpoints and data models?
   - Recommendation: Target a small but meaningful application: 3-5 FastAPI endpoints with Pydantic models, basic CRUD operations, and input validation. This is complex enough to exercise all 5 agents meaningfully but small enough to stay within LLM context budgets. The specific application should be driven by the user's natural language input.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9+ with pytest-asyncio |
| Config file | `tests/conftest.py` (shared fixtures), `apps/server/tests/conftest.py` (server fixtures) |
| Quick run command | `uv run pytest tests/unit/agents/ tests/unit/input/ tests/unit/debug/ -x --timeout=30` |
| Full suite command | `uv run pytest tests/ -x --timeout=120` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INPT-01 | Natural language input accepted and processed | unit | `uv run pytest tests/unit/input/test_extractor.py::test_natural_language_input -x` | No -- Wave 0 |
| INPT-02 | Structured PRD (MD/JSON/YAML) accepted | unit | `uv run pytest tests/unit/input/test_extractor.py::test_structured_input_formats -x` | No -- Wave 0 |
| INPT-04 | Requirements, NFRs, constraints, acceptance criteria extracted | unit | `uv run pytest tests/unit/input/test_extractor.py::test_extraction_completeness -x` | No -- Wave 0 |
| INPT-05 | Clarification triggered on ambiguous input | unit | `uv run pytest tests/unit/input/test_clarifier.py::test_ambiguity_detection -x` | No -- Wave 0 |
| IMPL-02 | Backend Dev generates FastAPI code from requirements | unit | `uv run pytest tests/unit/agents/test_backend_dev.py::test_code_generation -x` | No -- Wave 0 |
| IMPL-07 | Generated code passes ruff + mypy | unit | `uv run pytest tests/unit/agents/test_backend_dev.py::test_lint_typecheck -x` | No -- Wave 0 |
| QA-01 | Code Reviewer produces actionable review | unit | `uv run pytest tests/unit/agents/test_code_reviewer.py::test_review_output -x` | No -- Wave 0 |
| QA-06 | Quality gate blocks on critical issues | unit | `uv run pytest tests/unit/agents/test_code_reviewer.py::test_quality_gate -x` | No -- Wave 0 |
| TEST-01 | Unit tests generated with coverage target | unit | `uv run pytest tests/unit/agents/test_tester.py::test_unit_test_generation -x` | No -- Wave 0 |
| TEST-02 | Integration tests generated for API endpoints | unit | `uv run pytest tests/unit/agents/test_tester.py::test_integration_test_generation -x` | No -- Wave 0 |
| TEST-05 | Failed test results route to Debugger | integration | `uv run pytest tests/integration/test_vertical_slice_e2e.py::test_failure_routes_to_debugger -x` | No -- Wave 0 |
| DBUG-01 | Root cause analysis on test failures | unit | `uv run pytest tests/unit/debug/test_analyzer.py::test_root_cause_analysis -x` | No -- Wave 0 |
| DBUG-02 | Fix proposals generated and applied | unit | `uv run pytest tests/unit/debug/test_fixer.py::test_fix_generation -x` | No -- Wave 0 |
| DBUG-03 | Experiment loop with circuit breakers | unit | `uv run pytest tests/unit/debug/test_loop_controller.py::test_experiment_loop -x` | No -- Wave 0 |
| EVNT-01 | NATS JetStream events emitted on agent transitions | integration | `uv run pytest tests/integration/test_vertical_slice_e2e.py::test_event_emission -x` | No -- Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/unit/agents/ tests/unit/input/ tests/unit/debug/ -x --timeout=30`
- **Per wave merge:** `uv run pytest tests/ -x --timeout=120`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/agents/test_orchestrator.py` -- covers INPT-01, INPT-02
- [ ] `tests/unit/agents/test_backend_dev.py` -- covers IMPL-02, IMPL-07
- [ ] `tests/unit/agents/test_code_reviewer.py` -- covers QA-01, QA-06
- [ ] `tests/unit/agents/test_tester.py` -- covers TEST-01, TEST-02
- [ ] `tests/unit/agents/test_debugger.py` -- covers DBUG-01, DBUG-02, DBUG-03
- [ ] `tests/unit/input/test_extractor.py` -- covers INPT-01, INPT-02, INPT-04
- [ ] `tests/unit/input/test_clarifier.py` -- covers INPT-05
- [ ] `tests/unit/debug/test_analyzer.py` -- covers DBUG-01
- [ ] `tests/unit/debug/test_fixer.py` -- covers DBUG-02
- [ ] `tests/unit/debug/test_loop_controller.py` -- covers DBUG-03
- [ ] `tests/integration/test_vertical_slice_e2e.py` -- covers TEST-05, EVNT-01, full pipeline
- [ ] Test dependency: `uv add --dev pytest-json-report`
- [ ] LLM mock fixtures: `tests/conftest.py` needs mock instructor/litellm responses

### Testing Strategy for LLM-Dependent Code

All unit tests MUST mock LLM calls (CLAUDE.md rule: "Mock LLM providers in tests -- never call real APIs"). Use `unittest.mock.AsyncMock` or `pytest-mock` to mock `instructor.from_litellm()` returns. Pre-canned responses should be valid Pydantic model instances.

```python
# Example fixture for mocked requirement extraction
@pytest.fixture
def mock_extractor(monkeypatch):
    """Mock the LLM call in RequirementExtractor."""
    from unittest.mock import AsyncMock
    from codebot.input.models import (
        ExtractedRequirements,
        FunctionalRequirement,
        AcceptanceCriterion,
    )

    mock_requirements = ExtractedRequirements(
        project_name="Todo API",
        project_description="A simple todo list API",
        functional_requirements=[
            FunctionalRequirement(
                id="FR-01",
                title="Create todo item",
                description="User can create a new todo item with title and description",
                priority="Must",
                acceptance_criteria=[
                    AcceptanceCriterion(
                        description="POST /todos returns 201 with created item",
                        test_strategy="integration",
                    )
                ],
                confidence=0.95,
            )
        ],
        non_functional_requirements=["Response time < 200ms"],
        constraints=["Python 3.12+", "FastAPI framework"],
        ambiguities=[],
    )
    monkeypatch.setattr(
        "codebot.input.extractor.RequirementExtractor.extract",
        AsyncMock(return_value=mock_requirements),
    )
    return mock_requirements
```

## Sources

### Primary (HIGH confidence)
- CodeBot design docs: `docs/design/SYSTEM_DESIGN.md` Sections 9 (Test Execution), 10 (Debug and Fix Loop), 11 (Event System) -- detailed architecture for Tester and Debugger agents
- CodeBot agent catalog: `docs/design/AGENT_CATALOG.md` -- specifications for all 5 vertical slice agents (Orchestrator, Backend Dev, Code Reviewer, Tester, Debugger)
- CodeBot workflows: `docs/workflows/AGENT_WORKFLOWS.md` Sections 3.7 (Testing Phase), 3.8 (Debug and Fix Loop with ExperimentLoop)
- Phase 3 Research: `.planning/phases/03-agent-framework/03-RESEARCH.md` -- BaseAgent architecture, PRA cycle, state machine, YAML config
- Phase 6 Research: `.planning/phases/06-pipeline-orchestration/06-RESEARCH.md` -- Temporal workflow patterns, NATS event emission, pipeline presets
- [instructor PyPI](https://pypi.org/project/instructor/) -- Version 1.14.5 verified (2026-01-29)
- [LiteLLM PyPI](https://pypi.org/project/litellm/) -- Version 1.82.4 verified (2026-03-16)
- [LiteLLM Structured Output docs](https://docs.litellm.ai/docs/completion/json_mode) -- JSON mode and structured output patterns
- [Instructor + LiteLLM Integration](https://python.useinstructor.com/integrations/litellm/) -- Integration guide

### Secondary (MEDIUM confidence)
- [Instructor library docs](https://python.useinstructor.com/) -- Multi-provider structured output, Pydantic integration, retry semantics
- [LiteLLM Instructor Tutorial](https://docs.litellm.ai/docs/tutorials/instructor) -- Using instructor with LiteLLM
- [Best AI Coding Agents 2026](https://www.faros.ai/blog/best-ai-coding-agents-2026) -- Community patterns for code generation agents
- [Agentic AI Coding Best Practices](https://codescene.com/blog/agentic-ai-coding-best-practice-patterns-for-speed-with-quality) -- Quality metrics, feedback loops, test-driven agent patterns
- [Addy Osmani: LLM Coding Workflow 2026](https://addyosmani.com/blog/ai-coding-workflow/) -- Generate-run-fix loop best practices

### Tertiary (LOW confidence)
- [Google LangExtract](https://github.com/google/langextract) -- Alternative approach to structured extraction; not needed since instructor covers our use case, but worth monitoring
- [Structured Output Comparison](https://simmering.dev/blog/structured_output/) -- Comparison of structured output libraries; validates instructor as top choice

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified on PyPI with current versions; instructor + LiteLLM is the documented recommended pattern
- Architecture: HIGH - All 5 agent designs specified in AGENT_CATALOG.md; pipeline composition follows Phase 6 Temporal patterns; ExperimentLoop fully specified in SYSTEM_DESIGN.md
- Pitfalls: HIGH - Derived from known LLM structured output failure modes, test generation patterns, and the documented experiment loop design
- Validation: HIGH - Test strategy follows project conventions (pytest, mock LLM); all requirements mapped to test commands

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (30 days -- instructor and LiteLLM release frequently but APIs are stable; core architecture patterns are stable)
