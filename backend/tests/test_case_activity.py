import inspect
import json
import uuid
from datetime import datetime, timezone

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase, ResearchDocument, ResearchSource, ResearchTask
from backend.services.investment.case_activity import (
    build_research_case_activity_timeline,
    build_situation_activity_timeline,
)
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


def _workspace() -> dict:
    return {
        "template_key": "merger_arbitrage",
        "workflow_status": "needs_resources",
        "research_case_id": "3a5c6e82-3e39-4dd5-bd64-4c6ef845e4a2",
        "required_resources": [
            {
                "resource_id": "sec_filing",
                "title": "SEC filing",
                "status": "evidence_found",
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
                "status": "needs_evidence",
                "human_review_required": True,
            }
        ],
        "resource_candidates": [
            {
                "resource_candidate_id": "candidate-1",
                "title": "SEC filing candidate",
                "url": SEC_URL,
                "source_type": "sec_filing",
                "status": "evidence_found",
                "related_resource_ids": ["sec_filing"],
                "related_check_ids": ["offer_terms"],
                "discovered_at": "2026-05-11T09:00:00+00:00",
            },
            {
                "resource_candidate_id": "candidate-2",
                "title": "Rejected press item",
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
                "created_at": "2026-05-11T10:00:00+00:00",
            }
        ],
    }


def _situation() -> SpecialSituation:
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type="merger_arbitrage",
        company_name="Forian Inc.",
        ticker="FORA",
        filing_type="SC TO-T",
        filing_url=SEC_URL,
        detected_at=datetime(2026, 5, 8, 12, 0, tzinfo=timezone.utc),
        created_at=datetime(2026, 5, 8, 12, 5, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 11, 11, 0, tzinfo=timezone.utc),
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
                "selected_playbook": "merger_arbitrage",
                "detection_confidence": "high",
            },
            WORKSPACE_KEY: _workspace(),
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
        disclaimer="Educational research only.",
        created_at=datetime(2026, 5, 12, 8, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 5, 12, 9, 0, tzinfo=timezone.utc),
        brief={
            "title": "Forian Inc. - SC TO-T",
            "source": "special_situation_promotion",
            "detection_summary": {
                "company_name": situation.company_name,
                "ticker": situation.ticker,
                "filing_type": situation.filing_type,
                "filing_url": situation.filing_url,
                "detected_at": situation.detected_at.isoformat(),
                "selected_playbook": "merger_arbitrage",
            },
            "methodology_workspace_snapshot": _workspace(),
        },
    )
    rc.sources = [
        ResearchSource(
            id=uuid.uuid4(),
            source_name="SEC EDGAR",
            source_url=SEC_URL,
            signal_quality="high",
            created_at=datetime(2026, 5, 12, 8, 15, tzinfo=timezone.utc),
        )
    ]
    rc.documents = [
        ResearchDocument(
            id=uuid.uuid4(),
            url="https://example.com/offer-document",
            title="Offer document",
            doc_type="offer_document",
            created_at=datetime(2026, 5, 12, 8, 30, tzinfo=timezone.utc),
        )
    ]
    rc.tasks = [
        ResearchTask(
            id=uuid.uuid4(),
            description="Verify offer terms",
            status="open",
            priority=2,
            created_at=datetime(2026, 5, 12, 8, 45, tzinfo=timezone.utc),
        )
    ]
    return rc


def test_situation_timeline_includes_detection_candidates_and_search_suggestions():
    situation = _situation()
    evidence = build_situation_evidence_links(situation)
    guide = build_situation_documentation_guide(situation, evidence)

    timeline = build_situation_activity_timeline(
        situation,
        evidence_links=evidence,
        documentation_guide=guide,
    )

    titles = [event.title for event in timeline.events]
    assert "SEC detection created" in titles
    assert any(event.event_type == "resource_candidate" and event.status == "evidence_found" for event in timeline.events)
    assert any(event.event_type == "resource_candidate" and event.status == "rejected" for event in timeline.events)
    assert any(event.event_type == "search_suggestion" and "\"Forian Inc.\" offer document" in event.description for event in timeline.events)


def test_missing_required_resources_and_checklist_are_attention_events():
    timeline = build_situation_activity_timeline(_situation())

    assert any(
        event.event_type == "evidence_mapping"
        and "Offer document" in event.title
        and event.status == "needs_attention"
        and event.timestamp is None
        for event in timeline.events
    )
    assert any(
        event.event_type == "quality_signal"
        and "Verify offer terms" in event.title
        and event.status == "manual_review_required"
        for event in timeline.events
    )


def test_research_case_timeline_includes_linked_context_sources_tasks_and_documents():
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

    timeline = build_research_case_activity_timeline(
        rc,
        evidence_links=evidence,
        evaluation_prep=prep,
        intelligence_score=score,
        documentation_guide=guide,
        source_situation=situation,
    )

    assert any(event.title == "ResearchCase created" for event in timeline.events)
    assert any(event.title == "Linked SpecialSituation context" for event in timeline.events)
    assert any(event.event_type == "source" and "SEC EDGAR" in event.title for event in timeline.events)
    assert any(event.event_type == "document" and "Offer document" in event.title for event in timeline.events)
    assert any(event.event_type == "task" and event.status == "needs_attention" for event in timeline.events)
    assert any(event.title == "Evidence Links package available" for event in timeline.events)
    assert any(event.title == "Evaluation Preparation available" for event in timeline.events)
    assert any(event.title == "Intelligence Score available" for event in timeline.events)


def test_missing_timestamps_are_grouped_as_current_state():
    timeline = build_situation_activity_timeline(_situation())

    untimestamped = [event for event in timeline.events if event.timestamp is None]
    assert untimestamped
    assert all(event.timestamp_label == "Current state - timestamp unavailable" for event in untimestamped)
    assert timeline.events[-1].timestamp is None


def test_case_activity_output_has_no_buy_sell_hold_or_recommendation_language():
    situation = _situation()
    timeline = build_situation_activity_timeline(situation)
    text = json.dumps(timeline.model_dump()).lower()

    assert "buy" not in text
    assert "sell" not in text
    assert "hold" not in text
    assert "recommendation" not in text


def test_case_activity_service_does_not_import_network_clients():
    import backend.services.investment.case_activity as case_activity

    source = inspect.getsource(case_activity)

    assert "httpx" not in source
    assert "requests" not in source
    assert "urllib.request" not in source
