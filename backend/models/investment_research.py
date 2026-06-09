import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.database import Base


def _now():
    return datetime.now(timezone.utc)


class ResearchCase(Base):
    __tablename__ = "research_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    situation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("special_situations.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="detected")
    brief: Mapped[dict | None] = mapped_column(JSONB)
    brief_version: Mapped[str | None] = mapped_column(String(20))
    playbook_version: Mapped[str | None] = mapped_column(String(100))
    model_used: Mapped[str | None] = mapped_column(String(100))
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text)
    disclaimer: Mapped[str] = mapped_column(
        Text, nullable=False,
        default="Este análisis es educativo. No es asesoramiento financiero."
    )
    investment_readiness: Mapped[str | None] = mapped_column(String(50))
    source_origin_name: Mapped[str | None] = mapped_column(Text)
    investment_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investment_sources.id", ondelete="SET NULL"), nullable=True
    )
    intake_method: Mapped[str | None] = mapped_column(String(50))
    connector_key: Mapped[str | None] = mapped_column(String(100))
    intake_event_id: Mapped[str | None] = mapped_column(String(100))
    evidence_level: Mapped[str | None] = mapped_column(String(50))
    official_source_status: Mapped[str | None] = mapped_column(String(50))
    methodology_status: Mapped[str | None] = mapped_column(String(50))
    playbook_used: Mapped[str | None] = mapped_column(String(100))
    checklist_used: Mapped[str | None] = mapped_column(String(100))
    course_reference: Mapped[str | None] = mapped_column(Text)
    duplicate_status: Mapped[str | None] = mapped_column(String(50))
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    discarded_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    tasks: Mapped[list["ResearchTask"]] = relationship(back_populates="research_case", cascade="all, delete-orphan")
    documents: Mapped[list["ResearchDocument"]] = relationship(back_populates="research_case", cascade="all, delete-orphan")
    sources: Mapped[list["ResearchSource"]] = relationship(back_populates="research_case")

    __table_args__ = (
        Index("idx_research_cases_situation_id", "situation_id"),
        Index("idx_research_cases_status", "status"),
        Index("idx_research_cases_investment_readiness", "investment_readiness"),
        Index("idx_research_cases_investment_source_id", "investment_source_id"),
        Index("idx_research_cases_intake_method", "intake_method"),
        Index("idx_research_cases_evidence_level", "evidence_level"),
        Index("idx_research_cases_official_source_status", "official_source_status"),
        Index("idx_research_cases_methodology_status", "methodology_status"),
        Index("idx_research_cases_duplicate_status", "duplicate_status"),
        Index("idx_research_cases_next_follow_up_at", "next_follow_up_at"),
    )


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_cases.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    source: Mapped[str | None] = mapped_column(String(20))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    research_case: Mapped["ResearchCase"] = relationship(back_populates="tasks")

    __table_args__ = (
        Index("idx_research_tasks_case_id", "research_case_id"),
        Index("idx_research_tasks_status", "status"),
    )


class ResearchDocument(Base):
    __tablename__ = "research_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_cases.id", ondelete="CASCADE"), nullable=True
    )
    historical_case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("historical_cases.id", ondelete="CASCADE"), nullable=True
    )
    doc_type: Mapped[str | None] = mapped_column(String(50))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[str | None] = mapped_column(Text)
    added_by: Mapped[str | None] = mapped_column(String(50))
    body_text: Mapped[str | None] = mapped_column(Text)
    body_text_excerpt: Mapped[str | None] = mapped_column(Text)
    body_text_sha256: Mapped[str | None] = mapped_column(String(64))
    body_text_acquired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    body_text_status: Mapped[str | None] = mapped_column(String(40))
    body_text_error: Mapped[str | None] = mapped_column(Text)
    body_text_size_bytes: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    research_case: Mapped["ResearchCase | None"] = relationship(back_populates="documents")
    historical_case: Mapped["HistoricalCase | None"] = relationship(back_populates="documents")

    __table_args__ = (
        Index("idx_research_documents_case_id", "research_case_id"),
        Index("idx_research_documents_doc_type", "doc_type"),
    )


class ResearchSource(Base):
    __tablename__ = "research_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_cases.id", ondelete="SET NULL"), nullable=True
    )
    historical_case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("historical_cases.id", ondelete="SET NULL"), nullable=True
    )
    investment_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investment_sources.id", ondelete="SET NULL"), nullable=True
    )
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    signal_quality: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    research_case: Mapped["ResearchCase | None"] = relationship(back_populates="sources")
    historical_case: Mapped["HistoricalCase | None"] = relationship(back_populates="sources")

    __table_args__ = (
        Index("idx_research_sources_case_id", "research_case_id"),
        Index("idx_research_sources_historical_case_id", "historical_case_id"),
        Index("idx_research_sources_investment_source_id", "investment_source_id"),
        Index("idx_research_sources_signal_quality", "signal_quality"),
    )


class HistoricalCase(Base):
    __tablename__ = "historical_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    situation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_date_approx: Mapped[str | None] = mapped_column(String(20))
    seed_notes: Mapped[str | None] = mapped_column(Text)
    course_chapter_ref: Mapped[int | None] = mapped_column(Integer)
    reconstruction: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="seed")
    linked_situation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("special_situations.id", ondelete="SET NULL"), nullable=True
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True
    )
    disclaimer: Mapped[str] = mapped_column(
        Text, nullable=False,
        default="Este análisis es educativo. No es asesoramiento financiero."
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    documents: Mapped[list["ResearchDocument"]] = relationship(back_populates="historical_case", cascade="all, delete-orphan")
    sources: Mapped[list["ResearchSource"]] = relationship(back_populates="historical_case")

    __table_args__ = (
        Index("idx_historical_cases_status", "status"),
        Index("idx_historical_cases_situation_type", "situation_type"),
        Index("idx_historical_cases_linked_situation_id", "linked_situation_id"),
    )
