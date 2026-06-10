import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from backend.models.investment import CasePriceContext, PriceSnapshot, SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.price_context import (
    DisabledPriceProvider,
    PRICE_STALENESS_DAYS,
    SPREAD_STATUS_AVAILABLE,
    SPREAD_STATUS_MISSING_MARKET_PRICE,
    SPREAD_STATUS_MISSING_OFFER_PRICE,
    SPREAD_STATUS_NOT_APPLICABLE,
    SPREAD_STATUS_STALE_PRICE,
    build_case_price_context,
    classify_price_context,
    compute_estimated_spread_pct,
    fetch_price_quote,
    normalize_ticker,
    serialize_price_context,
)
from backend.services.investment.research_inbox import build_research_inbox_queue


def _snapshot(*, latest_close_price=Decimal("8.75"), close_date=date(2026, 6, 9)):
    return PriceSnapshot(
        id=uuid.uuid4(),
        ticker="XYZ",
        provider="fake",
        latest_close_price=latest_close_price,
        close_date=close_date,
        fetched_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
        created_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
        updated_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
    )


def test_normalize_ticker():
    assert normalize_ticker(" xyz ") == "XYZ"
    assert normalize_ticker("") is None
    assert normalize_ticker(None) is None


def test_formula_exactness_with_decimal_math():
    spread = compute_estimated_spread_pct(Decimal("10.00"), Decimal("8.75"))

    assert spread == Decimal("14.2857")


def test_available_status():
    status, spread, reason = classify_price_context(
        situation_type="tender_offer",
        offer_price=Decimal("10.00"),
        latest_close_price=Decimal("8.75"),
        latest_close_date=date(2026, 6, 9),
        today=date(2026, 6, 10),
    )

    assert status == SPREAD_STATUS_AVAILABLE
    assert spread == Decimal("14.2857")
    assert "available" in reason


@pytest.mark.parametrize("offer_price", [None, Decimal("0"), Decimal("-1"), "not-a-number"])
def test_missing_offer_price_status(offer_price):
    status, spread, _ = classify_price_context(
        situation_type="tender_offer",
        offer_price=offer_price,
        latest_close_price=Decimal("8.75"),
        latest_close_date=date(2026, 6, 9),
        today=date(2026, 6, 10),
    )

    assert status == SPREAD_STATUS_MISSING_OFFER_PRICE
    assert spread is None


@pytest.mark.parametrize("latest_close_price", [None, Decimal("0"), Decimal("-1"), "not-a-number"])
def test_missing_market_price_status(latest_close_price):
    status, spread, _ = classify_price_context(
        situation_type="tender_offer",
        offer_price=Decimal("10.00"),
        latest_close_price=latest_close_price,
        latest_close_date=date(2026, 6, 9),
        today=date(2026, 6, 10),
    )

    assert status == SPREAD_STATUS_MISSING_MARKET_PRICE
    assert spread is None


def test_stale_price_status_uses_threshold():
    status, spread, _ = classify_price_context(
        situation_type="tender_offer",
        offer_price=Decimal("10.00"),
        latest_close_price=Decimal("8.75"),
        latest_close_date=date(2026, 6, 4),
        today=date(2026, 6, 10),
    )

    assert PRICE_STALENESS_DAYS == 5
    assert status == SPREAD_STATUS_STALE_PRICE
    assert spread is None


def test_not_applicable_precedence_without_offer_price():
    status, spread, _ = classify_price_context(
        situation_type="bankruptcy",
        offer_price=None,
        latest_close_price=Decimal("8.75"),
        latest_close_date=date(2026, 6, 9),
        today=date(2026, 6, 10),
    )

    assert status == SPREAD_STATUS_NOT_APPLICABLE
    assert spread is None


@pytest.mark.asyncio
async def test_disabled_provider_fails_closed():
    quote = await fetch_price_quote(DisabledPriceProvider(), "XYZ")

    assert quote is None


def test_build_case_price_context_requires_one_parent():
    with pytest.raises(ValueError):
        build_case_price_context(
            ticker="XYZ",
            situation_type="tender_offer",
            special_situation_id=uuid.uuid4(),
            research_case_id=uuid.uuid4(),
        )


def test_build_case_price_context_available():
    situation_id = uuid.uuid4()
    context = build_case_price_context(
        ticker="xyz",
        situation_type="tender_offer",
        offer_price=Decimal("10.00"),
        offer_price_source="manual",
        price_snapshot=_snapshot(),
        special_situation_id=situation_id,
        today=date(2026, 6, 10),
    )

    assert context.special_situation_id == situation_id
    assert context.research_case_id is None
    assert context.ticker == "XYZ"
    assert context.spread_status == SPREAD_STATUS_AVAILABLE
    assert context.estimated_spread_pct == Decimal("14.2857")


def test_serialize_price_context_uses_neutral_fields():
    context = CasePriceContext(
        ticker="XYZ",
        offer_price=Decimal("10.00"),
        offer_price_source="manual",
        latest_close_price=Decimal("8.75"),
        latest_close_date=date(2026, 6, 9),
        estimated_spread_pct=Decimal("14.2857"),
        spread_status=SPREAD_STATUS_AVAILABLE,
        status_reason="Price context is available.",
        updated_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
    )

    serialized = serialize_price_context(context)

    assert serialized is not None
    assert serialized.estimated_spread_pct == "14.2857"
    assert serialized.spread_status == SPREAD_STATUS_AVAILABLE


def test_research_inbox_includes_optional_price_context_without_side_effects():
    situation = SpecialSituation(
        id=uuid.uuid4(),
        situation_type="tender_offer",
        company_name="Example Co",
        ticker="XYZ",
        filing_type="SC TO-T",
        filing_url="https://www.sec.gov/Archives/example.txt",
        detected_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
        status="detected",
        evaluation={},
        created_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
        updated_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
    )
    context = CasePriceContext(
        special_situation_id=situation.id,
        ticker="XYZ",
        offer_price=Decimal("10.00"),
        latest_close_price=Decimal("8.75"),
        latest_close_date=date(2026, 6, 9),
        estimated_spread_pct=Decimal("14.2857"),
        spread_status=SPREAD_STATUS_AVAILABLE,
        updated_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
    )

    queue = build_research_inbox_queue([situation], [], [context])

    assert queue.items[0].price_context is not None
    assert queue.items[0].price_context.estimated_spread_pct == "14.2857"
    assert situation.status == "detected"


def test_price_context_does_not_mutate_research_case_status():
    rc = ResearchCase(id=uuid.uuid4(), status="under_investigation")

    build_research_inbox_queue([], [rc], [])

    assert rc.status == "under_investigation"
