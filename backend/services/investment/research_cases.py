import json
import os
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from backend.models.investment_research import ResearchCase, ResearchTask, ResearchDocument, ResearchSource, HistoricalCase
from backend.models.source_intelligence import SourceIntelligenceSuggestion
from backend.models.publishing import PublicArticleDraft
from backend.models.investment import SpecialSituation
from backend.services.ai_client import complete_with_usage
from backend.services.investment.routing_engine import check_scope, route_playbook

def _load_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", filename)
    with open(os.path.normpath(path), "r", encoding="utf-8") as f:
        return f.read().strip()

_DISCLAIMER = "Este análisis es educativo. No es asesoramiento financiero."


def _nullable_str(value) -> str | None:
    return value if isinstance(value, str) else None


def _nullable_uuid_str(value) -> str | None:
    return str(value) if isinstance(value, uuid.UUID) else None


def _nullable_datetime_str(value) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


def _safe_attr_str(obj, name: str) -> str | None:
    value = getattr(obj, name, None)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _situation_has_sec_metadata(situation: SpecialSituation) -> bool:
    filing_url = _safe_attr_str(situation, "filing_url")
    filing_type = _safe_attr_str(situation, "filing_type")
    return bool(filing_type or (filing_url and "sec.gov" in filing_url.lower()))


def _derive_methodology_metadata(situation: SpecialSituation) -> dict[str, str | None]:
    situation_type = _safe_attr_str(situation, "situation_type")
    filing_type = _safe_attr_str(situation, "filing_type")
    if not situation_type:
        return {
            "methodology_status": "unknown",
            "playbook_used": None,
            "checklist_used": None,
            "course_reference": None,
        }

    try:
        routing = route_playbook(situation_type, None, filing_type)
        scope = check_scope(situation_type, None)
    except Exception:
        return {
            "methodology_status": "unknown",
            "playbook_used": None,
            "checklist_used": None,
            "course_reference": None,
        }

    playbook = routing.get("routed_to") or routing.get("selected_playbook")
    methodology_status = scope.get("playbook_status") or "unknown"
    course_parts: list[str] = []
    if playbook:
        course_parts.append(f"course_index/playbooks/{playbook}")

    course_chapter = getattr(situation, "course_chapter", None)
    if isinstance(course_chapter, int):
        course_parts.append(f"course_chapter:{course_chapter}")

    return {
        "methodology_status": methodology_status,
        "playbook_used": playbook,
        "checklist_used": "global_checklist.md" if playbook else None,
        "course_reference": "; ".join(course_parts) if course_parts else None,
    }


def _derive_v2_metadata_from_situation(situation: SpecialSituation) -> dict:
    has_sec_metadata = _situation_has_sec_metadata(situation)
    methodology = _derive_methodology_metadata(situation)

    return {
        "source_origin_name": "SEC EDGAR" if has_sec_metadata else "Legacy Evaluation",
        "intake_method": "evaluation_linked",
        "connector_key": ("sec" + "_edgar_efts") if has_sec_metadata else "legacy_evaluation",
        "intake_event_id": None,
        "evidence_level": "official_primary" if has_sec_metadata else "unknown",
        "official_source_status": "official_attached" if has_sec_metadata else "unknown",
        "duplicate_status": "unique",
        "next_follow_up_at": None,
        "discarded_reason": None,
        **methodology,
    }


def _initial_tasks_for_situation() -> list[ResearchTask]:
    descriptions = [
        "Verify official filing/source and key event terms.",
        "Confirm situation type against course methodology.",
        "Identify key dates, deadlines, or transaction milestones.",
        "Document missing information and risks.",
        "Decide whether the case should move to deep research, monitoring, or archive.",
    ]
    return [
        ResearchTask(description=description, status="open", priority=2, source="system")
        for description in descriptions
    ]

VALID_STATUSES = {
    "detected", "brief_generated", "under_investigation", "documented", "archived", "published",
}
VALID_READINESS = {
    "monitor", "not_actionable", "needs_more_work", "candidate",
}
VALID_TASK_STATUSES = {"open", "done", "deferred", "cancelled"}
VALID_SIGNAL_QUALITY = {"high", "medium", "low", "no_signal"}
VALID_PUBLIC_DRAFT_STATUSES = {"draft", "in_review", "approved", "archived"}
PUBLIC_DRAFT_STATUS_TRANSITIONS = {
    "draft": {"in_review", "archived"},
    "in_review": {"approved", "archived"},
    "approved": {"archived"},
    "archived": set(),
}
_BUY_SELL_PATTERNS = ["buy ", "sell ", "short ", "long position", "go long", "go short", "invest now", "buy now"]


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ResearchTaskRead(BaseModel):
    id: str
    research_case_id: str
    description: str
    status: str
    priority: int
    source: str | None
    notes: str | None
    created_at: str
    resolved_at: str | None

    @classmethod
    def from_orm(cls, t: ResearchTask) -> "ResearchTaskRead":
        return cls(
            id=str(t.id),
            research_case_id=str(t.research_case_id),
            description=t.description,
            status=t.status,
            priority=t.priority,
            source=t.source,
            notes=t.notes,
            created_at=t.created_at.isoformat(),
            resolved_at=t.resolved_at.isoformat() if t.resolved_at else None,
        )


class ResearchDocumentRead(BaseModel):
    id: str
    research_case_id: str | None
    historical_case_id: str | None
    doc_type: str | None
    url: str
    title: str | None
    retrieved_at: str | None
    summary: str | None
    added_by: str | None
    created_at: str

    @classmethod
    def from_orm(cls, d: ResearchDocument) -> "ResearchDocumentRead":
        return cls(
            id=str(d.id),
            research_case_id=str(d.research_case_id) if d.research_case_id else None,
            historical_case_id=str(d.historical_case_id) if d.historical_case_id else None,
            doc_type=d.doc_type,
            url=d.url,
            title=d.title,
            retrieved_at=d.retrieved_at.isoformat() if d.retrieved_at else None,
            summary=d.summary,
            added_by=d.added_by,
            created_at=d.created_at.isoformat(),
        )


class ResearchSourceRead(BaseModel):
    id: str
    research_case_id: str | None
    historical_case_id: str | None
    investment_source_id: str | None
    source_name: str
    source_url: str | None
    signal_quality: str
    notes: str | None
    created_at: str

    @classmethod
    def from_orm(cls, s: ResearchSource) -> "ResearchSourceRead":
        return cls(
            id=str(s.id),
            research_case_id=str(s.research_case_id) if s.research_case_id else None,
            historical_case_id=str(s.historical_case_id) if s.historical_case_id else None,
            investment_source_id=str(s.investment_source_id) if s.investment_source_id else None,
            source_name=s.source_name,
            source_url=s.source_url,
            signal_quality=s.signal_quality,
            notes=s.notes,
            created_at=s.created_at.isoformat(),
        )


class ResearchCaseRead(BaseModel):
    id: str
    situation_id: str | None
    status: str
    brief: dict | None
    brief_version: str | None
    playbook_version: str | None
    model_used: str | None
    run_id: str | None
    notes: str | None
    disclaimer: str
    investment_readiness: str | None
    source_origin_name: str | None
    investment_source_id: str | None
    intake_method: str | None
    connector_key: str | None
    intake_event_id: str | None
    evidence_level: str | None
    official_source_status: str | None
    methodology_status: str | None
    playbook_used: str | None
    checklist_used: str | None
    course_reference: str | None
    duplicate_status: str | None
    next_follow_up_at: str | None
    discarded_reason: str | None
    created_at: str
    updated_at: str
    tasks: list[ResearchTaskRead]
    documents: list[ResearchDocumentRead]
    sources: list[ResearchSourceRead]

    @classmethod
    def from_orm(cls, rc: ResearchCase) -> "ResearchCaseRead":
        return cls(
            id=str(rc.id),
            situation_id=str(rc.situation_id) if rc.situation_id else None,
            status=rc.status,
            brief=rc.brief,
            brief_version=rc.brief_version,
            playbook_version=rc.playbook_version,
            model_used=rc.model_used,
            run_id=str(rc.run_id) if rc.run_id else None,
            notes=rc.notes,
            disclaimer=rc.disclaimer,
            investment_readiness=rc.investment_readiness,
            source_origin_name=_nullable_str(rc.source_origin_name),
            investment_source_id=_nullable_uuid_str(rc.investment_source_id),
            intake_method=_nullable_str(rc.intake_method),
            connector_key=_nullable_str(rc.connector_key),
            intake_event_id=_nullable_str(rc.intake_event_id),
            evidence_level=_nullable_str(rc.evidence_level),
            official_source_status=_nullable_str(rc.official_source_status),
            methodology_status=_nullable_str(rc.methodology_status),
            playbook_used=_nullable_str(rc.playbook_used),
            checklist_used=_nullable_str(rc.checklist_used),
            course_reference=_nullable_str(rc.course_reference),
            duplicate_status=_nullable_str(rc.duplicate_status),
            next_follow_up_at=_nullable_datetime_str(rc.next_follow_up_at),
            discarded_reason=_nullable_str(rc.discarded_reason),
            created_at=rc.created_at.isoformat(),
            updated_at=rc.updated_at.isoformat(),
            tasks=[ResearchTaskRead.from_orm(t) for t in rc.tasks],
            documents=[ResearchDocumentRead.from_orm(d) for d in rc.documents],
            sources=[ResearchSourceRead.from_orm(s) for s in rc.sources],
        )


