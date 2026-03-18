# Phase 6: Pipeline Orchestration - Research

**Researched:** 2026-03-18
**Domain:** Durable workflow orchestration, multi-stage pipeline execution, checkpoint/resume, human-in-the-loop gates
**Confidence:** HIGH

## Summary

Phase 6 builds the Pipeline Orchestration layer that drives CodeBot's 10-stage SDLC pipeline (S0-S9) using Temporal for durable workflow orchestration and NATS JetStream for event emission. This phase sits on top of the Graph Engine (Phase 2), Agent Framework (Phase 3), LLM Abstraction (Phase 4), and Context Management (Phase 5), wiring them together into a resilient, checkpoint-enabled pipeline with human approval gates and configurable presets.

The research confirms that the **Activity-StateGraph pattern** (wrapping agent/graph execution inside Temporal activities, with Temporal managing the workflow-level orchestration) is the production-proven approach for this architecture. Temporal provides durable execution with automatic retry, crash recovery, and signal-based human-in-the-loop -- all requirements for PIPE-01 through PIPE-08. NATS JetStream provides the event emission layer for real-time pipeline observability.

The primary risk flagged in STATE.md -- "Activity-StateGraph pattern has limited production documentation" -- is now lower. Multiple production case studies (Grid Dynamics, Fortune 500 pilots) validate this pattern as of late 2025. The key architectural decision is to make each pipeline phase a Temporal activity (or child workflow for parallel phases), with the top-level SDLC workflow managing phase sequencing, checkpointing, and gate logic.

**Primary recommendation:** Use Temporal workflows for pipeline orchestration with each phase as an activity/child-workflow, signals for human gates, continue-as-new for long-running pipelines, and NATS JetStream for event emission. Load pipeline presets from YAML via Pydantic v2 model_validate.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PIPE-01 | 10-stage SDLC pipeline (S0-S9) executes end-to-end | Temporal workflow with sequential phase execution; each phase is a Temporal activity or child workflow |
| PIPE-02 | S3, S5, S6 execute agents in parallel via DAG topology | Temporal child workflows + asyncio.gather for parallel phase execution; merge results before advancing |
| PIPE-03 | Pipeline supports entry/exit gates with human approval | Temporal signals + workflow.wait_condition for human-in-the-loop gates with configurable timeout |
| PIPE-04 | Pipeline configurations loadable from YAML presets | Pydantic v2 models + PyYAML yaml.safe_load + model_validate for typed config loading |
| PIPE-05 | Temporal provides durable workflow orchestration with retry, timeout, crash recovery | Native Temporal capability: activity retry policies, workflow timeouts, automatic replay on crash |
| PIPE-06 | Pipeline can resume from last checkpoint after failure or manual pause | Temporal's built-in durable execution replays to last completed activity; continue-as-new for event history management |
| PIPE-07 | Pipeline detects project type and adapts stage configuration | YAML preset system with conditional stage skipping; project type detection feeds into preset selection |
| PIPE-08 | Pipeline emits events to NATS JetStream for every stage transition, agent action, gate decision | nats-py async client with JetStream publish for event emission at pipeline orchestration boundaries |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| temporalio | 1.23.0 | Durable workflow orchestration | 18.9K stars, MIT, used by Stripe/Netflix/Datadog; provides retry, crash recovery, signals, child workflows |
| nats-py | 2.14.0 | Event emission to NATS JetStream | Official async Python client for NATS; sub-ms latency pub/sub with JetStream persistence |
| pydantic | 2.x (already in project) | Pipeline config validation | Already project standard per CLAUDE.md; model_validate for YAML-loaded configs |
| pyyaml | 6.0.3 | YAML config parsing | Standard YAML parser; yaml.safe_load feeds into Pydantic model_validate |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| temporalio[opentelemetry] | 1.23.0 | Distributed tracing integration | When adding observability to pipeline workflows |
| aiofiles | 24.x (already in project) | Async file I/O for checkpoint artifacts | When reading/writing checkpoint metadata alongside Temporal state |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Temporal for orchestration | LangGraph alone | LangGraph lacks production-grade retry, crash recovery, distributed execution; fine for agent-level logic but not pipeline-level durability |
| Temporal for orchestration | Taskiq (already in stack) | Taskiq is a task queue, not a workflow engine; no native checkpointing, signal handling, or workflow replay |
| NATS JetStream for events | Redis Streams | NATS provides better exactly-once delivery and replay; already decided in ADR-005 |

