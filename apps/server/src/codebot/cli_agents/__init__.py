"""CLI agent integration package.

Provides adapters for delegating coding tasks to external CLI tools
(Claude Code, OpenAI Codex, Google Gemini) and the runner that
orchestrates worktree acquisition, port allocation, execution, and
security scanning.
"""

from codebot.cli_agents.adapters.base import BaseCLIAdapter
from codebot.cli_agents.adapters.claude_code import ClaudeCodeAdapter
from codebot.cli_agents.adapters.codex import CodexAdapter
from codebot.cli_agents.adapters.gemini import GeminiCLIAdapter
from codebot.cli_agents.runner import CLIAgentRunner

__all__ = [
    "BaseCLIAdapter",
    "CLIAgentRunner",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "GeminiCLIAdapter",
]
