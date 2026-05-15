from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.methodology_workspace import WORKSPACE_KEY


DANI_WEBER_GUARDRAILS = [
    "Read-only deterministic COO metrics.",
    "No AI or evaluator is called.",
    "No external fetch is called.",
    "No database writes are performed.",
    "No automatic ResearchCase creation, promotion, evaluation, verification, or publishing.",
    "Improvement proposals require Dani approval before implementation.",
    "Candidate / Watchlist / Reject are operational workflow labels, not investment advice.",
]

MISSING_STATUSES = {"missing", "needs_evidence", "not_started"}
DOCUMENTED_STATUSES = {"candidate_found", "evidence_found", "verified", "manual_review_required"}
REVIEW_STATUSES = {"candidate_found", "manual_review_required", "evidence_found"}
LOW_PRIORITY_STATUSES = {"ignored", "archived", "rejected", "low_priority", "noise"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _workspace(situation: SpecialSituation) -> dict[str, Any]:
    evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    workspace = evaluation.get(WORKSPACE_KEY)
    return workspace if isinstance(workspace, dict) else {}


def _items(container: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = container.get(key)
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _increment(counter: dict[str, int], key: str | None, fallback: str = "unknown") -> None:
    normalized = str(key or fallback)
    counter[normalized] = counter.get(normalized, 0) + 1


def _percent(part: int, total: int) -> int:
    return round((part / total) * 100) if total else 0


def _resource_label(item: dict[str, Any]) -> str:
    for key in ("title", "name", "label", "id"):
        value = item.get(key)
        if value:
            return str(value)
    return "Unnamed resource"


def _candidate_source(item: dict[str, Any]) -> str:
    for key in ("source_type", "source", "source_name", "provider"):
        value = item.get(key)
        if value:
            return str(value)
    return "unknown"


def _is_promoted(situation: SpecialSituation, linked_case_ids: set[str]) -> bool:
    workspace = _workspace(situation)
    workspace_case_id = workspace.get("research_case_id")
    return bool(workspace_case_id) or str(situation.id) in linked_case_ids


def _top_counts(counter: dict[str, int], *, limit: int = 8) -> list[dict[str, Any]]:
    return [
        {"key": key, "count": count}
        for key, count in sorted(counter.items(), key=lambda row: (-row[1], row[0]))[:limit]
    ]


def _improvement(
    *,
    proposal_id: str,
    title: str,
    category: str,
    evidence: str,
    recommendation: str,
    expected_impact: str,
) -> dict[str, Any]:
    return {
        "id": proposal_id,
        "title": title,
        "category": category,
        "evidence": evidence,
        "recommendation": recommendation,
        "expected_impact": expected_impact,
        "requires_dani_approval": True,
        "auto_apply": False,
    }


def build_dani_weber_metrics_package(
    special_situations: list[SpecialSituation],
    research_cases: list[ResearchCase],
) -> dict[str, Any]:
    linked_case_ids = {str(rc.situation_id) for rc in research_cases if rc.situation_id}
    total = len(special_situations)
    promoted = 0
    by_workflow_phase: dict[str, int] = {}
    by_situation_type: dict[str, int] = {}
    research_case_statuses: dict[str, int] = {}
    missing_resource_counts: dict[str, int] = {}
    candidate_source_counts: dict[str, int] = {}
    cases_by_phase: dict[str, list[dict[str, str]]] = {}
    low_priority_or_noise_count = 0

    required_total = 0
    missing_required_total = 0
    checklist_total = 0
    checklist_blocked_total = 0
    human_review_required_total = 0
    resource_candidates_total = 0
    candidate_found_total = 0
    rejected_candidate_total = 0

    for rc in research_cases:
        _increment(research_case_statuses, rc.status)

    for situation in special_situations:
        workspace = _workspace(situation)
        phase = str(workspace.get("workflow_status") or situation.status or "unknown")
        _increment(by_workflow_phase, phase)
        _increment(by_situation_type, situation.situation_type)

        if _is_promoted(situation, linked_case_ids):
            promoted += 1

        if phase in {"new_detection", "triage_needed", "needs_resources", "checklist_in_progress"}:
            cases_by_phase.setdefault(phase, []).append({
                "id": str(situation.id),
                "title": situation.company_name,
                "href": f"/investment/situations/{situation.id}",
            })

        if str(situation.status or "").lower() in LOW_PRIORITY_STATUSES or phase.lower() in LOW_PRIORITY_STATUSES:
            low_priority_or_noise_count += 1

        required_resources = _items(workspace, "required_resources")
        resource_candidates = _items(workspace, "resource_candidates")
        checklist = _items(workspace, "checklist")
        required_total += len(required_resources)
        resource_candidates_total += len(resource_candidates)
        checklist_total += len(checklist)

        for item in required_resources:
            status = str(item.get("status") or "")
            if status in MISSING_STATUSES:
                missing_required_total += 1
                _increment(missing_resource_counts, _resource_label(item))
            if status in DOCUMENTED_STATUSES:
                candidate_found_total += 1

        for item in resource_candidates:
            status = str(item.get("status") or "")
            if status in REVIEW_STATUSES:
                candidate_found_total += 1
            if status == "rejected":
                rejected_candidate_total += 1
                low_priority_or_noise_count += 1
            _increment(candidate_source_counts, _candidate_source(item))

        for item in checklist:
            status = str(item.get("status") or "")
            if status in MISSING_STATUSES:
                checklist_blocked_total += 1
            if item.get("human_review_required") is True:
                human_review_required_total += 1

    cases_stuck_by_phase = [
        {"phase": phase, "count": len(rows), "cases": rows[:5]}
        for phase, rows in sorted(cases_by_phase.items(), key=lambda row: (-len(row[1]), row[0]))
    ]

    documentation_blockers = {
        "missing_required_resources": missing_required_total,
        "checklist_blocked_items": checklist_blocked_total,
        "human_review_required_items": human_review_required_total,
        "rejected_resource_candidates": rejected_candidate_total,
    }
    candidate_source_coverage = {
        "required_resources_total": required_total,
        "resource_candidates_total": resource_candidates_total,
        "candidate_found_total": candidate_found_total,
        "coverage_percent": _percent(candidate_found_total, required_total),
        "by_source_type": _top_counts(candidate_source_counts),
    }

    top_bottlenecks: list[dict[str, Any]] = []
    if missing_required_total:
        top_bottlenecks.append({
            "id": "missing_required_resources",
            "title": "Missing required resources",
            "count": missing_required_total,
            "severity": "needs_attention",
        })
    if checklist_blocked_total:
        top_bottlenecks.append({
            "id": "checklist_blocked",
            "title": "Checklist evidence gaps",
            "count": checklist_blocked_total,
            "severity": "needs_attention",
        })
    if total and _percent(promoted, total) < 25:
        top_bottlenecks.append({
            "id": "low_promotion_rate",
            "title": "Low promotion rate to ResearchCase",
            "count": total - promoted,
            "severity": "watch",
        })
    if low_priority_or_noise_count:
        top_bottlenecks.append({
            "id": "noise_reduction",
            "title": "Noise or low-priority rows",
            "count": low_priority_or_noise_count,
            "severity": "watch",
        })

    recommended_process_improvements: list[dict[str, Any]] = []
    if missing_required_total:
        recommended_process_improvements.append(_improvement(
            proposal_id="coo-improve-documentation-workflow",
            title="Tighten required-resource workflow",
            category="IMPROVE_DOCUMENTATION_WORKFLOW",
            evidence=f"{missing_required_total} required resource item(s) are missing or not started.",
            recommendation="Review missing-resource patterns and add clearer manual next steps to case documentation.",
            expected_impact="Improves documentation quality and reduces stalled evidence review.",
        ))
    if candidate_source_coverage["coverage_percent"] < 50 and required_total:
        recommended_process_improvements.append(_improvement(
            proposal_id="coo-add-source-coverage",
            title="Improve candidate source coverage",
            category="ADD_SOURCE",
            evidence=f"Candidate source coverage is {candidate_source_coverage['coverage_percent']}% across required resources.",
            recommendation="Identify recurring missing official-source categories and propose approved source coverage improvements.",
            expected_impact="Improves detection-to-documentation throughput without auto-verification.",
        ))
    if total and _percent(promoted, total) < 25:
        recommended_process_improvements.append(_improvement(
            proposal_id="coo-fix-promotion-bottleneck",
            title="Review promotion bottleneck",
            category="FIX_BOTTLENECK",
            evidence=f"{promoted} of {total} SpecialSituation row(s) are linked to ResearchCases.",
            recommendation="Review why detected rows are not reaching durable ResearchCase documentation.",
            expected_impact="Clarifies whether the bottleneck is detection quality, documentation gaps, or manual triage capacity.",
        ))
    if low_priority_or_noise_count:
        recommended_process_improvements.append(_improvement(
            proposal_id="coo-improve-detection-rule",
            title="Reduce noisy detections",
            category="IMPROVE_DETECTION_RULE",
            evidence=f"{low_priority_or_noise_count} row(s) or resource candidate(s) are low-priority, ignored, archived, rejected, or noisy.",
            recommendation="Review recurring noise patterns before changing detection rules.",
            expected_impact="Reduces review load while keeping detection coverage visible.",
        ))
    if not recommended_process_improvements:
        recommended_process_improvements.append(_improvement(
            proposal_id="coo-add-kpi-history",
            title="Add historical COO KPI trend later",
            category="ADD_KPI",
            evidence="No dominant bottleneck is visible in the current deterministic snapshot.",
            recommendation="Keep the current metrics read-only and consider a future trend snapshot after Dani approves KPI definitions.",
            expected_impact="Improves process monitoring without adding automation.",
        ))

    return {
        "generated_at": _now_iso(),
        "mode": "deterministic_read_only",
        "total_special_situations": total,
        "by_workflow_phase": by_workflow_phase,
        "by_situation_type": by_situation_type,
        "research_case_statuses": research_case_statuses,
        "promotion_rate_to_research_case": {
            "promoted_count": promoted,
            "total_special_situations": total,
            "rate_percent": _percent(promoted, total),
        },
        "documentation_blockers": documentation_blockers,
        "missing_resource_frequency": _top_counts(missing_resource_counts),
        "candidate_source_coverage": candidate_source_coverage,
        "cases_stuck_by_phase": cases_stuck_by_phase,
        "low_priority_or_noise_count": low_priority_or_noise_count,
        "top_bottlenecks": top_bottlenecks,
        "recommended_process_improvements": recommended_process_improvements,
        "guardrails": DANI_WEBER_GUARDRAILS,
    }


async def collect_dani_weber_metrics_package(db: AsyncSession) -> dict[str, Any]:
    situation_result = await db.execute(select(SpecialSituation))
    research_case_result = await db.execute(select(ResearchCase))
    return build_dani_weber_metrics_package(
        list(situation_result.scalars().all()),
        list(research_case_result.scalars().all()),
    )
