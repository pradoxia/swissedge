import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from backend.db.database import get_db as _real_get_db
from backend.main import app
from backend.models.investment import DecisionRecord, SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.decision_records import (
    DecisionRecordCreate,
    DecisionRecordError,
    build_decision_record,
    create_decision_record,
    serialize_decision_record,
)

client = TestClient(app)


def _now():
    return datetime.now(timezone.utc)


def _situation(**overrides):
    values = {
        "id": uuid.uuid4(),
        "situation_type": "tender_offer",
        "company_name": "Example Co",
        "ticker": "EXM",
        "filing_type": "SC TO-T",
        "filing_url": "https://www.sec.gov/Archives/example.txt",
        "detected_at": _now(),
        "status": "detected",
        "evaluation": {},
        "published": False,
        "created_at": _now(),
        "updated_at": _now(),
    }
    values.update(overrides)
    return SpecialSituation(**values)


def _case(**overrides):
    values = {
        "id": uuid.uuid4(),
        "status": "under_investigation",
        "brief": {"title": "Research case title"},
        "investment_readiness": "needs_more_work",
        "created_at": _now(),
        "updated_at": _now(),
    }
    values.update(overrides)
    return ResearchCase(**values)


class FakeDecisionDb:
    def __init__(self, *, situation=None, research_case=None):
        self.situation = situation
        self.research_case = research_case
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
            if record.id is None:
                record.id = uuid.uuid4()
            if record.created_at is None:
                record.created_at = _now()
            if record.updated_at is None:
                record.updated_at = record.created_at

    async def commit(self):
        self.committed = True

    async def refresh(self, _record):
        return None

    async def rollback(self):
        self.rolled_back = True


@pytest.mark.asyncio
async def test_create_decision_for_special_situation():
    situation = _situation()
    db = FakeDecisionDb(situation=situation)

    record = await create_decision_record(
        db,
        DecisionRecordCreate(
            target_type="special_situation",
            target_id=str(situation.id),
            outcome="REJECT",
            reason=" Missing transaction terms. ",
            author=" Dani ",
        ),
    )

    assert record.special_situation_id == situation.id
    assert record.research_case_id is None
    assert record.outcome == "REJECT"
    assert record.reason == "Missing transaction terms."
    assert record.author == "Dani"
    assert situation.status == "detected"
    assert situation.published is False


@pytest.mark.asyncio
async def test_create_decision_for_research_case():
    rc = _case()
    db = FakeDecisionDb(research_case=rc)

    record = await create_decision_record(
        db,
        DecisionRecordCreate(
            target_type="research_case",
            target_id=str(rc.id),
            outcome="NEED_MORE_EVIDENCE",
            reason="Need merger agreement before manual review.",
            author="Dani",
        ),
    )

    assert record.research_case_id == rc.id
    assert record.special_situation_id is None
    assert record.outcome == "NEED_MORE_EVIDENCE"
    assert rc.status == "under_investigation"


@pytest.mark.parametrize("reason", ["", "   "])
@pytest.mark.asyncio
async def test_rejects_missing_or_whitespace_reason(reason):
    situation = _situation()
    db = FakeDecisionDb(situation=situation)

    with pytest.raises(DecisionRecordError, match="reason"):
        await create_decision_record(
            db,
            DecisionRecordCreate(
                target_type="special_situation",
                target_id=str(situation.id),
                outcome="WATCHLIST",
                reason=reason,
                author="Dani",
            ),
        )


@pytest.mark.asyncio
async def test_rejects_invalid_outcome():
    situation = _situation()
    db = FakeDecisionDb(situation=situation)

    with pytest.raises(DecisionRecordError, match="Invalid decision outcome"):
        await create_decision_record(
            db,
            DecisionRecordCreate(
                target_type="special_situation",
                target_id=str(situation.id),
                outcome="APPROVE",
                reason="Needs manual queue tracking.",
                author="Dani",
            ),
        )


def test_rejects_invalid_target_type_at_api_boundary():
    response = client.post(
        "/api/investment/research-inbox/decision",
        json={
            "target_type": "company",
            "target_id": str(uuid.uuid4()),
            "outcome": "CANDIDATE",
            "reason": "Manual note.",
            "author": "Dani",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_rejects_missing_target():
    db = FakeDecisionDb()

    with pytest.raises(DecisionRecordError, match="not found") as exc:
        await create_decision_record(
            db,
            DecisionRecordCreate(
                target_type="research_case",
                target_id=str(uuid.uuid4()),
                outcome="CANDIDATE",
                reason="Manual note.",
                author="Dani",
            ),
        )

    assert exc.value.status_code == 404


def test_enforces_exactly_one_target_in_service_logic():
    with pytest.raises(DecisionRecordError):
        build_decision_record(
            outcome="CANDIDATE",
            reason="Manual note.",
            author="Dani",
        )
    with pytest.raises(DecisionRecordError):
        build_decision_record(
            special_situation_id=uuid.uuid4(),
            research_case_id=uuid.uuid4(),
            outcome="CANDIDATE",
            reason="Manual note.",
            author="Dani",
        )


def test_serialize_decision_record_target_shape():
    situation_id = uuid.uuid4()
    record = DecisionRecord(
        id=uuid.uuid4(),
        special_situation_id=situation_id,
        outcome="WATCHLIST",
        reason="Track until evidence is clearer.",
        author="Dani",
        source_surface="research_inbox",
        created_at=_now(),
    )

    serialized = serialize_decision_record(record)

    assert serialized.target_type == "special_situation"
    assert serialized.target_id == str(situation_id)
    assert serialized.outcome == "WATCHLIST"


def test_decision_post_creates_only_record_and_preserves_target_state():
    situation = _situation(status="detected", published=False)
    db = FakeDecisionDb(situation=situation)

    async def get_db_override():
        yield db

    app.dependency_overrides[_real_get_db] = get_db_override
    try:
        response = client.post(
            "/api/investment/research-inbox/decision",
            json={
                "target_type": "special_situation",
                "target_id": str(situation.id),
                "outcome": "REJECT",
                "reason": "No filed transaction terms yet.",
                "author": "Dani",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["outcome"] == "REJECT"
    assert len(db.added) == 1
    assert db.committed is True
    assert situation.status == "detected"
    assert situation.published is False


def test_decision_post_preserves_research_case_status():
    rc = _case(status="under_investigation")
    db = FakeDecisionDb(research_case=rc)

    async def get_db_override():
        yield db

    app.dependency_overrides[_real_get_db] = get_db_override
    try:
        response = client.post(
            "/api/investment/research-inbox/decision",
            json={
                "target_type": "research_case",
                "target_id": str(rc.id),
                "outcome": "NEED_MORE_EVIDENCE",
                "reason": "Need source documents before next review.",
                "author": "Dani",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(db.added) == 1
    assert rc.status == "under_investigation"
