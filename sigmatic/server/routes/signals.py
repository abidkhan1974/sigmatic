"""Signal management endpoints."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from sigmatic.server.dependencies import DbSession
from sigmatic.server.schemas.signal import SignalResponse
from sigmatic.server.services import signal_service

router = APIRouter()

# Query param bounds
_MAX_LIMIT = 500
_DEFAULT_LIMIT = 50


@router.get("/signals", response_model=list[SignalResponse])
async def list_signals(
    session: DbSession,
    symbol: Annotated[str | None, Query(description="Filter by symbol (case-insensitive)")] = None,
    source_id: Annotated[str | None, Query(description="Filter by source ID")] = None,
    status: Annotated[str | None, Query(description="Filter by status (INGESTED, ADAPTER_ERROR, …)")] = None,
    direction: Annotated[str | None, Query(description="Filter by direction (long/short/flat)")] = None,
    limit: Annotated[int, Query(ge=1, le=_MAX_LIMIT, description="Page size")] = _DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0, description="Page offset")] = 0,
) -> list[SignalResponse]:
    """List recent signals with optional filters.

    Results are ordered newest-first. Use limit/offset for pagination.
    """
    signals = await signal_service.list_signals(
        session,
        symbol=symbol,
        source_id=source_id,
        status=status,
        direction=direction,
        limit=limit,
        offset=offset,
    )
    return [SignalResponse.model_validate(s) for s in signals]


@router.get("/signals/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: str, session: DbSession) -> SignalResponse:
    """Get full detail for a single signal."""
    signal = await signal_service.get_signal(session, signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail=f"Signal '{signal_id}' not found")
    return SignalResponse.model_validate(signal)
