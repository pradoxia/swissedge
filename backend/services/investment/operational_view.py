from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

from backend.models.investment_research import ResearchCase
from backend.services.investment.case_completion import CaseCompletionPackage
from backend.services.investment.evidence_links import ResearchCaseEvidenceLinksPackage
from backend.services.investment.historical_analogues import HistoricalAnaloguesPackage
from backend.services.investment.intelligence_score import IntelligenceScorePackage
from backend.services.investment.research_cases import EvaluationPrepPackage
from backend.services.investment.sec_document_acquisition import SecDocumentAcquisitionPackage


OperationalView = Literal["candidate", "watchlist", "reject", "insufficient_information"]
Confidence = Literal["low", "medium", "high"]


class OperationalViewPackage(BaseModel):
    research_case_id: str
    operational_view: OperationalView
    confidence: Confidence
    rationale: list[str]
    blockers: list[str]
    what_would_change_view: list[str]
    next_manual_actions: list[str]
    guardrails: list[str]
    not_investment_advice: bool = True
    final_decision_by_dani: bool = True


GUARDRAILS = [
    "Operational View is a workflow label for manual review.",
    "It is not investment advice and does not imply a private action.",
    "Candidate / Watchlist / Reject are product workflow labels only.",
    "Dani makes the final manual decision.",
    "No status is changed automatically.",
    "No evidence or checklist item is verified automatically.",
]

WEAK_STATUSES = {"archived", "ignored", "rejected", "discarded", "not_actionable"}
NOISE_WORDS = {"stale", "expired", "unsupported", "noise", "false positive", "noisy"}
WATCHLIST_WORDS = {"catalyst", "event", "timing", "spread", "vote", "regulatory", "approval"}


def _completion_summary(completion: CaseCompletionPackage | None) -> Any:
    return completion.summary if completion else None


def _has_sec_candidate(sec_preview: SecDocumentAcquisitionPackage | None) -> bool:
    if not sec_preview:
        return False
    return bool(sec_preview.known_official_links or sec_preview.likely_document_targets or sec_preview.acquired_documents)


def _brief_text(rc: ResearchCase) -> str:
    brief = rc.brief if isinstance(rc.brief, dict) else {}
    values = [str(value) for value in brief.values() if isinstance(value, str)]
    return " ".join([rc.status or "", rc.investment_readiness or "", rc.notes or "", *values]).lower()


def _critical_missing_official_resources(prep: EvaluationPrepPackage | None, completion: CaseCompletionPackage | None) -> int:
    prep_missing = len(prep.required_resources.missing) if prep else 0
    completion_missing = _completion_summary(completion).missing_required_resources if completion else 0
    return max(prep_missing, completion_missing)


def _checklist_gap_count(prep: EvaluationPrepPackage | None, completion: CaseCompletionPackage | None) -> int:
    prep_missing = len(prep.checklist.missing) if prep else 0
    completion_missing = _completion_summary(completion).checklist_items_needing_evidence if completion else 0
    return max(prep_missing, completion_missing)


def _source_count(rc: ResearchCase, evidence_links: ResearchCaseEvidenceLinksPackage | None) -> int:
    links = len(evidence_links.links) if evidence_links else 0
    return max(links, len(getattr(rc, "documents", []) or []) + len(getattr(rc, "sources", []) or []))


def _risk_clean(score: IntelligenceScorePackage | None, completion: CaseCompletionPackage | None) -> bool:
    if score and score.warnings:
        return False
    if completion and any(item.severity == "high" for item in completion.blocking_items):
        return False
    return True


def _confidence(view: OperationalView, score: IntelligenceScorePackage | None, completion: CaseCompletionPackage | None) -> Confidence:
    if view == "insufficient_information":
        return "low"
    score_value = score.total_score if score else 0
    completion_score = completion.completion_score if completion else 0
    if score_value >= 85 and completion_score >= 80:
        return "high"
    if score_value >= 60 or completion_score >= 60:
        return "medium"
    return "low"


