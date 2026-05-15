from __future__ import annotations

import inspect
import uuid
from types import SimpleNamespace

from backend.models.investment_research import ResearchCase
from backend.services.investment import operational_view as module
from backend.services.investment.operational_view import build_operational_view_package


def _case(
    *,
    status: str = "under_investigation",
    readiness: str | None = None,
    brief: dict | None = None,
    notes: str | None = None,
    linked_situation: bool = False,
) -> ResearchCase:
    return ResearchCase(
        id=uuid.uuid4(),
        status=status,
        investment_readiness=readiness,
        brief=brief or {},
        notes=notes,
        situation_id=uuid.uuid4() if linked_situation else None,
    )


def _prep(*, missing_resources: int = 0, checklist_missing: int = 0, actions: list[str] | None = None):
    return SimpleNamespace(
        required_resources=SimpleNamespace(missing=[{}] * missing_resources),
        checklist=SimpleNamespace(missing=[{}] * checklist_missing),
        suggested_next_actions=[SimpleNamespace(label=action) for action in actions or []],
    )


def _score(*, total: int = 80, warnings: list[str] | None = None):
    return SimpleNamespace(total_score=total, warnings=warnings or [])


def _completion(
    *,
    score: int = 80,
    missing_resources: int = 0,
    checklist_missing: int = 0,
    high_blockers: int = 0,
    actions: list[str] | None = None,
):
    return SimpleNamespace(
        completion_score=score,
        summary=SimpleNamespace(
            missing_required_resources=missing_resources,
            checklist_items_needing_evidence=checklist_missing,
        ),
        blocking_items=[SimpleNamespace(severity="high") for _ in range(high_blockers)],
        next_manual_actions=[SimpleNamespace(label=action) for action in actions or []],
    )


def _evidence(count: int = 2):
    return SimpleNamespace(links=[object()] * count)


def _analogues(count: int = 1):
    return SimpleNamespace(historical_case_matches=[object()] * count, matched_patterns=[])


def _sec(count: int = 1):
    return SimpleNamespace(known_official_links=[object()] * count, likely_document_targets=[], acquired_documents=[])


def test_operational_view_returns_insufficient_information_for_sparse_metadata():
    package = build_operational_view_package(_case())

    assert package.operational_view == "insufficient_information"
    assert package.confidence == "low"
    assert package.not_investment_advice is True
    assert package.final_decision_by_dani is True
    assert package.blockers


def test_operational_view_returns_candidate_for_strong_metadata():
    package = build_operational_view_package(
        _case(linked_situation=True),
        evaluation_prep=_prep(),
        intelligence_score=_score(total=88),
        completion_workbench=_completion(score=86),
        evidence_links=_evidence(3),
        historical_analogues=_analogues(1),
        sec_preview=_sec(1),
    )

    assert package.operational_view == "candidate"
    assert package.confidence == "high"
    assert package.not_investment_advice is True
    assert package.final_decision_by_dani is True


def test_operational_view_returns_watchlist_for_interesting_case_with_missing_catalyst_context():
    package = build_operational_view_package(
        _case(readiness="monitor", notes="Catalyst timing still unclear", linked_situation=True),
        evaluation_prep=_prep(missing_resources=1),
        intelligence_score=_score(total=72),
        completion_workbench=_completion(score=68, missing_resources=1),
        evidence_links=_evidence(2),
        sec_preview=_sec(1),
    )

    assert package.operational_view == "watchlist"
    assert package.blockers
    assert package.what_would_change_view


def test_operational_view_returns_reject_for_weak_or_expired_case():
    package = build_operational_view_package(
        _case(status="archived", notes="Expired event with noisy unsupported context", linked_situation=True),
        evaluation_prep=_prep(),
        intelligence_score=_score(total=40),
        completion_workbench=_completion(score=30),
        evidence_links=_evidence(1),
    )

    assert package.operational_view == "reject"
    assert package.confidence == "low"


def test_operational_view_output_avoids_private_action_language():
    package = build_operational_view_package(
        _case(linked_situation=True),
        evaluation_prep=_prep(),
        intelligence_score=_score(total=88),
        completion_workbench=_completion(score=86),
        evidence_links=_evidence(3),
        historical_analogues=_analogues(1),
        sec_preview=_sec(1),
    )
    rendered = str(package.model_dump()).lower()

    for banned in ("buy", "sell", "hold"):
        assert banned not in rendered
    assert package.operational_view == "candidate"
    assert package.not_investment_advice is True
    assert package.final_decision_by_dani is True


def test_operational_view_service_has_no_runtime_automation_or_db_writes():
    source = inspect.getsource(module).lower()

    for banned in (
        "openai",
        "anthropic",
        "evaluate_situation",
        "run_v2",
        "/api/investment/scan",
        "scheduler",
        "cron",
        "db.add",
        ".commit(",
        ".flush(",
        "flag_modified",
    ):
        assert banned not in source
