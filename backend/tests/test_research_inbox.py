import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from backend.db.database import get_db as _real_get_db
from backend.main import app
from backend.models.investment import CasePriceContext, DecisionRecord, SpecialSituation
from backend.models.investment_research import ResearchCase, ResearchTask
from backend.services.investment.methodology_workspace import WORKSPACE_KEY
from backend.services.investment.research_inbox import build_research_inbox_queue

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
        "evaluation": {
            "sec_detection": {"candidate_only": False},
            WORKSPACE_KEY: {
                "workflow_status": "needs_resources",
                "required_resources": [
                    {"resource_id": "offer_document", "title": "Offer document", "status": "missing"}
                ],
                "checklist": [],
            },
        },
        "created_at": _now(),
        "updated_at": _now(),
    }
    values.update(overrides)
    return SpecialSituation(**values)


def _case(**overrides):
    rc = ResearchCase(
        id=uuid.uuid4(),
        status="under_investigation",
        brief={"title": "Research case title"},
        investment_readiness="needs_more_work",
        source_origin_name="SEC EDGAR",
        intake_method="manual_promotion",
        evidence_level="official_primary",
        created_at=_now(),
        updated_at=_now(),
    )
    rc.tasks = [
        ResearchTask(
            id=uuid.uuid4(),
            research_case_id=rc.id,
            description="Review documents",
            status="open",
            priority=2,
            created_at=_now(),
        )
    ]
    rc.documents = []
    rc.sources = []
    for key, value in overrides.items():
        setattr(rc, key, value)
    return rc


def test_unified_queue_includes_special_situations_and_research_cases():
    queue = build_research_inbox_queue([_situation()], [_case()])

    assert queue.count == 2
    assert {item.entity_type for item in queue.items} == {"special_situation", "research_case"}


def test_candidate_only_flag_appears_when_present():
    situation = _situation(evaluation={"sec_detection": {"candidate_only": True}})

    queue = build_research_inbox_queue([situation], [])
    item = queue.items[0]

    assert item.candidate_only is True
    assert item.phase == "candidate_only"
    assert item.next_action == "Review candidate-only filing"
    assert item.detail_href == f"/investment/situations/{situation.id}"
    assert item.actions[0].href == f"/investment/situations/{situation.id}"


def test_missing_fields_do_not_crash_and_are_explicit():
    situation = _situation(
        ticker=None,
        filing_type=None,
        filing_url=None,
        evaluation=None,
    )
    rc = _case(brief=None, source_origin_name=None, intake_method=None, evidence_level=None)

    queue = build_research_inbox_queue([situation], [rc])

    assert queue.count == 2
    assert all(item.source_context for item in queue.items)
    assert any(item.source_context == "unknown" for item in queue.items)
    assert all(item.blocker_summary for item in queue.items)


def test_next_action_labels_are_safe_and_manual_only():
    queue = build_research_inbox_queue([_situation()], [_case()])
    serialized = " ".join([item.next_action for item in queue.items]).lower()

    for prohibited in ("buy", "sell", "recommendation"):
        assert prohibited not in serialized
    for item in queue.items:
        assert item.actions
        assert all(action.manual_only is True for action in item.actions)


def test_build_queue_has_no_auto_promotion_or_decision_side_effects():
    situation = _situation(status="detected")
    rc = _case(status="under_investigation")

    build_research_inbox_queue([situation], [rc])

    assert situation.status == "detected"
    assert rc.status == "under_investigation"


def test_archived_research_cases_are_excluded():
    queue = build_research_inbox_queue([], [_case(status="archived")])

    assert queue.count == 0
    assert queue.items == []


def test_decision_actions_are_manual_audit_context():
    queue = build_research_inbox_queue([_situation()], [])

    actions = [action.action for item in queue.items for action in item.actions]
    assert "reject" not in actions
    assert any("manual audit context" in item for item in queue.deferred_decisions)


def test_research_inbox_includes_latest_decision_when_present():
    situation = _situation()
    older = DecisionRecord(
        id=uuid.uuid4(),
        special_situation_id=situation.id,
        outcome="CANDIDATE",
        reason="Initial manual queue note.",
        author="Dani",
        source_surface="research_inbox",
        created_at=datetime(2026, 6, 9, tzinfo=timezone.utc),
    )
    latest = DecisionRecord(
        id=uuid.uuid4(),
        special_situation_id=situation.id,
        outcome="NEED_MORE_EVIDENCE",
        reason="Need full filing body before review.",
        author="Dani",
        source_surface="research_inbox",
        created_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
    )

    queue = build_research_inbox_queue([situation], [], decision_records=[latest, older])

    assert queue.items[0].latest_decision is not None
    assert queue.items[0].latest_decision.outcome == "NEED_MORE_EVIDENCE"
    assert queue.items[0].latest_decision.reason == "Need full filing body before review."


def test_research_inbox_absence_of_decision_is_safe():
    queue = build_research_inbox_queue([_situation()], [])

    assert queue.items[0].latest_decision is None


def test_research_inbox_preserves_price_context_when_decision_present():
    situation = _situation()
    context = CasePriceContext(
        special_situation_id=situation.id,
        ticker="EXM",
        offer_price=Decimal("10.00"),
        latest_close_price=Decimal("8.75"),
        latest_close_date=date(2026, 6, 9),
        estimated_spread_pct=Decimal("14.2857"),
        spread_status="available",
        updated_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
    )
    decision = DecisionRecord(
        id=uuid.uuid4(),
        special_situation_id=situation.id,
        outcome="WATCHLIST",
        reason="Track manually until more evidence arrives.",
        author="Dani",
        created_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
    )

    queue = build_research_inbox_queue([situation], [], [context], [decision])

    assert queue.items[0].price_context is not None
    assert queue.items[0].price_context.estimated_spread_pct == "14.2857"
    assert queue.items[0].latest_decision is not None
    assert queue.items[0].latest_decision.outcome == "WATCHLIST"


def test_research_inbox_shows_curated_source_context():
    situation = _situation(
        filing_type="curated_source",
        status="detected",
        evaluation={
            "origin": "curated",
            "candidate_only": True,
            "verified": False,
            "curated_intake": {
                "source_name": "Special Situation Journal",
                "source_url": "https://example.com/writeup",
            },
        },
    )

    queue = build_research_inbox_queue([situation], [])
    item = queue.items[0]

    assert item.candidate_only is True
    assert item.phase == "candidate_only"
    assert item.source_context == "Curated source / Special Situation Journal / tender_offer"


def test_research_inbox_endpoint_returns_unified_queue():
    situation = _situation()
    rc = _case()
    db = AsyncMock()
    situation_result = MagicMock()
    situation_result.scalars.return_value.all.return_value = [situation]
    rc_result = MagicMock()
    rc_result.scalars.return_value.all.return_value = [rc]
    context_result = MagicMock()
    context_result.scalars.return_value.all.return_value = []
    decision_result = MagicMock()
    decision_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(side_effect=[situation_result, rc_result, context_result, decision_result])

    async def get_db_override():
        yield db

    app.dependency_overrides[_real_get_db] = get_db_override
    try:
        response = client.get("/api/investment/research-inbox")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert {item["entity_type"] for item in data["items"]} == {"special_situation", "research_case"}
    assert "No automatic ResearchCase creation" in " ".join(data["guardrails"])
