"""Add documentation extraction draft fields.

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-05-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "g7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documentation_extraction_fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("situation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("special_situations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_source_id", sa.String(100), nullable=False),
        sa.Column("document_key", sa.String(100), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_title", sa.Text(), nullable=True),
        sa.Column("field_key", sa.String(100), nullable=False),
        sa.Column("field_label", sa.Text(), nullable=False),
        sa.Column("extracted_value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source_snippet", sa.Text(), nullable=True),
        sa.Column("section_reference", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("reviewed_by", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_doc_extraction_situation", "documentation_extraction_fields", ["situation_id"])
    op.create_index(
        "idx_doc_extraction_candidate_document",
        "documentation_extraction_fields",
        ["candidate_source_id", "document_key"],
    )
    op.create_index("idx_doc_extraction_status", "documentation_extraction_fields", ["status"])


def downgrade() -> None:
    op.drop_index("idx_doc_extraction_status", table_name="documentation_extraction_fields")
    op.drop_index("idx_doc_extraction_candidate_document", table_name="documentation_extraction_fields")
    op.drop_index("idx_doc_extraction_situation", table_name="documentation_extraction_fields")
    op.drop_table("documentation_extraction_fields")
