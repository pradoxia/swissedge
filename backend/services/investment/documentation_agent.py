from __future__ import annotations

import uuid
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.course_documentation_map import get_course_documentation_map
from backend.services.investment.document_package import (
    DocumentPackage,
    build_research_case_document_package,
    build_situation_document_package,
)
from backend.services.investment.evidence_links import (
    build_research_case_evidence_links,
    build_situation_evidence_links,
)
from backend.services.investment.promotion_readiness import (
    PromotionReadinessPackage,
    build_promotion_readiness_package,
)
from backend.services.investment.sec_document_acquisition import (
    SecDocumentAcquisitionPackage,
    build_research_case_sec_document_acquisition_preview,
    build_situation_sec_document_acquisition_preview,
)
from backend.services.investment.skill_registry import get_skill_requirements_map


DocumentationStatus = Literal[
    "blocked",
    "useful_incomplete",
    "mostly_documented",
    "ready_for_manual_review",
]


class DocumentationAgentReport(BaseModel):
    subject_type: Literal["special_situation", "research_case"]
    subject_id: str
    case_type: str
    documentation_status: DocumentationStatus
    summary: str
    course_chapters: list[dict[str, Any]] = Field(default_factory=list)
    applicable_playbooks: list[str] = Field(default_factory=list)
    checklist: list[dict[str, Any]] = Field(default_factory=list)
    documents_found: list[dict[str, Any]] = Field(default_factory=list)
    documents_missing: list[dict[str, Any]] = Field(default_factory=list)
    critical_missing_documents: list[dict[str, Any]] = Field(default_factory=list)
    required_information: list[dict[str, Any]] = Field(default_factory=list)
    required_skills: list[dict[str, Any]] = Field(default_factory=list)
    implemented_skills: list[dict[str, Any]] = Field(default_factory=list)
    missing_skills: list[dict[str, Any]] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    manual_actions: list[str] = Field(default_factory=list)
    suggested_searches: list[dict[str, Any]] = Field(default_factory=list)
    next_best_action: str
    warnings: list[str] = Field(default_factory=list)
    guardrails: dict[str, bool]


async def build_special_situation_documentation_report(
    situation_id: str | uuid.UUID,
    db: AsyncSession,
) -> DocumentationAgentReport:
    situation = await _load_situation(db, _parse_uuid(situation_id, "situation_id"))
    evidence_links = build_situation_evidence_links(situation)
    sec_preview = build_situation_sec_document_acquisition_preview(situation)
    document_package = build_situation_document_package(
        situation,
        evidence_links=evidence_links,
        sec_preview=sec_preview,
    )
    promotion = build_promotion_readiness_package(
        situation,
        document_package=document_package,
        evidence_links=evidence_links,
    )

    return _build_report(
        subject_type="special_situation",
        subject_id=str(situation.id),
        title=situation.company_name,
        situation_type=document_package.situation_type or situation.situation_type,
        document_package=document_package,
        sec_preview=sec_preview,
        promotion=promotion,
        source_search_suggestions=evidence_links.search_suggestions,
    )


async def build_research_case_documentation_report(
    research_case_id: str | uuid.UUID,
    db: AsyncSession,
) -> DocumentationAgentReport:
    rc = await _load_research_case(db, _parse_uuid(research_case_id, "research_case_id"))
    source_situation = await _load_source_situation(db, rc)
    evidence_links = build_research_case_evidence_links(rc)
    sec_preview = build_research_case_sec_document_acquisition_preview(rc, source_situation=source_situation)
    document_package = build_research_case_document_package(
        rc,
        evidence_links=evidence_links,
        sec_preview=sec_preview,
        source_situation=source_situation,
    )

    return _build_report(
        subject_type="research_case",
        subject_id=str(rc.id),
        title=_research_case_title(rc),
        situation_type=document_package.situation_type,
        document_package=document_package,
        sec_preview=sec_preview,
        promotion=None,
        source_search_suggestions=[],
    )


def _parse_uuid(value: str | uuid.UUID, field_name: str) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid {field_name}: expected UUID") from None


