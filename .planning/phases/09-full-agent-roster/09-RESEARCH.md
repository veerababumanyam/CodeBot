# Phase 9: Full Agent Roster - Research

**Researched:** 2026-03-18
**Domain:** Multi-agent system implementation -- 30 specialized agents across 10 SDLC stages with YAML configs, parallel execution, stage-specific graph compositions, and event sourcing
**Confidence:** HIGH

## Summary

Phase 9 is the breadth-expansion phase that builds on the validated vertical slice (Phase 7) and security/worktree infrastructure (Phase 8) to implement all 30 specialized agents across every SDLC stage (S0-S9). The Phase 3 agent framework provides `BaseAgent` with PRA cycle, `AgentNode` for graph execution, state machine, YAML configuration, and recovery strategies. Phase 7 proved this architecture with 5 agents (Orchestrator, Backend Dev, Code Reviewer, Tester, Debugger). Phase 9 extends coverage to the remaining 25 agents organized into 10 categories: Orchestration (already done), Ideation, Planning, Research, Design, Implementation, Quality, Testing (partially done), Operations, Tooling, and Coordination.

The work naturally divides into stage-based waves. Each wave adds a group of agents that share a pipeline stage, enabling them to be tested as a composed subgraph. The agents in this phase span three distinct execution patterns: (1) sequential single-agent stages (S1 Brainstorming, S2 Research), (2) parallel fan-out/fan-in stages (S3 Architecture with 4-5 agents, S5 Implementation with 5-6 agents, S6 QA with 5 agents), and (3) post-pipeline stages (S9 Documentation with 3 agents). Each agent is a concrete `BaseAgent` subclass with a YAML configuration specifying its system prompt, tools, LLM model, context tiers, and retry policy. Additionally, this phase must wire agents into the pipeline orchestration graphs defined in Phase 6 and register them in the agent registry (AGNT-08).

