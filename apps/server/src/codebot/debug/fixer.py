"""FixGenerator -- generates targeted code patches via LLM.

Takes a ``FailureAnalysis`` and source files, uses LLM to generate
targeted fix proposals as ``FixProposal`` objects. Can also apply
the fixes to a workspace directory.
"""

from __future__ import annotations

import logging
from pathlib import Path

import instructor
import litellm
from pydantic import BaseModel, Field

from codebot.debug.analyzer import FailureAnalysis

logger = logging.getLogger(__name__)


class FixProposal(BaseModel):
    """A targeted code patch for a specific file.

    Attributes:
        file_path: Path to the file to fix (relative to workspace).
        original_content: Content before the fix.
        fixed_content: Content after the fix.
        hypothesis: What this fix is trying to resolve.
        diff_lines: Number of lines changed.
    """

    file_path: str
    original_content: str
    fixed_content: str
    hypothesis: str = Field(description="What this fix is trying to resolve")
    diff_lines: int = Field(description="Number of lines changed")


class FixGenerator:
    """Generates targeted code patches based on failure analysis.

    Uses instructor + LiteLLM to produce structured fix proposals.
    Each proposal targets a specific file with before/after content
    and a hypothesis explaining what the fix addresses.
    """

    def __init__(self, model: str = "anthropic/claude-sonnet-4") -> None:
        """Initialize generator with LLM model.

        Args:
            model: LiteLLM model identifier.
        """
        self.client = instructor.from_litellm(litellm.completion)
        self.model = model

    async def generate(
        self,
        analysis: FailureAnalysis,
        source_files: dict[str, str],
    ) -> list[FixProposal]:
        """Generate targeted code patches based on failure analysis.

        Args:
            analysis: FailureAnalysis with root cause and affected files.
            source_files: Dict of file_path -> file_content.

        Returns:
            List of FixProposal objects with targeted patches.
        """
        # Format source files relevant to the analysis
        relevant_source = "\n\n".join(
            f"### {path}\n```python\n{content}\n```"
            for path, content in source_files.items()
            if path in analysis.affected_files or len(source_files) <= 5
        )

        user_msg = (
            f"Generate a targeted fix for this issue.\n\n"
            f"## Root Cause\n{analysis.root_cause}\n\n"
            f"## Suggested Approach\n{analysis.suggested_approach}\n\n"
            f"## Affected Files\n{', '.join(analysis.affected_files)}\n\n"
            f"## Source Code\n{relevant_source}\n\n"
            f"For each affected file, provide the complete fixed file content."
        )

        fixes: list[FixProposal] = self.client.chat.completions.create(
            model=self.model,
            response_model=list[FixProposal],
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior software engineer fixing bugs. "
                        "Generate minimal, targeted fixes. Change only what is "
                        "necessary to resolve the issue. Preserve all existing "
                        "functionality and code style."
                    ),
                },
                {"role": "user", "content": user_msg},
            ],
            max_retries=2,
        )

        return fixes

    async def apply(
        self,
        fixes: list[FixProposal],
        workspace: str,
    ) -> None:
        """Write fixed content to workspace files.

        Creates parent directories as needed. Each fix's ``fixed_content``
        is written to ``workspace/fix.file_path``.

        Args:
            fixes: List of FixProposal objects to apply.
            workspace: Path to the workspace directory.
        """
        for fix in fixes:
            file_path = Path(workspace) / fix.file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(fix.fixed_content)
            logger.info("Applied fix to %s (%d lines changed)", fix.file_path, fix.diff_lines)
