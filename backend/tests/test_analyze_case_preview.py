import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.db.database import get_db as _real_get_db
from backend.main import app
from backend.models.investment_research import ResearchCase, ResearchDocument
from backend.services import ai_client
from backend.services.investment.research_cases import (
    AnalyzeCasePreview,
    BriefDraftPreview,
    BriefSectionPreview,
    CaseClassificationPreview,
    EvidenceCoverageSummary,
    GuardrailFinding,
    QualityChecklistPreview,
)

client = TestClient(app)


def _now():
    return datetime.now(timezone.utc)


def _make_doc(*, body_text: str | None = "Acquired SEC body text. " * 20):
    doc = MagicMock(spec=ResearchDocument)
    doc.id = uuid.uuid4()
    doc.research_case_id = uuid.uuid4()
    doc.historical_case_id = None
    doc.doc_type = "sec_filing"
    doc.url = "https://www.sec.gov/Archives/example.txt"
    doc.title = "SEC filing"
    doc.summary = None
    doc.body_text = body_text
    doc.created_at = _now()
    return doc


def _mock_run_logger():
    return (
        patch("backend.api.investment.research_cases.run_logger.start_run", new=AsyncMock(return_value=uuid.uuid4())),
        patch("backend.api.investment.research_cases.run_logger.finish_run", new=AsyncMock()),
        patch("backend.api.investment.research_cases.run_logger.fail_run", new=AsyncMock()),
        patch("backend.api.investment.research_cases.run_logger.log_ai_usage", new=AsyncMock()),
    )


def _make_case(*, documents=None):
    rc = MagicMock(spec=ResearchCase)
    rc.id = uuid.uuid4()
    rc.situation_id = None
    rc.status = "under_investigation"
    rc.investment_readiness = "needs_more_work"
    rc.notes = "Manual preview test case."
    rc.tasks = []
    rc.documents = documents if documents is not None else [_make_doc()]
    rc.sources = []
    rc.created_at = _now()
    rc.updated_at = _now()
    return rc


def _make_db_for_case(rc):
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.first.return_value = rc
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _override_db(db):
    async def get_db_override():
        yield db

    app.dependency_overrides[_real_get_db] = get_db_override


def _preview(rc_id: uuid.UUID) -> AnalyzeCasePreview:
    return AnalyzeCasePreview(
        research_case_id=str(rc_id),
        status="preview_ready",
        classification_preview=CaseClassificationPreview(
            classification="tender_offer",
            rationale="Based only on supplied document text.",
            confidence="medium",
        ),
        evidence_coverage_summary=EvidenceCoverageSummary(
            documents_reviewed=1,
            documents_with_body_text=1,
            coverage_summary="One acquired document was reviewed.",
            missing_information=[],
        ),
        brief_draft_preview=BriefDraftPreview(
            sections=[
                BriefSectionPreview(
                    section_name=f"section_{i}",
                    draft_text="Neutral draft text.",
                    source_document_ids=[],
                )
                for i in range(14)
            ]
        ),
        quality_checklist_preview=QualityChecklistPreview(items=[], overall_status="needs_review"),
        guardrail_findings=[
            GuardrailFinding(guardrail="language", status="passed", notes="Neutral wording only.")
        ],
    )


def teardown_function():
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_missing_body_text_blocks_preview_and_skips_ai():
    from backend.services.investment.research_cases import generate_analyze_case_preview

    rc = _make_case(documents=[_make_doc(body_text=None)])
    db = _make_db_for_case(rc)
    ai = AsyncMock()

    with patch("backend.services.investment.research_cases.complete_structured_with_usage", new=ai):
        result = await generate_analyze_case_preview(db, rc.id)

    ai.assert_not_called()
    assert result.saved_to_db is False
    assert result.status == "blocked_missing_documents"
    assert result.missing_documents


def test_disabled_live_ai_returns_controlled_503_and_provider_not_called(monkeypatch):
    rc = _make_case()
    db = _make_db_for_case(rc)
    provider = AsyncMock()
    monkeypatch.setattr(
        ai_client,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "ai_provider": "openai",
                "ai_live_enabled": False,
                "ai_daily_budget_usd": 0.0,
                "ai_openai_model": "gpt-test",
                "ai_anthropic_model": "claude-test",
                "ai_task_model_overrides": {},
                "openai_api_key": "test",
                "anthropic_api_key": "test",
            },
        )(),
    )
    monkeypatch.setattr(ai_client, "_openai_with_usage", provider)
    _override_db(db)

    start_patch, finish_patch, fail_patch, usage_patch = _mock_run_logger()
    with start_patch as start_run:
        with finish_patch as finish_run:
            with fail_patch as fail_run:
                with usage_patch as log_ai_usage:
                    response = client.post(f"/api/investment/research-cases/{rc.id}/analyze-preview")

    assert response.status_code == 503
    assert response.json()["detail"] == "Live AI is disabled. Dani approval is required before running AI previews."
    provider.assert_not_called()
    start_run.assert_awaited_once()
    finish_run.assert_awaited_once()
    assert finish_run.await_args.kwargs["final_outcome"] == "ai_disabled"
    fail_run.assert_not_called()
    log_ai_usage.assert_not_called()
    assert db.commit.await_count == 1


