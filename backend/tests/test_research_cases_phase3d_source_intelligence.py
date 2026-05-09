"""Phase 3D tests: source intelligence preview endpoint and service."""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_db as _real_get_db
from backend.models.investment_research import ResearchCase, ResearchSource, ResearchDocument, ResearchTask

client = TestClient(app)

DISCLAIMER = "Este análisis es educativo. No es asesoramiento financiero."
_FAKE_USAGE = {"provider": "anthropic", "model": "claude-haiku-4-5-20251001", "input_tokens": 80, "output_tokens": 200}

_FAKE_INTEL_JSON = """{
  "source_scores": [
    {
      "source_id": "PLACEHOLDER_ID",
      "source_name": "SEC EDGAR",
      "signal_quality": "high",
      "usefulness_reason": "Primary source for activist filings. Directly relevant to 13D event.",
      "suggested_follow_up": "Check for amendments filed after the initial 13D."
    }
  ],
  "suggestions": [
    {
      "action": "add",
      "source_name": "Company IR Website",
      "source_type": "ir_website",
      "reason": "Board response to activist may be published on IR page.",
      "evidence_from_case": "Open task: verify board response",
      "confidence": "high",
      "manual_review_required": true
    }
  ],
  "warnings": []
}"""


def _now():
    return datetime.now(timezone.utc)


def _make_source(src_id=None, rc_id=None):
    src_id = src_id or uuid.uuid4()
    src = MagicMock(spec=ResearchSource)
    src.id = src_id
    src.research_case_id = rc_id or uuid.uuid4()
    src.source_name = "SEC EDGAR"
    src.source_url = "https://sec.gov"
    src.signal_quality = "high"
    src.notes = "Sector: financials; Jurisdiction: US"
    src.created_at = _now()
    return src


def _make_rc(rc_id=None, with_source=True):
    rc_id = rc_id or uuid.uuid4()
    rc = MagicMock(spec=ResearchCase)
    rc.id = rc_id
    rc.status = "under_investigation"
    rc.investment_readiness = "needs_more_work"
    rc.notes = "Activist case."
    rc.situation_id = None
    rc.brief = {"executive_summary": "This is a test brief."}
    rc.created_at = _now()
    rc.updated_at = _now()
    src = _make_source(rc_id=rc_id) if with_source else None
    rc.sources = [src] if with_source else []
    rc.documents = []
    rc.tasks = []
    return rc, (src if with_source else None)


def _make_db_for_rc(rc):
    db = AsyncMock()

    async def execute_side_effect(query):
        mock_result = MagicMock()
        scalars = MagicMock()
        scalars.first.return_value = rc
        mock_result.scalars.return_value = scalars
        return mock_result

    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    return db


class TestSourceIntelligencePreviewService:
    """Unit tests for generate_source_intelligence_preview service function."""

    @pytest.mark.asyncio
    async def test_returns_saved_to_db_false(self):
        from backend.services.investment.research_cases import generate_source_intelligence_preview

        rc, src = _make_rc()
        intel_json = _FAKE_INTEL_JSON.replace("PLACEHOLDER_ID", str(src.id))
        db = _make_db_for_rc(rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(intel_json, _FAKE_USAGE))):
            result = await generate_source_intelligence_preview(db, rc.id)

        assert result["saved_to_db"] is False

    @pytest.mark.asyncio
    async def test_no_db_write(self):
        from backend.services.investment.research_cases import generate_source_intelligence_preview

        rc, src = _make_rc()
        intel_json = _FAKE_INTEL_JSON.replace("PLACEHOLDER_ID", str(src.id))
        db = _make_db_for_rc(rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(intel_json, _FAKE_USAGE))):
            await generate_source_intelligence_preview(db, rc.id)

        db.add.assert_not_called()
        db.flush.assert_not_called()
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_disclaimer_always_present(self):
        from backend.services.investment.research_cases import generate_source_intelligence_preview

        rc, src = _make_rc()
        intel_json = _FAKE_INTEL_JSON.replace("PLACEHOLDER_ID", str(src.id))
        db = _make_db_for_rc(rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(intel_json, _FAKE_USAGE))):
            result = await generate_source_intelligence_preview(db, rc.id)

        assert result["disclaimer"] == DISCLAIMER

    @pytest.mark.asyncio
    async def test_empty_sources_skips_ai_and_warns(self):
        from backend.services.investment.research_cases import generate_source_intelligence_preview

        rc, _ = _make_rc(with_source=False)
        db = _make_db_for_rc(rc)

        mock_ai = AsyncMock()
        with patch("backend.services.investment.research_cases.complete_with_usage", new=mock_ai):
            result = await generate_source_intelligence_preview(db, rc.id)

        mock_ai.assert_not_called()
        assert result["saved_to_db"] is False
        assert len(result["warnings"]) > 0
        assert any("no sources" in w.lower() or "sources recorded" in w.lower() for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_malformed_json_returns_defaults(self):
        from backend.services.investment.research_cases import generate_source_intelligence_preview

        rc, _ = _make_rc()
        db = _make_db_for_rc(rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=("not json at all", _FAKE_USAGE))):
            result = await generate_source_intelligence_preview(db, rc.id)

        assert result["saved_to_db"] is False
        assert isinstance(result["source_scores"], list)
        assert isinstance(result["suggestions"], list)
        assert any("JSON parse error" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_suggestions_always_have_manual_review_required(self):
        from backend.services.investment.research_cases import generate_source_intelligence_preview

        rc, src = _make_rc()
        intel_json = _FAKE_INTEL_JSON.replace("PLACEHOLDER_ID", str(src.id))
        db = _make_db_for_rc(rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(intel_json, _FAKE_USAGE))):
            result = await generate_source_intelligence_preview(db, rc.id)

        for suggestion in result["suggestions"]:
            assert suggestion["manual_review_required"] is True

    @pytest.mark.asyncio
    async def test_404_when_case_not_found(self):
        from backend.services.investment.research_cases import generate_source_intelligence_preview
        from fastapi import HTTPException

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await generate_source_intelligence_preview(db, uuid.uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_response_has_required_keys(self):
        from backend.services.investment.research_cases import generate_source_intelligence_preview

        rc, src = _make_rc()
        intel_json = _FAKE_INTEL_JSON.replace("PLACEHOLDER_ID", str(src.id))
        db = _make_db_for_rc(rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(intel_json, _FAKE_USAGE))):
            result = await generate_source_intelligence_preview(db, rc.id)

        for key in ("saved_to_db", "research_case_id", "source_scores", "suggestions", "warnings", "disclaimer", "usage"):
            assert key in result

    @pytest.mark.asyncio
    async def test_buy_sell_stripped_from_usefulness_reason(self):
        from backend.services.investment.research_cases import generate_source_intelligence_preview

        rc, src = _make_rc()
        dirty_json = _FAKE_INTEL_JSON.replace(
            "Directly relevant to 13D event.",
            "You should buy this stock immediately."
        ).replace("PLACEHOLDER_ID", str(src.id))
        db = _make_db_for_rc(rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(dirty_json, _FAKE_USAGE))):
            result = await generate_source_intelligence_preview(db, rc.id)

        for score in result["source_scores"]:
            assert "buy" not in score["usefulness_reason"].lower()
        assert any("buy/sell" in w.lower() or "directive" in w.lower() for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_invalid_suggestion_action_defaults_to_add(self):
        from backend.services.investment.research_cases import generate_source_intelligence_preview

        rc, src = _make_rc()
        bad_action_json = _FAKE_INTEL_JSON.replace(
            '"action": "add"', '"action": "buy_it_now"'
        ).replace("PLACEHOLDER_ID", str(src.id))
        db = _make_db_for_rc(rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(bad_action_json, _FAKE_USAGE))):
            result = await generate_source_intelligence_preview(db, rc.id)

        for suggestion in result["suggestions"]:
            assert suggestion["action"] in ("add", "update_priority", "deactivate")


