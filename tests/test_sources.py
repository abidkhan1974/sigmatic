"""Integration tests for source CRUD endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clean_sources(authed_client: TestClient) -> None:
    """Delete all sources created during each test to keep tests isolated."""
    yield
    sources = authed_client.get("/v1/sources").json()
    if isinstance(sources, list):
        for s in sources:
            authed_client.delete(f"/v1/sources/{s['source_id']}")


# ---------------------------------------------------------------------------
# POST /v1/sources — create
# ---------------------------------------------------------------------------

def test_create_source_returns_201(authed_client: TestClient) -> None:
    resp = authed_client.post("/v1/sources", json={
        "name": "tv-alerts",
        "type": "webhook",
        "schema_adapter": "tradingview",
    })
    assert resp.status_code == 201


def test_create_source_response_schema(authed_client: TestClient) -> None:
    resp = authed_client.post("/v1/sources", json={
        "name": "tv-alerts",
        "type": "webhook",
    })
    data = resp.json()
    assert "source_id" in data
    assert data["name"] == "tv-alerts"
    assert data["type"] == "webhook"
    assert data["schema_adapter"] == "generic"
    assert data["status"] == "active"
    assert data["trust_score"] == 0.5
    assert "webhook_token" in data
    assert data["webhook_token"] is not None


def test_create_source_generates_unique_webhook_token(authed_client: TestClient) -> None:
    r1 = authed_client.post("/v1/sources", json={"name": "src-a", "type": "webhook"})
    r2 = authed_client.post("/v1/sources", json={"name": "src-b", "type": "webhook"})
    assert r1.json()["webhook_token"] != r2.json()["webhook_token"]
    # cleanup second source (first cleaned by autouse fixture)
    authed_client.delete(f"/v1/sources/{r2.json()['source_id']}")


def test_create_source_duplicate_name_returns_409(authed_client: TestClient) -> None:
    authed_client.post("/v1/sources", json={"name": "dup-src", "type": "webhook"})
    resp = authed_client.post("/v1/sources", json={"name": "dup-src", "type": "api"})
    assert resp.status_code == 409


def test_create_source_invalid_type_returns_422(authed_client: TestClient) -> None:
    resp = authed_client.post("/v1/sources", json={"name": "bad", "type": "fax"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /v1/sources — list
# ---------------------------------------------------------------------------

def test_list_sources_returns_list(authed_client: TestClient) -> None:
    resp = authed_client.get("/v1/sources")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_sources_includes_created(authed_client: TestClient) -> None:
    authed_client.post("/v1/sources", json={"name": "list-me", "type": "api"})
    sources = authed_client.get("/v1/sources").json()
    names = [s["name"] for s in sources]
    assert "list-me" in names


# ---------------------------------------------------------------------------
# GET /v1/sources/{id} — detail
# ---------------------------------------------------------------------------

def test_get_source_returns_200(authed_client: TestClient) -> None:
    created = authed_client.post("/v1/sources", json={"name": "get-me", "type": "webhook"}).json()
    resp = authed_client.get(f"/v1/sources/{created['source_id']}")
    assert resp.status_code == 200
    assert resp.json()["source_id"] == created["source_id"]


def test_get_source_not_found_returns_404(authed_client: TestClient) -> None:
    resp = authed_client.get("/v1/sources/nonexistent-id")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /v1/sources/{id} — update
# ---------------------------------------------------------------------------

def test_update_source_name(authed_client: TestClient) -> None:
    created = authed_client.post("/v1/sources", json={"name": "old-name", "type": "api"}).json()
    resp = authed_client.put(
        f"/v1/sources/{created['source_id']}",
        json={"name": "new-name"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "new-name"


def test_update_source_trust_score(authed_client: TestClient) -> None:
    created = authed_client.post("/v1/sources", json={"name": "score-src", "type": "api"}).json()
    resp = authed_client.put(
        f"/v1/sources/{created['source_id']}",
        json={"trust_score": 0.9},
    )
    assert resp.status_code == 200
    assert resp.json()["trust_score"] == pytest.approx(0.9)


def test_update_source_not_found_returns_404(authed_client: TestClient) -> None:
    resp = authed_client.put("/v1/sources/no-such-id", json={"name": "x"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /v1/sources/{id}
# ---------------------------------------------------------------------------

def test_delete_source_returns_204(authed_client: TestClient) -> None:
    created = authed_client.post("/v1/sources", json={"name": "del-me", "type": "api"}).json()
    resp = authed_client.delete(f"/v1/sources/{created['source_id']}")
    assert resp.status_code == 204


def test_delete_source_not_found_returns_404(authed_client: TestClient) -> None:
    resp = authed_client.delete("/v1/sources/ghost-id")
    assert resp.status_code == 404


def test_deleted_source_not_in_list(authed_client: TestClient) -> None:
    created = authed_client.post("/v1/sources", json={"name": "gone", "type": "api"}).json()
    authed_client.delete(f"/v1/sources/{created['source_id']}")
    sources = authed_client.get("/v1/sources").json()
    assert created["source_id"] not in [s["source_id"] for s in sources]


# ---------------------------------------------------------------------------
# POST /v1/sources/{id}/pause and /resume
# ---------------------------------------------------------------------------

def test_pause_source(authed_client: TestClient) -> None:
    created = authed_client.post("/v1/sources", json={"name": "pause-me", "type": "webhook"}).json()
    resp = authed_client.post(f"/v1/sources/{created['source_id']}/pause")
    assert resp.status_code == 200
    assert resp.json()["status"] == "paused"


def test_resume_source(authed_client: TestClient) -> None:
    created = authed_client.post("/v1/sources", json={"name": "resume-me", "type": "webhook"}).json()
    authed_client.post(f"/v1/sources/{created['source_id']}/pause")
    resp = authed_client.post(f"/v1/sources/{created['source_id']}/resume")
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_pause_nonexistent_source_returns_404(authed_client: TestClient) -> None:
    resp = authed_client.post("/v1/sources/no-id/pause")
    assert resp.status_code == 404
