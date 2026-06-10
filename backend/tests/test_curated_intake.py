import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from backend.db.database import get_db as _real_get_db
from backend.main import app
from backend.models.investment import CasePriceContext, DecisionRecord, SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.curated_intake import (
    CuratedIntakeError,
    CuratedIntakePayload,
    build_curated_special_situation,
    create_curated_special_situation,
    normalize_curated_url,
)
from backend.services.investment.research_inbox import build_research_inbox_queue

client = TestClient(app)


class FakeCuratedDb:
    def __init__(self, *, existing=None):
        self.existing = existing
        self.added = []
        self.committed = False
        self.rolled_back = False

    async def execute(self, _query):
        existing = self.existing

        class Result:
            def scalars(self_inner):
                class Scalars:
                    def first(self_scalars):
                        return existing

                return Scalars()

        return Result()

    def add(self, record):
        self.added.append(record)

    async def flush(self):
        for record in self.added:
            if getattr(record, "id", None) is None:
                record.id = uuid.uuid4()

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


def _payload(**overrides):
    values = {
        "url": "https://example.com/special-situation-writeup",
        "source_name": "Special Situation Journal",
        "ticker": "XYZ",
        "company_name": "XYZ Corp",
        "situation_type": "tender_offer",
        "title": "XYZ tender offer writeup",
        "notes": "Manual curated source intake for triage.",
        "source_published_at": "2026-06-10",
        "submitted_by": "Dani",
    }
    values.update(overrides)
    return CuratedIntakePayload(**values)


def test_normalize_curated_url_requires_http_https():
    assert normalize_curated_url(" HTTPS://Example.com/path#section ") == "https://example.com/path"

    for url in ("javascript:alert(1)", "data:text/html,test", "file:///tmp/test", "example.com/no-scheme"):
        with pytest.raises(CuratedIntakeError):
            normalize_curated_url(url)


def test_build_curated_special_situation_sets_candidate_origin():
    situation = build_curated_special_situation(
        {
            "url": "https://example.com/writeup",
            "source_name": "Special Situation Journal",
            "situation_type": "tender_offer",
            "title": "XYZ tender offer writeup",
            "summary": None,
            "ticker": "XYZ",
            "company_name": "XYZ Corp",
            "notes": "Manual note.",
            "source_published_at": "2026-06-10",
            "submitted_by": "Dani",
            "source_tier": None,
            "source_confidence": None,
        }
    )

    assert situation.status == "candidate"
    assert situation.filing_type == "curated_source"
    assert situation.evaluation["origin"] == "curated"
    assert situation.evaluation["candidate_only"] is True
    assert situation.evaluation["verified"] is False
    assert situation.evaluation["curated_intake"]["source_name"] == "Special Situation Journal"


@pytest.mark.asyncio
async def test_create_curated_special_situation():
    db = FakeCuratedDb()

    response = await create_curated_special_situation(db, _payload())

    assert response.origin == "curated"
    assert response.status == "candidate"
    assert response.candidate_only is True
    assert len(db.added) == 1
    assert isinstance(db.added[0], SpecialSituation)
    assert db.added[0].evaluation["curated_intake"]["submitted_by"] == "Dani"


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("url", "", "url"),
        ("source_name", " ", "source_name"),
        ("situation_type", "", "situation_type"),
        ("title", "", "title or summary"),
    ],
)
@pytest.mark.asyncio
async def test_required_fields(field, value, match):
    kwargs = {field: value}
    if field == "title":
        kwargs["summary"] = ""

    with pytest.raises(CuratedIntakeError, match=match):
        await create_curated_special_situation(FakeCuratedDb(), _payload(**kwargs))


@pytest.mark.asyncio
async def test_duplicate_url_safe_handling():
    existing = SpecialSituation(
        id=uuid.uuid4(),
        situation_type="tender_offer",
        company_name="Existing",
        filing_url="https://example.com/special-situation-writeup",
        status="detected",
    )

    with pytest.raises(CuratedIntakeError, match="already exists") as exc:
        await create_curated_special_situation(FakeCuratedDb(existing=existing), _payload())

    assert exc.value.status_code == 409


def test_curated_item_appears_in_research_inbox_with_origin():
    situation = build_curated_special_situation(
        {
            "url": "https://example.com/writeup",
            "source_name": "Special Situation Journal",
            "situation_type": "tender_offer",
            "title": "XYZ tender offer writeup",
            "summary": None,
            "ticker": "XYZ",
            "company_name": "XYZ Corp",
            "notes": "Manual note.",
            "source_published_at": "2026-06-10",
            "submitted_by": "Dani",
            "source_tier": None,
            "source_confidence": None,
        }
    )
    situation.id = uuid.uuid4()
    situation.created_at = datetime(2026, 6, 10, tzinfo=timezone.utc)
    decision = DecisionRecord(
        id=uuid.uuid4(),
        special_situation_id=situation.id,
        outcome="CANDIDATE",
        reason="Manual intake accepted for triage.",
        author="Dani",
        created_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
    )
    context = CasePriceContext(
        special_situation_id=situation.id,
        ticker="XYZ",
        spread_status="missing_offer_price",
        updated_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
    )

    queue = build_research_inbox_queue([situation], [], [context], [decision])

    assert queue.count == 1
    item = queue.items[0]
    assert item.candidate_only is True
    assert item.source_context == "Curated source / Special Situation Journal / tender_offer"
    assert item.latest_decision is not None
    assert item.price_context is not None


def test_endpoint_creates_no_related_records_or_automation(monkeypatch):
    db = FakeCuratedDb()

    async def fail_if_called(*_args, **_kwargs):
        raise AssertionError("scanner/provider/AI path should not be called")

    monkeypatch.setattr("backend.api.investment.router.run_special_situation_scan", fail_if_called)
    monkeypatch.setattr("backend.api.investment.router.evaluate_situation", fail_if_called)

    async def get_db_override():
        yield db

    app.dependency_overrides[_real_get_db] = get_db_override
    try:
        response = client.post(
            "/api/investment/research-inbox/curated-intake",
            json=_payload().model_dump(),
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["origin"] == "curated"
    assert db.committed is True
    assert len(db.added) == 1
    assert isinstance(db.added[0], SpecialSituation)
    assert not any(isinstance(item, ResearchCase) for item in db.added)
    assert not any(isinstance(item, DecisionRecord) for item in db.added)
    assert not any(isinstance(item, CasePriceContext) for item in db.added)
