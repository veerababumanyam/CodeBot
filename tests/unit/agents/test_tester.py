"""Unit tests for TesterAgent, TestRunner, and TestResultParser.

Tests cover:
- ParsedTestResult model fields
- TestResultParser.parse() extracting pass/fail counts and coverage
- TestRunner.run() executing pytest subprocess
- TesterAgent PRA cycle (perceive, reason, act, review)
- Failure routing to Debugger via shared state
"""

from __future__ import annotations

import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_sdk.agents.base import AgentInput, AgentOutput, PRAResult
from agent_sdk.models.enums import AgentType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_test_report_all_pass() -> dict[str, Any]:
    """Pytest-json-report output where all tests pass."""
    return {
        "created": 1710000000.0,
        "duration": 2.5,
        "exitcode": 0,
        "summary": {
            "total": 5,
            "passed": 5,
            "failed": 0,
            "error": 0,
            "skipped": 0,
        },
        "tests": [
            {
                "nodeid": "tests/test_main.py::test_health",
                "outcome": "passed",
                "duration": 0.1,
            },
            {
                "nodeid": "tests/test_main.py::test_create",
                "outcome": "passed",
                "duration": 0.2,
            },
            {
                "nodeid": "tests/test_main.py::test_list",
                "outcome": "passed",
                "duration": 0.15,
            },
            {
                "nodeid": "tests/test_main.py::test_get",
                "outcome": "passed",
                "duration": 0.12,
            },
            {
                "nodeid": "tests/test_main.py::test_delete",
                "outcome": "passed",
                "duration": 0.11,
            },
        ],
    }


@pytest.fixture
def sample_test_report_with_failures() -> dict[str, Any]:
    """Pytest-json-report output with some test failures."""
    return {
        "created": 1710000000.0,
        "duration": 1.5,
        "exitcode": 1,
        "summary": {
            "total": 5,
            "passed": 3,
            "failed": 2,
            "error": 0,
            "skipped": 0,
        },
        "tests": [
            {
                "nodeid": "tests/test_main.py::test_health",
                "outcome": "passed",
                "duration": 0.1,
            },
            {
                "nodeid": "tests/test_main.py::test_create",
                "outcome": "passed",
                "duration": 0.2,
            },
            {
                "nodeid": "tests/test_main.py::test_list",
                "outcome": "passed",
                "duration": 0.15,
            },
            {
                "nodeid": "tests/test_main.py::test_get",
                "outcome": "failed",
                "duration": 0.12,
                "longrepr": "AssertionError: Expected 200 but got 404",
            },
            {
                "nodeid": "tests/test_main.py::test_delete",
                "outcome": "failed",
                "duration": 0.11,
                "longrepr": "KeyError: 'item_id'",
            },
        ],
    }


@pytest.fixture
def sample_coverage_data() -> dict[str, Any]:
    """Coverage.json output with 85% coverage."""
    return {
        "meta": {"format": 3, "version": "7.6.0"},
        "totals": {
            "covered_lines": 85,
            "num_statements": 100,
            "percent_covered": 85.0,
            "missing_lines": 15,
        },
    }


@pytest.fixture
def sample_coverage_low() -> dict[str, Any]:
    """Coverage.json output with 60% coverage (below target)."""
    return {
        "meta": {"format": 3, "version": "7.6.0"},
        "totals": {
            "covered_lines": 60,
            "num_statements": 100,
            "percent_covered": 60.0,
            "missing_lines": 40,
        },
    }


@pytest.fixture
def shared_state_for_tester() -> dict[str, Any]:
    """Shared state from BackendDevAgent with generated files."""
    return {
        "backend_dev.generated_files": {
            "src/main.py": (
                "from fastapi import FastAPI\n\napp = FastAPI()\n\n\n"
                '@app.get("/health")\nasync def health() -> dict[str, str]:\n'
                '    return {"status": "ok"}\n'
            ),
        },
        "backend_dev.entry_point": "src/main.py",
        "backend_dev.dependencies": ["fastapi", "pydantic"],
        "requirements": {
            "project_name": "Todo API",
            "functional_requirements": [
                {"id": "FR-01", "title": "Health endpoint"},
            ],
        },
    }


