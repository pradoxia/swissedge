import uuid
from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from backend.db.database import get_db
from backend.models.agent_ops import AgentActivity
from backend.models.investment import DetectionRun, SpecialSituation, SituationHistory, InvestmentSource
from backend.models.investment_research import HistoricalCase
from backend.models.investment_research import ResearchCase
from backend.services.investment.sources.sec_edgar import SECEdgarAdapter
from backend.services.investment.sources.base import Filing
from backend.services.investment.evaluator import evaluate_situation
from backend.services.investment.course_index import load_master_index
from backend.services.investment.course_documentation_map import get_course_documentation_map
from backend.services.investment.skill_registry import get_skill_requirements_map
from backend.services.investment.methodology_workspace import ALLOWED_WORKFLOW_STATUSES, WORKSPACE_KEY
from backend.services.investment.resource_scout import (
    VALID_RESOURCE_REVIEW_STATUSES,
    VALID_SOURCE_TYPES,
    add_manual_resource_candidate,
    update_resource_candidate_review,
    update_workflow_status,
)
from backend.services.investment.evidence_links import build_situation_evidence_links
from backend.services.investment.case_documentation import (
    CaseDocumentationGuidePackage,
    build_situation_documentation_guide,
)
from backend.services.investment.case_activity import (
    CaseActivityTimelinePackage,
    build_situation_activity_timeline,
)
from backend.services.investment.fontana_report import collect_fontana_diagnostic_report
from backend.services.investment.dani_weber_metrics import collect_dani_weber_metrics_package
from backend.services.investment.executive_review import collect_executive_review_package
from backend.services.investment.intelligence_kpis import collect_intelligence_kpi_package
from backend.services.investment.official_source_finder import (
    OfficialSourceFinderPackage,
    build_situation_official_source_finder,
)
from backend.services.investment.historical_analogues import (
    HistoricalAnaloguesPackage,
    build_situation_historical_analogues,
)
from backend.services.investment.case_completion import (
    CaseCompletionPackage,
    build_situation_completion_workbench,
)
from backend.services.investment.sec_document_acquisition import (
    SecDocumentAcquisitionPackage,
    acquire_sec_documents_from_preview,
    apply_situation_sec_acquisition_metadata,
    build_situation_sec_document_acquisition_preview,
)
from backend.services.investment.detection_run_service import (
    build_detection_run_status,
    get_latest_runs,
    serialize_detection_run,
)
from backend.services.investment.detection_readiness import (
    DetectionReadinessPackage,
    build_detection_readiness,
)
from backend.services.investment.document_package import (
    DocumentPackage,
    build_situation_document_package,
)
from backend.services.investment.documentation_agent import (
    DocumentationAgentReport,
    build_special_situation_documentation_report,
)
from backend.services.investment.documentation_extraction import (
    DocumentationExtractionFieldRead,
    list_extraction_fields,
    read_and_store_draft_fields,
    review_extraction_field,
)
from backend.services.investment.documentation_sources import (
    add_link_documentation_source,
    add_uploaded_document_source,
    list_documentation_sources,
)
from backend.services.investment.knowledge_base import (
    KnowledgeEntry,
    get_knowledge_entry,
    list_knowledge_entries,
)
from backend.services.investment.promotion_readiness import (
    PromotionReadinessPackage,
    build_promotion_readiness_package,
)
from backend.services.investment.intelligence_score import build_intelligence_score_package
from backend.services.investment.research_cases import build_evaluation_prep_package
from backend.services.investment.research_cases import (
    PromoteSpecialSituationPayload,
    ResearchCaseRead,
    get_research_case,
    promote_special_situation_to_research_case,
)
from backend.services.observability import run_logger

router = APIRouter()
_sec = SECEdgarAdapter()

VALID_STATUSES = {
    "detected", "reviewing", "watchlist", "ignored", "archived",
}

# Simple in-memory daily cap for v2 evaluations (MVP - replace with Redis later)
_v2_daily_counter = {"date": None, "count": 0}
_V2_DAILY_LIMIT = 10


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


