"""Phase 2D/2E tests: AI quality-preview endpoint with mocked AI client."""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import get_db as _real_get_db
from backend.models.investment_research import ResearchCase, ResearchTask, ResearchDocument, ResearchSource
from backend.models.investment import SpecialSituation

client = TestClient(app)

DISCLAIMER = "Este análisis es educativo. No es asesoramiento financiero."
_FAKE_USAGE = {"provider": "anthropic", "model": "claude-haiku-4-5-20251001", "input_tokens": 80, "output_tokens": 150}

_FAKE_QUALITY_JSON = """{
  "quality_checklist": {
    "brief_completeness": false,
    "missing_information_noted": true,
    "key_risks_identified": true,
    "documents_attached": true,
    "tasks_open": true,
    "sources_recorded": true,
    "disclaimer_present": true,
    "no_buy_sell_language": true,
    "readiness_label_valid": true
  },
  "suggested_status": "under_investigation",
  "suggested_readiness": "needs_more_work",
  "rationale": "Case has open tasks and incomplete brief. Further investigation needed."
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
    s.situation_type = "activist"
    s.evaluation = {"summary": "Activist disclosed.", "risk_flags": ["hostile bid risk"]}
    return s


def _make_db(rc, situation=None):
    db = AsyncMock()

    async def execute_side_effect(query):
        mock_result = MagicMock()
        scalars = MagicMock()
        if "ResearchCase" in str(type(query)) or "research_cases" in str(query).lower():
            scalars.first.return_value = rc
        elif "SpecialSituation" in str(type(query)) or "special_situations" in str(query).lower():
            scalars.first.return_value = situation
        else:
            scalars.first.return_value = None
        mock_result.scalars.return_value = scalars
        return mock_result

    db.execute = AsyncMock(side_effect=execute_side_effect)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


class TestQualityPreviewService:
    """Unit tests for generate_quality_preview service function."""

    @pytest.mark.asyncio
    async def test_returns_saved_to_db_false(self):
        from backend.services.investment.research_cases import generate_quality_preview

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_QUALITY_JSON, _FAKE_USAGE))):
            result = await generate_quality_preview(db, rc.id)

        assert result["saved_to_db"] is False

    @pytest.mark.asyncio
    async def test_no_db_write(self):
        from backend.services.investment.research_cases import generate_quality_preview

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_QUALITY_JSON, _FAKE_USAGE))):
            await generate_quality_preview(db, rc.id)

        db.add.assert_not_called()
        db.flush.assert_not_called()
        db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_suggested_status(self):
        from backend.services.investment.research_cases import generate_quality_preview, VALID_STATUSES

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_QUALITY_JSON, _FAKE_USAGE))):
            result = await generate_quality_preview(db, rc.id)

        assert result["suggested_status"] in VALID_STATUSES

    @pytest.mark.asyncio
    async def test_valid_suggested_readiness(self):
        from backend.services.investment.research_cases import generate_quality_preview, VALID_READINESS

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_QUALITY_JSON, _FAKE_USAGE))):
            result = await generate_quality_preview(db, rc.id)

        assert result["suggested_readiness"] in VALID_READINESS

    @pytest.mark.asyncio
    async def test_checklist_has_all_keys(self):
        from backend.services.investment.research_cases import generate_quality_preview, _QUALITY_CHECKLIST_KEYS

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_QUALITY_JSON, _FAKE_USAGE))):
            result = await generate_quality_preview(db, rc.id)

        for key in _QUALITY_CHECKLIST_KEYS:
            assert key in result["quality_checklist"]
            assert isinstance(result["quality_checklist"][key], bool)

    @pytest.mark.asyncio
    async def test_disclaimer_always_present(self):
        from backend.services.investment.research_cases import generate_quality_preview

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_QUALITY_JSON, _FAKE_USAGE))):
            result = await generate_quality_preview(db, rc.id)

        assert result["disclaimer"] == DISCLAIMER

    @pytest.mark.asyncio
    async def test_malformed_json_returns_defaults(self):
        from backend.services.investment.research_cases import generate_quality_preview, VALID_STATUSES, VALID_READINESS

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=("not json at all", _FAKE_USAGE))):
            result = await generate_quality_preview(db, rc.id)

        assert result["saved_to_db"] is False
        assert result["suggested_status"] in VALID_STATUSES
        assert result["suggested_readiness"] in VALID_READINESS
        assert any("JSON parse error" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_invalid_status_in_response_defaults(self):
        from backend.services.investment.research_cases import generate_quality_preview

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        bad_json = '{"quality_checklist": {}, "suggested_status": "buy_now", "suggested_readiness": "candidate", "rationale": "test"}'

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(bad_json, _FAKE_USAGE))):
            result = await generate_quality_preview(db, rc.id)

        assert result["suggested_status"] == "detected"
        assert any("suggested_status" in w and "invalid" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_invalid_readiness_in_response_defaults(self):
        from backend.services.investment.research_cases import generate_quality_preview

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        bad_json = '{"quality_checklist": {}, "suggested_status": "detected", "suggested_readiness": "strong_buy", "rationale": "test"}'

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(bad_json, _FAKE_USAGE))):
            result = await generate_quality_preview(db, rc.id)

        assert result["suggested_readiness"] == "needs_more_work"
        assert any("suggested_readiness" in w and "invalid" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_404_when_case_not_found(self):
        from backend.services.investment.research_cases import generate_quality_preview
        from fastapi import HTTPException

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await generate_quality_preview(db, uuid.uuid4())
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_works_without_linked_situation(self):
        from backend.services.investment.research_cases import generate_quality_preview

        rc = _make_rc()
        rc.situation_id = None
        db = _make_db(rc, situation=None)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_QUALITY_JSON, _FAKE_USAGE))):
            result = await generate_quality_preview(db, rc.id)

        assert result["saved_to_db"] is False

    @pytest.mark.asyncio
    async def test_published_status_downgraded_to_documented_when_brief_complete(self):
        from backend.services.investment.research_cases import generate_quality_preview

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        published_json = (
            '{"quality_checklist": {"brief_completeness": true, "missing_information_noted": true,'
            ' "key_risks_identified": true, "documents_attached": true, "tasks_open": false,'
            ' "sources_recorded": true, "disclaimer_present": true, "no_buy_sell_language": true,'
            ' "readiness_label_valid": true},'
            ' "suggested_status": "published", "suggested_readiness": "candidate", "rationale": "all done"}'
        )

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(published_json, _FAKE_USAGE))):
            result = await generate_quality_preview(db, rc.id)

        assert result["suggested_status"] == "documented"
        assert any(
            "published status cannot be suggested by AI" in w and "manual editorial approval" in w
            for w in result["warnings"]
        )
        assert any("Downgraded to 'documented'" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_published_status_downgraded_to_under_investigation_when_brief_incomplete(self):
        from backend.services.investment.research_cases import generate_quality_preview

        rc = _make_rc()
        sit = _make_situation(rc.situation_id)
        db = _make_db(rc, sit)

        published_json = (
            '{"quality_checklist": {"brief_completeness": false, "missing_information_noted": false,'
            ' "key_risks_identified": false, "documents_attached": false, "tasks_open": true,'
            ' "sources_recorded": false, "disclaimer_present": true, "no_buy_sell_language": true,'
            ' "readiness_label_valid": true},'
            ' "suggested_status": "published", "suggested_readiness": "needs_more_work", "rationale": "not ready"}'
        )

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(published_json, _FAKE_USAGE))):
            result = await generate_quality_preview(db, rc.id)

        assert result["suggested_status"] == "under_investigation"
        assert any(
            "published status cannot be suggested by AI" in w and "manual editorial approval" in w
            for w in result["warnings"]
        )
        assert any("Downgraded to 'under_investigation'" in w for w in result["warnings"])


class TestQualityPreviewEndpoint:
    """Integration tests for POST /api/investment/research-cases/{id}/quality-preview."""

    def _override_db(self, rc, situation=None):
        db = _make_db(rc, situation)

        async def get_db_override():
            yield db

        app.dependency_overrides[_real_get_db] = get_db_override
        return db

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_endpoint_returns_quality_preview(self):
        rc_id = uuid.uuid4()
        sit_id = uuid.uuid4()
        rc = _make_rc(rc_id, sit_id)
        sit = _make_situation(sit_id)
        self._override_db(rc, sit)

        with patch("backend.services.investment.research_cases.complete_with_usage",
                   new=AsyncMock(return_value=(_FAKE_QUALITY_JSON, _FAKE_USAGE))):
            with patch("backend.services.observability.run_logger.start_run", new=AsyncMock(return_value=uuid.uuid4())):
                with patch("backend.services.observability.run_logger.finish_run", new=AsyncMock()):
                    with patch("backend.services.observability.run_logger.log_ai_usage", new=AsyncMock()):
                        response = client.post(f"/api/investment/research-cases/{rc_id}/quality-preview")

        assert response.status_code == 200
        data = response.json()
        assert data["saved_to_db"] is False
        assert "quality_checklist" in data
        assert "suggested_status" in data
        assert "suggested_readiness" in data
        assert "rationale" in data
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
                response = client.post(f"/api/investment/research-cases/{bad_id}/quality-preview")

        assert response.status_code == 404
