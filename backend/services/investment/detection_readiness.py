from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from backend.models.investment import DetectionRun
from backend.services.investment.detection_run_service import FAILED, SUCCESS, serialize_detection_run


ReadinessLevel = Literal["not_ready", "observe_more", "ready_for_limited_live_create"]


class DetectionLiveCreateScope(BaseModel):
    allowed_forms: list[str]
    conservative_forms: list[str]
    notes: list[str]


class DetectionReadinessPackage(BaseModel):
    readiness_level: ReadinessLevel
    reasons: list[str]
    blockers: list[str]
    warnings: list[str]
    recommended_next_step: str
    suggested_live_create_scope: DetectionLiveCreateScope
    recent_runs_evaluated: int
    latest_run: dict[str, Any] | None
    guardrails: dict[str, bool]


DEFAULT_SCOPE = DetectionLiveCreateScope(
    allowed_forms=["SC TO-T", "SC TO-I", "Form 10"],
    conservative_forms=["8-K"],
    notes=[
        "8-K should remain conservative: strong liquidation/dissolution signals only or review-only.",
        "Limited live-create creates SpecialSituations only; it must not create ResearchCases.",
    ],
)


def build_detection_readiness(runs: list[DetectionRun]) -> DetectionReadinessPackage:
    latest = serialize_detection_run(runs[0]) if runs else None
    reasons: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []

    if not runs:
        blockers.append("No DetectionRun records exist yet.")
        return _package("not_ready", reasons, blockers, warnings, "Run at least one SEC EDGAR dry-run and review DetectionRun status.", latest, 0)

    latest_status = str(latest.get("status") if latest else "")
    if latest_status == FAILED:
        blockers.append("Latest DetectionRun failed.")
        return _package("not_ready", reasons, blockers, warnings, "Fix the latest detection error, then run another dry-run.", latest, len(runs))

    recent_errors = sum(int((serialize_detection_run(run).get("errors_count") or 0)) for run in runs)
    if recent_errors > 0:
        warnings.append(f"Recent DetectionRuns include {recent_errors} error(s).")

    raw_hits = int((latest or {}).get("raw_hits") or 0)
    classified = int((latest or {}).get("classified_filings") or 0)
    created = int((latest or {}).get("special_situations_created") or 0)
    dry_run = bool((latest or {}).get("dry_run"))
    backoff_events = _latest_backoff_events(latest)
    healthy_dry_runs = [
        serialize_detection_run(run)
        for run in runs
        if run.status == SUCCESS and run.dry_run and int((run.errors_count or 0)) == 0
    ]

    if backoff_events:
        warnings.append(_backoff_warning(backoff_events))
    if raw_hits > 0 and classified == 0:
        warnings.append("Latest run saw raw SEC hits but classified no candidates; observe more unless this matches expected quiet-period behavior.")
    if created > 0 and dry_run:
        blockers.append("Latest run is marked dry-run but reports created SpecialSituations.")
        return _package("not_ready", reasons, blockers, warnings, "Investigate dry-run creation counters before considering live-create.", latest, len(runs))
    if latest_status != SUCCESS:
        warnings.append(f"Latest DetectionRun status is {latest_status}.")
        return _package("observe_more", reasons, blockers, warnings, "Wait for a successful dry-run before live-create review.", latest, len(runs))
    if not dry_run:
        warnings.append("Latest run was already live-create; this readiness package does not activate or validate live-create.")

    if recent_errors > 0:
        return _package("observe_more", reasons, blockers, warnings, "Observe additional clean dry-runs before considering live-create.", latest, len(runs))

    reasons.append("Latest DetectionRun completed successfully with zero errors.")
    if dry_run:
        reasons.append("Latest run was dry-run, so no SpecialSituations were created.")
    if backoff_events:
        reasons.append("Latest DetectionRun completed, but SEC backoff events require another dry-run observation.")
        return _package("observe_more", reasons, blockers, warnings, "Keep dry-run enabled and observe the next scheduled run.", latest, len(runs))
    if len(healthy_dry_runs) >= 2:
        reasons.append("Multiple recent dry-runs are healthy.")
        return _package("ready_for_limited_live_create", reasons, blockers, warnings, "Dani may review limited live-create scope; do not enable it until explicitly approved.", latest, len(runs))

    reasons.append("Only one recent healthy dry-run is available.")
    return _package("observe_more", reasons, blockers, warnings, "Collect another healthy dry-run before deciding on limited live-create.", latest, len(runs))


def _latest_backoff_events(latest: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not latest:
        return []

    summary = latest.get("summary_json")
    if not isinstance(summary, dict):
        return []

    events = summary.get("rate_limit_backoff_events")
    if not isinstance(events, list):
        return []

    return [event for event in events if isinstance(event, dict)]


def _backoff_warning(events: list[dict[str, Any]]) -> str:
    details = []
    for event in events:
        detail = (
            f"filing_type={event.get('filing_type') or 'unknown'}, "
            f"status_code={event.get('status_code') or 'unknown'}, "
            f"backoff_seconds={event.get('backoff_seconds') or 'unknown'}"
        )
        details.append(detail)

    return f"SEC backoff events occurred during the latest run. Details: {'; '.join(details)}."


def _package(
    level: ReadinessLevel,
    reasons: list[str],
    blockers: list[str],
    warnings: list[str],
    next_step: str,
    latest_run: dict[str, Any] | None,
    count: int,
) -> DetectionReadinessPackage:
    return DetectionReadinessPackage(
        readiness_level=level,
        reasons=reasons,
        blockers=blockers,
        warnings=warnings,
        recommended_next_step=next_step,
        suggested_live_create_scope=DEFAULT_SCOPE,
        recent_runs_evaluated=count,
        latest_run=latest_run,
        guardrails={
            "read_only": True,
            "no_scan_trigger": True,
            "no_live_ai": True,
            "no_evaluator": True,
            "no_auto_promotion": True,
            "no_auto_discard": True,
            "no_auto_verification": True,
        },
    )
