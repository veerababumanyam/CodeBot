"""Abstract base class for CLI agent adapters.

All adapters inherit from :class:`BaseCLIAdapter` and implement
``build_command()`` to generate the correct CLI invocation for
their respective tool (Claude Code, Codex, Gemini).
"""

from __future__ import annotations

import os
import shutil
from abc import ABC, abstractmethod

from codebot.cli_agents.models import AdapterInfo, CLITask


class BaseCLIAdapter(ABC):
    """Abstract base for CLI agent adapters.

    Subclasses must set the ``binary`` class attribute and implement
    ``build_command()``.  ``build_env()`` and ``check_available()`` are
    provided with sensible defaults.

    Attributes:
        binary: Name of the CLI binary this adapter wraps.
    """

    binary: str

    @abstractmethod
    def build_command(self, task: CLITask, worktree_path: str) -> list[str]:
        """Build the command-line invocation for the adapter's tool.

        Args:
            task: The CLI task describing the work to perform.
            worktree_path: Absolute path to the worktree directory.

        Returns:
            List of command-line arguments (first element is the binary).
        """
        ...

    def build_env(
        self, worktree_path: str, ports: dict[str, int]
    ) -> dict[str, str]:
        """Build environment variables for the CLI process.

        Sets ``CODEBOT_WORKTREE`` and ``PORT_<SERVICE>`` variables so the
        CLI tool and any spawned processes know their isolation context.

        Args:
            worktree_path: Absolute path to the worktree directory.
            ports: Mapping of service name to allocated port number.

        Returns:
            A copy of the current environment with worktree/port vars added.
        """
        env = os.environ.copy()
        env["CODEBOT_WORKTREE"] = worktree_path
        for service, port in ports.items():
            env[f"PORT_{service.upper()}"] = str(port)
        return env

    async def check_available(self) -> bool:
        """Check whether the adapter's binary is available on PATH.

        Returns:
            True if the binary is found, False otherwise.
        """
        return shutil.which(self.binary) is not None

    async def get_info(self) -> AdapterInfo:
        """Return metadata about this adapter and its availability.

        Returns:
            An :class:`AdapterInfo` with name, binary, and availability.
        """
        available = await self.check_available()
        return AdapterInfo(
            name=self.__class__.__name__,
            binary=self.binary,
            available=available,
        )
