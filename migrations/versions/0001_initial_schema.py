"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # sources table
    op.create_table(
        "sources",
        sa.Column("source_id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("schema_adapter", sa.String(50), nullable=False, server_default="generic"),
        sa.Column("config", postgresql.JSON, nullable=True),
        sa.Column("throttle", postgresql.JSON, nullable=True),
        sa.Column("trust_score", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("stats", postgresql.JSON, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("webhook_token", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("webhook_token"),
    )
    op.create_index("ix_sources_status", "sources", ["status"])

    # signals table
    op.create_table(
        "signals",
        sa.Column("signal_id", sa.String(36), primary_key=True),
        sa.Column(
            "source_id",
            sa.String(36),
            sa.ForeignKey("sources.source_id"),
            nullable=True,
        ),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("entry_zone", sa.Float, nullable=True),
        sa.Column("stop_distance", sa.Float, nullable=True),
        sa.Column("target", sa.Float, nullable=True),
        sa.Column("strategy_id", sa.String(100), nullable=True),
        sa.Column("timeframe", sa.String(10), nullable=True),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="INGESTED"),
        sa.Column("route_destinations", postgresql.JSON, nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("routed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_signals_source_id", "signals", ["source_id"])
    op.create_index("ix_signals_symbol", "signals", ["symbol"])
    op.create_index("ix_signals_status", "signals", ["status"])

    # routing_rules table
    op.create_table(
        "routing_rules",
        sa.Column("route_id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("destination", postgresql.JSON, nullable=False),
        sa.Column("filters", postgresql.JSON, nullable=True),
        sa.Column("retry_policy", postgresql.JSON, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_routing_rules_status", "routing_rules", ["status"])

    # deliveries table
    op.create_table(
        "deliveries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "signal_id",
            sa.String(36),
            sa.ForeignKey("signals.signal_id"),
            nullable=False,
        ),
        sa.Column(
            "route_id",
            sa.String(36),
            sa.ForeignKey("routing_rules.route_id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("response_code", sa.Integer, nullable=True),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_deliveries_signal_id", "deliveries", ["signal_id"])
    op.create_index("ix_deliveries_route_id", "deliveries", ["route_id"])

    # outcomes table
    op.create_table(
        "outcomes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "signal_id",
            sa.String(36),
            sa.ForeignKey("signals.signal_id"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            sa.String(36),
            sa.ForeignKey("sources.source_id"),
            nullable=True,
        ),
        sa.Column("hit", sa.Boolean, nullable=True),
        sa.Column("pnl", sa.Float, nullable=True),
        sa.Column("r_multiple", sa.Float, nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("recorded_by", sa.String(100), nullable=True),
    )
    op.create_index("ix_outcomes_signal_id", "outcomes", ["signal_id"])

    # api_keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key_hash", sa.String(128), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.UniqueConstraint("key_hash"),
    )

    # audit_log table
    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("context", postgresql.JSON, nullable=True),
    )
    op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("api_keys")
    op.drop_table("outcomes")
    op.drop_table("deliveries")
    op.drop_table("routing_rules")
    op.drop_table("signals")
    op.drop_table("sources")
