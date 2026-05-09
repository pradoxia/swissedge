"""Phase 1B tests: ORM relationship fix, service layer, and API endpoints."""
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.investment_research import ResearchCase, ResearchTask, ResearchDocument, ResearchSource, HistoricalCase
from backend.models.investment import SpecialSituation

client = TestClient(app)

DISCLAIMER = "Este análisis es educativo. No es asesoramiento financiero."


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now():
    return datetime.now(timezone.utc)


def _make_situation(sit_id=None):
    sit_id = sit_id or uuid.uuid4()
    s = MagicMock(spec=SpecialSituation)
    s.id = sit_id
    s.situation_type = "merger"
    s.company_name = "Test Corp"
    s.ticker = "TC"
    s.filing_type = None
    s.filing_url = None
    s.course_chapter = None
    return s


def _make_rc(rc_id=None, sit_id=None, status="detected", readiness=None):
    rc_id = rc_id or uuid.uuid4()
    sit_id = sit_id or uuid.uuid4()
    now = _now()
    rc = MagicMock(spec=ResearchCase)
    rc.id = rc_id
    rc.situation_id = sit_id
    rc.status = status
    rc.brief = None
    rc.brief_version = None
    rc.playbook_version = None
    rc.model_used = None
    rc.run_id = None
    rc.notes = None
    rc.disclaimer = DISCLAIMER
    rc.investment_readiness = readiness
    rc.created_at = now
    rc.updated_at = now
    rc.tasks = []
    rc.documents = []
    rc.sources = []
    return rc


def _make_db_mock(
    situation=None,
    research_case=None,
    research_cases=None,
    no_existing_case=False,
):
    db = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    db.refresh = AsyncMock()

    call_count = [0]

    async def execute_side_effect(query):
        result = MagicMock()
        idx = call_count[0]
        call_count[0] += 1

        if idx == 0:
            # first call: situation lookup
            result.scalars.return_value.first.return_value = situation
        elif idx == 1:
            # second call: duplicate check
            if no_existing_case:
                result.scalars.return_value.first.return_value = None
            else:
                result.scalars.return_value.first.return_value = research_case
        else:
            # subsequent calls: return research_case or list
            if research_cases is not None:
                result.scalars.return_value.all.return_value = research_cases
                result.scalars.return_value.first.return_value = research_cases[0] if research_cases else None
            else:
                result.scalars.return_value.first.return_value = research_case
                result.scalars.return_value.all.return_value = [research_case] if research_case else []

        return result

    db.execute = AsyncMock(side_effect=execute_side_effect)
    return db


# ── 1. ORM relationship fix ───────────────────────────────────────────────────

def test_historical_case_has_sources_relationship():
    assert hasattr(HistoricalCase, "sources")


def test_research_source_has_historical_case_relationship():
    assert hasattr(ResearchSource, "historical_case")


def test_research_source_historical_case_back_populates():
    from sqlalchemy.orm import RelationshipProperty
    rel = ResearchSource.__mapper__.relationships["historical_case"]
    assert isinstance(rel, RelationshipProperty)
    assert rel.back_populates == "sources"


def test_historical_case_sources_back_populates():
    from sqlalchemy.orm import RelationshipProperty
    rel = HistoricalCase.__mapper__.relationships["sources"]
    assert isinstance(rel, RelationshipProperty)
    assert rel.back_populates == "historical_case"


def test_historical_case_still_has_documents_relationship():
    assert hasattr(HistoricalCase, "documents")


def test_research_source_still_has_research_case_relationship():
    assert hasattr(ResearchSource, "research_case")


# ── 2. Schema serialization ───────────────────────────────────────────────────

def test_research_case_read_disclaimer_always_present():
    from backend.services.investment.research_cases import ResearchCaseRead
    rc = _make_rc()
    data = ResearchCaseRead.from_orm(rc)
    assert data.disclaimer == DISCLAIMER


def test_research_case_read_ids_are_strings():
    from backend.services.investment.research_cases import ResearchCaseRead
    rc = _make_rc()
    data = ResearchCaseRead.from_orm(rc)
    assert isinstance(data.id, str)
    assert isinstance(data.situation_id, str)


def test_research_case_read_null_situation_id():
    from backend.services.investment.research_cases import ResearchCaseRead
    rc = _make_rc()
    rc.situation_id = None
    data = ResearchCaseRead.from_orm(rc)
    assert data.situation_id is None