**Primary recommendation:** Implement agents wave-by-wave following the pipeline order (S0/S1 first, then S2, S3-S4, S5, S6, S7-S8 extensions, S9, cross-cutting), with each wave producing: (1) concrete agent class extending BaseAgent, (2) YAML configuration in `configs/agents/`, (3) stage subgraph YAML wiring agents together, (4) unit tests mocking the LLM layer. Use the design patterns established in Phase 3 (PRA cycle, state machine, recovery) and Phase 7 (vertical slice agents as reference implementations). Prioritize agents in the critical pipeline path. Tooling agents (Skill/Hooks/Tools Creator) are lower priority and can be minimal implementations.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AGNT-08 | System supports 30 specialized agents across 10 categories | Agent registry populated with all 30 AgentType entries; each has YAML config; factory instantiates by type |
| INPT-03 | System accepts multi-modal input: text, images, reference URLs | S0 input processing: extend Orchestrator to handle image/URL inputs via multimodal LLM (Claude Opus 4 supports vision) |
| INPT-06 | User can select UI/UX template (Shadcn/ui, Tailwind UI, etc.) | Template Agent in S4 provides template selection from registry |
| INPT-07 | User can select or auto-recommend tech stack | TechStack Builder agent in S4 recommends and validates stack |
| INPT-08 | System imports existing codebases from Git repos for brownfield | S0 Orchestrator + brownfield detection in pipeline config (PIPE-07 from Phase 6) |
| BRST-01 | System facilitates idea exploration sessions | Brainstorming Agent with web_search, idea_matrix, user_dialog tools |
| BRST-02 | System maps problems to potential solution approaches | Brainstorming Agent divergent thinking mode (3-5 alternatives) |
| BRST-03 | System performs competitive analysis | Brainstorming Agent web_search + reference_finder tools |
| BRST-04 | System prioritizes features using MoSCoW or RICE | Brainstorming Agent feature prioritization output |
| BRST-05 | System presents trade-off analysis | Brainstorming Agent convergent refinement with comparison matrix |
| BRST-06 | System generates user personas | Brainstorming Agent persona generation from product idea |
| BRST-07 | System defines MVP scope vs future iterations | Brainstorming Agent MVP scoping with priority-based feature splitting |
| RSRC-01 | Researcher evaluates libraries, APIs, frameworks | Researcher Agent with web_search, github_search, npm/pypi_registry, docs_reader tools |
| RSRC-02 | Researcher discovers best practices and reference implementations | Researcher Agent reference_finder + arxiv_search tools |
| RSRC-03 | Researcher identifies potential risks and compatibility issues | Researcher Agent dependency_analyzer with health scoring |
| RSRC-04 | Research outputs feed into Architecture phase as structured context | Researcher Agent state flow output -> SharedState consumed by S3 agents |
| ARCH-01 | Architect designs system architecture with component boundaries | Architect Agent with diagram_generator, pattern_library, adr_writer tools |
| ARCH-02 | API Designer generates REST/GraphQL API specifications | API Gateway Agent with openapi_designer, graphql_designer tools |
| ARCH-03 | Database Designer creates schema with migrations | Database Agent with schema_generator, migration_generator, erd_generator tools |
| ARCH-04 | UI/UX Designer generates wireframes and component hierarchy | Designer Agent with wireframe_generator, component_tree_builder tools |
| ARCH-05 | S3 agents execute in parallel with SharedState | S3 subgraph definition: fan-out to Architect/Designer/Database/API Gateway, fan-in merge |
| ARCH-06 | Architecture outputs validated against requirements | Gate G3 validation at S3 exit; architecture conformance checker |
| PLAN-01 | Planner decomposes architecture into tasks with dependencies | Planner Agent with task_decomposer, dependency_resolver, complexity_estimator tools |
| PLAN-02 | Task dependency graph determines execution order | Planner Agent parallel_scheduler + critical_path_analyzer tools |
| PLAN-03 | Each task specifies target files, acceptance criteria, complexity | Planner Agent structured task output with JSON task graph |
| IMPL-01 | Frontend agent generates React/TypeScript UI code | Frontend Dev Agent extending BaseAgent with file_read/write/edit, bash, browser_preview tools |
| IMPL-03 | Mobile agent generates cross-platform mobile code | Mobile Dev Agent with simulator_preview, cocoapods/gradle tools |
| IMPL-04 | Infrastructure agent generates Docker, CI/CD, config files | Infrastructure Engineer Agent with terraform_validate, docker_build, kubectl tools |
| QA-02 | Security Scanner runs Semgrep, Trivy, Gitleaks | Security Auditor Agent (extends Phase 8 security pipeline integration) |
| QA-03 | Accessibility agent audits UI for WCAG 2.1 AA | Accessibility Agent with axe_core, lighthouse, color_contrast_checker tools |
| QA-04 | Performance agent profiles code for bottlenecks | Performance Agent with lighthouse, webpack_analyzer, load_tester, profiler tools |
| QA-05 | i18n/L10n agent verifies internationalization completeness | i18n Agent with string_extractor, i18n_configurator, pseudo_localizer, rtl_validator tools |
| QA-07 | S6 agents execute in parallel | S6 subgraph: parallel fan-out for all 5 QA agents, fan-in merge of reports |
| TEST-03 | Test Generator creates E2E tests using Playwright/Vitest | Extend Tester Agent (from Phase 7) with playwright and snapshot_tester tools |
| TEST-04 | Tests execute in sandboxed environments (Docker containers) | Tester Agent integration with worktree Docker profiles from Phase 8 |
| DBUG-04 | Security-specific debugging addresses vulnerability findings | Extend Debugger Agent (from Phase 7) to parse SecurityAuditor findings and generate security fixes |
| DOCS-01 | Documentation agent generates API docs from code | Documentation Writer Agent with openapi_renderer, docstring_generator tools |
| DOCS-02 | Documentation agent creates user guides and setup instructions | Documentation Writer Agent with readme_generator, diagram_renderer tools |
| DOCS-03 | Documentation agent produces architecture decision records | Documentation Writer Agent with adr_formatter tool |
| DOCS-04 | Generated docs include deployment guides | Documentation Writer Agent with deployment guide from Infrastructure config |
| EVNT-02 | Event replay capability for debugging and audit | NATS JetStream replay from stored events; agent events all published via EventBus |
| EVNT-03 | Full audit trail: every agent action persisted | All agent state transitions and tool calls logged as events via EventBus |
| EVNT-04 | Event-sourced architecture enables pipeline reconstruction | Events stored in JetStream; pipeline state reconstructable from event log |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Agent runtime | Project convention; asyncio.TaskGroup, ExceptionGroup |
| Pydantic | >=2.9 | YAML config validation, agent I/O schemas | Already in project; v2 with ConfigDict |
| PyYAML | >=6.0 | Agent YAML config parsing | Already installed; standard parser |
| SQLAlchemy | >=2.0.35 | Agent/AgentExecution ORM persistence | Already in project; async with asyncpg |
| nats-py | >=2.9.0 | Event publishing for agent state transitions and audit trail | Already in project via EventBus |
| LiteLLM | (from Phase 4) | Provider-agnostic LLM calls | Unified interface for Anthropic/OpenAI/Google |
| GitPython | >=3.1.0 | Worktree operations for coding agents | Already in project from Phase 8 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | >=0.27 | HTTP client for web_search, API registry tools | Agent tools that call external APIs |
| Jinja2 | >=3.1 | Template rendering for scaffold/config generation | Template Agent, Infrastructure Agent config generation |
| tree-sitter | (from Phase 5) | Code parsing for AST-aware agent tools | Code Reviewer, i18n string extraction, complexity analysis |
| Playwright (Python) | >=1.40 | Browser automation for accessibility/E2E testing | Accessibility Agent, Tester Agent E2E, browser_preview |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Individual agent classes | Generic LLM-chain agent | Individual classes allow typed I/O, agent-specific recovery, and custom tool bindings per the AGENT_CATALOG spec |
| YAML agent configs | Python-only configs | YAML is a Phase 3 decision (AGNT-05) enabling non-code agent configuration and marketplace |
| Agent-per-file structure | Single large agents module | Agent-per-file scales to 30 agents without merge conflicts; clear ownership per stage |

