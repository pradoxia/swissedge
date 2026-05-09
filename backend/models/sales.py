import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Text, Integer, Boolean, Numeric, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.database import Base


def _now():
    return datetime.now(timezone.utc)


class SalesItemStatus:
    NEEDS_INFO = "needs_info"
    DRAFT_READY = "draft_ready"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHED = "published"
    SOLD = "sold"
    ARCHIVED = "archived"


class PlatformListingStatus:
    NOT_LISTED = "not_listed"
    DRAFT = "draft"
    PUBLISHED = "published"
    SOLD = "sold"
    ARCHIVED = "archived"


class Platform:
    RICARDO = "ricardo"
    TUTTI = "tutti"
    ANIBIS = "anibis"
    FACEBOOK_MARKETPLACE_CH = "facebook_marketplace_ch"


class PhotoType:
    ORIGINAL = "original"
    AI_GENERATED = "ai_generated"
    EDITED = "edited"


class SalesItem(Base):
    __tablename__ = "sales_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str | None] = mapped_column(String(200))
    brand_model: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(100))
    condition: Mapped[str | None] = mapped_column(String(40))
    description: Mapped[str | None] = mapped_column(Text)
    internal_notes: Mapped[str | None] = mapped_column(Text)
    target_price_chf: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    pickup_location: Mapped[str | None] = mapped_column(String(200))
    shipping_policy: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), nullable=False, default=SalesItemStatus.NEEDS_INFO)
    needs_action_reason: Mapped[str | None] = mapped_column(Text)
    created_from: Mapped[str | None] = mapped_column(String(40))
    telegram_chat_id: Mapped[str | None] = mapped_column(String(60))
    telegram_message_id: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    photos: Mapped[list["SalesItemPhoto"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
    platform_listings: Mapped[list["SalesPlatformListing"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_sales_items_status", "status"),
        Index("ix_sales_items_created_at", "created_at"),
    )


class SalesItemPhoto(Base):
    __tablename__ = "sales_item_photos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales_items.id", ondelete="CASCADE"), nullable=False
    )
    photo_type: Mapped[str] = mapped_column(String(40), nullable=False, default=PhotoType.ORIGINAL)
    telegram_file_id: Mapped[str | None] = mapped_column(String(200))
    local_path: Mapped[str | None] = mapped_column(String(500))
    storage_url: Mapped[str | None] = mapped_column(Text)
    caption: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)

    item: Mapped["SalesItem"] = relationship(back_populates="photos")

    __table_args__ = (
        Index("ix_sales_item_photos_item_id", "item_id"),
    )


class SalesPlatformListing(Base):
    __tablename__ = "sales_platform_listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales_items.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default=PlatformListingStatus.NOT_LISTED)
    title: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    category_suggestion: Mapped[str | None] = mapped_column(String(200))
    price_chf: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    publish_url: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    item: Mapped["SalesItem"] = relationship(back_populates="platform_listings")

    __table_args__ = (
        UniqueConstraint("item_id", "platform", name="uq_sales_platform_listings_item_platform"),
        Index("ix_sales_platform_listings_item_id", "item_id"),
        Index("ix_sales_platform_listings_platform", "platform"),
    )
