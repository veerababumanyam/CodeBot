"""Unit tests for CodeReviewerAgent.

Tests cover:
- ReviewComment and CodeReviewReport Pydantic model validation
- Quality gate logic (gate_passed based on severity)
- Agent type identification
- PRA cycle methods (perceive, reason, act, review)
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from agent_sdk.agents.base import AgentInput, AgentOutput, PRAResult
from agent_sdk.models.enums import AgentType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def shared_state_with_files() -> dict[str, Any]:
    """Shared state containing generated files from BackendDevAgent."""
    return {
        "backend_dev.generated_files": {
            "src/main.py": (
                'from fastapi import FastAPI\n\n'
                'app = FastAPI()\n\n\n'
                '@app.get("/health")\n'
                'async def health() -> dict[str, str]:\n'
                '    """Health check endpoint."""\n'
                '    return {"status": "ok"}\n'
            ),
            "src/models.py": (
                'from pydantic import BaseModel\n\n\n'
                'class TodoItem(BaseModel):\n'
                '    """A todo item."""\n\n'
                '    title: str\n'
                '    description: str\n'
                '    completed: bool = False\n'
            ),
        },
    }


@pytest.fixture
def agent_input(shared_state_with_files: dict[str, Any]) -> AgentInput:
    """Construct an AgentInput with generated files."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state=shared_state_with_files,
        context_tiers={"l0": {}, "l1": {}},
    )


@pytest.fixture
def reviewer_agent() -> Any:
    """Create a CodeReviewerAgent instance."""
    from codebot.agents.code_reviewer import CodeReviewerAgent

    return CodeReviewerAgent()


# ---------------------------------------------------------------------------
# ReviewComment model validation
# ---------------------------------------------------------------------------


class TestReviewCommentModel:
    """ReviewComment Pydantic model validation."""

    def test_review_comment_validates(self) -> None:
        """ReviewComment validates with all required fields."""
        from codebot.agents.code_reviewer import ReviewComment

        comment = ReviewComment(
            file_path="src/main.py",
            line_start=5,
            line_end=10,
            severity="medium",
            category="style",
            message="Consider using a constant for the status string.",
        )
        assert comment.file_path == "src/main.py"
        assert comment.line_start == 5
        assert comment.line_end == 10
        assert comment.severity == "medium"
        assert comment.category == "style"

    def test_review_comment_severity_values(self) -> None:
        """ReviewComment severity accepts critical/high/medium/low/info."""
        from codebot.agents.code_reviewer import ReviewComment

        for severity in ("critical", "high", "medium", "low", "info"):
            comment = ReviewComment(
                file_path="src/main.py",
                line_start=1,
                line_end=1,
                severity=severity,
                category="bug",
                message="test",
            )
            assert comment.severity == severity

    def test_review_comment_category_values(self) -> None:
        """ReviewComment category accepts bug/style/performance/security/architecture/suggestion."""
        from codebot.agents.code_reviewer import ReviewComment

        for category in (
            "bug",
            "style",
            "performance",
            "security",
            "architecture",
            "suggestion",
        ):
            comment = ReviewComment(
                file_path="src/main.py",
                line_start=1,
                line_end=1,
                severity="info",
                category=category,
                message="test",
            )
            assert comment.category == category

    def test_review_comment_optional_suggested_fix(self) -> None:
        """ReviewComment suggested_fix is optional."""
        from codebot.agents.code_reviewer import ReviewComment

        comment_without = ReviewComment(
            file_path="src/main.py",
            line_start=1,
            line_end=1,
            severity="low",
            category="style",
            message="test",
        )
        assert comment_without.suggested_fix is None

        comment_with = ReviewComment(
            file_path="src/main.py",
            line_start=1,
            line_end=1,
            severity="low",
            category="style",
            message="test",
            suggested_fix="Use f-string instead.",
        )
        assert comment_with.suggested_fix == "Use f-string instead."


# ---------------------------------------------------------------------------
# CodeReviewReport model + quality gate logic
# ---------------------------------------------------------------------------


class TestCodeReviewReportModel:
    """CodeReviewReport model validation and quality gate logic."""

    def test_review_output(self) -> None:
        """CodeReviewReport validates with comments, quality, gate, summary."""
        from codebot.agents.code_reviewer import CodeReviewReport, ReviewComment

        report = CodeReviewReport(
            comments=[
                ReviewComment(
                    file_path="src/main.py",
                    line_start=1,
                    line_end=1,
                    severity="info",
                    category="suggestion",
                    message="Consider adding logging.",
                )
            ],
            overall_quality="good",
            gate_passed=True,
            summary="Code is well-structured with minor suggestions.",
        )
        assert report.overall_quality == "good"
        assert report.gate_passed is True
        assert len(report.comments) == 1

    def test_quality_gate(self) -> None:
        """gate_passed=False when comments contain critical or high severity."""
        from codebot.agents.code_reviewer import CodeReviewReport, ReviewComment

        report_critical = CodeReviewReport(
            comments=[
                ReviewComment(
                    file_path="src/main.py",
                    line_start=5,
                    line_end=10,
                    severity="critical",
                    category="security",
                    message="SQL injection vulnerability.",
                )
            ],
            overall_quality="poor",
            gate_passed=False,
            summary="Critical security issue found.",
        )
        assert report_critical.gate_passed is False

    def test_quality_gate_passes_with_low_severity(self) -> None:
        """gate_passed=True when no critical or high severity comments exist."""
        from codebot.agents.code_reviewer import CodeReviewReport, ReviewComment

        report_clean = CodeReviewReport(
            comments=[
                ReviewComment(
                    file_path="src/main.py",
                    line_start=1,
                    line_end=1,
                    severity="low",
                    category="style",
                    message="Minor style suggestion.",
                ),
                ReviewComment(
                    file_path="src/models.py",
                    line_start=3,
                    line_end=3,
                    severity="info",
                    category="suggestion",
                    message="Consider adding docstring.",
                ),
            ],
            overall_quality="good",
            gate_passed=True,
            summary="No critical issues.",
        )
        assert report_clean.gate_passed is True

    def test_quality_gate_fails_with_high_severity(self) -> None:
        """gate_passed=False when high severity comment exists."""
        from codebot.agents.code_reviewer import CodeReviewReport, ReviewComment

        report_high = CodeReviewReport(
            comments=[
                ReviewComment(
                    file_path="src/main.py",
                    line_start=10,
                    line_end=15,
                    severity="high",
                    category="bug",
                    message="Null pointer dereference.",
                )
            ],
            overall_quality="needs_work",
            gate_passed=False,
            summary="High severity bug found.",
        )
        assert report_high.gate_passed is False