def build_operational_view_package(
    rc: ResearchCase,
    *,
    evaluation_prep: EvaluationPrepPackage | None = None,
    intelligence_score: IntelligenceScorePackage | None = None,
    completion_workbench: CaseCompletionPackage | None = None,
    evidence_links: ResearchCaseEvidenceLinksPackage | None = None,
    historical_analogues: HistoricalAnaloguesPackage | None = None,
    sec_preview: SecDocumentAcquisitionPackage | None = None,
) -> OperationalViewPackage:
    rationale: list[str] = []
    blockers: list[str] = []
    what_would_change_view: list[str] = []
    next_manual_actions: list[str] = []
    brief_text = _brief_text(rc)
    source_count = _source_count(rc, evidence_links)
    missing_resources = _critical_missing_official_resources(evaluation_prep, completion_workbench)
    checklist_gaps = _checklist_gap_count(evaluation_prep, completion_workbench)
    completion_score = completion_workbench.completion_score if completion_workbench else 0
    score_value = intelligence_score.total_score if intelligence_score else 0
    analogue_count = 0
    if historical_analogues:
        analogue_count = len(historical_analogues.historical_case_matches) + len(historical_analogues.matched_patterns)
    status = (rc.status or "").lower()
    readiness = (rc.investment_readiness or "").lower()

    if missing_resources:
        blockers.append(f"{missing_resources} required resource item(s) still need official evidence.")
        what_would_change_view.append("Resolve missing official resources and rerun manual review.")
    if checklist_gaps:
        blockers.append(f"{checklist_gaps} checklist item(s) still need evidence.")
        what_would_change_view.append("Map evidence to checklist gaps without auto-verification.")
    if completion_workbench:
        next_manual_actions.extend(action.label for action in completion_workbench.next_manual_actions[:4])
    if evaluation_prep:
        next_manual_actions.extend(action.label for action in evaluation_prep.suggested_next_actions[:4])

    if status in WEAK_STATUSES or readiness in WEAK_STATUSES or any(word in brief_text for word in NOISE_WORDS):
        view: OperationalView = "reject"
        rationale.append("Stored metadata indicates weak support, stale/noisy context, or an archived/not-actionable workflow state.")
        what_would_change_view.append("Add fresh official evidence and clear the unsupported/noisy status before reconsidering the workflow label.")
    elif source_count == 0 and not _has_sec_candidate(sec_preview) and not rc.situation_id:
        view = "insufficient_information"
        rationale.append("There is not enough stored source, document, SEC, or linked-situation metadata to choose a workflow label safely.")
        blockers.append("Add official source metadata, documents, or linked SpecialSituation context.")
        what_would_change_view.append("Attach official source metadata and run manual documentation review.")
    elif missing_resources or checklist_gaps:
        if any(word in brief_text for word in WATCHLIST_WORDS) or readiness == "monitor":
            view = "watchlist"
            rationale.append("The case has an interesting workflow signal but still lacks event, timing, approval, catalyst, or documentation clarity.")
        else:
            view = "insufficient_information"
            rationale.append("Documentation gaps are too large to choose Candidate / Watchlist / Reject safely.")
    elif (
        source_count >= 2
        and completion_score >= 70
        and score_value >= 70
        and _risk_clean(intelligence_score, completion_workbench)
        and (analogue_count > 0 or _has_sec_candidate(sec_preview))
    ):
        view = "candidate"
        rationale.append("Stored metadata shows adequate documentation, source coverage, completion score, and clean risk-discipline checks for manual review.")
        what_would_change_view.append("If new blockers, stale event data, or unresolved evidence gaps appear, downgrade the workflow label.")
    else:
        view = "watchlist"
        rationale.append("The case has enough structure to monitor, but needs more clarity before Candidate workflow review.")
        what_would_change_view.append("Improve completion score, source coverage, historical analogue context, or event clarity.")

    if not next_manual_actions:
        next_manual_actions.append("Review source/document metadata and evidence mapping manually.")

    return OperationalViewPackage(
        research_case_id=str(rc.id),
        operational_view=view,
        confidence=_confidence(view, intelligence_score, completion_workbench),
        rationale=rationale,
        blockers=blockers,
        what_would_change_view=what_would_change_view,
        next_manual_actions=list(dict.fromkeys(next_manual_actions))[:6],
        guardrails=GUARDRAILS,
    )
