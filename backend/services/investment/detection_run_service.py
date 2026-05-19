from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.db.database import AsyncSessionLocal
from backend.models.investment import DetectionRun


logger = logging.getLogger(__name__)

RUNNING = "running"
SUCCESS = "success"
PARTIAL = "partial"
FAILED = "failed"


class DetectionRunRead(BaseModel):
    id: str
    source: str
    started_at: str | None
    finished_at: str | None
    status: str
    dry_run: bool
    hours_back: int | None
    raw_hits: int
    parsed_filings: int
    classified_filings: int
    unclassified_filings: int
    outside_lookback_skipped: int
    missing_filing_date_skipped: int
    unsupported_forms_skipped: int
    candidates_detected: int
    duplicates_skipped: int
    special_situations_created: int
    errors_count: int
    runtime_seconds: float | None
    forms_checked_json: Any = None
    per_form_summary: Any = None
    per_form_summary_json: Any = None
    summary_json: Any = None
    error_message: str | None = None
    created_at: str | None


def serialize_detection_run(run: DetectionRun) -> dict[str, Any]:
    summary = run.summary_json if isinstance(run.summary_json, dict) else {}
    per_form = run.per_form_summary_json if isinstance(run.per_form_summary_json, dict) else {}
    fallback_counters = counters_from_summary({**summary, "per_form_summary": summary.get("per_form_summary") or per_form})
    diagnostics = diagnostics_from_summary({**summary, "per_form_summary": summary.get("per_form_summary") or per_form})
    return DetectionRunRead(
        id=str(run.id),
        source=run.source,
        started_at=run.started_at.isoformat() if run.started_at else None,
        finished_at=run.finished_at.isoformat() if run.finished_at else None,
        status=run.status,
        dry_run=run.dry_run,
        hours_back=run.hours_back,
        raw_hits=_stored_or_fallback(run.raw_hits, fallback_counters["raw_hits"]),
        parsed_filings=_stored_or_fallback(run.parsed_filings, fallback_counters["parsed_filings"]),
        classified_filings=_stored_or_fallback(run.classified_filings, fallback_counters["classified_filings"]),
        unclassified_filings=_stored_or_fallback(run.unclassified_filings, fallback_counters["unclassified_filings"]),
        outside_lookback_skipped=diagnostics["outside_lookback_skipped"],
        missing_filing_date_skipped=diagnostics["missing_filing_date_skipped"],
        unsupported_forms_skipped=diagnostics["unsupported_forms_skipped"],
        candidates_detected=diagnostics["candidates_detected"],
        duplicates_skipped=_stored_or_fallback(run.duplicates_skipped, fallback_counters["duplicates_skipped"]),
        special_situations_created=_stored_or_fallback(run.special_situations_created, fallback_counters["special_situations_created"]),
        errors_count=_stored_or_fallback(run.errors_count, fallback_counters["errors_count"]),
        runtime_seconds=run.runtime_seconds if run.runtime_seconds is not None else fallback_counters["runtime_seconds"],
        forms_checked_json=run.forms_checked_json,
        per_form_summary=run.per_form_summary_json or fallback_counters["per_form_summary_json"],
        per_form_summary_json=run.per_form_summary_json or fallback_counters["per_form_summary_json"],
        summary_json=run.summary_json,
        error_message=run.error_message,
        created_at=run.created_at.isoformat() if run.created_at else None,
    ).model_dump()


