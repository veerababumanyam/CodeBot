# CodeBot Agent Workflows

**Version:** 2.3
**Date:** 2026-03-18
**Status:** Draft
**Author:** Architecture Team
**Related:** [PRD v2.1](../prd/PRD.md) | [MASFactory (arXiv:2603.06007)](https://github.com/BUPT-GAMMA/MASFactory)

---

## Table of Contents

1. [Workflow Overview](#1-workflow-overview)
2. [End-to-End Pipeline Workflow](#2-end-to-end-pipeline-workflow)
3. [Phase Workflows (Detailed)](#3-phase-workflows-detailed)
   - 3.1 [Brainstorming Phase](#31-brainstorming-phase)
   - 3.2 [Research Phase](#32-research-phase)
   - 3.3 [Architecture & Design Phase](#33-architecture--design-phase)
   - 3.4 [Planning & Configuration Phase](#34-planning--configuration-phase)
   - 3.5 [Implementation Phase](#35-implementation-phase)
   - 3.6 [Quality Assurance Phase](#36-quality-assurance-phase)
   - 3.7 [Testing Phase](#37-testing-phase)
   - 3.8 [Debug & Fix Loop](#38-debug--fix-loop)
   - 3.9 [Documentation & Knowledge Phase](#39-documentation--knowledge-phase)
   - 3.10 [Deployment & Delivery Phase](#310-deployment--delivery-phase)
   - 3.11 [Failure Mode Analysis per Phase](#311-failure-mode-analysis-per-phase)
4. [Agent Interaction Patterns](#4-agent-interaction-patterns)
   - 4.1 [State Flow Pattern](#41-state-flow-pattern)
   - 4.2 [Message Flow Pattern](#42-message-flow-pattern)
   - 4.3 [Control Flow Pattern](#43-control-flow-pattern)
   - 4.4 [Collaboration Pattern](#44-collaboration-pattern)
   - 4.5 [Supervision Pattern](#45-supervision-pattern)
   - 4.6 [Agent Lifecycle Workflow](#46-agent-lifecycle-workflow)
5. [Project Type Workflows](#5-project-type-workflows)
   - 5.1 [Greenfield Workflow](#51-greenfield-workflow)
   - 5.2 [Inflight Workflow](#52-inflight-workflow)
   - 5.3 [Brownfield Workflow](#53-brownfield-workflow)
6. [Error Handling & Recovery Workflows](#6-error-handling--recovery-workflows)
   - 6.1 [Agent Failure Recovery](#61-agent-failure-recovery)
   - 6.2 [Pipeline Failure Recovery](#62-pipeline-failure-recovery)
   - 6.3 [LLM Rate Limiting Handling](#63-llm-rate-limiting-handling)
   - 6.4 [Error Taxonomy](#64-error-taxonomy)
   - 6.5 [Dead Letter Queue (DLQ) Workflow](#65-dead-letter-queue-dlq-workflow)
   - 6.6 [Circuit Breaker Workflow](#66-circuit-breaker-workflow)
7. [Human-in-the-Loop Workflows](#7-human-in-the-loop-workflows)
   - 7.1 [Approval Gates](#71-approval-gates)
   - 7.2 [Clarification Requests](#72-clarification-requests)
   - 7.3 [Real-time Collaboration](#73-real-time-collaboration)
8. [Multi-LLM Routing Workflows](#8-multi-llm-routing-workflows)
9. [Sequence Diagrams](#9-sequence-diagrams)
   - 9.1 [Complete Pipeline Execution](#91-complete-pipeline-execution)
   - 9.2 [Debug/Fix Loop](#92-debugfix-loop)
   - 9.3 [Agent Collaboration](#93-agent-collaboration)
   - 9.4 [Human Approval Flow](#94-human-approval-flow)
   - 9.5 [Deployment Flow](#95-deployment-flow)
- [Appendix A: Cross-Cutting Concerns](#appendix-a-cross-cutting-concerns)
- [Appendix B: Complete Pipeline Timing Estimate](#appendix-b-complete-pipeline-timing-estimate)
- [Appendix C: Agent Registry](#appendix-c-agent-registry)

---

## 1. Workflow Overview

### 1.1 Graph-Centric Pipeline Architecture

CodeBot uses a **directed computation graph** where nodes represent agents and edges represent
dependencies and message flows. This architecture is inspired by MASFactory (arXiv:2603.06007),
which defines multi-agent systems as composable graphs of specialized workers.

```
                        +---------------------------+
                        |   COMPUTATION GRAPH        |
                        |                           |
  User Input ---------> |  [Brainstorm]             |
                        |       |                   |
                        |       v                   |
                        |  [Research]               |
                        |       |                   |
                        |       v                   |
                        |  [Architect] [Design] [DB]|
                        |  [API GW]  (parallel)     |
                        |       |        |      |   |
                        |       v        v      v   |
                        |  [Plan] [TechStack]       |
                        |  [Template] (sequential)  |
                        |              |            |
                        |    +---------+---------+  |
                        |    |    |    |    |     |  |
                        |    v    v    v    v     v  |
                        |   FE   BE   MW  Mobile Inf|
                        |    |    |    |    |     |  |
                        |    +---------+---------+  |
                        |              |            |
                        |    +---------+---------+  |
                        |    v    v    v    v     v  |
                        |  Review Sec A11y i18n Perf|
                        |    +---------+---------+  |
                        |              |            |
                        |              v            |
                        |          [Testing]        |
                        |              |            |
                        |         +----+----+       |
                        |         |         |       |
                        |       pass      fail      |
                        |         |         |       |
                        |         v         v       |
                        |      [Docs]   [Debug]--+  |
                        |         |         |    |  |
                        |         v         +----+  |
                        |     [Deploy/Deliver]      |
                        +---------------------------+
                                   |
                                   v
                            Delivered Application
```

**Key Principles:**

- **Nodes are agents.** Each node in the graph is a specialized agent with defined inputs, outputs, and capabilities.
- **Edges are dependencies.** An edge from A to B means B depends on A's output. B will not execute until A completes and passes its quality gate.
- **The graph is dynamic.** The Orchestrator can add, remove, or rewire edges at runtime based on project requirements (e.g., skip Mobile Developer if no mobile target is specified).
- **Execution follows topological order.** Agents with no unmet dependencies execute in parallel. Agents with dependencies wait until all upstream agents complete.

### 1.2 Phase-Based Execution with Quality Gates

The pipeline is organized into sequential phases. Each phase has an entry gate (preconditions),
execution logic, and an exit gate (quality checks). A phase cannot advance until its exit gate passes.

```
 PHASE EXECUTION MODEL:

 +----------+     +-----------+     +----------+     +-----------+
 |  ENTRY   |---->| EXECUTION |---->|  EXIT    |---->|   NEXT    |
 |  GATE    |     |           |     |  GATE    |     |   PHASE   |
 +----------+     +-----------+     +----------+     +-----------+
      |                                   |
      | preconditions                     | quality checks
      | not met                           | not met
      |                                   |
      v                                   v
 [BLOCK / WAIT]                    [REMEDIATE / RETRY]
                                          |
                                          v
                                   [RE-EVALUATE GATE]
                                          |
                                     +----+----+
                                     |         |
                                   pass      fail (max retries)
                                     |         |
                                     v         v
                                  [NEXT]   [ESCALATE TO HUMAN]
```

**Gate Types:**

| Gate | Phase Boundary | Type | Description |
|------|---------------|------|-------------|
| G1 | Brainstorming -> Research | Approval | User confirms refined requirements |
| G2 | Research -> Architecture | Automatic | Research report completeness check |
| G3 | Architecture -> Planning | Approval | User approves system architecture |
| G4 | Planning -> Implementation | Approval | User confirms plan + tech stack selections |
| G5 | Implementation -> Quality Assurance | Automatic | All agents complete, code compiles |
| G6 | Quality Assurance -> Testing | Automatic | No critical/blocker findings |
| G7 | Testing -> Debug/Fix | Automatic | Test results collected |
| G8 | Debug/Fix -> Documentation | Automatic | All tests pass, coverage met |
| G9 | Documentation -> Deployment | Automatic | Documentation completeness check |
| G10 | Deployment -> Delivery | Automatic | Deployment health checks pass |

### 1.3 Parallel vs Sequential Execution Strategies

```
 EXECUTION STRATEGY:

 Sequential:  A ---> B ---> C ---> D
              (each waits for the previous)

 Parallel:    A --+
               B --+--> Merge ---> D
               C --+
              (independent agents run simultaneously)

 Fan-out /    A --+--> B1 --+
 Fan-in:          +--> B2 --+--> C
                  +--> B3 --+
              (one agent triggers many, results converge)

 Pipeline:    A1 -+-> B1     (A streams output to B as it produces it;
              A2 -+-> B2      used for real-time code streaming)
```

| Stage | Phase | Strategy | Parallelism Details |
|-------|-------|----------|-------------------|
| S0 | Project Initialization | Sequential | Orchestrator + GitHub Agent setup |
| S1 | Brainstorming | Sequential | Single agent, interactive with user |
| S2 | Research | Internal parallel | Multiple research queries run concurrently |
| S3 | Architecture & Design | **Fan-out / Fan-in** | Architect, Designer, DB Agent, API Gateway work in parallel |
| S4 | Planning & Configuration | Sequential | Planner + TechStack Builder + Template Agent pipeline |
| S5 | Implementation | **Full parallel** | FE, BE, MW, Mobile, Infra, Integrations in isolated git worktrees |
| S6 | Quality Assurance | **Full parallel** | Code Reviewer, Security Auditor, A11y, i18n, Perf run simultaneously |
| S7 | Testing | Internal parallel | Unit, integration, E2E, UI component, smoke, regression, mutation suites run concurrently |
| S8 | Debug & Stabilization | Sequential per issue | Issues fixed one at a time to avoid conflicts |
| S9 | Documentation & Knowledge | Internal parallel | Doc Writer, Skill/Hook/Tool Creators work concurrently |
| S10 | Deployment & Delivery | Sequential | Pipeline stages must execute in order |

### 1.4 Human-in-the-Loop Intervention Points

```
 INTERVENTION SPECTRUM:

 Fully Autonomous <---------------------------------------------> Fully Manual
       |                    |                    |                    |
  Auto-approve         Notify only          Approval gate       Block until
  all gates            (can override)       (timeout=auto)      human acts
       |                    |                    |                    |
  "autopilot"          "supervised"          "collaborative"      "manual"
```

| Intervention Point | Gate | Trigger | Required? | Timeout Action | Mode Override |
|--------------------|------|---------|-----------|----------------|---------------|
| Requirements Refinement | G1 | Brainstorming complete (S1) | Configurable (default: yes) | Auto-accept after 15 min | autopilot: skip |
| Architecture Approval | G3 | Architecture phase complete (S3) | Configurable (default: yes) | Auto-approve after 30 min | autopilot: skip |
| Plan + Tech Stack Approval | G4 | Planning & configuration complete (S4) | Configurable (default: yes) | Auto-approve after 30 min | autopilot: skip |
| Requirement Clarification | -- | Ambiguous requirements detected | Always | Skip ambiguous items, document assumptions | N/A |
| Debug Escalation | -- | 3 failed fix iterations (S8) | Always | Pause pipeline, alert user | N/A |
| Security Exception | -- | Critical vulnerability found (S6) | Always | Block delivery until resolved | N/A |
| Deployment Approval | G10 | Pre-production deploy (S10) | Configurable (default: yes) | Auto-approve after 30 min | autopilot: skip |
| Code Review Override | -- | Major architectural issue flagged (S6) | Optional | Auto-accept suggestions | N/A |

### 1.5 Checkpoint and Resume Mechanism

Every phase transition creates a checkpoint. If the pipeline crashes, it can resume from the last
successful checkpoint without repeating completed work.

```
 CHECKPOINT ARCHITECTURE:

 .codebot/
   checkpoints/
     +--- session_<uuid>/
     |      +--- manifest.json              (session metadata, current phase)
     |      +--- phase_00_initialization.json (project setup, repo creation)
     |      +--- phase_01_brainstorming.json (refined requirements)
     |      +--- phase_02_research.json      (research report)
     |      +--- phase_03_architecture.json  (arch docs + schemas + design)
     |      +--- phase_04_planning.json      (plan + task graph + tech stack + scaffold)
     |      +--- phase_05_implementation/    (per-agent snapshots)
     |      |       +--- frontend.json
     |      |       +--- backend.json
     |      |       +--- middleware.json
     |      |       +--- mobile.json
     |      |       +--- infrastructure.json
     |      |       +--- integrations.json
     |      +--- phase_06_quality.json       (review + security + a11y + i18n reports)
     |      +--- phase_07_testing.json       (test results + coverage)
     |      +--- phase_08_debug_fix.json     (fix history + iterations)
     |      +--- phase_09_documentation.json (docs + knowledge artifacts)
     |      +--- phase_10_deployment.json    (deploy config + status + handoff)
     +--- latest -> session_<uuid>/          (symlink to latest session)

 RESUME BEHAVIOR:
 1. On restart, read manifest.json to find current_phase
 2. Restore git state from checkpoint commit SHA
 3. Skip all phases before current_phase
 4. Re-run current_phase from the beginning (phases are idempotent)
 5. Continue pipeline from there

 CHECKPOINT DATA (per phase):
 {
   "phase": "planning",
   "status": "completed",
   "started_at": "2026-03-18T10:00:00Z",
   "completed_at": "2026-03-18T10:03:22Z",
   "git_commit_sha": "a1b2c3d4",
   "agent_states": { ... },
   "output_artifacts": [ ... ],
   "metrics": {
     "tokens_used": 12450,
     "cost_usd": 0.23,
     "duration_ms": 202000
   }
 }
```

---

## 2. End-to-End Pipeline Workflow

### 2.1 Complete Pipeline Flow

```
 User Input --> Initialization --> Brainstorming --> Research --> Architecture & Design -->
 Planning & Configuration --> Implementation --> Quality Assurance --> Testing --> Debug/Fix -->
 Documentation --> Deployment & Delivery
```

### 2.2 Complete Sequence Diagram

```
 User              Orchestrator       Pipeline Phases              Git/Storage
  |                      |                     |                          |
  |  Submit idea/PRD     |                     |                          |
  |--------------------->|                     |                          |
  |                      |  S0: INITIALIZATION |                          |
  |                      |  Init project repo  |                          |
  |                      |----------------------------------------------->|
  |                      |                     |                     repo created
  |                      |                     |                          |
  |                      |  S1: BRAINSTORMING  |                          |
  |                      |-------------------->|                          |
  |  Interactive Q&A     |                     |                          |
  |<-------------------->|                     |                          |
  |                      |  Requirements refined                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |  [GATE G1] Confirm   |                     |                          |
  |  requirements?       |                     |                          |
  |<---------------------|                     |                          |
  |  Confirmed           |                     |                          |
  |--------------------->|                     |                          |
  |                      |                     |                          |
  |                      |  S2: RESEARCH       |                          |
  |                      |-------------------->|                          |
  |                      |  Research complete  |                          |
  |                      |<--------------------|                          |
  |                      |  [GATE G2]          |                          |
  |                      |                     |                          |
  |                      |  S3: ARCHITECTURE & DESIGN (parallel)          |
  |                      |-------------------->| Architect --|            |
  |                      |-------------------->| Designer  --|            |
  |                      |-------------------->| DB Agent  --|            |
  |                      |-------------------->| API GW    --|            |
  |                      |  All outputs ready  |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |  [GATE G3] Approve   |                     |                          |
  |  architecture?       |                     |                          |
  |<---------------------|                     |                          |
  |  Approved            |                     |                          |
  |--------------------->|                     |                          |
  |                      |                     |                          |
  |                      |  S4: PLANNING & CONFIGURATION                  |
  |                      |-------------------->|                          |
  |  Clarification Q?    |                     |                          |
  |<---------------------|                     |                          |
  |  Answers             |                     |                          |
  |--------------------->|                     |                          |
  |                      |  Plan + stack ready |                          |
  |                      |<--------------------|                          |
  |  Select tech stack   |                     |                          |
  |<-------------------->|                     |                          |
  |  Select templates    |                     |                          |
  |<-------------------->|                     |                          |
  |                      |  Scaffold generated |                          |
  |                      |<--------------------|                          |
  |                      |  Commit scaffold    |                          |
  |                      |----------------------------------------------->|
  |                      |                     |                          |
  |  [GATE G4] Approve   |                     |                          |
  |  plan + tech stack?  |                     |                          |
  |<---------------------|                     |                          |
  |  Approved            |                     |                          |
  |--------------------->|                     |                          |
  |                      |                     |                          |
  |                      |  S5: IMPLEMENTATION (PARALLEL)                 |
  |                      |-------------------->| Frontend --|             |
  |                      |-------------------->| Backend  --|-- worktrees |
  |                      |-------------------->| Middleware--|             |
  |                      |-------------------->| Mobile   --|             |
  |                      |-------------------->| Infra    --|             |
  |                      |-------------------->| Integrations-|           |
  |                      |  All agents done    |                          |
  |                      |<--------------------|                          |
  |                      |  Merge worktrees    |                          |
  |                      |----------------------------------------------->|
  |                      |                     |                     merged
  |                      |                     |                          |
  |                      |  S6: QUALITY ASSURANCE (PARALLEL)              |
  |                      |-------------------->| Code Review --|          |
  |                      |-------------------->| Security Audit|          |
  |                      |-------------------->| A11y Check ---|          |
  |                      |-------------------->| i18n Check ---|          |
  |                      |-------------------->| Perf Check ---|          |
  |                      |  Reviews complete   |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |                      |  S7: TESTING        |                          |
  |                      |-------------------->|                          |
  |                      |  Tests complete     |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |                      |  S8: DEBUG & STABILIZATION LOOP                |
  |                      |-------------------->|                          |
  |                      |  (iterates until    |                          |
  |                      |   all pass or       |                          |
  |                      |   escalate)         |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |  [GATE] Human needed?|                     |                          |
  |<------(if stuck)-----|                     |                          |
  |                      |                     |                          |
  |                      |  S9: DOCUMENTATION & KNOWLEDGE                 |
  |                      |-------------------->|                          |
  |                      |  Docs complete      |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |                      |  S10: DEPLOYMENT & DELIVERY                    |
  |                      |-------------------->|                          |
  |                      |  Deployed           |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |  [GATE G10] Approve  |                     |                          |
  |  deployment?         |                     |                          |
  |<---------------------|                     |                          |
  |  Approved            |                     |                          |
  |--------------------->|                     |                          |
  |                      |                     |                          |
  |                      |  Package ready      |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |  Delivery handoff    |                     |                          |
  |<---------------------|                     |                          |
  |                      |                     |                          |
```

### 2.3 Phase Transitions and Gates

```
 State Machine: Pipeline Phases

  [START]
     |
     v
 +--------------+
 |INITIALIZATION|  (S0: Orchestrator + GitHub Agent)
 +--------------+
     | project repo created
     v
 +--------------+
 |BRAINSTORMING |  (S1: interactive with user)
 +--------------+
     | refined requirements
     v
 +----------+   GATE G1: Requirements Confirmed
 |GATE_REQS |---[rejected]---> BRAINSTORMING (iterate)
 +----------+
     | confirmed
     v
 +--------+
 |RESEARCH|  (S2: technology evaluation)
 +--------+
     | ok
     v
 +----------+   GATE G2: Research Completeness
 |GATE_RES  |---[incomplete]---> RESEARCH (extend)
 +----------+
     | complete
     v
 +---------------------+
 |ARCHITECTURE & DESIGN|  (S3: parallel sub-agents)
 +---------------------+
     | ok
     v
 +---------+   GATE G3: Architecture Approval
 |GATE_ARCH|---[rejected]---> ARCHITECTURE (revise)
 +---------+
     | approved
     v
 +------------------------+    fail     +----------+
 |PLANNING & CONFIGURATION|----------->|ESCALATION|---> [HUMAN]
 +------------------------+             +----------+
     | ok (S4: plan + tech stack + scaffold)
     v
 +----------+   GATE G4: Plan + Tech Stack Approval
 |GATE_PLAN |---[rejected]---> PLANNING (revise)
 +----------+
     | approved
     v
 +--------------+
 |IMPLEMENTATION|  (S5: parallel sub-states: FE, BE, MW, Mobile, Infra, Integrations)
 +--------------+
     | all merged
     v
 +-----------------+
 |QUALITY ASSURANCE|  (S6: parallel sub-states: Code, Security, A11y, i18n, Perf)
 +-----------------+
     | ok (no critical/blocker findings)
     v
 +-------+
 |TESTING|  (S7: all test suites)
 +-------+
     | results
     v
 +-------------------+
 |DEBUG_STABILIZATION|<-----+  (S8: sequential fix loop)
 +-------------------+      |
     |            |
     |--[pass]--->|--- (loop if regressions)
     |            |
     |--[fail, iteration < 3]---+
     |
     |--[fail, iteration >= 3]---> [HUMAN ESCALATION]
     |
     |--[all pass]
     v
 +-------------------------+
 |DOCUMENTATION & KNOWLEDGE|  (S9: Doc Writer, Skill/Hook/Tool Creators)
 +-------------------------+
     | ok
     v
 +---------------------+
 |DEPLOYMENT & DELIVERY|  (S10: DevOps, Infra, PM)
 +---------------------+
     | ok
     v
 +----------+   GATE G10: Deployment Approval (optional)
 |GATE_DEPLOY|---[rejected]---> DEPLOYMENT (rollback)
 +----------+
     | approved
     v
  [END]
```

### 2.4 Phase Transition Details

For each transition, the following data flows between phases:

| From | To | Trigger | Data Flowing | Gate | On Failure |
|------|----|---------|-------------|------|------------|
| User Input | Initialization (S0) | User submits idea/PRD | Raw requirements, user preferences | None | N/A |
| Initialization | Brainstorming (S1) | Repo created | Project repo, session metadata | None | N/A |
| Brainstorming | Research (S2) | Requirements refined | Refined PRD, risk assessment, tech recs | G1: User confirms | Re-enter brainstorming |
| Research | Architecture (S3) | Research complete | Research report, dep manifest, patterns | G2: Completeness | Extend research |
| Architecture | Planning (S4) | Architecture approved | C4 docs, API specs, schemas, wireframes | G3: User approves | Revise architecture |
| Planning | Implementation (S5) | Plan + stack confirmed | Task graph, tech config, scaffold | G4: User approves | Revise plan/stack |
| Implementation | Quality Assurance (S6) | All agents complete | Complete codebase, merged branches | G5: Compiles | Fix compilation |
| Quality Assurance | Testing (S7) | No critical findings | Review reports, remediation items | G6: No blockers | Fix blockers |
| Testing | Debug/Fix (S8) | Tests collected | Test results, coverage, failures | G7: Auto | N/A |
| Debug/Fix | Documentation (S9) | All tests pass | Fixed codebase, regression tests | G8: Coverage met | Continue fixing |
| Documentation | Deployment (S10) | Docs complete | Documentation, knowledge artifacts | G9: Completeness | Re-generate |
| Deployment | End | Package ready | Deployed app, docs, handoff report | G10: Optional | Rollback |

### 2.5 Parallel Execution Opportunities

| Stage | Phase | Parallelism | Details |
|-------|-------|-------------|---------|
| S0 | Initialization | Sequential | Orchestrator + GitHub Agent setup |
| S1 | Brainstorming | Sequential | Single Brainstorming Agent, interactive with user |
| S2 | Research | Internal parallelism | Multiple research queries can run concurrently |
| S3 | Architecture & Design | **Fan-out** | Architect, Designer, DB Agent, API Gateway work in parallel |
| S4 | Planning & Configuration | Sequential | Planner + TechStack Builder + Template Agent pipeline |
| S5 | Implementation | **Full parallelism** | 6 agents in isolated worktrees (FE, BE, MW, Mobile, Infra, Integrations) |
| S6 | Quality Assurance | **Full parallelism** | Code Reviewer + Security Auditor + A11y + i18n + Perf simultaneously |
| S7 | Testing | Internal parallelism | Unit, integration, E2E, UI component, smoke, regression, mutation suites run concurrently |
| S8 | Debug & Stabilization | Sequential per issue | Issues prioritized and fixed one at a time |
| S9 | Documentation & Knowledge | Internal parallelism | Doc Writer, Skill/Hook/Tool Creators work concurrently |
| S10 | Deployment & Delivery | Sequential | Pipeline stages must execute in order |

---

## 3. Phase Workflows (Detailed)

### 3.1 Brainstorming Phase

**Description:** The Brainstorming Phase is the first point of contact between the user and CodeBot. The Brainstorming Agent takes a raw idea, requirement, or vague description and expands it into a well-defined, actionable set of requirements through interactive exploration.

**Goals:**
- Explore the idea space and identify alternative approaches
- Surface hidden requirements, edge cases, and constraints
- Assess technical feasibility and risk
- Produce a refined requirements document ready for planning

**Agent(s) Involved:** Brainstorming Agent, Orchestrator

**Input:**
```json
{
  "user_input": {
    "type": "idea | prd | description | reference_url",
    "content": "Raw user input text or document",
    "preferences": {
      "platform_targets": ["web", "mobile", "desktop"],
      "budget_constraints": "string",
      "timeline_constraints": "string",
      "tech_preferences": ["React", "Node.js"]
    }
  }
}
```

**Output:**
```json
{
  "refined_requirements": {
    "project_name": "string",
    "project_description": "string",
    "core_features": [
      {
        "id": "F001",
        "name": "User Authentication",
        "description": "...",
        "priority": "must-have | should-have | nice-to-have",
        "complexity": "low | medium | high"
      }
    ],
    "non_functional_requirements": {
      "performance": "...",
      "scalability": "...",
      "security": "...",
      "accessibility": "WCAG 2.1 AA"
    },
    "platform_targets": ["web-spa", "ios-native"],
    "user_personas": [ ... ],
    "constraints": [ ... ]
  },
  "alternative_approaches": [
    {
      "name": "Approach A: Monolithic SPA",
      "pros": ["..."],
      "cons": ["..."],
      "recommended": true
    }
  ],
  "tech_recommendations": {
    "suggested_stack": { ... },
    "rationale": "..."
  },
  "risk_assessment": [
    {
      "risk": "Third-party API rate limits",
      "severity": "medium",
      "mitigation": "Implement caching layer"
    }
  ],
  "open_questions": [
    "Should the app support offline mode?"
  ]
}
```

**Step-by-Step Workflow:**

```
 1. User submits initial idea/PRD
 2. Brainstorming Agent analyzes the input
 3. Agent generates clarifying questions
 4. User answers questions (interactive Q&A loop)
 5. Agent explores alternative approaches
 6. Agent identifies risks and challenges
 7. Agent produces refined requirements document
 8. User reviews and confirms requirements
 9. Checkpoint saved, transition to Research
```

**Sequence Diagram:**

```
 User            Orchestrator      Brainstorming       Knowledge
                                    Agent               Base
  |                   |                |                   |
  | Submit idea       |                |                   |
  |------------------>|                |                   |
  |                   | Create session |                   |
  |                   |---+            |                   |
  |                   |<--+            |                   |
  |                   |                |                   |
  |                   | Analyze input  |                   |
  |                   |--------------->|                   |
  |                   |                |  Lookup similar   |
  |                   |                |  projects         |
  |                   |                |------------------>|
  |                   |                |  Similar projects |
  |                   |                |<------------------|
  |                   |                |                   |
  |                   |                | Generate Qs       |
  |                   |                |---+               |
  |                   |                |<--+               |
  |                   |                |                   |
  | Clarifying Qs     |                |                   |
  |<------------------|<---------------|                   |
  |                   |                |                   |
  | Answers           |                |                   |
  |------------------>|--------------->|                   |
  |                   |                |                   |
  |                   |                | (loop until       |
  |                   |                |  requirements     |
  |                   |                |  are clear)       |
  |                   |                |                   |
  |                   |                | Generate          |
  |                   |                | alternatives      |
  |                   |                |---+               |
  |                   |                |<--+               |
  |                   |                |                   |
  |                   |                | Risk assessment   |
  |                   |                |---+               |
  |                   |                |<--+               |
  |                   |                |                   |
  |                   | Refined reqs   |                   |
  |                   |<---------------|                   |
  | Review reqs       |                |                   |
  |<------------------|                |                   |
  |                   |                |                   |
  | Confirm / Edit    |                |                   |
  |------------------>|                |                   |
  |                   | [GATE G1]      |                   |
  |                   | Save checkpoint|                   |
  |                   |---+            |                   |
  |                   |<--+            |                   |
```

**Decision Points:**
- If user input is a complete PRD: skip most Q&A, validate and refine
- If user input is vague: enter deep Q&A mode (up to 10 rounds)
- If multiple viable approaches exist: present comparison matrix to user
- If critical risks identified: flag for user attention before proceeding

**Error Handling:**
- User unresponsive for >15 min: send reminder notification
- User unresponsive for >60 min: save state, pause session
- LLM failure during analysis: retry with fallback model
- Input too vague after 5 Q&A rounds: suggest starting from a template

**Quality Gate G1: Requirements Confirmation**
- All core features have priority assignments
- At least one platform target specified
- No unresolved critical open questions
- User has explicitly confirmed the requirements

---

### 3.2 Research Phase

**Description:** The Researcher Agent investigates technologies, patterns, libraries, and reference implementations relevant to the project. It evaluates dependencies for security, licensing, and maintenance health. This phase runs AFTER brainstorming and BEFORE architecture, ensuring design decisions are informed by thorough research.

**Goals:**
- Evaluate technology choices for the project
- Find reference implementations and best practices
- Assess dependency health (security, licensing, maintenance)
- Recommend architectural patterns

**Agent(s) Involved:** Researcher

**Input:**
```json
{
  "refined_requirements": { },
  "tech_recommendations": { },
  "constraints": {
    "licensing": "MIT | Apache-2.0 | any-oss",
    "security_requirements": "SOC2 | HIPAA | none",
    "min_maintenance_score": 0.7
  }
}
```

**Output:**
```json
{
  "research_report": {
    "technology_evaluations": [
      {
        "category": "frontend_framework",
        "evaluated": [
          {
            "name": "Next.js 15",
            "version": "15.2.0",
            "score": 0.92,
            "pros": ["SSR support", "App Router", "Built-in optimization"],
            "cons": ["Learning curve for App Router"],
            "license": "MIT",
            "security_advisories": 0,
            "maintenance_score": 0.95,
            "last_release": "2026-02-15"
          }
        ],
        "recommendation": "Next.js 15"
      }
    ],
    "dependency_manifest": {
      "production": [
        { "name": "next", "version": "^15.2.0", "license": "MIT", "health": "healthy" }
      ],
      "development": [ ]
    },
    "pattern_recommendations": [
      {
        "pattern": "Repository Pattern",
        "rationale": "Decouples data access from business logic",
        "reference": "https://..."
      }
    ],
    "reference_implementations": [
      {
        "name": "T3 Stack Example",
        "url": "https://...",
        "relevance": 0.85
      }
    ],
    "security_findings": [ ],
    "licensing_conflicts": [ ]
  }
}
```

**Step-by-Step Workflow:**

```
 1. Receive refined requirements and tech recommendations from Brainstorming
 2. Researcher identifies technology categories to evaluate
 3. For each category, research top 3-5 options
 4. Evaluate each option against criteria:
    - Compatibility with other chosen technologies
    - Community size and activity
    - Security track record
    - License compatibility
    - Performance benchmarks
 5. Run dependency security scan (npm audit, Snyk-style)
 6. Check license compatibility across all dependencies
 7. Find reference implementations for key patterns
 8. Compile research report
 9. [GATE G2] Report completeness validation
 10. Checkpoint saved, transition to Architecture & Design
```

**Sequence Diagram:**

```
 Orchestrator      Researcher         Web/APIs        Vuln DB       License DB
     |                 |                  |               |              |
     | Start research  |                  |               |              |
     |---------------->|                  |               |              |
     |                 | Identify categories              |              |
     |                 |---+              |               |              |
     |                 |<--+              |               |              |
     |                 |                  |               |              |
     |                 | Search tech options              |              |
     |                 |----------------->|               |              |
     |                 |  Results         |               |              |
     |                 |<-----------------|               |              |
     |                 |                  |               |              |
     |                 | Check vulnerabilities            |              |
     |                 |--------------------------------->|              |
     |                 |  CVE data        |               |              |
     |                 |<---------------------------------|              |
     |                 |                  |               |              |
     |                 | Check licenses   |               |              |
     |                 |----------------------------------------------->|
     |                 |  License data    |               |              |
     |                 |<-----------------------------------------------|
     |                 |                  |               |              |
     |                 | Compile report   |               |              |
     |                 |---+              |               |              |
     |                 |<--+              |               |              |
     |                 |                  |               |              |
     | Research report |                  |               |              |
     |<----------------|                  |               |              |
     | [GATE G2]       |                  |               |              |
```

**Error Handling:**
- Web search fails: use cached/local knowledge base
- Vulnerability database unavailable: flag as "unverified" and continue
- No viable option for a technology category: escalate to user with alternatives

**Quality Gate G2: Research Completeness**
- All technology categories have at least one evaluated option
- No unresolved licensing conflicts
- No critical unpatched vulnerabilities in recommended dependencies
- Reference implementations found for key architectural patterns

---

### 3.3 Architecture & Design Phase

**Description:** Multiple agents collaborate in parallel to produce the complete system architecture, UI/UX design, database schemas, and API contracts. This phase uses the fan-out/fan-in pattern.

**Goals:**
- Create system architecture (C4 model: Context, Container, Component, Code)
- Design UI/UX with component hierarchy and design system
- Design database schemas, ERDs, and migrations
- Design API contracts and gateway configuration
- Ensure all outputs are consistent and compatible

**Agent(s) Involved:** Architect, Designer, Database Agent, API Gateway Agent

**Input:**
```json
{
  "plan": { },
  "research_report": { },
  "refined_requirements": { },
  "tech_recommendations": { }
}
```

**Output:**
```json
{
  "architecture": {
    "c4_context": { },
    "c4_container": { },
    "c4_component": { },
    "deployment_topology": { },
    "data_flow_diagrams": [ ],
    "security_architecture": { }
  },
  "design": {
    "design_system": {
      "colors": { },
      "typography": { },
      "spacing": { },
      "components": [ ]
    },
    "wireframes": [ ],
    "component_hierarchy": { },
    "navigation_map": { },
    "responsive_breakpoints": { }
  },
  "database": {
    "erd": { },
    "schemas": [ ],
    "migrations": [ ],
    "seed_data": { },
    "indexes": [ ]
  },
  "api": {
    "openapi_spec": { },
    "graphql_schema": { },
    "gateway_config": {
      "rate_limiting": { },
      "auth_config": { },
      "cors_config": { },
      "versioning_strategy": "url | header"
    },
    "endpoint_catalog": [ ]
  }
}
```

**Step-by-Step Workflow:**

```
 1. Orchestrator fans out to 4 agents in parallel:
    a. Architect: System architecture (C4 model)
    b. Designer: UI/UX design and component hierarchy
    c. Database Agent: Schema design, ERDs, migrations
    d. API Gateway Agent: API contracts and gateway config
 2. Each agent receives the same input context
 3. Agents work independently but share a coordination channel
 4. Cross-agent coordination points:
    a. Architect publishes data models -> DB Agent consumes
    b. Architect publishes service boundaries -> API GW Agent consumes
    c. Designer publishes component list -> Architect validates feasibility
    d. API GW Agent publishes endpoints -> Designer maps to UI flows
 5. Orchestrator collects all outputs
 6. Orchestrator runs consistency validation:
    a. API endpoints match UI flows
    b. Database schema supports all API operations
    c. Architecture supports all non-functional requirements
 7. If inconsistencies found: targeted re-work by affected agent(s)
 8. Present architecture to user
 9. [GATE G3] User approves architecture
 10. Checkpoint saved, transition to Planning & Configuration
```

**Parallel Execution Diagram:**

```
                    +-- [Architect] --------> C4 Docs
                    |                         Deployment Topology
                    |
 Orchestrator ------+-- [Designer] ---------> Design System
 (fan-out)          |                         Wireframes
                    |                         Component Hierarchy
                    |
                    +-- [Database Agent] ---> ERD, Schemas
                    |                         Migrations
                    |
                    +-- [API Gateway Agent] -> OpenAPI Spec
                                              Gateway Config

                    |
                    v

              [Orchestrator]  <--- fan-in, consistency check
                    |
                    v
              [GATE G3: User Approval]
```

**Cross-Agent Coordination:**

```
 Architect ----data models----> Database Agent
     |                              |
     |---service boundaries-------->| API Gateway Agent
     |                              |      |
     |<---endpoint catalog----------|------+
     |                              |
 Designer <---API endpoints--------|------+
     |                              |
     |---component list------------>| Architect (feasibility check)
```

**Error Handling:**
- Agent produces inconsistent output: re-run with consistency constraints
- Cross-agent conflict: Orchestrator mediates, Architect has final authority on technical decisions
- User rejects architecture: capture feedback, re-enter phase with constraints
- Timeout on any agent: use partial results, flag incomplete sections

**Quality Gate G3: Architecture Approval**
- C4 context and container diagrams complete
- All API endpoints documented with request/response schemas
- Database schema supports all CRUD operations implied by features
- Design system has at minimum: colors, typography, spacing, core components
- No unresolved cross-agent inconsistencies
- User has approved the architecture direction

---

### 3.4 Planning & Configuration Phase

**Description:** The Planning & Configuration phase combines project planning, technology selection, and scaffold generation into a single cohesive stage. The Planner Agent decomposes the refined requirements into a structured execution plan, the TechStack Builder recommends specific technologies based on the architecture and research outputs, and the Template Agent generates the project scaffold. This phase runs AFTER architecture is approved, ensuring plans are grounded in concrete architectural decisions.

**Goals:**
- Break requirements into implementable tasks
- Create dependency graph with topological ordering
- Identify parallel execution opportunities
- Estimate complexity and timeline
- Finalize technology selections for every layer
- Validate compatibility across all selections
- Select UI/UX templates and design kits
- Generate project scaffold with all boilerplate

**Agent(s) Involved:** Planner, TechStack Builder, Template Agent, Orchestrator

**Input:**
```json
{
  "architecture": { },
  "research_report": { },
  "design": { },
  "user_preferences": {
    "tech_preferences": ["React", "TypeScript"],
    "template_style": "minimal | full-featured | enterprise"
  }
}
```

**Output:**
```json
{
  "tech_stack": {
    "frontend": {
      "framework": "Next.js 15",
      "language": "TypeScript 5.4",
      "state_management": "Zustand",
      "styling": "Tailwind CSS 4",
      "testing": "Vitest + Playwright"
    },
    "backend": {
      "framework": "Hono",
      "language": "TypeScript 5.4",
      "orm": "Drizzle ORM",
      "auth": "Better Auth",
      "testing": "Vitest"
    },
    "database": {
      "primary": "PostgreSQL 16",
      "cache": "Redis 7",
      "search": "none | Typesense"
    },
    "infrastructure": {
      "containerization": "Docker",
      "orchestration": "Docker Compose | Kubernetes",
      "ci_cd": "GitHub Actions",
      "cloud": "Vercel | AWS | GCP"
    },
    "compatibility_matrix": {
      "verified": true,
      "conflicts": []
    }
  },
  "template_selections": {
    "ui_template": {
      "name": "ShadcnUI Dashboard",
      "source": "template_registry",
      "customizations": [ ]
    },
    "project_template": {
      "name": "T3 Stack",
      "includes": ["next.js", "trpc", "drizzle", "tailwind"]
    }
  },
  "scaffold": {
    "structure": { },
    "files_generated": 47,
    "git_commit_sha": "abc123"
  }
}
```

**Step-by-Step Workflow:**

```
 1. TechStack Builder analyzes architecture and research report
 2. TechStack Builder generates tech stack recommendation
    2a. Validates compatibility across all layers
    2b. Checks version compatibility matrix
    2c. Verifies license compliance
 3. Present tech stack recommendation to user
 4. User selects/modifies tech stack
 5. [GATE G4a] User confirms tech stack
 6. Template Agent searches template registry
    6a. Filters by tech stack compatibility
    6b. Filters by design system compatibility
    6c. Ranks by feature coverage and quality
 7. Present template options to user
 8. User selects templates
 9. Template Agent generates scaffold:
    9a. Clone/instantiate project template
    9b. Apply tech stack configuration
    9c. Integrate design system tokens
    9d. Set up development tooling (linters, formatters, git hooks)
    9e. Create initial directory structure
    9f. Generate configuration files
 10. Scaffold committed to repository
 11. [GATE G4] Plan + scaffold validation (compiles, lints pass)
 12. Checkpoint saved, transition to Implementation
```

**Sequence Diagram:**

```
 User          Orchestrator    TechStack       Template        Git
                                Builder         Agent
  |                 |              |               |             |
  |                 | Analyze arch |               |             |
  |                 |------------->|               |             |
  |                 |              | Validate      |             |
  |                 |              | compatibility |             |
  |                 |              |---+           |             |
  |                 |              |<--+           |             |
  |                 |              |               |             |
  |                 | Tech stack   |               |             |
  |                 | recommendation               |             |
  |                 |<-------------|               |             |
  |                 |              |               |             |
  | Review stack    |              |               |             |
  |<----------------|              |               |             |
  | Select/modify   |              |               |             |
  |---------------->|              |               |             |
  |                 | [GATE G4a]   |               |             |
  |                 |              |               |             |
  |                 | Search       |               |             |
  |                 | templates    |               |             |
  |                 |---------------------------->|             |
  |                 |              |  Template     |             |
  |                 |              |  options      |             |
  |                 |<----------------------------|             |
  |                 |              |               |             |
  | Review templates|              |               |             |
  |<----------------|              |               |             |
  | Select template |              |               |             |
  |---------------->|              |               |             |
  |                 |              |               |             |
  |                 | Generate     |               |             |
  |                 | scaffold     |               |             |
  |                 |---------------------------->|             |
  |                 |              |  Scaffold     |             |
  |                 |              |  generated    |             |
  |                 |<----------------------------|             |
  |                 |              |               |             |
  |                 | Commit scaffold              |             |
  |                 |---------------------------------------------->|
  |                 |              |               |         committed
  |                 | [GATE G4]    |               |             |
```

**Decision Points:**
- If user has strong tech preferences: weight those heavily in recommendations
- If compatibility conflict detected: present alternatives with trade-off analysis
- If no suitable template exists: generate custom scaffold from architecture
- If enterprise template selected: include additional security/compliance boilerplate

**Error Handling:**
- Compatibility conflict in tech stack: present alternatives, never proceed with conflicts
- Template generation fails: fall back to minimal scaffold, flag missing features
- User rejects all template options: generate custom scaffold from architecture outputs
- Version mismatch detected post-scaffold: auto-fix versions, re-validate

**Quality Gate G4: Plan + Scaffold Validation**
- Project compiles/builds successfully
- Linting passes with zero errors
- All configuration files are valid
- Directory structure matches architecture specifications
- Development server starts without errors

---

### 3.5 Implementation Phase

**Description:** The Implementation Phase is the core production phase where multiple developer agents work in parallel, each in an isolated git worktree, to build the complete application. The Orchestrator coordinates task assignment and monitors progress in real time.

**Goals:**
- Implement all features defined in the plan
- Maintain code quality and consistency across agents
- Enable parallel development without conflicts
- Stream code to the dashboard in real time

**Agent(s) Involved:** Frontend Developer, Backend Developer, Middleware Developer, Mobile Developer, Infrastructure Engineer, Orchestrator

**Input:**
```json
{
  "plan": { },
  "architecture": { },
  "design": { },
  "database": { },
  "api": { },
  "tech_stack": { },
  "scaffold": { }
}
```

**Output:**
```json
{
  "codebase": {
    "frontend": {
      "files_created": 85,
      "lines_of_code": 12000,
      "worktree_branch": "agent/frontend-dev",
      "commit_count": 23
    },
    "backend": {
      "files_created": 62,
      "lines_of_code": 8500,
      "worktree_branch": "agent/backend-dev",
      "commit_count": 18
    },
    "middleware": { },
    "mobile": { },
    "infrastructure": { }
  },
  "merge_result": {
    "status": "clean | conflicts_resolved | manual_intervention",
    "final_commit_sha": "def456",
    "conflicts_encountered": 0,
    "conflicts_auto_resolved": 0
  }
}
```

**Step-by-Step Workflow:**

```
 1. Orchestrator creates git worktrees for each active developer agent:
    - git worktree add ../worktree-frontend agent/frontend-dev
    - git worktree add ../worktree-backend  agent/backend-dev
    - git worktree add ../worktree-middleware agent/middleware-dev
    - git worktree add ../worktree-mobile   agent/mobile-dev
    - git worktree add ../worktree-infra    agent/infra-dev
 2. Orchestrator assigns task waves from the execution schedule
 3. Each agent receives its task list + context:
    - Architecture docs relevant to its layer
    - API contracts it must implement or consume
    - Design tokens and component specs (for Frontend)
    - Database schemas and migration files (for Backend)
 4. Agents begin implementing tasks in parallel
 5. Each agent commits atomically per task completion
 6. Code is streamed to the dashboard in real time
 7. Orchestrator monitors agent progress:
    - Tracks task completion percentage
    - Detects stalled agents (no commits for >5 min)
    - Monitors token/cost consumption
 8. Cross-agent coordination events:
    - Backend publishes API implementation -> Frontend can integrate
    - Infrastructure publishes deployment config -> All agents can reference
    - Middleware publishes auth middleware -> Backend/Frontend consume
 9. All agents complete their tasks
 10. Orchestrator initiates merge sequence:
     a. Merge infrastructure first (base layer)
     b. Merge backend (depends on infra)
     c. Merge middleware (depends on backend)
     d. Merge frontend (depends on API contracts)
     e. Merge mobile (depends on API contracts)
 11. Resolve any merge conflicts (see 3.5.2)
 12. Run compilation check on merged code
 13. [GATE G5] Code compiles successfully
 14. Checkpoint saved, transition to Quality Assurance
```

**Worktree Isolation Model:**

```
 Repository Structure During Implementation:

 main-repo/                        (main branch - scaffold)
   |
   +-- .git/                       (shared git database)
   |
   +-- worktree-frontend/          (agent/frontend-dev branch)
   |     +-- src/app/              (Next.js pages)
   |     +-- src/components/       (React components)
   |     +-- src/hooks/            (Custom hooks)
   |
   +-- worktree-backend/           (agent/backend-dev branch)
   |     +-- src/api/              (API routes)
   |     +-- src/services/         (Business logic)
   |     +-- src/models/           (Data models)
   |
   +-- worktree-middleware/        (agent/middleware-dev branch)
   |     +-- src/middleware/       (Auth, logging, caching)
   |     +-- src/integrations/     (Third-party services)
   |
   +-- worktree-mobile/            (agent/mobile-dev branch)
   |     +-- ios/                  (iOS-specific)
   |     +-- android/              (Android-specific)
   |     +-- src/                  (Shared mobile code)
   |
   +-- worktree-infra/             (agent/infra-dev branch)
         +-- docker/               (Dockerfiles)
         +-- .github/workflows/    (CI/CD)
         +-- terraform/            (IaC)
```

**Merge Strategy:**

```
 MERGE ORDER (bottom-up by dependency):

 1. main <-- agent/infra-dev        (infrastructure layer)
      |
 2. main <-- agent/backend-dev      (data + API layer)
      |
 3. main <-- agent/middleware-dev    (integration layer)
      |
 4. main <-- agent/frontend-dev     (presentation layer)
      |
 5. main <-- agent/mobile-dev       (mobile layer)

 CONFLICT RESOLUTION:

 [MERGE_ATTEMPT]
      |
      +---> [CLEAN_MERGE] ---> done
      |
      +---> [CONFLICT_DETECTED]
               |
               v
          [ANALYZE_CONFLICT]
               |
        +------+------+------+
        |      |      |      |
   whitespace  non-   semantic  destructive
   /format   overlapping        conflict
        |      |      |         |
        v      v      v         v
   [AUTO_FIX  [MERGE  [LLM    [ESCALATE
    FORMAT]    BOTH    RESOLVE] TO HUMAN]
        |     SECTIONS]  |
        v      v         v
   [RUN_TESTS after merge]
        |
   +----+----+
   |         |
 pass      fail
   |         |
   v         v
 [ACCEPT]  [ROLLBACK_MERGE]
                |
                v
           [ESCALATE]
```

**Error Handling:**
- Agent stalls (no progress for >5 min): restart agent with same context
- Agent produces non-compiling code: retry task with error feedback
- Merge conflict unresolvable by LLM: escalate to human
- Token budget exceeded for agent: summarize context, continue with reduced context
- Agent exceeds task count: redistribute remaining tasks to other agents

---

### 3.6 Quality Assurance Phase

**Description:** Multiple review agents run in parallel to assess code quality, security, accessibility, internationalization, and performance. Each produces a findings report that feeds into the testing and debug phases.

**Goals:**
- Verify code quality and adherence to best practices
- Identify security vulnerabilities (SAST, DAST, SCA)
- Check accessibility compliance (WCAG 2.1 AA)
- Verify internationalization readiness
- Profile initial performance characteristics
- Verify architecture conformance

**Agent(s) Involved:** Code Reviewer, Security Auditor, Accessibility Agent, i18n/L10n Agent, Performance Agent

**Input:**
```json
{
  "codebase": { },
  "architecture": { },
  "api_spec": { },
  "design_system": { },
  "merge_result": { }
}
```

**Output:**
```json
{
  "code_review": {
    "findings": [
      {
        "id": "CR001",
        "severity": "warning",
        "category": "code_smell",
        "file": "src/api/users.ts",
        "line": 42,
        "message": "Function exceeds recommended complexity threshold",
        "suggestion": "Extract validation logic into separate function",
        "auto_fixable": true
      }
    ],
    "metrics": {
      "total_files_reviewed": 147,
      "issues_found": 12,
      "critical": 0,
      "warnings": 8,
      "info": 4
    }
  },
  "security_audit": {
    "sast_findings": [ ],
    "sca_findings": [ ],
    "secret_scan_findings": [ ],
    "overall_risk": "low | medium | high | critical"
  },
  "accessibility_audit": {
    "wcag_level": "A | AA | AAA",
    "violations": [ ],
    "warnings": [ ],
    "compliance_score": 0.95
  },
  "performance_profile": {
    "bundle_size": { },
    "lighthouse_scores": { },
    "api_response_times": { },
    "recommendations": [ ]
  }
}
```

**Step-by-Step Workflow:**

```
 1. Orchestrator fans out to 5 review agents in parallel:
    a. Code Reviewer: style, patterns, architecture conformance
    b. Security Auditor: SAST, SCA, secret scanning
    c. Accessibility Agent: WCAG compliance check
    d. i18n/L10n Agent: internationalization readiness check
    e. Performance Agent: bundle analysis, profiling
 2. Each agent scans the entire codebase
 3. Agents produce findings reports with severity ratings
 4. Orchestrator collects and aggregates all findings
 5. Auto-fix applicable issues:
    a. Code style issues -> auto-format
    b. Simple security fixes -> auto-patch
    c. Accessibility quick wins -> auto-fix
 6. Categorize remaining findings:
    a. Critical/Blocker -> must fix before testing
    b. Warning -> fix during debug phase
    c. Info -> document for future improvement
 7. If critical/blocker findings exist:
    a. Route back to relevant developer agent for fix
    b. Re-run affected reviews after fix
 8. [GATE G6] No critical/blocker findings remain
 9. Checkpoint saved, transition to Testing
```

**Sequence Diagram:**

```
 Orchestrator     Code          Security       A11y          Performance
                  Reviewer      Auditor        Agent         Agent
     |               |              |              |              |
     | Fan-out       |              |              |              |
     |-------------->|              |              |              |
     |----------------------------->|              |              |
     |------------------------------------------>|              |
     |------------------------------------------------------>|
     |               |              |              |              |
     |               | Scan code    | Run SAST     | Check WCAG  | Profile
     |               |---+          |---+          |---+         |---+
     |               |<--+          |<--+          |<--+         |<--+
     |               |              |              |              |
     |               | Scan style   | Run SCA      | Check ARIA  | Bundle
     |               |---+          |---+          |---+         | analysis
     |               |<--+          |<--+          |<--+         |---+
     |               |              |              |              |<--+
     |               | Check arch   | Scan secrets |              |
     |               | conformance  |---+          |              |
     |               |---+          |<--+          |              |
     |               |<--+          |              |              |
     |               |              |              |              |
     | CR Report     |              |              |              |
     |<--------------|              |              |              |
     | Sec Report    |              |              |              |
     |<-----------------------------|              |              |
     | A11y Report   |              |              |              |
     |<------------------------------------------|              |
     | Perf Report   |              |              |              |
     |<------------------------------------------------------|
     |               |              |              |              |
     | Aggregate     |              |              |              |
     |---+           |              |              |              |
     |<--+           |              |              |              |
     | [GATE G6]     |              |              |              |
```

**Error Handling:**
- Review agent crashes: restart and re-scan
- False positive detected: mark as suppressed, add to exclusion list
- SAST tool unavailable: log warning, proceed with available tools
- Performance profiling fails: skip, flag for manual review

**Quality Gate G6: Review Clearance**
- Zero critical or blocker severity findings
- Security audit shows no critical vulnerabilities
- No hardcoded secrets detected
- Accessibility compliance score >= 0.85

---

### 3.7 Testing Phase

**Description:** The Tester Agent generates and executes comprehensive test suites covering unit, integration, end-to-end, UI component, smoke, regression, and mutation tests. The Performance Agent runs load tests and the Accessibility Agent runs automated a11y tests.

**Goals:**
- Generate unit tests for all business logic
- Generate integration tests for API endpoints
- Generate E2E tests for critical user flows
- Generate UI component tests (Storybook, Testing Library)
- Run smoke tests (post-build/post-deploy sanity checks)
- Run regression tests (full suite re-run after fixes)
- Run mutation tests (Stryker, mutmut - test quality verification)
- Run performance/load tests
- Achieve target code coverage
- Run accessibility tests

**Agent(s) Involved:** Tester, Performance Agent, Accessibility Agent

**Input:**
```json
{
  "codebase": { },
  "api_spec": { },
  "architecture": { },
  "review_reports": { },
  "coverage_target": 80
}
```

**Output:**
```json
{
  "test_results": {
    "unit": {
      "total": 245,
      "passed": 238,
      "failed": 7,
      "skipped": 0,
      "duration_ms": 12400
    },
    "integration": {
      "total": 58,
      "passed": 55,
      "failed": 3,
      "skipped": 0,
      "duration_ms": 45200
    },
    "e2e": {
      "total": 22,
      "passed": 20,
      "failed": 2,
      "skipped": 0,
      "duration_ms": 120000
    },
    "performance": {
      "load_test_results": { },
      "p99_response_time_ms": 250,
      "throughput_rps": 1200,
      "error_rate": 0.001
    },
    "accessibility": {
      "axe_violations": 3,
      "screen_reader_tested": true,
      "keyboard_nav_tested": true
    }
  },
  "coverage": {
    "overall": 82.5,
    "by_module": { },
    "uncovered_critical_paths": [ ]
  },
  "failure_details": [
    {
      "test_id": "unit/auth/login.test.ts:42",
      "name": "should reject invalid credentials",
      "error": "Expected 401 but received 500",
      "stack_trace": "...",
      "related_file": "src/api/auth/login.ts",
      "related_line": 28
    }
  ]
}
```

**Step-by-Step Workflow:**

```
 1. Tester analyzes codebase and API spec
 2. Generate test suites:
    a. Unit tests for all services, utilities, and models
    b. Integration tests for API endpoints against test database
    c. E2E tests for critical user flows (login, CRUD, checkout, etc.)
    d. UI component tests (Storybook visual tests, Testing Library interaction tests)
 3. Set up test infrastructure:
    a. Test database with seed data
    b. Mock external services
    c. Test environment variables
    d. Storybook environment for component testing
 4. Execute test suites (parallel where possible):
    a. Unit tests (fastest, run first)
    b. UI component tests (Testing Library, Storybook)
    c. Integration tests (medium speed)
    d. E2E tests (slowest, run last)
 5. Run smoke tests:
    a. Post-build sanity checks (app starts, routes resolve)
    b. Post-deploy verification (health endpoints, critical paths)
 6. Performance Agent runs load tests:
    a. Ramp-up test (gradual traffic increase)
    b. Stress test (peak load simulation)
    c. Endurance test (sustained load)
 7. Accessibility Agent runs automated tests:
    a. axe-core scan on all pages
    b. Keyboard navigation check
    c. Screen reader compatibility check
 8. Run mutation tests (test quality verification):
    a. Stryker (JavaScript/TypeScript) or mutmut (Python)
    b. Identify tests that don't catch code mutations
    c. Flag weak test coverage areas
 9. Collect all results and compute coverage
 10. Run regression tests (full suite re-run to verify stability)
 11. Classify failures by severity and root cause
 12. [GATE G7] Test results collected (auto-pass to Debug phase)
 13. Checkpoint saved, transition to Debug & Stabilization
```

**State Machine:**

```
 [TEST_INIT]
      |
      v
 [GENERATE_TESTS]
      |
      v
 [SETUP_TEST_INFRA]
      |
      +---> [SETUP_FAILED] ---> [RETRY_SETUP] ---> (max 3 retries)
      |                                                  |
      |                                             [ESCALATE]
      v
 [RUN_UNIT_TESTS]
      |
      v
 [RUN_UI_COMPONENT_TESTS]    (Testing Library, Storybook - parallel with unit)
      |
      v
 [RUN_INTEGRATION_TESTS]     (can run in parallel with unit tests)
      |
      v
 [RUN_E2E_TESTS]
      |
      v
 [RUN_SMOKE_TESTS]           (post-build sanity checks)
      |
      v
 [RUN_PERF_TESTS]            (parallel with E2E)
      |
      v
 [RUN_A11Y_TESTS]            (parallel with E2E)
      |
      v
 [RUN_MUTATION_TESTS]        (Stryker/mutmut - test quality verification)
      |
      v
 [COLLECT_RESULTS]
      |
      v
 [RUN_REGRESSION_TESTS]      (full suite re-run after all results)
      |
      v
 [COMPUTE_COVERAGE]
      |
      +---> coverage >= target ---> [PASS]
      |
      +---> coverage < target  ---> [FLAG_LOW_COVERAGE]
      |
      v
 [CLASSIFY_FAILURES]
      |
      v
 [GATE G7: AUTO]
```

**Error Handling:**
- Test infrastructure fails to start: retry setup, fall back to in-memory DB
- Test generation produces invalid tests: re-generate with error context
- E2E browser launch fails: retry with headless mode
- Performance test causes OOM: reduce load parameters, retry
- Flaky test detected (passes on retry): mark as flaky, exclude from failure count

---

### 3.8 Debug & Fix Loop

**Description:** The Debugger Agent analyzes test failures, identifies root causes, generates fixes, creates targeted regression tests, and iterates until all tests pass or the maximum iteration count is reached.

**Goals:**
- Analyze all test failures and identify root causes
- Generate targeted fixes for each failure
- Create regression tests to prevent recurrence
- Iterate until all tests pass
- Escalate to human if max iterations exceeded

**Agent(s) Involved:** Debugger, Tester (for re-running tests)

**Step-by-Step Workflow:**

```
 1. Receive test failure details from Testing phase
 2. Prioritize failures:
    a. Critical: security, data loss, crashes
    b. High: core feature broken
    c. Medium: edge case failure
    d. Low: cosmetic, non-functional
 3. For each failure (highest priority first):
    a. Analyze error message and stack trace
    b. Read related source code
    c. Identify root cause
    d. Generate fix
    e. Generate targeted regression test
    f. Apply fix to codebase
    g. Run targeted test to verify fix
    h. Run full test suite to check for regressions
 4. If all tests pass: proceed to Documentation & Knowledge
 5. If new regressions introduced:
    a. Add regressions to failure queue
    b. Increment iteration counter
    c. Loop back to step 3
 6. If iteration count >= MAX_ITERATIONS (default: 3):
    a. Escalate to human with:
       - Remaining failures
       - Fix attempts history
       - Root cause analysis
       - Suggested manual steps
```

**Debug/Fix Loop Diagram:**

```
 Test Failure -----> Failure Analysis -----> Root Cause ID
      ^                                          |
      |                                          v
      |                                    Fix Generation
      |                                          |
      |                                          v
      |                              Targeted Test Creation
      |                                          |
      |                                          v
      |                                   Fix Application
      |                                          |
      |                                          v
      |                                   Re-run Tests
      |                                          |
      |                                     +----+----+
      |                                     |         |
      |                                   pass      fail
      |                                     |         |
      |                                     v         |
      |                              [Continue]       |
      |                                               |
      +---- iteration < MAX ----<---------------------+
                                               |
                                         iteration >= MAX
                                               |
                                               v
                                      [ESCALATE TO HUMAN]
```

**Detailed Sequence Diagram:**

```
 Orchestrator      Debugger         Tester           Codebase        User
     |                |                |                 |              |
     | Failures       |                |                 |              |
     |--------------->|                |                 |              |
     |                | Prioritize     |                 |              |
     |                |---+            |                 |              |
     |                |<--+            |                 |              |
     |                |                |                 |              |
     |   +----------- ITERATION LOOP (max 3) ----------+              |
     |   |            |                |                 |              |
     |   |            | Analyze error  |                 |              |
     |   |            |---+            |                 |              |
     |   |            |<--+            |                 |              |
     |   |            |                |                 |              |
     |   |            | Read source    |                 |              |
     |   |            |--------------------------------->|              |
     |   |            | Source code    |                 |              |
     |   |            |<---------------------------------|              |
     |   |            |                |                 |              |
     |   |            | Generate fix   |                 |              |
     |   |            |---+            |                 |              |
     |   |            |<--+            |                 |              |
     |   |            |                |                 |              |
     |   |            | Generate test  |                 |              |
     |   |            |---+            |                 |              |
     |   |            |<--+            |                 |              |
     |   |            |                |                 |              |
     |   |            | Apply fix      |                 |              |
     |   |            |--------------------------------->|              |
     |   |            |                |                 |              |
     |   |            | Run targeted   |                 |              |
     |   |            | test           |                 |              |
     |   |            |--------------->|                 |              |
     |   |            | Result         |                 |              |
     |   |            |<---------------|                 |              |
     |   |            |                |                 |              |
     |   |            | Run full suite |                 |              |
     |   |            |--------------->|                 |              |
     |   |            | Results        |                 |              |
     |   |            |<---------------|                 |              |
     |   |            |                |                 |              |
     |   |   +--------+--------+      |                 |              |
     |   |   |                 |      |                 |              |
     |   | all pass        new failures                 |              |
     |   |   |                 |      |                 |              |
     |   |   v                 v      |                 |              |
     |   | [DONE]        [LOOP BACK]  |                 |              |
     |   |                     |      |                 |              |
     |   +---------------------+      |                 |              |
     |                |                |                 |              |
     |   (if max iterations reached)   |                 |              |
     |                |                |                 |              |
     | Escalation     |                |                 |              |
     | report         |                |                 |              |
     |<---------------|                |                 |              |
     |                                                                 |
     | Escalate to human                                               |
     |---------------------------------------------------------------->|
```

**Fix Strategies:**

| Strategy | When Used | Description |
|----------|-----------|-------------|
| Targeted Fix | Single, isolated bug | Fix the specific line/function causing the failure |
| Refactor | Systemic issue | Restructure the affected module to address root cause |
| Alternative Approach | Fix causes regressions | Try a completely different implementation strategy |
| Rollback + Redo | Multiple regressions | Revert to last known good state, re-implement differently |
| Partial Skip | Non-critical, time constrained | Mark test as known-issue, document, and proceed |

**Error Handling:**
- Debugger cannot identify root cause: provide best guess + escalate
- Fix introduces more failures than it resolves: rollback fix, try alternative
- Debugger exceeds token budget: summarize context, continue with essential code only
- Circular regression loop detected: break cycle, escalate to human

---

### 3.9 Documentation & Knowledge Phase

**Description:** The Documentation Writer generates all project documentation, and the Skill/Hook/Tool Creators produce reusable knowledge artifacts. This phase runs AFTER debug stabilization and BEFORE deployment, ensuring all documentation reflects the final stable codebase.

**Goals:**
- Generate complete project documentation
- Create Architecture Decision Records (ADRs)
- Generate API documentation from OpenAPI spec
- Produce deployment and development guides
- Create reusable skills, hooks, and tools for the knowledge base

**Agent(s) Involved:** Documentation Writer, Skill Creator, Hooks Creator, Tools Creator, Orchestrator

**Input:**
```json
{
  "codebase": { },
  "architecture": { },
  "api_spec": { },
  "test_results": { },
  "all_phase_outputs": { }
}
```

**Output:**
```json
{
  "documentation": {
    "readme": "README.md",
    "api_docs": "docs/api/",
    "architecture_decision_records": "docs/adr/",
    "deployment_guide": "docs/deployment.md",
    "development_guide": "docs/development.md",
    "changelog": "CHANGELOG.md",
    "contributing": "CONTRIBUTING.md"
  },
  "knowledge_artifacts": {
    "skills_created": [],
    "hooks_created": [],
    "tools_created": [],
    "patterns_documented": []
  }
}
```

**Step-by-Step Workflow:**

```
 1. Documentation Writer generates documentation (parallel):
    a. README.md with project overview, setup, and usage
    b. API documentation from OpenAPI spec
    c. Architecture Decision Records (ADRs)
    d. Deployment guide with step-by-step instructions
    e. Development guide (local setup, testing, contributing)
    f. CHANGELOG.md with version history
 2. All documentation committed to repository
 3. Skill Creator analyzes codebase for reusable patterns:
    a. Extract common patterns as reusable skills
    b. Document skill interfaces and usage
 4. Hooks Creator generates lifecycle hooks:
    a. Pre/post build hooks
    b. Pre/post deploy hooks
    c. Pre/post test hooks
 5. Tools Creator generates custom tools:
    a. Project-specific CLI tools
    b. Integration utilities
 6. [GATE G9] Documentation completeness validation
 7. Checkpoint saved, transition to Deployment & Delivery
```

**Sequence Diagram:**

```
 Orchestrator      Doc Writer     Skill Creator   Hooks Creator   Tools Creator
     |                 |               |               |               |
     | Generate docs   |               |               |               |
     |---------------->|               |               |               |
     |                 | README        |               |               |
     |                 |---+           |               |               |
     |                 |<--+           |               |               |
     |                 | API docs      |               |               |
     |                 |---+           |               |               |
     |                 |<--+           |               |               |
     |                 | ADRs         |               |               |
     |                 |---+           |               |               |
     |                 |<--+           |               |               |
     |                 |               |               |               |
     | Create skills   |               |               |               |
     |------------------------------>|               |               |
     |                 |               |---+           |               |
     |                 |               |<--+           |               |
     |                 |               |               |               |
     | Create hooks    |               |               |               |
     |-------------------------------------------->|               |
     |                 |               |               |---+           |
     |                 |               |               |<--+           |
     |                 |               |               |               |
     | Create tools    |               |               |               |
     |---------------------------------------------------------->|
     |                 |               |               |               |---+
     |                 |               |               |               |<--+
     |                 |               |               |               |
     | All artifacts   |               |               |               |
     |<----------------|               |               |               |
     |<-------------------------------|               |               |
     |<--------------------------------------------|               |
     |<------------------------------------------------------------|
     |                 |               |               |               |
     | [GATE G9]       |               |               |               |
```

**Error Handling:**
- Documentation generation fails: produce minimal docs, flag incomplete sections
- Skill extraction fails: skip, document patterns manually
- Hook generation fails: provide template hooks for manual customization

**Quality Gate G9: Documentation Completeness**
- README.md exists and covers setup instructions
- API documentation generated for all endpoints
- At least one ADR documenting key architectural decisions
- Deployment guide covers all target environments

---

### 3.10 Deployment & Delivery Phase

**Description:** The DevOps Agent, Infrastructure Engineer, and GitHub Agent collaborate to create CI/CD pipelines, generate Infrastructure-as-Code, deploy the application, create a release with artifacts, and produce a comprehensive handoff report for the user. This is the LAST stage of the pipeline.

**Goals:**
- Create CI/CD pipeline (GitHub Actions by default)
- Generate Infrastructure-as-Code (Terraform/Pulumi/Docker)
- Configure deployment environments (staging, production)
- Deploy application with health checks
- Set up monitoring and alerting
- Create GitHub release with all artifacts
- Produce handoff report for the user
- Archive project state for future reference

**Agent(s) Involved:** DevOps Agent, Infrastructure Engineer, GitHub Agent, Project Manager

**Input:**
```json
{
  "codebase": { },
  "tech_stack": { },
  "architecture": { },
  "test_results": { },
  "deployment_target": {
    "provider": "vercel | aws | gcp | azure | self-hosted",
    "environments": ["staging", "production"],
    "domain": "app.example.com",
    "ssl": true
  }
}
```

**Output:**
```json
{
  "ci_cd": {
    "pipeline_file": ".github/workflows/deploy.yml",
    "stages": ["lint", "test", "build", "deploy-staging", "deploy-production"],
    "triggers": ["push to main", "pull_request"],
    "secrets_required": ["DEPLOY_TOKEN", "DATABASE_URL"]
  },
  "infrastructure": {
    "iac_files": ["terraform/main.tf", "terraform/variables.tf"],
    "docker_files": ["Dockerfile", "docker-compose.yml"],
    "kubernetes_files": [],
    "estimated_monthly_cost": "$25-50"
  },
  "deployment": {
    "staging_url": "https://staging.app.example.com",
    "production_url": "https://app.example.com",
    "health_check_status": "healthy",
    "deployment_time_seconds": 120
  },
  "monitoring": {
    "uptime_check": "configured",
    "error_tracking": "Sentry configured",
    "log_aggregation": "configured",
    "alerting_channels": ["email", "slack"]
  }
}
```

**Step-by-Step Workflow:**

```
 1. DevOps Agent analyzes tech stack and architecture
 2. DevOps Agent generates CI/CD pipeline:
    a. Linting stage
    b. Testing stage (unit + integration)
    c. Build stage (Docker image or static build)
    d. Deploy-to-staging stage
    e. Deploy-to-production stage (manual gate or auto)
 3. Infrastructure Engineer generates IaC:
    a. Compute resources (containers, serverless, VMs)
    b. Database provisioning
    c. Cache layer (Redis)
    d. CDN configuration
    e. DNS and SSL certificates
    f. Networking (VPC, security groups)
 4. GitHub Agent sets up repository:
    a. Create/configure branch protection rules
    b. Set up required secrets
    c. Configure GitHub Actions
    d. Create initial PR for deployment config
 5. Deploy to staging environment:
    a. Provision infrastructure (if not exists)
    b. Build application
    c. Deploy application
    d. Run smoke tests against staging
    e. Run health checks
 6. If staging healthy:
    a. [GATE G10] Optional: user approval for production
    b. Deploy to production
    c. Run production health checks
    d. Configure monitoring and alerting
 7. GitHub Agent creates release:
    a. Create git tag (v1.0.0)
    b. Build release artifacts
    c. Create GitHub Release with changelog
    d. Attach artifacts to release
 8. Orchestrator generates handoff report:
    a. Project summary and feature list
    b. Known limitations and technical debt
    c. Recommended next steps
    d. Cost and timeline summary
    e. All agent execution logs
 9. Deliver to user:
    a. Repository URL with all code
    b. Deployment URL (staging + production)
    c. Documentation URL
    d. Handoff report
 10. Final checkpoint saved
 11. Session archived
```

**Sequence Diagram:**

```
 Orchestrator     DevOps       Infra          GitHub        Cloud
                  Agent        Engineer       Agent         Provider
     |               |            |              |              |
     | Start deploy  |            |              |              |
     |-------------->|            |              |              |
     |               |            |              |              |
     |               | Gen CI/CD  |              |              |
     |               |---+        |              |              |
     |               |<--+        |              |              |
     |               |            |              |              |
     |               |  Gen IaC   |              |              |
     |               |----------->|              |              |
     |               |            |---+          |              |
     |               |            |<--+          |              |
     |               |  IaC ready |              |              |
     |               |<-----------|              |              |
     |               |            |              |              |
     |               | Setup repo |              |              |
     |               |---------------------------->|              |
     |               |            |  Configured  |              |
     |               |<----------------------------|              |
     |               |            |              |              |
     |               | Provision staging          |              |
     |               |--------------------------------------------->|
     |               |            |              |         provisioned
     |               |<---------------------------------------------|
     |               |            |              |              |
     |               | Deploy to staging          |              |
     |               |--------------------------------------------->|
     |               |            |              |         deployed
     |               |<---------------------------------------------|
     |               |            |              |              |
     |               | Health check               |              |
     |               |--------------------------------------------->|
     |               |            |              |          healthy
     |               |<---------------------------------------------|
     |               |            |              |              |
     | Staging OK    |            |              |              |
     |<--------------|            |              |              |
     |               |            |              |              |
     | [GATE G10]    |            |              |              |
     | (optional)    |            |              |              |
     |               |            |              |              |
     |               | Deploy to production       |              |
     |               |--------------------------------------------->|
     |               |            |              |         deployed
     |               |<---------------------------------------------|
     |               |            |              |              |
     |               | Setup monitoring           |              |
     |               |--------------------------------------------->|
     |               |            |              |       configured
     |               |<---------------------------------------------|
```

**Error Handling:**
- IaC provisioning fails: retry with diagnostic output, escalate if persistent
- Deployment fails: rollback to previous version, analyze logs
- Health check fails: rollback deployment, enter debug loop
- Secret not configured: prompt user for secrets, pause deployment
- Cost estimate exceeds budget: suggest cheaper alternatives, await approval

**Quality Gate G10: Deployment & Delivery Validation**
- Application responds to health check endpoint
- All smoke tests pass against staging
- No error spikes in monitoring
- SSL certificate valid
- DNS resolves correctly

---

### 3.11 Failure Mode Analysis per Phase

Each pipeline phase has characteristic failure modes. The following table documents common failures, how they are detected, and the recovery strategy applied.

| Stage | Phase | Common Failures | Detection | Recovery |
|---|---|---|---|---|
| S0 | Initialization | Repo creation failure, permission issues | Git/GitHub API errors | Retry, prompt for credentials |
| S1 | Brainstorming | User abandonment, infinite loop | Session timeout (60min), repetition detection | Auto-finalize with current state |
| S2 | Research | Outdated info, hallucinated references | Source verification, cross-reference check | Flag unverified, fallback to cached knowledge |
| S3 | Architecture & Design | Over-engineering, inconsistent design | Complexity metrics, schema validation | Simplify, apply reference architecture |
| S4 | Planning & Configuration | Over-decomposition, missing dependencies, tech stack conflicts | Task count threshold, dependency cycle detection, compatibility validation | Simplify plan, merge tasks, resolve conflicts |
| S5 | Implementation | Compilation errors, type mismatches | Build verification after each agent | Route to Debugger, retry with context |
| S6 | Quality Assurance | False positives, scanner crashes | Result validation, scanner health check | Re-run with different config, manual review flag |
| S7 | Testing | Flaky tests, environment issues | Test stability tracking, retry detection | Quarantine flaky tests, environment reset |
| S8 | Debug & Stabilization | Infinite fix loop, regression introduction | Iteration counter (max 5), regression detection | Escalate to human after 3 iterations |
| S9 | Documentation & Knowledge | Missing artifacts, incomplete docs | Completeness checklist validation | Re-generate missing items |
| S10 | Deployment & Delivery | Health check failure, resource exhaustion | Health endpoint monitoring, resource metrics | Auto-rollback, scale resources |

---

## 4. Agent Interaction Patterns

CodeBot agents interact through five primary patterns. These patterns govern how data, control, and state flow through the computation graph.

### 4.1 State Flow Pattern

**Description:** Shared state propagates through the computation graph via a centralized state store. Each agent reads from and writes to this store, allowing downstream agents to consume outputs from upstream agents without direct coupling.

```
 STATE STORE ARCHITECTURE:

 +-------------------------------------------------------------------+
 |                        STATE STORE                                 |
 |                                                                   |
 |  +------------------+  +------------------+  +-----------------+  |
 |  | project_meta     |  | requirements     |  | plan            |  |
 |  |   name, id       |  |   features[]     |  |   epics[]       |  |
 |  |   created_at     |  |   constraints[]  |  |   task_graph    |  |
 |  |   status         |  |   personas[]     |  |   schedule      |  |
 |  +------------------+  +------------------+  +-----------------+  |
 |                                                                   |
 |  +------------------+  +------------------+  +-----------------+  |
 |  | research         |  | architecture     |  | design          |  |
 |  |   evaluations[]  |  |   c4_docs        |  |   design_system |  |
 |  |   dependencies   |  |   api_spec       |  |   wireframes    |  |
 |  |   patterns[]     |  |   data_flow      |  |   components    |  |
 |  +------------------+  +------------------+  +-----------------+  |
 |                                                                   |
 |  +------------------+  +------------------+  +-----------------+  |
 |  | implementation   |  | review           |  | testing         |  |
 |  |   files{}        |  |   findings[]     |  |   results       |  |
 |  |   branches{}     |  |   security       |  |   coverage      |  |
 |  |   merge_status   |  |   accessibility  |  |   failures[]    |  |
 |  +------------------+  +------------------+  +-----------------+  |
 +-------------------------------------------------------------------+
        ^        ^        ^        ^        ^        ^
        |        |        |        |        |        |
     Agent1   Agent2   Agent3   Agent4   Agent5   Agent6
     (read/   (read/   (read/   (read/   (read/   (read/
      write)   write)   write)   write)   write)   write)
```

**State Access Rules:**

| Agent | Can Read | Can Write |
|-------|----------|-----------|
| Brainstorming Agent | project_meta | requirements |
| Researcher | requirements | research |
| Architect | research, requirements | architecture |
| Designer | architecture, requirements | design |
| Database Agent | architecture, research | architecture.database |
| API Gateway Agent | architecture, research | architecture.api |
| Planner | architecture, research, requirements | plan |
| TechStack Builder | architecture, research | tech_stack |
| Template Agent | tech_stack, design | scaffold |
| Frontend Developer | architecture, design, api_spec | implementation.frontend |
| Backend Developer | architecture, database, api_spec | implementation.backend |
| Middleware Developer | architecture, api_spec | implementation.middleware |
| Mobile Developer | architecture, design, api_spec | implementation.mobile |
| Infrastructure Engineer | architecture, tech_stack | implementation.infrastructure |
| Code Reviewer | implementation, architecture | review.code |
| Security Auditor | implementation | review.security |
| Accessibility Agent | implementation, design | review.accessibility |
| Performance Agent | implementation, architecture | review.performance |
| Tester | implementation, api_spec | testing |
| Debugger | testing.failures, implementation | implementation (fixes) |
| DevOps Agent | tech_stack, architecture | deployment.ci_cd |
| GitHub Agent | all (read-only) | deployment.github |
| Documentation Writer | all (read-only) | documentation |
| Project Manager | all (read-only) | project_status, reports |

**State Versioning:**

Every write to the state store creates a new version. Agents always read the latest version unless explicitly pinned to a specific version (for reproducibility).

```
 state_store/
   v001/ <- Initialization output
   v002/ <- Brainstorming output
   v003/ <- Research output
   v004/ <- Architecture & Design output
   v005/ <- Planning & Configuration output
   ...
   latest -> v011/
```

---

### 4.2 Message Flow Pattern

**Description:** Direct agent-to-agent messaging for task handoff, coordination signals, and real-time data sharing. Messages are asynchronous and go through a message bus.

```
 MESSAGE BUS ARCHITECTURE:

 +--Agent A--+     +--Message Bus--+     +--Agent B--+
 |           |     |               |     |           |
 | produce() |---->| queue/topic   |---->| consume() |
 |           |     |               |     |           |
 +-----------+     | - ordered     |     +-----------+
                   | - persistent  |
                   | - at-least-   |
                   |   once        |
                   +---------------+
```

**Message Types:**

| Type | Description | Example |
|------|-------------|---------|
| `task.assigned` | Orchestrator assigns task to agent | `{agent: "frontend", task: "T003", context: {...}}` |
| `task.completed` | Agent reports task completion | `{agent: "frontend", task: "T003", output: {...}}` |
| `task.failed` | Agent reports task failure | `{agent: "frontend", task: "T003", error: {...}}` |
| `coordination.request` | Agent requests info from another agent | `{from: "frontend", to: "backend", need: "api_types"}` |
| `coordination.response` | Agent responds to coordination request | `{from: "backend", to: "frontend", data: {...}}` |
| `progress.update` | Agent reports incremental progress | `{agent: "frontend", progress: 0.45, current_file: "..."}` |
| `health.heartbeat` | Agent reports it is alive | `{agent: "frontend", status: "active", memory: "..."}` |
| `escalation.request` | Agent escalates issue to Orchestrator | `{agent: "debugger", issue: "...", severity: "critical"}` |

**Message Flow Example - API Contract Coordination:**

```
 Frontend Dev          Message Bus          Backend Dev
      |                     |                     |
      | Need API types      |                     |
      | for /api/users      |                     |
      |-------------------->|                     |
      |                     | coordination.request|
      |                     |-------------------->|
      |                     |                     |
      |                     |                     | Generate types
      |                     |                     |---+
      |                     |                     |<--+
      |                     |                     |
      |                     | coordination.response
      |                     |<--------------------|
      | Receive types       |                     |
      |<--------------------|                     |
      |                     |                     |
      | Implement with types|                     |
      |---+                 |                     |
      |<--+                 |                     |
```

**Communication Protocol Details:**

All inter-agent messages follow a standardized envelope format:

```json
{
  "id": "msg-uuid",
  "version": "1.0",
  "type": "task_handoff | result | error | clarification | approval_request | broadcast",
  "source_agent": "string",
  "target_agent": "string | *",
  "correlation_id": "task-uuid",
  "timestamp": "ISO 8601",
  "priority": "low | normal | high | critical",
  "payload": {},
  "metadata": { "tokens_used": 0, "model": "", "duration_ms": 0 }
}
```

**Delivery Guarantees:**

- **At-least-once delivery:** Every message is guaranteed to be delivered at least once. Consumers must be idempotent or deduplicate by `id`.
- **Per source-target pair ordering:** Messages between any given source and target agent are delivered in the order they were sent. No global ordering guarantee across different pairs.
- **Large message handling:** Messages exceeding 100KB are stored in blob storage; the message envelope contains a reference URI to the blob instead of the inline payload.

---

### 4.3 Control Flow Pattern

**Description:** The Orchestrator drives phase transitions, manages agent lifecycle, and handles error escalation. It is the single source of truth for pipeline state.

```
 ORCHESTRATOR CONTROL FLOW:

                          +-------------------+
                          |   ORCHESTRATOR    |
                          |                   |
                          | - Phase manager   |
                          | - Agent registry  |
                          | - Error handler   |
                          | - Gate evaluator  |
                          +-------------------+
                           /    |    |    \
                          /     |    |     \
                         v      v    v      v
                      [Start] [Monitor] [Stop] [Restart]
                       Agent   Agent    Agent   Agent
                         |      |        |       |
                         v      v        v       v
                      +------+ +------+ +------+ +------+
                      |Agent1| |Agent2| |Agent3| |Agent4|
                      +------+ +------+ +------+ +------+
```

**Control Commands:**

| Command | Description | When Used |
|---------|-------------|-----------|
| `start_phase(phase)` | Begin a new pipeline phase | Phase transition |
| `spawn_agent(type, config)` | Create and start an agent | Phase requires agent |
| `stop_agent(id)` | Gracefully stop an agent | Phase complete or agent failed |
| `restart_agent(id)` | Stop and restart with same context | Agent stalled or crashed |
| `pause_pipeline()` | Pause entire pipeline | Human intervention needed |
| `resume_pipeline()` | Resume from paused state | Human intervention complete |
| `escalate(issue)` | Send issue to human | Max retries exceeded |
| `checkpoint()` | Save pipeline state | Phase transition |
| `rollback(phase)` | Revert to phase checkpoint | Unrecoverable error |

**Phase Transition State Machine:**

```
 [IDLE]
   |
   | start_phase(brainstorming)
   v
 [PHASE_ACTIVE]
   |
   +---> agent reports completion
   |       |
   |       v
   |    [EVALUATE_GATE]
   |       |
   |    +--+--+
   |    |     |
   |  pass   fail
   |    |     |
   |    v     v
   | [SAVE   [REMEDIATE]
   |  CHECKPOINT]  |
   |    |     +---> retry gate
   |    |     +---> escalate
   |    v
   | [TRANSITION_TO_NEXT_PHASE]
   |    |
   |    v
   | [PHASE_ACTIVE] (next phase)
   |
   +---> agent reports error
   |       |
   |       v
   |    [ERROR_HANDLER]
   |       |
   |    +--+--+
   |    |     |
   | retryable non-retryable
   |    |     |
   |    v     v
   | [RETRY] [ESCALATE]
   |
   +---> human intervention requested
           |
           v
        [PAUSED]
           |
           | human responds
           v
        [PHASE_ACTIVE]
```

---

### 4.4 Collaboration Pattern

**Description:** How agents collaborate within a single phase when multiple agents must coordinate their work. This pattern is critical during the Architecture & Design phase and the Implementation phase.

**Intra-Phase Collaboration Model:**

```
 COLLABORATION WITHIN A PHASE:

 +------------------------------------------------------------------+
 |  PHASE: Architecture & Design                                     |
 |                                                                   |
 |  +----------+    data models    +----------+                      |
 |  | Architect |----------------->| DB Agent |                      |
 |  +----------+                   +----------+                      |
 |       |                              |                            |
 |       | service                      | schema                     |
 |       | boundaries                   | ready                      |
 |       v                              v                            |
 |  +----------+    endpoints      +----------+                      |
 |  | API GW   |<-----------------|Consistency|                      |
 |  | Agent    |                   | Checker  |                      |
 |  +----------+                   +----------+                      |
 |       |                              ^                            |
 |       | API                          |                            |
 |       | catalog                      | component                  |
 |       v                              | list                       |
 |  +----------+                   +----------+                      |
 |  | Designer |------------------>| Architect|                      |
 |  +----------+  feasibility check+----------+                      |
 +------------------------------------------------------------------+
```

**Collaboration Protocol:**

```
 1. PUBLISH-SUBSCRIBE:
    - Agents publish intermediate artifacts to shared topics
    - Interested agents subscribe and react to published artifacts
    - Example: Architect publishes data models, DB Agent subscribes

 2. REQUEST-RESPONSE:
    - Agent A sends a coordination.request to Agent B
    - Agent B processes and returns coordination.response
    - Used for synchronous coordination needs

 3. SHARED ARTIFACT:
    - Multiple agents contribute to a single artifact (e.g., OpenAPI spec)
    - Write locks prevent concurrent modifications
    - Merge conflicts resolved by Orchestrator

 4. REVIEW LOOP:
    - Agent A produces output
    - Agent B reviews and provides feedback
    - Agent A incorporates feedback
    - Example: Designer produces wireframe, Architect reviews feasibility
```

**Implementation Phase Collaboration:**

```
 Frontend Dev <-------- API Contract ---------> Backend Dev
      |                                              |
      | Shared types                    Shared types |
      | (generated                      (generated   |
      |  from OpenAPI)                  from OpenAPI) |
      |                                              |
      v                                              v
 Consumes:                                     Produces:
 - API response types                          - API endpoints
 - Error schemas                               - Response schemas
 - WebSocket events                            - Event definitions
      |                                              |
      +---------- Middleware Dev -------------------+
                       |
                 Produces:
                 - Auth middleware
                 - Rate limiting
                 - Request validation
                 - CORS configuration
```

**Conflict Resolution:**

When two agents produce conflicting outputs (e.g., Frontend expects a field that Backend doesn't provide):

```
 [CONFLICT_DETECTED]
      |
      v
 [ORCHESTRATOR_NOTIFIED]
      |
      v
 [ANALYZE_CONFLICT]
      |
      +---> API contract mismatch ---> Backend adjusts (API contract is source of truth)
      |
      +---> Schema incompatibility ---> Architect mediates
      |
      +---> Design infeasibility ---> Designer adjusts (architecture is constraint)
      |
      +---> Unresolvable ---> Escalate to human
```

---

### 4.5 Supervision Pattern

**Description:** How the Orchestrator monitors and manages agent health, detects failures, and ensures the pipeline remains operational.

**Health Monitoring:**

```
 AGENT SUPERVISION MODEL:

 +-------------------+
 |   ORCHESTRATOR    |
 |                   |
 | Health Monitor:   |
 | - Heartbeat check |
 | - Progress check  |
 | - Resource check  |
 | - Output check    |
 +-------------------+
        |
        | Monitors every 10s
        |
   +----+----+----+----+
   |    |    |    |    |
   v    v    v    v    v
  A1   A2   A3   A4   A5
   |    |    |    |    |
   |    |    |    |    +-- heartbeat: OK
   |    |    |    +------- heartbeat: OK
   |    |    +------------ heartbeat: MISSING (>30s)
   |    +----------------- heartbeat: OK
   +---------------------- heartbeat: OK
                                |
                                v
                         [INVESTIGATE A3]
                                |
                           +----+----+
                           |         |
                       recoverable  dead
                           |         |
                           v         v
                      [RESTART]  [REPLACE]
```

**Supervision Rules:**

| Check | Interval | Threshold | Action |
|-------|----------|-----------|--------|
| Heartbeat | 10s | Missing for 30s | Restart agent |
| Progress | 30s | No progress for 5 min | Investigate, possibly restart |
| Memory | 30s | >80% of limit | Reduce context, warn |
| Token Rate | Per request | >10K tokens/request | Summarize context |
| Error Rate | Per minute | >3 errors/min | Throttle, investigate |
| Output Quality | Per task completion | Validation fails | Retry task |

**Agent Lifecycle:**

```
 [CREATED]
    |
    | initialize(config)
    v
 [INITIALIZING]
    |
    | context loaded
    v
 [READY]
    |
    | assign_task(task)
    v
 [EXECUTING]
    |
    +---> task_complete ---> [READY] (await next task)
    |
    +---> task_failed ---> [ERROR]
    |                         |
    |                    +----+----+
    |                    |         |
    |               retryable  fatal
    |                    |         |
    |                    v         v
    |               [EXECUTING] [TERMINATED]
    |               (retry)        |
    |                              v
    +---> shutdown ----------> [TERMINATED]
    |                              |
    +---> stall_detected           v
           |                  [REPLACED]
           v                  (new agent spawned)
     [RESTARTING]
           |
           v
     [INITIALIZING]
```

**Escalation Chain:**

```
 Agent detects issue
      |
      v
 [SELF-RECOVERY ATTEMPT]  (retry internally, up to 2 times)
      |
      | failed
      v
 [REPORT TO ORCHESTRATOR]
      |
      v
 [ORCHESTRATOR RECOVERY]  (restart agent, switch model, reduce context)
      |
      | failed
      v
 [PIPELINE-LEVEL RECOVERY]  (rollback phase, try alternative strategy)
      |
      | failed
      v
 [HUMAN ESCALATION]  (pause pipeline, notify user, provide diagnosis)
```

---

### 4.6 Agent Lifecycle Workflow

Every agent in the pipeline follows a standardized lifecycle managed by the Orchestrator.

```
 AGENT LIFECYCLE:

 SPAWN → INITIALIZE → EXECUTE → CHECKPOINT → TERMINATE
   ↓         ↓           ↓          ↓           ↓
 Config   Load L0     Process    Serialize   Release
 loaded   context     tasks      state       resources
          Connect     Produce    to storage  Cleanup
          to LLM      artifacts              worktree
          Register    Emit                   Record
          tools       events                 metrics
```

**Lifecycle Stages:**

| Stage | Description | Failure Handling |
|-------|-------------|-----------------|
| **SPAWN** | Load agent configuration, allocate resources | Fail fast — configuration errors are fatal |
| **INITIALIZE** | Load L0 context, connect to LLM provider, register tools | Retry LLM connection up to 3 times, then fallback provider |
| **EXECUTE** | Process assigned tasks, produce artifacts, emit events | See Section 6 error handling strategies |
| **CHECKPOINT** | Serialize current state to persistent storage | Retry write; on failure, hold state in memory and alert |
| **TERMINATE** | Release resources, cleanup worktree, record metrics | Best-effort cleanup; log failures but do not block pipeline |

**Health Monitoring:**

- **Heartbeat:** Orchestrator pings each active agent every 30 seconds
- **Unresponsive detection:** 3 consecutive missed pings triggers restart
- **Restart procedure:** Terminate unresponsive agent, spawn new instance, restore from last checkpoint
- **Resource limits enforced:**
  - Token budget per agent (configurable, default varies by LLM tier)
  - Execution timeout (configurable per phase)
  - Memory limit (prevents runaway agents from exhausting system resources)

---

## 5. Project Type Workflows

CodeBot supports three project types, each with a different pipeline configuration. The project type is determined during the Brainstorming phase and affects which phases are active, which agents are spawned, and how the pipeline flows.

### 5.1 Greenfield Workflow

**Description:** Complete flow for building a new project from scratch. This is the default workflow and uses all phases.

```
 GREENFIELD PIPELINE:

 [User Input]
      |
      v
 [S0: Initialization]     <-- Project setup, repo creation
      |
      v
 [S1: Brainstorming]      <-- Full idea exploration
      |
      v
 [S2: Research]            <-- Full technology evaluation
      |
      v
 [S3: Architecture]        <-- Design from scratch
      |
      v
 [S4: Planning & Config]   <-- Task decomposition + tech stack + scaffold
      |
      v
 [S5: Implementation]      <-- Build everything
      |
      v
 [S6: Quality Assurance]   <-- Full review suite
      |
      v
 [S7: Testing]             <-- Comprehensive test generation
      |
      v
 [S8: Debug/Fix]           <-- Fix all issues
      |
      v
 [S9: Documentation]       <-- Complete documentation
      |
      v
 [S10: Deploy & Deliver]   <-- Full deployment + handoff
```

**Key Characteristics:**
- All phases are active
- All agent types may be spawned
- Template selection is important for productivity
- Full documentation generated from scratch
- CI/CD pipeline created from scratch
- Estimated timeline: 25-60 minutes (depending on complexity)

**Agent Activation Matrix for Greenfield:**

| Agent | Active | Stage | Phase |
|-------|--------|-------|-------|
| Orchestrator | Always | S0-S10 | All |
| Brainstorming Agent | Yes | S1 | Brainstorming |
| Researcher | Yes | S2 | Research |
| Architect | Yes | S3 | Architecture & Design |
| Designer | Yes | S3 | Architecture & Design |
| Database Agent | Yes | S3 | Architecture & Design |
| API Gateway Agent | Yes | S3 | Architecture & Design |
| Planner | Yes | S4 | Planning & Configuration |
| TechStack Builder | Yes | S4 | Planning & Configuration |
| Template Agent | Yes | S4 | Planning & Configuration |
| Frontend Developer | Yes | S5 | Implementation |
| Backend Developer | Yes | S5 | Implementation |
| Middleware Developer | Conditional | S5 | Implementation |
| Mobile Developer | Conditional | S5 | Implementation |
| Infrastructure Engineer | Yes | S5 | Implementation |
| Integrations Agent | Conditional | S5 | Implementation |
| Code Reviewer | Yes | S6 | Quality Assurance |
| Security Auditor | Yes | S6 | Quality Assurance |
| Accessibility Agent | Yes | S6 | Quality Assurance |
| i18n/L10n Agent | Conditional | S6 | Quality Assurance |
| Performance Agent | Yes | S6 + S7 | Quality Assurance + Testing |
| Tester | Yes | S7 | Testing |
| Debugger | Conditional | S8 | Debug & Stabilization |
| Documentation Writer | Yes | S9 | Documentation & Knowledge |
| Skill Creator | Conditional | S9 | Documentation & Knowledge |
| Hooks Creator | Conditional | S9 | Documentation & Knowledge |
| Tools Creator | Conditional | S9 | Documentation & Knowledge |
| DevOps Agent | Yes | S10 | Deployment & Delivery |
| GitHub Agent | Yes | S0 + S10 | Initialization + Deployment & Delivery |
| Project Manager | Yes | S0-S10 | Cross-cutting (All) |

---

### 5.2 Inflight Workflow

**Description:** Flow for joining an existing project mid-development. CodeBot analyzes the existing codebase, reverse-engineers the architecture, identifies gaps, and continues development.

```
 INFLIGHT PIPELINE:

 [User Input + Existing Repo URL]
      |
      v
 [Codebase Analysis]       <-- PRE-PIPELINE: Analyze existing code
      |
      +-- Clone repository
      +-- Detect tech stack
      +-- Map file structure
      +-- Identify patterns
      +-- Detect test coverage
      |
      v
 [Architecture Recovery]    <-- PRE-PIPELINE: Reverse-engineer architecture
      |
      +-- Infer C4 model from code
      +-- Extract API contracts from routes
      +-- Reverse-engineer DB schema from models/migrations
      +-- Map component hierarchy
      |
      v
 [Gap Analysis]             <-- PRE-PIPELINE: What's missing?
      |
      +-- Compare requirements vs implemented features
      +-- Identify missing tests
      +-- Find incomplete features
      +-- Detect technical debt
      |
      v
 === ENTER STANDARD PIPELINE (scoped) ===
      |
      v
 [S1: Brainstorming]        <-- Scoped to remaining work
      |
      v
 [S2: Research]              <-- SKIP if tech stack is fixed
      |
      v
 [S3: Architecture]          <-- SKIP if architecture is recovered
      |
      v
 [S4: Planning]              <-- Plan only remaining tasks (no scaffold)
      |
      v
 [S5: Implementation]        <-- Build only missing pieces
      |                           (no scaffold, work on existing code)
      v
 [S6: Quality Assurance]     <-- Review new + changed code only
      |
      v
 [S7: Testing]               <-- Generate tests for new code + increase coverage
      |
      v
 [S8: Debug/Fix]
      |
      v
 [S9: Documentation]         <-- Update existing docs, don't overwrite
      |
      v
 [S10: Deploy & Deliver]     <-- SKIP if CI/CD already exists, else enhance
```

**Key Differences from Greenfield:**
- Three new pre-phases: Codebase Analysis, Architecture Recovery, Gap Analysis
- No Template/Scaffold phase (code already exists)
- Implementation works on existing codebase (no worktree isolation by default)
- Review focuses on changed files only
- Testing augments existing tests rather than generating from scratch
- Documentation updates rather than creates
- Research may be skipped if tech stack is fixed

**Codebase Analysis Sequence:**

```
 User          Orchestrator      Analyzer        Git           Codebase
  |                 |                |              |              |
  | Submit repo URL |                |              |              |
  |---------------->|                |              |              |
  |                 | Clone repo     |              |              |
  |                 |-------------------------------->|              |
  |                 |                |         cloned|              |
  |                 |<-------------------------------|              |
  |                 |                |              |              |
  |                 | Analyze        |              |              |
  |                 |--------------->|              |              |
  |                 |                | Scan files   |              |
  |                 |                |----------------------------->|
  |                 |                | Detect tech  |              |
  |                 |                |---+          |              |
  |                 |                |<--+          |              |
  |                 |                |              |              |
  |                 |                | Map structure|              |
  |                 |                |---+          |              |
  |                 |                |<--+          |              |
  |                 |                |              |              |
  |                 |                | Find patterns|              |
  |                 |                |---+          |              |
  |                 |                |<--+          |              |
  |                 |                |              |              |
  |                 | Analysis report|              |              |
  |                 |<---------------|              |              |
  |                 |                |              |              |
  | Codebase summary|               |              |              |
  |<----------------|                |              |              |
```

**Architecture Recovery Output:**

```json
{
  "recovered_architecture": {
    "detected_tech_stack": {
      "frontend": "React 18 + TypeScript + Tailwind",
      "backend": "Express.js + TypeScript",
      "database": "PostgreSQL + Prisma ORM",
      "infrastructure": "Docker + GitHub Actions"
    },
    "inferred_c4": {
      "context": { },
      "containers": ["web-app", "api-server", "database", "redis-cache"],
      "components": { }
    },
    "api_contracts": {
      "extracted_from": "route files",
      "endpoints": [ ]
    },
    "database_schema": {
      "extracted_from": "prisma/schema.prisma",
      "models": [ ]
    },
    "test_coverage": {
      "current": 45,
      "tested_modules": [ ],
      "untested_modules": [ ]
    },
    "technical_debt": [
      {
        "type": "missing_error_handling",
        "files": ["src/api/users.ts"],
        "severity": "medium"
      }
    ]
  }
}
```

---

### 5.3 Brownfield Workflow

**Description:** Flow for modernizing legacy codebases. CodeBot assesses the legacy system, develops a modernization strategy, and incrementally refactors with comprehensive test coverage to prevent regressions.

```
 BROWNFIELD PIPELINE:

 [User Input + Legacy Repo URL + Modernization Goals]
      |
      v
 [Legacy Assessment]        <-- PRE-PIPELINE: Deep legacy analysis
      |
      +-- Identify deprecated dependencies
      +-- Detect anti-patterns
      +-- Map coupling and cohesion
      +-- Assess test coverage (usually very low)
      +-- Identify security vulnerabilities
      +-- Estimate modernization effort
      |
      v
 [Modernization Strategy]   <-- PRE-PIPELINE: Plan the transformation
      |
      +-- Strangler Fig pattern vs Big Bang
      +-- Identify modules to modernize first
      +-- Define target architecture
      +-- Create migration path
      +-- Risk assessment
      |
      v
 [Safety Net Creation]      <-- PRE-PIPELINE: Tests before changes
      |
      +-- Generate characterization tests (capture current behavior)
      +-- Generate integration tests for critical paths
      +-- Set up regression detection
      +-- Establish baseline metrics
      |
      v
 === ENTER STANDARD PIPELINE (assessment-informed) ===
      |
      v
 [Incremental Modernization] <-- S5: Iterative refactoring
      |
      +-- For each module (in dependency order):
      |     1. Add/improve tests for module
      |     2. Refactor module to target architecture
      |     3. Run full test suite
      |     4. If tests pass -> commit, next module
      |     5. If tests fail -> fix or rollback
      |
      v
 [Dependency Modernization]  <-- Update deps separately
      |
      +-- Update one dependency at a time
      +-- Run tests after each update
      +-- Resolve breaking changes
      |
      v
 [S6: Quality Assurance]
      |
      v
 [S7: Testing]               <-- Full regression suite
      |
      v
 [S8: Debug/Fix]
      |
      v
 [S9: Documentation]
      |
      v
 [S10: Deploy & Deliver]
```

**Key Differences from Greenfield:**
- Three new pre-phases: Legacy Assessment, Modernization Strategy, Safety Net
- No Brainstorming/Planning/Research (replaced by assessment and strategy)
- Implementation is incremental and cautious (one module at a time)
- Tests are created BEFORE making changes (safety net)
- Characterization tests capture existing behavior even if undocumented
- Dependency updates are isolated and tested individually
- Much higher emphasis on regression prevention

**Modernization Strategy Decision Tree:**

```
 [ASSESS_CODEBASE]
      |
      v
 [EVALUATE_MODERNIZATION_APPROACH]
      |
      +---> Codebase < 10K LOC
      |         |
      |         v
      |    [BIG_BANG_REWRITE]
      |    (rebuild from scratch using Greenfield workflow)
      |
      +---> Codebase 10K-100K LOC, modular
      |         |
      |         v
      |    [STRANGLER_FIG_PATTERN]
      |    (gradually replace modules)
      |         |
      |         +-- 1. Build new module alongside legacy
      |         +-- 2. Route traffic to new module
      |         +-- 3. Retire legacy module
      |         +-- 4. Repeat for next module
      |
      +---> Codebase >100K LOC or tightly coupled
      |         |
      |         v
      |    [INCREMENTAL_REFACTORING]
      |    (refactor in place, one function/class at a time)
      |         |
      |         +-- 1. Add tests around target code
      |         +-- 2. Extract function/class
      |         +-- 3. Apply modern patterns
      |         +-- 4. Verify tests still pass
      |         +-- 5. Repeat
      |
      +---> Legacy framework with no path forward
                |
                v
           [HYBRID_APPROACH]
           (new features in new stack, legacy maintained separately)
                |
                +-- 1. Set up new stack alongside legacy
                +-- 2. Build API gateway to route between old/new
                +-- 3. All new features go to new stack
                +-- 4. Migrate existing features over time
```

**Safety Net Test Generation:**

```
 [ANALYZE_LEGACY_CODE]
      |
      v
 [IDENTIFY_CRITICAL_PATHS]
      |
      +--- User authentication flow
      +--- Payment processing
      +--- Data CRUD operations
      +--- External API integrations
      |
      v
 [GENERATE_CHARACTERIZATION_TESTS]
      |
      +--- For each critical path:
      |      1. Record current input/output behavior
      |      2. Generate test that asserts current behavior
      |      3. Test passes = behavior captured
      |      4. Any future change that breaks test = regression
      |
      v
 [ESTABLISH_BASELINE_METRICS]
      |
      +--- Response times
      +--- Memory usage
      +--- Error rates
      +--- Test coverage percentage
      |
      v
 [SAFETY_NET_READY]
      (proceed with modernization only after this point)
```

---

## 6. Error Handling & Recovery Workflows

### 6.1 Agent Failure Recovery

```
 AGENT FAILURE RECOVERY:

 [AGENT_EXECUTING]
      |
      +---> [SUCCESS] ---> continue pipeline
      |
      +---> [ERROR]
               |
               v
          [CLASSIFY_ERROR]
               |
        +------+------+------+
        |      |      |      |
   transient  LLM   code   fatal
        |      |      |      |
        v      v      v      v
   [RETRY]  [SWITCH  [FIX   [ESCALATE]
    (exp     MODEL]  CODE]      |
    backoff)    |      |        v
        |      v      v    [HUMAN_
        |   [RETRY   [RETRY INTERVENTION]
        |    WITH     WITH
        |    NEW      FIX]
        |    MODEL]
        |      |      |
        +------+------+
               |
          (attempts < max_retries?)
               |
          +----+----+
          |         |
        yes        no
          |         |
          v         v
       [RETRY]  [ESCALATE]
```

**Retry Policy:**

```json
{
  "retry_policy": {
    "max_retries": 3,
    "backoff": {
      "type": "exponential",
      "initial_delay_ms": 1000,
      "max_delay_ms": 30000,
      "multiplier": 2.0,
      "jitter": true
    },
    "retryable_errors": [
      "rate_limit_exceeded",
      "timeout",
      "connection_error",
      "internal_server_error",
      "model_overloaded"
    ],
    "non_retryable_errors": [
      "invalid_api_key",
      "content_policy_violation",
      "context_window_exceeded"
    ]
  }
}
```

**Fallback Strategy Per Error Type:**

| Error Type | Retry? | Fallback | Ultimate Action |
|------------|--------|----------|-----------------|
| Rate limit | Yes (with backoff) | Switch provider | Queue for later |
| Timeout | Yes (2x timeout) | Reduce context size | Split into smaller tasks |
| Model overloaded | Yes (with backoff) | Switch to fallback model | Queue for later |
| Context too large | No | Summarize context | Split task |
| Invalid output | Yes (with feedback) | Switch model | Escalate |
| Code compilation error | Yes (with error) | Try different approach | Escalate |
| Fatal/unknown | No | None | Escalate immediately |

### 6.2 Pipeline Failure Recovery

**Description:** Recovery strategies when the entire pipeline or a phase fails, not just a single agent.

```
 PIPELINE FAILURE RECOVERY:

 [PHASE_FAILURE]
      |
      v
 [SAVE_FAILURE_CHECKPOINT]
      |
      v
 [CLASSIFY_FAILURE_SCOPE]
      |
      +---> Single agent failed
      |         |
      |         v
      |    [RESTART_AGENT]
      |    (see 6.1 Agent Failure Recovery)
      |
      +---> Multiple agents failed in same phase
      |         |
      |         v
      |    [ROLLBACK_PHASE]
      |         |
      |         +-- Restore phase checkpoint
      |         +-- Restart all phase agents
      |         +-- Re-execute phase from beginning
      |         |
      |         v
      |    [RE_EXECUTE_PHASE]
      |         |
      |    +----+----+
      |    |         |
      |  success    fail again
      |    |         |
      |    v         v
      |  [CONTINUE] [ESCALATE_TO_HUMAN]
      |
      +---> Infrastructure failure (git, storage, network)
      |         |
      |         v
      |    [WAIT_AND_RETRY]
      |         |
      |         +-- Exponential backoff up to 5 min
      |         +-- Check infrastructure health
      |         |
      |         v
      |    (recovered?)
      |    +----+----+
      |    |         |
      |  yes        no
      |    |         |
      |    v         v
      | [RESUME]  [PAUSE_PIPELINE]
      |           [NOTIFY_USER]
      |
      +---> Unrecoverable error
                |
                v
           [SAVE_ALL_STATE]
                |
                v
           [GENERATE_DIAGNOSTIC_REPORT]
                |
                v
           [NOTIFY_USER_WITH_REPORT]
                |
                v
           [PAUSE_PIPELINE_INDEFINITELY]
```

**Partial Pipeline Re-execution:**

```
 When resuming after a failure, the pipeline does NOT restart from the beginning.
 Instead, it uses the checkpoint system:

 Example: Failure during Implementation phase

 [Checkpoint: phase_04_planning.json]   <-- Last successful phase
      |
      v
 [Skip: S0 Initialization]     already completed
 [Skip: S1 Brainstorming]      already completed
 [Skip: S2 Research]            already completed
 [Skip: S3 Architecture]       already completed
 [Skip: S4 Planning & Config]  already completed
      |
      v
 [Resume: S5 Implementation]   <-- Re-execute from here
      |
      v
 [Continue: S6 QA, S7 Testing, etc.]
```

### 6.3 LLM Rate Limiting Handling

```
 LLM RATE LIMITING STRATEGY:

 [API_REQUEST]
      |
      v
 [CHECK_RATE_LIMIT_STATUS]
      |
      +---> [WITHIN_LIMITS] ---> [SEND_REQUEST]
      |                               |
      |                          +----+----+
      |                          |         |
      |                       success    rate_limited
      |                          |         |
      |                          v         v
      |                    [RETURN]   [HANDLE_LIMIT]
      |
      +---> [APPROACHING_LIMIT] (>80% of quota)
      |         |
      |         v
      |    [THROTTLE]
      |         |
      |         +-- Reduce request frequency
      |         +-- Batch smaller requests
      |         +-- Delay non-critical requests
      |         |
      |         v
      |    [SEND_THROTTLED]
      |
      +---> [AT_LIMIT]
               |
               v
          [QUEUE_REQUEST]
               |
               v
          [CHECK_ALTERNATIVE_PROVIDERS]
               |
          +----+----+
          |         |
       available  none available
          |         |
          v         v
     [ROUTE_TO    [WAIT_FOR_RESET]
      FALLBACK]       |
          |           +-- Track reset time per provider
          v           +-- Notify if wait > 5 min
     [SEND_TO        |
      FALLBACK]      v
                [RETRY_AFTER_RESET]
```

**Provider Rotation Strategy:**

```
 PROVIDER ROTATION:

 Request Queue:  [R1] [R2] [R3] [R4] [R5] [R6] ...
                  |    |    |    |    |    |
 Provider Pool:   |    |    |    |    |    |
                  v    v    v    v    v    v
 Provider A:     R1        R3        R5         (33% of traffic)
 Provider B:          R2        R4              (33% of traffic)
 Provider C:                              R6    (33% of traffic)

 When Provider A is rate-limited:
 Provider A:     [PAUSED - reset in 60s]
 Provider B:     R1   R2   R3   R4              (50% of traffic)
 Provider C:                    R5   R6         (50% of traffic)
```

**Backpressure Mechanism:**

```
 [MONITOR_QUEUE_DEPTH]
      |
      +---> depth < 10  ---> [NORMAL_PROCESSING]
      |
      +---> depth 10-50 ---> [SLOW_DOWN_PRODUCERS]
      |                           |
      |                           +-- Reduce agent parallelism
      |                           +-- Increase batch sizes
      |                           +-- Defer non-critical work
      |
      +---> depth > 50  ---> [APPLY_BACKPRESSURE]
                                   |
                                   +-- Pause new agent spawning
                                   +-- Complete current tasks only
                                   +-- Alert user of delay
```

### 6.4 Error Taxonomy

All errors encountered during pipeline execution are classified into five categories, each with a defined response strategy:

| Category | Description | Strategy | Details |
|----------|-------------|----------|---------|
| **Transient** | Temporary failures (network blips, rate limits) | Retry with exponential backoff (max 3), then fallback provider | If all retries exhausted, route to fallback LLM provider |
| **Recoverable** | Errors that can be fixed programmatically | Route to Debugger agent for automated fix | Debugger analyzes error context and generates a patch |
| **Blocking** | Errors requiring human judgment | Pause pipeline, emit notification, wait for user input | Pipeline state preserved; user notified via all configured channels |
| **Fatal** | Unrecoverable system errors | Stop pipeline, preserve checkpoint, alert user | Full diagnostic report generated; pipeline can be resumed after manual fix |
| **Quality Gate** | Phase output does not meet quality threshold | Block phase transition, route to appropriate fix agent | Fix agent attempts remediation; escalates to human after max retries |

### 6.5 Dead Letter Queue (DLQ) Workflow

Failed messages that exhaust all retry attempts are routed to a Dead Letter Queue for manual inspection and replay.

```
 DEAD LETTER QUEUE WORKFLOW:

 [MESSAGE_FAILED]
      |
      v
 [RETRY_WITH_BACKOFF]
      |
 (attempts < max_retries?)
      |
 +----+----+
 |         |
 yes       no
 |         |
 v         v
[RETRY]  [ROUTE_TO_DLQ]
              |
              v
         [DLQ_STORAGE]
              |
              +-- Store original message
              +-- Store error context
              +-- Store retry history
              +-- Timestamp entry
              |
              v
         [DLQ_DASHBOARD]
              |
              +-- Display DLQ items for manual inspection
              +-- Allow filtering by error type, agent, phase
              +-- Provide replay capability per item or batch
              |
              v
         [MANUAL_ACTION]
              |
              +---> [REPLAY] ---> Re-inject message into pipeline
              +---> [DISCARD] ---> Mark as resolved, archive
              +---> [MODIFY_AND_REPLAY] ---> Edit payload, re-inject
```

### 6.6 Circuit Breaker Workflow

Prevents cascading failures by tracking consecutive errors per LLM provider and automatically routing to fallback providers.

```
 CIRCUIT BREAKER STATE MACHINE:

 +----------+     5 consecutive     +----------+     60s timeout     +-----------+
 |  CLOSED  |---  failures  ------->|   OPEN   |--- elapsed ------->| HALF-OPEN |
 | (normal) |                       | (reject  |                    | (test one |
 +----------+                       |  all)    |                    |  request) |
      ^                             +----------+                    +-----------+
      |                                  ^                               |
      |                                  |                          +----+----+
      |                                  |                          |         |
      +---------- success --------------+                        success   failure
                                                                    |         |
                                                                    v         v
                                                              [CLOSE]   [RE-OPEN]
```

**Circuit Breaker Rules:**

- **Track** consecutive failures per LLM provider
- **Open** circuit after 5 consecutive failures — all requests routed to fallback provider
- **Half-open** after 60 seconds — send a single test request to the original provider
- **Close** circuit if test request succeeds — resume normal routing
- **Re-open** circuit if test request fails — restart the 60s timeout

---

## 7. Human-in-the-Loop Workflows

### 7.1 Approval Gates

**Description:** Structured decision points where the pipeline pauses for human review and approval before proceeding.

```
 APPROVAL GATE FLOW:

 [PHASE_COMPLETE]
      |
      v
 [PREPARE_GATE_PACKAGE]
      |
      +-- Summary of phase output
      +-- Key decisions made
      +-- Risks identified
      +-- Recommended next steps
      +-- Estimated cost for next phase
      |
      v
 [PRESENT_TO_USER]
      |
      +-- Dashboard notification
      +-- Email notification (if configured)
      +-- Slack notification (if configured)
      |
      v
 [AWAIT_RESPONSE]
      |
      +---> [APPROVED] ---> [PROCEED_TO_NEXT_PHASE]
      |
      +---> [REJECTED]
      |         |
      |         v
      |    [CAPTURE_FEEDBACK]
      |         |
      |         v
      |    [RE_ENTER_PHASE_WITH_FEEDBACK]
      |
      +---> [MODIFY]
      |         |
      |         v
      |    [APPLY_MODIFICATIONS]
      |         |
      |         v
      |    [RE_EVALUATE_GATE]
      |
      +---> [TIMEOUT] (configurable, default 30 min)
               |
               v
          [AUTO_APPROVE_WITH_LOG]
          (unless configured as mandatory)
```

**Gate Configuration:**

```json
{
  "gate_config": {
    "G1_requirements": {
      "type": "approval",
      "mandatory": true,
      "timeout_minutes": 30,
      "timeout_action": "auto_approve",
      "notify_channels": ["dashboard", "email"],
      "auto_skip_in_mode": "autopilot"
    },
    "G3_architecture": {
      "type": "approval",
      "mandatory": true,
      "timeout_minutes": 30,
      "timeout_action": "auto_approve",
      "notify_channels": ["dashboard", "email"],
      "auto_skip_in_mode": "autopilot"
    },
    "G10_deployment": {
      "type": "approval",
      "mandatory": false,
      "timeout_minutes": 15,
      "timeout_action": "auto_approve",
      "notify_channels": ["dashboard"],
      "auto_skip_in_mode": "autopilot"
    }
  }
}
```

### 7.2 Clarification Requests

**Description:** When agents encounter ambiguous requirements or need human input to make a decision.

```
 CLARIFICATION REQUEST FLOW:

 [AGENT_ENCOUNTERS_AMBIGUITY]
      |
      v
 [FORMULATE_QUESTION]
      |
      +-- Specific, actionable question
      +-- Context for why this matters
      +-- Default answer if user doesn't respond
      +-- Impact assessment for each option
      |
      v
 [SEND_TO_USER]
      |
      v
 [AWAIT_RESPONSE]
      |
      +---> [USER_RESPONDS]
      |         |
      |         v
      |    [VALIDATE_RESPONSE]
      |         |
      |    +----+----+
      |    |         |
      |  valid    ambiguous
      |    |         |
      |    v         v
      | [APPLY]   [ASK_FOLLOWUP]
      |    |         |
      |    v         +---> (loop, max 3 followups)
      | [CONTINUE]
      |
      +---> [TIMEOUT] (default: 15 min)
               |
               v
          [USE_DEFAULT_ANSWER]
               |
               v
          [LOG_ASSUMPTION]
               |
               v
          [CONTINUE_WITH_ASSUMPTION]
```

**Timeout Handling for Unresponsive Humans:**

| Timeout Stage | Duration | Action |
|---------------|----------|--------|
| First reminder | 5 min | Dashboard notification |
| Second reminder | 10 min | Email notification |
| Third reminder | 15 min | Use default answer, log assumption |
| Pipeline pause | 60 min (critical only) | Pause pipeline entirely |

### 7.3 Real-time Collaboration

**Description:** How humans and agents can work simultaneously on the same codebase, with conflict resolution and live feedback.

```
 REAL-TIME COLLABORATION MODEL:

 +-------------------+                    +-------------------+
 |  HUMAN EDITOR     |                    |  AGENT EDITOR     |
 |  (VS Code, etc.)  |                    |  (CodeBot Agent)  |
 +-------------------+                    +-------------------+
          |                                         |
          |    File change event                    |
          |-------->+                               |
          |         |                               |
          |    +----v----+                          |
          |    | CHANGE  |                          |
          |    | DETECTOR|     File change event    |
          |    +----+----+<-------------------------|
          |         |                               |
          |    +----v---------+                     |
          |    | CONFLICT     |                     |
          |    | RESOLUTION   |                     |
          |    +----+---------+                     |
          |         |                               |
          |    +----+----+                          |
          |    |         |                          |
          |  no conflict  conflict                  |
          |    |         |                          |
          |    v         v                          |
          |  [MERGE]  [RESOLVE]                     |
          |    |         |                          |
          |    |    +----+----+                     |
          |    |    |         |                     |
          |    |  human     agent                   |
          |    |  wins      wins                    |
          |    |  (default)  (explicit)              |
          |    |    |         |                     |
          |    v    v         v                     |
          |  [APPLY_MERGED_STATE]                   |
          |         |                               |
          |    [SYNC_TO_BOTH_EDITORS]               |
          |<--------|                               |
          |         |------>----------------------->|
```

**Conflict Resolution Rules:**

| Scenario | Resolution | Rationale |
|----------|------------|-----------|
| Human edits file agent is working on | Human wins, agent adapts | Human intent takes priority |
| Agent edits file human is viewing | Agent proceeds, human sees diff | Non-blocking for agent |
| Both edit same line | Human wins | Human intent is authoritative |
| Human reverts agent's change | Agent skips that file | Respect human decision |
| Human provides inline feedback | Agent reads and incorporates | Live feedback loop |

**Live Feedback Loop:**

```
 [HUMAN_ADDS_COMMENT_IN_CODE]
      |
      | // TODO: CodeBot, use a different approach here
      |
      v
 [AGENT_DETECTS_COMMENT]
      |
      v
 [PARSE_INSTRUCTION]
      |
      v
 [ADJUST_IMPLEMENTATION]
      |
      v
 [NOTIFY_HUMAN_OF_CHANGE]
      |
      v
 [HUMAN_REVIEWS]
      |
      +---> [ACCEPTS] ---> continue
      |
      +---> [ADDS_MORE_FEEDBACK] ---> loop back
```

---

## 8. Multi-LLM Routing Workflows

### 8.1 Task Classification and Model Selection

```
 [INCOMING_TASK]
      |
      v
 [CLASSIFY_TASK]
      |
      +--- Task type (architecture, code_gen, review, research, docs, simple)
      +--- Complexity (low, medium, high, critical)
      +--- Context size (small <4K, medium <16K, large <64K, huge >64K)
      +--- Latency requirement (real-time, normal, batch)
      |
      v
 [LOOKUP_ROUTING_TABLE]
      |
      +---> [USER_OVERRIDE_EXISTS?]
      |         |
      |    +----+----+
      |    |         |
      |  yes        no
      |    |         |
      |    v         v
      | [USE_USER   [USE_DEFAULT
      |  MODEL]      ROUTING]
      |    |         |
      |    +----+----+
      |         |
      v         v
 [CHECK_MODEL_AVAILABILITY]
      |
      +---> [AVAILABLE] ---> [DISPATCH_TO_MODEL]
      |
      +---> [UNAVAILABLE]
               |
               v
          [USE_FALLBACK_CHAIN]
```

**Routing Table:**

```
 +------------------+-----------+-----------------+------------------+-----------------+
 | Task Type        | Complexity| Primary Model   | Fallback 1       | Fallback 2      |
 +------------------+-----------+-----------------+------------------+-----------------+
 | Architecture     | High      | Claude Opus     | GPT-4.1          | Gemini 2.5 Pro  |
 | Architecture     | Medium    | Claude Sonnet   | GPT-4.1          | Gemini 2.5 Pro  |
 | Code Generation  | High      | Claude Sonnet   | GPT-4.1          | Gemini 2.5 Pro  |
 | Code Generation  | Medium    | Claude Sonnet   | GPT-4.1-mini     | Gemini Flash    |
 | Code Generation  | Low       | Claude Haiku    | GPT-4.1-mini     | Gemini Flash    |
 | Code Review      | Any       | Claude Opus     | GPT-4.1          | Gemini 2.5 Pro  |
 | Research         | Any       | Gemini 2.5 Pro  | Claude Sonnet    | GPT-4.1         |
 | Testing          | High      | Claude Sonnet   | GPT-4.1          | Gemini 2.5 Pro  |
 | Testing          | Low       | Claude Haiku    | GPT-4.1-mini     | Gemini Flash    |
 | Documentation    | Any       | Gemini 2.5 Pro  | Claude Sonnet    | GPT-4.1         |
 | Simple/Format    | Low       | Claude Haiku    | GPT-4.1-mini     | Gemini Flash    |
 | Debug/Fix        | High      | Claude Opus     | GPT-4.1          | Gemini 2.5 Pro  |
 | Debug/Fix        | Medium    | Claude Sonnet   | GPT-4.1          | Gemini 2.5 Pro  |
 | Security Audit   | Any       | Claude Opus     | GPT-4.1          | Gemini 2.5 Pro  |
 | Brainstorming    | Any       | Claude Opus     | GPT-4.1          | Gemini 2.5 Pro  |
 | Planning         | Any       | Claude Sonnet   | GPT-4.1          | Gemini 2.5 Pro  |
 +------------------+-----------+-----------------+------------------+-----------------+
```

### 8.2 Cost Optimization Routing

```
 [TASK_RECEIVED]
      |
      v
 [ESTIMATE_COST]
      |
      +--- Input tokens (from context size)
      +--- Expected output tokens (from task type)
      +--- Model pricing lookup
      |
      v
 [CHECK_BUDGET]
      |
      +---> [WITHIN_BUDGET] ---> [USE_OPTIMAL_MODEL]
      |
      +---> [APPROACHING_LIMIT]  (>80% of budget)
      |         |
      |         v
      |    [DOWNGRADE_MODEL]
      |         |
      |         +--- Opus -> Sonnet
      |         +--- Sonnet -> Haiku
      |         +--- GPT-4.1 -> GPT-4.1-mini
      |         +--- Gemini Pro -> Gemini Flash
      |         |
      |         v
      |    [USE_DOWNGRADED_MODEL]
      |
      +---> [BUDGET_EXCEEDED]
               |
               v
          [NOTIFY_USER]
               |
          +----+----+
          |         |
       increase  stop
          |         |
          v         v
       [CONTINUE] [PAUSE_PIPELINE]
```

**Cost Tracking:**

```
 +------------------+----------------+----------------+
 | Model            | Input $/1M tok | Output $/1M tok|
 +------------------+----------------+----------------+
 | Claude Opus      | $15.00         | $75.00         |
 | Claude Sonnet    | $3.00          | $15.00         |
 | Claude Haiku     | $0.25          | $1.25          |
 | GPT-4.1          | $2.00          | $8.00          |
 | GPT-4.1-mini     | $0.40          | $1.60          |
 | Gemini 2.5 Pro   | $1.25          | $10.00         |
 | Gemini 2.5 Flash | $0.15          | $0.60          |
 +------------------+----------------+----------------+

 Budget Allocation (default per project):

 +------+----------------------------+-------------+
 | Stage| Phase                      | Budget %    |
 +------+----------------------------+-------------+
 | S0   | Initialization             | 1%          |
 | S1   | Brainstorming              | 3%          |
 | S2   | Research                   | 5%          |
 | S3   | Architecture & Design      | 12%         |
 | S4   | Planning & Configuration   | 7%          |
 | S5   | Implementation             | 35%         |
 | S6   | Quality Assurance          | 7%          |
 | S7   | Testing                    | 10%         |
 | S8   | Debug & Stabilization      | 10%         |
 | S9   | Documentation & Knowledge  | 5%          |
 | S10  | Deployment & Delivery      | 5%          |
 +------+----------------------------+-------------+
```

### 8.3 Self-Hosted LLM Routing

**Description:** For offline or private development, CodeBot supports routing to self-hosted LLMs via compatible APIs (Ollama, vLLM, text-generation-inference).

```
 SELF-HOSTED ROUTING:

 [TASK]
      |
      v
 [CHECK_CONNECTIVITY]
      |
      +---> [ONLINE] ---> [USE_CLOUD_PROVIDERS]
      |                    (normal routing table)
      |
      +---> [OFFLINE / PRIVATE_MODE]
               |
               v
          [DISCOVER_LOCAL_MODELS]
               |
               +--- Scan Ollama endpoints
               +--- Scan vLLM endpoints
               +--- Scan custom OpenAI-compatible endpoints
               |
               v
          [MAP_TO_ROUTING_TABLE]
               |
               +--- llama-3.1-70b  -> replaces Claude Sonnet tier
               +--- llama-3.1-8b   -> replaces Claude Haiku tier
               +--- codestral      -> replaces code generation tier
               +--- qwen-2.5-72b   -> replaces Gemini Pro tier
               |
               v
          [ROUTE_WITH_LOCAL_MODELS]
               |
               +--- Adjust context windows
               +--- Adjust quality expectations
               +--- Log quality degradation warnings
```

### 8.4 Fallback Chain Execution

```
 [DISPATCH_REQUEST]
      |
      v
 [TRY_PRIMARY_MODEL]
      |
      +---> [SUCCESS]
      |         |
      |         v
      |    [RECORD_METRICS]
      |         |
      |         +--- latency
      |         +--- token usage
      |         +--- cost
      |         +--- quality score
      |         |
      |         v
      |    [RETURN_RESULT]
      |
      +---> [FAILURE]
               |
               v
          [LOG_FAILURE]
               |
               v
          [TRY_FALLBACK_1]
               |
               +---> [SUCCESS] ---> [RECORD_METRICS] ---> [RETURN_RESULT]
               |
               +---> [FAILURE]
                        |
                        v
                   [TRY_FALLBACK_2]
                        |
                        +---> [SUCCESS] ---> [RECORD_METRICS] ---> [RETURN_RESULT]
                        |
                        +---> [FAILURE]
                                 |
                                 v
                            [ALL_PROVIDERS_FAILED]
                                 |
                                 v
                            [QUEUE_FOR_RETRY]
                                 |
                                 +--- Wait for shortest rate-limit reset
                                 +--- Notify user if delay > 5 min
                                 |
                                 v
                            [RETRY_FROM_PRIMARY]
```

---

## 9. Sequence Diagrams

### 9.1 Complete Pipeline Execution

```
 User        Orch       Brain    Research   Arch     Design    DB      API GW   Plan
  |            |           |        |         |        |        |        |        |
  | Idea       |           |        |         |        |        |        |        |
  |----------->|           |        |         |        |        |        |        |
  |            | S1: Start |        |         |        |        |        |        |
  |            |---------->|        |         |        |        |        |        |
  |            |           |        |         |        |        |        |        |
  | Q&A loop   |           |        |         |        |        |        |        |
  |<---------->|<--------->|        |         |        |        |        |        |
  |            |           |        |         |        |        |        |        |
  | Confirm    |           |        |         |        |        |        |        |
  |----------->| G1 OK     |        |         |        |        |        |        |
  |            |           |        |         |        |        |        |        |
  |            | S2: Start |        |         |        |        |        |        |
  |            |------------------>|         |        |        |        |        |
  |            |           | Report |         |        |        |        |        |
  |            |<------------------|         |        |        |        |        |
  |            | G2 OK     |        |         |        |        |        |        |
  |            |           |        |         |        |        |        |        |
  |            | S3: Fan-out (parallel)       |        |        |        |        |
  |            |------------------------------>|        |        |        |        |
  |            |-------------------------------------->|        |        |        |
  |            |--------------------------------------------->|        |        |
  |            |--------------------------------------------------->|        |
  |            |           |        |  Docs   | Wireframes| Schema| Spec|        |
  |            |<------------------------------|        |        |        |        |
  |            |<--------------------------------------|        |        |        |
  |            |<----------------------------------------------|        |        |
  |            |<------------------------------------------------------|        |
  |            | G3 OK     |        |         |        |        |        |        |
  |            |           |        |         |        |        |        |        |
  | Approve    |           |        |         |        |        |        |        |
  | arch       |           |        |         |        |        |        |        |
  |<-----------|           |        |         |        |        |        |        |
  |----------->|           |        |         |        |        |        |        |
  |            |           |        |         |        |        |        |        |
  |            | S4: Plan  |        |         |        |        |        |        |
  |            |---------------------------------------------------------------->|
  |            |           |        |  Tasks  |        |        |        |        |
  |            |<----------------------------------------------------------------|
  | Approve    |           |        |         |        |        |        |        |
  | plan+stack |           |        |         |        |        |        |        |
  |<-----------|           |        |         |        |        |        |        |
  |----------->| G4 OK     |        |         |        |        |        |        |
```

```
 (continued)

 User   Orch    TechSt  Template  FE     BE      MW     Infra   Review  Test   Debug
  |      |        |        |       |      |       |       |       |       |       |
  |      | Stack  |        |       |      |       |       |       |       |       |
  |      |------->|        |       |      |       |       |       |       |       |
  |      |<-------|        |       |      |       |       |       |       |       |
  | Pick |        |        |       |      |       |       |       |       |       |
  |<---->|        |        |       |      |       |       |       |       |       |
  |      | G6     |        |       |      |       |       |       |       |       |
  |      |        | Scaffold       |      |       |       |       |       |       |
  |      |--------------->|       |      |       |       |       |       |       |
  |      |<---------------|       |      |       |       |       |       |       |
  |      |        |        |       |      |       |       |       |       |       |
  |      | Implementation (parallel worktrees)    |       |       |       |       |
  |      |----------------------------->|      |       |       |       |       |
  |      |-------------------------------------->|       |       |       |       |
  |      |--------------------------------------------->|       |       |       |
  |      |--------------------------------------------------->|       |       |
  |      |        |        |  done |      |       |       |       |       |       |
  |      |<-----------------------------|      |       |       |       |       |
  |      |<---------------------------------------|       |       |       |       |
  |      |<----------------------------------------------|       |       |       |
  |      |<----------------------------------------------------|       |       |
  |      | Merge + G5     |       |      |       |       |       |       |       |
  |      |        |        |       |      |       |       |       |       |       |
  |      | Review (parallel)      |      |       |       |       |       |       |
  |      |---------------------------------------------------------------->|     |
  |      |<----------------------------------------------------------------|     |
  |      | G6 OK  |        |       |      |       |       |       |       |       |
  |      |        |        |       |      |       |       |       |       |       |
  |      | Test   |        |       |      |       |       |       |       |       |
  |      |------------------------------------------------------------------------>|
  |      |<------------------------------------------------------------------------|
  |      |        |        |       |      |       |       |       |       |       |
  |      | Debug loop     |       |      |       |       |       |       |       |
  |      |--------------------------------------------------------------------------->|
  |      |<----------------------------------------------------------------------------|
  |      |        |        |       |      |       |       |       |       |       |
  | Done |        |        |       |      |       |       |       |       |       |
  |<-----|        |        |       |      |       |       |       |       |       |
```

### 9.2 Debug/Fix Loop

```
 Orchestrator      Debugger         Tester         Codebase
     |                |                |               |
     | 7 failures     |                |               |
     |--------------->|                |               |
     |                |                |               |
     |   === ITERATION 1 ===          |               |
     |                |                |               |
     |                | Prioritize     |               |
     |                |---+            |               |
     |                |<--+            |               |
     |                |                |               |
     |                | Fix #1 (critical)              |
     |                |---+            |               |
     |                |<--+            |               |
     |                | Apply fix      |               |
     |                |------------------------------->|
     |                |                |               |
     |                | Run targeted   |               |
     |                |--------------->|               |
     |                | PASS           |               |
     |                |<---------------|               |
     |                |                |               |
     |                | Fix #2 (high)  |               |
     |                |---+            |               |
     |                |<--+            |               |
     |                | Apply fix      |               |
     |                |------------------------------->|
     |                |                |               |
     |                | Full suite     |               |
     |                |--------------->|               |
     |                | 5 pass,        |               |
     |                | 2 regress      |               |
     |                |<---------------|               |
     |                |                |               |
     |   === ITERATION 2 ===          |               |
     |                |                |               |
     |                | Fix regressions|               |
     |                |---+            |               |
     |                |<--+            |               |
     |                | Apply fixes    |               |
     |                |------------------------------->|
     |                |                |               |
     |                | Full suite     |               |
     |                |--------------->|               |
     |                | ALL PASS       |               |
     |                |<---------------|               |
     |                |                |               |
     | All pass       |                |               |
     |<---------------|                |               |
     |                |                |               |
     | -> Deployment  |                |               |
```

### 9.3 Agent Collaboration

```
 Architect        Designer        DB Agent       API GW Agent    Orchestrator
     |                |               |               |               |
     | Publish data   |               |               |               |
     | models         |               |               |               |
     |---+            |               |               |               |
     |<--+            |               |               |               |
     |                |               |               |               |
     |  data_models_published event   |               |               |
     |------------------------------->|               |               |
     |                |               |               |               |
     | Publish service|               |               |               |
     | boundaries     |               |               |               |
     |---+            |               |               |               |
     |<--+            |               |               |               |
     |                |               |               |               |
     |  service_boundaries event      |               |               |
     |----------------------------------------------->|               |
     |                |               |               |               |
     |                | Design        |               |               |
     |                | components    |               |               |
     |                |---+           |               |               |
     |                |<--+           |               |               |
     |                |               |               |               |
     |                | Request       |               |               |
     |                | feasibility   |               |               |
     |                | check         |               |               |
     |<---------------|               |               |               |
     | Feasible       |               |               |               |
     |--------------->|               |               |               |
     |                |               |               |               |
     |                |               | Schema done   |               |
     |                |               |---+           |               |
     |                |               |<--+           |               |
     |                |               |               |               |
     |                |               |               | Endpoints done|
     |                |               |               |---+           |
     |                |               |               |<--+           |
     |                |               |               |               |
     |                |               |               | Publish       |
     |                |               |               | API catalog   |
     |                |               |               |-------------->|
     |                |               |               |               |
     |                | Consume API   |               |               |
     |                | catalog for   |               |               |
     |                | UI flows      |               |               |
     |                |<----------------------------------------------|
     |                |               |               |               |
     |                |               |               |          Consistency
     |                |               |               |          check
     |                |               |               |          +----|
     |                |               |               |          |    |
     |                |               |               |          +--->|
     |                |               |               |               |
     |                |               |               |          All consistent
     |                |               |               |          G4 ready
```

### 9.4 Human Approval Flow

```
 Pipeline        Orchestrator       Dashboard        Email          User
     |                |                 |               |              |
     | Phase done     |                 |               |              |
     |--------------->|                 |               |              |
     |                |                 |               |              |
     |                | Prepare gate    |               |              |
     |                | package         |               |              |
     |                |---+             |               |              |
     |                |<--+             |               |              |
     |                |                 |               |              |
     |                | Notify          |               |              |
     |                |---------------->|               |              |
     |                |                 | Show approval |              |
     |                |                 | UI            |              |
     |                |                 |-------------->|----->------->|
     |                |                 |               |              |
     |                | Start timer     |               |              |
     |                | (30 min)        |               |              |
     |                |---+             |               |              |
     |                |<--+             |               |              |
     |                |                 |               |              |
     |                |                 |               |              |
     |                |     (scenario 1: user approves quickly)       |
     |                |                 |               |              |
     |                |                 |               |  Approve     |
     |                |                 |<-----------------------------|
     |                | Approved        |               |              |
     |                |<----------------|               |              |
     |                |                 |               |              |
     | Continue       |                 |               |              |
     |<---------------|                 |               |              |
     |                |                 |               |              |
     |                |                 |               |              |
     |                |     (scenario 2: user rejects)                |
     |                |                 |               |              |
     |                |                 |               |  Reject +    |
     |                |                 |               |  feedback    |
     |                |                 |<-----------------------------|
     |                | Rejected        |               |              |
     |                |<----------------|               |              |
     |                |                 |               |              |
     | Re-enter phase |                 |               |              |
     | with feedback  |                 |               |              |
     |<---------------|                 |               |              |
     |                |                 |               |              |
     |                |                 |               |              |
     |                |     (scenario 3: timeout)                     |
     |                |                 |               |              |
     |                | Timer expires   |               |              |
     |                |---+             |               |              |
     |                |<--+             |               |              |
     |                |                 |               |              |
     |                | Auto-approve    |               |              |
     |                | (log decision)  |               |              |
     |                |---+             |               |              |
     |                |<--+             |               |              |
     |                |                 |               |              |
     | Continue       |                 |               |              |
     | (auto-approved)|                 |               |              |
     |<---------------|                 |               |              |
```

### 9.5 Deployment Flow

```
 Orchestrator     DevOps       Infra Eng     GitHub       Cloud        Monitor
     |               |            |            |            |            |
     | Start deploy  |            |            |            |            |
     |-------------->|            |            |            |            |
     |               |            |            |            |            |
     |               | Gen CI/CD  |            |            |            |
     |               |---+        |            |            |            |
     |               |<--+        |            |            |            |
     |               |            |            |            |            |
     |               | Gen IaC    |            |            |            |
     |               |----------->|            |            |            |
     |               |            | Terraform  |            |            |
     |               |            |---+        |            |            |
     |               |            |<--+        |            |            |
     |               |            |            |            |            |
     |               |            | Docker     |            |            |
     |               |            |---+        |            |            |
     |               |            |<--+        |            |            |
     |               |            |            |            |            |
     |               | IaC ready  |            |            |            |
     |               |<-----------|            |            |            |
     |               |            |            |            |            |
     |               | Setup repo |            |            |            |
     |               |------------------------>|            |            |
     |               |            | Secrets    |            |            |
     |               |            |----------->|            |            |
     |               |            | Actions    |            |            |
     |               |            |----------->|            |            |
     |               |            |            |            |            |
     |               | Provision staging       |            |            |
     |               |---------------------------------------->|        |
     |               |            |            |     provisioned         |
     |               |<----------------------------------------|        |
     |               |            |            |            |            |
     |               | Build + Deploy staging  |            |            |
     |               |---------------------------------------->|        |
     |               |            |            |      deployed           |
     |               |<----------------------------------------|        |
     |               |            |            |            |            |
     |               | Smoke tests|            |            |            |
     |               |---------------------------------------->|        |
     |               |            |            |         pass            |
     |               |<----------------------------------------|        |
     |               |            |            |            |            |
     |               | Health check|           |            |            |
     |               |---------------------------------------->|        |
     |               |            |            |       healthy           |
     |               |<----------------------------------------|        |
     |               |            |            |            |            |
     | Staging OK    |            |            |            |            |
     |<--------------|            |            |            |            |
     |               |            |            |            |            |
     | [G10: Approve production?]  |            |            |            |
     |               |            |            |            |            |
     |               | Deploy production       |            |            |
     |               |---------------------------------------->|        |
     |               |            |            |      deployed           |
     |               |<----------------------------------------|        |
     |               |            |            |            |            |
     |               | Setup monitoring        |            |            |
     |               |---------------------------------------------------->|
     |               |            |            |            |  configured|
     |               |<----------------------------------------------------|
     |               |            |            |            |            |
     | Deployed!     |            |            |            |            |
     |<--------------|            |            |            |            |
```

---

## Appendix A: Cross-Cutting Concerns

### A.1 Context Loading Strategy Per Phase

Each agent loads context in three tiers to optimize token usage:

| Stage | Phase | L0 (Always Loaded) | L1 (On-Demand) | L2 (Deep Retrieval) |
|-------|-------|-------------------|-----------------|---------------------|
| S0 | Initialization | Project meta, user input | GitHub config | Repository templates |
| S1 | Brainstorming | Project meta, user input | Similar past projects | Domain knowledge base |
| S2 | Research | Requirements + tech constraints | Brainstorming output | Web search results |
| S3 | Architecture & Design | Research + requirements summary | Full research detail | Reference architectures, design system examples |
| S4 | Planning & Configuration | Architecture + research summary | Full architecture, API spec | Template registry, similar plans |
| S5 | Implementation | Task assignment, file spec | Architecture, design tokens, related code | Full codebase search |
| S6 | Quality Assurance | File under review | Architecture doc, style guide | Security rule database |
| S7 | Testing | Code under test | API spec, test patterns | Coverage data |
| S8 | Debug & Stabilization | Error + stack trace | Failing test, source file | Related code, similar fixes |
| S9 | Documentation & Knowledge | Project summary | All phase outputs | Code comments, README patterns |
| S10 | Deployment & Delivery | Tech stack, architecture | Build config, CI/CD templates | Cloud provider docs |

### A.2 Observability and Monitoring

```
 Metrics exported per agent per phase:

 +----------------------------+------------------+
 | Metric                     | Type             |
 +----------------------------+------------------+
 | agent.task.duration_ms     | histogram        |
 | agent.task.tokens_used     | counter          |
 | agent.task.cost_usd        | counter          |
 | agent.task.success_rate    | gauge            |
 | agent.task.retries         | counter          |
 | agent.context.load_time_ms | histogram        |
 | pipeline.phase.duration_ms | histogram        |
 | pipeline.total_duration_ms | gauge            |
 | pipeline.gates.approved    | counter          |
 | pipeline.gates.rejected    | counter          |
 | llm.request.latency_ms    | histogram        |
 | llm.request.errors        | counter          |
 | llm.provider.availability | gauge            |
 | llm.cost.total_usd        | counter          |
 | git.merge.conflicts       | counter          |
 | git.commits.total         | counter          |
 | test.pass_rate             | gauge            |
 | test.coverage_pct          | gauge            |
 | deploy.duration_ms         | histogram        |
 | deploy.health_check_status | gauge            |
 +----------------------------+------------------+
```

---

## Appendix B: Complete Pipeline Timing Estimate

```
 Stage  Phase                       Estimated Time    Parallelism     Agents Active
 ---------------------------------------------------------------------------------
 S0.  Initialization              0-1 min           Sequential      2 (Orch + GitHub)
 S1.  Brainstorming               2-5 min           Sequential      1 (Brainstorm)
 S2.  Research                    3-5 min           Internal //     1 (Researcher)
 S3.  Architecture & Design       3-5 min           Fan-out //      4 (Arch+Design+DB+API)
 S4.  Planning & Configuration    2-5 min           Sequential      3 (Plan+TechStack+Template)
 S5.  Implementation              5-15 min          Full //         6 (FE+BE+MW+Mobile+Infra+Integ)
      - Merge                     1-2 min           Sequential      1 (Git Manager)
 S6.  Quality Assurance           2-3 min           Full //         5 (CR+Sec+A11y+i18n+Perf)
 S7.  Testing                     3-5 min           Internal //     3 (Test+Perf+A11y)
 S8.  Debug & Stabilization       2-10 min          Sequential      2 (Debug+Test)
 S9.  Documentation & Knowledge   2-3 min           Internal //     4 (DocWriter+Skill+Hook+Tool)
 S10. Deployment & Delivery       3-5 min           Sequential      4 (DevOps+Infra+GitHub+PM)
 ---------------------------------------------------------------------------------
 TOTAL (simple app)               ~28-64 min
 TOTAL (target)                   <30 min for simple apps

 Pipeline Acceleration Opportunities:
 - Template selection reduces Implementation by ~30%
 - Cached research results reduce Research by ~50%
 - Parallel architecture phase saves ~40% vs sequential
 - Pre-warmed agent pools reduce startup overhead
```

---

## Appendix C: Agent Registry

Complete list of all agents in the CodeBot system with their roles and capabilities.

| # | Agent | Role | Primary Stage | Primary Phase | LLM Tier |
|---|-------|------|---------------|---------------|----------|
| 1 | Orchestrator | Master coordinator, task decomposition, agent assignment | S0-S10 | All | Sonnet |
| 2 | Brainstorming Agent | Ideation, alternative exploration, requirement refinement | S1 | Brainstorming | Opus |
| 3 | Researcher | Technology research, reference implementation discovery | S2 | Research | Gemini Pro |
| 4 | Architect | System architecture, C4 model, data flow | S3 | Architecture & Design | Opus |
| 5 | Designer | UI/UX design, component hierarchy, design systems | S3 | Architecture & Design | Sonnet |
| 6 | Database Agent | Schema design, optimization, migrations, seeding | S3 | Architecture & Design | Sonnet |
| 7 | API Gateway Agent | API design, gateway config, rate limiting | S3 | Architecture & Design | Sonnet |
| 8 | Planner | Project planning, task scheduling, dependency graphs | S4 | Planning & Configuration | Sonnet |
| 9 | TechStack Builder | Technology selection, compatibility validation | S4 | Planning & Configuration | Sonnet |
| 10 | Template Agent | Template selection, scaffolding, boilerplate | S4 | Planning & Configuration | Haiku |
| 11 | Frontend Developer | UI implementation, client-side logic | S5 | Implementation | Sonnet |
| 12 | Backend Developer | API implementation, business logic, data access | S5 | Implementation | Sonnet |
| 13 | Middleware Developer | Integration layer, message queues, caching, auth | S5 | Implementation | Sonnet |
| 14 | Mobile Developer | iOS/Android/React Native/Flutter development | S5 | Implementation | Sonnet |
| 15 | Infrastructure Engineer | IaC, Docker, CI/CD, deployment configs | S5 + S10 | Implementation + Deployment | Sonnet |
| 16 | Integrations Agent | Third-party service integrations | S5 | Implementation | Sonnet |
| 17 | Code Reviewer | Code quality, style, best practices, arch conformance | S6 | Quality Assurance | Opus |
| 18 | Security Auditor | SAST, DAST, secret scanning, vulnerability assessment | S6 | Quality Assurance | Opus |
| 19 | Accessibility Agent | WCAG compliance, accessibility testing | S6 + S7 | Quality Assurance + Testing | Sonnet |
| 20 | i18n/L10n Agent | Internationalization and localization | S6 | Quality Assurance | Haiku |
| 21 | Performance Agent | Profiling, optimization, benchmarking | S6 + S7 | Quality Assurance + Testing | Sonnet |
| 22 | Tester | Test generation, execution, coverage analysis | S7 | Testing | Sonnet |
| 23 | Debugger | Root cause analysis, fix generation, regression testing | S8 | Debug & Stabilization | Opus |
| 24 | Documentation Writer | API docs, README, ADRs, deployment guides | S9 | Documentation & Knowledge | Gemini Pro |
| 25 | Skill Creator | Creates reusable skills/capabilities for other agents | S9 | Documentation & Knowledge | Opus |
| 26 | Hooks Creator | Creates lifecycle hooks (pre/post build, deploy, test) | S9 | Documentation & Knowledge | Sonnet |
| 27 | Tools Creator | Creates custom tools and integrations | S9 | Documentation & Knowledge | Sonnet |
| 28 | DevOps Agent | CI/CD pipelines, monitoring, logging, alerting | S10 | Deployment & Delivery | Sonnet |
| 29 | GitHub Agent | Repository management, PRs, Issues, Actions, releases | S0 + S10 | Initialization + Deployment & Delivery | Haiku |
| 30 | Project Manager | Project progress tracking, status reports, timeline management, blocker identification, notifications | S0-S10 | Cross-cutting (All) | Sonnet |

---

*This document is a living specification. It will be updated as the CodeBot platform evolves through development milestones M1-M8 as defined in the PRD.*
