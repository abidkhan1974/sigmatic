"""Signal management endpoints."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/signals")
async def list_signals() -> dict:
    """List recent signals with optional filters."""
    raise HTTPException(status_code=501, detail="Signal listing not yet implemented")


@router.get("/signals/{signal_id}")
async def get_signal(signal_id: str) -> dict:
    """Get full detail for a single signal."""
    raise HTTPException(status_code=501, detail="Signal detail not yet implemented")