**Installation:**
```bash
# Most dependencies already installed from Phase 1-8.
# Additional packages for agent tooling:
uv add httpx jinja2
# Playwright (if not already from Phase 7/8):
uv add playwright
playwright install chromium
```

## Architecture Patterns

### Recommended Project Structure

```
apps/server/src/codebot/agents/
  __init__.py
  registry.py                # AgentRegistry: factory + type->class mapping
  # --- S0/S1: Ideation ---
  brainstorming.py           # BrainstormingAgent
  # --- S2: Research ---
  researcher.py              # ResearcherAgent
  # --- S3: Architecture & Design ---
  architect.py               # ArchitectAgent
  designer.py                # DesignerAgent (UI/UX)
  template_curator.py        # TemplateAgent
  database_designer.py       # DatabaseAgent
  api_designer.py            # APIGatewayAgent
  # --- S4: Planning ---
  planner.py                 # PlannerAgent
  techstack_builder.py       # TechStackBuilderAgent
  # --- S5: Implementation ---
  frontend_dev.py            # FrontendDevAgent
  backend_dev.py             # BackendDevAgent (from Phase 7)
  middleware_dev.py           # MiddlewareDevAgent
  mobile_dev.py              # MobileDevAgent
  infra_engineer.py          # InfraEngineerAgent
  integrations.py            # IntegrationsAgent
  # --- S6: Quality ---
  code_reviewer.py           # CodeReviewerAgent (from Phase 7)
  security_auditor.py        # SecurityAuditorAgent (from Phase 8)
  accessibility.py           # AccessibilityAgent
  performance.py             # PerformanceAgent
  i18n_l10n.py               # I18nL10nAgent
  # --- S7/S8: Testing & Debug ---
  tester.py                  # TesterAgent (from Phase 7, extended)
  debugger.py                # DebuggerAgent (from Phase 7, extended)
  # --- S9: Documentation ---
  doc_writer.py              # DocumentationWriterAgent
  devops.py                  # DevOpsAgent
  github_agent.py            # GitHubAgent
  # --- Cross-cutting ---
  orchestrator.py            # OrchestratorAgent (from Phase 7)
  project_manager.py         # ProjectManagerAgent
  # --- Tooling (Phase 11-deferred but stub here) ---
  skill_creator.py           # SkillCreatorAgent (stub)
  hooks_creator.py           # HooksCreatorAgent (stub)
  tools_creator.py           # ToolsCreatorAgent (stub)

configs/agents/
  orchestrator.yaml
  brainstorming.yaml
  planner.yaml
  techstack_builder.yaml
  researcher.yaml
  architect.yaml
  designer.yaml
  template.yaml
  database.yaml
  api_gateway.yaml
  frontend_dev.yaml
  backend_dev.yaml
  middleware_dev.yaml
  mobile_dev.yaml
  infra_engineer.yaml
  integrations.yaml
  code_reviewer.yaml
  security_auditor.yaml
  accessibility.yaml
  performance.yaml
  i18n_l10n.yaml
  tester.yaml
  debugger.yaml
  doc_writer.yaml
  devops.yaml
  github.yaml
  skill_creator.yaml
  hooks_creator.yaml
  tools_creator.yaml
  project_manager.yaml

configs/pipelines/
  full.yaml                  # Full pipeline with all 30 agents
  quick.yaml                 # Quick pipeline with essential agents
  review-only.yaml           # Review-only pipeline

apps/server/src/codebot/agents/tools/
  __init__.py
  web_search.py              # Tavily/SerpAPI wrapper
  github_search.py           # GitHub API search
  package_registry.py        # npm/PyPI query
  diagram_generator.py       # Mermaid diagram generation
  scaffold_generator.py      # Project scaffolding
  # ... (each tool as a separate module)
```

### Pattern 1: Concrete Agent Implementation

**What:** Each agent is a concrete `BaseAgent` subclass that overrides the PRA cycle methods with stage-specific logic. The agent delegates actual work to the LLM via the Multi-LLM abstraction layer (Phase 4), using tools specific to its domain.

