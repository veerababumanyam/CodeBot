"""Google Gemini CLI adapter.

Builds command-line invocations for the Google Gemini CLI tool,
supporting JSON output, working directory specification, and
max token configuration.
"""

from __future__ import annotations

from codebot.cli_agents.adapters.base import BaseCLIAdapter
from codebot.cli_agents.models import CLITask


class GeminiCLIAdapter(BaseCLIAdapter):
    """Adapter for the Google Gemini CLI (``gemini`` binary).

    Generates commands using ``--json`` for structured output with
    working directory and token limits.
    """

    binary: str = "gemini"

    def build_command(self, task: CLITask, worktree_path: str) -> list[str]:
        """Build a Gemini CLI command.

        Args:
            task: The CLI task describing the work to perform.
            worktree_path: Absolute path to the worktree directory.

        Returns:
            Command list starting with ``gemini`` and including all flags.
        """
        cmd: list[str] = ["gemini", "--json"]

        cmd.extend(["--cwd", worktree_path])

        if task.max_tokens:
            cmd.extend(["--max-tokens", str(task.max_tokens)])

        cmd.append(task.prompt)
        return cmd
