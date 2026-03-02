"""Webhook ingestion pipeline service.

Pipeline:
  1. Fetch + validate source (exists, active)
  2. Validate per-source webhook token (constant-time comparison)
  3. Run schema adapter → NormalizedSignal
  4. Persist Signal record with final status
  5. Return Signal (always 202; errors are captured in status / metadata)
"""

import hmac
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from sigmatic.server.adapters import get_adapter
from sigmatic.server.models.base import generate_uuid
from sigmatic.server.models.signal import Signal
from sigmatic.server.schemas.signal import NormalizedSignal
from sigmatic.server.services.source_manager import get_source

_UTC = timezone.utc


# ---------------------------------------------------------------------------
# Domain exceptions — caught in the route handler and mapped to HTTP errors
# ---------------------------------------------------------------------------


class SourceNotFoundError(Exception):
    pass


class SourceNotActiveError(Exception):
    pass


class InvalidWebhookTokenError(Exception):
    pass


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


async def ingest_webhook(
    session: AsyncSession,
    source_id: str,
    webhook_token: str | None,
    raw_payload: dict[str, Any],
) -> Signal:
    """Run the full ingestion pipeline for one webhook call.

    Domain exceptions (SourceNotFoundError, SourceNotActiveError,
    InvalidWebhookTokenError) are propagated to the caller.

    Adapter / validation errors are captured inside the Signal record
    (status = ADAPTER_ERROR or VALIDATION_ERROR) — the function still
    returns 202 so the raw payload is never silently dropped.
    """
    # 1 — Validate source
    source = await get_source(session, source_id)
    if source is None:
        raise SourceNotFoundError(source_id)
    if source.status != "active":
        raise SourceNotActiveError(source_id)

    # 2 — Validate webhook token (constant-time to resist timing attacks)
    expected = source.webhook_token or ""
    provided = webhook_token or ""
    if not hmac.compare_digest(expected, provided):
        raise InvalidWebhookTokenError()

    # 3 — Attempt normalization
    raw_str = json.dumps(raw_payload)
    status = "INGESTED"
    error_meta: dict[str, Any] | None = None
    normalized: dict[str, Any] = {}

    try:
        adapter = get_adapter(source.schema_adapter)
        normalized = adapter.normalize(raw_payload, source.config or {})
    except Exception as exc:
        status = "ADAPTER_ERROR"
        error_meta = {"stage": "adapter", "error": str(exc)}

    if status == "INGESTED":
        try:
            validated = NormalizedSignal(**normalized)
            normalized = validated.model_dump(exclude_none=True)
        except (ValidationError, Exception) as exc:
            status = "VALIDATION_ERROR"
            error_meta = {"stage": "validation", "error": str(exc), "normalized": normalized}

    # 4 — Persist (always, even on error — raw payload is preserved)
    signal = Signal(
        signal_id=generate_uuid(),
        source_id=source.source_id,
        symbol=normalized.get("symbol", "UNKNOWN"),
        direction=normalized.get("direction", "unknown"),
        confidence=normalized.get("confidence"),
        entry_zone=normalized.get("entry_zone"),
        stop_distance=normalized.get("stop_distance"),
        target=normalized.get("target"),
        strategy_id=normalized.get("strategy_id"),
        timeframe=normalized.get("timeframe"),
        status=status,
        raw_payload=raw_str,
        metadata_=error_meta,
        ingested_at=datetime.now(_UTC),
    )
    session.add(signal)
    await session.commit()
    await session.refresh(signal)

    # 5 — Broadcast to any connected WebSocket clients (fire-and-forget)
    from sigmatic.server.websocket.manager import manager  # local import avoids circular deps

    await manager.broadcast(
        {
            "signal_id": signal.signal_id,
            "status": signal.status,
            "symbol": signal.symbol,
            "direction": signal.direction,
            "source_id": signal.source_id,
            "ingested_at": signal.ingested_at.isoformat() if signal.ingested_at else None,
        }
    )

    return signal
