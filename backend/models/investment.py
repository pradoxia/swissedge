import uuid
from decimal import Decimal
from datetime import datetime, date, timezone
from sqlalchemy import String, Text, Integer, Boolean, DateTime, Date, ForeignKey, Float, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.database import Base


def _now():
    return datetime.now(timezone.utc)


class SpecialSituation(Base):
    __tablename__ = "special_situations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    situation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(20))
    filing_type: Mapped[str | None] = mapped_column(String(50))
    filing_url: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    status: Mapped[str] = mapped_column(String(50), default="detected")
    evaluation: Mapped[dict | None] = mapped_column(JSONB)
    strengths: Mapped[dict | None] = mapped_column(JSONB)
    weaknesses: Mapped[dict | None] = mapped_column(JSONB)
    risks: Mapped[dict | None] = mapped_column(JSONB)
    course_chapter: Mapped[int | None] = mapped_column(Integer)
    course_timestamp: Mapped[str | None] = mapped_column(String(20))
    source_urls: Mapped[dict | None] = mapped_column(JSONB)
    notes: Mapped[str | None] = mapped_column(Text)
    follow_up_date: Mapped[date | None] = mapped_column(Date)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    history: Mapped[list["SituationHistory"]] = relationship(back_populates="situation", cascade="all, delete-orphan")


class SituationHistory(Base):
    __tablename__ = "situation_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    situation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("special_situations.id"))
    status_from: Mapped[str | None] = mapped_column(String(50))
    status_to: Mapped[str | None] = mapped_column(String(50))
    reason: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    situation: Mapped["SpecialSituation"] = relationship(back_populates="history")


class InvestmentSource(Base):
    __tablename__ = "investment_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(50))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    check_frequency_hours: Mapped[int] = mapped_column(Integer, default=6)
    notes: Mapped[str | None] = mapped_column(Text)
    # Extended fields for observability and source management
    description: Mapped[str | None] = mapped_column(Text)
    market: Mapped[str | None] = mapped_column(String(100))
    jurisdiction: Mapped[str | None] = mapped_column(String(100))
    priority: Mapped[int] = mapped_column(Integer, default=5)
    requires_api_key: Mapped[bool] = mapped_column(Boolean, default=False)
    access_method: Mapped[str | None] = mapped_column(String(50))
    query_template: Mapped[str | None] = mapped_column(Text)
    last_success: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)


class DetectionRun(Base):
    __tablename__ = "detection_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="sec_edgar")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hours_back: Mapped[int | None] = mapped_column(Integer)
    raw_hits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    parsed_filings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    classified_filings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unclassified_filings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicates_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    special_situations_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    runtime_seconds: Mapped[float | None] = mapped_column(Float)
    forms_checked_json: Mapped[dict | None] = mapped_column(JSONB)
    per_form_summary_json: Mapped[dict | None] = mapped_column(JSONB)
    summary_json: Mapped[dict | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class DocumentationExtractionField(Base):
    __tablename__ = "documentation_extraction_fields"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    situation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("special_situations.id", ondelete="CASCADE"), nullable=False)
    candidate_source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    document_key: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_title: Mapped[str | None] = mapped_column(Text)
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    field_label: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_value: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    source_snippet: Mapped[str | None] = mapped_column(Text)
    section_reference: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    reviewed_by: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    situation: Mapped["SpecialSituation"] = relationship()


class InvestorContact(Base):
    __tablename__ = "investor_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str | None] = mapped_column(Text)
    platform: Mapped[str | None] = mapped_column(String(100))
    url: Mapped[str | None] = mapped_column(Text)
    discovered_via: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    latest_close_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    close_date: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str | None] = mapped_column(String(10))
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(24, 2))
    average_daily_volume: Mapped[Decimal | None] = mapped_column(Numeric(24, 2))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    safe_metadata: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (
        Index("idx_price_snapshots_ticker", "ticker"),
        Index("idx_price_snapshots_provider", "provider"),
        Index("idx_price_snapshots_close_date", "close_date"),
    )


class CasePriceContext(Base):
    __tablename__ = "case_price_contexts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    special_situation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("special_situations.id", ondelete="CASCADE"), nullable=True
    )
    research_case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_cases.id", ondelete="CASCADE"), nullable=True
    )
    ticker: Mapped[str | None] = mapped_column(String(20))
    offer_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    offer_price_source: Mapped[str | None] = mapped_column(Text)
    price_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("price_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    latest_close_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    latest_close_date: Mapped[date | None] = mapped_column(Date)
    estimated_spread_pct: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    spread_status: Mapped[str] = mapped_column(String(40), nullable=False)
    status_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    __table_args__ = (
        Index("idx_case_price_contexts_special_situation_id", "special_situation_id"),
        Index("idx_case_price_contexts_research_case_id", "research_case_id"),
        Index("idx_case_price_contexts_ticker", "ticker"),
        Index("idx_case_price_contexts_spread_status", "spread_status"),
    )
