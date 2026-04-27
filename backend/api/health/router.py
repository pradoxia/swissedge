import time
from datetime import datetime, timezone
from pathlib import Path

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.health import HealthCheck
from backend.services.observability import run_logger

router = APIRouter()
_start_time = time.time()

EXPECTED_INTERVALS: dict[str, int] = {
    "scan_special_situations": 6,
    "follow_up_watchlist": 24,
    "check_watched_prices": 12,
    "system_health": 12,
}


class HeartbeatRequest(BaseModel):
    task_name: str
    status: str = "completed"
    items_processed: int = 0
    errors: int = 0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── component checks ──────────────────────────────────────────────────────────

async def _check_postgres() -> dict:
    try:
        from backend.db.database import engine
        async with engine.connect() as conn:
            t0 = time.monotonic()
            await conn.execute(sa.text("SELECT 1"))
            ms = round((time.monotonic() - t0) * 1000)
        status = "warning" if ms > 2000 else "ok"
        return {"name": "postgresql", "category": "infrastructure", "status": status,
                "message": f"Connected. Response {ms}ms.", "response_time_ms": ms, "last_checked": _now_iso()}
    except Exception as e:
        return {"name": "postgresql", "category": "infrastructure", "status": "error",
                "message": str(e), "last_checked": _now_iso()}


async def _check_redis() -> dict:
    try:
        try:
            import redis.asyncio as aioredis
        except ImportError:
            return {"name": "redis", "category": "infrastructure", "status": "warning",
                    "message": "redis package not installed.", "last_checked": _now_iso()}
        from backend.config import get_settings
        settings = get_settings()
        client = aioredis.from_url(settings.redis_url)
        t0 = time.monotonic()
        await client.ping()
        ms = round((time.monotonic() - t0) * 1000)
        await client.aclose()
        status = "warning" if ms > 1000 else "ok"
        return {"name": "redis", "category": "infrastructure", "status": status,
                "message": f"PONG received in {ms}ms.", "response_time_ms": ms, "last_checked": _now_iso()}
    except Exception as e:
        return {"name": "redis", "category": "infrastructure", "status": "error",
                "message": str(e), "last_checked": _now_iso()}


async def _check_tutti() -> dict:
    try:
        from backend.services.marketplace.adapters.tutti import TuttiAdapter
        adapter = TuttiAdapter()
        result = await adapter.health_check()
        result["name"] = "tutti_scraper"
        result["category"] = "marketplace"
        result["last_checked"] = _now_iso()
        return result
    except Exception as e:
        return {"name": "tutti_scraper", "category": "marketplace", "status": "error",
                "message": str(e), "last_checked": _now_iso()}


async def _check_sec_edgar() -> dict:
    try:
        from backend.services.investment.sources.sec_edgar import SECEdgarAdapter
        adapter = SECEdgarAdapter()
        result = await adapter.health_check()
        result["name"] = "sec_edgar"
        result["category"] = "investment"
        result["last_checked"] = _now_iso()
        return result
    except Exception as e:
        return {"name": "sec_edgar", "category": "investment", "status": "error",
                "message": str(e), "last_checked": _now_iso()}


def _check_course_index() -> dict:
    index_dir = Path("course_index")
    master = index_dir / "master_index.json"
    if not master.exists():
        return {"name": "course_index", "category": "investment", "status": "error",
                "message": "master_index.json not found.", "last_checked": _now_iso()}
    import json
    index = json.loads(master.read_text(encoding="utf-8"))
    chapters = list(index_dir.glob("chapter_*_summary.md"))
    return {"name": "course_index", "category": "investment", "status": "ok",
            "message": f"master_index.json valid. {len(index)} situation types, {len(chapters)} chapters indexed.",
            "last_checked": _now_iso()}


