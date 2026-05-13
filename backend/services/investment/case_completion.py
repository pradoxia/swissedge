from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

from pydantic import BaseModel

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.intelligence_score import IntelligenceScorePackage
from backend.services.investment.methodology_workspace import WORKSPACE_KEY
from backend.services.investment.research_cases import EvaluationPrepPackage


CaseType = Literal["special_situation", "research_case"]
CompletionLevel = Literal["blocked", "needs_sources", "needs_evidence_mapping", "ready_for_manual_review", "promoted"]
Severity = Literal["high", "medium", "low"]
Priority = Literal["high", "medium", "low"]


class CompletionSummary(BaseModel):
    missing_required_resources: int
    candidate_sources_to_review: int
    checklist_items_needing_evidence: int
    evidence_found_not_verified: int
    rejected_or_noisy_sources: int
    manual_review_required: bool
    research_case_exists: bool


class BlockingItem(BaseModel):
    id: str
    label: str
    reason: str
    severity: Severity
    related_section: str
    anchor: str


class ManualAction(BaseModel):
    id: str
    label: str
    description: str
    priority: Priority
    action_type: str
    manual_only: bool = True
    improves: list[str]
    target_anchor: str


class ScoreImprovementPlan(BaseModel):
    detection: list[str]
    structuring: list[str]
    risk_discipline: list[str]


class SectionStatus(BaseModel):
    section: str
    status: Literal["ok", "needs_work", "missing"]
    anchor: str


class CaseCompletionPackage(BaseModel):
    case_id: str
    case_type: CaseType
    completion_level: CompletionLevel
    completion_score: int
    summary: CompletionSummary
    blocking_items: list[BlockingItem]
    next_manual_actions: list[ManualAction]
    score_improvement_plan: ScoreImprovementPlan
    section_status: list[SectionStatus]
    guardrails: list[str]


MISSING_STATUSES = {"missing", "needs_evidence", "not_started", "open"}
EVIDENCE_STATUSES = {"evidence_found", "verified"}
GUARDRAILS = [
    "This is a manual completion checklist.",
    "No automatic evaluation is performed.",
    "No investment action is generated.",
    "Manual review remains required.",
]


