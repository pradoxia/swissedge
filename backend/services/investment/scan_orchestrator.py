from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.investment import DetectionRun
from backend.services.investment.auto_acquisition import auto_acquire_for_created_situations
from backend.services.investment.sec_detection import run_sec_edgar_detection
from backend.services.investment.sources.sec_edgar import SECEdgarAdapter


logger = logging.getLogger(__name__)

ScanTriggerType = Literal["manual", "scheduled"]
ScanSource = Literal["sec_edgar"]

SUCCESS_WITH_RESULTS = "success_with_results"
SUCCESS_EMPTY = "success_empty"
PARTIAL_SUCCESS = "partial_success"
FAILED_SOURCE_ERROR = "failed_source_error"
FAILED_CONFIG_ERROR = "failed_config_error"
FAILED_DATABASE_ERROR = "failed_database_error"
FAILED_UNKNOWN = "failed_unknown"


async def run_special_situation_scan(
    db: AsyncSession,
    *,
    source: ScanSource = "sec_edgar",
    trigger_type: ScanTriggerType,
    hours_back: int = 36,
    dry_run: bool = False,
    adapter: SECEdgarAdapter | None = None,
    require_sec_user_agent: bool = True,
) -> dict[str, Any]:
    """Run controlled special situation detection and record a DetectionRun."""
    if source != "sec_edgar":
        raise ValueError("Sprint 2 only supports source=sec_edgar")
    if trigger_type not in {"manual", "scheduled"}:
        raise ValueError("trigger_type must be manual or scheduled")
    if hours_back <= 0:
        raise ValueError("hours_back must be positive")

    started = datetime.now(timezone.utc)
    settings = get_settings()
    forms_checked = list(SECEdgarAdapter.FILING_TYPES)
    config_status = _sec_config_status(settings.sec_user_agent)

    run = DetectionRun(
        source=source,
        started_at=started,
        status="running",
        dry_run=dry_run,
        hours_back=hours_back,
        forms_checked_json=forms_checked,
        summary_json={
            "source": source,
            "trigger_type": trigger_type,
            "forms_checked": forms_checked,
            "config": config_status,
            "guardrails": _guardrails(),
        },
    )
    db.add(run)
    try:
        await db.flush()
        await db.commit()
    except Exception as exc:
        logger.exception("DetectionRun start failed for source=%s trigger_type=%s", source, trigger_type)
        raise RuntimeError("failed_database_error: could not start DetectionRun") from exc

    if require_sec_user_agent and not config_status["sec_user_agent_configured"]:
        summary = _base_summary(
            run_id=str(run.id),
            source=source,
            trigger_type=trigger_type,
            started_at=started,
            status=FAILED_CONFIG_ERROR,
            hours_back=hours_back,
            dry_run=dry_run,
            forms_checked=forms_checked,
            config_status=config_status,
            warnings=["SEC_USER_AGENT is not configured; scan was not started."],
            errors=["Missing SEC_USER_AGENT"],
        )
        await _finish_run(db, run, summary, error_message="Missing SEC_USER_AGENT")
        return summary

    logger.info(
        "Special situation scan started run_id=%s source=%s trigger_type=%s hours_back=%s dry_run=%s",
        run.id,
        source,
        trigger_type,
        hours_back,
        dry_run,
    )

    try:
        detection_summary = await run_sec_edgar_detection(
            db,
            hours_back=hours_back,
            dry_run=dry_run,
            adapter=adapter,
            trigger_type=trigger_type,
        )
    except Exception as exc:
        logger.exception("Special situation scan failed unexpectedly run_id=%s", run.id)
        summary = _base_summary(
            run_id=str(run.id),
            source=source,
            trigger_type=trigger_type,
            started_at=started,
            status=FAILED_UNKNOWN,
            hours_back=hours_back,
            dry_run=dry_run,
            forms_checked=forms_checked,
            config_status=config_status,
            warnings=[],
            errors=[str(exc)],
        )
        await _finish_run(db, run, summary, error_message=str(exc))
        return summary

    # W1 (Dani-approved 2026-06-11): automatic SEC document acquisition for
    # situations created in this run. Bounded, SEC-only, fail-safe: any failure
    # becomes a warning and never breaks detection. evidence_found != verified.
    auto_acquisition_summary: dict[str, Any] = {
        "enabled": bool(getattr(settings, "auto_acquire_documents", True)),
        "situations_processed": 0,
        "documents_acquired": 0,
        "resources_marked_evidence_found": 0,
        "warnings": [],
    }
    created_entries = list(detection_summary.get("created_situations") or [])
    if auto_acquisition_summary["enabled"] and not dry_run and created_entries:
        try:
            enrichment = await auto_acquire_for_created_situations(db, created_entries)
            auto_acquisition_summary.update(enrichment)
        except Exception as exc:  # never break detection
            logger.exception("Auto-acquisition enrichment failed safely run_id=%s", run.id)
            auto_acquisition_summary["warnings"].append(f"Auto-acquisition failed safely: {exc}")
    detection_summary["auto_acquisition"] = auto_acquisition_summary

    warnings = _warnings_from_detection_summary(detection_summary)
    warnings.extend(auto_acquisition_summary.get("warnings") or [])
    errors = list(detection_summary.get("errors") or [])
    status = _status_from_detection_summary(detection_summary, errors)
    summary = {
        **detection_summary,
        "run_id": str(run.id),
        "source": source,
        "trigger_type": trigger_type,
        "status": status,
        "started_at": detection_summary.get("started_at") or started.isoformat(),
        "finished_at": detection_summary.get("completed_at"),
        "forms_checked": detection_summary.get("forms_checked") or forms_checked,
        "raw_hits_found": detection_summary.get("raw_hits_count", detection_summary.get("raw_hits", 0)),
        "classified_hits": detection_summary.get("classified_count", detection_summary.get("classified_filings", 0)),
        "duplicates_skipped": detection_summary.get("duplicates_skipped", 0),
        "new_special_situations_created": detection_summary.get("special_situations_created", 0),
        "existing_special_situations_touched": detection_summary.get("special_situations_updated", 0),
        "warnings": warnings,
        "errors": errors,
        "duration_seconds": _duration_seconds(detection_summary),
        "config": config_status,
        "guardrails": _guardrails(),
    }

    await _finish_run(db, run, summary, error_message="; ".join(errors) if errors else None)
    logger.info(
        "Special situation scan finished run_id=%s status=%s raw_hits=%s created=%s duplicates=%s errors=%s",
        run.id,
        status,
        summary.get("raw_hits_found"),
        summary.get("new_special_situations_created"),
        summary.get("duplicates_skipped"),
        len(errors),
    )
    return summary


