"""Phase 1E tests: task/document/source add-edit endpoints and service functions."""
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_db as _real_get_db
from backend.models.investment_research import ResearchCase, ResearchTask, ResearchDocument, ResearchSource

client = TestClient(app)

DISCLAIMER = "Este análisis es educativo. No es asesoramiento financiero."


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now():
    return datetime.now(timezone.utc)


def _make_rc(rc_id=None):
    rc_id = rc_id or uuid.uuid4()
    now = _now()
    rc = MagicMock(spec=ResearchCase)
    rc.id = rc_id
    rc.situation_id = uuid.uuid4()
    rc.status = "detected"
    rc.brief = None
    rc.brief_version = None
    rc.playbook_version = None
    rc.model_used = None
    rc.run_id = None
    rc.notes = None
    rc.disclaimer = DISCLAIMER
    rc.investment_readiness = None
    rc.created_at = now
    rc.updated_at = now
    rc.tasks = []
    rc.documents = []
    rc.sources = []
    return rc


def _make_task(task_id=None, rc_id=None, status="open"):
    task_id = task_id or uuid.uuid4()
    rc_id = rc_id or uuid.uuid4()
    now = _now()
    t = MagicMock(spec=ResearchTask)
    t.id = task_id
    t.research_case_id = rc_id
    t.description = "Test task description"
    t.status = status
    t.priority = 3
    t.source = None
    t.notes = None
    t.created_at = now
    t.resolved_at = None
    return t


def _make_doc(doc_id=None, rc_id=None):
    doc_id = doc_id or uuid.uuid4()
    rc_id = rc_id or uuid.uuid4()
    now = _now()
    d = MagicMock(spec=ResearchDocument)
    d.id = doc_id
    d.research_case_id = rc_id
    d.historical_case_id = None
    d.doc_type = "filing"
    d.url = "https://example.com/doc.pdf"
    d.title = "Test Document"
    d.retrieved_at = None
    d.summary = None
    d.added_by = "dani"
    d.created_at = now
    return d


def _make_source(src_id=None, rc_id=None):
    src_id = src_id or uuid.uuid4()
    rc_id = rc_id or uuid.uuid4()
    now = _now()
    s = MagicMock(spec=ResearchSource)
    s.id = src_id
    s.research_case_id = rc_id
    s.historical_case_id = None
    s.investment_source_id = None
    s.source_name = "SEC EDGAR"
    s.source_url = "https://sec.gov"
    s.signal_quality = "high"
    s.notes = None
    s.created_at = now
    return s


def _override_db(db_mock):
    async def _fake():
        yield db_mock
    app.dependency_overrides[_real_get_db] = _fake


def _clear_db_override():
    app.dependency_overrides.pop(_real_get_db, None)


def _simple_db(first_return=None, all_return=None):
    db = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    db.refresh = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.first.return_value = first_return
    result.scalars.return_value.all.return_value = all_return or []
    db.execute = AsyncMock(return_value=result)
    return db


# ── Schema tests ──────────────────────────────────────────────────────────────

def test_research_task_create_defaults():
    from backend.services.investment.research_cases import ResearchTaskCreate
    payload = ResearchTaskCreate(description="Do something")
    assert payload.priority == 3
    assert payload.notes is None


def test_research_task_update_all_optional():
    from backend.services.investment.research_cases import ResearchTaskUpdate
    payload = ResearchTaskUpdate()
    assert payload.status is None
    assert payload.notes is None


def test_research_document_create_requires_url():
    from backend.services.investment.research_cases import ResearchDocumentCreate
    payload = ResearchDocumentCreate(url="https://example.com")
    assert payload.url == "https://example.com"
    assert payload.title is None


def test_research_source_create_requires_name_and_quality():
    from backend.services.investment.research_cases import ResearchSourceCreate
    payload = ResearchSourceCreate(source_name="Reuters", signal_quality="medium")
    assert payload.source_name == "Reuters"
    assert payload.signal_quality == "medium"


def test_valid_task_statuses_constant():
    from backend.services.investment.research_cases import VALID_TASK_STATUSES
    assert VALID_TASK_STATUSES == {"open", "done", "deferred", "cancelled"}


