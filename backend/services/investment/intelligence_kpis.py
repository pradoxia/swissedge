from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.agent_ops import AgentActivity, AgentDiagnosticEvent, AgentProfile, AgentRoom
from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
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


KPI_GUARDRAILS = [
    "Read-only deterministic aggregation.",
    "No AI or evaluator was called.",
    "No scanner, crawler, PDF download, or external fetch was called.",
    "No database writes are performed.",
    "Manual review remains required.",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _workspace(situation: SpecialSituation) -> dict[str, Any]:
    evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    workspace = evaluation.get(WORKSPACE_KEY)
    return workspace if isinstance(workspace, dict) else {}


def _snapshot_workspace(rc: ResearchCase) -> dict[str, Any]:
    brief = rc.brief if isinstance(rc.brief, dict) else {}
    workspace = brief.get("methodology_workspace_snapshot")
    return workspace if isinstance(workspace, dict) else {}


def _items(container: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = container.get(key)
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _status_count(items: list[dict[str, Any]], statuses: set[str]) -> int:
    return sum(1 for item in items if item.get("status") in statuses)


def _case_title(rc: ResearchCase) -> str:
    brief = rc.brief if isinstance(rc.brief, dict) else {}
    title = brief.get("title") or brief.get("company_name") or rc.source_origin_name
    return str(title) if title else f"ResearchCase {str(rc.id)[:8]}"


def _situation_title(situation: SpecialSituation) -> str:
    return situation.company_name or f"SpecialSituation {str(situation.id)[:8]}"


def _average(values: list[int]) -> int:
    return round(sum(values) / len(values)) if values else 0


def _evidence_counts_from_workspace(workspace: dict[str, Any]) -> dict[str, int]:
    required = _items(workspace, "required_resources")
    candidates = _items(workspace, "resource_candidates")
    return {
        "required_resources_total": len(required),
        "missing_required_resources_total": _status_count(required, {"missing", "needs_evidence", "not_started"}),
        "candidate_found_total": _status_count(required, {"candidate_found"}) + _status_count(candidates, {"candidate_found"}),
        "evidence_found_total": _status_count(required, {"evidence_found", "verified"}) + _status_count(candidates, {"evidence_found", "verified"}),
        "rejected_total": _status_count(candidates, {"rejected"}),
    }


def _add_counts(target: dict[str, int], source: dict[str, int]) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def _case_needs_manual_work(rc: ResearchCase, score: Any) -> bool:
    prep = getattr(score, "evaluation_prep_summary", {}) or {}
    if prep.get("required_resources_missing", 0) > 0 or prep.get("checklist_missing", 0) > 0:
        return True
    return bool(getattr(rc, "tasks", []) or [])


def build_intelligence_kpi_package(
    research_cases: list[ResearchCase],
    special_situations: list[SpecialSituation],
    *,
    agent_rooms: list[AgentRoom] | None = None,
    agent_profiles: list[AgentProfile] | None = None,
    agent_activities: list[AgentActivity] | None = None,
    agent_diagnostics: list[AgentDiagnosticEvent] | None = None,
) -> dict[str, Any]:
    agent_rooms = agent_rooms or []
    agent_profiles = agent_profiles or []
    agent_activities = agent_activities or []
    agent_diagnostics = agent_diagnostics or []
    situations_by_id = {situation.id: situation for situation in special_situations}

    score_rows: list[dict[str, Any]] = []
    score_values: list[int] = []
    grade_counts = {
        "approvable_count": 0,
        "useful_incomplete_count": 0,
        "review_pipeline_count": 0,
    }
    documentation_scores: list[int] = []
    documentation_levels = {
        "good_count": 0,
        "needs_links_count": 0,
        "needs_required_resources_count": 0,
        "needs_evidence_mapping_count": 0,
    }
    evidence = {
        "required_resources_total": 0,
        "missing_required_resources_total": 0,
        "candidate_found_total": 0,
        "evidence_found_total": 0,
        "rejected_total": 0,
        "evidence_links_total": 0,
    }
    missing_evidence_cases: list[dict[str, Any]] = []
    manual_work_cases: list[dict[str, Any]] = []

    for situation in special_situations:
        workspace = _workspace(situation)
        _add_counts(evidence, _evidence_counts_from_workspace(workspace))
        evidence_links = build_situation_evidence_links(situation)
        evidence["evidence_links_total"] += len(evidence_links.links)
        guide = build_situation_documentation_guide(situation, evidence_links)
        documentation_scores.append(guide.documentation_quality.score)
        level_key = f"{guide.documentation_quality.level}_count"
        if level_key in documentation_levels:
            documentation_levels[level_key] += 1
        missing_count = len(guide.missing_evidence.missing_required_resources) + len(guide.missing_evidence.missing_checklist_items)
        if missing_count:
            missing_evidence_cases.append({
                "id": str(situation.id),
                "case_type": "special_situation",
                "title": _situation_title(situation),
                "missing_items": missing_count,
                "href": f"/investment/situations/{situation.id}",
            })

    for rc in research_cases:
        workspace = _snapshot_workspace(rc)
        _add_counts(evidence, _evidence_counts_from_workspace(workspace))
        score = build_intelligence_score_package(rc)
        evidence["evidence_links_total"] += int(score.evidence_links_summary.get("total_links", 0) or 0)
        score_values.append(score.total_score)
        score_rows.append({
            "id": str(rc.id),
            "case_type": "research_case",
            "title": _case_title(rc),
            "score": score.total_score,
            "grade": score.grade,
            "href": f"/investment/research/{rc.id}",
        })
        if score.grade == "APPROVABLE":
            grade_counts["approvable_count"] += 1
        elif score.grade == "USEFUL_INCOMPLETE":
            grade_counts["useful_incomplete_count"] += 1
        else:
            grade_counts["review_pipeline_count"] += 1

        source_situation = situations_by_id.get(rc.situation_id) if rc.situation_id else None
        evidence_links = build_research_case_evidence_links(rc)
        prep = build_evaluation_prep_package(rc)
        guide = build_research_case_documentation_guide(
            rc,
            evidence_links=evidence_links,
            evaluation_prep=prep,
            intelligence_score=score,
            source_situation=source_situation,
        )
        documentation_scores.append(guide.documentation_quality.score)
        level_key = f"{guide.documentation_quality.level}_count"
        if level_key in documentation_levels:
            documentation_levels[level_key] += 1
        missing_count = len(guide.missing_evidence.missing_required_resources) + len(guide.missing_evidence.missing_checklist_items)
        if missing_count:
            missing_evidence_cases.append({
                "id": str(rc.id),
                "case_type": "research_case",
                "title": _case_title(rc),
                "missing_items": missing_count,
                "href": f"/investment/research/{rc.id}",
            })
        if _case_needs_manual_work(rc, score):
            manual_work_cases.append({
                "id": str(rc.id),
                "case_type": "research_case",
                "title": _case_title(rc),
                "score": score.total_score,
                "grade": score.grade,
                "href": f"/investment/research/{rc.id}",
            })

    promoted_count = sum(1 for situation in special_situations if _workspace(situation).get("research_case_id"))
    ready_for_manual_review = sum(1 for row in score_rows if row["grade"] in {"APPROVABLE", "USEFUL_INCOMPLETE"})
    missing_evidence_hunter_load = evidence["missing_required_resources_total"] + len(missing_evidence_cases)
    lowest_scoring = sorted(score_rows, key=lambda row: row["score"])[:5]

    bottlenecks: list[dict[str, Any]] = []
    if evidence["missing_required_resources_total"]:
        bottlenecks.append({
            "key": "missing_required_resources",
            "label": "Missing required resources",
            "severity": "needs_attention",
            "count": evidence["missing_required_resources_total"],
        })
    if grade_counts["review_pipeline_count"]:
        bottlenecks.append({
            "key": "review_pipeline",
            "label": "Cases still in preparation-quality review pipeline",
            "severity": "needs_attention",
            "count": grade_counts["review_pipeline_count"],
        })
    if documentation_levels["needs_links_count"] or documentation_levels["needs_required_resources_count"]:
        bottlenecks.append({
            "key": "documentation_gaps",
            "label": "Documentation guide gaps",
            "severity": "manual_review_required",
            "count": documentation_levels["needs_links_count"] + documentation_levels["needs_required_resources_count"],
        })

    manual_next_actions: list[dict[str, Any]] = []
    if missing_evidence_cases:
        manual_next_actions.append({
            "label": "Review missing evidence cases",
            "reason": "Some cases have missing required resources or checklist evidence.",
            "target_href": missing_evidence_cases[0]["href"],
        })
    if lowest_scoring:
        manual_next_actions.append({
            "label": "Inspect lowest preparation-quality cases",
            "reason": "Lowest scoring cases are likely to reveal the next documentation bottleneck.",
            "target_href": lowest_scoring[0]["href"],
        })
    if agent_diagnostics:
        manual_next_actions.append({
            "label": "Review Agent Ops diagnostics",
            "reason": "Diagnostic rows are available for manual triage.",
            "target_href": "/agent-ops",
        })

    return {
        "generated_at": _now_iso(),
        "case_counts": {
            "research_cases_total": len(research_cases),
            "special_situations_total": len(special_situations),
            "sec_detected": sum(1 for situation in special_situations if situation.filing_url or situation.filing_type),
            "promoted_to_research_case": promoted_count,
            "ready_for_manual_review": ready_for_manual_review,
            "missing_evidence": len(missing_evidence_cases),
        },
        "intelligence": {
            "average_score": _average(score_values),
            **grade_counts,
            "lowest_scoring_cases": lowest_scoring,
            "cases_needing_manual_work": manual_work_cases[:8],
        },
        "documentation": {
            "average_documentation_quality": _average(documentation_scores),
            **documentation_levels,
        },
        "evidence": evidence,
        "agent_ops": {
            "rooms_count": len(agent_rooms),
            "agents_count": len(agent_profiles),
            "activity_rows_count": len(agent_activities),
            "diagnostics_count": len(agent_diagnostics),
            "missing_evidence_hunter_load": missing_evidence_hunter_load,
            "rooms": [
                {
                    "id": str(room.id),
                    "key": room.key,
                    "name": room.name,
                    "href": f"/agent-ops/rooms/{room.key}",
                }
                for room in agent_rooms[:6]
            ],
        },
        "bottlenecks": bottlenecks,
        "manual_next_actions": manual_next_actions,
        "missing_evidence_cases": missing_evidence_cases[:10],
        "guardrails": KPI_GUARDRAILS,
    }


async def collect_intelligence_kpi_package(db: AsyncSession) -> dict[str, Any]:
    rc_result = await db.execute(
        select(ResearchCase).options(
            selectinload(ResearchCase.tasks),
            selectinload(ResearchCase.documents),
            selectinload(ResearchCase.sources),
        )
    )
    situation_result = await db.execute(select(SpecialSituation))
    research_cases = list(rc_result.scalars().all())
    special_situations = list(situation_result.scalars().all())

    agent_rooms: list[AgentRoom] = []
    agent_profiles: list[AgentProfile] = []
    agent_activities: list[AgentActivity] = []
    agent_diagnostics: list[AgentDiagnosticEvent] = []
    try:
        rooms_result = await db.execute(select(AgentRoom))
        agents_result = await db.execute(select(AgentProfile))
        activity_result = await db.execute(select(AgentActivity))
        diagnostics_result = await db.execute(select(AgentDiagnosticEvent))
        agent_rooms = list(rooms_result.scalars().all())
        agent_profiles = list(agents_result.scalars().all())
        agent_activities = list(activity_result.scalars().all())
        agent_diagnostics = list(diagnostics_result.scalars().all())
    except Exception:
        agent_rooms = []
        agent_profiles = []
        agent_activities = []
        agent_diagnostics = []

    return build_intelligence_kpi_package(
        research_cases,
        special_situations,
        agent_rooms=agent_rooms,
        agent_profiles=agent_profiles,
        agent_activities=agent_activities,
        agent_diagnostics=agent_diagnostics,
    )


def build_fontana_diagnostic_report(kpis: dict[str, Any]) -> dict[str, Any]:
    case_counts = kpis.get("case_counts", {})
    intelligence = kpis.get("intelligence", {})
    documentation = kpis.get("documentation", {})
    evidence = kpis.get("evidence", {})
    agent_ops = kpis.get("agent_ops", {})

    system_health = [
        f"{case_counts.get('special_situations_total', 0)} SpecialSituation row(s) detected in the stored pipeline.",
        f"{case_counts.get('research_cases_total', 0)} ResearchCase row(s) available for preparation-quality review.",
        f"Average Intelligence Score is {intelligence.get('average_score', 0)}/100.",
        f"Average documentation quality is {documentation.get('average_documentation_quality', 0)}/100.",
    ]
    case_bottlenecks = [
        item.get("label", "Unnamed bottleneck")
        for item in kpis.get("bottlenecks", [])
    ]
    evidence_gaps = []
    if evidence.get("missing_required_resources_total", 0):
        evidence_gaps.append(f"{evidence['missing_required_resources_total']} required resource(s) are missing.")
    if evidence.get("candidate_found_total", 0):
        evidence_gaps.append(f"{evidence['candidate_found_total']} candidate resource(s) need human review.")
    if evidence.get("rejected_total", 0):
        evidence_gaps.append(f"{evidence['rejected_total']} rejected resource candidate(s) remain visible for traceability.")
    if not evidence_gaps:
        evidence_gaps.append("No aggregate evidence gap detected in stored metadata.")

    agent_ops_findings = [
        f"{agent_ops.get('rooms_count', 0)} Agent Ops room(s), {agent_ops.get('agents_count', 0)} agent profile(s), and {agent_ops.get('diagnostics_count', 0)} diagnostic row(s) are visible.",
        f"Missing Evidence Hunter load indicator: {agent_ops.get('missing_evidence_hunter_load', 0)}.",
    ]
    manual_steps = [
        item.get("label", "Manual review")
        for item in kpis.get("manual_next_actions", [])
    ] or ["Review the Intelligence KPI Dashboard for the next manual triage target."]
    findings = [
        {
            "severity": "info",
            "area": "System health",
            "title": "Stored pipeline inventory",
            "description": item,
        }
        for item in system_health
    ]
    findings.extend(
        {
            "severity": "needs_attention",
            "area": "Case bottlenecks",
            "title": "Case bottleneck",
            "description": item,
        }
        for item in case_bottlenecks
    )
    findings.extend(
        {
            "severity": "needs_attention" if "missing" in item.lower() or "human review" in item.lower() else "info",
            "area": "Evidence",
            "title": "Evidence diagnostic",
            "description": item,
        }
        for item in evidence_gaps
    )
    severity_summary: dict[str, int] = {}
    for finding in findings:
        severity = finding["severity"]
        severity_summary[severity] = severity_summary.get(severity, 0) + 1
    guardrail_note = "Diagnostic-only read-only report. It did not run scanners, crawlers, evaluators, AI, production mutation, case promotion, or investment advice."

    return {
        "title": "Fontana Diagnostic Report",
        "mode": "deterministic_observer",
        "run_mode": "diagnostic_only",
        "generated_at": kpis.get("generated_at", _now_iso()),
        "next_run_at": None,
        "summary": "Fontana observes platform preparation quality, documentation gaps, evidence coverage, and manual workload. It does not execute changes.",
        "system_health": system_health,
        "scope_reviewed": [
            "case counts",
            "intelligence score aggregates",
            "documentation quality aggregates",
            "evidence coverage aggregates",
            "Agent Ops aggregate visibility",
        ],
        "severity_summary": severity_summary,
        "findings": findings,
        "case_bottlenecks": case_bottlenecks,
        "evidence_gaps": evidence_gaps,
        "agent_ops_findings": agent_ops_findings,
        "recommended_manual_next_steps": manual_steps,
        "recommended_engineering_tasks": manual_steps,
        "suggested_future_sprints": [
            "Improve missing-evidence triage UX after manual review.",
            "Add historical trend charts after KPI definitions are reviewed.",
            "Review Agent Ops diagnostic taxonomy before adding automation.",
        ],
        "guardrail_note": guardrail_note,
        "guardrails": [
            "Fontana does not execute changes.",
            "This report is deterministic and read-only.",
            "No AI or evaluator was called.",
            "No scanner, crawler, or external fetch was called.",
            "Manual review remains required.",
        ],
    }


async def collect_fontana_diagnostic_report(db: AsyncSession) -> dict[str, Any]:
    return build_fontana_diagnostic_report(await collect_intelligence_kpi_package(db))
