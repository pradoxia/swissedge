"""
Non-blocking observability helpers.
All public functions are wrapped in try/except so a DB failure never breaks business logic.
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.observability import AgentRun, AiUsage


# ── Cost table ────────────────────────────────────────────────────────────────
# Per-million-token prices in USD. Update when pricing changes.
_COST_PER_M: dict[str, dict[str, float]] = {
    "gpt-4o-mini":        {"input": 0.150,  "output": 0.600},
    "gpt-4o":             {"input": 2.500,  "output": 10.000},
    "claude-haiku-4-5":   {"input": 0.800,  "output": 4.000},
    "claude-haiku-4-5-20251001": {"input": 0.800, "output": 4.000},
    "claude-sonnet-4-6":  {"input": 3.000,  "output": 15.000},
    "claude-opus-4-7":    {"input": 15.000, "output": 75.000},
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = _COST_PER_M.get(model)
    if not prices:
        return 0.0
    return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# ── Run lifecycle ─────────────────────────────────────────────────────────────

async def start_run(
    db: AsyncSession,
    *,
    agent_name: str,
    agent_type: str,
    module: str = "",
    runtime: str = "fastapi",
    trigger_source: str = "api_call",
    task_name: str = "",
    input_summary: str = "",
    human_approval_required: bool = False,
) -> uuid.UUID | None:
    try:
        run = AgentRun(
            agent_name=agent_name,
            agent_type=agent_type,
            module=module,
            runtime=runtime,
            trigger_source=trigger_source,
            task_name=task_name,
            input_summary=input_summary,
            status="started",
            started_at=datetime.now(timezone.utc),
            human_approval_required=human_approval_required,
        )
        db.add(run)
        await db.flush()
        return run.id
    except Exception:
        return None


async def finish_run(
    db: AsyncSession,
    run_id: uuid.UUID | None,
    *,
    output_summary: str = "",
    final_outcome: str = "",
    outcome_score: int | None = None,
    model_used: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    api_calls_made: list[Any] | None = None,
    database_records_created: dict[str, int] | None = None,
) -> None:
    if run_id is None:
        return
    try:
        from sqlalchemy import select
        result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = result.scalars().first()
        if not run:
            return
        now = datetime.now(timezone.utc)
        run.status = "completed"
        run.finished_at = now
        run.duration_ms = round((now - run.started_at).total_seconds() * 1000)
        run.output_summary = output_summary
        run.final_outcome = final_outcome
        run.outcome_score = outcome_score
        run.model_used = model_used
        run.input_tokens = input_tokens
        run.output_tokens = output_tokens
        if model_used and input_tokens is not None and output_tokens is not None:
            run.estimated_cost = estimate_cost(model_used, input_tokens, output_tokens)
        if api_calls_made is not None:
            run.api_calls_made = api_calls_made
        if database_records_created is not None:
            run.database_records_created = database_records_created
        await db.flush()
    except Exception:
        pass


async def fail_run(
    db: AsyncSession,
    run_id: uuid.UUID | None,
    error_message: str,
) -> None:
    if run_id is None:
        return
    try:
        from sqlalchemy import select
        result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = result.scalars().first()
        if not run:
            return
        now = datetime.now(timezone.utc)
        run.status = "failed"
        run.finished_at = now
        run.duration_ms = round((now - run.started_at).total_seconds() * 1000)
        run.error_message = error_message[:2000]
        run.outcome_score = 0
        await db.flush()
    except Exception:
        pass


async def log_ai_usage(
    db: AsyncSession,
    *,
    run_id: uuid.UUID | None,
    agent_name: str,
    provider: str,
    model: str,
    prompt_name: str = "",
    input_tokens: int,
    output_tokens: int,
) -> None:
    try:
        cost = estimate_cost(model, input_tokens, output_tokens)
        usage = AiUsage(
            run_id=run_id,
            agent_name=agent_name,
            provider=provider,
            model=model,
            prompt_name=prompt_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost=cost,
        )
        db.add(usage)
        await db.flush()
    except Exception:
        pass
