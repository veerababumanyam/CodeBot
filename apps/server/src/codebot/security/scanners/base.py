"""Abstract base class for security scanner adapters.

Every scanner (Semgrep, Trivy, Gitleaks) inherits from ``BaseScanner``
and normalizes its CLI output into a ``ScanResult``.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

from codebot.security.models import ScanResult


class BaseScanner(ABC):
    """Abstract base for all security scanner adapters.

    Subclasses must implement :meth:`scan` to run their CLI tool and
    parse output into a :class:`ScanResult`.
    """

    @abstractmethod
    async def scan(self, project_path: str) -> ScanResult:
        """Run the scanner against *project_path* and return findings."""
        ...

    async def _run_cli(
        self, cmd: list[str], timeout: int = 300
    ) -> tuple[str, str, int]:
        """Run a CLI command asynchronously with timeout.

        Args:
            cmd: Command and arguments to execute.
            timeout: Maximum seconds to wait before killing the process.

        Returns:
            Tuple of (stdout, stderr, returncode).

        Raises:
            asyncio.TimeoutError: If the process exceeds *timeout*.
        """
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return stdout.decode(), stderr.decode(), proc.returncode or 0
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            raise