class FilingInput(BaseModel):
    company: str
    ticker: str | None = None
    filing_type: str
    date: str
    url: str
    summary: str
    situation_type: str | None = None
    cik: str | None = None
    accession_number: str | None = None
    save_to_db: bool = False


class WorkflowStatusPatch(BaseModel):
    workflow_status: str


class ResourceCandidateCreate(BaseModel):
    title: str | None = None
    url: str
    source_type: str
    notes: str | None = None
    related_resource_ids: list[str] = []
    related_check_ids: list[str] = []


class ResourceCandidatePatch(BaseModel):
    status: str | None = None
    notes: str | None = None
    related_resource_ids: list[str] | None = None
    related_check_ids: list[str] | None = None


class DocumentationExtractionReadRequest(BaseModel):
    candidate_source_id: str
    document_key: str


class DocumentationSourceLinkCreate(BaseModel):
    url: str
    document_key: str
    title: str | None = None
    source_type: str = "source_link"
    related_required_resource_ids: list[str] = []
    related_checklist_item_ids: list[str] = []


class DocumentationExtractionReviewRequest(BaseModel):
    status: str
    extracted_value: str | None = None
    reviewed_by: str | None = "Dani"


# ── Serializers ───────────────────────────────────────────────────────────────

def _split_form_ids(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _extract_v2_fields(evaluation: dict | None) -> dict:
    """Extract v2 schema fields from evaluation JSON for dashboard display."""
    if not evaluation:
        return {}

    return {
        "evaluator_version": evaluation.get("evaluator_version", "v1"),
        "v2_situation_type": evaluation.get("situation_type"),
        "v2_subtype": evaluation.get("subtype"),
        "selected_playbook": evaluation.get("routing_decision", {}).get("selected_playbook"),
        "playbook_status": evaluation.get("playbook_status"),
        "recommendation": evaluation.get("recommendation"),
        "evaluator_confidence": evaluation.get("evaluator_confidence"),
        "human_review_required_count": len(evaluation.get("human_review_required", [])),
        "risk_flags_count": len(evaluation.get("risk_flags", [])),
        "prohibited_inferences_count": len(evaluation.get("prohibited_inferences_detected", [])),
        "missing_documents_count": len(evaluation.get("missing_documents", [])),
        "fallback_occurred": evaluation.get("fallback_occurred", False),
    }


def _serialize(s: SpecialSituation) -> dict:
    base = {
        "id": str(s.id),
        "situation_type": s.situation_type,
        "company_name": s.company_name,
        "ticker": s.ticker,
        "filing_type": s.filing_type,
        "filing_url": s.filing_url,
        "detected_at": s.detected_at.isoformat() if s.detected_at else None,
        "status": s.status,
        "evaluation": s.evaluation,
        "methodology_workspace": (s.evaluation or {}).get(WORKSPACE_KEY) if isinstance(s.evaluation, dict) else None,
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

    # Add v2 dashboard fields
    base.update(_extract_v2_fields(s.evaluation))

    return base


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


def _check_v2_daily_limit() -> bool:
    """Check if v2 daily limit has been reached. Returns True if under limit."""
    global _v2_daily_counter
    today = date.today().isoformat()

    if _v2_daily_counter["date"] != today:
        _v2_daily_counter = {"date": today, "count": 0}

    return _v2_daily_counter["count"] < _V2_DAILY_LIMIT


def _increment_v2_counter():
    """Increment v2 daily counter."""
    global _v2_daily_counter
    _v2_daily_counter["count"] += 1


def _empty_scanner_funnel(hours_back: int) -> dict:
    return {
        "adapter_name": "SECEdgarAdapter",
        "source": "sec_edgar",
        "source_registry_used": False,
        "hours_back": hours_back,
        "forms_searched": list(SECEdgarAdapter.FILING_TYPES),
        "raw_hits_total": None,
        "parsed_filings_total": 0,
        "classified_candidates_count": 0,
        "classified_candidates_by_type": {},
        "skipped_unclassified_count": 0,
        "skipped_duplicate_count": 0,
        "evaluated_count": 0,
        "evaluation_error_count": 0,
        "created_count": 0,
    }


def _count_classified_by_type(filings: list[Filing]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for filing in filings:
        if not filing.situation_type:
            continue
        counts[filing.situation_type] = counts.get(filing.situation_type, 0) + 1
    return counts


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/intelligence/kpis")
async def get_intelligence_kpis(db: AsyncSession = Depends(get_db)):
    return await collect_intelligence_kpi_package(db)


@router.get("/detection-runs/latest")
async def get_latest_detection_run(db: AsyncSession = Depends(get_db)):
    runs = await get_latest_runs(db, limit=1)
    if not runs:
        return {"run": None}
    return {"run": serialize_detection_run(runs[0])}


@router.get("/detection-runs/status")
async def get_detection_runs_status(db: AsyncSession = Depends(get_db)):
    runs = await get_latest_runs(db, limit=20)
    return build_detection_run_status(runs)


@router.get("/detection-runs/readiness", response_model=DetectionReadinessPackage)
async def get_detection_runs_readiness(db: AsyncSession = Depends(get_db)):
    runs = await get_latest_runs(db, limit=10)
    return build_detection_readiness(runs)


@router.get("/detection-runs")
async def list_detection_runs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    limit = max(1, min(limit, 100))
    runs = await get_latest_runs(db, limit=limit)
    return {"count": len(runs), "runs": [serialize_detection_run(run) for run in runs]}


@router.get("/detection-runs/{run_id}")
async def get_detection_run(run_id: str, db: AsyncSession = Depends(get_db)):
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Detection run not found") from None

    run = await db.get(DetectionRun, run_uuid)
    if not run:
        raise HTTPException(status_code=404, detail="Detection run not found")
    return serialize_detection_run(run)


@router.get("/intelligence/fontana-report")
async def get_fontana_report(db: AsyncSession = Depends(get_db)):
    return await collect_fontana_diagnostic_report(db)


@router.get("/executive/dani-weber-metrics")
async def get_dani_weber_metrics(db: AsyncSession = Depends(get_db)):
    return await collect_dani_weber_metrics_package(db)


@router.get("/executive/review")
async def get_executive_review(db: AsyncSession = Depends(get_db)):
    return await collect_executive_review_package(db)


@router.post("/evaluate-v2")
async def evaluate_v2_manual(
    filing_input: FilingInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Manual evaluator v2 endpoint for controlled testing.
    Always uses v2 evaluator. Limited to 10 evaluations per day.
    V1 remains default for all other flows.

    If save_to_db=true, persists the evaluation result as a SpecialSituation row.
    """
    if not _check_v2_daily_limit():
        raise HTTPException(
            status_code=429,
            detail=f"Daily v2 evaluation limit reached ({_V2_DAILY_LIMIT}/day). Try again tomorrow."
        )

    filing = Filing(
        company=filing_input.company,
        ticker=filing_input.ticker,
        filing_type=filing_input.filing_type,
        date=filing_input.date,
        url=filing_input.url,
        summary=filing_input.summary,
        situation_type=filing_input.situation_type,
        cik=filing_input.cik,
        accession_number=filing_input.accession_number,
    )

    run_id = await run_logger.start_run(
        db,
        agent_name="investment_evaluator",
        agent_type="analyzer",
        module="backend.services.investment.evaluator",
        runtime="fastapi",
        trigger_source="manual_v2_endpoint",
        task_name=f"Evaluate {filing.company} ({filing.filing_type})",
        input_summary=f"{filing.filing_type} for {filing.company}",
    )

    import os
    original_version = os.environ.get("EVALUATOR_VERSION")
    fallback_occurred = False
    situation_id = None

    try:
        os.environ["EVALUATOR_VERSION"] = "v2"
        result, usage = await evaluate_situation(filing)

        if "evaluator_version" not in result:
            result["evaluator_version"] = "v2"

        if result.get("_fallback_to_v1"):
            fallback_occurred = True
            result["evaluator_version"] = "v1"
            result["fallback_occurred"] = True

        _increment_v2_counter()

        # Optionally persist to database
        if filing_input.save_to_db:
            sit = SpecialSituation(
                situation_type=filing.situation_type or result.get("situation_type"),
                company_name=filing.company,
                ticker=filing.ticker,
                filing_type=filing.filing_type,
                filing_url=filing.url,
                status="detected",
                evaluation=result,
                source_urls=[filing.url],
            )
            db.add(sit)
            await db.flush()
            situation_id = str(sit.id)

        await run_logger.finish_run(
            db,
            run_id,
            output_summary=f"Evaluated as {result.get('situation_type', 'unknown')}" + (f"; saved as {situation_id}" if situation_id else ""),
            final_outcome="success",
            model_used=usage.get("model"),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )

        await run_logger.log_ai_usage(
            db,
            run_id=run_id,
            agent_name="investment_evaluator",
            provider=usage.get("provider", "unknown"),
            model=usage.get("model", "unknown"),
            prompt_name="situation_evaluator_v2",
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )

        await db.commit()

        response = {
            "result": result,
            "usage": usage,
            "evaluator_version": result.get("evaluator_version", "v2"),
            "fallback_occurred": fallback_occurred,
            "daily_limit": {
                "used": _v2_daily_counter["count"],
                "limit": _V2_DAILY_LIMIT,
                "remaining": _V2_DAILY_LIMIT - _v2_daily_counter["count"],
            }
        }

        if situation_id:
            response["situation_id"] = situation_id

        return response

    except Exception as e:
        await run_logger.fail_run(db, run_id, str(e))
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

    finally:
        if original_version is None:
            os.environ.pop("EVALUATOR_VERSION", None)
        else:
            os.environ["EVALUATOR_VERSION"] = original_version


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
    funnel = _empty_scanner_funnel(hours_back)

    try:
        filings, sec_diagnostics = await _sec.search_recent_with_diagnostics(hours_back=hours_back)
        funnel.update(sec_diagnostics)
        funnel.update({
            "parsed_filings_total": len(filings),
            "classified_candidates_count": sum(1 for f in filings if f.situation_type),
            "classified_candidates_by_type": _count_classified_by_type(filings),
        })
        api_calls.append({
            "source": "sec_edgar",
            "url": "https://efts.sec.gov/LATEST/search-index",
            "filings_returned": len(filings),
            "diagnostics": funnel,
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
            funnel["skipped_unclassified_count"] += 1
            continue

        existing = await db.execute(
            select(SpecialSituation).where(SpecialSituation.filing_url == filing.url)
        )
        if existing.scalars().first():
            funnel["skipped_duplicate_count"] += 1
            continue

        evaluation: dict = {}
        try:
            funnel["evaluated_count"] += 1
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
            funnel["evaluation_error_count"] += 1
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

    funnel["created_count"] = len(new_situations)
    if api_calls and api_calls[0].get("source") == "sec_edgar":
        api_calls[0]["diagnostics"] = funnel

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
    evaluator_version: str | None = None,
    playbook_status: str | None = None,
    recommendation: str | None = None,
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    List special situations with optional filters.
    Supports filtering by v2 fields extracted from evaluation JSON.
    By default, archived situations are excluded unless include_archived=true.
    """
    q = select(SpecialSituation)
    filters = []

    # Exclude archived by default
    if not include_archived:
        filters.append(SpecialSituation.status != "archived")

    if status:
        filters.append(SpecialSituation.status == status)
    if situation_type:
        filters.append(SpecialSituation.situation_type == situation_type)

    # V2 filters require JSON extraction - apply post-query
    if filters:
        q = q.where(and_(*filters))
    q = q.order_by(SpecialSituation.detected_at.desc())
    result = await db.execute(q)
    items = result.scalars().all()

    # Apply v2 filters in Python (since they're in JSONB)
    serialized = [_serialize(s) for s in items]

    if evaluator_version:
        serialized = [s for s in serialized if s.get("evaluator_version") == evaluator_version]
    if playbook_status:
        serialized = [s for s in serialized if s.get("playbook_status") == playbook_status]
    if recommendation:
        serialized = [s for s in serialized if s.get("recommendation") == recommendation]

    return {"count": len(serialized), "situations": serialized}


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


@router.get("/situations/{situation_id}/evidence-links")
async def get_situation_evidence_links(situation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")
    return build_situation_evidence_links(sit).model_dump()


@router.get("/knowledge", response_model=list[KnowledgeEntry])
async def get_knowledge_entries(type: str | None = None, situation_type: str | None = None):
    return list_knowledge_entries(type=type, situation_type=situation_type)


@router.get("/knowledge/{knowledge_key}", response_model=KnowledgeEntry)
async def get_investment_knowledge_entry(knowledge_key: str):
    entry = get_knowledge_entry(knowledge_key)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return entry


@router.get("/situations/{situation_id}/documentation-guide", response_model=CaseDocumentationGuidePackage)
async def get_situation_documentation_guide(situation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")
    evidence_links = build_situation_evidence_links(sit)
    return build_situation_documentation_guide(sit, evidence_links)


@router.get("/situations/{situation_id}/document-package", response_model=DocumentPackage)
async def get_situation_document_package(situation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")
    evidence_links = build_situation_evidence_links(sit)
    sec_preview = build_situation_sec_document_acquisition_preview(sit)
    return build_situation_document_package(sit, evidence_links=evidence_links, sec_preview=sec_preview)


@router.get("/situations/{situation_id}/documentation-agent-report", response_model=DocumentationAgentReport)
async def get_situation_documentation_agent_report(situation_id: str, db: AsyncSession = Depends(get_db)):
    return await build_special_situation_documentation_report(situation_id, db)


@router.get("/situations/{situation_id}/documentation-extractions", response_model=list[DocumentationExtractionFieldRead])
async def get_situation_documentation_extractions(
    situation_id: str,
    document_key: str | None = None,
    candidate_source_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    rows = await list_extraction_fields(
        db,
        uuid.UUID(situation_id),
        document_key=document_key,
        candidate_source_id=candidate_source_id,
    )
    return [DocumentationExtractionFieldRead.from_orm(row) for row in rows]


@router.get("/situations/{situation_id}/documentation-sources")
async def get_situation_documentation_sources(situation_id: str, db: AsyncSession = Depends(get_db)):
    situation = await db.get(SpecialSituation, uuid.UUID(situation_id))
    if not situation:
        raise HTTPException(status_code=404, detail="Situation not found")
    return list_documentation_sources(situation)


@router.post("/situations/{situation_id}/documentation-sources/link")
async def create_situation_documentation_source_link(
    situation_id: str,
    body: DocumentationSourceLinkCreate,
    db: AsyncSession = Depends(get_db),
):
    situation = await db.get(SpecialSituation, uuid.UUID(situation_id))
    if not situation:
        raise HTTPException(status_code=404, detail="Situation not found")
    try:
        candidate = add_link_documentation_source(
            situation,
            url=body.url,
            document_key=body.document_key,
            title=body.title,
            source_type=body.source_type,
            related_required_resource_ids=body.related_required_resource_ids,
            related_checklist_item_ids=body.related_checklist_item_ids,
        )
        await db.commit()
        return {
            "source": candidate,
            "verified": False,
            "guardrails": [
                "Adding a link does not verify the document.",
                "No extraction runs until Dani manually requests Read & map draft.",
            ],
        }
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/situations/{situation_id}/documentation-sources/upload")
async def upload_situation_documentation_source(
    situation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    situation = await db.get(SpecialSituation, uuid.UUID(situation_id))
    if not situation:
        raise HTTPException(status_code=404, detail="Situation not found")
    try:
        form = await request.form()
        file = form.get("file")
        document_key = str(form.get("document_key") or "").strip()
        if not isinstance(file, UploadFile):
            raise ValueError("file is required")
        if not document_key:
            raise ValueError("document_key is required")
        candidate = await add_uploaded_document_source(
            situation,
            file=file,
            document_key=document_key,
            title=str(form.get("title") or "") or None,
            related_required_resource_ids=_split_form_ids(str(form.get("related_required_resource_ids") or "")),
            related_checklist_item_ids=_split_form_ids(str(form.get("related_checklist_item_ids") or "")),
        )
        await db.commit()
        return {
            "source": candidate,
            "verified": False,
            "guardrails": [
                "Uploading a document does not verify it.",
                "No extraction runs until Dani manually requests Read & map draft.",
            ],
        }
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/situations/{situation_id}/documentation-extractions/read-draft", response_model=list[DocumentationExtractionFieldRead])
async def read_situation_documentation_source_draft(
    situation_id: str,
    body: DocumentationExtractionReadRequest,
    db: AsyncSession = Depends(get_db),
):
    rows = await read_and_store_draft_fields(
        db,
        uuid.UUID(situation_id),
        candidate_source_id=body.candidate_source_id,
        document_key=body.document_key,
    )
    await db.commit()
    return [DocumentationExtractionFieldRead.from_orm(row) for row in rows]


@router.post("/situations/{situation_id}/documentation-sources/{source_id}/extract-draft", response_model=list[DocumentationExtractionFieldRead])
async def extract_situation_documentation_source_draft(
    situation_id: str,
    source_id: str,
    body: DocumentationExtractionReadRequest,
    db: AsyncSession = Depends(get_db),
):
    if body.candidate_source_id != source_id:
        raise HTTPException(status_code=422, detail="candidate_source_id must match source_id")
    rows = await read_and_store_draft_fields(
        db,
        uuid.UUID(situation_id),
        candidate_source_id=source_id,
        document_key=body.document_key,
    )
    await db.commit()
    return [DocumentationExtractionFieldRead.from_orm(row) for row in rows]


@router.patch("/documentation-extractions/{field_id}", response_model=DocumentationExtractionFieldRead)
async def review_documentation_extraction_field(
    field_id: str,
    body: DocumentationExtractionReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    row = await review_extraction_field(
        db,
        uuid.UUID(field_id),
        status=body.status,
        extracted_value=body.extracted_value,
        reviewed_by=body.reviewed_by,
    )
    await db.commit()
    return DocumentationExtractionFieldRead.from_orm(row)


@router.get("/situations/{situation_id}/promotion-readiness", response_model=PromotionReadinessPackage)
async def get_situation_promotion_readiness(situation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")
    evidence_links = build_situation_evidence_links(sit)
    sec_preview = build_situation_sec_document_acquisition_preview(sit)
    document_package = build_situation_document_package(sit, evidence_links=evidence_links, sec_preview=sec_preview)
    return build_promotion_readiness_package(
        sit,
        document_package=document_package,
        evidence_links=evidence_links,
    )


@router.get("/situations/{situation_id}/official-source-finder", response_model=OfficialSourceFinderPackage)
async def get_situation_official_source_finder(situation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")
    evidence_links = build_situation_evidence_links(sit)
    return build_situation_official_source_finder(sit, evidence_links)


@router.get("/situations/{situation_id}/historical-analogues", response_model=HistoricalAnaloguesPackage)
async def get_situation_historical_analogues(situation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")
    historical_result = await db.execute(
        select(HistoricalCase).options(
            selectinload(HistoricalCase.documents),
            selectinload(HistoricalCase.sources),
        )
    )
    return build_situation_historical_analogues(
        sit,
        historical_cases=list(historical_result.scalars().all()),
    )


@router.get("/situations/{situation_id}/completion-workbench", response_model=CaseCompletionPackage)
async def get_situation_completion_workbench(situation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")

    workspace = sit.evaluation.get(WORKSPACE_KEY, {}) if isinstance(sit.evaluation, dict) else {}
    rc_id = workspace.get("research_case_id") if isinstance(workspace, dict) else None
    linked_rc = None
    score = None
    prep = None
    if rc_id:
        rc_result = await db.execute(
            select(ResearchCase)
            .where(ResearchCase.id == uuid.UUID(str(rc_id)))
            .options(
                selectinload(ResearchCase.tasks),
                selectinload(ResearchCase.documents),
                selectinload(ResearchCase.sources),
            )
        )
        linked_rc = rc_result.scalars().first()
        if linked_rc:
            prep = build_evaluation_prep_package(linked_rc)
            score = build_intelligence_score_package(linked_rc)

    return build_situation_completion_workbench(
        sit,
        linked_research_case=linked_rc,
        intelligence_score=score,
        evaluation_prep=prep,
    )


@router.get("/situations/{situation_id}/sec-document-acquisition-preview", response_model=SecDocumentAcquisitionPackage)
async def get_situation_sec_document_acquisition_preview(situation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")
    return build_situation_sec_document_acquisition_preview(sit)


@router.post("/situations/{situation_id}/sec-document-acquisition", response_model=SecDocumentAcquisitionPackage)
async def post_situation_sec_document_acquisition(situation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")

    preview = build_situation_sec_document_acquisition_preview(sit)
    package = await acquire_sec_documents_from_preview(preview)
    if package.acquired_documents:
        apply_situation_sec_acquisition_metadata(sit, package)
        flag_modified(sit, "evaluation")
        await db.commit()
        await db.refresh(sit)
    return package


@router.get("/situations/{situation_id}/activity-timeline", response_model=CaseActivityTimelinePackage)
async def get_situation_activity_timeline(situation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")

    evidence_links = build_situation_evidence_links(sit)
    documentation_guide = build_situation_documentation_guide(sit, evidence_links)
    related_ids = {str(sit.id)}
    workspace = sit.evaluation.get(WORKSPACE_KEY, {}) if isinstance(sit.evaluation, dict) else {}
    if isinstance(workspace, dict) and workspace.get("research_case_id"):
        related_ids.add(str(workspace["research_case_id"]))
    activity_result = await db.execute(
        select(AgentActivity)
        .where(AgentActivity.related_entity_id.in_(related_ids))
        .options(selectinload(AgentActivity.agent))
    )
    return build_situation_activity_timeline(
        sit,
        evidence_links=evidence_links,
        documentation_guide=documentation_guide,
        agent_activities=list(activity_result.scalars().all()),
    )


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


@router.post("/situations/{situation_id}/resources")
async def add_situation_resource(
    situation_id: str,
    body: ResourceCandidateCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")
    try:
        result_payload = add_manual_resource_candidate(
            sit,
            title=body.title,
            url=body.url,
            source_type=body.source_type,
            notes=body.notes,
            related_resource_ids=body.related_resource_ids,
            related_check_ids=body.related_check_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    await db.commit()
    await db.refresh(sit)
    return {
        **result_payload,
        "situation": _serialize(sit),
        "valid_source_types": sorted(VALID_SOURCE_TYPES),
    }


@router.patch("/situations/{situation_id}/workflow-status")
async def patch_situation_workflow_status(
    situation_id: str,
    body: WorkflowStatusPatch,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")
    try:
        update_workflow_status(sit, body.workflow_status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    sit.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(sit)
    return {
        "situation": _serialize(sit),
        "valid_workflow_statuses": sorted(ALLOWED_WORKFLOW_STATUSES),
    }


@router.patch("/situations/{situation_id}/resources/{resource_candidate_id}")
async def patch_situation_resource(
    situation_id: str,
    resource_candidate_id: str,
    body: ResourceCandidatePatch,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SpecialSituation).where(SpecialSituation.id == uuid.UUID(situation_id))
    )
    sit = result.scalars().first()
    if not sit:
        raise HTTPException(status_code=404, detail="Situation not found")
    try:
        result_payload = update_resource_candidate_review(
            sit,
            resource_candidate_id=resource_candidate_id,
            status=body.status,
            notes=body.notes,
            related_resource_ids=body.related_resource_ids,
            related_check_ids=body.related_check_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    sit.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(sit)
    return {
        **result_payload,
        "situation": _serialize(sit),
        "valid_resource_statuses": sorted(VALID_RESOURCE_REVIEW_STATUSES),
    }


@router.post("/situations/{situation_id}/promote-to-research-case")
async def promote_situation_to_research_case(
    situation_id: str,
    body: PromoteSpecialSituationPayload | None = None,
    db: AsyncSession = Depends(get_db),
):
    rc, created = await promote_special_situation_to_research_case(
        db,
        uuid.UUID(situation_id),
        body,
    )
    await db.commit()
    rc = await get_research_case(db, rc.id)
    return {
        "created": created,
        "research_case": ResearchCaseRead.from_orm(rc).model_dump(),
    }


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


@router.get("/course-documentation-map/{situation_type}")
def get_course_documentation_map_endpoint(situation_type: str):
    return get_course_documentation_map(situation_type)


@router.get("/skill-requirements/{situation_type}")
def get_skill_requirements_endpoint(situation_type: str):
    return get_skill_requirements_map(situation_type)


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
