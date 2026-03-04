"""Signal quality scorer.

Computes a quality_score in [0, 1] for each ingested signal and
updates Signal.quality_score + Signal.status → SCORED.

Score formula
-------------
    quality_score = source_trust × signal_confidence

where:
    source_trust   = source.trust_score       (default 0.5 if source unknown)
    signal_confidence = signal.confidence     (default 0.5 if not provided)

Both inputs are clamped to [0, 1].  The product is rounded to 4 dp.

This is a simple multiplicative model intentionally left extensible:
future revisions can incorporate historical hit-rate from outcomes.
"""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from sigmatic.server.models.signal import Signal
from sigmatic.server.services.source_manager import get_source

_UTC = timezone.utc

_DEFAULT_TRUST = 0.5
_DEFAULT_CONFIDENCE = 0.5


async def score_signal(session: AsyncSession, signal: Signal) -> Signal:
    """Compute and persist quality_score for *signal*.

    Looks up the source's trust_score; uses defaults when fields are absent.
    Updates signal in-place and commits.
    """
    if signal.source_id:
        source = await get_source(session, signal.source_id)
        trust = float(source.trust_score) if source and source.trust_score is not None else _DEFAULT_TRUST
    else:
        trust = _DEFAULT_TRUST

    confidence = float(signal.confidence) if signal.confidence is not None else _DEFAULT_CONFIDENCE

    quality_score = round(
        max(0.0, min(1.0, trust)) * max(0.0, min(1.0, confidence)),
        4,
    )

    signal.quality_score = quality_score
    signal.status = "SCORED"
    signal.scored_at = datetime.now(_UTC)

    await session.commit()
    await session.refresh(signal)
    return signal
