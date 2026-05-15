import inspect
import uuid

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment import dani_weber_metrics as module
from backend.services.investment.dani_weber_metrics import build_dani_weber_metrics_package
from backend.services.investment.methodology_workspace import WORKSPACE_KEY


def _workspace(
    *,
    workflow_status: str = "needs_resources",
    required_resources: list[dict] | None = None,
    resource_candidates: list[dict] | None = None,
    checklist: list[dict] | None = None,
    research_case_id: str | None = None,
) -> dict:
    workspace = {
        "workflow_status": workflow_status,
        "required_resources": required_resources or [],
        "resource_candidates": resource_candidates or [],
        "checklist": checklist or [],
    }
    if research_case_id:
        workspace["research_case_id"] = research_case_id
    return {WORKSPACE_KEY: workspace}


def _situation(
    *,
    situation_type: str = "merger_arbitrage",
    status: str = "detected",
    workflow_status: str = "needs_resources",
    required_resources: list[dict] | None = None,
    resource_candidates: list[dict] | None = None,
    checklist: list[dict] | None = None,
    research_case_id: str | None = None,
) -> SpecialSituation:
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type=situation_type,
        company_name="Example Corp",
        ticker="EXM",
        filing_type="SC TO-T",
        filing_url="https://www.sec.gov/Archives/edgar/data/1/example.htm",
        status=status,
        evaluation=_workspace(
            workflow_status=workflow_status,
            required_resources=required_resources,
            resource_candidates=resource_candidates,
            checklist=checklist,
            research_case_id=research_case_id,
        ),
    )


def _research_case(situation: SpecialSituation | None = None, *, status: str = "candidate") -> ResearchCase:
    return ResearchCase(
        id=uuid.uuid4(),
        situation_id=situation.id if situation else None,
        status=status,
        brief={},
        source_origin_name="SpecialSituation" if situation else "Manual",
    )


def test_empty_data_returns_zero_metrics_and_safe_proposal():
    package = build_dani_weber_metrics_package([], [])

    assert package["total_special_situations"] == 0
    assert package["promotion_rate_to_research_case"]["rate_percent"] == 0
    assert package["documentation_blockers"]["missing_required_resources"] == 0
    assert package["recommended_process_improvements"][0]["requires_dani_approval"] is True
    assert package["recommended_process_improvements"][0]["auto_apply"] is False


def test_many_detected_but_few_promoted_creates_promotion_bottleneck():
    situations = [_situation() for _ in range(4)]
    linked = _research_case(situations[0])

    package = build_dani_weber_metrics_package(situations, [linked])

    assert package["total_special_situations"] == 4
    assert package["promotion_rate_to_research_case"] == {
        "promoted_count": 1,
        "total_special_situations": 4,
        "rate_percent": 25,
    }


def test_missing_resource_bottleneck_frequency_and_source_coverage():
    situation = _situation(
        required_resources=[
            {"id": "sc_to_t", "title": "SC TO-T filing", "status": "missing"},
            {"id": "offer", "title": "Offer to Purchase", "status": "needs_evidence"},
            {"id": "agreement", "title": "Merger Agreement", "status": "candidate_found"},
        ],
        resource_candidates=[
            {"title": "SC TO-T candidate", "status": "candidate_found", "source_type": "official_sec"},
        ],
    )

    package = build_dani_weber_metrics_package([situation], [])

    assert package["documentation_blockers"]["missing_required_resources"] == 2
    assert package["missing_resource_frequency"][:2] == [
        {"key": "Offer to Purchase", "count": 1},
        {"key": "SC TO-T filing", "count": 1},
    ]
    assert package["candidate_source_coverage"]["coverage_percent"] == 67
    assert package["candidate_source_coverage"]["by_source_type"] == [{"key": "official_sec", "count": 1}]


def test_documentation_blocker_frequency_counts_checklist_and_review_items():
    situation = _situation(
        checklist=[
            {"id": "terms", "status": "needs_evidence", "human_review_required": True},
            {"id": "financing", "status": "not_started"},
            {"id": "approval", "status": "verified", "human_review_required": True},
        ],
        resource_candidates=[
            {"title": "Noisy source", "status": "rejected", "source_type": "generic_web"},
        ],
    )

    package = build_dani_weber_metrics_package([situation], [])

    assert package["documentation_blockers"]["checklist_blocked_items"] == 2
    assert package["documentation_blockers"]["human_review_required_items"] == 2
    assert package["documentation_blockers"]["rejected_resource_candidates"] == 1


def test_low_priority_or_noise_count_uses_statuses_and_rejected_candidates():
    ignored = _situation(status="ignored", workflow_status="triage_needed")
    noisy_candidate = _situation(
        resource_candidates=[
            {"title": "Noisy source", "status": "rejected", "source_type": "generic_web"},
        ],
    )

    package = build_dani_weber_metrics_package([ignored, noisy_candidate], [])

    assert package["low_priority_or_noise_count"] == 2
    assert any(item["id"] == "noise_reduction" for item in package["top_bottlenecks"])


def test_recommended_process_improvement_requires_dani_approval():
    situation = _situation(
        required_resources=[{"title": "Offer to Purchase", "status": "missing"}],
    )

    package = build_dani_weber_metrics_package([situation], [])

    for improvement in package["recommended_process_improvements"]:
        assert improvement["requires_dani_approval"] is True
        assert improvement["auto_apply"] is False
        assert improvement["category"] in {
            "ADD_SOURCE",
            "IMPROVE_DOCUMENTATION_WORKFLOW",
            "IMPROVE_DETECTION_RULE",
            "IMPROVE_AGENT_SKILL",
            "FIX_BOTTLENECK",
            "ADD_KPI",
        }


def test_no_investment_recommendation_language():
    situation = _situation(
        required_resources=[{"title": "Offer to Purchase", "status": "missing"}],
    )

    package = build_dani_weber_metrics_package([situation], [])
    rendered = str(package).lower()

    for banned in ["buy", "sell", "hold"]:
        assert banned not in rendered


def test_service_source_has_no_db_writes_or_ai_evaluator_scan_calls():
    source = inspect.getsource(module).lower()

    banned = [
        "evaluate_situation",
        "run_v2",
        "/api/investment/scan",
        "scheduler",
        "cron",
        "openai",
        "anthropic",
        "db.add",
        ".commit(",
        ".flush(",
        "flag_modified",
    ]
    assert not any(token in source for token in banned)
