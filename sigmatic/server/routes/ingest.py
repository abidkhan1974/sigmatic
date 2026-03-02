"""Signal ingestion endpoints.

Two routers with different auth requirements:
- webhook_router:    public, authenticated via per-source X-Webhook-Token header
- api_ingest_router: protected by X-API-Key (Issue #2, still stubbed)
"""

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from sigmatic.server.dependencies import DbSession
from sigmatic.server.schemas.signal import WebhookIngestResponse
from sigmatic.server.services.ingest_service import (
    InvalidWebhookTokenError,
    SourceNotActiveError,
    SourceNotFoundError,
    ingest_webhook,
)

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


@api_ingest_router.post("/ingest/signal", status_code=202)
async def ingest_signal() -> dict:  # type: ignore[type-arg]
    """Ingest a pre-normalized signal via API key auth."""
    raise HTTPException(status_code=501, detail="API signal ingestion not yet implemented")
