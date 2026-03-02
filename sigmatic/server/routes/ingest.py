"""Signal ingestion endpoints."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/ingest/webhook/{source_id}", status_code=202)
async def ingest_webhook(source_id: str) -> dict:
    """Receive a signal via webhook from a registered source."""
    raise HTTPException(status_code=501, detail="Webhook ingestion not yet implemented")


@router.post("/ingest/signal", status_code=202)
async def ingest_signal() -> dict:
    """Ingest a pre-normalized signal via API."""
    raise HTTPException(status_code=501, detail="API signal ingestion not yet implemented")