def test_missing_body_text_endpoint_logs_blocked_and_skips_ai():
    rc = _make_case(documents=[_make_doc(body_text=None)])
    db = _make_db_for_case(rc)
    _override_db(db)
    ai = AsyncMock()

    start_patch, finish_patch, fail_patch, usage_patch = _mock_run_logger()
    with patch("backend.services.investment.research_cases.complete_structured_with_usage", new=ai):
        with start_patch:
            with finish_patch as finish_run:
                with fail_patch as fail_run:
                    with usage_patch as log_ai_usage:
                        response = client.post(f"/api/investment/research-cases/{rc.id}/analyze-preview")

    assert response.status_code == 200
    assert response.json()["status"] == "blocked_missing_documents"
    ai.assert_not_called()
    finish_run.assert_awaited_once()
    assert finish_run.await_args.kwargs["final_outcome"] == "blocked_missing_documents"
    fail_run.assert_not_called()
    log_ai_usage.assert_not_called()


def test_budget_cap_error_maps_to_429():
    rc = _make_case()
    db = _make_db_for_case(rc)
    _override_db(db)

    start_patch, finish_patch, fail_patch, usage_patch = _mock_run_logger()
    with patch(
        "backend.services.investment.research_cases.complete_structured_with_usage",
        new=AsyncMock(side_effect=ai_client.AIBudgetExceededError("cap")),
    ):
        with start_patch:
            with finish_patch as finish_run:
                with fail_patch as fail_run:
                    with usage_patch:
                        response = client.post(f"/api/investment/research-cases/{rc.id}/analyze-preview")

    assert response.status_code == 429
    assert response.json()["detail"] == "AI daily budget cap would be exceeded."
    assert finish_run.await_args.kwargs["final_outcome"] == "budget_exceeded"
    fail_run.assert_not_called()


def test_parse_error_maps_to_explicit_502():
    rc = _make_case()
    db = _make_db_for_case(rc)
    _override_db(db)

    start_patch, finish_patch, fail_patch, usage_patch = _mock_run_logger()
    with patch(
        "backend.services.investment.research_cases.complete_structured_with_usage",
        new=AsyncMock(side_effect=ai_client.AIResponseParseError("bad json")),
    ):
        with start_patch:
            with finish_patch as finish_run:
                with fail_patch as fail_run:
                    with usage_patch:
                        response = client.post(f"/api/investment/research-cases/{rc.id}/analyze-preview")

    assert response.status_code == 502
    assert response.json()["detail"] == "AI response was not valid JSON."
    assert finish_run.await_args.kwargs["final_outcome"] == "parse_error"
    fail_run.assert_not_called()


def test_schema_validation_error_maps_to_explicit_502():
    rc = _make_case()
    db = _make_db_for_case(rc)
    _override_db(db)

    start_patch, finish_patch, fail_patch, usage_patch = _mock_run_logger()
    with patch(
        "backend.services.investment.research_cases.complete_structured_with_usage",
        new=AsyncMock(side_effect=ai_client.AIResponseValidationError("bad schema")),
    ):
        with start_patch:
            with finish_patch as finish_run:
                with fail_patch as fail_run:
                    with usage_patch:
                        response = client.post(f"/api/investment/research-cases/{rc.id}/analyze-preview")

    assert response.status_code == 502
    assert response.json()["detail"] == "AI response did not match the required preview schema."
    assert finish_run.await_args.kwargs["final_outcome"] == "validation_error"
    fail_run.assert_not_called()


def test_successful_endpoint_logs_finish_and_usage_without_body_text():
    secret_body = "CONFIDENTIAL_BODY_TEXT_SHOULD_NOT_BE_LOGGED"
    rc = _make_case(documents=[_make_doc(body_text=secret_body)])
    db = _make_db_for_case(rc)
    _override_db(db)
    usage = {"provider": "test", "model": "model", "input_tokens": 10, "output_tokens": 20}
    ai = AsyncMock(return_value=(_preview(rc.id), usage))

    start_patch, finish_patch, fail_patch, usage_patch = _mock_run_logger()
    with patch("backend.services.investment.research_cases.complete_structured_with_usage", new=ai):
        with start_patch as start_run:
            with finish_patch as finish_run:
                with fail_patch as fail_run:
                    with usage_patch as log_ai_usage:
                        response = client.post(f"/api/investment/research-cases/{rc.id}/analyze-preview")

    assert response.status_code == 200
    assert response.json()["saved_to_db"] is False
    assert finish_run.await_args.kwargs["final_outcome"] == "success_preview_generated"
    log_ai_usage.assert_awaited_once()
    fail_run.assert_not_called()
    logged_text = json.dumps(
        {
            "start": start_run.await_args.kwargs,
            "finish": finish_run.await_args.kwargs,
        }
    )
    assert secret_body not in logged_text


@pytest.mark.asyncio
async def test_success_preview_does_not_persist_or_mutate_case():
    from backend.services.investment.research_cases import generate_analyze_case_preview

    rc = _make_case()
    original_status = rc.status
    db = _make_db_for_case(rc)
    ai = AsyncMock(return_value=(_preview(rc.id), {"provider": "test", "model": "model"}))

    with patch("backend.services.investment.research_cases.complete_structured_with_usage", new=ai):
        result = await generate_analyze_case_preview(db, rc.id)

    assert result.saved_to_db is False
    assert rc.status == original_status
    db.add.assert_not_called()
    db.flush.assert_not_called()
    db.commit.assert_not_called()


def test_analyze_preview_schema_avoids_prohibited_output_language():
    schema_text = json.dumps(AnalyzeCasePreview.model_json_schema()).lower()

    for prohibited in ("buy", "sell", "recommendation", "target_price", "investment advice"):
        assert prohibited not in schema_text
