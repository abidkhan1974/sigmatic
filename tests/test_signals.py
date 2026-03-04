"""Integration tests for the signals list/detail and API ingest endpoints."""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_TV_PAYLOAD = {"ticker": "TSLA", "action": "buy", "price": 250.0, "interval": "15m"}
_TV_PAYLOAD_SHORT = {"ticker": "TSLA", "action": "sell", "price": 249.0}
_GENERIC_PAYLOAD = {"symbol": "ETHUSDT", "direction": "short", "entry_zone": 3200.0}


@pytest.fixture
def tv_source(authed_client: TestClient) -> dict:
    """Create a TradingView webhook source."""
    resp = authed_client.post(
        "/v1/sources",
        json={"name": "signals-test-tv", "type": "webhook", "schema_adapter": "tradingview"},
    )
    assert resp.status_code == 201
    source = resp.json()
    yield source
    authed_client.delete(f"/v1/sources/{source['source_id']}")


@pytest.fixture
def generic_source(authed_client: TestClient) -> dict:
    """Create a generic webhook source."""
    resp = authed_client.post(
        "/v1/sources",
        json={"name": "signals-test-generic", "type": "webhook", "schema_adapter": "generic"},
    )
    assert resp.status_code == 201
    source = resp.json()
    yield source
    authed_client.delete(f"/v1/sources/{source['source_id']}")


def _send_webhook(client: TestClient, source: dict, payload: dict) -> dict:
    resp = client.post(
        f"/v1/ingest/webhook/{source['source_id']}",
        json=payload,
        headers={"X-Webhook-Token": source["webhook_token"]},
    )
    assert resp.status_code == 202
    return resp.json()


# ---------------------------------------------------------------------------
# GET /v1/signals — list
# ---------------------------------------------------------------------------


def test_list_signals_returns_200(authed_client: TestClient) -> None:
    resp = authed_client.get("/v1/signals")
    assert resp.status_code == 200


def test_list_signals_returns_list(authed_client: TestClient) -> None:
    assert isinstance(authed_client.get("/v1/signals").json(), list)


def test_list_signals_includes_ingested_signal(
    authed_client: TestClient, client: TestClient, tv_source: dict
) -> None:
    ingested = _send_webhook(client, tv_source, _TV_PAYLOAD)
    signal_ids = [s["signal_id"] for s in authed_client.get("/v1/signals").json()]
    assert ingested["signal_id"] in signal_ids


def test_list_signals_filter_by_symbol(
    authed_client: TestClient, client: TestClient, tv_source: dict
) -> None:
    _send_webhook(client, tv_source, _TV_PAYLOAD)
    resp = authed_client.get("/v1/signals", params={"symbol": "TSLA"})
    assert resp.status_code == 200
    symbols = {s["symbol"] for s in resp.json()}
    assert symbols == {"TSLA"}


def test_list_signals_filter_by_source_id(
    authed_client: TestClient, client: TestClient, tv_source: dict, generic_source: dict
) -> None:
    _send_webhook(client, tv_source, _TV_PAYLOAD)
    _send_webhook(client, generic_source, _GENERIC_PAYLOAD)
    resp = authed_client.get("/v1/signals", params={"source_id": tv_source["source_id"]})
    source_ids = {s["source_id"] for s in resp.json()}
    assert source_ids == {tv_source["source_id"]}


def test_list_signals_filter_by_direction(
    authed_client: TestClient, client: TestClient, tv_source: dict
) -> None:
    _send_webhook(client, tv_source, _TV_PAYLOAD)        # buy → long
    _send_webhook(client, tv_source, _TV_PAYLOAD_SHORT)  # sell → short
    resp = authed_client.get("/v1/signals", params={"direction": "long"})
    directions = {s["direction"] for s in resp.json()}
    assert "short" not in directions


def test_list_signals_filter_by_status(
    authed_client: TestClient, client: TestClient, tv_source: dict
) -> None:
    _send_webhook(client, tv_source, _TV_PAYLOAD)
    _send_webhook(client, tv_source, {"ticker": "BAD"})  # adapter error
    resp = authed_client.get("/v1/signals", params={"status": "INGESTED"})
    statuses = {s["status"] for s in resp.json()}
    assert "ADAPTER_ERROR" not in statuses


def test_list_signals_limit(
    authed_client: TestClient, client: TestClient, tv_source: dict
) -> None:
    for _ in range(3):
        _send_webhook(client, tv_source, _TV_PAYLOAD)
    resp = authed_client.get("/v1/signals", params={"limit": 2})
    assert len(resp.json()) <= 2


def test_list_signals_invalid_limit_returns_422(authed_client: TestClient) -> None:
    resp = authed_client.get("/v1/signals", params={"limit": 9999})
    assert resp.status_code == 422