class ResearchCaseCreate(BaseModel):
    situation_id: str
    notes: str | None = None
    investment_readiness: str | None = None


class ResearchCaseUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None
    investment_readiness: str | None = None
    brief: dict | None = None
    brief_version: str | None = None
    playbook_version: str | None = None
    model_used: str | None = None


class ResearchTaskCreate(BaseModel):
    description: str
    priority: int = 3
    notes: str | None = None


class ResearchTaskUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


class ResearchDocumentCreate(BaseModel):
    url: str
    title: str | None = None
    doc_type: str | None = None
    summary: str | None = None
    added_by: str | None = None


class ResearchDocumentUpdate(BaseModel):
    title: str | None = None
    doc_type: str | None = None
    summary: str | None = None


class ResearchSourceCreate(BaseModel):
    source_name: str
    source_url: str | None = None
    signal_quality: str
    notes: str | None = None


class ResearchSourceUpdate(BaseModel):
    signal_quality: str | None = None
    notes: str | None = None


class PublicArticleDraftRead(BaseModel):
    id: str
    research_case_id: str
    status: str
    title: str | None
    content: str
    readiness_label: str
    disclaimer: str
    disclaimer_present: bool
    buy_sell_language_check: bool
    tags: dict | None
    created_at: str
    approved_at: str | None
    published_at: str | None
    validation_warnings: list[str]

    @classmethod
    def from_orm(cls, d: PublicArticleDraft) -> "PublicArticleDraftRead":
        return cls(
            id=str(d.id),
            research_case_id=str(d.research_case_id),
            status=d.status,
            title=d.title,
            content=d.content,
            readiness_label=d.readiness_label,
            disclaimer=d.disclaimer,
            disclaimer_present=d.disclaimer_present,
            buy_sell_language_check=d.buy_sell_language_check,
            tags=d.tags,
            created_at=d.created_at.isoformat(),
            approved_at=d.approved_at.isoformat() if d.approved_at else None,
            published_at=d.published_at.isoformat() if d.published_at else None,
            validation_warnings=validate_public_article_draft(d),
        )


class PublicArticleDraftUpdate(BaseModel):
    status: str | None = None
    title: str | None = None
    content: str | None = None
    readiness_label: str | None = None
    disclaimer: str | None = None
    tags: dict | None = None


# ── Service functions ─────────────────────────────────────────────────────────

async def create_research_case_from_situation(
    db: AsyncSession,
    situation_id: uuid.UUID,
    notes: str | None = None,
    investment_readiness: str | None = None,
) -> ResearchCase:
    sit_result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == situation_id)
    )
    situation = sit_result.scalars().first()
    if not situation:
        raise HTTPException(status_code=404, detail="Situation not found")

    existing = await db.execute(
        select(ResearchCase).where(ResearchCase.situation_id == situation_id)
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=409,
            detail=f"A research case already exists for situation {situation_id}. Use PATCH to update it.",
        )

    if investment_readiness is not None and investment_readiness not in VALID_READINESS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid investment_readiness '{investment_readiness}'. Valid values: {sorted(VALID_READINESS)}",
        )

    metadata = _derive_v2_metadata_from_situation(situation)
    has_sec_metadata = _situation_has_sec_metadata(situation)

    rc = ResearchCase(
        situation_id=situation_id,
        status="detected",
        notes=notes,
        investment_readiness=investment_readiness,
        disclaimer=_DISCLAIMER,
        **metadata,
    )
    db.add(rc)
    await db.flush()

    for task in _initial_tasks_for_situation():
        task.research_case_id = rc.id
        db.add(task)

    source = ResearchSource(
        research_case_id=rc.id,
        source_name="SEC EDGAR" if has_sec_metadata else "Linked Evaluation",
        source_url=_safe_attr_str(situation, "filing_url"),
        signal_quality="high" if has_sec_metadata else "medium",
        notes="Created from linked SpecialSituation/Evaluation. Metadata only; URL not fetched.",
    )
    db.add(source)
    await db.flush()
    await db.refresh(rc)
    return rc


async def get_research_case(db: AsyncSession, research_case_id: uuid.UUID) -> ResearchCase:
    result = await db.execute(
        select(ResearchCase)
        .where(ResearchCase.id == research_case_id)
        .options(
            selectinload(ResearchCase.tasks),
            selectinload(ResearchCase.documents),
            selectinload(ResearchCase.sources),
        )
    )
    rc = result.scalars().first()
    if not rc:
        raise HTTPException(status_code=404, detail="Research case not found")
    return rc


async def list_research_cases(
    db: AsyncSession,
    status: str | None = None,
    investment_readiness: str | None = None,
    situation_id: str | None = None,
) -> list[ResearchCase]:
    if status and status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status}'. Valid values: {sorted(VALID_STATUSES)}",
        )
    if investment_readiness and investment_readiness not in VALID_READINESS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid investment_readiness '{investment_readiness}'. Valid values: {sorted(VALID_READINESS)}",
        )

    q = select(ResearchCase).options(
        selectinload(ResearchCase.tasks),
        selectinload(ResearchCase.documents),
        selectinload(ResearchCase.sources),
    )

    if status:
        q = q.where(ResearchCase.status == status)
    if investment_readiness:
        q = q.where(ResearchCase.investment_readiness == investment_readiness)
    if situation_id:
        q = q.where(ResearchCase.situation_id == uuid.UUID(situation_id))

    q = q.order_by(ResearchCase.created_at.desc())
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_research_case(
    db: AsyncSession,
    research_case_id: uuid.UUID,
    payload: ResearchCaseUpdate,
) -> ResearchCase:
    result = await db.execute(
        select(ResearchCase)
        .where(ResearchCase.id == research_case_id)
        .options(
            selectinload(ResearchCase.tasks),
            selectinload(ResearchCase.documents),
            selectinload(ResearchCase.sources),
        )
    )
    rc = result.scalars().first()
    if not rc:
        raise HTTPException(status_code=404, detail="Research case not found")

    if payload.status is not None:
        if payload.status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{payload.status}'. Valid values: {sorted(VALID_STATUSES)}",
            )
        rc.status = payload.status

    if payload.investment_readiness is not None:
        if payload.investment_readiness not in VALID_READINESS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid investment_readiness '{payload.investment_readiness}'. Valid values: {sorted(VALID_READINESS)}",
            )
        rc.investment_readiness = payload.investment_readiness

    if payload.notes is not None:
        rc.notes = payload.notes
    if payload.brief is not None:
        rc.brief = payload.brief
    if payload.brief_version is not None:
        rc.brief_version = payload.brief_version
    if payload.playbook_version is not None:
        rc.playbook_version = payload.playbook_version
    if payload.model_used is not None:
        rc.model_used = payload.model_used

    rc.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(rc)
    return rc