**When to use:** Every new agent in Phase 9.

**Example:**
```python
# apps/server/src/codebot/agents/brainstorming.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_sdk.agents.base import BaseAgent, AgentInput, AgentOutput
from agent_sdk.models.enums import AgentType


@dataclass(slots=True, kw_only=True)
class BrainstormingAgent(BaseAgent):
    """Facilitates idea exploration and requirement refinement.

    Implements the S1 Brainstorming phase: divergent idea generation,
    competitive analysis, feature prioritization, and MVP scoping.
    """

    agent_type: AgentType = AgentType.BRAINSTORM_FACILITATOR

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Load user PRD/idea, prior project references, domain context."""
        context = {}
        context["user_input"] = agent_input.shared_state.get("user_input", {})
        context["preferences"] = agent_input.shared_state.get("preferences", {})
        # L2: fetch similar projects from vector store
        context["similar_projects"] = await self._retrieve_l2(
            query="similar projects to " + context["user_input"].get("content", ""),
            max_tokens=self._config.context_tiers.get("l2", 20000),
        )
        return context

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Invoke LLM to generate alternatives, questions, risk assessment."""
        messages = self._build_messages(context)
        response = await self._llm.generate(
            messages=messages,
            tools=self._tools,
            model=self._config.model,
            temperature=self._config.temperature,
            max_tokens=self._config.max_tokens,
        )
        return {"response": response, "context": context}

    async def act(self, plan: dict[str, Any]) -> Any:
        """Execute tool calls (web_search, reference_finder) or produce output."""
        response = plan["response"]
        if response.has_tool_calls:
            results = await self._execute_tools(response.tool_calls)
            return AgentActionResult(is_complete=False, data=results)
        return AgentActionResult(
            is_complete=True,
            data={
                "refined_requirements": response.content,
                "alternatives": response.structured_output.get("alternatives"),
                "risk_assessment": response.structured_output.get("risks"),
            },
        )

    async def review(self, result: Any) -> AgentOutput:
        """Verify all required outputs are present."""
        data = result.data
        review_passed = all([
            data.get("refined_requirements"),
            data.get("alternatives"),
        ])
        return AgentOutput(
            task_id=self._current_task_id,
            state_updates={"brainstorming_output": data},
            review_passed=review_passed,
        )
```

### Pattern 2: YAML Agent Configuration

**What:** Every agent has a YAML config file that fully specifies its behavior without code changes.

**When to use:** All 30 agents.

**Example:**
```yaml
# configs/agents/brainstorming.yaml
brainstorming:
  agent_type: BRAINSTORM_FACILITATOR
  model: claude-opus-4
  fallback_model: o3
  provider: anthropic
  max_tokens: 8192
  temperature: 0.7
  system_prompt: |
    You are a creative brainstorming facilitator for software projects.
    Your job is to explore the solution space, identify alternatives,
    assess risks, and refine requirements through interactive Q&A.

    Always generate at least 3 alternative approaches.
    Always identify at least 3 risks.
    Always produce a feature prioritization using MoSCoW framework.
  tools:
    - web_search
    - idea_matrix
    - user_dialog
    - reference_finder
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 20000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 3
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 300
  settings:
    min_alternatives: 3
    max_alternatives: 5
    require_user_confirmation: true
```

### Pattern 3: Stage Subgraph Composition

**What:** Each pipeline stage is a subgraph that composes agents with the right execution topology (sequential, parallel fan-out/fan-in). Stage subgraphs are loaded by the pipeline orchestrator (Phase 6).

**When to use:** S3 (Architecture), S5 (Implementation), S6 (QA) which require parallel agent execution.

**Example:**
```yaml
# configs/stages/s3_architecture.yaml
stage:
  name: architecture_and_design
  type: subgraph
  execution: fan_out_fan_in
  entry_gate:
    type: automatic
    check: research_report_completeness
  agents:
    - id: architect
      type: ARCHITECT
      parallel_group: design
    - id: designer
      type: DESIGNER
      parallel_group: design
    - id: database
      type: API_DESIGNER  # maps to Database Agent
      parallel_group: design
    - id: api_gateway
      type: API_DESIGNER
      parallel_group: design
  merge_strategy:
    type: state_merge
    conflict_resolution: architect_authority
  exit_gate:
    type: approval
    gate_id: G3
    timeout_minutes: 30
    auto_approve_on_timeout: false
```

### Pattern 4: Agent Registry and Factory

**What:** A centralized registry maps `AgentType` enum values to concrete agent classes. The factory creates agent instances from YAML config + type.

**When to use:** When the Orchestrator or pipeline engine needs to instantiate agents dynamically.

