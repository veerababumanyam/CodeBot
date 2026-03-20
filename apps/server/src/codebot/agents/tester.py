"""TesterAgent -- generates and executes tests against generated code.

Implements the PRA cognitive cycle:
- perceive(): Reads generated source files and requirements from shared state
- reason(): Uses LLM to plan test structure (unit tests + integration tests)
- act(): Generates test files via LLM, writes to workspace, runs TestRunner,
         parses results with TestResultParser
- review(): Sets test_results and tests_passing in state_updates;
            routes failures to Debugger via test_failures

Uses instructor + LiteLLM for structured test generation output.
"""

from __future__ import annotations

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

from codebot.testing.parser import TestResultParser
from codebot.testing.runner import TestRunner

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
<role>
You are a senior Python test engineer specializing in pytest test suites.
You write thorough, deterministic, non-flaky tests.
</role>

<responsibilities>
- Generate pytest unit tests targeting >= 80% line coverage
- Generate integration tests using httpx.AsyncClient for FastAPI endpoints
- Ensure each test is independent and deterministic
- Use fixtures for setup/teardown
- Mock all external dependencies
- Never depend on test execution order
</responsibilities>

<output_format>
Generate complete test files with all imports, fixtures, and test functions.
Each file must be self-contained and runnable with pytest.
</output_format>

<constraints>
- Use pytest as the test framework
- Use httpx.AsyncClient for API integration tests
- Use unittest.mock for mocking
- Include docstrings for test functions explaining what they verify
- Each test must be independent and deterministic (anti-flakiness)
- Use fixtures for shared setup (not global state)
- Assert specific values, not just truthiness
</constraints>
"""

# ---------------------------------------------------------------------------
# Pydantic models for structured test generation
# ---------------------------------------------------------------------------


class GeneratedTest(BaseModel):
    """A single generated test file."""

    path: str = Field(
        description="Test file path relative to workspace, e.g. tests/test_main.py"
    )
    content: str = Field(description="Complete test file content")
    test_type: str = Field(description="unit or integration")


class TestGenerationPlan(BaseModel):
    """Plan for test generation -- unit and integration test files."""

    unit_tests: list[GeneratedTest]
    integration_tests: list[GeneratedTest]
    conftest: str | None = Field(
        default=None, description="Shared conftest.py content if needed"
    )


# ---------------------------------------------------------------------------
# Agent implementation
# ---------------------------------------------------------------------------

_COVERAGE_TARGET = 80


@dataclass(slots=True, kw_only=True)
class TesterAgent(BaseAgent):
    """Generates unit and integration tests, executes them, and parses results.

    Uses the PRA cognitive cycle to:
    1. Perceive generated source files from shared state
    2. Reason about test structure using LLM
    3. Act by generating tests, running them, and parsing results
    4. Review test results and route failures to Debugger
    """

    agent_type: AgentType = field(default=AgentType.TESTER, init=False)
    coverage_target: int = _COVERAGE_TARGET

    async def _initialize(self, agent_input: AgentInput) -> None:
        """Prepare for test generation.

        Args:
            agent_input: The task input for initialization context.
        """
        # No additional initialization needed

    async def perceive(self, agent_input: AgentInput) -> dict[str, Any]:
        """Read generated source files and requirements from shared state.

        Args:
            agent_input: The task input with shared state.

        Returns:
            Dict with source_files, requirements, and workspace_path.
        """
        source_files = agent_input.shared_state.get(
            "backend_dev.generated_files", {}
        )
        requirements = agent_input.shared_state.get("requirements", {})
        workspace_path = agent_input.shared_state.get(
            "backend_dev.workspace", tempfile.gettempdir()
        )

        return {
            "source_files": source_files,
            "requirements": requirements,
            "workspace_path": workspace_path,
        }

    async def reason(self, context: dict[str, Any]) -> dict[str, Any]:
        """Call LLM to plan test structure (unit tests + integration tests).

        Args:
            context: Assembled context from perceive().

        Returns:
            Action plan dict with test_plan and workspace_path.
        """
        client = instructor.from_litellm(litellm.completion)

        source_files = context.get("source_files", {})
        requirements = context.get("requirements", {})

        file_contents = "\n\n".join(
            f"### {path}\n```python\n{content}\n```"
            for path, content in source_files.items()
        )
        requirements_str = str(requirements)

        user_msg = (
            f"Generate a comprehensive test suite for this code.\n\n"
            f"Source files:\n{file_contents}\n\n"
            f"Requirements:\n{requirements_str}\n\n"
            f"Coverage target: >= {self.coverage_target}% line coverage.\n\n"
            f"Generate pytest unit tests and httpx.AsyncClient integration tests."
        )

        test_plan: TestGenerationPlan = client.chat.completions.create(
            model="anthropic/claude-sonnet-4",
            response_model=TestGenerationPlan,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_retries=3,
        )

        return {
            "test_plan": test_plan,
            "workspace_path": context.get("workspace_path", tempfile.gettempdir()),
        }

    async def act(self, plan: dict[str, Any]) -> PRAResult:
        """Generate test files, write to workspace, run tests, parse results.

        Writes generated test files to the workspace directory, then
        executes them via TestRunner with pytest-json-report and coverage.
        Parses results with TestResultParser.

        Args:
            plan: Action plan from reason() with test_plan and workspace_path.

        Returns:
            PRAResult with test results and coverage data.
        """
        test_plan: TestGenerationPlan = plan["test_plan"]
        workspace = plan.get("workspace_path", tempfile.gettempdir())

        # Write generated test files to workspace
        all_tests = list(test_plan.unit_tests) + list(test_plan.integration_tests)
        for test_file in all_tests:
            file_path = Path(workspace) / test_file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(test_file.content)

        # Write conftest if provided
        if test_plan.conftest:
            conftest_path = Path(workspace) / "tests" / "conftest.py"
            conftest_path.parent.mkdir(parents=True, exist_ok=True)
            conftest_path.write_text(test_plan.conftest)

        # Execute tests via TestRunner
        runner = TestRunner()
        test_report, coverage_data = await runner.run(workspace)

        # Parse results
        parsed = TestResultParser.parse(test_report, coverage_data)

        return PRAResult(
            is_complete=True,
            data={
                "test_results": {
                    "total": parsed.total,
                    "passed": parsed.passed,
                    "failed": parsed.failed,
                    "errors": parsed.errors,
                    "skipped": parsed.skipped,
                    "coverage_percent": parsed.coverage_percent,
                    "all_passed": parsed.all_passed,
                    "failure_details": parsed.failure_details,
                    "duration_seconds": parsed.duration_seconds,
                },
                "tests_passing": parsed.all_passed,
                "test_failures": parsed.failure_details if not parsed.all_passed else [],
            },
        )

    async def review(self, result: PRAResult) -> AgentOutput:
        """Set test_results and tests_passing in state_updates.

        When tests fail, includes test_failures for the Debugger agent
        to consume from shared state.

        Args:
            result: PRAResult from act() with test execution data.

        Returns:
            AgentOutput with test results in state_updates.
        """
        data = result.data
        tests_passing = bool(data.get("tests_passing", False))
        test_failures = data.get("test_failures", [])

        state_updates: dict[str, Any] = {
            "test_results": data.get("test_results", {}),
            "tests_passing": tests_passing,
        }

        if not tests_passing and test_failures:
            state_updates["test_failures"] = test_failures

        return AgentOutput(
            task_id=self.agent_id,
            state_updates=state_updates,
            review_passed=tests_passing,
        )
