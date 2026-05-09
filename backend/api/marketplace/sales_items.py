import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.sales import (
    SalesItem,
    SalesItemPhoto,
    SalesPlatformListing,
    SalesItemStatus,
    PlatformListingStatus,
    Platform,
    PhotoType,
)
from backend.services.marketplace.listing_gen import generate_listing

router = APIRouter()

_REQUIRED_FOR_DRAFT = {"title", "condition", "target_price_chf", "pickup_location"}
_ALL_PLATFORMS = [
    Platform.RICARDO,
    Platform.TUTTI,
    Platform.ANIBIS,
    Platform.FACEBOOK_MARKETPLACE_CH,
]


# ── Schemas ────────────────────────────────────────────────────────────────────

class SalesItemCreate(BaseModel):
    title: Optional[str] = None
    brand_model: Optional[str] = None
    category: Optional[str] = None
    condition: Optional[str] = None
    description: Optional[str] = None
    internal_notes: Optional[str] = None
    target_price_chf: Optional[Decimal] = None
    pickup_location: Optional[str] = None
    shipping_policy: Optional[str] = None
    needs_action_reason: Optional[str] = None
    created_from: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_message_id: Optional[str] = None


class SalesItemPatch(BaseModel):
    title: Optional[str] = None
    brand_model: Optional[str] = None
    category: Optional[str] = None
    condition: Optional[str] = None
    description: Optional[str] = None
    internal_notes: Optional[str] = None
    target_price_chf: Optional[Decimal] = None
    pickup_location: Optional[str] = None
    shipping_policy: Optional[str] = None
    status: Optional[str] = None
    needs_action_reason: Optional[str] = None


