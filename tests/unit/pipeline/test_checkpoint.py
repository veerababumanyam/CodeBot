"""Tests for pipeline data transfer objects and checkpoint model.

Validates that PipelineInput, PhaseInput, PhaseResult, and PipelineCheckpoint
are JSON-serializable dataclasses suitable for Temporal activity boundaries.
"""

from __future__ import annotations

import dataclasses
import json

from codebot.pipeline.checkpoint import (
    PhaseInput,
    PhaseResult,
    PipelineCheckpoint,
    PipelineInput,
)


class TestPipelineInput:
    """Tests for PipelineInput dataclass."""

    def test_fields(self) -> None:
        inp = PipelineInput(
            project_id="proj-1",
            preset_name="full",
            project_type="greenfield",
        )
        assert inp.project_id == "proj-1"
        assert inp.preset_name == "full"
        assert inp.project_type == "greenfield"
        assert inp.resume_from_phase is None

    def test_resume_from_phase(self) -> None:
        inp = PipelineInput(
            project_id="proj-1",
            preset_name="quick",
            project_type="inflight",
            resume_from_phase=3,
        )
        assert inp.resume_from_phase == 3

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(PipelineInput)

    def test_json_serializable(self) -> None:
        inp = PipelineInput(
            project_id="proj-1",
            preset_name="full",
            project_type="greenfield",
        )
        data = dataclasses.asdict(inp)
        serialized = json.dumps(data)
        deserialized = json.loads(serialized)
        assert deserialized["project_id"] == "proj-1"


class TestPhaseInput:
    """Tests for PhaseInput dataclass."""

    def test_fields(self) -> None:
        inp = PhaseInput(
            project_id="proj-1",
            phase_name="design",
            phase_idx=3,
            agents=["architect", "designer"],
            parallel=True,
            config={"on_failure": "escalate"},
        )
        assert inp.project_id == "proj-1"
        assert inp.phase_name == "design"
        assert inp.phase_idx == 3
        assert inp.agents == ["architect", "designer"]
        assert inp.parallel is True
        assert inp.config == {"on_failure": "escalate"}

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(PhaseInput)

    def test_json_serializable(self) -> None:
        inp = PhaseInput(
            project_id="proj-1",
            phase_name="implement",
            phase_idx=5,
            agents=["backend_dev"],
            parallel=False,
            config={},
        )
        data = dataclasses.asdict(inp)
        serialized = json.dumps(data)
        deserialized = json.loads(serialized)
        assert deserialized["phase_name"] == "implement"
        assert deserialized["agents"] == ["backend_dev"]


class TestPhaseResult:
    """Tests for PhaseResult dataclass."""

    def test_fields(self) -> None:
        result = PhaseResult(
            phase_name="design",
            phase_idx=3,
            status="completed",
        )
        assert result.phase_name == "design"
        assert result.phase_idx == 3
        assert result.status == "completed"
        assert result.agent_results == []
        assert result.duration_ms == 0
        assert result.tokens_used == 0
        assert result.cost_usd == 0.0

    def test_with_agent_results(self) -> None:
        result = PhaseResult(
            phase_name="implement",
            phase_idx=5,
            status="completed",
            agent_results=[{"agent": "backend_dev", "status": "completed"}],
            duration_ms=1500,
            tokens_used=5000,
            cost_usd=0.05,
        )
        assert len(result.agent_results) == 1
        assert result.duration_ms == 1500
        assert result.cost_usd == 0.05

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(PhaseResult)

    def test_json_serializable(self) -> None:
        result = PhaseResult(
            phase_name="test",
            phase_idx=7,
            status="failed",
            agent_results=[{"agent": "tester", "status": "failed"}],
            duration_ms=2000,
            tokens_used=3000,
            cost_usd=0.03,
        )
        data = dataclasses.asdict(result)
        serialized = json.dumps(data)
        deserialized = json.loads(serialized)
        assert deserialized["status"] == "failed"
        assert deserialized["duration_ms"] == 2000


class TestPipelineCheckpoint:
    """Tests for PipelineCheckpoint dataclass."""

    def test_fields(self) -> None:
        cp = PipelineCheckpoint(
            project_id="proj-1",
            preset_name="full",
            project_type="greenfield",
            completed_phase_idx=4,
        )
        assert cp.project_id == "proj-1"
        assert cp.preset_name == "full"
        assert cp.project_type == "greenfield"
        assert cp.completed_phase_idx == 4
        assert cp.phase_results == []

    def test_with_phase_results(self) -> None:
        cp = PipelineCheckpoint(
            project_id="proj-2",
            preset_name="quick",
            project_type="inflight",
            completed_phase_idx=2,
            phase_results=[
                {"phase_name": "init", "status": "completed"},
                {"phase_name": "brainstorm", "status": "completed"},
                {"phase_name": "research", "status": "completed"},
            ],
        )
        assert len(cp.phase_results) == 3

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(PipelineCheckpoint)

    def test_json_serializable(self) -> None:
        cp = PipelineCheckpoint(
            project_id="proj-1",
            preset_name="full",
            project_type="greenfield",
            completed_phase_idx=4,
            phase_results=[{"phase_name": "init", "status": "completed"}],
        )
        data = dataclasses.asdict(cp)
        serialized = json.dumps(data)
        deserialized = json.loads(serialized)
        assert deserialized["completed_phase_idx"] == 4