**Example:**
```python
# apps/server/src/codebot/agents/registry.py
from __future__ import annotations

from typing import TYPE_CHECKING

from agent_sdk.models.enums import AgentType

if TYPE_CHECKING:
    from agent_sdk.agents.base import BaseAgent

_REGISTRY: dict[AgentType, type[BaseAgent]] = {}


def register_agent(agent_type: AgentType):
    """Decorator to register an agent class for a given AgentType."""
    def decorator(cls: type[BaseAgent]) -> type[BaseAgent]:
        _REGISTRY[agent_type] = cls
        return cls
    return decorator


def create_agent(agent_type: AgentType, config: dict) -> BaseAgent:
    """Factory: instantiate an agent by type with the given config."""
    cls = _REGISTRY.get(agent_type)
    if cls is None:
        raise ValueError(f"No agent registered for type {agent_type}")
    return cls(**config)


def get_all_registered() -> dict[AgentType, type[BaseAgent]]:
    """Return all registered agent types and their classes."""
    return dict(_REGISTRY)
```

### Pattern 5: Tool Abstraction

**What:** Agent tools are Python async callables with typed inputs/outputs registered in a tool registry. Tools are bound to agents via YAML config.

**When to use:** Every agent tool (web_search, diagram_generator, file_read, etc.).

**Example:**
```python
# apps/server/src/codebot/agents/tools/web_search.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, kw_only=True)
class WebSearchTool:
    """Web search tool using Tavily or SerpAPI."""

    api_key: str
    max_results: int = 10

    async def __call__(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Search the web and return structured results."""
        # Implementation delegates to Tavily/SerpAPI
        ...
```

### Anti-Patterns to Avoid

- **Monolithic agent file:** Do NOT put all 30 agents in a single file. One agent per file, organized by stage.
- **Hardcoded LLM calls:** Do NOT call LLM APIs directly. Always go through the Multi-LLM abstraction layer from Phase 4.
- **Shared mutable state between parallel agents:** Do NOT share mutable state between agents in S3/S5/S6 parallel stages. Use SharedState with merge strategies.
- **Skipping self-review:** Do NOT omit the `review()` step. Every agent must validate its output against acceptance criteria before marking COMPLETED.
- **Tools without error handling:** Do NOT let tool failures crash the agent. Wrap tool calls in try/except and use recovery strategies.
- **Copying agent configs into code:** Do NOT duplicate YAML config values in Python. Load from YAML at runtime.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM provider abstraction | Custom HTTP clients per provider | LiteLLM (Phase 4) | Handles auth, retries, streaming, 100+ providers |
| Agent state machine | Complex state tracking in each agent | AgentStateMachine (Phase 3) | Centralized transition validation, event emission |
| YAML config validation | Manual dict parsing | Pydantic AgentConfig model (Phase 3) | Type safety, validation, defaults |
| Graph execution | Custom parallel execution | Graph Engine (Phase 2) with asyncio.TaskGroup | Topological ordering, parallel branches, checkpointing |
| Event publishing | Direct NATS calls in agents | EventBus (Phase 1) | Abstracted pub/sub, JetStream persistence |
| Git worktree management | Manual git commands | WorktreeManager (Phase 8) | Lifecycle management, cleanup, port allocation |
| Security scanning | Custom scanner integration | Security Pipeline (Phase 8) | Semgrep/Trivy/Gitleaks orchestration, quality gates |
| Context assembly | Manual context building | ContextManager (Phase 5) | L0/L1/L2 tier assembly, token budgets, compression |

**Key insight:** Phase 9 is primarily an integration/composition phase. The infrastructure (Phases 1-8) is already built. Each agent is a composition of: BaseAgent (Phase 3) + LLM calls (Phase 4) + Context (Phase 5) + Pipeline position (Phase 6) + Tools (domain-specific). The new code is primarily: (1) system prompts, (2) tool implementations, (3) YAML configs, and (4) stage subgraph definitions.

## Common Pitfalls

### Pitfall 1: Agent Explosion -- Trying to Build All 30 at Once
**What goes wrong:** Attempting to implement all 30 agents simultaneously leads to integration chaos, untestable combinations, and compounding bugs.
**Why it happens:** The requirement says "all 30 agents" and the natural instinct is to parallelize.
**How to avoid:** Implement in pipeline-order waves. Each wave adds agents for one stage, tests them in isolation, then integrates with the pipeline. Wave order: S1 (1 agent) -> S2 (1) -> S3 (5) -> S4 (2) -> S5 (5, some already done) -> S6 (5, some already done) -> S7-S8 extensions (2) -> S9 (3) -> Cross-cutting (2) -> Tooling stubs (3).
**Warning signs:** More than 5-6 agents being developed simultaneously without integration tests.

