"""FastAPI application factory."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sigmatic.server.middleware.auth import require_api_key
from sigmatic.server.routes.health import router as health_router
from sigmatic.server.routes.ingest import api_ingest_router, webhook_router
from sigmatic.server.routes.outcomes import router as outcomes_router
from sigmatic.server.routes.routes import router as routes_router
from sigmatic.server.routes.signals import router as signals_router
from sigmatic.server.routes.sources import router as sources_router


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    """Application lifespan: startup and shutdown events."""
    yield
    from sigmatic.server.database import engine

    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Sigmatic",
        description="Signal aggregation, quality scoring & routing infrastructure for traders",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _auth = [Depends(require_api_key)]

    # Public — no auth
    app.include_router(health_router, prefix="/v1", tags=["health"])

    # Webhook ingest: public, per-source token auth handled inside the handler (Issue #1)
    app.include_router(webhook_router, prefix="/v1", tags=["ingestion"])
    # API signal ingestion: requires API key
    app.include_router(api_ingest_router, prefix="/v1", tags=["ingestion"], dependencies=_auth)

    # All other routes require a valid API key
    app.include_router(signals_router, prefix="/v1", tags=["signals"], dependencies=_auth)
    app.include_router(sources_router, prefix="/v1", tags=["sources"], dependencies=_auth)
    app.include_router(routes_router, prefix="/v1", tags=["routes"], dependencies=_auth)
    app.include_router(outcomes_router, prefix="/v1", tags=["outcomes"], dependencies=_auth)

    monitor_dir = Path(__file__).parent.parent / "monitor"
    if monitor_dir.exists():
        app.mount("/monitor", StaticFiles(directory=str(monitor_dir), html=True), name="monitor")

    return app


app = create_app()
