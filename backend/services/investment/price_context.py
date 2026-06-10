from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Literal, Protocol

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.investment import CasePriceContext, PriceSnapshot, SpecialSituation
from backend.models.investment_research import ResearchCase

SPREAD_STATUS_AVAILABLE = "available"
SPREAD_STATUS_MISSING_OFFER_PRICE = "missing_offer_price"
SPREAD_STATUS_MISSING_MARKET_PRICE = "missing_market_price"
SPREAD_STATUS_STALE_PRICE = "stale_price"
SPREAD_STATUS_NOT_APPLICABLE = "not_applicable"
MANUAL_SPREAD_STATUS_OVERRIDES = {
    SPREAD_STATUS_NOT_APPLICABLE,
    SPREAD_STATUS_MISSING_OFFER_PRICE,
    SPREAD_STATUS_MISSING_MARKET_PRICE,
    SPREAD_STATUS_STALE_PRICE,
}

PRICE_STALENESS_DAYS = 5
SPREAD_APPLICABLE_SITUATION_TYPES = {
    "tender_offer",
    "merger_arbitrage",
    "going_private",
}
_FOUR_DP = Decimal("0.0001")


class PriceProviderUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class PriceQuote:
    ticker: str
    provider: str
    latest_close_price: Decimal
    close_date: date
    currency: str | None = None
    market_cap: Decimal | None = None
    average_daily_volume: Decimal | None = None
    safe_metadata: dict | None = None


class PriceProvider(Protocol):
    async def get_latest_close(self, ticker: str) -> PriceQuote:
        ...


class DisabledPriceProvider:
    async def get_latest_close(self, ticker: str) -> PriceQuote:
        raise PriceProviderUnavailable("Price provider is not configured.")


class PriceContextRead(BaseModel):
    ticker: str | None = None
    offer_price: str | None = None
    offer_price_source: str | None = None
    latest_close_price: str | None = None
    latest_close_date: str | None = None
    estimated_spread_pct: str | None = None
    spread_status: str
    status_reason: str | None = None
    updated_at: str | None = None


PriceContextTargetType = Literal["special_situation", "research_case"]


class ManualPriceContextPayload(BaseModel):
    target_type: PriceContextTargetType
    target_id: str
    ticker: str | None = None
    offer_price: str | None = None
    offer_price_source: str | None = None
    latest_close_price: str | None = None
    latest_close_date: str | None = None
    currency: str | None = None
    spread_status: str | None = None
    status_reason: str | None = None


class PriceContextResponse(BaseModel):
    price_context: PriceContextRead