**Installation:**
```bash
uv add temporalio nats-py pyyaml
```

**Version verification:** Versions confirmed against PyPI on 2026-03-18. temporalio 1.23.0 (released 2026-02-18), nats-py 2.14.0 (released 2026-02-23), pyyaml 6.0.3 (stable).

## Architecture Patterns

### Recommended Project Structure

```
apps/server/src/codebot/pipeline/
    __init__.py
    models.py              # Pydantic models: PipelineConfig, PhaseConfig, GateConfig, PresetConfig
    loader.py              # YAML preset loader: load_preset() -> PipelineConfig
    workflows.py           # Temporal workflows: SDLCPipelineWorkflow, PhaseWorkflow
    activities.py          # Temporal activities: execute_phase, run_human_gate, emit_event
    gates.py               # HumanGate logic: approval request/response via Temporal signals
    checkpoint.py          # Checkpoint data models and helpers (supplements Temporal's built-in state)
    escalation.py          # ErrorEscalation strategies (retry, fallback, simplify, escalate)
    presets/               # YAML pipeline preset files
        full.yaml          # All 10 stages, all gates enabled
        quick.yaml         # Subset of stages, gates auto-approved
        review-only.yaml   # S6 QA only, for code review workflows
    project_detector.py    # Project type detection (greenfield/inflight/brownfield)
    events.py              # Pipeline event definitions and NATS emission helpers
    registry.py            # Phase-to-agent mapping registry
```

### Pattern 1: Activity-StateGraph (Top-Level Pipeline Workflow)

**What:** The top-level SDLC pipeline is a Temporal workflow. Each phase is executed as a Temporal activity or child workflow. Temporal manages sequencing, checkpointing, and crash recovery.

**When to use:** Always -- this is the core pipeline orchestration pattern.

**Example:**

