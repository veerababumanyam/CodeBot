"""FailureAnalyzer -- parses stack traces and identifies root causes via LLM.

Takes test failure details and source code, uses LLM to identify the root
cause and suggest a fix approach. Produces structured ``FailureAnalysis``
output via instructor + LiteLLM.
"""

from __future__ import annotations

import logging

import instructor
import litellm
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FailureAnalysis(BaseModel):
    """Structured output from root cause analysis.

    Attributes:
        root_cause: Identified root cause of the failure.
        affected_files: File paths that need modification.
        confidence: Analysis confidence (0.0 to 1.0).
        suggested_approach: How to fix the issue.
        failure_category: Category of the failure.
    """

    root_cause: str = Field(description="Identified root cause of the failure")
    affected_files: list[str] = Field(description="File paths that need modification")
    confidence: float = Field(ge=0.0, le=1.0, description="Analysis confidence")
    suggested_approach: str = Field(description="How to fix the issue")
    failure_category: str = Field(
        description="syntax_error/logic_error/import_error/type_error/test_setup/other"
    )


class FailureAnalyzer:
    """Analyzes test failures to identify root causes via LLM.

    Uses instructor + LiteLLM for structured analysis output.
    Parses stack traces, reads affected source code, and produces
    a structured FailureAnalysis with root cause, affected files,
    and suggested fix approach.
    """

    def __init__(self, model: str = "anthropic/claude-sonnet-4") -> None:
        """Initialize analyzer with LLM model.

        Args:
            model: LiteLLM model identifier.
        """
        self.client = instructor.from_litellm(litellm.completion)
        self.model = model

    async def analyze(
        self,
        failure_details: list[dict],  # noqa: ANN401
        source_files: dict[str, str],
    ) -> FailureAnalysis:
        """Analyze test failures: parse stack traces, identify root cause via LLM.

        Args:
            failure_details: List of dicts with nodeid, outcome, longrepr.
            source_files: Dict of file_path -> file_content.

        Returns:
            FailureAnalysis with root cause, affected files, and fix approach.
        """
        # Format failure details
        failures_str = "\n\n".join(
            f"Test: {f.get('nodeid', 'unknown')}\n"
            f"Outcome: {f.get('outcome', 'unknown')}\n"
            f"Error:\n{f.get('longrepr', 'No details')}"
            for f in failure_details
        )

        # Format source files
        source_str = "\n\n".join(
            f"### {path}\n```python\n{content}\n```"
            for path, content in source_files.items()
        )

        user_msg = (
            f"Analyze these test failures and identify the root cause.\n\n"
            f"## Test Failures\n{failures_str}\n\n"
            f"## Source Code\n{source_str}\n\n"
            f"Identify the root cause, which files need fixing, and how to fix them."
        )

        analysis: FailureAnalysis = self.client.chat.completions.create(
            model=self.model,
            response_model=FailureAnalysis,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior software debugger. Analyze test failures, "
                        "identify root causes from stack traces and source code, and "
                        "suggest targeted fixes. Be precise about which files need "
                        "changes and what the fix should be."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
            max_retries=2,
        )

        return analysis
