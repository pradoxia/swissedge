"""Add special_situation_id link to research_documents (W1 auto-acquisition).

Revision ID: k1f2g3h4i5j6
Revises: j0e1f2g3h4i5
Create Date: 2026-06-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "k1f2g3h4i5j6"
down_revision = "j0e1f2g3h4i5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "research_documents",
        sa.Column("special_situation_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_research_documents_special_situation_id",
        "research_documents",
        "special_situations",
        ["special_situation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "idx_research_documents_special_situation_id",
        "research_documents",
        ["special_situation_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_research_documents_special_situation_id", table_name="research_documents")
    op.drop_constraint(
        "fk_research_documents_special_situation_id", "research_documents", type_="foreignkey"
    )
    op.drop_column("research_documents", "special_situation_id")
