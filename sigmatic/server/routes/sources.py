"""Source management endpoints."""

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from sigmatic.server.dependencies import DbSession
from sigmatic.server.schemas.source import SourceCreate, SourceResponse, SourceUpdate
from sigmatic.server.services import source_manager

router = APIRouter()


@router.post("/sources", status_code=201, response_model=SourceResponse)
async def create_source(body: SourceCreate, session: DbSession) -> SourceResponse:
    """Register a new signal source and generate its webhook token."""
    try:
        source = await source_manager.create_source(session, body)
    except IntegrityError:
        raise HTTPException(status_code=409, detail=f"Source name '{body.name}' already exists")
    return SourceResponse.model_validate(source)


@router.get("/sources", response_model=list[SourceResponse])
async def list_sources(session: DbSession) -> list[SourceResponse]:
    """List all registered signal sources."""
    sources = await source_manager.list_sources(session)
    return [SourceResponse.model_validate(s) for s in sources]


@router.get("/sources/{source_id}", response_model=SourceResponse)
async def get_source(source_id: str, session: DbSession) -> SourceResponse:
    """Get full detail for a single source."""
    source = await source_manager.get_source(session, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")
    return SourceResponse.model_validate(source)


@router.put("/sources/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: str, body: SourceUpdate, session: DbSession
) -> SourceResponse:
    """Update a source's configuration."""
    try:
        source = await source_manager.update_source(session, source_id, body)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Source name already taken")
    if source is None:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")
    return SourceResponse.model_validate(source)


@router.delete("/sources/{source_id}", status_code=204)
async def delete_source(source_id: str, session: DbSession) -> None:
    """Delete a source."""
    deleted = await source_manager.delete_source(session, source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")


@router.post("/sources/{source_id}/pause", response_model=SourceResponse)
async def pause_source(source_id: str, session: DbSession) -> SourceResponse:
    """Pause a source — it will stop accepting new signals."""
    source = await source_manager.set_source_status(session, source_id, "paused")
    if source is None:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")
    return SourceResponse.model_validate(source)


@router.post("/sources/{source_id}/resume", response_model=SourceResponse)
async def resume_source(source_id: str, session: DbSession) -> SourceResponse:
    """Resume a paused source."""
    source = await source_manager.set_source_status(session, source_id, "active")
    if source is None:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")
    return SourceResponse.model_validate(source)
