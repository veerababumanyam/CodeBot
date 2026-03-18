"""Shared fixtures for context management integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def lance_dir(tmp_path: Path) -> Path:
    """Return a temporary directory for LanceDB storage."""
    db_dir = tmp_path / "lancedb_integration"
    db_dir.mkdir()
    return db_dir
