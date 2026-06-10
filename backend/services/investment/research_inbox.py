from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.methodology_workspace import WORKSPACE_KEY


EntityType = Literal["special_situation", "research_case"]


class ResearchInboxAction(BaseModel):
    action: str
    label: str
    href: str
    method: str = "GET"
    manual_only: bool = True
    reason_required: bool = False


class ResearchInboxItem(BaseModel):
    id: str
    entity_type: EntityType
    title: str
    ticker: str | None = None
    source_context: str
    status: str
    phase: str
    candidate_only: bool
    blocker_summary: str
    created_at: str | None = None
    detected_at: str | None = None
    next_action: str
    detail_href: str
    actions: list[ResearchInboxAction] = Field(default_factory=list)


class ResearchInboxQueue(BaseModel):
    count: int
    items: list[ResearchInboxItem]
    guardrails: list[str]
    deferred_decisions: list[str]


GUARDRAILS = [
    "Research Inbox is a manual queue only.",
    "No automatic ResearchCase creation, rejection, discard, publication, or AI decision is triggered.",
    "Candidate-only items are unverified and require human review.",
]

DEFERRED_DECISIONS = [
    "Reject requires a persisted reason/audit model and remains deferred to M3B.",
    "Need-more-evidence and watchlist decisions require reasoned decision logging before a new endpoint is added.",
]


def _iso(value) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


def _evaluation(situation: SpecialSituation) -> dict:
    return situation.evaluation if isinstance(situation.evaluation, dict) else {}


def _workspace_from_situation(situation: SpecialSituation) -> dict:
    workspace = _evaluation(situation).get(WORKSPACE_KEY)
    return workspace if isinstance(workspace, dict) else {}


def _workspace_from_case(rc: ResearchCase) -> dict:
    brief = rc.brief if isinstance(rc.brief, dict) else {}
    workspace = brief.get("methodology_workspace_snapshot")
    return workspace if isinstance(workspace, dict) else {}


def _candidate_only(situation: SpecialSituation) -> bool:
    evaluation = _evaluation(situation)
    sec_detection = evaluation.get("sec_detection")
    if isinstance(sec_detection, dict) and sec_detection.get("candidate_only") is True:
        return True
    return evaluation.get("candidate_only") is True


def _missing_from_workspace(workspace: dict) -> list[str]:
    missing: list[str] = []
    for resource in workspace.get("required_resources") or []:
        if isinstance(resource, dict) and str(resource.get("status") or "missing") in {"missing", "needs_evidence"}:
            missing.append(str(resource.get("title") or resource.get("resource_id") or "Required resource"))
    for item in workspace.get("checklist") or []:
        if isinstance(item, dict) and str(item.get("status") or "missing") in {"missing", "needs_evidence"}:
            missing.append(str(item.get("title") or item.get("check_id") or "Checklist item"))
    return missing


def _blocker_summary_for_situation(situation: SpecialSituation) -> str:
    missing = _missing_from_workspace(_workspace_from_situation(situation))
    if missing:
        return f"{len(missing)} missing evidence item(s): {', '.join(missing[:3])}"
    evaluation = _evaluation(situation)
    missing_docs = evaluation.get("missing_documents")
    if isinstance(missing_docs, list) and missing_docs:
        return f"{len(missing_docs)} missing document(s) from evaluator metadata."
    return "No blocker summary available."


def _blocker_summary_for_case(rc: ResearchCase) -> str:
    open_tasks = [task for task in getattr(rc, "tasks", []) or [] if task.status == "open"]
    docs = list(getattr(rc, "documents", []) or [])
    sources = list(getattr(rc, "sources", []) or [])
    missing = _missing_from_workspace(_workspace_from_case(rc))
    if missing:
        return f"{len(missing)} missing evidence item(s): {', '.join(missing[:3])}"
    if open_tasks:
        return f"{len(open_tasks)} open research task(s)."
    if not docs:
        return "No research documents attached."
    if not sources:
        return "No research sources recorded."
    return "No blocker summary available."


def _situation_phase(situation: SpecialSituation) -> str:
    if _candidate_only(situation):
        return "candidate_only"
    workspace = _workspace_from_situation(situation)
    workflow_status = workspace.get("workflow_status") if isinstance(workspace, dict) else None
    return str(workflow_status or situation.status or "unknown")


def _case_phase(rc: ResearchCase) -> str:
    if rc.status in {"under_investigation", "brief_generated"}:
        return "in_progress"
    return str(rc.status or "unknown")


def _situation_source_context(situation: SpecialSituation) -> str:
    parts = [
        part
        for part in [
            situation.filing_type,
            "SEC" if situation.filing_url and "sec.gov" in situation.filing_url.lower() else None,
            situation.situation_type,
        ]
        if part
    ]
    return " / ".join(parts) if parts else "unknown"


