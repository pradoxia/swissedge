import inspect
import json
import uuid
from datetime import datetime, timezone

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase, ResearchDocument, ResearchSource
from backend.services.investment.evidence_links import (
    build_research_case_evidence_links,
    build_situation_evidence_links,
)
from backend.services.investment.methodology_workspace import WORKSPACE_KEY


SEC_URL = "https://www.sec.gov/Archives/edgar/data/1829280/000114036126019536/filing.htm"


def _workspace(candidate_status: str = "candidate_found") -> dict:
    return {
        "template_key": "merger_arbitrage",
        "required_resources": [
            {"resource_id": "ma_sc_to_t", "title": "SC TO-T filing", "status": "evidence_found"},
            {"resource_id": "ma_offer_purchase", "title": "Offer to Purchase", "status": "missing"},
        ],
        "checklist": [
            {"check_id": "ma_offer_terms", "title": "Verify offer terms", "status": "evidence_found"},
            {"check_id": "ma_financing", "title": "Verify financing", "status": "needs_evidence"},
        ],
        "resource_candidates": [
            {
                "resource_candidate_id": "candidate-1",
                "title": "SC TO-T filing",
                "url": SEC_URL,
                "source_type": "sec_filing",
                "status": candidate_status,
                "related_resource_ids": ["ma_sc_to_t"],
                "related_check_ids": ["ma_offer_terms"],
                "notes": "Stored from detection metadata.",
            },
            {
                "resource_candidate_id": "candidate-2",
                "title": "Rejected source",
                "url": "https://example.com/rejected",
                "source_type": "press_release",
                "status": "rejected",
                "related_resource_ids": ["ma_offer_purchase"],
                "related_check_ids": ["ma_financing"],
            },
        ],
        "search_suggestions": [
            {
                "suggestion_id": "suggestion-1",
                "query": "\"Forian Inc.\" offer to purchase",
                "suggestion_type": "offer_document",
                "status": "suggested",
                "discovered_by": "resource_scout_v1",
                "created_at": "2026-05-11T00:00:00+00:00",
            }
        ],
    }


def _situation(candidate_status: str = "candidate_found") -> SpecialSituation:
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type="merger_arbitrage",
        company_name="Forian Inc.",
        ticker="FORA",
        filing_type="SC TO-T",
        filing_url=SEC_URL,
        detected_at=datetime(2026, 5, 8, tzinfo=timezone.utc),
        status="detected",
        source_urls=[SEC_URL],
        evaluation={
            "source": "sec_edgar",
            "detected_only": True,
            "sec_detection": {
                "accession_number": "0001140361-26-019536",
                "cik": "0001829280",
                "filing_url": SEC_URL,
                "filing_date": "2026-05-08",
                "detected_form_type": "SC TO-T",
            },
            WORKSPACE_KEY: _workspace(candidate_status),
        },
    )


def _research_case() -> ResearchCase:
    workspace = _workspace("evidence_found")
    rc = ResearchCase(
        id=uuid.uuid4(),
        situation_id=uuid.uuid4(),
        status="under_investigation",
        intake_method="special_situation_promotion",
        source_origin_name="SpecialSituation",
        official_source_status="official_attached",
        disclaimer="Este análisis es educativo. No es asesoramiento financiero.",
        brief={
            "title": "Forian Inc. - SC TO-T",
            "source": "special_situation_promotion",
            "detection_summary": {
                "company_name": "Forian Inc.",
                "filing_type": "SC TO-T",
                "filing_url": SEC_URL,
                "accession_number": "0001140361-26-019536",
                "filing_date": "2026-05-08",
            },
            "methodology_workspace_snapshot": workspace,
        },
    )
    rc.sources = [
        ResearchSource(
            source_name="SEC EDGAR",
            source_url=SEC_URL,
            signal_quality="high",
            notes="Metadata only.",
        )
    ]
    rc.documents = [
        ResearchDocument(
            url="https://example.com/press-release",
            title="Company press release",
            doc_type="press_release",
        )
    ]
    return rc


def test_situation_sec_filing_url_produces_source_link():
    package = build_situation_evidence_links(_situation())

    sec_links = [link for link in package.links if link.origin == "sec_detection"]

    assert sec_links
    assert sec_links[0].url == SEC_URL
    assert sec_links[0].source_type == "sec_filing"
    assert sec_links[0].metadata_only is True
    assert sec_links[0].verified is False


def test_resource_candidate_url_appears_with_candidate_status():
    package = build_situation_evidence_links(_situation("candidate_found"))

    candidate = next(link for link in package.links if link.origin == "resource_candidate" and link.url == SEC_URL)

    assert candidate.status == "candidate_found"
    assert candidate.linked_required_resource_ids == ["ma_sc_to_t"]
    assert candidate.linked_checklist_item_ids == ["ma_offer_terms"]


def test_evidence_found_candidate_links_required_resource_and_checklist_ids():
    package = build_situation_evidence_links(_situation("evidence_found"))

    candidate = next(link for link in package.links if link.origin == "resource_candidate" and link.url == SEC_URL)
    resource_row = next(row for row in package.required_resource_links if row["resource_id"] == "ma_sc_to_t")
    checklist_row = next(row for row in package.checklist_links if row["check_id"] == "ma_offer_terms")

    assert candidate.status == "evidence_found"
    assert resource_row["links"]
    assert checklist_row["links"]


def test_rejected_candidate_remains_visible():
    package = build_situation_evidence_links(_situation())

    rejected = next(link for link in package.links if link.status == "rejected")

    assert rejected.url == "https://example.com/rejected"
    assert rejected.verified is False


def test_research_case_promoted_snapshot_sources_and_documents_are_traceable():
    package = build_research_case_evidence_links(_research_case())

    assert any(link.origin == "brief_snapshot" and link.url == SEC_URL for link in package.snapshot_links)
    assert any(link.origin == "research_case_source" and link.url == SEC_URL for link in package.source_links)
    assert any(link.origin == "research_case_document" and link.url == "https://example.com/press-release" for link in package.document_links)
    assert all(link.metadata_only for link in package.links)


def test_duplicate_url_is_grouped_by_origin_safely():
    package = build_research_case_evidence_links(_research_case())

    by_origin = {(link.url, link.origin) for link in package.links}

    assert (SEC_URL, "brief_snapshot") in by_origin
    assert (SEC_URL, "research_case_source") in by_origin
    assert len([link for link in package.snapshot_links if link.url == SEC_URL and link.origin == "brief_snapshot"]) == 1


def test_evidence_links_output_has_no_buy_sell_hold_language():
    payload = build_research_case_evidence_links(_research_case()).model_dump()
    text = json.dumps(payload).lower()

    assert "buy" not in text
    assert "sell" not in text
    assert "hold" not in text
    assert "recommendation" in text


def test_evidence_links_service_does_not_import_network_clients():
    import backend.services.investment.evidence_links as evidence_links

    source = inspect.getsource(evidence_links)

    assert "httpx" not in source
    assert "requests" not in source
    assert "urllib.request" not in source
