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
from backend.services.investment.sec_company_facts import build_competition_lens, fetch_public_float
from backend.services.investment.sources.base import Filing
from backend.services.investment.sources.sec_edgar import SECEdgarAdapter


logger = logging.getLogger(__name__)

STRICT_CREATION_ALLOWLIST = {"SC TO-T", "SC TO-T/A", "SC TO-I", "SC TO-I/A", "Form 10"}
CLASSIFICATION_REPORT_FORMS = {
    *STRICT_CREATION_ALLOWLIST,
    "8-K",
    "SC 14D9",
    "SC 14D9/A",
    "DEFM14A",
    "PREM14A",
    "DFAN14A",
    "S-4",
    "S-4/A",
}
CORE_CLASSIFICATION_FORMS = {*STRICT_CREATION_ALLOWLIST, "8-K"}

# Forms added by the detection quick-wins sprint: classified filings on these
# forms (plus the existing report forms) are persisted as candidate-only
# SpecialSituations instead of report-only summary rows.
CLASSIFICATION_REPORT_FORMS.update({"13E-3", "Form 25"})

# Ignored reasons that still allow candidate-only persistence (human review queue).
_CANDIDATE_PERSIST_REASONS = {
    "outside_strict_creation_allowlist",
    "classification_confidence_not_high",
}
_CANDIDATE_PERSIST_CONFIDENCES = {"high", "medium"}

# Best-effort SEC public-float enrichment budget per detection run.
_MAX_FLOAT_LOOKUPS_PER_RUN = 10


@dataclass
class SecDetectionRunSummary:
    started_at: str
    completed_at: str | None = None
    lookback_hours: int = 36
    filings_fetched: int = 0
    filings_inspected: int = 0
    candidates_detected: int = 0
    candidate_only_count: int = 0
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
    classification_reports: list[dict[str, Any]] = field(default_factory=list)
    per_situation_type_counts: dict[str, int] = field(default_factory=dict)
    ignored_reasons: dict[str, int] = field(default_factory=dict)
    special_situations_created: int = 0
    special_situations_updated: int = 0
    candidate_only_created: int = 0
    created_situations: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
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
            "candidate_only_count": self.candidate_only_count,
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
            "classification_reports": self.classification_reports,
            "per_situation_type_counts": self.per_situation_type_counts,
            "ignored_reasons": self.ignored_reasons,
            "raw_hits": sum(item.get("raw", 0) for item in self.per_form_summary.values()),
            "parsed_filings": self.filings_fetched,
            "forms_checked": sorted(self.per_form_summary.keys()),
            "forms_checked_count": len(self.per_form_summary),
            "raw_hits_count": sum(item.get("raw", 0) for item in self.per_form_summary.values()),
            "parsed_count": self.filings_fetched,
            "classified_count": self.candidates_detected + self.candidate_only_count,
            "ignored_count": self.unclassified_filings + self.candidate_only_count + self.duplicates_skipped,
            "duplicates_count": self.duplicates_skipped,
            "created_count": self.special_situations_created,
            "errors_count": len(self.errors),
            "ignored_reasons_summary": self.ignored_reasons,
            "special_situations_created": self.special_situations_created,
            "special_situations_updated": self.special_situations_updated,
            "candidate_only_created": self.candidate_only_created,
            "created_situations": self.created_situations,
            "warnings": self.warnings,
            "errors": self.errors,
            "rate_limit_backoff_events": self.rate_limit_backoff_events,
            "dry_run": self.dry_run,
        }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_sec_p1_candidate(filing: Filing) -> dict[str, Any] | None:
    decision = build_routing_decision(filing)
    form_type = decision["detected_form_type"]
    if form_type not in CORE_CLASSIFICATION_FORMS:
        return None
    if form_type == "8-K" and decision["subtype"] != "voluntary_liquidation":
        return None
    if decision["situation_type"] == "unknown":
        return None
    return decision


def build_sec_classification_report(
    filing: Filing,
    *,
    duplicate_detected: bool = False,
) -> dict[str, Any]:
    decision = build_routing_decision(filing)
    form_type = decision["detected_form_type"]
    confidence = str(decision.get("detection_confidence") or "LOW").lower()
    detected_situation_type = decision.get("situation_type") or "unknown"
    required_missing = _required_identifiers_missing(filing)
    human_review_required = False
    ignored_reason = None

    if form_type not in CLASSIFICATION_REPORT_FORMS:
        ignored_reason = "unsupported_form"
        human_review_required = True
    elif detected_situation_type == "unknown":
        ignored_reason = decision.get("reason_code") or "unknown_situation_type"
        human_review_required = True
    elif confidence != "high":
        ignored_reason = "classification_confidence_not_high"
        human_review_required = True
    elif form_type not in STRICT_CREATION_ALLOWLIST:
        ignored_reason = "outside_strict_creation_allowlist"
        human_review_required = True
    elif required_missing:
        ignored_reason = "required_identifiers_missing"
        human_review_required = True
    elif duplicate_detected:
        ignored_reason = "duplicate_detected"
        human_review_required = True

    creation_eligible = (
        form_type in STRICT_CREATION_ALLOWLIST
        and confidence == "high"
        and detected_situation_type != "unknown"
        and not required_missing
        and not duplicate_detected
    )

    return {
        "form_type": form_type,
        "company_name": filing.company,
        "ticker": filing.ticker,
        "cik": filing.cik,
        "accession_number": filing.accession_number,
        "filing_date": filing.date,
        "filing_url": filing.url,
        "detected_situation_type": detected_situation_type,
        "detected_subtype": decision.get("subtype"),
        "classification_reason": decision.get("detected_signal") or decision.get("reason_code") or "",
        "classification_confidence": confidence,
        "creation_eligible": creation_eligible,
        "human_review_required": human_review_required,
        "duplicate_detected": duplicate_detected,
        "ignored_reason": ignored_reason,
        "required_identifiers_missing": required_missing,
    }


