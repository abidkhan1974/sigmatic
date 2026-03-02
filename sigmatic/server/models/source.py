"""Source SQLAlchemy model."""

from typing import Any

from sqlalchemy import Float, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from sigmatic.server.models.base import Base, TimestampMixin, generate_uuid


class Source(Base, TimestampMixin):
    """Represents a signal source (webhook, API, strategy, etc.)."""

    __tablename__ = "sources"

    source_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False)  # webhook/api/internal
    schema_adapter: Mapped[str] = mapped_column(
        String(50), nullable=False, default="generic"
    )
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    throttle: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    stats: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )
    webhook_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
