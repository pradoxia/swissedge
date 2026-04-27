import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.observability import AgentRun, AiUsage

router = APIRouter()


# ── GET /runs ─────────────────────────────────────────────────────────────────

@router.get("/runs")
async def list_runs(
    agent_name: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(AgentRun).order_by(desc(AgentRun.started_at))
    if agent_name:
        q = q.where(AgentRun.agent_name == agent_name)
    if status:
        q = q.where(AgentRun.status == status)
    q = q.offset(offset).limit(min(limit, 200))
    result = await db.execute(q)
    runs = result.scalars().all()
    return {"count": len(runs), "offset": offset, "runs": [_serialize_run(r) for r in runs]}


# ── GET /runs/{id} ────────────────────────────────────────────────────────────

@router.get("/runs/{run_id}")
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run_id")
    result = await db.execute(select(AgentRun).where(AgentRun.id == rid))
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return _serialize_run(run)


# ── GET /summary ──────────────────────────────────────────────────────────────

@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    total_result = await db.execute(select(func.count()).select_from(AgentRun))
    total_runs = total_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count()).select_from(AgentRun).where(AgentRun.status == "failed")
    )
    failed_runs = failed_result.scalar() or 0

    cost_result = await db.execute(select(func.sum(AiUsage.estimated_cost)).select_from(AiUsage))
    total_cost = float(cost_result.scalar() or 0)

    top_agents_result = await db.execute(
        select(AgentRun.agent_name, func.count().label("run_count"))
        .group_by(AgentRun.agent_name)
        .order_by(desc("run_count"))
        .limit(5)
    )
    top_agents = [{"agent_name": row[0], "run_count": row[1]} for row in top_agents_result]

    recent_result = await db.execute(
        select(AgentRun).order_by(desc(AgentRun.started_at)).limit(5)
    )
    recent_runs = [_serialize_run(r) for r in recent_result.scalars().all()]

    pending_approval_result = await db.execute(
        select(func.count()).select_from(AgentRun).where(
            AgentRun.human_approval_required == True,  # noqa: E712
            AgentRun.human_approved == None,           # noqa: E711
        )
    )
    pending_approvals = pending_approval_result.scalar() or 0

    return {
        "total_runs": total_runs,
        "failed_runs": failed_runs,
        "success_rate": round((total_runs - failed_runs) / total_runs, 3) if total_runs else None,
        "total_ai_cost_usd": round(total_cost, 4),
        "pending_human_approvals": pending_approvals,
        "top_agents": top_agents,
        "recent_runs": recent_runs,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── GET /costs ────────────────────────────────────────────────────────────────

@router.get("/costs")
async def get_costs(db: AsyncSession = Depends(get_db)):
    by_agent = await db.execute(
        select(
            AiUsage.agent_name,
            AiUsage.model,
            func.sum(AiUsage.input_tokens).label("total_input_tokens"),
            func.sum(AiUsage.output_tokens).label("total_output_tokens"),
            func.sum(AiUsage.estimated_cost).label("total_cost"),
            func.count().label("call_count"),
        )
        .group_by(AiUsage.agent_name, AiUsage.model)
        .order_by(desc("total_cost"))
    )
    rows = by_agent.all()

    return {
        "breakdown": [
            {
                "agent_name": r[0],
                "model": r[1],
                "total_input_tokens": r[2],
                "total_output_tokens": r[3],
                "total_cost_usd": round(float(r[4] or 0), 4),
                "call_count": r[5],
            }
            for r in rows
        ],
        "grand_total_usd": round(sum(float(r[4] or 0) for r in rows), 4),
    }


# ── GET /agents ───────────────────────────────────────────────────────────────

@router.get("/agents")
async def get_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            AgentRun.agent_name,
            AgentRun.agent_type,
            AgentRun.runtime,
            func.count().label("total_runs"),
            func.max(AgentRun.started_at).label("last_run"),
        )
        .group_by(AgentRun.agent_name, AgentRun.agent_type, AgentRun.runtime)
        .order_by(desc("total_runs"))
    )
    rows = result.all()
    return {
        "agents": [
            {
                "agent_name": r[0],
                "agent_type": r[1],
                "runtime": r[2],
                "total_runs": r[3],
                "last_run": r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ]
    }


# ── POST /claude-session ──────────────────────────────────────────────────────

class ClaudeSessionRequest(BaseModel):
    task_name: str
    input_summary: str = ""
    output_summary: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    files_touched: list[str] | None = None
    outcome: str = ""
    outcome_score: int | None = None


@router.post("/claude-session")
async def log_claude_session(req: ClaudeSessionRequest, db: AsyncSession = Depends(get_db)):
    from backend.services.observability.run_logger import estimate_cost
    model = "claude-sonnet-4-6"
    cost = req.estimated_cost_usd
    if cost is None and req.input_tokens and req.output_tokens:
        cost = estimate_cost(model, req.input_tokens, req.output_tokens)

    run = AgentRun(
        agent_name="claude_engineer",
        agent_type="claude_code",
        module="claude_code",
        runtime="claude_code",
        trigger_source="manual",
        task_name=req.task_name,
        input_summary=req.input_summary,
        output_summary=req.output_summary,
        status="completed",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        model_used=model,
        input_tokens=req.input_tokens,
        output_tokens=req.output_tokens,
        estimated_cost=cost,
        files_touched=req.files_touched,
        final_outcome=req.outcome,
        outcome_score=req.outcome_score,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return {"run_id": str(run.id), "status": "logged"}


# ── helpers ───────────────────────────────────────────────────────────────────

def _serialize_run(r: AgentRun) -> dict[str, Any]:
    return {
        "id": str(r.id),
        "agent_name": r.agent_name,
        "agent_type": r.agent_type,
        "runtime": r.runtime,
        "trigger_source": r.trigger_source,
        "task_name": r.task_name,
        "input_summary": r.input_summary,
        "output_summary": r.output_summary,
        "status": r.status,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "duration_ms": r.duration_ms,
        "model_used": r.model_used,
        "input_tokens": r.input_tokens,
        "output_tokens": r.output_tokens,
        "estimated_cost_usd": float(r.estimated_cost) if r.estimated_cost else None,
        "error_message": r.error_message,
        "human_approval_required": r.human_approval_required,
        "human_approved": r.human_approved,
        "final_outcome": r.final_outcome,
        "outcome_score": r.outcome_score,
        "api_calls_made": r.api_calls_made,
        "database_records_created": r.database_records_created,
    }