### Pitfall 2: Over-Engineering Agent Tools
**What goes wrong:** Building full-featured tool implementations (complete Terraform validator, full Lighthouse integration) when the agent only needs to delegate to CLI commands.
**Why it happens:** The AGENT_CATALOG lists sophisticated tools, and the temptation is to build them completely.
**How to avoid:** Most agent tools are thin wrappers around CLI commands (semgrep, trivy, lighthouse, terraform, etc.) or HTTP APIs (npm registry, GitHub API). Start with subprocess-based CLI wrappers, not SDK integrations. The LLM agent interprets the output.
**Warning signs:** Tool implementation exceeds 100 lines; building custom parsers instead of using `subprocess.run` + LLM interpretation.

### Pitfall 3: Parallel Stage Merge Conflicts
**What goes wrong:** S3/S5/S6 agents running in parallel write to SharedState simultaneously, causing race conditions or lost updates.
**Why it happens:** Multiple agents writing to the same state namespace without coordination.
**How to avoid:** Each parallel agent writes to its own namespace in SharedState (e.g., `architect_output`, `designer_output`). The MERGE node combines them after all complete. Never have two parallel agents write to the same key.
**Warning signs:** Test flakiness in parallel execution; different results on repeated runs.

### Pitfall 4: System Prompt Bloat
**What goes wrong:** System prompts grow to 5000+ tokens, consuming agent context budget before any actual work context is loaded.
**Why it happens:** Trying to encode every possible behavior in the system prompt.
**How to avoid:** Keep system prompts under 1000 tokens. Use L0 context for core instructions and L1 for phase-specific guidance. The LLM model handles most reasoning without exhaustive instructions.
**Warning signs:** System prompt exceeds 1500 tokens; agent L0 context tier is exhausted by the prompt alone.

### Pitfall 5: Missing Agent Registration
**What goes wrong:** Agent class exists but is not registered in the AgentRegistry, so the pipeline cannot instantiate it.
**Why it happens:** Agent code is written but the `@register_agent` decorator or registry entry is forgotten.
**How to avoid:** Use the decorator pattern on every agent class. The registry should be checked at startup and emit warnings for any AgentType without a registered class.
**Warning signs:** `ValueError: No agent registered for type X` at runtime.

### Pitfall 6: Ignoring the Vertical Slice Reference
**What goes wrong:** Phase 9 agents are implemented with different patterns than the Phase 7 vertical slice agents, creating inconsistency.
**Why it happens:** Different developer, different session, drift from established patterns.
**How to avoid:** Use the Phase 7 agents (Orchestrator, Backend Dev, Code Reviewer, Tester, Debugger) as the canonical reference implementation. All Phase 9 agents should follow the same BaseAgent subclass pattern, same YAML config structure, same tool registration pattern.
**Warning signs:** New agent code looks structurally different from Phase 7 agents.

## Code Examples

### Agent Registry Bootstrap (verified from Phase 3 research)

```python
# apps/server/src/codebot/agents/__init__.py
"""Agent package -- imports trigger registration."""
from codebot.agents.registry import create_agent, get_all_registered  # noqa: F401

# Import all agent modules to trigger @register_agent decorators
from codebot.agents import (  # noqa: F401
    brainstorming,
    researcher,
    architect,
    designer,
    template_curator,
    database_designer,
    api_designer,
    planner,
    techstack_builder,
    frontend_dev,
    backend_dev,
    middleware_dev,
    mobile_dev,
    infra_engineer,
    integrations,
    code_reviewer,
    security_auditor,
    accessibility,
    performance,
    i18n_l10n,
    tester,
    debugger,
    doc_writer,
    devops,
    github_agent,
    orchestrator,
    project_manager,
    skill_creator,
    hooks_creator,
    tools_creator,
)
```

### Parallel Stage Subgraph Execution

```python
# Example: S6 QA stage with parallel agents
import asyncio
from typing import Any


async def execute_qa_stage(shared_state: dict[str, Any]) -> dict[str, Any]:
    """Execute S6 QA agents in parallel, merge results."""
    qa_agents = [
        create_agent(AgentType.CODE_REVIEWER, load_config("code_reviewer")),
        create_agent(AgentType.SECURITY_AUDITOR, load_config("security_auditor")),
        create_agent(AgentType.ACCESSIBILITY_AUDITOR, load_config("accessibility")),
        create_agent(AgentType.PERFORMANCE_TESTER, load_config("performance")),
        create_agent(AgentType.I18N_SPECIALIST, load_config("i18n_l10n")),
    ]

    agent_input = AgentInput(
        task_id=current_task_id,
        shared_state=shared_state,
        context_tiers=assemble_l0_l1(),
    )

    results: dict[str, AgentOutput] = {}
    async with asyncio.TaskGroup() as tg:
        for agent in qa_agents:
            async def run(a=agent):
                output = await a.execute(agent_input)
                results[a.agent_type.value] = output
            tg.create_task(run())

    # Merge all QA reports
    merged = merge_qa_results(results)
    # Check quality gate
    gate_passed = evaluate_qa_gate(merged)
    return {"qa_results": merged, "qa_gate_passed": gate_passed}
```

