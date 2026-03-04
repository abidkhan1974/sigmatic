"""Integration tests for routing rule endpoints and quality scoring."""

import pytest
from fastapi.testclient import TestClient

_DEST = {"url": "https://hook.example.com/signals", "method": "POST"}
_FILTERS = {"symbols": ["AAPL"], "directions": ["long"], "min_quality_score": 0.2}


# ---------------------------------------------------------------------------
# POST /v1/routes — create
# ---------------------------------------------------------------------------


def test_create_route_returns_201(authed_client: TestClient) -> None:
    resp = authed_client.post("/v1/routes", json={"name": "test-route", "destination": _DEST})
    assert resp.status_code == 201
    authed_client.delete(f"/v1/routes/{resp.json()['route_id']}")


def test_create_route_response_schema(authed_client: TestClient) -> None:
    resp = authed_client.post(
        "/v1/routes",
        json={"name": "schema-route", "destination": _DEST, "filters": _FILTERS},
    )
    data = resp.json()
    assert "route_id" in data
    assert data["name"] == "schema-route"
    assert data["status"] == "active"
    assert data["destination"] == _DEST
    assert data["filters"] == _FILTERS
    authed_client.delete(f"/v1/routes/{data['route_id']}")


def test_create_route_missing_url_returns_422(authed_client: TestClient) -> None:
    resp = authed_client.post(
        "/v1/routes", json={"name": "bad", "destination": {"method": "POST"}}
    )
    assert resp.status_code == 422


def test_create_route_requires_auth(client: TestClient) -> None:
    resp = client.post("/v1/routes", json={"name": "x", "destination": _DEST})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /v1/routes — list + detail
# ---------------------------------------------------------------------------


def test_list_routes_returns_list(authed_client: TestClient) -> None:
    resp = authed_client.get("/v1/routes")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_routes_includes_created(authed_client: TestClient) -> None:
    r = authed_client.post("/v1/routes", json={"name": "list-me", "destination": _DEST})
    route_id = r.json()["route_id"]
    ids = [x["route_id"] for x in authed_client.get("/v1/routes").json()]
    assert route_id in ids
    authed_client.delete(f"/v1/routes/{route_id}")


def test_get_route_returns_200(authed_client: TestClient) -> None:
    r = authed_client.post("/v1/routes", json={"name": "get-me", "destination": _DEST})
    route_id = r.json()["route_id"]
    resp = authed_client.get(f"/v1/routes/{route_id}")
    assert resp.status_code == 200
    assert resp.json()["route_id"] == route_id
    authed_client.delete(f"/v1/routes/{route_id}")


def test_get_route_not_found_returns_404(authed_client: TestClient) -> None:
    assert authed_client.get("/v1/routes/no-such-id").status_code == 404


# ---------------------------------------------------------------------------
# PUT /v1/routes/{id} — update
# ---------------------------------------------------------------------------