def test_research_case_read_children_lists():
    from backend.services.investment.research_cases import ResearchCaseRead
    rc = _make_rc()
    data = ResearchCaseRead.from_orm(rc)
    assert data.tasks == []
    assert data.documents == []
    assert data.sources == []


def test_research_task_read_serialization():
    from backend.services.investment.research_cases import ResearchTaskRead
    t = MagicMock(spec=ResearchTask)
    t.id = uuid.uuid4()
    t.research_case_id = uuid.uuid4()
    t.description = "Check 8-K filing"
    t.status = "open"
    t.priority = 2
    t.source = "agent"
    t.notes = None
    t.created_at = _now()
    t.resolved_at = None
    data = ResearchTaskRead.from_orm(t)
    assert data.status == "open"
    assert data.priority == 2
    assert data.resolved_at is None


def test_research_document_read_serialization():
    from backend.services.investment.research_cases import ResearchDocumentRead
    d = MagicMock(spec=ResearchDocument)
    d.id = uuid.uuid4()
    d.research_case_id = uuid.uuid4()
    d.historical_case_id = None
    d.doc_type = "sec_filing"
    d.url = "https://sec.gov/test"
    d.title = "Form 8-K"
    d.retrieved_at = None
    d.summary = None
    d.added_by = "agent"
    d.created_at = _now()
    data = ResearchDocumentRead.from_orm(d)
    assert data.url == "https://sec.gov/test"
    assert data.historical_case_id is None


def test_research_source_read_serialization():
    from backend.services.investment.research_cases import ResearchSourceRead
    s = MagicMock(spec=ResearchSource)
    s.id = uuid.uuid4()
    s.research_case_id = uuid.uuid4()
    s.historical_case_id = None
    s.investment_source_id = None
    s.source_name = "SEC EDGAR"
    s.source_url = "https://efts.sec.gov"
    s.signal_quality = "high"
    s.notes = None
    s.created_at = _now()
    data = ResearchSourceRead.from_orm(s)
    assert data.signal_quality == "high"


# ── 3. Service layer — create ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_case_situation_not_found():
    from backend.services.investment.research_cases import create_research_case_from_situation
    from fastapi import HTTPException

    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.first.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc_info:
        await create_research_case_from_situation(db, uuid.uuid4())
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_case_duplicate_rejected():
    from backend.services.investment.research_cases import create_research_case_from_situation
    from fastapi import HTTPException

    sit_id = uuid.uuid4()
    sit = _make_situation(sit_id)
    existing_rc = _make_rc(sit_id=sit_id)

    call_count = [0]
    async def execute_side_effect(query):
        result = MagicMock()
        if call_count[0] == 0:
            result.scalars.return_value.first.return_value = sit
        else:
            result.scalars.return_value.first.return_value = existing_rc
        call_count[0] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=execute_side_effect)

    with pytest.raises(HTTPException) as exc_info:
        await create_research_case_from_situation(db, sit_id)
    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_case_invalid_readiness_rejected():
    from backend.services.investment.research_cases import create_research_case_from_situation
    from fastapi import HTTPException

    sit_id = uuid.uuid4()
    sit = _make_situation(sit_id)

    call_count = [0]
    async def execute_side_effect(query):
        result = MagicMock()
        if call_count[0] == 0:
            result.scalars.return_value.first.return_value = sit
        else:
            result.scalars.return_value.first.return_value = None
        call_count[0] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.flush = AsyncMock()
    db.add = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await create_research_case_from_situation(db, sit_id, investment_readiness="BUY")
    assert exc_info.value.status_code == 400
    assert "BUY" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_case_valid_readiness_accepted():
    from backend.services.investment.research_cases import create_research_case_from_situation, VALID_READINESS

    for label in VALID_READINESS:
        sit_id = uuid.uuid4()
        sit = _make_situation(sit_id)
        new_rc = _make_rc(sit_id=sit_id, readiness=label)

        call_count = [0]
        async def execute_side_effect(query, _label=label):
            result = MagicMock()
            if call_count[0] == 0:
                result.scalars.return_value.first.return_value = sit
            else:
                result.scalars.return_value.first.return_value = None
            call_count[0] += 1
            return result

        db = AsyncMock()
        db.execute = AsyncMock(side_effect=execute_side_effect)
        db.flush = AsyncMock()
        db.add = MagicMock()
        db.refresh = AsyncMock()

        rc = await create_research_case_from_situation(db, sit_id, investment_readiness=label)
        assert db.add.called


