"""Signal Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

# Canonical direction values accepted throughout the system
_VALID_DIRECTIONS = {"long", "short", "flat"}


class NormalizedSignal(BaseModel):
    """Output contract for all schema adapters.

    Adapters must produce a dict that satisfies this schema.
    Missing optional fields are stored as NULL on the Signal record.
    """

    symbol: str = Field(..., min_length=1, max_length=20)
    direction: str

    confidence: float | None = Field(None, ge=0.0, le=1.0)
    entry_zone: float | None = None
    stop_distance: float | None = None
    target: float | None = None
    strategy_id: str | None = Field(None, max_length=100)
    timeframe: str | None = Field(None, max_length=10)

    @field_validator("symbol")
    @classmethod
    def upper_symbol(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        canonical = v.strip().lower()
        if canonical not in _VALID_DIRECTIONS:
            raise ValueError(
                f"direction must be one of {sorted(_VALID_DIRECTIONS)}, got '{v}'"
            )
        return canonical


class WebhookIngestResponse(BaseModel):
    """Response body for POST /v1/ingest/webhook/{source_id}."""

    signal_id: str
    status: str
    symbol: str
    direction: str


class SignalResponse(BaseModel):
    """Full signal detail for GET /v1/signals endpoints."""

    signal_id: str
    source_id: str | None
    symbol: str
    direction: str
    confidence: float | None
    entry_zone: float | None
    stop_distance: float | None
    target: float | None
    strategy_id: str | None
    timeframe: str | None
    quality_score: float | None
    status: str
    metadata: dict[str, Any] | None = Field(None, alias="metadata_")
    ingested_at: datetime | None
    scored_at: datetime | None
    routed_at: datetime | None

    model_config = {"from_attributes": True, "populate_by_name": True}
