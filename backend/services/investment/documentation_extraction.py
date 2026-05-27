from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Awaitable, Callable

import httpx
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from backend.models.investment import DocumentationExtractionField, SpecialSituation
from backend.services.investment.methodology_workspace import WORKSPACE_KEY


MAX_SOURCE_CHARS = 250_000
VALID_REVIEW_STATUSES = {"accepted", "rejected", "edited"}


class DocumentationExtractionFieldRead(BaseModel):
    id: str
    situation_id: str
    candidate_source_id: str
    document_key: str
    source_url: str | None
    source_title: str | None
    field_key: str
    field_label: str
    extracted_value: str | None
    confidence: float | None
    source_snippet: str | None
    section_reference: str | None
    status: str
    reviewed_by: str | None
    reviewed_at: str | None
    created_at: str | None
    updated_at: str | None

    @classmethod
    def from_orm(cls, row: DocumentationExtractionField) -> "DocumentationExtractionFieldRead":
        return cls(
            id=str(row.id),
            situation_id=str(row.situation_id),
            candidate_source_id=row.candidate_source_id,
            document_key=row.document_key,
            source_url=row.source_url,
            source_title=row.source_title,
            field_key=row.field_key,
            field_label=row.field_label,
            extracted_value=row.extracted_value,
            confidence=row.confidence,
            source_snippet=row.source_snippet,
            section_reference=row.section_reference,
            status=row.status,
            reviewed_by=row.reviewed_by,
            reviewed_at=row.reviewed_at.isoformat() if row.reviewed_at else None,
            created_at=row.created_at.isoformat() if row.created_at else None,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )


@dataclass(frozen=True)
class DraftField:
    field_key: str
    field_label: str
    extracted_value: str
    confidence: float
    source_snippet: str
    section_reference: str | None = None


async def fetch_source_text(url: str) -> str:
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "SwissEdge manual documentation intake contact@example.com"})
        response.raise_for_status()
        return response.text[:MAX_SOURCE_CHARS]


async def list_extraction_fields(
    db: AsyncSession,
    situation_id: uuid.UUID,
    *,
    document_key: str | None = None,
    candidate_source_id: str | None = None,
) -> list[DocumentationExtractionField]:
    query = select(DocumentationExtractionField).where(DocumentationExtractionField.situation_id == situation_id)
    if document_key:
        query = query.where(DocumentationExtractionField.document_key == document_key)
    if candidate_source_id:
        query = query.where(DocumentationExtractionField.candidate_source_id == candidate_source_id)
    query = query.order_by(DocumentationExtractionField.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def read_and_store_draft_fields(
    db: AsyncSession,
    situation_id: uuid.UUID,
    *,
    candidate_source_id: str,
    document_key: str,
    fetcher: Callable[[str], Awaitable[str]] | None = None,
) -> list[DocumentationExtractionField]:
    situation = await _load_situation(db, situation_id)
    candidate = _candidate_for(situation, candidate_source_id)
    if document_key not in [str(item) for item in candidate.get("related_resource_ids", [])]:
        raise HTTPException(status_code=422, detail="Candidate source is not mapped to this document_key")
    url = candidate.get("url")
    stored_path = candidate.get("stored_path")
    if isinstance(stored_path, str) and stored_path.strip():
        source_text = _read_uploaded_source(stored_path, candidate.get("mime_type"))
    elif isinstance(url, str) and url.strip():
        source_text = await (fetcher or fetch_source_text)(url.strip())
    else:
        raise HTTPException(status_code=422, detail="Candidate source has no readable URL or uploaded file")
    fields = extract_draft_fields(
        source_text,
        situation_type=_situation_type(situation),
        document_key=document_key,
    )
    if not fields:
        fields = [
            DraftField(
                field_key="manual_review_needed",
                field_label="Manual review needed",
                extracted_value="No structured fields were detected automatically.",
                confidence=0.1,
                source_snippet=_snippet(_clean_text(source_text), "offer", fallback=True),
            )
        ]

    existing = await list_extraction_fields(
        db,
        situation_id,
        document_key=document_key,
        candidate_source_id=candidate_source_id,
    )
    existing_by_key = {row.field_key: row for row in existing}
    rows: list[DocumentationExtractionField] = []
    now = datetime.now(timezone.utc)
    for field in fields:
        row = existing_by_key.get(field.field_key)
        if row and row.status == "draft":
            row.field_label = field.field_label
            row.extracted_value = field.extracted_value
            row.confidence = field.confidence
            row.source_snippet = field.source_snippet
            row.section_reference = field.section_reference
            row.updated_at = now
        else:
            row = DocumentationExtractionField(
                situation_id=situation_id,
                candidate_source_id=candidate_source_id,
                document_key=document_key,
                source_url=url,
                source_title=str(candidate.get("title") or "") or None,
                field_key=field.field_key,
                field_label=field.field_label,
                extracted_value=field.extracted_value,
                confidence=field.confidence,
                source_snippet=field.source_snippet,
                section_reference=field.section_reference,
                status="draft",
            )
            db.add(row)
        rows.append(row)
    if candidate.get("verified") is not True:
        candidate["status"] = "draft_extracted"
        candidate["verified"] = False
        candidate["updated_at"] = datetime.now(timezone.utc).isoformat()
        flag_modified(situation, "evaluation")
    await db.flush()
    return rows


def _read_uploaded_source(stored_path: str, mime_type: object) -> str:
    path = Path(stored_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=422, detail="Uploaded source file is not available to read")
    lower_name = path.name.lower()
    lower_mime = str(mime_type or "").lower()
    if lower_name.endswith(".pdf") or lower_mime == "application/pdf":
        raise HTTPException(
            status_code=422,
            detail="Document reader not available for PDF uploads yet. Upload a text/HTML version or add the SEC exhibit link if readable.",
        )
    if not (lower_name.endswith((".txt", ".htm", ".html")) or lower_mime.startswith("text/") or "html" in lower_mime):
        raise HTTPException(
            status_code=422,
            detail="Document reader not available for this uploaded source type yet. Upload a text/HTML version or add the SEC exhibit link if readable.",
        )
    return path.read_text(encoding="utf-8", errors="ignore")[:MAX_SOURCE_CHARS]


async def review_extraction_field(
    db: AsyncSession,
    field_id: uuid.UUID,
    *,
    status: str,
    extracted_value: str | None = None,
    reviewed_by: str | None = "Dani",
) -> DocumentationExtractionField:
    if status not in VALID_REVIEW_STATUSES:
        raise HTTPException(status_code=422, detail="status must be accepted, rejected, or edited")
    result = await db.execute(select(DocumentationExtractionField).where(DocumentationExtractionField.id == field_id))
    row = result.scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="Extraction field not found")
    row.status = status
    if extracted_value is not None:
        row.extracted_value = extracted_value
    row.reviewed_by = reviewed_by or "Dani"
    row.reviewed_at = datetime.now(timezone.utc)
    row.updated_at = row.reviewed_at
    await db.flush()
    return row


