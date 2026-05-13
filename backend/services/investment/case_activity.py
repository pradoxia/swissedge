from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from backend.models.agent_ops import AgentActivity
from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.case_documentation import (
    CaseDocumentationGuidePackage,
    MissingEvidence,
)
from backend.services.investment.evidence_links import (
    ResearchCaseEvidenceLinksPackage,
    SituationEvidenceLinksPackage,
)
from backend.services.investment.intelligence_score import IntelligenceScorePackage
from backend.services.investment.methodology_workspace import WORKSPACE_KEY
from backend.services.investment.research_cases import EvaluationPrepPackage


EventType = Literal[
    "detection",
    "workspace",
    "resource_candidate",
    "search_suggestion",
    "evidence_mapping",
    "promotion",
    "research_case",
    "task",
    "source",
    "document",
    "agent_activity",
    "quality_signal",
    "current_state",
]

EventStatus = Literal[
    "info",
    "needs_attention",
    "evidence_found",
    "rejected",
    "manual_review_required",
    "completed",
]


class CaseActivityEvent(BaseModel):
    id: str
    timestamp: str | None = None
    timestamp_label: str
    event_type: EventType
    title: str
    description: str
    origin: str
    agent_key: str | None = None
    agent_name: str | None = None
    related_entity_type: str
    related_entity_id: str | None = None
    status: EventStatus
    link_url: str | None = None
    metadata_only: bool = True


class CaseActivityTimelinePackage(BaseModel):
    case_id: str
    case_type: Literal["special_situation", "research_case"]
    title: str
    events: list[CaseActivityEvent]
    summary: dict
    guardrails: list[str]


GUARDRAILS = [
    "Derived timeline only; this is not a persisted audit log yet.",
    "No autonomous agent run is triggered by this timeline.",
    "No document body has been fetched.",
    "Manual review is required before treating evidence as verified.",
]


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _timestamp_label(timestamp: str | None) -> str:
    return timestamp if timestamp else "Current state - timestamp unavailable"


def _stable_id(*parts: Any) -> str:
    raw = "|".join(str(part or "") for part in parts)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"swissedge-case-activity:{raw}"))


def _event(
    *,
    event_type: EventType,
    title: str,
    description: str,
    origin: str,
    related_entity_type: str,
    related_entity_id: str | None,
    status: EventStatus = "info",
    timestamp: str | None = None,
    agent_key: str | None = None,
    agent_name: str | None = None,
    link_url: str | None = None,
) -> CaseActivityEvent:
    return CaseActivityEvent(
        id=_stable_id(event_type, title, timestamp, related_entity_type, related_entity_id, origin),
        timestamp=timestamp,
        timestamp_label=_timestamp_label(timestamp),
        event_type=event_type,
        title=title,
        description=description,
        origin=origin,
        agent_key=agent_key,
        agent_name=agent_name,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        status=status,
        link_url=link_url,
    )


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


def _detection_from_case(rc: ResearchCase, source_situation: SpecialSituation | None) -> dict:
    detection = _brief_from_case(rc).get("detection_summary")
    if isinstance(detection, dict):
        return deepcopy(detection)
    if source_situation is None:
        return {}
    sec = _sec_detection_from_situation(source_situation)
    return {
        "company_name": source_situation.company_name,
        "filing_type": source_situation.filing_type,
        "filing_url": source_situation.filing_url,
        "detected_at": _iso(source_situation.detected_at),
        "accession_number": sec.get("accession_number"),
        "cik": sec.get("cik"),
    }


