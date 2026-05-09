"""Add sales_items, sales_item_photos, sales_platform_listings tables.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── sales_items ───────────────────────────────────────────────────────────
    op.create_table(
        "sales_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(200)),
        sa.Column("brand_model", sa.String(200)),
        sa.Column("category", sa.String(100)),
        sa.Column("condition", sa.String(40)),
        sa.Column("description", sa.Text),
        sa.Column("internal_notes", sa.Text),
        sa.Column("target_price_chf", sa.Numeric(10, 2)),
        sa.Column("pickup_location", sa.String(200)),
        sa.Column("shipping_policy", sa.String(40)),
        sa.Column("status", sa.String(40), nullable=False, server_default="needs_info"),
        sa.Column("needs_action_reason", sa.Text),
        sa.Column("created_from", sa.String(40)),
        sa.Column("telegram_chat_id", sa.String(60)),
        sa.Column("telegram_message_id", sa.String(60)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sales_items_status", "sales_items", ["status"])
    op.create_index("ix_sales_items_created_at", "sales_items", ["created_at"])

    # ── sales_item_photos ─────────────────────────────────────────────────────
    op.create_table(
        "sales_item_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sales_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("photo_type", sa.String(40), nullable=False, server_default="original"),
        sa.Column("telegram_file_id", sa.String(200)),
        sa.Column("local_path", sa.String(500)),
        sa.Column("storage_url", sa.Text),
        sa.Column("caption", sa.Text),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sales_item_photos_item_id", "sales_item_photos", ["item_id"])

    # ── sales_platform_listings ───────────────────────────────────────────────
    op.create_table(
        "sales_platform_listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sales_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False, server_default="not_listed"),
        sa.Column("title", sa.String(200)),
        sa.Column("description", sa.Text),
        sa.Column("category_suggestion", sa.String(200)),
        sa.Column("price_chf", sa.Numeric(10, 2)),
        sa.Column("publish_url", sa.Text),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("sold_at", sa.DateTime(timezone=True)),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sales_platform_listings_item_id", "sales_platform_listings", ["item_id"])
    op.create_index("ix_sales_platform_listings_platform", "sales_platform_listings", ["platform"])
    op.create_unique_constraint(
        "uq_sales_platform_listings_item_platform",
        "sales_platform_listings",
        ["item_id", "platform"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_sales_platform_listings_item_platform", "sales_platform_listings", type_="unique")
    op.drop_index("ix_sales_platform_listings_platform", "sales_platform_listings")
    op.drop_index("ix_sales_platform_listings_item_id", "sales_platform_listings")
    op.drop_table("sales_platform_listings")

    op.drop_index("ix_sales_item_photos_item_id", "sales_item_photos")
    op.drop_table("sales_item_photos")

    op.drop_index("ix_sales_items_created_at", "sales_items")
    op.drop_index("ix_sales_items_status", "sales_items")
    op.drop_table("sales_items")