def _sec_config_status(sec_user_agent: str | None) -> dict[str, Any]:
    configured = bool((sec_user_agent or "").strip())
    return {
        "sec_user_agent_configured": configured,
        "sec_user_agent_status": "configured" if configured else "missing",
        "secret_values_logged": False,
    }


def _guardrails() -> dict[str, bool]:
    return {
        "no_live_ai": True,
        "no_research_case_creation": True,
        "no_auto_promotion": True,
        "no_auto_discard": True,
        "no_auto_publish": True,
        "no_investment_recommendation": True,
    }


def _base_summary(
    *,
    run_id: str,
    source: str,
    trigger_type: str,
    started_at: datetime,
    status: str,
    hours_back: int,
    dry_run: bool,
    forms_checked: list[str],
    config_status: dict[str, Any],
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any]:
    finished = datetime.now(timezone.utc)
    return {
        "run_id": run_id,
        "source": source,
        "trigger_type": trigger_type,
        "started_at": started_at.isoformat(),
        "finished_at": finished.isoformat(),
        "completed_at": finished.isoformat(),
        "status": status,
        "hours_back": hours_back,
        "dry_run": dry_run,
        "forms_checked": forms_checked,
        "raw_hits": 0,
        "raw_hits_found": 0,
        "filings_fetched": 0,
        "classified_hits": 0,
        "duplicates_skipped": 0,
        "special_situations_created": 0,
        "new_special_situations_created": 0,
        "existing_special_situations_touched": 0,
        "warnings": warnings,
        "errors": errors,
        "duration_seconds": (finished - started_at).total_seconds(),
        "config": config_status,
        "guardrails": _guardrails(),
    }


