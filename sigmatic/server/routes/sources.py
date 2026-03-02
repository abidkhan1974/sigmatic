"""Source management endpoints."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/sources")
async def list_sources() -> dict:
    """List all registered signal sources."""
    raise HTTPException(status_code=501, detail="Source listing not yet implemented")


@router.post("/sources", status_code=201)
async def create_source() -> dict:
    """Register a new signal source."""
    raise HTTPException(status_code=501, detail="Source creation not yet implemented")


@router.get("/sources/{source_id}")
async def get_source(source_id: str) -> dict:
    """Get detail for a single source."""
    raise HTTPException(status_code=501, detail="Source detail not yet implemented")


@router.put("/sources/{source_id}")
async def update_source(source_id: str) -> dict:
    """Update a source's configuration."""
    raise HTTPException(status_code=501, detail="Source update not yet implemented")


@router.delete("/sources/{source_id}", status_code=204)
async def delete_source(source_id: str) -> None:
    """Delete a source."""
    raise HTTPException(status_code=501, detail="Source deletion not yet implemented")


@router.post("/sources/{source_id}/pause")
async def pause_source(source_id: str) -> dict:
    """Pause a source from ingesting signals."""
    raise HTTPException(status_code=501, detail="Source pause not yet implemented")


@router.post("/sources/{source_id}/resume")
async def resume_source(source_id: str) -> dict:
    """Resume a paused source."""
    raise HTTPException(status_code=501, detail="Source resume not yet implemented")
