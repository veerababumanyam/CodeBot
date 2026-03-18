---
name: CodeBot Pipeline Phase Implementation
description: >
  How to implement, modify, and extend pipeline phases in the CodeBot SDLC pipeline.
  Covers phase models, execution flow, parallel stages, approval gates, and project-type routing.
tags:
  - codebot
  - pipeline
  - sdlc
  - orchestration
  - phases
globs:
  - "apps/server/src/codebot/core/**"
  - "apps/server/src/codebot/events/**"
---

# CodeBot Pipeline Phase Implementation

## Overview

CodeBot uses an 11-stage SDLC pipeline orchestrated by a graph-centric multi-agent system.
Pipeline code lives under `apps/server/src/codebot/core/` with four key modules:

| Module              | Purpose                                              |
|---------------------|------------------------------------------------------|
| `orchestrator.py`   | Top-level pipeline lifecycle and agent coordination   |
| `pipeline.py`       | Pipeline and phase model definitions                 |
| `phase_executor.py` | Runs individual phases, manages entry/exit gates     |
| `task_scheduler.py` | Task dependency resolution and topological ordering  |

Events for phase transitions are in `apps/server/src/codebot/events/`.

---

## Pipeline Stages

| Stage | Name                    | Parallel | Notes                                    |
|-------|-------------------------|----------|------------------------------------------|
| S0    | Project Init            | No       | Input parsing, project type detection    |
| S1    | Discovery/Brainstorming | No       | Idea exploration, scope definition       |
| S2    | Research                | No       | Tech research, competitive analysis      |
| S3    | Architecture & Design   | Yes (4)  | 4 parallel agents                        |
| S4    | Planning & Config       | No       | Task breakdown, config generation        |
| S5    | Implementation          | Yes (6)  | 6 parallel worktrees                     |
| S6    | QA                      | Yes (5)  | 5 parallel QA agents                     |
| S7    | Testing                 | No       | Integration/E2E test execution           |
| S8    | Debug & Stabilize       | No       | Fix failures from S6/S7                  |
| S9    | Documentation           | No       | Generate docs, changelogs, API refs      |
| S10   | Deployment              | No       | Optional -- user can opt out             |

---

## Core Data Models

### PipelinePhase

Every stage is represented as a `PipelinePhase` record with these fields:

| Field              | Type          | Description                                      |
|--------------------|---------------|--------------------------------------------------|
| `id`               | UUID          | Unique phase identifier                          |
| `pipeline_id`      | UUID          | Parent pipeline reference                        |
| `name`             | str           | Human-readable phase name                        |
| `phase_type`       | PhaseType     | Enum value (see below)                           |
| `status`           | PhaseStatus   | Current execution status                         |
| `order`            | int           | Execution order within the pipeline              |
| `requires_approval`| bool          | Whether a human approval gate precedes this phase|
| `input_data`       | dict          | Data passed in from previous phase or user       |
| `output_data`      | dict          | Results produced by this phase                   |

### PhaseType Enum

```python
class PhaseType(str, Enum):
    BRAINSTORMING = "brainstorming"
    TECH_STACK_SELECTION = "tech_stack_selection"
    TEMPLATE_SELECTION = "template_selection"
    PLANNING = "planning"
    RESEARCH = "research"
    ARCHITECTURE = "architecture"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    TESTING = "testing"
    DEBUG_FIX = "debug_fix"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    DELIVERY = "delivery"
```

### PhaseStatus Enum

```python
class PhaseStatus(str, Enum):
    PENDING = "pending"
    WAITING_APPROVAL = "waiting_approval"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
```

---

## Project Type Routing

Different project types enter the pipeline at different points and follow different paths:

### Greenfield (new project)
Full pipeline: S0 -> S1 -> S2 -> S3 -> S4 -> S5 -> S6 -> S7 -> S8 -> S9 -> (S10)

### Inflight (joining mid-development)
Analysis -> S1 (scoped) -> S4 -> S5 -> S6 -> S7 -> S8 -> S9 -> (S10)

- Skips S2 (Research) and S3 (Architecture) since the project already has those decisions made.
- S1 is scoped to understanding what exists and what needs to be built next.

### Brownfield (legacy modernization)
Assessment -> S3 -> S4 -> S5 -> S6 -> S7 -> S8 -> S9 -> (S10)

- Starts with a codebase assessment phase.
- Skips S1-S2 since the product already exists.

### Improve (experiment/iterate)
Analysis -> ExperimentLoop -> Report

- Does not follow the standard linear pipeline.
- Runs an iterative experiment loop with its own internal phases.

---

## Adding a New Phase

### Step 1: Define the PhaseType

