"""Outcome SQLAlchemy model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from sigmatic.server.models.base import Base, generate_uuid


class Outcome(Base):
    """Records the outcome of a signal (hit/miss, P&L, R-multiple)."""

    __tablename__ = "outcomes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    signal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("signals.signal_id"), nullable=False, index=True
    )
    source_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sources.source_id"), nullable=True
    )
    hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    r_multiple: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    recorded_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
