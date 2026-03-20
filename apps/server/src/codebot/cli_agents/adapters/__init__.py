"""CLI agent adapters for external coding tools.

Exports all adapter classes and the abstract base.
"""

from codebot.cli_agents.adapters.base import BaseCLIAdapter
from codebot.cli_agents.adapters.claude_code import ClaudeCodeAdapter
from codebot.cli_agents.adapters.codex import CodexAdapter
from codebot.cli_agents.adapters.gemini import GeminiCLIAdapter

__all__ = [
    "BaseCLIAdapter",
    "ClaudeCodeAdapter",
    "CodexAdapter",
    "GeminiCLIAdapter",
]
