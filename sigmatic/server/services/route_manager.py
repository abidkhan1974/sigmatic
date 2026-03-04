"""Routing rule service: CRUD and filter-matching helpers."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sigmatic.server.models.base import generate_uuid
from sigmatic.server.models.route import RoutingRule
from sigmatic.server.schemas.route import RouteCreate, RouteUpdate


async def create_route(session: AsyncSession, body: RouteCreate) -> RoutingRule:
    """Create and persist a new routing rule."""
    rule = RoutingRule(
        route_id=generate_uuid(),
        name=body.name,
        destination=body.destination,
        filters=body.filters,
        retry_policy=body.retry_policy,
        status="active",
    )
    session.add(rule)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    await session.refresh(rule)
    return rule


async def list_routes(session: AsyncSession) -> list[RoutingRule]:
    """Return all routing rules, newest first."""
    result = await session.execute(
        select(RoutingRule).order_by(RoutingRule.created_at.desc())
    )
    return list(result.scalars().all())


async def get_route(session: AsyncSession, route_id: str) -> RoutingRule | None:
    """Return a routing rule by ID, or None if not found."""
    result = await session.execute(
        select(RoutingRule).where(RoutingRule.route_id == route_id)
    )
    return result.scalar_one_or_none()


async def update_route(
    session: AsyncSession, route_id: str, body: RouteUpdate
) -> RoutingRule | None:
    """Apply a partial update. Returns None if not found."""
    rule = await get_route(session, route_id)
    if rule is None:
        return None
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await session.commit()
    await session.refresh(rule)
    return rule


async def delete_route(session: AsyncSession, route_id: str) -> bool:
    """Delete a routing rule. Returns True if deleted, False if not found."""
    rule = await get_route(session, route_id)
    if rule is None:
        return False
    await session.delete(rule)
    await session.commit()
    return True


async def set_route_status(
    session: AsyncSession, route_id: str, status: str
) -> RoutingRule | None:
    """Set status to active or paused. Returns None if not found."""
    rule = await get_route(session, route_id)
    if rule is None:
        return None
    rule.status = status
    await session.commit()
    await session.refresh(rule)
    return rule


def matches_signal(rule: RoutingRule, signal_data: dict) -> tuple[bool, str]:
    """Check whether *signal_data* satisfies *rule.filters*.

    signal_data keys: symbol, direction, source_id, quality_score.

    Returns (matched, reason_string).
    """
    if rule.status != "active":
        return False, "rule is paused"

    f = rule.filters or {}

    allowed_symbols = f.get("symbols")
    if allowed_symbols and signal_data.get("symbol") not in allowed_symbols:
        return False, f"symbol {signal_data.get('symbol')!r} not in {allowed_symbols}"

    allowed_dirs = f.get("directions")
    if allowed_dirs and signal_data.get("direction") not in allowed_dirs:
        return False, f"direction {signal_data.get('direction')!r} not in {allowed_dirs}"

    allowed_sources = f.get("source_ids")
    if allowed_sources and signal_data.get("source_id") not in allowed_sources:
        return False, "source_id not in allowed list"

    min_q = f.get("min_quality_score")
    if min_q is not None:
        qs = signal_data.get("quality_score") or 0.0
        if qs < min_q:
            return False, f"quality_score {qs:.3f} < min {min_q}"

    return True, "all filters matched"