```python
# Source: Temporal Python SDK docs + CodeBot design docs
from dataclasses import dataclass
from typing import Optional
from datetime import timedelta
import asyncio

from temporalio import workflow, activity
from temporalio.common import RetryPolicy


@dataclass
class PipelineInput:
    """Input to the SDLC pipeline workflow."""
    project_id: str
    preset_name: str  # "full", "quick", "review-only"
    project_type: str  # "greenfield", "inflight", "brownfield"
    resume_from_phase: Optional[int] = None


@dataclass
class PhaseInput:
    """Input to a single phase activity."""
    project_id: str
    phase_name: str
    phase_idx: int
    agents: list[str]
    parallel: bool
    config: dict  # serializable phase config


@dataclass
class PhaseResult:
    """Result from a phase execution."""
    phase_name: str
    phase_idx: int
    status: str  # "completed", "failed", "skipped"
    agent_results: list[dict]
    duration_ms: int
    tokens_used: int
    cost_usd: float


@workflow.defn
class SDLCPipelineWorkflow:
    """Top-level durable SDLC pipeline workflow."""

    def __init__(self) -> None:
        self.gate_decisions: dict[str, str] = {}
        self.current_phase_idx: int = 0
        self.is_paused: bool = False

    @workflow.signal
    async def approve_gate(self, gate_id: str, decision: str, feedback: str = "") -> None:
        """Signal handler for human gate decisions."""
        self.gate_decisions[gate_id] = decision

    @workflow.signal
    async def pause_pipeline(self) -> None:
        """Signal to pause the pipeline."""
        self.is_paused = True

    @workflow.signal
    async def resume_pipeline(self) -> None:
        """Signal to resume a paused pipeline."""
        self.is_paused = False

    @workflow.query
    def get_status(self) -> dict:
        """Query current pipeline status."""
        return {
            "current_phase_idx": self.current_phase_idx,
            "is_paused": self.is_paused,
        }

    @workflow.run
    async def run(self, input: PipelineInput) -> dict:
        # Load pipeline config (activity -- non-deterministic I/O)
        config = await workflow.execute_activity(
            load_pipeline_config,
            input.preset_name,
            start_to_close_timeout=timedelta(seconds=30),
        )

        start_idx = input.resume_from_phase or 0
        results: list[PhaseResult] = []

        for idx, phase in enumerate(config["phases"]):
            if idx < start_idx:
                continue  # Skip already-completed phases on resume

            self.current_phase_idx = idx

            # Check if paused
            await workflow.wait_condition(lambda: not self.is_paused)

            # Emit phase start event
            await workflow.execute_activity(
                emit_pipeline_event,
                {"type": "pipeline.phase_transition", "phase": phase["name"], "status": "started"},
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Execute the phase
            if phase.get("parallel", False):
                result = await self._execute_parallel_phase(input.project_id, phase, idx)
            else:
                result = await self._execute_sequential_phase(input.project_id, phase, idx)

            results.append(result)

            # Human gate check
            if phase.get("human_gate", False):
                gate_result = await self._wait_for_gate(
                    gate_id=f"gate_{phase['name']}",
                    timeout_minutes=phase.get("gate_timeout_minutes", 30),
                )
                if gate_result == "rejected":
                    # Re-execute phase with feedback
                    continue

            # Emit phase complete event
            await workflow.execute_activity(
                emit_pipeline_event,
                {"type": "pipeline.phase_transition", "phase": phase["name"], "status": "completed"},
                start_to_close_timeout=timedelta(seconds=10),
            )

            # Check if continue-as-new is suggested (event history management)
            if workflow.info().is_continue_as_new_suggested():
                await workflow.wait_condition(workflow.all_handlers_finished)
                workflow.continue_as_new(
                    PipelineInput(
                        project_id=input.project_id,
                        preset_name=input.preset_name,
                        project_type=input.project_type,
                        resume_from_phase=idx + 1,
                    )
                )

        return {"status": "completed", "phases_completed": len(results)}

    async def _execute_parallel_phase(
        self, project_id: str, phase: dict, idx: int
    ) -> PhaseResult:
        """Execute agents in parallel via child workflows."""
        child_handles = []
        for agent in phase["agents"]:
            handle = await workflow.start_child_workflow(
                PhaseAgentWorkflow.run,
                PhaseInput(
                    project_id=project_id,
                    phase_name=phase["name"],
                    phase_idx=idx,
                    agents=[agent],
                    parallel=False,
                    config=phase,
                ),
            )
            child_handles.append(handle)
        results = await asyncio.gather(*child_handles)
        return PhaseResult(
            phase_name=phase["name"],
            phase_idx=idx,
            status="completed",
            agent_results=[r for r in results],
            duration_ms=0,
            tokens_used=0,
            cost_usd=0.0,
        )

    async def _wait_for_gate(self, gate_id: str, timeout_minutes: int) -> str:
        """Wait for human approval signal with timeout."""
        # Emit approval required event
        await workflow.execute_activity(
            emit_pipeline_event,
            {"type": "approval.required", "gate_id": gate_id},
            start_to_close_timeout=timedelta(seconds=10),
        )
        try:
            await workflow.wait_condition(
                lambda: gate_id in self.gate_decisions,
                timeout=timedelta(minutes=timeout_minutes),
            )
            return self.gate_decisions[gate_id]
        except asyncio.TimeoutError:
            return "auto_approved"  # Default on timeout
```

### Pattern 2: YAML Preset Loading with Pydantic v2

**What:** Pipeline configurations are defined in YAML files and validated through Pydantic v2 models.

**When to use:** Loading pipeline presets (full, quick, review-only) and project-type-specific configurations.

**Example:**

```python
# Source: Pydantic v2 docs + PyYAML
from pathlib import Path
from pydantic import BaseModel, field_validator
import yaml


class GateConfig(BaseModel):
    enabled: bool = False
    prompt: str = ""
    timeout_minutes: int = 30
    timeout_action: str = "auto_approve"  # "auto_approve" | "pause"
    mandatory: bool = False


class PhaseConfig(BaseModel):
    name: str
    agents: list[str]
    sequential: bool = True
    human_gate: GateConfig = GateConfig()
    on_failure: str = "escalate"  # "reroute_to_implement" | "escalate"
    loop: dict | None = None
    skip_for_project_types: list[str] = []

    @property
    def parallel(self) -> bool:
        return not self.sequential


class PipelineSettings(BaseModel):
    max_parallel_agents: int = 5
    checkpoint_after_each_phase: bool = True
    cost_limit_usd: float = 50.0
    timeout_minutes: int = 120


class PipelineConfig(BaseModel):
    name: str
    version: str
    description: str = ""
    settings: PipelineSettings = PipelineSettings()
    phases: list[PhaseConfig]

    @field_validator("phases")
    @classmethod
    def validate_phases_not_empty(cls, v: list[PhaseConfig]) -> list[PhaseConfig]:
        if not v:
            raise ValueError("Pipeline must have at least one phase")
        return v


def load_preset(preset_name: str, config_dir: Path = Path("configs/pipelines")) -> PipelineConfig:
    """Load and validate a pipeline preset from YAML."""
    path = config_dir / f"{preset_name}.yaml"
    with open(path) as f:
        raw = yaml.safe_load(f)
    return PipelineConfig.model_validate(raw["pipeline"])
```