def extract_draft_fields(source_text: str, *, situation_type: str | None, document_key: str) -> list[DraftField]:
    text = _clean_text(source_text)
    if (situation_type or "").lower() == "tender_offer" or document_key in {
        "offer_to_purchase",
        "issuer_tender_statement",
        "letter_of_transmittal",
        "key_exhibits",
    }:
        return _extract_tender_offer_fields(text)
    return []


def _extract_tender_offer_fields(text: str) -> list[DraftField]:
    specs = [
        ("offer_price", "Offer price or price range", r"(\$\s?\d+(?:\.\d{1,4})?\s*(?:per share|per unit|in cash)?)"),
        ("expiration_date", "Expiration date", r"(?:expire|expiration date|expires)[^.]{0,100}?((?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},\s+\d{4}[^.]*)"),
        ("proration_terms", "Proration terms", r"((?:proration|prorated)[^.]{0,180}\.)"),
        ("odd_lot_priority", "Odd-lot priority", r"((?:odd[- ]lot|odd lot)[^.]{0,180}\.)"),
        ("source_of_funds", "Source of funds", r"((?:source of funds|available cash|cash on hand|borrowings)[^.]{0,220}\.)"),
        ("withdrawal_rights", "Withdrawal rights", r"((?:withdrawal rights|may withdraw|right to withdraw)[^.]{0,220}\.)"),
        ("offer_size", "Offer size / amount", r"((?:up to|not more than|aggregate purchase price)[^.]{0,180}(?:shares|units|million|billion|aggregate)[^.]*\.)"),
        ("conditions_of_offer", "Conditions of offer", r"((?:conditions to the offer|subject to conditions|conditioned upon)[^.]{0,220}\.)"),
        ("important_dates", "Important dates", r"((?:commence|commenced|settlement date|payment date)[^.]{0,180}\.)"),
        ("amendments", "Amendments mentioned", r"((?:amendment|amended|supplement)[^.]{0,180}\.)"),
        ("fees_or_costs", "Fees or costs", r"((?:fees|expenses|costs)[^.]{0,180}\.)"),
    ]
    rows: list[DraftField] = []
    for key, label, pattern in specs:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        value = " ".join(match.group(1).split())
        rows.append(DraftField(
            field_key=key,
            field_label=label,
            extracted_value=value,
            confidence=0.55,
            source_snippet=_snippet(text, value),
            section_reference=None,
        ))
    return rows


async def _load_situation(db: AsyncSession, situation_id: uuid.UUID) -> SpecialSituation:
    result = await db.execute(select(SpecialSituation).where(SpecialSituation.id == situation_id))
    situation = result.scalars().first()
    if not situation:
        raise HTTPException(status_code=404, detail="Situation not found")
    return situation


def _candidate_for(situation: SpecialSituation, candidate_source_id: str) -> dict:
    evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    workspace = evaluation.get(WORKSPACE_KEY) if isinstance(evaluation.get(WORKSPACE_KEY), dict) else {}
    for candidate in workspace.get("resource_candidates", []) or []:
        if isinstance(candidate, dict) and candidate.get("resource_candidate_id") == candidate_source_id:
            return candidate
    raise HTTPException(status_code=404, detail="Candidate source not found")


def _situation_type(situation: SpecialSituation) -> str | None:
    evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    detection = evaluation.get("sec_detection") if isinstance(evaluation.get("sec_detection"), dict) else {}
    return detection.get("situation_type") or situation.situation_type


def _clean_text(source_text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", source_text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()[:MAX_SOURCE_CHARS]


def _snippet(text: str, value: str, *, fallback: bool = False) -> str:
    if fallback:
        return text[:500]
    index = text.lower().find(value.lower()[:80])
    if index < 0:
        return value[:500]
    start = max(0, index - 180)
    end = min(len(text), index + len(value) + 180)
    return text[start:end].strip()