def _items(workspace: dict, key: str) -> list[dict]:
    value = workspace.get(key)
    return [deepcopy(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _title(item: dict, fallback: str) -> str:
    value = item.get("title") or item.get("label") or item.get("resource_id") or item.get("check_id") or item.get("query")
    return str(value) if value else fallback


def _status(item: dict) -> str:
    return str(item.get("status") or "missing")


def _status_to_event_status(status: str) -> EventStatus:
    if status == "rejected":
        return "rejected"
    if status in {"evidence_found", "verified"}:
        return "evidence_found"
    if status in {"missing", "needs_evidence", "not_started", "open"}:
        return "needs_attention"
    if status == "candidate_found":
        return "manual_review_required"
    return "info"


def _missing_summary(missing: MissingEvidence | None) -> str:
    if missing is None:
        return "Missing evidence summary is not available."
    total = len(missing.missing_required_resources) + len(missing.missing_checklist_items)
    if total == 0:
        return "No missing required resources or checklist gaps in the current guide."
    return f"{total} missing documentation item(s) need manual attention."


def _sort_events(events: list[CaseActivityEvent]) -> list[CaseActivityEvent]:
    timestamped = [event for event in events if event.timestamp]
    untimestamped = [event for event in events if not event.timestamp]
    timestamped.sort(key=lambda event: event.timestamp or "", reverse=True)
    return timestamped + untimestamped


def _summary(events: list[CaseActivityEvent]) -> dict:
    return {
        "total_events": len(events),
        "needs_attention": len([event for event in events if event.status in {"needs_attention", "manual_review_required"}]),
        "agent_events": len([event for event in events if event.event_type == "agent_activity"]),
        "metadata_only": True,
        "derived_only": True,
    }


def _agent_activity_events(activities: list[AgentActivity], related_type: str) -> list[CaseActivityEvent]:
    events: list[CaseActivityEvent] = []
    for activity in activities:
        agent_key = activity.agent.key if getattr(activity, "agent", None) else None
        agent_name = activity.agent.name if getattr(activity, "agent", None) else None
        status: EventStatus = "completed" if activity.status in {"completed", "success"} else "info"
        if activity.severity in {"warning", "error", "critical"}:
            status = "needs_attention"
        events.append(_event(
            event_type="agent_activity",
            title=activity.title,
            description=activity.summary or f"Agent Ops activity: {activity.activity_type}",
            origin="agent_ops",
            agent_key=agent_key,
            agent_name=agent_name,
            related_entity_type=activity.related_entity_type or related_type,
            related_entity_id=activity.related_entity_id,
            status=status,
            timestamp=_iso(activity.created_at),
        ))
    return events


def build_situation_activity_timeline(
    situation: SpecialSituation,
    *,
    evidence_links: SituationEvidenceLinksPackage | None = None,
    documentation_guide: CaseDocumentationGuidePackage | None = None,
    agent_activities: list[AgentActivity] | None = None,
) -> CaseActivityTimelinePackage:
    workspace = _workspace_from_situation(situation)
    sec = _sec_detection_from_situation(situation)
    situation_id = str(situation.id)
    filing_url = str(sec.get("filing_url") or situation.filing_url or "") or None
    filing_type = str(sec.get("detected_form_type") or situation.filing_type or "") or None
    events: list[CaseActivityEvent] = [
        _event(
            event_type="detection",
            title="SEC detection created",
            description=f"{situation.company_name} was detected from stored SEC metadata for {filing_type or 'an official filing'}.",
            origin="sec_detection",
            agent_key="sec_edgar_detector",
            agent_name="SEC EDGAR Detector",
            related_entity_type="SpecialSituation",
            related_entity_id=situation_id,
            status="completed",
            timestamp=_iso(situation.detected_at or situation.created_at),
            link_url=filing_url,
        )
    ]
    if workspace:
        events.append(_event(
            event_type="workspace",
            title="Methodology workspace attached",
            description=f"Required resources and checklist were attached using template {workspace.get('template_key') or 'unknown'}.",
            origin="methodology_workspace",
            agent_key="methodology_workspace",
            agent_name="Methodology Workspace",
            related_entity_type="SpecialSituation",
            related_entity_id=situation_id,
            status="manual_review_required" if workspace.get("requires_course_review") else "info",
            timestamp=_iso(situation.updated_at),
        ))

    for resource in _items(workspace, "required_resources"):
        status = _status(resource)
        events.append(_event(
            event_type="evidence_mapping",
            title=f"Required resource: {_title(resource, 'Required resource')}",
            description=f"Current required-resource status is {status}.",
            origin="methodology_workspace",
            agent_key="missing_evidence_hunter",
            agent_name="Missing Evidence Hunter",
            related_entity_type="SpecialSituation",
            related_entity_id=situation_id,
            status=_status_to_event_status(status),
        ))

    for item in _items(workspace, "checklist"):
        status = _status(item)
        events.append(_event(
            event_type="quality_signal",
            title=f"Checklist item: {_title(item, 'Checklist item')}",
            description=f"Checklist evidence status is {status}.",
            origin="methodology_workspace",
            agent_key="quality_sentinel" if item.get("human_review_required") else "missing_evidence_hunter",
            agent_name="Quality Sentinel" if item.get("human_review_required") else "Missing Evidence Hunter",
            related_entity_type="SpecialSituation",
            related_entity_id=situation_id,
            status="manual_review_required" if item.get("human_review_required") else _status_to_event_status(status),
        ))

    for candidate in _items(workspace, "resource_candidates"):
        status = _status(candidate)
        events.append(_event(
            event_type="resource_candidate",
            title=f"Resource candidate {status}: {_title(candidate, 'Resource candidate')}",
            description=(
                str(candidate.get("notes"))
                if candidate.get("notes")
                else f"Candidate source status is {status}; manual review is still required."
            ),
            origin=str(candidate.get("discovered_by") or "resource_scout"),
            agent_key="resource_scout",
            agent_name="Resource Scout",
            related_entity_type="SpecialSituation",
            related_entity_id=situation_id,
            status=_status_to_event_status(status),
            timestamp=_iso(candidate.get("discovered_at")),
            link_url=str(candidate.get("url")) if candidate.get("url") else None,
        ))

    for suggestion in _items(workspace, "search_suggestions"):
        events.append(_event(
            event_type="search_suggestion",
            title="Search suggestion stored",
            description=str(suggestion.get("query") or "Stored manual search query."),
            origin=str(suggestion.get("discovered_by") or "resource_scout"),
            agent_key="missing_evidence_hunter",
            agent_name="Missing Evidence Hunter",
            related_entity_type="SpecialSituation",
            related_entity_id=situation_id,
            status="info",
            timestamp=_iso(suggestion.get("created_at")),
        ))

    if workspace.get("research_case_id"):
        events.append(_event(
            event_type="promotion",
            title="ResearchCase linked",
            description="This SpecialSituation has been manually promoted or linked to a ResearchCase.",
            origin="manual_review",
            agent_key="case_builder",
            agent_name="Case Builder",
            related_entity_type="ResearchCase",
            related_entity_id=str(workspace.get("research_case_id")),
            status="completed",
        ))

    if evidence_links is not None:
        events.append(_event(
            event_type="quality_signal",
            title="Evidence Links package available",
            description=f"{len(evidence_links.links)} metadata-only traceability link(s) are available.",
            origin="derived",
            agent_key="evidence_mapper",
            agent_name="Evidence Mapper",
            related_entity_type="SpecialSituation",
            related_entity_id=situation_id,
            status="info" if evidence_links.links else "needs_attention",
        ))

    if documentation_guide is not None:
        events.append(_event(
            event_type="quality_signal",
            title="Case Documentation Guide available",
            description=(
                f"Documentation quality is {documentation_guide.documentation_quality.level} "
                f"({documentation_guide.documentation_quality.score}/100). "
                f"{_missing_summary(documentation_guide.missing_evidence)}"
            ),
            origin="derived",
            agent_key="missing_evidence_hunter",
            agent_name="Missing Evidence Hunter",
            related_entity_type="SpecialSituation",
            related_entity_id=situation_id,
            status="needs_attention" if documentation_guide.documentation_quality.level != "good" else "info",
        ))

    events.extend(_agent_activity_events(agent_activities or [], "SpecialSituation"))
    events = _sort_events(events)
    return CaseActivityTimelinePackage(
        case_id=situation_id,
        case_type="special_situation",
        title=situation.company_name,
        events=events,
        summary=_summary(events),
        guardrails=GUARDRAILS,
    )


def build_research_case_activity_timeline(
    rc: ResearchCase,
    *,
    evidence_links: ResearchCaseEvidenceLinksPackage | None = None,
    evaluation_prep: EvaluationPrepPackage | None = None,
    intelligence_score: IntelligenceScorePackage | None = None,
    documentation_guide: CaseDocumentationGuidePackage | None = None,
    source_situation: SpecialSituation | None = None,
    agent_activities: list[AgentActivity] | None = None,
) -> CaseActivityTimelinePackage:
    rc_id = str(rc.id)
    workspace = _workspace_from_case(rc)
    detection = _detection_from_case(rc, source_situation)
    title = str(_brief_from_case(rc).get("title") or detection.get("company_name") or f"ResearchCase {rc_id[:8]}")
    events: list[CaseActivityEvent] = [
        _event(
            event_type="research_case",
            title="ResearchCase created",
            description=f"ResearchCase entered the private research desk from {rc.intake_method or rc.source_origin_name or 'stored metadata'}.",
            origin="research_case",
            agent_key="case_builder",
            agent_name="Case Builder",
            related_entity_type="ResearchCase",
            related_entity_id=rc_id,
            status="completed",
            timestamp=_iso(rc.created_at),
        ),
        _event(
            event_type="research_case",
            title="ResearchCase updated",
            description=f"Current ResearchCase status is {rc.status}.",
            origin="research_case",
            agent_key="case_builder",
            agent_name="Case Builder",
            related_entity_type="ResearchCase",
            related_entity_id=rc_id,
            status="info",
            timestamp=_iso(rc.updated_at),
        ),
    ]
    if rc.situation_id:
        events.append(_event(
            event_type="promotion",
            title="Linked SpecialSituation context",
            description="This ResearchCase keeps a link back to the original SpecialSituation.",
            origin="manual_review",
            agent_key="case_builder",
            agent_name="Case Builder",
            related_entity_type="SpecialSituation",
            related_entity_id=str(rc.situation_id),
            status="completed",
            timestamp=_iso(detection.get("detected_at")),
            link_url=detection.get("filing_url") if isinstance(detection.get("filing_url"), str) else None,
        ))

    for task in getattr(rc, "tasks", []) or []:
        status = "completed" if task.status == "done" else "needs_attention" if task.status == "open" else "info"
        events.append(_event(
            event_type="task",
            title=f"Research task {task.status}: {task.description}",
            description=task.notes or f"Task priority {task.priority}; source {task.source or 'manual research plan'}.",
            origin="research_case",
            agent_key="missing_evidence_hunter",
            agent_name="Missing Evidence Hunter",
            related_entity_type="ResearchTask",
            related_entity_id=str(task.id) if task.id else None,
            status=status,
            timestamp=_iso(task.resolved_at or task.created_at),
        ))

    for source in getattr(rc, "sources", []) or []:
        events.append(_event(
            event_type="source",
            title=f"Research source added: {source.source_name}",
            description=f"Signal quality: {source.signal_quality}. Source URL is metadata-only.",
            origin="research_case",
            agent_key="source_intelligence",
            agent_name="Source Intelligence",
            related_entity_type="ResearchSource",
            related_entity_id=str(source.id) if source.id else None,
            status="info",
            timestamp=_iso(source.created_at),
            link_url=source.source_url,
        ))

    for document in getattr(rc, "documents", []) or []:
        events.append(_event(
            event_type="document",
            title=f"Research document added: {document.title or document.doc_type or 'Document'}",
            description=f"Document type: {document.doc_type or 'unknown'}. URL is metadata-only.",
            origin="research_case",
            agent_key="evidence_mapper",
            agent_name="Evidence Mapper",
            related_entity_type="ResearchDocument",
            related_entity_id=str(document.id) if document.id else None,
            status="info",
            timestamp=_iso(document.created_at),
            link_url=document.url,
        ))

    for resource in _items(workspace, "required_resources"):
        status = _status(resource)
        events.append(_event(
            event_type="evidence_mapping",
            title=f"Required resource snapshot: {_title(resource, 'Required resource')}",
            description=f"Promoted workspace snapshot status is {status}.",
            origin="research_case",
            agent_key="missing_evidence_hunter",
            agent_name="Missing Evidence Hunter",
            related_entity_type="ResearchCase",
            related_entity_id=rc_id,
            status=_status_to_event_status(status),
        ))

    if evidence_links is not None:
        events.append(_event(
            event_type="quality_signal",
            title="Evidence Links package available",
            description=f"{len(evidence_links.links)} metadata-only traceability link(s) are available.",
            origin="derived",
            agent_key="evidence_mapper",
            agent_name="Evidence Mapper",
            related_entity_type="ResearchCase",
            related_entity_id=rc_id,
            status="info" if evidence_links.links else "needs_attention",
        ))
    if evaluation_prep is not None:
        events.append(_event(
            event_type="quality_signal",
            title="Evaluation Preparation available",
            description=f"Preparation level is {evaluation_prep.readiness.level} with score {evaluation_prep.readiness.score}/100.",
            origin="derived",
            agent_key="evaluation_prep_assistant",
            agent_name="Evaluation Prep Assistant",
            related_entity_type="ResearchCase",
            related_entity_id=rc_id,
            status="needs_attention" if evaluation_prep.readiness.blocking_reasons else "info",
        ))
    if intelligence_score is not None:
        events.append(_event(
            event_type="quality_signal",
            title="Intelligence Score available",
            description=f"IA Score is {intelligence_score.total_score}/100 with grade {intelligence_score.grade}.",
            origin="derived",
            agent_key="intelligence_scorer",
            agent_name="Intelligence Scorer",
            related_entity_type="ResearchCase",
            related_entity_id=rc_id,
            status="info",
        ))
    if documentation_guide is not None:
        events.append(_event(
            event_type="quality_signal",
            title="Case Documentation Guide available",
            description=(
                f"Documentation quality is {documentation_guide.documentation_quality.level} "
                f"({documentation_guide.documentation_quality.score}/100). "
                f"{_missing_summary(documentation_guide.missing_evidence)}"
            ),
            origin="derived",
            agent_key="missing_evidence_hunter",
            agent_name="Missing Evidence Hunter",
            related_entity_type="ResearchCase",
            related_entity_id=rc_id,
            status="needs_attention" if documentation_guide.documentation_quality.level != "good" else "info",
        ))

    events.extend(_agent_activity_events(agent_activities or [], "ResearchCase"))
    events = _sort_events(events)
    return CaseActivityTimelinePackage(
        case_id=rc_id,
        case_type="research_case",
        title=title,
        events=events,
        summary=_summary(events),
        guardrails=GUARDRAILS,
    )
