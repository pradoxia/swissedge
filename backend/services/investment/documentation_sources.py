from __future__ import annotations

import re
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import UploadFile
from sqlalchemy.orm.attributes import flag_modified

from backend.models.investment import SpecialSituation
from backend.services.investment.methodology_workspace import (
    WORKSPACE_KEY,
    attach_methodology_workspace_to_evidence,
    calculate_workspace_progress,
)


DOCUMENTATION_SOURCE_TYPES = {
    "uploaded_file",
    "source_link",
    "sec_filing",
    "company_ir",
    "other",
}
UPLOAD_ROOT = Path("storage/documentation_sources")
MAX_UPLOAD_BYTES = 15 * 1024 * 1024


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _domain(url: str | None) -> str | None:
    if not url:
        return None
    return urlparse(url).netloc.lower() or None


def _validate_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must be an absolute http/https URL")


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned[:120] or "uploaded_document"


def _workspace_for(situation: SpecialSituation) -> tuple[dict[str, Any], dict[str, Any]]:
    evaluation = deepcopy(situation.evaluation) if isinstance(situation.evaluation, dict) else {}
    evaluation = attach_methodology_workspace_to_evidence(evaluation)
    workspace = evaluation.get(WORKSPACE_KEY)
    if not isinstance(workspace, dict):
        raise ValueError("methodology_workspace is missing or unsupported for this situation")
    workspace.setdefault("resource_candidates", [])
    return evaluation, workspace


def _candidate_payload(
    *,
    situation_id: str,
    document_key: str,
    title: str,
    source_type: str,
    status: str,
    url: str | None = None,
    original_filename: str | None = None,
    stored_path: str | None = None,
    mime_type: str | None = None,
    related_required_resource_ids: list[str] | None = None,
    related_checklist_item_ids: list[str] | None = None,
) -> dict[str, Any]:
    if source_type not in DOCUMENTATION_SOURCE_TYPES:
        raise ValueError(f"Invalid source_type. Valid values: {sorted(DOCUMENTATION_SOURCE_TYPES)}")
    if url:
        _validate_http_url(url)
    related_resources = list(dict.fromkeys([document_key, *(related_required_resource_ids or [])]))
    return {
        "resource_candidate_id": str(uuid.uuid4()),
        "documentation_source_id": str(uuid.uuid4()),
        "case_type": "special_situation",
        "case_id": situation_id,
        "document_key": document_key,
        "title": title.strip() or original_filename or url or document_key,
        "source_type": source_type,
        "source_domain": _domain(url),
        "url": url,
        "original_filename": original_filename,
        "stored_path": stored_path,
        "mime_type": mime_type,
        "status": status,
        "verified": False,
        "confidence": "unknown",
        "related_resource_ids": related_resources,
        "related_required_resource_ids": related_resources,
        "related_check_ids": list(dict.fromkeys(related_checklist_item_ids or [])),
        "related_checklist_item_ids": list(dict.fromkeys(related_checklist_item_ids or [])),
        "discovered_by": "manual_documentation_intake",
        "discovered_at": _utc_now(),
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "notes": "Candidate documentation source. Not read, extracted, or verified automatically.",
    }


def _apply_candidate(situation: SpecialSituation, candidate: dict[str, Any]) -> dict[str, Any]:
    evaluation, workspace = _workspace_for(situation)
    candidates = workspace.setdefault("resource_candidates", [])
    candidates.append(candidate)
    for resource in workspace.get("required_resources", []):
        if not isinstance(resource, dict):
            continue
        if resource.get("resource_id") in set(candidate.get("related_resource_ids") or []) and resource.get("status") == "missing":
            resource["status"] = "candidate_found"
    workspace["progress"] = calculate_workspace_progress(workspace)
    situation.evaluation = evaluation
    flag_modified(situation, "evaluation")
    return candidate


async def add_uploaded_document_source(
    situation: SpecialSituation,
    *,
    file: UploadFile,
    document_key: str,
    title: str | None = None,
    related_required_resource_ids: list[str] | None = None,
    related_checklist_item_ids: list[str] | None = None,
) -> dict[str, Any]:
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError("Uploaded file is too large for documentation intake")
    source_id = str(uuid.uuid4())
    filename = _safe_filename(file.filename or "uploaded_document")
    target_dir = UPLOAD_ROOT / str(situation.id) / document_key
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{source_id}-{filename}"
    target.write_bytes(raw)
    candidate = _candidate_payload(
        situation_id=str(situation.id),
        document_key=document_key,
        title=title or file.filename or document_key,
        source_type="uploaded_file",
        status="uploaded_pending_review",
        original_filename=file.filename,
        stored_path=str(target),
        mime_type=file.content_type,
        related_required_resource_ids=related_required_resource_ids,
        related_checklist_item_ids=related_checklist_item_ids,
    )
    candidate["documentation_source_id"] = source_id
    return _apply_candidate(situation, candidate)


def add_link_documentation_source(
    situation: SpecialSituation,
    *,
    url: str,
    document_key: str,
    title: str | None = None,
    source_type: str = "source_link",
    related_required_resource_ids: list[str] | None = None,
    related_checklist_item_ids: list[str] | None = None,
) -> dict[str, Any]:
    candidate = _candidate_payload(
        situation_id=str(situation.id),
        document_key=document_key,
        title=title or _domain(url) or document_key,
        source_type=source_type,
        status="source_link_pending_review",
        url=url,
        related_required_resource_ids=related_required_resource_ids,
        related_checklist_item_ids=related_checklist_item_ids,
    )
    return _apply_candidate(situation, candidate)


def list_documentation_sources(situation: SpecialSituation) -> dict[str, Any]:
    evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    workspace = evaluation.get(WORKSPACE_KEY) if isinstance(evaluation.get(WORKSPACE_KEY), dict) else {}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for candidate in workspace.get("resource_candidates", []) or []:
        if not isinstance(candidate, dict):
            continue
        document_keys = candidate.get("related_resource_ids") or []
        if candidate.get("document_key") and candidate.get("document_key") not in document_keys:
            document_keys = [candidate.get("document_key"), *document_keys]
        for key in dict.fromkeys(str(item) for item in document_keys if item):
            grouped.setdefault(key, []).append(candidate)
    source_counts = {key: len(items) for key, items in grouped.items()}
    latest_sources = {
        key: sorted(
            items,
            key=lambda item: str(item.get("updated_at") or item.get("created_at") or item.get("discovered_at") or ""),
            reverse=True,
        )[0]
        for key, items in grouped.items()
        if items
    }
    return {
        "case_type": "special_situation",
        "case_id": str(situation.id),
        "sources_by_document_key": grouped,
        "source_counts_by_document_key": source_counts,
        "latest_source_by_document_key": latest_sources,
        "guardrails": [
            "Uploaded or linked sources are not verified evidence.",
            "No extraction runs until Dani manually requests Read & map draft.",
        ],
    }
