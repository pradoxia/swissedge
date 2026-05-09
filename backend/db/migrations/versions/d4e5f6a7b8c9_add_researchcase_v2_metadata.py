"""Add V2 metadata fields to research_cases.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("research_cases", sa.Column("source_origin_name", sa.Text(), nullable=True))
    op.add_column(
        "research_cases",
        sa.Column("investment_source_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("research_cases", sa.Column("intake_method", sa.String(length=50), nullable=True))
    op.add_column("research_cases", sa.Column("connector_key", sa.String(length=100), nullable=True))
    op.add_column("research_cases", sa.Column("intake_event_id", sa.String(length=100), nullable=True))
    op.add_column("research_cases", sa.Column("evidence_level", sa.String(length=50), nullable=True))
    op.add_column("research_cases", sa.Column("official_source_status", sa.String(length=50), nullable=True))
    op.add_column("research_cases", sa.Column("methodology_status", sa.String(length=50), nullable=True))
    op.add_column("research_cases", sa.Column("playbook_used", sa.String(length=100), nullable=True))
    op.add_column("research_cases", sa.Column("checklist_used", sa.String(length=100), nullable=True))
    op.add_column("research_cases", sa.Column("course_reference", sa.Text(), nullable=True))
    op.add_column("research_cases", sa.Column("duplicate_status", sa.String(length=50), nullable=True))
    op.add_column("research_cases", sa.Column("next_follow_up_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("research_cases", sa.Column("discarded_reason", sa.Text(), nullable=True))

    op.create_foreign_key(
        "fk_research_cases_investment_source_id",
        "research_cases",
        "investment_sources",
        ["investment_source_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_research_cases_investment_source_id", "research_cases", ["investment_source_id"])
    op.create_index("idx_research_cases_intake_method", "research_cases", ["intake_method"])
    op.create_index("idx_research_cases_evidence_level", "research_cases", ["evidence_level"])
    op.create_index("idx_research_cases_official_source_status", "research_cases", ["official_source_status"])
    op.create_index("idx_research_cases_methodology_status", "research_cases", ["methodology_status"])
    op.create_index("idx_research_cases_duplicate_status", "research_cases", ["duplicate_status"])
    op.create_index("idx_research_cases_next_follow_up_at", "research_cases", ["next_follow_up_at"])


def downgrade() -> None:
    op.drop_index("idx_research_cases_next_follow_up_at", table_name="research_cases")
    op.drop_index("idx_research_cases_duplicate_status", table_name="research_cases")
    op.drop_index("idx_research_cases_methodology_status", table_name="research_cases")
    op.drop_index("idx_research_cases_official_source_status", table_name="research_cases")
    op.drop_index("idx_research_cases_evidence_level", table_name="research_cases")
    op.drop_index("idx_research_cases_intake_method", table_name="research_cases")
    op.drop_index("idx_research_cases_investment_source_id", table_name="research_cases")
    op.drop_constraint("fk_research_cases_investment_source_id", "research_cases", type_="foreignkey")

    op.drop_column("research_cases", "discarded_reason")
    op.drop_column("research_cases", "next_follow_up_at")
    op.drop_column("research_cases", "duplicate_status")
    op.drop_column("research_cases", "course_reference")
    op.drop_column("research_cases", "checklist_used")
    op.drop_column("research_cases", "playbook_used")
    op.drop_column("research_cases", "methodology_status")
    op.drop_column("research_cases", "official_source_status")
    op.drop_column("research_cases", "evidence_level")
    op.drop_column("research_cases", "intake_event_id")
    op.drop_column("research_cases", "connector_key")
    op.drop_column("research_cases", "intake_method")
    op.drop_column("research_cases", "investment_source_id")
    op.drop_column("research_cases", "source_origin_name")
