"""Phase 3A/3B/3C tests: document/source PATCH and document analysis preview."""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_db as _real_get_db
from backend.models.investment_research import ResearchCase, ResearchDocument, ResearchSource

client = TestClient(app)

DISCLAIMER = "Este análisis es educativo. No es asesoramiento financiero."
_FAKE_USAGE = {"provider": "anthropic", "model": "claude-haiku-4-5-20251001", "input_tokens": 60, "output_tokens": 120}

_FAKE_ANALYSIS_JSON = """{
  "summary": "The snippet describes a 13D filing by an activist investor.",
  "key_points": ["Activist holds 8.5% stake", "Board change demanded"],
  "risks": ["Hostile response from management", "Regulatory review possible"],
  "timeline_items": ["Filing date: 2026-03-15"],
  "missing_information": "Board composition not provided.",
  "suggested_research_tasks": ["Review proxy filings", "Identify other activists"],
  "source_usefulness": "High relevance — primary SEC disclosure."
}"""

_LONG_SNIPPET = "A" * 100


def _now():
    return datetime.now(timezone.utc)


def _make_doc(doc_id=None, rc_id=None, summary=None):
    doc_id = doc_id or uuid.uuid4()
    doc = MagicMock(spec=ResearchDocument)
    doc.id = doc_id
    doc.research_case_id = rc_id or uuid.uuid4()
    doc.title = "Form 13D — Activist Disclosure"
    doc.url = "https://sec.gov/example"
    doc.doc_type = "sec_filing"
    doc.summary = summary
    doc.added_by = "analyst"
    doc.created_at = _now()
    return doc


def _make_rc(rc_id=None):
    rc_id = rc_id or uuid.uuid4()
    rc = MagicMock(spec=ResearchCase)
    rc.id = rc_id
    rc.status = "under_investigation"
    rc.investment_readiness = "needs_more_work"
    rc.notes = "Activist case — needs further research."
    rc.situation_id = uuid.uuid4()
    rc.created_at = _now()
    rc.updated_at = _now()
    return rc


def _make_db_for_doc(doc, rc=None):
    db = AsyncMock()

    async def execute_side_effect(query):
        mock_result = MagicMock()
        scalars = MagicMock()
        q_str = str(query).lower()
        if "researchdocument" in str(type(query)) or "research_document" in q_str or "researchdocument" in q_str:
            scalars.first.return_value = doc
        elif "researchcase" in str(type(query)) or "research_case" in q_str or "researchcase" in q_str:
            scalars.first.return_value = rc
        else:
            scalars.first.return_value = doc
        mock_result.scalars.return_value = scalars
        return mock_result

    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    return db


class TestPatchDocument:
    """Unit tests for patch_document service function."""

    @pytest.mark.asyncio
    async def test_updates_doc_type(self):
        from backend.services.investment.research_cases import patch_document, ResearchDocumentUpdate

        doc = _make_doc()
        db = _make_db_for_doc(doc)

        result = await patch_document(db, doc.id, ResearchDocumentUpdate(doc_type="press_release"))
        assert doc.doc_type == "press_release"

    @pytest.mark.asyncio
    async def test_updates_summary(self):
        from backend.services.investment.research_cases import patch_document, ResearchDocumentUpdate

        doc = _make_doc()
        db = _make_db_for_doc(doc)

        result = await patch_document(db, doc.id, ResearchDocumentUpdate(summary="New snippet text."))
        assert doc.summary == "New snippet text."

    @pytest.mark.asyncio
    async def test_updates_title(self):
        from backend.services.investment.research_cases import patch_document, ResearchDocumentUpdate

        doc = _make_doc()
        db = _make_db_for_doc(doc)

        await patch_document(db, doc.id, ResearchDocumentUpdate(title="New Title"))
        assert doc.title == "New Title"

    @pytest.mark.asyncio
    async def test_404_when_doc_not_found(self):
        from backend.services.investment.research_cases import patch_document, ResearchDocumentUpdate
        from fastapi import HTTPException

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await patch_document(db, uuid.uuid4(), ResearchDocumentUpdate(doc_type="news"))
        assert exc_info.value.status_code == 404


