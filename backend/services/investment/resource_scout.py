from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from backend.models.investment import SpecialSituation
from backend.services.investment.methodology_workspace import (
    ALLOWED_CHECKLIST_STATUSES,
    ALLOWED_REQUIRED_RESOURCE_STATUSES,
    ALLOWED_WORKFLOW_STATUSES,
    WORKSPACE_KEY,
    attach_methodology_workspace_to_evidence,
    calculate_workspace_progress,
    recalculate_methodology_progress,
)


DISCOVERED_BY = "resource_scout_v1"
VALID_SOURCE_TYPES = {
    "sec_filing",
    "company_ir",
    "press_release",
    "transaction_page",
    "offer_document",
    "pdf_link",
    "news",
    "market_data_reference",
    "other",
}
VALID_RESOURCE_REVIEW_STATUSES = {
    "candidate_found",
    "evidence_found",
    "rejected",
    "human_review_required",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _validate_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must be an absolute http/https URL")


def _title_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower() or "Manual resource"


def _candidate_id(situation_id: str, url: str, title: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"swissedge-resource:{situation_id}:{url}:{title}"))


def _resource_map_for_form(filing_type: str | None) -> list[str]:
    form = (filing_type or "").upper()
    if "SC TO-T" in form:
        return ["ma_sc_to_t"]
    if "SC TO-I" in form:
        return ["st_sc_to_i"]
    if "FORM 10" in form or form == "10":
        return ["so_form_10"]
    if "8-K" in form:
        return ["liq_8k"]
    return []


def _query_suggestions(company_name: str, ticker: str | None, filing_type: str | None, workspace: dict[str, Any]) -> list[dict[str, Any]]:
    company = f'"{company_name}"'
    ticker_part = f" {ticker}" if ticker else ""
    form = (filing_type or "").upper()
    base = [
        ("company_ir", f"{company}{ticker_part} investor relations"),
        ("press_release", f"{company} press release {filing_type or ''}".strip()),
    ]
    if "SC TO-T" in form:
        base.extend([
            ("offer_document", f"{company} offer to purchase SC TO-T"),
            ("merger_agreement", f"{company} merger agreement tender offer"),
            ("sc_14d9", f"{company} SC 14D9"),
            ("transaction_page", f"{company} tender offer transaction page"),
        ])
    elif "SC TO-I" in form:
        base.extend([
            ("offer_document", f"{company} offer to purchase SC TO-I"),
            ("letter_transmittal", f"{company} letter of transmittal self tender"),
            ("source_funds", f"{company} self tender source of funds"),
        ])
    elif "FORM 10" in form or form == "10":
        base.extend([
            ("form_10_amendments", f"{company} Form 10 amendment spin-off"),
            ("information_statement", f"{company} spin-off information statement"),
            ("parent_release", f"{company} spin-off press release distribution ratio"),
        ])
    elif "8-K" in form:
        base.extend([
            ("liquidation_plan", f"{company} plan of liquidation dissolution"),
            ("liquidation_release", f"{company} liquidation press release"),
            ("liquidation_amendments", f"{company} liquidation dissolution 8-K amendment"),
        ])

    existing = {
        item.get("query")
        for item in workspace.get("search_suggestions", [])
        if isinstance(item, dict)
    }
    suggestions = []
    for suggestion_type, query in base:
        if query in existing:
            continue
        suggestions.append({
            "suggestion_id": str(uuid5(NAMESPACE_URL, f"swissedge-search:{company_name}:{query}")),
            "query": query,
            "suggestion_type": suggestion_type,
            "status": "suggested",
            "discovered_by": DISCOVERED_BY,
            "created_at": _utc_now(),
        })
    return suggestions


def _sec_archive_directory(cik: str | None, accession: str | None) -> str | None:
    if not cik or not accession:
        return None
    return f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession.replace('-', '')}/"


def _candidate(
    *,
    situation_id: str,
    title: str,
    url: str,
    source_type: str,
    confidence: str,
    related_resource_ids: list[str],
    related_check_ids: list[str],
    notes: str | None = None,
) -> dict[str, Any]:
    _validate_http_url(url)
    return {
        "resource_candidate_id": _candidate_id(situation_id, url, title),
        "title": title,
        "url": url,
        "source_type": source_type,
        "source_domain": _domain(url),
        "status": "candidate_found",
        "confidence": confidence,
        "related_resource_ids": related_resource_ids,
        "related_check_ids": related_check_ids,
        "discovered_by": DISCOVERED_BY,
        "discovered_at": _utc_now(),
        "notes": notes,
    }


def ensure_resource_workspace(evaluation: dict[str, Any]) -> dict[str, Any]:
    updated = attach_methodology_workspace_to_evidence(evaluation)
    workspace = updated.get(WORKSPACE_KEY)
    if not isinstance(workspace, dict):
        return updated
    workspace.setdefault("resource_candidates", [])
    workspace.setdefault("search_suggestions", [])
    return updated