def _required_identifiers_missing(filing: Filing) -> list[str]:
    missing: list[str] = []
    if not filing.url:
        missing.append("filing_url")
    if not (filing.cik or filing.accession_number):
        missing.append("cik_or_accession_number")
    return missing


async def run_sec_edgar_detection(
    db: AsyncSession,
    *,
    hours_back: int = 36,
    dry_run: bool = True,
    adapter: SECEdgarAdapter | None = None,
    trigger_type: str | None = None,
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
    seen_dedupe_keys: set[str] = set()
    float_budget = {"remaining": _MAX_FLOAT_LOOKUPS_PER_RUN}

    # Silent-breakage warning: a fully empty scan across all forms usually means
    # a query/auth/parser problem rather than a quiet market.
    if int(diagnostics.get("raw_hits_total", 0)) == 0 and not summary.rate_limit_backoff_events:
        summary.warnings.append(
            "SEC EDGAR returned 0 raw hits across all forms and sweeps in this run; "
            "verify query parameters, User-Agent, and EFTS availability."
        )

    for filing in filings:
        summary.filings_inspected += 1
        form_key = build_routing_decision(filing)["detected_form_type"]
        form_metrics = summary.per_form_summary.setdefault(form_key, _empty_form_summary())
        form_metrics["parsed"] += 1

        initial_report = build_sec_classification_report(filing)
        decision = build_routing_decision(filing)
        if initial_report["detected_situation_type"] != "unknown":
            situation_key = initial_report["detected_situation_type"]
            summary.per_situation_type_counts[situation_key] = summary.per_situation_type_counts.get(situation_key, 0) + 1

        if initial_report["ignored_reason"] and initial_report["ignored_reason"] != "duplicate_detected":
            _increment_ignored_reason(summary, initial_report["ignored_reason"])

        if form_key not in CLASSIFICATION_REPORT_FORMS or initial_report["detected_situation_type"] == "unknown":
            summary.unsupported_forms_skipped += 1
            summary.unclassified_filings += 1
            form_metrics["unclassified"] += 1
            summary.classification_reports.append(initial_report)
            continue

        if not initial_report["creation_eligible"]:
            summary.candidate_only_count += 1
            form_metrics["candidate_only"] += 1
            summary.classification_reports.append(initial_report)
            # Quick-wins sprint: classified medium/high-confidence filings on
            # supported forms become candidate-only SpecialSituations so they
            # surface in the triage queue instead of dying in run summaries.
            persistable = (
                initial_report["ignored_reason"] in _CANDIDATE_PERSIST_REASONS
                and initial_report["detected_situation_type"] != "unknown"
                and not initial_report["required_identifiers_missing"]
                and str(initial_report["classification_confidence"]).lower() in _CANDIDATE_PERSIST_CONFIDENCES
            )
            if persistable and not dry_run:
                batch_duplicate = _is_batch_duplicate(filing, seen_dedupe_keys)
                existing = await _find_existing_situation(db, filing)
                if not existing and not batch_duplicate:
                    evidence = _build_minimal_evidence(
                        filing, decision, initial_report, trigger_type=trigger_type, candidate_only=True
                    )
                    evidence = await _maybe_enrich_market_context(evidence, filing, float_budget)
                    candidate_sit = SpecialSituation(
                        situation_type=decision["situation_type"],
                        company_name=filing.company,
                        ticker=filing.ticker,
                        filing_type=decision["detected_form_type"],
                        filing_url=filing.url,
                        status="detected",
                        evaluation=evidence,
                        source_urls=[filing.url] if filing.url else [],
                    )
                    db.add(candidate_sit)
                    await db.flush()
                    summary.candidate_only_created += 1
                    form_metrics["created"] += 1
                    summary.created_situations.append({
                        "id": str(candidate_sit.id),
                        "company_name": candidate_sit.company_name,
                        "ticker": candidate_sit.ticker,
                        "situation_type": candidate_sit.situation_type,
                        "filing_type": candidate_sit.filing_type,
                        "filing_url": candidate_sit.filing_url,
                        "status": candidate_sit.status,
                        "source": "sec_edgar",
                        "trigger_type": trigger_type or "manual",
                        "accession_number": filing.accession_number,
                        "cik": filing.cik,
                        "candidate_only": True,
                        "creation_reason": initial_report["ignored_reason"],
                    })
            continue

        summary.candidates_detected += 1
        form_metrics["classified"] += 1
        batch_duplicate = _is_batch_duplicate(filing, seen_dedupe_keys)
        existing = None if dry_run else await _find_existing_situation(db, filing)
        report = build_sec_classification_report(filing, duplicate_detected=bool(existing) or batch_duplicate)
        if report["ignored_reason"]:
            _increment_ignored_reason(summary, report["ignored_reason"])
        summary.classification_reports.append(report)
        if existing or batch_duplicate:
            if not dry_run and _needs_detection_evidence_update(existing):
                existing.evaluation = _build_minimal_evidence(filing, decision, report, trigger_type=trigger_type)
                existing.updated_at = datetime.now(timezone.utc)
                await db.flush()
                summary.special_situations_updated += 1
            else:
                summary.duplicates_skipped += 1
                form_metrics["duplicates"] += 1
            continue

        if dry_run or not report["creation_eligible"]:
            continue

        strict_evidence = _build_minimal_evidence(filing, decision, report, trigger_type=trigger_type)
        strict_evidence = await _maybe_enrich_market_context(strict_evidence, filing, float_budget)
        sit = SpecialSituation(
            situation_type=decision["situation_type"],
            company_name=filing.company,
            ticker=filing.ticker,
            filing_type=decision["detected_form_type"],
            filing_url=filing.url,
            status="detected",
            evaluation=strict_evidence,
            source_urls=[filing.url] if filing.url else [],
        )
        db.add(sit)
        await db.flush()
        summary.special_situations_created += 1
        summary.created_situations.append({
            "id": str(sit.id),
            "company_name": sit.company_name,
            "ticker": sit.ticker,
            "situation_type": sit.situation_type,
            "filing_type": sit.filing_type,
            "filing_url": sit.filing_url,
            "status": sit.status,
            "source": "sec_edgar",
            "trigger_type": trigger_type or "manual",
            "accession_number": filing.accession_number,
            "cik": filing.cik,
        })
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


def _normalize_form(form: str | None) -> str:
    """Normalize amendment suffixes so SC TO-T/A dedupes against SC TO-T."""
    if not form:
        return ""
    return form.strip().upper().removesuffix("/A").strip()


def _is_batch_duplicate(filing: Filing, seen: set[str]) -> bool:
    keys = [
        f"url:{filing.url}" if filing.url else "",
        f"accession:{filing.accession_number}" if filing.accession_number else "",
        f"company-form:{filing.company}:{_normalize_form(filing.filing_type)}"
        if filing.company and filing.filing_type
        else "",
    ]
    keys = [key for key in keys if key]
    duplicate = any(key in seen for key in keys)
    seen.update(keys)
    return duplicate


async def _maybe_enrich_market_context(
    evidence: dict[str, Any],
    filing: Filing,
    float_budget: dict[str, int],
) -> dict[str, Any]:
    """Best-effort SEC public-float enrichment, bounded per run.

    Never raises; unknown stays unknown. Adds `market_context` with public float
    and an explainable competition-lens flag (prioritization only, not advice).
    """
    if float_budget.get("remaining", 0) <= 0:
        evidence["market_context"] = {
            "status": "skipped",
            "reason": "per-run SEC company-facts lookup budget exhausted",
        }
        return evidence
    float_budget["remaining"] -= 1
    try:
        public_float = await fetch_public_float(filing.cik)
    except Exception:  # defensive: enrichment must never break detection
        public_float = None
    evidence["market_context"] = {
        "public_float": public_float,
        "competition_lens": build_competition_lens(public_float),
        "status": "derived" if public_float else "unavailable",
    }
    return evidence


def _increment_ignored_reason(summary: SecDetectionRunSummary, reason: str | None) -> None:
    if not reason:
        return
    summary.ignored_reasons[reason] = summary.ignored_reasons.get(reason, 0) + 1


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

    normalized_form = _normalize_form(filing.filing_type)
    form_variants = {filing.filing_type, normalized_form, f"{normalized_form}/A"}
    result = await db.execute(
        select(SpecialSituation).where(
            SpecialSituation.company_name == filing.company,
            SpecialSituation.filing_type.in_(sorted(v for v in form_variants if v)),
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


def _build_minimal_evidence(
    filing: Filing,
    decision: dict[str, Any],
    classification_report: dict[str, Any] | None = None,
    *,
    trigger_type: str | None = None,
    candidate_only: bool = False,
) -> dict[str, Any]:
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
        "classification_report": classification_report or build_sec_classification_report(filing),
        "creation_context": {
            "created_by": "sec_edgar_scan",
            "source": "sec_edgar",
            "trigger_type": trigger_type or "manual",
            "evidence_status": "metadata-only",
            "requires_human_review": True,
            "candidate_only": candidate_only,
            "creation_reason": (
                (classification_report or {}).get("ignored_reason") if candidate_only else "strict_allowlist"
            ),
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
        "candidate_only": 0,
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