def _status_from_detection_summary(summary: dict[str, Any], errors: list[str]) -> str:
    created = int(summary.get("special_situations_created") or 0)
    parsed = int(summary.get("parsed_filings") or summary.get("filings_fetched") or 0)
    raw_hits = int(summary.get("raw_hits_count") or summary.get("raw_hits") or 0)
    if errors:
        if created > 0 or parsed > 0 or raw_hits > 0:
            return PARTIAL_SUCCESS
        return FAILED_SOURCE_ERROR
    if created > 0:
        return SUCCESS_WITH_RESULTS
    return SUCCESS_EMPTY


def _warnings_from_detection_summary(summary: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if summary.get("rate_limit_backoff_events"):
        warnings.append("SEC EDGAR rate-limit/backoff events occurred.")
    if int(summary.get("duplicates_skipped") or 0) > 0 and int(summary.get("special_situations_created") or 0) == 0:
        warnings.append("Scan completed with duplicate-only results.")
    if int(summary.get("raw_hits_count") or summary.get("raw_hits") or 0) == 0:
        warnings.append("Scan completed with no raw hits.")
    return warnings


def _duration_seconds(summary: dict[str, Any]) -> float | None:
    started = _parse_dt(summary.get("started_at"))
    completed = _parse_dt(summary.get("completed_at"))
    if started and completed:
        return (completed - started).total_seconds()
    return None


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


async def _finish_run(db: AsyncSession, run: DetectionRun, summary: dict[str, Any], *, error_message: str | None = None) -> None:
    counters = _counters_from_orchestrator_summary(summary)
    run.status = str(summary["status"])
    run.finished_at = datetime.now(timezone.utc)
    run.raw_hits = counters["raw_hits"]
    run.parsed_filings = counters["parsed_filings"]
    run.classified_filings = counters["classified_filings"]
    run.unclassified_filings = counters["unclassified_filings"]
    run.duplicates_skipped = counters["duplicates_skipped"]
    run.special_situations_created = counters["special_situations_created"]
    run.errors_count = counters["errors_count"]
    run.runtime_seconds = counters["runtime_seconds"]
    run.forms_checked_json = summary.get("forms_checked")
    run.per_form_summary_json = summary.get("per_form_summary")
    run.summary_json = summary
    run.error_message = error_message
    try:
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.exception("DetectionRun finish failed for run_id=%s", run.id)
        raise RuntimeError("failed_database_error: could not finish DetectionRun") from exc


def _counters_from_orchestrator_summary(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw_hits": int(summary.get("raw_hits_found") or summary.get("raw_hits_count") or summary.get("raw_hits") or 0),
        "parsed_filings": int(summary.get("parsed_filings") or summary.get("filings_fetched") or 0),
        "classified_filings": int(summary.get("classified_hits") or summary.get("classified_count") or summary.get("classified_filings") or 0),
        "unclassified_filings": int(summary.get("unclassified_filings") or summary.get("unsupported_forms_skipped") or 0),
        "duplicates_skipped": int(summary.get("duplicates_skipped") or 0),
        "special_situations_created": int(summary.get("new_special_situations_created") or summary.get("special_situations_created") or 0),
        "errors_count": len(summary.get("errors") or []),
        "runtime_seconds": summary.get("duration_seconds"),
    }
