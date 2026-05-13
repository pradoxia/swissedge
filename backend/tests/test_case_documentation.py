import inspect
import json
import uuid
from datetime import datetime, timezone

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase, ResearchDocument, ResearchSource, ResearchTask
from backend.services.investment.case_documentation import (
    build_research_case_documentation_guide,
    build_situation_documentation_guide,
)
from backend.services.investment.evidence_links import (
    build_research_case_evidence_links,
    build_situation_evidence_links,
)
from backend.services.investment.intelligence_score import build_intelligence_score_package
from backend.services.investment.methodology_workspace import WORKSPACE_KEY
from backend.services.investment.research_cases import build_evaluation_prep_package


SEC_URL = "https://www.sec.gov/Archives/edgar/data/1829280/000114036126019536/filing.htm"


def _workspace(*, filing_url: str | None = SEC_URL) -> dict:
    return {
        "template_key": "merger_arbitrage",
        "workflow_status": "needs_resources",
        "required_resources": [
            {
                "resource_id": "sec_filing",
                "title": "SEC filing",
                "status": "evidence_found" if filing_url else "missing",
                "required_or_optional": "required",
            },
            {
                "resource_id": "offer_document",
                "title": "Offer document",
                "status": "missing",
                "required_or_optional": "required",
            },
        ],
        "checklist": [
            {
                "check_id": "offer_terms",
                "title": "Verify offer terms",
                "status": "evidence_found",
                "human_review_required": True,
            },
            {
                "check_id": "financing",
                "title": "Verify financing",
                "status": "needs_evidence",
                "human_review_required": True,
            },
        ],
        "resource_candidates": [
            {
                "resource_candidate_id": "candidate-1",
                "title": "SEC filing candidate",
                "url": filing_url or "https://example.com/sec-search",
                "source_type": "sec_filing",
                "status": "candidate_found",
                "related_resource_ids": ["sec_filing"],
                "related_check_ids": ["offer_terms"],
                "discovered_at": "2026-05-11T00:00:00+00:00",
            },
            {
                "resource_candidate_id": "candidate-2",
                "title": "Rejected item",
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


def _situation(*, filing_url: str | None = SEC_URL) -> SpecialSituation:
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type="merger_arbitrage",
        company_name="Forian Inc.",
        ticker="FORA",
        filing_type="SC TO-T" if filing_url else None,
        filing_url=filing_url,
        detected_at=datetime(2026, 5, 8, tzinfo=timezone.utc),
        status="detected",
        source_urls=[filing_url] if filing_url else [],
        evaluation={
            "source": "sec_edgar",
            "sec_detection": {
                "accession_number": "0001140361-26-019536",
                "cik": "0001829280",
                "filing_url": filing_url,
                "filing_date": "2026-05-08",
                "detected_form_type": "SC TO-T",
                "selected_playbook": "merger_arbitrage",
                "detection_confidence": "high",
            },
            WORKSPACE_KEY: _workspace(filing_url=filing_url),
        },
    )


def _research_case(situation: SpecialSituation) -> ResearchCase:
    rc = ResearchCase(
        id=uuid.uuid4(),
        situation_id=situation.id,
        status="under_investigation",
        intake_method="special_situation_promotion",
        source_origin_name="SpecialSituation",
        official_source_status="official_attached",
        disclaimer="Este análisis es educativo. No es asesoramiento financiero.",
        brief={
            "title": "Forian Inc. - SC TO-T",
            "source": "special_situation_promotion",
            "detection_summary": {
                "company_name": situation.company_name,
                "ticker": situation.ticker,
                "filing_type": situation.filing_type,
                "filing_url": situation.filing_url,
                "accession_number": "0001140361-26-019536",
                "cik": "0001829280",
                "filing_date": "2026-05-08",
                "detected_at": situation.detected_at.isoformat(),
                "selected_playbook": "merger_arbitrage",
            },
            "methodology_workspace_snapshot": _workspace(),
        },
    )
    rc.sources = [
        ResearchSource(source_name="SEC EDGAR", source_url=SEC_URL, signal_quality="high")
    ]
    rc.documents = [
        ResearchDocument(url="https://example.com/offer-document", title="Offer document", doc_type="offer_document")
    ]
    rc.tasks = [
        ResearchTask(description="Verify offer terms", status="open", priority=2)
    ]
    return rc


def test_situation_documentation_guide_includes_detection_and_missing_items():
    situation = _situation()
    evidence = build_situation_evidence_links(situation)

    guide = build_situation_documentation_guide(situation, evidence)

    assert guide.case_type == "special_situation"
    assert guide.detection_guide.source == "SEC EDGAR"
    assert guide.detection_guide.accession_number == "0001140361-26-019536"
    assert guide.detection_guide.filing_url == SEC_URL
    assert guide.missing_evidence.missing_required_resources[0]["title"] == "Offer document"
    assert guide.search_plan.copyable_queries
    assert guide.research_agent.agent_name == "Missing Evidence Hunter"


def test_search_suggestions_are_copyable_queries():
    guide = build_situation_documentation_guide(_situation(), build_situation_evidence_links(_situation()))

    assert "\"Forian Inc.\" offer document" in guide.search_plan.copyable_queries
    assert guide.search_plan.manual_search_steps[0].startswith("Copy a stored query")


def test_research_case_documentation_guide_connects_original_context():
    situation = _situation()
    rc = _research_case(situation)
    evidence = build_research_case_evidence_links(rc)
    prep = build_evaluation_prep_package(rc)
    score = build_intelligence_score_package(rc)

    guide = build_research_case_documentation_guide(
        rc,
        evidence_links=evidence,
        evaluation_prep=prep,
        intelligence_score=score,
        source_situation=situation,
    )

    assert guide.case_type == "research_case"
    assert guide.detection_guide.source == "SpecialSituation promotion"
    assert guide.detection_guide.filing_url == SEC_URL
    assert any(event.label == "Evaluation Preparation available" for event in guide.activity_timeline)
    assert any(event.label == "Intelligence Score available" for event in guide.activity_timeline)


def test_documentation_quality_is_lower_without_filing_url():
    low = build_situation_documentation_guide(
        _situation(filing_url=None),
        build_situation_evidence_links(_situation(filing_url=None)),
    )
    high = build_situation_documentation_guide(_situation(), build_situation_evidence_links(_situation()))

    assert low.documentation_quality.score < high.documentation_quality.score
    assert low.documentation_quality.level in {"needs_required_resources", "needs_evidence_mapping", "needs_links"}


def test_documentation_output_has_no_buy_sell_hold_or_recommendation_language():
    situation = _situation()
    guide = build_situation_documentation_guide(situation, build_situation_evidence_links(situation))
    text = json.dumps(guide.model_dump()).lower()

    assert "buy" not in text
    assert "sell" not in text
    assert "hold" not in text
    assert "recommendation" not in text


def test_case_documentation_service_does_not_import_network_clients():
    import backend.services.investment.case_documentation as case_documentation

    source = inspect.getsource(case_documentation)

    assert "httpx" not in source
    assert "requests" not in source
    assert "urllib.request" not in source
