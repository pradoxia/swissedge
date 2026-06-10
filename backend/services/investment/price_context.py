from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Protocol

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


def situation_type_from_case(rc: ResearchCase, situation: SpecialSituation | None = None) -> str | None:
    if situation and situation.situation_type:
        return situation.situation_type
    brief = rc.brief if isinstance(rc.brief, dict) else {}
    value = brief.get("situation_type") or brief.get("detected_situation_type")
    return str(value) if value else None
