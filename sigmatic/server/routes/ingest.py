"""Signal ingestion endpoints.

Two routers with different auth requirements:
- webhook_router:    public, authenticated via per-source X-Webhook-Token header
- api_ingest_router: protected by X-API-Key
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from sigmatic.server.dependencies import DbSession
from sigmatic.server.models.base import generate_uuid
from sigmatic.server.models.signal import Signal
from sigmatic.server.schemas.signal import NormalizedSignal, WebhookIngestResponse
from sigmatic.server.services.ingest_service import (
    InvalidWebhookTokenError,
    SourceNotActiveError,
    SourceNotFoundError,
    ingest_webhook,
)

_UTC = timezone.utc

# Public — per-source token auth handled inside the handler
webhook_router = APIRouter()

# Protected — requires X-API-Key (wired in app.py)
api_ingest_router = APIRouter()


@webhook_router.post(
    "/ingest/webhook/{source_id}",
    status_code=202,
    response_model=WebhookIngestResponse,
)
async def ingest_webhook_endpoint(
    source_id: str,
    request: Request,
    session: DbSession,
    x_webhook_token: str | None = Header(None),
) -> WebhookIngestResponse:
    """Receive a raw signal payload from a registered webhook source.

    Auth: X-Webhook-Token header must match the source's webhook_token.
    Always returns 202 — adapter / validation errors are recorded on the
    signal record rather than rejected, so no payload is ever silently lost.
    """
    try:
        raw_payload: dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON")

    try:
        signal = await ingest_webhook(session, source_id, x_webhook_token, raw_payload)
    except SourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")
    except SourceNotActiveError:
        raise HTTPException(status_code=403, detail=f"Source '{source_id}' is paused")
    except InvalidWebhookTokenError:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Webhook-Token")

    return WebhookIngestResponse(
        signal_id=signal.signal_id,
        status=signal.status,
        symbol=signal.symbol,
        direction=signal.direction,
    )


@api_ingest_router.post("/ingest/signal", status_code=202, response_model=WebhookIngestResponse)
async def ingest_signal(body: NormalizedSignal, session: DbSession) -> WebhookIngestResponse:
    """Ingest a pre-normalized signal via API key auth.

    The request body must conform to the NormalizedSignal schema
    (symbol, direction required; all other fields optional).
    No adapter step — the payload is validated directly.
    """
    signal = Signal(
        signal_id=generate_uuid(),
        source_id=None,
        symbol=body.symbol,
        direction=body.direction,
        confidence=body.confidence,
        entry_zone=body.entry_zone,
        stop_distance=body.stop_distance,
        target=body.target,
        strategy_id=body.strategy_id,
        timeframe=body.timeframe,
        status="INGESTED",
        raw_payload=body.model_dump_json(),
        ingested_at=datetime.now(_UTC),
    )
    session.add(signal)
    await session.commit()
    await session.refresh(signal)
    return WebhookIngestResponse(
        signal_id=signal.signal_id,
        status=signal.status,
        symbol=signal.symbol,
        direction=signal.direction,
    )
