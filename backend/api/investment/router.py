import uuid
from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.database import get_db
from backend.models.investment import SpecialSituation, SituationHistory, InvestmentSource
from backend.services.investment.sources.sec_edgar import SECEdgarAdapter
from backend.services.investment.evaluator import evaluate_situation
from backend.services.investment.course_index import load_master_index
from backend.services.observability import run_logger

router = APIRouter()
_sec = SECEdgarAdapter()

VALID_STATUSES = {
    "detected", "analyzing", "watchlist", "active",
    "closed_profit", "closed_loss", "passed", "expired",
}


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class SituationPatch(BaseModel):
    status: str | None = None
    notes: str | None = None
    follow_up_date: str | None = None


class SourceCreate(BaseModel):
    name: str
    url: str
    source_type: str | None = None
    active: bool = True
    check_frequency_hours: int = 6
    description: str | None = None
    market: str | None = None
    jurisdiction: str | None = None
    priority: int = 5
    requires_api_key: bool = False
    access_method: str | None = None
    query_template: str | None = None
    notes: str | None = None


class SourcePatch(BaseModel):
    name: str | None = None
    url: str | None = None
    source_type: str | None = None
    active: bool | None = None
    check_frequency_hours: int | None = None
    description: str | None = None
    market: str | None = None
    jurisdiction: str | None = None
    priority: int | None = None
    requires_api_key: bool | None = None
    access_method: str | None = None
    query_template: str | None = None
    notes: str | None = None


# ── Serializers ───────────────────────────────────────────────────────────────

