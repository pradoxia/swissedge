"""Add agent_runs, ai_usage tables and extend investment_sources.

Revision ID: a1b2c3d4e5f6
Revises: 05bd29309df7
Create Date: 2026-04-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = "05bd29309df7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── agent_runs ────────────────────────────────────────────────────────────
    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("module", sa.String(200)),
        sa.Column("runtime", sa.String(50), nullable=False),
        sa.Column("trigger_source", sa.String(50), nullable=False, server_default="api_call"),
        sa.Column("task_name", sa.String(200)),
        sa.Column("input_summary", sa.Text),
        sa.Column("output_summary", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="started"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("model_used", sa.String(100)),
        sa.Column("input_tokens", sa.Integer),
        sa.Column("output_tokens", sa.Integer),
        sa.Column("estimated_cost", sa.Numeric(12, 6)),
        sa.Column("files_touched", postgresql.JSONB),
        sa.Column("api_calls_made", postgresql.JSONB),
        sa.Column("database_records_created", postgresql.JSONB),
        sa.Column("error_message", sa.Text),
        sa.Column("human_approval_required", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("human_approved", sa.Boolean),
        sa.Column("final_outcome", sa.Text),
        sa.Column("outcome_score", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agent_runs_agent_name", "agent_runs", ["agent_name"])
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])
    op.create_index("ix_agent_runs_started_at", "agent_runs", ["started_at"])

    # ── ai_usage ──────────────────────────────────────────────────────────────
    op.create_table(
        "ai_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_runs.id", ondelete="SET NULL")),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt_name", sa.String(200)),
        sa.Column("input_tokens", sa.Integer),
        sa.Column("output_tokens", sa.Integer),
        sa.Column("total_tokens", sa.Integer),
        sa.Column("estimated_cost", sa.Numeric(12, 6)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ai_usage_agent_name", "ai_usage", ["agent_name"])
    op.create_index("ix_ai_usage_model", "ai_usage", ["model"])

    # ── investment_sources: new columns ───────────────────────────────────────
    op.add_column("investment_sources", sa.Column("description", sa.Text))
    op.add_column("investment_sources", sa.Column("market", sa.String(100)))
    op.add_column("investment_sources", sa.Column("jurisdiction", sa.String(100)))
    op.add_column("investment_sources", sa.Column("priority", sa.Integer, server_default="5"))
    op.add_column("investment_sources", sa.Column("requires_api_key", sa.Boolean, server_default="false"))
    op.add_column("investment_sources", sa.Column("access_method", sa.String(50)))
    op.add_column("investment_sources", sa.Column("query_template", sa.Text))
    op.add_column("investment_sources", sa.Column("last_success", sa.DateTime(timezone=True)))
    op.add_column("investment_sources", sa.Column("last_error", sa.Text))


def downgrade() -> None:
    # Remove investment_sources extensions
    for col in ["description", "market", "jurisdiction", "priority",
                 "requires_api_key", "access_method", "query_template",
                 "last_success", "last_error"]:
        op.drop_column("investment_sources", col)

    op.drop_index("ix_ai_usage_model", "ai_usage")
    op.drop_index("ix_ai_usage_agent_name", "ai_usage")
    op.drop_table("ai_usage")

    op.drop_index("ix_agent_runs_started_at", "agent_runs")
    op.drop_index("ix_agent_runs_status", "agent_runs")
    op.drop_index("ix_agent_runs_agent_name", "agent_runs")
    op.drop_table("agent_runs")
