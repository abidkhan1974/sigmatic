"""Routing rule management endpoints."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/routes")
async def list_routes() -> dict:
    """List all routing rules."""
    raise HTTPException(status_code=501, detail="Route listing not yet implemented")


@router.post("/routes", status_code=201)
async def create_route() -> dict:
    """Create a new routing rule."""
    raise HTTPException(status_code=501, detail="Route creation not yet implemented")


@router.put("/routes/{route_id}")
async def update_route(route_id: str) -> dict:
    """Update a routing rule."""
    raise HTTPException(status_code=501, detail="Route update not yet implemented")


@router.delete("/routes/{route_id}", status_code=204)
async def delete_route(route_id: str) -> None:
    """Delete a routing rule."""
    raise HTTPException(status_code=501, detail="Route deletion not yet implemented")


@router.post("/routes/{route_id}/test")
async def test_route(route_id: str) -> dict:
    """Test a routing rule with a sample signal."""
    raise HTTPException(status_code=501, detail="Route testing not yet implemented")
