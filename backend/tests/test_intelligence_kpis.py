import inspect
import json
import os
import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

if os.environ.get("DEBUG") not in {None, "", "0", "1", "true", "false", "True", "False"}:
    os.environ["DEBUG"] = "false"

from backend.main import app
from backend.models.agent_ops import AgentActivity, AgentDiagnosticEvent, AgentProfile, AgentRoom
from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase, ResearchDocument, ResearchSource, ResearchTask
from backend.services.investment.intelligence_kpis import (
    build_fontana_diagnostic_report,
    build_intelligence_kpi_package,
)
from backend.services.investment.methodology_workspace import WORKSPACE_KEY


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


def _workspace(*, complete: bool = True) -> dict:
    return {
        "template_key": "merger_arbitrage",
        "workflow_status": "ready_for_research_case" if complete else "needs_resources",
        "required_resources": [
            _resource("sec_filing", "evidence_found" if complete else "missing"),
            _resource("offer_doc", "evidence_found" if complete else "candidate_found"),
            _resource("financing", "verified" if complete else "missing"),
        ],
        "checklist": [
            _check("offer_terms", "evidence_found" if complete else "needs_evidence"),
            _check("financing", "verified" if complete else "needs_evidence"),
        ],
        "resource_candidates": [
            {
                "resource_candidate_id": "candidate-1",
                "title": "SEC filing",
                "url": SEC_URL,
                "source_type": "sec_filing",
                "status": "evidence_found" if complete else "candidate_found",
                "related_resource_ids": ["sec_filing"],
                "related_check_ids": ["offer_terms"],
            },
            {
                "resource_candidate_id": "candidate-2",
                "title": "Rejected source",
                "url": "https://example.com/rejected",
                "source_type": "press_release",
                "status": "rejected",
            },
        ],
        "search_suggestions": [
            {
                "suggestion_id": "suggestion-1",
                "query": "\"Forian Inc.\" offer document",
                "suggestion_type": "offer_document",
                "status": "suggested",
                "created_at": "2026-05-11T00:00:00+00:00",
            }
        ],
    }


def _brief(*, complete: bool = True) -> dict:
    brief = {
        "title": "Forian Inc. - SC TO-T",
        "source": "special_situation_promotion",
        "detection_summary": {
            "company_name": "Forian Inc.",
            "filing_type": "SC TO-T",
            "filing_url": SEC_URL if complete else None,
            "accession_number": "0001140361-26-019536" if complete else None,
            "filing_date": "2026-05-08" if complete else None,
        },
        "methodology_workspace_snapshot": _workspace(complete=complete),
    }
    if complete:
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


def _situation(*, complete: bool = False, promoted: bool = False) -> SpecialSituation:
    workspace = _workspace(complete=complete)
    if promoted:
        workspace["research_case_id"] = str(uuid.uuid4())
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type="merger_arbitrage",
        company_name="Forian Inc.",
        ticker="FORA",
        filing_type="SC TO-T",
        filing_url=SEC_URL,
        status="detected",
        source_urls=[SEC_URL],
        evaluation={
            "source": "sec_edgar",
            "sec_detection": {
                "accession_number": "0001140361-26-019536",
                "cik": "0001829280",
                "filing_url": SEC_URL,
                "filing_date": "2026-05-08",
                "detected_form_type": "SC TO-T",
            },
            WORKSPACE_KEY: workspace,
        },
    )


def _case(*, complete: bool = True, grade: str = "approvable") -> ResearchCase:
    is_complete = complete and grade == "approvable"
    rc = ResearchCase(
        id=uuid.uuid4(),
        situation_id=uuid.uuid4() if complete else None,
        status="under_investigation",
        intake_method="special_situation_promotion" if complete else None,
        source_origin_name="SpecialSituation",
        evidence_level="official_primary" if is_complete else None,
        official_source_status="official_attached" if is_complete else None,
        disclaimer="Este análisis es educativo. No es asesoramiento financiero.",
        brief=_brief(complete=is_complete),
    )
    rc.tasks = [ResearchTask(description="Manual review required.", status="open", priority=2)] if not is_complete else []
    rc.sources = [ResearchSource(source_name="SEC EDGAR", source_url=SEC_URL, signal_quality="high")] if is_complete else []
    rc.documents = [ResearchDocument(url=SEC_URL, title="SEC filing", doc_type="sec_filing")] if is_complete else []
    return rc


def test_kpi_service_handles_empty_datasets():
    package = build_intelligence_kpi_package([], [])

    assert package["case_counts"]["research_cases_total"] == 0
    assert package["case_counts"]["special_situations_total"] == 0
    assert package["intelligence"]["average_score"] == 0
    assert package["documentation"]["average_documentation_quality"] == 0
    assert package["evidence"]["evidence_links_total"] == 0


