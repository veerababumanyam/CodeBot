"""Shared pytest fixtures for the codebot-server test suite."""

from __future__ import annotations

import subprocess
from collections.abc import AsyncGenerator, Callable
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from codebot.config import settings


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional AsyncSession that rolls back after each test.

    Creates a fresh engine per test function so there are no cross-loop issues
    when asyncio_default_fixture_loop_scope is "function".  Each session wraps
    the test in a SAVEPOINT so inserts/updates are never committed to the DB.
    """
    engine = create_async_engine(settings.database_url, echo=False, pool_size=1, max_overflow=0)
    factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with factory() as session:
        async with session.begin_nested():
            yield session
        await session.rollback()
    await engine.dispose()


@pytest.fixture
def mock_subprocess() -> Callable[..., tuple[MagicMock, AsyncMock]]:
    """Factory fixture for mocking asyncio.create_subprocess_exec.

    Returns a callable that configures a mock subprocess with the given
    stdout, stderr, and returncode.  The returned tuple contains:
    - The patcher mock (to inspect calls)
    - The process AsyncMock (to verify communicate() etc.)

    Usage::

        def test_example(mock_subprocess):
            patcher, proc = mock_subprocess(
                stdout=b'{"results":[]}',
                stderr=b'',
                returncode=0,
            )
            with patcher:
                # ... code that calls create_subprocess_exec ...
    """

    def _factory(
        stdout: bytes = b"",
        stderr: bytes = b"",
        returncode: int = 0,
    ) -> tuple[MagicMock, AsyncMock]:
        proc = AsyncMock()
        proc.communicate = AsyncMock(return_value=(stdout, stderr))
        proc.returncode = returncode
        proc.kill = MagicMock()

        patcher = patch(
            "asyncio.create_subprocess_exec",
            return_value=proc,
        )
        return patcher, proc

    return _factory  # type: ignore[return-value]


@pytest.fixture
def tmp_git_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a temporary directory with an initialized git repo.

    Creates a git repo with an initial commit containing a dummy file.
    Useful for worktree tests that need a real git structure.
    """
    repo_dir = tmp_path_factory.mktemp("git_repo")
    subprocess.run(
        ["git", "init", str(repo_dir)],
        check=True,
        capture_output=True,
    )
    # Configure user for commits
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "user.email", "test@test.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "user.name", "Test User"],
        check=True,
        capture_output=True,
    )
    # Create initial commit
    dummy_file = repo_dir / "README.md"
    dummy_file.write_text("# Test Repo\n")
    subprocess.run(
        ["git", "-C", str(repo_dir), "add", "."],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "commit", "-m", "Initial commit"],
        check=True,
        capture_output=True,
    )
    return repo_dir


@pytest.fixture
def security_fixtures_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Return a directory containing sample scanner JSON outputs.

    Creates fixture files with realistic scanner outputs for testing
    the SecurityOrchestrator with mocked CLI subprocesses.
    """
    fixtures_dir = tmp_path_factory.mktemp("security_fixtures")

    # Sample Semgrep JSON output
    semgrep_output = fixtures_dir / "semgrep_output.json"
    semgrep_output.write_text(
        '{"results": [{"check_id": "python.lang.security.audit.exec-used",'
        '"path": "app.py", "start": {"line": 10}, "end": {"line": 10},'
        '"extra": {"severity": "WARNING", "message": "exec() used",'
        '"lines": "exec(code)", "metadata": {"cwe": ["CWE-78"]}}}]}'
    )

    # Sample Trivy JSON output
    trivy_output = fixtures_dir / "trivy_output.json"
    trivy_output.write_text(
        '{"Results": [{"Target": "requirements.txt",'
        '"Vulnerabilities": [{"VulnerabilityID": "CVE-2024-0001",'
        '"PkgName": "requests", "Severity": "HIGH",'
        '"Title": "Request smuggling", "Description": "HTTP request smuggling",'
        '"FixedVersion": "2.32.0"}]}]}'
    )

    # Sample Gitleaks JSON output
    gitleaks_output = fixtures_dir / "gitleaks_output.json"
    gitleaks_output.write_text(
        '[{"RuleID": "aws-access-key-id", "Description": "AWS Access Key",'
        '"File": "config.py", "StartLine": 5, "EndLine": 5,'
        '"Match": "AKIA..."}]'
    )

    return fixtures_dir
