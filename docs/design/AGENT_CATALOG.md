# CodeBot — Enhanced Agent Catalog

**Version:** 2.5
**Date:** 2026-03-18
**Status:** Draft
**Architecture:** Graph-Centric Multi-Agent System (inspired by MASFactory, arXiv:2603.06007)
**Related:** [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) | [AGENT_WORKFLOWS.md](../workflows/AGENT_WORKFLOWS.md) | [ARCHITECTURE.md](../architecture/ARCHITECTURE.md)

---

## Table of Contents

1. [Agent Catalog Overview](#agent-catalog-overview)
2. [Agent Category Summary](#agent-category-summary)
3. [Agent Graph Visualization](#agent-graph-visualization)
4. [Orchestration Agents](#orchestration-agents)
5. [Ideation Agents](#ideation-agents)
6. [Planning Agents](#planning-agents)
7. [Research Agents](#research-agents)
8. [Design Agents](#design-agents)
9. [Implementation Agents](#implementation-agents)
10. [Quality Agents](#quality-agents)
11. [Testing Agents](#testing-agents)
12. [Operations Agents](#operations-agents)
13. [Tooling Agents](#tooling-agents)
14. [Coordination Agents](#coordination-agents)
15. [Agent Collaboration Matrix](#agent-collaboration-matrix)
16. [Agent Scaling Strategy](#agent-scaling-strategy)
17. [Agent Extension Points](#agent-extension-points)
18. [Agent Template Configurations](#agent-template-configurations)

---

## Agent Catalog Overview

CodeBot employs **30 specialized agents** organized across **10 categories** to cover every aspect of the software development lifecycle. Each agent is a node in a directed computation graph, with typed edges encoding data flow, message passing, and control signals between them.

All agents share a common state machine and cognitive model:

```
IDLE --> INITIALIZING --> EXECUTING --> REVIEWING --> COMPLETED
  \          |               |              |            /
   \         v               v              v           /
    +----> FAILED <---------+--------------+----------+
              |
              v
          RECOVERING --> EXECUTING (retry)
```

**Agent Status Definitions:**

| Status | Description |
|--------|-------------|
| IDLE | Agent instantiated but not yet assigned a task |
| INITIALIZING | Loading system prompt, context tiers, and tools |
| EXECUTING | Running the Perception-Reasoning-Action (PRA) cognitive cycle (see below) |
| REVIEWING | Self-reviewing output against acceptance criteria |
| COMPLETED | Task finished successfully; output artifacts available |
| FAILED | Task failed after exhausting retries; escalation triggered |
| RECOVERING | Applying recovery strategy before retry |

**Perception-Reasoning-Action (PRA) Cognitive Cycle:**

During the EXECUTING state, every agent operates on the MASFactory PRA loop:

1. **Perception** — Assemble context: load L0/L1/L2 context tiers, read MCP resources, retrieve episodic memory, ingest upstream SharedState
2. **Reasoning** — Invoke the LLM with assembled context, system prompt, and tool schemas; the model analyzes the task, forms a plan, and selects the next action
3. **Action** — Execute the chosen action: invoke tools (file ops, code gen, git), delegate to sub-agents, emit events, or update SharedState

The PRA cycle repeats within `execute()` until the agent produces a final output, exhausts its token budget, or hits its max iteration limit. State is checkpointed between iterations for crash recovery. See SYSTEM_DESIGN.md Section 2.0.1 for the full specification.

---

## Agent Category Summary

| Category | Agents | Count | Pipeline Phase |
|----------|--------|-------|----------------|
| Orchestration | Orchestrator | 1 | All phases |
| Ideation | Brainstorming | 1 | Pre-planning |
| Planning | Planner, TechStack Builder | 2 | Phase 1 |
| Research | Researcher | 1 | Phase 2 |
| Design | Architect, Designer, Template, Database, API Gateway | 5 | Phase 3-4 |
| Implementation | Frontend Dev, Backend Dev, Middleware Dev, Mobile Dev, Infrastructure Engineer | 5 | Phase 5 |
| Quality | Security Auditor, Code Reviewer, Accessibility, Performance, i18n/L10n | 5 | Phase 6 |
| Testing | Tester, Debugger | 2 | Phase 7-8 |
| Operations | DevOps, GitHub, Documentation Writer | 3 | Phase 9-10 |
| Tooling | Skill Creator, Hooks Creator, Tools Creator, Integrations | 4 | Cross-cutting |
| Coordination | Project Manager | 1 | Cross-cutting |
| **Total** | | **30** | |

---

## Agent Graph Visualization

```
                                    USER INPUT (PRD)
                                         |
                                         v
                               +-------------------+
                               |   ORCHESTRATOR    |-------> monitors all agents
                               +--------+----------+
                                        |
                                        v
                               +-------------------+
                               |  BRAINSTORMING    |
                               +--------+----------+
                                        |
                          +-------------+-------------+
                          |                           |
                          v                           v
                  +---------------+         +------------------+
                  |    PLANNER    |         | TECHSTACK BUILDER|
                  +-------+-------+         +--------+---------+
                          |                          |
                          +------------+-------------+
                                       |
                                       v
                              +-------------------+
                              |    RESEARCHER     |
                              +--------+----------+
                                       |
                     +-----------+-----+-----+-----------+
                     |           |           |           |
                     v           v           v           v
              +-----------+ +--------+ +----------+ +------------+
              | ARCHITECT | |DESIGNER| |DATABASE  | |API GATEWAY |
              +-----+-----+ +---+----+ +----+-----+ +-----+------+
                    |            |           |              |
                    |            v           |              |
                    |      +-----------+     |              |
                    |      | TEMPLATE  |     |              |
                    |      +-----+-----+     |              |
                    |            |           |              |
          +---------+----+-------+-----+-----+------+------+
          |              |             |            |
          v              v             v            v
   +-----------+  +-----------+  +-----------+  +-----------+
   |FRONTEND   |  |BACKEND    |  |MIDDLEWARE |  |INFRA      |
   |DEVELOPER  |  |DEVELOPER  |  |DEVELOPER  |  |ENGINEER   |
   +-----------+  +-----------+  +-----------+  +-----------+
          |              |             |            |
          |         +----+             |            |
          |         |    +-----+-------+            |
          |         |          |                    |
          |         v          v                    |
          |   +-----------+  +-----------+          |
          +-->|MOBILE DEV |  |INTEGRATIONS|<--------+
              +-----------+  +-----------+
                    |              |
     +---------+---+----+---------+----+---------+
     |         |        |              |         |
     v         v        v              v         v
+--------+ +--------+ +-----------+ +------+ +-------+
|CODE    | |SECURITY| |ACCESSIBLTY| |PERF  | |i18n   |
|REVIEWER| |AUDITOR | |AGENT      | |AGENT | |L10n   |
+--------+ +--------+ +-----------+ +------+ +-------+
     |         |        |              |         |
     +---------+--------+--------------+---------+
                         |
                         v
                  +-------------+
                  |   TESTER    |
                  +------+------+
                         |
                         v
                  +-------------+
                  |  DEBUGGER   |<------- fix loop (max 5 iterations)
                  +------+------+
                         |
          +--------------+---------------+
          |              |               |
          v              v               v
   +-----------+  +-----------+   +-----------+
   |  DEVOPS   |  |  GITHUB   |   |DOC WRITER |
   +-----------+  +-----------+   +-----------+
          |              |               |
          +--------------+---------------+
                         |
          +--------------+---------------+
          |              |               |
          v              v               v
   +-----------+  +-----------+   +-----------+
   |SKILL      |  |HOOKS      |   |TOOLS      |
   |CREATOR    |  |CREATOR    |   |CREATOR    |
   +-----------+  +-----------+   +-----------+
                         |
                         v
                    [DELIVERY]
```

---

## Orchestration Agents

---

### 1. Orchestrator Agent

#### Overview
- **Role**: Master coordinator of the entire SDLC pipeline
- **Category**: Orchestration
- **Graph Position**: Root node; supervises all other nodes
- **Upstream Dependencies**: User input (PRD), Human-in-the-loop approvals
- **Downstream Consumers**: All 28 other agents

#### Responsibilities
1. Parse and validate incoming PRD or natural language requirements
2. Decompose high-level requirements into a task dependency graph
3. Assign agents to tasks based on task type, complexity, and model routing strategy
4. Manage phase transitions (planning to research to architecture to implementation, etc.)
5. Monitor agent progress in real-time and emit WebSocket events to the dashboard
6. Handle error escalation: retry, reassign, or escalate to human
7. Enforce human-in-the-loop approval gates at architecture and delivery phases
8. Manage token budgets and cost tracking across all agents
9. Coordinate parallel agent execution during implementation and review phases
10. Produce final delivery report summarizing all decisions, artifacts, and metrics

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `graph_executor` | Execute the agent DAG with topological ordering | Core graph engine |
| `task_scheduler` | Schedule tasks with dependency resolution | `core/task_scheduler.py` |
| `event_bus` | Publish/subscribe real-time events | NATS + JetStream (or in-memory for dev) |
| `checkpoint_manager` | Save/restore pipeline state | Filesystem + database |
| `budget_tracker` | Monitor token usage and cost per agent | LLM cost module |
| `approval_gate` | Block execution pending human approval | WebSocket + REST API |
| `agent_registry` | Instantiate and configure agent instances | Agent factory |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| PRD document | User upload or API submission | Markdown, JSON, or YAML |
| Human approvals | Dashboard or CLI | Boolean + optional feedback |
| Agent results | All downstream agents | Structured JSON artifacts |
| Error reports | Failed agents | Error objects with stack traces |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Task graph | Planner, all agents | JSON DAG definition |
| Phase transition signals | Pipeline engine | Control flow events |
| Progress updates | Dashboard WebSocket | Real-time event stream |
| Delivery report | User | Markdown summary document |
| Cost report | User, budget system | JSON with per-agent breakdown |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| PRD parsing & decomposition | Claude Opus 4 | GPT-4.1 | Complex reasoning required for requirement extraction |
| Task graph construction | Claude Sonnet 4 | Gemini 2.5 Pro | Structured output generation |
| Error triage & escalation | Claude Opus 4 | o3 | Nuanced judgment on failure severity |
| Progress summarization | Claude Haiku 3.5 | Gemini 2.5 Flash | Low-latency, cost-effective summaries |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Project summary, current phase, active agents, system prompt | ~2,000 tokens |
| L1 | Task graph, phase outputs, agent status map, recent errors | ~10,000 tokens |
| L2 | Full PRD, architecture decisions, accumulated agent outputs | ~20,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> EXECUTING --> REVIEWING --> COMPLETED
              |               |              |
              v               v              v
           FAILED        RECOVERING       FAILED
              |               |
              v               v
         [ESCALATE]     EXECUTING (retry)
```

#### Error Handling
- **Recovery strategies**: Retry failed agent up to 3 times with exponential backoff; reassign to alternate model on provider failure; reduce context window if token limit exceeded
- **Fallback behaviors**: Switch to fallback LLM provider chain (Anthropic -> OpenAI -> Google); degrade to simpler task decomposition; skip optional phases
- **Escalation paths**: After 3 retries, pause pipeline and emit `HumanApprovalRequired` event; log full error context for human review

#### Interaction Patterns
- **Primary collaborators**: Planner (task handoff), all Implementation agents (progress monitoring), Debugger (fix loop coordination)
- **Communication protocol**: State flow for shared context propagation; control flow for phase transitions; message flow for error escalation
- **Conflict resolution**: Orchestrator has final authority on task priority and agent assignment; merge conflicts resolved via three-way merge with human fallback

#### Configuration
```yaml
orchestrator:
  model: claude-opus-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 8192
  temperature: 0.3
  tools:
    - graph_executor
    - task_scheduler
    - event_bus
    - checkpoint_manager
    - budget_tracker
    - approval_gate
    - agent_registry
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 20000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 2
    max_delay_seconds: 60
    exponential_base: 2
  timeout: 600
  human_gates:
    - post_planning
    - post_architecture
    - pre_delivery
```

---

## Ideation Agents

---

### 2. Brainstorming Agent

#### Overview
- **Role**: Facilitates initial brainstorming and idea exploration before formal planning
- **Category**: Ideation
- **Graph Position**: Between Orchestrator and Planner; first creative phase
- **Upstream Dependencies**: Orchestrator (parsed PRD)
- **Downstream Consumers**: Planner, TechStack Builder, Architect

#### Responsibilities
1. Explore the solution space by generating multiple alternative approaches to the requirements
2. Identify potential technical challenges, risks, and unknowns early in the process
3. Refine ambiguous requirements through interactive Q&A with the user
4. Perform divergent thinking: generate 3-5 distinct architectural approaches (e.g., monolith vs. microservices vs. serverless)
5. Perform convergent refinement: evaluate trade-offs and recommend the top 1-2 approaches
6. Identify missing requirements or implicit assumptions that should be made explicit
7. Generate a creativity report summarizing explored ideas, rejected alternatives, and rationale

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `web_search` | Research comparable products and prior art | Tavily / SerpAPI |
| `idea_matrix` | Generate structured comparison of approaches | Internal template engine |
| `user_dialog` | Interactive Q&A with the user for clarification | WebSocket / CLI |
| `reference_finder` | Find open-source reference implementations | GitHub API |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Parsed PRD | Orchestrator | Structured JSON requirements |
| User clarifications | Human-in-the-loop | Natural language responses |
| Domain context | User or prior projects | Markdown documents |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Creativity report | Planner, Architect | Markdown with comparison tables |
| Refined requirements | Planner, TechStack Builder | Updated JSON requirements |
| Risk register | Orchestrator, Architect | JSON list of identified risks |
| Recommended approaches | TechStack Builder, Architect | Ranked list with trade-off analysis |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Divergent idea generation | Claude Opus 4 | o3 | High creativity and broad knowledge |
| Trade-off analysis | Gemini 2.5 Pro | Claude Sonnet 4 | Long-context comparative reasoning |
| Interactive Q&A | Claude Sonnet 4 | GPT-4.1 | Conversational fluency |
| Report generation | Claude Haiku 3.5 | Gemini 2.5 Flash | Cost-effective document generation |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Project summary, brainstorming prompt, agent instructions | ~2,000 tokens |
| L1 | Full PRD, domain-specific context, user Q&A history | ~10,000 tokens |
| L2 | Reference implementations, competitor analysis, prior art | ~20,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> EXECUTING --> REVIEWING --> COMPLETED
                              |
                              v
                      WAITING_FOR_USER --> EXECUTING (resumed)
```

#### Error Handling
- **Recovery strategies**: If idea generation produces generic results, inject domain-specific context from L2 and retry; if user is unresponsive to clarification requests, proceed with documented assumptions
- **Fallback behaviors**: Skip brainstorming phase entirely if PRD is sufficiently detailed (>5,000 words with clear technical constraints)
- **Escalation paths**: Flag ambiguous requirements for human review before passing to Planner

#### Interaction Patterns
- **Primary collaborators**: Orchestrator (receives PRD, reports completion), Planner (hands off refined requirements), TechStack Builder (provides recommended approaches)
- **Communication protocol**: Message flow for user Q&A; state flow for refined requirements propagation
- **Conflict resolution**: If user rejects all proposed approaches, re-enter divergent thinking with adjusted constraints

#### Configuration
```yaml
brainstorming:
  model: claude-opus-4
  fallback_model: o3
  provider: anthropic
  max_tokens: 8192
  temperature: 0.7
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

---

## Planning Agents

---

### 3. Planner Agent

#### Overview
- **Role**: Project planning, task decomposition, and dependency scheduling
- **Category**: Planning
- **Graph Position**: After Brainstorming; before Research and Architecture
- **Upstream Dependencies**: Orchestrator (PRD), Brainstorming Agent (refined requirements)
- **Downstream Consumers**: Researcher, Architect, all Implementation agents

#### Responsibilities
1. Decompose refined requirements into epics, stories, and tasks with clear acceptance criteria
2. Create a task dependency graph with topological ordering for execution
3. Identify opportunities for parallel execution across implementation agents
4. Estimate task complexity using a weighted scoring model (1-13 Fibonacci scale)
5. Assign task priorities based on dependency depth and business value
6. Generate critical path analysis to identify bottleneck tasks
7. Create milestone definitions with measurable completion criteria
8. Produce a project execution plan document

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `task_decomposer` | Break epics into stories and tasks | Internal NLP pipeline |
| `dependency_resolver` | Build and validate task dependency graph | Graph engine |
| `complexity_estimator` | Score task complexity (1-13 scale) | LLM-based heuristics |
| `critical_path_analyzer` | Identify longest dependency chain | Topological sort algorithm |
| `parallel_scheduler` | Group independent tasks for concurrent execution | Graph scheduler |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Refined requirements | Brainstorming Agent | JSON with requirements list |
| Creativity report | Brainstorming Agent | Markdown with recommended approaches |
| Project constraints | Orchestrator | JSON (budget, timeline, tech preferences) |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Task dependency graph | Orchestrator, all agents | JSON DAG with nodes and edges |
| Execution plan | Orchestrator, Dashboard | Markdown document |
| Complexity estimates | Orchestrator (for LLM routing) | JSON map of task_id to score |
| Milestone definitions | Orchestrator, Dashboard | JSON with criteria |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Requirement decomposition | Claude Sonnet 4 | GPT-4.1 | Structured reasoning with good instruction following |
| Dependency analysis | Claude Sonnet 4 | Gemini 2.5 Pro | Logical relationship extraction |
| Complexity estimation | Claude Haiku 3.5 | GPT-4.1-mini | Fast, cost-effective scoring |
| Plan document generation | Gemini 2.5 Flash | Claude Haiku 3.5 | Long-form document generation |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Project summary, planning instructions, task template | ~2,000 tokens |
| L1 | Full refined requirements, creativity report, constraints | ~10,000 tokens |
| L2 | Reference project plans, estimation benchmarks | ~15,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> EXECUTING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If decomposition produces tasks that are too coarse, increase decomposition depth parameter and retry; if circular dependencies are detected, flag and request human clarification
- **Fallback behaviors**: Use a simpler flat task list if dependency graph becomes too complex (>200 nodes)
- **Escalation paths**: Escalate to Orchestrator if requirements are contradictory or infeasible

#### Interaction Patterns
- **Primary collaborators**: Brainstorming (receives refined requirements), Orchestrator (reports plan), Researcher (hands off research topics), Architect (provides task structure)
- **Communication protocol**: State flow for plan propagation; message flow for clarification requests
- **Conflict resolution**: Planner has authority on task ordering; Architect can request re-planning if architecture constraints invalidate the plan

#### Configuration
```yaml
planner:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 4096
  temperature: 0.2
  tools:
    - task_decomposer
    - dependency_resolver
    - complexity_estimator
    - critical_path_analyzer
    - parallel_scheduler
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 15000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 2
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 300
  settings:
    max_task_depth: 3
    complexity_scale: fibonacci
    enable_parallel_scheduling: true
```

---

### 4. TechStack Builder Agent

#### Overview
- **Role**: Technology selection, compatibility validation, and environment configuration
- **Category**: Planning
- **Graph Position**: Parallel with Planner; feeds into Architect and all Implementation agents
- **Upstream Dependencies**: Brainstorming Agent (recommended approaches), Orchestrator (constraints)
- **Downstream Consumers**: Architect, all Implementation agents, Infrastructure Engineer

#### Responsibilities
1. Recommend programming languages, frameworks, and libraries based on project requirements
2. Select databases (SQL, NoSQL, vector) appropriate for the data model and scale requirements
3. Choose hosting/deployment targets (AWS, GCP, Azure, Vercel, Railway) based on constraints
4. Validate compatibility between selected technologies (version conflicts, license compatibility)
5. Generate configuration files: `package.json`, `pyproject.toml`, `docker-compose.yml`, etc.
6. Set up development environment specifications (dev containers, toolchain requirements)
7. Produce a technology decision record (TDR) documenting rationale for each selection

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `package_registry` | Query npm, PyPI, crates.io for package metadata | HTTP APIs |
| `compatibility_checker` | Validate version compatibility across dependencies | Internal resolver |
| `license_scanner` | Check dependency license compatibility | ScanCode integration |
| `config_generator` | Generate project configuration files | Template engine (Jinja2) |
| `benchmark_db` | Compare framework performance benchmarks | Internal database |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Recommended approaches | Brainstorming Agent | Ranked list with trade-offs |
| Project constraints | Orchestrator | JSON (performance, scale, budget) |
| Non-functional requirements | PRD | Extracted NFRs |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Tech stack specification | Architect, all Implementation agents | JSON tech_stack object |
| Configuration files | Infrastructure Engineer, Implementation agents | Generated files (YAML, JSON, TOML) |
| Technology decision record | Documentation Writer, User | Markdown ADR document |
| Dependency manifest | Security Auditor | Lock files (package-lock, uv.lock) |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Technology recommendation | Claude Opus 4 | Gemini 2.5 Pro | Broad knowledge of ecosystem trade-offs |
| Compatibility validation | Claude Sonnet 4 | GPT-4.1 | Precise version constraint reasoning |
| Config file generation | Claude Haiku 3.5 | GPT-4.1-mini | Template-based generation, low complexity |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Project summary, tech constraints, agent instructions | ~2,000 tokens |
| L1 | Full requirements, recommended approaches, NFRs | ~8,000 tokens |
| L2 | Framework comparisons, benchmark data, ecosystem reports | ~15,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> EXECUTING --> VALIDATING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If selected packages have known vulnerabilities, substitute with alternatives; if version conflicts are unresolvable, relax version constraints and document trade-offs
- **Fallback behaviors**: Default to well-established, stable technology choices (React, FastAPI, PostgreSQL) when novel frameworks lack sufficient validation data
- **Escalation paths**: Flag license incompatibilities and breaking version conflicts to Orchestrator for human decision

#### Interaction Patterns
- **Primary collaborators**: Brainstorming (receives approaches), Architect (provides stack for architecture), Infrastructure Engineer (provides deployment config), Security Auditor (provides dependency manifest)
- **Communication protocol**: State flow for tech stack propagation; message flow for compatibility alerts
- **Conflict resolution**: TechStack Builder has authority on dependency versions; Architect can request stack changes if architectural constraints conflict

#### Configuration
```yaml
techstack_builder:
  model: claude-opus-4
  fallback_model: gemini-2.5-pro
  provider: anthropic
  max_tokens: 4096
  temperature: 0.2
  tools:
    - package_registry
    - compatibility_checker
    - license_scanner
    - config_generator
    - benchmark_db
  context_tiers:
    l0: 2000
    l1: 8000
    l2: 15000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 3
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 240
  settings:
    prefer_stable: true
    license_policy: permissive_only
    validate_compatibility: true
```

---

## Research Agents

---

### 5. Researcher Agent

#### Overview
- **Role**: Technology research, pattern discovery, and reference implementation analysis
- **Category**: Research
- **Graph Position**: After Planning; before Architecture and Design
- **Upstream Dependencies**: Planner (research topics from plan), TechStack Builder (selected technologies)
- **Downstream Consumers**: Architect, Designer, all Implementation agents

#### Responsibilities
1. Investigate frameworks, libraries, and APIs identified in the project plan
2. Evaluate third-party dependencies for security posture, maintenance status, and community health
3. Discover design patterns and architectural patterns applicable to the requirements
4. Find and analyze reference implementations and open-source projects with similar requirements
5. Research API documentation for external services the project will integrate with
6. Assess licensing implications of all researched dependencies
7. Produce a structured research report with findings, recommendations, and citations

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `web_search` | General web search for documentation and articles | Tavily / SerpAPI |
| `github_search` | Search GitHub for reference implementations | GitHub API |
| `npm_registry` | Query npm package metadata, downloads, issues | npm API |
| `pypi_registry` | Query PyPI package metadata and versions | PyPI API |
| `arxiv_search` | Search academic papers for algorithms and patterns | arXiv API |
| `docs_reader` | Parse and summarize technical documentation | Web scraper + LLM |
| `dependency_analyzer` | Analyze dependency health (stars, issues, last commit) | GitHub + registry APIs |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Research topics | Planner | JSON list of topics with priority |
| Tech stack | TechStack Builder | JSON tech stack specification |
| Specific questions | Architect, Designer | Message flow queries |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Research report | Architect, Designer, Orchestrator | Markdown document with citations |
| Dependency evaluations | Security Auditor, TechStack Builder | JSON health scores per dependency |
| Reference implementations | Implementation agents | JSON list of repos with analysis |
| Pattern recommendations | Architect | JSON list of applicable patterns |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Research synthesis | Gemini 2.5 Pro | Claude Opus 4 | 1M+ token context for large documentation sets |
| Dependency evaluation | Claude Sonnet 4 | GPT-4.1 | Analytical reasoning on security and health metrics |
| Documentation summarization | Gemini 2.5 Flash | Claude Haiku 3.5 | Fast processing of large documents |
| Pattern matching | Claude Opus 4 | o3 | Deep domain knowledge for pattern identification |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Research topics, tech stack summary, agent instructions | ~2,000 tokens |
| L1 | Full project plan, technology constraints, prior research | ~10,000 tokens |
| L2 | External documentation, API specs, reference code | ~25,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> RESEARCHING --> SYNTHESIZING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If web search fails, fall back to LLM knowledge; if package registry is unreachable, use cached data; if research is inconclusive, flag gaps and proceed with documented assumptions
- **Fallback behaviors**: Use LLM's training data as fallback when live research APIs are unavailable; reduce research scope to critical dependencies only under time pressure
- **Escalation paths**: Escalate to human when license concerns are found (GPL/AGPL in dependency tree) or when critical dependencies have known unpatched vulnerabilities

#### Interaction Patterns
- **Primary collaborators**: Planner (receives research topics), Architect (provides findings for architecture decisions), TechStack Builder (feeds back dependency evaluations)
- **Communication protocol**: State flow for research report; message flow for ad-hoc queries from Architect/Designer
- **Conflict resolution**: Researcher provides recommendations; Architect makes final decisions on pattern adoption

#### Configuration
```yaml
researcher:
  model: gemini-2.5-pro
  fallback_model: claude-opus-4
  provider: google
  max_tokens: 8192
  temperature: 0.4
  tools:
    - web_search
    - github_search
    - npm_registry
    - pypi_registry
    - arxiv_search
    - docs_reader
    - dependency_analyzer
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 25000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 5
    max_delay_seconds: 60
    exponential_base: 2
  timeout: 600
  settings:
    max_search_results: 20
    dependency_health_threshold: 0.6
    require_license_check: true
```

---

## Design Agents

---

### 6. Architect Agent

#### Overview
- **Role**: System architecture design, API contract definition, and component boundary specification
- **Category**: Design
- **Graph Position**: After Research; before Designer and all Implementation agents
- **Upstream Dependencies**: Planner (task graph), Researcher (research report), TechStack Builder (tech stack)
- **Downstream Consumers**: Designer, Database Agent, API Gateway Agent, all Implementation agents

#### Responsibilities
1. Create C4-model architecture diagrams (Context, Container, Component, Code levels)
2. Define component boundaries with clear interfaces and responsibilities
3. Design API contracts (REST endpoints, GraphQL schema, gRPC services)
4. Plan database schema at the logical level (entities, relationships, cardinalities)
5. Select architectural patterns: monolith, microservices, serverless, event-driven, or hybrid
6. Define cross-cutting concerns: authentication, authorization, logging, monitoring, error handling
7. Specify deployment topology and infrastructure requirements
8. Produce an Architecture Decision Record (ADR) for every significant decision

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `diagram_generator` | Generate C4 model diagrams in Mermaid/PlantUML | Mermaid CLI |
| `openapi_generator` | Generate OpenAPI 3.1 specification | Internal template |
| `schema_designer` | Design logical database schema | ERD generation tool |
| `pattern_library` | Reference library of architectural patterns | Internal knowledge base |
| `adr_writer` | Generate Architecture Decision Records | Markdown template engine |
| `file_writer` | Write architecture documents to repository | Git worktree filesystem |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Task graph | Planner | JSON DAG |
| Research report | Researcher | Markdown with recommendations |
| Tech stack | TechStack Builder | JSON specification |
| Refined requirements | Brainstorming Agent | JSON requirements |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Architecture document | All agents, Dashboard | Markdown with embedded diagrams |
| OpenAPI specification | Backend Dev, API Gateway Agent | YAML (OpenAPI 3.1) |
| Logical database schema | Database Agent | JSON schema definition |
| Component diagram | Frontend Dev, Backend Dev | Mermaid diagram code |
| ADRs | Documentation Writer, User | Markdown documents |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Architecture design | Claude Opus 4 | o3 | Deep reasoning for architectural trade-offs |
| API contract design | Claude Sonnet 4 | GPT-4.1 | Precise specification generation |
| Diagram generation | Claude Sonnet 4 | Gemini 2.5 Pro | Structured Mermaid/PlantUML output |
| ADR writing | Claude Sonnet 4 | Gemini 2.5 Flash | Clear, concise technical writing |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Project summary, architecture prompt, selected tech stack | ~2,500 tokens |
| L1 | Full task graph, research report, NFRs, constraints | ~12,000 tokens |
| L2 | Reference architectures, pattern documentation, similar projects | ~20,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> DESIGNING --> DIAGRAMMING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If architecture is rejected at approval gate, incorporate feedback and re-design specific components; if diagram generation fails, produce text-based descriptions as fallback
- **Fallback behaviors**: Default to monolithic architecture for simple projects (<10 components); use established patterns from pattern library rather than novel approaches
- **Escalation paths**: Escalate conflicting NFRs (e.g., "real-time + serverless + SQL") to human for prioritization; flag security-critical architecture decisions

#### Interaction Patterns
- **Primary collaborators**: Researcher (receives findings), Planner (receives task structure), Designer (provides component boundaries), Backend Dev (provides API contracts), Database Agent (provides logical schema)
- **Communication protocol**: State flow for architecture document propagation; message flow for design clarifications
- **Conflict resolution**: Architect has final authority on system-level design; implementation agents can request architectural amendments through the Orchestrator

#### Configuration
```yaml
architect:
  model: claude-opus-4
  fallback_model: o3
  provider: anthropic
  max_tokens: 8192
  temperature: 0.2
  tools:
    - diagram_generator
    - openapi_generator
    - schema_designer
    - pattern_library
    - adr_writer
    - file_writer
  context_tiers:
    l0: 2500
    l1: 12000
    l2: 20000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 5
    max_delay_seconds: 60
    exponential_base: 2
  timeout: 600
  settings:
    diagram_format: mermaid
    api_spec_version: "3.1"
    require_adr: true
```

---

### 7. Designer Agent

#### Overview
- **Role**: UI/UX design, component hierarchy definition, and design system specification
- **Category**: Design
- **Graph Position**: After Architect; before Frontend Developer and Template Agent
- **Upstream Dependencies**: Architect (component boundaries, architecture doc), Researcher (UI/UX research)
- **Downstream Consumers**: Frontend Developer, Template Agent, Accessibility Agent

#### Responsibilities
1. Create component hierarchy trees for the entire user interface
2. Define wireframe layouts for all screens and user flows
3. Specify the design system: color palette, typography scale, spacing system, elevation
4. Design responsive breakpoints and layout strategies (mobile-first or desktop-first)
5. Create user flow diagrams showing navigation paths and state transitions
6. Define component API specifications (props, events, slots) for the UI framework
7. Select and configure a UI component library (Material UI, Ant Design, Shadcn, Tailwind UI)
8. Produce a design specification document with visual guidelines

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `wireframe_generator` | Generate wireframe layouts in ASCII or SVG | Internal renderer |
| `design_system_builder` | Create design tokens and theme configuration | Template engine |
| `component_tree_builder` | Generate hierarchical component structures | AST-based builder |
| `color_palette_generator` | Generate accessible color palettes | Color theory algorithms |
| `user_flow_designer` | Create user flow diagrams | Mermaid flowcharts |
| `responsive_planner` | Define breakpoint strategies and layouts | CSS media query templates |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Architecture document | Architect | Markdown with component diagrams |
| Component boundaries | Architect | JSON component list |
| UI/UX research | Researcher | Markdown with UI pattern recommendations |
| User stories | Planner | JSON with acceptance criteria |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Design specification | Frontend Developer, Template Agent | Markdown with visual specs |
| Component hierarchy | Frontend Developer | JSON tree structure |
| Design tokens | Frontend Developer, Template Agent | JSON/CSS custom properties |
| Wireframe layouts | Frontend Developer, Accessibility Agent | ASCII art or SVG |
| User flow diagrams | Frontend Developer, Tester | Mermaid flowcharts |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Component hierarchy | Claude Sonnet 4 | GPT-4.1 | Structured UI reasoning |
| Design system specification | Claude Sonnet 4 | Gemini 2.5 Pro | Precise token/variable definitions |
| Wireframe generation | Claude Opus 4 | GPT-4.1 | Spatial reasoning for layouts |
| User flow design | Claude Sonnet 4 | Gemini 2.5 Flash | Flowchart generation |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Project summary, design brief, agent instructions | ~2,000 tokens |
| L1 | Architecture doc, component boundaries, user stories | ~10,000 tokens |
| L2 | UI pattern references, design system examples, accessibility guidelines | ~15,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> DESIGNING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If wireframes fail accessibility contrast checks, regenerate with adjusted color palette; if component hierarchy is too deep (>6 levels), flatten and restructure
- **Fallback behaviors**: Use default design system (Shadcn + Tailwind defaults) if custom design system generation fails
- **Escalation paths**: Escalate design decisions requiring brand-specific input to human stakeholders

#### Interaction Patterns
- **Primary collaborators**: Architect (receives component boundaries), Frontend Developer (provides design specs), Template Agent (coordinates on template selection), Accessibility Agent (validates accessibility)
- **Communication protocol**: State flow for design spec propagation; message flow for iterative design refinements
- **Conflict resolution**: Designer has authority on visual and interaction design; Architect can override if structural changes are needed

#### Configuration
```yaml
designer:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 4096
  temperature: 0.3
  tools:
    - wireframe_generator
    - design_system_builder
    - component_tree_builder
    - color_palette_generator
    - user_flow_designer
    - responsive_planner
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 15000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 3
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 300
  settings:
    design_system: shadcn
    css_framework: tailwindcss
    responsive_strategy: mobile_first
```

---

### 8. Template Agent

#### Overview
- **Role**: Manages project templates, scaffolding, and UI component library curation
- **Category**: Design
- **Graph Position**: Parallel with Designer; feeds into Frontend Developer
- **Upstream Dependencies**: Designer (design system specification), TechStack Builder (tech stack)
- **Downstream Consumers**: Frontend Developer, Backend Developer, Infrastructure Engineer

#### Responsibilities
1. Curate and manage a library of UI/UX templates (Material UI, Ant Design, Shadcn, Tailwind UI, custom)
2. Select the optimal template or component library based on the design specification
3. Generate project scaffolding (file structure, boilerplate code, configuration files)
4. Configure build tools (Vite, Webpack, Turbopack) based on the selected tech stack
5. Set up routing, state management, and data fetching patterns for the chosen framework
6. Generate component stubs based on the Designer's component hierarchy
7. Maintain a template registry for cross-project reuse

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `scaffold_generator` | Generate project file structure and boilerplate | Yeoman-style template engine |
| `template_registry` | Browse and select from template library | Internal registry database |
| `component_stub_generator` | Create component files from hierarchy | AST-based code generator |
| `build_configurator` | Configure Vite, Webpack, or other build tools | Config template engine |
| `file_writer` | Write generated files to repository | Git worktree filesystem |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Design specification | Designer | Markdown with design system |
| Component hierarchy | Designer | JSON tree structure |
| Tech stack | TechStack Builder | JSON specification |
| Architecture document | Architect | Markdown with component diagram |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Project scaffold | Frontend Dev, Backend Dev | Generated file tree |
| Component stubs | Frontend Developer | TypeScript/JSX files |
| Build configuration | Infrastructure Engineer | Vite/Webpack config files |
| Template selection report | Documentation Writer | Markdown document |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Template selection | Claude Sonnet 4 | GPT-4.1 | Good judgment on template fitness |
| Scaffold generation | Claude Haiku 3.5 | GPT-4.1-mini | Fast, template-based code generation |
| Build configuration | Claude Sonnet 4 | GPT-4.1 | Precise configuration output |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Project summary, tech stack, scaffolding instructions | ~2,000 tokens |
| L1 | Design specification, component hierarchy, architecture doc | ~8,000 tokens |
| L2 | Template library catalog, framework documentation | ~12,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> SELECTING --> SCAFFOLDING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If selected template is incompatible with tech stack, fall back to minimal boilerplate; if scaffold generation produces invalid files, validate and regenerate
- **Fallback behaviors**: Use a bare-bones project structure if template library is unavailable
- **Escalation paths**: Flag template licensing issues to TechStack Builder for review

#### Interaction Patterns
- **Primary collaborators**: Designer (receives design spec), Frontend Developer (provides scaffold), TechStack Builder (validates compatibility)
- **Communication protocol**: State flow for scaffold propagation; message flow for template compatibility queries
- **Conflict resolution**: Template Agent defers to Designer on visual choices and to TechStack Builder on framework compatibility

#### Configuration
```yaml
template:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 4096
  temperature: 0.2
  tools:
    - scaffold_generator
    - template_registry
    - component_stub_generator
    - build_configurator
    - file_writer
  context_tiers:
    l0: 2000
    l1: 8000
    l2: 12000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 2
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 240
  settings:
    default_template_library: shadcn
    generate_stubs: true
```

---

### 9. Database Agent

#### Overview
- **Role**: Database design specialist handling schemas, migrations, and data modeling
- **Category**: Design
- **Graph Position**: After Architect; parallel with Designer; feeds into Backend Developer
- **Upstream Dependencies**: Architect (logical schema), TechStack Builder (database selection)
- **Downstream Consumers**: Backend Developer, Middleware Developer, Infrastructure Engineer

#### Responsibilities
1. Transform logical schema from Architect into physical database schemas with data types, constraints, and indexes
2. Create Entity-Relationship Diagrams (ERDs) for documentation
3. Generate migration scripts using the project's ORM migration tool (Alembic, Prisma Migrate, TypeORM)
4. Design seed data for development and testing environments
5. Implement normalization rules (3NF minimum) while allowing strategic denormalization for performance
6. Design indexing strategy based on expected query patterns
7. Create query optimization patterns and prepared statement templates
8. Support both SQL (PostgreSQL, MySQL, SQLite) and NoSQL (MongoDB, DynamoDB, Redis) databases

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `schema_generator` | Generate DDL statements from logical schema | SQL/NoSQL code generator |
| `erd_generator` | Create ER diagrams in Mermaid format | Mermaid renderer |
| `migration_generator` | Generate ORM migration files | Alembic / Prisma CLI |
| `seed_generator` | Generate realistic seed data | Faker integration |
| `index_advisor` | Recommend indexes based on query patterns | Query analysis engine |
| `query_optimizer` | Generate optimized query templates | SQL EXPLAIN analyzer |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Logical schema | Architect | JSON schema definition |
| Database selection | TechStack Builder | JSON (type, version, provider) |
| Query patterns | Planner | JSON list of expected queries |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Physical schema (DDL) | Backend Developer | SQL files or ORM models |
| Migration scripts | Backend Dev, Infrastructure Engineer | Python/TypeScript migration files |
| ERD diagram | Documentation Writer | Mermaid diagram code |
| Seed data | Tester, Backend Developer | SQL/JSON seed files |
| Index recommendations | Backend Developer | JSON index specification |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Schema design | Claude Opus 4 | GPT-4.1 | Deep reasoning for normalization and constraint design |
| Migration generation | Claude Sonnet 4 | GPT-4.1 | Precise code generation |
| Seed data creation | Claude Haiku 3.5 | GPT-4.1-mini | Cost-effective data generation |
| Query optimization | Claude Opus 4 | o3 | Complex query plan analysis |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Project summary, database type, agent instructions | ~2,000 tokens |
| L1 | Logical schema, query patterns, architecture doc | ~10,000 tokens |
| L2 | Database best practices, indexing guides, ORM documentation | ~15,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> DESIGNING --> GENERATING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If schema violates normalization rules, apply automatic normalization; if migration script conflicts with existing schema, generate incremental migration instead
- **Fallback behaviors**: Use SQLite-compatible schema as baseline if target database features are unavailable
- **Escalation paths**: Escalate data modeling decisions with privacy implications (PII storage) to human review

#### Interaction Patterns
- **Primary collaborators**: Architect (receives logical schema), Backend Developer (provides physical schema and migrations), Infrastructure Engineer (provides database deployment config)
- **Communication protocol**: State flow for schema propagation; message flow for query pattern clarifications
- **Conflict resolution**: Database Agent has authority on schema design; Backend Developer can request schema modifications through the Architect

#### Configuration
```yaml
database:
  model: claude-opus-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 4096
  temperature: 0.1
  tools:
    - schema_generator
    - erd_generator
    - migration_generator
    - seed_generator
    - index_advisor
    - query_optimizer
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 15000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 3
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 300
  settings:
    default_db: postgresql
    normalization_level: 3NF
    generate_seed_data: true
    orm: sqlalchemy
```

---

### 10. API Gateway Agent

#### Overview
- **Role**: API design specialist handling gateway configuration, schema design, and middleware patterns
- **Category**: Design
- **Graph Position**: After Architect; parallel with Database Agent; feeds into Backend Developer and Middleware Developer
- **Upstream Dependencies**: Architect (API contracts, OpenAPI spec), TechStack Builder (API framework selection)
- **Downstream Consumers**: Backend Developer, Middleware Developer, Frontend Developer, Integrations Agent

#### Responsibilities
1. Create detailed OpenAPI 3.1 specifications with complete schemas, examples, and error responses
2. Design GraphQL schemas when GraphQL is selected as the API layer
3. Configure API gateway patterns: rate limiting, throttling, circuit breakers
4. Design API versioning strategy (URL path, header, or query parameter based)
5. Implement authentication middleware patterns (OAuth2, JWT, API keys)
6. Design request/response validation middleware
7. Create API documentation with interactive examples (Swagger UI, Redoc)
8. Define CORS policies and security headers

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `openapi_designer` | Create and validate OpenAPI 3.1 specs | OpenAPI validator |
| `graphql_designer` | Create GraphQL type definitions and resolvers | GraphQL schema tools |
| `middleware_configurator` | Generate middleware chain configuration | Express/FastAPI middleware |
| `auth_pattern_generator` | Generate authentication flow implementations | OAuth2/JWT templates |
| `rate_limiter_configurator` | Configure rate limiting and throttling | Redis-based rate limiter |
| `api_doc_generator` | Generate interactive API documentation | Swagger UI / Redoc |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| API contracts | Architect | OpenAPI YAML (draft) |
| Database schema | Database Agent | JSON schema |
| Authentication requirements | PRD / Architect | JSON constraints |
| External API specs | Researcher | OpenAPI/GraphQL specs |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Complete OpenAPI spec | Backend Dev, Frontend Dev, Tester | YAML (OpenAPI 3.1) |
| GraphQL schema | Backend Dev, Frontend Dev | `.graphql` schema files |
| Middleware configuration | Middleware Developer | YAML/JSON config |
| Authentication patterns | Backend Dev, Middleware Dev | Code templates |
| API documentation | Documentation Writer, User | HTML (Swagger UI) |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| OpenAPI specification | Claude Sonnet 4 | GPT-4.1 | Precise schema definition |
| GraphQL schema design | Claude Sonnet 4 | Gemini 2.5 Pro | Type system reasoning |
| Middleware configuration | Claude Haiku 3.5 | GPT-4.1-mini | Configuration generation |
| Auth pattern design | Claude Opus 4 | GPT-4.1 | Security-critical reasoning |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Project summary, API style, agent instructions | ~2,000 tokens |
| L1 | Architecture doc, database schema, auth requirements | ~10,000 tokens |
| L2 | API best practices, OAuth2 specs, external API docs | ~15,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> DESIGNING --> VALIDATING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If OpenAPI spec fails validation, auto-fix common schema errors and re-validate; if GraphQL schema has circular type references, refactor with interface types
- **Fallback behaviors**: Generate a minimal REST API spec if GraphQL design fails; use basic JWT auth if OAuth2 configuration is too complex for the project scope
- **Escalation paths**: Escalate API security decisions (auth flow selection, CORS policies) to Security Auditor for review

#### Interaction Patterns
- **Primary collaborators**: Architect (receives API contracts), Backend Developer (provides complete specs), Middleware Developer (provides middleware config), Frontend Developer (provides client SDK types)
- **Communication protocol**: State flow for spec propagation; message flow for schema clarifications
- **Conflict resolution**: API Gateway Agent has authority on API design; Architect can override for architectural consistency

#### Configuration
```yaml
api_gateway:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 4096
  temperature: 0.1
  tools:
    - openapi_designer
    - graphql_designer
    - middleware_configurator
    - auth_pattern_generator
    - rate_limiter_configurator
    - api_doc_generator
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 15000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 3
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 300
  settings:
    api_style: rest
    spec_version: "3.1"
    auth_strategy: jwt
    enable_rate_limiting: true
```

---

## Implementation Agents

---

### 11. Frontend Developer Agent

#### Overview
- **Role**: UI implementation across modern frontend frameworks
- **Category**: Implementation
- **Graph Position**: Implementation phase (parallel with Backend, Middleware, Infrastructure)
- **Upstream Dependencies**: Designer (design spec), Template Agent (scaffold), Architect (component diagram), API Gateway (API spec)
- **Downstream Consumers**: Code Reviewer, Security Auditor, Tester, Accessibility Agent

#### Responsibilities
1. Implement React, Vue, Angular, Svelte, Next.js, or Nuxt components based on design specifications
2. Set up state management (Zustand, Redux, Pinia, Vuex) per architecture decisions
3. Implement client-side routing with the chosen framework's router
4. Build responsive layouts using CSS framework (Tailwind, CSS Modules, Styled Components)
5. Integrate with backend APIs using generated client SDKs or fetch wrappers
6. Implement form handling, validation, and error display
7. Set up real-time features (WebSocket connections, SSE) when required
8. Optimize bundle size through code splitting, tree shaking, and lazy loading

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `file_read` | Read existing code files | Git worktree filesystem |
| `file_write` | Write/modify source files | Git worktree filesystem |
| `file_edit` | Make targeted edits to existing files | AST-aware editor |
| `bash` | Run build tools, linters, dev server | Subprocess execution |
| `grep` | Search codebase for patterns | ripgrep integration |
| `glob` | Find files by pattern | Glob matcher |
| `browser_preview` | Preview UI in headless browser | Playwright |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Design specification | Designer | Markdown with component specs |
| Component hierarchy | Designer | JSON tree |
| Project scaffold | Template Agent | File tree with stubs |
| API specification | API Gateway Agent | OpenAPI YAML |
| Design tokens | Designer | JSON/CSS custom properties |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Frontend source code | Code Reviewer, Tester | TypeScript/JSX files |
| Component tests | Tester | Test files (Vitest) |
| Build artifacts | Infrastructure Engineer | Bundle output |
| Style files | Accessibility Agent | CSS/Tailwind files |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Component implementation | Claude Sonnet 4 (via Claude Code) | GPT-4.1 (via Codex) | Best code generation with tool use |
| State management setup | Claude Sonnet 4 | GPT-4.1 | Framework-specific patterns |
| CSS/Tailwind implementation | Claude Haiku 3.5 | GPT-4.1-mini | Fast styling tasks |
| Complex UI logic | Claude Opus 4 | o3 | Complex state machine and animation logic |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Current task, component spec, framework conventions | ~2,000 tokens |
| L1 | Related component files, API spec, design tokens, routing config | ~10,000 tokens |
| L2 | Full codebase search, framework documentation, examples | ~20,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> CODING --> BUILDING --> SELF_TESTING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If build fails, parse error messages and fix; if TypeScript type errors, adjust types and rebuild; if component renders incorrectly, compare against wireframe and adjust
- **Fallback behaviors**: Fall back to simpler CSS if complex animations fail; use inline styles if CSS framework integration fails
- **Escalation paths**: Escalate to Designer if wireframe is ambiguous; escalate to Architect if component API is unclear

#### Interaction Patterns
- **Primary collaborators**: Designer (receives specs), Template Agent (receives scaffold), Backend Developer (coordinates API integration), Accessibility Agent (receives accessibility feedback)
- **Communication protocol**: State flow for code artifacts; message flow for API integration questions
- **Conflict resolution**: Frontend Developer follows Designer's specs; defers to Architect on structural decisions

#### Configuration
```yaml
frontend_dev:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  cli_agent: claude-code
  max_tokens: 8192
  temperature: 0.1
  tools:
    - file_read
    - file_write
    - file_edit
    - bash
    - grep
    - glob
    - browser_preview
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 20000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 2
    max_delay_seconds: 60
    exponential_base: 2
  timeout: 600
  worktree: true
  settings:
    framework: react
    css_framework: tailwindcss
    test_framework: vitest
    enable_self_test: true
```

---

### 12. Backend Developer Agent

#### Overview
- **Role**: Server-side API implementation and business logic
- **Category**: Implementation
- **Graph Position**: Implementation phase (parallel with Frontend, Middleware, Infrastructure)
- **Upstream Dependencies**: Architect (architecture doc), API Gateway (OpenAPI spec), Database Agent (schema, migrations)
- **Downstream Consumers**: Code Reviewer, Security Auditor, Tester

#### Responsibilities
1. Implement REST or GraphQL API endpoints based on OpenAPI or GraphQL specifications
2. Build business logic layers with proper separation of concerns (controller, service, repository)
3. Implement data access layer using the selected ORM (SQLAlchemy, Prisma, TypeORM)
4. Set up authentication and authorization middleware (JWT validation, RBAC)
5. Implement input validation, error handling, and response serialization
6. Create database migration execution and seed data loading
7. Build WebSocket handlers for real-time features when required
8. Implement background task processing (Celery, Bull, or async task queues)

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `file_read` | Read existing code files | Git worktree filesystem |
| `file_write` | Write/modify source files | Git worktree filesystem |
| `file_edit` | Make targeted edits to existing files | AST-aware editor |
| `bash` | Run server, tests, migrations, linting | Subprocess execution |
| `grep` | Search codebase for patterns | ripgrep integration |
| `glob` | Find files by pattern | Glob matcher |
| `db_query` | Execute test queries against development database | Database connector |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| OpenAPI specification | API Gateway Agent | YAML (OpenAPI 3.1) |
| Database schema | Database Agent | DDL/ORM model files |
| Migration scripts | Database Agent | Python/TypeScript files |
| Architecture document | Architect | Markdown |
| Auth patterns | API Gateway Agent | Code templates |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Backend source code | Code Reviewer, Tester | Python/TypeScript files |
| API endpoint implementations | Tester (API tests) | Route handler files |
| Unit tests | Tester | pytest/Vitest test files |
| Database seed execution | Tester | Populated test database |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| API endpoint implementation | GPT-4.1 (via Codex) | Claude Sonnet 4 (via Claude Code) | Strong code generation with API patterns |
| Business logic | Claude Sonnet 4 | GPT-4.1 | Complex logic implementation |
| Database queries | Claude Opus 4 | GPT-4.1 | Complex query optimization |
| Auth implementation | Claude Opus 4 | o3 | Security-critical code |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Current task, API endpoint spec, framework conventions | ~2,000 tokens |
| L1 | OpenAPI spec, database schema, related source files | ~12,000 tokens |
| L2 | Full codebase, framework docs, security best practices | ~20,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> CODING --> MIGRATING --> SELF_TESTING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If API endpoint fails validation against OpenAPI spec, regenerate; if database migration fails, roll back and regenerate; if tests fail, parse errors and fix
- **Fallback behaviors**: Use in-memory storage if database connection fails during development; generate stub implementations for complex integrations
- **Escalation paths**: Escalate database schema issues to Database Agent; escalate API contract conflicts to API Gateway Agent

#### Interaction Patterns
- **Primary collaborators**: API Gateway Agent (receives API spec), Database Agent (receives schema), Frontend Developer (coordinates on API contracts), Middleware Developer (coordinates on integration layer)
- **Communication protocol**: State flow for code artifacts; message flow for API contract clarifications
- **Conflict resolution**: Backend Developer follows API Gateway spec; defers to Architect on architectural decisions

#### Configuration
```yaml
backend_dev:
  model: gpt-4.1
  fallback_model: claude-sonnet-4
  provider: openai
  cli_agent: codex
  max_tokens: 8192
  temperature: 0.1
  tools:
    - file_read
    - file_write
    - file_edit
    - bash
    - grep
    - glob
    - db_query
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
  worktree: true
  settings:
    framework: fastapi
    orm: sqlalchemy
    test_framework: pytest
    enable_self_test: true
```

---

### 13. Middleware Developer Agent

#### Overview
- **Role**: Integration layer implementation including message queues, caching, and service mesh
- **Category**: Implementation
- **Graph Position**: Implementation phase (parallel with Frontend, Backend, Infrastructure)
- **Upstream Dependencies**: Architect (architecture doc), API Gateway (middleware config)
- **Downstream Consumers**: Code Reviewer, Security Auditor, Tester

#### Responsibilities
1. Implement message queue integrations (RabbitMQ, Kafka, Redis Streams)
2. Set up caching layers (Redis, Memcached) with invalidation strategies
3. Implement authentication middleware (OAuth2 flows, JWT validation, session management)
4. Configure API gateway middleware (rate limiting, request transformation, circuit breakers)
5. Build service mesh configurations for microservices (Envoy, Linkerd sidecar configs)
6. Implement event bus patterns for inter-service communication
7. Set up health check endpoints and readiness/liveness probes
8. Configure logging middleware with structured log output

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `file_read` | Read existing code files | Git worktree filesystem |
| `file_write` | Write/modify source files | Git worktree filesystem |
| `file_edit` | Make targeted edits to existing files | AST-aware editor |
| `bash` | Run middleware services, tests | Subprocess execution |
| `grep` | Search codebase for patterns | ripgrep integration |
| `docker_compose` | Start and manage middleware services | Docker Compose CLI |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Architecture document | Architect | Markdown with integration patterns |
| Middleware configuration | API Gateway Agent | YAML/JSON config |
| Service topology | Architect | Component diagram |
| Auth requirements | API Gateway Agent | Auth flow specification |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Middleware source code | Code Reviewer, Tester | Python/TypeScript files |
| Docker Compose services | Infrastructure Engineer | docker-compose.yml additions |
| Integration tests | Tester | Test files |
| Health check endpoints | DevOps Agent | API endpoint implementations |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Queue integration | Claude Sonnet 4 (via Claude Code) | GPT-4.1 | Complex async patterns |
| Cache implementation | Claude Haiku 3.5 | GPT-4.1-mini | Well-established patterns |
| Auth middleware | Claude Opus 4 | GPT-4.1 | Security-critical implementation |
| Service mesh config | Claude Sonnet 4 | Gemini 2.5 Pro | Infrastructure configuration |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Current task, middleware type, agent instructions | ~2,000 tokens |
| L1 | Architecture doc, service topology, related config files | ~8,000 tokens |
| L2 | Middleware documentation, integration patterns, examples | ~15,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> CODING --> INTEGRATING --> SELF_TESTING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If middleware service fails to start, check Docker logs and fix configuration; if integration tests fail, verify service connectivity and retry
- **Fallback behaviors**: Use in-memory implementations (in-memory queue, local cache) if external services are unavailable; skip optional middleware (circuit breakers) if time-constrained
- **Escalation paths**: Escalate service connectivity issues to Infrastructure Engineer; escalate auth flow issues to Security Auditor

#### Interaction Patterns
- **Primary collaborators**: Backend Developer (coordinates on service integration), Infrastructure Engineer (coordinates on service deployment), API Gateway Agent (receives middleware config)
- **Communication protocol**: State flow for code artifacts; message flow for service configuration coordination
- **Conflict resolution**: Middleware Developer follows Architect's integration patterns; coordinates with Backend Developer on API contracts

#### Configuration
```yaml
middleware_dev:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  cli_agent: claude-code
  max_tokens: 4096
  temperature: 0.1
  tools:
    - file_read
    - file_write
    - file_edit
    - bash
    - grep
    - docker_compose
  context_tiers:
    l0: 2000
    l1: 8000
    l2: 15000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 2
    max_delay_seconds: 60
    exponential_base: 2
  timeout: 600
  worktree: true
  settings:
    queue_type: redis_streams
    cache_type: redis
    auth_type: jwt
```

---

### 14. Mobile Developer Agent

#### Overview
- **Role**: Mobile application development across iOS, Android, and cross-platform frameworks
- **Category**: Implementation
- **Graph Position**: Implementation phase (parallel with other developers); optional based on project requirements
- **Upstream Dependencies**: Designer (mobile design spec), Architect (mobile architecture), API Gateway (API spec)
- **Downstream Consumers**: Code Reviewer, Security Auditor, Tester, Accessibility Agent

#### Responsibilities
1. Implement iOS applications using Swift/SwiftUI with UIKit fallback
2. Implement Android applications using Kotlin/Jetpack Compose
3. Build cross-platform applications using React Native or Flutter
4. Integrate with backend APIs using generated client SDKs
5. Implement native device integrations (camera, GPS, push notifications, biometrics)
6. Set up offline-first data synchronization patterns
7. Configure push notification handling (APNs, FCM)
8. Implement app navigation patterns (tab bar, drawer, stack navigation)

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `file_read` | Read existing code files | Git worktree filesystem |
| `file_write` | Write/modify source files | Git worktree filesystem |
| `file_edit` | Make targeted edits to existing files | AST-aware editor |
| `bash` | Run build tools, simulators, linting | Subprocess execution |
| `grep` | Search codebase for patterns | ripgrep integration |
| `simulator_preview` | Preview app in iOS/Android simulator | Xcode/Android Studio CLI |
| `cocoapods` / `gradle` | Manage native dependencies | Package manager CLI |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Mobile design specification | Designer | Markdown with mobile-specific layouts |
| API specification | API Gateway Agent | OpenAPI YAML |
| Architecture document | Architect | Markdown with mobile architecture |
| Push notification config | Infrastructure Engineer | JSON configuration |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Mobile source code | Code Reviewer, Tester | Swift/Kotlin/Dart/TypeScript files |
| Unit tests | Tester | XCTest/JUnit/Widget tests |
| Build configuration | DevOps Agent | Xcode project / Gradle build files |
| App assets | Accessibility Agent | Image assets, localization files |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| iOS/SwiftUI implementation | Claude Sonnet 4 (via Claude Code) | GPT-4.1 | Strong Swift/SwiftUI knowledge |
| Android/Kotlin implementation | GPT-4.1 (via Codex) | Claude Sonnet 4 | Strong Kotlin/Compose knowledge |
| React Native implementation | Claude Sonnet 4 | GPT-4.1 | Good TypeScript + React knowledge |
| Flutter implementation | Gemini 2.5 Pro | Claude Sonnet 4 | Strong Dart/Flutter knowledge |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Current task, platform target, framework conventions | ~2,000 tokens |
| L1 | Mobile design spec, API spec, navigation structure | ~10,000 tokens |
| L2 | Platform documentation, native API references, examples | ~20,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> CODING --> BUILDING --> SIMULATOR_TEST --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If build fails, parse Xcode/Gradle errors and fix; if simulator launch fails, retry with clean build; if native API integration fails, implement mock fallback
- **Fallback behaviors**: Use web-based fallback (PWA) if native build toolchain is unavailable; use platform-agnostic libraries when platform-specific APIs are problematic
- **Escalation paths**: Escalate platform-specific signing/provisioning issues to human; escalate App Store / Play Store compliance questions to human

#### Interaction Patterns
- **Primary collaborators**: Designer (receives mobile design), Backend Developer (coordinates on API), Infrastructure Engineer (coordinates on CI/CD for mobile builds)
- **Communication protocol**: State flow for code artifacts; message flow for API integration questions
- **Conflict resolution**: Mobile Developer follows Designer's mobile specs; defers to Architect on cross-platform strategy decisions

#### Configuration
```yaml
mobile_dev:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  cli_agent: claude-code
  max_tokens: 8192
  temperature: 0.1
  tools:
    - file_read
    - file_write
    - file_edit
    - bash
    - grep
    - simulator_preview
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 20000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 3
    max_delay_seconds: 60
    exponential_base: 2
  timeout: 600
  worktree: true
  settings:
    platforms:
      - ios
      - android
    framework: react_native
    enable_offline_sync: false
```

---

### 15. Infrastructure Engineer Agent

#### Overview
- **Role**: Infrastructure as Code, containerization, CI/CD pipelines, and deployment configuration
- **Category**: Implementation
- **Graph Position**: Implementation phase (parallel with other developers)
- **Upstream Dependencies**: Architect (deployment topology), TechStack Builder (hosting selection), Middleware Developer (service configs)
- **Downstream Consumers**: DevOps Agent, Code Reviewer, Security Auditor

#### Responsibilities
1. Write Terraform/Pulumi/CloudFormation modules for cloud infrastructure provisioning
2. Create Docker multi-stage build files optimized for production
3. Generate Kubernetes manifests (Deployments, Services, Ingress, ConfigMaps, Secrets)
4. Set up CI/CD pipeline definitions (GitHub Actions, GitLab CI, Jenkins)
5. Configure environment management (dev, staging, production) with proper secret handling
6. Set up monitoring infrastructure (Prometheus, Grafana dashboards, alerting rules)
7. Configure log aggregation (ELK stack, Loki, CloudWatch)
8. Implement backup and disaster recovery configurations

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `file_read` | Read existing config files | Git worktree filesystem |
| `file_write` | Write IaC and config files | Git worktree filesystem |
| `file_edit` | Modify existing configurations | AST-aware editor |
| `bash` | Run terraform plan, docker build, kubectl | Subprocess execution |
| `terraform_validate` | Validate Terraform configurations | Terraform CLI |
| `docker_build` | Build and test Docker images | Docker CLI |
| `kubectl` | Validate Kubernetes manifests | kubectl CLI |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Deployment topology | Architect | Markdown with infrastructure diagram |
| Hosting selection | TechStack Builder | JSON (cloud provider, services) |
| Service configurations | Middleware Developer | Docker Compose additions |
| Application requirements | Planner | JSON (scaling, availability) |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Terraform modules | DevOps Agent, Security Auditor | HCL files |
| Dockerfiles | DevOps Agent | Multi-stage Dockerfiles |
| Kubernetes manifests | DevOps Agent | YAML manifests |
| CI/CD pipeline definitions | GitHub Agent, DevOps Agent | YAML workflow files |
| Monitoring configuration | DevOps Agent | Prometheus/Grafana configs |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Terraform modules | GPT-4.1 (via Codex) | Claude Sonnet 4 | Strong IaC code generation |
| Docker optimization | Claude Sonnet 4 | GPT-4.1 | Multi-stage build optimization |
| Kubernetes manifests | GPT-4.1 | Claude Sonnet 4 | Strong K8s pattern knowledge |
| CI/CD pipelines | Claude Sonnet 4 | GPT-4.1 | Complex workflow logic |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Current task, cloud provider, agent instructions | ~2,000 tokens |
| L1 | Deployment topology, service configs, application requirements | ~8,000 tokens |
| L2 | Cloud provider documentation, IaC best practices, security baselines | ~15,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> CODING --> VALIDATING --> PLANNING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If Terraform validation fails, parse errors and fix HCL syntax; if Docker build fails, adjust base images or build steps; if K8s manifest is invalid, validate against schema and fix
- **Fallback behaviors**: Use simpler deployment targets (Docker Compose instead of K8s) if infrastructure complexity exceeds project scope; use managed services instead of self-hosted alternatives
- **Escalation paths**: Escalate cloud cost concerns to Orchestrator; escalate security group / IAM policy decisions to Security Auditor

#### Interaction Patterns
- **Primary collaborators**: Architect (receives deployment topology), DevOps Agent (hands off deployment configs), Middleware Developer (coordinates on service infrastructure), Security Auditor (validates IaC security)
- **Communication protocol**: State flow for IaC artifacts; message flow for cloud provider specific questions
- **Conflict resolution**: Infrastructure Engineer has authority on infrastructure decisions; Architect can override for architectural consistency; Security Auditor can veto insecure configurations

#### Configuration
```yaml
infra_engineer:
  model: gpt-4.1
  fallback_model: claude-sonnet-4
  provider: openai
  cli_agent: codex
  max_tokens: 4096
  temperature: 0.1
  tools:
    - file_read
    - file_write
    - file_edit
    - bash
    - terraform_validate
    - docker_build
    - kubectl
  context_tiers:
    l0: 2000
    l1: 8000
    l2: 15000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 3
    max_delay_seconds: 60
    exponential_base: 2
  timeout: 600
  worktree: true
  settings:
    cloud_provider: aws
    iac_tool: terraform
    container_runtime: docker
    orchestrator: kubernetes
```

---

## Quality Agents

---

### 16. Security Auditor Agent

#### Overview
- **Role**: Comprehensive security analysis across SAST, DAST, SCA, secrets, licensing, and IaC. **Optional ExperimentLoop-based autonomous hardening**
- **Category**: Quality
- **Graph Position**: Review phase (parallel with Code Reviewer); after Implementation. Optionally participates in ExperimentLoop (Improve mode or post-pipeline hardening)
- **Upstream Dependencies**: All Implementation agents (source code), Infrastructure Engineer (IaC configs)
- **Downstream Consumers**: Debugger, Orchestrator (quality gate), Documentation Writer

#### Responsibilities
1. Run Static Application Security Testing (SAST) via Semgrep and CodeQL
2. Execute Dynamic Application Security Testing (DAST) via Shannon for deployed endpoints
3. Perform Software Composition Analysis (SCA) via Trivy and OpenSCA for dependency vulnerabilities
4. Detect hardcoded secrets and credentials via Gitleaks
5. Audit license compliance via ScanCode and ORT against allowed license policy
6. Scan Infrastructure as Code (IaC) for security misconfigurations via KICS
7. Generate a comprehensive security report with findings, severity scores, and remediation guidance
8. Enforce security quality gates (zero critical/high findings required to pass)
9. **ExperimentLoop mode** (optional, Improve mode): Autonomously generate and apply security fixes as discrete experiments — each fix is re-scanned and kept only if it reduces findings count without breaking tests

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `semgrep` | SAST scanning with custom and community rules | Semgrep CLI |
| `codeql` | GitHub-native SAST with security queries | CodeQL CLI |
| `trivy` | Container and dependency vulnerability scanning | Trivy CLI |
| `gitleaks` | Secret and credential detection | Gitleaks CLI |
| `scancode` | License detection and compliance | ScanCode Toolkit |
| `kics` | IaC security scanning (Terraform, Docker, K8s) | KICS CLI |
| `shannon` | Dynamic application security testing | Shannon CLI |
| `security_report_generator` | Aggregate findings into unified report | Internal tool |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Source code (all languages) | All Implementation agents | Code files in git repository |
| IaC configurations | Infrastructure Engineer | Terraform, Docker, K8s files |
| Dependency manifests | TechStack Builder | package.json, requirements.txt, etc. |
| Container images | Infrastructure Engineer | Docker images |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Security report | Orchestrator, Debugger, Dashboard | JSON + Markdown |
| SARIF results | GitHub Agent (for PR annotations) | SARIF format |
| Finding list | Debugger (for remediation) | JSON array of findings |
| Quality gate result | Orchestrator | Boolean pass/fail + details |
| License compliance report | Documentation Writer | Markdown report |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Finding triage and prioritization | Claude Opus 4 | o3 | Nuanced security reasoning |
| Remediation guidance | Claude Sonnet 4 | GPT-4.1 | Specific fix recommendations |
| Report generation | Claude Haiku 3.5 | Gemini 2.5 Flash | Cost-effective report writing |
| False positive analysis | Claude Opus 4 | o3 | Requires deep code understanding |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Scan configuration, security policies, agent instructions | ~2,000 tokens |
| L1 | Scan results, affected source files, dependency tree | ~12,000 tokens |
| L2 | Vulnerability databases (CVE details), remediation guides, CWE descriptions | ~20,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> SCANNING --> TRIAGING --> REPORTING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If scanner crashes, retry with reduced scope; if scanner produces too many false positives, adjust rule sensitivity; if scanner is unavailable, skip and document gap
- **Fallback behaviors**: Run at least Semgrep + Gitleaks if other scanners fail; accept partial scan results with documented gaps
- **Escalation paths**: Immediately escalate critical severity findings to Orchestrator; flag license violations for human legal review

#### Interaction Patterns
- **Primary collaborators**: All Implementation agents (scans their code), Debugger (provides findings for remediation), Orchestrator (reports quality gate status), Infrastructure Engineer (scans IaC)
- **Communication protocol**: State flow for scan results; message flow for urgent critical findings
- **Conflict resolution**: Security Auditor has veto authority on security quality gates; Orchestrator can override with explicit human approval for accepted risks

#### Configuration
```yaml
security_auditor:
  model: claude-opus-4
  fallback_model: o3
  provider: anthropic
  max_tokens: 8192
  temperature: 0.1
  tools:
    - semgrep
    - codeql
    - trivy
    - gitleaks
    - scancode
    - kics
    - shannon
    - security_report_generator
  context_tiers:
    l0: 2000
    l1: 12000
    l2: 20000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 5
    max_delay_seconds: 60
    exponential_base: 2
  timeout: 600
  settings:
    quality_gate:
      max_critical: 0
      max_high: 0
      max_medium: 5
    scanners:
      - semgrep
      - trivy
      - gitleaks
      - scancode
    license_policy: permissive_only
```

---

### 17. Code Reviewer Agent

#### Overview
- **Role**: Automated code quality review, style enforcement, and architecture conformance checking
- **Category**: Quality
- **Graph Position**: Review phase (parallel with Security Auditor); after Implementation
- **Upstream Dependencies**: All Implementation agents (source code), Architect (architecture doc)
- **Downstream Consumers**: Debugger, Orchestrator (quality gate), Documentation Writer

#### Responsibilities
1. Enforce coding style guides and formatting rules (ESLint, Ruff, Prettier)
2. Check adherence to design patterns specified in the architecture document
3. Verify architecture conformance (components respect defined boundaries)
4. Identify performance anti-patterns (N+1 queries, unbounded loops, memory leaks)
5. Check for maintainability issues (excessive complexity, long methods, deep nesting)
6. Verify error handling completeness (all error paths handled, proper logging)
7. Assess code documentation quality (docstrings, comments, type annotations)
8. Generate inline review comments with specific suggestions for improvement

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `eslint` | JavaScript/TypeScript linting | ESLint CLI |
| `ruff` | Python linting and formatting | Ruff CLI |
| `prettier` | Code formatting verification | Prettier CLI |
| `complexity_analyzer` | Cyclomatic complexity measurement | radon / eslint-plugin-complexity |
| `ast_parser` | Parse code AST for pattern detection | tree-sitter |
| `architecture_validator` | Check component boundary violations | Custom dependency analyzer |
| `review_comment_writer` | Generate inline review comments | Internal tool |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Source code (all languages) | All Implementation agents | Code files in git repository |
| Architecture document | Architect | Markdown with component boundaries |
| Style guide configuration | TechStack Builder | ESLint/Ruff/Prettier config files |
| Git diff | Git worktree | Unified diff format |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Review comments | Debugger, GitHub Agent | JSON array of inline comments |
| Quality report | Orchestrator, Dashboard | Markdown summary |
| Lint results | Debugger | JSON lint output |
| Complexity metrics | Documentation Writer | JSON metrics |
| Quality gate result | Orchestrator | Boolean pass/fail |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Code review analysis | Claude Opus 4 | GPT-4.1 | Deep code understanding |
| Architecture conformance | Claude Opus 4 | o3 | Structural reasoning |
| Review comment generation | Claude Sonnet 4 | GPT-4.1 | Clear, actionable feedback |
| Pattern detection | Claude Sonnet 4 | Gemini 2.5 Pro | Pattern matching across codebase |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Review criteria, style guide summary, agent instructions | ~2,000 tokens |
| L1 | Files under review, architecture doc, git diff | ~15,000 tokens |
| L2 | Full codebase for cross-reference, pattern documentation | ~20,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> LINTING --> ANALYZING --> COMMENTING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If lint tools crash, run LLM-based style review as fallback; if complexity analysis times out on large files, analyze in chunks
- **Fallback behaviors**: Provide LLM-only review if static analysis tools are unavailable; focus on critical issues if review scope is too large
- **Escalation paths**: Escalate architectural violations to Architect for decision; flag significant quality regressions to Orchestrator

#### Interaction Patterns
- **Primary collaborators**: All Implementation agents (reviews their code), Debugger (provides fix targets), Architect (validates architectural compliance), GitHub Agent (posts review comments)
- **Communication protocol**: State flow for review report; message flow for urgent quality issues
- **Conflict resolution**: Code Reviewer provides recommendations; implementation agents decide on adoption; Architect arbitrates on architectural issues

#### Configuration
```yaml
code_reviewer:
  model: claude-opus-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 8192
  temperature: 0.2
  tools:
    - eslint
    - ruff
    - prettier
    - complexity_analyzer
    - ast_parser
    - architecture_validator
    - review_comment_writer
  context_tiers:
    l0: 2000
    l1: 15000
    l2: 20000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 3
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 600
  settings:
    max_complexity: 10
    require_docstrings: true
    enforce_type_hints: true
    review_depth: thorough
```

---

### 18. Accessibility Agent

#### Overview
- **Role**: WCAG 2.1 AA/AAA compliance validation and accessibility improvement
- **Category**: Quality
- **Graph Position**: Review phase; after Frontend Developer and Mobile Developer
- **Upstream Dependencies**: Frontend Developer (UI code), Mobile Developer (mobile UI), Designer (design tokens)
- **Downstream Consumers**: Debugger, Frontend Developer (fixes), Documentation Writer

#### Responsibilities
1. Run automated accessibility testing using axe-core and lighthouse
2. Verify screen reader compatibility by analyzing ARIA attributes and semantic HTML
3. Validate keyboard navigation paths and focus management
4. Check color contrast ratios against WCAG 2.1 AA (4.5:1) and AAA (7:1) standards
5. Verify ARIA attribute correctness and completeness
6. Validate form accessibility (labels, error messages, fieldset/legend)
7. Check image alt text quality and descriptive accuracy
8. Generate an accessibility compliance report with remediation recommendations

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `axe_core` | Automated accessibility rule validation | axe-core CLI / Playwright integration |
| `lighthouse` | Accessibility scoring and auditing | Lighthouse CLI |
| `color_contrast_checker` | WCAG contrast ratio validation | Internal color analysis |
| `html_validator` | Semantic HTML validation | Nu HTML Checker |
| `aria_validator` | ARIA attribute correctness | Custom ARIA rule engine |
| `keyboard_nav_tester` | Keyboard navigation path testing | Playwright automation |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Frontend source code | Frontend Developer | HTML/JSX/TSX files |
| Design tokens | Designer | JSON color palette and typography |
| Rendered pages | Frontend Developer | URL or HTML snapshots |
| Mobile UI code | Mobile Developer | SwiftUI/Compose/RN components |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Accessibility report | Debugger, Frontend Developer | JSON + Markdown |
| WCAG compliance score | Orchestrator, Dashboard | Numeric score (0-100) |
| Remediation suggestions | Frontend Developer, Debugger | JSON array of fixes |
| Contrast ratio report | Designer | JSON with failing color pairs |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| ARIA attribute analysis | Claude Sonnet 4 | GPT-4.1 | Precise HTML/ARIA reasoning |
| Remediation suggestions | Claude Sonnet 4 | GPT-4.1 | Actionable code fix generation |
| Report generation | Claude Haiku 3.5 | Gemini 2.5 Flash | Cost-effective report writing |
| Screen reader compatibility | Claude Opus 4 | GPT-4.1 | Deep understanding of assistive technology |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | WCAG criteria, compliance target (AA/AAA), agent instructions | ~2,000 tokens |
| L1 | Source code under review, axe-core results, design tokens | ~10,000 tokens |
| L2 | WCAG 2.1 specification, remediation patterns, best practices | ~15,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> SCANNING --> ANALYZING --> REPORTING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If axe-core fails on dynamic content, use Playwright to render first then scan; if contrast checker produces false positives on dark mode, analyze per-theme
- **Fallback behaviors**: Use LLM-only accessibility review if automated tools fail; focus on critical WCAG violations (Level A) if full scan times out
- **Escalation paths**: Escalate WCAG Level A failures as blocking issues; flag complex accessibility decisions (custom widget ARIA) for human UX review

#### Interaction Patterns
- **Primary collaborators**: Frontend Developer (scans UI code, provides fixes), Designer (validates color palette accessibility), Debugger (receives accessibility fixes)
- **Communication protocol**: State flow for accessibility report; message flow for urgent WCAG Level A violations
- **Conflict resolution**: Accessibility Agent has authority on WCAG compliance; Designer adjusts color palette if contrast ratios fail

#### Configuration
```yaml
accessibility:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 4096
  temperature: 0.1
  tools:
    - axe_core
    - lighthouse
    - color_contrast_checker
    - html_validator
    - aria_validator
    - keyboard_nav_tester
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 15000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 3
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 300
  settings:
    compliance_level: AA
    check_dark_mode: true
    check_mobile: true
```

---

### 19. Performance Agent

#### Overview
- **Role**: Performance analysis, optimization recommendations, benchmark enforcement, and **optional ExperimentLoop-based autonomous optimization**
- **Category**: Quality
- **Graph Position**: Review phase; after Implementation agents. Optionally participates in ExperimentLoop (Improve mode or post-pipeline optimization)
- **Upstream Dependencies**: All Implementation agents (source code), Infrastructure Engineer (deployment configs)
- **Downstream Consumers**: Debugger, Frontend Developer, Backend Developer, Documentation Writer

#### Responsibilities
1. Profile application performance and identify bottlenecks
2. Analyze Core Web Vitals (LCP, FID, CLS) for frontend applications
3. Perform bundle size analysis and recommend code splitting strategies
4. Identify N+1 query patterns and database query optimization opportunities
5. Run load testing to validate scalability requirements
6. Analyze memory usage patterns and detect potential memory leaks
7. Review API response times and recommend caching strategies
8. Generate performance benchmark report with optimization recommendations
9. **ExperimentLoop mode** (optional, Improve mode): Autonomously apply optimizations as discrete experiments — each optimization is measured against baseline Lighthouse/bundle/response-time metrics and kept only if it improves the target metric without regressions

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `lighthouse` | Core Web Vitals and performance scoring | Lighthouse CLI |
| `webpack_analyzer` | Bundle size analysis and visualization | webpack-bundle-analyzer |
| `load_tester` | HTTP load testing | k6 or Artillery |
| `profiler` | CPU and memory profiling | py-spy / Node.js profiler |
| `query_analyzer` | Database query performance analysis | EXPLAIN analyzer |
| `bundle_analyzer` | Frontend bundle composition analysis | Source-map-explorer |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Frontend bundle | Frontend Developer | Build output |
| Backend application | Backend Developer | Running application |
| Database queries | Backend Developer | SQL query log |
| Infrastructure config | Infrastructure Engineer | Resource allocation specs |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Performance report | Orchestrator, Dashboard | Markdown with metrics |
| Optimization recommendations | Debugger, Implementation agents | JSON prioritized list |
| Bundle analysis | Frontend Developer | HTML visualization |
| Load test results | DevOps Agent | JSON metrics |
| Core Web Vitals scores | Documentation Writer | JSON scores |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Performance analysis | Claude Opus 4 | o3 | Deep reasoning on bottleneck identification |
| Optimization recommendations | Claude Sonnet 4 | GPT-4.1 | Actionable code-level suggestions |
| Report generation | Claude Haiku 3.5 | Gemini 2.5 Flash | Cost-effective report writing |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Performance targets, current metrics, agent instructions | ~2,000 tokens |
| L1 | Profiling results, query logs, bundle analysis | ~10,000 tokens |
| L2 | Performance optimization guides, framework-specific tuning docs | ~15,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> PROFILING --> ANALYZING --> REPORTING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If load testing overloads test environment, reduce concurrency; if profiler crashes, use sampling-based profiling instead
- **Fallback behaviors**: Use LLM-based code review for performance anti-patterns if profiling tools fail; skip load testing if no staging environment is available
- **Escalation paths**: Escalate critical performance regressions (>2x slowdown) to Orchestrator; flag infrastructure scaling needs to Infrastructure Engineer

#### Interaction Patterns
- **Primary collaborators**: Frontend Developer (bundle optimization), Backend Developer (query optimization), Infrastructure Engineer (scaling recommendations), Debugger (receives optimization tasks)
- **Communication protocol**: State flow for performance report; message flow for urgent performance regressions
- **Conflict resolution**: Performance Agent provides recommendations; implementation agents decide on adoption; Architect arbitrates if optimizations conflict with architecture

#### Configuration
```yaml
performance:
  model: claude-opus-4
  fallback_model: o3
  provider: anthropic
  max_tokens: 4096
  temperature: 0.2
  tools:
    - lighthouse
    - webpack_analyzer
    - load_tester
    - profiler
    - query_analyzer
    - bundle_analyzer
  context_tiers:
    l0: 2000
    l1: 10000
    l2: 15000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 5
    max_delay_seconds: 60
    exponential_base: 2
  timeout: 600
  settings:
    core_web_vitals:
      lcp_threshold_ms: 2500
      fid_threshold_ms: 100
      cls_threshold: 0.1
    bundle_size_limit_kb: 500
    api_response_time_ms: 200
```

---

### 20. i18n/L10n Agent

#### Overview
- **Role**: Internationalization preparation and localization management
- **Category**: Quality
- **Graph Position**: Review phase; after Frontend Developer and Mobile Developer
- **Upstream Dependencies**: Frontend Developer (UI code), Mobile Developer (mobile UI), Designer (text content)
- **Downstream Consumers**: Debugger, Frontend Developer (i18n fixes), Documentation Writer

#### Responsibilities
1. Extract hardcoded strings from source code into translation resource files
2. Set up i18n framework configuration (react-intl, i18next, vue-i18n, Flutter intl)
3. Implement RTL (right-to-left) support for Arabic, Hebrew, and other RTL languages
4. Configure locale-specific formatting for dates, numbers, currencies, and units
5. Implement pluralization rules following CLDR standards
6. Validate that all user-facing strings are externalized and translatable
7. Generate translation key maps and export to translation management systems
8. Test rendering with pseudo-localization to detect layout issues

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `string_extractor` | Extract hardcoded strings from source files | AST-based extraction |
| `i18n_configurator` | Set up i18n framework and config files | Framework-specific templates |
| `pseudo_localizer` | Generate pseudo-translations for testing | Internal tool |
| `rtl_validator` | Validate RTL layout correctness | Playwright + CSS analysis |
| `cldr_formatter` | Configure locale-specific formatting | CLDR data library |
| `translation_exporter` | Export translations to TMX/XLIFF/JSON | File format converter |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Frontend source code | Frontend Developer | TSX/JSX files with strings |
| Mobile source code | Mobile Developer | Swift/Kotlin/Dart files |
| Target locales | PRD / Orchestrator | JSON list of locale codes |
| Design specification | Designer | Layout specs for RTL |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Translation resource files | Frontend Dev, Mobile Dev | JSON/YAML/ARB files |
| i18n configuration | Frontend Dev, Mobile Dev | Framework config files |
| String extraction report | Documentation Writer | Markdown with key map |
| Pseudo-localization test results | Debugger | JSON with layout issues |
| RTL compatibility report | Frontend Developer | Markdown with fixes needed |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| String extraction | Claude Sonnet 4 | GPT-4.1 | AST-aware code analysis |
| i18n configuration | Claude Haiku 3.5 | GPT-4.1-mini | Framework config generation |
| RTL analysis | Claude Sonnet 4 | Gemini 2.5 Pro | Layout reasoning |
| Translation key naming | Claude Haiku 3.5 | GPT-4.1-mini | Consistent naming conventions |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Target locales, i18n framework, agent instructions | ~2,000 tokens |
| L1 | Source files with strings, existing translations, locale config | ~8,000 tokens |
| L2 | CLDR data, i18n framework documentation, RTL guides | ~12,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> EXTRACTING --> CONFIGURING --> TESTING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If string extraction misses dynamic strings, use regex fallback; if pseudo-localization reveals layout breaks, generate CSS fixes
- **Fallback behaviors**: Extract strings manually using grep patterns if AST parser fails; skip RTL testing if no RTL locales are targeted
- **Escalation paths**: Escalate untranslatable UI patterns (text in images, hardcoded layouts) to Designer for redesign

#### Interaction Patterns
- **Primary collaborators**: Frontend Developer (provides UI code, receives i18n setup), Mobile Developer (provides mobile UI), Designer (coordinates on RTL layouts)
- **Communication protocol**: State flow for translation files; message flow for layout issues requiring redesign
- **Conflict resolution**: i18n Agent has authority on internationalization standards; Designer adjusts layouts if i18n requirements conflict

#### Configuration
```yaml
i18n_l10n:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 4096
  temperature: 0.1
  tools:
    - string_extractor
    - i18n_configurator
    - pseudo_localizer
    - rtl_validator
    - cldr_formatter
    - translation_exporter
  context_tiers:
    l0: 2000
    l1: 8000
    l2: 12000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 3
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 300
  settings:
    default_locale: en-US
    target_locales: []
    enable_rtl: false
    enable_pseudo_localization: true
    i18n_framework: i18next
```

---

## Testing Agents

---

### 21. Tester Agent

#### Overview
- **Role**: Test generation, execution, and coverage analysis across all test levels
- **Category**: Testing
- **Graph Position**: Testing phase; after Review phase
- **Upstream Dependencies**: All Implementation agents (source code), Code Reviewer (review report), Security Auditor (security report)
- **Downstream Consumers**: Debugger, Orchestrator (quality gate), Documentation Writer

#### Responsibilities
1. Generate unit tests for all modules using the appropriate framework (pytest, Vitest, Jest)
2. Create integration tests for API endpoints and service interactions
3. Build end-to-end tests using Playwright for user workflow validation
4. Generate API contract tests from OpenAPI specifications
5. Create snapshot tests for UI component regression detection
6. Execute all test suites and collect results
7. Analyze code coverage and enforce minimum thresholds (80% line, 70% branch)
8. Generate a comprehensive test report with results, coverage, and recommendations

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `pytest` | Python test execution | pytest CLI |
| `vitest` | JavaScript/TypeScript test execution | Vitest CLI |
| `playwright` | End-to-end browser testing | Playwright CLI |
| `coverage_analyzer` | Code coverage measurement and reporting | Coverage.py / c8 |
| `test_generator` | AI-powered test case generation | LLM-based generation |
| `api_tester` | API contract testing from OpenAPI spec | httpx / supertest |
| `snapshot_tester` | UI snapshot comparison | Vitest snapshots |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Source code | All Implementation agents | Code files |
| OpenAPI specification | API Gateway Agent | YAML spec |
| Review comments | Code Reviewer | JSON comments |
| Security findings | Security Auditor | JSON findings |
| User flow diagrams | Designer | Mermaid flowcharts |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Test files | Git repository | Python/TypeScript test files |
| Test results | Debugger, Orchestrator | JSON test report |
| Coverage report | Orchestrator, Dashboard | HTML + JSON coverage |
| Quality gate result | Orchestrator | Boolean pass/fail |
| Failed test details | Debugger | JSON with stack traces |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Unit test generation | GPT-4.1 | Claude Sonnet 4 | Strong test pattern generation |
| Integration test generation | Claude Sonnet 4 | GPT-4.1 | Complex setup/teardown logic |
| E2E test generation | Claude Sonnet 4 | Gemini 2.5 Pro | User flow reasoning |
| Test result analysis | Claude Haiku 3.5 | GPT-4.1-mini | Fast failure categorization |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Test framework config, coverage targets, agent instructions | ~2,000 tokens |
| L1 | Source code under test, API spec, review comments | ~12,000 tokens |
| L2 | Testing best practices, framework documentation, similar test patterns | ~18,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> GENERATING --> EXECUTING --> ANALYZING --> REPORTING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If test execution environment fails, retry with clean state; if test generation produces invalid tests, validate syntax and regenerate; if coverage threshold not met, generate additional tests for uncovered paths
- **Fallback behaviors**: Run unit tests only if integration test infrastructure is unavailable; use LLM-based test review if coverage tools fail
- **Escalation paths**: Escalate persistent test failures (>3 runs) to Debugger; escalate coverage gaps in critical modules to Orchestrator

#### Interaction Patterns
- **Primary collaborators**: All Implementation agents (tests their code), Debugger (provides test failures for fixing), Code Reviewer (incorporates review feedback into tests), Orchestrator (reports quality gate)
- **Communication protocol**: State flow for test results; message flow for test failure details to Debugger
- **Conflict resolution**: Tester has authority on test quality standards; implementation agents provide source for testability improvements

#### Configuration
```yaml
tester:
  model: gpt-4.1
  fallback_model: claude-sonnet-4
  provider: openai
  max_tokens: 4096
  temperature: 0.1
  tools:
    - pytest
    - vitest
    - playwright
    - coverage_analyzer
    - test_generator
    - api_tester
    - snapshot_tester
  context_tiers:
    l0: 2000
    l1: 12000
    l2: 18000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 2
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 600
  settings:
    coverage_thresholds:
      line: 80
      branch: 70
      function: 85
    test_frameworks:
      python: pytest
      javascript: vitest
      e2e: playwright
    max_test_retries: 2
```

---

### 22. Debugger Agent

#### Overview
- **Role**: Root cause analysis, automated fix generation, and **experiment-based fix-test loop** with keep/discard semantics (inspired by Karpathy's autoresearch)
- **Category**: Testing
- **Graph Position**: Debug/Fix phase (ExperimentLoopNode); after Testing; loops back to Implementation agents
- **Upstream Dependencies**: Tester (failed tests), Security Auditor (security findings), Code Reviewer (review comments)
- **Downstream Consumers**: All Implementation agents (via fix loop), Orchestrator, Documentation Writer

#### Responsibilities
1. Analyze test failures to identify root causes through stack trace parsing and code analysis
2. Parse and prioritize issues from security findings, review comments, and accessibility violations
3. **Formulate fix hypotheses** — each fix attempt is a discrete experiment with a stated hypothesis
4. **Create experiment branches** — each fix gets its own git branch (`experiment/N`) for isolation
5. Generate targeted code fixes and regression tests
6. **Measure experiment outcomes** — compare test pass rate before/after, check regression guards
7. **Keep or discard** — merge experiment branch if improved, delete if degraded (no cascading breakage)
8. **Log all experiments** to `experiment_log.tsv` — both kept and discarded attempts for learning
9. Apply **circuit breakers**: stop after time budget, token budget, or N consecutive non-improvements
10. Generate experiment report documenting all attempts (kept + discarded), root causes, and remaining items

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `file_read` | Read source code and test files | Git worktree filesystem |
| `file_write` | Write fix patches | Git worktree filesystem |
| `file_edit` | Apply targeted code edits | AST-aware editor |
| `bash` | Run tests, linters, build tools | Subprocess execution |
| `grep` | Search for error patterns in codebase | ripgrep integration |
| `stack_trace_parser` | Parse and analyze stack traces | Internal parser |
| `git_diff` | Compare changes between fix iterations | Git CLI |
| `git_branch_manager` | Create/merge/delete experiment branches | Git CLI |
| `experiment_logger` | Log experiment results to experiment_log.tsv | Internal logger |
| `metric_collector` | Measure test pass rate, coverage, and secondary metrics | Test runner integration |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Failed test results | Tester | JSON with stack traces |
| Security findings | Security Auditor | JSON finding list |
| Review comments | Code Reviewer | JSON comment list |
| Accessibility issues | Accessibility Agent | JSON issue list |
| Performance issues | Performance Agent | JSON optimization list |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Code fixes | Implementation agents (via git) | Modified source files |
| Fix verification tests | Tester | New test files |
| Debug report | Orchestrator, Documentation Writer | Markdown report |
| Remaining issues | Orchestrator (for human escalation) | JSON issue list |
| Fix iteration metrics | Dashboard | JSON metrics |
| Experiment log | Dashboard, Knowledge system | TSV (commit, hypothesis, metrics, status) |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Root cause analysis | Claude Opus 4 (via Claude Code) | o3 | Deep reasoning for complex bugs |
| Fix generation | Claude Sonnet 4 (via Claude Code) | GPT-4.1 (via Codex) | Precise code editing |
| Regression analysis | Claude Sonnet 4 | GPT-4.1 | Cross-reference impact analysis |
| Fix verification | Claude Haiku 3.5 | GPT-4.1-mini | Fast test execution and validation |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Current issue, stack trace, agent instructions | ~2,000 tokens |
| L1 | Affected source files, test files, related config | ~15,000 tokens |
| L2 | Full codebase search, error pattern database, fix history | ~20,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> BASELINING --> HYPOTHESIZING --> BRANCHING --> FIXING --> MEASURING
                                              ^                                       |
                                              |                              +--------+--------+
                                              |                              |                 |
                                              |                           KEEP              DISCARD
                                              |                           (merge)           (delete branch)
                                              |                              |                 |
                                              +-----[next experiment]--------+-----------------+
                                              |
                                     [circuit breaker triggered]
                                              |
                                              v
                                      COMPLETED / ESCALATED
```

#### Error Handling
- **Recovery strategies**: If fix degrades test pass rate, it is automatically DISCARDED (branch deleted) — no manual rollback needed. If root cause is unclear, expand analysis context. Circular regression loops are impossible by design since each experiment is evaluated against the stable baseline, not the previous experiment
- **Fallback behaviors**: Apply minimal fixes (suppress warnings, add error handling) if root cause fix is too complex; skip non-critical issues and document as known limitations
- **Escalation paths**: After 5 fix iterations without convergence, escalate to human with full debug report; immediately escalate security-critical bugs that resist automated fixing

#### Interaction Patterns
- **Primary collaborators**: Tester (receives failures, runs verification), all Implementation agents (applies fixes to their code), Orchestrator (manages fix loop lifecycle), Security Auditor (receives security fix verification)
- **Communication protocol**: State flow for fix artifacts; message flow for fix-test loop coordination; control flow for loop termination
- **Conflict resolution**: Debugger has authority on fix approach; implementation agents can suggest alternatives; Orchestrator decides on escalation timing

#### Configuration
```yaml
debugger:
  model: claude-opus-4
  fallback_model: o3
  provider: anthropic
  cli_agent: claude-code
  max_tokens: 8192
  temperature: 0.2
  tools:
    - file_read
    - file_write
    - file_edit
    - bash
    - grep
    - stack_trace_parser
    - git_diff
  context_tiers:
    l0: 2000
    l1: 15000
    l2: 20000
  retry_policy:
    max_retries: 5
    base_delay_seconds: 2
    max_delay_seconds: 60
    exponential_base: 2
  timeout: 600
  worktree: true
  settings:
    max_fix_iterations: 5
    enable_regression_testing: true
    escalation_threshold: 3
```

---

## Operations Agents

---

### 23. DevOps Agent

#### Overview
- **Role**: CI/CD pipeline design, monitoring setup, and operational infrastructure management
- **Category**: Operations
- **Graph Position**: Delivery phase; after Debug/Fix loop
- **Upstream Dependencies**: Infrastructure Engineer (IaC configs), Tester (test pipeline), Security Auditor (scan pipeline)
- **Downstream Consumers**: GitHub Agent, Documentation Writer, User

#### Responsibilities
1. Design and implement CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)
2. Configure multi-stage deployment pipelines (build, test, scan, deploy)
3. Set up monitoring infrastructure (Prometheus, Grafana dashboards, alerting rules)
4. Configure log aggregation and centralized logging (ELK stack, Loki, CloudWatch)
5. Implement alerting rules and escalation policies for production incidents
6. Set up SLA monitoring and uptime tracking
7. Configure automated rollback strategies for failed deployments
8. Create operational runbooks for common maintenance tasks

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `pipeline_generator` | Generate CI/CD pipeline definitions | YAML template engine |
| `monitoring_configurator` | Set up Prometheus/Grafana configs | Config generator |
| `alerting_configurator` | Define alerting rules and channels | Alertmanager config |
| `log_configurator` | Set up log aggregation pipelines | ELK/Loki config |
| `runbook_generator` | Create operational runbooks | Markdown template |
| `deployment_validator` | Validate deployment configurations | Dry-run validators |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Infrastructure configs | Infrastructure Engineer | Terraform/K8s files |
| Test pipeline | Tester | Test framework config |
| Security scan pipeline | Security Auditor | Scanner config |
| Application architecture | Architect | Architecture document |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| CI/CD pipeline files | GitHub Agent | YAML workflow files |
| Monitoring dashboards | User, Ops team | Grafana JSON |
| Alerting rules | User, Ops team | Prometheus rules YAML |
| Operational runbooks | Documentation Writer, User | Markdown documents |
| Deployment scripts | GitHub Agent | Shell/YAML scripts |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Pipeline design | Claude Sonnet 4 | GPT-4.1 | Complex multi-stage workflow logic |
| Monitoring setup | Claude Haiku 3.5 | GPT-4.1-mini | Configuration generation |
| Alerting rules | Claude Sonnet 4 | GPT-4.1 | Threshold reasoning |
| Runbook generation | Gemini 2.5 Flash | Claude Haiku 3.5 | Long-form document generation |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | CI/CD platform, deployment target, agent instructions | ~2,000 tokens |
| L1 | Infrastructure configs, test pipeline, application structure | ~8,000 tokens |
| L2 | CI/CD best practices, monitoring guides, deployment patterns | ~12,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> DESIGNING --> CONFIGURING --> VALIDATING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If pipeline validation fails, fix YAML syntax and retry; if monitoring config is incompatible with target platform, adapt to available metrics
- **Fallback behaviors**: Use simple single-stage pipeline if complex multi-stage fails; use default Grafana dashboards if custom dashboard generation fails
- **Escalation paths**: Escalate deployment strategy decisions (blue-green vs. canary) to Architect; flag missing infrastructure requirements to Infrastructure Engineer

#### Interaction Patterns
- **Primary collaborators**: Infrastructure Engineer (receives IaC), GitHub Agent (delivers pipelines), Tester (integrates test pipeline), Security Auditor (integrates scan pipeline)
- **Communication protocol**: State flow for pipeline artifacts; message flow for infrastructure requirements
- **Conflict resolution**: DevOps Agent has authority on CI/CD pipeline design; Infrastructure Engineer provides infrastructure constraints

#### Configuration
```yaml
devops:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 4096
  temperature: 0.2
  tools:
    - pipeline_generator
    - monitoring_configurator
    - alerting_configurator
    - log_configurator
    - runbook_generator
    - deployment_validator
  context_tiers:
    l0: 2000
    l1: 8000
    l2: 12000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 3
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 300
  settings:
    ci_platform: github_actions
    monitoring_stack: prometheus_grafana
    log_stack: loki
```

---

### 24. GitHub Agent

#### Overview
- **Role**: GitHub operations management including repository setup, PR automation, and release management
- **Category**: Operations
- **Graph Position**: Delivery phase; works throughout pipeline for git operations
- **Upstream Dependencies**: Orchestrator (project config), DevOps Agent (CI/CD pipelines), all Implementation agents (code branches)
- **Downstream Consumers**: User, Documentation Writer

#### Responsibilities
1. Create and configure GitHub repositories with proper settings (branch protection, webhooks)
2. Manage branch strategies (feature branches, release branches, gitflow or trunk-based)
3. Automate pull request creation with descriptions, labels, and reviewers
4. Post review comments from Code Reviewer and Security Auditor as PR annotations
5. Configure GitHub Actions workflows from DevOps Agent output
6. Manage releases with semantic versioning, changelogs, and release notes
7. Set up GitHub project boards for task tracking
8. Configure issue templates, PR templates, and contributing guidelines

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `gh_cli` | GitHub CLI for repository and PR management | GitHub CLI (`gh`) |
| `git` | Git operations (branch, commit, merge, tag) | Git CLI |
| `pr_creator` | Create PRs with descriptions and metadata | GitHub API |
| `review_commenter` | Post inline review comments on PRs | GitHub API |
| `release_manager` | Create releases with changelogs | GitHub API |
| `project_board` | Manage GitHub project boards | GitHub Projects API |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Repository configuration | Orchestrator | JSON settings |
| CI/CD pipeline files | DevOps Agent | YAML workflow files |
| Code branches | All Implementation agents | Git branches |
| Review comments | Code Reviewer, Security Auditor | JSON comments |
| Release notes | Documentation Writer | Markdown |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Repository URL | User, Dashboard | URL string |
| Pull request URLs | User, Dashboard | URL strings |
| Release URL | User | URL string |
| CI/CD status | Dashboard | JSON status |
| Merge results | Orchestrator | JSON success/failure |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| PR description generation | Claude Sonnet 4 | GPT-4.1 | Clear technical writing |
| Changelog generation | Claude Haiku 3.5 | Gemini 2.5 Flash | Structured summary |
| Merge conflict resolution | Claude Opus 4 | GPT-4.1 | Complex code merge reasoning |
| Branch strategy | Claude Haiku 3.5 | GPT-4.1-mini | Standard pattern application |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Repository name, branch strategy, agent instructions | ~1,500 tokens |
| L1 | Git log, branch status, PR template, review comments | ~8,000 tokens |
| L2 | Git best practices, GitHub API documentation | ~10,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> EXECUTING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If PR creation fails due to merge conflicts, attempt auto-merge resolution; if GitHub API rate limit hit, queue operations with exponential backoff
- **Fallback behaviors**: Use local git operations if GitHub API is unavailable; create PRs manually via git push if `gh` CLI fails
- **Escalation paths**: Escalate merge conflicts that cannot be auto-resolved to human; escalate repository permission issues to admin

#### Interaction Patterns
- **Primary collaborators**: All Implementation agents (manages their branches), DevOps Agent (receives pipeline files), Code Reviewer (posts review comments), Documentation Writer (publishes releases)
- **Communication protocol**: State flow for repository status; message flow for merge conflict alerts
- **Conflict resolution**: GitHub Agent has authority on git operations; Orchestrator decides on merge order; human resolves unresolvable merge conflicts

#### Configuration
```yaml
github:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 4096
  temperature: 0.2
  tools:
    - gh_cli
    - git
    - pr_creator
    - review_commenter
    - release_manager
    - project_board
  context_tiers:
    l0: 1500
    l1: 8000
    l2: 10000
  retry_policy:
    max_retries: 3
    base_delay_seconds: 2
    max_delay_seconds: 60
    exponential_base: 2
  timeout: 300
  settings:
    branch_strategy: trunk_based
    branch_prefix: "codebot/"
    commit_prefix: "[CodeBot]"
    auto_merge: false
    enable_branch_protection: true
```

---

### 25. Documentation Writer Agent

#### Overview
- **Role**: Comprehensive technical documentation generation across all project artifacts
- **Category**: Operations
- **Graph Position**: Documentation phase; after Debug/Fix loop; before Delivery
- **Upstream Dependencies**: All agents (accumulated artifacts and decisions)
- **Downstream Consumers**: User, GitHub Agent (for publishing)

#### Responsibilities
1. Generate API documentation from OpenAPI specifications (Swagger UI, Redoc)
2. Create comprehensive README files with setup, usage, and contribution instructions
3. Write Architecture Decision Records (ADRs) from Architect's decisions
4. Generate deployment guides from Infrastructure Engineer's configurations
5. Create user manuals and feature guides for end users
6. Generate changelog from git history and agent activity logs
7. Produce a project handoff document summarizing all decisions, trade-offs, and known limitations
8. Generate inline code documentation (JSDoc, Python docstrings) where missing

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `openapi_renderer` | Generate API docs from OpenAPI spec | Swagger UI / Redoc |
| `readme_generator` | Create README from project structure and docs | Template engine |
| `adr_formatter` | Format ADRs in standard template | MADR template |
| `changelog_generator` | Generate changelog from git history | Conventional commits parser |
| `docstring_generator` | Generate missing code documentation | AST analysis + LLM |
| `file_writer` | Write documentation files | Git filesystem |
| `diagram_renderer` | Render architecture diagrams | Mermaid CLI |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Architecture document | Architect | Markdown |
| OpenAPI specification | API Gateway Agent | YAML |
| ADRs | Architect | Markdown |
| Infrastructure configs | Infrastructure Engineer | Terraform/K8s files |
| Git history | GitHub Agent | Git log |
| Test results | Tester | JSON report |
| Security report | Security Auditor | JSON report |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| README.md | User, GitHub | Markdown |
| API documentation | User | HTML (Swagger UI) |
| Deployment guide | User, Ops team | Markdown |
| Architecture Decision Records | User | Markdown files |
| Changelog | User, GitHub Agent | Markdown |
| Project handoff document | User | Markdown |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| README generation | Gemini 2.5 Flash | Claude Haiku 3.5 | Cost-effective long-form writing |
| API documentation | Claude Haiku 3.5 | Gemini 2.5 Flash | Structured spec transformation |
| ADR writing | Claude Sonnet 4 | GPT-4.1 | Clear technical reasoning |
| Deployment guide | Gemini 2.5 Flash | Claude Haiku 3.5 | Step-by-step instruction writing |
| Handoff document | Gemini 2.5 Pro | Claude Sonnet 4 | Comprehensive project summarization |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Documentation types needed, project summary, agent instructions | ~2,000 tokens |
| L1 | Architecture doc, API spec, test results, security report | ~15,000 tokens |
| L2 | Full codebase, git history, all agent outputs | ~25,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> GATHERING --> WRITING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If API doc rendering fails, generate plain Markdown API docs; if diagram rendering fails, use text-based diagrams; if source artifacts are missing, generate documentation from code analysis
- **Fallback behaviors**: Generate minimal README + API docs if full documentation generation times out; skip optional docs (user manual) under time pressure
- **Escalation paths**: Flag documentation gaps (missing architecture decisions, undocumented APIs) to Orchestrator; request human review for user-facing documentation

#### Interaction Patterns
- **Primary collaborators**: All agents (gathers their outputs), GitHub Agent (publishes documentation), User (final consumer)
- **Communication protocol**: State flow for gathering inputs from all agents; message flow for requesting missing information
- **Conflict resolution**: Documentation Writer presents accumulated information; Architect and Orchestrator verify accuracy of technical content

#### Configuration
```yaml
doc_writer:
  model: gemini-2.5-flash
  fallback_model: claude-haiku-3.5
  provider: google
  max_tokens: 8192
  temperature: 0.3
  tools:
    - openapi_renderer
    - readme_generator
    - adr_formatter
    - changelog_generator
    - docstring_generator
    - file_writer
    - diagram_renderer
  context_tiers:
    l0: 2000
    l1: 15000
    l2: 25000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 3
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 600
  settings:
    generate_readme: true
    generate_api_docs: true
    generate_adrs: true
    generate_changelog: true
    generate_deployment_guide: true
    doc_format: markdown
```

---

## Tooling Agents

---

### 26. Skill Creator Agent

#### Overview
- **Role**: Creates reusable skills and capabilities that other agents can invoke across projects
- **Category**: Tooling
- **Graph Position**: Cross-cutting; operates post-delivery to extract reusable patterns
- **Upstream Dependencies**: All Implementation agents (code patterns), Orchestrator (pipeline patterns)
- **Downstream Consumers**: All agents (via skill library), Orchestrator (skill registry)

#### Responsibilities
1. Identify common patterns across completed projects (auth flows, CRUD operations, deployment configs)
2. Extract reusable patterns into parameterized skill definitions
3. Package skills with input/output schemas, documentation, and test cases
4. Maintain a searchable skill library with versioning and compatibility metadata
5. Generate skill composition guides for combining multiple skills
6. Track skill usage analytics to prioritize maintenance and improvements
7. Create skill documentation with usage examples and best practices

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `pattern_extractor` | Identify reusable patterns from code | AST analysis + LLM |
| `skill_packager` | Package patterns into skill definitions | Internal packaging tool |
| `skill_registry` | Register and version skills in library | Internal registry |
| `skill_tester` | Validate skill correctness with test cases | Test framework |
| `skill_documenter` | Generate skill documentation | Markdown generator |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Completed project code | Implementation agents | Source code files |
| Pipeline execution logs | Orchestrator | JSON execution history |
| Agent interaction patterns | Event bus | Event stream data |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Skill definitions | All agents | YAML + code templates |
| Skill documentation | Documentation Writer | Markdown |
| Skill test suites | Tester | Test files |
| Skill registry updates | Orchestrator | JSON registry entries |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Pattern identification | Claude Opus 4 | Gemini 2.5 Pro | Cross-project pattern recognition |
| Skill extraction | Claude Sonnet 4 | GPT-4.1 | Code abstraction and parameterization |
| Documentation | Claude Haiku 3.5 | Gemini 2.5 Flash | Technical writing |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Skill creation instructions, existing skill catalog | ~2,000 tokens |
| L1 | Project code samples, pipeline patterns | ~10,000 tokens |
| L2 | Cross-project code analysis, skill library | ~20,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> ANALYZING --> EXTRACTING --> PACKAGING --> TESTING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If pattern extraction produces overly specific skills, generalize parameters; if skill tests fail, refine skill implementation
- **Fallback behaviors**: Create documentation-only skills (guides without automation) if code packaging fails
- **Escalation paths**: Request human review for skills that affect security-critical patterns

#### Configuration
```yaml
skill_creator:
  model: claude-opus-4
  fallback_model: gemini-2.5-pro
  provider: anthropic
  max_tokens: 4096
  temperature: 0.3
  tools:
    - pattern_extractor
    - skill_packager
    - skill_registry
    - skill_tester
    - skill_documenter
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
```

---

### 27. Hooks Creator Agent

#### Overview
- **Role**: Creates lifecycle hooks for build, test, deploy, and review phases
- **Category**: Tooling
- **Graph Position**: Cross-cutting; configures hooks during pipeline setup
- **Upstream Dependencies**: DevOps Agent (CI/CD pipeline), Orchestrator (pipeline configuration)
- **Downstream Consumers**: All agents (via hook execution), Orchestrator (hook registry)

#### Responsibilities
1. Create pre/post hooks for build phases (pre-build validation, post-build artifact signing)
2. Create pre/post hooks for test phases (test environment setup, coverage threshold validation)
3. Create pre/post hooks for deploy phases (pre-deploy smoke tests, post-deploy health checks)
4. Create review phase hooks (pre-review lint check, post-review auto-merge conditions)
5. Build custom validation hooks (schema validation, API contract testing)
6. Create notification hooks (Slack, Discord, email notifications on pipeline events)
7. Build integration hooks (external service callbacks, webhook triggers)

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `hook_generator` | Generate hook scripts | Shell/Python template engine |
| `hook_registry` | Register hooks in pipeline configuration | Pipeline config updater |
| `hook_tester` | Validate hook execution | Test runner |
| `webhook_configurator` | Configure external webhook integrations | HTTP client |
| `notification_sender` | Send notifications to configured channels | Slack/Discord API |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Pipeline configuration | DevOps Agent | YAML pipeline definitions |
| Hook requirements | Orchestrator | JSON hook specifications |
| Integration endpoints | Integrations Agent | JSON webhook URLs |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Hook scripts | Pipeline executor | Shell/Python scripts |
| Hook configuration | DevOps Agent | YAML config |
| Hook documentation | Documentation Writer | Markdown |
| Notification templates | Pipeline executor | Template strings |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Hook script generation | Claude Sonnet 4 | GPT-4.1 | Reliable script generation |
| Integration hook design | Claude Haiku 3.5 | GPT-4.1-mini | Configuration-heavy tasks |
| Notification template | Claude Haiku 3.5 | Gemini 2.5 Flash | Template generation |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Hook type, phase, agent instructions | ~1,500 tokens |
| L1 | Pipeline config, integration endpoints, existing hooks | ~6,000 tokens |
| L2 | Hook best practices, webhook documentation | ~10,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> GENERATING --> TESTING --> REGISTERING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If hook script fails validation, regenerate with simpler logic; if webhook integration fails, retry with timeout adjustment
- **Fallback behaviors**: Create no-op hooks that log but do not block pipeline if complex hook generation fails
- **Escalation paths**: Escalate hook failures that block the pipeline to DevOps Agent; flag notification delivery failures for human attention

#### Configuration
```yaml
hooks_creator:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 4096
  temperature: 0.1
  tools:
    - hook_generator
    - hook_registry
    - hook_tester
    - webhook_configurator
    - notification_sender
  context_tiers:
    l0: 1500
    l1: 6000
    l2: 10000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 2
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 240
```

---

### 28. Tools Creator Agent

#### Overview
- **Role**: Creates custom tools and MCP server integrations for extending agent capabilities
- **Category**: Tooling
- **Graph Position**: Cross-cutting; operates during pipeline setup or on demand
- **Upstream Dependencies**: Orchestrator (tool requirements), Researcher (external service APIs)
- **Downstream Consumers**: All agents (via tool registry), Orchestrator (tool configuration)

#### Responsibilities
1. Build tool wrappers for external services (APIs, CLIs, databases)
2. Create MCP (Model Context Protocol) server configurations for tool exposure
3. Develop custom analysis tools (code complexity, dependency graphs, architecture validators)
4. Build data transformation tools (format converters, schema validators)
5. Create monitoring and instrumentation tools (custom metrics, trace spans)
6. Package tools with input/output schemas, documentation, and error handling
7. Register tools in the agent tool registry with capability descriptions

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `tool_generator` | Generate tool implementation code | Code template engine |
| `mcp_configurator` | Create MCP server configurations | MCP SDK |
| `schema_validator` | Validate tool input/output schemas | JSON Schema validator |
| `tool_registry` | Register tools in agent tool registry | Internal registry |
| `tool_tester` | Test tool implementations | Test framework |
| `api_wrapper_generator` | Generate API client wrappers | OpenAPI codegen |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Tool requirements | Orchestrator | JSON specification |
| External API specs | Researcher | OpenAPI/docs |
| Existing tool catalog | Tool registry | JSON catalog |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Tool implementations | All agents | Python/TypeScript code |
| MCP server configs | CLI agents | JSON MCP configuration |
| Tool documentation | Documentation Writer | Markdown |
| Tool registry updates | Orchestrator | JSON registry |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Tool implementation | Claude Sonnet 4 | GPT-4.1 | Reliable code generation |
| MCP configuration | Claude Haiku 3.5 | GPT-4.1-mini | Configuration generation |
| API wrapper generation | Claude Sonnet 4 | GPT-4.1 | SDK-aware code generation |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Tool specification, agent instructions | ~1,500 tokens |
| L1 | External API docs, existing tools, MCP schema | ~8,000 tokens |
| L2 | MCP documentation, tool pattern library | ~12,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> DESIGNING --> IMPLEMENTING --> TESTING --> REGISTERING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If tool implementation fails tests, iterate on error handling; if MCP configuration is invalid, validate against schema and fix
- **Fallback behaviors**: Create simple passthrough tools if complex wrapper generation fails; use subprocess-based tool execution if SDK integration fails
- **Escalation paths**: Escalate security-sensitive tool implementations (credential handling) for human review; flag tools with external network access for security audit

#### Configuration
```yaml
tools_creator:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 4096
  temperature: 0.1
  tools:
    - tool_generator
    - mcp_configurator
    - schema_validator
    - tool_registry
    - tool_tester
    - api_wrapper_generator
  context_tiers:
    l0: 1500
    l1: 8000
    l2: 12000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 3
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 300
```

---

### 29. Integrations Agent

#### Overview
- **Role**: Third-party service integration for payment, auth, email, storage, analytics, and more
- **Category**: Tooling
- **Graph Position**: Implementation phase; parallel with other implementation agents when integrations are needed
- **Upstream Dependencies**: Architect (integration requirements), Researcher (service API documentation), API Gateway (API contracts)
- **Downstream Consumers**: Backend Developer, Middleware Developer, Code Reviewer, Tester

#### Responsibilities
1. Integrate payment gateways (Stripe, PayPal, Square) with checkout flows and webhook handling
2. Configure authentication providers (Auth0, Firebase Auth, Clerk, Supabase Auth)
3. Set up email services (SendGrid, Mailgun, AWS SES) with templates and transactional email
4. Configure cloud storage (S3, Cloudinary, Supabase Storage) for file uploads
5. Integrate analytics platforms (Mixpanel, Google Analytics, PostHog, Amplitude)
6. Set up push notification services (Firebase Cloud Messaging, OneSignal)
7. Configure search services (Algolia, Elasticsearch, Meilisearch)
8. Create integration test suites for all third-party service connections

#### Tools & Capabilities
| Tool | Purpose | Integration |
|------|---------|-------------|
| `api_client_generator` | Generate typed API clients for services | OpenAPI codegen |
| `webhook_handler_generator` | Create webhook endpoint handlers | Template engine |
| `env_configurator` | Set up environment variables for services | `.env` file manager |
| `integration_tester` | Test third-party service connectivity | HTTP client |
| `mock_service_generator` | Create mock services for testing | MSW / respx |
| `file_writer` | Write integration code | Git filesystem |

#### Input/Output Specification
**Inputs:**

| Input | Source | Format |
|-------|--------|--------|
| Integration requirements | Architect | JSON list of services |
| Service API documentation | Researcher | Markdown summaries |
| API contracts | API Gateway Agent | OpenAPI specification |
| Environment configuration | Infrastructure Engineer | `.env` template |

**Outputs:**

| Output | Consumers | Format |
|--------|-----------|--------|
| Integration code | Backend Dev, Middleware Dev | Python/TypeScript files |
| API client modules | Backend Developer | SDK wrapper files |
| Webhook handlers | Backend Developer | Route handler files |
| Mock services | Tester | Mock configuration files |
| Integration tests | Tester | Test files |
| Service configuration | Infrastructure Engineer | Environment variables |

#### LLM Configuration
| Task | Recommended Model | Fallback | Rationale |
|------|-------------------|----------|-----------|
| Payment integration | Claude Opus 4 | GPT-4.1 | Security-critical; requires precision |
| Auth provider setup | Claude Sonnet 4 | GPT-4.1 | Complex OAuth flow implementation |
| Email/storage/analytics | Claude Haiku 3.5 | GPT-4.1-mini | Well-established patterns |
| Mock service generation | Claude Haiku 3.5 | GPT-4.1-mini | Template-based generation |

#### Context Requirements
| Tier | Content | Token Budget |
|------|---------|--------------|
| L0 | Service list, API keys (names, not values), agent instructions | ~2,000 tokens |
| L1 | Service API docs, architecture doc, API contracts | ~12,000 tokens |
| L2 | Full service documentation, integration examples, best practices | ~20,000 tokens |

#### Agent State Machine
```
IDLE --> INITIALIZING --> IMPLEMENTING --> TESTING --> REVIEWING --> COMPLETED/FAILED
```

#### Error Handling
- **Recovery strategies**: If service API has breaking changes, consult latest documentation and adapt; if API key is missing, create placeholder with clear setup instructions; if integration test fails, verify API credentials and endpoint URLs
- **Fallback behaviors**: Use mock implementations for services without available API keys; generate stub integrations with clear TODO markers for manual completion
- **Escalation paths**: Escalate payment integration issues (PCI compliance concerns) to Security Auditor; flag missing API credentials to user for provisioning

#### Interaction Patterns
- **Primary collaborators**: Backend Developer (provides integration code), Middleware Developer (provides middleware integrations), Researcher (provides API documentation), Security Auditor (validates integration security)
- **Communication protocol**: State flow for integration code; message flow for API credential requirements
- **Conflict resolution**: Integrations Agent follows Architect's integration decisions; defers to Security Auditor on security-sensitive integrations

#### Configuration
```yaml
integrations:
  model: claude-sonnet-4
  fallback_model: gpt-4.1
  provider: anthropic
  max_tokens: 4096
  temperature: 0.1
  tools:
    - api_client_generator
    - webhook_handler_generator
    - env_configurator
    - integration_tester
    - mock_service_generator
    - file_writer
  context_tiers:
    l0: 2000
    l1: 12000
    l2: 20000
  retry_policy:
    max_retries: 2
    base_delay_seconds: 3
    max_delay_seconds: 30
    exponential_base: 2
  timeout: 600
  settings:
    generate_mocks: true
    require_integration_tests: true
    supported_services:
      payment: [stripe, paypal]
      auth: [auth0, firebase_auth, clerk]
      email: [sendgrid, mailgun]
      storage: [s3, cloudinary]
      analytics: [mixpanel, posthog]
```

---

## Coordination Agents

### 17.1 Project Manager Agent (#30)

**Stage:** S0 (Project Initialization) / Cross-cutting
**Category:** Coordination
**Model:** Claude Opus 4

#### Overview
The Project Manager Agent serves as the cross-cutting coordination layer that tracks project-wide progress, manages timelines, allocates resources across agent pools, and ensures pipeline-level coherence. It monitors all stage gates, handles escalations, and provides unified project status reporting.

#### Responsibilities
- Track project-wide progress across all pipeline stages (S0-S10)
- Monitor stage gate pass/fail metrics and escalate blockers
- Allocate and rebalance agent pool resources based on workload
- Generate unified project status reports and dashboards
- Manage inter-stage dependencies and handoff coordination
- Handle timeline estimation and milestone tracking
- Coordinate human-in-the-loop approvals and notifications

#### Input/Output Specification

**Input:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | string | Yes | Active project identifier |
| `stage_statuses` | object | Yes | Current status of each pipeline stage |
| `agent_pool_metrics` | object | No | Resource utilization across agent pools |
| `escalations` | array | No | Pending escalation items |

**Output:**
| Field | Type | Description |
|-------|------|-------------|
| `project_report` | object | Unified project status report |
| `resource_allocations` | object | Updated agent pool assignments |
| `escalation_decisions` | array | Resolution actions for escalated items |
| `timeline_updates` | object | Updated milestone estimates |

#### Tools
| Tool | Description | Implementation |
|------|-------------|----------------|
| `pipeline_monitor` | Track stage gate metrics | NATS + JetStream subscription |
| `resource_allocator` | Manage agent pool sizing | LangGraph state management |
| `report_generator` | Generate project status reports | Template + LLM synthesis |
| `escalation_handler` | Process and route escalations | Rule engine + LLM triage |
| `timeline_tracker` | Estimate and track milestones | Historical data analysis |

#### Error Handling
| Error | Recovery | Fallback |
|-------|----------|----------|
| Stage gate timeout | Retry with extended timeout | Escalate to human operator |
| Agent pool exhaustion | Queue tasks, alert operator | Degrade to sequential execution |
| Metrics collection failure | Use cached metrics | Log gap, continue with partial data |

#### Configuration
```yaml
project_manager:
  model: claude-opus-4
  poll_interval: 30s
  escalation_timeout: 300s
  report_frequency: per_stage_completion
  max_concurrent_projects: 5
  resource_rebalance_threshold: 0.8
```

---

## Agent Collaboration Matrix

The following matrix shows interaction patterns between all 30 agents. Each cell indicates the type of interaction:

- **D** = Data flow (state propagation)
- **M** = Message flow (direct communication)
- **C** = Control flow (execution triggers)
- **A** = Approval flow (gate validation)
- **--** = No direct interaction

```
                 ORC BRA PLA TSB RES ARC DES TMP DBA API FED BED MID MOB INF SEC CRV ACC PER I18 TST DBG DEV GIT DOC SKL HKS TLS INT
Orchestrator(1)   -   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C   C
Brainstorming(2)  D   -   D   D   --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --
Planner(3)        D   --  -   M   D   D   --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --
TechStack(4)      D   --  M   -   M   D   D   D   D   D   D   D   D   D   D   D   --  --  --  --  --  --  --  --  --  --  --  --  --
Researcher(5)     D   --  --  M   -   D   D   --  --  --  D   D   --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  D
Architect(6)      D   --  --  --  --  -   D   D   D   D   D   D   D   D   D   --  --  --  --  --  --  --  --  --  D   --  --  --  D
Designer(7)       D   --  --  --  --  --  -   D   --  --  D   --  --  D   --  --  --  D   --  D   --  --  --  --  --  --  --  --  --
Template(8)       D   --  --  --  --  --  --  -   --  --  D   D   --  --  D   --  --  --  --  --  --  --  --  --  --  --  --  --  --
Database(9)       D   --  --  --  --  --  --  --  -   M   --  D   D   --  D   --  --  --  --  --  --  --  --  --  --  --  --  --  --
API Gateway(10)   D   --  --  --  --  --  --  --  M   -   D   D   D   D   --  --  --  --  --  --  D   --  --  --  --  --  --  --  D
Frontend(11)      D   --  --  --  --  --  --  --  --  --  -   M   --  --  --  D   D   D   D   D   D   D   --  --  --  --  --  --  --
Backend(12)       D   --  --  --  --  --  --  --  --  --  M   -   M   --  --  D   D   --  D   --  D   D   --  --  --  --  --  --  --
Middleware(13)     D   --  --  --  --  --  --  --  --  --  --  M   -   --  M   D   D   --  --  --  D   D   --  --  --  --  --  --  --
Mobile(14)        D   --  --  --  --  --  --  --  --  --  --  --  --  -   --  D   D   D   D   D   D   D   --  --  --  --  --  --  --
Infrastructure(15)D   --  --  --  --  --  --  --  --  --  --  --  --  --  -   D   D   --  --  --  --  --  D   D   --  --  --  --  --
Security(16)      D   --  --  --  --  --  --  --  --  --  --  --  --  --  --  -   M   --  --  --  --  D   --  --  D   --  --  --  --
Code Reviewer(17) D   --  --  --  --  --  --  --  --  --  --  --  --  --  --  M   -   --  --  --  --  D   --  D   D   --  --  --  --
Accessibility(18) D   --  --  --  --  --  --  --  --  --  D   --  --  D   --  --  --  -   --  --  --  D   --  --  --  --  --  --  --
Performance(19)   D   --  --  --  --  --  --  --  --  --  D   D   --  --  D   --  --  --  -   --  --  D   --  --  D   --  --  --  --
i18n/L10n(20)     D   --  --  --  --  --  M   --  --  --  D   --  --  D   --  --  --  --  --  -   --  D   --  --  --  --  --  --  --
Tester(21)        D   --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  -   D   --  --  D   --  --  --  --
Debugger(22)      D   --  --  --  --  --  --  --  --  --  D   D   D   D   D   --  --  D   D   D   --  -   --  --  D   --  --  --  --
DevOps(23)        D   --  --  --  --  --  --  --  --  --  --  --  --  --  D   --  --  --  --  --  D   --  -   D   D   --  D   --  --
GitHub(24)        D   --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  D   --  --  --  --  --  D   -   D   --  --  --  --
Doc Writer(25)    D   --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  D   -   --  --  --  --
Skill Creator(26) D   --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  D   -   --  --  --
Hooks Creator(27) D   --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  D   --  D   --  -   --  --
Tools Creator(28) D   --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  --  D   --  --  -   --
Integrations(29)  D   --  --  --  --  --  --  --  --  M   --  D   D   --  --  D   --  --  --  --  D   --  --  --  --  --  --  --  -
```

---

## Agent Scaling Strategy

### Horizontal Scaling

Each agent category scales independently based on workload:

| Category | Scaling Strategy | Max Instances | Resource Per Instance |
|----------|-----------------|---------------|----------------------|
| Orchestration | Single instance (singleton) | 1 | 2 CPU, 4GB RAM |
| Ideation | On-demand, single instance | 1 | 1 CPU, 2GB RAM |
| Planning | On-demand, single instance per project | 1 | 1 CPU, 2GB RAM |
| Research | Parallel per research topic | 3 | 1 CPU, 2GB RAM |
| Design | Parallel by design domain | 5 | 1 CPU, 2GB RAM |
| Implementation | Parallel per feature/component | 10 | 2 CPU, 4GB RAM |
| Quality | Parallel per scan type | 5 | 2 CPU, 4GB RAM |
| Testing | Parallel per test suite | 3 | 2 CPU, 4GB RAM |
| Operations | On-demand, single instance | 3 | 1 CPU, 2GB RAM |
| Tooling | On-demand, single instance | 4 | 1 CPU, 2GB RAM |

### Resource Allocation Algorithm

```python
def allocate_resources(agent_type: str, task_complexity: int) -> ResourceConfig:
    """Allocate resources based on agent type and task complexity."""
    base_config = AGENT_RESOURCE_DEFAULTS[agent_type]

    # Scale up for complex tasks (complexity > 8 on Fibonacci scale)
    if task_complexity > 8:
        base_config.cpu *= 1.5
        base_config.memory *= 1.5
        base_config.timeout *= 2

    # Check global resource budget
    available = get_available_resources()
    if base_config.exceeds(available):
        base_config = base_config.scale_down_to(available)

    return base_config
```

### Concurrency Management

- **Git worktree pool**: Pre-allocate 5 worktrees; expand to 10 under load; clean up on task completion
- **LLM connection pool**: Per-provider connection limits (Anthropic: 3, OpenAI: 5, Google: 5)
- **Task queue**: Redis-based priority queue with dead letter queue for failed tasks
- **Rate limiting**: Token bucket per provider per model; backpressure propagated to task scheduler

---

## Agent Extension Points

### Creating Custom Agents

Users can extend the agent system by creating custom agents that implement the `BaseAgent` interface:

```python
from codebot.agents.base import BaseAgent, AgentConfig, AgentResult
from codebot.context import ContextManager
from codebot.tools import ToolRegistry

class CustomAgent(BaseAgent):
    """Template for creating a custom agent."""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.name = "custom_agent"
        self.category = "custom"

    async def execute(self, task: Task, context: ContextManager) -> AgentResult:
        """Main execution logic implementing the PRA cognitive cycle."""
        artifacts = []

        for iteration in range(self.config.max_iterations):
            # --- PERCEPTION: assemble context ---
            ctx = await context.load_tiers(task, tiers=["l0", "l1"])

            # --- REASONING: invoke LLM ---
            prompt = self.build_prompt(task, ctx)
            response = await self.llm.generate(prompt, tools=self.tools)

            # --- ACTION: execute tool calls or produce output ---
            new_artifacts = self.process_response(response)
            artifacts.extend(new_artifacts)

            # Check if task is complete (no more tool calls)
            if not response.has_tool_calls:
                break

            # Checkpoint between PRA iterations for crash recovery
            await self.checkpoint(iteration, artifacts)

        return AgentResult(
            status="completed",
            artifacts=artifacts,
            tokens_used=response.usage.total_tokens,
            cost_usd=response.usage.cost_usd,
        )

    def build_prompt(self, task: Task, context: dict) -> str:
        """Build the agent's prompt from task and context."""
        return f"""
        You are a {self.name} agent.

        ## Task
        {task.description}

        ## Context
        {context}

        ## Instructions
        {self.config.system_prompt}
        """
```

### Registering Custom Agents

```yaml
# configs/custom_agents.yaml
custom_agents:
  - name: compliance_checker
    class: myproject.agents.ComplianceAgent
    category: quality
    model: claude-opus-4
    tools:
      - policy_checker
      - regulation_db
    graph_position:
      after: [code_reviewer]
      before: [tester]

  - name: documentation_verifier
    class: myproject.agents.DocVerifierAgent
    category: quality
    model: claude-haiku-3.5
    tools:
      - doc_coverage_analyzer
      - link_checker
    graph_position:
      after: [doc_writer]
      before: [delivery]
```

### Extending Existing Agents

Extend any built-in agent by subclassing and overriding specific methods:

```python
from codebot.agents.security_auditor import SecurityAuditorAgent

class EnhancedSecurityAuditor(SecurityAuditorAgent):
    """Extended security auditor with custom compliance checks."""

    async def execute(self, task, context):
        # Run standard security scans
        result = await super().execute(task, context)

        # Add custom compliance check
        compliance = await self.run_compliance_check(task)
        result.artifacts["compliance_report"] = compliance

        return result

    async def run_compliance_check(self, task):
        """Run HIPAA/SOC2/GDPR compliance checks."""
        # Custom compliance logic
        pass
```

---

## Agent Template Configurations

### Full Pipeline (All 30 Agents)

```yaml
# configs/pipelines/full.yaml
pipeline:
  name: full_sdlc
  description: "Complete SDLC pipeline with all 30 agents"
  phases:
    - name: ideation
      agents: [brainstorming]
      timeout_minutes: 15
      requires_approval: false

    - name: planning
      agents: [planner, techstack_builder]
      timeout_minutes: 30
      requires_approval: true
      parallel: true

    - name: research
      agents: [researcher]
      timeout_minutes: 20

    - name: design
      agents: [architect, designer, template, database, api_gateway]
      timeout_minutes: 45
      requires_approval: true
      parallel: true

    - name: implementation
      agents: [frontend_dev, backend_dev, middleware_dev, mobile_dev, infra_engineer, integrations]
      timeout_minutes: 120
      parallel: true
      worktree_isolation: true

    - name: review
      agents: [security_auditor, code_reviewer, accessibility, performance, i18n_l10n]
      timeout_minutes: 45
      parallel: true

    - name: testing
      agents: [tester]
      timeout_minutes: 30

    - name: debug_fix
      agents: [debugger]
      timeout_minutes: 60
      max_iterations: 5
      loop: true

    - name: documentation
      agents: [doc_writer]
      timeout_minutes: 20

    - name: delivery
      agents: [devops, github]
      timeout_minutes: 15
      requires_approval: true
      parallel: true

    - name: tooling
      agents: [skill_creator, hooks_creator, tools_creator]
      timeout_minutes: 20
      parallel: true
      optional: true
```

### Quick Pipeline (Essential Agents Only)

```yaml
# configs/pipelines/quick.yaml
pipeline:
  name: quick_prototype
  description: "Rapid prototyping with essential agents (10 agents)"
  phases:
    - name: planning
      agents: [planner, techstack_builder]
      timeout_minutes: 15
      parallel: true

    - name: design
      agents: [architect]
      timeout_minutes: 15

    - name: implementation
      agents: [frontend_dev, backend_dev, infra_engineer]
      timeout_minutes: 60
      parallel: true
      worktree_isolation: true

    - name: review
      agents: [code_reviewer]
      timeout_minutes: 15

    - name: testing
      agents: [tester]
      timeout_minutes: 15

    - name: debug_fix
      agents: [debugger]
      timeout_minutes: 30
      max_iterations: 3
      loop: true

    - name: delivery
      agents: [github]
      timeout_minutes: 10
```

### Review-Only Pipeline

```yaml
# configs/pipelines/review_only.yaml
pipeline:
  name: review_only
  description: "Review existing codebase (5 agents)"
  phases:
    - name: analysis
      agents: [researcher]
      timeout_minutes: 10

    - name: review
      agents: [security_auditor, code_reviewer, accessibility, performance]
      timeout_minutes: 45
      parallel: true

    - name: reporting
      agents: [doc_writer]
      timeout_minutes: 15
```

### Mobile Pipeline

```yaml
# configs/pipelines/mobile.yaml
pipeline:
  name: mobile_app
  description: "Mobile-focused pipeline (15 agents)"
  phases:
    - name: ideation
      agents: [brainstorming]
      timeout_minutes: 15

    - name: planning
      agents: [planner, techstack_builder]
      timeout_minutes: 20
      parallel: true

    - name: research
      agents: [researcher]
      timeout_minutes: 15

    - name: design
      agents: [architect, designer, database, api_gateway]
      timeout_minutes: 30
      requires_approval: true
      parallel: true

    - name: implementation
      agents: [backend_dev, mobile_dev, infra_engineer, integrations]
      timeout_minutes: 90
      parallel: true
      worktree_isolation: true

    - name: review
      agents: [security_auditor, code_reviewer, accessibility]
      timeout_minutes: 30
      parallel: true

    - name: testing
      agents: [tester]
      timeout_minutes: 30

    - name: debug_fix
      agents: [debugger]
      timeout_minutes: 45
      max_iterations: 5
      loop: true

    - name: delivery
      agents: [devops, github, doc_writer]
      timeout_minutes: 20
      parallel: true
```

### Brownfield / Modernization Pipeline

```yaml
# configs/pipelines/brownfield.yaml
pipeline:
  name: brownfield_modernization
  description: "Modernize existing codebase (14 agents)"
  phases:
    - name: analysis
      agents: [researcher]
      timeout_minutes: 30
      settings:
        analyze_existing_codebase: true
        generate_dependency_report: true

    - name: planning
      agents: [planner, techstack_builder]
      timeout_minutes: 30
      parallel: true
      settings:
        brownfield_mode: true
        preserve_existing_architecture: true

    - name: design
      agents: [architect, database, api_gateway]
      timeout_minutes: 30
      requires_approval: true
      parallel: true
      settings:
        migration_strategy: true
        backward_compatibility: true

    - name: review_existing
      agents: [security_auditor, code_reviewer, performance]
      timeout_minutes: 30
      parallel: true

    - name: implementation
      agents: [frontend_dev, backend_dev, middleware_dev, infra_engineer]
      timeout_minutes: 120
      parallel: true
      worktree_isolation: true
      settings:
        incremental_migration: true

    - name: testing
      agents: [tester]
      timeout_minutes: 30
      settings:
        regression_focus: true

    - name: debug_fix
      agents: [debugger]
      timeout_minutes: 60
      max_iterations: 5
      loop: true

    - name: delivery
      agents: [devops, github, doc_writer]
      timeout_minutes: 20
      parallel: true
```

---

*End of Agent Catalog Document*
