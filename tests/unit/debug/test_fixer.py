"""Unit tests for FixGenerator.

Tests cover:
- FixProposal model fields
- FixGenerator.generate() creates targeted code patches via LLM (mocked)
- FixGenerator.apply() writes fixed content to workspace
"""

from __future__ import annotations

import os
import tempfile
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# FixProposal model
# ---------------------------------------------------------------------------


class TestFixProposal:
    """FixProposal model contains required fields."""

    def test_fix_proposal_fields(self) -> None:
        from codebot.debug.fixer import FixProposal

        proposal = FixProposal(
            file_path="src/handlers.py",
            original_content="def get_item(data): return data['item_id']",
            fixed_content="def get_item(data): return data.get('item_id')",
            hypothesis="Replace dict key access with .get() to handle missing keys",
            diff_lines=1,
        )
        assert proposal.file_path == "src/handlers.py"
        assert proposal.original_content == "def get_item(data): return data['item_id']"
        assert proposal.fixed_content == "def get_item(data): return data.get('item_id')"
        assert proposal.hypothesis == "Replace dict key access with .get() to handle missing keys"
        assert proposal.diff_lines == 1


# ---------------------------------------------------------------------------
# FixGenerator.generate()
# ---------------------------------------------------------------------------


class TestFixGenerator:
    """FixGenerator.generate() creates targeted code patches."""

    async def test_fix_generation(self) -> None:
        """generate() calls LLM with analysis and returns FixProposal list."""
        from codebot.debug.analyzer import FailureAnalysis
        from codebot.debug.fixer import FixGenerator, FixProposal

        mock_fixes = [
            FixProposal(
                file_path="src/handlers.py",
                original_content="return data['item_id']",
                fixed_content="return data.get('item_id')",
                hypothesis="Use .get() for safe key access",
                diff_lines=1,
            )
        ]

        analysis = FailureAnalysis(
            root_cause="KeyError on missing key",
            affected_files=["src/handlers.py"],
            confidence=0.9,
            suggested_approach="Use dict.get()",
            failure_category="logic_error",
        )

        with patch("codebot.debug.fixer.instructor") as mock_instructor:
            mock_client = MagicMock()
            mock_instructor.from_litellm.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_fixes

            generator = FixGenerator()
            result = await generator.generate(
                analysis=analysis,
                source_files={"src/handlers.py": "def get_item(data): return data['item_id']"},
            )

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0].file_path == "src/handlers.py"

    async def test_generate_multiple_fixes(self) -> None:
        """generate() can return multiple fix proposals for different files."""
        from codebot.debug.analyzer import FailureAnalysis
        from codebot.debug.fixer import FixGenerator, FixProposal

        mock_fixes = [
            FixProposal(
                file_path="src/main.py",
                original_content="app.get('/item')",
                fixed_content="app.get('/items/{item_id}')",
                hypothesis="Fix route path",
                diff_lines=1,
            ),
            FixProposal(
                file_path="src/models.py",
                original_content="class Item: pass",
                fixed_content="class Item(BaseModel): id: int",
                hypothesis="Add Pydantic model fields",
                diff_lines=2,
            ),
        ]

        analysis = FailureAnalysis(
            root_cause="Multiple issues",
            affected_files=["src/main.py", "src/models.py"],
            confidence=0.8,
            suggested_approach="Fix route and model",
            failure_category="logic_error",
        )

        with patch("codebot.debug.fixer.instructor") as mock_instructor:
            mock_client = MagicMock()
            mock_instructor.from_litellm.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_fixes

            generator = FixGenerator()
            result = await generator.generate(
                analysis=analysis,
                source_files={
                    "src/main.py": "app.get('/item')",
                    "src/models.py": "class Item: pass",
                },
            )

            assert len(result) == 2


# ---------------------------------------------------------------------------
# FixGenerator.apply()
# ---------------------------------------------------------------------------


class TestFixApply:
    """FixGenerator.apply() writes fixed content to workspace files."""

    async def test_apply_writes_files(self) -> None:
        """apply() writes fix.fixed_content to workspace/fix.file_path."""
        from codebot.debug.fixer import FixGenerator, FixProposal

        workspace = tempfile.mkdtemp(prefix="test_fixer_")

        fixes = [
            FixProposal(
                file_path="src/handlers.py",
                original_content="return data['item_id']",
                fixed_content="return data.get('item_id')",
                hypothesis="Safe key access",
                diff_lines=1,
            )
        ]

        generator = FixGenerator()
        await generator.apply(fixes, workspace)

        fixed_path = os.path.join(workspace, "src", "handlers.py")
        assert os.path.exists(fixed_path)
        with open(fixed_path) as f:
            content = f.read()
        assert content == "return data.get('item_id')"
