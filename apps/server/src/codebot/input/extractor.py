"""Requirement extraction from natural language and structured input.

Uses instructor + LiteLLM for structured LLM output with automatic
Pydantic validation and retry on schema mismatch.
"""

from __future__ import annotations

import instructor
import litellm

from codebot.input.models import ExtractedRequirements


class RequirementExtractor:
    """Extract structured requirements from user input using LLM.

    The extractor accepts natural language, JSON, YAML, or Markdown input
    and returns a validated ``ExtractedRequirements`` Pydantic model.

    Attributes:
        model: LiteLLM model identifier (e.g. ``anthropic/claude-sonnet-4``).
        client: instructor-wrapped async LiteLLM client.
    """

    def __init__(self, model: str = "anthropic/claude-sonnet-4") -> None:
        self.model = model
        self.client = instructor.from_litellm(litellm.acompletion)

    async def extract(self, user_input: str) -> ExtractedRequirements:
        """Extract structured requirements from user input.

        Args:
            user_input: Natural language description, JSON, YAML, or Markdown
                containing project requirements.

        Returns:
            Validated ExtractedRequirements with functional requirements,
            NFRs, constraints, and ambiguities.
        """
        input_format = self._detect_format(user_input)

        format_hint = ""
        if input_format != "natural_language":
            format_hint = f"\n\nThe input appears to be in {input_format} format."

        result: ExtractedRequirements = await self.client.chat.completions.create(
            model=self.model,
            response_model=ExtractedRequirements,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior requirements analyst. Extract structured "
                        "software requirements from the user's project description. "
                        "Be thorough: identify functional requirements, non-functional "
                        "requirements, constraints, and testable acceptance criteria. "
                        "Flag any ambiguities that need clarification. "
                        "Assign confidence scores (0-1) to each requirement."
                        f"{format_hint}"
                    ),
                },
                {"role": "user", "content": user_input},
            ],
            max_retries=3,
        )
        return result

    @staticmethod
    def _detect_format(input_text: str) -> str:
        """Detect whether input is plain text, markdown, JSON, or YAML.

        Args:
            input_text: The raw user input string.

        Returns:
            One of "json", "yaml", "markdown", or "natural_language".
        """
        stripped = input_text.strip()
        if stripped.startswith("{"):
            return "json"
        if stripped.startswith("---") or ":\n" in stripped[:200]:
            return "yaml"
        if stripped.startswith("#") or "## " in stripped[:200]:
            return "markdown"
        return "natural_language"
