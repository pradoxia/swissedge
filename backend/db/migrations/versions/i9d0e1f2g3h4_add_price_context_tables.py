"""Add price context tables.

Revision ID: i9d0e1f2g3h4
Revises: h8c9d0e1f2g3
Create Date: 2026-06-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "i9d0e1f2g3h4"
down_revision = "h8c9d0e1f2g3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("latest_close_price", sa.Numeric(18, 6), nullable=False),
        sa.Column("close_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("market_cap", sa.Numeric(24, 2), nullable=True),
        sa.Column("average_daily_volume", sa.Numeric(24, 2), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("safe_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_price_snapshots_ticker", "price_snapshots", ["ticker"])
    op.create_index("idx_price_snapshots_provider", "price_snapshots", ["provider"])
    op.create_index("idx_price_snapshots_close_date", "price_snapshots", ["close_date"])

    op.create_table(
        "case_price_contexts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("special_situation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("research_case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ticker", sa.String(length=20), nullable=True),
        sa.Column("offer_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("offer_price_source", sa.Text(), nullable=True),
        sa.Column("price_snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("latest_close_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("latest_close_date", sa.Date(), nullable=True),
        sa.Column("estimated_spread_pct", sa.Numeric(18, 6), nullable=True),
        sa.Column("spread_status", sa.String(length=40), nullable=False),
        sa.Column("status_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["special_situation_id"], ["special_situations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["research_case_id"], ["research_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["price_snapshot_id"], ["price_snapshots.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_case_price_contexts_special_situation_id", "case_price_contexts", ["special_situation_id"])
    op.create_index("idx_case_price_contexts_research_case_id", "case_price_contexts", ["research_case_id"])
    op.create_index("idx_case_price_contexts_ticker", "case_price_contexts", ["ticker"])
    op.create_index("idx_case_price_contexts_spread_status", "case_price_contexts", ["spread_status"])


def downgrade() -> None:
    op.drop_index("idx_case_price_contexts_spread_status", table_name="case_price_contexts")
    op.drop_index("idx_case_price_contexts_ticker", table_name="case_price_contexts")
    op.drop_index("idx_case_price_contexts_research_case_id", table_name="case_price_contexts")
    op.drop_index("idx_case_price_contexts_special_situation_id", table_name="case_price_contexts")
    op.drop_table("case_price_contexts")
    op.drop_index("idx_price_snapshots_close_date", table_name="price_snapshots")
    op.drop_index("idx_price_snapshots_provider", table_name="price_snapshots")
    op.drop_index("idx_price_snapshots_ticker", table_name="price_snapshots")
    op.drop_table("price_snapshots")
