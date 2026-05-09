"""Phase 4A+4B+4C tests: source intelligence approval queue, historical cases, historical case source intelligence preview."""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_db as _real_get_db
from backend.models.investment_research import ResearchCase, HistoricalCase
from backend.models.source_intelligence import SourceIntelligenceSuggestion

client = TestClient(app)

_DISCLAIMER = "Este análisis es educativo. No es asesoramiento financiero."
_FAKE_USAGE = {"provider": "anthropic", "model": "claude-haiku-4-5-20251001", "input_tokens": 80, "output_tokens": 200}

_FAKE_HIST_INTEL_JSON = """{
  "source_scores": [],
  "suggestions": [
    {
      "action": "add",
      "source_name": "SEC EDGAR 13D Filings",
      "source_type": "regulatory",
      "reason": "Primary source for activist disclosure in this situation type.",
      "evidence_from_case": "Seed notes mention activist involvement.",
      "confidence": "high",
      "manual_review_required": true
    }
  ],
  "warnings": []
}"""


def _now():
    return datetime.now(timezone.utc)


def _make_rc(rc_id=None):
    rc_id = rc_id or uuid.uuid4()
    rc = MagicMock(spec=ResearchCase)
    rc.id = rc_id
    rc.status = "under_investigation"
    rc.investment_readiness = "needs_more_work"
    rc.notes = "Test case."
    rc.situation_id = None
    rc.brief = {}
    rc.created_at = _now()
    rc.updated_at = _now()
    rc.sources = []
    rc.documents = []
    rc.tasks = []
    return rc


def _make_hc(hc_id=None):
    hc_id = hc_id or uuid.uuid4()
    hc = MagicMock(spec=HistoricalCase)
    hc.id = hc_id
    hc.company_name = "Acme Corp"
    hc.situation_type = "spinoff"
    hc.event_date_approx = "2015-Q2"
    hc.seed_notes = "Historical spinoff case. Analyst notes from course chapter 4."
    hc.course_chapter_ref = 4
    hc.reconstruction = None
    hc.status = "seed"
    hc.linked_situation_id = None
    hc.disclaimer = _DISCLAIMER
    hc.created_at = _now()
    hc.updated_at = _now()
    return hc


def _make_suggestion(sid=None, rc_id=None, hc_id=None, status="proposed"):
    sid = sid or uuid.uuid4()
    s = MagicMock(spec=SourceIntelligenceSuggestion)
    s.id = sid
    s.research_case_id = rc_id
    s.historical_case_id = hc_id
    s.action = "add"
    s.proposed_name = "SEC EDGAR 13D Filings"
    s.proposed_source_type = "regulatory"
    s.rationale = "Primary source for activist disclosure."
    s.status = status
    s.created_at = _now()
    s.reviewed_at = None
    return s


def _make_db_generic(first_return=None, all_return=None):
    db = AsyncMock()

    async def execute_side_effect(query):
        mock_result = MagicMock()
        scalars = MagicMock()
        scalars.first.return_value = first_return
        scalars.all.return_value = all_return or []
        mock_result.scalars.return_value = scalars
        return mock_result

    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    return db


def _override_db(db):
    async def get_db_override():
        yield db
    app.dependency_overrides[_real_get_db] = get_db_override
    return db


def _teardown():
    app.dependency_overrides.clear()


# ── Pre-check: model and table imports ───────────────────────────────────────

class TestPreCheck:
    def test_source_intelligence_suggestion_model_importable(self):
        from backend.models.source_intelligence import SourceIntelligenceSuggestion
        assert SourceIntelligenceSuggestion.__tablename__ == "source_intelligence_suggestions"

    def test_historical_case_model_importable(self):
        from backend.models.investment_research import HistoricalCase
        assert HistoricalCase.__tablename__ == "historical_cases"

    def test_source_intelligence_suggestion_has_research_case_id(self):
        from backend.models.source_intelligence import SourceIntelligenceSuggestion
        assert hasattr(SourceIntelligenceSuggestion, "research_case_id")

    def test_source_intelligence_suggestion_has_historical_case_id(self):
        from backend.models.source_intelligence import SourceIntelligenceSuggestion
        assert hasattr(SourceIntelligenceSuggestion, "historical_case_id")

    def test_source_intelligence_suggestion_has_status(self):
        from backend.models.source_intelligence import SourceIntelligenceSuggestion
        assert hasattr(SourceIntelligenceSuggestion, "status")

    def test_source_intelligence_suggestion_has_reviewed_at(self):
        from backend.models.source_intelligence import SourceIntelligenceSuggestion
        assert hasattr(SourceIntelligenceSuggestion, "reviewed_at")

    def test_no_migration_needed(self):
        """Both tables exist in c3d4e5f6a7b8 migration — no new migration required."""
        import importlib
        migration = importlib.import_module(
            "backend.db.migrations.versions.c3d4e5f6a7b8_add_investment_research_tables"
        )
        import inspect
        source = inspect.getsource(migration.upgrade)
        assert "source_intelligence_suggestions" in source
        assert "historical_cases" in source