@pytest.mark.asyncio
async def test_create_case_disclaimer_set():
    from backend.services.investment.research_cases import create_research_case_from_situation

    sit_id = uuid.uuid4()
    sit = _make_situation(sit_id)

    call_count = [0]
    async def execute_side_effect(query):
        result = MagicMock()
        if call_count[0] == 0:
            result.scalars.return_value.first.return_value = sit
        else:
            result.scalars.return_value.first.return_value = None
        call_count[0] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.refresh = AsyncMock()

    await create_research_case_from_situation(db, sit_id)

    added = next(call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], ResearchCase))
    assert added.disclaimer == DISCLAIMER


@pytest.mark.asyncio
async def test_create_case_from_sec_situation_sets_v2_metadata():
    from backend.services.investment.research_cases import create_research_case_from_situation

    sit_id = uuid.uuid4()
    sit = _make_situation(sit_id)
    sit.situation_type = "merger_arbitrage"
    sit.filing_type = "SC TO-T"
    sit.filing_url = "https://www.sec.gov/Archives/edgar/data/test"

    call_count = [0]
    async def execute_side_effect(query):
        result = MagicMock()
        result.scalars.return_value.first.return_value = sit if call_count[0] == 0 else None
        call_count[0] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.refresh = AsyncMock()

    rc = await create_research_case_from_situation(db, sit_id)

    assert rc.source_origin_name == "SEC EDGAR"
    assert rc.intake_method == "evaluation_linked"
    assert rc.connector_key == "sec_edgar_efts"
    assert rc.evidence_level == "official_primary"
    assert rc.official_source_status == "official_attached"
    assert rc.duplicate_status == "unique"
    assert rc.methodology_status in {"evaluator_ready", "partial", "routing_detection_only", "detection_only", "unknown"}


@pytest.mark.asyncio
async def test_create_case_from_non_sec_situation_sets_safe_v2_fallbacks():
    from backend.services.investment.research_cases import create_research_case_from_situation

    sit_id = uuid.uuid4()
    sit = _make_situation(sit_id)
    sit.filing_type = None
    sit.filing_url = None

    call_count = [0]
    async def execute_side_effect(query):
        result = MagicMock()
        result.scalars.return_value.first.return_value = sit if call_count[0] == 0 else None
        call_count[0] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.refresh = AsyncMock()

    rc = await create_research_case_from_situation(db, sit_id)

    assert rc.source_origin_name == "Legacy Evaluation"
    assert rc.intake_method == "evaluation_linked"
    assert rc.connector_key == "legacy_evaluation"
    assert rc.evidence_level == "unknown"
    assert rc.official_source_status == "unknown"


@pytest.mark.asyncio
async def test_create_case_from_situation_adds_initial_tasks_and_source():
    from backend.services.investment.research_cases import create_research_case_from_situation

    sit_id = uuid.uuid4()
    sit = _make_situation(sit_id)
    sit.filing_type = "8-K"
    sit.filing_url = "https://www.sec.gov/Archives/edgar/data/test"

    call_count = [0]
    async def execute_side_effect(query):
        result = MagicMock()
        result.scalars.return_value.first.return_value = sit if call_count[0] == 0 else None
        call_count[0] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.refresh = AsyncMock()

    await create_research_case_from_situation(db, sit_id)

    added = [call.args[0] for call in db.add.call_args_list]
    tasks = [item for item in added if isinstance(item, ResearchTask)]
    sources = [item for item in added if isinstance(item, ResearchSource)]
    assert len(tasks) == 5
    assert all(task.status == "open" for task in tasks)
    assert all(task.priority == 2 for task in tasks)
    assert len(sources) == 1
    assert sources[0].source_name == "SEC EDGAR"
    assert sources[0].source_url == sit.filing_url
    assert sources[0].signal_quality == "high"


def test_create_from_situation_does_not_call_live_ai():
    import inspect
    import backend.services.investment.research_cases as svc

    src = inspect.getsource(svc.create_research_case_from_situation)
    assert "complete_with_usage" not in src
    assert "generate_" not in src


