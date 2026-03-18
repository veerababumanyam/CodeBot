# CodeBot Agent Workflows

**Version:** 2.1
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
   - 3.2 [Planning Phase](#32-planning-phase)
   - 3.3 [Research Phase](#33-research-phase)
   - 3.4 [Architecture & Design Phase](#34-architecture--design-phase)
   - 3.5 [Tech Stack & Template Selection Phase](#35-tech-stack--template-selection-phase)
   - 3.6 [Implementation Phase](#36-implementation-phase)
   - 3.7 [Review Phase](#37-review-phase)
   - 3.8 [Testing Phase](#38-testing-phase)
   - 3.9 [Debug & Fix Loop](#39-debug--fix-loop)
   - 3.10 [Deployment Phase](#310-deployment-phase)
   - 3.11 [Delivery Phase](#311-delivery-phase)
   - 3.12 [Failure Mode Analysis per Phase](#312-failure-mode-analysis-per-phase)
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
  User Input ---------> |  [Brainstorm] --> [Plan]  |
                        |       |             |     |
                        |       v             v     |
                        |  [Research] --> [Architect]|
                        |       |        /    |     |
                        |       v       v     v     |
                        |  [TechStack] [Design] [DB]|
                        |       |        |      |   |
                        |       v        v      v   |
                        |      [Template Selection] |
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
                        |  Review Sec  A11y Perf    |
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
                        |      [Deploy] [Debug]--+  |
                        |         |         |    |  |
                        |         v         +----+  |
                        |     [Deliver]             |
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
| G1 | Brainstorming -> Planning | Approval | User confirms refined requirements |
| G2 | Planning -> Research | Automatic | Plan passes structural validation |
| G3 | Research -> Architecture | Automatic | Research report completeness check |
| G4 | Architecture -> Design | Approval | User approves system architecture |
| G5 | Design -> Tech Stack | Approval | User approves UI/UX direction |
| G6 | Tech Stack -> Implementation | Approval | User confirms tech stack selections |
| G7 | Implementation -> Review | Automatic | All agents complete, code compiles |
| G8 | Review -> Testing | Automatic | No critical/blocker findings |
| G9 | Testing -> Debug/Fix | Automatic | Test results collected |
| G10 | Debug/Fix -> Deployment | Automatic | All tests pass, coverage met |
| G11 | Deployment -> Delivery | Automatic | Deployment health checks pass |

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

| Phase | Strategy | Parallelism Details |
|-------|----------|-------------------|
| Brainstorming | Sequential | Single agent, interactive with user |
| Planning | Sequential | Orchestrator + Planner pipeline |
| Research | Internal parallel | Multiple research queries run concurrently |
| Architecture & Design | Fan-out / Fan-in | Architect, Designer, DB Agent, API Gateway work in parallel |
| Tech Stack & Template | Sequential | Requires user approval at each step |
| Implementation | **Full parallel** | FE, BE, MW, Mobile, Infra in isolated git worktrees |
| Review | **Full parallel** | Code Reviewer, Security Auditor, A11y, Perf run simultaneously |
| Testing | Internal parallel | Unit, integration, E2E suites run concurrently |
| Debug & Fix | Sequential per issue | Issues fixed one at a time to avoid conflicts |
| Deployment | Sequential | Pipeline stages must execute in order |
| Delivery | Internal parallel | Multiple doc types generated concurrently |

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

| Intervention Point | Trigger | Required? | Timeout Action | Mode Override |
|--------------------|---------|-----------|----------------|---------------|
| Requirements Refinement | Brainstorming complete | Configurable (default: yes) | Auto-accept after 15 min | autopilot: skip |
| Plan Approval | Plan phase complete | Configurable (default: yes) | Auto-approve after 30 min | autopilot: skip |
| Architecture Approval | Architecture phase complete | Configurable (default: yes) | Auto-approve after 30 min | autopilot: skip |
| Design Approval | Design phase complete | Configurable (default: no) | Auto-approve after 30 min | always skippable |
| Tech Stack Approval | Tech stack selected | Configurable (default: yes) | Auto-approve after 30 min | autopilot: skip |
| Requirement Clarification | Ambiguous requirements detected | Always | Skip ambiguous items, document assumptions | N/A |
| Debug Escalation | 3 failed fix iterations | Always | Pause pipeline, alert user | N/A |
| Security Exception | Critical vulnerability found | Always | Block delivery until resolved | N/A |
| Deployment Approval | Pre-production deploy | Configurable (default: yes) | Auto-approve after 30 min | autopilot: skip |
| Code Review Override | Major architectural issue flagged | Optional | Auto-accept suggestions | N/A |

### 1.5 Checkpoint and Resume Mechanism

Every phase transition creates a checkpoint. If the pipeline crashes, it can resume from the last
successful checkpoint without repeating completed work.

```
 CHECKPOINT ARCHITECTURE:

 .codebot/
   checkpoints/
     +--- session_<uuid>/
     |      +--- manifest.json              (session metadata, current phase)
     |      +--- phase_01_brainstorming.json (refined requirements)
     |      +--- phase_02_planning.json      (plan + task graph)
     |      +--- phase_03_research.json      (research report)
     |      +--- phase_04_architecture.json  (arch docs + schemas)
     |      +--- phase_05_design.json        (design spec + wireframes)
     |      +--- phase_06_techstack.json     (tech stack + template selections)
     |      +--- phase_07_implementation/    (per-agent snapshots)
     |      |       +--- frontend.json
     |      |       +--- backend.json
     |      |       +--- middleware.json
     |      |       +--- mobile.json
     |      |       +--- infrastructure.json
     |      +--- phase_08_review.json        (review + security reports)
     |      +--- phase_09_testing.json       (test results + coverage)
     |      +--- phase_10_debug_fix.json     (fix history + iterations)
     |      +--- phase_11_deployment.json    (deploy config + status)
     |      +--- phase_12_delivery.json      (build + handoff report)
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
 User Input --> Brainstorming --> Planning --> Research --> Architecture -->
 Design --> Tech Stack Selection --> Template Selection --> Implementation -->
 Review --> Testing --> Debug/Fix --> Deployment --> Delivery
```

### 2.2 Complete Sequence Diagram

```
 User              Orchestrator       Pipeline Phases              Git/Storage
  |                      |                     |                          |
  |  Submit idea/PRD     |                     |                          |
  |--------------------->|                     |                          |
  |                      |  Init project repo  |                          |
  |                      |----------------------------------------------->|
  |                      |                     |                     repo created
  |                      |                     |                          |
  |                      |  PHASE 1: BRAINSTORMING                        |
  |                      |-------------------->|                          |
  |  Interactive Q&A     |                     |                          |
  |<-------------------->|                     |                          |
  |                      |  Requirements refined                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |  [GATE] Confirm      |                     |                          |
  |  requirements?       |                     |                          |
  |<---------------------|                     |                          |
  |  Confirmed           |                     |                          |
  |--------------------->|                     |                          |
  |                      |                     |                          |
  |                      |  PHASE 2: PLANNING  |                          |
  |                      |-------------------->|                          |
  |  Clarification Q?    |                     |                          |
  |<---------------------|                     |                          |
  |  Answers             |                     |                          |
  |--------------------->|                     |                          |
  |                      |  Plan complete      |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |  [GATE] Approve plan?|                     |                          |
  |<---------------------|                     |                          |
  |  Approved            |                     |                          |
  |--------------------->|                     |                          |
  |                      |                     |                          |
  |                      |  PHASE 3: RESEARCH  |                          |
  |                      |-------------------->|                          |
  |                      |  Research complete  |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |                      |  PHASE 4: ARCHITECTURE & DESIGN (parallel)     |
  |                      |-------------------->| Architect --|            |
  |                      |-------------------->| Designer  --|            |
  |                      |-------------------->| DB Agent  --|            |
  |                      |-------------------->| API GW    --|            |
  |                      |  All outputs ready  |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |  [GATE] Approve arch?|                     |                          |
  |<---------------------|                     |                          |
  |  Approved            |                     |                          |
  |--------------------->|                     |                          |
  |                      |                     |                          |
  |                      |  PHASE 5: TECH STACK & TEMPLATE                |
  |                      |-------------------->|                          |
  |  Select tech stack   |                     |                          |
  |<-------------------->|                     |                          |
  |  Select templates    |                     |                          |
  |<-------------------->|                     |                          |
  |                      |  Scaffold generated |                          |
  |                      |<--------------------|                          |
  |                      |  Commit scaffold    |                          |
  |                      |----------------------------------------------->|
  |                      |                     |                          |
  |                      |  PHASE 6: IMPLEMENTATION (PARALLEL)            |
  |                      |-------------------->| Frontend --|             |
  |                      |-------------------->| Backend  --|-- worktrees |
  |                      |-------------------->| Middleware--|             |
  |                      |-------------------->| Mobile   --|             |
  |                      |-------------------->| Infra    --|             |
  |                      |  All agents done    |                          |
  |                      |<--------------------|                          |
  |                      |  Merge worktrees    |                          |
  |                      |----------------------------------------------->|
  |                      |                     |                     merged
  |                      |                     |                          |
  |                      |  PHASE 7: REVIEW (PARALLEL)                    |
  |                      |-------------------->| Code Review --|          |
  |                      |-------------------->| Security Audit|          |
  |                      |-------------------->| A11y Check ---|          |
  |                      |-------------------->| Perf Check ---|          |
  |                      |  Reviews complete   |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |                      |  PHASE 8: TESTING   |                          |
  |                      |-------------------->|                          |
  |                      |  Tests complete     |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |                      |  PHASE 9: DEBUG & FIX LOOP                     |
  |                      |-------------------->|                          |
  |                      |  (iterates until    |                          |
  |                      |   all pass or       |                          |
  |                      |   escalate)         |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |  [GATE] Human needed?|                     |                          |
  |<------(if stuck)-----|                     |                          |
  |                      |                     |                          |
  |                      |  PHASE 10: DEPLOYMENT                          |
  |                      |-------------------->|                          |
  |                      |  Deployed           |                          |
  |                      |<--------------------|                          |
  |                      |                     |                          |
  |  [GATE] Approve      |                     |                          |
  |  deployment?         |                     |                          |
  |<---------------------|                     |                          |
  |  Approved            |                     |                          |
  |--------------------->|                     |                          |
  |                      |                     |                          |
  |                      |  PHASE 11: DELIVERY |                          |
  |                      |-------------------->|                          |
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
 |BRAINSTORMING |
 +--------------+
     | refined requirements
     v
 +----------+   GATE G1: Requirements Confirmed
 |GATE_REQS |---[rejected]---> BRAINSTORMING (iterate)
 +----------+
     | confirmed
     v
 +--------+    fail     +----------+
 |PLANNING|------------>|ESCALATION|---> [HUMAN]
 +--------+             +----------+
     | ok
     v
 +---------+   GATE G2: Plan Approval
 |GATE_PLAN|---[rejected]---> PLANNING (revise)
 +---------+
     | approved
     v
 +--------+
 |RESEARCH|
 +--------+
     | ok
     v
 +---------------------+
 |ARCHITECTURE & DESIGN|  (parallel sub-agents)
 +---------------------+
     | ok
     v
 +---------+   GATE G4: Architecture Approval
 |GATE_ARCH|---[rejected]---> ARCHITECTURE (revise)
 +---------+
     | approved
     v
 +-----------+
 |TECH_STACK |
 +-----------+
     | ok
     v
 +----------+   GATE G6: Tech Stack Approval
 |GATE_TECH |---[rejected]---> TECH_STACK (revise)
 +----------+
     | approved
     v
 +--------------+
 |IMPLEMENTATION|  (parallel sub-states: FE, BE, MW, Mobile, Infra)
 +--------------+
     | all merged
     v
 +------+
 |REVIEW|  (parallel sub-states: Code, Security, A11y, Perf)
 +------+
     | ok (no critical/blocker findings)
     v
 +-------+
 |TESTING|
 +-------+
     | results
     v
 +---------+
 |DEBUG_FIX|<-----+
 +---------+      |
     |            |
     |--[pass]--->|--- (loop if regressions)
     |            |
     |--[fail, iteration < 3]---+
     |
     |--[fail, iteration >= 3]---> [HUMAN ESCALATION]
     |
     |--[all pass]
     v
 +----------+
 |DEPLOYMENT|
 +----------+
     | ok
     v
 +----------+   GATE G11: Deployment Approval (optional)
 |GATE_DEPLOY|---[rejected]---> DEPLOYMENT (rollback)
 +----------+
     | approved
     v
 +--------+
 |DELIVERY|
 +--------+
     |
     v
  [END]
```

### 2.4 Phase Transition Details

For each transition, the following data flows between phases:

| From | To | Trigger | Data Flowing | Gate | On Failure |
|------|----|---------|-------------|------|------------|
| User Input | Brainstorming | User submits idea/PRD | Raw requirements, user preferences | None | N/A |
| Brainstorming | Planning | Requirements refined | Refined PRD, risk assessment, tech recs | G1: User confirms | Re-enter brainstorming |
| Planning | Research | Plan approved | Task graph, dependency map, schedule | G2: Plan validation | Revise plan |
| Research | Architecture | Research complete | Research report, dep manifest, patterns | G3: Completeness | Extend research |
| Architecture | Tech Stack | Architecture approved | C4 docs, API specs, schemas, wireframes | G4: User approves | Revise architecture |
| Tech Stack | Implementation | Stack confirmed | Tech config, template code, scaffold | G6: User approves | Revise stack |
| Implementation | Review | All agents complete | Complete codebase, merged branches | G7: Compiles | Fix compilation |
| Review | Testing | No critical findings | Review reports, remediation items | G8: No blockers | Fix blockers |
| Testing | Debug/Fix | Tests collected | Test results, coverage, failures | G9: Auto | N/A |
| Debug/Fix | Deployment | All tests pass | Fixed codebase, regression tests | G10: Coverage met | Continue fixing |
| Deployment | Delivery | Health checks pass | Deployed app, CI/CD config | G11: Optional | Rollback |
| Delivery | End | Package ready | Docs, release, handoff report | None | N/A |

### 2.5 Parallel Execution Opportunities

| Phase | Parallelism | Details |
|-------|-------------|---------|
| Brainstorming | Sequential | Single Brainstorming Agent, interactive with user |
| Planning | Sequential | Single Orchestrator + Planner pipeline |
| Research | Internal parallelism | Multiple research queries can run concurrently |
| Architecture & Design | **Fan-out** | Architect, Designer, DB Agent, API Gateway work in parallel |
| Tech Stack & Template | Sequential | Requires user selection steps |
| Implementation | **Full parallelism** | 5 agents in isolated worktrees (FE, BE, MW, Mobile, Infra) |
| Review | **Full parallelism** | Code Reviewer + Security Auditor + A11y + Perf simultaneously |
| Testing | Internal parallelism | Unit, integration, E2E test suites run concurrently |
| Debug & Fix | Sequential per issue | Issues prioritized and fixed one at a time |
| Deployment | Sequential | Pipeline stages must execute in order |
| Delivery | Internal parallelism | Multiple doc types generated concurrently |

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
 9. Checkpoint saved, transition to Planning
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

### 3.2 Planning Phase

**Description:** The Planner Agent decomposes the refined requirements into a structured execution plan with epics, user stories, and tasks organized in a dependency graph.

**Goals:**
- Break requirements into implementable tasks
- Create dependency graph with topological ordering
- Identify parallel execution opportunities
- Estimate complexity and timeline

**Agent(s) Involved:** Planner, Orchestrator

**Input:**
```json
{
  "refined_requirements": { },
  "risk_assessment": [ ],
  "tech_recommendations": { },
  "project_type": "greenfield | inflight | brownfield"
}
```

**Output:**
```json
{
  "plan": {
    "epics": [
      {
        "id": "E001",
        "name": "User Authentication System",
        "stories": [
          {
            "id": "S001",
            "name": "User Registration",
            "tasks": [
              {
                "id": "T001",
                "name": "Create User model and migration",
                "agent": "database",
                "depends_on": [],
                "estimated_complexity": "low",
                "estimated_tokens": 2000
              },
              {
                "id": "T002",
                "name": "Implement registration API endpoint",
                "agent": "backend",
                "depends_on": ["T001"],
                "estimated_complexity": "medium",
                "estimated_tokens": 5000
              }
            ]
          }
        ]
      }
    ],
    "dependency_graph": {
      "nodes": ["T001", "T002", "T003"],
      "edges": [["T001", "T002"], ["T001", "T003"]]
    },
    "execution_schedule": {
      "wave_1": ["T001", "T004", "T007"],
      "wave_2": ["T002", "T003", "T005"],
      "wave_3": ["T006", "T008"]
    },
    "parallel_groups": [
      {
        "agents": ["frontend", "backend", "infrastructure"],
        "tasks": { "frontend": ["T003"], "backend": ["T002"], "infrastructure": ["T007"] }
      }
    ]
  }
}
```

**Step-by-Step Workflow:**

```
 1. Receive refined requirements from Brainstorming
 2. Orchestrator parses requirements into structured format
 3. Detect ambiguities or gaps
    3a. If gaps found -> request clarification from user
    3b. If clear -> continue
 4. Planner decomposes into epics and stories
 5. Planner creates task-level breakdown
 6. Planner assigns each task to an agent type
 7. Planner builds dependency graph
 8. Planner computes topological ordering
 9. Planner identifies parallel execution waves
 10. Planner estimates complexity per task
 11. Generate execution schedule
 12. Present plan to user for approval
 13. [GATE G2] User approves plan
 14. Checkpoint saved, transition to Research
```

**Sequence Diagram:**

```
 User          Orchestrator       Planner          Context DB        Git
  |                 |                |                  |              |
  | (auto from G1)  |                |                  |              |
  |                 | Parse reqs     |                  |              |
  |                 |---+            |                  |              |
  |                 |<--+            |                  |              |
  |                 |                |                  |              |
  |                 | Detect gaps    |                  |              |
  |                 |---+            |                  |              |
  |                 |<--+            |                  |              |
  |                 |                |                  |              |
  | Clarification?  |                |                  |              |
  |<----------------|                |                  |              |
  | Answers         |                |                  |              |
  |---------------->|                |                  |              |
  |                 |                |                  |              |
  |                 | Decompose      |                  |              |
  |                 |--------------->|                  |              |
  |                 |                | Load similar     |              |
  |                 |                | project plans    |              |
  |                 |                |----------------->|              |
  |                 |                |<-----------------|              |
  |                 |                |                  |              |
  |                 |                | Build task graph |              |
  |                 |                |---+              |              |
  |                 |                |<--+              |              |
  |                 |                |                  |              |
  |                 |                | Compute schedule |              |
  |                 |                |---+              |              |
  |                 |                |<--+              |              |
  |                 |                |                  |              |
  |                 | Plan ready     |                  |              |
  |                 |<---------------|                  |              |
  |                 |                |                  |              |
  | Review plan     |                |                  |              |
  |<----------------|                |                  |              |
  |                 |                |                  |              |
  | Approve/Reject  |                |                  |              |
  |---------------->|                |                  |              |
  |                 | [GATE G2]      |                  |              |
  |                 | Save checkpoint|                  |              |
  |                 |---+            |                  |              |
  |                 |<--+            |                  |              |
  |                 | Store plan     |                  |              |
  |                 |------------------------------------+------------>|
```

**Decision Points:**
- If requirements map to a known template: suggest template-based acceleration
- If complexity exceeds estimated budget: present trade-off options to user
- If circular dependencies detected: resolve and notify

**Error Handling:**
- Planner produces invalid graph: retry with explicit constraints
- Task count exceeds agent capacity: break into sub-projects
- User rejects plan 3 times: escalate to human architect consultation

**Quality Gate G2: Plan Approval**
- All requirements mapped to at least one task
- Dependency graph is a valid DAG (no cycles)
- Every task has an assigned agent type
- Complexity estimates are within budget tolerance
- User has approved the plan

---

### 3.3 Research Phase

**Description:** The Researcher Agent investigates technologies, patterns, libraries, and reference implementations relevant to the project. It evaluates dependencies for security, licensing, and maintenance health.

**Goals:**
- Evaluate technology choices for the project
- Find reference implementations and best practices
- Assess dependency health (security, licensing, maintenance)
- Recommend architectural patterns

**Agent(s) Involved:** Researcher

**Input:**
```json
{
  "plan": { },
  "tech_recommendations": { },
  "refined_requirements": { },
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
 1. Receive plan and tech recommendations from Planning
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
 9. [GATE G3] Report completeness validation
 10. Checkpoint saved, transition to Architecture
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
     | [GATE G3]       |                  |               |              |
```

**Error Handling:**
- Web search fails: use cached/local knowledge base
- Vulnerability database unavailable: flag as "unverified" and continue
- No viable option for a technology category: escalate to user with alternatives

**Quality Gate G3: Research Completeness**
- All technology categories have at least one evaluated option
- No unresolved licensing conflicts
- No critical unpatched vulnerabilities in recommended dependencies
- Reference implementations found for key architectural patterns

---

### 3.4 Architecture & Design Phase

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
 9. [GATE G4] User approves architecture
 10. Checkpoint saved, transition to Tech Stack Selection
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
              [GATE G4: User Approval]
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

**Quality Gate G4: Architecture Approval**
- C4 context and container diagrams complete
- All API endpoints documented with request/response schemas
- Database schema supports all CRUD operations implied by features
- Design system has at minimum: colors, typography, spacing, core components
- No unresolved cross-agent inconsistencies
- User has approved the architecture direction

---

### 3.5 Tech Stack & Template Selection Phase

**Description:** Based on the architecture and research outputs, the TechStack Builder recommends specific technologies and the Template Agent presents scaffolding options. The user makes final selections, and the scaffold is generated.

**Goals:**
- Finalize technology selections for every layer
- Validate compatibility across all selections
- Select UI/UX templates and design kits
- Generate project scaffold with all boilerplate

**Agent(s) Involved:** TechStack Builder, Template Agent, Orchestrator

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
 5. [GATE G5] User confirms tech stack
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
 11. [GATE G6] Scaffold validation (compiles, lints pass)
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
  |                 | [GATE G5]    |               |             |
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
  |                 | [GATE G6]    |               |             |
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

**Quality Gate G6: Scaffold Validation**
- Project compiles/builds successfully
- Linting passes with zero errors
- All configuration files are valid
- Directory structure matches architecture specifications
- Development server starts without errors

---

### 3.6 Implementation Phase

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
 11. Resolve any merge conflicts (see 3.6.2)
 12. Run compilation check on merged code
 13. [GATE G7] Code compiles successfully
 14. Checkpoint saved, transition to Review
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

### 3.7 Review Phase

**Description:** Multiple review agents run in parallel to assess code quality, security, accessibility, and performance. Each produces a findings report that feeds into the testing and debug phases.

**Goals:**
- Verify code quality and adherence to best practices
- Identify security vulnerabilities (SAST, DAST, SCA)
- Check accessibility compliance (WCAG 2.1 AA)
- Profile initial performance characteristics
- Verify architecture conformance

**Agent(s) Involved:** Code Reviewer, Security Auditor, Accessibility Agent, Performance Agent

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
 1. Orchestrator fans out to 4 review agents in parallel:
    a. Code Reviewer: style, patterns, architecture conformance
    b. Security Auditor: SAST, SCA, secret scanning
    c. Accessibility Agent: WCAG compliance check
    d. Performance Agent: bundle analysis, profiling
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
 8. [GATE G8] No critical/blocker findings remain
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
     | [GATE G8]     |              |              |              |
```

**Error Handling:**
- Review agent crashes: restart and re-scan
- False positive detected: mark as suppressed, add to exclusion list
- SAST tool unavailable: log warning, proceed with available tools
- Performance profiling fails: skip, flag for manual review

**Quality Gate G8: Review Clearance**
- Zero critical or blocker severity findings
- Security audit shows no critical vulnerabilities
- No hardcoded secrets detected
- Accessibility compliance score >= 0.85

---

### 3.8 Testing Phase

**Description:** The Tester Agent generates and executes comprehensive test suites covering unit, integration, and end-to-end tests. The Performance Agent runs load tests and the Accessibility Agent runs automated a11y tests.

**Goals:**
- Generate unit tests for all business logic
- Generate integration tests for API endpoints
- Generate E2E tests for critical user flows
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
 3. Set up test infrastructure:
    a. Test database with seed data
    b. Mock external services
    c. Test environment variables
 4. Execute test suites (parallel where possible):
    a. Unit tests (fastest, run first)
    b. Integration tests (medium speed)
    c. E2E tests (slowest, run last)
 5. Performance Agent runs load tests:
    a. Ramp-up test (gradual traffic increase)
    b. Stress test (peak load simulation)
    c. Endurance test (sustained load)
 6. Accessibility Agent runs automated tests:
    a. axe-core scan on all pages
    b. Keyboard navigation check
    c. Screen reader compatibility check
 7. Collect all results and compute coverage
 8. Classify failures by severity and root cause
 9. [GATE G9] Test results collected (auto-pass to Debug phase)
 10. Checkpoint saved, transition to Debug & Fix
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
 [RUN_INTEGRATION_TESTS]     (can run in parallel with unit tests)
      |
      v
 [RUN_E2E_TESTS]
      |
      v
 [RUN_PERF_TESTS]            (parallel with E2E)
      |
      v
 [RUN_A11Y_TESTS]            (parallel with E2E)
      |
      v
 [COLLECT_RESULTS]
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
 [GATE G9: AUTO]
```

**Error Handling:**
- Test infrastructure fails to start: retry setup, fall back to in-memory DB
- Test generation produces invalid tests: re-generate with error context
- E2E browser launch fails: retry with headless mode
- Performance test causes OOM: reduce load parameters, retry
- Flaky test detected (passes on retry): mark as flaky, exclude from failure count

---

### 3.9 Debug & Fix Loop

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
 4. If all tests pass: proceed to Deployment
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

### 3.10 Deployment Phase

**Description:** The DevOps Agent and Infrastructure Engineer collaborate to create CI/CD pipelines, generate Infrastructure-as-Code, and deploy the application to the selected cloud provider or self-hosted environment.

**Goals:**
- Create CI/CD pipeline (GitHub Actions by default)
- Generate Infrastructure-as-Code (Terraform/Pulumi/Docker)
- Configure deployment environments (staging, production)
- Deploy application with health checks
- Set up monitoring and alerting

**Agent(s) Involved:** DevOps Agent, Infrastructure Engineer, GitHub Agent

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
    a. [GATE G11] Optional: user approval for production
    b. Deploy to production
    c. Run production health checks
    d. Configure monitoring and alerting
 7. Checkpoint saved, transition to Delivery
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
     | [GATE G11]    |            |              |              |
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

**Quality Gate G10/G11: Deployment Validation**
- Application responds to health check endpoint
- All smoke tests pass against staging
- No error spikes in monitoring
- SSL certificate valid
- DNS resolves correctly

---

### 3.11 Delivery Phase

**Description:** The Documentation Writer generates all project documentation, the GitHub Agent creates a release with artifacts, and a comprehensive handoff report is generated for the user.

**Goals:**
- Generate complete project documentation
- Create GitHub release with all artifacts
- Produce handoff report for the user
- Archive project state for future reference

**Agent(s) Involved:** Documentation Writer, GitHub Agent, Orchestrator

**Input:**
```json
{
  "codebase": { },
  "architecture": { },
  "api_spec": { },
  "test_results": { },
  "deployment": { },
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
  "release": {
    "version": "1.0.0",
    "tag": "v1.0.0",
    "github_release_url": "https://github.com/...",
    "artifacts": [
      "source-code.tar.gz",
      "docker-image:latest",
      "api-docs.zip"
    ]
  },
  "handoff_report": {
    "project_summary": "...",
    "features_implemented": [ ],
    "known_limitations": [ ],
    "recommended_next_steps": [ ],
    "cost_summary": {
      "total_tokens_used": 2450000,
      "total_cost_usd": 45.67,
      "cost_by_phase": { }
    },
    "timeline_summary": {
      "total_duration_minutes": 32,
      "duration_by_phase": { }
    }
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
 3. GitHub Agent creates release:
    a. Create git tag (v1.0.0)
    b. Build release artifacts
    c. Create GitHub Release with changelog
    d. Attach artifacts to release
 4. Orchestrator generates handoff report:
    a. Project summary and feature list
    b. Known limitations and technical debt
    c. Recommended next steps
    d. Cost and timeline summary
    e. All agent execution logs
 5. Deliver to user:
    a. Repository URL with all code
    b. Deployment URL (staging + production)
    c. Documentation URL
    d. Handoff report
 6. Final checkpoint saved
 7. Session archived
```

**Sequence Diagram:**

```
 Orchestrator      Doc Writer       GitHub Agent      Git           User
     |                 |                 |              |              |
     | Generate docs   |                 |              |              |
     |---------------->|                 |              |              |
     |                 | README          |              |              |
     |                 |---+             |              |              |
     |                 |<--+             |              |              |
     |                 | API docs        |              |              |
     |                 |---+             |              |              |
     |                 |<--+             |              |              |
     |                 | ADRs            |              |              |
     |                 |---+             |              |              |
     |                 |<--+             |              |              |
     |                 | Deploy guide    |              |              |
     |                 |---+             |              |              |
     |                 |<--+             |              |              |
     |                 |                 |              |              |
     |                 | Commit docs     |              |              |
     |                 |------------------------------------>|         |
     |                 |                 |              |              |
     | Docs ready      |                 |              |              |
     |<----------------|                 |              |              |
     |                 |                 |              |              |
     | Create release  |                 |              |              |
     |---------------------------------->|              |              |
     |                 |                 | Tag + release|              |
     |                 |                 |------------->|              |
     |                 |                 |              |              |
     | Release URL     |                 |              |              |
     |<----------------------------------|              |              |
     |                 |                 |              |              |
     | Generate handoff|                 |              |              |
     |---+             |                 |              |              |
     |<--+             |                 |              |              |
     |                 |                 |              |              |
     | Deliver to user |                 |              |              |
     |---------------------------------------------------------------->|
     |                 |                 |              |              |
     | Archive session |                 |              |              |
     |---+             |                 |              |              |
     |<--+             |                 |              |              |
```

**Error Handling:**
- Documentation generation fails: produce minimal docs, flag incomplete sections
- GitHub release creation fails: retry, fall back to manual instructions
- Artifact build fails: deliver source code without pre-built artifacts
- User unreachable for handoff: email notification with all links and report

---

### 3.12 Failure Mode Analysis per Phase

Each pipeline phase has characteristic failure modes. The following table documents common failures, how they are detected, and the recovery strategy applied.

| Phase | Common Failures | Detection | Recovery |
|---|---|---|---|
| Brainstorming | User abandonment, infinite loop | Session timeout (60min), repetition detection | Auto-finalize with current state |
| Planning | Over-decomposition, missing dependencies | Task count threshold, dependency cycle detection | Simplify plan, merge tasks |
| Research | Outdated info, hallucinated references | Source verification, cross-reference check | Flag unverified, fallback to cached knowledge |
| Architecture | Over-engineering, inconsistent design | Complexity metrics, schema validation | Simplify, apply reference architecture |
| Implementation | Compilation errors, type mismatches | Build verification after each agent | Route to Debugger, retry with context |
| Review | False positives, scanner crashes | Result validation, scanner health check | Re-run with different config, manual review flag |
| Testing | Flaky tests, environment issues | Test stability tracking, retry detection | Quarantine flaky tests, environment reset |
| Debug/Fix | Infinite fix loop, regression introduction | Iteration counter (max 5), regression detection | Escalate to human after 3 iterations |
| Deployment | Health check failure, resource exhaustion | Health endpoint monitoring, resource metrics | Auto-rollback, scale resources |
| Delivery | Missing artifacts, incomplete docs | Completeness checklist validation | Re-generate missing items |

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
| Planner | requirements | plan |
| Researcher | plan, requirements | research |
| Architect | plan, research, requirements | architecture |
| Designer | architecture, requirements | design |
| Database Agent | architecture, plan | architecture.database |
| API Gateway Agent | architecture, plan | architecture.api |
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
   v001/ <- Brainstorming output
   v002/ <- Planning output
   v003/ <- Research output
   ...
   latest -> v012/
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
 [Brainstorming]     <-- Full idea exploration
      |
      v
 [Planning]           <-- Complete task decomposition
      |
      v
 [Research]           <-- Full technology evaluation
      |
      v
 [Architecture]       <-- Design from scratch
      |
      v
 [Tech Stack]         <-- Select all technologies
      |
      v
 [Template]           <-- Generate full scaffold
      |
      v
 [Implementation]     <-- Build everything
      |
      v
 [Review]             <-- Full review suite
      |
      v
 [Testing]            <-- Comprehensive test generation
      |
      v
 [Debug/Fix]          <-- Fix all issues
      |
      v
 [Deployment]         <-- Full deployment setup
      |
      v
 [Delivery]           <-- Complete documentation
```

**Key Characteristics:**
- All phases are active
- All agent types may be spawned
- Template selection is important for productivity
- Full documentation generated from scratch
- CI/CD pipeline created from scratch
- Estimated timeline: 25-60 minutes (depending on complexity)

**Agent Activation Matrix for Greenfield:**

| Agent | Active | Phase |
|-------|--------|-------|
| Orchestrator | Always | All |
| Brainstorming Agent | Yes | Brainstorming |
| Planner | Yes | Planning |
| Researcher | Yes | Research |
| Architect | Yes | Architecture |
| Designer | Yes | Architecture |
| Database Agent | Yes | Architecture |
| API Gateway Agent | Yes | Architecture |
| TechStack Builder | Yes | Tech Stack |
| Template Agent | Yes | Tech Stack |
| Frontend Developer | Yes | Implementation |
| Backend Developer | Yes | Implementation |
| Middleware Developer | Conditional | Implementation |
| Mobile Developer | Conditional | Implementation |
| Infrastructure Engineer | Yes | Implementation |
| Code Reviewer | Yes | Review |
| Security Auditor | Yes | Review |
| Accessibility Agent | Yes | Review |
| Performance Agent | Yes | Review + Testing |
| Tester | Yes | Testing |
| Debugger | Conditional | Debug/Fix |
| DevOps Agent | Yes | Deployment |
| GitHub Agent | Yes | Deployment + Delivery |
| Documentation Writer | Yes | Delivery |
| Project Manager | Yes | Cross-cutting (All) |

---

### 5.2 Inflight Workflow

**Description:** Flow for joining an existing project mid-development. CodeBot analyzes the existing codebase, reverse-engineers the architecture, identifies gaps, and continues development.

```
 INFLIGHT PIPELINE:

 [User Input + Existing Repo URL]
      |
      v
 [Codebase Analysis]       <-- NEW: Analyze existing code
      |
      +-- Clone repository
      +-- Detect tech stack
      +-- Map file structure
      +-- Identify patterns
      +-- Detect test coverage
      |
      v
 [Architecture Recovery]    <-- NEW: Reverse-engineer architecture
      |
      +-- Infer C4 model from code
      +-- Extract API contracts from routes
      +-- Reverse-engineer DB schema from models/migrations
      +-- Map component hierarchy
      |
      v
 [Gap Analysis]             <-- NEW: What's missing?
      |
      +-- Compare requirements vs implemented features
      +-- Identify missing tests
      +-- Find incomplete features
      +-- Detect technical debt
      |
      v
 [Brainstorming]            <-- Scoped to remaining work
      |
      v
 [Planning]                 <-- Plan only remaining tasks
      |
      v
 [Research]                 <-- SKIP if tech stack is fixed
      |
      v
 [Implementation]           <-- Build only missing pieces
      |                          (no scaffold, work on existing code)
      v
 [Review]                   <-- Review new + changed code only
      |
      v
 [Testing]                  <-- Generate tests for new code + increase coverage
      |
      v
 [Debug/Fix]
      |
      v
 [Deployment]               <-- SKIP if CI/CD already exists, else enhance
      |
      v
 [Delivery]                 <-- Update existing docs, don't overwrite
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
 [Legacy Assessment]        <-- NEW: Deep legacy analysis
      |
      +-- Identify deprecated dependencies
      +-- Detect anti-patterns
      +-- Map coupling and cohesion
      +-- Assess test coverage (usually very low)
      +-- Identify security vulnerabilities
      +-- Estimate modernization effort
      |
      v
 [Modernization Strategy]   <-- NEW: Plan the transformation
      |
      +-- Strangler Fig pattern vs Big Bang
      +-- Identify modules to modernize first
      +-- Define target architecture
      +-- Create migration path
      +-- Risk assessment
      |
      v
 [Safety Net Creation]      <-- NEW: Tests before changes
      |
      +-- Generate characterization tests (capture current behavior)
      +-- Generate integration tests for critical paths
      +-- Set up regression detection
      +-- Establish baseline metrics
      |
      v
 [Incremental Modernization] <-- Iterative refactoring
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
 [Review]
      |
      v
 [Testing]                   <-- Full regression suite
      |
      v
 [Debug/Fix]
      |
      v
 [Deployment]
      |
      v
 [Delivery]
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

 [Checkpoint: phase_06_techstack.json]  <-- Last successful phase
      |
      v
 [Skip: Brainstorming]     already completed
 [Skip: Planning]          already completed
 [Skip: Research]          already completed
 [Skip: Architecture]      already completed
 [Skip: Tech Stack]        already completed
      |
      v
 [Resume: Implementation]  <-- Re-execute from here
      |
      v
 [Continue: Review, Testing, etc.]
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
    "G4_architecture": {
      "type": "approval",
      "mandatory": true,
      "timeout_minutes": 30,
      "timeout_action": "auto_approve",
      "notify_channels": ["dashboard", "email"],
      "auto_skip_in_mode": "autopilot"
    },
    "G11_deployment": {
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

 +------------------+-------------+
 | Phase            | Budget %    |
 +------------------+-------------+
 | Brainstorming    | 3%          |
 | Planning         | 5%          |
 | Research         | 5%          |
 | Architecture     | 10%         |
 | Design           | 5%          |
 | Tech Stack       | 2%          |
 | Implementation   | 35%         |
 | Review           | 5%          |
 | Testing          | 10%         |
 | Debug & Fix      | 10%         |
 | Deployment       | 3%          |
 | Documentation    | 4%          |
 | Delivery         | 3%          |
 +------------------+-------------+
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
 User        Orch       Brain    Plan    Research   Arch     Design    DB      API GW
  |            |           |       |        |         |        |        |        |
  | Idea       |           |       |        |         |        |        |        |
  |----------->|           |       |        |         |        |        |        |
  |            | Start     |       |        |         |        |        |        |
  |            |---------->|       |        |         |        |        |        |
  |            |           |       |        |         |        |        |        |
  | Q&A loop   |           |       |        |         |        |        |        |
  |<---------->|<--------->|       |        |         |        |        |        |
  |            |           |       |        |         |        |        |        |
  | Confirm    |           |       |        |         |        |        |        |
  |----------->| G1 OK     |       |        |         |        |        |        |
  |            |           |       |        |         |        |        |        |
  |            | Start     |       |        |         |        |        |        |
  |            |------------------>|        |         |        |        |        |
  |            |           | Tasks |        |         |        |        |        |
  |            |<------------------|        |         |        |        |        |
  |            |           |       |        |         |        |        |        |
  | Plan       |           |       |        |         |        |        |        |
  |<-----------|           |       |        |         |        |        |        |
  | Approve    |           |       |        |         |        |        |        |
  |----------->| G2 OK     |       |        |         |        |        |        |
  |            |           |       |        |         |        |        |        |
  |            | Start     |       |        |         |        |        |        |
  |            |-------------------------->|         |        |        |        |
  |            |           |       | Report |         |        |        |        |
  |            |<--------------------------|         |        |        |        |
  |            | G3 OK     |       |        |         |        |        |        |
  |            |           |       |        |         |        |        |        |
  |            | Fan-out (parallel)         |         |        |        |        |
  |            |-------------------------------------->|        |        |        |
  |            |--------------------------------------------->|        |        |
  |            |---------------------------------------------------->|        |
  |            |--------------------------------------------------------->|
  |            |           |       |        |  Docs   | Wireframes| Schema| Spec|
  |            |<--------------------------------------|        |        |        |
  |            |<---------------------------------------------|        |        |
  |            |<----------------------------------------------------|        |
  |            |<---------------------------------------------------------|
  |            | G4 OK     |       |        |         |        |        |        |
  |            |           |       |        |         |        |        |        |
  | Approve    |           |       |        |         |        |        |        |
  |<-----------|           |       |        |         |        |        |        |
  |----------->|           |       |        |         |        |        |        |
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
  |      | Merge + G7     |       |      |       |       |       |       |       |
  |      |        |        |       |      |       |       |       |       |       |
  |      | Review (parallel)      |      |       |       |       |       |       |
  |      |---------------------------------------------------------------->|     |
  |      |<----------------------------------------------------------------|     |
  |      | G8 OK  |        |       |      |       |       |       |       |       |
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
     | [G11: Approve production?]  |            |            |            |
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

| Phase | L0 (Always Loaded) | L1 (On-Demand) | L2 (Deep Retrieval) |
|-------|-------------------|-----------------|---------------------|
| Brainstorming | Project meta, user input | Similar past projects | Domain knowledge base |
| Planning | Requirements, agent role | PRD full text | Similar past project plans |
| Research | Task + tech constraints | Plan summary | Web search results |
| Architecture | Plan + research summary | Full plan, research detail | Reference architectures |
| Design | Architecture summary | Full architecture, API spec | Design system examples |
| Tech Stack | Architecture + research | Full research evaluations | Template registry |
| Implementation | Task assignment, file spec | Architecture, design tokens, related code | Full codebase search |
| Review | File under review | Architecture doc, style guide | Security rule database |
| Testing | Code under test | API spec, test patterns | Coverage data |
| Debug & Fix | Error + stack trace | Failing test, source file | Related code, similar fixes |
| Deployment | Tech stack, architecture | Build config, CI/CD templates | Cloud provider docs |
| Delivery | Project summary | All phase outputs | Code comments, README patterns |

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
 Phase                          Estimated Time    Parallelism     Agents Active
 ---------------------------------------------------------------------------------
 1.  Brainstorming              2-5 min           Sequential      1 (Brainstorm)
 2.  Planning                   2-5 min           Sequential      2 (Orch + Plan)
 3.  Research                   3-5 min           Internal //     1 (Researcher)
 4.  Architecture & Design      3-5 min           Fan-out //      4 (Arch+Design+DB+API)
 5.  Tech Stack & Template      2-3 min           Sequential      2 (TechStack+Template)
 6.  Implementation             5-15 min          Full //         5 (FE+BE+MW+Mobile+Infra)
     - Merge                    1-2 min           Sequential      1 (Git Manager)
 7.  Review                     2-3 min           Full //         4 (CR+Sec+A11y+Perf)
 8.  Testing                    3-5 min           Internal //     3 (Test+Perf+A11y)
 9.  Debug & Fix                2-10 min          Sequential      2 (Debug+Test)
 10. Deployment                 3-5 min           Sequential      3 (DevOps+Infra+GitHub)
 11. Delivery                   2-3 min           Internal //     2 (DocWriter+GitHub)
 ---------------------------------------------------------------------------------
 TOTAL (simple app)             ~30-66 min
 TOTAL (target)                 <30 min for simple apps

 Pipeline Acceleration Opportunities:
 - Template selection reduces Implementation by ~30%
 - Cached research results reduce Research by ~50%
 - Parallel architecture phase saves ~40% vs sequential
 - Pre-warmed agent pools reduce startup overhead
```

---

## Appendix C: Agent Registry

Complete list of all agents in the CodeBot system with their roles and capabilities.

| # | Agent | Role | Primary Phase | LLM Tier |
|---|-------|------|---------------|----------|
| 1 | Orchestrator | Master coordinator, task decomposition, agent assignment | All | Sonnet |
| 2 | Brainstorming Agent | Ideation, alternative exploration, requirement refinement | Brainstorming | Opus |
| 3 | Planner | Project planning, task scheduling, dependency graphs | Planning | Sonnet |
| 4 | Researcher | Technology research, reference implementation discovery | Research | Gemini Pro |
| 5 | Architect | System architecture, C4 model, data flow | Architecture | Opus |
| 6 | Designer | UI/UX design, component hierarchy, design systems | Architecture | Sonnet |
| 7 | TechStack Builder | Technology selection, compatibility validation | Tech Stack | Sonnet |
| 8 | Template Agent | Template selection, scaffolding, boilerplate | Tech Stack | Haiku |
| 9 | Frontend Developer | UI implementation, client-side logic | Implementation | Sonnet |
| 10 | Backend Developer | API implementation, business logic, data access | Implementation | Sonnet |
| 11 | Middleware Developer | Integration layer, message queues, caching, auth | Implementation | Sonnet |
| 12 | Mobile Developer | iOS/Android/React Native/Flutter development | Implementation | Sonnet |
| 13 | Database Agent | Schema design, optimization, migrations, seeding | Architecture | Sonnet |
| 14 | API Gateway Agent | API design, gateway config, rate limiting | Architecture | Sonnet |
| 15 | Infrastructure Engineer | IaC, Docker, CI/CD, deployment configs | Implementation + Deploy | Sonnet |
| 16 | DevOps Agent | CI/CD pipelines, monitoring, logging, alerting | Deployment | Sonnet |
| 17 | Security Auditor | SAST, DAST, secret scanning, vulnerability assessment | Review | Opus |
| 18 | Code Reviewer | Code quality, style, best practices, arch conformance | Review | Opus |
| 19 | Tester | Test generation, execution, coverage analysis | Testing | Sonnet |
| 20 | Performance Agent | Profiling, optimization, benchmarking | Review + Testing | Sonnet |
| 21 | Accessibility Agent | WCAG compliance, accessibility testing | Review + Testing | Sonnet |
| 22 | i18n/L10n Agent | Internationalization and localization | Implementation | Haiku |
| 23 | Debugger | Root cause analysis, fix generation, regression testing | Debug/Fix | Opus |
| 24 | Documentation Writer | API docs, README, ADRs, deployment guides | Delivery | Gemini Pro |
| 25 | GitHub Agent | Repository management, PRs, Issues, Actions, releases | Deploy + Delivery | Haiku |
| 26 | Skill Creator | Creates reusable skills/capabilities for other agents | On-demand | Opus |
| 27 | Hooks Creator | Creates lifecycle hooks (pre/post build, deploy, test) | On-demand | Sonnet |
| 28 | Tools Creator | Creates custom tools and integrations | On-demand | Sonnet |
| 29 | Integrations Agent | Third-party service integrations | Implementation | Sonnet |
| 30 | Project Manager | Project progress tracking, status reports, timeline management, blocker identification, notifications | Cross-cutting (All) | Sonnet |

---

*This document is a living specification. It will be updated as the CodeBot platform evolves through development milestones M1-M8 as defined in the PRD.*
