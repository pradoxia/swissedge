"""Add Agent Ops foundation tables.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_rooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(50), nullable=False, server_default="planned"),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_agent_rooms_status", "agent_rooms", ["status"])
    op.create_index("idx_agent_rooms_display_order", "agent_rooms", ["display_order"])

    op.create_table(
        "agent_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "room_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_rooms.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("role", sa.Text),
        sa.Column("status", sa.String(50), nullable=False, server_default="planned"),
        sa.Column("implementation_status", sa.String(50), nullable=False, server_default="documented"),
        sa.Column("autonomy_level", sa.String(50), nullable=False, server_default="observer"),
        sa.Column("guardrails", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_agent_profiles_room_id", "agent_profiles", ["room_id"])
    op.create_index("idx_agent_profiles_status", "agent_profiles", ["status"])
    op.create_index("idx_agent_profiles_implementation_status", "agent_profiles", ["implementation_status"])

    op.create_table(
        "agent_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_profiles.id", ondelete="SET NULL")),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_rooms.id", ondelete="SET NULL")),
        sa.Column("activity_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("summary", sa.Text),
        sa.Column("severity", sa.String(50), nullable=False, server_default="info"),
        sa.Column("status", sa.String(50), nullable=False, server_default="completed"),
        sa.Column("related_entity_type", sa.String(100)),
        sa.Column("related_entity_id", sa.String(100)),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_agent_activities_created_at", "agent_activities", ["created_at"])
    op.create_index("idx_agent_activities_agent_id", "agent_activities", ["agent_id"])
    op.create_index("idx_agent_activities_room_id", "agent_activities", ["room_id"])
    op.create_index("idx_agent_activities_severity", "agent_activities", ["severity"])
    op.create_index("idx_agent_activities_status", "agent_activities", ["status"])
    op.create_index(
        "idx_agent_activities_related_entity",
        "agent_activities",
        ["related_entity_type", "related_entity_id"],
    )

    op.create_table(
        "agent_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "activity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_activities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("result_type", sa.String(100), nullable=False),
        sa.Column("summary", sa.Text),
        sa.Column("status", sa.String(50), nullable=False, server_default="success"),
        sa.Column("metrics", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_agent_results_activity_id", "agent_results", ["activity_id"])
    op.create_index("idx_agent_results_status", "agent_results", ["status"])
    op.create_index("idx_agent_results_created_at", "agent_results", ["created_at"])

    op.create_table(
        "agent_diagnostic_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_profiles.id", ondelete="SET NULL")),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_rooms.id", ondelete="SET NULL")),
        sa.Column("severity", sa.String(50), nullable=False, server_default="info"),
        sa.Column("diagnostic_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("evidence", postgresql.JSONB),
        sa.Column("related_entity_type", sa.String(100)),
        sa.Column("related_entity_id", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_agent_diagnostic_events_created_at", "agent_diagnostic_events", ["created_at"])
    op.create_index("idx_agent_diagnostic_events_type", "agent_diagnostic_events", ["diagnostic_type"])
    op.create_index("idx_agent_diagnostic_events_severity", "agent_diagnostic_events", ["severity"])
    op.create_index(
        "idx_agent_diagnostic_events_related_entity",
        "agent_diagnostic_events",
        ["related_entity_type", "related_entity_id"],
    )

    op.create_table(
        "agent_learning_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_diagnostic_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_diagnostic_events.id", ondelete="SET NULL"),
        ),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_profiles.id", ondelete="SET NULL")),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_rooms.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("problem_statement", sa.Text, nullable=False),
        sa.Column("proposed_change", sa.Text, nullable=False),
        sa.Column("expected_benefit", sa.Text),
        sa.Column("risk_level", sa.String(50), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(50), nullable=False, server_default="proposed"),
        sa.Column("reviewer_note", sa.Text),
        sa.Column("reviewed_by", sa.String(100)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_agent_learning_proposals_status", "agent_learning_proposals", ["status"])
    op.create_index("idx_agent_learning_proposals_risk_level", "agent_learning_proposals", ["risk_level"])
    op.create_index("idx_agent_learning_proposals_created_at", "agent_learning_proposals", ["created_at"])
    op.create_index("idx_agent_learning_proposals_room_id", "agent_learning_proposals", ["room_id"])
    op.create_index("idx_agent_learning_proposals_agent_id", "agent_learning_proposals", ["agent_id"])


def downgrade() -> None:
    op.drop_index("idx_agent_learning_proposals_agent_id", table_name="agent_learning_proposals")
    op.drop_index("idx_agent_learning_proposals_room_id", table_name="agent_learning_proposals")
    op.drop_index("idx_agent_learning_proposals_created_at", table_name="agent_learning_proposals")
    op.drop_index("idx_agent_learning_proposals_risk_level", table_name="agent_learning_proposals")
    op.drop_index("idx_agent_learning_proposals_status", table_name="agent_learning_proposals")
    op.drop_table("agent_learning_proposals")

    op.drop_index("idx_agent_diagnostic_events_related_entity", table_name="agent_diagnostic_events")
    op.drop_index("idx_agent_diagnostic_events_severity", table_name="agent_diagnostic_events")
    op.drop_index("idx_agent_diagnostic_events_type", table_name="agent_diagnostic_events")
    op.drop_index("idx_agent_diagnostic_events_created_at", table_name="agent_diagnostic_events")
    op.drop_table("agent_diagnostic_events")

    op.drop_index("idx_agent_results_created_at", table_name="agent_results")
    op.drop_index("idx_agent_results_status", table_name="agent_results")
    op.drop_index("idx_agent_results_activity_id", table_name="agent_results")
    op.drop_table("agent_results")

    op.drop_index("idx_agent_activities_related_entity", table_name="agent_activities")
    op.drop_index("idx_agent_activities_status", table_name="agent_activities")
    op.drop_index("idx_agent_activities_severity", table_name="agent_activities")
    op.drop_index("idx_agent_activities_room_id", table_name="agent_activities")
    op.drop_index("idx_agent_activities_agent_id", table_name="agent_activities")
    op.drop_index("idx_agent_activities_created_at", table_name="agent_activities")
    op.drop_table("agent_activities")

    op.drop_index("idx_agent_profiles_implementation_status", table_name="agent_profiles")
    op.drop_index("idx_agent_profiles_status", table_name="agent_profiles")
    op.drop_index("idx_agent_profiles_room_id", table_name="agent_profiles")
    op.drop_table("agent_profiles")

    op.drop_index("idx_agent_rooms_display_order", table_name="agent_rooms")
    op.drop_index("idx_agent_rooms_status", table_name="agent_rooms")
    op.drop_table("agent_rooms")
