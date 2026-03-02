"""Signal query service: list, detail, and lookup helpers."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sigmatic.server.models.signal import Signal


async def list_signals(
    session: AsyncSession,
    *,
    symbol: str | None = None,
    source_id: str | None = None,
    status: str | None = None,
    direction: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Signal]:
    """Return signals matching optional filters, newest first."""
    query = select(Signal)

    if symbol is not None:
        query = query.where(Signal.symbol == symbol.strip().upper())
    if source_id is not None:
        query = query.where(Signal.source_id == source_id)
    if status is not None:
        query = query.where(Signal.status == status.upper())
    if direction is not None:
        query = query.where(Signal.direction == direction.strip().lower())

    query = query.order_by(Signal.ingested_at.desc()).limit(limit).offset(offset)

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_signal(session: AsyncSession, signal_id: str) -> Signal | None:
    """Return a single signal by ID, or None if not found."""
    result = await session.execute(
        select(Signal).where(Signal.signal_id == signal_id)
    )
    return result.scalar_one_or_none()
