"""Shared pytest fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Absolute path to the repository root."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_raw_csv(project_root: Path) -> Path:
    """Path to the synthetic dirty sample CSV."""
    return project_root / "data" / "raw" / "customers_raw.csv"
