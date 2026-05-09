import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.observability import AgentRun, AiUsage
from backend.services.observability import agent_registry, cron_reader

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
# Returns ALL registered agents (not just those with runs).

@router.get("/agents")
async def get_agents(db: AsyncSession = Depends(get_db)):
    # Query DB: counts per (agent_name, status)
    counts_result = await db.execute(
        select(AgentRun.agent_name, AgentRun.status, func.count().label("cnt"))
        .group_by(AgentRun.agent_name, AgentRun.status)
    )
    db_counts: dict[str, dict[str, int]] = {}
    for row in counts_result.all():
        name, status, cnt = row
        if name not in db_counts:
            db_counts[name] = {"total": 0, "failed": 0}
        db_counts[name]["total"] += cnt
        if status == "failed":
            db_counts[name]["failed"] += cnt

    # Query DB: last_run per agent
    last_run_result = await db.execute(
        select(AgentRun.agent_name, func.max(AgentRun.started_at).label("last_run"))
        .group_by(AgentRun.agent_name)
    )
    last_runs: dict[str, datetime] = {row[0]: row[1] for row in last_run_result.all()}

    agents = []
    for card in agent_registry.get_all():
        name = card["agent_name"]
        counts = db_counts.get(name, {"total": 0, "failed": 0})
        last_run = last_runs.get(name)
        agents.append({
            "agent_name": name,
            "display_name": card["display_name"],
            "purpose": card["purpose"],
            "runtime": card["runtime"],
            "current_status": card["current_status"],
            "total_runs": counts["total"],
            "failed_runs": counts["failed"],
            "last_run": last_run.isoformat() if last_run else None,
            "warnings": card["warnings"],
            "recommended_next_action": card["recommended_next_action"],
        })

    return {"count": len(agents), "agents": agents}


# ── GET /agents/{agent_name} ──────────────────────────────────────────────────

@router.get("/agents/{agent_name}/text")
async def get_agent_detail_text(agent_name: str, db: AsyncSession = Depends(get_db)):
    data = await _agent_detail(agent_name, db)
    return Response(content=_format_agent_text(data), media_type="text/plain")


@router.get("/agents/{agent_name}")
async def get_agent_detail(agent_name: str, db: AsyncSession = Depends(get_db)):
    return await _agent_detail(agent_name, db)


async def _agent_detail(agent_name: str, db: AsyncSession) -> dict[str, Any]:
    card = agent_registry.get_one(agent_name)
    if not card:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not registered")

    recent_runs_result = await db.execute(
        select(AgentRun)
        .where(AgentRun.agent_name == agent_name)
        .order_by(desc(AgentRun.started_at))
        .limit(10)
    )
    recent_runs = [_serialize_run(r) for r in recent_runs_result.scalars().all()]

    recent_usage_result = await db.execute(
        select(AiUsage)
        .where(AiUsage.agent_name == agent_name)
        .order_by(desc(AiUsage.created_at))
        .limit(10)
    )
    recent_ai_usage = [_serialize_usage(u) for u in recent_usage_result.scalars().all()]

    # Stats
    total_result = await db.execute(
        select(func.count()).select_from(AgentRun).where(AgentRun.agent_name == agent_name)
    )
    total_runs = total_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count()).select_from(AgentRun).where(
            AgentRun.agent_name == agent_name, AgentRun.status == "failed"
        )
    )
    failed_runs = failed_result.scalar() or 0

    agg_result = await db.execute(
        select(
            func.sum(AgentRun.estimated_cost),
            func.sum(AgentRun.input_tokens),
            func.sum(AgentRun.output_tokens),
            func.max(AgentRun.started_at),
        ).where(AgentRun.agent_name == agent_name)
    )
    agg_row = agg_result.first()
    total_cost = float(agg_row[0] or 0) if agg_row else 0.0
    total_input_tokens = int(agg_row[1] or 0) if agg_row else 0
    total_output_tokens = int(agg_row[2] or 0) if agg_row else 0
    last_run_dt = agg_row[3] if agg_row else None

    last_run = recent_runs[0] if recent_runs else None

    return {
        **card,
        "stats": {
            "total_runs": total_runs,
            "failed_runs": failed_runs,
            "last_run": last_run_dt.isoformat() if last_run_dt else None,
            "total_cost_usd": round(total_cost, 6),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
        },
        "last_outcome": last_run["final_outcome"] if last_run else None,
        "last_error": last_run["error_message"] if last_run else None,
        "recent_runs": recent_runs,
        "recent_ai_usage": recent_ai_usage,
    }