async def create_task(
    db: AsyncSession,
    research_case_id: uuid.UUID,
    payload: ResearchTaskCreate,
) -> ResearchTask:
    result = await db.execute(select(ResearchCase).where(ResearchCase.id == research_case_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Research case not found")
    task = ResearchTask(
        research_case_id=research_case_id,
        description=payload.description,
        priority=payload.priority,
        notes=payload.notes,
        status="open",
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def list_tasks(db: AsyncSession, research_case_id: uuid.UUID) -> list[ResearchTask]:
    result = await db.execute(select(ResearchCase).where(ResearchCase.id == research_case_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Research case not found")
    q = select(ResearchTask).where(ResearchTask.research_case_id == research_case_id).order_by(ResearchTask.priority)
    rows = await db.execute(q)
    return list(rows.scalars().all())


async def update_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    payload: ResearchTaskUpdate,
) -> ResearchTask:
    result = await db.execute(select(ResearchTask).where(ResearchTask.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if payload.status is not None:
        if payload.status not in VALID_TASK_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{payload.status}'. Valid values: {sorted(VALID_TASK_STATUSES)}",
            )
        task.status = payload.status
        if payload.status == "done":
            task.resolved_at = datetime.now(timezone.utc)
        elif task.resolved_at is not None:
            task.resolved_at = None
    if payload.notes is not None:
        task.notes = payload.notes
    await db.flush()
    await db.refresh(task)
    return task


async def create_document(
    db: AsyncSession,
    research_case_id: uuid.UUID,
    payload: ResearchDocumentCreate,
) -> ResearchDocument:
    result = await db.execute(select(ResearchCase).where(ResearchCase.id == research_case_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Research case not found")
    doc = ResearchDocument(
        research_case_id=research_case_id,
        url=payload.url,
        title=payload.title,
        doc_type=payload.doc_type,
        summary=payload.summary,
        added_by=payload.added_by,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


async def list_documents(db: AsyncSession, research_case_id: uuid.UUID) -> list[ResearchDocument]:
    result = await db.execute(select(ResearchCase).where(ResearchCase.id == research_case_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Research case not found")
    q = select(ResearchDocument).where(ResearchDocument.research_case_id == research_case_id).order_by(ResearchDocument.created_at)
    rows = await db.execute(q)
    return list(rows.scalars().all())


async def create_source(
    db: AsyncSession,
    research_case_id: uuid.UUID,
    payload: ResearchSourceCreate,
) -> ResearchSource:
    result = await db.execute(select(ResearchCase).where(ResearchCase.id == research_case_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Research case not found")
    if payload.signal_quality not in VALID_SIGNAL_QUALITY:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid signal_quality '{payload.signal_quality}'. Valid values: {sorted(VALID_SIGNAL_QUALITY)}",
        )
    src = ResearchSource(
        research_case_id=research_case_id,
        source_name=payload.source_name,
        source_url=payload.source_url,
        signal_quality=payload.signal_quality,
        notes=payload.notes,
    )
    db.add(src)
    await db.flush()
    await db.refresh(src)
    return src


async def list_sources(db: AsyncSession, research_case_id: uuid.UUID) -> list[ResearchSource]:
    result = await db.execute(select(ResearchCase).where(ResearchCase.id == research_case_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Research case not found")
    q = select(ResearchSource).where(ResearchSource.research_case_id == research_case_id).order_by(ResearchSource.created_at)
    rows = await db.execute(q)
    return list(rows.scalars().all())


async def patch_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    payload: ResearchDocumentUpdate,
) -> ResearchDocument:
    result = await db.execute(select(ResearchDocument).where(ResearchDocument.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if payload.title is not None:
        doc.title = payload.title
    if payload.doc_type is not None:
        doc.doc_type = payload.doc_type
    if payload.summary is not None:
        doc.summary = payload.summary
    await db.flush()
    await db.refresh(doc)
    return doc


async def patch_source(
    db: AsyncSession,
    source_id: uuid.UUID,
    payload: ResearchSourceUpdate,
) -> ResearchSource:
    result = await db.execute(select(ResearchSource).where(ResearchSource.id == source_id))
    src = result.scalars().first()
    if not src:
        raise HTTPException(status_code=404, detail="Source not found")
    if payload.signal_quality is not None:
        if payload.signal_quality not in VALID_SIGNAL_QUALITY:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid signal_quality '{payload.signal_quality}'. Valid values: {sorted(VALID_SIGNAL_QUALITY)}",
            )
        src.signal_quality = payload.signal_quality
    if payload.notes is not None:
        src.notes = payload.notes
    await db.flush()
    await db.refresh(src)
    return src


# ── Phase 5 — Public Article Drafts ───────────────────────────────────────────

_PUBLIC_BLOCKED_TERMS = [
    "internal id",
    "research_case_id",
    "situation_id",
    "run_id",
    "agent_runs",
    "ai_usage",
    "api/",
    "/api/",
    "backend",
    "frontend",
    "database",
    "postgres",
    "vps",
    "tailscale",
    "file path",
]


def _contains_buy_sell_language(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    extra_patterns = [
        "purchase shares",
        "take a position",
        "recommend buying",
        "recommend selling",
        "strong buy",
        "target price",
    ]
    return any(p in lowered for p in [*_BUY_SELL_PATTERNS, *extra_patterns])


def _public_text_safe(value: object) -> str:
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if _contains_buy_sell_language(text):
        return "[Removed during public draft safety review.]"
    lowered = text.lower()
    if any(term in lowered for term in _PUBLIC_BLOCKED_TERMS):
        return "[Removed during public draft safety review.]"
    return text


def _brief_text(brief: dict | None, key: str) -> str:
    if not isinstance(brief, dict):
        return ""
    return _public_text_safe(brief.get(key))


def _build_public_article_content(rc: ResearchCase) -> tuple[str, str]:
    brief = rc.brief if isinstance(rc.brief, dict) else {}
    title_seed = (
        _brief_text(brief, "executive_summary")
        or _brief_text(brief, "situation_type")
        or "Public research note"
    )
    title = title_seed.splitlines()[0][:120].strip(" #-")
    if not title:
        title = "Public research note"

    sections: list[tuple[str, str]] = [
        ("Overview", _brief_text(brief, "executive_summary")),
        ("Situation", _brief_text(brief, "situation_type")),
        ("Why It May Be Interesting", _brief_text(brief, "why_interesting")),
        ("Company Context", _brief_text(brief, "company_context")),
        ("Timeline", _brief_text(brief, "timeline")),
        ("Key Risks", _brief_text(brief, "risk_analysis")),
        ("Information Still To Verify", _brief_text(brief, "missing_information")),
        ("Research Readiness", _brief_text(brief, "investment_readiness_note")),
        ("Public Summary", _brief_text(brief, "public_summary_draft")),
    ]

    lines: list[str] = []
    for heading, body in sections:
        if body:
            lines.append(f"## {heading}")
            lines.append("")
            lines.append(body)
            lines.append("")

    open_tasks = [_public_text_safe(t.description) for t in rc.tasks if t.status == "open"]
    open_tasks = [t for t in open_tasks if t and not t.startswith("[Removed")]
    if open_tasks:
        lines.append("## Open Research Questions")
        lines.append("")
        for task in open_tasks[:8]:
            lines.append(f"- {task}")
        lines.append("")

    public_documents = []
    for doc in rc.documents:
        label = _public_text_safe(doc.title) or _public_text_safe(doc.doc_type) or "Public reference"
        url = _public_text_safe(doc.url)
        if url:
            public_documents.append((label, url))
    if public_documents:
        lines.append("## Public References")
        lines.append("")
        for label, url in public_documents[:10]:
            lines.append(f"- [{label}]({url})")
        lines.append("")

    public_sources = []
    for src in rc.sources:
        name = _public_text_safe(src.source_name)
        url = _public_text_safe(src.source_url)
        if name:
            public_sources.append((name, url))
    if public_sources:
        lines.append("## Sources Followed")
        lines.append("")
        for name, url in public_sources[:10]:
            lines.append(f"- [{name}]({url})" if url else f"- {name}")
        lines.append("")

    lines.append(_DISCLAIMER)
    content = "\n".join(lines).strip()
    return title, content


def validate_public_article_draft(draft: PublicArticleDraft) -> list[str]:
    warnings: list[str] = []
    if not (draft.title or "").strip():
        warnings.append("Title is required before approval.")
    if not (draft.content or "").strip():
        warnings.append("Public body is required before approval.")
    if draft.disclaimer != _DISCLAIMER:
        warnings.append("Canonical disclaimer is missing or modified.")
    if _DISCLAIMER not in (draft.content or ""):
        warnings.append("Canonical disclaimer must appear in the public body.")
    if _contains_buy_sell_language(draft.title) or _contains_buy_sell_language(draft.content):
        warnings.append("Buy/sell recommendation language detected.")
    lowered = f"{draft.title or ''}\n{draft.content or ''}".lower()
    if any(term in lowered for term in _PUBLIC_BLOCKED_TERMS):
        warnings.append("Public draft contains internal or operational metadata.")
    return warnings


def _refresh_public_draft_flags(draft: PublicArticleDraft) -> None:
    draft.disclaimer_present = draft.disclaimer == _DISCLAIMER and _DISCLAIMER in (draft.content or "")
    draft.buy_sell_language_check = not (
        _contains_buy_sell_language(draft.title) or _contains_buy_sell_language(draft.content)
    )


def _validate_public_draft_status_transition(current_status: str, next_status: str) -> None:
    if next_status == current_status:
        return
    allowed = PUBLIC_DRAFT_STATUS_TRANSITIONS.get(current_status, set())
    if next_status in allowed:
        return
    if current_status == "draft" and next_status == "approved":
        raise HTTPException(status_code=422, detail="Draft must be moved to in_review before approval.")
    if current_status == "archived":
        raise HTTPException(status_code=422, detail="Archived drafts cannot transition back to another status.")
    raise HTTPException(
        status_code=422,
        detail=f"Invalid status transition from '{current_status}' to '{next_status}'.",
    )


async def create_public_article_draft(
    db: AsyncSession,
    research_case_id: uuid.UUID,
) -> PublicArticleDraft:
    rc = await get_research_case(db, research_case_id)
    title, content = _build_public_article_content(rc)
    readiness = rc.investment_readiness if rc.investment_readiness in VALID_READINESS else "needs_more_work"
    draft = PublicArticleDraft(
        research_case_id=research_case_id,
        status="draft",
        title=title,
        content=content,
        readiness_label=readiness,
        disclaimer=_DISCLAIMER,
        disclaimer_present=_DISCLAIMER in content,
        buy_sell_language_check=not _contains_buy_sell_language(f"{title}\n{content}"),
        tags={"values": []},
    )
    db.add(draft)
    await db.flush()
    await db.refresh(draft)
    return draft


async def list_public_article_drafts(
    db: AsyncSession,
    status: str | None = None,
    research_case_id: uuid.UUID | None = None,
) -> list[PublicArticleDraft]:
    if status is not None and status not in VALID_PUBLIC_DRAFT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status}'. Valid values: {sorted(VALID_PUBLIC_DRAFT_STATUSES)}",
        )
    q = select(PublicArticleDraft)
    if status:
        q = q.where(PublicArticleDraft.status == status)
    if research_case_id:
        q = q.where(PublicArticleDraft.research_case_id == research_case_id)
    q = q.order_by(PublicArticleDraft.created_at.desc())
    rows = await db.execute(q)
    return list(rows.scalars().all())


async def get_public_article_draft(db: AsyncSession, draft_id: uuid.UUID) -> PublicArticleDraft:
    result = await db.execute(select(PublicArticleDraft).where(PublicArticleDraft.id == draft_id))
    draft = result.scalars().first()
    if not draft:
        raise HTTPException(status_code=404, detail="Public article draft not found")
    return draft


async def update_public_article_draft(
    db: AsyncSession,
    draft_id: uuid.UUID,
    payload: PublicArticleDraftUpdate,
) -> PublicArticleDraft:
    draft = await get_public_article_draft(db, draft_id)

    next_status = payload.status if payload.status is not None else draft.status
    if next_status not in VALID_PUBLIC_DRAFT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{next_status}'. Valid values: {sorted(VALID_PUBLIC_DRAFT_STATUSES)}",
        )
    if payload.status is not None:
        _validate_public_draft_status_transition(draft.status, next_status)

    if payload.title is not None:
        draft.title = payload.title
    if payload.content is not None:
        draft.content = payload.content
    if payload.readiness_label is not None:
        if payload.readiness_label not in VALID_READINESS:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid readiness_label '{payload.readiness_label}'. Valid values: {sorted(VALID_READINESS)}",
            )
        draft.readiness_label = payload.readiness_label
    if payload.disclaimer is not None:
        draft.disclaimer = payload.disclaimer
    if payload.tags is not None:
        draft.tags = payload.tags

    _refresh_public_draft_flags(draft)
    if payload.status is not None:
        if payload.status == "approved":
            warnings = validate_public_article_draft(draft)
            if warnings:
                raise HTTPException(status_code=422, detail={"validation_warnings": warnings})
            if draft.status != "approved":
                draft.approved_at = datetime.now(timezone.utc)
        draft.status = payload.status

    await db.flush()
    await db.refresh(draft)
    return draft


def render_public_article_markdown(draft: PublicArticleDraft) -> str:
    title = (draft.title or "Public research note").strip()
    body = (draft.content or "").strip()
    if _DISCLAIMER not in body:
        body = f"{body}\n\n{_DISCLAIMER}".strip()
    return f"# {title}\n\n{body}\n"


_BRIEF_SECTIONS = [
    "executive_summary",
    "situation_type",
    "why_interesting",
    "methodology_reference",
    "company_context",
    "board_management",
    "key_documents",
    "timeline",
    "risk_analysis",
    "verify_before_investing",
    "missing_information",
    "source_intelligence",
    "investment_readiness_note",
    "public_summary_draft",
]

_BRIEF_SYSTEM = (
    "You are a private investment research assistant. "
    "You write structured, factual research notes for a single analyst (not for distribution). "
    "Use only the context provided — do not invent facts, do not fetch URLs, do not use external knowledge beyond what is stated. "
    "Write in clear, direct English. "
    "Never use buy/sell language. Never give financial advice. "
    "Every section must end with: '— Este análisis es educativo. No es asesoramiento financiero.'"
)


def _build_brief_prompt(rc: ResearchCase, situation: SpecialSituation | None) -> tuple[str, list[str]]:
    """Build the brief generation prompt and return (prompt_text, source_context_used)."""
    source_context_used: list[str] = []
    lines: list[str] = []

    lines.append("=== RESEARCH BRIEF GENERATION REQUEST ===")
    lines.append("")
    lines.append(f"Research Case ID: {rc.id}")
    lines.append(f"Status: {rc.status}")
    if rc.investment_readiness:
        lines.append(f"Current Readiness Assessment: {rc.investment_readiness}")
    lines.append("")

    if situation:
        lines.append("--- LINKED SITUATION ---")
        lines.append(f"Company: {situation.company_name}")
        if situation.ticker:
            lines.append(f"Ticker: {situation.ticker}")
        if situation.filing_type:
            lines.append(f"Filing Type: {situation.filing_type}")
        if situation.situation_type:
            lines.append(f"Detected Situation Type: {situation.situation_type}")
        if situation.filing_url:
            lines.append(f"Filing URL (do not fetch): {situation.filing_url}")
        if situation.detected_at:
            lines.append(f"Detected At: {situation.detected_at.isoformat()}")
        eval_data = situation.evaluation or {}
        if eval_data.get("summary"):
            lines.append(f"Evaluator Summary: {eval_data['summary']}")
        if eval_data.get("situation_type"):
            lines.append(f"Evaluator Situation Type: {eval_data['situation_type']}")
        if eval_data.get("recommendation"):
            lines.append(f"Evaluator Recommendation: {eval_data['recommendation']}")
        if eval_data.get("risk_flags"):
            lines.append(f"Risk Flags: {', '.join(eval_data['risk_flags'])}")
        if eval_data.get("missing_documents"):
            lines.append(f"Missing Documents: {', '.join(eval_data['missing_documents'])}")
        source_context_used.append("linked_situation")
        lines.append("")

    if rc.notes:
        lines.append("--- ANALYST NOTES ---")
        lines.append(rc.notes)
        source_context_used.append("analyst_notes")
        lines.append("")

    open_tasks = [t for t in rc.tasks if t.status not in ("done", "cancelled")]
    if open_tasks:
        lines.append("--- OPEN RESEARCH TASKS ---")
        for t in sorted(open_tasks, key=lambda x: x.priority):
            lines.append(f"- [P{t.priority}] {t.description}" + (f" ({t.notes})" if t.notes else ""))
        source_context_used.append("open_tasks")
        lines.append("")

    if rc.documents:
        lines.append("--- KEY DOCUMENTS (URLs not fetched — titles/summaries only) ---")
        for d in rc.documents:
            doc_line = f"- [{d.doc_type or 'other'}] {d.title or d.url}"
            if d.summary:
                doc_line += f": {d.summary}"
            lines.append(doc_line)
        source_context_used.append("documents")
        lines.append("")

    if rc.sources:
        lines.append("--- SOURCE INTELLIGENCE ---")
        for s in rc.sources:
            src_line = f"- [{s.signal_quality}] {s.source_name}"
            if s.notes:
                src_line += f": {s.notes}"
            lines.append(src_line)
        source_context_used.append("sources")
        lines.append("")

    lines.append("=== INSTRUCTIONS ===")
    lines.append("")
    lines.append(
        "Generate a structured research brief as a JSON object with exactly these 14 keys. "
        "Each value must be a non-empty string (3–10 sentences). "
        "Base ALL content strictly on the context above. "
        "Do not invent company facts not mentioned above. "
        "Do not fetch any URLs. "
        "Do not use buy/sell language."
    )
    lines.append("")
    lines.append("Required JSON keys:")
    for key in _BRIEF_SECTIONS:
        lines.append(f"  - {key}")
    lines.append("")
    lines.append(
        'Respond with ONLY a valid JSON object. No markdown, no code fences, no preamble. '
        'Example structure: {"executive_summary": "...", "situation_type": "...", ...}'
    )

    return "\n".join(lines), source_context_used


def _parse_brief_json(raw: str) -> tuple[dict[str, str], list[str]]:
    """Parse AI response into brief dict. Returns (sections_dict, warnings)."""
    warnings: list[str] = []
    text = raw.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        warnings.append(f"JSON parse error: {e}. Raw response stored in executive_summary.")
        return {"executive_summary": raw}, warnings

    if not isinstance(data, dict):
        warnings.append("AI response was not a JSON object.")
        return {"executive_summary": raw}, warnings

    result: dict[str, str] = {}
    for key in _BRIEF_SECTIONS:
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            result[key] = val.strip()
        else:
            result[key] = ""
            warnings.append(f"Section '{key}' missing or empty in AI response.")

    extra_keys = [k for k in data if k not in _BRIEF_SECTIONS]
    if extra_keys:
        warnings.append(f"Unexpected keys ignored: {extra_keys}")

    return result, warnings


async def generate_brief_preview(
    db: AsyncSession,
    research_case_id: uuid.UUID,
) -> dict:
    """
    Generate an AI research brief preview. Does NOT save to DB.
    Returns preview sections, source context used, warnings, and usage metadata.
    """
    result = await db.execute(
        select(ResearchCase)
        .where(ResearchCase.id == research_case_id)
        .options(
            selectinload(ResearchCase.tasks),
            selectinload(ResearchCase.documents),
            selectinload(ResearchCase.sources),
        )
    )
    rc = result.scalars().first()
    if not rc:
        raise HTTPException(status_code=404, detail="Research case not found")

    situation: SpecialSituation | None = None
    if rc.situation_id:
        sit_result = await db.execute(
            select(SpecialSituation).where(SpecialSituation.id == rc.situation_id)
        )
        situation = sit_result.scalars().first()

    prompt, source_context_used = _build_brief_prompt(rc, situation)
    text, usage = await complete_with_usage(prompt, system=_BRIEF_SYSTEM, max_tokens=4000)
    sections, warnings = _parse_brief_json(text)

    return {
        "saved_to_db": False,
        "preview": sections,
        "source_context_used": source_context_used,
        "warnings": warnings,
        "disclaimer": _DISCLAIMER,
        "usage": usage,
    }


# ── Quality Preview ───────────────────────────────────────────────────────────

_QUALITY_SYSTEM = (
    "You are a private investment research quality reviewer. "
    "You evaluate the completeness and readiness of a research case based solely on the provided data. "
    "Use only the context provided — do not invent facts, do not fetch URLs, do not use external knowledge. "
    "Write concisely and factually. "
    "Never use buy/sell language. Never give financial advice. "
    "Never suggest 'published' status unless the case is documented with a complete brief and no open tasks. "
    "If data is insufficient, prefer 'needs_more_work' for readiness. "
    "Return your assessment as a single JSON object with exactly these keys: "
    "quality_checklist (object), suggested_status (string), suggested_readiness (string), rationale (string). "
    "quality_checklist must have these boolean keys: "
    "brief_completeness, missing_information_noted, key_risks_identified, "
    "documents_attached, tasks_open, sources_recorded, disclaimer_present, "
    "no_buy_sell_language, readiness_label_valid. "
    "suggested_status must be one of: detected, brief_generated, under_investigation, documented, archived, published. "
    "suggested_readiness must be one of: monitor, not_actionable, needs_more_work, candidate."
)

_QUALITY_CHECKLIST_KEYS = [
    "brief_completeness",
    "missing_information_noted",
    "key_risks_identified",
    "documents_attached",
    "tasks_open",
    "sources_recorded",
    "disclaimer_present",
    "no_buy_sell_language",
    "readiness_label_valid",
]


def _build_quality_prompt(rc: ResearchCase, situation: SpecialSituation | None) -> str:
    lines: list[str] = []
    lines.append("=== RESEARCH QUALITY REVIEW REQUEST ===")
    lines.append("")
    lines.append(f"Research Case ID: {rc.id}")
    lines.append(f"Current Status: {rc.status}")
    lines.append(f"Current Readiness: {rc.investment_readiness or 'not set'}")
    lines.append(f"Disclaimer present: {'yes' if rc.disclaimer else 'no'}")
    lines.append("")

    if situation:
        lines.append("--- LINKED SITUATION ---")
        lines.append(f"Company: {situation.company_name}")
        if situation.ticker:
            lines.append(f"Ticker: {situation.ticker}")
        if situation.situation_type:
            lines.append(f"Situation Type: {situation.situation_type}")
        eval_data = situation.evaluation or {}
        if eval_data.get("summary"):
            lines.append(f"Evaluator Summary: {eval_data['summary']}")
        if eval_data.get("risk_flags"):
            lines.append(f"Risk Flags: {', '.join(eval_data['risk_flags'])}")
        lines.append("")

    if rc.notes:
        lines.append("--- ANALYST NOTES ---")
        lines.append(rc.notes)
        lines.append("")

    brief = rc.brief or {}
    filled = [k for k in _BRIEF_SECTIONS if brief.get(k, "").strip()]
    lines.append(f"--- BRIEF: {len(filled)}/{len(_BRIEF_SECTIONS)} sections filled ---")
    if filled:
        lines.append(f"Filled sections: {', '.join(filled)}")
    missing = [k for k in _BRIEF_SECTIONS if k not in filled]
    if missing:
        lines.append(f"Missing sections: {', '.join(missing)}")
    lines.append("")

    open_tasks = [t for t in rc.tasks if t.status not in ("done", "cancelled")]
    done_tasks = [t for t in rc.tasks if t.status == "done"]
    lines.append(f"--- TASKS: {len(open_tasks)} open, {len(done_tasks)} done ---")
    for t in open_tasks:
        lines.append(f"- [OPEN P{t.priority}] {t.description}")
    lines.append("")

    lines.append(f"--- DOCUMENTS: {len(rc.documents)} attached (URLs not fetched) ---")
    for d in rc.documents:
        lines.append(f"- [{d.doc_type or 'other'}] {d.title or d.url}")
    lines.append("")

    lines.append(f"--- SOURCES: {len(rc.sources)} recorded ---")
    for s in rc.sources:
        lines.append(f"- [{s.signal_quality}] {s.source_name}")
    lines.append("")

    lines.append("=== INSTRUCTIONS ===")
    lines.append(
        "Evaluate this research case and return a JSON object with these keys: "
        "quality_checklist, suggested_status, suggested_readiness, rationale. "
        "quality_checklist must contain boolean values for: "
        + ", ".join(_QUALITY_CHECKLIST_KEYS) + ". "
        "Respond with ONLY a valid JSON object. No markdown, no code fences, no preamble."
    )

    return "\n".join(lines)


def _parse_quality_json(raw: str) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    text = raw.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        warnings.append(f"JSON parse error: {e}. Returning defaults.")
        return _quality_defaults(), warnings

    if not isinstance(data, dict):
        warnings.append("AI response was not a JSON object. Returning defaults.")
        return _quality_defaults(), warnings

    checklist_raw = data.get("quality_checklist", {})
    if not isinstance(checklist_raw, dict):
        warnings.append("quality_checklist missing or not an object. Using defaults.")
        checklist_raw = {}

    checklist: dict[str, bool] = {}
    for key in _QUALITY_CHECKLIST_KEYS:
        val = checklist_raw.get(key)
        checklist[key] = bool(val) if isinstance(val, bool) else False
        if not isinstance(val, bool):
            warnings.append(f"Checklist key '{key}' missing or non-boolean; defaulted to false.")

    suggested_status = data.get("suggested_status", "detected")
    if suggested_status == "published":
        fallback = "documented" if checklist.get("brief_completeness") else "under_investigation"
        warnings.append(
            f"published status cannot be suggested by AI; manual editorial approval is required. "
            f"Downgraded to '{fallback}'."
        )
        suggested_status = fallback
    elif suggested_status not in VALID_STATUSES:
        warnings.append(f"suggested_status '{suggested_status}' invalid; defaulted to 'detected'.")
        suggested_status = "detected"

    suggested_readiness = data.get("suggested_readiness", "needs_more_work")
    if suggested_readiness not in VALID_READINESS:
        warnings.append(f"suggested_readiness '{suggested_readiness}' invalid; defaulted to 'needs_more_work'.")
        suggested_readiness = "needs_more_work"

    rationale = data.get("rationale", "")
    if not isinstance(rationale, str):
        rationale = ""
        warnings.append("rationale missing or not a string.")

    return {
        "quality_checklist": checklist,
        "suggested_status": suggested_status,
        "suggested_readiness": suggested_readiness,
        "rationale": rationale,
    }, warnings


def _quality_defaults() -> dict:
    return {
        "quality_checklist": {k: False for k in _QUALITY_CHECKLIST_KEYS},
        "suggested_status": "detected",
        "suggested_readiness": "needs_more_work",
        "rationale": "",
    }


async def generate_quality_preview(
    db: AsyncSession,
    research_case_id: uuid.UUID,
) -> dict:
    """
    Generate an AI quality checklist and readiness suggestion. Does NOT save to DB.
    """
    result = await db.execute(
        select(ResearchCase)
        .where(ResearchCase.id == research_case_id)
        .options(
            selectinload(ResearchCase.tasks),
            selectinload(ResearchCase.documents),
            selectinload(ResearchCase.sources),
        )
    )
    rc = result.scalars().first()
    if not rc:
        raise HTTPException(status_code=404, detail="Research case not found")

    situation: SpecialSituation | None = None
    if rc.situation_id:
        sit_result = await db.execute(
            select(SpecialSituation).where(SpecialSituation.id == rc.situation_id)
        )
        situation = sit_result.scalars().first()

    prompt = _build_quality_prompt(rc, situation)
    text, usage = await complete_with_usage(prompt, system=_QUALITY_SYSTEM, max_tokens=1200)
    parsed, warnings = _parse_quality_json(text)

    return {
        "saved_to_db": False,
        "quality_checklist": parsed["quality_checklist"],
        "suggested_status": parsed["suggested_status"],
        "suggested_readiness": parsed["suggested_readiness"],
        "rationale": parsed["rationale"],
        "warnings": warnings,
        "disclaimer": _DISCLAIMER,
        "usage": usage,
    }


# ── Document Analysis Preview ─────────────────────────────────────────────────

_MIN_SNIPPET_LENGTH = 50

_ANALYSIS_SYSTEM = (
    "You are a private investment research assistant helping an analyst review a document excerpt. "
    "The analyst has pasted a text snippet from a document — analyse it strictly based on the provided text. "
    "Do NOT attempt to fetch any URLs. Treat any URL as a metadata label only. "
    "Do not invent facts not stated in the snippet or case context. "
    "Write in clear, factual English. Never use buy/sell language. Never give financial advice. "
    "Return your analysis as a single JSON object with exactly these keys: "
    "summary (string), key_points (array of strings), risks (array of strings), "
    "timeline_items (array of strings), missing_information (string), "
    "suggested_research_tasks (array of strings), source_usefulness (string)."
)

_ANALYSIS_KEYS = ["summary", "key_points", "risks", "timeline_items", "missing_information", "suggested_research_tasks", "source_usefulness"]


def _parse_analysis_json(raw: str) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    text = raw.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        warnings.append(f"JSON parse error: {e}. Returning defaults.")
        return _analysis_defaults(), warnings

    if not isinstance(data, dict):
        warnings.append("AI response was not a JSON object. Returning defaults.")
        return _analysis_defaults(), warnings

    result: dict = {}
    for key in _ANALYSIS_KEYS:
        val = data.get(key)
        if key in ("key_points", "risks", "timeline_items", "suggested_research_tasks"):
            result[key] = val if isinstance(val, list) else []
        else:
            result[key] = val if isinstance(val, str) else ""

    return result, warnings


def _analysis_defaults() -> dict:
    return {
        "summary": "",
        "key_points": [],
        "risks": [],
        "timeline_items": [],
        "missing_information": "",
        "suggested_research_tasks": [],
        "source_usefulness": "",
    }


def _build_analysis_prompt(doc: ResearchDocument, rc: ResearchCase | None) -> str:
    lines: list[str] = []
    lines.append("=== DOCUMENT SNIPPET ANALYSIS REQUEST ===")
    lines.append("")
    lines.append(f"Document ID: {doc.id}")
    if doc.title:
        lines.append(f"Document Title: {doc.title}")
    if doc.doc_type:
        lines.append(f"Document Type: {doc.doc_type}")
    lines.append(f"Document URL (metadata only — DO NOT attempt to fetch or access this URL. Treat it as a label only): {doc.url}")
    lines.append("")

    if rc:
        lines.append("--- RESEARCH CASE CONTEXT ---")
        lines.append(f"Case Status: {rc.status}")
        if rc.investment_readiness:
            lines.append(f"Readiness: {rc.investment_readiness}")
        if rc.notes:
            lines.append(f"Analyst Notes: {rc.notes}")
        lines.append("")

    lines.append("--- DOCUMENT SNIPPET (analyst-pasted text) ---")
    lines.append(doc.summary)
    lines.append("")
    lines.append("=== INSTRUCTIONS ===")
    lines.append(
        "Analyse the snippet above and return a JSON object with exactly these keys: "
        "summary, key_points (array), risks (array), timeline_items (array), "
        "missing_information, suggested_research_tasks (array), source_usefulness. "
        "Base ALL content strictly on the snippet and context above. "
        "Do not fetch any URLs. Do not use buy/sell language. "
        "Respond with ONLY a valid JSON object. No markdown, no code fences."
    )
    return "\n".join(lines)


def _strip_buy_sell(analysis: dict, warnings: list[str]) -> tuple[dict, list[str]]:
    for key in ("summary", "source_usefulness", "missing_information"):
        val = analysis.get(key, "")
        if isinstance(val, str):
            lower = val.lower()
            if any(p in lower for p in _BUY_SELL_PATTERNS):
                analysis[key] = "[Content removed: contained investment directive language.]"
                warnings.append(f"Field '{key}' contained buy/sell directive language and was removed.")
    for list_key in ("key_points", "risks", "timeline_items", "suggested_research_tasks"):
        cleaned = []
        for item in analysis.get(list_key, []):
            if isinstance(item, str) and any(p in item.lower() for p in _BUY_SELL_PATTERNS):
                warnings.append(f"Item in '{list_key}' contained buy/sell directive language and was removed.")
            else:
                cleaned.append(item)
        analysis[list_key] = cleaned
    return analysis, warnings


async def generate_document_analysis_preview(
    db: AsyncSession,
    document_id: uuid.UUID,
) -> dict:
    result = await db.execute(select(ResearchDocument).where(ResearchDocument.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    snippet = (doc.summary or "").strip()
    if len(snippet) < _MIN_SNIPPET_LENGTH:
        return {
            "saved_to_db": False,
            "document_id": str(document_id),
            "analysis": _analysis_defaults(),
            "warnings": [
                f"Snippet is too short (minimum {_MIN_SNIPPET_LENGTH} characters). "
                "Paste a text excerpt into the snippet field before generating analysis."
            ],
            "disclaimer": _DISCLAIMER,
            "usage": {},
        }

    rc: ResearchCase | None = None
    if doc.research_case_id:
        rc_result = await db.execute(select(ResearchCase).where(ResearchCase.id == doc.research_case_id))
        rc = rc_result.scalars().first()

    prompt = _build_analysis_prompt(doc, rc)
    text, usage = await complete_with_usage(prompt, system=_ANALYSIS_SYSTEM, max_tokens=1500)
    analysis, warnings = _parse_analysis_json(text)
    analysis, warnings = _strip_buy_sell(analysis, warnings)

    return {
        "saved_to_db": False,
        "document_id": str(document_id),
        "analysis": analysis,
        "warnings": warnings,
        "disclaimer": _DISCLAIMER,
        "usage": usage,
    }


# ── Source Intelligence Preview ───────────────────────────────────────────────

_SOURCE_INTEL_SUGGESTION_KEYS = ["action", "source_name", "source_type", "reason", "evidence_from_case", "confidence", "manual_review_required"]
_SOURCE_INTEL_SCORE_KEYS = ["source_id", "source_name", "signal_quality", "usefulness_reason", "suggested_follow_up"]
_VALID_SUGGESTION_ACTIONS = {"add", "update_priority", "deactivate"}
_VALID_CONFIDENCE = {"high", "medium", "low"}


def _build_source_intel_prompt(rc: ResearchCase, situation: "SpecialSituation | None") -> str:
    lines: list[str] = []
    lines.append("=== SOURCE INTELLIGENCE REVIEW REQUEST ===")
    lines.append("")
    lines.append(f"Research Case ID: {rc.id}")
    lines.append(f"Case Status: {rc.status}")
    if rc.investment_readiness:
        lines.append(f"Investment Readiness: {rc.investment_readiness}")
    if rc.notes:
        lines.append(f"Analyst Notes: {rc.notes}")

    if situation:
        lines.append("")
        lines.append("--- LINKED SITUATION ---")
        lines.append(f"Company: {situation.company_name}")
        if situation.ticker:
            lines.append(f"Ticker: {situation.ticker}")
        if situation.filing_type:
            lines.append(f"Filing Type: {situation.filing_type}")
        if getattr(situation, "situation_type", None):
            lines.append(f"Situation Type: {situation.situation_type}")

    lines.append("")
    lines.append("--- RECORDED SOURCES ---")
    if rc.sources:
        for s in rc.sources:
            lines.append(f"  ID: {s.id}")
            lines.append(f"  Name: {s.source_name}")
            lines.append(f"  Signal Quality: {s.signal_quality}")
            if s.source_url:
                lines.append(f"  URL (metadata only — DO NOT fetch): {s.source_url}")
            if s.notes:
                lines.append(f"  Analyst Notes: {s.notes}")
            lines.append("")
    else:
        lines.append("  (none recorded)")
        lines.append("")

    lines.append("--- RECORDED DOCUMENTS ---")
    if rc.documents:
        for d in rc.documents:
            parts = [f"  [{d.doc_type or 'unknown'}] {d.title or '(no title)'}"]
            if d.url:
                parts.append(f"— URL (metadata only): {d.url}")
            lines.append(" ".join(parts))
    else:
        lines.append("  (none recorded)")
    lines.append("")

    lines.append("--- OPEN TASKS ---")
    open_tasks = [t for t in rc.tasks if t.status == "open"]
    if open_tasks:
        for t in open_tasks:
            lines.append(f"  [{t.priority}] {t.description}")
    else:
        lines.append("  (none open)")
    lines.append("")

    if rc.brief:
        lines.append("--- RESEARCH BRIEF CONTEXT (first 500 chars of executive summary) ---")
        exec_summary = rc.brief.get("executive_summary", "")
        if exec_summary:
            lines.append(str(exec_summary)[:500])
        else:
            lines.append("(not written)")
        lines.append("")

    lines.append("=== INSTRUCTIONS ===")
    lines.append(
        "Based ONLY on the data above, score each recorded source and suggest additional sources relevant to this case. "
        "Do NOT fetch any URLs. Do NOT use buy/sell language. "
        "Return a single JSON object with keys: source_scores, suggestions, warnings. "
        "Respond with ONLY a valid JSON object. No markdown, no code fences."
    )
    return "\n".join(lines)


def _parse_source_intel_json(raw: str, sources: list) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    text = raw.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        warnings.append(f"JSON parse error: {e}. Returning defaults.")
        return _source_intel_defaults(sources), warnings

    if not isinstance(data, dict):
        warnings.append("AI response was not a JSON object. Returning defaults.")
        return _source_intel_defaults(sources), warnings

    raw_scores = data.get("source_scores", [])
    if not isinstance(raw_scores, list):
        raw_scores = []
        warnings.append("source_scores missing or not a list; using defaults.")

    source_scores = []
    for item in raw_scores:
        if not isinstance(item, dict):
            continue
        score = {
            "source_id": str(item.get("source_id", "")),
            "source_name": str(item.get("source_name", "")),
            "signal_quality": str(item.get("signal_quality", "medium")),
            "usefulness_reason": str(item.get("usefulness_reason", "")),
            "suggested_follow_up": str(item.get("suggested_follow_up", "")),
        }
        if any(p in score["usefulness_reason"].lower() for p in _BUY_SELL_PATTERNS):
            score["usefulness_reason"] = "[Content removed: contained investment directive language.]"
            warnings.append("usefulness_reason contained buy/sell directive language and was removed.")
        if any(p in score["suggested_follow_up"].lower() for p in _BUY_SELL_PATTERNS):
            score["suggested_follow_up"] = "[Content removed: contained investment directive language.]"
            warnings.append("suggested_follow_up contained buy/sell directive language and was removed.")
        source_scores.append(score)

    raw_suggestions = data.get("suggestions", [])
    if not isinstance(raw_suggestions, list):
        raw_suggestions = []
        warnings.append("suggestions missing or not a list.")

    suggestions = []
    for item in raw_suggestions:
        if not isinstance(item, dict):
            continue
        action = str(item.get("action", "add"))
        if action not in _VALID_SUGGESTION_ACTIONS:
            warnings.append(f"Suggestion action '{action}' invalid; defaulted to 'add'.")
            action = "add"
        confidence = str(item.get("confidence", "low"))
        if confidence not in _VALID_CONFIDENCE:
            warnings.append(f"Confidence '{confidence}' invalid; defaulted to 'low'.")
            confidence = "low"
        reason = str(item.get("reason", ""))
        evidence = str(item.get("evidence_from_case", ""))
        if any(p in reason.lower() for p in _BUY_SELL_PATTERNS):
            reason = "[Content removed: contained investment directive language.]"
            warnings.append("suggestion reason contained buy/sell directive language and was removed.")
        if any(p in evidence.lower() for p in _BUY_SELL_PATTERNS):
            evidence = "[Content removed: contained investment directive language.]"
            warnings.append("suggestion evidence_from_case contained buy/sell directive language and was removed.")
        suggestions.append({
            "action": action,
            "source_name": str(item.get("source_name", "")),
            "source_type": str(item.get("source_type", "other")),
            "reason": reason,
            "evidence_from_case": evidence,
            "confidence": confidence,
            "manual_review_required": True,
        })

    ai_warnings = data.get("warnings", [])
    if isinstance(ai_warnings, list):
        for w in ai_warnings:
            if isinstance(w, str):
                warnings.append(w)

    return {"source_scores": source_scores, "suggestions": suggestions}, warnings


def _source_intel_defaults(sources: list) -> dict:
    return {
        "source_scores": [
            {
                "source_id": str(s.id),
                "source_name": s.source_name,
                "signal_quality": s.signal_quality,
                "usefulness_reason": "",
                "suggested_follow_up": "",
            }
            for s in sources
        ],
        "suggestions": [],
    }


async def generate_source_intelligence_preview(
    db: AsyncSession,
    research_case_id: uuid.UUID,
) -> dict:
    result = await db.execute(
        select(ResearchCase)
        .where(ResearchCase.id == research_case_id)
        .options(
            selectinload(ResearchCase.tasks),
            selectinload(ResearchCase.documents),
            selectinload(ResearchCase.sources),
        )
    )
    rc = result.scalars().first()
    if not rc:
        raise HTTPException(status_code=404, detail="Research case not found")

    if not rc.sources:
        return {
            "saved_to_db": False,
            "research_case_id": str(research_case_id),
            "source_scores": [],
            "suggestions": [],
            "warnings": ["No sources recorded for this case. Add sources before running source intelligence preview."],
            "disclaimer": _DISCLAIMER,
            "usage": {},
        }

    situation: SpecialSituation | None = None
    if rc.situation_id:
        sit_result = await db.execute(
            select(SpecialSituation).where(SpecialSituation.id == rc.situation_id)
        )
        situation = sit_result.scalars().first()

    system_prompt = _load_prompt("source_intelligence_preview.txt")
    prompt = _build_source_intel_prompt(rc, situation)
    text, usage = await complete_with_usage(prompt, system=system_prompt, max_tokens=2000)
    parsed, warnings = _parse_source_intel_json(text, rc.sources)

    return {
        "saved_to_db": False,
        "research_case_id": str(research_case_id),
        "source_scores": parsed["source_scores"],
        "suggestions": parsed["suggestions"],
        "warnings": warnings,
        "disclaimer": _DISCLAIMER,
        "usage": usage,
    }


# ── Phase 4A — Source Intelligence Suggestion Schemas ────────────────────────

class SourceIntelligenceSuggestionRead(BaseModel):
    id: str
    research_case_id: str | None
    historical_case_id: str | None
    action: str
    proposed_name: str | None
    proposed_source_type: str | None
    rationale: str
    status: str
    created_at: str
    reviewed_at: str | None

    @classmethod
    def from_orm(cls, s: SourceIntelligenceSuggestion) -> "SourceIntelligenceSuggestionRead":
        return cls(
            id=str(s.id),
            research_case_id=str(s.research_case_id) if s.research_case_id else None,
            historical_case_id=str(s.historical_case_id) if s.historical_case_id else None,
            action=s.action,
            proposed_name=s.proposed_name,
            proposed_source_type=s.proposed_source_type,
            rationale=s.rationale,
            status=s.status,
            created_at=s.created_at.isoformat(),
            reviewed_at=s.reviewed_at.isoformat() if s.reviewed_at else None,
        )


class SaveSuggestionsPayload(BaseModel):
    suggestions: list[dict]


class ReviewSuggestionPayload(BaseModel):
    status: str


VALID_SUGGESTION_STATUSES = {"proposed", "approved", "rejected"}


# ── Phase 4A — Service functions ──────────────────────────────────────────────

async def save_source_intelligence_suggestions(
    db: AsyncSession,
    research_case_id: uuid.UUID,
    suggestions: list[dict],
) -> list[SourceIntelligenceSuggestion]:
    result = await db.execute(select(ResearchCase).where(ResearchCase.id == research_case_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Research case not found")

    if not suggestions:
        raise HTTPException(status_code=422, detail="No suggestions provided")

    rows: list[SourceIntelligenceSuggestion] = []
    for item in suggestions:
        if not isinstance(item, dict):
            continue
        action = item.get("action", "add")
        if action not in _VALID_SUGGESTION_ACTIONS:
            action = "add"
        row = SourceIntelligenceSuggestion(
            research_case_id=research_case_id,
            action=action,
            proposed_name=item.get("source_name") or item.get("proposed_name"),
            proposed_source_type=item.get("source_type") or item.get("proposed_source_type"),
            rationale=item.get("reason") or item.get("rationale") or "",
            status="proposed",
        )
        db.add(row)
        rows.append(row)

    await db.flush()
    for row in rows:
        await db.refresh(row)
    return rows


async def list_source_intelligence_suggestions(
    db: AsyncSession,
    research_case_id: uuid.UUID | None = None,
    historical_case_id: uuid.UUID | None = None,
    status: str | None = None,
    action: str | None = None,
) -> list[SourceIntelligenceSuggestion]:
    q = select(SourceIntelligenceSuggestion)
    if research_case_id is not None:
        q = q.where(SourceIntelligenceSuggestion.research_case_id == research_case_id)
    if historical_case_id is not None:
        q = q.where(SourceIntelligenceSuggestion.historical_case_id == historical_case_id)
    if status is not None:
        q = q.where(SourceIntelligenceSuggestion.status == status)
    if action is not None:
        q = q.where(SourceIntelligenceSuggestion.action == action)
    q = q.order_by(SourceIntelligenceSuggestion.created_at.desc())
    rows = await db.execute(q)
    return list(rows.scalars().all())


async def review_source_intelligence_suggestion(
    db: AsyncSession,
    suggestion_id: uuid.UUID,
    new_status: str,
) -> SourceIntelligenceSuggestion:
    if new_status not in ("approved", "rejected"):
        raise HTTPException(status_code=422, detail="status must be 'approved' or 'rejected'")

    result = await db.execute(
        select(SourceIntelligenceSuggestion).where(SourceIntelligenceSuggestion.id == suggestion_id)
    )
    suggestion = result.scalars().first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    if suggestion.status != "proposed":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot review suggestion with status '{suggestion.status}'. Only 'proposed' suggestions can be reviewed.",
        )

    suggestion.status = new_status
    suggestion.reviewed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(suggestion)
    return suggestion


# ── Phase 4B — Historical Case Schemas ───────────────────────────────────────

VALID_HISTORICAL_STATUSES = {"seed", "reconstructed", "lessons_extracted", "source_intel_applied"}


class HistoricalCaseRead(BaseModel):
    id: str
    company_name: str
    situation_type: str
    event_date_approx: str | None
    seed_notes: str | None
    course_chapter_ref: int | None
    reconstruction: dict | None
    status: str
    linked_situation_id: str | None
    disclaimer: str
    created_at: str
    updated_at: str

    @classmethod
    def from_orm(cls, hc: HistoricalCase) -> "HistoricalCaseRead":
        return cls(
            id=str(hc.id),
            company_name=hc.company_name,
            situation_type=hc.situation_type,
            event_date_approx=hc.event_date_approx,
            seed_notes=hc.seed_notes,
            course_chapter_ref=hc.course_chapter_ref,
            reconstruction=hc.reconstruction,
            status=hc.status,
            linked_situation_id=str(hc.linked_situation_id) if hc.linked_situation_id else None,
            disclaimer=hc.disclaimer,
            created_at=hc.created_at.isoformat(),
            updated_at=hc.updated_at.isoformat(),
        )


class HistoricalCaseCreate(BaseModel):
    company_name: str
    situation_type: str
    event_date_approx: str | None = None
    seed_notes: str | None = None
    course_chapter_ref: int | None = None


class HistoricalCaseUpdate(BaseModel):
    status: str | None = None
    seed_notes: str | None = None
    event_date_approx: str | None = None
    course_chapter_ref: int | None = None
    reconstruction: dict | None = None


# ── Phase 4B — Service functions ──────────────────────────────────────────────

async def create_historical_case(
    db: AsyncSession,
    payload: HistoricalCaseCreate,
) -> HistoricalCase:
    hc = HistoricalCase(
        company_name=payload.company_name,
        situation_type=payload.situation_type,
        event_date_approx=payload.event_date_approx,
        seed_notes=payload.seed_notes,
        course_chapter_ref=payload.course_chapter_ref,
        status="seed",
        disclaimer=_DISCLAIMER,
    )
    db.add(hc)
    await db.flush()
    await db.refresh(hc)
    return hc


async def list_historical_cases(
    db: AsyncSession,
    status: str | None = None,
    situation_type: str | None = None,
) -> list[HistoricalCase]:
    if status is not None and status not in VALID_HISTORICAL_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status}'. Valid values: {sorted(VALID_HISTORICAL_STATUSES)}",
        )
    q = select(HistoricalCase)
    if status:
        q = q.where(HistoricalCase.status == status)
    if situation_type:
        q = q.where(HistoricalCase.situation_type == situation_type)
    q = q.order_by(HistoricalCase.created_at.desc())
    rows = await db.execute(q)
    return list(rows.scalars().all())


async def get_historical_case(db: AsyncSession, historical_case_id: uuid.UUID) -> HistoricalCase:
    result = await db.execute(
        select(HistoricalCase).where(HistoricalCase.id == historical_case_id)
    )
    hc = result.scalars().first()
    if not hc:
        raise HTTPException(status_code=404, detail="Historical case not found")
    return hc


async def update_historical_case(
    db: AsyncSession,
    historical_case_id: uuid.UUID,
    payload: HistoricalCaseUpdate,
) -> HistoricalCase:
    hc = await get_historical_case(db, historical_case_id)

    if payload.status is not None:
        if payload.status not in VALID_HISTORICAL_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{payload.status}'. Valid values: {sorted(VALID_HISTORICAL_STATUSES)}",
            )
        hc.status = payload.status
    if payload.seed_notes is not None:
        hc.seed_notes = payload.seed_notes
    if payload.event_date_approx is not None:
        hc.event_date_approx = payload.event_date_approx
    if payload.course_chapter_ref is not None:
        hc.course_chapter_ref = payload.course_chapter_ref
    if payload.reconstruction is not None:
        hc.reconstruction = payload.reconstruction

    hc.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(hc)
    return hc


# ── Phase 4C — Historical Case Source Intelligence Preview ───────────────────

_HIST_INTEL_SYSTEM = (
    "You are a private investment research assistant reviewing a historical special situation case study. "
    "The analyst has manually reconstructed this case from memory and notes. "
    "Use only the context provided — do not invent facts, do not fetch URLs, do not use external knowledge beyond what is stated. "
    "Write in clear, factual English. Never use buy/sell language. Never give financial advice. "
    "Return your analysis as a single JSON object with keys: source_scores (array), suggestions (array), warnings (array). "
    "source_scores items: source_id, source_name, signal_quality, usefulness_reason, suggested_follow_up. "
    "suggestions items: action (add/update_priority/deactivate), source_name, source_type, reason, evidence_from_case, confidence (high/medium/low), manual_review_required (always true). "
    "Respond with ONLY a valid JSON object. No markdown, no code fences."
)


def _build_hist_intel_prompt(hc: HistoricalCase) -> str:
    lines: list[str] = []
    lines.append("=== HISTORICAL CASE SOURCE INTELLIGENCE REQUEST ===")
    lines.append("")
    lines.append(f"Historical Case ID: {hc.id}")
    lines.append(f"Company: {hc.company_name}")
    lines.append(f"Situation Type: {hc.situation_type}")
    if hc.event_date_approx:
        lines.append(f"Event Date (approx): {hc.event_date_approx}")
    if hc.course_chapter_ref:
        lines.append(f"Course Chapter Reference: {hc.course_chapter_ref}")
    lines.append(f"Status: {hc.status}")
    lines.append("")

    if hc.seed_notes:
        lines.append("--- ANALYST SEED NOTES ---")
        lines.append(hc.seed_notes)
        lines.append("")

    if hc.reconstruction:
        lines.append("--- RECONSTRUCTION NOTES (analyst-entered) ---")
        for k, v in hc.reconstruction.items():
            if isinstance(v, str) and v.strip():
                lines.append(f"  {k}: {v[:300]}")
        lines.append("")

    lines.append("=== INSTRUCTIONS ===")
    lines.append(
        "Based ONLY on the historical case data above, suggest sources relevant to researching this situation type. "
        "Do NOT fetch any URLs. Do NOT use buy/sell language. "
        "Return a JSON object with keys: source_scores (empty array — no existing sources to score), suggestions, warnings."
    )
    return "\n".join(lines)


async def generate_historical_case_source_intelligence_preview(
    db: AsyncSession,
    historical_case_id: uuid.UUID,
) -> dict:
    hc = await get_historical_case(db, historical_case_id)

    if not hc.seed_notes and not hc.reconstruction:
        return {
            "saved_to_db": False,
            "historical_case_id": str(historical_case_id),
            "source_scores": [],
            "suggestions": [],
            "warnings": ["No seed notes or reconstruction data. Add notes before generating source intelligence preview."],
            "disclaimer": _DISCLAIMER,
            "usage": {},
        }

    prompt = _build_hist_intel_prompt(hc)
    text, usage = await complete_with_usage(prompt, system=_HIST_INTEL_SYSTEM, max_tokens=2000)
    parsed, warnings = _parse_source_intel_json(text, [])

    return {
        "saved_to_db": False,
        "historical_case_id": str(historical_case_id),
        "source_scores": parsed["source_scores"],
        "suggestions": parsed["suggestions"],
        "warnings": warnings,
        "disclaimer": _DISCLAIMER,
        "usage": usage,
    }


async def save_historical_case_source_intelligence_suggestions(
    db: AsyncSession,
    historical_case_id: uuid.UUID,
    suggestions: list[dict],
) -> list[SourceIntelligenceSuggestion]:
    hc = await get_historical_case(db, historical_case_id)

    if not suggestions:
        raise HTTPException(status_code=422, detail="No suggestions provided")

    rows: list[SourceIntelligenceSuggestion] = []
    for item in suggestions:
        if not isinstance(item, dict):
            continue
        action = item.get("action", "add")
        if action not in _VALID_SUGGESTION_ACTIONS:
            action = "add"
        row = SourceIntelligenceSuggestion(
            historical_case_id=hc.id,
            action=action,
            proposed_name=item.get("source_name") or item.get("proposed_name"),
            proposed_source_type=item.get("source_type") or item.get("proposed_source_type"),
            rationale=item.get("reason") or item.get("rationale") or "",
            status="proposed",
        )
        db.add(row)
        rows.append(row)

    await db.flush()
    for row in rows:
        await db.refresh(row)
    return rows
