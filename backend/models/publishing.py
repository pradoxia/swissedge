import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.database import Base


def _now():
    return datetime.now(timezone.utc)


class PublicArticleDraft(Base):
    __tablename__ = "public_article_drafts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_cases.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    title: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    readiness_label: Mapped[str] = mapped_column(String(50), nullable=False)
    disclaimer: Mapped[str] = mapped_column(
        Text, nullable=False,
        default="Este análisis es educativo. No es asesoramiento financiero."
    )
    disclaimer_present: Mapped[bool] = mapped_column(Boolean, nullable=False)
    buy_sell_language_check: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB)
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_public_article_drafts_case_id", "research_case_id"),
        Index("idx_public_article_drafts_status", "status"),
        Index("idx_public_article_drafts_readiness_label", "readiness_label"),
    )
