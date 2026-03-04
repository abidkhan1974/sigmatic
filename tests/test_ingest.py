"""Integration tests for the webhook ingestion endpoint.

Endpoint: POST /v1/ingest/webhook/{source_id}
Auth:      X-Webhook-Token header (per-source token, not the global API key)
Response:  always 202 on auth+source success; errors captured in signal status
"""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_TV_PAYLOAD = {
    "ticker": "AAPL",
    "action": "buy",
    "price": 185.50,
    "interval": "1h",
}

_GENERIC_PAYLOAD = {
    "symbol": "BTCUSDT",
    "direction": "short",
    "entry_zone": 65000.0,
}


@pytest.fixture
def webhook_source(authed_client: TestClient) -> dict:
    """Create a TradingView webhook source and yield its full record (incl. token)."""
    resp = authed_client.post(
        "/v1/sources",
        json={
            "name": "ingest-test-tv",
            "type": "webhook",
            "schema_adapter": "tradingview",
        },
    )
    assert resp.status_code == 201
    source = resp.json()
    yield source
    # Cleanup — best-effort
    authed_client.delete(f"/v1/sources/{source['source_id']}")


@pytest.fixture
def generic_source(authed_client: TestClient) -> dict:
    """Create a generic webhook source and yield its full record."""
    resp = authed_client.post(
        "/v1/sources",
        json={
            "name": "ingest-test-generic",
            "type": "webhook",
            "schema_adapter": "generic",
        },
    )
    assert resp.status_code == 201
    source = resp.json()
    yield source
    authed_client.delete(f"/v1/sources/{source['source_id']}")


def _post_webhook(
    client: TestClient,
    source_id: str,
    token: str | None,
    payload: dict,
) -> object:
    headers = {}
    if token is not None:
        headers["X-Webhook-Token"] = token
    return client.post(
        f"/v1/ingest/webhook/{source_id}",
        json=payload,
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Basic happy-path — status code and response shape
# ---------------------------------------------------------------------------


def test_webhook_returns_202_for_valid_tv_payload(
    client: TestClient, webhook_source: dict
) -> None:
    resp = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], _TV_PAYLOAD
    )
    assert resp.status_code == 202


def test_webhook_response_contains_required_fields(
    client: TestClient, webhook_source: dict
) -> None:
    resp = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], _TV_PAYLOAD
    )
    data = resp.json()
    assert "signal_id" in data
    assert "status" in data
    assert "symbol" in data
    assert "direction" in data


def test_webhook_status_is_ingested_for_valid_tv_payload(
    client: TestClient, webhook_source: dict
) -> None:
    resp = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], _TV_PAYLOAD
    )
    assert resp.json()["status"] == "SCORED"


def test_webhook_tv_maps_ticker_to_symbol(
    client: TestClient, webhook_source: dict
) -> None:
    resp = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], _TV_PAYLOAD
    )
    assert resp.json()["symbol"] == "AAPL"


def test_webhook_tv_maps_buy_to_long(
    client: TestClient, webhook_source: dict
) -> None:
    resp = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], _TV_PAYLOAD
    )
    assert resp.json()["direction"] == "long"


def test_webhook_tv_maps_sell_to_short(
    client: TestClient, webhook_source: dict
) -> None:
    payload = {**_TV_PAYLOAD, "action": "sell"}
    resp = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], payload
    )
    assert resp.json()["direction"] == "short"


def test_webhook_tv_maps_close_to_flat(
    client: TestClient, webhook_source: dict
) -> None:
    payload = {**_TV_PAYLOAD, "action": "close"}
    resp = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], payload
    )
    assert resp.json()["direction"] == "flat"


def test_webhook_signal_id_is_non_empty_string(
    client: TestClient, webhook_source: dict
) -> None:
    resp = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], _TV_PAYLOAD
    )
    sid = resp.json()["signal_id"]
    assert isinstance(sid, str) and len(sid) > 0


# ---------------------------------------------------------------------------
# Generic adapter
# ---------------------------------------------------------------------------


def test_webhook_generic_passthrough_returns_202(
    client: TestClient, generic_source: dict
) -> None:
    resp = _post_webhook(
        client, generic_source["source_id"], generic_source["webhook_token"], _GENERIC_PAYLOAD
    )
    assert resp.status_code == 202


def test_webhook_generic_passthrough_preserves_symbol(
    client: TestClient, generic_source: dict
) -> None:
    resp = _post_webhook(
        client, generic_source["source_id"], generic_source["webhook_token"], _GENERIC_PAYLOAD
    )
    assert resp.json()["symbol"] == "BTCUSDT"