# ── 4. Service layer — list filters ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_cases_invalid_status_rejected():
    from backend.services.investment.research_cases import list_research_cases
    from fastapi import HTTPException

    db = AsyncMock()
    with pytest.raises(HTTPException) as exc_info:
        await list_research_cases(db, status="INVALID")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_list_cases_invalid_readiness_rejected():
    from backend.services.investment.research_cases import list_research_cases
    from fastapi import HTTPException

    db = AsyncMock()
    with pytest.raises(HTTPException) as exc_info:
        await list_research_cases(db, investment_readiness="sell_now")
    assert exc_info.value.status_code == 400
    assert "sell_now" in exc_info.value.detail


@pytest.mark.asyncio
async def test_list_cases_valid_readiness_labels():
    from backend.services.investment.research_cases import list_research_cases, VALID_READINESS

    for label in VALID_READINESS:
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db = AsyncMock()
        db.execute = AsyncMock(return_value=result)
        cases = await list_research_cases(db, investment_readiness=label)
        assert cases == []


# ── 5. Service layer — update ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_case_invalid_status():
    from backend.services.investment.research_cases import update_research_case, ResearchCaseUpdate
    from fastapi import HTTPException

    rc = _make_rc()
    result = MagicMock()
    result.scalars.return_value.first.return_value = rc
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    db.flush = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await update_research_case(db, rc.id, ResearchCaseUpdate(status="SELL"))
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_update_case_invalid_readiness():
    from backend.services.investment.research_cases import update_research_case, ResearchCaseUpdate
    from fastapi import HTTPException

    rc = _make_rc()
    result = MagicMock()
    result.scalars.return_value.first.return_value = rc
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    db.flush = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await update_research_case(db, rc.id, ResearchCaseUpdate(investment_readiness="buy"))
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_update_case_not_found():
    from backend.services.investment.research_cases import update_research_case, ResearchCaseUpdate
    from fastapi import HTTPException

    result = MagicMock()
    result.scalars.return_value.first.return_value = None
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc_info:
        await update_research_case(db, uuid.uuid4(), ResearchCaseUpdate(status="documented"))
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_case_valid_status_and_readiness():
    from backend.services.investment.research_cases import update_research_case, ResearchCaseUpdate

    rc_id = uuid.uuid4()
    rc = _make_rc(rc_id=rc_id)

    result = MagicMock()
    result.scalars.return_value.first.return_value = rc
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    await update_research_case(db, rc_id, ResearchCaseUpdate(status="documented", investment_readiness="candidate"))
    assert rc.status == "documented"
    assert rc.investment_readiness == "candidate"


# ── 6. Readiness label contract ───────────────────────────────────────────────

def test_valid_readiness_labels_exact_set():
    from backend.services.investment.research_cases import VALID_READINESS
    assert VALID_READINESS == {"monitor", "not_actionable", "needs_more_work", "candidate"}


def test_valid_readiness_labels_no_buy_sell():
    from backend.services.investment.research_cases import VALID_READINESS
    forbidden = {"buy", "sell", "purchase", "short"}
    for label in VALID_READINESS:
        for term in forbidden:
            assert term not in label.lower()


def test_valid_statuses_exact_set():
    from backend.services.investment.research_cases import VALID_STATUSES
    assert VALID_STATUSES == {
        "detected", "brief_generated", "under_investigation",
        "documented", "archived", "published",
    }


# ── 7. API endpoint tests ─────────────────────────────────────────────────────
# Use app.dependency_overrides to inject mock DB — required for TestClient.

from backend.db.database import get_db as _real_get_db


def _override_db(db_mock):
    async def _fake():
        yield db_mock
    app.dependency_overrides[_real_get_db] = _fake


def _clear_db_override():
    app.dependency_overrides.pop(_real_get_db, None)


def test_api_list_cases_returns_shape():
    rc_id = uuid.uuid4()
    sit_id = uuid.uuid4()
    rc = _make_rc(rc_id=rc_id, sit_id=sit_id)

    result = MagicMock()
    result.scalars.return_value.all.return_value = [rc]
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    _override_db(db)
    try:
        resp = client.get("/api/investment/research-cases")
    finally:
        _clear_db_override()

    assert resp.status_code == 200
    data = resp.json()
    assert "research_cases" in data
    assert "count" in data


def test_api_list_cases_invalid_status_returns_400():
    db = AsyncMock()
    _override_db(db)
    try:
        resp = client.get("/api/investment/research-cases?status=GARBAGE")
    finally:
        _clear_db_override()
    assert resp.status_code == 400