### Pattern 3: NATS JetStream Event Emission

**What:** Every pipeline state transition emits an event to NATS JetStream for observability.

**When to use:** At every phase start/complete/fail, gate decision, and pipeline lifecycle event.

**Example:**

```python
# Source: nats-py docs
import nats
from nats.js.api import StreamConfig
import json
from datetime import datetime, timezone


class PipelineEventEmitter:
    """Emits pipeline events to NATS JetStream."""

    def __init__(self, nc: nats.NATS, stream_name: str = "PIPELINE_EVENTS") -> None:
        self._nc = nc
        self._js = nc.jetstream()
        self._stream_name = stream_name

    async def ensure_stream(self) -> None:
        """Create the JetStream stream if it doesn't exist."""
        await self._js.add_stream(
            StreamConfig(
                name=self._stream_name,
                subjects=["pipeline.>"],
                retention="limits",
                max_age=7 * 24 * 3600 * 1_000_000_000,  # 7 days in nanoseconds
            )
        )

    async def emit(self, event_type: str, data: dict) -> None:
        """Emit a pipeline event to JetStream."""
        payload = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        subject = f"pipeline.{event_type.replace('.', '_')}"
        ack = await self._js.publish(
            subject,
            json.dumps(payload).encode(),
        )
        # ack confirms durable storage
```

### Pattern 4: Project Type Detection and Adaptive Pipeline

**What:** Detect whether a project is greenfield, inflight, or brownfield and adapt the pipeline configuration accordingly.

**When to use:** At pipeline initialization (PIPE-07).

**Example:**

```python
# Source: CodeBot design docs (AGENT_WORKFLOWS.md Section 5)
from enum import Enum


class ProjectType(str, Enum):
    GREENFIELD = "greenfield"
    INFLIGHT = "inflight"
    BROWNFIELD = "brownfield"


def adapt_pipeline_for_project_type(
    config: PipelineConfig,
    project_type: ProjectType,
) -> PipelineConfig:
    """Filter pipeline phases based on project type."""
    adapted_phases = [
        phase for phase in config.phases
        if project_type.value not in phase.skip_for_project_types
    ]
    return config.model_copy(update={"phases": adapted_phases})
```

### Anti-Patterns to Avoid

- **Putting non-deterministic code in Temporal workflows:** All I/O, random number generation, and system clock access must happen inside activities, not in the workflow function. Workflows must be deterministic for replay.
- **Skipping continue-as-new for long pipelines:** A full SDLC pipeline with many activities can exceed Temporal's 50K event history limit. Use `is_continue_as_new_suggested()` and pass pipeline state forward.
- **Sharing LangGraph state across Temporal activity boundaries:** LangGraph instances in different activities cannot share state directly. Serialize all state at activity boundaries using Pydantic models or dataclasses.
- **Direct agent-to-agent calls inside pipeline orchestration:** Per CLAUDE.md architecture rules, agents communicate via NATS event bus and SharedState, not direct calls. The pipeline orchestrator dispatches work through the graph engine.
- **Blocking the Temporal event loop with synchronous code:** All agent execution and LLM calls are async. Use `activity.defn` with async functions or threaded activities for sync operations.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Workflow durability / crash recovery | Custom checkpoint system with filesystem JSON | Temporal's built-in durable execution | Temporal replays workflow history automatically; hand-rolled checkpoints miss edge cases (partial writes, corruption, race conditions) |
| Activity retry with backoff | Custom retry loop with sleep | Temporal RetryPolicy | Temporal retries survive process crashes; custom loops don't |
| Human-in-the-loop blocking | Custom asyncio.Event + polling | Temporal signals + wait_condition | Temporal signals are durable (survive crashes, wait indefinitely at zero resource cost); custom solutions require active processes |
| Parallel execution coordination | Custom asyncio.gather with error handling | Temporal child workflows + gather | Child workflows are individually durable; if one fails, others aren't lost |
| Event history management | Manual log truncation | Temporal continue-as-new | Temporal's event history has a 50K event / 50MB hard limit; continue-as-new handles this correctly |
| Timer-based timeouts | Custom threading.Timer or asyncio.sleep | Temporal workflow timers (workflow.wait_condition with timeout) | Temporal timers survive crashes; asyncio.sleep does not |

