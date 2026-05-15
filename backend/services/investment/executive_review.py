from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.investment.dani_weber_metrics import collect_dani_weber_metrics_package
from backend.services.investment.fontana_report import collect_fontana_diagnostic_report


EXECUTIVE_REVIEW_GUARDRAILS = [
    "Read-only deterministic Executive Review.",
    "No AI or evaluator is called.",
    "No external fetch is called.",
    "No database writes are performed.",
    "No automatic ResearchCase creation, promotion, evaluation, verification, discard, or publishing.",
    "Joint recommendations require Dani approval before implementation.",
    "Candidate / Watchlist / Reject are operational workflow labels, not investment advice.",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _recommendation(
    *,
    recommendation_id: str,
    title: str,
    product_area: str,
    evidence: str,
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "id": recommendation_id,
        "title": title,
        "product_area": product_area,
        "evidence": evidence,
        "recommended_action": recommended_action,
        "requires_dani_approval": True,
        "auto_apply": False,
    }


def _finding(
    *,
    finding_id: str,
    coo_observation: str,
    cto_interpretation: str,
    product_area: str,
    severity: str,
    evidence: str,
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "coo_observation": coo_observation,
        "cto_interpretation": cto_interpretation,
        "product_area": product_area,
        "severity": severity,
        "evidence": evidence,
        "recommended_action": recommended_action,
        "requires_dani_approval": True,
        "auto_apply": False,
    }


def _severity_for(count: int, default: str = "warning") -> str:
    if count >= 10:
        return "critical"
    if count > 0:
        return default
    return "info"


def _is_meaningful_gap(value: str) -> bool:
    normalized = value.lower()
    return bool(value) and "no aggregate evidence gap" not in normalized


def build_executive_review_package(
    coo_metrics: dict[str, Any],
    fontana_report: dict[str, Any],
) -> dict[str, Any]:
    coo_bottlenecks = coo_metrics.get("top_bottlenecks") if isinstance(coo_metrics.get("top_bottlenecks"), list) else []
    cto_bottlenecks = fontana_report.get("case_bottlenecks") if isinstance(fontana_report.get("case_bottlenecks"), list) else []
    evidence_gaps = [
        str(item)
        for item in (fontana_report.get("evidence_gaps") if isinstance(fontana_report.get("evidence_gaps"), list) else [])
        if _is_meaningful_gap(str(item))
    ]
    improvements = coo_metrics.get("recommended_process_improvements") if isinstance(coo_metrics.get("recommended_process_improvements"), list) else []

    coo_summary = (
        f"{coo_metrics.get('total_special_situations', 0)} SpecialSituation signal(s), "
        f"{coo_metrics.get('promotion_rate_to_research_case', {}).get('rate_percent', 0)}% promoted to ResearchCase, "
        f"{coo_metrics.get('documentation_blockers', {}).get('missing_required_resources', 0)} missing required resource item(s)."
    )
    cto_summary = str(fontana_report.get("summary") or "Fontana deterministic report not available.")

    joint_findings: list[dict[str, Any]] = []
    for bottleneck in coo_bottlenecks[:3]:
        finding_id = str(bottleneck.get("id") or "coo_bottleneck")
        count = int(bottleneck.get("count") or 0)
        title = str(bottleneck.get("title") or "COO bottleneck")
        related_cto = cto_bottlenecks[0] if cto_bottlenecks else "Fontana should interpret product and technical causes before implementation."
        product_area = "Documentation Workflow" if "resource" in finding_id or "checklist" in finding_id else "Executive Office"
        joint_findings.append(_finding(
            finding_id=f"exec-{finding_id}",
            coo_observation=f"{title}: {count} item(s) in Dani Weber metrics.",
            cto_interpretation=str(related_cto),
            product_area=product_area,
            severity=_severity_for(count),
            evidence=str(bottleneck),
            recommended_action="Review the bottleneck with Fontana interpretation and approve a future process-improvement sprint if warranted.",
        ))

    if evidence_gaps and not any(item["id"] == "exec-missing_required_resources" for item in joint_findings):
        joint_findings.append(_finding(
            finding_id="exec-fontana-evidence-gap",
            coo_observation="Documentation quality depends on closing source and evidence gaps manually.",
            cto_interpretation=evidence_gaps[0],
            product_area="Evidence Review",
            severity="warning",
            evidence=evidence_gaps[0],
            recommended_action="Use official-source workflow and SEC acquisition deployment QA before expanding automation.",
        ))

    joint_recommendations = [
        _recommendation(
            recommendation_id="exec-review-top-bottleneck",
            title="Review top COO / CTO bottleneck",
            product_area=joint_findings[0]["product_area"],
            evidence=joint_findings[0]["evidence"],
            recommended_action=joint_findings[0]["recommended_action"],
        )
    ] if joint_findings else [
        _recommendation(
            recommendation_id="exec-continue-monitoring",
            title="Continue deterministic monitoring",
            product_area="Executive Office",
            evidence="No dominant COO / CTO joint finding is visible in the current deterministic snapshot.",
            recommended_action="Keep metrics read-only and review again after the next manual deployment or documentation batch.",
        )
    ]

    pending_approval_items = []
    for improvement in improvements[:5]:
        pending_approval_items.append({
            "id": str(improvement.get("id") or "coo-improvement"),
            "title": str(improvement.get("title") or "COO process improvement"),
            "source": "Dani Weber COO Metrics",
            "category": str(improvement.get("category") or "FIX_BOTTLENECK"),
            "evidence": str(improvement.get("evidence") or "Deterministic process metric."),
            "requires_dani_approval": True,
            "auto_apply": False,
        })
    pending_approval_items.extend({
        "id": item["id"],
        "title": item["title"],
        "source": "Executive Review",
        "category": "CREATE_SPRINT",
        "evidence": item["evidence"],
        "requires_dani_approval": True,
        "auto_apply": False,
    } for item in joint_recommendations[:2])

    next_sprint_candidates = [
        {
            "id": "exec-next-process-sprint",
            "title": recommendation["title"],
            "reason": recommendation["recommended_action"],
            "requires_dani_approval": True,
            "auto_apply": False,
        }
        for recommendation in joint_recommendations[:3]
    ]

    return {
        "generated_at": _now_iso(),
        "coo_summary": coo_summary,
        "cto_summary": cto_summary,
        "joint_findings": joint_findings,
        "joint_recommendations": joint_recommendations,
        "pending_approval_items": pending_approval_items,
        "guardrails": EXECUTIVE_REVIEW_GUARDRAILS,
        "next_sprint_candidates": next_sprint_candidates,
    }


async def collect_executive_review_package(db: AsyncSession) -> dict[str, Any]:
    coo_metrics = await collect_dani_weber_metrics_package(db)
    fontana_report = await collect_fontana_diagnostic_report(db)
    return build_executive_review_package(coo_metrics, fontana_report)
