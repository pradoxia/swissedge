"""Phase 2A tests: AI brief preview endpoint with mocked AI client."""
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_db as _real_get_db
from backend.models.investment_research import ResearchCase, ResearchTask, ResearchDocument, ResearchSource
from backend.models.investment import SpecialSituation

client = TestClient(app)

DISCLAIMER = "Este análisis es educativo. No es asesoramiento financiero."

_FAKE_USAGE = {"provider": "anthropic", "model": "claude-haiku-4-5-20251001", "input_tokens": 100, "output_tokens": 200}

_FAKE_BRIEF_JSON = """{
  "executive_summary": "Test executive summary.",
  "situation_type": "Merger arbitrage.",
  "why_interesting": "Spread exists.",
  "methodology_reference": "Chapter 3.",
  "company_context": "Mid-cap company.",
  "board_management": "Experienced board.",
  "key_documents": "10-K filed.",
  "timeline": "Q1 2026.",
  "risk_analysis": "Regulatory risk.",
  "verify_before_investing": "Check antitrust filing.",
  "missing_information": "No proxy yet.",
  "source_intelligence": "SEC EDGAR signal.",
  "investment_readiness_note": "Monitor for now.",
  "public_summary_draft": "Company announced merger."
}"""


def _now():
    return datetime.now(timezone.utc)


def _make_rc(rc_id=None, situation_id=None):
    rc_id = rc_id or uuid.uuid4()
    now = _now()
    rc = MagicMock(spec=ResearchCase)
    rc.id = rc_id
    rc.situation_id = situation_id or uuid.uuid4()
    rc.status = "detected"
    rc.brief = None
    rc.brief_version = None
    rc.playbook_version = None
    rc.model_used = None
    rc.run_id = None
    rc.notes = "Some analyst notes."
    rc.disclaimer = DISCLAIMER
    rc.investment_readiness = "monitor"
    rc.created_at = now
    rc.updated_at = now
    rc.tasks = []
    rc.documents = []
    rc.sources = []
    return rc


def _make_situation(sit_id=None):
    sit_id = sit_id or uuid.uuid4()
    s = MagicMock(spec=SpecialSituation)
    s.id = sit_id
    s.company_name = "Acme Corp"
    s.ticker = "ACME"
    s.filing_type = "SC 13G"
    s.situation_type = "activist"
    s.filing_url = "https://example.com/filing.htm"
    s.detected_at = _now()
    s.evaluation = {"summary": "Activist investor disclosed.", "risk_flags": ["hostile bid risk"]}
    return s


def _make_db(rc, situation=None):
    db = AsyncMock()

    async def execute_side_effect(query):
        mock_result = MagicMock()
        scalars = MagicMock()
        if "research_cases" in str(query).lower() or "ResearchCase" in str(type(query)):
            scalars.first.return_value = rc
        elif "special_situations" in str(query).lower() or "SpecialSituation" in str(type(query)):
            scalars.first.return_value = situation
        else:
            scalars.first.return_value = None
        mock_result.scalars.return_value = scalars
        return mock_result

    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


class TestBriefPreviewService:
    """Unit tests for generate_brief_preview service function."""

    @pytest.mark.asyncio
    async def test_generates_preview_with_all_sections(self):
        from backend.services.investment.research_cases import generate_brief_preview

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_BRIEF_JSON, _FAKE_USAGE))):
            result = await generate_brief_preview(db, rc.id)

        assert result["saved_to_db"] is False
        assert result["disclaimer"] == DISCLAIMER
        assert "executive_summary" in result["preview"]
        assert result["preview"]["executive_summary"] == "Test executive summary."
        assert len(result["preview"]) == 14
        assert result["warnings"] == []
        assert "linked_situation" in result["source_context_used"]
        assert "analyst_notes" in result["source_context_used"]

    @pytest.mark.asyncio
    async def test_warns_on_missing_section(self):
        from backend.services.investment.research_cases import generate_brief_preview

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        partial_json = '{"executive_summary": "Only this section."}'

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(partial_json, _FAKE_USAGE))):
            result = await generate_brief_preview(db, rc.id)

        assert result["preview"]["executive_summary"] == "Only this section."
        assert result["preview"]["situation_type"] == ""
        assert any("situation_type" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_handles_malformed_json(self):
        from backend.services.investment.research_cases import generate_brief_preview

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=("not json at all", _FAKE_USAGE))):
            result = await generate_brief_preview(db, rc.id)

        assert result["saved_to_db"] is False
        assert any("JSON parse error" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_404_when_case_not_found(self):
        from backend.services.investment.research_cases import generate_brief_preview
        from fastapi import HTTPException

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await generate_brief_preview(db, uuid.uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_works_without_linked_situation(self):
        from backend.services.investment.research_cases import generate_brief_preview

        rc = _make_rc()
        rc.situation_id = None
        db = _make_db(rc, situation=None)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_BRIEF_JSON, _FAKE_USAGE))):
            result = await generate_brief_preview(db, rc.id)

        assert result["saved_to_db"] is False
        assert "linked_situation" not in result["source_context_used"]


class TestBriefPreviewEndpoint:
    """Integration tests for POST /api/investment/research-cases/{id}/generate-brief-preview."""

    def _override_db(self, rc, situation=None):
        db = _make_db(rc, situation)

        async def get_db_override():
            yield db

        app.dependency_overrides[_real_get_db] = get_db_override
        return db

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_endpoint_returns_preview(self):
        rc_id = uuid.uuid4()
        sit_id = uuid.uuid4()
        rc = _make_rc(rc_id, sit_id)
        sit = _make_situation(sit_id)
        db = self._override_db(rc, sit)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_BRIEF_JSON, _FAKE_USAGE))):
            with patch("backend.services.observability.run_logger.start_run", new=AsyncMock(return_value=uuid.uuid4())):
                with patch("backend.services.observability.run_logger.finish_run", new=AsyncMock()):
                    with patch("backend.services.observability.run_logger.log_ai_usage", new=AsyncMock()):
                        response = client.post(f"/api/investment/research-cases/{rc_id}/generate-brief-preview")

        assert response.status_code == 200
        data = response.json()
        assert data["saved_to_db"] is False
        assert "preview" in data
        assert "executive_summary" in data["preview"]
        assert "disclaimer" in data
        assert data["disclaimer"] == DISCLAIMER

    def test_endpoint_404_unknown_case(self):
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
                response = client.post(f"/api/investment/research-cases/{bad_id}/generate-brief-preview")

        assert response.status_code == 404
