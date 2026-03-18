"""Three-tier context loading system.

Loads L0 (always-present) and L1 (phase-scoped) context from the filesystem
using async I/O. L2 (on-demand retrieval) is handled separately by the
vector store module.

Filesystem layout expected:

    {project_root}/.codebot/context/
        L0/
            summary.md      -- project name, description, tech stack
            conventions.md  -- coding conventions
            constraints.md  -- non-functional requirements
        L1/
            phases/{phase_name}/requirements.md
            architecture/decisions.md
            schemas/*.md
            api-specs/*.md
            designs/*.md
            test-plans/*.md
            test-results/*.md
            conventions/*.md
"""

from __future__ import annotations

import glob
from pathlib import Path
from typing import ClassVar

import aiofiles
import tiktoken

from codebot.context.models import L0Context, L1Context


class ThreeTierLoader:
    """Loads L0 and L1 context from the project filesystem.

    L0 context is always-present project essentials (capped at ~2500 tokens).
    L1 context is phase-scoped materials selected by agent role.

    Args:
        project_root: Path to the project root directory.
    """

    _ROLE_FILE_PATTERNS: ClassVar[dict[str, list[str]]] = {
        "BACKEND_DEV": [
            "schemas/*.md",
            "api-specs/*.md",
            "architecture/decisions.md",
        ],
        "FRONTEND_DEV": [
            "api-specs/*.md",
            "architecture/decisions.md",
            "designs/*.md",
        ],
        "TESTER": [
            "schemas/*.md",
            "api-specs/*.md",
            "test-plans/*.md",
        ],
        "DEBUGGER": [
            "schemas/*.md",
            "api-specs/*.md",
            "test-results/*.md",
        ],
        "CODE_REVIEWER": [
            "architecture/decisions.md",
            "conventions/*.md",
        ],
        "ARCHITECT": [
            "architecture/*.md",
            "schemas/*.md",
            "api-specs/*.md",
        ],
        "DEFAULT": [
            "architecture/decisions.md",
        ],
    }

    _MAX_L0_TOKENS: ClassVar[int] = 2500

    __slots__ = ("_l0_dir", "_l1_dir", "_project_root")

    def __init__(self, project_root: str | Path) -> None:
        """Initialize the loader with a project root path.

        Args:
            project_root: Path to the project root directory.
        """
        self._project_root = Path(project_root)
        self._l0_dir = self._project_root / ".codebot" / "context" / "L0"
        self._l1_dir = self._project_root / ".codebot" / "context" / "L1"

    async def load_l0(
        self,
        agent_system_prompt: str = "",
        pipeline_phase: str = "",
    ) -> L0Context:
        """Load L0 (always-present) context from the filesystem.

        Reads project summary, conventions, and constraints from
        ``{project_root}/.codebot/context/L0/``. Returns graceful
        defaults when files are missing. Truncates conventions first
        if total content exceeds ~2500 tokens.

        Args:
            agent_system_prompt: System prompt for the current agent.
            pipeline_phase: Current pipeline phase name.

        Returns:
            Populated L0Context with project essentials.
        """
        summary_text = await self._read_file(self._l0_dir / "summary.md")
        conventions_text = await self._read_file(self._l0_dir / "conventions.md")
        constraints_text = await self._read_file(self._l0_dir / "constraints.md")

        # Parse summary.md
        project_name = self._extract_heading(summary_text)
        project_description = self._extract_first_paragraph(summary_text)
        tech_stack = self._extract_bullet_items(summary_text)

        # Parse constraints as list of lines
        constraints = [
            line.strip()
            for line in constraints_text.strip().splitlines()
            if line.strip()
        ]

        # Enforce L0 token cap -- truncate conventions first if needed
        conventions_text = self._enforce_l0_cap(
            project_name=project_name,
            project_description=project_description,
            tech_stack=tech_stack,
            conventions=conventions_text,
            agent_system_prompt=agent_system_prompt,
            pipeline_phase=pipeline_phase,
            constraints=constraints,
        )

        return L0Context(
            project_name=project_name,
            project_description=project_description,
            tech_stack=tech_stack,
            conventions=conventions_text,
            pipeline_phase=pipeline_phase,
            agent_system_prompt=agent_system_prompt,
            constraints=constraints,
        )

    async def load_l1(self, phase: str, agent_role: str) -> L1Context:
        """Load L1 (phase-scoped) context based on phase and agent role.

        Reads phase requirements and role-specific files from
        ``{project_root}/.codebot/context/L1/``.

        Args:
            phase: Pipeline phase name (e.g., ``IMPLEMENTATION``).
            agent_role: Agent role name (e.g., ``BACKEND_DEV``).

        Returns:
            Populated L1Context with phase requirements and role-specific files.
        """
        # Load phase requirements
        phase_req_path = self._l1_dir / "phases" / phase / "requirements.md"
        phase_requirements = await self._read_file(phase_req_path)

        # Load architecture decisions
        arch_decisions_path = self._l1_dir / "architecture" / "decisions.md"
        architecture_decisions = await self._read_file(arch_decisions_path)

        # Determine file patterns for this role
        patterns = self._ROLE_FILE_PATTERNS.get(
            agent_role,
            self._ROLE_FILE_PATTERNS["DEFAULT"],
        )

        # Glob matching files from L1 directory
        related_files: list[str] = []
        for pattern in patterns:
            full_pattern = str(self._l1_dir / pattern)
            matched = sorted(glob.glob(full_pattern))
            for match in matched:
                if match not in related_files:
                    related_files.append(match)

        return L1Context(
            phase_requirements=phase_requirements,
            related_files=related_files,
            architecture_decisions=architecture_decisions,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _read_file(path: Path) -> str:
        """Read a file asynchronously, returning empty string if missing.

        Args:
            path: Path to the file.

        Returns:
            File contents or empty string if the file doesn't exist.
        """
        if not path.is_file():
            return ""
        async with aiofiles.open(path, mode="r", encoding="utf-8") as f:
            return await f.read()

    @staticmethod
    def _extract_heading(text: str) -> str:
        """Extract the first ``# heading`` from markdown text.

        Args:
            text: Markdown text.

        Returns:
            Heading text (without ``#`` prefix), or empty string.
        """
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
        return ""

    @staticmethod
    def _extract_first_paragraph(text: str) -> str:
        """Extract the first non-heading paragraph from markdown text.

        Args:
            text: Markdown text.

        Returns:
            First paragraph text, or empty string.
        """
        lines = text.splitlines()
        paragraph_lines: list[str] = []
        in_paragraph = False

        for line in lines:
            stripped = line.strip()
            # Skip headings
            if stripped.startswith("#"):
                if in_paragraph:
                    break
                continue
            # Skip empty lines before paragraph
            if not stripped:
                if in_paragraph:
                    break
                continue
            # Collect paragraph lines
            in_paragraph = True
            paragraph_lines.append(stripped)

        return " ".join(paragraph_lines)

    @staticmethod
    def _extract_bullet_items(text: str) -> list[str]:
        """Extract bulleted list items from markdown text.

        Looks for lines starting with ``-`` or ``*``.

        Args:
            text: Markdown text.

        Returns:
            List of item texts (stripped of bullet prefix).
        """
        items: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                items.append(stripped[2:].strip())
            elif stripped.startswith("* "):
                items.append(stripped[2:].strip())
        return items

    def _enforce_l0_cap(
        self,
        *,
        project_name: str,
        project_description: str,
        tech_stack: list[str],
        conventions: str,
        agent_system_prompt: str,
        pipeline_phase: str,
        constraints: list[str],
    ) -> str:
        """Truncate conventions if combined L0 content exceeds token cap.

        Args:
            project_name: Project name.
            project_description: Project description.
            tech_stack: List of tech stack items.
            conventions: Conventions text (may be truncated).
            agent_system_prompt: Agent system prompt.
            pipeline_phase: Pipeline phase.
            constraints: List of constraints.

        Returns:
            Conventions text, potentially truncated to fit within the cap.
        """
        encoder = tiktoken.get_encoding("cl100k_base")

        # Build combined text excluding conventions for base count
        base_parts = [
            project_name,
            project_description,
            " ".join(tech_stack),
            agent_system_prompt,
            pipeline_phase,
            " ".join(constraints),
        ]
        base_text = "\n".join(base_parts)
        base_tokens = len(encoder.encode(base_text))

        # Check if conventions fit within budget
        conventions_tokens = len(encoder.encode(conventions))
        total = base_tokens + conventions_tokens

        if total <= self._MAX_L0_TOKENS:
            return conventions

        # Truncate conventions to fit
        available = max(0, self._MAX_L0_TOKENS - base_tokens)
        if available == 0:
            return ""

        # Encode and truncate
        convention_token_ids = encoder.encode(conventions)
        truncated_ids = convention_token_ids[:available]
        return encoder.decode(truncated_ids)
