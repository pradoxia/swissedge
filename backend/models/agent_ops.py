import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.database import Base


def _now():
    return datetime.now(timezone.utc)


class AgentRoom(Base):
    __tablename__ = "agent_rooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="planned")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    agents: Mapped[list["AgentProfile"]] = relationship(back_populates="room")

    __table_args__ = (
        Index("idx_agent_rooms_status", "status"),
        Index("idx_agent_rooms_display_order", "display_order"),
    )


class AgentProfile(Base):
    __tablename__ = "agent_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_rooms.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="planned")
    implementation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="documented")
    autonomy_level: Mapped[str] = mapped_column(String(50), nullable=False, default="observer")
    guardrails: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    room: Mapped["AgentRoom"] = relationship(back_populates="agents")

    __table_args__ = (
        Index("idx_agent_profiles_room_id", "room_id"),
        Index("idx_agent_profiles_status", "status"),
        Index("idx_agent_profiles_implementation_status", "implementation_status"),
    )


class AgentActivity(Base):
    __tablename__ = "agent_activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id", ondelete="SET NULL"), nullable=True
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_rooms.id", ondelete="SET NULL"), nullable=True
    )
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="info")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    related_entity_type: Mapped[str | None] = mapped_column(String(100))
    related_entity_id: Mapped[str | None] = mapped_column(String(100))
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    agent: Mapped["AgentProfile | None"] = relationship()
    room: Mapped["AgentRoom | None"] = relationship()
    results: Mapped[list["AgentResult"]] = relationship(back_populates="activity", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_agent_activities_created_at", "created_at"),
        Index("idx_agent_activities_agent_id", "agent_id"),
        Index("idx_agent_activities_room_id", "room_id"),
        Index("idx_agent_activities_severity", "severity"),
        Index("idx_agent_activities_status", "status"),
        Index("idx_agent_activities_related_entity", "related_entity_type", "related_entity_id"),
    )


class AgentResult(Base):
    __tablename__ = "agent_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_activities.id", ondelete="CASCADE"), nullable=False
    )
    result_type: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="success")
    metrics: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    activity: Mapped["AgentActivity"] = relationship(back_populates="results")

    __table_args__ = (
        Index("idx_agent_results_activity_id", "activity_id"),
        Index("idx_agent_results_status", "status"),
        Index("idx_agent_results_created_at", "created_at"),
    )


class AgentDiagnosticEvent(Base):
    __tablename__ = "agent_diagnostic_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id", ondelete="SET NULL"), nullable=True
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_rooms.id", ondelete="SET NULL"), nullable=True
    )
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default="info")
    diagnostic_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[dict | None] = mapped_column(JSONB)
    related_entity_type: Mapped[str | None] = mapped_column(String(100))
    related_entity_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    agent: Mapped["AgentProfile | None"] = relationship()
    room: Mapped["AgentRoom | None"] = relationship()

    __table_args__ = (
        Index("idx_agent_diagnostic_events_created_at", "created_at"),
        Index("idx_agent_diagnostic_events_type", "diagnostic_type"),
        Index("idx_agent_diagnostic_events_severity", "severity"),
        Index("idx_agent_diagnostic_events_related_entity", "related_entity_type", "related_entity_id"),
    )


class AgentLearningProposal(Base):
    __tablename__ = "agent_learning_proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_diagnostic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_diagnostic_events.id", ondelete="SET NULL"), nullable=True
    )
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_profiles.id", ondelete="SET NULL"), nullable=True
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_rooms.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_change: Mapped[str] = mapped_column(Text, nullable=False)
    expected_benefit: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="proposed")
    reviewer_note: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[str | None] = mapped_column(String(100))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    source_diagnostic: Mapped["AgentDiagnosticEvent | None"] = relationship()
    agent: Mapped["AgentProfile | None"] = relationship()
    room: Mapped["AgentRoom | None"] = relationship()

    __table_args__ = (
        Index("idx_agent_learning_proposals_status", "status"),
        Index("idx_agent_learning_proposals_risk_level", "risk_level"),
        Index("idx_agent_learning_proposals_created_at", "created_at"),
        Index("idx_agent_learning_proposals_room_id", "room_id"),
        Index("idx_agent_learning_proposals_agent_id", "agent_id"),
    )