def _serialize(s: SpecialSituation) -> dict:
    return {
        "id": str(s.id),
        "situation_type": s.situation_type,
        "company_name": s.company_name,
        "ticker": s.ticker,
        "filing_type": s.filing_type,
        "filing_url": s.filing_url,
        "detected_at": s.detected_at.isoformat() if s.detected_at else None,
        "status": s.status,
        "evaluation": s.evaluation,
        "strengths": s.strengths,
        "weaknesses": s.weaknesses,
        "risks": s.risks,
        "course_chapter": s.course_chapter,
        "source_urls": s.source_urls,
        "notes": s.notes,
        "follow_up_date": s.follow_up_date.isoformat() if s.follow_up_date else None,
        "published": s.published,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _serialize_source(src: InvestmentSource) -> dict:
    return {
        "id": str(src.id),
        "name": src.name,
        "url": src.url,
        "source_type": src.source_type,
        "active": src.active,
        "check_frequency_hours": src.check_frequency_hours,
        "last_checked": src.last_checked.isoformat() if src.last_checked else None,
        "last_success": src.last_success.isoformat() if src.last_success else None,
        "last_error": src.last_error,
        "description": src.description,
        "market": src.market,
        "jurisdiction": src.jurisdiction,
        "priority": src.priority,
        "requires_api_key": src.requires_api_key,
        "access_method": src.access_method,
        "query_template": src.query_template,
        "notes": src.notes,
    }


# ── Scan endpoint (instrumented) ──────────────────────────────────────────────

@router.post("/scan")
async def scan_situations(hours_back: int = 6, db: AsyncSession = Depends(get_db)):
    """Scan SEC EDGAR for recent filings and evaluate them."""
    run_id = await run_logger.start_run(
        db,
        agent_name="investment_scanner",
        agent_type="fastapi",
        module="api.investment.router",
        runtime="fastapi",
        trigger_source="api_call",
        task_name="scan_situations",
        input_summary=f"Scanning SEC EDGAR for filings in last {hours_back}h",
    )

    api_calls: list[dict] = []
    new_situations: list[dict] = []

    try:
        filings = await _sec.search_recent(hours_back=hours_back)
        api_calls.append({
            "source": "sec_edgar",
            "url": "https://efts.sec.gov/LATEST/search-index",
            "filings_returned": len(filings),
            "errors": None,
        })
    except Exception as e:
        api_calls.append({"source": "sec_edgar", "errors": str(e)})
        await run_logger.fail_run(db, run_id, f"SEC EDGAR scan failed: {e}")
        await db.commit()
        raise HTTPException(status_code=502, detail=f"SEC EDGAR scan failed: {e}")

    total_input_tokens = 0
    total_output_tokens = 0
    eval_model: str | None = None

    for filing in filings:
        if not filing.situation_type:
            continue

        existing = await db.execute(
            select(SpecialSituation).where(SpecialSituation.filing_url == filing.url)
        )
        if existing.scalars().first():
            continue

        evaluation: dict = {}
        try:
            evaluation, usage = await evaluate_situation(filing)
            eval_model = usage.get("model")
            in_tok = usage.get("input_tokens", 0) or 0
            out_tok = usage.get("output_tokens", 0) or 0
            total_input_tokens += in_tok
            total_output_tokens += out_tok
            await run_logger.log_ai_usage(
                db,
                run_id=run_id,
                agent_name="investment_evaluator",
                provider=usage.get("provider", "openai"),
                model=usage.get("model", "gpt-4o-mini"),
                prompt_name="situation_evaluator",
                input_tokens=in_tok,
                output_tokens=out_tok,
            )
        except Exception as e:
            evaluation = {"error": str(e), "disclaimer": "This is not financial advice."}

        sit = SpecialSituation(
            situation_type=filing.situation_type,
            company_name=filing.company,
            ticker=filing.ticker,
            filing_type=filing.filing_type,
            filing_url=filing.url,
            status="detected",
            evaluation=evaluation,
            source_urls=[filing.url],
        )
        db.add(sit)
        await db.flush()
        new_situations.append(_serialize(sit))

    await run_logger.finish_run(
        db,
        run_id,
        output_summary=f"Scanned 1 source. {len(filings)} filings found. {len(new_situations)} new situations created.",
        final_outcome=f"{len(new_situations)} new situations stored",
        outcome_score=1,
        model_used=eval_model,
        input_tokens=total_input_tokens or None,
        output_tokens=total_output_tokens or None,
        api_calls_made=api_calls,
        database_records_created={"special_situations": len(new_situations)},
    )
    await db.commit()

    return {
        "scanned_filings": len(filings),
        "new_situations": len(new_situations),
        "situations": new_situations,
    }


# ── Situations CRUD ───────────────────────────────────────────────────────────

@router.get("/situations")
async def list_situations(
    status: str | None = None,
    situation_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(SpecialSituation)
    filters = []
    if status:
        filters.append(SpecialSituation.status == status)
    if situation_type:
        filters.append(SpecialSituation.situation_type == situation_type)
    if filters:
        q = q.where(and_(*filters))
    q = q.order_by(SpecialSituation.detected_at.desc())
    result = await db.execute(q)
    items = result.scalars().all()
    return {"count": len(items), "situations": [_serialize(s) for s in items]}


@router.get("/situations/{situation_id}")
async def get_situation(situation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SpecialSituation)
        .where(SpecialSituation.id == uuid.UUID(situation_id))
        .options(selectinload(SpecialSituation.history))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")
    data = _serialize(sit)
    data["history"] = [
        {
            "status_from": h.status_from,
            "status_to": h.status_to,
            "reason": h.reason,
            "changed_at": h.changed_at.isoformat(),
        }
        for h in sit.history
    ]
    return data


@router.patch("/situations/{situation_id}")
async def update_situation(
    situation_id: str,
    patch: SituationPatch,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")

    if patch.status:
        if patch.status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status. Valid: {VALID_STATUSES}")
        hist = SituationHistory(
            situation_id=sit.id,
            status_from=sit.status,
            status_to=patch.status,
        )
        db.add(hist)
        sit.status = patch.status

    if patch.notes is not None:
        sit.notes = patch.notes
    if patch.follow_up_date is not None:
        sit.follow_up_date = date.fromisoformat(patch.follow_up_date)

    sit.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(sit)
    return _serialize(sit)


@router.get("/follow-up")
@router.post("/follow-up")
async def follow_up_watchlist(db: AsyncSession = Depends(get_db)):
    """Return situations with a follow_up_date on or before today."""
    today = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(SpecialSituation).where(
            and_(
                SpecialSituation.follow_up_date <= today,
                SpecialSituation.status.in_(["watchlist", "analyzing"]),
            )
        )
    )
    due = result.scalars().all()
    return {"due_for_follow_up": len(due), "situations": [_serialize(s) for s in due]}


@router.get("/course-index")
async def get_course_index():
    index = load_master_index()
    if not index:
        raise HTTPException(
            status_code=503,
            detail="Course index not found. Run scripts/ingest_course.py first.",
        )
    return index


# ── Investment Sources CRUD ───────────────────────────────────────────────────

@router.get("/sources")
async def list_sources(active_only: bool = False, db: AsyncSession = Depends(get_db)):
    q = select(InvestmentSource).order_by(InvestmentSource.priority.desc(), InvestmentSource.name)
    if active_only:
        q = q.where(InvestmentSource.active == True)  # noqa: E712
    result = await db.execute(q)
    sources = result.scalars().all()
    return {"count": len(sources), "sources": [_serialize_source(s) for s in sources]}


@router.post("/sources")
async def create_source(body: SourceCreate, db: AsyncSession = Depends(get_db)):
    src = InvestmentSource(**body.model_dump())
    db.add(src)
    await db.commit()
    await db.refresh(src)
    return _serialize_source(src)


@router.patch("/sources/{source_id}")
async def update_source(source_id: str, body: SourcePatch, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InvestmentSource).where(InvestmentSource.id == uuid.UUID(source_id))
    )
    src = result.scalars().first()
    if not src:
        raise HTTPException(status_code=404, detail="Source not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(src, field, value)
    await db.commit()
    await db.refresh(src)
    return _serialize_source(src)


@router.delete("/sources/{source_id}")
async def delete_source(source_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InvestmentSource).where(InvestmentSource.id == uuid.UUID(source_id))
    )
    src = result.scalars().first()
    if not src:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(src)
    await db.commit()
    return {"deleted": source_id}


@router.post("/sources/{source_id}/test")
async def test_source(source_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InvestmentSource).where(InvestmentSource.id == uuid.UUID(source_id))
    )
    src = result.scalars().first()
    if not src:
        raise HTTPException(status_code=404, detail="Source not found")

    if src.source_type == "sec_edgar":
        try:
            filings = await _sec.search_recent(hours_back=24)
            src.last_success = datetime.now(timezone.utc)
            src.last_error = None
            src.last_checked = datetime.now(timezone.utc)
            await db.commit()
            return {"status": "ok", "source": src.name, "filings_returned": len(filings)}
        except Exception as e:
            src.last_error = str(e)
            src.last_checked = datetime.now(timezone.utc)
            await db.commit()
            return {"status": "error", "source": src.name, "error": str(e)}

    src.last_checked = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "skipped", "source": src.name, "reason": f"No test adapter for source_type={src.source_type}"}
