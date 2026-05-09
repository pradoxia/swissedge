"""Add investment research platform tables.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── research_cases ────────────────────────────────────────────────────────
    op.create_table(
        "research_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("situation_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("special_situations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="detected"),
        sa.Column("brief", postgresql.JSONB),
        sa.Column("brief_version", sa.String(20)),
        sa.Column("playbook_version", sa.String(100)),
        sa.Column("model_used", sa.String(100)),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text),
        sa.Column("disclaimer", sa.Text, nullable=False,
                  server_default="Este análisis es educativo. No es asesoramiento financiero."),
        sa.Column("investment_readiness", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_research_cases_situation_id", "research_cases", ["situation_id"])
    op.create_index("idx_research_cases_status", "research_cases", ["status"])
    op.create_index("idx_research_cases_investment_readiness", "research_cases", ["investment_readiness"])

    # ── research_tasks ────────────────────────────────────────────────────────
    op.create_table(
        "research_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("research_case_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="3"),
        sa.Column("source", sa.String(20)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_research_tasks_case_id", "research_tasks", ["research_case_id"])
    op.create_index("idx_research_tasks_status", "research_tasks", ["status"])

    # ── historical_cases ──────────────────────────────────────────────────────
    op.create_table(
        "historical_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.Text, nullable=False),
        sa.Column("situation_type", sa.String(100), nullable=False),
        sa.Column("event_date_approx", sa.String(20)),
        sa.Column("seed_notes", sa.Text),
        sa.Column("course_chapter_ref", sa.Integer),
        sa.Column("reconstruction", postgresql.JSONB),
        sa.Column("status", sa.String(50), nullable=False, server_default="seed"),
        sa.Column("linked_situation_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("special_situations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("disclaimer", sa.Text, nullable=False,
                  server_default="Este análisis es educativo. No es asesoramiento financiero."),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_historical_cases_status", "historical_cases", ["status"])
    op.create_index("idx_historical_cases_situation_type", "historical_cases", ["situation_type"])
    op.create_index("idx_historical_cases_linked_situation_id", "historical_cases", ["linked_situation_id"])

    # ── research_documents ────────────────────────────────────────────────────
    op.create_table(
        "research_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("research_case_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_cases.id", ondelete="CASCADE"), nullable=True),
        sa.Column("historical_case_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("historical_cases.id", ondelete="CASCADE"), nullable=True),
        sa.Column("doc_type", sa.String(50)),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("title", sa.Text),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("summary", sa.Text),
        sa.Column("added_by", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_research_documents_case_id", "research_documents", ["research_case_id"])
    op.create_index("idx_research_documents_doc_type", "research_documents", ["doc_type"])

    # ── research_sources ──────────────────────────────────────────────────────
    op.create_table(
        "research_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("research_case_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("historical_case_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("historical_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("investment_source_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("investment_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_name", sa.Text, nullable=False),
        sa.Column("source_url", sa.Text),
        sa.Column("signal_quality", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_research_sources_case_id", "research_sources", ["research_case_id"])
    op.create_index("idx_research_sources_historical_case_id", "research_sources", ["historical_case_id"])
    op.create_index("idx_research_sources_investment_source_id", "research_sources", ["investment_source_id"])
    op.create_index("idx_research_sources_signal_quality", "research_sources", ["signal_quality"])

    # ── source_intelligence_suggestions ──────────────────────────────────────
    op.create_table(
        "source_intelligence_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("research_case_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("historical_case_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("historical_cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("existing_source_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("investment_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("proposed_name", sa.Text),
        sa.Column("proposed_url", sa.Text),
        sa.Column("proposed_source_type", sa.String(50)),
        sa.Column("proposed_priority", sa.Integer),
        sa.Column("rationale", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="proposed"),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_si_suggestions_status", "source_intelligence_suggestions", ["status"])
    op.create_index("idx_si_suggestions_research_case_id", "source_intelligence_suggestions", ["research_case_id"])
    op.create_index("idx_si_suggestions_historical_case_id", "source_intelligence_suggestions", ["historical_case_id"])

    # ── public_article_drafts ─────────────────────────────────────────────────
    op.create_table(
        "public_article_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("research_case_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("research_cases.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("title", sa.Text),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("readiness_label", sa.String(50), nullable=False),
        sa.Column("disclaimer", sa.Text, nullable=False,
                  server_default="Este análisis es educativo. No es asesoramiento financiero."),
        sa.Column("disclaimer_present", sa.Boolean, nullable=False),
        sa.Column("buy_sell_language_check", sa.Boolean, nullable=False),
        sa.Column("tags", postgresql.JSONB),
        sa.Column("run_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_public_article_drafts_case_id", "public_article_drafts", ["research_case_id"])
    op.create_index("idx_public_article_drafts_status", "public_article_drafts", ["status"])
    op.create_index("idx_public_article_drafts_readiness_label", "public_article_drafts", ["readiness_label"])


def downgrade() -> None:
    op.drop_index("idx_public_article_drafts_readiness_label", "public_article_drafts")
    op.drop_index("idx_public_article_drafts_status", "public_article_drafts")
    op.drop_index("idx_public_article_drafts_case_id", "public_article_drafts")
    op.drop_table("public_article_drafts")

    op.drop_index("idx_si_suggestions_historical_case_id", "source_intelligence_suggestions")
    op.drop_index("idx_si_suggestions_research_case_id", "source_intelligence_suggestions")
    op.drop_index("idx_si_suggestions_status", "source_intelligence_suggestions")
    op.drop_table("source_intelligence_suggestions")

    op.drop_index("idx_research_sources_signal_quality", "research_sources")
    op.drop_index("idx_research_sources_investment_source_id", "research_sources")
    op.drop_index("idx_research_sources_historical_case_id", "research_sources")
    op.drop_index("idx_research_sources_case_id", "research_sources")
    op.drop_table("research_sources")

    op.drop_index("idx_research_documents_doc_type", "research_documents")
    op.drop_index("idx_research_documents_case_id", "research_documents")
    op.drop_table("research_documents")

    op.drop_index("idx_historical_cases_linked_situation_id", "historical_cases")
    op.drop_index("idx_historical_cases_situation_type", "historical_cases")
    op.drop_index("idx_historical_cases_status", "historical_cases")
    op.drop_table("historical_cases")

    op.drop_index("idx_research_tasks_status", "research_tasks")
    op.drop_index("idx_research_tasks_case_id", "research_tasks")
    op.drop_table("research_tasks")

    op.drop_index("idx_research_cases_investment_readiness", "research_cases")
    op.drop_index("idx_research_cases_status", "research_cases")
    op.drop_index("idx_research_cases_situation_id", "research_cases")
    op.drop_table("research_cases")
