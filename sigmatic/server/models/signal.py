"""Signal SQLAlchemy model."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from sigmatic.server.models.base import Base, TimestampMixin, generate_uuid


class Signal(Base, TimestampMixin):
    """Represents an ingested trading signal."""

    __tablename__ = "signals"

    signal_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sources.source_id"), nullable=True, index=True
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # long/short/flat
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    entry_zone: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    target: Mapped[float | None] = mapped_column(Float, nullable=True)
    strategy_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timeframe: Mapped[str | None] = mapped_column(String(10), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="INGESTED", index=True
    )
    route_destinations: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    ingested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scored_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    routed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