**Key insight:** Temporal's value proposition is exactly crash-proof workflow orchestration. Building a custom version would duplicate the hardest part of distributed systems (exactly-once execution, durable state) while missing subtle edge cases that Temporal has solved over years of production use.

## Common Pitfalls

### Pitfall 1: Non-Deterministic Workflow Code

**What goes wrong:** Using `datetime.now()`, `uuid.uuid4()`, `random.random()`, or any I/O inside a Temporal workflow function causes replay failures.
**Why it happens:** Temporal replays workflows by re-executing the workflow code and matching against recorded history. Non-deterministic calls produce different results on replay.
**How to avoid:** Move all non-deterministic operations into activities. Use `workflow.uuid4()` for UUIDs and `workflow.now()` for timestamps inside workflows.
**Warning signs:** `NonDeterminismError` exceptions during workflow replay.

### Pitfall 2: Forgetting Continue-As-New for Long Pipelines

**What goes wrong:** A full SDLC pipeline with many parallel agents generates thousands of events. The workflow hits the 50K event / 50MB history limit and fails.
**Why it happens:** Each activity start, activity complete, child workflow start, signal, and timer is an event. A 10-phase pipeline with parallel agents easily generates thousands.
**How to avoid:** Check `workflow.info().is_continue_as_new_suggested()` after each phase. Pass current pipeline state (completed phases, results) as input to the continued workflow.
**Warning signs:** Workflow execution slowing down; `workflow.info().get_current_history_length()` approaching 50,000.

### Pitfall 3: Signals Lost During Continue-As-New

**What goes wrong:** A human approval signal arrives while the workflow is performing continue-as-new. The signal is lost because the old workflow execution has closed.
**Why it happens:** Continue-as-new closes the current execution. Pending signals for the closed execution are lost.
**How to avoid:** Before calling `continue_as_new()`, drain all pending signals and wait for all handlers to finish: `await workflow.wait_condition(workflow.all_handlers_finished)`. Signal with empty Run ID so Temporal routes to the current open execution.
**Warning signs:** Human approvals seem to disappear; gate decisions not being recorded.

### Pitfall 4: Temporal Sandbox Passthrough for LangGraph

**What goes wrong:** Temporal's deterministic sandbox blocks imports of LangGraph/LangChain modules inside workflows.
**Why it happens:** Temporal restricts non-deterministic library imports in workflow code to enforce determinism.
**How to avoid:** Configure sandbox passthrough for langchain modules in the Worker: `workflow_sandbox_unrestricted_modules=["langchain_core", "langchain_openai", ...]`. Better yet, keep all LangGraph execution inside activities (not workflows).
**Warning signs:** `ImportError` or `RestrictedWorkflowAccessError` when starting workers.

### Pitfall 5: Activity Timeout Configuration

**What goes wrong:** Agent execution activities time out because the default timeout is too short for LLM-heavy operations, or too long for simple operations.
**Why it happens:** A single `start_to_close_timeout` doesn't fit all activity types. LLM agent execution can take minutes; event emission takes milliseconds.
**How to avoid:** Configure timeouts per activity type. Agent execution: 10-30 minute `start_to_close_timeout` with `heartbeat_timeout` of 60 seconds. Event emission: 10 second timeout. Config loading: 30 second timeout.
**Warning signs:** Activities being retried unnecessarily (timeout too short) or hanging indefinitely (no timeout set).

### Pitfall 6: Serialization at Activity Boundaries

**What goes wrong:** Complex Python objects (e.g., LangGraph state, agent instances) fail to serialize when passed between Temporal workflows and activities.
**Why it happens:** Temporal serializes all inputs/outputs via its data converter (JSON by default). Non-serializable objects cause failures.
**How to avoid:** Use only dataclasses or Pydantic models with primitive fields for all activity inputs/outputs. Convert complex state to dictionaries at boundaries. Design state transfer objects (DTOs) specifically for cross-boundary communication.
**Warning signs:** `DataConverter` errors; `TypeError: Object of type X is not JSON serializable`.