class PriceContextError(ValueError):
    def __init__(self, message: str, *, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


def normalize_ticker(ticker: str | None) -> str | None:
    if not isinstance(ticker, str):
        return None
    normalized = ticker.strip().upper()
    return normalized or None


def _decimal_or_none(value) -> Decimal | None:
    if value is None:
        return None
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if decimal <= 0:
        return None
    return decimal


def _parse_decimal_field(value, field_name: str) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    decimal = _decimal_or_none(value)
    if decimal is None:
        raise PriceContextError(f"{field_name} must be a positive decimal")
    return decimal


def _parse_date_field(value: str | None, field_name: str) -> date | None:
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    try:
        return date.fromisoformat(trimmed)
    except ValueError:
        raise PriceContextError(f"{field_name} must be an ISO date") from None


def _parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        raise PriceContextError("target_id must be a valid UUID") from None


def _is_stale(close_date: date | None, *, today: date | None = None) -> bool:
    if close_date is None:
        return False
    current = today or datetime.now(timezone.utc).date()
    return (current - close_date).days > PRICE_STALENESS_DAYS


def _situation_type_key(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    return value.strip().lower() or None


def _spread_math_applicable(situation_type: str | None, offer_price: Decimal | None) -> bool:
    if offer_price is not None:
        return True
    return _situation_type_key(situation_type) in SPREAD_APPLICABLE_SITUATION_TYPES


def compute_estimated_spread_pct(offer_price: Decimal, latest_close_price: Decimal) -> Decimal:
    return (((offer_price / latest_close_price) - Decimal("1")) * Decimal("100")).quantize(
        _FOUR_DP,
        rounding=ROUND_HALF_UP,
    )


def classify_price_context(
    *,
    situation_type: str | None,
    offer_price,
    latest_close_price,
    latest_close_date: date | None,
    today: date | None = None,
) -> tuple[str, Decimal | None, str]:
    offer = _decimal_or_none(offer_price)
    close = _decimal_or_none(latest_close_price)

    if not _spread_math_applicable(situation_type, offer):
        return SPREAD_STATUS_NOT_APPLICABLE, None, "Spread math is not applicable to the current context."
    if offer is None:
        return SPREAD_STATUS_MISSING_OFFER_PRICE, None, "Offer price is missing or invalid."
    if close is None:
        return SPREAD_STATUS_MISSING_MARKET_PRICE, None, "Latest close price is missing or invalid."
    if _is_stale(latest_close_date, today=today):
        return SPREAD_STATUS_STALE_PRICE, None, "Latest close price is stale."
    return SPREAD_STATUS_AVAILABLE, compute_estimated_spread_pct(offer, close), "Price context is available."


def serialize_price_context(context: CasePriceContext | None) -> PriceContextRead | None:
    if context is None:
        return None
    return PriceContextRead(
        ticker=context.ticker,
        offer_price=_decimal_to_str(context.offer_price),
        offer_price_source=context.offer_price_source,
        latest_close_price=_decimal_to_str(context.latest_close_price),
        latest_close_date=context.latest_close_date.isoformat() if context.latest_close_date else None,
        estimated_spread_pct=_decimal_to_str(context.estimated_spread_pct),
        spread_status=context.spread_status,
        status_reason=context.status_reason,
        updated_at=context.updated_at.isoformat() if context.updated_at else None,
    )


def _decimal_to_str(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value.normalize(), "f")


def _trim_optional(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


async def fetch_price_quote(provider: PriceProvider, ticker: str) -> PriceQuote | None:
    normalized = normalize_ticker(ticker)
    if normalized is None:
        return None
    try:
        return await provider.get_latest_close(normalized)
    except Exception:
        return None


def build_case_price_context(
    *,
    ticker: str | None,
    situation_type: str | None,
    offer_price=None,
    offer_price_source: str | None = None,
    price_snapshot: PriceSnapshot | None = None,
    special_situation_id: uuid.UUID | None = None,
    research_case_id: uuid.UUID | None = None,
    today: date | None = None,
) -> CasePriceContext:
    if bool(special_situation_id) == bool(research_case_id):
        raise ValueError("Price context must relate to exactly one SpecialSituation or ResearchCase.")

    latest_close_price = price_snapshot.latest_close_price if price_snapshot else None
    latest_close_date = price_snapshot.close_date if price_snapshot else None
    status, spread, reason = classify_price_context(
        situation_type=situation_type,
        offer_price=offer_price,
        latest_close_price=latest_close_price,
        latest_close_date=latest_close_date,
        today=today,
    )
    return CasePriceContext(
        special_situation_id=special_situation_id,
        research_case_id=research_case_id,
        ticker=normalize_ticker(ticker),
        offer_price=_decimal_or_none(offer_price),
        offer_price_source=offer_price_source,
        price_snapshot_id=price_snapshot.id if price_snapshot else None,
        latest_close_price=latest_close_price,
        latest_close_date=latest_close_date,
        estimated_spread_pct=spread,
        spread_status=status,
        status_reason=reason,
    )


async def upsert_case_price_context(
    db: AsyncSession,
    *,
    ticker: str | None,
    situation_type: str | None,
    offer_price=None,
    offer_price_source: str | None = None,
    price_snapshot: PriceSnapshot | None = None,
    special_situation_id: uuid.UUID | None = None,
    research_case_id: uuid.UUID | None = None,
    today: date | None = None,
) -> CasePriceContext:
    replacement = build_case_price_context(
        ticker=ticker,
        situation_type=situation_type,
        offer_price=offer_price,
        offer_price_source=offer_price_source,
        price_snapshot=price_snapshot,
        special_situation_id=special_situation_id,
        research_case_id=research_case_id,
        today=today,
    )
    query = select(CasePriceContext)
    if special_situation_id:
        query = query.where(CasePriceContext.special_situation_id == special_situation_id)
    else:
        query = query.where(CasePriceContext.research_case_id == research_case_id)

    result = await db.execute(query)
    existing = result.scalars().first()
    if existing is None:
        db.add(replacement)
        await db.flush()
        return replacement

    for field in (
        "ticker",
        "offer_price",
        "offer_price_source",
        "price_snapshot_id",
        "latest_close_price",
        "latest_close_date",
        "estimated_spread_pct",
        "spread_status",
        "status_reason",
    ):
        setattr(existing, field, getattr(replacement, field))
    await db.flush()
    return existing


def build_manual_price_context(
    *,
    ticker: str | None,
    situation_type: str | None,
    offer_price=None,
    offer_price_source: str | None = None,
    latest_close_price=None,
    latest_close_date: date | None = None,
    price_snapshot_id: uuid.UUID | None = None,
    special_situation_id: uuid.UUID | None = None,
    research_case_id: uuid.UUID | None = None,
    spread_status: str | None = None,
    status_reason: str | None = None,
    today: date | None = None,
) -> CasePriceContext:
    if bool(special_situation_id) == bool(research_case_id):
        raise PriceContextError("Price context must relate to exactly one SpecialSituation or ResearchCase.")

    override = _trim_optional(spread_status)
    reason = _trim_optional(status_reason)
    if override is not None and override not in MANUAL_SPREAD_STATUS_OVERRIDES:
        raise PriceContextError("spread_status is not valid for manual price context")
    if override == SPREAD_STATUS_NOT_APPLICABLE and not reason:
        raise PriceContextError("status_reason is required when spread_status is not_applicable")

    offer = _parse_decimal_field(offer_price, "offer_price")
    close = _parse_decimal_field(latest_close_price, "latest_close_price")
    status, spread, default_reason = classify_price_context(
        situation_type=situation_type,
        offer_price=offer,
        latest_close_price=close,
        latest_close_date=latest_close_date,
        today=today,
    )
    if override is not None:
        status = override
        spread = None

    return CasePriceContext(
        special_situation_id=special_situation_id,
        research_case_id=research_case_id,
        ticker=normalize_ticker(ticker),
        offer_price=offer,
        offer_price_source=_trim_optional(offer_price_source),
        price_snapshot_id=price_snapshot_id,
        latest_close_price=close,
        latest_close_date=latest_close_date,
        estimated_spread_pct=spread,
        spread_status=status,
        status_reason=reason or default_reason,
    )


async def upsert_manual_price_context(
    db: AsyncSession,
    payload: ManualPriceContextPayload,
    *,
    today: date | None = None,
) -> CasePriceContext:
    target_id = _parse_uuid(payload.target_id)
    latest_close_date = _parse_date_field(payload.latest_close_date, "latest_close_date")
    latest_close_price = _parse_decimal_field(payload.latest_close_price, "latest_close_price")
    currency = _trim_optional(payload.currency)
    ticker = normalize_ticker(payload.ticker)

    special_situation_id = None
    research_case_id = None
    situation_type = None
    if payload.target_type == "special_situation":
        target = await db.get(SpecialSituation, target_id)
        if not target:
            raise PriceContextError("SpecialSituation target not found", status_code=404)
        special_situation_id = target.id
        situation_type = target.situation_type
        ticker = ticker or normalize_ticker(target.ticker)
    else:
        target = await db.get(ResearchCase, target_id)
        if not target:
            raise PriceContextError("ResearchCase target not found", status_code=404)
        research_case_id = target.id
        situation = None
        if target.situation_id:
            situation = await db.get(SpecialSituation, target.situation_id)
        situation_type = situation_type_from_case(target, situation)

    price_snapshot = None
    if ticker and latest_close_price is not None and latest_close_date is not None:
        price_snapshot = PriceSnapshot(
            ticker=ticker,
            provider="manual",
            latest_close_price=latest_close_price,
            close_date=latest_close_date,
            currency=currency,
            fetched_at=datetime.now(timezone.utc),
            safe_metadata={"source": "manual_research_inbox"},
        )
        db.add(price_snapshot)
        await db.flush()

    replacement = build_manual_price_context(
        ticker=ticker,
        situation_type=situation_type,
        offer_price=payload.offer_price,
        offer_price_source=payload.offer_price_source,
        latest_close_price=latest_close_price,
        latest_close_date=latest_close_date,
        price_snapshot_id=price_snapshot.id if price_snapshot else None,
        special_situation_id=special_situation_id,
        research_case_id=research_case_id,
        spread_status=payload.spread_status,
        status_reason=payload.status_reason,
        today=today,
    )
    query = select(CasePriceContext)
    if special_situation_id:
        query = query.where(CasePriceContext.special_situation_id == special_situation_id)
    else:
        query = query.where(CasePriceContext.research_case_id == research_case_id)

    result = await db.execute(query)
    existing = result.scalars().first()
    if existing is None:
        db.add(replacement)
        await db.flush()
        return replacement

    for field in (
        "ticker",
        "offer_price",
        "offer_price_source",
        "price_snapshot_id",
        "latest_close_price",
        "latest_close_date",
        "estimated_spread_pct",
        "spread_status",
        "status_reason",
    ):
        setattr(existing, field, getattr(replacement, field))
    await db.flush()
    return existing


def situation_type_from_case(rc: ResearchCase, situation: SpecialSituation | None = None) -> str | None:
    if situation and situation.situation_type:
        return situation.situation_type
    brief = rc.brief if isinstance(rc.brief, dict) else {}
    value = brief.get("situation_type") or brief.get("detected_situation_type")
    return str(value) if value else None