# ── Phase 4A — Source Intelligence Approval Queue (service layer) ─────────────

class TestSaveSuggestionsService:
    @pytest.mark.asyncio
    async def test_save_creates_proposed_suggestions(self):
        from backend.services.investment.research_cases import save_source_intelligence_suggestions

        rc_id = uuid.uuid4()
        rc = _make_rc(rc_id)
        db = _make_db_generic(first_return=rc)

        suggestions = [{"action": "add", "source_name": "SEC EDGAR", "reason": "Primary source."}]
        result = await save_source_intelligence_suggestions(db, rc_id, suggestions)

        db.add.assert_called()
        db.flush.assert_called()

    @pytest.mark.asyncio
    async def test_save_404_when_case_not_found(self):
        from backend.services.investment.research_cases import save_source_intelligence_suggestions
        from fastapi import HTTPException

        db = _make_db_generic(first_return=None)
        with pytest.raises(HTTPException) as exc:
            await save_source_intelligence_suggestions(db, uuid.uuid4(), [{"action": "add", "source_name": "X", "reason": "Y"}])
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_save_422_when_no_suggestions(self):
        from backend.services.investment.research_cases import save_source_intelligence_suggestions
        from fastapi import HTTPException

        rc = _make_rc()
        db = _make_db_generic(first_return=rc)
        with pytest.raises(HTTPException) as exc:
            await save_source_intelligence_suggestions(db, rc.id, [])
        assert exc.value.status_code == 422


class TestReviewSuggestionService:
    @pytest.mark.asyncio
    async def test_approve_proposed_suggestion(self):
        from backend.services.investment.research_cases import review_source_intelligence_suggestion

        suggestion = _make_suggestion(status="proposed")
        db = _make_db_generic(first_return=suggestion)

        result = await review_source_intelligence_suggestion(db, suggestion.id, "approved")
        assert suggestion.status == "approved"
        assert suggestion.reviewed_at is not None

    @pytest.mark.asyncio
    async def test_reject_proposed_suggestion(self):
        from backend.services.investment.research_cases import review_source_intelligence_suggestion

        suggestion = _make_suggestion(status="proposed")
        db = _make_db_generic(first_return=suggestion)

        await review_source_intelligence_suggestion(db, suggestion.id, "rejected")
        assert suggestion.status == "rejected"

    @pytest.mark.asyncio
    async def test_reject_already_approved_returns_409(self):
        from backend.services.investment.research_cases import review_source_intelligence_suggestion
        from fastapi import HTTPException

        suggestion = _make_suggestion(status="approved")
        db = _make_db_generic(first_return=suggestion)

        with pytest.raises(HTTPException) as exc:
            await review_source_intelligence_suggestion(db, suggestion.id, "rejected")
        assert exc.value.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_status_returns_422(self):
        from backend.services.investment.research_cases import review_source_intelligence_suggestion
        from fastapi import HTTPException

        suggestion = _make_suggestion(status="proposed")
        db = _make_db_generic(first_return=suggestion)

        with pytest.raises(HTTPException) as exc:
            await review_source_intelligence_suggestion(db, suggestion.id, "applied")
        assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_404_when_suggestion_not_found(self):
        from backend.services.investment.research_cases import review_source_intelligence_suggestion
        from fastapi import HTTPException

        db = _make_db_generic(first_return=None)
        with pytest.raises(HTTPException) as exc:
            await review_source_intelligence_suggestion(db, uuid.uuid4(), "approved")
        assert exc.value.status_code == 404


# ── Phase 4A — No investment_sources write guardrail ─────────────────────────