@pytest.fixture
def agent_input_for_tester(shared_state_for_tester: dict[str, Any]) -> AgentInput:
    """AgentInput with shared state for TesterAgent."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state=shared_state_for_tester,
        context_tiers={},
    )


@pytest.fixture
def tester_agent() -> Any:
    """Create a TesterAgent instance."""
    from codebot.agents.tester import TesterAgent

    return TesterAgent()


# ---------------------------------------------------------------------------
# ParsedTestResult model
# ---------------------------------------------------------------------------


class TestParsedTestResult:
    """ParsedTestResult model contains required fields."""

    def test_parsed_result_has_required_fields(self) -> None:
        from codebot.testing.parser import ParsedTestResult

        result = ParsedTestResult(
            total=10,
            passed=8,
            failed=2,
            errors=0,
            skipped=0,
            coverage_percent=85.0,
            all_passed=False,
            failure_details=[],
            duration_seconds=2.5,
        )
        assert result.total == 10
        assert result.passed == 8
        assert result.failed == 2
        assert result.errors == 0
        assert result.skipped == 0
        assert result.coverage_percent == 85.0
        assert result.all_passed is False
        assert result.failure_details == []
        assert result.duration_seconds == 2.5


# ---------------------------------------------------------------------------
# TestResultParser.parse()
# ---------------------------------------------------------------------------


class TestTestResultParser:
    """TestResultParser.parse() extracts data from pytest JSON report."""

    def test_parse_extracts_pass_counts(
        self,
        sample_test_report_all_pass: dict[str, Any],
        sample_coverage_data: dict[str, Any],
    ) -> None:
        from codebot.testing.parser import TestResultParser

        result = TestResultParser.parse(
            sample_test_report_all_pass, sample_coverage_data
        )
        assert result.total == 5
        assert result.passed == 5
        assert result.failed == 0

    def test_parse_extracts_coverage_percentage(
        self,
        sample_test_report_all_pass: dict[str, Any],
        sample_coverage_data: dict[str, Any],
    ) -> None:
        from codebot.testing.parser import TestResultParser

        result = TestResultParser.parse(
            sample_test_report_all_pass, sample_coverage_data
        )
        assert result.coverage_percent == 85.0

    def test_parse_all_passed_true_when_no_failures(
        self,
        sample_test_report_all_pass: dict[str, Any],
        sample_coverage_data: dict[str, Any],
    ) -> None:
        from codebot.testing.parser import TestResultParser

        result = TestResultParser.parse(
            sample_test_report_all_pass, sample_coverage_data
        )
        assert result.all_passed is True

    def test_parse_all_passed_false_when_failures(
        self,
        sample_test_report_with_failures: dict[str, Any],
        sample_coverage_data: dict[str, Any],
    ) -> None:
        from codebot.testing.parser import TestResultParser

        result = TestResultParser.parse(
            sample_test_report_with_failures, sample_coverage_data
        )
        assert result.all_passed is False

    def test_parse_extracts_failure_details(
        self,
        sample_test_report_with_failures: dict[str, Any],
        sample_coverage_data: dict[str, Any],
    ) -> None:
        from codebot.testing.parser import TestResultParser

        result = TestResultParser.parse(
            sample_test_report_with_failures, sample_coverage_data
        )
        assert len(result.failure_details) == 2
        nodeids = [d["nodeid"] for d in result.failure_details]
        assert "tests/test_main.py::test_get" in nodeids
        assert "tests/test_main.py::test_delete" in nodeids


# ---------------------------------------------------------------------------
# TestRunner.run()
# ---------------------------------------------------------------------------


class TestTestRunner:
    """TestRunner.run() executes pytest subprocess."""

    async def test_run_executes_pytest_with_json_report(self) -> None:
        """TestRunner.run() calls pytest with --json-report and --cov flags."""
        from codebot.testing.runner import TestRunner

        runner = TestRunner()

        # Build mock process
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"", b"")

        test_report = {
            "summary": {"total": 1, "passed": 1, "failed": 0, "error": 0, "skipped": 0},
            "tests": [],
            "duration": 1.0,
        }
        coverage_data = {"totals": {"percent_covered": 90.0}}

        with (
            patch(
                "codebot.testing.runner.asyncio.create_subprocess_exec",
                new_callable=AsyncMock,
            ) as mock_subprocess,
            patch(
                "codebot.testing.runner.Path.exists",
                return_value=True,
            ),
            patch(
                "codebot.testing.runner.Path.read_text",
                side_effect=[
                    json.dumps(test_report),
                    json.dumps(coverage_data),
                ],
            ),
        ):
            mock_subprocess.return_value = mock_proc
            report, coverage = await runner.run("/tmp/workspace")

            # Verify pytest was called with json-report
            call_args_str = str(mock_subprocess.call_args)
            assert "json-report" in call_args_str

    async def test_run_returns_dicts(self) -> None:
        """TestRunner.run() returns (test_report_dict, coverage_dict)."""
        from codebot.testing.runner import TestRunner

        runner = TestRunner()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"", b"")

        test_report = {
            "summary": {"total": 2, "passed": 2, "failed": 0, "error": 0, "skipped": 0},
            "tests": [],
            "duration": 1.0,
        }
        coverage_data = {"totals": {"percent_covered": 80.0}}

        with (
            patch(
                "codebot.testing.runner.asyncio.create_subprocess_exec",
                new_callable=AsyncMock,
            ) as mock_subprocess,
            patch(
                "codebot.testing.runner.Path.exists",
                return_value=True,
            ),
            patch(
                "codebot.testing.runner.Path.read_text",
                side_effect=[
                    json.dumps(test_report),
                    json.dumps(coverage_data),
                ],
            ),
        ):
            mock_subprocess.return_value = mock_proc
            report, coverage = await runner.run("/tmp/workspace")
            assert isinstance(report, dict)
            assert isinstance(coverage, dict)
            assert report["summary"]["total"] == 2


# ---------------------------------------------------------------------------
# TesterAgent
# ---------------------------------------------------------------------------


class TestTesterAgentType:
    """TesterAgent has agent_type == AgentType.TESTER."""

    def test_agent_type(self, tester_agent: Any) -> None:
        assert tester_agent.agent_type == AgentType.TESTER


class TestTesterPerceive:
    """TesterAgent.perceive() reads generated source files from shared state."""

    async def test_perceive_reads_generated_files(
        self, tester_agent: Any, agent_input_for_tester: AgentInput
    ) -> None:
        result = await tester_agent.perceive(agent_input_for_tester)
        assert "source_files" in result
        assert "src/main.py" in result["source_files"]

    async def test_perceive_reads_requirements(
        self, tester_agent: Any, agent_input_for_tester: AgentInput
    ) -> None:
        result = await tester_agent.perceive(agent_input_for_tester)
        assert "requirements" in result


class TestTesterReason:
    """TesterAgent.reason() calls LLM to plan test structure."""

    async def test_reason_returns_test_generation_plan(
        self, tester_agent: Any
    ) -> None:
        from codebot.agents.tester import GeneratedTest, TestGenerationPlan

        mock_plan = TestGenerationPlan(
            unit_tests=[
                GeneratedTest(
                    path="tests/test_main.py",
                    content="def test_health(): assert True",
                    test_type="unit",
                )
            ],
            integration_tests=[
                GeneratedTest(
                    path="tests/test_integration.py",
                    content="async def test_endpoint(): pass",
                    test_type="integration",
                )
            ],
        )

        with patch("codebot.agents.tester.instructor") as mock_instructor:
            mock_client = MagicMock()
            mock_instructor.from_litellm.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_plan

            context = {
                "source_files": {"src/main.py": "app = FastAPI()"},
                "requirements": {"project_name": "Todo API"},
                "workspace_path": "/tmp/workspace",
            }
            result = await tester_agent.reason(context)
            assert "test_plan" in result


class TestTesterAct:
    """TesterAgent.act() generates test files, runs TestRunner, parses results."""

    async def test_unit_test_generation(self, tester_agent: Any) -> None:
        """act() writes generated test files and runs them via TestRunner."""
        from codebot.agents.tester import GeneratedTest, TestGenerationPlan
        from codebot.testing.parser import ParsedTestResult

        mock_plan = TestGenerationPlan(
            unit_tests=[
                GeneratedTest(
                    path="tests/test_main.py",
                    content="def test_health(): assert True",
                    test_type="unit",
                )
            ],
            integration_tests=[],
        )

        test_report = {
            "summary": {"total": 1, "passed": 1, "failed": 0, "error": 0, "skipped": 0},
            "tests": [
                {"nodeid": "tests/test_main.py::test_health", "outcome": "passed", "duration": 0.1}
            ],
            "duration": 0.5,
        }
        coverage_data = {"totals": {"percent_covered": 90.0}}

        with (
            patch("codebot.agents.tester.TestRunner") as mock_runner_cls,
            patch("codebot.agents.tester.TestResultParser") as mock_parser_cls,
            patch("codebot.agents.tester.Path") as mock_path_cls,
        ):
            mock_runner = AsyncMock()
            mock_runner.run.return_value = (test_report, coverage_data)
            mock_runner_cls.return_value = mock_runner

            parsed = ParsedTestResult(
                total=1,
                passed=1,
                failed=0,
                errors=0,
                skipped=0,
                coverage_percent=90.0,
                all_passed=True,
                failure_details=[],
                duration_seconds=0.5,
            )
            mock_parser_cls.parse.return_value = parsed

            plan = {
                "test_plan": mock_plan,
                "workspace_path": "/tmp/workspace",
            }
            result = await tester_agent.act(plan)
            assert isinstance(result, PRAResult)
            assert result.is_complete is True

    async def test_integration_test_generation(self, tester_agent: Any) -> None:
        """act() generates integration tests using httpx.AsyncClient pattern."""
        from codebot.agents.tester import GeneratedTest, TestGenerationPlan
        from codebot.testing.parser import ParsedTestResult

        mock_plan = TestGenerationPlan(
            unit_tests=[],
            integration_tests=[
                GeneratedTest(
                    path="tests/test_api.py",
                    content=(
                        "import httpx\n\nasync def test_endpoint():\n"
                        "    async with httpx.AsyncClient() as client:\n"
                        "        resp = await client.get('/health')\n"
                        "        assert resp.status_code == 200\n"
                    ),
                    test_type="integration",
                )
            ],
        )

        test_report = {
            "summary": {"total": 1, "passed": 1, "failed": 0, "error": 0, "skipped": 0},
            "tests": [
                {"nodeid": "tests/test_api.py::test_endpoint", "outcome": "passed", "duration": 0.3}
            ],
            "duration": 0.8,
        }
        coverage_data = {"totals": {"percent_covered": 82.0}}

        with (
            patch("codebot.agents.tester.TestRunner") as mock_runner_cls,
            patch("codebot.agents.tester.TestResultParser") as mock_parser_cls,
            patch("codebot.agents.tester.Path") as mock_path_cls,
        ):
            mock_runner = AsyncMock()
            mock_runner.run.return_value = (test_report, coverage_data)
            mock_runner_cls.return_value = mock_runner

            parsed = ParsedTestResult(
                total=1,
                passed=1,
                failed=0,
                errors=0,
                skipped=0,
                coverage_percent=82.0,
                all_passed=True,
                failure_details=[],
                duration_seconds=0.8,
            )
            mock_parser_cls.parse.return_value = parsed

            plan = {
                "test_plan": mock_plan,
                "workspace_path": "/tmp/workspace",
            }
            result = await tester_agent.act(plan)
            assert isinstance(result, PRAResult)
            assert result.is_complete is True


class TestTesterReview:
    """TesterAgent.review() sets test_results and tests_passing in state_updates."""

    async def test_review_sets_tests_passing_true(self, tester_agent: Any) -> None:
        result = PRAResult(
            is_complete=True,
            data={
                "test_results": {
                    "total": 5,
                    "passed": 5,
                    "failed": 0,
                    "errors": 0,
                    "skipped": 0,
                    "coverage_percent": 85.0,
                    "all_passed": True,
                    "failure_details": [],
                    "duration_seconds": 2.5,
                },
                "tests_passing": True,
            },
        )
        output = await tester_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.state_updates["tests_passing"] is True
        assert "test_results" in output.state_updates

    async def test_review_sets_tests_passing_false_on_failure(
        self, tester_agent: Any
    ) -> None:
        failure_details = [
            {
                "nodeid": "tests/test_main.py::test_get",
                "outcome": "failed",
                "longrepr": "AssertionError",
            }
        ]
        result = PRAResult(
            is_complete=True,
            data={
                "test_results": {
                    "total": 5,
                    "passed": 3,
                    "failed": 2,
                    "errors": 0,
                    "skipped": 0,
                    "coverage_percent": 70.0,
                    "all_passed": False,
                    "failure_details": failure_details,
                    "duration_seconds": 1.5,
                },
                "tests_passing": False,
                "test_failures": failure_details,
            },
        )
        output = await tester_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.state_updates["tests_passing"] is False
        assert "test_failures" in output.state_updates

    async def test_review_routes_to_debugger_on_failure(
        self, tester_agent: Any
    ) -> None:
        """When tests fail, review() includes test_failures for Debugger agent."""
        failure_details = [
            {
                "nodeid": "tests/test_main.py::test_delete",
                "outcome": "failed",
                "longrepr": "KeyError: 'item_id'",
            }
        ]
        result = PRAResult(
            is_complete=True,
            data={
                "test_results": {
                    "total": 3,
                    "passed": 2,
                    "failed": 1,
                    "errors": 0,
                    "skipped": 0,
                    "coverage_percent": 75.0,
                    "all_passed": False,
                    "failure_details": failure_details,
                    "duration_seconds": 1.0,
                },
                "tests_passing": False,
                "test_failures": failure_details,
            },
        )
        output = await tester_agent.review(result)
        assert output.state_updates["tests_passing"] is False
        assert output.state_updates["test_failures"] == failure_details
        assert output.review_passed is False
