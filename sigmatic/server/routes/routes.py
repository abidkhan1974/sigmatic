"""Routing rule management endpoints."""

from fastapi import APIRouter, HTTPException

from sigmatic.server.dependencies import DbSession
from sigmatic.server.schemas.route import (
    RouteCreate,
    RouteResponse,
    RouteTestResult,
    RouteUpdate,
)
from sigmatic.server.services import route_manager, signal_service

router = APIRouter()


@router.get("/routes", response_model=list[RouteResponse])
async def list_routes(session: DbSession) -> list[RouteResponse]:
    """List all routing rules."""
    rules = await route_manager.list_routes(session)
    return [RouteResponse.model_validate(r) for r in rules]


@router.post("/routes", status_code=201, response_model=RouteResponse)
async def create_route(body: RouteCreate, session: DbSession) -> RouteResponse:
    """Create a new routing rule."""
    if not body.destination.get("url"):
        raise HTTPException(status_code=422, detail="destination.url is required")
    rule = await route_manager.create_route(session, body)
    return RouteResponse.model_validate(rule)


@router.get("/routes/{route_id}", response_model=RouteResponse)
async def get_route(route_id: str, session: DbSession) -> RouteResponse:
    """Get a single routing rule by ID."""
    rule = await route_manager.get_route(session, route_id)
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")
    return RouteResponse.model_validate(rule)


@router.put("/routes/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: str, body: RouteUpdate, session: DbSession
) -> RouteResponse:
    """Update a routing rule (partial update, all fields optional)."""
    rule = await route_manager.update_route(session, route_id, body)
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")
    return RouteResponse.model_validate(rule)


@router.delete("/routes/{route_id}", status_code=204)
async def delete_route(route_id: str, session: DbSession) -> None:
    """Delete a routing rule."""
    deleted = await route_manager.delete_route(session, route_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")


@router.post("/routes/{route_id}/pause", response_model=RouteResponse)
async def pause_route(route_id: str, session: DbSession) -> RouteResponse:
    """Pause a routing rule (stop matching signals)."""
    rule = await route_manager.set_route_status(session, route_id, "paused")
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")
    return RouteResponse.model_validate(rule)


@router.post("/routes/{route_id}/resume", response_model=RouteResponse)
async def resume_route(route_id: str, session: DbSession) -> RouteResponse:
    """Resume a paused routing rule."""
    rule = await route_manager.set_route_status(session, route_id, "active")
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")
    return RouteResponse.model_validate(rule)


@router.post("/routes/{route_id}/test", response_model=RouteTestResult)
async def test_route(
    route_id: str, signal_id: str, session: DbSession
) -> RouteTestResult:
    """Test whether a routing rule matches a given signal.

    Query param: signal_id — the signal to evaluate against the rule.
    """
    rule = await route_manager.get_route(session, route_id)
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Route '{route_id}' not found")

    signal = await signal_service.get_signal(session, signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail=f"Signal '{signal_id}' not found")

    signal_data = {
        "symbol": signal.symbol,
        "direction": signal.direction,
        "source_id": signal.source_id,
        "quality_score": signal.quality_score,
    }
    matched, reason = route_manager.matches_signal(rule, signal_data)
    return RouteTestResult(route_id=route_id, matched=matched, reason=reason)
