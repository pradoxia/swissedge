import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Text, Integer, Boolean, DateTime, Date, ForeignKey
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


class InvestorContact(Base):
    __tablename__ = "investor_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str | None] = mapped_column(Text)
    platform: Mapped[str | None] = mapped_column(String(100))
    url: Mapped[str | None] = mapped_column(Text)
    discovered_via: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
