import json
import uuid

from backend.models.investment_research import ResearchCase, ResearchDocument, ResearchSource
from backend.services.investment.research_cases import build_evaluation_prep_package


def _resource(resource_id: str, title: str, status: str) -> dict:
    return {
        "resource_id": resource_id,
        "title": title,
        "status": status,
        "required_or_optional": "required",
        "source_type": "sec_filing",
    }


def _check(check_id: str, title: str, status: str) -> dict:
    return {
        "check_id": check_id,
        "title": title,
        "status": status,
        "section": "Source verification",
        "human_review_required": True,
    }


def _case(*, resources=None, checklist=None, official=True) -> ResearchCase:
    rc = ResearchCase(
        id=uuid.uuid4(),
        situation_id=uuid.uuid4(),
        status="under_investigation",
        investment_readiness="needs_more_work",
        intake_method="special_situation_promotion",
        source_origin_name="SpecialSituation",
        official_source_status="official_attached" if official else "unknown",
        disclaimer="Este análisis es educativo. No es asesoramiento financiero.",
        brief={
            "title": "Example Co - SC TO-T",
            "source": "special_situation_promotion",
            "methodology_workspace_snapshot": {
                "required_resources": resources if resources is not None else [],
                "checklist": checklist if checklist is not None else [],
                "progress": {},
            },
        },
    )
    rc.sources = []
    rc.documents = []
    return rc


def test_evaluation_prep_without_promoted_snapshot_is_not_ready():
    rc = ResearchCase(
        id=uuid.uuid4(),
        status="under_investigation",
        disclaimer="Este análisis es educativo. No es asesoramiento financiero.",
        brief={},
    )
    rc.sources = []
    rc.documents = []

    prep = build_evaluation_prep_package(rc)

    assert prep.readiness.level == "not_ready"
    assert prep.readiness.score == 0
    assert "No promoted methodology snapshot" in prep.readiness.blocking_reasons[0]


def test_evaluation_prep_with_missing_resources_blocks_readiness():
    rc = _case(
        resources=[
            _resource("sec_filing", "SEC filing", "missing"),
            _resource("offer_doc", "Offer document", "missing"),
        ],
        checklist=[_check("terms", "Verify offer terms", "needs_evidence")],
    )

    prep = build_evaluation_prep_package(rc)

    assert prep.readiness.level == "not_ready"
    assert len(prep.required_resources.missing) == 2
    assert prep.suggested_next_actions[0].label == "Collect missing required resources"


def test_evaluation_prep_with_candidate_resources_needs_more_evidence():
    rc = _case(
        resources=[
            _resource("sec_filing", "SEC filing", "candidate_found"),
            _resource("offer_doc", "Offer document", "candidate_found"),
        ],
        checklist=[_check("terms", "Verify offer terms", "needs_evidence")],
    )

    prep = build_evaluation_prep_package(rc)

    assert prep.readiness.level == "needs_more_evidence"
    assert len(prep.required_resources.candidate_found) == 2
    assert any("Resources are present as candidates" in issue for issue in prep.source_quality.issues)


def test_evaluation_prep_with_evidence_found_can_be_ready_for_manual_evaluation():
    rc = _case(
        resources=[
            _resource("sec_filing", "SEC filing", "evidence_found"),
            _resource("offer_doc", "Offer document", "evidence_found"),
        ],
        checklist=[
            _check("terms", "Verify offer terms", "evidence_found"),
            _check("dates", "Verify dates", "evidence_found"),
        ],
    )
    rc.sources = [
        ResearchSource(
            source_name="SEC EDGAR",
            source_url="https://www.sec.gov/example",
            signal_quality="high",
        )
    ]

    prep = build_evaluation_prep_package(rc)

    assert prep.readiness.level == "ready_for_manual_evaluation"
    assert prep.readiness.score == 100
    assert len(prep.required_resources.evidence_found) == 2


def test_evaluation_prep_reports_checklist_gaps():
    rc = _case(
        resources=[_resource("sec_filing", "SEC filing", "evidence_found")],
        checklist=[
            _check("terms", "Verify offer terms", "evidence_found"),
            _check("financing", "Verify financing", "needs_evidence"),
        ],
    )

    prep = build_evaluation_prep_package(rc)

    assert len(prep.checklist.missing) == 1
    assert prep.checklist.missing[0]["title"] == "Verify financing"
    assert any(action.label == "Map evidence to checklist gaps" for action in prep.suggested_next_actions)


def test_evaluation_prep_output_contains_no_buy_sell_hold_recommendation_language():
    rc = _case(
        resources=[_resource("sec_filing", "SEC filing", "candidate_found")],
        checklist=[_check("terms", "Verify offer terms", "needs_evidence")],
    )
    rc.documents = [ResearchDocument(url="https://www.sec.gov/example", title="SEC filing")]

    payload = build_evaluation_prep_package(rc).model_dump()
    text = json.dumps(payload).lower()

    assert "buy" not in text
    assert "sell" not in text
    assert "hold" not in text
    assert "recommendation" in text
    assert payload["guardrails"][0] == "This is not an evaluation."
