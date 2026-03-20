"""Health checker for CLI agent processes and binaries.

Provides lightweight checks to determine if a CLI process is still
running and if a binary is available on PATH.
"""

from __future__ import annotations

import asyncio
import shutil


class HealthChecker:
    """Checks health of CLI agent processes and binary availability.

    Used to verify that a spawned CLI tool process is still alive
    and that required binaries are installed.
    """

    async def check_process(
        self, proc: asyncio.subprocess.Process
    ) -> bool:
        """Check whether a subprocess is still running.

        Args:
            proc: The subprocess to check.

        Returns:
            True if the process is still running (returncode is None).
        """
        return proc.returncode is None

    async def check_binary(self, binary: str) -> bool:
        """Check whether a binary is available on PATH.

        Args:
            binary: Name of the binary to look up.

        Returns:
            True if the binary is found on PATH.
        """
        return shutil.which(binary) is not None
