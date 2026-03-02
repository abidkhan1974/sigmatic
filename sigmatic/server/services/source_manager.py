"""Source management service: create, list, get, update, delete, pause/resume."""

import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from sigmatic.server.models.base import generate_uuid
from sigmatic.server.models.source import Source
from sigmatic.server.schemas.source import SourceCreate, SourceUpdate


def _generate_webhook_token() -> str:
    """Generate a URL-safe webhook token (48 chars)."""
    return secrets.token_urlsafe(36)  # 36 bytes → 48 URL-safe chars


async def create_source(session: AsyncSession, body: SourceCreate) -> Source:
    """Create and persist a new source, generating a unique webhook token."""
    source = Source(
        source_id=generate_uuid(),
        name=body.name,
        type=body.type,
        schema_adapter=body.schema_adapter,
        config=body.config,
        throttle=body.throttle,
        webhook_token=_generate_webhook_token(),
        status="active",
    )
    session.add(source)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    await session.refresh(source)
    return source


async def list_sources(session: AsyncSession) -> list[Source]:
    """Return all sources ordered by creation date, newest first."""
    result = await session.execute(
        select(Source).order_by(Source.created_at.desc())
    )
    return list(result.scalars().all())


async def get_source(session: AsyncSession, source_id: str) -> Source | None:
    """Return a single source by ID, or None if not found."""
    result = await session.execute(
        select(Source).where(Source.source_id == source_id)
    )
    return result.scalar_one_or_none()


async def update_source(
    session: AsyncSession, source_id: str, body: SourceUpdate
) -> Source | None:
    """Apply a partial update to a source. Returns None if source not found."""
    source = await get_source(session, source_id)
    if source is None:
        return None

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(source, field, value)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    await session.refresh(source)
    return source


async def delete_source(session: AsyncSession, source_id: str) -> bool:
    """Delete a source. Returns True if deleted, False if not found."""
    source = await get_source(session, source_id)
    if source is None:
        return False
    await session.delete(source)
    await session.commit()
    return True


async def set_source_status(
    session: AsyncSession, source_id: str, status: str
) -> Source | None:
    """Set the status of a source (active / paused). Returns None if not found."""
    source = await get_source(session, source_id)
    if source is None:
        return None
    source.status = status
    await session.commit()
    await session.refresh(source)
    return source
