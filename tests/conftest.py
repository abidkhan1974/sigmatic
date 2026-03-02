"""Pytest configuration and shared fixtures."""

import asyncio
import os

import pytest
from fastapi.testclient import TestClient

# Use test database
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://sigmatic:sigmatic@localhost:5432/sigmatic_test",
)
os.environ.setdefault(
    "DATABASE_URL_SYNC",
    "postgresql://sigmatic:sigmatic@localhost:5432/sigmatic_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENVIRONMENT", "test")


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Session-scoped test client — no auth override."""
    from sigmatic.server.app import app

    with TestClient(app) as c:
        yield c  # type: ignore[misc]


@pytest.fixture
def authed_client(client: TestClient) -> TestClient:
    """Reuses the session-level TestClient with auth bypassed per-test.

    Function-scoped so the override is cleanly set/cleared each test,
    and the underlying event loop / connection pool is shared with `client`.
    """
    from sigmatic.server.app import app
    from sigmatic.server.middleware.auth import require_api_key
    from sigmatic.server.models.api_key import APIKey

    fake_key = APIKey(id="test-key-id", key_hash="x", name="test", status="active")
    app.dependency_overrides[require_api_key] = lambda: fake_key
    yield client
    app.dependency_overrides.pop(require_api_key, None)


@pytest.fixture(scope="session", autouse=True)
def create_schema() -> None:
    """Create all DB tables in the test database before the session starts.

    Silently skips if the test database is not reachable. Tests that need
    the DB will fail individually in that case.
    """
    from sqlalchemy.ext.asyncio import create_async_engine

    from sigmatic.server.models import Base

    url = os.environ["DATABASE_URL"]

    async def _setup() -> None:
        engine = create_async_engine(url)
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
        finally:
            await engine.dispose()

    try:
        asyncio.run(_setup())
    except Exception:
        pass  # DB not available — tests that need it will fail individually