If the new phase does not map to an existing `PhaseType`, add a new value to the enum
in `apps/server/src/codebot/core/pipeline.py`:

```python
class PhaseType(str, Enum):
    # ... existing values ...
    MY_NEW_PHASE = "my_new_phase"
```

### Step 2: Create the Phase Executor Logic

Add a handler in `apps/server/src/codebot/core/phase_executor.py`. The executor must:

1. Accept `input_data` from the previous phase.
2. Perform its work (call agents, run tools, etc.).
3. Return `output_data` for the next phase.
4. Update `PhaseStatus` throughout execution.

```python
async def execute_my_new_phase(phase: PipelinePhase, context: PipelineContext) -> dict:
    phase.status = PhaseStatus.RUNNING
    # ... do work ...
    phase.status = PhaseStatus.COMPLETED
    return {"result": "..."}
```

### Step 3: Register the Phase in the Pipeline

In `orchestrator.py`, add the phase to the appropriate position in the stage sequence.
Set the `order` field to control where it runs relative to other phases:

```python
PipelinePhase(
    pipeline_id=pipeline.id,
    name="My New Phase",
    phase_type=PhaseType.MY_NEW_PHASE,
    status=PhaseStatus.PENDING,
    order=35,  # between S3 (order=30) and S4 (order=40)
    requires_approval=True,
    input_data={},
    output_data={},
)
```

### Step 4: Wire Up Events

Register phase transition events in `apps/server/src/codebot/events/`:

```python
@event_handler("phase.my_new_phase.started")
async def on_my_new_phase_started(event: PhaseEvent):
    # Notify listeners, update UI, log metrics
    ...

@event_handler("phase.my_new_phase.completed")
async def on_my_new_phase_completed(event: PhaseEvent):
    # Trigger downstream phases, update dashboard
    ...
```

### Step 5: Update Project Type Routing

If the new phase should only run for certain project types, update the routing logic
in `orchestrator.py`. Each project type has a list of phase types that are included:

```python
GREENFIELD_PHASES = [..., PhaseType.MY_NEW_PHASE, ...]
INFLIGHT_PHASES = [...]  # include or exclude as needed
BROWNFIELD_PHASES = [...]
```

---

## Entry and Exit Gates

Each phase transition passes through gates that enforce preconditions:

### Entry Gates (before a phase starts)
- Verify all predecessor phases are `COMPLETED`.
- Check `requires_approval` -- if true, block until human approves.
- Validate that `input_data` meets the phase's schema requirements.

### Exit Gates (after a phase completes)
- Validate `output_data` against expected schema.
- Run quality checks (e.g., S5 exit gate checks that code compiles).
- Update checkpoint state for pause/resume support.

To add a custom gate, implement a gate function and register it:

```python
async def my_entry_gate(phase: PipelinePhase, context: PipelineContext) -> bool:
    """Return True to allow phase to proceed, False to block."""
    if not context.has_required_data("architecture_doc"):
        return False
    return True
```

---

## Parallel Execution Within Stages

Stages S3, S5, and S6 run multiple agents in parallel. The `task_scheduler.py` module
handles this using topological ordering of task dependencies.

### How Parallel Phases Work

1. The phase executor spawns multiple tasks within the phase.
2. Each task declares its dependencies on other tasks.
3. `task_scheduler.py` computes a topological sort and groups independent tasks.
4. Independent task groups execute concurrently.
5. The phase is `COMPLETED` only when all tasks finish successfully.

### Example: Adding a Parallel Agent to S6 (QA)

```python
# In the S6 phase executor
qa_tasks = [
    Task(name="lint_check", agent="LintAgent", depends_on=[]),
    Task(name="security_scan", agent="SecurityAgent", depends_on=[]),
    Task(name="accessibility_audit", agent="A11yAgent", depends_on=[]),
    Task(name="perf_profile", agent="PerfAgent", depends_on=[]),
    Task(name="code_review", agent="ReviewAgent", depends_on=[]),
    # Add your new parallel task:
    Task(name="license_check", agent="LicenseAgent", depends_on=[]),
]
schedule = task_scheduler.topological_sort(qa_tasks)
results = await task_scheduler.execute_parallel(schedule, context)
```

Tasks with `depends_on` values will wait for their dependencies before starting.

---

## Cross-Cutting Agents

Three agents operate across all pipeline stages and do not belong to any single phase:

| Agent            | Role                                                  |
|------------------|-------------------------------------------------------|
| Orchestrator     | Manages pipeline flow, phase transitions, error recovery |
| Project Manager  | Tracks progress, manages scope, reports status        |
| GitHub Agent     | Handles repo operations, PRs, branch management       |