### Pitfall 7: NATS Connection Management in Activities

**What goes wrong:** Each activity invocation creates a new NATS connection, leading to connection exhaustion.
**Why it happens:** Activities are meant to be short-lived, but NATS connection setup has overhead.
**How to avoid:** Manage the NATS connection at the Worker level (outside activities). Pass the connection via activity context or use a singleton pattern within the Worker process. Register the connection as a shared resource.
**Warning signs:** NATS connection errors; "too many connections" from NATS server logs.

## Code Examples

### Temporal Worker Setup

```python
# Source: Temporal Python SDK docs
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker


async def main() -> None:
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="codebot-pipeline",
        workflows=[SDLCPipelineWorkflow, PhaseAgentWorkflow],
        activities=[
            load_pipeline_config,
            execute_phase_activity,
            emit_pipeline_event,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
```

### Activity: Execute Phase

```python
# Source: Temporal Python SDK docs + CodeBot design
from temporalio import activity
from datetime import timedelta


@activity.defn
async def execute_phase_activity(input: PhaseInput) -> PhaseResult:
    """Execute a single pipeline phase via the graph engine."""
    activity.heartbeat("Starting phase execution")

    # Get the graph engine and agent registry (injected via worker context)
    graph_engine = get_graph_engine()
    agent_registry = get_agent_registry()

    results = []
    if input.parallel:
        # Use asyncio.TaskGroup for parallel agent execution within this activity
        async with asyncio.TaskGroup() as tg:
            tasks = []
            for agent_name in input.agents:
                agent = agent_registry.get(agent_name)
                task = tg.create_task(agent.execute(input.project_id))
                tasks.append(task)
        results = [t.result() for t in tasks]
    else:
        for agent_name in input.agents:
            activity.heartbeat(f"Executing agent: {agent_name}")
            agent = agent_registry.get(agent_name)
            result = await agent.execute(input.project_id)
            results.append(result)

    return PhaseResult(
        phase_name=input.phase_name,
        phase_idx=input.phase_idx,
        status="completed",
        agent_results=results,
        duration_ms=0,
        tokens_used=0,
        cost_usd=0.0,
    )
```

### Activity: Emit Pipeline Event via NATS

```python
# Source: nats-py JetStream docs
from temporalio import activity
import nats
import json
from datetime import datetime, timezone


@activity.defn
async def emit_pipeline_event(event_data: dict) -> None:
    """Emit a pipeline event to NATS JetStream."""
    nc = await nats.connect("nats://localhost:4222")
    js = nc.jetstream()

    payload = {
        **event_data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    subject = f"pipeline.{event_data['type'].replace('.', '_')}"
    await js.publish(subject, json.dumps(payload).encode())
    await nc.close()
```

### Starting and Signaling a Pipeline

```python
# Source: Temporal Python SDK client docs
from temporalio.client import Client


async def start_pipeline(project_id: str, preset: str = "full") -> str:
    """Start a new SDLC pipeline execution."""
    client = await Client.connect("localhost:7233")
    handle = await client.start_workflow(
        SDLCPipelineWorkflow.run,
        PipelineInput(project_id=project_id, preset_name=preset, project_type="greenfield"),
        id=f"pipeline-{project_id}",
        task_queue="codebot-pipeline",
    )
    return handle.id


async def approve_gate(workflow_id: str, gate_id: str, decision: str = "approved") -> None:
    """Send human approval signal to a running pipeline."""
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(workflow_id)
    await handle.signal(SDLCPipelineWorkflow.approve_gate, gate_id, decision)
```

### Docker Compose Addition for Temporal Server

