from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.investment import SpecialSituation
from backend.services.investment.methodology_workspace import attach_methodology_workspace_to_evidence
from backend.services.investment.routing_engine import build_routing_decision
from backend.services.investment.sources.base import Filing
from backend.services.investment.sources.sec_edgar import SECEdgarAdapter


logger = logging.getLogger(__name__)

SUPPORTED_P1_FORMS = {"SC TO-T", "SC TO-I", "Form 10", "8-K"}


@dataclass
class SecDetectionRunSummary:
    started_at: str
    completed_at: str | None = None
    lookback_hours: int = 36
    filings_fetched: int = 0
    filings_inspected: int = 0
    candidates_detected: int = 0
    unclassified_filings: int = 0
    duplicates_skipped: int = 0
    unsupported_forms_skipped: int = 0
    outside_lookback_skipped: int = 0
    missing_filing_date_skipped: int = 0
    query_start_date: str | None = None
    query_end_date: str | None = None
    oldest_filing_date_seen: str | None = None
    newest_filing_date_seen: str | None = None
    form_counts: dict[str, int] = field(default_factory=dict)
    per_form_summary: dict[str, dict[str, int]] = field(default_factory=dict)
    special_situations_created: int = 0
    special_situations_updated: int = 0
    errors: list[str] = field(default_factory=list)
    rate_limit_backoff_events: list[dict[str, Any]] = field(default_factory=list)
    dry_run: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "lookback_hours": self.lookback_hours,
            "filings_fetched": self.filings_fetched,
            "filings_inspected": self.filings_inspected,
            "candidates_detected": self.candidates_detected,
            "classified_filings": self.candidates_detected,
            "unclassified_filings": self.unclassified_filings,
            "duplicates_skipped": self.duplicates_skipped,
            "unsupported_forms_skipped": self.unsupported_forms_skipped,
            "outside_lookback_skipped": self.outside_lookback_skipped,
            "missing_filing_date_skipped": self.missing_filing_date_skipped,
            "query_start_date": self.query_start_date,
            "query_end_date": self.query_end_date,
            "oldest_filing_date_seen": self.oldest_filing_date_seen,
            "newest_filing_date_seen": self.newest_filing_date_seen,
            "form_counts": self.form_counts,
            "per_form_summary": self.per_form_summary,
            "raw_hits": sum(item.get("raw", 0) for item in self.per_form_summary.values()),
            "parsed_filings": self.filings_fetched,
            "special_situations_created": self.special_situations_created,
            "special_situations_updated": self.special_situations_updated,
            "errors": self.errors,
            "rate_limit_backoff_events": self.rate_limit_backoff_events,
            "dry_run": self.dry_run,
        }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_sec_p1_candidate(filing: Filing) -> dict[str, Any] | None:
    decision = build_routing_decision(filing)
    form_type = decision["detected_form_type"]
    if form_type not in SUPPORTED_P1_FORMS:
        return None
    if form_type == "8-K" and decision["subtype"] != "voluntary_liquidation":
        return None
    if decision["situation_type"] == "unknown":
        return None
    return decision


async def run_sec_edgar_detection(
    db: AsyncSession,
    *,
    hours_back: int = 36,
    dry_run: bool = False,
    adapter: SECEdgarAdapter | None = None,
) -> dict[str, Any]:
    summary = SecDetectionRunSummary(
        started_at=_utc_now_iso(),
        lookback_hours=hours_back,
        dry_run=dry_run,
    )
    adapter = adapter or SECEdgarAdapter()

    try:
        filings, diagnostics = await adapter.search_recent_with_diagnostics(hours_back=hours_back)
    except Exception as exc:
        summary.errors.append(f"SEC EDGAR fetch failed: {exc}")
        summary.completed_at = _utc_now_iso()
        return summary.as_dict()

    summary.filings_fetched = len(filings)
    summary.rate_limit_backoff_events = _extract_backoff_events(diagnostics)
    summary.outside_lookback_skipped = int(diagnostics.get("outside_lookback_skipped", 0))
    summary.missing_filing_date_skipped = int(diagnostics.get("missing_filing_date_skipped", 0))
    summary.query_start_date = diagnostics.get("query_start_date")
    summary.query_end_date = diagnostics.get("query_end_date")
    summary.oldest_filing_date_seen = diagnostics.get("oldest_filing_date_seen")
    summary.newest_filing_date_seen = diagnostics.get("newest_filing_date_seen")
    summary.form_counts = diagnostics.get("form_counts", {})
    summary.per_form_summary = _initial_per_form_summary(diagnostics, filings)

    for filing in filings:
        summary.filings_inspected += 1
        form_key = build_routing_decision(filing)["detected_form_type"]
        form_metrics = summary.per_form_summary.setdefault(form_key, _empty_form_summary())
        form_metrics["parsed"] += 1
        decision = classify_sec_p1_candidate(filing)
        if decision is None:
            summary.unsupported_forms_skipped += 1
            summary.unclassified_filings += 1
            form_metrics["unclassified"] += 1
            continue

        summary.candidates_detected += 1
        form_metrics["classified"] += 1
        existing = await _find_existing_situation(db, filing)
        if existing:
            if not dry_run and _needs_detection_evidence_update(existing):
                existing.evaluation = _build_minimal_evidence(filing, decision)
                existing.updated_at = datetime.now(timezone.utc)
                await db.flush()
                summary.special_situations_updated += 1
            else:
                summary.duplicates_skipped += 1
                form_metrics["duplicates"] += 1
            continue

        if dry_run:
            continue

        sit = SpecialSituation(
            situation_type=decision["situation_type"],
            company_name=filing.company,
            ticker=filing.ticker,
            filing_type=decision["detected_form_type"],
            filing_url=filing.url,
            status="detected",
            evaluation=_build_minimal_evidence(filing, decision),
            source_urls=[filing.url] if filing.url else [],
        )
        db.add(sit)
        await db.flush()
        summary.special_situations_created += 1
        form_metrics["created"] += 1

    summary.completed_at = _utc_now_iso()
    return summary.as_dict()


