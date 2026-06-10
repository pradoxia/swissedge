from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.investment import DecisionRecord, SpecialSituation
from backend.models.investment_research import ResearchCase


DecisionTargetType = Literal["special_situation", "research_case"]
ALLOWED_DECISION_OUTCOMES = {"CANDIDATE", "WATCHLIST", "REJECT", "NEED_MORE_EVIDENCE"}


class DecisionRecordCreate(BaseModel):
    target_type: DecisionTargetType
    target_id: str
    outcome: str
    reason: str
    author: str = "Dani"
    source_surface: str | None = "research_inbox"


class DecisionRecordRead(BaseModel):
    id: str
    target_type: DecisionTargetType
    target_id: str
    outcome: str
    reason: str
    author: str
    source_surface: str | None = None
    created_at: str | None = None


class DecisionRecordError(ValueError):
    def __init__(self, message: str, *, status_code: int = 422):
        super().__init__(message)
        self.status_code = status_code


def _iso(value) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


def _parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        raise DecisionRecordError("target_id must be a valid UUID") from None


def normalize_decision_payload(payload: DecisionRecordCreate) -> tuple[DecisionTargetType, uuid.UUID, str, str, str, str | None]:
    outcome = str(payload.outcome or "").strip().upper()
    reason = str(payload.reason or "").strip()
    author = str(payload.author or "").strip()
    source_surface = str(payload.source_surface).strip() if payload.source_surface is not None else None

    if outcome not in ALLOWED_DECISION_OUTCOMES:
        raise DecisionRecordError("Invalid decision outcome")
    if not reason:
        raise DecisionRecordError("Decision reason is required")
    if not author:
        raise DecisionRecordError("Decision author is required")

    return payload.target_type, _parse_uuid(payload.target_id), outcome, reason, author, source_surface or None


def serialize_decision_record(record: DecisionRecord) -> DecisionRecordRead:
    if record.special_situation_id:
        target_type: DecisionTargetType = "special_situation"
        target_id = record.special_situation_id
    elif record.research_case_id:
        target_type = "research_case"
        target_id = record.research_case_id
    else:
        raise DecisionRecordError("DecisionRecord must target exactly one entity")

    return DecisionRecordRead(
        id=str(record.id),
        target_type=target_type,
        target_id=str(target_id),
        outcome=record.outcome,
        reason=record.reason,
        author=record.author,
        source_surface=record.source_surface,
        created_at=_iso(record.created_at),
    )


def build_decision_record(
    *,
    special_situation_id: uuid.UUID | None = None,
    research_case_id: uuid.UUID | None = None,
    outcome: str,
    reason: str,
    author: str,
    source_surface: str | None = "research_inbox",
) -> DecisionRecord:
    if (special_situation_id is None) == (research_case_id is None):
        raise DecisionRecordError("DecisionRecord must target exactly one entity")
    return DecisionRecord(
        special_situation_id=special_situation_id,
        research_case_id=research_case_id,
        outcome=outcome,
        reason=reason,
        author=author,
        source_surface=source_surface,
    )


async def create_decision_record(db: AsyncSession, payload: DecisionRecordCreate) -> DecisionRecord:
    target_type, target_id, outcome, reason, author, source_surface = normalize_decision_payload(payload)

    if target_type == "special_situation":
        target = await db.get(SpecialSituation, target_id)
        if not target:
            raise DecisionRecordError("SpecialSituation target not found", status_code=404)
        record = build_decision_record(
            special_situation_id=target_id,
            outcome=outcome,
            reason=reason,
            author=author,
            source_surface=source_surface,
        )
    else:
        target = await db.get(ResearchCase, target_id)
        if not target:
            raise DecisionRecordError("ResearchCase target not found", status_code=404)
        record = build_decision_record(
            research_case_id=target_id,
            outcome=outcome,
            reason=reason,
            author=author,
            source_surface=source_surface,
        )

    db.add(record)
    await db.flush()
    return record
