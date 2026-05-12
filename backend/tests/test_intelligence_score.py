import inspect
import json
import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.models.investment_research import ResearchCase, ResearchDocument, ResearchSource, ResearchTask
from backend.services.investment.intelligence_score import build_intelligence_score_package


SEC_URL = "https://www.sec.gov/Archives/edgar/data/1829280/000114036126019536/filing.htm"


def _resource(resource_id: str, status: str) -> dict:
    return {
        "resource_id": resource_id,
        "title": resource_id.replace("_", " ").title(),
        "status": status,
        "required_or_optional": "required",
        "source_type": "sec_filing",
    }


def _check(check_id: str, status: str, human_review_required: bool = True) -> dict:
    return {
        "check_id": check_id,
        "title": check_id.replace("_", " ").title(),
        "status": status,
        "section": "Source verification",
        "human_review_required": human_review_required,
    }


def _brief(resources=None, checklist=None, fill_sections: bool = True) -> dict:
    brief = {
        "title": "Forian Inc. - SC TO-T",
        "source": "special_situation_promotion",
        "detection_summary": {
            "company_name": "Forian Inc.",
            "filing_type": "SC TO-T",
            "filing_url": SEC_URL,
            "accession_number": "0001140361-26-019536",
            "filing_date": "2026-05-08",
        },
        "methodology_workspace_snapshot": {
            "required_resources": resources if resources is not None else [],
            "checklist": checklist if checklist is not None else [],
            "progress": {},
        },
    }
    if fill_sections:
        for section in [
            "executive_summary",
            "situation_type",
            "why_interesting",
            "methodology_reference",
            "company_context",
            "board_management",
            "key_documents",
            "timeline",
            "risk_analysis",
            "verify_before_investing",
            "missing_information",
            "source_intelligence",
            "investment_readiness_note",
            "public_summary_draft",
        ]:
            brief[section] = "Prepared for manual review."
    return brief


def _case(*, complete: bool = True) -> ResearchCase:
    resources = [
        _resource("sec_filing", "evidence_found" if complete else "missing"),
        _resource("offer_doc", "evidence_found" if complete else "missing"),
    ]
    checklist = [
        _check("offer_terms", "evidence_found" if complete else "needs_evidence"),
        _check("financing", "evidence_found" if complete else "needs_evidence"),
    ]
    rc = ResearchCase(
        id=uuid.uuid4(),
        situation_id=uuid.uuid4() if complete else None,
        status="under_investigation",
        investment_readiness="needs_more_work",
        intake_method="special_situation_promotion" if complete else None,
        evidence_level="official_primary" if complete else None,
        official_source_status="official_attached" if complete else None,
        disclaimer="Este análisis es educativo. No es asesoramiento financiero.",
        brief=_brief(resources, checklist, fill_sections=complete),
    )
    rc.tasks = [ResearchTask(description="Manual review required.", status="open", priority=2)] if complete else []
    rc.sources = [
        ResearchSource(source_name="SEC EDGAR", source_url=SEC_URL, signal_quality="high")
    ] if complete else []
    rc.documents = [
        ResearchDocument(url=SEC_URL, title="SEC filing", doc_type="sec_filing")
    ] if complete else []
    return rc


def test_complete_research_case_scores_approvable_for_manual_review_only():
    package = build_intelligence_score_package(_case(complete=True))

    assert package.total_score == 100
    assert package.grade == "APPROVABLE"
    assert "manual review" in package.grade_explanation
    assert "not investment approval" in package.grade_explanation
    assert [component.max_score for component in package.components] == [40, 40, 20]
    assert package.evaluation_prep_summary["level"] == "ready_for_manual_evaluation"
    assert package.evidence_links_summary["sec_links"] >= 1


def test_incomplete_case_is_review_pipeline_with_actionable_gaps():
    package = build_intelligence_score_package(_case(complete=False))

    assert package.total_score < 70
    assert package.grade == "REVIEW_PIPELINE"
    assert any("Official source metadata" in warning for warning in package.warnings)
    assert "Collect missing required resources" in package.suggested_next_actions


def test_candidate_resources_receive_partial_structuring_credit():
    rc = _case(complete=True)
    rc.brief["methodology_workspace_snapshot"]["required_resources"] = [
        _resource("sec_filing", "candidate_found"),
        _resource("offer_doc", "candidate_found"),
    ]

    package = build_intelligence_score_package(rc)

    structuring = next(component for component in package.components if component.key == "structuring")
    assert structuring.score < 40
    assert any("partial credit" in signal for signal in structuring.signals)


def test_bare_research_case_is_review_pipeline_with_manual_review_guardrail():
    rc = ResearchCase(
        id=uuid.uuid4(),
        brief=None,
        disclaimer="Este análisis es educativo. No es asesoramiento financiero.",
    )
    rc.tasks = []
    rc.sources = []
    rc.documents = []

    package = build_intelligence_score_package(rc)

    assert package.grade == "REVIEW_PIPELINE"
    assert package.total_score < 70
    assert "Manual review remains mandatory." in package.guardrails


def test_score_detects_directive_investment_language_as_risk_gap():
    rc = _case(complete=True)
    rc.notes = "This case says buy now, which must not appear in preparation metadata."

    package = build_intelligence_score_package(rc)

    risk = next(component for component in package.components if component.key == "risk_discipline")
    assert risk.score < risk.max_score
    assert any("Directive investment language" in gap for gap in risk.gaps)


def test_intelligence_score_output_has_no_buy_sell_hold_recommendation_language():
    payload = build_intelligence_score_package(_case(complete=True)).model_dump()
    text = json.dumps(payload).lower()

    assert "buy" not in text
    assert "sell" not in text
    assert "hold" not in text
    assert "recommendation" in text


def test_intelligence_score_service_does_not_import_network_clients():
    import backend.services.investment.intelligence_score as intelligence_score

    source = inspect.getsource(intelligence_score)

    assert "httpx" not in source
    assert "requests" not in source
    assert "urllib.request" not in source
    assert "aiohttp" not in source
    assert "subprocess" not in source


def test_intelligence_score_endpoint_is_read_only_get_package():
    client = TestClient(app)
    rc = _case(complete=True)

    with patch(
        "backend.api.investment.research_cases.get_research_case",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = rc
        response = client.get(f"/api/investment/research-cases/{rc.id}/intelligence-score")

    assert response.status_code == 200
    data = response.json()
    assert data["research_case_id"] == str(rc.id)
    assert data["total_score"] == 100
    assert data["grade"] == "APPROVABLE"