def test_kpi_service_counts_research_cases_and_special_situations():
    package = build_intelligence_kpi_package([_case()], [_situation(promoted=True), _situation()])

    assert package["case_counts"]["research_cases_total"] == 1
    assert package["case_counts"]["special_situations_total"] == 2
    assert package["case_counts"]["sec_detected"] == 2
    assert package["case_counts"]["promoted_to_research_case"] == 1


def test_intelligence_grade_counts_are_correct():
    package = build_intelligence_kpi_package([_case(complete=True), _case(complete=False)], [])

    assert package["intelligence"]["approvable_count"] == 1
    assert package["intelligence"]["review_pipeline_count"] == 1
    assert package["intelligence"]["lowest_scoring_cases"][0]["score"] < 70


def test_documentation_quality_aggregation_is_safe():
    package = build_intelligence_kpi_package([_case(complete=False)], [_situation(complete=False)])

    assert 0 <= package["documentation"]["average_documentation_quality"] <= 100
    assert package["documentation"]["needs_links_count"] + package["documentation"]["needs_required_resources_count"] >= 0


def test_evidence_missing_candidate_evidence_rejected_counts_are_correct():
    package = build_intelligence_kpi_package([], [_situation(complete=False)])

    assert package["evidence"]["required_resources_total"] == 3
    assert package["evidence"]["missing_required_resources_total"] == 2
    assert package["evidence"]["candidate_found_total"] == 2
    assert package["evidence"]["evidence_found_total"] == 0
    assert package["evidence"]["rejected_total"] == 1


def test_agent_ops_indicators_are_counted_without_seeding():
    room = AgentRoom(id=uuid.uuid4(), key="radar_room", name="Radar Room")
    agent = AgentProfile(id=uuid.uuid4(), key="missing_evidence_hunter", name="Missing Evidence Hunter", room_id=room.id)
    activity = AgentActivity(id=uuid.uuid4(), title="Checked gaps", activity_type="diagnostic")
    diagnostic = AgentDiagnosticEvent(id=uuid.uuid4(), title="Missing evidence", diagnostic_type="case_gap")

    package = build_intelligence_kpi_package(
        [],
        [_situation(complete=False)],
        agent_rooms=[room],
        agent_profiles=[agent],
        agent_activities=[activity],
        agent_diagnostics=[diagnostic],
    )

    assert package["agent_ops"]["rooms_count"] == 1
    assert package["agent_ops"]["agents_count"] == 1
    assert package["agent_ops"]["activity_rows_count"] == 1
    assert package["agent_ops"]["diagnostics_count"] == 1
    assert package["agent_ops"]["missing_evidence_hunter_load"] > 0
    assert package["agent_ops"]["rooms"][0]["href"] == "/agent-ops/rooms/radar_room"


def test_fontana_report_contains_deterministic_findings():
    kpis = build_intelligence_kpi_package([_case(complete=False)], [_situation(complete=False)])
    report = build_fontana_diagnostic_report(kpis)

    assert report["title"] == "Fontana Diagnostic Report"
    assert report["mode"] == "deterministic_observer"
    assert report["system_health"]
    assert report["evidence_gaps"]
    assert "Fontana does not execute changes." in report["guardrails"]


def test_kpi_and_fontana_outputs_have_no_buy_sell_hold_or_investment_recommendation_language():
    kpis = build_intelligence_kpi_package([_case()], [_situation()])
    report = build_fontana_diagnostic_report(kpis)
    text = json.dumps({"kpis": kpis, "report": report}).lower()

    assert "buy" not in text
    assert "sell" not in text
    assert "hold" not in text
    assert "investment recommendation" not in text


def test_intelligence_kpi_service_does_not_import_network_clients():
    import backend.services.investment.intelligence_kpis as intelligence_kpis

    source = inspect.getsource(intelligence_kpis)

    assert "httpx" not in source
    assert "requests" not in source
    assert "urllib.request" not in source
    assert "aiohttp" not in source
    assert "subprocess" not in source


def test_intelligence_kpi_endpoint_is_read_only_get_package():
    client = TestClient(app)
    package = build_intelligence_kpi_package([], [])

    with patch(
        "backend.api.investment.router.collect_intelligence_kpi_package",
        new_callable=AsyncMock,
    ) as mock_collect:
        mock_collect.return_value = package
        response = client.get("/api/investment/intelligence/kpis")

    assert response.status_code == 200
    assert response.json()["case_counts"]["research_cases_total"] == 0
    mock_collect.assert_awaited_once()


def test_fontana_report_endpoint_is_read_only_get_package():
    client = TestClient(app)
    report = build_fontana_diagnostic_report(build_intelligence_kpi_package([], []))

    with patch(
        "backend.api.investment.router.collect_fontana_diagnostic_report",
        new_callable=AsyncMock,
    ) as mock_collect:
        mock_collect.return_value = report
        response = client.get("/api/investment/intelligence/fontana-report")

    assert response.status_code == 200
    assert response.json()["mode"] == "deterministic_observer"
    mock_collect.assert_awaited_once()
