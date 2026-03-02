"""Pytest configuration and shared fixtures."""

import os

import pytest
from fastapi.testclient import TestClient

# Use test database
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://sigmatic:sigmatic@localhost:5432/sigmatic_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENVIRONMENT", "test")


@pytest.fixture(scope="session")
def client():
    """Create a test client for the FastAPI app."""
    from sigmatic.server.app import app

    with TestClient(app) as c:
        yield c
