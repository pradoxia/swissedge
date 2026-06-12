"""W1 — Automatic SEC document acquisition + checklist evidence mapping.

After detection creates a SpecialSituation (or on explicit manual trigger),
this service:

1. Fetches the SEC filing index page and extracts official document candidates
   (reusing the manual SEC acquisition machinery from M1/AN+AO).
2. Downloads the body text of up to ``max_documents`` candidates (SEC hosts
   only, size-capped, throttled) into ``ResearchDocument`` rows linked to the
   SpecialSituation via ``special_situation_id``.
3. Deterministically maps acquired documents to the methodology workspace's
   required resources and related checklist items, upgrading their status from
   ``missing``/``needs_evidence``/``candidate_found`` to ``evidence_found``.

Guardrails (Dani-approved 2026-06-11):
- SEC hosts only; non-SEC URLs are skipped, never fetched.
- ``evidence_found`` NEVER means verified. Every mark carries
  ``verified: false`` and ``human_review_required: true``.
- No AI, no promotion, no rejection, no publishing, no decisions.
- Failures degrade to warnings; enrichment must never break detection.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchDocument
from backend.services.investment import sec_document_acquisition as seq
from backend.services.investment.methodology_workspace import WORKSPACE_KEY

logger = logging.getLogger(__name__)

MAX_AUTO_DOCUMENTS = 8
BODY_HEAD_CHARS = 4_000
_UPGRADABLE_STATUSES = {"missing", "needs_evidence", "candidate_found"}
_FETCHABLE_EXTENSIONS = (".htm", ".html", ".txt")
_TITLE_STOPWORDS = {"filing", "if", "available", "document", "later", "current"}


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _resource_title_variants(title: str | None) -> list[str]:
    """Deterministic search phrases for a required-resource title.

    'Plan of liquidation / dissolution' -> ['plan of liquidation', 'dissolution']
    'SC 14D9 if available' -> ['sc 14d9', 'sc 14d 9']
    """
    if not title:
        return []
    variants: list[str] = []
    for segment in re.split(r"[/|]", title):
        normalized = _normalize(segment)
        words = [w for w in normalized.split() if w not in _TITLE_STOPWORDS]
        phrase = " ".join(words).strip()
        if len(phrase) >= 4:
            variants.append(phrase)
    extra: list[str] = []
    for phrase in variants:
        # '14d9' is commonly written '14d-9' in filings -> normalized '14d 9'
        spaced = re.sub(r"(\d)([a-z])(\d)", r"\1\2 \3", phrase)
        if spaced != phrase:
            extra.append(spaced)
    return variants + extra


def _document_haystack(doc: ResearchDocument) -> str:
    parts = [
        _normalize(doc.title),
        _normalize(doc.url.rsplit("/", 1)[-1] if doc.url else None),
        _normalize((doc.body_text or "")[:BODY_HEAD_CHARS]),
    ]
    return " | ".join(part for part in parts if part)


def _match_document_to_resources(
    doc: ResearchDocument,
    resources: list[dict],
    claimed_resource_ids: set[str],
) -> list[dict]:
    """Return workspace resources this acquired document supports (deterministic)."""
    haystack = _document_haystack(doc)
    if not haystack:
        return []
    matches: list[dict] = []
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        resource_id = str(resource.get("resource_id") or "")
        if not resource_id or resource_id in claimed_resource_ids:
            continue
        if str(resource.get("status") or "missing") not in _UPGRADABLE_STATUSES:
            continue
        source_type = str(resource.get("source_type") or "")
        if source_type not in {"sec_filing", "sec_exhibit", "press_release"}:
            continue
        for phrase in _resource_title_variants(resource.get("title")):
            if phrase and phrase in haystack:
                matches.append(resource)
                claimed_resource_ids.add(resource_id)
                break
    return matches


def _evidence_ref(doc: ResearchDocument) -> dict[str, Any]:
    return {
        "document_id": str(doc.id),
        "url": doc.url,
        "title": doc.title,
        "source": "auto_acquisition",
        "verified": False,
        "human_review_required": True,
        "found_at": datetime.now(timezone.utc).isoformat(),
    }


def _mark_evidence_found(
    workspace: dict,
    resource: dict,
    doc: ResearchDocument,
) -> list[str]:
    """Upgrade one resource (and its related checks) to evidence_found. Returns check ids touched."""
    resource["status"] = "evidence_found"
    refs = resource.get("evidence_refs")
    if not isinstance(refs, list):
        refs = []
    refs.append(_evidence_ref(doc))
    resource["evidence_refs"] = refs
    resource["verified"] = False

    touched: list[str] = []
    related = resource.get("related_check_ids") or []
    checklist = workspace.get("checklist") if isinstance(workspace.get("checklist"), list) else []
    for check in checklist:
        if not isinstance(check, dict):
            continue
        if str(check.get("check_id") or "") not in related:
            continue
        if str(check.get("status") or "missing") not in _UPGRADABLE_STATUSES:
            continue
        check["status"] = "evidence_found"
        check_refs = check.get("evidence_refs")
        if not isinstance(check_refs, list):
            check_refs = []
        check_refs.append(_evidence_ref(doc))
        check["evidence_refs"] = check_refs
        touched.append(str(check.get("check_id")))
    return touched


def _fetchable(doc: seq.SecAcquiredDocument) -> bool:
    filename = (doc.url or "").rsplit("/", 1)[-1].lower()
    if not filename.endswith(_FETCHABLE_EXTENSIONS):
        return False
    if "index" in filename:
        return False
    return True


async def _existing_document_urls(db: AsyncSession, situation_id: uuid.UUID) -> set[str]:
    result = await db.execute(
        select(ResearchDocument.url).where(ResearchDocument.special_situation_id == situation_id)
    )
    return {row[0] for row in result.all() if row[0]}


async def auto_acquire_situation_documents(
    db: AsyncSession,
    situation: SpecialSituation,
    *,
    index_fetcher=None,
    body_fetcher=None,
    max_documents: int = MAX_AUTO_DOCUMENTS,
) -> dict[str, Any]:
    """Acquire SEC document bodies for a situation and map them to checklist evidence.

    Returns a summary dict. Never raises for per-document failures; the caller
    decides what to do with ``warnings``.
    """
    summary: dict[str, Any] = {
        "situation_id": str(situation.id),
        "documents_considered": 0,
        "documents_acquired": 0,
        "documents_failed": 0,
        "resources_marked_evidence_found": [],
        "checks_marked_evidence_found": [],
        "warnings": [],
        "verified": False,
        "human_review_required": True,
    }

    preview = seq.build_situation_sec_document_acquisition_preview(situation)
    if not seq._is_sec_url(preview.available_identifiers.filing_url):
        summary["warnings"].append("No official sec.gov filing URL; auto-acquisition skipped.")
        return summary

    preview = await seq.acquire_sec_documents_from_preview(preview, fetcher=index_fetcher)
    seq.apply_situation_sec_acquisition_metadata(situation, preview)

    candidates = [doc for doc in preview.acquired_documents if _fetchable(doc)][:max_documents]
    summary["documents_considered"] = len(candidates)
    if not candidates:
        summary["warnings"].append("No fetchable SEC document candidates found on the filing index.")
        return summary

    existing_urls = await _existing_document_urls(db, situation.id)

    evaluation = dict(situation.evaluation or {})
    workspace = dict(evaluation.get(WORKSPACE_KEY) or {})
    resources = workspace.get("required_resources")
    resources = resources if isinstance(resources, list) else []
    claimed: set[str] = set()

    acquired_docs: list[ResearchDocument] = []
    for candidate in candidates:
        if candidate.url in existing_urls:
            continue
        document = ResearchDocument(
            special_situation_id=situation.id,
            doc_type=candidate.doc_type,
            url=candidate.url,
            title=candidate.title,
            retrieved_at=datetime.now(timezone.utc),
            summary="Auto-acquired SEC document. Candidate evidence; human review required; not verified.",
            added_by="auto_acquisition",
        )
        try:
            await seq.acquire_research_document_body_text(document, fetcher=body_fetcher)
        except Exception as exc:  # defensive: never break the batch
            summary["documents_failed"] += 1
            summary["warnings"].append(f"Body acquisition failed safely for {candidate.url}: {exc}")
            continue
        db.add(document)
        await db.flush()
        existing_urls.add(candidate.url)
        if document.body_text_status == seq.BODY_STATUS_ACQUIRED:
            summary["documents_acquired"] += 1
            acquired_docs.append(document)
        else:
            summary["documents_failed"] += 1
            if document.body_text_error:
                summary["warnings"].append(
                    f"{candidate.title}: {document.body_text_status} ({document.body_text_error})"
                )

    for document in acquired_docs:
        for resource in _match_document_to_resources(document, resources, claimed):
            touched = _mark_evidence_found(workspace, resource, document)
            summary["resources_marked_evidence_found"].append(str(resource.get("resource_id")))
            summary["checks_marked_evidence_found"].extend(touched)

    workspace["required_resources"] = resources
    workspace["auto_acquisition"] = {
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "documents_acquired": summary["documents_acquired"],
        "documents_failed": summary["documents_failed"],
        "resources_marked_evidence_found": summary["resources_marked_evidence_found"],
        "verified": False,
        "human_review_required": True,
        "note": "evidence_found means located, not verified. Dani review required.",
    }
    evaluation[WORKSPACE_KEY] = workspace
    situation.evaluation = evaluation
    situation.updated_at = datetime.now(timezone.utc)
    await db.flush()

    summary["checks_marked_evidence_found"] = sorted(set(summary["checks_marked_evidence_found"]))
    return summary


async def auto_acquire_for_created_situations(
    db: AsyncSession,
    created_situations: list[dict[str, Any]],
    *,
    max_situations: int = 5,
    index_fetcher=None,
    body_fetcher=None,
) -> dict[str, Any]:
    """Post-detection enrichment hook. Bounded, fail-safe, SEC-only."""
    overall: dict[str, Any] = {
        "situations_processed": 0,
        "documents_acquired": 0,
        "resources_marked_evidence_found": 0,
        "warnings": [],
    }
    for entry in created_situations[:max_situations]:
        situation_id = entry.get("id") if isinstance(entry, dict) else None
        if not situation_id:
            continue
        try:
            situation = await db.get(SpecialSituation, uuid.UUID(str(situation_id)))
            if situation is None:
                continue
            result = await auto_acquire_situation_documents(
                db,
                situation,
                index_fetcher=index_fetcher,
                body_fetcher=body_fetcher,
            )
            overall["situations_processed"] += 1
            overall["documents_acquired"] += int(result.get("documents_acquired") or 0)
            overall["resources_marked_evidence_found"] += len(
                result.get("resources_marked_evidence_found") or []
            )
            overall["warnings"].extend(result.get("warnings") or [])
        except Exception as exc:  # enrichment must never break detection
            logger.exception("Auto-acquisition failed safely for situation %s", situation_id)
            overall["warnings"].append(f"Auto-acquisition failed safely for {situation_id}: {exc}")
    if len(created_situations) > max_situations:
        overall["warnings"].append(
            f"Auto-acquisition capped at {max_situations} situations this run; "
            f"{len(created_situations) - max_situations} remain for manual trigger."
        )
    return overall
