from __future__ import annotations

import json
from copy import copy
from typing import Any

from pydantic import BaseModel

from backend.models.investment_research import ResearchCase
from backend.services.investment.evidence_links import (
    build_research_case_evidence_links,
    summarize_evidence_links,
)
from backend.services.investment.research_cases import build_evaluation_prep_package


class IntelligenceScoreComponent(BaseModel):
    key: str
    label: str
    score: int
    max_score: int
    signals: list[str]
    gaps: list[str]


class IntelligenceScorePackage(BaseModel):
    research_case_id: str
    total_score: int
    grade: str
    grade_explanation: str
    components: list[IntelligenceScoreComponent]
    evaluation_prep_summary: dict
    evidence_links_summary: dict
    strengths: list[str]
    warnings: list[str]
    suggested_next_actions: list[str]
    guardrails: list[str]


_BRIEF_SECTIONS = [
    "executive_summary",
    "situation_type",
    "why_interesting",
    "methodology_reference",
    "company_context",
    "board_management",
    "key_documents",
    "timeline",
    "risk_analysis",
    "verify_before_investing",
    "missing_information",
    "source_intelligence",
    "investment_readiness_note",
    "public_summary_draft",
]

_DIRECTIVE_PATTERNS = [
    "buy ",
    "sell ",
    "hold ",
    "short ",
    "go long",
    "go short",
    "invest now",
    "investment recommendation",
]


def _brief(rc: ResearchCase) -> dict:
    return rc.brief if isinstance(rc.brief, dict) else {}


def _workspace(rc: ResearchCase) -> dict:
    snapshot = _brief(rc).get("methodology_workspace_snapshot")
    return snapshot if isinstance(snapshot, dict) else {}


def _detection(rc: ResearchCase) -> dict:
    summary = _brief(rc).get("detection_summary")
    return summary if isinstance(summary, dict) else {}


def _status_bucket(items: list[Any], positive_statuses: set[str]) -> int:
    count = 0
    for item in items:
        if isinstance(item, dict) and item.get("status") in positive_statuses:
            count += 1
    return count


def _coverage_points(done: int, total: int, max_points: int) -> int:
    if total <= 0:
        return 0
    return round(max_points * min(1.0, done / total))


def _weighted_resource_coverage(resources: list[Any]) -> tuple[float, int, int, int]:
    weights = {
        "verified": 1.0,
        "evidence_found": 1.0,
        "candidate_found": 0.5,
    }
    weighted = 0.0
    candidates = 0
    evidence_or_verified = 0
    total = 0
    for item in resources:
        if not isinstance(item, dict):
            continue
        total += 1
        status = item.get("status")
        weighted += weights.get(status, 0.0)
        if status == "candidate_found":
            candidates += 1
        if status in {"evidence_found", "verified"}:
            evidence_or_verified += 1
    return weighted, candidates, evidence_or_verified, total


def _contains_directive_language(rc: ResearchCase) -> bool:
    values: list[Any] = [rc.notes, rc.disclaimer, _brief(rc)]
    values.extend(getattr(rc, "tasks", []) or [])
    values.extend(getattr(rc, "documents", []) or [])
    values.extend(getattr(rc, "sources", []) or [])

    serializable: list[Any] = []
    for value in values:
        if isinstance(value, (str, dict, list)):
            serializable.append(value)
        elif value is not None:
            serializable.append(getattr(value, "description", None))
            serializable.append(getattr(value, "notes", None))
            serializable.append(getattr(value, "summary", None))
            serializable.append(getattr(value, "source_name", None))

    text = json.dumps(serializable, default=str).lower()
    return any(pattern in text for pattern in _DIRECTIVE_PATTERNS)


def _grade(total_score: int) -> tuple[str, str]:
    if total_score >= 90:
        return (
            "APPROVABLE",
            "Structurally approvable for manual review only. This is not investment approval.",
        )
    if total_score >= 70:
        return (
            "USEFUL_INCOMPLETE",
            "Useful preparation package, but still incomplete for manual review.",
        )
    return (
        "REVIEW_PIPELINE",
        "Pipeline review recommended before relying on the preparation package.",
    )


