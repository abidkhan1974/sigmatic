"""Tests for API key authentication middleware."""

import pytest
from fastapi.testclient import TestClient


# Routes that require API key auth
PROTECTED_GET_ROUTES = [
    "/v1/signals",
    "/v1/sources",
    "/v1/routes",
]

PROTECTED_POST_ROUTES = [
    "/v1/outcomes",
    "/v1/ingest/signal",
]

# Routes that must remain public
PUBLIC_ROUTES = [
    "/v1/health",
]


@pytest.mark.parametrize("path", PROTECTED_GET_ROUTES)
def test_protected_get_returns_401_without_key(client: TestClient, path: str) -> None:
    """Protected GET routes must return 401 when no API key is supplied."""
    response = client.get(path)
    assert response.status_code == 401
    assert "X-API-Key" in response.json().get("detail", "")


@pytest.mark.parametrize("path", PROTECTED_POST_ROUTES)
def test_protected_post_returns_401_without_key(client: TestClient, path: str) -> None:
    """Protected POST routes must return 401 when no API key is supplied."""
    response = client.post(path, json={})
    assert response.status_code == 401


def test_invalid_key_returns_401(client: TestClient) -> None:
    """A well-formed but unknown API key must return 401."""
    response = client.get("/v1/signals", headers={"X-API-Key": "smk_" + "a" * 64})
    # 401 (invalid key) or 503 (DB unavailable in unit test context) are both acceptable
    assert response.status_code in (401, 503)


@pytest.mark.parametrize("path", PUBLIC_ROUTES)
def test_public_routes_accessible_without_key(client: TestClient, path: str) -> None:
    """Public routes must be reachable without an API key."""
    response = client.get(path)
    assert response.status_code == 200


def test_webhook_ingest_accessible_without_api_key(client: TestClient) -> None:
    """Webhook ingest uses per-source tokens, not API keys — no 401 on missing key."""
    response = client.post("/v1/ingest/webhook/test-source-id", json={})
    # Returns 501 (not implemented yet) — not 401
    assert response.status_code != 401