```yaml
# Source: temporalio/samples-server compose
# Add to existing docker-compose.yml
services:
  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"   # gRPC frontend
    environment:
      - DB=postgres12
      - DB_PORT=5432
      - POSTGRES_USER=codebot
      - POSTGRES_PWD=codebot
      - POSTGRES_SEEDS=postgres
    depends_on:
      - postgres

  temporal-ui:
    image: temporalio/ui:latest
    ports:
      - "8233:8080"  # Temporal Web UI
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
    depends_on:
      - temporal
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Redis-based state management with custom retry | Temporal durable workflows | 2024-2025 | Eliminates custom checkpoint/retry code; state becomes intrinsic to workflow |
| LangGraph-only orchestration | Temporal (orchestration) + LangGraph (agent logic) | 2025 | Separation of concerns; LangGraph for agent decision graphs, Temporal for pipeline durability |
| Custom human-in-the-loop polling | Temporal signals + wait_condition | 2024 | Zero resource cost while waiting; durable across crashes; supports indefinite waits |
| Manual event history management | Temporal continue-as-new | Built-in | Automatic workflow chain management for long-running pipelines |
| Temporal suggest_continue_as_new | `workflow.info().is_continue_as_new_suggested()` | SDK 1.x | Server-side suggestion based on actual history size vs. limits |

**Deprecated/outdated:**
- `temporalio.Client` older connection patterns: Use `Client.connect()` (async context manager style) in current SDK.
- Redis Streams for event bus: NATS JetStream provides superior exactly-once delivery, replay, and consumer groups (ADR-005).
- LangGraph 0.x patterns: LangGraph 1.0 (released October 2025) has different persistence APIs. Since we use LangGraph only inside Temporal activities, this affects agent-level code (Phase 2/3), not pipeline orchestration.

## Open Questions

1. **Temporal Server Resource Requirements for Pipeline Scale**
   - What we know: Temporal server runs on PostgreSQL (already in our stack). Default config handles thousands of concurrent workflows.
   - What's unclear: How many concurrent SDLC pipelines CodeBot should target for v1. This affects Temporal server sizing.
   - Recommendation: Start with single-pipeline execution for v1. Temporal scales horizontally, so defer multi-pipeline scaling to later.

2. **Activity-StateGraph Pattern: Granularity of Activities**
   - What we know: Each pipeline phase should be at minimum one activity. Parallel phases use child workflows.
   - What's unclear: Should individual agent executions within a phase each be separate activities (fine-grained durability) or grouped into one phase-level activity (simpler)?
   - Recommendation: Start with one activity per phase. If a phase crashes mid-execution (e.g., 3 of 5 agents complete), the entire phase re-executes. This is simpler and avoids serialization complexity. Individual agent durability can be added in a later optimization pass.

3. **NATS Connection Lifecycle in Temporal Workers**
   - What we know: NATS connections should be shared within a Worker process.
   - What's unclear: Best pattern for injecting a shared NATS connection into Temporal activities.
   - Recommendation: Use Temporal's activity context / worker-level dependency injection. Initialize NATS connection when the Worker starts; pass via a custom activity class or module-level singleton.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9+ with pytest-asyncio |
| Config file | `tests/conftest.py` (will need Temporal test fixtures) |
| Quick run command | `uv run pytest tests/unit/pipeline/ -x --timeout=30` |
| Full suite command | `uv run pytest tests/ -x --timeout=120` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PIPE-01 | 10-stage pipeline executes end-to-end | integration | `uv run pytest tests/integration/test_pipeline_e2e.py -x` | No -- Wave 0 |
| PIPE-02 | S3/S5/S6 parallel execution and merge | unit | `uv run pytest tests/unit/pipeline/test_parallel_phases.py -x` | No -- Wave 0 |
| PIPE-03 | Human approval gates block/resume | unit | `uv run pytest tests/unit/pipeline/test_gates.py -x` | No -- Wave 0 |
| PIPE-04 | YAML preset loading and validation | unit | `uv run pytest tests/unit/pipeline/test_preset_loader.py -x` | No -- Wave 0 |
| PIPE-05 | Temporal retry/timeout/crash recovery | integration | `uv run pytest tests/integration/test_temporal_durability.py -x` | No -- Wave 0 |
| PIPE-06 | Resume from checkpoint after crash | integration | `uv run pytest tests/integration/test_pipeline_resume.py -x` | No -- Wave 0 |
| PIPE-07 | Project type detection and adaptation | unit | `uv run pytest tests/unit/pipeline/test_project_detector.py -x` | No -- Wave 0 |
| PIPE-08 | NATS JetStream event emission | unit | `uv run pytest tests/unit/pipeline/test_event_emission.py -x` | No -- Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/unit/pipeline/ -x --timeout=30`
- **Per wave merge:** `uv run pytest tests/ -x --timeout=120`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/unit/pipeline/test_preset_loader.py` -- covers PIPE-04
- [ ] `tests/unit/pipeline/test_gates.py` -- covers PIPE-03
- [ ] `tests/unit/pipeline/test_parallel_phases.py` -- covers PIPE-02
- [ ] `tests/unit/pipeline/test_project_detector.py` -- covers PIPE-07
- [ ] `tests/unit/pipeline/test_event_emission.py` -- covers PIPE-08
- [ ] `tests/integration/test_pipeline_e2e.py` -- covers PIPE-01, PIPE-05
- [ ] `tests/integration/test_temporal_durability.py` -- covers PIPE-05
- [ ] `tests/integration/test_pipeline_resume.py` -- covers PIPE-06
- [ ] `tests/conftest.py` -- shared Temporal test environment fixtures (WorkflowEnvironment)
- [ ] Temporal testing dependency: `uv add --dev temporalio[testing]`
- [ ] NATS test dependency: consider embedded nats-server or mock

### Testing Temporal Workflows

Temporal provides a `WorkflowEnvironment` for testing workflows without a real Temporal server:

```python
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