async def _load_situation(db: AsyncSession, situation_id: uuid.UUID) -> SpecialSituation:
    result = await db.execute(select(SpecialSituation).where(SpecialSituation.id == situation_id))
    situation = result.scalars().first()
    if not situation:
        raise HTTPException(status_code=404, detail="Situation not found")
    return situation


async def _load_research_case(db: AsyncSession, research_case_id: uuid.UUID) -> ResearchCase:
    result = await db.execute(
        select(ResearchCase)
        .where(ResearchCase.id == research_case_id)
        .options(
            selectinload(ResearchCase.documents),
            selectinload(ResearchCase.sources),
        )
    )
    rc = result.scalars().first()
    if not rc:
        raise HTTPException(status_code=404, detail="Research case not found")
    return rc


async def _load_source_situation(db: AsyncSession, rc: ResearchCase) -> SpecialSituation | None:
    if not rc.situation_id:
        return None
    result = await db.execute(select(SpecialSituation).where(SpecialSituation.id == rc.situation_id))
    return result.scalars().first()


def _build_report(
    *,
    subject_type: Literal["special_situation", "research_case"],
    subject_id: str,
    title: str,
    situation_type: str | None,
    document_package: DocumentPackage,
    sec_preview: SecDocumentAcquisitionPackage,
    promotion: PromotionReadinessPackage | None,
    source_search_suggestions: list[dict[str, Any]],
) -> DocumentationAgentReport:
    course_map = get_course_documentation_map(situation_type)
    skill_map = get_skill_requirements_map(situation_type)
    documents_found = _documents_found(document_package)
    documents_missing = _documents_missing(document_package)
    critical_missing = _critical_missing_documents(document_package)
    blocking_issues = _blocking_issues(
        document_package=document_package,
        promotion=promotion,
        critical_missing=critical_missing,
    )
    manual_actions = _manual_actions(document_package, promotion, sec_preview)
    suggested_searches = _suggested_searches(
        sec_preview=sec_preview,
        source_search_suggestions=source_search_suggestions,
        missing_documents=documents_missing,
    )
    status = _documentation_status(
        document_package=document_package,
        blocking_issues=blocking_issues,
        critical_missing=critical_missing,
    )
    next_best_action = _next_best_action(status, promotion, manual_actions, suggested_searches)

    return DocumentationAgentReport(
        subject_type=subject_type,
        subject_id=subject_id,
        case_type=course_map["situation_type"],
        documentation_status=status,
        summary=_summary(
            title=title,
            subject_type=subject_type,
            case_type=course_map["display_name"],
            status=status,
            found_count=len(documents_found),
            missing_count=len(documents_missing),
            missing_skills_count=len(skill_map["missing_skills"]),
        ),
        course_chapters=course_map["relevant_course_chapters"],
        applicable_playbooks=course_map["applicable_playbooks"],
        checklist=_checklist(course_map, document_package),
        documents_found=documents_found,
        documents_missing=documents_missing,
        critical_missing_documents=critical_missing,
        required_information=course_map["required_information"],
        required_skills=skill_map["required_skills"],
        implemented_skills=skill_map["implemented_skills"],
        missing_skills=skill_map["missing_skills"],
        blocking_issues=blocking_issues,
        manual_actions=manual_actions,
        suggested_searches=suggested_searches,
        next_best_action=next_best_action,
        warnings=_warnings(document_package, promotion, sec_preview, skill_map),
        guardrails=_guardrails(),
    )


def _research_case_title(rc: ResearchCase) -> str:
    brief = rc.brief if isinstance(rc.brief, dict) else {}
    title = brief.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return f"ResearchCase {str(rc.id)[:8]}"


def _documents_found(package: DocumentPackage) -> list[dict[str, Any]]:
    return [
        _document_row(item.model_dump())
        for item in package.documents
        if item.status == "found"
    ]


def _documents_missing(package: DocumentPackage) -> list[dict[str, Any]]:
    return [
        _document_row(item.model_dump())
        for item in package.documents
        if item.status in {"missing", "needs_manual_check", "suggested"}
    ]


def _critical_missing_documents(package: DocumentPackage) -> list[dict[str, Any]]:
    return [
        _document_row(item.model_dump())
        for item in package.documents
        if item.priority == "required" and item.status in {"missing", "needs_manual_check"}
    ]