class TestPatchSource:
    """Unit tests for patch_source service function."""

    @pytest.mark.asyncio
    async def test_updates_signal_quality(self):
        from backend.services.investment.research_cases import patch_source, ResearchSourceUpdate

        src = MagicMock(spec=ResearchSource)
        src.id = uuid.uuid4()
        src.signal_quality = "low"
        src.notes = None
        src.created_at = _now()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = src
        db.execute = AsyncMock(return_value=mock_result)
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        await patch_source(db, src.id, ResearchSourceUpdate(signal_quality="high"))
        assert src.signal_quality == "high"

    @pytest.mark.asyncio
    async def test_rejects_invalid_signal_quality(self):
        from backend.services.investment.research_cases import patch_source, ResearchSourceUpdate
        from fastapi import HTTPException

        src = MagicMock(spec=ResearchSource)
        src.id = uuid.uuid4()
        src.signal_quality = "low"
        src.notes = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = src
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await patch_source(db, src.id, ResearchSourceUpdate(signal_quality="excellent"))
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_updates_notes(self):
        from backend.services.investment.research_cases import patch_source, ResearchSourceUpdate

        src = MagicMock(spec=ResearchSource)
        src.id = uuid.uuid4()
        src.signal_quality = "medium"
        src.notes = None
        src.created_at = _now()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = src
        db.execute = AsyncMock(return_value=mock_result)
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        await patch_source(db, src.id, ResearchSourceUpdate(notes="Sector: tech; Jurisdiction: US"))
        assert src.notes == "Sector: tech; Jurisdiction: US"

    @pytest.mark.asyncio
    async def test_404_when_source_not_found(self):
        from backend.services.investment.research_cases import patch_source, ResearchSourceUpdate
        from fastapi import HTTPException

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await patch_source(db, uuid.uuid4(), ResearchSourceUpdate(signal_quality="high"))
        assert exc_info.value.status_code == 404


class TestDocumentAnalysisPreviewService:
    """Unit tests for generate_document_analysis_preview service function."""

    @pytest.mark.asyncio
    async def test_returns_saved_to_db_false(self):
        from backend.services.investment.research_cases import generate_document_analysis_preview

        doc = _make_doc(summary=_LONG_SNIPPET)
        rc = _make_rc(doc.research_case_id)
        db = _make_db_for_doc(doc, rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_ANALYSIS_JSON, _FAKE_USAGE))):
            result = await generate_document_analysis_preview(db, doc.id)

        assert result["saved_to_db"] is False

    @pytest.mark.asyncio
    async def test_no_db_write(self):
        from backend.services.investment.research_cases import generate_document_analysis_preview

        doc = _make_doc(summary=_LONG_SNIPPET)
        rc = _make_rc(doc.research_case_id)
        db = _make_db_for_doc(doc, rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_ANALYSIS_JSON, _FAKE_USAGE))):
            await generate_document_analysis_preview(db, doc.id)

        db.add.assert_not_called()
        db.flush.assert_not_called()
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_disclaimer_always_present(self):
        from backend.services.investment.research_cases import generate_document_analysis_preview

        doc = _make_doc(summary=_LONG_SNIPPET)
        rc = _make_rc(doc.research_case_id)
        db = _make_db_for_doc(doc, rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_ANALYSIS_JSON, _FAKE_USAGE))):
            result = await generate_document_analysis_preview(db, doc.id)

        assert result["disclaimer"] == DISCLAIMER

    @pytest.mark.asyncio
    async def test_empty_snippet_skips_ai_and_warns(self):
        from backend.services.investment.research_cases import generate_document_analysis_preview

        doc = _make_doc(summary="short")
        rc = _make_rc(doc.research_case_id)
        db = _make_db_for_doc(doc, rc)

        mock_ai = AsyncMock()
        with patch("backend.services.investment.research_cases.complete_with_usage", new=mock_ai):
            result = await generate_document_analysis_preview(db, doc.id)

        mock_ai.assert_not_called()
        assert result["saved_to_db"] is False
        assert len(result["warnings"]) > 0
        assert any("too short" in w.lower() or "snippet" in w.lower() for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_none_snippet_skips_ai_and_warns(self):
        from backend.services.investment.research_cases import generate_document_analysis_preview

        doc = _make_doc(summary=None)
        rc = _make_rc(doc.research_case_id)
        db = _make_db_for_doc(doc, rc)

        mock_ai = AsyncMock()
        with patch("backend.services.investment.research_cases.complete_with_usage", new=mock_ai):
            result = await generate_document_analysis_preview(db, doc.id)

        mock_ai.assert_not_called()
        assert result["saved_to_db"] is False

    @pytest.mark.asyncio
    async def test_malformed_json_returns_defaults(self):
        from backend.services.investment.research_cases import generate_document_analysis_preview

        doc = _make_doc(summary=_LONG_SNIPPET)
        rc = _make_rc(doc.research_case_id)
        db = _make_db_for_doc(doc, rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=("not json at all", _FAKE_USAGE))):
            result = await generate_document_analysis_preview(db, doc.id)

        assert result["saved_to_db"] is False
        assert isinstance(result["analysis"]["key_points"], list)
        assert any("JSON parse error" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_404_when_doc_not_found(self):
        from backend.services.investment.research_cases import generate_document_analysis_preview
        from fastapi import HTTPException

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await generate_document_analysis_preview(db, uuid.uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_analysis_has_required_keys(self):
        from backend.services.investment.research_cases import generate_document_analysis_preview, _ANALYSIS_KEYS

        doc = _make_doc(summary=_LONG_SNIPPET)
        rc = _make_rc(doc.research_case_id)
        db = _make_db_for_doc(doc, rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_ANALYSIS_JSON, _FAKE_USAGE))):
            result = await generate_document_analysis_preview(db, doc.id)

        for key in _ANALYSIS_KEYS:
            assert key in result["analysis"]


