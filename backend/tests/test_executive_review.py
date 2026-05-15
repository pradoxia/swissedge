import inspect

from backend.services.investment import executive_review as module
from backend.services.investment.executive_review import build_executive_review_package


def _coo_metrics(*, bottlenecks: list[dict] | None = None, improvements: list[dict] | None = None) -> dict:
    return {
        "total_special_situations": 12,
        "promotion_rate_to_research_case": {"promoted_count": 2, "total_special_situations": 12, "rate_percent": 17},
        "documentation_blockers": {"missing_required_resources": 8},
        "top_bottlenecks": bottlenecks or [],
        "recommended_process_improvements": improvements or [],
    }


def _fontana_report(*, case_bottlenecks: list[str] | None = None, evidence_gaps: list[str] | None = None) -> dict:
    return {
        "summary": "Fontana observes preparation quality and technical guardrails without execution.",
        "case_bottlenecks": case_bottlenecks or [],
        "evidence_gaps": evidence_gaps or ["No aggregate evidence gap detected in stored metadata."],
        "suggested_future_sprints": [],
    }


def test_combines_coo_and_cto_findings():
    package = build_executive_review_package(
        _coo_metrics(
            bottlenecks=[
                {"id": "missing_required_resources", "title": "Missing required resources", "count": 8, "severity": "needs_attention"}
            ]
        ),
        _fontana_report(case_bottlenecks=["SEC acquisition exists; deployment QA should confirm the service file is present."]),
    )

    assert package["joint_findings"]
    finding = package["joint_findings"][0]
    assert finding["coo_observation"] == "Missing required resources: 8 item(s) in Dani Weber metrics."
    assert finding["cto_interpretation"] == "SEC acquisition exists; deployment QA should confirm the service file is present."
    assert finding["requires_dani_approval"] is True
    assert finding["auto_apply"] is False


def test_no_findings_returns_healthy_empty_state():
    package = build_executive_review_package(
        _coo_metrics(bottlenecks=[]),
        _fontana_report(case_bottlenecks=[], evidence_gaps=[]),
    )

    assert package["joint_findings"] == []
    assert package["joint_recommendations"][0]["id"] == "exec-continue-monitoring"
    assert "No dominant COO / CTO joint finding" in package["joint_recommendations"][0]["evidence"]


def test_all_recommendations_and_approval_items_require_dani_approval():
    package = build_executive_review_package(
        _coo_metrics(
            bottlenecks=[{"id": "low_promotion_rate", "title": "Low promotion rate to ResearchCase", "count": 10}],
            improvements=[
                {
                    "id": "coo-fix-promotion-bottleneck",
                    "title": "Review promotion bottleneck",
                    "category": "FIX_BOTTLENECK",
                    "evidence": "Few SpecialSituation rows are linked to ResearchCases.",
                }
            ],
        ),
        _fontana_report(case_bottlenecks=["Architecture should keep promotion manual."]),
    )

    for item in package["joint_recommendations"] + package["pending_approval_items"] + package["next_sprint_candidates"]:
        assert item["requires_dani_approval"] is True
        assert item["auto_apply"] is False


def test_no_investment_recommendation_language():
    package = build_executive_review_package(
        _coo_metrics(bottlenecks=[{"id": "noise_reduction", "title": "Noise or low-priority rows", "count": 3}]),
        _fontana_report(case_bottlenecks=["Keep the process manual and deterministic."]),
    )
    rendered = str(package).lower()

    for banned in ["buy", "sell", "hold"]:
        assert banned not in rendered


def test_service_source_has_no_db_writes_or_ai_evaluator_scan_or_cron_calls():
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