### Event Sourcing for Audit Trail

```python
# Pattern for EVNT-02, EVNT-03, EVNT-04
from agent_sdk.models.events import AgentEvent, EventEnvelope
from agent_sdk.models.enums import EventType


async def emit_agent_event(
    event_bus,
    agent_type: str,
    event_type: EventType,
    payload: dict,
) -> None:
    """Emit an event for every agent action for full audit trail."""
    event = EventEnvelope(
        event_type=event_type,
        source=f"agent.{agent_type}",
        payload=payload,
        # JetStream persists for replay (EVNT-02)
        # Full payload enables pipeline reconstruction (EVNT-04)
    )
    await event_bus.publish(event)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single agent does everything | Specialized agents with clear domains | MASFactory pattern (2026) | Better quality per domain, parallel execution |
| Hardcoded agent behavior | YAML-declarative configuration | Phase 3 decision | Hot-reload, marketplace, non-code configuration |
| Sequential pipeline | Parallel fan-out/fan-in stages | Phase 2/6 graph engine | 3-5x faster pipeline execution for S3/S5/S6 |
| Manual code review | AI Code Reviewer + Security Scanner | Phase 7/8 foundation | Automated quality gates before human review |
| Single LLM provider | Multi-LLM routing | Phase 4 LiteLLM | Cost optimization, capability matching per task |

**Deprecated/outdated:**
- Direct LLM API calls (use LiteLLM abstraction from Phase 4)
- Shared working directories for coding agents (use git worktrees from Phase 8)
- In-memory event passing (use NATS JetStream for persistence and replay)

## Open Questions

1. **Tool Implementation Depth**
   - What we know: Each agent has 4-8 tools specified in AGENT_CATALOG. Many are CLI wrappers.
   - What's unclear: How deep should tool implementations be in Phase 9 vs. later phases? Full CLI integrations vs. stub tools?
   - Recommendation: Implement tools as thin async wrappers around subprocess calls for CLI tools (semgrep, trivy, lighthouse, etc.) and httpx calls for API tools. The LLM agent parses the output. Full SDK integrations can come later.

2. **Agent-Specific System Prompts**
   - What we know: Each agent needs a system prompt in its YAML config.
   - What's unclear: Optimal prompt engineering for each of the 30 agents.
   - Recommendation: Start with concise prompts (500-800 tokens) based on the AGENT_CATALOG responsibilities. Iterate based on output quality. Do not over-engineer prompts upfront.

3. **Tooling Agents (Skill/Hooks/Tools Creator) Scope**
   - What we know: AGNT-09, AGNT-10, AGNT-11 are assigned to Phase 11 in the requirements traceability.
   - What's unclear: Phase 9 requires AGNT-08 (30 agents registered), which includes Tooling agents.
   - Recommendation: Implement Tooling agents as minimal stubs that satisfy AGNT-08 registration but defer full functionality to Phase 11. The stubs should extend BaseAgent, have YAML configs, but produce minimal/placeholder outputs.

4. **Integration with Phase 6 Pipeline Orchestration**
   - What we know: Phase 6 builds the pipeline orchestrator with Temporal. Agents need to be wired into stage subgraphs.
   - What's unclear: Exact Temporal activity interface for agent execution.
   - Recommendation: Define agents as Temporal activities. Each stage creates a subgraph that fans out to agents and fans in results. The pipeline orchestrator calls `execute_stage(stage_config)` which internally creates agents and runs them.

5. **Existing Phase 7 Agents: Extension vs. Rewrite**
   - What we know: Phase 7 implements Orchestrator, Backend Dev, Code Reviewer, Tester, Debugger.
   - What's unclear: How much these agents need to change for Phase 9 (extended tools, broader scope).
   - Recommendation: Extend, do not rewrite. Add new tools (TEST-03 Playwright for Tester, DBUG-04 security debugging for Debugger), update YAML configs, but preserve the existing PRA cycle implementations.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio |
| Config file | `apps/server/pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run pytest apps/server/tests/unit/ -x --tb=short` |
| Full suite command | `uv run pytest apps/server/tests/ -x --tb=short` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AGNT-08 | All 30 agents registered | unit | `uv run pytest apps/server/tests/unit/test_agent_registry.py -x` | Wave 0 |
| BRST-01 | Brainstorming explores ideas | unit | `uv run pytest apps/server/tests/unit/test_brainstorming.py -x` | Wave 0 |
| RSRC-01 | Researcher evaluates libraries | unit | `uv run pytest apps/server/tests/unit/test_researcher.py -x` | Wave 0 |
| ARCH-05 | S3 agents parallel execution | integration | `uv run pytest apps/server/tests/integration/test_s3_parallel.py -x` | Wave 0 |
| IMPL-01 | Frontend agent generates code | unit | `uv run pytest apps/server/tests/unit/test_frontend_dev.py -x` | Wave 0 |
| QA-07 | S6 agents parallel execution | integration | `uv run pytest apps/server/tests/integration/test_s6_parallel.py -x` | Wave 0 |
| DOCS-01 | Doc agent generates API docs | unit | `uv run pytest apps/server/tests/unit/test_doc_writer.py -x` | Wave 0 |
| EVNT-03 | Full audit trail persisted | integration | `uv run pytest apps/server/tests/integration/test_event_audit.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest apps/server/tests/unit/ -x --tb=short -q`
- **Per wave merge:** `uv run pytest apps/server/tests/ -x --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `apps/server/tests/unit/test_agent_registry.py` -- covers AGNT-08 (all 30 agents registered)
- [ ] `apps/server/tests/unit/test_brainstorming.py` -- covers BRST-01 through BRST-07
- [ ] `apps/server/tests/unit/test_researcher.py` -- covers RSRC-01 through RSRC-04
- [ ] `apps/server/tests/unit/test_architect.py` -- covers ARCH-01
- [ ] `apps/server/tests/unit/test_designer.py` -- covers ARCH-04
- [ ] `apps/server/tests/unit/test_planner.py` -- covers PLAN-01 through PLAN-03
- [ ] `apps/server/tests/unit/test_frontend_dev.py` -- covers IMPL-01
- [ ] `apps/server/tests/unit/test_mobile_dev.py` -- covers IMPL-03
- [ ] `apps/server/tests/unit/test_infra_engineer.py` -- covers IMPL-04
- [ ] `apps/server/tests/unit/test_accessibility.py` -- covers QA-03
- [ ] `apps/server/tests/unit/test_performance.py` -- covers QA-04
- [ ] `apps/server/tests/unit/test_i18n.py` -- covers QA-05
- [ ] `apps/server/tests/unit/test_doc_writer.py` -- covers DOCS-01 through DOCS-04
- [ ] `apps/server/tests/integration/test_s3_parallel.py` -- covers ARCH-05
- [ ] `apps/server/tests/integration/test_s6_parallel.py` -- covers QA-07
- [ ] `apps/server/tests/integration/test_event_audit.py` -- covers EVNT-02 through EVNT-04
- [ ] `apps/server/tests/conftest.py` -- extend with agent mock fixtures (mock LLM, mock tools)
- [ ] Framework install: already available from Phase 1

