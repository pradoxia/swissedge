import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.database import get_db
from backend.models.agent_ops import AgentActivity
from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.research_cases import (
    ResearchCaseRead,
    ResearchCaseUpdate,
    EvaluationPrepPackage,
    build_evaluation_prep_package,
    ResearchTaskRead,
    ResearchTaskCreate,
    ResearchTaskUpdate,
    ResearchDocumentRead,
    ResearchDocumentCreate,
    ResearchDocumentUpdate,
    ResearchSourceRead,
    ResearchSourceCreate,
    ResearchSourceUpdate,
    create_research_case_from_situation,
    get_research_case,
    get_evaluation_prep_package,
    list_research_cases,
    update_research_case,
    create_task,
    list_tasks,
    update_task,
    create_document,
    list_documents,
    patch_document,
    create_source,
    list_sources,
    patch_source,
    generate_brief_preview,
    generate_quality_preview,
    generate_document_analysis_preview,
    generate_source_intelligence_preview,
    SourceIntelligenceSuggestionRead,
    SaveSuggestionsPayload,
    ReviewSuggestionPayload,
    save_source_intelligence_suggestions,
    list_source_intelligence_suggestions,
    review_source_intelligence_suggestion,
    HistoricalCaseRead,
    HistoricalCaseCreate,
    HistoricalCaseUpdate,
    create_historical_case,
    list_historical_cases,
    get_historical_case,
    update_historical_case,
    generate_historical_case_source_intelligence_preview,
    save_historical_case_source_intelligence_suggestions,
    PublicArticleDraftRead,
    PublicArticleDraftUpdate,
    create_public_article_draft,
    list_public_article_drafts,
    get_public_article_draft,
    update_public_article_draft,
    render_public_article_markdown,
)
from backend.services.investment.evidence_links import build_research_case_evidence_links
from backend.services.investment.intelligence_score import (
    IntelligenceScorePackage,
    build_intelligence_score_package,
)
from backend.services.investment.case_documentation import (
    CaseDocumentationGuidePackage,
    build_research_case_documentation_guide,
)
from backend.services.investment.case_activity import (
    CaseActivityTimelinePackage,
    build_research_case_activity_timeline,
)
from backend.services.observability import run_logger

router = APIRouter()


