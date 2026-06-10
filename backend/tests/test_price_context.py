import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.db.database import get_db as _real_get_db
from backend.main import app
from backend.models.investment import CasePriceContext, PriceSnapshot, SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.price_context import (
    DisabledPriceProvider,
    ManualPriceContextPayload,
    PRICE_STALENESS_DAYS,
    PriceContextError,
    SPREAD_STATUS_AVAILABLE,
    SPREAD_STATUS_MISSING_MARKET_PRICE,
    SPREAD_STATUS_MISSING_OFFER_PRICE,
    SPREAD_STATUS_NOT_APPLICABLE,
    SPREAD_STATUS_STALE_PRICE,
    build_case_price_context,
    build_manual_price_context,
    classify_price_context,
    compute_estimated_spread_pct,
    fetch_price_quote,
    normalize_ticker,
    serialize_price_context,
    upsert_manual_price_context,
)
from backend.services.investment.research_inbox import build_research_inbox_queue

client = TestClient(app)


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


def _situation(**overrides):
    values = {
        "id": uuid.uuid4(),
        "situation_type": "tender_offer",
        "company_name": "Example Co",
        "ticker": "XYZ",
        "filing_type": "SC TO-T",
        "filing_url": "https://www.sec.gov/Archives/example.txt",
        "detected_at": datetime(2026, 6, 10, tzinfo=timezone.utc),
        "status": "detected",
        "evaluation": {},
        "created_at": datetime(2026, 6, 10, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 10, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return SpecialSituation(**values)


def _case(**overrides):
    values = {
        "id": uuid.uuid4(),
        "status": "under_investigation",
        "brief": {"title": "Research case title", "situation_type": "tender_offer"},
        "created_at": datetime(2026, 6, 10, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 6, 10, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return ResearchCase(**values)


class FakePriceContextDb:
    def __init__(self, *, situation=None, research_case=None, existing_context=None):
        self.situation = situation
        self.research_case = research_case
        self.existing_context = existing_context
        self.added = []
        self.committed = False
        self.rolled_back = False

    async def get(self, model, target_id):
        if model is SpecialSituation and self.situation and self.situation.id == target_id:
            return self.situation
        if model is ResearchCase and self.research_case and self.research_case.id == target_id:
            return self.research_case
        return None

    def add(self, record):
        self.added.append(record)

    async def flush(self):
        for record in self.added:
            if getattr(record, "id", None) is None:
                record.id = uuid.uuid4()
            if getattr(record, "created_at", None) is None:
                record.created_at = datetime(2026, 6, 10, tzinfo=timezone.utc)
            if getattr(record, "updated_at", None) is None:
                record.updated_at = datetime(2026, 6, 10, tzinfo=timezone.utc)

    async def execute(self, _query):
        context = self.existing_context

        class Result:
            def scalars(self_inner):
                class Scalars:
                    def first(self_scalars):
                        return context

                return Scalars()

        return Result()

    async def commit(self):
        self.committed = True

    async def refresh(self, record):
        if getattr(record, "updated_at", None) is None:
            record.updated_at = datetime(2026, 6, 10, tzinfo=timezone.utc)

    async def rollback(self):
        self.rolled_back = True


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


def test_manual_price_context_calculates_with_decimal_exactness():
    context = build_manual_price_context(
        ticker=" xyz ",
        situation_type="tender_offer",
        offer_price="10.00",
        offer_price_source=" 8-K transaction terms ",
        latest_close_price="8.75",
        latest_close_date=date(2026, 6, 10),
        special_situation_id=uuid.uuid4(),
        status_reason=" Manual close entered by Dani. ",
        today=date(2026, 6, 10),
    )

    assert context.ticker == "XYZ"
    assert context.offer_price == Decimal("10.00")
    assert context.offer_price_source == "8-K transaction terms"
    assert context.estimated_spread_pct == Decimal("14.2857")
    assert context.spread_status == SPREAD_STATUS_AVAILABLE
    assert context.status_reason == "Manual close entered by Dani."


def test_manual_missing_offer_price_status():
    context = build_manual_price_context(
        ticker="XYZ",
        situation_type="tender_offer",
        latest_close_price="8.75",
        latest_close_date=date(2026, 6, 10),
        special_situation_id=uuid.uuid4(),
        today=date(2026, 6, 10),
    )

    assert context.spread_status == SPREAD_STATUS_MISSING_OFFER_PRICE
    assert context.estimated_spread_pct is None


def test_manual_missing_market_price_status():
    context = build_manual_price_context(
        ticker="XYZ",
        situation_type="tender_offer",
        offer_price="10.00",
        special_situation_id=uuid.uuid4(),
        today=date(2026, 6, 10),
    )

    assert context.spread_status == SPREAD_STATUS_MISSING_MARKET_PRICE
    assert context.estimated_spread_pct is None


def test_manual_stale_price_status():
    context = build_manual_price_context(
        ticker="XYZ",
        situation_type="tender_offer",
        offer_price="10.00",
        latest_close_price="8.75",
        latest_close_date=date(2026, 6, 4),
        special_situation_id=uuid.uuid4(),
        today=date(2026, 6, 10),
    )

    assert context.spread_status == SPREAD_STATUS_STALE_PRICE
    assert context.estimated_spread_pct is None


def test_manual_not_applicable_requires_reason():
    with pytest.raises(PriceContextError, match="status_reason"):
        build_manual_price_context(
            ticker="XYZ",
            situation_type="tender_offer",
            spread_status=SPREAD_STATUS_NOT_APPLICABLE,
            special_situation_id=uuid.uuid4(),
        )


def test_manual_not_applicable_does_not_calculate_spread():
    context = build_manual_price_context(
        ticker="XYZ",
        situation_type="tender_offer",
        offer_price="10.00",
        latest_close_price="8.75",
        latest_close_date=date(2026, 6, 10),
        spread_status=SPREAD_STATUS_NOT_APPLICABLE,
        status_reason="No fixed offer price; not a spread-to-offer case.",
        special_situation_id=uuid.uuid4(),
        today=date(2026, 6, 10),
    )

    assert context.spread_status == SPREAD_STATUS_NOT_APPLICABLE
    assert context.estimated_spread_pct is None


@pytest.mark.parametrize("field_name", ["offer_price", "latest_close_price"])
def test_manual_invalid_prices_rejected(field_name):
    kwargs = {
        "ticker": "XYZ",
        "situation_type": "tender_offer",
        "offer_price": "10.00",
        "latest_close_price": "8.75",
        "latest_close_date": date(2026, 6, 10),
        "special_situation_id": uuid.uuid4(),
    }
    kwargs[field_name] = "not-a-price"

    with pytest.raises(PriceContextError, match=field_name):
        build_manual_price_context(**kwargs)


@pytest.mark.asyncio
async def test_manual_upsert_for_special_situation():
    situation = _situation(status="detected")
    db = FakePriceContextDb(situation=situation)

    context = await upsert_manual_price_context(
        db,
        ManualPriceContextPayload(
            target_type="special_situation",
            target_id=str(situation.id),
            ticker="XYZ",
            offer_price="10.00",
            offer_price_source="8-K transaction terms",
            latest_close_price="8.75",
            latest_close_date="2026-06-10",
            currency="USD",
            status_reason="Manual close entered by Dani for triage context.",
        ),
        today=date(2026, 6, 10),
    )

    assert context.special_situation_id == situation.id
    assert context.estimated_spread_pct == Decimal("14.2857")
    assert context.spread_status == SPREAD_STATUS_AVAILABLE
    assert situation.status == "detected"
    assert any(isinstance(item, PriceSnapshot) for item in db.added)


@pytest.mark.asyncio
async def test_manual_upsert_for_research_case():
    rc = _case(status="under_investigation")
    db = FakePriceContextDb(research_case=rc)

    context = await upsert_manual_price_context(
        db,
        ManualPriceContextPayload(
            target_type="research_case",
            target_id=str(rc.id),
            ticker="XYZ",
            offer_price="10.00",
            latest_close_price="8.75",
            latest_close_date="2026-06-10",
            status_reason="Manual close entered by Dani for triage context.",
        ),
        today=date(2026, 6, 10),
    )

    assert context.research_case_id == rc.id
    assert context.special_situation_id is None
    assert rc.status == "under_investigation"


@pytest.mark.asyncio
async def test_manual_upsert_rejects_invalid_target():
    db = FakePriceContextDb()

    with pytest.raises(PriceContextError, match="not found") as exc:
        await upsert_manual_price_context(
            db,
            ManualPriceContextPayload(
                target_type="special_situation",
                target_id=str(uuid.uuid4()),
                ticker="XYZ",
                status_reason="Manual context.",
            ),
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_manual_upsert_does_not_call_provider_or_ai(monkeypatch):
    situation = _situation()
    db = FakePriceContextDb(situation=situation)

    async def fail_provider(*_args, **_kwargs):
        raise AssertionError("provider call should not happen")

    monkeypatch.setattr("backend.services.investment.price_context.fetch_price_quote", fail_provider)

    context = await upsert_manual_price_context(
        db,
        ManualPriceContextPayload(
            target_type="special_situation",
            target_id=str(situation.id),
            ticker="XYZ",
            offer_price="10.00",
            latest_close_price="8.75",
            latest_close_date="2026-06-10",
        ),
        today=date(2026, 6, 10),
    )

    assert context.spread_status == SPREAD_STATUS_AVAILABLE


def test_price_context_endpoint_preserves_target_status():
    situation = _situation(status="detected")
    db = FakePriceContextDb(situation=situation)

    async def get_db_override():
        yield db

    app.dependency_overrides[_real_get_db] = get_db_override
    try:
        response = client.post(
            "/api/investment/research-inbox/price-context",
            json={
                "target_type": "special_situation",
                "target_id": str(situation.id),
                "ticker": "XYZ",
                "offer_price": "10.00",
                "offer_price_source": "8-K transaction terms",
                "latest_close_price": "8.75",
                "latest_close_date": "2026-06-10",
                "currency": "USD",
                "status_reason": "Manual close entered by Dani for triage context.",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()["price_context"]
    assert data["estimated_spread_pct"] == "14.2857"
    assert data["spread_status"] == SPREAD_STATUS_AVAILABLE
    assert db.committed is True
    assert situation.status == "detected"