def test_list_signals_newest_first(
    authed_client: TestClient, client: TestClient, tv_source: dict
) -> None:
    for _ in range(3):
        _send_webhook(client, tv_source, _TV_PAYLOAD)
    signals = authed_client.get("/v1/signals", params={"symbol": "TSLA"}).json()
    ingested_ats = [s["ingested_at"] for s in signals if s["ingested_at"]]
    assert ingested_ats == sorted(ingested_ats, reverse=True)


def test_list_signals_requires_auth(client: TestClient) -> None:
    resp = client.get("/v1/signals")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /v1/signals/{signal_id} — detail
# ---------------------------------------------------------------------------


def test_get_signal_returns_200(
    authed_client: TestClient, client: TestClient, tv_source: dict
) -> None:
    ingested = _send_webhook(client, tv_source, _TV_PAYLOAD)
    resp = authed_client.get(f"/v1/signals/{ingested['signal_id']}")
    assert resp.status_code == 200


def test_get_signal_response_has_all_fields(
    authed_client: TestClient, client: TestClient, tv_source: dict
) -> None:
    ingested = _send_webhook(client, tv_source, _TV_PAYLOAD)
    data = authed_client.get(f"/v1/signals/{ingested['signal_id']}").json()
    for field in ("signal_id", "source_id", "symbol", "direction", "status", "ingested_at"):
        assert field in data, f"Missing field: {field}"


def test_get_signal_symbol_is_uppercased(
    authed_client: TestClient, client: TestClient, tv_source: dict
) -> None:
    ingested = _send_webhook(client, tv_source, _TV_PAYLOAD)
    data = authed_client.get(f"/v1/signals/{ingested['signal_id']}").json()
    assert data["symbol"] == "TSLA"


def test_get_signal_entry_zone_preserved(
    authed_client: TestClient, client: TestClient, tv_source: dict
) -> None:
    ingested = _send_webhook(client, tv_source, _TV_PAYLOAD)
    data = authed_client.get(f"/v1/signals/{ingested['signal_id']}").json()
    assert data["entry_zone"] == pytest.approx(250.0)


def test_get_signal_not_found_returns_404(authed_client: TestClient) -> None:
    resp = authed_client.get("/v1/signals/no-such-id")
    assert resp.status_code == 404


def test_get_signal_requires_auth(client: TestClient) -> None:
    resp = client.get("/v1/signals/some-id")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /v1/ingest/signal — API key ingest (Issue #2)
# ---------------------------------------------------------------------------


def test_api_ingest_returns_202(authed_client: TestClient) -> None:
    resp = authed_client.post(
        "/v1/ingest/signal",
        json={"symbol": "BTCUSDT", "direction": "long"},
    )
    assert resp.status_code == 202


def test_api_ingest_response_shape(authed_client: TestClient) -> None:
    resp = authed_client.post(
        "/v1/ingest/signal",
        json={"symbol": "BTCUSDT", "direction": "short"},
    )
    data = resp.json()
    assert "signal_id" in data
    assert data["status"] == "SCORED"
    assert data["symbol"] == "BTCUSDT"
    assert data["direction"] == "short"


def test_api_ingest_with_all_optional_fields(authed_client: TestClient) -> None:
    resp = authed_client.post(
        "/v1/ingest/signal",
        json={
            "symbol": "AAPL",
            "direction": "long",
            "confidence": 0.85,
            "entry_zone": 185.0,
            "stop_distance": 3.0,
            "target": 192.0,
            "strategy_id": "momentum-v1",
            "timeframe": "4h",
        },
    )
    assert resp.status_code == 202
    assert resp.json()["symbol"] == "AAPL"


def test_api_ingest_invalid_direction_returns_422(authed_client: TestClient) -> None:
    resp = authed_client.post(
        "/v1/ingest/signal",
        json={"symbol": "AAPL", "direction": "sideways"},
    )
    assert resp.status_code == 422


def test_api_ingest_missing_symbol_returns_422(authed_client: TestClient) -> None:
    resp = authed_client.post(
        "/v1/ingest/signal",
        json={"direction": "long"},
    )
    assert resp.status_code == 422


def test_api_ingest_requires_auth(client: TestClient) -> None:
    resp = client.post(
        "/v1/ingest/signal",
        json={"symbol": "AAPL", "direction": "long"},
    )
    assert resp.status_code == 401


def test_api_ingest_signal_appears_in_list(authed_client: TestClient) -> None:
    resp = authed_client.post(
        "/v1/ingest/signal",
        json={"symbol": "NVDA", "direction": "long"},
    )
    signal_id = resp.json()["signal_id"]
    signal_ids = [s["signal_id"] for s in authed_client.get("/v1/signals").json()]
    assert signal_id in signal_ids