def _document_row(item: dict[str, Any]) -> dict[str, Any]:
    status = item["status"]
    report_status = "found_metadata" if status == "found" else ("needs_manual_check" if status == "suggested" else status)
    return {
        "document_key": item["document_key"],
        "label": item["label"],
        "importance": _importance(item["priority"]),
        "priority": item["priority"],
        "source_hint": item["source_hint"],
        "status": report_status,
        "description": item["description"],
        "matched_links": item.get("matched_links", []),
        "suggested_links": item.get("suggested_links", []),
        "verified": False,
        "notes": item.get("notes"),
    }


def _importance(priority: str) -> str:
    if priority == "required":
        return "critical"
    if priority == "recommended":
        return "high"
    return "medium"


def _checklist(course_map: dict[str, Any], package: DocumentPackage) -> list[dict[str, Any]]:
    document_status = {item.document_key: item.status for item in package.documents}
    rows = []
    for item in course_map["checklist_items"]:
        required_keys = item.get("required_document_keys", [])
        statuses = [document_status.get(key) for key in required_keys]
        missing_keys = [key for key in required_keys if document_status.get(key) in {None, "missing"}]
        manual_check_keys = [key for key in required_keys if document_status.get(key) in {"suggested", "needs_manual_check"}]
        found_keys = [key for key in required_keys if document_status.get(key) == "found"]
        rows.append({
            **item,
            "status": _checklist_status(statuses),
            "missing_document_keys": missing_keys,
            "manual_check_document_keys": manual_check_keys,
            "found_document_keys": found_keys,
            "verified": False,
        })
    return rows


def _checklist_status(statuses: list[str | None]) -> str:
    if not statuses:
        return "not_applicable"
    if any(status in {None, "missing"} for status in statuses):
        return "missing"
    if any(status in {"suggested", "needs_manual_check"} for status in statuses):
        return "needs_manual_check"
    if all(status == "found" for status in statuses):
        return "found_metadata" if len(statuses) == 1 else "ready_for_manual_review"
    return "needs_manual_check"


def _blocking_issues(
    *,
    document_package: DocumentPackage,
    promotion: PromotionReadinessPackage | None,
    critical_missing: list[dict[str, Any]],
) -> list[str]:
    issues = []
    if document_package.readiness_level == "not_ready":
        issues.append("Document package is not ready.")
    if critical_missing:
        issues.append("Critical required documents are missing or need manual check.")
    if promotion:
        issues.extend(promotion.blocking_reasons)
    return list(dict.fromkeys(issues))


def _manual_actions(
    package: DocumentPackage,
    promotion: PromotionReadinessPackage | None,
    sec_preview: SecDocumentAcquisitionPackage,
) -> list[str]:
    actions = _sec_first_actions(sec_preview)
    if promotion:
        actions.extend(promotion.suggested_manual_actions)
    actions.extend(package.manual_next_actions)
    actions.extend(sec_preview.manual_next_steps[:2])
    if not actions:
        actions.append("Dani should manually review the documentation report and decide the next research step.")
    return _dedupe_actions(actions)[:10]


def _sec_first_actions(sec_preview: SecDocumentAcquisitionPackage) -> list[str]:
    url = sec_preview.available_identifiers.filing_url
    if not url:
        return []
    return [
        "Open the existing SEC filing/detail directory first and inspect exhibits for Offer to Purchase, Letter of Transmittal, and amendments.",
        f"Use the stored SEC filing/detail URL: {url}",
    ]


def _dedupe_actions(actions: list[str]) -> list[str]:
    seen = set()
    rows = []
    for action in actions:
        normalized = " ".join(action.lower().replace("find or manually confirm", "review").split())
        if normalized in seen:
            continue
        seen.add(normalized)
        rows.append(action)
    return rows