async def _check_openclaw_crons(db: AsyncSession) -> list[dict]:
    now = datetime.now(timezone.utc)
    results = []
    for task_name, expected_hours in EXPECTED_INTERVALS.items():
        # Query most recent heartbeat for this task from DB
        row = await db.execute(
            sa.select(HealthCheck)
            .where(HealthCheck.component == f"cron_{task_name}")
            .order_by(HealthCheck.checked_at.desc())
            .limit(1)
        )
        hb = row.scalars().first()

        if hb is None:
            results.append({
                "name": f"openclaw_cron_{task_name}",
                "category": "operational",
                "status": "warning",
                "message": f"No heartbeat received yet. Expected every {expected_hours}h.",
                "last_checked": _now_iso(),
            })
            continue

        elapsed_h = (now - hb.checked_at).total_seconds() / 3600
        if elapsed_h > expected_hours * 2:
            status, suffix = "error", "STALLED."
        elif elapsed_h > expected_hours * 1.5:
            status, suffix = "warning", ""
        else:
            status, suffix = "ok", ""

        results.append({
            "name": f"openclaw_cron_{task_name}",
            "category": "operational",
            "status": status,
            "message": f"Last run {elapsed_h:.1f}h ago. Expected every {expected_hours}h. {suffix}".strip(),
            "last_run": hb.checked_at.isoformat(),
            "expected_interval_hours": expected_hours,
            "last_checked": _now_iso(),
        })
    return results


def _build_recommendations(components: list[dict]) -> list[str]:
    recs = []
    for c in components:
        if c["status"] == "error":
            name = c["name"]
            msg = c.get("message", "")
            if name == "postgresql":
                recs.append(f"PostgreSQL is down: {msg}. Check: docker compose ps")
            elif name == "redis":
                recs.append(f"Redis is down: {msg}. Check: docker compose ps")
            elif name == "tutti_scraper":
                recs.append("Tutti.ch scraper blocked. Options: rotate User-Agent or use proxy.")
            elif name == "sec_edgar":
                recs.append(f"SEC EDGAR failing: {msg}. Check SEC_USER_AGENT env var.")
            elif name == "course_index":
                recs.append("Course index missing. Run: python scripts/ingest_course.py")
            elif "openclaw_cron" in name:
                task = name.replace("openclaw_cron_", "")
                recs.append(f"OpenClaw cron '{task}' stalled. Check crontab -l on VPS.")
        elif c["status"] == "warning":
            if "openclaw_cron" in c["name"]:
                task = c["name"].replace("openclaw_cron_", "")
                recs.append(f"OpenClaw cron '{task}' running late.")
    return recs


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("/ping")
async def ping():
    return {"status": "ok", "timestamp": _now_iso()}


@router.get("/full")
async def full_health_check(db: AsyncSession = Depends(get_db)):
    import asyncio
    pg, redis, tutti, sec = await asyncio.gather(
        _check_postgres(), _check_redis(), _check_tutti(), _check_sec_edgar(),
    )
    components: list[dict] = [pg, redis, tutti, sec]
    components.append(_check_course_index())
    components.extend(await _check_openclaw_crons(db))

    ok = sum(1 for c in components if c["status"] == "ok")
    warnings = sum(1 for c in components if c["status"] == "warning")
    errors = sum(1 for c in components if c["status"] == "error")

    overall = "healthy"
    if errors > 0:
        overall = "critical" if errors >= len(components) // 2 else "degraded"
    elif warnings > 0:
        overall = "degraded"

    return {
        "status": overall,
        "timestamp": _now_iso(),
        "uptime_seconds": round(time.time() - _start_time),
        "components": components,
        "recommendations": _build_recommendations(components),
        "summary": {"total_components": len(components), "ok": ok, "warning": warnings, "error": errors},
    }


@router.post("/heartbeat")
async def heartbeat(req: HeartbeatRequest, db: AsyncSession = Depends(get_db)):
    """Called by OpenClaw crons after each task execution. Persists to DB."""
    hb = HealthCheck(
        component=f"cron_{req.task_name}",
        status=req.status,
        message=f"items_processed={req.items_processed} errors={req.errors}",
    )
    db.add(hb)

    run_id = await run_logger.start_run(
        db,
        agent_name="system_doctor",
        agent_type="cron",
        module="api.health.router",
        runtime="cron",
        trigger_source="cron",
        task_name=req.task_name,
        input_summary=f"Heartbeat: items_processed={req.items_processed} errors={req.errors}",
    )
    await run_logger.finish_run(
        db, run_id,
        output_summary=f"Heartbeat received: {req.status}",
        final_outcome=req.status,
        outcome_score=1 if req.errors == 0 else 0,
    )

    await db.commit()
    return {"acknowledged": True, "task_name": req.task_name}
