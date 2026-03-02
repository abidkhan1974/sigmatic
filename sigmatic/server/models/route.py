"""RoutingRule SQLAlchemy model."""

from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from sigmatic.server.models.base import Base, TimestampMixin, generate_uuid


class RoutingRule(Base, TimestampMixin):
    """Represents a signal routing rule."""

    __tablename__ = "routing_rules"

    route_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    destination: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    filters: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    retry_policy: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )
