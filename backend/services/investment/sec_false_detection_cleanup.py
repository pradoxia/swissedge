from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.investment import SpecialSituation


CUTOFF_FILING_DATE = date(2026, 5, 4)
DETECTED_START = datetime(2026, 5, 11, 11, 30, tzinfo=timezone.utc)
DETECTED_END = datetime(2026, 5, 11, 11, 45, tzinfo=timezone.utc)
DELETE_CONFIRMATION = "DELETE_FALSE_SEC_DETECTIONS"


@dataclass
class CleanupMatch:
    id: str
    company_name: str
    filing_type: str | None
    filing_date: str | None
    accession_number: str | None
    detected_at: str | None


def _as_aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_filing_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip()[:10]).date()
    except ValueError:
        return None


def is_false_sec_detection_candidate(situation: SpecialSituation) -> bool:
    if situation.status != "detected":
        return False

    evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    sec_detection = evaluation.get("sec_detection")
    if not isinstance(sec_detection, dict):
        return False
    if evaluation.get("source") != "sec_edgar":
        return False
    if evaluation.get("detected_only") is not True:
        return False

    filing_date = _parse_filing_date(sec_detection.get("filing_date"))
    if filing_date is None or filing_date >= CUTOFF_FILING_DATE:
        return False

    detected_at = _as_aware_utc(situation.detected_at)
    return detected_at is not None and DETECTED_START <= detected_at <= DETECTED_END


def serialize_cleanup_match(situation: SpecialSituation) -> CleanupMatch:
    evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    sec_detection = evaluation.get("sec_detection") if isinstance(evaluation.get("sec_detection"), dict) else {}
    detected_at = _as_aware_utc(situation.detected_at)
    return CleanupMatch(
        id=str(situation.id),
        company_name=situation.company_name,
        filing_type=situation.filing_type,
        filing_date=sec_detection.get("filing_date"),
        accession_number=sec_detection.get("accession_number"),
        detected_at=detected_at.isoformat() if detected_at else None,
    )


async def find_false_sec_detections(db: AsyncSession) -> list[SpecialSituation]:
    result = await db.execute(
        select(SpecialSituation).where(
            SpecialSituation.status == "detected",
            SpecialSituation.detected_at >= DETECTED_START,
            SpecialSituation.detected_at <= DETECTED_END,
        )
    )
    return [item for item in result.scalars().all() if is_false_sec_detection_candidate(item)]


async def run_false_detection_cleanup(
    db: AsyncSession,
    *,
    delete: bool = False,
    confirm: str | None = None,
) -> dict[str, Any]:
    matches = await find_false_sec_detections(db)
    summary: dict[str, Any] = {
        "dry_run": not delete,
        "matched_count": len(matches),
        "deleted_count": 0,
        "matches": [serialize_cleanup_match(item).__dict__ for item in matches],
    }

    if not delete:
        return summary

    if confirm != DELETE_CONFIRMATION:
        summary["error"] = f"--confirm must equal {DELETE_CONFIRMATION!r} when using --delete"
        return summary

    for item in matches:
        await db.delete(item)
    summary["deleted_count"] = len(matches)
    return summary