def test_api_list_cases_invalid_readiness_returns_400():
    db = AsyncMock()
    _override_db(db)
    try:
        resp = client.get("/api/investment/research-cases?investment_readiness=buy_now")
    finally:
        _clear_db_override()
    assert resp.status_code == 400


def test_api_get_case_not_found():
    case_id = str(uuid.uuid4())
    result = MagicMock()
    result.scalars.return_value.first.return_value = None
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    _override_db(db)
    try:
        resp = client.get(f"/api/investment/research-cases/{case_id}")
    finally:
        _clear_db_override()
    assert resp.status_code == 404


def test_api_create_from_situation_not_found():
    sit_id = str(uuid.uuid4())
    result = MagicMock()
    result.scalars.return_value.first.return_value = None
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)

    _override_db(db)
    try:
        resp = client.post(f"/api/investment/research-cases/from-situation/{sit_id}")
    finally:
        _clear_db_override()
    assert resp.status_code == 404


def test_api_create_from_situation_duplicate_returns_409():
    sit_id = uuid.uuid4()
    sit = _make_situation(sit_id)
    existing_rc = _make_rc(sit_id=sit_id)
    call_count = [0]

    async def execute_side_effect(query):
        result = MagicMock()
        result.scalars.return_value.first.return_value = sit if call_count[0] == 0 else existing_rc
        call_count[0] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()

    _override_db(db)
    try:
        resp = client.post(f"/api/investment/research-cases/from-situation/{sit_id}")
    finally:
        _clear_db_override()
    assert resp.status_code == 409


def test_api_create_from_situation_invalid_readiness_returns_400():
    sit_id = uuid.uuid4()
    sit = _make_situation(sit_id)
    call_count = [0]

    async def execute_side_effect(query):
        result = MagicMock()
        result.scalars.return_value.first.return_value = sit if call_count[0] == 0 else None
        call_count[0] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()

    _override_db(db)
    try:
        resp = client.post(
            f"/api/investment/research-cases/from-situation/{sit_id}",
            params={"investment_readiness": "BUY"},
        )
    finally:
        _clear_db_override()
    assert resp.status_code == 400


def test_api_patch_invalid_readiness_returns_400():
    rc_id = uuid.uuid4()
    rc = _make_rc(rc_id=rc_id)
    result = MagicMock()
    result.scalars.return_value.first.return_value = rc
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    db.flush = AsyncMock()
    db.commit = AsyncMock()

    _override_db(db)
    try:
        resp = client.patch(
            f"/api/investment/research-cases/{rc_id}",
            json={"investment_readiness": "sell"},
        )
    finally:
        _clear_db_override()
    assert resp.status_code == 400


def test_api_patch_invalid_status_returns_400():
    rc_id = uuid.uuid4()
    rc = _make_rc(rc_id=rc_id)
    result = MagicMock()
    result.scalars.return_value.first.return_value = rc
    db = AsyncMock()
    db.execute = AsyncMock(return_value=result)
    db.flush = AsyncMock()
    db.commit = AsyncMock()

    _override_db(db)
    try:
        resp = client.patch(
            f"/api/investment/research-cases/{rc_id}",
            json={"status": "GARBAGE"},
        )
    finally:
        _clear_db_override()
    assert resp.status_code == 400


# ── 8. Scope containment ──────────────────────────────────────────────────────

def test_no_scanner_imports_in_research_cases_service():
    import backend.services.investment.research_cases as svc
    import inspect
    src = inspect.getsource(svc)
    assert "sec_edgar" not in src
    assert "evaluate_situation" not in src
    assert "scan" not in src.lower().replace("research_case", "")


def test_no_scanner_imports_in_research_cases_router():
    import backend.api.investment.research_cases as rtr
    import inspect
    src = inspect.getsource(rtr)
    assert "sec_edgar" not in src
    assert "evaluate_situation" not in src


def test_research_cases_router_registered():
    from backend.main import app
    routes = [r.path for r in app.routes]
    assert "/api/investment/research-cases" in routes
    assert "/api/investment/research-cases/{research_case_id}" in routes
    assert "/api/investment/research-cases/from-situation/{situation_id}" in routes


def test_existing_investment_router_unchanged():
    from backend.main import app
    routes = [r.path for r in app.routes]
    assert "/api/investment/scan" in routes
    assert "/api/investment/situations" in routes
    assert "/api/investment/sources" in routes
