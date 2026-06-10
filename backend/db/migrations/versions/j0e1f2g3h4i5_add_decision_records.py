"""Add decision records.

Revision ID: j0e1f2g3h4i5
Revises: i9d0e1f2g3h4
Create Date: 2026-06-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "j0e1f2g3h4i5"
down_revision = "i9d0e1f2g3h4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decision_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("special_situation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("research_case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("source_surface", sa.String(length=100), nullable=True),
        sa.Column("safe_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(special_situation_id IS NOT NULL AND research_case_id IS NULL) OR "
            "(special_situation_id IS NULL AND research_case_id IS NOT NULL)",
            name="ck_decision_records_exactly_one_target",
        ),
        sa.ForeignKeyConstraint(["special_situation_id"], ["special_situations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["research_case_id"], ["research_cases.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_decision_records_special_situation_id", "decision_records", ["special_situation_id"])
    op.create_index("idx_decision_records_research_case_id", "decision_records", ["research_case_id"])
    op.create_index("idx_decision_records_outcome", "decision_records", ["outcome"])
    op.create_index("idx_decision_records_created_at", "decision_records", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_decision_records_created_at", table_name="decision_records")
    op.drop_index("idx_decision_records_outcome", table_name="decision_records")
    op.drop_index("idx_decision_records_research_case_id", table_name="decision_records")
    op.drop_index("idx_decision_records_special_situation_id", table_name="decision_records")
    op.drop_table("decision_records")
