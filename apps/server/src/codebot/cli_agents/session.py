"""Session manager for CLI agent subprocess execution.

Handles launching CLI tool processes, capturing output, enforcing
timeouts, and returning structured :class:`CLIResult` objects.
"""

from __future__ import annotations

import asyncio
import logging
import time

from codebot.cli_agents.models import CLIResult

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages subprocess execution for CLI agent adapters.

    Launches processes via ``asyncio.create_subprocess_exec``, captures
    stdout/stderr, enforces timeouts, and tracks execution duration.
    Uses create_subprocess_exec (not shell) for safety against injection.
    """

    async def run(
        self,
        cmd: list[str],
        env: dict[str, str],
        cwd: str,
        timeout: int = 300,
    ) -> CLIResult:
        """Execute a CLI command and return a structured result.

        Args:
            cmd: Command and arguments to execute.
            env: Environment variables for the subprocess.
            cwd: Working directory for the subprocess.
            timeout: Maximum execution time in seconds.

        Returns:
            A :class:`CLIResult` with captured output and timing info.
        """
        start = time.monotonic()

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=cwd,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )

            duration_ms = int((time.monotonic() - start) * 1000)
            return CLIResult(
                stdout=stdout_bytes.decode() if stdout_bytes else "",
                stderr=stderr_bytes.decode() if stderr_bytes else "",
                returncode=proc.returncode or 0,
                duration_ms=duration_ms,
            )

        except TimeoutError:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.warning("Process timed out after %ds: %s", timeout, cmd[0])
            try:
                proc.kill()  # type: ignore[possibly-undefined]
                await proc.wait()
            except Exception:
                pass
            return CLIResult(
                returncode=-1,
                stderr="Process timed out",
                duration_ms=duration_ms,
            )
