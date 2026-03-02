"""Signal ingestion endpoints.

Two routers with different auth requirements:
- webhook_router: public, authenticated via per-source webhook token (Issue #1)
- api_ingest_router: protected by X-API-Key (implemented in Phase 1)
"""

from fastapi import APIRouter, HTTPException

# Public — per-source token auth handled inside the handler (Issue #1)
webhook_router = APIRouter()

# Protected — requires X-API-Key (wired in app.py)
api_ingest_router = APIRouter()


@webhook_router.post("/ingest/webhook/{source_id}", status_code=202)
async def ingest_webhook(source_id: str) -> dict:
    """Receive a signal via webhook from a registered source."""
    raise HTTPException(status_code=501, detail="Webhook ingestion not yet implemented")


@api_ingest_router.post("/ingest/signal", status_code=202)
async def ingest_signal() -> dict:
    """Ingest a pre-normalized signal via API key auth."""
    raise HTTPException(status_code=501, detail="API signal ingestion not yet implemented")
