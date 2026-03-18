"""Root test configuration with shared fixtures.

Provides a Temporal WorkflowEnvironment fixture using the in-memory
time-skipping server so integration tests run without an external
Temporal deployment.
"""

from __future__ import annotations

import pytest
from temporalio.testing import WorkflowEnvironment


@pytest.fixture
async def temporal_env() -> WorkflowEnvironment:  # type: ignore[misc]
    """Yield a Temporal time-skipping test environment.

    The environment uses an embedded Temporal test server with
    time-skipping support so timer-dependent workflows complete
    instantly.  No external Temporal server is required.
    """
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env  # type: ignore[misc]
