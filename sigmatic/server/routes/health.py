"""Health check endpoint."""

from fastapi import APIRouter
from sqlalchemy import text

from sigmatic.server.config import settings
from sigmatic.server.database import AsyncSessionLocal

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Check server health including database and Redis connectivity."""
    db_status = "disconnected"
    redis_status = "disconnected"

    # Check database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        pass

    # Check Redis
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url, socket_timeout=2)
        await r.ping()
        await r.aclose()
        redis_status = "connected"
    except Exception:
        pass

    return {
        "status": "healthy",
        "database": db_status,
        "redis": redis_status,
        "version": "0.1.0",
    }
