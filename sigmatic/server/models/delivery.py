"""Delivery SQLAlchemy model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from sigmatic.server.models.base import Base, generate_uuid


class Delivery(Base):
    """Tracks signal delivery attempts to routing destinations."""

    __tablename__ = "deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    signal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("signals.signal_id"), nullable=False, index=True
    )
    route_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("routing_rules.route_id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
