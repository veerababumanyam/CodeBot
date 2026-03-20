"""BackendDevAgent -- generates Python/FastAPI code from extracted requirements.

Implements the PRA cognitive cycle:
- perceive(): Assembles requirements, API spec, conventions from shared state
- reason(): Uses LLM to plan code structure (files, signatures, models)
- act(): Generates code via LLM, validates with ruff + mypy, re-prompts on failure
- review(): Self-review checking lint and typecheck results

Uses instructor + LiteLLM for structured output extraction.
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import instructor
import litellm
from agent_sdk.agents.base import AgentInput, AgentOutput, BaseAgent, PRAResult
from agent_sdk.models.enums import AgentType
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<role>
You are a senior Python backend developer specializing in FastAPI applications.
You write production-quality, well-structured, and thoroughly tested code.
</role>

<responsibilities>
- Generate complete, runnable Python/FastAPI code from requirements
- Follow project conventions and style guidelines strictly
- Create proper Pydantic v2 request/response models
- Implement comprehensive error handling with appropriate HTTP status codes
- Use async/await for all endpoint handlers and database operations
- Write Google-style docstrings for all public functions and classes
</responsibilities>

<output_format>
Generate complete file contents with all imports, type hints, and docstrings.
Each file should be self-contained and ready to run after dependency installation.
</output_format>

<constraints>
- Use Pydantic v2 (BaseModel with model_config, not class Config)
- Use async def for all route handlers
- Use Google-style docstrings
- Include comprehensive error handling (try/except with specific exceptions)
- Follow PEP 8 and ruff-compatible formatting
- Use type hints for all function parameters and return values
- Do NOT use deprecated APIs or patterns
</constraints>
"""

# ---------------------------------------------------------------------------
# Pydantic models for structured LLM output
# ---------------------------------------------------------------------------


class GeneratedFile(BaseModel):
    """A single generated source file."""

    path: str = Field(description="Relative file path, e.g. src/main.py")
    content: str = Field(description="Complete file content")
    purpose: str = Field(description="What this file does")


class CodeGenerationPlan(BaseModel):
    """Plan for code generation -- file list and structure."""

    files: list[GeneratedFile]
    entry_point: str = Field(description="Main entry file path")
    dependencies: list[str] = Field(description="Required pip packages")


class CodeGenerationResult(BaseModel):
    """Result of code generation with validation status."""

    files: list[GeneratedFile]
    entry_point: str
    dependencies: list[str]
    lint_passed: bool
    typecheck_passed: bool


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------

_MAX_LINT_RETRIES = 2


