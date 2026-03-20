"""Unit tests for FailureAnalyzer.

Tests cover:
- FailureAnalysis model fields
- FailureAnalyzer.analyze() root cause identification via LLM (mocked)
- FailureAnalyzer.analyze() returns affected_files list
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# FailureAnalysis model
# ---------------------------------------------------------------------------


class TestFailureAnalysis:
    """FailureAnalysis model contains required fields."""

    def test_failure_analysis_fields(self) -> None:
        from codebot.debug.analyzer import FailureAnalysis

        analysis = FailureAnalysis(
            root_cause="Missing null check in get_item handler",
            affected_files=["src/main.py", "src/models.py"],
            confidence=0.85,
            suggested_approach="Add null check before accessing item.id",
            failure_category="logic_error",
        )
        assert analysis.root_cause == "Missing null check in get_item handler"
        assert len(analysis.affected_files) == 2
        assert analysis.confidence == 0.85
        assert analysis.suggested_approach == "Add null check before accessing item.id"
        assert analysis.failure_category == "logic_error"


# ---------------------------------------------------------------------------
# FailureAnalyzer.analyze()
# ---------------------------------------------------------------------------


class TestFailureAnalyzer:
    """FailureAnalyzer.analyze() parses stack traces and identifies root cause."""

    async def test_root_cause_analysis(self) -> None:
        """analyze() calls LLM with failure details and returns FailureAnalysis."""
        from codebot.debug.analyzer import FailureAnalysis, FailureAnalyzer

        mock_analysis = FailureAnalysis(
            root_cause="KeyError in get_item: missing 'item_id' key",
            affected_files=["src/handlers.py"],
            confidence=0.9,
            suggested_approach="Add key existence check before access",
            failure_category="logic_error",
        )

        with patch("codebot.debug.analyzer.instructor") as mock_instructor:
            mock_client = MagicMock()
            mock_instructor.from_litellm.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_analysis

            analyzer = FailureAnalyzer()
            result = await analyzer.analyze(
                failure_details=[
                    {
                        "nodeid": "tests/test_main.py::test_get",
                        "outcome": "failed",
                        "longrepr": "KeyError: 'item_id'\n  File src/handlers.py:25",
                    }
                ],
                source_files={"src/handlers.py": "def get_item(data): return data['item_id']"},
            )

            assert isinstance(result, FailureAnalysis)
            assert result.root_cause == "KeyError in get_item: missing 'item_id' key"
            assert "src/handlers.py" in result.affected_files
            assert result.confidence == 0.9

    async def test_analyze_returns_affected_files(self) -> None:
        """analyze() identifies affected files from stack trace context."""
        from codebot.debug.analyzer import FailureAnalysis, FailureAnalyzer

        mock_analysis = FailureAnalysis(
            root_cause="Type error in create_item",
            affected_files=["src/main.py", "src/models.py"],
            confidence=0.75,
            suggested_approach="Fix type annotation",
            failure_category="type_error",
        )

        with patch("codebot.debug.analyzer.instructor") as mock_instructor:
            mock_client = MagicMock()
            mock_instructor.from_litellm.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_analysis

            analyzer = FailureAnalyzer()
            result = await analyzer.analyze(
                failure_details=[
                    {
                        "nodeid": "tests/test_main.py::test_create",
                        "outcome": "failed",
                        "longrepr": "TypeError: expected str, got int",
                    }
                ],
                source_files={
                    "src/main.py": "app = FastAPI()",
                    "src/models.py": "class Item(BaseModel): ...",
                },
            )

            assert len(result.affected_files) == 2