def _suggested_searches(
    *,
    sec_preview: SecDocumentAcquisitionPackage,
    source_search_suggestions: list[dict[str, Any]],
    missing_documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    searches: list[dict[str, Any]] = []
    for query in sec_preview.copyable_queries:
        searches.append(query.model_dump())
    for suggestion in source_search_suggestions:
        query = suggestion.get("query") if isinstance(suggestion, dict) else None
        if isinstance(query, str) and query.strip():
            searches.append({
                "query": query.strip(),
                "purpose": suggestion.get("purpose") or "Manual source search from stored case metadata.",
                "where_to_use": suggestion.get("where_to_use") or "Manual browser search",
                "not_executed_by_swissedge": True,
            })
    for document in missing_documents[:4]:
        searches.append({
            "query": document["label"],
            "purpose": f"Find or confirm missing document: {document['label']}.",
            "where_to_use": "SEC EDGAR or company investor relations",
            "not_executed_by_swissedge": True,
        })
    return _dedupe_searches(searches)[:10]


def _dedupe_searches(searches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    rows = []
    for search in searches:
        key = str(search.get("query") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        rows.append(search)
    return rows


def _documentation_status(
    *,
    document_package: DocumentPackage,
    blocking_issues: list[str],
    critical_missing: list[dict[str, Any]],
) -> DocumentationStatus:
    if document_package.readiness_level == "not_ready" or (
        blocking_issues and not document_package.documents
    ):
        return "blocked"
    critical_needs_manual = _critical_documents_needing_manual_check(document_package)
    if document_package.readiness_level == "ready_for_manual_evaluation" and not critical_needs_manual:
        return "ready_for_manual_review"
    if document_package.readiness_level in {"mostly_ready", "ready_for_manual_evaluation"} and not critical_missing:
        return "mostly_documented"
    return "useful_incomplete"


def _critical_documents_needing_manual_check(document_package: DocumentPackage) -> list[str]:
    return [
        item.document_key
        for item in document_package.documents
        if item.priority == "required" and item.status in {"suggested", "needs_manual_check", "missing"}
    ]


def _next_best_action(
    status: DocumentationStatus,
    promotion: PromotionReadinessPackage | None,
    manual_actions: list[str],
    suggested_searches: list[dict[str, Any]],
) -> str:
    if status == "ready_for_manual_review":
        return "Dani should manually review the found evidence and decide whether deeper research is warranted."
    sec_action = next((action for action in manual_actions if action.startswith("Open the existing SEC filing/detail directory first")), None)
    if sec_action:
        return sec_action
    if promotion and promotion.recommended_next_step:
        return promotion.recommended_next_step
    if manual_actions:
        return manual_actions[0]
    if suggested_searches:
        return f"Run a manual search for: {suggested_searches[0]['query']}."
    return "Add or confirm primary source metadata before deeper research."


def _warnings(
    package: DocumentPackage,
    promotion: PromotionReadinessPackage | None,
    sec_preview: SecDocumentAcquisitionPackage,
    skill_map: dict[str, Any],
) -> list[str]:
    warnings = []
    warnings.extend(package.warnings)
    if promotion:
        warnings.extend(promotion.warnings)
    warnings.extend(sec_preview.warnings)
    if skill_map["missing_skills"]:
        warnings.append("Some required documentation skills are not implemented yet; manual review remains necessary.")
    warnings.append("Documentation Agent v1 is deterministic metadata support, not live AI or investment advice.")
    return list(dict.fromkeys(warnings))


def _summary(
    *,
    title: str,
    subject_type: str,
    case_type: str,
    status: DocumentationStatus,
    found_count: int,
    missing_count: int,
    missing_skills_count: int,
) -> str:
    label = "SpecialSituation" if subject_type == "special_situation" else "ResearchCase"
    return (
        f"{label} '{title}' maps to {case_type}. "
        f"Documentation status is {status}; {found_count} document(s) found, "
        f"{missing_count} document(s) missing or needing manual check, "
        f"and {missing_skills_count} required skill(s) are not implemented."
    )


def _guardrails() -> dict[str, bool]:
    return {
        "read_only": True,
        "deterministic": True,
        "metadata_only": True,
        "no_scan_trigger": True,
        "no_live_ai": True,
        "no_evaluator": True,
        "no_live_create": True,
        "no_auto_promotion": True,
        "no_auto_discard": True,
        "no_auto_verification": True,
    }