def test_webhook_generic_passthrough_preserves_direction(
    client: TestClient, generic_source: dict
) -> None:
    resp = _post_webhook(
        client, generic_source["source_id"], generic_source["webhook_token"], _GENERIC_PAYLOAD
    )
    assert resp.json()["direction"] == "short"


def test_webhook_generic_with_field_map(
    authed_client: TestClient, client: TestClient
) -> None:
    """field_map in source config remaps incoming keys before validation."""
    resp = authed_client.post(
        "/v1/sources",
        json={
            "name": "field-map-src",
            "type": "webhook",
            "schema_adapter": "generic",
            "config": {"field_map": {"ticker": "symbol", "side": "direction"}},
        },
    )
    source = resp.json()
    payload = {"ticker": "ETHUSDT", "side": "long"}
    r = _post_webhook(client, source["source_id"], source["webhook_token"], payload)
    assert r.status_code == 202
    assert r.json()["symbol"] == "ETHUSDT"
    assert r.json()["direction"] == "long"
    # cleanup
    authed_client.delete(f"/v1/sources/{source['source_id']}")


# ---------------------------------------------------------------------------
# Authentication failures
# ---------------------------------------------------------------------------


def test_webhook_missing_token_returns_401(
    client: TestClient, webhook_source: dict
) -> None:
    resp = _post_webhook(client, webhook_source["source_id"], None, _TV_PAYLOAD)
    assert resp.status_code == 401


def test_webhook_wrong_token_returns_401(
    client: TestClient, webhook_source: dict
) -> None:
    resp = _post_webhook(
        client, webhook_source["source_id"], "completely-wrong-token", _TV_PAYLOAD
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Source-level failures
# ---------------------------------------------------------------------------


def test_webhook_unknown_source_returns_404(client: TestClient) -> None:
    resp = _post_webhook(client, "does-not-exist", "any-token", _TV_PAYLOAD)
    assert resp.status_code == 404


def test_webhook_paused_source_returns_403(
    authed_client: TestClient, client: TestClient, webhook_source: dict
) -> None:
    authed_client.post(f"/v1/sources/{webhook_source['source_id']}/pause")
    resp = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], _TV_PAYLOAD
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Bad request body
# ---------------------------------------------------------------------------


def test_webhook_non_json_body_returns_400(
    client: TestClient, webhook_source: dict
) -> None:
    resp = client.post(
        f"/v1/ingest/webhook/{webhook_source['source_id']}",
        content=b"not-json-at-all",
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Token": webhook_source["webhook_token"],
        },
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Error capture — adapter and validation errors still yield 202
# ---------------------------------------------------------------------------


def test_webhook_adapter_error_still_returns_202(
    client: TestClient, webhook_source: dict
) -> None:
    """TradingView payload missing required 'action' → ADAPTER_ERROR, not 5xx."""
    bad_payload = {"ticker": "SPY"}  # missing 'action'
    resp = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], bad_payload
    )
    assert resp.status_code == 202


def test_webhook_adapter_error_status_is_adapter_error(
    client: TestClient, webhook_source: dict
) -> None:
    bad_payload = {"ticker": "SPY"}  # missing 'action'
    resp = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], bad_payload
    )
    assert resp.json()["status"] == "ADAPTER_ERROR"


def test_webhook_validation_error_still_returns_202(
    client: TestClient, generic_source: dict
) -> None:
    """Generic payload with invalid direction value → VALIDATION_ERROR, not 5xx."""
    bad_payload = {"symbol": "SPY", "direction": "sideways"}  # invalid direction
    resp = _post_webhook(
        client, generic_source["source_id"], generic_source["webhook_token"], bad_payload
    )
    assert resp.status_code == 202


def test_webhook_validation_error_status_is_validation_error(
    client: TestClient, generic_source: dict
) -> None:
    bad_payload = {"symbol": "SPY", "direction": "sideways"}
    resp = _post_webhook(
        client, generic_source["source_id"], generic_source["webhook_token"], bad_payload
    )
    assert resp.json()["status"] == "VALIDATION_ERROR"


def test_webhook_empty_payload_adapter_error_returns_202(
    client: TestClient, webhook_source: dict
) -> None:
    """Completely empty payload should capture error gracefully."""
    resp = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], {}
    )
    assert resp.status_code == 202


# ---------------------------------------------------------------------------
# Each signal gets a unique ID
# ---------------------------------------------------------------------------


def test_webhook_each_call_produces_unique_signal_id(
    client: TestClient, webhook_source: dict
) -> None:
    r1 = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], _TV_PAYLOAD
    )
    r2 = _post_webhook(
        client, webhook_source["source_id"], webhook_source["webhook_token"], _TV_PAYLOAD
    )
    assert r1.json()["signal_id"] != r2.json()["signal_id"]