class TestDocumentAnalysisPreviewEndpoint:
    """Integration tests for POST /api/investment/research-documents/{id}/analysis-preview."""

    def _override_db(self, doc, rc=None):
        db = _make_db_for_doc(doc, rc)

        async def get_db_override():
            yield db

        app.dependency_overrides[_real_get_db] = get_db_override
        return db

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_endpoint_returns_analysis_preview(self):
        doc_id = uuid.uuid4()
        rc_id = uuid.uuid4()
        doc = _make_doc(doc_id, rc_id, summary=_LONG_SNIPPET)
        rc = _make_rc(rc_id)
        self._override_db(doc, rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_ANALYSIS_JSON, _FAKE_USAGE))):
            with patch("backend.services.observability.run_logger.start_run", new=AsyncMock(return_value=uuid.uuid4())):
                with patch("backend.services.observability.run_logger.finish_run", new=AsyncMock()):
                    with patch("backend.services.observability.run_logger.log_ai_usage", new=AsyncMock()):
                        response = client.post(f"/api/investment/research-documents/{doc_id}/analysis-preview")

        assert response.status_code == 200
        data = response.json()
        assert data["saved_to_db"] is False
        assert "analysis" in data
        assert "disclaimer" in data
        assert data["disclaimer"] == DISCLAIMER

    def test_endpoint_returns_warning_for_empty_snippet(self):
        doc_id = uuid.uuid4()
        rc_id = uuid.uuid4()
        doc = _make_doc(doc_id, rc_id, summary=None)
        rc = _make_rc(rc_id)
        self._override_db(doc, rc)

        with patch("backend.services.observability.run_logger.start_run", new=AsyncMock(return_value=uuid.uuid4())):
            with patch("backend.services.observability.run_logger.finish_run", new=AsyncMock()):
                response = client.post(f"/api/investment/research-documents/{doc_id}/analysis-preview")

        assert response.status_code == 200
        data = response.json()
        assert data["saved_to_db"] is False
        assert len(data["warnings"]) > 0

    def test_endpoint_404_unknown_document(self):
        bad_id = uuid.uuid4()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        async def get_db_override():
            yield db

        app.dependency_overrides[_real_get_db] = get_db_override

        with patch("backend.services.observability.run_logger.start_run", new=AsyncMock(return_value=uuid.uuid4())):
            with patch("backend.services.observability.run_logger.fail_run", new=AsyncMock()):
                response = client.post(f"/api/investment/research-documents/{bad_id}/analysis-preview")

        assert response.status_code == 404
