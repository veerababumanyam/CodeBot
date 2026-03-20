"""Unit tests for BackendDevAgent.

Tests cover:
- Agent type identification
- PRA cycle methods (perceive, reason, act, review)
- Lint/typecheck subprocess validation
- Re-prompting on lint/type errors
- Code generation via instructor + LiteLLM
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
def shared_state() -> dict[str, Any]:
    """Sample shared state with requirements and API spec."""
    return {
        "requirements": {
            "project_name": "Todo API",
            "functional_requirements": [
                {
                    "id": "FR-01",
                    "title": "Create todo",
                    "description": "POST /todos creates a todo item",
                }
            ],
        },
        "api_spec": {
            "endpoints": [{"method": "POST", "path": "/todos"}],
        },
    }


@pytest.fixture
def agent_input(shared_state: dict[str, Any]) -> AgentInput:
    """Construct an AgentInput with sample data."""
    return AgentInput(
        task_id=uuid.uuid4(),
        shared_state=shared_state,
        context_tiers={
            "l0": {"conventions": "Use Pydantic v2, async/await, Google docstrings."},
        },
    )


@pytest.fixture
def backend_agent() -> Any:
    """Create a BackendDevAgent instance."""
    from codebot.agents.backend_dev import BackendDevAgent

    return BackendDevAgent()


# ---------------------------------------------------------------------------
# Agent type
# ---------------------------------------------------------------------------


class TestBackendDevAgentType:
    """BackendDevAgent has agent_type == AgentType.BACKEND_DEV."""

    async def test_agent_type(self, backend_agent: Any) -> None:
        assert backend_agent.agent_type == AgentType.BACKEND_DEV


# ---------------------------------------------------------------------------
# perceive()
# ---------------------------------------------------------------------------


class TestPerceive:
    """BackendDevAgent.perceive() assembles requirements, api_spec, conventions."""

    async def test_perceive_returns_requirements(
        self, backend_agent: Any, agent_input: AgentInput
    ) -> None:
        result = await backend_agent.perceive(agent_input)
        assert "requirements" in result
        assert result["requirements"]["project_name"] == "Todo API"

    async def test_perceive_returns_api_spec(
        self, backend_agent: Any, agent_input: AgentInput
    ) -> None:
        result = await backend_agent.perceive(agent_input)
        assert "api_spec" in result

    async def test_perceive_returns_conventions(
        self, backend_agent: Any, agent_input: AgentInput
    ) -> None:
        result = await backend_agent.perceive(agent_input)
        assert "conventions" in result

    async def test_perceive_includes_review_comments_when_present(
        self, backend_agent: Any, agent_input: AgentInput
    ) -> None:
        agent_input.shared_state["review_comments"] = [
            {"message": "Missing error handling"}
        ]
        result = await backend_agent.perceive(agent_input)
        assert "review_comments" in result


# ---------------------------------------------------------------------------
# reason()
# ---------------------------------------------------------------------------


class TestReason:
    """BackendDevAgent.reason() calls LLM to plan code structure."""

    async def test_reason_returns_planned_files(
        self, backend_agent: Any
    ) -> None:
        from codebot.agents.backend_dev import CodeGenerationPlan, GeneratedFile

        mock_plan = CodeGenerationPlan(
            files=[
                GeneratedFile(
                    path="src/main.py",
                    content="from fastapi import FastAPI\napp = FastAPI()",
                    purpose="Main entry point",
                )
            ],
            entry_point="src/main.py",
            dependencies=["fastapi", "pydantic"],
        )

        with patch(
            "codebot.agents.backend_dev.instructor"
        ) as mock_instructor:
            mock_client = MagicMock()
            mock_instructor.from_litellm.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_plan

            context = {
                "requirements": {"project_name": "Todo API"},
                "api_spec": None,
                "conventions": "Use Pydantic v2",
            }
            result = await backend_agent.reason(context)
            assert "planned_files" in result
            assert len(result["planned_files"]) > 0


# ---------------------------------------------------------------------------
# act()
# ---------------------------------------------------------------------------


class TestAct:
    """BackendDevAgent.act() generates code, validates with ruff/mypy."""

    async def test_code_generation(self, backend_agent: Any) -> None:
        """act() generates code files via LLM and returns PRAResult."""
        from codebot.agents.backend_dev import (
            CodeGenerationResult,
            GeneratedFile,
        )

        mock_result = CodeGenerationResult(
            files=[
                GeneratedFile(
                    path="src/main.py",
                    content='from fastapi import FastAPI\n\napp = FastAPI()\n\n\n@app.get("/health")\nasync def health() -> dict[str, str]:\n    """Health check."""\n    return {"status": "ok"}\n',
                    purpose="Main entry point",
                )
            ],
            entry_point="src/main.py",
            dependencies=["fastapi"],
            lint_passed=True,
            typecheck_passed=True,
        )

        with (
            patch(
                "codebot.agents.backend_dev.instructor"
            ) as mock_instructor,
            patch(
                "codebot.agents.backend_dev.asyncio.create_subprocess_exec",
                new_callable=AsyncMock,
            ) as mock_subprocess,
        ):
            mock_client = MagicMock()
            mock_instructor.from_litellm.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_result

            # Mock subprocess for ruff and mypy returning success
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = (b"", b"")
            mock_subprocess.return_value = mock_proc

            plan = {
                "planned_files": [{"path": "src/main.py", "purpose": "Entry point"}],
                "entry_point": "src/main.py",
                "dependencies": ["fastapi"],
            }
            result = await backend_agent.act(plan)
            assert isinstance(result, PRAResult)
            assert result.is_complete is True

    async def test_lint_typecheck(self, backend_agent: Any) -> None:
        """act() calls ruff check and mypy --strict on generated code."""
        from codebot.agents.backend_dev import (
            CodeGenerationResult,
            GeneratedFile,
        )

        mock_result = CodeGenerationResult(
            files=[
                GeneratedFile(
                    path="src/main.py",
                    content="import os\n",
                    purpose="Main",
                )
            ],
            entry_point="src/main.py",
            dependencies=[],
            lint_passed=True,
            typecheck_passed=True,
        )

        with (
            patch(
                "codebot.agents.backend_dev.instructor"
            ) as mock_instructor,
            patch(
                "codebot.agents.backend_dev.asyncio.create_subprocess_exec",
                new_callable=AsyncMock,
            ) as mock_subprocess,
        ):
            mock_client = MagicMock()
            mock_instructor.from_litellm.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_result

            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = (b"", b"")
            mock_subprocess.return_value = mock_proc

            plan = {
                "planned_files": [{"path": "src/main.py", "purpose": "Entry point"}],
                "entry_point": "src/main.py",
                "dependencies": [],
            }
            await backend_agent.act(plan)

            # Verify ruff and mypy were called
            calls = [str(c) for c in mock_subprocess.call_args_list]
            call_str = " ".join(calls)
            assert "ruff" in call_str
            assert "mypy" in call_str

    async def test_act_reprompts_on_lint_failure(
        self, backend_agent: Any
    ) -> None:
        """act() re-prompts LLM with lint errors when ruff check fails."""
        from codebot.agents.backend_dev import (
            CodeGenerationResult,
            GeneratedFile,
        )

        good_file = GeneratedFile(
            path="src/main.py",
            content="from fastapi import FastAPI\napp = FastAPI()\n",
            purpose="Main",
        )
        first_result = CodeGenerationResult(
            files=[good_file],
            entry_point="src/main.py",
            dependencies=["fastapi"],
            lint_passed=False,
            typecheck_passed=True,
        )
        second_result = CodeGenerationResult(
            files=[good_file],
            entry_point="src/main.py",
            dependencies=["fastapi"],
            lint_passed=True,
            typecheck_passed=True,
        )

        with (
            patch(
                "codebot.agents.backend_dev.instructor"
            ) as mock_instructor,
            patch(
                "codebot.agents.backend_dev.asyncio.create_subprocess_exec",
                new_callable=AsyncMock,
            ) as mock_subprocess,
        ):
            mock_client = MagicMock()
            mock_instructor.from_litellm.return_value = mock_client
            mock_client.chat.completions.create.side_effect = [
                first_result,
                second_result,
            ]

            # First ruff call fails, second succeeds; mypy always succeeds
            mock_proc_fail = AsyncMock()
            mock_proc_fail.returncode = 1
            mock_proc_fail.communicate.return_value = (
                b"src/main.py:1:1 F401 unused import",
                b"",
            )
            mock_proc_ok = AsyncMock()
            mock_proc_ok.returncode = 0
            mock_proc_ok.communicate.return_value = (b"", b"")
            mock_subprocess.side_effect = [
                mock_proc_fail,  # ruff check fails
                mock_proc_ok,    # ruff format (ok)
                mock_proc_ok,    # mypy (ok, but will re-prompt)
                mock_proc_ok,    # ruff check (retry, ok)
                mock_proc_ok,    # ruff format (retry, ok)
                mock_proc_ok,    # mypy (retry, ok)
            ]

            plan = {
                "planned_files": [{"path": "src/main.py", "purpose": "Entry point"}],
                "entry_point": "src/main.py",
                "dependencies": ["fastapi"],
            }
            result = await backend_agent.act(plan)
            assert result.is_complete is True
            # LLM was called twice (initial + retry)
            assert mock_client.chat.completions.create.call_count >= 2

    async def test_act_reprompts_on_typecheck_failure(
        self, backend_agent: Any
    ) -> None:
        """act() re-prompts LLM with type errors when mypy fails."""
        from codebot.agents.backend_dev import (
            CodeGenerationResult,
            GeneratedFile,
        )

        good_file = GeneratedFile(
            path="src/main.py",
            content="from fastapi import FastAPI\napp = FastAPI()\n",
            purpose="Main",
        )
        first_result = CodeGenerationResult(
            files=[good_file],
            entry_point="src/main.py",
            dependencies=["fastapi"],
            lint_passed=True,
            typecheck_passed=False,
        )
        second_result = CodeGenerationResult(
            files=[good_file],
            entry_point="src/main.py",
            dependencies=["fastapi"],
            lint_passed=True,
            typecheck_passed=True,
        )

        with (
            patch(
                "codebot.agents.backend_dev.instructor"
            ) as mock_instructor,
            patch(
                "codebot.agents.backend_dev.asyncio.create_subprocess_exec",
                new_callable=AsyncMock,
            ) as mock_subprocess,
        ):
            mock_client = MagicMock()
            mock_instructor.from_litellm.return_value = mock_client
            mock_client.chat.completions.create.side_effect = [
                first_result,
                second_result,
            ]

            mock_proc_ok = AsyncMock()
            mock_proc_ok.returncode = 0
            mock_proc_ok.communicate.return_value = (b"", b"")

            mock_proc_mypy_fail = AsyncMock()
            mock_proc_mypy_fail.returncode = 1
            mock_proc_mypy_fail.communicate.return_value = (
                b"src/main.py:2: error: Need type annotation",
                b"",
            )

            mock_subprocess.side_effect = [
                mock_proc_ok,          # ruff check ok
                mock_proc_ok,          # ruff format ok
                mock_proc_mypy_fail,   # mypy fails
                mock_proc_ok,          # ruff check retry
                mock_proc_ok,          # ruff format retry
                mock_proc_ok,          # mypy retry ok
            ]

            plan = {
                "planned_files": [{"path": "src/main.py", "purpose": "Entry point"}],
                "entry_point": "src/main.py",
                "dependencies": ["fastapi"],
            }
            result = await backend_agent.act(plan)
            assert result.is_complete is True
            assert mock_client.chat.completions.create.call_count >= 2


# ---------------------------------------------------------------------------
# _run_lint_check / _run_type_check
# ---------------------------------------------------------------------------


class TestLintAndTypeCheck:
    """BackendDevAgent._run_lint_check and _run_type_check."""

    async def test_run_lint_check_calls_ruff(
        self, backend_agent: Any
    ) -> None:
        """_run_lint_check calls subprocess with 'ruff check --fix'."""
        with patch(
            "codebot.agents.backend_dev.asyncio.create_subprocess_exec",
            new_callable=AsyncMock,
        ) as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = (b"All checks passed!", b"")
            mock_subprocess.return_value = mock_proc

            success, errors = await backend_agent._run_lint_check("/tmp/workspace")
            assert success is True
            assert errors == ""
            call_args = mock_subprocess.call_args
            args = call_args[0] if call_args[0] else []
            assert "ruff" in args
            assert "check" in args

    async def test_run_type_check_calls_mypy(
        self, backend_agent: Any
    ) -> None:
        """_run_type_check calls subprocess with 'mypy --strict'."""
        with patch(
            "codebot.agents.backend_dev.asyncio.create_subprocess_exec",
            new_callable=AsyncMock,
        ) as mock_subprocess:
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = (b"Success: no issues found", b"")
            mock_subprocess.return_value = mock_proc

            success, errors = await backend_agent._run_type_check("/tmp/workspace")
            assert success is True
            assert errors == ""
            call_args = mock_subprocess.call_args
            args = call_args[0] if call_args[0] else []
            assert "mypy" in args
            assert "--strict" in args


# ---------------------------------------------------------------------------
# review()
# ---------------------------------------------------------------------------


class TestReview:
    """BackendDevAgent.review() returns AgentOutput based on validation results."""

    async def test_review_passed_when_all_checks_pass(
        self, backend_agent: Any
    ) -> None:
        """review() returns review_passed=True when lint+type pass."""
        result = PRAResult(
            is_complete=True,
            data={
                "generated_files": {"src/main.py": "app = FastAPI()"},
                "lint_passed": True,
                "typecheck_passed": True,
            },
        )
        output = await backend_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is True

    async def test_review_failed_when_validation_fails(
        self, backend_agent: Any
    ) -> None:
        """review() returns review_passed=False when code fails checks after retries."""
        result = PRAResult(
            is_complete=True,
            data={
                "generated_files": {},
                "lint_passed": False,
                "typecheck_passed": False,
            },
        )
        output = await backend_agent.review(result)
        assert isinstance(output, AgentOutput)
        assert output.review_passed is False