async def test_pipeline_completes():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-queue",
            workflows=[SDLCPipelineWorkflow],
            activities=[load_pipeline_config, execute_phase_activity, emit_pipeline_event],
        ):
            result = await env.client.execute_workflow(
                SDLCPipelineWorkflow.run,
                PipelineInput(project_id="test", preset_name="quick", project_type="greenfield"),
                id="test-pipeline",
                task_queue="test-queue",
            )
            assert result["status"] == "completed"
```

## Sources

### Primary (HIGH confidence)
- [Temporal Python SDK GitHub](https://github.com/temporalio/sdk-python) - SDK API, decorators, patterns
- [Temporal Python SDK Developer Guide](https://docs.temporal.io/develop/python) - Workflow/activity patterns, message passing, failure detection
- [Temporal Human-in-the-Loop AI Agent](https://docs.temporal.io/ai-cookbook/human-in-the-loop-python) - Signal + wait_condition pattern
- [Temporal Continue-As-New (Python)](https://docs.temporal.io/develop/python/continue-as-new) - Long-running workflow management
- [temporalio PyPI](https://pypi.org/project/temporalio/) - Version 1.23.0 verified
- [nats-py GitHub](https://github.com/nats-io/nats.py) - JetStream async Python client
- [nats-py PyPI](https://pypi.org/project/nats-py/) - Version 2.14.0 verified
- [NATS JetStream Docs](https://docs.nats.io/nats-concepts/jetstream) - Stream configuration, publish/subscribe
- [Pydantic v2 Models](https://docs.pydantic.dev/latest/concepts/models/) - model_validate pattern
- CodeBot design docs: `docs/design/SYSTEM_DESIGN.md` Section 6 (Pipeline Orchestration Design)
- CodeBot workflows: `docs/workflows/AGENT_WORKFLOWS.md` Sections 1-7 (Pipeline workflows, gates, recovery)

### Secondary (MEDIUM confidence)
- [Temporal + LangGraph Two-Layer Architecture](https://www.anup.io/temporal-langgraph-a-two-layer-architecture-for-multi-agent-coordination/) - Activity-StateGraph pattern validation
- [Grid Dynamics: Prototype to Production-Ready Agentic AI](https://temporal.io/blog/prototype-to-prod-ready-agentic-ai-grid-dynamics) - Migration from LangGraph+Redis to Temporal
- [Temporal Parallel Child Workflows](https://www.danielcorin.com/til/temporal/parallel-child-workflows/) - asyncio.gather pattern with child workflows
- [Temporal Blog: Managing Very Long-Running Workflows](https://temporal.io/blog/very-long-running-workflows) - Continue-as-new best practices
- [Temporal Official Docker Compose](https://github.com/temporalio/samples-server/tree/main/compose) - Local dev setup

### Tertiary (LOW confidence)
- [Temporal Durable Digest August 2025](https://temporal.io/blog/durable-digest-august-2025) - Temporal's position on LangGraph overlap (needs validation)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified against PyPI; versions confirmed; extensive official documentation
- Architecture: HIGH - Activity-StateGraph pattern validated by multiple production case studies; CodeBot design docs provide detailed specifications
- Pitfalls: HIGH - Derived from official Temporal documentation, community forums, and known production issues
- Validation: MEDIUM - Test patterns are standard pytest + Temporal testing utilities; integration test complexity depends on Phase 2-5 deliverables

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (30 days -- Temporal SDK is mature and stable; NATS client is stable)