class DetectionRunService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal):
        self.session_factory = session_factory

    async def start_run(self, *, source: str = "sec_edgar", hours_back: int | None = None, dry_run: bool = True, forms_checked: list[str] | None = None) -> uuid.UUID | None:
        try:
            async with self.session_factory() as db:
                run = DetectionRun(
                    id=uuid.uuid4(),
                    source=source,
                    status=RUNNING,
                    dry_run=dry_run,
                    hours_back=hours_back,
                    forms_checked_json=forms_checked or [],
                )
                db.add(run)
                await db.commit()
                return run.id
        except Exception as exc:
            logger.warning("DetectionRun start failed safely: %s", exc)
            return None

    async def update_counters(self, run_id: uuid.UUID | str | None, **counters: Any) -> None:
        if not run_id:
            return
        allowed = {
            "raw_hits",
            "parsed_filings",
            "classified_filings",
            "unclassified_filings",
            "duplicates_skipped",
            "special_situations_created",
            "errors_count",
            "runtime_seconds",
            "forms_checked_json",
            "per_form_summary_json",
            "summary_json",
            "error_message",
        }
        await self._safe_update(run_id, {key: value for key, value in counters.items() if key in allowed})

    async def store_per_form_metrics(self, run_id: uuid.UUID | str | None, per_form_summary: dict[str, Any]) -> None:
        await self.update_counters(run_id, per_form_summary_json=per_form_summary)

    async def mark_success(self, run_id: uuid.UUID | str | None, summary: dict[str, Any] | None = None) -> None:
        await self._finish(run_id, SUCCESS, summary=summary)

    async def mark_partial(self, run_id: uuid.UUID | str | None, summary: dict[str, Any] | None = None, error_message: str | None = None) -> None:
        await self._finish(run_id, PARTIAL, summary=summary, error_message=error_message)

    async def mark_failed(self, run_id: uuid.UUID | str | None, error_message: str, summary: dict[str, Any] | None = None) -> None:
        await self._finish(run_id, FAILED, summary=summary, error_message=error_message)

    async def _finish(
        self,
        run_id: uuid.UUID | str | None,
        status: str,
        *,
        summary: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        updates: dict[str, Any] = {
            "status": status,
            "finished_at": datetime.now(timezone.utc),
        }
        if summary is not None:
            updates.update(counters_from_summary(summary))
            updates["summary_json"] = summary
        if error_message:
            updates["error_message"] = error_message
            updates["errors_count"] = max(int(updates.get("errors_count") or 0), 1)
        await self._safe_update(run_id, updates)

    async def _safe_update(self, run_id: uuid.UUID | str | None, updates: dict[str, Any]) -> None:
        if not run_id or not updates:
            return
        try:
            async with self.session_factory() as db:
                run = await db.get(DetectionRun, uuid.UUID(str(run_id)))
                if not run:
                    return
                for key, value in updates.items():
                    setattr(run, key, value)
                await db.commit()
        except Exception as exc:
            logger.warning("DetectionRun update failed safely: %s", exc)


def counters_from_summary(summary: dict[str, Any]) -> dict[str, Any]:
    per_form = summary.get("per_form_summary") or summary.get("by_form") or {}
    form_counts = summary.get("form_counts") if isinstance(summary.get("form_counts"), dict) else {}
    raw_hits = _first_present(summary, "raw_hits", "raw_hits_total")
    if raw_hits is None:
        raw_hits = _sum_per_form(per_form, "raw", "raw_hits")
    if raw_hits is None:
        raw_hits = _first_present(summary, "filings_fetched", "parsed_filings", "parsed_filings_total", default=0)
    started = _parse_dt(summary.get("started_at"))
    completed = _parse_dt(summary.get("completed_at"))
    runtime = (completed - started).total_seconds() if started and completed else summary.get("runtime_seconds")
    return {
        "raw_hits": int(raw_hits or 0),
        "parsed_filings": int(_first_present(summary, "parsed_filings", "filings_fetched", "parsed_filings_total", default=0) or 0),
        "classified_filings": int(_first_present(summary, "classified_filings", "candidates_detected", "classified_candidates_count", default=0) or 0),
        "unclassified_filings": int(_first_present(summary, "unclassified_filings", "unsupported_forms_skipped", "skipped_unclassified_count", default=0) or 0),
        "duplicates_skipped": int(_first_present(summary, "duplicates_skipped", "skipped_duplicate_count", default=0) or 0),
        "special_situations_created": int(_first_present(summary, "special_situations_created", "created_count", default=0) or 0),
        "errors_count": len(summary.get("errors") or []),
        "runtime_seconds": runtime,
        "forms_checked_json": list(form_counts.keys()) if form_counts else summary.get("forms_checked"),
        "per_form_summary_json": per_form or form_counts,
    }


def diagnostics_from_summary(summary: dict[str, Any]) -> dict[str, int]:
    return {
        "outside_lookback_skipped": int(_first_present(summary, "outside_lookback_skipped", default=0) or 0),
        "missing_filing_date_skipped": int(_first_present(summary, "missing_filing_date_skipped", default=0) or 0),
        "unsupported_forms_skipped": int(_first_present(summary, "unsupported_forms_skipped", "skipped_unclassified_count", default=0) or 0),
        "candidates_detected": int(_first_present(summary, "candidates_detected", "classified_filings", "classified_candidates_count", default=0) or 0),
    }


def _stored_or_fallback(stored: Any, fallback: Any) -> int:
    stored_int = int(stored or 0)
    fallback_int = int(fallback or 0)
    return stored_int if stored_int != 0 else fallback_int


def _first_present(summary: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = summary.get(key)
        if value is not None:
            return value
    return default


def _sum_per_form(per_form: Any, *keys: str) -> int | None:
    if not isinstance(per_form, dict):
        return None
    total = 0
    found = False
    for item in per_form.values():
        if not isinstance(item, dict):
            continue
        for key in keys:
            if item.get(key) is not None:
                total += int(item.get(key) or 0)
                found = True
                break
    return total if found else None


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


async def get_latest_runs(db: AsyncSession, *, limit: int = 20) -> list[DetectionRun]:
    result = await db.execute(select(DetectionRun).order_by(DetectionRun.started_at.desc()).limit(limit))
    return list(result.scalars().all())


def build_detection_run_status(runs: list[DetectionRun], *, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    latest = runs[0] if runs else None
    latest_success = next((run for run in runs if run.status == SUCCESS), None)
    latest_failed = next((run for run in runs if run.status == FAILED), None)
    recent_errors_count = sum((run.errors_count or 0) for run in runs)
    age_minutes = None
    if latest and latest.started_at:
        age_minutes = round((now - latest.started_at).total_seconds() / 60, 1)

    if latest is None:
        status = "no_runs"
    elif age_minutes is not None and age_minutes > 24 * 60:
        status = "stale"
    elif latest.status in {FAILED, RUNNING} or recent_errors_count:
        status = "warning"
    else:
        status = "healthy"

    return {
        "latest_run": serialize_detection_run(latest) if latest else None,
        "latest_successful_run": serialize_detection_run(latest_success) if latest_success else None,
        "latest_failed_run": serialize_detection_run(latest_failed) if latest_failed else None,
        "total_recent_runs": len(runs),
        "recent_errors_count": recent_errors_count,
        "last_run_age_minutes": age_minutes,
        "status": status,
        "cron_safe_defaults": {
            "enabled_default": False,
            "dry_run_default": True,
            "hours_back_default": 48,
        },
        "guardrails": {
            "no_scan_trigger": True,
            "read_only_api": True,
            "no_live_ai": True,
            "no_auto_promotion": True,
        },
    }