def _case_source_context(rc: ResearchCase) -> str:
    parts = [
        part
        for part in [
            rc.source_origin_name,
            rc.intake_method,
            rc.connector_key,
            rc.evidence_level,
        ]
        if part
    ]
    return " / ".join(parts) if parts else "unknown"


def _situation_next_action(situation: SpecialSituation) -> tuple[str, list[ResearchInboxAction]]:
    if _candidate_only(situation):
        return "Review candidate-only filing", [
            ResearchInboxAction(
                action="open_special_situation",
                label="Open situation",
                href=f"/investment/situations/{situation.id}",
            )
        ]
    workspace = _workspace_from_situation(situation)
    if workspace.get("research_case_id"):
        rc_id = str(workspace["research_case_id"])
        return "Open existing ResearchCase", [
            ResearchInboxAction(
                action="open_research_case",
                label="Open ResearchCase",
                href=f"/investment/research/{rc_id}",
            )
        ]
    return "Manual review for promotion readiness", [
        ResearchInboxAction(
            action="promote_to_research_case",
            label="Promote manually",
            href=f"/api/investment/situations/{situation.id}/promote-to-research-case",
            method="POST",
        ),
        ResearchInboxAction(
            action="open_special_situation",
            label="Open situation",
            href=f"/investment/situations/{situation.id}",
        ),
    ]


def _case_next_action(rc: ResearchCase) -> tuple[str, list[ResearchInboxAction]]:
    if rc.status == "documented":
        label = "Open documented ResearchCase"
    elif _blocker_summary_for_case(rc) != "No blocker summary available.":
        label = "Review missing evidence"
    else:
        label = "Open ResearchCase"
    return label, [
        ResearchInboxAction(
            action="open_research_case",
            label="Open ResearchCase",
            href=f"/investment/research/{rc.id}",
        )
    ]


def build_research_inbox_queue(
    situations: list[SpecialSituation],
    research_cases: list[ResearchCase],
) -> ResearchInboxQueue:
    items: list[ResearchInboxItem] = []

    for situation in situations:
        if situation.status == "archived":
            continue
        next_action, actions = _situation_next_action(situation)
        title = situation.company_name or "Unknown company"
        items.append(
            ResearchInboxItem(
                id=str(situation.id),
                entity_type="special_situation",
                title=title,
                ticker=situation.ticker,
                source_context=_situation_source_context(situation),
                status=situation.status or "unknown",
                phase=_situation_phase(situation),
                candidate_only=_candidate_only(situation),
                blocker_summary=_blocker_summary_for_situation(situation),
                created_at=_iso(situation.created_at),
                detected_at=_iso(situation.detected_at),
                next_action=next_action,
                detail_href=f"/investment/situations/{situation.id}",
                actions=actions,
            )
        )

    for rc in research_cases:
        if rc.status == "archived":
            continue
        title = None
        brief = rc.brief if isinstance(rc.brief, dict) else {}
        if isinstance(brief.get("title"), str) and brief["title"].strip():
            title = brief["title"].strip()
        next_action, actions = _case_next_action(rc)
        items.append(
            ResearchInboxItem(
                id=str(rc.id),
                entity_type="research_case",
                title=title or f"ResearchCase {str(rc.id)[:8]}",
                ticker=None,
                source_context=_case_source_context(rc),
                status=rc.status or "unknown",
                phase=_case_phase(rc),
                candidate_only=False,
                blocker_summary=_blocker_summary_for_case(rc),
                created_at=_iso(rc.created_at),
                detected_at=None,
                next_action=next_action,
                detail_href=f"/investment/research/{rc.id}",
                actions=actions,
            )
        )

    items.sort(key=lambda item: item.detected_at or item.created_at or "", reverse=True)
    return ResearchInboxQueue(
        count=len(items),
        items=items,
        guardrails=GUARDRAILS,
        deferred_decisions=DEFERRED_DECISIONS,
    )


async def get_research_inbox_queue(db: AsyncSession) -> ResearchInboxQueue:
    situation_result = await db.execute(select(SpecialSituation).order_by(SpecialSituation.detected_at.desc()))
    rc_result = await db.execute(
        select(ResearchCase)
        .options(
            selectinload(ResearchCase.tasks),
            selectinload(ResearchCase.documents),
            selectinload(ResearchCase.sources),
        )
        .order_by(ResearchCase.updated_at.desc())
    )
    return build_research_inbox_queue(
        list(situation_result.scalars().all()),
        list(rc_result.scalars().all()),
    )