def test_update_route_name(authed_client: TestClient) -> None:
    r = authed_client.post("/v1/routes", json={"name": "old", "destination": _DEST})
    route_id = r.json()["route_id"]
    resp = authed_client.put(f"/v1/routes/{route_id}", json={"name": "new-name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "new-name"
    authed_client.delete(f"/v1/routes/{route_id}")


def test_update_route_not_found_returns_404(authed_client: TestClient) -> None:
    assert authed_client.put("/v1/routes/ghost", json={"name": "x"}).status_code == 404


# ---------------------------------------------------------------------------
# DELETE /v1/routes/{id}
# ---------------------------------------------------------------------------


def test_delete_route_returns_204(authed_client: TestClient) -> None:
    r = authed_client.post("/v1/routes", json={"name": "del-me", "destination": _DEST})
    route_id = r.json()["route_id"]
    assert authed_client.delete(f"/v1/routes/{route_id}").status_code == 204


def test_delete_route_not_found_returns_404(authed_client: TestClient) -> None:
    assert authed_client.delete("/v1/routes/ghost-id").status_code == 404


# ---------------------------------------------------------------------------
# POST /v1/routes/{id}/pause and /resume
# ---------------------------------------------------------------------------


def test_pause_route(authed_client: TestClient) -> None:
    r = authed_client.post("/v1/routes", json={"name": "pause-me", "destination": _DEST})
    route_id = r.json()["route_id"]
    resp = authed_client.post(f"/v1/routes/{route_id}/pause")
    assert resp.status_code == 200
    assert resp.json()["status"] == "paused"
    authed_client.delete(f"/v1/routes/{route_id}")


def test_resume_route(authed_client: TestClient) -> None:
    r = authed_client.post("/v1/routes", json={"name": "resume-me", "destination": _DEST})
    route_id = r.json()["route_id"]
    authed_client.post(f"/v1/routes/{route_id}/pause")
    resp = authed_client.post(f"/v1/routes/{route_id}/resume")
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"
    authed_client.delete(f"/v1/routes/{route_id}")


# ---------------------------------------------------------------------------
# POST /v1/routes/{id}/test — filter matching
# ---------------------------------------------------------------------------


@pytest.fixture
def route_with_filters(authed_client: TestClient) -> dict:
    r = authed_client.post(
        "/v1/routes",
        json={
            "name": "filter-route",
            "destination": _DEST,
            "filters": {"symbols": ["AAPL"], "directions": ["long"]},
        },
    )
    route = r.json()
    yield route
    authed_client.delete(f"/v1/routes/{route['route_id']}")


@pytest.fixture
def aapl_long_signal(authed_client: TestClient) -> dict:
    r = authed_client.post(
        "/v1/ingest/signal", json={"symbol": "AAPL", "direction": "long"}
    )
    return r.json()


@pytest.fixture
def tsla_short_signal(authed_client: TestClient) -> dict:
    r = authed_client.post(
        "/v1/ingest/signal", json={"symbol": "TSLA", "direction": "short"}
    )
    return r.json()


def test_route_test_matches(
    authed_client: TestClient, route_with_filters: dict, aapl_long_signal: dict
) -> None:
    resp = authed_client.post(
        f"/v1/routes/{route_with_filters['route_id']}/test",
        params={"signal_id": aapl_long_signal["signal_id"]},
    )
    assert resp.status_code == 200
    assert resp.json()["matched"] is True


def test_route_test_no_match_symbol(
    authed_client: TestClient, route_with_filters: dict, tsla_short_signal: dict
) -> None:
    resp = authed_client.post(
        f"/v1/routes/{route_with_filters['route_id']}/test",
        params={"signal_id": tsla_short_signal["signal_id"]},
    )
    assert resp.status_code == 200
    assert resp.json()["matched"] is False


def test_route_test_unknown_route_returns_404(
    authed_client: TestClient, aapl_long_signal: dict
) -> None:
    resp = authed_client.post(
        "/v1/routes/no-such/test",
        params={"signal_id": aapl_long_signal["signal_id"]},
    )
    assert resp.status_code == 404


def test_route_test_unknown_signal_returns_404(
    authed_client: TestClient, route_with_filters: dict
) -> None:
    resp = authed_client.post(
        f"/v1/routes/{route_with_filters['route_id']}/test",
        params={"signal_id": "no-such-signal"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Quality scoring — signals get quality_score after ingest
# ---------------------------------------------------------------------------


def test_api_ingest_signal_is_scored(authed_client: TestClient) -> None:
    """POST /v1/ingest/signal → signal should have quality_score set."""
    ingest_resp = authed_client.post(
        "/v1/ingest/signal",
        json={"symbol": "NVDA", "direction": "long", "confidence": 0.8},
    )
    signal_id = ingest_resp.json()["signal_id"]
    detail = authed_client.get(f"/v1/signals/{signal_id}").json()
    assert detail["quality_score"] is not None
    assert 0.0 <= detail["quality_score"] <= 1.0


def test_quality_score_uses_confidence(authed_client: TestClient) -> None:
    """Higher confidence → higher quality_score (with default trust 0.5)."""
    low = authed_client.post(
        "/v1/ingest/signal", json={"symbol": "SPY", "direction": "long", "confidence": 0.2}
    ).json()["signal_id"]
    high = authed_client.post(
        "/v1/ingest/signal", json={"symbol": "SPY", "direction": "long", "confidence": 0.9}
    ).json()["signal_id"]

    qs_low = authed_client.get(f"/v1/signals/{low}").json()["quality_score"]
    qs_high = authed_client.get(f"/v1/signals/{high}").json()["quality_score"]
    assert qs_high > qs_low


def test_quality_score_status_is_scored(authed_client: TestClient) -> None:
    """Ingested + scored signal should have status=SCORED."""
    r = authed_client.post(
        "/v1/ingest/signal", json={"symbol": "AAPL", "direction": "flat"}
    )
    signal_id = r.json()["signal_id"]
    detail = authed_client.get(f"/v1/signals/{signal_id}").json()
    assert detail["status"] == "SCORED"


def test_webhook_signal_is_scored(authed_client: TestClient, client: TestClient) -> None:
    """Webhook-ingested INGESTED signals get scored too."""
    src = authed_client.post(
        "/v1/sources",
        json={"name": "score-test-src", "type": "webhook", "schema_adapter": "tradingview"},
    ).json()
    resp = client.post(
        f"/v1/ingest/webhook/{src['source_id']}",
        json={"ticker": "MSFT", "action": "buy", "price": 420.0},
        headers={"X-Webhook-Token": src["webhook_token"]},
    )
    signal_id = resp.json()["signal_id"]
    detail = authed_client.get(f"/v1/signals/{signal_id}").json()
    assert detail["quality_score"] is not None
    assert detail["status"] == "SCORED"
    authed_client.delete(f"/v1/sources/{src['source_id']}")
