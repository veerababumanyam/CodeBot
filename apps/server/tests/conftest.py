"""Shared pytest fixtures for the codebot-server test suite."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.db.engine import async_session_factory


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio as the anyio backend for all async tests."""
    return "asyncio"


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional AsyncSession that rolls back after each test.

    Using a nested transaction (SAVEPOINT) keeps tests isolated without
    requiring the database to be recreated between runs.
    """
    async with async_session_factory() as session:
        # Begin a nested SAVEPOINT so individual tests don't commit to the DB.
        async with session.begin_nested():
            yield session
        await session.rollback()