class TestNoInvestmentSourcesWrite:
    def test_no_apply_endpoint_exists(self):
        """Confirm there is no /apply endpoint on suggestions."""
        routes = [r.path for r in app.routes]
        apply_routes = [r for r in routes if "apply" in r.lower() and "suggestion" in r.lower()]
        assert len(apply_routes) == 0, f"Unexpected apply routes found: {apply_routes}"

    def test_investment_sources_not_written_on_save(self):
        """Save suggestions service never touches investment_sources table (adds SourceIntelligenceSuggestion rows only)."""
        from backend.models.source_intelligence import SourceIntelligenceSuggestion
        from backend.models.investment import InvestmentSource

        rc_id = uuid.uuid4()
        rc = _make_rc(rc_id)
        added_types = []

        async def run():
            from backend.services.investment.research_cases import save_source_intelligence_suggestions
            db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalars.return_value.first.return_value = rc
            db.execute = AsyncMock(return_value=mock_result)
            db.add = MagicMock(side_effect=lambda obj: added_types.append(type(obj).__name__))
            db.flush = AsyncMock()
            db.refresh = AsyncMock()

            suggestions = [{"action": "add", "source_name": "Test", "reason": "Test reason."}]
            await save_source_intelligence_suggestions(db, rc_id, suggestions)

        import asyncio
        asyncio.get_event_loop().run_until_complete(run())
        assert all("InvestmentSource" not in t for t in added_types), f"Unexpected InvestmentSource write: {added_types}"


# ── Phase 4B — Historical Cases service layer ─────────────────────────────────

class TestHistoricalCaseService:
    @pytest.mark.asyncio
    async def test_create_historical_case(self):
        from backend.services.investment.research_cases import create_historical_case, HistoricalCaseCreate

        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        payload = HistoricalCaseCreate(
            company_name="Acme Corp",
            situation_type="spinoff",
            event_date_approx="2015-Q2",
            seed_notes="Test notes.",
        )
        hc = await create_historical_case(db, payload)
        db.add.assert_called_once()
        db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_historical_case_404(self):
        from backend.services.investment.research_cases import get_historical_case
        from fastapi import HTTPException

        db = _make_db_generic(first_return=None)
        with pytest.raises(HTTPException) as exc:
            await get_historical_case(db, uuid.uuid4())
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_historical_case_invalid_status(self):
        from backend.services.investment.research_cases import update_historical_case, HistoricalCaseUpdate
        from fastapi import HTTPException

        hc = _make_hc()
        db = _make_db_generic(first_return=hc)
        payload = HistoricalCaseUpdate(status="invalid_status")

        with pytest.raises(HTTPException) as exc:
            await update_historical_case(db, hc.id, payload)
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_historical_case_valid_status(self):
        from backend.services.investment.research_cases import update_historical_case, HistoricalCaseUpdate

        hc = _make_hc()
        db = _make_db_generic(first_return=hc)
        payload = HistoricalCaseUpdate(status="reconstructed")

        await update_historical_case(db, hc.id, payload)
        assert hc.status == "reconstructed"


# ── Phase 4B — Historical Cases endpoint integration ─────────────────────────

