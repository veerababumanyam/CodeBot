"""Unit tests for BranchStrategy and CommitManager."""

from __future__ import annotations

from unittest.mock import AsyncMock, call, patch

import pytest

from codebot.worktree.branch_strategy import BranchStrategy
from codebot.worktree.commit_manager import CommitManager
from codebot.worktree.models import BranchConfig, MergeResult


# ---------------------------------------------------------------------------
# BranchStrategy tests
# ---------------------------------------------------------------------------


class TestCreateBranchName:
    """Tests for BranchStrategy.create_branch_name()."""

    def test_create_branch_name_standard(self) -> None:
        """Standard config produces 'prefix/task_id-sanitized_agent_id' format."""
        strategy = BranchStrategy()
        config = BranchConfig(
            prefix="feature", task_id="TASK-123", agent_id="backend_dev"
        )
        name = strategy.create_branch_name(config)
        assert name == "feature/TASK-123-backend-dev"

    def test_create_branch_name_sanitizes_special_chars(self) -> None:
        """Special characters in agent_id are replaced with hyphens."""
        strategy = BranchStrategy()
        config = BranchConfig(
            prefix="feature", task_id="TASK-001", agent_id="Backend Dev #1"
        )
        name = strategy.create_branch_name(config)
        assert name == "feature/TASK-001-backend-dev-1"

    def test_create_branch_name_no_task_id(self) -> None:
        """When task_id is empty, format is 'prefix/sanitized_agent_id'."""
        strategy = BranchStrategy()
        config = BranchConfig(prefix="feature", task_id="", agent_id="backend_dev")
        name = strategy.create_branch_name(config)
        assert name == "feature/backend-dev"


# ---------------------------------------------------------------------------
# BranchStrategy merge tests
# ---------------------------------------------------------------------------


class TestMergeSequential:
    """Tests for BranchStrategy.merge_sequential()."""

    @pytest.mark.asyncio
    async def test_merge_sequential_success(self) -> None:
        """Successful merge returns MergeResult with success=True."""
        strategy = BranchStrategy()
        mock_git = AsyncMock(return_value=("", "", 0))

        with patch.object(strategy, "_run_git", mock_git):
            result = await strategy.merge_sequential(
                repo_path="/repo",
                source_branch="feature/task-1",
                target_branch="main",
            )

        assert isinstance(result, MergeResult)
        assert result.success is True
        assert result.merged_branch == "feature/task-1"
        assert result.target_branch == "main"
        assert result.conflicts == []

    @pytest.mark.asyncio
    async def test_merge_sequential_conflict(self) -> None:
        """Merge conflict returns MergeResult with success=False and conflict files."""
        strategy = BranchStrategy()

        async def mock_git_side_effect(
            cwd: str, *args: str
        ) -> tuple[str, str, int]:
            cmd = args
            if cmd[0] == "checkout":
                return ("", "", 0)
            if cmd[0] == "merge":
                if "--abort" in cmd:
                    return ("", "", 0)
                return ("", "CONFLICT (content): Merge conflict", 1)
            if cmd[0] == "diff":
                return ("file1.py\nfile2.py\n", "", 0)
            return ("", "", 0)

        with patch.object(strategy, "_run_git", side_effect=mock_git_side_effect):
            result = await strategy.merge_sequential(
                repo_path="/repo",
                source_branch="feature/task-1",
                target_branch="main",
            )

        assert result.success is False
        assert result.conflicts == ["file1.py", "file2.py"]
        assert result.error == "Merge conflicts detected"


# ---------------------------------------------------------------------------
# BranchStrategy check_conflicts tests
# ---------------------------------------------------------------------------


class TestCheckConflicts:
    """Tests for BranchStrategy.check_conflicts()."""

    @pytest.mark.asyncio
    async def test_check_conflicts_clean(self) -> None:
        """No conflicts returns an empty list."""
        strategy = BranchStrategy()
        mock_git = AsyncMock(return_value=("abc123\n", "", 0))

        with patch.object(strategy, "_run_git", mock_git):
            conflicts = await strategy.check_conflicts(
                repo_path="/repo",
                source_branch="feature/task-1",
                target_branch="main",
            )

        assert conflicts == []

    @pytest.mark.asyncio
    async def test_check_conflicts_detected(self) -> None:
        """Conflict output from merge-tree produces non-empty conflict list."""
        strategy = BranchStrategy()

        call_count = 0

        async def mock_git_side_effect(
            cwd: str, *args: str
        ) -> tuple[str, str, int]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # merge-base
                return ("abc123\n", "", 0)
            # merge-tree with conflict
            return (
                "changed in both\n  base   100644 abc src/main.py\n"
                "  our    100644 def src/main.py\n"
                "  their  100644 ghi src/main.py\n",
                "",
                0,
            )

        with patch.object(strategy, "_run_git", side_effect=mock_git_side_effect):
            conflicts = await strategy.check_conflicts(
                repo_path="/repo",
                source_branch="feature/task-1",
                target_branch="main",
            )

        assert len(conflicts) > 0


# ---------------------------------------------------------------------------
# CommitManager tests
# ---------------------------------------------------------------------------


class TestCommitManager:
    """Tests for CommitManager.commit() with agent trailers."""

    @pytest.mark.asyncio
    async def test_commit_with_trailers(self) -> None:
        """commit() creates a git commit with agent attribution and task ref."""
        manager = CommitManager(worktree_path="/worktree")
        mock_git = AsyncMock(return_value=("abc123def456\n", "", 0))

        with patch.object(manager, "_run_git", mock_git):
            sha = await manager.commit(
                message="feat: add auth endpoint",
                paths=["src/auth.py", "tests/test_auth.py"],
                agent_id="backend-dev",
                task_id="TASK-42",
            )

        # Verify git add was called for each path
        add_calls = [
            c for c in mock_git.call_args_list if c[0][0] == "add"
        ]
        assert len(add_calls) == 2
        assert add_calls[0] == call("add", "src/auth.py")
        assert add_calls[1] == call("add", "tests/test_auth.py")

        # Verify commit message contains agent trailer
        commit_calls = [
            c for c in mock_git.call_args_list if c[0][0] == "commit"
        ]
        assert len(commit_calls) == 1
        commit_msg = commit_calls[0][0][2]  # args: "commit", "-m", message
        assert "Agent: backend-dev" in commit_msg
        assert "Refs: TASK-42" in commit_msg

        # Verify SHA is returned
        assert sha == "abc123def456"
