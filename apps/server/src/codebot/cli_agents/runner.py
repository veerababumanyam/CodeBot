"""CLIAgentRunner -- orchestrates worktree, ports, adapters, and security.

The runner is the central coordinator for CLI agent execution.  It
acquires a worktree from the pool, allocates ports, builds the CLI
command via an adapter, runs it via :class:`SessionManager`, and then
automatically invokes :class:`SecurityOrchestrator` to scan the
worktree (SECP-05).  Resources are released in a ``finally`` block.
"""

from __future__ import annotations

import logging

from codebot.cli_agents.adapters.base import BaseCLIAdapter
from codebot.cli_agents.adapters.claude_code import ClaudeCodeAdapter
from codebot.cli_agents.adapters.codex import CodexAdapter
from codebot.cli_agents.adapters.gemini import GeminiCLIAdapter
from codebot.cli_agents.models import AdapterInfo, CLIResult, CLITask
from codebot.cli_agents.output_parser import OutputParser
from codebot.cli_agents.session import SessionManager
from codebot.security.orchestrator import SecurityOrchestrator
from codebot.worktree.branch_strategy import BranchStrategy
from codebot.worktree.models import BranchConfig
from codebot.worktree.pool import WorktreePool
from codebot.worktree.port_allocator import PortAllocator

logger = logging.getLogger(__name__)

DEFAULT_SERVICES = ["web", "api", "db"]


class CLIAgentRunner:
    """Orchestrates CLI agent execution in isolated worktrees.

    Integrates :class:`WorktreePool`, :class:`PortAllocator`,
    :class:`BranchStrategy`, CLI adapters, and optionally
    :class:`SecurityOrchestrator` into a single ``execute()`` flow.

    After every code generation step, if a ``security_orchestrator``
    is provided, ``SecurityOrchestrator.scan()`` runs on the worktree
    and the resulting :class:`SecurityReport` is attached to the
    :class:`CLIResult` (SECP-05).  Scan failures are logged but
    non-fatal.

    Args:
        pool: Worktree pool for acquiring/releasing isolated worktrees.
        port_allocator: Allocator for unique service ports.
        branch_strategy: Strategy for generating branch names.
        services: Service names to allocate ports for.
        security_orchestrator: Optional orchestrator for post-generation scans.
    """

    def __init__(
        self,
        pool: WorktreePool,
        port_allocator: PortAllocator,
        branch_strategy: BranchStrategy,
        services: list[str] | None = None,
        security_orchestrator: SecurityOrchestrator | None = None,
    ) -> None:
        self.pool = pool
        self.port_allocator = port_allocator
        self.branch_strategy = branch_strategy
        self.services = services or DEFAULT_SERVICES
        self.session = SessionManager()
        self.parser = OutputParser()
        self.security_orchestrator = security_orchestrator
        self._adapters: dict[str, BaseCLIAdapter] = {
            "claude": ClaudeCodeAdapter(),
            "codex": CodexAdapter(),
            "gemini": GeminiCLIAdapter(),
        }

    async def execute(
        self,
        adapter_name: str,
        task: CLITask,
        agent_id: str,
        task_id: str = "",
    ) -> CLIResult:
        """Execute a CLI agent task in an isolated worktree.

        Acquires a worktree, allocates ports, runs the adapter's command,
        optionally scans for security issues, and releases resources.

        Args:
            adapter_name: Name of the adapter to use (claude, codex, gemini).
            task: The CLI task describing the work to perform.
            agent_id: Identifier of the requesting agent.
            task_id: Optional task identifier for branch naming.

        Returns:
            A :class:`CLIResult` with output and optional security report.
        """
        adapter = self._adapters.get(adapter_name)
        if adapter is None:
            return CLIResult(
                returncode=-1, stderr=f"Unknown adapter: {adapter_name}"
            )

        branch_config = BranchConfig(
            prefix="feature", task_id=task_id, agent_id=agent_id
        )
        branch_name = self.branch_strategy.create_branch_name(branch_config)

        worktree = await self.pool.acquire(agent_id, branch_name)
        ports = await self.port_allocator.allocate(worktree.id, self.services)
        worktree.ports = ports

        try:
            cmd = adapter.build_command(task, worktree.path)
            env = adapter.build_env(worktree.path, ports)
            result = await self.session.run(
                cmd=cmd, env=env, cwd=worktree.path, timeout=task.timeout
            )
            result.parsed_output = self.parser.parse_json(result.stdout)

            # SECP-05: Run security scan after every code generation step
            if self.security_orchestrator is not None:
                try:
                    security_report = await self.security_orchestrator.scan(
                        worktree.path
                    )
                    result.security_report = security_report
                    if (
                        not security_report.gate_result
                        or not security_report.gate_result.passed
                    ):
                        logger.warning(
                            "Security gate FAILED for agent %s in %s: %s",
                            agent_id,
                            worktree.path,
                            (
                                security_report.gate_result.reason
                                if security_report.gate_result
                                else "no gate result"
                            ),
                        )
                except Exception:
                    logger.exception(
                        "Security scan failed for agent %s in %s (non-fatal)",
                        agent_id,
                        worktree.path,
                    )

            return result
        except Exception as exc:
            logger.exception("CLI agent execution failed for %s", agent_id)
            return CLIResult(returncode=-1, stderr=str(exc))
        finally:
            await self.port_allocator.release(worktree.id)
            await self.pool.release(worktree)

    async def list_available(self) -> list[AdapterInfo]:
        """List all registered adapters with their availability status.

        Returns:
            List of :class:`AdapterInfo` for each registered adapter.
        """
        infos: list[AdapterInfo] = []
        for adapter in self._adapters.values():
            info = await adapter.get_info()
            infos.append(info)
        return infos
