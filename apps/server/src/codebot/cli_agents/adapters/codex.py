"""OpenAI Codex CLI adapter.

Builds command-line invocations for the OpenAI Codex CLI tool,
supporting quiet mode, JSON output, tool selection, and working
directory specification.
"""

from __future__ import annotations

from codebot.cli_agents.adapters.base import BaseCLIAdapter
from codebot.cli_agents.models import CLITask


class CodexAdapter(BaseCLIAdapter):
    """Adapter for the OpenAI Codex CLI (``codex`` binary).

    Generates commands using ``--quiet`` and ``--json`` flags for
    non-interactive, structured output.
    """

    binary: str = "codex"

    def build_command(self, task: CLITask, worktree_path: str) -> list[str]:
        """Build a Codex CLI command.

        Args:
            task: The CLI task describing the work to perform.
            worktree_path: Absolute path to the worktree directory.

        Returns:
            Command list starting with ``codex`` and including all flags.
        """
        cmd: list[str] = ["codex", "--quiet", "--json"]

        if task.allowed_tools:
            cmd.extend(["--tools", ",".join(task.allowed_tools)])

        cmd.extend(["--cwd", worktree_path])
        cmd.append(task.prompt)
        return cmd