def _format_agent_text(data: dict[str, Any]) -> str:
    sep = "─" * 60
    lines = [
        sep,
        f"AGENT   : {data['agent_name']}",
        f"DISPLAY : {data['display_name']}",
        f"STATUS  : {data['current_status']}  |  RUNTIME: {data['runtime']}",
        f"MODULE  : {data['module']}",
        f"OWNER   : {data['owner']}",
        sep,
        "",
        "PURPOSE:",
        f"  {data['purpose']}",
        "",
        "INSTRUCTIONS:",
        f"  {data['instructions']}",
        "",
        f"PERMISSIONS     : {data['permissions']}",
        f"HUMAN APPROVAL  : {data['human_approval_rules']}",
        f"MODEL           : {data.get('model') or 'None (no AI)'}",
        f"TOOLS           : {', '.join(data.get('tools', []))}",
        f"COST METRIC     : {data['cost_metric']}",
        f"SUCCESS METRIC  : {data['success_metric']}",
        f"FAILURE MODES   : {' | '.join(data.get('failure_modes', []))}",
        f"OUTCOME SCORE   : {data['outcome_score_definition']}",
    ]

    warnings = data.get("warnings", [])
    if warnings:
        lines += ["", "WARNINGS:"] + [f"  ⚠ {w}" for w in warnings]

    lines += [
        "",
        "RECOMMENDED NEXT ACTION:",
        f"  {data['recommended_next_action']}",
        "",
    ]

    stats = data.get("stats", {})
    lines += [
        "STATS:",
        f"  total_runs={stats.get('total_runs', 0)}  "
        f"failed={stats.get('failed_runs', 0)}  "
        f"cost=${stats.get('total_cost_usd', 0):.6f}  "
        f"tokens_in={stats.get('total_input_tokens', 0)}  "
        f"tokens_out={stats.get('total_output_tokens', 0)}",
        f"  last_run={stats.get('last_run') or 'never'}",
        "",
        f"LAST OUTCOME : {data.get('last_outcome') or 'N/A'}",
        f"LAST ERROR   : {data.get('last_error') or 'None'}",
    ]

    recent_runs = data.get("recent_runs", [])
    if recent_runs:
        lines += ["", "RECENT RUNS (last 10):"]
        for r in recent_runs:
            lines.append(
                f"  {r['started_at']} | {r['status']} | {r['duration_ms']}ms | {r.get('output_summary', '')[:60]}"
            )

    recent_usage = data.get("recent_ai_usage", [])
    if recent_usage:
        lines += ["", "RECENT AI USAGE:"]
        for u in recent_usage:
            lines.append(
                f"  {u['created_at']} | {u['model']} | in={u['input_tokens']} out={u['output_tokens']} | ${u.get('estimated_cost_usd', 0):.6f}"
            )

    return "\n".join(lines)


# ── GET /mission-control ──────────────────────────────────────────────────────

@router.get("/mission-control/text")
async def get_mission_control_text(db: AsyncSession = Depends(get_db)):
    data = await _mission_control(db)
    return Response(content=_format_mission_control_text(data), media_type="text/plain")


@router.get("/mission-control")
async def get_mission_control(db: AsyncSession = Depends(get_db)):
    return await _mission_control(db)


