"""Add ResearchDocument body text fields.

Revision ID: h8c9d0e1f2g3
Revises: g7b8c9d0e1f2
Create Date: 2026-06-10
"""
from alembic import op
import sqlalchemy as sa

revision = "h8c9d0e1f2g3"
down_revision = "g7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("research_documents", sa.Column("body_text", sa.Text(), nullable=True))
    op.add_column("research_documents", sa.Column("body_text_excerpt", sa.Text(), nullable=True))
    op.add_column("research_documents", sa.Column("body_text_sha256", sa.String(length=64), nullable=True))
    op.add_column("research_documents", sa.Column("body_text_acquired_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("research_documents", sa.Column("body_text_status", sa.String(length=40), nullable=True))
    op.add_column("research_documents", sa.Column("body_text_error", sa.Text(), nullable=True))
    op.add_column("research_documents", sa.Column("body_text_size_bytes", sa.Integer(), nullable=True))
    op.create_index("idx_research_documents_body_text_status", "research_documents", ["body_text_status"])


def downgrade() -> None:
    op.drop_index("idx_research_documents_body_text_status", table_name="research_documents")
    op.drop_column("research_documents", "body_text_size_bytes")
    op.drop_column("research_documents", "body_text_error")
    op.drop_column("research_documents", "body_text_status")
    op.drop_column("research_documents", "body_text_acquired_at")
    op.drop_column("research_documents", "body_text_sha256")
    op.drop_column("research_documents", "body_text_excerpt")
    op.drop_column("research_documents", "body_text")