def _clean_dict(value: Any) -> dict:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_list(value: Any) -> list[dict]:
    return [deepcopy(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _status(item: dict) -> str:
    return str(item.get("status") or "missing")


def _title(item: dict, fallback: str) -> str:
    return _text(item.get("title") or item.get("label") or item.get("name") or item.get("resource_id") or item.get("check_id")) or fallback


def _resource_id(item: dict) -> str:
    return _text(item.get("resource_id") or item.get("id")) or _title(item, "resource").lower().replace(" ", "_")


def _check_id(item: dict) -> str:
    return _text(item.get("check_id") or item.get("id")) or _title(item, "check").lower().replace(" ", "_")


def _workspace_from_situation(situation: SpecialSituation) -> dict:
    evaluation = _clean_dict(situation.evaluation)
    return _clean_dict(evaluation.get(WORKSPACE_KEY))


def _workspace_from_case(rc: ResearchCase) -> dict:
    brief = _clean_dict(rc.brief)
    return _clean_dict(brief.get("methodology_workspace_snapshot"))


def _sec_detection_from_situation(situation: SpecialSituation) -> dict:
    return _clean_dict(_clean_dict(situation.evaluation).get("sec_detection"))


def _detection_from_case(rc: ResearchCase) -> dict:
    return _clean_dict(_clean_dict(rc.brief).get("detection_summary"))


def _required_resources(workspace: dict) -> list[dict]:
    return _clean_list(workspace.get("required_resources"))


def _checklist(workspace: dict) -> list[dict]:
    return _clean_list(workspace.get("checklist"))


def _candidates(workspace: dict) -> list[dict]:
    return _clean_list(workspace.get("resource_candidates"))


def _suggestions(workspace: dict) -> list[dict]:
    return _clean_list(workspace.get("search_suggestions"))


def _has_sec_origin(case_type: CaseType, situation: SpecialSituation | None, rc: ResearchCase | None) -> bool:
    if case_type == "special_situation" and situation is not None:
        sec = _sec_detection_from_situation(situation)
        return bool(situation.filing_url or sec.get("filing_url") or sec.get("accession_number") or sec.get("cik"))
    if rc is not None:
        detection = _detection_from_case(rc)
        return bool(detection.get("filing_url") or detection.get("accession_number") or detection.get("cik") or rc.situation_id)
    return False


def _summary(workspace: dict, *, research_case_exists: bool) -> CompletionSummary:
    resources = _required_resources(workspace)
    checklist = _checklist(workspace)
    candidates = _candidates(workspace)
    evidence_found = [item for item in resources + checklist + candidates if _status(item) == "evidence_found"]
    return CompletionSummary(
        missing_required_resources=len([item for item in resources if _status(item) in MISSING_STATUSES]),
        candidate_sources_to_review=len([item for item in candidates if _status(item) == "candidate_found"]),
        checklist_items_needing_evidence=len([item for item in checklist if _status(item) in MISSING_STATUSES]),
        evidence_found_not_verified=len(evidence_found),
        rejected_or_noisy_sources=len([item for item in candidates if _status(item) == "rejected"]),
        manual_review_required=any(bool(item.get("human_review_required")) for item in checklist) or bool(evidence_found),
        research_case_exists=research_case_exists,
    )


def _blocking_items(workspace: dict, summary: CompletionSummary, *, has_sec_origin: bool) -> list[BlockingItem]:
    rows: list[BlockingItem] = []
    if not has_sec_origin:
        rows.append(BlockingItem(
            id="missing_sec_origin",
            label="SEC origin is incomplete",
            reason="Add or confirm SEC filing metadata before relying on the case.",
            severity="high",
            related_section="official_source_finder",
            anchor="#official-source-finder",
        ))
    for resource in _required_resources(workspace):
        if _status(resource) in MISSING_STATUSES:
            rid = _resource_id(resource)
            rows.append(BlockingItem(
                id=f"missing_resource_{rid}",
                label=_title(resource, "Missing required resource"),
                reason=f"Required resource status is {_status(resource)}.",
                severity="high",
                related_section="required_resources",
                anchor="#guide-required-resources",
            ))
    for item in _checklist(workspace):
        if _status(item) in MISSING_STATUSES:
            cid = _check_id(item)
            rows.append(BlockingItem(
                id=f"checklist_gap_{cid}",
                label=_title(item, "Checklist item needs evidence"),
                reason=f"Checklist item status is {_status(item)}.",
                severity="medium",
                related_section="checklist",
                anchor="#guide-checklist",
            ))
    if summary.candidate_sources_to_review:
        rows.append(BlockingItem(
            id="candidate_sources_need_review",
            label="Candidate sources need manual review",
            reason="Candidate sources should be reviewed, mapped, accepted as evidence_found, or rejected.",
            severity="medium",
            related_section="evidence_links",
            anchor="#guide-evidence-links",
        ))
    return rows[:12]


def _manual_actions(workspace: dict, summary: CompletionSummary, *, case_type: CaseType, has_sec_origin: bool) -> list[ManualAction]:
    actions: list[ManualAction] = []
    if not has_sec_origin:
        actions.append(ManualAction(
            id="confirm_sec_source",
            label="Add or confirm SEC source link",
            description="Confirm filing URL, form type, company, date, CIK, and accession before mapping evidence.",
            priority="high",
            action_type="open_link",
            improves=["documentation_quality", "detection_score", "manual_review_readiness"],
            target_anchor="#official-source-finder",
        ))
    for candidate in _candidates(workspace):
        if _status(candidate) != "candidate_found":
            continue
        cid = _text(candidate.get("resource_candidate_id") or candidate.get("id")) or _title(candidate, "candidate")
        actions.append(ManualAction(
            id=f"review_candidate_{cid}",
            label=f"Review candidate: {_title(candidate, 'Candidate source')}",
            description="Open manually, decide whether it supports a required resource/checklist item, then map or reject it.",
            priority="high",
            action_type="review_candidate",
            improves=["documentation_quality", "evidence_coverage", "structuring_score"],
            target_anchor="#guide-evidence-links",
        ))
    for resource in _required_resources(workspace):
        if _status(resource) in MISSING_STATUSES:
            rid = _resource_id(resource)
            actions.append(ManualAction(
                id=f"find_resource_{rid}",
                label=f"Find required resource: {_title(resource, 'Required resource')}",
                description="Use Official Source Finder and manual search suggestions to locate official evidence.",
                priority="high",
                action_type="copy_query",
                improves=["documentation_quality", "evidence_coverage", "structuring_score"],
                target_anchor="#official-source-finder",
            ))
    for item in _checklist(workspace):
        if _status(item) in MISSING_STATUSES:
            cid = _check_id(item)
            actions.append(ManualAction(
                id=f"map_checklist_{cid}",
                label=f"Map checklist evidence: {_title(item, 'Checklist item')}",
                description="Link reviewed source material to this checklist item after manual confirmation.",
                priority="medium",
                action_type="map_evidence",
                improves=["documentation_quality", "structuring_score", "manual_review_readiness"],
                target_anchor="#guide-checklist",
            ))
    if case_type == "special_situation" and not summary.research_case_exists and not actions:
        actions.append(ManualAction(
            id="manual_promotion_review",
            label="Review whether the case is ready for ResearchCase promotion",
            description="Promotion remains manual. Confirm evidence coverage and review flags before promoting.",
            priority="medium",
            action_type="manual_review",
            improves=["manual_review_readiness"],
            target_anchor="#situation-researchcase-promotion",
        ))
    if _suggestions(workspace) and not any(action.action_type == "copy_query" for action in actions):
        actions.append(ManualAction(
            id="use_manual_search_suggestions",
            label="Use stored manual search suggestions",
            description="Copy stored queries into Google, SEC search, or company IR. SwissEdge has not run them.",
            priority="medium",
            action_type="copy_query",
            improves=["documentation_quality", "evidence_coverage"],
            target_anchor="#guide-search-suggestions",
        ))
    if not actions:
        actions.append(ManualAction(
            id="manual_review_gate",
            label="Perform final manual review",
            description="Confirm evidence_found items, review assumptions, and keep manual review required where needed.",
            priority="medium",
            action_type="manual_review",
            improves=["risk_discipline_score", "manual_review_readiness"],
            target_anchor="#research-intelligence-score" if case_type == "research_case" else "#guide-checklist",
        ))
    priority_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(actions, key=lambda item: priority_order[item.priority])[:12]


def _score_plan(
    *,
    has_sec_origin: bool,
    summary: CompletionSummary,
    score: IntelligenceScorePackage | None,
    prep: EvaluationPrepPackage | None,
) -> ScoreImprovementPlan:
    detection = []
    structuring = []
    risk = []
    if not has_sec_origin:
        detection.append("Confirm SEC filing link, filing type, company, date, CIK, and accession.")
    detection.append("Keep source traceability links visible.")
    if summary.missing_required_resources:
        structuring.append("Reduce missing required resources by adding reviewed source metadata.")
    if summary.candidate_sources_to_review:
        structuring.append("Review candidate sources and map useful ones to required resources or checklist items.")
    if summary.checklist_items_needing_evidence:
        structuring.append("Map evidence_found sources to checklist items after manual review.")
    if prep and prep.readiness.blocking_reasons:
        structuring.extend(prep.readiness.blocking_reasons[:2])
    if score:
        for component in score.components:
            if component.key == "risk_discipline":
                risk.extend(component.gaps[:2])
    risk.append("Do not treat evidence_found as verified without human review.")
    risk.append("Keep manual review required for partial playbooks and uncertain evidence.")
    return ScoreImprovementPlan(
        detection=detection[:5],
        structuring=structuring[:6] or ["Confirm required resources, checklist mapping, sources, and documents are complete."],
        risk_discipline=risk[:5],
    )


def _section_status(
    *,
    has_sec_origin: bool,
    workspace: dict,
    summary: CompletionSummary,
    case_type: CaseType,
    score: IntelligenceScorePackage | None,
    prep: EvaluationPrepPackage | None,
) -> list[SectionStatus]:
    resource_total = len(_required_resources(workspace))
    checklist_total = len(_checklist(workspace))
    return [
        SectionStatus(section="SEC Origin", status="ok" if has_sec_origin else "missing", anchor="#guide-find-case"),
        SectionStatus(
            section="Required Resources",
            status="missing" if resource_total == 0 else "needs_work" if summary.missing_required_resources else "ok",
            anchor="#guide-required-resources",
        ),
        SectionStatus(
            section="Checklist Evidence",
            status="missing" if checklist_total == 0 else "needs_work" if summary.checklist_items_needing_evidence else "ok",
            anchor="#guide-checklist",
        ),
        SectionStatus(
            section="Candidate Review",
            status="needs_work" if summary.candidate_sources_to_review else "ok",
            anchor="#guide-evidence-links",
        ),
        SectionStatus(
            section="Intelligence Score",
            status="needs_work" if score and score.total_score < 90 else "ok" if score else "missing",
            anchor="#research-intelligence-score" if case_type == "research_case" else "#situation-researchcase-promotion",
        ),
        SectionStatus(
            section="Evaluation Preparation",
            status="needs_work" if prep and prep.readiness.level != "ready_for_manual_evaluation" else "ok" if prep else "missing",
            anchor="#research-evaluation-preparation" if case_type == "research_case" else "#situation-researchcase-promotion",
        ),
    ]


def _completion_score(summary: CompletionSummary, *, has_sec_origin: bool, score: IntelligenceScorePackage | None) -> int:
    points = 0
    if has_sec_origin:
        points += 20
    if summary.missing_required_resources == 0:
        points += 25
    else:
        points += max(0, 25 - summary.missing_required_resources * 7)
    if summary.checklist_items_needing_evidence == 0:
        points += 20
    else:
        points += max(0, 20 - summary.checklist_items_needing_evidence * 5)
    if summary.candidate_sources_to_review == 0:
        points += 10
    if summary.evidence_found_not_verified:
        points += 10
    if summary.research_case_exists:
        points += 10
    if score:
        points += round(min(score.total_score, 100) * 0.05)
    return max(0, min(100, points))


def _completion_level(summary: CompletionSummary, score: int, *, case_type: CaseType) -> CompletionLevel:
    if case_type == "special_situation" and summary.research_case_exists:
        return "promoted"
    if summary.missing_required_resources:
        return "needs_sources"
    if summary.candidate_sources_to_review or summary.checklist_items_needing_evidence:
        return "needs_evidence_mapping"
    if score >= 80:
        return "ready_for_manual_review"
    return "blocked"


def build_situation_completion_workbench(
    situation: SpecialSituation,
    *,
    linked_research_case: ResearchCase | None = None,
    intelligence_score: IntelligenceScorePackage | None = None,
    evaluation_prep: EvaluationPrepPackage | None = None,
) -> CaseCompletionPackage:
    workspace = _workspace_from_situation(situation)
    has_sec = _has_sec_origin("special_situation", situation, None)
    summary = _summary(workspace, research_case_exists=linked_research_case is not None)
    score = _completion_score(summary, has_sec_origin=has_sec, score=intelligence_score)
    return CaseCompletionPackage(
        case_id=str(situation.id),
        case_type="special_situation",
        completion_level=_completion_level(summary, score, case_type="special_situation"),
        completion_score=score,
        summary=summary,
        blocking_items=_blocking_items(workspace, summary, has_sec_origin=has_sec),
        next_manual_actions=_manual_actions(workspace, summary, case_type="special_situation", has_sec_origin=has_sec),
        score_improvement_plan=_score_plan(has_sec_origin=has_sec, summary=summary, score=intelligence_score, prep=evaluation_prep),
        section_status=_section_status(has_sec_origin=has_sec, workspace=workspace, summary=summary, case_type="special_situation", score=intelligence_score, prep=evaluation_prep),
        guardrails=GUARDRAILS,
    )


def build_research_case_completion_workbench(
    rc: ResearchCase,
    *,
    intelligence_score: IntelligenceScorePackage | None = None,
    evaluation_prep: EvaluationPrepPackage | None = None,
) -> CaseCompletionPackage:
    workspace = _workspace_from_case(rc)
    has_sec = _has_sec_origin("research_case", None, rc)
    summary = _summary(workspace, research_case_exists=True)
    score = _completion_score(summary, has_sec_origin=has_sec, score=intelligence_score)
    return CaseCompletionPackage(
        case_id=str(rc.id),
        case_type="research_case",
        completion_level=_completion_level(summary, score, case_type="research_case"),
        completion_score=score,
        summary=summary,
        blocking_items=_blocking_items(workspace, summary, has_sec_origin=has_sec),
        next_manual_actions=_manual_actions(workspace, summary, case_type="research_case", has_sec_origin=has_sec),
        score_improvement_plan=_score_plan(has_sec_origin=has_sec, summary=summary, score=intelligence_score, prep=evaluation_prep),
        section_status=_section_status(has_sec_origin=has_sec, workspace=workspace, summary=summary, case_type="research_case", score=intelligence_score, prep=evaluation_prep),
        guardrails=GUARDRAILS,
    )