async def _mission_control(db: AsyncSession) -> dict[str, Any]:
    counts_result = await db.execute(
        select(AgentRun.agent_name, AgentRun.status, func.count().label("cnt"))
        .group_by(AgentRun.agent_name, AgentRun.status)
    )
    db_counts: dict[str, dict[str, int]] = {}
    for row in counts_result.all():
        name, status, cnt = row
        if name not in db_counts:
            db_counts[name] = {"total": 0, "failed": 0}
        db_counts[name]["total"] += cnt
        if status == "failed":
            db_counts[name]["failed"] += cnt

    last_run_result = await db.execute(
        select(AgentRun.agent_name, func.max(AgentRun.started_at).label("last_run"))
        .group_by(AgentRun.agent_name)
    )
    last_runs: dict[str, datetime] = {row[0]: row[1] for row in last_run_result.all()}

    last_outcome_result = await db.execute(
        select(AgentRun.agent_name, AgentRun.final_outcome, AgentRun.error_message)
        .distinct(AgentRun.agent_name)
        .order_by(AgentRun.agent_name, desc(AgentRun.started_at))
    )
    last_outcomes: dict[str, dict] = {
        row[0]: {"outcome": row[1], "error": row[2]} for row in last_outcome_result.all()
    }

    cost_result = await db.execute(
        select(AgentRun.agent_name, func.sum(AgentRun.estimated_cost).label("cost"))
        .group_by(AgentRun.agent_name)
    )
    costs: dict[str, float] = {row[0]: float(row[1] or 0) for row in cost_result.all()}

    agents = []
    for card in agent_registry.get_all():
        name = card["agent_name"]
        counts = db_counts.get(name, {"total": 0, "failed": 0})
        last_run = last_runs.get(name)
        lo = last_outcomes.get(name, {})
        agents.append({
            "agent_name": name,
            "display_name": card["display_name"],
            "purpose": card["purpose"],
            "runtime": card["runtime"],
            "current_status": card["current_status"],
            "model": card.get("model"),
            "total_runs": counts["total"],
            "failed_runs": counts["failed"],
            "last_run": last_run.isoformat() if last_run else None,
            "total_cost_usd": round(costs.get(name, 0.0), 6),
            "last_outcome": lo.get("outcome"),
            "last_error": lo.get("error"),
            "warnings": card["warnings"],
            "recommended_next_action": card["recommended_next_action"],
        })

    total_cost = sum(costs.values())

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_agents": len(agents),
        "total_cost_usd": round(total_cost, 6),
        "agents": agents,
    }


def _format_mission_control_text(data: dict[str, Any]) -> str:
    lines = [
        "SWISSEDGE — AGENT MISSION CONTROL",
        f"Generated : {data['generated_at']}",
        f"Agents    : {data['total_agents']}  |  Total AI cost: ${data['total_cost_usd']:.4f}",
        "=" * 60,
        "STATUS LEGEND: [active] [partial] [pending] [future]",
        "",
    ]

    by_status: dict[str, list] = {}
    for agent in data["agents"]:
        s = agent["current_status"]
        by_status.setdefault(s, []).append(agent)

    for status in ["active", "partial", "pending", "future"]:
        group = by_status.get(status, [])
        if not group:
            continue
        lines.append(f"[{status.upper()}] ({len(group)} agents):")
        for a in group:
            run_info = (
                f"runs={a['total_runs']} failed={a['failed_runs']} "
                f"last={a['last_run'][:16] if a['last_run'] else 'never'}"
            )
            lines.append(f"  {a['agent_name']:<30} {run_info}")
            lines.append(f"    {a['purpose'][:70]}")
            for w in a.get("warnings", []):
                lines.append(f"    ⚠ {w[:75]}")
            if a.get("recommended_next_action"):
                lines.append(f"    → {a['recommended_next_action'][:75]}")
        lines.append("")

    return "\n".join(lines)


# ── GET /cron/upcoming ────────────────────────────────────────────────────────

@router.get("/cron/upcoming/text")
async def get_cron_upcoming_text(days: int = Query(default=3, ge=1, le=30)):
    data = cron_reader.get_upcoming(days=days)
    return Response(content=cron_reader.format_upcoming_text(data), media_type="text/plain")


@router.get("/cron/upcoming")
async def get_cron_upcoming(days: int = Query(default=3, ge=1, le=30)):
    return cron_reader.get_upcoming(days=days)


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


def _serialize_usage(u: AiUsage) -> dict[str, Any]:
    return {
        "id": str(u.id),
        "agent_name": u.agent_name,
        "provider": u.provider,
        "model": u.model,
        "prompt_name": u.prompt_name,
        "input_tokens": u.input_tokens,
        "output_tokens": u.output_tokens,
        "total_tokens": u.total_tokens,
        "estimated_cost_usd": float(u.estimated_cost) if u.estimated_cost else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }
