from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.evidence_links import (
    ResearchCaseEvidenceLinksPackage,
    SituationEvidenceLinksPackage,
)
from backend.services.investment.intelligence_score import IntelligenceScorePackage
from backend.services.investment.methodology_workspace import WORKSPACE_KEY
from backend.services.investment.research_cases import EvaluationPrepPackage


QualityLevel = Literal[
    "good",
    "needs_links",
    "needs_required_resources",
    "needs_evidence_mapping",
    "needs_manual_review",
]


class DocumentationCheck(BaseModel):
    label: str
    status: Literal["ok", "needs_work"]


class DocumentationQuality(BaseModel):
    level: QualityLevel
    score: int
    summary: str
    checks: list[DocumentationCheck]


class DetectionGuide(BaseModel):
    source: str
    company_name: str | None = None
    ticker: str | None = None
    cik: str | None = None
    accession_number: str | None = None
    filing_type: str | None = None
    filing_date: str | None = None
    detected_at: str | None = None
    situation_type: str | None = None
    selected_playbook: str | None = None
    detection_confidence: str | None = None
    filing_url: str | None = None
    manual_verification_steps: list[str]


class MissingEvidence(BaseModel):
    missing_required_resources: list[dict]
    missing_checklist_items: list[dict]
    candidate_only_resources: list[dict]
    evidence_found_not_verified: list[dict]
    rejected_resources: list[dict]


class ResearchAgentGuide(BaseModel):
    agent_name: str
    agent_key: str
    mode: str
    current_mission: str
    last_activity: str | None
    next_manual_actions: list[str]
    future_scheduler_note: str


class SearchPlan(BaseModel):
    stored_search_suggestions: list[dict]
    manual_search_steps: list[str]
    copyable_queries: list[str]


class QuickLink(BaseModel):
    label: str
    url: str
    source_type: str
    metadata_only: bool = True


class TimelineEvent(BaseModel):
    label: str
    timestamp: str | None = None
    detail: str | None = None
    derived: bool = True


class CaseDocumentationGuidePackage(BaseModel):
    case_id: str
    case_type: Literal["special_situation", "research_case"]
    title: str
    documentation_quality: DocumentationQuality
    detection_guide: DetectionGuide
    missing_evidence: MissingEvidence
    research_agent: ResearchAgentGuide
    search_plan: SearchPlan
    quick_links: list[QuickLink]
    activity_timeline: list[TimelineEvent]
    guardrails: list[str]


GUARDRAILS = [
    "Detection does not mean evaluated.",
    "Source candidate does not mean verified.",
    "Evidence found does not mean verified.",
    "Manual review is required.",
    "No document body has been fetched.",
    "No autonomous agent run has occurred in this sprint.",
]


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _clean_dict(item: dict) -> dict:
    return deepcopy(item)


def _evaluation_from_situation(situation: SpecialSituation) -> dict:
    return situation.evaluation if isinstance(situation.evaluation, dict) else {}


def _workspace_from_situation(situation: SpecialSituation) -> dict:
    workspace = _evaluation_from_situation(situation).get(WORKSPACE_KEY)
    return workspace if isinstance(workspace, dict) else {}


def _sec_detection_from_situation(situation: SpecialSituation) -> dict:
    sec_detection = _evaluation_from_situation(situation).get("sec_detection")
    return sec_detection if isinstance(sec_detection, dict) else {}


def _brief_from_case(rc: ResearchCase) -> dict:
    return rc.brief if isinstance(rc.brief, dict) else {}


def _workspace_from_case(rc: ResearchCase) -> dict:
    workspace = _brief_from_case(rc).get("methodology_workspace_snapshot")
    return workspace if isinstance(workspace, dict) else {}


def _detection_from_case(rc: ResearchCase, situation: SpecialSituation | None) -> dict:
    detection = _brief_from_case(rc).get("detection_summary")
    if isinstance(detection, dict):
        return deepcopy(detection)
    if situation is not None:
        sec = _sec_detection_from_situation(situation)
        return {
            "company_name": situation.company_name,
            "ticker": situation.ticker,
            "situation_type": situation.situation_type,
            "filing_type": situation.filing_type,
            "filing_url": situation.filing_url,
            "detected_at": _iso(situation.detected_at),
            "accession_number": sec.get("accession_number"),
            "cik": sec.get("cik"),
            "filing_date": sec.get("filing_date"),
            "selected_playbook": sec.get("selected_playbook"),
            "detection_confidence": sec.get("detection_confidence"),
        }
    return {}


def _required_resources(workspace: dict) -> list[dict]:
    items = workspace.get("required_resources")
    return [_clean_dict(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _checklist(workspace: dict) -> list[dict]:
    items = workspace.get("checklist")
    return [_clean_dict(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _resource_candidates(workspace: dict) -> list[dict]:
    items = workspace.get("resource_candidates")
    return [_clean_dict(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _search_suggestions(workspace: dict) -> list[dict]:
    items = workspace.get("search_suggestions")
    return [_clean_dict(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _status(item: dict) -> str:
    return str(item.get("status") or "missing")


def _title(item: dict, fallback: str) -> str:
    value = item.get("title") or item.get("label") or item.get("resource_id") or item.get("check_id")
    return str(value) if value else fallback


def _missing_evidence(workspace: dict) -> MissingEvidence:
    resources = _required_resources(workspace)
    checks = _checklist(workspace)
    candidates = _resource_candidates(workspace)
    return MissingEvidence(
        missing_required_resources=[item for item in resources if _status(item) in {"missing", "needs_evidence", "not_started"}],
        missing_checklist_items=[item for item in checks if _status(item) in {"missing", "needs_evidence", "not_started", "open"}],
        candidate_only_resources=[item for item in candidates if _status(item) == "candidate_found"],
        evidence_found_not_verified=[item for item in candidates + resources + checks if _status(item) == "evidence_found"],
        rejected_resources=[item for item in candidates + resources if _status(item) == "rejected"],
    )


def _quick_links_from_situation(
    situation: SpecialSituation,
    evidence_links: SituationEvidenceLinksPackage,
) -> list[QuickLink]:
    links: list[QuickLink] = []
    if situation.filing_url:
        links.append(QuickLink(label="Stored SEC filing", url=situation.filing_url, source_type="sec_filing"))
    for link in evidence_links.links:
        if link.url and not any(existing.url == link.url for existing in links):
            links.append(QuickLink(label=link.label, url=link.url, source_type=link.source_type))
    return links[:10]


def _quick_links_from_case(
    rc: ResearchCase,
    evidence_links: ResearchCaseEvidenceLinksPackage,
) -> list[QuickLink]:
    links: list[QuickLink] = []
    for link in evidence_links.links:
        if link.url and not any(existing.url == link.url for existing in links):
            links.append(QuickLink(label=link.label, url=link.url, source_type=link.source_type))
    for source in getattr(rc, "sources", []) or []:
        if source.source_url and not any(existing.url == source.source_url for existing in links):
            links.append(QuickLink(label=source.source_name, url=source.source_url, source_type="research_source"))
    for document in getattr(rc, "documents", []) or []:
        if document.url and not any(existing.url == document.url for existing in links):
            links.append(QuickLink(label=document.title or document.doc_type or "Research document", url=document.url, source_type="research_document"))
    return links[:10]


def _manual_verification_steps(detection: dict, filing_url: str | None) -> list[str]:
    steps = [
        "Confirm the company, ticker, form type, filing date, CIK, and accession number against the stored SEC metadata.",
        "Open the stored SEC filing link manually if present and verify that it matches this case.",
        "Compare the filing type and event language with the selected playbook.",
        "Record the primary transaction or offer materials as metadata links only.",
        "Map every accepted source to a required resource or checklist item before deeper review.",
    ]
    if not filing_url:
        steps.insert(1, "Find the filing manually from the stored CIK/accession metadata because no filing URL is stored.")
    if not detection.get("accession_number") and not detection.get("cik"):
        steps.append("Add or confirm SEC identifiers before relying on the detection trail.")
    return steps


def _quality(
    *,
    sec_metadata_present: bool,
    filing_url_present: bool,
    required_resources: list[dict],
    candidates: list[dict],
    checklist: list[dict],
    evidence_links_count: int,
    search_suggestions_count: int,
    research_case_present: bool,
    human_review_visible: bool,
) -> DocumentationQuality:
    score = 0
    checks: list[DocumentationCheck] = []

    def add(label: str, points: int, ok: bool) -> None:
        nonlocal score
        if ok:
            score += points
        checks.append(DocumentationCheck(label=label, status="ok" if ok else "needs_work"))

    add("SEC origin present", 20, sec_metadata_present)
    add("Filing URL present", 15, filing_url_present)
    add("Required resources mapped", 15, bool(required_resources))
    add("Resource candidates or evidence present", 15, bool(candidates))
    add("Checklist present", 10, bool(checklist))
    add("Evidence links present", 10, evidence_links_count > 0)
    add("Search suggestions present", 5, search_suggestions_count > 0)
    add("ResearchCase connection present", 5, research_case_present)
    add("Human review flags visible", 5, human_review_visible)

    score = max(0, min(100, score))
    if score >= 80:
        level: QualityLevel = "good"
    elif score >= 50:
        level = "needs_evidence_mapping"
    elif score >= 25:
        level = "needs_required_resources"
    else:
        level = "needs_links"
    if not filing_url_present and level == "good":
        level = "needs_evidence_mapping"
    if human_review_visible and level == "good":
        summary = "Documentation is strong enough for manual review planning. This is not an evaluation."
    else:
        summary = "Documentation needs more source links, resource mapping, or checklist evidence before deeper manual review."
    return DocumentationQuality(level=level, score=score, summary=summary, checks=checks)


def _search_plan(suggestions: list[dict], detection: dict) -> SearchPlan:
    queries = [
        str(item.get("query"))
        for item in suggestions
        if isinstance(item.get("query"), str) and item.get("query")
    ]
    company = detection.get("company_name")
    filing = detection.get("filing_type") or detection.get("detected_form_type")
    if isinstance(company, str) and company and isinstance(filing, str) and filing:
        queries.append(f'"{company}" "{filing}"')
    return SearchPlan(
        stored_search_suggestions=suggestions,
        manual_search_steps=[
            "Copy a stored query and run it manually in the browser.",
            "Prefer official company, SEC, exchange, or transaction pages.",
            "Paste useful source URLs into the case as metadata links.",
            "Mark candidate resources only after Dani manually reviews the link target.",
        ],
        copyable_queries=list(dict.fromkeys(queries))[:10],
    )


def _agent_guide(missing: MissingEvidence, timeline: list[TimelineEvent]) -> ResearchAgentGuide:
    actions: list[str] = []
    if missing.missing_required_resources:
        actions.append(f"Collect metadata links for {len(missing.missing_required_resources)} missing required resource(s).")
    if missing.missing_checklist_items:
        actions.append(f"Map evidence for {len(missing.missing_checklist_items)} checklist gap(s).")
    if missing.candidate_only_resources:
        actions.append(f"Review {len(missing.candidate_only_resources)} candidate resource(s) and mark accepted evidence only after manual inspection.")
    if missing.evidence_found_not_verified:
        actions.append(f"Manually verify {len(missing.evidence_found_not_verified)} evidence-found item(s).")
    if not actions:
        actions.append("Review current documentation and keep adding source metadata when new primary materials appear.")
    return ResearchAgentGuide(
        agent_name="Missing Evidence Hunter",
        agent_key="missing_evidence_hunter",
        mode="manual_observer",
        current_mission="Turn stored detection metadata into a clear manual research plan with missing evidence called out.",
        last_activity=next((event.timestamp for event in timeline if event.timestamp), None),
        next_manual_actions=actions,
        future_scheduler_note="Frequent missing-evidence checks are planned for a future approved sprint. No cron is active in this sprint.",
    )


def _sort_timeline(rows: list[TimelineEvent]) -> list[TimelineEvent]:
    dated = [row for row in rows if row.timestamp]
    undated = [row for row in rows if not row.timestamp]
    dated.sort(key=lambda row: row.timestamp or "", reverse=True)
    return (dated + undated)[:20]


def _situation_timeline(
    situation: SpecialSituation,
    workspace: dict,
    evidence_links_count: int,
) -> list[TimelineEvent]:
    rows = [
        TimelineEvent(label="Detection created", timestamp=_iso(situation.detected_at), detail=situation.filing_type),
        TimelineEvent(label="Methodology workspace attached", timestamp=_iso(situation.updated_at), detail=workspace.get("template_key") if workspace else None),
    ]
    for candidate in _resource_candidates(workspace):
        rows.append(TimelineEvent(
            label=f"Resource candidate {_status(candidate)}",
            timestamp=_iso(candidate.get("discovered_at")),
            detail=_title(candidate, "Resource candidate"),
        ))
    for suggestion in _search_suggestions(workspace):
        rows.append(TimelineEvent(
            label="Search suggestion created",
            timestamp=_iso(suggestion.get("created_at")),
            detail=str(suggestion.get("query") or ""),
        ))
    if evidence_links_count:
        rows.append(TimelineEvent(label="Evidence links available", detail=f"{evidence_links_count} metadata link(s)"))
    if workspace.get("research_case_id"):
        rows.append(TimelineEvent(label="ResearchCase connected", detail=str(workspace.get("research_case_id"))))
    if not any(row.timestamp for row in rows):
        rows.append(TimelineEvent(label="Current state - timestamp unavailable", detail="Derived from stored case metadata."))
    return _sort_timeline(rows)


def _case_timeline(
    rc: ResearchCase,
    detection: dict,
    evidence_links_count: int,
    prep: EvaluationPrepPackage | None,
    score: IntelligenceScorePackage | None,
) -> list[TimelineEvent]:
    rows = [
        TimelineEvent(label="ResearchCase created", timestamp=_iso(rc.created_at), detail=rc.intake_method),
        TimelineEvent(label="ResearchCase updated", timestamp=_iso(rc.updated_at), detail=rc.status),
    ]
    if detection:
        rows.append(TimelineEvent(label="Original detection snapshot available", timestamp=_iso(detection.get("detected_at")), detail=detection.get("filing_type")))
    for source in getattr(rc, "sources", []) or []:
        rows.append(TimelineEvent(label="ResearchCase source added", timestamp=_iso(source.created_at), detail=source.source_name))
    for document in getattr(rc, "documents", []) or []:
        rows.append(TimelineEvent(label="ResearchCase document added", timestamp=_iso(document.created_at), detail=document.title or document.doc_type))
    for task in getattr(rc, "tasks", []) or []:
        rows.append(TimelineEvent(label=f"ResearchCase task {task.status}", timestamp=_iso(task.created_at), detail=task.description))
    if evidence_links_count:
        rows.append(TimelineEvent(label="Evidence links available", detail=f"{evidence_links_count} metadata link(s)"))
    if prep is not None:
        rows.append(TimelineEvent(label="Evaluation Preparation available", detail=prep.readiness.level))
    if score is not None:
        rows.append(TimelineEvent(label="Intelligence Score available", detail=f"{score.total_score}/100"))
    if not any(row.timestamp for row in rows):
        rows.append(TimelineEvent(label="Current state - timestamp unavailable", detail="Derived from stored ResearchCase metadata."))
    return _sort_timeline(rows)


def build_situation_documentation_guide(
    situation: SpecialSituation,
    evidence_links: SituationEvidenceLinksPackage,
) -> CaseDocumentationGuidePackage:
    workspace = _workspace_from_situation(situation)
    sec = _sec_detection_from_situation(situation)
    filing_url = str(sec.get("filing_url") or situation.filing_url or "") or None
    filing_type = str(sec.get("detected_form_type") or sec.get("filing_type") or situation.filing_type or "") or None
    detection = {
        "company_name": situation.company_name,
        "ticker": situation.ticker,
        "situation_type": sec.get("situation_type") or situation.situation_type,
        "filing_type": filing_type,
        "filing_url": filing_url,
        "detected_at": _iso(situation.detected_at),
        "accession_number": sec.get("accession_number"),
        "cik": sec.get("cik"),
        "filing_date": sec.get("filing_date"),
        "selected_playbook": sec.get("selected_playbook") or workspace.get("template_key"),
        "detection_confidence": sec.get("detection_confidence"),
    }
    missing = _missing_evidence(workspace)
    timeline = _situation_timeline(situation, workspace, len(evidence_links.links))
    suggestions = _search_suggestions(workspace)
    resources = _required_resources(workspace)
    checks = _checklist(workspace)
    candidates = _resource_candidates(workspace)
    quality = _quality(
        sec_metadata_present=bool(sec or situation.filing_type),
        filing_url_present=bool(filing_url),
        required_resources=resources,
        candidates=candidates,
        checklist=checks,
        evidence_links_count=len(evidence_links.links),
        search_suggestions_count=len(suggestions),
        research_case_present=bool(workspace.get("research_case_id")),
        human_review_visible=any(item.get("human_review_required") is True for item in checks),
    )
    return CaseDocumentationGuidePackage(
        case_id=str(situation.id),
        case_type="special_situation",
        title=situation.company_name,
        documentation_quality=quality,
        detection_guide=DetectionGuide(
            source="SEC EDGAR" if sec or filing_url else "Stored case metadata",
            company_name=situation.company_name,
            ticker=situation.ticker,
            cik=sec.get("cik"),
            accession_number=sec.get("accession_number"),
            filing_type=filing_type,
            filing_date=sec.get("filing_date"),
            detected_at=_iso(situation.detected_at),
            situation_type=detection["situation_type"],
            selected_playbook=detection["selected_playbook"],
            detection_confidence=sec.get("detection_confidence"),
            filing_url=filing_url,
            manual_verification_steps=_manual_verification_steps(detection, filing_url),
        ),
        missing_evidence=missing,
        research_agent=_agent_guide(missing, timeline),
        search_plan=_search_plan(suggestions, detection),
        quick_links=_quick_links_from_situation(situation, evidence_links),
        activity_timeline=timeline,
        guardrails=GUARDRAILS,
    )


def build_research_case_documentation_guide(
    rc: ResearchCase,
    *,
    evidence_links: ResearchCaseEvidenceLinksPackage,
    evaluation_prep: EvaluationPrepPackage | None = None,
    intelligence_score: IntelligenceScorePackage | None = None,
    source_situation: SpecialSituation | None = None,
) -> CaseDocumentationGuidePackage:
    workspace = _workspace_from_case(rc)
    detection = _detection_from_case(rc, source_situation)
    filing_url = str(detection.get("filing_url") or "") or None
    suggestions = _search_suggestions(workspace)
    missing = _missing_evidence(workspace)
    timeline = _case_timeline(rc, detection, len(evidence_links.links), evaluation_prep, intelligence_score)
    resources = _required_resources(workspace)
    checks = _checklist(workspace)
    candidates = _resource_candidates(workspace)
    title = str(_brief_from_case(rc).get("title") or detection.get("company_name") or f"ResearchCase {str(rc.id)[:8]}")
    quality = _quality(
        sec_metadata_present=bool(detection.get("accession_number") or detection.get("cik") or detection.get("filing_type")),
        filing_url_present=bool(filing_url),
        required_resources=resources,
        candidates=candidates,
        checklist=checks,
        evidence_links_count=len(evidence_links.links),
        search_suggestions_count=len(suggestions),
        research_case_present=True,
        human_review_visible=any(item.get("human_review_required") is True for item in checks),
    )
    if evaluation_prep is not None and evaluation_prep.readiness.blocking_reasons:
        quality.summary = f"{quality.summary} Evaluation Preparation reports blocking documentation gaps."
    return CaseDocumentationGuidePackage(
        case_id=str(rc.id),
        case_type="research_case",
        title=title,
        documentation_quality=quality,
        detection_guide=DetectionGuide(
            source="SpecialSituation promotion" if rc.situation_id else (rc.source_origin_name or "ResearchCase metadata"),
            company_name=detection.get("company_name"),
            ticker=detection.get("ticker"),
            cik=detection.get("cik"),
            accession_number=detection.get("accession_number"),
            filing_type=detection.get("filing_type") or detection.get("detected_form_type"),
            filing_date=detection.get("filing_date"),
            detected_at=detection.get("detected_at"),
            situation_type=detection.get("situation_type"),
            selected_playbook=detection.get("selected_playbook") or rc.playbook_used,
            detection_confidence=detection.get("detection_confidence"),
            filing_url=filing_url,
            manual_verification_steps=_manual_verification_steps(detection, filing_url),
        ),
        missing_evidence=missing,
        research_agent=_agent_guide(missing, timeline),
        search_plan=_search_plan(suggestions, detection),
        quick_links=_quick_links_from_case(rc, evidence_links),
        activity_timeline=timeline,
        guardrails=GUARDRAILS,
    )