These agents react to phase events and can inject work into any phase. When adding a
new phase, ensure these agents are notified via the event system.

---

## Checkpoint and Pause/Resume

The pipeline supports checkpointing at phase boundaries for pause/resume:

- After each phase completes, a checkpoint is saved with the full pipeline state.
- To resume, load the checkpoint and restart from the next pending phase.
- Checkpoints include: all phase statuses, output_data, agent states, and context.

When implementing a new phase, ensure `output_data` is fully serializable so
checkpoints work correctly. Avoid storing non-serializable objects (file handles,
connections, etc.) in phase output.

---

## Human Approval Gates

Phases with `requires_approval=True` will pause the pipeline and wait for human input
before executing. The flow is:

1. Previous phase completes.
2. Pipeline sets next phase status to `WAITING_APPROVAL`.
3. UI/CLI notifies the user and presents phase details.
4. User approves, rejects, or requests changes.
5. On approval, phase transitions to `RUNNING`.
6. On rejection, phase transitions to `SKIPPED` and pipeline evaluates skip logic.

Set `requires_approval` based on how critical the phase is. Recommended approval gates:
- After S1 (Discovery) -- confirm scope before investing in research/architecture.
- After S3 (Architecture) -- confirm design before implementation begins.
- After S6 (QA) -- review quality results before proceeding to testing.
- Before S10 (Deployment) -- confirm readiness for production.

---

## Modifying an Existing Phase

### Changing Phase Behavior

Edit the corresponding handler in `phase_executor.py`. The phase's `input_data` and
`output_data` contracts should remain backward-compatible to avoid breaking checkpoints.

### Changing Phase Order

Update the `order` field in `orchestrator.py`. Ensure no two phases share the same
order value. Re-test all project type routing paths after reordering.

### Making a Phase Optional

Set a condition in the orchestrator that checks pipeline config:

```python
if pipeline.config.get("skip_documentation", False):
    doc_phase.status = PhaseStatus.SKIPPED
```

S10 (Deployment) is already optional by default -- users opt in during project init.

### Adding Dependencies Between Phases

Phases execute in `order` sequence by default. For explicit dependencies beyond
ordering, add them to the phase's entry gate:

```python
async def s7_entry_gate(phase, context):
    s5 = context.get_phase(PhaseType.IMPLEMENTATION)
    s6 = context.get_phase(PhaseType.REVIEW)
    return s5.status == PhaseStatus.COMPLETED and s6.status == PhaseStatus.COMPLETED
```

---

## Common Patterns

### Pattern: Phase That Calls a CLI Coding Agent

S5 (Implementation) uses CLI coding agents (Claude Code, OpenAI Codex, Gemini CLI)
in parallel worktrees. To add a new coding agent integration:

```python
async def run_coding_agent(task: Task, worktree_path: str, context: PipelineContext):
    agent_type = context.config.get("coding_agent", "claude_code")
    if agent_type == "claude_code":
        result = await claude_code_adapter.execute(worktree_path, task.prompt)
    elif agent_type == "codex":
        result = await codex_adapter.execute(worktree_path, task.prompt)
    # ... etc
    return result
```

### Pattern: Phase With Retry on Failure

Wrap the phase executor with retry logic for transient failures:

```python
async def execute_with_retry(phase, context, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await execute_phase(phase, context)
        except TransientError:
            if attempt == max_retries - 1:
                phase.status = PhaseStatus.FAILED
                raise
            await asyncio.sleep(2 ** attempt)
```

### Pattern: Conditional Phase Based on Previous Output

```python
async def should_run_debug_phase(context: PipelineContext) -> bool:
    qa_output = context.get_phase_output(PhaseType.REVIEW)
    test_output = context.get_phase_output(PhaseType.TESTING)
    has_failures = qa_output.get("failures", 0) > 0 or test_output.get("failures", 0) > 0
    return has_failures
```

---

## Debugging Tips

1. **Phase stuck in RUNNING**: Check `phase_executor.py` logs for unhandled exceptions.
   A phase that throws without catching will not transition to FAILED automatically
   unless the orchestrator's error handler catches it.

2. **Phase skipped unexpectedly**: Check project type routing. The phase may not be
   in the phase list for the current project type.

3. **Parallel tasks deadlocked**: Check for circular dependencies in `depends_on`.
   `task_scheduler.py` should raise on cycles, but verify the dependency graph.

4. **Checkpoint resume starts wrong phase**: Verify all phases before the resume point
   have status `COMPLETED` in the checkpoint data.

5. **Event not firing**: Ensure the event handler is registered in
   `apps/server/src/codebot/events/` and the event name matches exactly.
