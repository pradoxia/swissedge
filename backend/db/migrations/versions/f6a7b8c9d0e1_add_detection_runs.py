"""Add detection run visibility.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "detection_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(100), nullable=False, server_default="sec_edgar"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="running"),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("hours_back", sa.Integer(), nullable=True),
        sa.Column("raw_hits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parsed_filings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("classified_filings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unclassified_filings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("special_situations_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("runtime_seconds", sa.Float(), nullable=True),
        sa.Column("forms_checked_json", postgresql.JSONB(), nullable=True),
        sa.Column("per_form_summary_json", postgresql.JSONB(), nullable=True),
        sa.Column("summary_json", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_detection_runs_source_started_at", "detection_runs", ["source", "started_at"])
    op.create_index("idx_detection_runs_status", "detection_runs", ["status"])


def downgrade() -> None:
    op.drop_index("idx_detection_runs_status", table_name="detection_runs")
    op.drop_index("idx_detection_runs_source_started_at", table_name="detection_runs")
    op.drop_table("detection_runs")
