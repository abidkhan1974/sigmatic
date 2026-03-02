"""API key authentication dependency for FastAPI routes."""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from sigmatic.server.database import get_db
from sigmatic.server.models.api_key import APIKey
from sigmatic.server.services.api_key_service import get_active_key, touch_last_used

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    raw_key: str | None = Security(_api_key_header),
    session: AsyncSession = Depends(get_db),
) -> APIKey:
    """Validate the X-API-Key header; raise 401 if missing or invalid.

    Inject this as a router-level dependency for all protected endpoints.
    The /v1/health and /v1/ingest/webhook/* routes are intentionally excluded.
    """
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    try:
        record = await get_active_key(session, raw_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable",
        )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    try:
        await touch_last_used(session, record.id)
    except Exception:
        pass  # Non-critical — don't fail the request if last_used update fails

    return record