def _apply_candidates(workspace: dict[str, Any], candidates: list[dict[str, Any]]) -> tuple[int, int, int]:
    existing_keys = {
        (item.get("url"), item.get("title"))
        for item in workspace.get("resource_candidates", [])
        if isinstance(item, dict)
    }
    created = 0
    existing = 0
    updated_resources = 0
    candidate_list = workspace.setdefault("resource_candidates", [])

    for candidate in candidates:
        key = (candidate["url"], candidate["title"])
        if key in existing_keys:
            existing += 1
            continue
        candidate_list.append(candidate)
        existing_keys.add(key)
        created += 1
        related_ids = set(candidate.get("related_resource_ids", []))
        for resource in workspace.get("required_resources", []):
            if resource.get("resource_id") in related_ids and resource.get("status") == "missing":
                resource["status"] = "candidate_found"
                updated_resources += 1

    workspace["progress"] = calculate_workspace_progress(workspace)
    return created, existing, updated_resources


def build_resource_scout_plan(
    situation: SpecialSituation,
    evaluation: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    evaluation = evaluation if isinstance(evaluation, dict) else {}
    evaluation = ensure_resource_workspace(evaluation)
    workspace = evaluation.get(WORKSPACE_KEY)
    if not isinstance(workspace, dict):
        return evaluation, [], []

    sec_detection = evaluation.get("sec_detection") if isinstance(evaluation.get("sec_detection"), dict) else {}
    filing_type = sec_detection.get("detected_form_type") or situation.filing_type
    related_resource_ids = _resource_map_for_form(filing_type)
    related_check_ids = []
    for resource in workspace.get("required_resources", []):
        if resource.get("resource_id") in related_resource_ids:
            related_check_ids.extend(resource.get("related_check_ids", []))

    candidates: list[dict[str, Any]] = []
    filing_url = sec_detection.get("filing_url") or situation.filing_url
    if filing_url:
        candidates.append(_candidate(
            situation_id=str(situation.id),
            title=f"{filing_type or 'SEC'} filing",
            url=filing_url,
            source_type="sec_filing",
            confidence="high",
            related_resource_ids=related_resource_ids,
            related_check_ids=list(dict.fromkeys(related_check_ids)),
            notes="Existing SEC filing URL from detection metadata.",
        ))

    archive_url = _sec_archive_directory(sec_detection.get("cik"), sec_detection.get("accession_number"))
    if archive_url and archive_url != filing_url:
        candidates.append(_candidate(
            situation_id=str(situation.id),
            title="SEC archive filing directory",
            url=archive_url,
            source_type="sec_filing",
            confidence="high",
            related_resource_ids=related_resource_ids,
            related_check_ids=list(dict.fromkeys(related_check_ids)),
            notes="Derived from SEC CIK and accession metadata; contents not downloaded.",
        ))

    suggestions = _query_suggestions(
        situation.company_name,
        situation.ticker,
        filing_type,
        workspace,
    )
    return evaluation, candidates, suggestions


def scout_special_situation(situation: SpecialSituation, *, apply: bool = False) -> dict[str, Any]:
    evaluation = deepcopy(situation.evaluation) if isinstance(situation.evaluation, dict) else {}
    evaluation, candidates, suggestions = build_resource_scout_plan(situation, evaluation)
    workspace = evaluation.get(WORKSPACE_KEY) if isinstance(evaluation.get(WORKSPACE_KEY), dict) else None
    if not workspace:
        return {
            "situation_id": str(situation.id),
            "company_name": situation.company_name,
            "candidates_created": 0,
            "candidates_existing": 0,
            "required_resources_updated": 0,
            "search_queries_suggested": [],
            "errors": ["methodology_workspace_missing_or_unsupported"],
        }

    preview_workspace = deepcopy(workspace)
    created, existing, updated_resources = _apply_candidates(preview_workspace, candidates)
    existing_queries = {item.get("query") for item in workspace.get("search_suggestions", []) if isinstance(item, dict)}
    new_suggestions = [item for item in suggestions if item["query"] not in existing_queries]

    if apply:
        _apply_candidates(workspace, candidates)
        workspace.setdefault("search_suggestions", []).extend(new_suggestions)
        workspace["progress"] = calculate_workspace_progress(workspace)
        situation.evaluation = evaluation
        flag_modified(situation, "evaluation")

    return {
        "situation_id": str(situation.id),
        "company_name": situation.company_name,
        "candidates_created": created,
        "candidates_existing": existing,
        "required_resources_updated": updated_resources,
        "search_queries_suggested": [item["query"] for item in new_suggestions],
        "errors": [],
    }


async def run_resource_scout(
    db: AsyncSession,
    *,
    situation_id: str | None = None,
    limit: int | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    if situation_id:
        result = await db.execute(select(SpecialSituation).where(SpecialSituation.id == UUID(situation_id)))
        situations = [item for item in [result.scalars().first()] if item is not None]
    else:
        safe_limit = min(limit or 5, 25)
        result = await db.execute(
            select(SpecialSituation)
            .where(SpecialSituation.status == "detected")
            .order_by(SpecialSituation.detected_at.desc())
            .limit(safe_limit)
        )
        situations = result.scalars().all()

    summaries = [scout_special_situation(situation, apply=apply) for situation in situations]
    if apply and situations:
        await db.flush()
    return {
        "dry_run": not apply,
        "count": len(summaries),
        "limit": None if situation_id else min(limit or 5, 25),
        "results": summaries,
    }


def add_manual_resource_candidate(
    situation: SpecialSituation,
    *,
    title: str | None,
    url: str,
    source_type: str,
    notes: str | None = None,
    related_resource_ids: list[str] | None = None,
    related_check_ids: list[str] | None = None,
) -> dict[str, Any]:
    if source_type not in VALID_SOURCE_TYPES:
        raise ValueError(f"Invalid source_type. Valid values: {sorted(VALID_SOURCE_TYPES)}")
    cleaned_title = (title or "").strip() or _title_from_url(url)
    evaluation = deepcopy(situation.evaluation) if isinstance(situation.evaluation, dict) else {}
    evaluation = ensure_resource_workspace(evaluation)
    workspace = evaluation.get(WORKSPACE_KEY)
    if not isinstance(workspace, dict):
        raise ValueError("methodology_workspace is missing or unsupported for this situation")

    candidate = _candidate(
        situation_id=str(situation.id),
        title=cleaned_title,
        url=url,
        source_type=source_type,
        confidence="medium",
        related_resource_ids=related_resource_ids or [],
        related_check_ids=related_check_ids or [],
        notes=notes,
    )
    created, existing, updated_resources = _apply_candidates(workspace, [candidate])
    situation.evaluation = evaluation
    flag_modified(situation, "evaluation")
    return {
        "candidate": candidate,
        "created": created == 1,
        "existing": existing == 1,
        "required_resources_updated": updated_resources,
    }


def update_workflow_status(situation: SpecialSituation, workflow_status: str) -> dict[str, Any]:
    if workflow_status not in ALLOWED_WORKFLOW_STATUSES:
        raise ValueError(f"Invalid workflow_status. Valid values: {sorted(ALLOWED_WORKFLOW_STATUSES)}")
    evaluation = deepcopy(situation.evaluation) if isinstance(situation.evaluation, dict) else {}
    workspace = evaluation.get(WORKSPACE_KEY)
    if not isinstance(workspace, dict):
        raise ValueError("methodology_workspace is missing or unsupported for this situation")

    workspace["workflow_status"] = workflow_status
    workspace["progress"] = recalculate_methodology_progress(workspace)
    situation.evaluation = evaluation
    flag_modified(situation, "evaluation")
    return workspace


def _find_by_key(items: list[Any], key: str, value: str) -> dict[str, Any] | None:
    for item in items:
        if isinstance(item, dict) and item.get(key) == value:
            return item
    return None


def update_resource_candidate_review(
    situation: SpecialSituation,
    *,
    resource_candidate_id: str,
    status: str | None = None,
    notes: str | None = None,
    related_resource_ids: list[str] | None = None,
    related_check_ids: list[str] | None = None,
) -> dict[str, Any]:
    if status is not None and status not in VALID_RESOURCE_REVIEW_STATUSES:
        raise ValueError(f"Invalid status. Valid values: {sorted(VALID_RESOURCE_REVIEW_STATUSES)}")
    evaluation = deepcopy(situation.evaluation) if isinstance(situation.evaluation, dict) else {}
    workspace = evaluation.get(WORKSPACE_KEY)
    if not isinstance(workspace, dict):
        raise ValueError("methodology_workspace is missing or unsupported for this situation")

    candidates = workspace.get("resource_candidates") if isinstance(workspace.get("resource_candidates"), list) else []
    candidate = _find_by_key(candidates, "resource_candidate_id", resource_candidate_id)
    if candidate is None:
        raise ValueError("resource_candidate_id not found")

    if status is not None:
        candidate["status"] = status
    if notes is not None:
        candidate["notes"] = notes
    if related_resource_ids is not None:
        candidate["related_resource_ids"] = related_resource_ids
    if related_check_ids is not None:
        candidate["related_check_ids"] = related_check_ids

    effective_status = candidate.get("status")
    if effective_status == "evidence_found":
        linked_resources = set(candidate.get("related_resource_ids", []))
        for resource in workspace.get("required_resources", []):
            if not isinstance(resource, dict) or resource.get("resource_id") not in linked_resources:
                continue
            if resource.get("status") in {"missing", "candidate_found"}:
                resource["status"] = "evidence_found"
            if resource.get("status") not in ALLOWED_REQUIRED_RESOURCE_STATUSES:
                resource["status"] = "evidence_found"

        linked_checks = set(candidate.get("related_check_ids", []))
        for check in workspace.get("checklist", []):
            if not isinstance(check, dict) or check.get("check_id") not in linked_checks:
                continue
            if check.get("status") in {"not_started", "needs_evidence"}:
                check["status"] = "evidence_found"
            if check.get("status") not in ALLOWED_CHECKLIST_STATUSES:
                check["status"] = "evidence_found"

    workspace["progress"] = recalculate_methodology_progress(workspace)
    situation.evaluation = evaluation
    flag_modified(situation, "evaluation")
    return {
        "candidate": candidate,
        "workspace": workspace,
    }