class SalesItemPhotoResponse(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    photo_type: str
    telegram_file_id: Optional[str]
    local_path: Optional[str]
    storage_url: Optional[str]
    caption: Optional[str]
    is_primary: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SalesPlatformListingResponse(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    platform: str
    status: str
    title: Optional[str]
    description: Optional[str]
    category_suggestion: Optional[str]
    price_chf: Optional[Decimal]
    publish_url: Optional[str]
    published_at: Optional[datetime]
    sold_at: Optional[datetime]
    archived_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SalesItemResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    brand_model: Optional[str]
    category: Optional[str]
    condition: Optional[str]
    description: Optional[str]
    internal_notes: Optional[str]
    target_price_chf: Optional[Decimal]
    pickup_location: Optional[str]
    shipping_policy: Optional[str]
    status: str
    needs_action_reason: Optional[str]
    created_from: Optional[str]
    telegram_chat_id: Optional[str]
    telegram_message_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    photos: list[SalesItemPhotoResponse]
    platform_listings: list[SalesPlatformListingResponse]

    model_config = {"from_attributes": True}


# ── Helpers ────────────────────────────────────────────────────────────────────

_VALID_TRANSITIONS = {
    SalesItemStatus.NEEDS_INFO: {SalesItemStatus.DRAFT_READY, SalesItemStatus.ARCHIVED},
    SalesItemStatus.DRAFT_READY: {SalesItemStatus.NEEDS_INFO, SalesItemStatus.READY_TO_PUBLISH, SalesItemStatus.ARCHIVED},
    SalesItemStatus.READY_TO_PUBLISH: {SalesItemStatus.PUBLISHED, SalesItemStatus.DRAFT_READY, SalesItemStatus.ARCHIVED},
    SalesItemStatus.PUBLISHED: {SalesItemStatus.SOLD, SalesItemStatus.ARCHIVED},
    SalesItemStatus.SOLD: set(),
    SalesItemStatus.ARCHIVED: set(),
}


def _derive_status(data: dict) -> str:
    if all(data.get(f) is not None for f in _REQUIRED_FOR_DRAFT):
        return SalesItemStatus.DRAFT_READY
    return SalesItemStatus.NEEDS_INFO


async def _load_item(db: AsyncSession, item_id: uuid.UUID) -> SalesItem:
    result = await db.execute(
        select(SalesItem)
        .options(
            selectinload(SalesItem.photos),
            selectinload(SalesItem.platform_listings),
        )
        .where(SalesItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Sales item not found")
    return item


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/items", response_model=SalesItemResponse, status_code=201)
async def create_sales_item(payload: SalesItemCreate, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump(exclude_none=False)
    status = _derive_status(data)

    item = SalesItem(
        title=payload.title,
        brand_model=payload.brand_model,
        category=payload.category,
        condition=payload.condition,
        description=payload.description,
        internal_notes=payload.internal_notes,
        target_price_chf=payload.target_price_chf,
        pickup_location=payload.pickup_location,
        shipping_policy=payload.shipping_policy,
        status=status,
        needs_action_reason=payload.needs_action_reason,
        created_from=payload.created_from,
        telegram_chat_id=payload.telegram_chat_id,
        telegram_message_id=payload.telegram_message_id,
    )
    db.add(item)
    await db.flush()

    for platform in _ALL_PLATFORMS:
        db.add(SalesPlatformListing(item_id=item.id, platform=platform))

    await db.commit()
    return await _load_item(db, item.id)


@router.get("/items", response_model=list[SalesItemResponse])
async def list_sales_items(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(SalesItem)
        .options(
            selectinload(SalesItem.photos),
            selectinload(SalesItem.platform_listings),
        )
        .order_by(SalesItem.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status:
        q = q.where(SalesItem.status == status)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/items/{item_id}", response_model=SalesItemResponse)
async def get_sales_item(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await _load_item(db, item_id)


@router.patch("/items/{item_id}", response_model=SalesItemResponse)
async def patch_sales_item(
    item_id: uuid.UUID,
    payload: SalesItemPatch,
    db: AsyncSession = Depends(get_db),
):
    item = await _load_item(db, item_id)

    updates = payload.model_dump(exclude_unset=True)

    if "status" in updates:
        new_status = updates.pop("status")
        allowed = _VALID_TRANSITIONS.get(item.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status transition: {item.status!r} → {new_status!r}",
            )
        item.status = new_status

    for field, value in updates.items():
        setattr(item, field, value)

    item_data = {
        "title": item.title,
        "condition": item.condition,
        "target_price_chf": item.target_price_chf,
        "pickup_location": item.pickup_location,
    }
    if item.status == SalesItemStatus.NEEDS_INFO:
        derived = _derive_status(item_data)
        if derived == SalesItemStatus.DRAFT_READY:
            item.status = SalesItemStatus.DRAFT_READY

    await db.commit()
    return await _load_item(db, item_id)


# ── Telegram intake endpoint ───────────────────────────────────────────────────

_FRONTEND_BASE_URL = "http://100.73.109.52:3001"

class TelegramIntakeRequest(BaseModel):
    telegram_chat_id: str
    telegram_message_id: Optional[str] = None
    item_hint: Optional[str] = None


class TelegramIntakeResponse(BaseModel):
    item_id: str
    item_url: str
    reply_es: str


@router.post("/telegram-intake", response_model=TelegramIntakeResponse)
async def telegram_intake(payload: TelegramIntakeRequest, db: AsyncSession = Depends(get_db)):
    """
    Single-call endpoint for OpenClaw/Telegram sales trigger.
    Creates a SalesItem and returns the Spanish reply text + item URL ready to send.
    """
    item = SalesItem(
        brand_model=payload.item_hint[:200] if payload.item_hint else None,
        status=SalesItemStatus.NEEDS_INFO,
        created_from="telegram",
        telegram_chat_id=payload.telegram_chat_id,
        telegram_message_id=payload.telegram_message_id,
    )
    db.add(item)
    await db.flush()

    for platform in _ALL_PLATFORMS:
        db.add(SalesPlatformListing(item_id=item.id, platform=platform))

    await db.commit()

    item_id = str(item.id)
    item_url = f"{_FRONTEND_BASE_URL}/marketplace/sales/items/{item_id}"

    reply = (
        "Perfecto, preparo una venta asistida. 🇨🇭\n\n"
        "No publicaré nada sin tu confirmación.\n\n"
        "Para hacer un buen anuncio en Ricardo / Tutti / Anibis necesito:\n"
        "1. ¿Qué es exactamente el artículo?\n"
        "2. Estado: nuevo / como nuevo / muy bueno / bueno / con defectos\n"
        "3. Precio deseado en CHF\n"
        "4. Recogida o envío (y desde dónde)\n"
        "5. Defectos, accesorios o detalles importantes\n\n"
        f"🔗 Ver y editar: {item_url}\n\n"
        "Sin confirmación tuya no publico nada."
    )

    return TelegramIntakeResponse(item_id=item_id, item_url=item_url, reply_es=reply)


_DRAFT_REQUIRED = {"brand_model_or_title", "condition"}


@router.post("/items/{item_id}/generate-platform-drafts", response_model=SalesItemResponse)
async def generate_platform_drafts(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    item = await _load_item(db, item_id)

    missing: list[str] = []
    if not (item.title or item.brand_model):
        missing.append("title or brand_model")
    if not item.condition:
        missing.append("condition")
    has_context = any([item.description, item.internal_notes, item.category, item.target_price_chf])
    if not has_context:
        missing.append("at least one of: description, internal_notes, category, target_price_chf")
    if missing:
        raise HTTPException(status_code=400, detail={"missing_fields": missing})

    item_description = " ".join(filter(None, [item.title, item.brand_model]))
    draft, _usage = await generate_listing(
        item_description=item_description,
        brand=item.brand_model or "",
        condition=item.condition or "Gut",
        category=item.category or "",
        price=float(item.target_price_chf) if item.target_price_chf else 0,
    )

    for listing in item.platform_listings:
        listing.title = draft.get("title")
        listing.description = draft.get("description")
        listing.category_suggestion = draft.get("category_suggestion")
        if item.target_price_chf is not None:
            listing.price_chf = item.target_price_chf
        listing.status = PlatformListingStatus.DRAFT

    await db.commit()
    return await _load_item(db, item_id)
