"""Outcome recording endpoints."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/outcomes", status_code=201)
async def record_outcome() -> dict:
    """Record the outcome of a signal (hit/miss, P&L, R-multiple)."""
    raise HTTPException(status_code=501, detail="Outcome recording not yet implemented")


@router.get("/stats")
async def get_stats() -> dict:
    """Get pipeline-wide statistics."""
    raise HTTPException(status_code=501, detail="Stats not yet implemented")


@router.get("/stats/sources/{source_id}")
async def get_source_stats(source_id: str) -> dict:
    """Get statistics for a specific source."""
    raise HTTPException(
        status_code=501, detail="Per-source stats not yet implemented"
    )
