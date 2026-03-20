"""Claude Code CLI adapter.

Builds command-line invocations for Anthropic's Claude Code CLI tool,
supporting ``--print`` mode with JSON output, allowed tools, max tokens,
and file context injection.
"""

from __future__ import annotations

from codebot.cli_agents.adapters.base import BaseCLIAdapter
from codebot.cli_agents.models import CLITask


class ClaudeCodeAdapter(BaseCLIAdapter):
    """Adapter for the Claude Code CLI (``claude`` binary).

    Generates commands using ``--print`` mode with ``--output-format json``
    for structured, non-interactive output.
    """

    binary: str = "claude"

    def build_command(self, task: CLITask, worktree_path: str) -> list[str]:
        """Build a Claude Code CLI command.

        Args:
            task: The CLI task describing the work to perform.
            worktree_path: Absolute path to the worktree directory.

        Returns:
            Command list starting with ``claude`` and including all flags.
        """
        cmd: list[str] = ["claude", "--print", "--output-format", "json"]

        if task.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(task.allowed_tools)])

        if task.max_tokens:
            cmd.extend(["--max-tokens", str(task.max_tokens)])

        for file_path in task.files_context:
            cmd.extend(["--file", file_path])

        cmd.append(task.prompt)
        return cmd
