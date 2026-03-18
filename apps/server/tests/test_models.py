"""Tests for agent_sdk Pydantic models and cross-language enum parity.

Covers:
- Model instantiation with valid data
- Validation of required fields
- Enum values serialize to strings
- model_dump_json() / model_validate_json() round-trips
- Cross-language parity: Python enum members match TypeScript enum members
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from agent_sdk.models import (
    AgentEvent,
    AgentExecutionSchema,
    AgentSchema,
    AgentStatus,
    AgentType,
    CommentStatus,
    CommentType,
    EventEnvelope,
    EventType,
    ExecutionStatus,
    ExperimentStatus,
    FindingStatus,
    FindingType,
    PhaseStatus,
    PhaseType,
    PipelineCreateRequest,
    PipelineEvent,
    PipelinePhaseSchema,
    PipelineSchema,
    PipelineStatus,
    PipelineStatusResponse,
    ProjectSchema,
    ProjectStatus,
    ProjectType,
    Severity,
    TaskEvent,
    TaskSchema,
    TaskStatus,
    TestStatus,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime.now(tz=timezone.utc)
SAMPLE_UUID = uuid.uuid4()
SAMPLE_UUID2 = uuid.uuid4()


# ---------------------------------------------------------------------------
# Task 1: Model instantiation with valid data
# ---------------------------------------------------------------------------


class TestProjectSchema:
    def test_instantiation(self) -> None:
        proj = ProjectSchema(
            id=SAMPLE_UUID,
            name="My App",
            description="Test project",
            status=ProjectStatus.CREATED,
            project_type=ProjectType.GREENFIELD,
            tech_stack={"backend": "python"},
            created_at=NOW,
            updated_at=NOW,
        )
        assert proj.name == "My App"
        assert proj.status is ProjectStatus.CREATED

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            ProjectSchema(  # type: ignore[call-arg]
                id=SAMPLE_UUID,
                # name is required but omitted
                description="Test",
                status=ProjectStatus.CREATED,
                project_type=ProjectType.GREENFIELD,
                tech_stack={},
                created_at=NOW,
                updated_at=NOW,
            )

    def test_enum_serializes_to_string(self) -> None:
        proj = ProjectSchema(
            id=SAMPLE_UUID,
            name="Test",
            description="",
            status=ProjectStatus.COMPLETED,
            project_type=ProjectType.IMPROVE,
            tech_stack={},
            created_at=NOW,
            updated_at=NOW,
        )
        dumped = json.loads(proj.model_dump_json())
        assert dumped["status"] == "COMPLETED"
        assert dumped["project_type"] == "IMPROVE"

    def test_round_trip_json(self) -> None:
        proj = ProjectSchema(
            id=SAMPLE_UUID,
            name="Round Trip",
            description="",
            status=ProjectStatus.PLANNING,
            project_type=ProjectType.BROWNFIELD,
            tech_stack={"key": "value"},
            created_at=NOW,
            updated_at=NOW,
        )
        restored = ProjectSchema.model_validate_json(proj.model_dump_json())
        assert restored.id == proj.id
        assert restored.status is proj.status
        assert restored.tech_stack == proj.tech_stack


class TestPipelineSchema:
    def test_instantiation(self) -> None:
        pipeline = PipelineSchema(
            id=SAMPLE_UUID,
            project_id=SAMPLE_UUID2,
            status=PipelineStatus.RUNNING,
            current_phase="S3_ARCHITECTURE",
            total_tokens_used=1000,
            total_cost_usd=0.05,
            started_at=NOW,
        )
        assert pipeline.completed_at is None

    def test_enum_serializes_to_string(self) -> None:
        pipeline = PipelineSchema(
            id=SAMPLE_UUID,
            project_id=SAMPLE_UUID2,
            status=PipelineStatus.COMPLETED,
            current_phase="S10_DEPLOY",
            total_tokens_used=500,
            total_cost_usd=0.02,
            started_at=NOW,
            completed_at=NOW,
        )
        dumped = json.loads(pipeline.model_dump_json())
        assert dumped["status"] == "COMPLETED"


class TestPipelinePhaseSchema:
    def test_instantiation(self) -> None:
        phase = PipelinePhaseSchema(
            id=SAMPLE_UUID,
            pipeline_id=SAMPLE_UUID2,
            name="Architecture",
            phase_type=PhaseType.ARCHITECTURE,
            status=PhaseStatus.RUNNING,
            order=3,
            requires_approval=True,
        )
        assert phase.started_at is None
        assert phase.requires_approval is True


class TestAgentSchema:
    def test_instantiation(self) -> None:
        agent = AgentSchema(
            id=SAMPLE_UUID,
            project_id=SAMPLE_UUID2,
            agent_type=AgentType.BACKEND_DEV,
            status=AgentStatus.RUNNING,
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet",
            system_prompt_hash="abc123",
            tokens_used=200,
            cost_usd=0.01,
            started_at=NOW,
            error_count=0,
        )
        assert agent.worktree_path is None
        assert agent.agent_type is AgentType.BACKEND_DEV

    def test_enum_serializes_to_string(self) -> None:
        agent = AgentSchema(
            id=SAMPLE_UUID,
            project_id=SAMPLE_UUID2,
            agent_type=AgentType.TESTER,
            status=AgentStatus.COMPLETED,
            llm_provider="openai",
            llm_model="gpt-4o",
            system_prompt_hash="def456",
            tokens_used=100,
            cost_usd=0.001,
            started_at=NOW,
            error_count=0,
        )
        dumped = json.loads(agent.model_dump_json())
        assert dumped["agent_type"] == "TESTER"
        assert dumped["status"] == "COMPLETED"


class TestAgentExecutionSchema:
    def test_instantiation(self) -> None:
        execution = AgentExecutionSchema(
            id=SAMPLE_UUID,
            agent_id=SAMPLE_UUID2,
            task_id=uuid.uuid4(),
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet",
            input_tokens=500,
            output_tokens=200,
            total_tokens=700,
            cost_usd=0.02,
            duration_ms=1500,
            status=ExecutionStatus.SUCCESS,
            input_messages=[{"role": "user", "content": "hello"}],
            output_messages=[{"role": "assistant", "content": "world"}],
            tool_calls=[],
            created_at=NOW,
        )
        assert execution.error_message is None
        assert execution.total_tokens == 700


class TestTaskSchema:
    def test_instantiation(self) -> None:
        task = TaskSchema(
            id=SAMPLE_UUID,
            project_id=SAMPLE_UUID2,
            phase_id=uuid.uuid4(),
            title="Implement auth endpoint",
            description="Build the login endpoint",
            status=TaskStatus.PENDING,
            priority=1,
            assigned_agent_type="BACKEND_DEV",
            dependencies=[],
            input_context={"prd": "..."},
            created_at=NOW,
        )
        assert task.parent_task_id is None
        assert task.output_artifacts is None

    def test_enum_serializes_to_string(self) -> None:
        task = TaskSchema(
            id=SAMPLE_UUID,
            project_id=SAMPLE_UUID2,
            phase_id=uuid.uuid4(),
            title="Test",
            description="",
            status=TaskStatus.IN_PROGRESS,
            priority=2,
            assigned_agent_type="TESTER",
            dependencies=[],
            input_context={},
            created_at=NOW,
        )
        dumped = json.loads(task.model_dump_json())
        assert dumped["status"] == "IN_PROGRESS"


class TestEventModels:
    def test_agent_event_instantiation(self) -> None:
        event = AgentEvent(
            agent_id=SAMPLE_UUID,
            agent_type=AgentType.ORCHESTRATOR,
            status=AgentStatus.RUNNING,
        )
        assert event.payload is None
        assert isinstance(event.timestamp, datetime)

    def test_task_event_instantiation(self) -> None:
        event = TaskEvent(
            task_id=SAMPLE_UUID,
            agent_id=SAMPLE_UUID2,
            status=TaskStatus.COMPLETED,
        )
        assert isinstance(event.timestamp, datetime)

    def test_pipeline_event_instantiation(self) -> None:
        event = PipelineEvent(
            pipeline_id=SAMPLE_UUID,
            phase="S3_ARCHITECTURE",
            status="RUNNING",
        )
        assert isinstance(event.timestamp, datetime)

    def test_event_envelope_instantiation(self) -> None:
        inner = AgentEvent(
            agent_id=SAMPLE_UUID,
            agent_type=AgentType.PLANNER,
            status=AgentStatus.COMPLETED,
        )
        payload_bytes = inner.model_dump_json().encode()
        envelope = EventEnvelope(
            event_type=EventType.AGENT_COMPLETED,
            source_agent_id=SAMPLE_UUID,
            payload=payload_bytes,
        )
        assert envelope.event_type is EventType.AGENT_COMPLETED

    def test_event_envelope_round_trip(self) -> None:
        inner = AgentEvent(
            agent_id=SAMPLE_UUID,
            agent_type=AgentType.DEBUGGER,
            status=AgentStatus.FAILED,
            payload={"reason": "out_of_context"},
        )
        payload_bytes = inner.model_dump_json().encode()
        envelope = EventEnvelope(
            event_type=EventType.AGENT_FAILED,
            source_agent_id=SAMPLE_UUID,
            payload=payload_bytes,
        )
        restored_inner = AgentEvent.model_validate_json(envelope.payload)
        assert restored_inner.agent_id == inner.agent_id
        assert restored_inner.status is AgentStatus.FAILED
        assert restored_inner.payload == {"reason": "out_of_context"}


class TestPipelineContractModels:
    def test_create_request(self) -> None:
        req = PipelineCreateRequest(project_id=SAMPLE_UUID)
        assert req.config is None

    def test_status_response(self) -> None:
        resp = PipelineStatusResponse(
            id=SAMPLE_UUID,
            project_id=SAMPLE_UUID2,
            status=PipelineStatus.RUNNING,
            current_phase="S5_IMPL",
            total_tokens_used=5000,
            total_cost_usd=0.50,
        )
        dumped = json.loads(resp.model_dump_json())
        assert dumped["status"] == "RUNNING"


# ---------------------------------------------------------------------------
# Cross-language enum parity test
# ---------------------------------------------------------------------------

# Mapping from Python enum class name to the TypeScript enum name
# (they share identical names in our convention)
_TS_ENUMS_FILE = Path(__file__).parents[3] / "libs" / "shared-types" / "src" / "enums.ts"
_TS_FILE_MISSING = not _TS_ENUMS_FILE.exists()

_PYTHON_ENUMS: dict[str, type] = {
    "ProjectStatus": ProjectStatus,
    "ProjectType": ProjectType,
    "PipelineStatus": PipelineStatus,
    "PhaseType": PhaseType,
    "PhaseStatus": PhaseStatus,
    "TaskStatus": TaskStatus,
    "AgentType": AgentType,
    "AgentStatus": AgentStatus,
    "ExecutionStatus": ExecutionStatus,
    "TestStatus": TestStatus,
    "ExperimentStatus": ExperimentStatus,
    "FindingType": FindingType,
    "Severity": Severity,
    "FindingStatus": FindingStatus,
    "CommentType": CommentType,
    "CommentStatus": CommentStatus,
    "EventType": EventType,
}


def _parse_ts_enums(ts_source: str) -> dict[str, set[str]]:
    """Parse TypeScript ``enum Name { ... }`` blocks and extract member names."""
    result: dict[str, set[str]] = {}
    # Match: enum Name { MEMBER = "value", ... }
    enum_blocks = re.findall(
        r"export\s+enum\s+(\w+)\s*\{([^}]*)\}",
        ts_source,
        re.DOTALL,
    )
    for enum_name, body in enum_blocks:
        members: set[str] = set()
        for line in body.splitlines():
            line = line.strip().rstrip(",")
            if not line or line.startswith("//") or line.startswith("*"):
                continue
            # "MEMBER_NAME = ..." or just "MEMBER_NAME"
            name_part = line.split("=")[0].strip()
            if name_part:
                members.add(name_part)
        result[enum_name] = members
    return result


@pytest.mark.skipif(
    _TS_FILE_MISSING,
    reason="TypeScript enums.ts not found — skipping cross-language parity check",
)
def test_enum_parity_with_typescript() -> None:
    """Verify that Python enum members exactly match TypeScript enum members."""
    ts_source = _TS_ENUMS_FILE.read_text(encoding="utf-8")
    ts_enums = _parse_ts_enums(ts_source)

    mismatches: list[str] = []

    for name, py_enum in _PYTHON_ENUMS.items():
        if name not in ts_enums:
            mismatches.append(f"{name}: not found in TypeScript enums.ts")
            continue

        py_members = set(py_enum.__members__.keys())
        ts_members = ts_enums[name]

        only_in_python = py_members - ts_members
        only_in_ts = ts_members - py_members

        if only_in_python or only_in_ts:
            msgs = []
            if only_in_python:
                msgs.append(f"only in Python: {sorted(only_in_python)}")
            if only_in_ts:
                msgs.append(f"only in TypeScript: {sorted(only_in_ts)}")
            mismatches.append(f"{name}: {'; '.join(msgs)}")

    assert not mismatches, (
        "Cross-language enum parity check failed:\n"
        + "\n".join(f"  - {m}" for m in mismatches)
    )