def _detection_score(rc: ResearchCase, evidence_summary: dict) -> IntelligenceScoreComponent:
    score = 0
    signals: list[str] = []
    gaps: list[str] = []
    detection = _detection(rc)

    if rc.situation_id or rc.intake_method:
        score += 8
        signals.append("Case has intake lineage.")
    else:
        gaps.append("No intake lineage is attached.")

    if rc.official_source_status == "official_attached" or rc.evidence_level == "official_primary":
        score += 10
        signals.append("Official source metadata is attached.")
    else:
        gaps.append("Official source metadata is not confirmed.")

    detection_fields = ["company_name", "filing_type", "filing_url", "accession_number", "filing_date"]
    present_fields = [field for field in detection_fields if detection.get(field)]
    field_points = _coverage_points(len(present_fields), len(detection_fields), 12)
    score += field_points
    if present_fields:
        signals.append(f"Detection summary includes {len(present_fields)} key field(s).")
    if field_points < 12:
        gaps.append("Detection summary is missing one or more key fields.")

    if evidence_summary.get("sec_links", 0) > 0:
        score += 6
        signals.append("SEC traceability link is present.")
    else:
        gaps.append("No SEC traceability link is present.")

    if evidence_summary.get("total_links", 0) > 0:
        score += 4
        signals.append("Evidence links are traceable.")
    else:
        gaps.append("No traceability links are available.")

    return IntelligenceScoreComponent(
        key="detection",
        label="Detection Score",
        score=min(score, 40),
        max_score=40,
        signals=signals,
        gaps=gaps,
    )


def _structuring_score(rc: ResearchCase, prep_score: int) -> IntelligenceScoreComponent:
    score = 0
    signals: list[str] = []
    gaps: list[str] = []
    workspace = _workspace(rc)
    resources = workspace.get("required_resources") if isinstance(workspace.get("required_resources"), list) else []
    checklist = workspace.get("checklist") if isinstance(workspace.get("checklist"), list) else []

    prep_points = round(min(max(prep_score, 0), 100) * 0.12)
    score += prep_points
    signals.append(f"Evaluation preparation contributes {prep_points}/12 points.")

    resource_weighted, resource_candidates, resource_evidence, resource_total = _weighted_resource_coverage(resources)
    resource_points = round(8 * min(1.0, resource_weighted / resource_total)) if resource_total else 0
    score += resource_points
    if resource_points:
        signals.append(
            f"{resource_evidence}/{resource_total} required resource(s) have evidence or verified status."
        )
    if resource_candidates:
        signals.append(f"{resource_candidates} required resource candidate(s) receive partial credit only.")
    if resource_points < 8:
        gaps.append("Required-resource coverage is incomplete.")

    checklist_done = _status_bucket(checklist, {"evidence_found", "verified"})
    checklist_points = _coverage_points(checklist_done, len(checklist), 8)
    score += checklist_points
    if checklist_points:
        signals.append(f"{checklist_done}/{len(checklist)} checklist item(s) have evidence.")
    if checklist_points < 8:
        gaps.append("Checklist evidence mapping is incomplete.")

    filled_sections = [
        section for section in _BRIEF_SECTIONS
        if isinstance(_brief(rc).get(section), str) and _brief(rc).get(section, "").strip()
    ]
    brief_points = _coverage_points(len(filled_sections), len(_BRIEF_SECTIONS), 6)
    score += brief_points
    if brief_points:
        signals.append(f"{len(filled_sections)}/{len(_BRIEF_SECTIONS)} brief section(s) are filled.")
    if brief_points < 6:
        gaps.append("Brief structure is not fully populated.")

    records_points = 0
    if getattr(rc, "tasks", []) or []:
        records_points += 2
        signals.append("Research tasks are recorded.")
    else:
        gaps.append("No research tasks are recorded.")
    if getattr(rc, "documents", []) or []:
        records_points += 2
        signals.append("Research documents are recorded.")
    else:
        gaps.append("No research documents are recorded.")
    if getattr(rc, "sources", []) or []:
        records_points += 2
        signals.append("Research sources are recorded.")
    else:
        gaps.append("No research sources are recorded.")
    score += records_points

    return IntelligenceScoreComponent(
        key="structuring",
        label="Structuring Score",
        score=min(score, 40),
        max_score=40,
        signals=signals,
        gaps=gaps,
    )


