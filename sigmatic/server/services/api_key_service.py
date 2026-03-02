"""API key creation, hashing, and verification service."""

import hashlib
import secrets
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from sigmatic.server.models.api_key import APIKey
from sigmatic.server.models.base import generate_uuid

# API keys have 256 bits of entropy, so SHA-256 (no salt) is appropriate here.
# bcrypt is designed for low-entropy secrets (passwords); for random 32-byte keys
# SHA-256 provides equivalent security with much better request-time performance.
_PREFIX = "smk_"


def generate_key() -> str:
    """Generate a new raw API key with smk_ prefix."""
    return f"{_PREFIX}{secrets.token_hex(32)}"


def hash_key(raw_key: str) -> str:
    """Return the SHA-256 hex digest of a raw API key."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def create_api_key(session: AsyncSession, name: str) -> tuple[str, APIKey]:
    """Create and persist a new API key.

    Returns:
        (raw_key, record) — raw_key is shown once and never stored.
    """
    raw_key = generate_key()
    record = APIKey(
        id=generate_uuid(),
        key_hash=hash_key(raw_key),
        name=name,
        status="active",
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return raw_key, record


async def get_active_key(session: AsyncSession, raw_key: str) -> APIKey | None:
    """Look up an active API key record by its raw value."""
    result = await session.execute(
        select(APIKey).where(
            APIKey.key_hash == hash_key(raw_key),
            APIKey.status == "active",
        )
    )
    return result.scalar_one_or_none()


async def touch_last_used(session: AsyncSession, api_key_id: str) -> None:
    """Update last_used_at for an API key after successful authentication."""
    await session.execute(
        update(APIKey)
        .where(APIKey.id == api_key_id)
        .values(last_used_at=datetime.now(timezone.utc))
    )
    await session.commit()