class TestSourceIntelligencePreviewEndpoint:
    """Integration tests for POST /api/investment/research-cases/{id}/source-intelligence-preview."""

    def _override_db(self, rc):
        db = _make_db_for_rc(rc)

        async def get_db_override():
            yield db

        app.dependency_overrides[_real_get_db] = get_db_override
        return db

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_endpoint_returns_source_intelligence_preview(self):
        rc_id = uuid.uuid4()
        rc, src = _make_rc(rc_id)
        intel_json = _FAKE_INTEL_JSON.replace("PLACEHOLDER_ID", str(src.id))
        self._override_db(rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(intel_json, _FAKE_USAGE))):
            with patch("backend.services.observability.run_logger.start_run", new=AsyncMock(return_value=uuid.uuid4())):
                with patch("backend.services.observability.run_logger.finish_run", new=AsyncMock()):
                    with patch("backend.services.observability.run_logger.log_ai_usage", new=AsyncMock()):
                        response = client.post(f"/api/investment/research-cases/{rc_id}/source-intelligence-preview")

        assert response.status_code == 200
        data = response.json()
        assert data["saved_to_db"] is False
        assert "source_scores" in data
        assert "suggestions" in data
        assert "warnings" in data
        assert data["disclaimer"] == DISCLAIMER

    def test_endpoint_no_sources_returns_warning(self):
        rc_id = uuid.uuid4()
        rc, _ = _make_rc(rc_id, with_source=False)
        self._override_db(rc)

        with patch("backend.services.observability.run_logger.start_run", new=AsyncMock(return_value=uuid.uuid4())):
            with patch("backend.services.observability.run_logger.finish_run", new=AsyncMock()):
                response = client.post(f"/api/investment/research-cases/{rc_id}/source-intelligence-preview")

        assert response.status_code == 200
        data = response.json()
        assert data["saved_to_db"] is False
        assert len(data["warnings"]) > 0

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
                response = client.post(f"/api/investment/research-cases/{bad_id}/source-intelligence-preview")

        assert response.status_code == 404

    def test_suggestions_not_auto_applied_to_investment_sources(self):
        rc_id = uuid.uuid4()
        rc, src = _make_rc(rc_id)
        intel_json = _FAKE_INTEL_JSON.replace("PLACEHOLDER_ID", str(src.id))
        db = self._override_db(rc)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(intel_json, _FAKE_USAGE))):
            with patch("backend.services.observability.run_logger.start_run", new=AsyncMock(return_value=uuid.uuid4())):
                with patch("backend.services.observability.run_logger.finish_run", new=AsyncMock()):
                    with patch("backend.services.observability.run_logger.log_ai_usage", new=AsyncMock()):
                        response = client.post(f"/api/investment/research-cases/{rc_id}/source-intelligence-preview")

        assert response.status_code == 200
        db.add.assert_not_called()
        db.flush.assert_not_called()