def test_valid_signal_quality_constant():
    from backend.services.investment.research_cases import VALID_SIGNAL_QUALITY
    assert VALID_SIGNAL_QUALITY == {"high", "medium", "low", "no_signal"}


def test_research_task_read_from_orm():
    from backend.services.investment.research_cases import ResearchTaskRead
    t = _make_task()
    data = ResearchTaskRead.from_orm(t)
    assert data.status == "open"
    assert data.priority == 3
    assert data.resolved_at is None


def test_research_document_read_from_orm():
    from backend.services.investment.research_cases import ResearchDocumentRead
    d = _make_doc()
    data = ResearchDocumentRead.from_orm(d)
    assert data.url == "https://example.com/doc.pdf"
    assert data.historical_case_id is None


def test_research_source_read_from_orm():
    from backend.services.investment.research_cases import ResearchSourceRead
    s = _make_source()
    data = ResearchSourceRead.from_orm(s)
    assert data.signal_quality == "high"
    assert data.source_name == "SEC EDGAR"


# ── Service layer: tasks ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_task_case_not_found():
    from backend.services.investment.research_cases import create_task, ResearchTaskCreate
    from fastapi import HTTPException
    db = _simple_db(first_return=None)
    with pytest.raises(HTTPException) as exc_info:
        await create_task(db, uuid.uuid4(), ResearchTaskCreate(description="x"))
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_task_success():
    from backend.services.investment.research_cases import create_task, ResearchTaskCreate
    rc = _make_rc()
    task = _make_task(rc_id=rc.id)
    db = _simple_db(first_return=rc)

    async def refresh_side(obj):
        pass
    db.refresh = AsyncMock(side_effect=refresh_side)

    def add_side(obj):
        pass
    db.add = MagicMock(side_effect=add_side)

    result = await create_task(db, rc.id, ResearchTaskCreate(description="Test task"))
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_task_invalid_status():
    from backend.services.investment.research_cases import update_task, ResearchTaskUpdate
    from fastapi import HTTPException
    task = _make_task()
    db = _simple_db(first_return=task)
    with pytest.raises(HTTPException) as exc_info:
        await update_task(db, task.id, ResearchTaskUpdate(status="invalid_status"))
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_update_task_not_found():
    from backend.services.investment.research_cases import update_task, ResearchTaskUpdate
    from fastapi import HTTPException
    db = _simple_db(first_return=None)
    with pytest.raises(HTTPException) as exc_info:
        await update_task(db, uuid.uuid4(), ResearchTaskUpdate(status="done"))
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_task_done_sets_resolved_at():
    from backend.services.investment.research_cases import update_task, ResearchTaskUpdate
    task = _make_task()
    task.resolved_at = None
    db = _simple_db(first_return=task)
    await update_task(db, task.id, ResearchTaskUpdate(status="done"))
    assert task.resolved_at is not None


@pytest.mark.asyncio
async def test_update_task_non_done_clears_resolved_at():
    from backend.services.investment.research_cases import update_task, ResearchTaskUpdate
    task = _make_task(status="done")
    task.resolved_at = _now()
    db = _simple_db(first_return=task)
    await update_task(db, task.id, ResearchTaskUpdate(status="open"))
    assert task.resolved_at is None


@pytest.mark.asyncio
async def test_list_tasks_case_not_found():
    from backend.services.investment.research_cases import list_tasks
    from fastapi import HTTPException
    db = _simple_db(first_return=None)
    with pytest.raises(HTTPException) as exc_info:
        await list_tasks(db, uuid.uuid4())
    assert exc_info.value.status_code == 404


# ── Service layer: documents ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_document_case_not_found():
    from backend.services.investment.research_cases import create_document, ResearchDocumentCreate
    from fastapi import HTTPException
    db = _simple_db(first_return=None)
    with pytest.raises(HTTPException) as exc_info:
        await create_document(db, uuid.uuid4(), ResearchDocumentCreate(url="https://x.com"))
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_document_success():
    from backend.services.investment.research_cases import create_document, ResearchDocumentCreate
    rc = _make_rc()
    db = _simple_db(first_return=rc)
    await create_document(db, rc.id, ResearchDocumentCreate(url="https://sec.gov/doc.pdf", title="Filing"))
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_list_documents_case_not_found():
    from backend.services.investment.research_cases import list_documents
    from fastapi import HTTPException
    db = _simple_db(first_return=None)
    with pytest.raises(HTTPException) as exc_info:
        await list_documents(db, uuid.uuid4())
    assert exc_info.value.status_code == 404