def _parse_uuid(value: str, field_name: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid {field_name}: expected UUID")


@router.post("/research-cases/from-situation/{situation_id}", response_model=ResearchCaseRead, status_code=201)
async def create_case_from_situation(
    situation_id: str,
    notes: str | None = Query(default=None),
    investment_readiness: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    rc = await create_research_case_from_situation(
        db,
        situation_id=uuid.UUID(situation_id),
        notes=notes,
        investment_readiness=investment_readiness,
    )
    await db.commit()
    await db.refresh(rc)
    rc = await get_research_case(db, rc.id)
    return ResearchCaseRead.from_orm(rc)


@router.get("/research-cases", response_model=dict)
async def list_cases(
    status: str | None = Query(default=None),
    investment_readiness: str | None = Query(default=None),
    situation_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    cases = await list_research_cases(db, status=status, investment_readiness=investment_readiness, situation_id=situation_id)
    return {"count": len(cases), "research_cases": [ResearchCaseRead.from_orm(rc) for rc in cases]}


@router.get("/research-cases/{research_case_id}", response_model=ResearchCaseRead)
async def get_case(research_case_id: str, db: AsyncSession = Depends(get_db)):
    rc = await get_research_case(db, _parse_uuid(research_case_id, "research_case_id"))
    return ResearchCaseRead.from_orm(rc)


@router.get("/research-cases/{research_case_id}/evaluation-prep", response_model=EvaluationPrepPackage)
async def get_case_evaluation_prep(research_case_id: str, db: AsyncSession = Depends(get_db)):
    return await get_evaluation_prep_package(db, _parse_uuid(research_case_id, "research_case_id"))


@router.get("/research-cases/{research_case_id}/evidence-links")
async def get_case_evidence_links(research_case_id: str, db: AsyncSession = Depends(get_db)):
    rc = await get_research_case(db, _parse_uuid(research_case_id, "research_case_id"))
    return build_research_case_evidence_links(rc).model_dump()


@router.get("/research-cases/{research_case_id}/intelligence-score", response_model=IntelligenceScorePackage)
async def get_case_intelligence_score(research_case_id: str, db: AsyncSession = Depends(get_db)):
    rc = await get_research_case(db, _parse_uuid(research_case_id, "research_case_id"))
    return build_intelligence_score_package(rc)


@router.get("/research-cases/{research_case_id}/documentation-guide", response_model=CaseDocumentationGuidePackage)
async def get_case_documentation_guide(research_case_id: str, db: AsyncSession = Depends(get_db)):
    rc_id = _parse_uuid(research_case_id, "research_case_id")
    result = await db.execute(
        select(ResearchCase)
        .where(ResearchCase.id == rc_id)
        .options(
            selectinload(ResearchCase.tasks),
            selectinload(ResearchCase.documents),
            selectinload(ResearchCase.sources),
        )
    )
    rc = result.scalars().first()
    if not rc:
        raise HTTPException(status_code=404, detail="Research case not found")

    source_situation = None
    if rc.situation_id:
        sit_result = await db.execute(
            select(SpecialSituation).where(SpecialSituation.id == rc.situation_id)
        )
        source_situation = sit_result.scalars().first()

    evidence_links = build_research_case_evidence_links(rc)
    evaluation_prep = build_evaluation_prep_package(rc)
    intelligence_score = build_intelligence_score_package(rc)
    return build_research_case_documentation_guide(
        rc,
        evidence_links=evidence_links,
        evaluation_prep=evaluation_prep,
        intelligence_score=intelligence_score,
        source_situation=source_situation,
    )


@router.get("/research-cases/{research_case_id}/activity-timeline", response_model=CaseActivityTimelinePackage)
async def get_case_activity_timeline(research_case_id: str, db: AsyncSession = Depends(get_db)):
    rc_id = _parse_uuid(research_case_id, "research_case_id")
    result = await db.execute(
        select(ResearchCase)
        .where(ResearchCase.id == rc_id)
        .options(
            selectinload(ResearchCase.tasks),
            selectinload(ResearchCase.documents),
            selectinload(ResearchCase.sources),
        )
    )
    rc = result.scalars().first()
    if not rc:
        raise HTTPException(status_code=404, detail="Research case not found")

    source_situation = None
    related_ids = {str(rc.id)}
    if rc.situation_id:
        sit_result = await db.execute(
            select(SpecialSituation).where(SpecialSituation.id == rc.situation_id)
        )
        source_situation = sit_result.scalars().first()
        related_ids.add(str(rc.situation_id))

    evidence_links = build_research_case_evidence_links(rc)
    evaluation_prep = build_evaluation_prep_package(rc)
    intelligence_score = build_intelligence_score_package(rc)
    documentation_guide = build_research_case_documentation_guide(
        rc,
        evidence_links=evidence_links,
        evaluation_prep=evaluation_prep,
        intelligence_score=intelligence_score,
        source_situation=source_situation,
    )
    activity_result = await db.execute(
        select(AgentActivity)
        .where(AgentActivity.related_entity_id.in_(related_ids))
        .options(selectinload(AgentActivity.agent))
    )
    return build_research_case_activity_timeline(
        rc,
        evidence_links=evidence_links,
        evaluation_prep=evaluation_prep,
        intelligence_score=intelligence_score,
        documentation_guide=documentation_guide,
        source_situation=source_situation,
        agent_activities=list(activity_result.scalars().all()),
    )


@router.patch("/research-cases/{research_case_id}", response_model=ResearchCaseRead)
async def patch_case(
    research_case_id: str,
    payload: ResearchCaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    rc = await update_research_case(db, uuid.UUID(research_case_id), payload)
    await db.commit()
    rc = await get_research_case(db, rc.id)
    return ResearchCaseRead.from_orm(rc)


@router.get("/research-cases/{research_case_id}/tasks", response_model=list[ResearchTaskRead])
async def get_tasks(research_case_id: str, db: AsyncSession = Depends(get_db)):
    tasks = await list_tasks(db, uuid.UUID(research_case_id))
    return [ResearchTaskRead.from_orm(t) for t in tasks]


@router.post("/research-cases/{research_case_id}/tasks", response_model=ResearchTaskRead, status_code=201)
async def add_task(
    research_case_id: str,
    payload: ResearchTaskCreate,
    db: AsyncSession = Depends(get_db),
):
    task = await create_task(db, uuid.UUID(research_case_id), payload)
    await db.commit()
    await db.refresh(task)
    return ResearchTaskRead.from_orm(task)


@router.patch("/research-tasks/{task_id}", response_model=ResearchTaskRead)
async def patch_task(
    task_id: str,
    payload: ResearchTaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    task = await update_task(db, uuid.UUID(task_id), payload)
    await db.commit()
    await db.refresh(task)
    return ResearchTaskRead.from_orm(task)


@router.get("/research-cases/{research_case_id}/documents", response_model=list[ResearchDocumentRead])
async def get_documents(research_case_id: str, db: AsyncSession = Depends(get_db)):
    docs = await list_documents(db, uuid.UUID(research_case_id))
    return [ResearchDocumentRead.from_orm(d) for d in docs]


@router.post("/research-cases/{research_case_id}/documents", response_model=ResearchDocumentRead, status_code=201)
async def add_document(
    research_case_id: str,
    payload: ResearchDocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    doc = await create_document(db, uuid.UUID(research_case_id), payload)
    await db.commit()
    await db.refresh(doc)
    return ResearchDocumentRead.from_orm(doc)


@router.get("/research-cases/{research_case_id}/sources", response_model=list[ResearchSourceRead])
async def get_sources(research_case_id: str, db: AsyncSession = Depends(get_db)):
    srcs = await list_sources(db, uuid.UUID(research_case_id))
    return [ResearchSourceRead.from_orm(s) for s in srcs]


@router.post("/research-cases/{research_case_id}/sources", response_model=ResearchSourceRead, status_code=201)
async def add_source(
    research_case_id: str,
    payload: ResearchSourceCreate,
    db: AsyncSession = Depends(get_db),
):
    src = await create_source(db, uuid.UUID(research_case_id), payload)
    await db.commit()
    await db.refresh(src)
    return ResearchSourceRead.from_orm(src)


@router.patch("/research-cases/{research_case_id}/documents/{document_id}", response_model=ResearchDocumentRead)
async def update_document(
    research_case_id: str,
    document_id: str,
    payload: ResearchDocumentUpdate,
    db: AsyncSession = Depends(get_db),
):
    doc = await patch_document(db, uuid.UUID(document_id), payload)
    await db.commit()
    return ResearchDocumentRead.from_orm(doc)


@router.patch("/research-cases/{research_case_id}/sources/{source_id}", response_model=ResearchSourceRead)
async def update_source(
    research_case_id: str,
    source_id: str,
    payload: ResearchSourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    src = await patch_source(db, uuid.UUID(source_id), payload)
    await db.commit()
    return ResearchSourceRead.from_orm(src)


@router.post("/research-documents/{document_id}/analysis-preview")
async def preview_document_analysis(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    run_id = await run_logger.start_run(
        db,
        agent_name="document_analysis_previewer",
        agent_type="analyzer",
        module="backend.services.investment.research_cases",
        runtime="fastapi",
        trigger_source="manual_analysis_preview_endpoint",
        task_name=f"Document analysis preview for {document_id[:8]}",
        input_summary=f"document_id={document_id}",
    )
    try:
        result = await generate_document_analysis_preview(db, uuid.UUID(document_id))

        usage = result.get("usage", {})
        await run_logger.finish_run(
            db,
            run_id,
            output_summary=f"Analysis preview generated; warnings={len(result['warnings'])}",
            final_outcome="success",
            model_used=usage.get("model"),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )
        if usage:
            await run_logger.log_ai_usage(
                db,
                run_id=run_id,
                agent_name="document_analysis_previewer",
                provider=usage.get("provider", "unknown"),
                model=usage.get("model", "unknown"),
                prompt_name="document_analysis_preview",
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
            )
        await db.commit()
        return result

    except Exception as e:
        try:
            await run_logger.fail_run(db, run_id, str(e))
            await db.commit()
        except Exception:
            pass
        raise


@router.post("/research-cases/{research_case_id}/generate-brief-preview")
async def preview_brief(
    research_case_id: str,
    db: AsyncSession = Depends(get_db),
):
    run_id = await run_logger.start_run(
        db,
        agent_name="research_brief_generator",
        agent_type="analyzer",
        module="backend.services.investment.research_cases",
        runtime="fastapi",
        trigger_source="manual_preview_endpoint",
        task_name=f"Generate brief preview for case {research_case_id[:8]}",
        input_summary=f"research_case_id={research_case_id}",
    )
    try:
        result = await generate_brief_preview(db, uuid.UUID(research_case_id))

        usage = result.get("usage", {})
        await run_logger.finish_run(
            db,
            run_id,
            output_summary=f"Brief preview generated; {len(result['preview'])} sections; warnings={len(result['warnings'])}",
            final_outcome="success",
            model_used=usage.get("model"),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )
        await run_logger.log_ai_usage(
            db,
            run_id=run_id,
            agent_name="research_brief_generator",
            provider=usage.get("provider", "unknown"),
            model=usage.get("model", "unknown"),
            prompt_name="research_brief_preview",
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )
        await db.commit()
        return result

    except Exception as e:
        try:
            await run_logger.fail_run(db, run_id, str(e))
            await db.commit()
        except Exception:
            pass
        raise


@router.post("/research-cases/{research_case_id}/quality-preview")
async def preview_quality(
    research_case_id: str,
    db: AsyncSession = Depends(get_db),
):
    run_id = await run_logger.start_run(
        db,
        agent_name="research_quality_reviewer",
        agent_type="analyzer",
        module="backend.services.investment.research_cases",
        runtime="fastapi",
        trigger_source="manual_quality_preview_endpoint",
        task_name=f"Quality preview for case {research_case_id[:8]}",
        input_summary=f"research_case_id={research_case_id}",
    )
    try:
        result = await generate_quality_preview(db, uuid.UUID(research_case_id))

        usage = result.get("usage", {})
        await run_logger.finish_run(
            db,
            run_id,
            output_summary=(
                f"Quality preview generated; suggested_status={result['suggested_status']}; "
                f"suggested_readiness={result['suggested_readiness']}; warnings={len(result['warnings'])}"
            ),
            final_outcome="success",
            model_used=usage.get("model"),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )
        await run_logger.log_ai_usage(
            db,
            run_id=run_id,
            agent_name="research_quality_reviewer",
            provider=usage.get("provider", "unknown"),
            model=usage.get("model", "unknown"),
            prompt_name="research_quality_preview",
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )
        await db.commit()
        return result

    except Exception as e:
        try:
            await run_logger.fail_run(db, run_id, str(e))
            await db.commit()
        except Exception:
            pass
        raise


@router.post("/research-cases/{research_case_id}/source-intelligence-preview")
async def preview_source_intelligence(
    research_case_id: str,
    db: AsyncSession = Depends(get_db),
):
    run_id = await run_logger.start_run(
        db,
        agent_name="source_intelligence_previewer",
        agent_type="analyzer",
        module="backend.services.investment.research_cases",
        runtime="fastapi",
        trigger_source="manual_source_intelligence_preview_endpoint",
        task_name=f"Source intelligence preview for case {research_case_id[:8]}",
        input_summary=f"research_case_id={research_case_id}",
    )
    try:
        result = await generate_source_intelligence_preview(db, uuid.UUID(research_case_id))

        usage = result.get("usage", {})
        await run_logger.finish_run(
            db,
            run_id,
            output_summary=(
                f"Source intelligence preview generated; "
                f"scores={len(result['source_scores'])}; "
                f"suggestions={len(result['suggestions'])}; "
                f"warnings={len(result['warnings'])}"
            ),
            final_outcome="success",
            model_used=usage.get("model"),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )
        if usage:
            await run_logger.log_ai_usage(
                db,
                run_id=run_id,
                agent_name="source_intelligence_previewer",
                provider=usage.get("provider", "unknown"),
                model=usage.get("model", "unknown"),
                prompt_name="source_intelligence_preview",
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
            )
        await db.commit()
        return result

    except Exception as e:
        try:
            await run_logger.fail_run(db, run_id, str(e))
            await db.commit()
        except Exception:
            pass
        raise


# ── Phase 4A — Source Intelligence Suggestions (Approval Queue) ───────────────

@router.post(
    "/research-cases/{research_case_id}/source-intelligence-suggestions",
    response_model=list[SourceIntelligenceSuggestionRead],
    status_code=201,
)
async def save_suggestions(
    research_case_id: str,
    payload: SaveSuggestionsPayload,
    db: AsyncSession = Depends(get_db),
):
    rows = await save_source_intelligence_suggestions(
        db, uuid.UUID(research_case_id), payload.suggestions
    )
    await db.commit()
    for row in rows:
        await db.refresh(row)
    return [SourceIntelligenceSuggestionRead.from_orm(r) for r in rows]


@router.get(
    "/source-intelligence-suggestions",
    response_model=dict,
)
async def list_suggestions(
    research_case_id: str | None = Query(default=None),
    historical_case_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    action: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    rc_id = uuid.UUID(research_case_id) if research_case_id else None
    hc_id = uuid.UUID(historical_case_id) if historical_case_id else None
    rows = await list_source_intelligence_suggestions(db, rc_id, hc_id, status, action)
    return {"count": len(rows), "suggestions": [SourceIntelligenceSuggestionRead.from_orm(r) for r in rows]}


@router.patch(
    "/source-intelligence-suggestions/{suggestion_id}",
    response_model=SourceIntelligenceSuggestionRead,
)
async def review_suggestion(
    suggestion_id: str,
    payload: ReviewSuggestionPayload,
    db: AsyncSession = Depends(get_db),
):
    suggestion = await review_source_intelligence_suggestion(db, uuid.UUID(suggestion_id), payload.status)
    await db.commit()
    await db.refresh(suggestion)
    return SourceIntelligenceSuggestionRead.from_orm(suggestion)


# ── Phase 4B — Historical Cases ───────────────────────────────────────────────

@router.post("/historical-cases", response_model=HistoricalCaseRead, status_code=201)
async def create_hist_case(
    payload: HistoricalCaseCreate,
    db: AsyncSession = Depends(get_db),
):
    hc = await create_historical_case(db, payload)
    await db.commit()
    await db.refresh(hc)
    return HistoricalCaseRead.from_orm(hc)


@router.get("/historical-cases", response_model=dict)
async def list_hist_cases(
    status: str | None = Query(default=None),
    situation_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    cases = await list_historical_cases(db, status=status, situation_type=situation_type)
    return {"count": len(cases), "historical_cases": [HistoricalCaseRead.from_orm(hc) for hc in cases]}


@router.get("/historical-cases/{historical_case_id}", response_model=HistoricalCaseRead)
async def get_hist_case(historical_case_id: str, db: AsyncSession = Depends(get_db)):
    hc = await get_historical_case(db, uuid.UUID(historical_case_id))
    return HistoricalCaseRead.from_orm(hc)


@router.patch("/historical-cases/{historical_case_id}", response_model=HistoricalCaseRead)
async def patch_hist_case(
    historical_case_id: str,
    payload: HistoricalCaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    hc = await update_historical_case(db, uuid.UUID(historical_case_id), payload)
    await db.commit()
    return HistoricalCaseRead.from_orm(hc)


# ── Phase 4C — Historical Case Source Intelligence Preview ───────────────────

@router.post("/historical-cases/{historical_case_id}/source-intelligence-preview")
async def preview_hist_source_intelligence(
    historical_case_id: str,
    db: AsyncSession = Depends(get_db),
):
    run_id = await run_logger.start_run(
        db,
        agent_name="source_intelligence_previewer",
        agent_type="analyzer",
        module="backend.services.investment.research_cases",
        runtime="fastapi",
        trigger_source="manual_hist_source_intelligence_preview_endpoint",
        task_name=f"Historical case source intelligence preview for {historical_case_id[:8]}",
        input_summary=f"historical_case_id={historical_case_id}",
    )
    try:
        result = await generate_historical_case_source_intelligence_preview(db, uuid.UUID(historical_case_id))

        usage = result.get("usage", {})
        await run_logger.finish_run(
            db,
            run_id,
            output_summary=(
                f"Historical case source intelligence preview generated; "
                f"suggestions={len(result['suggestions'])}; "
                f"warnings={len(result['warnings'])}"
            ),
            final_outcome="success",
            model_used=usage.get("model"),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )
        if usage:
            await run_logger.log_ai_usage(
                db,
                run_id=run_id,
                agent_name="source_intelligence_previewer",
                provider=usage.get("provider", "unknown"),
                model=usage.get("model", "unknown"),
                prompt_name="historical_case_source_intelligence_preview",
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
            )
        await db.commit()
        return result

    except Exception as e:
        try:
            await run_logger.fail_run(db, run_id, str(e))
            await db.commit()
        except Exception:
            pass
        raise


@router.post(
    "/historical-cases/{historical_case_id}/source-intelligence-suggestions",
    response_model=list[SourceIntelligenceSuggestionRead],
    status_code=201,
)
async def save_hist_suggestions(
    historical_case_id: str,
    payload: SaveSuggestionsPayload,
    db: AsyncSession = Depends(get_db),
):
    rows = await save_historical_case_source_intelligence_suggestions(
        db, uuid.UUID(historical_case_id), payload.suggestions
    )
    await db.commit()
    for row in rows:
        await db.refresh(row)
    return [SourceIntelligenceSuggestionRead.from_orm(r) for r in rows]


# ── Phase 5 — Public Article Drafts ───────────────────────────────────────────

@router.post(
    "/research-cases/{research_case_id}/public-draft",
    response_model=PublicArticleDraftRead,
    status_code=201,
)
async def create_public_draft(
    research_case_id: str,
    db: AsyncSession = Depends(get_db),
):
    draft = await create_public_article_draft(db, uuid.UUID(research_case_id))
    await db.commit()
    await db.refresh(draft)
    return PublicArticleDraftRead.from_orm(draft)


@router.get("/public-drafts", response_model=dict)
async def list_public_drafts(
    status: str | None = Query(default=None),
    research_case_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    rc_id = uuid.UUID(research_case_id) if research_case_id else None
    drafts = await list_public_article_drafts(db, status=status, research_case_id=rc_id)
    return {"count": len(drafts), "public_drafts": [PublicArticleDraftRead.from_orm(d) for d in drafts]}


@router.get("/public-drafts/{draft_id}", response_model=PublicArticleDraftRead)
async def get_public_draft(draft_id: str, db: AsyncSession = Depends(get_db)):
    draft = await get_public_article_draft(db, uuid.UUID(draft_id))
    return PublicArticleDraftRead.from_orm(draft)


@router.patch("/public-drafts/{draft_id}", response_model=PublicArticleDraftRead)
async def patch_public_draft(
    draft_id: str,
    payload: PublicArticleDraftUpdate,
    db: AsyncSession = Depends(get_db),
):
    draft = await update_public_article_draft(db, uuid.UUID(draft_id), payload)
    await db.commit()
    await db.refresh(draft)
    return PublicArticleDraftRead.from_orm(draft)


@router.get("/public-drafts/{draft_id}/markdown", response_model=dict)
async def get_public_draft_markdown(draft_id: str, db: AsyncSession = Depends(get_db)):
    draft = await get_public_article_draft(db, uuid.UUID(draft_id))
    return {"markdown": render_public_article_markdown(draft)}
