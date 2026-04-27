import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Numeric, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.database import Base


def _now():
    return datetime.now(timezone.utc)


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description_de: Mapped[str | None] = mapped_column(Text)
    photos: Mapped[dict | None] = mapped_column(JSONB)
    category: Mapped[str | None] = mapped_column(String(100))
    condition: Mapped[str | None] = mapped_column(String(50))
    price_asked: Mapped[float | None] = mapped_column(Numeric(10, 2))
    price_market_avg: Mapped[float | None] = mapped_column(Numeric(10, 2))
    price_market_range: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    marketplace: Mapped[str | None] = mapped_column(String(100))
    listing_url: Mapped[str | None] = mapped_column(Text)
    trust_score: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