class TestHistoricalCaseEndpoints:
    def teardown_method(self):
        _teardown()

    def test_create_historical_case_endpoint(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        db.commit = AsyncMock()
        db.execute = AsyncMock()
        _override_db(db)

        hc = _make_hc()

        async def refresh_side_effect(obj):
            obj.id = hc.id
            obj.company_name = "Acme Corp"
            obj.situation_type = "spinoff"
            obj.event_date_approx = "2015-Q2"
            obj.seed_notes = "Test notes."
            obj.course_chapter_ref = None
            obj.reconstruction = None
            obj.status = "seed"
            obj.linked_situation_id = None
            obj.disclaimer = _DISCLAIMER
            obj.created_at = _now()
            obj.updated_at = _now()

        db.refresh = AsyncMock(side_effect=refresh_side_effect)

        response = client.post(
            "/api/investment/historical-cases",
            json={"company_name": "Acme Corp", "situation_type": "spinoff", "event_date_approx": "2015-Q2", "seed_notes": "Test notes."},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == "Acme Corp"
        assert data["status"] == "seed"
        assert data["disclaimer"] == _DISCLAIMER

    def test_list_historical_cases_endpoint(self):
        hc = _make_hc()
        db = _make_db_generic(first_return=hc, all_return=[hc])
        _override_db(db)

        response = client.get("/api/investment/historical-cases")
        assert response.status_code == 200

    def test_get_historical_case_404(self):
        db = _make_db_generic(first_return=None)
        _override_db(db)

        response = client.get(f"/api/investment/historical-cases/{uuid.uuid4()}")
        assert response.status_code == 404


# ── Phase 4C — Historical Case Source Intelligence Preview ────────────────────

class TestHistoricalCaseSourceIntelligencePreview:
    @pytest.mark.asyncio
    async def test_returns_saved_to_db_false(self):
        from backend.services.investment.research_cases import generate_historical_case_source_intelligence_preview

        hc = _make_hc()
        db = _make_db_generic(first_return=hc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_HIST_INTEL_JSON, _FAKE_USAGE))):
            result = await generate_historical_case_source_intelligence_preview(db, hc.id)

        assert result["saved_to_db"] is False

    @pytest.mark.asyncio
    async def test_no_db_write(self):
        from backend.services.investment.research_cases import generate_historical_case_source_intelligence_preview

        hc = _make_hc()
        db = _make_db_generic(first_return=hc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_HIST_INTEL_JSON, _FAKE_USAGE))):
            await generate_historical_case_source_intelligence_preview(db, hc.id)

        db.add.assert_not_called()
        db.flush.assert_not_called()
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_disclaimer_always_present(self):
        from backend.services.investment.research_cases import generate_historical_case_source_intelligence_preview

        hc = _make_hc()
        db = _make_db_generic(first_return=hc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_HIST_INTEL_JSON, _FAKE_USAGE))):
            result = await generate_historical_case_source_intelligence_preview(db, hc.id)

        assert result["disclaimer"] == _DISCLAIMER

    @pytest.mark.asyncio
    async def test_empty_notes_skips_ai(self):
        from backend.services.investment.research_cases import generate_historical_case_source_intelligence_preview

        hc = _make_hc()
        hc.seed_notes = None
        hc.reconstruction = None
        db = _make_db_generic(first_return=hc)

        mock_ai = AsyncMock()
        with patch("backend.services.investment.research_cases.complete_with_usage", new=mock_ai):
            result = await generate_historical_case_source_intelligence_preview(db, hc.id)

        mock_ai.assert_not_called()
        assert result["saved_to_db"] is False
        assert len(result["warnings"]) > 0

    @pytest.mark.asyncio
    async def test_suggestions_have_manual_review_required(self):
        from backend.services.investment.research_cases import generate_historical_case_source_intelligence_preview

        hc = _make_hc()
        db = _make_db_generic(first_return=hc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_HIST_INTEL_JSON, _FAKE_USAGE))):
            result = await generate_historical_case_source_intelligence_preview(db, hc.id)

        for sug in result["suggestions"]:
            assert sug["manual_review_required"] is True

    @pytest.mark.asyncio
    async def test_404_when_not_found(self):
        from backend.services.investment.research_cases import generate_historical_case_source_intelligence_preview
        from fastapi import HTTPException

        db = _make_db_generic(first_return=None)
        with pytest.raises(HTTPException) as exc:
            await generate_historical_case_source_intelligence_preview(db, uuid.uuid4())
        assert exc.value.status_code == 404

    def test_endpoint_returns_saved_to_db_false(self):
        hc_id = uuid.uuid4()
        hc = _make_hc(hc_id)
        db = _make_db_generic(first_return=hc)
        _override_db(db)

        try:
            with patch("backend.services.investment.research_cases.complete_with_usage",
                       new=AsyncMock(return_value=(_FAKE_HIST_INTEL_JSON, _FAKE_USAGE))):
                with patch("backend.services.observability.run_logger.start_run", new=AsyncMock(return_value=uuid.uuid4())):
                    with patch("backend.services.observability.run_logger.finish_run", new=AsyncMock()):
                        with patch("backend.services.observability.run_logger.log_ai_usage", new=AsyncMock()):
                            response = client.post(f"/api/investment/historical-cases/{hc_id}/source-intelligence-preview")

            assert response.status_code == 200
            data = response.json()
            assert data["saved_to_db"] is False
            assert "suggestions" in data
            assert data["disclaimer"] == _DISCLAIMER
        finally:
            _teardown()