## Sources

### Primary (HIGH confidence)
- `docs/design/AGENT_CATALOG.md` -- Complete specification for all 30 agents including tools, I/O, LLM config, YAML config, error handling, and interaction patterns
- `docs/workflows/AGENT_WORKFLOWS.md` -- Phase workflows, execution strategies, gate definitions, parallel execution patterns
- `docs/design/SYSTEM_DESIGN.md` -- Graph engine design, node types, edge types, execution flow
- `.planning/phases/03-agent-framework/03-RESEARCH.md` -- BaseAgent architecture, PRA cycle, state machine, YAML config patterns
- `libs/agent-sdk/src/agent_sdk/models/enums.py` -- All 30 AgentType enum values already defined
- `apps/server/src/codebot/db/models/agent.py` -- Agent ORM model with all fields

### Secondary (MEDIUM confidence)
- `.planning/ROADMAP.md` -- Phase 9 scope and success criteria
- `.planning/REQUIREMENTS.md` -- Full requirement text for all 43 Phase 9 requirements

### Tertiary (LOW confidence)
- Agent tool implementations (web_search, diagram_generator, etc.) -- exact API integrations need verification at implementation time against current API versions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in project from Phases 1-8, no new dependencies needed
- Architecture: HIGH -- BaseAgent, AgentNode, YAML config, state machine patterns established in Phase 3 and validated in Phase 7
- Pitfalls: HIGH -- common multi-agent system challenges are well-documented; parallel execution patterns are established
- Agent specifications: HIGH -- AGENT_CATALOG provides exhaustive detail for all 30 agents
- Tool implementations: MEDIUM -- tool specifications are clear but actual API integrations (Tavily, axe-core, Lighthouse CLI) need runtime verification

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable -- agent framework is established, specifications are locked)
