"""Unit tests for DebuggerAgent.

Tests cover:
- Agent type identification
- PRA cycle methods (perceive, reason, act, review)
- Integration with FailureAnalyzer, FixGenerator, ExperimentLoopController
- Experiment loop with KEEP/DISCARD semantics
"""

from __future__ import annotations

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
def shared_state_for_debugger() -> dict[str, Any]:
    """Shared state from TesterAgent with failed test results."""
    return {
        "test_failures": [
            {
                "nodeid": "tests/test_main.py::test_get",
                "outcome": "failed",
                "longrepr": "KeyError: 'item_id'\n  File src/handlers.py:25",
            }
        ],
        "tests_passing": False,
        "test_results": {
            "total": 5,
            "passed": 4,
            "failed": 1,
            "errors": 0,
            "skipped": 0,
            "coverage_percent": 80.0,
            "all_passed": False,
        },
        "backend_dev.generated_files": {
            "src/handlers.py": "def get_item(data): return data['item_id']",
            "src/main.py": "from fastapi import FastAPI\napp = FastAPI()",
        },
    }


@pytest.fixture
def agent_input_for_debugger(shared_state_for_debugger: dict[str, Any]) -> AgentInput:
    """AgentInput for DebuggerAgent."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state=shared_state_for_debugger,
        context_tiers={},
    )


@pytest.fixture
def debugger_agent() -> Any:
    """Create a DebuggerAgent instance."""
    from codebot.agents.debugger import DebuggerAgent

    return DebuggerAgent()


# ---------------------------------------------------------------------------
# Agent type
# ---------------------------------------------------------------------------


class TestDebuggerAgentType:
    """DebuggerAgent has agent_type == AgentType.DEBUGGER."""

    def test_agent_type(self, debugger_agent: Any) -> None:
        assert debugger_agent.agent_type == AgentType.DEBUGGER


# ---------------------------------------------------------------------------
# perceive()
# ---------------------------------------------------------------------------


class TestDebuggerPerceive:
    """DebuggerAgent.perceive() reads test failures from shared state."""

    async def test_perceive_reads_test_failures(
        self, debugger_agent: Any, agent_input_for_debugger: AgentInput
    ) -> None:
        result = await debugger_agent.perceive(agent_input_for_debugger)
        assert "test_failures" in result
        assert len(result["test_failures"]) == 1

    async def test_perceive_reads_source_files(
        self, debugger_agent: Any, agent_input_for_debugger: AgentInput
    ) -> None:
        result = await debugger_agent.perceive(agent_input_for_debugger)
        assert "source_files" in result
        assert "src/handlers.py" in result["source_files"]


# ---------------------------------------------------------------------------
# reason()
# ---------------------------------------------------------------------------


class TestDebuggerReason:
    """DebuggerAgent.reason() calls FailureAnalyzer.analyze()."""

    async def test_reason_performs_root_cause_analysis(
        self, debugger_agent: Any
    ) -> None:
        from codebot.debug.analyzer import FailureAnalysis

        mock_analysis = FailureAnalysis(
            root_cause="KeyError: missing key 'item_id'",
            affected_files=["src/handlers.py"],
            confidence=0.9,
            suggested_approach="Use dict.get() for safe access",
            failure_category="logic_error",
        )

        with patch("codebot.agents.debugger.FailureAnalyzer") as mock_analyzer_cls:
            mock_analyzer = AsyncMock()
            mock_analyzer.analyze.return_value = mock_analysis
            mock_analyzer_cls.return_value = mock_analyzer

            context = {
                "test_failures": [
                    {
                        "nodeid": "tests/test_main.py::test_get",
                        "outcome": "failed",
                        "longrepr": "KeyError: 'item_id'",
                    }
                ],
                "source_files": {
                    "src/handlers.py": "def get_item(data): return data['item_id']"
                },
                "baseline_pass_rate": 0.8,
                "workspace_path": "/tmp/workspace",
            }
            result = await debugger_agent.reason(context)
            assert "analysis" in result
            assert result["analysis"].root_cause == "KeyError: missing key 'item_id'"


# ---------------------------------------------------------------------------
# act()
# ---------------------------------------------------------------------------


class TestDebuggerAct:
    """DebuggerAgent.act() runs experiment loop."""

    async def test_act_runs_experiment_loop(self, debugger_agent: Any) -> None:
        """act() runs analyze -> generate fix -> apply -> re-test loop."""
        from codebot.debug.analyzer import FailureAnalysis
        from codebot.debug.fixer import FixProposal
        from codebot.testing.parser import ParsedTestResult

        mock_analysis = FailureAnalysis(
            root_cause="KeyError",
            affected_files=["src/handlers.py"],
            confidence=0.9,
            suggested_approach="Use .get()",
            failure_category="logic_error",
        )

        mock_fixes = [
            FixProposal(
                file_path="src/handlers.py",
                original_content="return data['item_id']",
                fixed_content="return data.get('item_id')",
                hypothesis="Safe key access",
                diff_lines=1,
            )
        ]

        # After fix, all tests pass
        test_report = {
            "summary": {"total": 5, "passed": 5, "failed": 0, "error": 0, "skipped": 0},
            "tests": [],
            "duration": 1.0,
        }
        coverage_data = {"totals": {"percent_covered": 85.0}}

        with (
            patch("codebot.agents.debugger.FixGenerator") as mock_fixer_cls,
            patch("codebot.agents.debugger.TestRunner") as mock_runner_cls,
            patch("codebot.agents.debugger.TestResultParser") as mock_parser_cls,
        ):
            mock_fixer = AsyncMock()
            mock_fixer.generate.return_value = mock_fixes
            mock_fixer.apply.return_value = None
            mock_fixer_cls.return_value = mock_fixer

            mock_runner = AsyncMock()
            mock_runner.run.return_value = (test_report, coverage_data)
            mock_runner_cls.return_value = mock_runner

            parsed_result = ParsedTestResult(
                total=5,
                passed=5,
                failed=0,
                errors=0,
                skipped=0,
                coverage_percent=85.0,
                all_passed=True,
                failure_details=[],
                duration_seconds=1.0,
            )
            mock_parser_cls.parse.return_value = parsed_result

            plan = {
                "analysis": mock_analysis,
                "test_failures": [{"nodeid": "tests/test_main.py::test_get"}],
                "source_files": {
                    "src/handlers.py": "def get_item(data): return data['item_id']"
                },
                "baseline_pass_rate": 0.8,
                "workspace_path": "/tmp/debug_workspace",
            }
            result = await debugger_agent.act(plan)
            assert isinstance(result, PRAResult)
            assert result.is_complete is True


# ---------------------------------------------------------------------------
# review()
# ---------------------------------------------------------------------------


class TestDebuggerReview:
    """DebuggerAgent.review() returns AgentOutput with tests_passing status."""

    async def test_review_returns_passing_status(self, debugger_agent: Any) -> None:
        result = PRAResult(
            is_complete=True,
            data={
                "tests_passing": True,
                "final_pass_rate": 1.0,
                "experiment_log": [
                    {
                        "experiment_id": 1,
                        "hypothesis": "Fix null check",
                        "status": "KEEP",
                        "delta": 0.2,
                    }
                ],
            },
        )
        output = await debugger_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.state_updates["tests_passing"] is True
        assert output.state_updates["final_pass_rate"] == 1.0
        assert "experiment_log" in output.state_updates

    async def test_review_returns_failing_status(self, debugger_agent: Any) -> None:
        result = PRAResult(
            is_complete=True,
            data={
                "tests_passing": False,
                "final_pass_rate": 0.8,
                "experiment_log": [
                    {
                        "experiment_id": 1,
                        "hypothesis": "Fix null check",
                        "status": "DISCARD",
                        "delta": 0.0,
                    }
                ],
            },
        )
        output = await debugger_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.state_updates["tests_passing"] is False
        assert output.review_passed is False
