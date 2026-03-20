"""End-to-end integration tests for the 5-agent vertical slice pipeline.

These tests mock all LLM calls but exercise the full pipeline wiring:
agent creation, SharedState data flow, quality gate enforcement,
test-failure-to-debugger routing, and NATS event emission.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from agent_sdk.agents.base import AgentOutput
from codebot.agents.backend_dev import BackendDevAgent
from codebot.agents.code_reviewer import CodeReviewerAgent
from codebot.agents.debugger import DebuggerAgent
from codebot.agents.orchestrator import OrchestratorAgent
from codebot.agents.tester import TesterAgent
from codebot.pipeline.vertical_slice import build_vertical_slice_graph

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def pipeline_id() -> uuid.UUID:
    """Deterministic pipeline ID for tests."""
    return uuid.uuid4()


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    """Mock EventBus that records published events instead of connecting to NATS.

    The mock tracks all calls to ``publish()`` in a ``published_events``
    list, allowing tests to assert on the types and payloads of emitted
    events without requiring a running NATS server.
    """
    bus = AsyncMock()
    bus.published_events: list[dict] = []  # type: ignore[annotation-unchecked]

    async def recording_publish(event_type: str, payload: bytes) -> None:
        bus.published_events.append({"event_type": event_type, "payload": payload})

    bus.publish = AsyncMock(side_effect=recording_publish)
    bus.is_connected = True
    return bus


# ---------------------------------------------------------------------------
# Pre-canned agent outputs
# ---------------------------------------------------------------------------

_REQUIREMENTS_DICT = {
    "project_name": "Todo API",
    "project_description": "A simple todo list API",
    "functional_requirements": [
        {
            "id": "FR-01",
            "title": "Create todo",
            "description": "User can create a todo item",
            "priority": "Must",
            "acceptance_criteria": [
                {
                    "description": "POST /todos returns 201",
                    "test_strategy": "integration_test",
                }
            ],
            "confidence": 0.95,
        },
        {
            "id": "FR-02",
            "title": "List todos",
            "description": "User can list all todo items",
            "priority": "Must",
            "acceptance_criteria": [
                {
                    "description": "GET /todos returns 200",
                    "test_strategy": "integration_test",
                }
            ],
            "confidence": 0.90,
        },
    ],
    "non_functional_requirements": ["Response time < 200ms"],
    "constraints": ["Python 3.12+", "FastAPI"],
    "ambiguities": [],
}

_GENERATED_FILES = {
    "src/main.py": (
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n\n"
        '@app.get("/todos")\n'
        "async def list_todos():\n"
        "    return []\n"
    ),
    "src/models.py": (
        "from pydantic import BaseModel\n\n"
        "class Todo(BaseModel):\n"
        "    title: str\n"
        "    done: bool = False\n"
    ),
}


def _orchestrator_output(agent_input: object) -> AgentOutput:
    """Pre-canned OrchestratorAgent output with requirements."""
    return AgentOutput(
        task_id=uuid.uuid4(),
        state_updates={"requirements": _REQUIREMENTS_DICT},
        review_passed=True,
    )


def _backend_dev_output(agent_input: object) -> AgentOutput:
    """Pre-canned BackendDevAgent output with generated files."""
    return AgentOutput(
        task_id=uuid.uuid4(),
        state_updates={
            "backend_dev.generated_files": _GENERATED_FILES,
            "backend_dev.entry_point": "src/main.py",
            "backend_dev.dependencies": ["fastapi", "uvicorn"],
            "backend_dev.lint_passed": True,
            "backend_dev.typecheck_passed": True,
        },
        review_passed=True,
    )


def _code_reviewer_output_pass(agent_input: object) -> AgentOutput:
    """Pre-canned CodeReviewerAgent output with gate_passed=True."""
    return AgentOutput(
        task_id=uuid.uuid4(),
        state_updates={
            "code_review.gate_passed": True,
            "code_review.report": {
                "comments": [],
                "overall_quality": "good",
                "gate_passed": True,
                "summary": "Code passes quality review.",
            },
            "code_review.comments": [],
        },
        review_passed=True,
    )


def _code_reviewer_output_fail(agent_input: object) -> AgentOutput:
    """Pre-canned CodeReviewerAgent output with gate_passed=False."""
    return AgentOutput(
        task_id=uuid.uuid4(),
        state_updates={
            "code_review.gate_passed": False,
            "code_review.report": {
                "comments": [
                    {
                        "file_path": "src/main.py",
                        "line_start": 5,
                        "line_end": 6,
                        "severity": "high",
                        "category": "bug",
                        "message": "Missing error handling",
                    }
                ],
                "overall_quality": "needs_work",
                "gate_passed": False,
                "summary": "Critical issues found.",
            },
            "code_review.comments": [
                {
                    "file_path": "src/main.py",
                    "line_start": 5,
                    "line_end": 6,
                    "severity": "high",
                    "category": "bug",
                    "message": "Missing error handling",
                }
            ],
        },
        review_passed=False,
    )


def _tester_output_pass(agent_input: object) -> AgentOutput:
    """Pre-canned TesterAgent output with all tests passing."""
    return AgentOutput(
        task_id=uuid.uuid4(),
        state_updates={
            "test_results": {
                "total": 5,
                "passed": 5,
                "failed": 0,
                "errors": 0,
                "skipped": 0,
                "coverage_percent": 85.0,
                "all_passed": True,
                "failure_details": [],
                "duration_seconds": 1.5,
            },
            "tests_passing": True,
        },
        review_passed=True,
    )


def _tester_output_fail(agent_input: object) -> AgentOutput:
    """Pre-canned TesterAgent output with test failures."""
    return AgentOutput(
        task_id=uuid.uuid4(),
        state_updates={
            "test_results": {
                "total": 5,
                "passed": 3,
                "failed": 2,
                "errors": 0,
                "skipped": 0,
                "coverage_percent": 60.0,
                "all_passed": False,
                "failure_details": [
                    {
                        "nodeid": "test_main.py::test_create_todo",
                        "outcome": "failed",
                        "longrepr": "AssertionError",
                        "duration": 0.1,
                    },
                    {
                        "nodeid": "test_main.py::test_validation",
                        "outcome": "failed",
                        "longrepr": "ValidationError",
                        "duration": 0.05,
                    },
                ],
                "duration_seconds": 2.0,
            },
            "tests_passing": False,
            "test_failures": [
                {
                    "nodeid": "test_main.py::test_create_todo",
                    "outcome": "failed",
                    "longrepr": "AssertionError",
                    "duration": 0.1,
                },
                {
                    "nodeid": "test_main.py::test_validation",
                    "outcome": "failed",
                    "longrepr": "ValidationError",
                    "duration": 0.05,
                },
            ],
        },
        review_passed=False,
    )


def _debugger_output(agent_input: object) -> AgentOutput:
    """Pre-canned DebuggerAgent output with tests fixed."""
    return AgentOutput(
        task_id=uuid.uuid4(),
        state_updates={
            "tests_passing": True,
            "final_pass_rate": 1.0,
            "experiment_log": [
                {
                    "experiment_id": 1,
                    "hypothesis": "Fix missing route handler",
                    "status": "KEEP",
                    "delta": 0.4,
                    "metric_before": 0.6,
                    "metric_after": 1.0,
                    "duration_seconds": 3.5,
                }
            ],
        },
        review_passed=True,
    )


def _patch_all_agents_happy_path():
    """Return a list of patch context managers for the happy path.

    All agents return pre-canned passing outputs:
    QA gate passes, tests pass, debugger not needed.
    """
    return [
        patch.object(
            OrchestratorAgent,
            "execute",
            new_callable=AsyncMock,
            side_effect=_orchestrator_output,
        ),
        patch.object(
            BackendDevAgent,
            "execute",
            new_callable=AsyncMock,
            side_effect=_backend_dev_output,
        ),
        patch.object(
            CodeReviewerAgent,
            "execute",
            new_callable=AsyncMock,
            side_effect=_code_reviewer_output_pass,
        ),
        patch.object(
            TesterAgent,
            "execute",
            new_callable=AsyncMock,
            side_effect=_tester_output_pass,
        ),
        patch.object(
            DebuggerAgent,
            "execute",
            new_callable=AsyncMock,
            side_effect=_debugger_output,
        ),
    ]


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


class TestFullPipelineExecution:
    """Test the happy path: all agents execute, tests pass, no debug needed."""

    async def test_pipeline_runs_all_five_agents(
        self, mock_event_bus: AsyncMock, pipeline_id: uuid.UUID
    ) -> None:
        """All 5 agents execute when quality gate passes and tests pass.

        Verifies that shared_state contains keys from all agents except
        debugger (since tests pass).
        """
        patches = _patch_all_agents_happy_path()
        with (
            patches[0] as m_orch,
            patches[1] as m_bdev,
            patches[2] as m_rev,
            patches[3] as m_test,
            patches[4] as m_dbg,
        ):  # noqa: E501
            pipeline = await build_vertical_slice_graph(
                event_bus=mock_event_bus, pipeline_id=pipeline_id
            )
            result = await pipeline.run("Build a todo list API with CRUD operations")

            # Assert: all expected keys present in shared_state
            assert "requirements" in result  # noqa: S101
            assert "backend_dev.generated_files" in result  # noqa: S101
            assert "code_review.gate_passed" in result  # noqa: S101
            assert result["code_review.gate_passed"] is True  # noqa: S101
            assert "test_results" in result  # noqa: S101
            assert "tests_passing" in result  # noqa: S101
            assert result["tests_passing"] is True  # noqa: S101

            # Assert: all agents were called
            m_orch.assert_awaited_once()
            m_bdev.assert_awaited_once()
            m_rev.assert_awaited_once()
            m_test.assert_awaited_once()

            # Assert: debugger was NOT called (tests passed)
            m_dbg.assert_not_awaited()

    async def test_pipeline_emits_events(
        self, mock_event_bus: AsyncMock, pipeline_id: uuid.UUID
    ) -> None:
        """NATS events are emitted for every agent start/complete and phase transition."""
        patches = _patch_all_agents_happy_path()
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            pipeline = await build_vertical_slice_graph(
                event_bus=mock_event_bus, pipeline_id=pipeline_id
            )
            await pipeline.run("Build a todo API")

        # Collect all published event types
        published = mock_event_bus.published_events
        event_types = [e["event_type"] for e in published]

        # Should include PIPELINE_STARTED and PIPELINE_COMPLETED
        assert any("pipeline.started" in et for et in event_types)  # noqa: S101
        assert any("pipeline.completed" in et for et in event_types)  # noqa: S101

        # Should include events for each of the 4 agents executed
        # (orchestrator, backend_dev, code_reviewer, tester -- debugger skipped)
        assert any("agent.started" in et for et in event_types)  # noqa: S101
        assert any("agent.completed" in et for et in event_types)  # noqa: S101

        # Should include phase events
        assert any("phase.started" in et for et in event_types)  # noqa: S101
        assert any("phase.completed" in et for et in event_types)  # noqa: S101

        # Expect at minimum: pipeline_start(1) + 4*(phase_start + agent_start +
        # agent_complete + phase_complete) + pipeline_complete(1) = 18 events
        assert len(published) >= 18  # noqa: S101


class TestFailureRoutesToDebugger:
    """Test that failed tests route to the Debugger agent (TEST-05)."""

    async def test_failure_routes_to_debugger(
        self, mock_event_bus: AsyncMock, pipeline_id: uuid.UUID
    ) -> None:
        """When Tester reports failures, pipeline executes Debugger."""
        with (
            patch.object(
                OrchestratorAgent,
                "execute",
                new_callable=AsyncMock,
                side_effect=_orchestrator_output,
            ),
            patch.object(
                BackendDevAgent,
                "execute",
                new_callable=AsyncMock,
                side_effect=_backend_dev_output,
            ),
            patch.object(
                CodeReviewerAgent,
                "execute",
                new_callable=AsyncMock,
                side_effect=_code_reviewer_output_pass,
            ),
            patch.object(
                TesterAgent,
                "execute",
                new_callable=AsyncMock,
                side_effect=_tester_output_fail,
            ),
            patch.object(
                DebuggerAgent,
                "execute",
                new_callable=AsyncMock,
                side_effect=_debugger_output,
            ) as m_dbg,
        ):
            pipeline = await build_vertical_slice_graph(
                event_bus=mock_event_bus, pipeline_id=pipeline_id
            )
            result = await pipeline.run("Build a todo API with CRUD")

            # Assert: Debugger was called
            m_dbg.assert_awaited_once()

        # Assert: final tests_passing comes from debugger output
        assert result["tests_passing"] is True  # noqa: S101
        assert result.get("final_pass_rate") == 1.0  # noqa: S101

        # Assert: experiment log present from debugger
        assert "experiment_log" in result  # noqa: S101
        assert len(result["experiment_log"]) >= 1  # noqa: S101

    async def test_debug_phase_skipped_when_tests_pass(
        self, mock_event_bus: AsyncMock, pipeline_id: uuid.UUID
    ) -> None:
        """When all tests pass, debug phase is skipped."""
        patches = _patch_all_agents_happy_path()
        with patches[0], patches[1], patches[2], patches[3], patches[4] as m_dbg:
            pipeline = await build_vertical_slice_graph(
                event_bus=mock_event_bus, pipeline_id=pipeline_id
            )
            await pipeline.run("Build a todo API")

            # Assert: Debugger was NOT called
            m_dbg.assert_not_awaited()

        # Assert: no DEBUGGER agent event in published events
        published = mock_event_bus.published_events
        for event in published:
            payload_bytes = event.get("payload", b"")
            if isinstance(payload_bytes, bytes):
                try:
                    payload = json.loads(payload_bytes)
                    inner_str = payload.get("payload", "{}")
                    inner = json.loads(inner_str)
                    if inner.get("agent_type") == "DEBUGGER":
                        pytest.fail("Found DEBUGGER event when debug phase should be skipped")
                except (json.JSONDecodeError, TypeError):
                    pass


class TestQualityGateEnforcement:
    """Test the QA gate blocks and reroutes on failure."""

    async def test_qa_gate_reroutes_to_implementation(
        self, mock_event_bus: AsyncMock, pipeline_id: uuid.UUID
    ) -> None:
        """When CodeReviewer gate_passed=False, pipeline reroutes to BackendDev."""
        review_call_count = 0

        def _review_side_effect(agent_input: object) -> AgentOutput:
            nonlocal review_call_count
            review_call_count += 1
            if review_call_count == 1:
                return _code_reviewer_output_fail(agent_input)
            return _code_reviewer_output_pass(agent_input)

        with (
            patch.object(
                OrchestratorAgent,
                "execute",
                new_callable=AsyncMock,
                side_effect=_orchestrator_output,
            ),
            patch.object(
                BackendDevAgent,
                "execute",
                new_callable=AsyncMock,
                side_effect=_backend_dev_output,
            ) as m_bdev,
            patch.object(
                CodeReviewerAgent,
                "execute",
                new_callable=AsyncMock,
                side_effect=_review_side_effect,
            ) as m_rev,
            patch.object(
                TesterAgent,
                "execute",
                new_callable=AsyncMock,
                side_effect=_tester_output_pass,
            ),
            patch.object(
                DebuggerAgent,
                "execute",
                new_callable=AsyncMock,
                side_effect=_debugger_output,
            ),
        ):
            pipeline = await build_vertical_slice_graph(
                event_bus=mock_event_bus, pipeline_id=pipeline_id
            )
            result = await pipeline.run("Build a todo API")

            # Assert: BackendDev was called at least 2 times
            assert m_bdev.await_count >= 2  # noqa: S101

            # Assert: CodeReviewer was called at least 2 times
            assert m_rev.await_count >= 2  # noqa: S101

        # Assert: final gate_passed is True
        assert result["code_review.gate_passed"] is True  # noqa: S101

        # Assert: review_comments were injected for the reroute
        assert "review_comments" in result  # noqa: S101


class TestEventEmission:
    """Verify NATS JetStream event emission (EVNT-01)."""

    async def test_event_emission(self, mock_event_bus: AsyncMock, pipeline_id: uuid.UUID) -> None:
        """Every agent transition emits a structured event."""
        patches = _patch_all_agents_happy_path()
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            pipeline = await build_vertical_slice_graph(
                event_bus=mock_event_bus, pipeline_id=pipeline_id
            )
            await pipeline.run("Build a todo API")

        published = mock_event_bus.published_events
        assert len(published) >= 10, (  # noqa: S101
            f"Expected at least 10 events, got {len(published)}"
        )

        # Each event payload should be valid JSON bytes
        for event in published:
            payload_bytes = event.get("payload", b"")
            assert isinstance(payload_bytes, bytes)  # noqa: S101
            parsed = json.loads(payload_bytes)
            assert "event_type" in parsed  # noqa: S101
            assert "timestamp" in parsed  # noqa: S101

        # Extract unique event_type slugs from published subjects
        event_type_slugs = {e["event_type"] for e in published}
        # Should have multiple distinct event types
        assert len(event_type_slugs) >= 4, (  # noqa: S101
            f"Expected at least 4 distinct event types, got {event_type_slugs}"
        )

    async def test_pipeline_runs_without_emitter(self) -> None:
        """Pipeline can run without event emitter (emitter=None)."""
        patches = _patch_all_agents_happy_path()
        with patches[0], patches[1], patches[2], patches[3], patches[4]:
            pipeline = await build_vertical_slice_graph(event_bus=None, pipeline_id=None)
            assert pipeline.emitter is None  # noqa: S101

            result = await pipeline.run("Build something simple")
            assert "requirements" in result  # noqa: S101
            assert result["tests_passing"] is True  # noqa: S101