# ── Service layer: sources ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_source_invalid_signal_quality():
    from backend.services.investment.research_cases import create_source, ResearchSourceCreate
    from fastapi import HTTPException
    rc = _make_rc()
    db = _simple_db(first_return=rc)
    with pytest.raises(HTTPException) as exc_info:
        await create_source(db, rc.id, ResearchSourceCreate(source_name="X", signal_quality="bad_value"))
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_create_source_case_not_found():
    from backend.services.investment.research_cases import create_source, ResearchSourceCreate
    from fastapi import HTTPException
    db = _simple_db(first_return=None)
    with pytest.raises(HTTPException) as exc_info:
        await create_source(db, uuid.uuid4(), ResearchSourceCreate(source_name="X", signal_quality="high"))
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_source_success():
    from backend.services.investment.research_cases import create_source, ResearchSourceCreate
    rc = _make_rc()
    db = _simple_db(first_return=rc)
    await create_source(db, rc.id, ResearchSourceCreate(source_name="Reuters", signal_quality="medium"))
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_list_sources_case_not_found():
    from backend.services.investment.research_cases import list_sources
    from fastapi import HTTPException
    db = _simple_db(first_return=None)
    with pytest.raises(HTTPException) as exc_info:
        await list_sources(db, uuid.uuid4())
    assert exc_info.value.status_code == 404


# ── API endpoint tests ────────────────────────────────────────────────────────

def test_get_tasks_endpoint_case_not_found():
    rc_id = str(uuid.uuid4())
    db = _simple_db(first_return=None)
    _override_db(db)
    try:
        resp = client.get(f"/api/investment/research-cases/{rc_id}/tasks")
        assert resp.status_code == 404
    finally:
        _clear_db_override()


def test_get_tasks_endpoint_returns_list():
    rc = _make_rc()
    task = _make_task(rc_id=rc.id)
    call_count = [0]

    async def execute_side(query):
        result = MagicMock()
        if call_count[0] == 0:
            result.scalars.return_value.first.return_value = rc
        else:
            result.scalars.return_value.all.return_value = [task]
        call_count[0] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=execute_side)
    _override_db(db)
    try:
        resp = client.get(f"/api/investment/research-cases/{rc.id}/tasks")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
    finally:
        _clear_db_override()


def test_add_task_endpoint_201():
    rc = _make_rc()
    task = _make_task(rc_id=rc.id)
    call_count = [0]

    async def execute_side(query):
        result = MagicMock()
        result.scalars.return_value.first.return_value = rc
        call_count[0] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=execute_side)
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()

    async def refresh_side(obj):
        if hasattr(obj, 'description') and not hasattr(obj, 'situation_id'):
            obj.id = task.id
            obj.research_case_id = task.research_case_id
            obj.description = task.description
            obj.status = task.status
            obj.priority = task.priority
            obj.source = task.source
            obj.notes = task.notes
            obj.created_at = task.created_at
            obj.resolved_at = task.resolved_at

    db.refresh = AsyncMock(side_effect=refresh_side)
    _override_db(db)
    try:
        resp = client.post(
            f"/api/investment/research-cases/{rc.id}/tasks",
            json={"description": "Investigate merger terms", "priority": 1},
        )
        assert resp.status_code == 201
    finally:
        _clear_db_override()


def test_patch_task_endpoint_not_found():
    task_id = str(uuid.uuid4())
    db = _simple_db(first_return=None)
    _override_db(db)
    try:
        resp = client.patch(f"/api/investment/research-tasks/{task_id}", json={"status": "done"})
        assert resp.status_code == 404
    finally:
        _clear_db_override()


def test_patch_task_endpoint_invalid_status():
    task = _make_task()
    db = _simple_db(first_return=task)
    _override_db(db)
    try:
        resp = client.patch(f"/api/investment/research-tasks/{task.id}", json={"status": "flying"})
        assert resp.status_code == 400
    finally:
        _clear_db_override()


