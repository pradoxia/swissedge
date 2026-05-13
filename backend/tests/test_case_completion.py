from __future__ import annotations

import inspect
import uuid

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase, ResearchSource
from backend.services.investment import case_completion as module
from backend.services.investment.case_completion import (
    build_research_case_completion_workbench,
    build_situation_completion_workbench,
)
from backend.services.investment.intelligence_score import build_intelligence_score_package
from backend.services.investment.methodology_workspace import WORKSPACE_KEY
from backend.services.investment.research_cases import build_evaluation_prep_package


def _workspace(*, complete: bool = False, promoted: bool = False) -> dict:
    missing_status = "evidence_found" if complete else "missing"
    checklist_status = "evidence_found" if complete else "needs_evidence"
    candidates = [] if complete else [
        {
            "resource_candidate_id": "candidate-1",
            "title": "Offer document candidate",
            "url": "https://example.com/offer",
            "source_type": "offer_document",
            "status": "candidate_found",
            "related_resource_ids": ["offer_document"],
        }
    ]
    return {
        "template_key": "tender_offer",
        "workflow_status": "promoted_to_research_case" if promoted else "needs_resources",
        "research_case_id": str(uuid.uuid4()) if promoted else None,
        "required_resources": [
            {"resource_id": "sec_filing", "title": "SEC filing", "status": "evidence_found"},
            {"resource_id": "offer_document", "title": "Offer document", "status": missing_status},
        ],
        "checklist": [
            {"check_id": "offer_terms", "title": "Offer terms", "status": checklist_status, "human_review_required": True},
        ],
        "resource_candidates": candidates,
        "search_suggestions": [{"suggestion_id": "q1", "query": '"Example" "Offer to Purchase"'}],
    }


def _situation(*, complete: bool = False, promoted: bool = False) -> SpecialSituation:
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type="tender_offer",
        company_name="Example Corp",
        ticker="EXM",
        filing_type="SC TO-I",
        filing_url="https://www.sec.gov/example",
        status="detected",
        evaluation={
            "sec_detection": {
                "filing_url": "https://www.sec.gov/example",
                "detected_form_type": "SC TO-I",
                "cik": "0000000000",
                "accession_number": "0000000000-26-000001",
            },
            WORKSPACE_KEY: _workspace(complete=complete, promoted=promoted),
        },
    )


def _case(*, complete: bool = False) -> ResearchCase:
    rc = ResearchCase(
        id=uuid.uuid4(),
        situation_id=uuid.uuid4(),
        status="under_investigation",
        intake_method="special_situation_promotion",
        official_source_status="official_attached",
        evidence_level="official_primary",
        disclaimer="Educational only.",
        brief={
            "title": "Example Corp SC TO-I",
            "detection_summary": {
                "company_name": "Example Corp",
                "filing_type": "SC TO-I",
                "filing_url": "https://www.sec.gov/example",
                "accession_number": "0000000000-26-000001",
                "filing_date": "2026-05-13",
            },
            "methodology_workspace_snapshot": _workspace(complete=complete, promoted=True),
        },
    )
    rc.sources = [ResearchSource(source_name="SEC EDGAR", source_url="https://www.sec.gov/example", signal_quality="high")]
    rc.documents = []
    rc.tasks = []
    return rc


def _text(value) -> str:
    if isinstance(value, dict):
        return " ".join(_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_text(v) for v in value)
    return str(value)


def test_missing_required_resources_produce_blocking_items():
    package = build_situation_completion_workbench(_situation())
    assert package.summary.missing_required_resources == 1
    assert any(item.related_section == "required_resources" for item in package.blocking_items)


def test_candidate_found_resources_produce_review_actions():
    package = build_situation_completion_workbench(_situation())
    assert package.summary.candidate_sources_to_review == 1
    assert any(action.action_type == "review_candidate" for action in package.next_manual_actions)


def test_checklist_needs_evidence_produces_mapping_actions():
    package = build_situation_completion_workbench(_situation())
    assert package.summary.checklist_items_needing_evidence == 1
    assert any(action.action_type == "map_evidence" for action in package.next_manual_actions)


def test_research_case_with_score_package_produces_score_improvement_plan():
    rc = _case()
    score = build_intelligence_score_package(rc)
    prep = build_evaluation_prep_package(rc)
    package = build_research_case_completion_workbench(rc, intelligence_score=score, evaluation_prep=prep)
    assert package.score_improvement_plan.detection
    assert package.score_improvement_plan.structuring
    assert package.score_improvement_plan.risk_discipline


def test_completion_score_increases_when_resources_are_evidence_found():
    incomplete = build_situation_completion_workbench(_situation(complete=False))
    complete = build_situation_completion_workbench(_situation(complete=True))
    assert complete.completion_score > incomplete.completion_score


def test_promoted_case_shows_research_case_exists():
    package = build_situation_completion_workbench(_situation(promoted=True), linked_research_case=_case())
    assert package.summary.research_case_exists is True
    assert package.completion_level == "promoted"


def test_no_investment_action_language():
    package = build_situation_completion_workbench(_situation())
    text = _text(package.model_dump()).lower()
    assert "buy" not in text
    assert "sell" not in text
    assert "hold" not in text
    assert "recommendation" not in text


def test_no_network_clients_imported():
    source = inspect.getsource(module)
    banned = ["requests", "httpx", "aiohttp", "urllib", "SECEdgarAdapter", "load_master_index"]
    assert not any(token in source for token in banned)