@dataclass(slots=True, kw_only=True)
class BackendDevAgent(BaseAgent):
    """Generates Python/FastAPI code from extracted requirements.

    Uses the PRA cognitive cycle to:
    1. Perceive requirements and conventions from shared state
    2. Reason about code structure using LLM
    3. Act by generating code and validating with ruff + mypy
    4. Review the generation results
    """

    agent_type: AgentType = field(default=AgentType.BACKEND_DEV, init=False)

    async def _initialize(self, agent_input: AgentInput) -> None:
        """Load system prompt and prepare workspace.

        Args:
            agent_input: The task input for initialization context.
        """
        # No additional initialization needed; workspace created in act()

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Assemble context: requirements, API spec, coding conventions.

        Args:
            agent_input: The task input with context tiers.

        Returns:
            Assembled context dict with requirements, api_spec, conventions,
            and optionally review_comments from a QA re-route.
        """
        context: dict[str, Any] = {
            "requirements": agent_input.shared_state.get("requirements"),
            "api_spec": agent_input.shared_state.get("api_spec"),
            "conventions": agent_input.context_tiers.get("l0", {}).get("conventions")
            if isinstance(agent_input.context_tiers.get("l0"), dict)
            else None,
        }

        # Include review comments from QA re-route if present
        review_comments = agent_input.shared_state.get("review_comments")
        if review_comments is not None:
            context["review_comments"] = review_comments

        return context

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Use LLM to plan code structure from requirements.

        Args:
            context: Assembled context from perceive().

        Returns:
            Action plan dict with planned_files, entry_point, dependencies.
        """
        client = instructor.from_litellm(litellm.completion)

        requirements_str = str(context.get("requirements", {}))
        api_spec_str = str(context.get("api_spec", {}))
        conventions_str = str(context.get("conventions", ""))

        user_msg = (
            f"Plan the code structure for this project.\n\n"
            f"Requirements:\n{requirements_str}\n\n"
            f"API Spec:\n{api_spec_str}\n\n"
            f"Conventions:\n{conventions_str}"
        )

        plan: CodeGenerationPlan = client.chat.completions.create(
            model="anthropic/claude-sonnet-4",
            response_model=CodeGenerationPlan,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_retries=3,
        )

        return {
            "planned_files": [{"path": f.path, "purpose": f.purpose} for f in plan.files],
            "entry_point": plan.entry_point,
            "dependencies": plan.dependencies,
        }

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Generate code files via LLM, validate with ruff check + mypy.

        Writes generated files to a temporary workspace directory, runs
        lint and type checks, and re-prompts the LLM on failures up to
        _MAX_LINT_RETRIES times.

        Args:
            plan: Action plan from reason().

        Returns:
            PRAResult with generated files and validation status.
        """
        client = instructor.from_litellm(litellm.completion)

        workspace = tempfile.mkdtemp(prefix="codebot_backend_")

        planned_files_str = str(plan.get("planned_files", []))
        user_msg = (
            f"Generate complete Python/FastAPI code files based on this plan:\n\n"
            f"Files to generate:\n{planned_files_str}\n\n"
            f"Entry point: {plan.get('entry_point', 'src/main.py')}\n"
            f"Dependencies: {plan.get('dependencies', [])}"
        )

        lint_errors = ""
        type_errors = ""
        lint_passed = False
        type_passed = False
        gen_result: CodeGenerationResult | None = None

        for attempt in range(_MAX_LINT_RETRIES + 1):
            if attempt > 0:
                # Re-prompt with error feedback
                user_msg = (
                    f"The previous code had issues. Fix them and regenerate.\n\n"
                    f"Lint errors:\n{lint_errors}\n\n"
                    f"Type errors:\n{type_errors}\n\n"
                    f"Original plan:\n{planned_files_str}"
                )

            gen_result = client.chat.completions.create(
                model="anthropic/claude-sonnet-4",
                response_model=CodeGenerationResult,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                max_retries=3,
            )

            # Write generated files to workspace
            for gen_file in gen_result.files:
                file_path = Path(workspace) / gen_file.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(gen_file.content)

            # Run lint check
            lint_passed, lint_errors = await self._run_lint_check(workspace)

            # Run type check
            type_passed, type_errors = await self._run_type_check(workspace)

            if lint_passed and type_passed:
                break

        assert gen_result is not None  # noqa: S101

        generated_files = {f.path: f.content for f in gen_result.files}
        return PRAResult(
            is_complete=True,
            data={
                "generated_files": generated_files,
                "entry_point": gen_result.entry_point,
                "dependencies": gen_result.dependencies,
                "lint_passed": lint_passed,
                "typecheck_passed": type_passed,
                "workspace": workspace,
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Self-review: check whether generated code passed lint and type checks.

        Args:
            result: The PRAResult from the final act() iteration.

        Returns:
            AgentOutput with review_passed indicating acceptance.
        """
        data = result.data
        lint_ok = data.get("lint_passed", False)
        type_ok = data.get("typecheck_passed", False)
        review_passed = bool(lint_ok and type_ok)

        return AgentOutput(
            task_id=self.agent_id,
            state_updates={
                "backend_dev.generated_files": data.get("generated_files", {}),
                "backend_dev.entry_point": data.get("entry_point", ""),
                "backend_dev.dependencies": data.get("dependencies", []),
                "backend_dev.lint_passed": lint_ok,
                "backend_dev.typecheck_passed": type_ok,
            },
            review_passed=review_passed,
        )

    async def _run_lint_check(self, workspace: str) -> tuple[bool, str]:
        """Run ruff check --fix on the workspace directory.

        Args:
            workspace: Path to the workspace directory.

        Returns:
            Tuple of (success, error_output).
        """
        proc = await asyncio.create_subprocess_exec(
            "ruff",
            "check",
            "--fix",
            workspace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        success = proc.returncode == 0
        errors = stdout.decode() + stderr.decode() if not success else ""
        return success, errors

    async def _run_type_check(self, workspace: str) -> tuple[bool, str]:
        """Run mypy --strict on the workspace directory.

        Args:
            workspace: Path to the workspace directory.

        Returns:
            Tuple of (success, error_output).
        """
        proc = await asyncio.create_subprocess_exec(
            "mypy",
            "--strict",
            workspace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        success = proc.returncode == 0
        errors = stdout.decode() + stderr.decode() if not success else ""
        return success, errors