def test_add_document_endpoint_201():
    rc = _make_rc()
    doc = _make_doc(rc_id=rc.id)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(**{
        'scalars.return_value.first.return_value': rc
    }))
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()

    async def refresh_side(obj):
        if isinstance(obj, ResearchDocument):
            obj.id = doc.id
            obj.research_case_id = doc.research_case_id
            obj.historical_case_id = doc.historical_case_id
            obj.doc_type = doc.doc_type
            obj.url = doc.url
            obj.title = doc.title
            obj.retrieved_at = doc.retrieved_at
            obj.summary = doc.summary
            obj.added_by = doc.added_by
            obj.created_at = doc.created_at

    db.refresh = AsyncMock(side_effect=refresh_side)
    _override_db(db)
    try:
        resp = client.post(
            f"/api/investment/research-cases/{rc.id}/documents",
            json={"url": "https://sec.gov/filing.pdf", "title": "10-K"},
        )
        assert resp.status_code == 201
    finally:
        _clear_db_override()


def test_add_document_endpoint_case_not_found():
    rc_id = str(uuid.uuid4())
    db = _simple_db(first_return=None)
    _override_db(db)
    try:
        resp = client.post(
            f"/api/investment/research-cases/{rc_id}/documents",
            json={"url": "https://example.com"},
        )
        assert resp.status_code == 404
    finally:
        _clear_db_override()


def test_get_documents_endpoint_returns_list():
    rc = _make_rc()
    doc = _make_doc(rc_id=rc.id)
    call_count = [0]

    async def execute_side(query):
        result = MagicMock()
        if call_count[0] == 0:
            result.scalars.return_value.first.return_value = rc
        else:
            result.scalars.return_value.all.return_value = [doc]
        call_count[0] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=execute_side)
    _override_db(db)
    try:
        resp = client.get(f"/api/investment/research-cases/{rc.id}/documents")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
    finally:
        _clear_db_override()


def test_add_source_endpoint_invalid_signal_quality():
    rc = _make_rc()
    db = _simple_db(first_return=rc)
    _override_db(db)
    try:
        resp = client.post(
            f"/api/investment/research-cases/{rc.id}/sources",
            json={"source_name": "Test", "signal_quality": "invalid"},
        )
        assert resp.status_code == 400
    finally:
        _clear_db_override()


def test_add_source_endpoint_201():
    rc = _make_rc()
    src = _make_source(rc_id=rc.id)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(**{
        'scalars.return_value.first.return_value': rc
    }))
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()

    async def refresh_side(obj):
        if isinstance(obj, ResearchSource):
            obj.id = src.id
            obj.research_case_id = src.research_case_id
            obj.historical_case_id = src.historical_case_id
            obj.investment_source_id = src.investment_source_id
            obj.source_name = src.source_name
            obj.source_url = src.source_url
            obj.signal_quality = src.signal_quality
            obj.notes = src.notes
            obj.created_at = src.created_at

    db.refresh = AsyncMock(side_effect=refresh_side)
    _override_db(db)
    try:
        resp = client.post(
            f"/api/investment/research-cases/{rc.id}/sources",
            json={"source_name": "Bloomberg", "signal_quality": "high"},
        )
        assert resp.status_code == 201
    finally:
        _clear_db_override()


def test_add_source_endpoint_case_not_found():
    rc_id = str(uuid.uuid4())
    db = _simple_db(first_return=None)
    _override_db(db)
    try:
        resp = client.post(
            f"/api/investment/research-cases/{rc_id}/sources",
            json={"source_name": "X", "signal_quality": "low"},
        )
        assert resp.status_code == 404
    finally:
        _clear_db_override()


def test_get_sources_endpoint_returns_list():
    rc = _make_rc()
    src = _make_source(rc_id=rc.id)
    call_count = [0]

    async def execute_side(query):
        result = MagicMock()
        if call_count[0] == 0:
            result.scalars.return_value.first.return_value = rc
        else:
            result.scalars.return_value.all.return_value = [src]
        call_count[0] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=execute_side)
    _override_db(db)
    try:
        resp = client.get(f"/api/investment/research-cases/{rc.id}/sources")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
    finally:
        _clear_db_override()
