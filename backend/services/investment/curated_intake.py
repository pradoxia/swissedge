from __future__ import annotations

from datetime import date, datetime, timezone
from urllib.parse import urlparse, urlunparse

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.investment import SpecialSituation


class CuratedIntakePayload(BaseModel):
    url: str
    source_name: str
    situation_type: str
    title: str | None = None
    summary: str | None = None
    ticker: str | None = None
    company_name: str | None = None
    notes: str | None = None
    source_published_at: str | None = None
    submitted_by: str = "Dani"
    source_tier: str | None = None
    source_confidence: str | None = None


class CuratedIntakeResponse(BaseModel):
    special_situation_id: str
    origin: str
    status: str
    candidate_only: bool
    research_inbox_href: str
    duplicate: bool = False


class CuratedIntakeError(ValueError):
    def __init__(self, message: str, *, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


def _trim(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def normalize_curated_url(value: str | None) -> str:
    raw = _trim(value)
    if not raw:
        raise CuratedIntakeError("url is required")
    parsed = urlparse(raw)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.netloc:
        raise CuratedIntakeError("url must be an http or https URL")
    normalized = parsed._replace(
        scheme=scheme,
        netloc=parsed.netloc.lower(),
        fragment="",
    )
    return urlunparse(normalized).rstrip("/")


def _parse_optional_date(value: str | None) -> str | None:
    raw = _trim(value)
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError:
        raise CuratedIntakeError("source_published_at must be an ISO date") from None


def _validated_payload(payload: CuratedIntakePayload) -> dict:
    source_name = _trim(payload.source_name)
    situation_type = _trim(payload.situation_type)
    title = _trim(payload.title)
    summary = _trim(payload.summary)
    submitted_by = _trim(payload.submitted_by) or "Dani"

    if not source_name:
        raise CuratedIntakeError("source_name is required")
    if not situation_type:
        raise CuratedIntakeError("situation_type is required")
    if not title and not summary:
        raise CuratedIntakeError("title or summary is required")
    if not submitted_by:
        raise CuratedIntakeError("submitted_by is required")

    return {
        "url": normalize_curated_url(payload.url),
        "source_name": source_name,
        "situation_type": situation_type,
        "title": title,
        "summary": summary,
        "ticker": _trim(payload.ticker),
        "company_name": _trim(payload.company_name),
        "notes": _trim(payload.notes),
        "source_published_at": _parse_optional_date(payload.source_published_at),
        "submitted_by": submitted_by,
        "source_tier": _trim(payload.source_tier),
        "source_confidence": _trim(payload.source_confidence),
    }


def build_curated_special_situation(values: dict) -> SpecialSituation:
    title = values["title"] or values["summary"] or "Curated source"
    company_name = values["company_name"] or title
    now = datetime.now(timezone.utc)
    evaluation = {
        "origin": "curated",
        "candidate_only": True,
        "verified": False,
        "curated_intake": {
            "source_url": values["url"],
            "source_name": values["source_name"],
            "title": values["title"],
            "summary": values["summary"],
            "notes": values["notes"],
            "source_published_at": values["source_published_at"],
            "submitted_by": values["submitted_by"],
            "source_tier": values["source_tier"],
            "source_confidence": values["source_confidence"],
            "origin": "curated",
            "candidate_only": True,
            "verified": False,
        },
    }
    return SpecialSituation(
        situation_type=values["situation_type"],
        company_name=company_name,
        ticker=values["ticker"],
        filing_type="curated_source",
        filing_url=values["url"],
        detected_at=now,
        status="candidate",
        evaluation=evaluation,
        source_urls=[values["url"]],
        notes=values["notes"],
        published=False,
        created_at=now,
        updated_at=now,
    )


async def create_curated_special_situation(
    db: AsyncSession,
    payload: CuratedIntakePayload,
) -> CuratedIntakeResponse:
    values = _validated_payload(payload)
    existing_result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.filing_url == values["url"])
    )
    existing = existing_result.scalars().first()
    if existing is not None:
        raise CuratedIntakeError("A SpecialSituation with this URL already exists", status_code=409)

    situation = build_curated_special_situation(values)
    db.add(situation)
    await db.flush()
    return CuratedIntakeResponse(
        special_situation_id=str(situation.id),
        origin="curated",
        status="candidate",
        candidate_only=True,
        research_inbox_href=f"/investment/situations/{situation.id}",
    )