# ---------------------------------------------------------------------------
# Agent type
# ---------------------------------------------------------------------------


class TestCodeReviewerAgentType:
    """CodeReviewerAgent has agent_type == AgentType.CODE_REVIEWER."""

    async def test_agent_type(self, reviewer_agent: Any) -> None:
        assert reviewer_agent.agent_type == AgentType.CODE_REVIEWER


# ---------------------------------------------------------------------------
# perceive()
# ---------------------------------------------------------------------------


class TestPerceive:
    """CodeReviewerAgent.perceive() reads generated source files."""

    async def test_perceive_reads_generated_files(
        self, reviewer_agent: Any, agent_input: AgentInput
    ) -> None:
        result = await reviewer_agent.perceive(agent_input)
        assert "source_files" in result
        assert "src/main.py" in result["source_files"]
        assert "src/models.py" in result["source_files"]


# ---------------------------------------------------------------------------
# reason()
# ---------------------------------------------------------------------------


class TestReason:
    """CodeReviewerAgent.reason() calls LLM and returns CodeReviewReport."""

    async def test_reason_returns_review_report(
        self, reviewer_agent: Any
    ) -> None:
        from codebot.agents.code_reviewer import CodeReviewReport, ReviewComment

        mock_report = CodeReviewReport(
            comments=[
                ReviewComment(
                    file_path="src/main.py",
                    line_start=7,
                    line_end=9,
                    severity="info",
                    category="suggestion",
                    message="Consider adding request validation.",
                )
            ],
            overall_quality="good",
            gate_passed=True,
            summary="Code looks good with minor suggestions.",
        )

        with patch(
            "codebot.agents.code_reviewer.instructor"
        ) as mock_instructor:
            mock_client = MagicMock()
            mock_instructor.from_litellm.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_report

            context = {
                "source_files": {
                    "src/main.py": "from fastapi import FastAPI\napp = FastAPI()\n"
                }
            }
            result = await reviewer_agent.reason(context)
            assert "report" in result
            assert result["report"].gate_passed is True


# ---------------------------------------------------------------------------
# act()
# ---------------------------------------------------------------------------


class TestAct:
    """CodeReviewerAgent.act() extracts gate result and returns PRAResult."""

    async def test_act_sets_quality_gate_result(
        self, reviewer_agent: Any
    ) -> None:
        from codebot.agents.code_reviewer import CodeReviewReport, ReviewComment

        report = CodeReviewReport(
            comments=[
                ReviewComment(
                    file_path="src/main.py",
                    line_start=1,
                    line_end=1,
                    severity="low",
                    category="style",
                    message="Minor issue.",
                )
            ],
            overall_quality="good",
            gate_passed=True,
            summary="All good.",
        )
        plan = {"report": report}
        result = await reviewer_agent.act(plan)
        assert isinstance(result, PRAResult)
        assert result.is_complete is True
        assert result.data["gate_passed"] is True


# ---------------------------------------------------------------------------
# review()
# ---------------------------------------------------------------------------


class TestReview:
    """CodeReviewerAgent.review() returns AgentOutput matching gate_passed."""

    async def test_review_passed_when_gate_passes(
        self, reviewer_agent: Any
    ) -> None:
        from codebot.agents.code_reviewer import CodeReviewReport, ReviewComment

        report = CodeReviewReport(
            comments=[],
            overall_quality="excellent",
            gate_passed=True,
            summary="No issues found.",
        )
        result = PRAResult(
            is_complete=True,
            data={
                "gate_passed": True,
                "report": report.model_dump(),
                "comments": [],
            },
        )
        output = await reviewer_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True
        assert output.state_updates["code_review.gate_passed"] is True

    async def test_review_failed_when_gate_fails(
        self, reviewer_agent: Any
    ) -> None:
        from codebot.agents.code_reviewer import CodeReviewReport, ReviewComment

        report = CodeReviewReport(
            comments=[
                ReviewComment(
                    file_path="src/main.py",
                    line_start=1,
                    line_end=5,
                    severity="critical",
                    category="security",
                    message="SQL injection.",
                )
            ],
            overall_quality="poor",
            gate_passed=False,
            summary="Critical issue.",
        )
        result = PRAResult(
            is_complete=True,
            data={
                "gate_passed": False,
                "report": report.model_dump(),
                "comments": [c.model_dump() for c in report.comments],
            },
        )
        output = await reviewer_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False
        assert output.state_updates["code_review.gate_passed"] is False
