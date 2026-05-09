import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.database import Base


def _now():
    return datetime.now(timezone.utc)


class SourceIntelligenceSuggestion(Base):
    __tablename__ = "source_intelligence_suggestions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_cases.id", ondelete="SET NULL"), nullable=True
    )
    historical_case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("historical_cases.id", ondelete="SET NULL"), nullable=True
    )
    existing_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("investment_sources.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    proposed_name: Mapped[str | None] = mapped_column(Text)
    proposed_url: Mapped[str | None] = mapped_column(Text)
    proposed_source_type: Mapped[str | None] = mapped_column(String(50))
    proposed_priority: Mapped[int | None] = mapped_column(Integer)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="proposed")
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_si_suggestions_status", "status"),
        Index("idx_si_suggestions_research_case_id", "research_case_id"),
        Index("idx_si_suggestions_historical_case_id", "historical_case_id"),
    )