def _extract_backoff_events(diagnostics: dict[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for form_type, item in diagnostics.get("by_form", {}).items():
        if item.get("rate_limited") or item.get("backoff"):
            events.append({
                "filing_type": form_type,
                "rate_limited": bool(item.get("rate_limited")),
                "status_code": item.get("backoff_status_code"),
                "error": item.get("backoff_error"),
                "backoff_seconds": item.get("backoff_seconds"),
            })
    return events


async def _find_existing_situation(db: AsyncSession, filing: Filing) -> SpecialSituation | None:
    if filing.url:
        result = await db.execute(select(SpecialSituation).where(SpecialSituation.filing_url == filing.url))
        existing = result.scalars().first()
        if existing:
            return existing

    if filing.accession_number:
        result = await db.execute(select(SpecialSituation).where(SpecialSituation.filing_type == filing.filing_type))
        for item in result.scalars().all():
            evidence = item.evaluation if isinstance(item.evaluation, dict) else {}
            sec_detection = evidence.get("sec_detection", {})
            if sec_detection.get("accession_number") == filing.accession_number:
                return item

    result = await db.execute(
        select(SpecialSituation).where(
            SpecialSituation.company_name == filing.company,
            SpecialSituation.filing_type == filing.filing_type,
        )
    )
    existing = result.scalars().first()
    if existing:
        logger.warning(
            "SEC detection fallback dedupe matched by company+form for company=%s filing_type=%s accession=%s",
            filing.company,
            filing.filing_type,
            filing.accession_number,
        )
    return existing


def _needs_detection_evidence_update(situation: SpecialSituation) -> bool:
    evidence = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    return "sec_detection" not in evidence


def _build_minimal_evidence(filing: Filing, decision: dict[str, Any]) -> dict[str, Any]:
    evidence = {
        "detected_only": True,
        "source": "sec_edgar",
        "sec_detection": {
            "accession_number": filing.accession_number,
            "cik": filing.cik,
            "filing_url": filing.url,
            "filing_date": filing.date,
            "detected_form_type": decision["detected_form_type"],
            "detected_signal": decision["detected_signal"],
            "reason_code": decision.get("reason_code"),
            "detection_confidence": decision["detection_confidence"],
            "situation_type": decision["situation_type"],
            "subtype": decision.get("subtype"),
            "selected_playbook": decision.get("selected_playbook"),
            "playbook_status": decision.get("playbook_status"),
        },
        "summary": filing.summary,
        "disclaimer": "Detected from official SEC metadata for human review. This is not investment advice.",
    }
    return attach_methodology_workspace_to_evidence(evidence)


def _empty_form_summary() -> dict[str, int]:
    return {
        "raw": 0,
        "parsed": 0,
        "classified": 0,
        "unclassified": 0,
        "duplicates": 0,
        "created": 0,
        "errors": 0,
    }


def _initial_per_form_summary(diagnostics: dict[str, Any], filings: list[Filing]) -> dict[str, dict[str, int]]:
    per_form: dict[str, dict[str, int]] = {}
    by_form = diagnostics.get("by_form") if isinstance(diagnostics.get("by_form"), dict) else {}
    for form, metrics in by_form.items():
        row = _empty_form_summary()
        if isinstance(metrics, dict):
            row["raw"] = int(metrics.get("raw_hits") or metrics.get("raw") or 0)
            row["errors"] = 1 if metrics.get("error") or metrics.get("backoff_error") else 0
        per_form[str(form)] = row

    form_counts = diagnostics.get("form_counts") if isinstance(diagnostics.get("form_counts"), dict) else {}
    for form, count in form_counts.items():
        row = per_form.setdefault(str(form), _empty_form_summary())
        row["raw"] = max(row["raw"], int(count or 0))

    for filing in filings:
        form_key = build_routing_decision(filing)["detected_form_type"]
        per_form.setdefault(form_key, _empty_form_summary())
    return per_form