def _risk_discipline_score(rc: ResearchCase, prep_warnings: list[str]) -> IntelligenceScoreComponent:
    score = 0
    signals: list[str] = []
    gaps: list[str] = []
    disclaimer = (rc.disclaimer or "").lower()

    if "no es asesoramiento financiero" in disclaimer or "not financial advice" in disclaimer:
        score += 5
        signals.append("Financial-advice disclaimer is present.")
    else:
        gaps.append("Financial-advice disclaimer is missing or weak.")

    if not _contains_directive_language(rc):
        score += 6
        signals.append("No directive investment language detected in stored metadata.")
    else:
        gaps.append("Directive investment language was detected and needs manual cleanup.")

    human_review_items = 0
    checklist = _workspace(rc).get("checklist")
    if isinstance(checklist, list):
        human_review_items = len([
            item for item in checklist
            if isinstance(item, dict) and item.get("human_review_required") is True
        ])
    if human_review_items:
        score += 4
        signals.append("Methodology checklist preserves human-review requirements.")
    else:
        gaps.append("Human-review requirements are not visible in the checklist snapshot.")

    if rc.status != "published":
        score += 3
        signals.append("Case is not marked published.")
    else:
        gaps.append("Published status requires separate editorial controls.")

    if prep_warnings:
        score += 1
        signals.append("Preparation warnings are surfaced for manual review.")
    else:
        score += 2
        signals.append("No evaluation-prep warnings are currently surfaced.")

    return IntelligenceScoreComponent(
        key="risk_discipline",
        label="Risk Discipline Score",
        score=min(score, 20),
        max_score=20,
        signals=signals,
        gaps=gaps,
    )


def build_intelligence_score_package(rc: ResearchCase) -> IntelligenceScorePackage:
    score_rc = copy(rc)
    if not getattr(score_rc, "status", None):
        score_rc.status = "detected"

    prep = build_evaluation_prep_package(score_rc)
    evidence_package = build_research_case_evidence_links(score_rc)
    missing_link_items = prep.evidence_links_summary.get("missing_link_items", []) if prep.evidence_links_summary else []
    evidence_summary = summarize_evidence_links(
        evidence_package.links,
        missing_link_items=missing_link_items,
    ).model_dump()

    components = [
        _detection_score(score_rc, evidence_summary),
        _structuring_score(score_rc, prep.readiness.score),
        _risk_discipline_score(score_rc, prep.readiness.warnings),
    ]
    total_score = sum(component.score for component in components)
    grade, explanation = _grade(total_score)

    strengths = [signal for component in components for signal in component.signals[:2]]
    warnings = [gap for component in components for gap in component.gaps]
    suggested_next_actions = [action.label for action in prep.suggested_next_actions]
    if grade == "APPROVABLE":
        suggested_next_actions.append("Proceed to mandatory manual review of the preparation package.")

    return IntelligenceScorePackage(
        research_case_id=str(rc.id),
        total_score=total_score,
        grade=grade,
        grade_explanation=explanation,
        components=components,
        evaluation_prep_summary={
            "level": prep.readiness.level,
            "score": prep.readiness.score,
            "blocking_reasons": prep.readiness.blocking_reasons,
            "warnings": prep.readiness.warnings,
            "required_resources_total": prep.required_resources.total,
            "required_resources_missing": len(prep.required_resources.missing),
            "checklist_total": prep.checklist.total,
            "checklist_missing": len(prep.checklist.missing),
        },
        evidence_links_summary=evidence_summary,
        strengths=strengths,
        warnings=warnings,
        suggested_next_actions=suggested_next_actions,
        guardrails=[
            "Read-only score. No database writes are performed.",
            "APPROVABLE means structurally approvable for manual review, not investment approval.",
            "No investment recommendation is generated.",
            "Manual review remains mandatory.",
            "Source links remain metadata-only; no document body is fetched.",
        ],
    )
