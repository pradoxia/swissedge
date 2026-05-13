from __future__ import annotations

from copy import deepcopy
from typing import Any, Literal

from pydantic import BaseModel

from backend.models.investment import SpecialSituation
from backend.models.investment_research import HistoricalCase, ResearchCase
from backend.services.investment.methodology_workspace import WORKSPACE_KEY


CaseType = Literal["special_situation", "research_case"]
Confidence = Literal["high", "medium", "low"]


class HistoricalAnalogueCaseSummary(BaseModel):
    company_name: str | None = None
    ticker: str | None = None
    filing_type: str | None = None
    situation_type: str | None = None
    selected_playbook: str | None = None
    methodology_status: str = "unknown"


class MatchedPattern(BaseModel):
    pattern_id: str
    title: str
    source: str = "sanitized_playbook"
    similarity_reason: str
    applies_because: list[str]
    manual_checks: list[str]
    risk_notes: list[str]
    confidence: Confidence
    not_evaluation: bool = True


class HistoricalCaseMatch(BaseModel):
    historical_case_id: str
    title: str
    situation_type: str | None = None
    similarity_score: int
    similarity_reasons: list[str]
    key_differences: list[str]
    manual_comparison_steps: list[str]
    source: str = "historical_case_workspace"
    not_evaluation: bool = True


class CourseMethodologyLink(BaseModel):
    label: str
    playbook: str
    section: str
    safe_summary: str
    human_review_required: bool = True


class AnalogueComparisonChecklistItem(BaseModel):
    label: str
    status: str
    why_it_matters: str
    related_required_resource_ids: list[str] = []
    related_check_ids: list[str] = []


class HistoricalAnaloguesPackage(BaseModel):
    case_id: str
    case_type: CaseType
    case_summary: HistoricalAnalogueCaseSummary
    matched_patterns: list[MatchedPattern]
    historical_case_matches: list[HistoricalCaseMatch]
    course_methodology_links: list[CourseMethodologyLink]
    comparison_checklist: list[AnalogueComparisonChecklistItem]
    warnings: list[str]
    guardrails: list[str]


WARNINGS = [
    "Historical similarity does not mean the same outcome.",
    "Course pattern mapping is not an investment evaluation.",
    "Manual review remains required before relying on any analogy.",
]

GUARDRAILS = [
    "This package uses stored metadata and processed methodology labels only.",
    "No raw course source files or long course excerpts are included.",
    "No live AI, evaluator, scanner, web search, crawl, SEC fetch, or PDF download was used.",
    "This is a methodology/context aid for manual research.",
]

MISSING_STATUSES = {"missing", "needs_evidence", "not_started", "open"}


def _clean_dict(value: Any) -> dict:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_list(value: Any) -> list[dict]:
    return [deepcopy(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _norm(value: Any) -> str:
    return (_text(value) or "").lower().replace("-", "_").replace(" ", "_")


def _title(item: dict, fallback: str) -> str:
    return _text(item.get("title") or item.get("label") or item.get("name") or item.get("resource_id") or item.get("check_id")) or fallback


def _status(item: dict) -> str:
    return str(item.get("status") or "missing")


def _resource_id(item: dict) -> str | None:
    return _text(item.get("resource_id") or item.get("id"))


def _check_id(item: dict) -> str | None:
    return _text(item.get("check_id") or item.get("id"))


def _workspace_from_situation(situation: SpecialSituation) -> dict:
    evaluation = _clean_dict(situation.evaluation)
    return _clean_dict(evaluation.get(WORKSPACE_KEY))


def _sec_detection_from_situation(situation: SpecialSituation) -> dict:
    evaluation = _clean_dict(situation.evaluation)
    return _clean_dict(evaluation.get("sec_detection"))


def _brief_from_case(rc: ResearchCase) -> dict:
    return _clean_dict(rc.brief)


def _workspace_from_case(rc: ResearchCase) -> dict:
    return _clean_dict(_brief_from_case(rc).get("methodology_workspace_snapshot"))


def _detection_from_case(rc: ResearchCase, source_situation: SpecialSituation | None) -> dict:
    brief = _brief_from_case(rc)
    detection = _clean_dict(brief.get("detection_summary"))
    if detection:
        return detection
    if source_situation is None:
        return {}
    sec = _sec_detection_from_situation(source_situation)
    return {
        "company_name": source_situation.company_name,
        "ticker": source_situation.ticker,
        "filing_type": sec.get("detected_form_type") or source_situation.filing_type,
        "situation_type": sec.get("situation_type") or source_situation.situation_type,
        "selected_playbook": sec.get("selected_playbook"),
    }


def _required_resources(workspace: dict) -> list[dict]:
    return _clean_list(workspace.get("required_resources"))


def _checklist(workspace: dict) -> list[dict]:
    return _clean_list(workspace.get("checklist"))


def _resource_tokens(workspace: dict) -> set[str]:
    values: set[str] = set()
    for item in _required_resources(workspace):
        for key in ("resource_id", "source_type", "title", "label"):
            value = _norm(item.get(key))
            if value:
                values.add(value)
    return values


def _checklist_tokens(workspace: dict) -> set[str]:
    values: set[str] = set()
    for item in _checklist(workspace):
        for key in ("check_id", "section", "title", "label"):
            value = _norm(item.get(key))
            if value:
                values.add(value)
    return values


def _playbook_from_workspace(workspace: dict) -> str | None:
    return _text(
        workspace.get("selected_playbook")
        or workspace.get("playbook")
        or workspace.get("template_key")
        or workspace.get("playbook_used")
    )


def _methodology_status_from_workspace(workspace: dict, fallback: str | None = None) -> str:
    return _text(workspace.get("methodology_status") or workspace.get("playbook_status") or fallback) or "unknown"


def _summary_for_situation(situation: SpecialSituation) -> HistoricalAnalogueCaseSummary:
    workspace = _workspace_from_situation(situation)
    sec = _sec_detection_from_situation(situation)
    return HistoricalAnalogueCaseSummary(
        company_name=situation.company_name,
        ticker=situation.ticker,
        filing_type=_text(sec.get("detected_form_type") or situation.filing_type),
        situation_type=_text(sec.get("situation_type") or situation.situation_type),
        selected_playbook=_text(sec.get("selected_playbook") or _playbook_from_workspace(workspace)),
        methodology_status=_methodology_status_from_workspace(workspace, _text(sec.get("playbook_status"))),
    )


def _summary_for_case(rc: ResearchCase, source_situation: SpecialSituation | None) -> HistoricalAnalogueCaseSummary:
    workspace = _workspace_from_case(rc)
    detection = _detection_from_case(rc, source_situation)
    return HistoricalAnalogueCaseSummary(
        company_name=_text(detection.get("company_name")) or _brief_title(rc),
        ticker=_text(detection.get("ticker")),
        filing_type=_text(detection.get("filing_type") or detection.get("detected_form_type")),
        situation_type=_text(detection.get("situation_type")) or rc.playbook_used,
        selected_playbook=_text(detection.get("selected_playbook") or _playbook_from_workspace(workspace) or rc.playbook_used),
        methodology_status=_methodology_status_from_workspace(workspace, rc.methodology_status),
    )


def _brief_title(rc: ResearchCase) -> str | None:
    brief = _brief_from_case(rc)
    for key in ("title", "company_name", "case_title"):
        value = _text(brief.get(key))
        if value:
            return value
    return None


def _pattern_rule(summary: HistoricalAnalogueCaseSummary) -> tuple[str, str, list[str], list[str], list[str], str]:
    filing = _norm(summary.filing_type)
    situation = _norm(summary.situation_type)
    if "sc_to_i" in filing:
        return (
            "self_tender_sc_to_i",
            "Issuer self-tender / SC TO-I pattern",
            ["Filing type is SC TO-I", "Situation type can map to tender_offer", "Required resources should include offer terms"],
            ["Confirm offer price or range", "Confirm expiration date", "Confirm proration terms", "Confirm source of funds"],
            ["Partial playbook: human review required", "Evidence_found is not automatically verified"],
            "high",
        )
    if "sc_to_t" in filing:
        return (
            "acquisition_tender_sc_to_t",
            "Acquisition tender / merger-arbitrage tender pattern",
            ["Filing type is SC TO-T", "Tender mechanics likely drive the workflow", "Offer and transaction documents must be mapped"],
            ["Confirm bidder and target", "Confirm offer terms", "Confirm conditions", "Compare timing and withdrawal rights"],
            ["Do not infer outcome from form type alone", "Manual review required"],
            "high",
        )
    if "form_10" in filing or "spin" in situation:
        return (
            "spin_off_form_10",
            "Spin-off / separation pattern",
            ["Filing type or situation type points to a separation", "Form 10 style disclosure usually anchors the case"],
            ["Confirm parent and spun entity", "Compare capital structure", "Review distribution mechanics", "Check pro forma financials"],
            ["Separation details can change before effectiveness", "Manual review required"],
            "high" if "form_10" in filing else "medium",
        )
    if "8_k" in filing and ("liquidation" in situation or "dissolution" in situation):
        return (
            "liquidation_dissolution_8k",
            "Liquidation / dissolution pattern",
            ["8-K metadata points to liquidation or dissolution", "Distribution and timing evidence must be confirmed"],
            ["Confirm board/shareholder approvals", "Check expected distributions", "Review liabilities and timing", "Confirm remaining assets"],
            ["Historical outcomes vary widely", "Manual review required"],
            "high",
        )
    return (
        "general_special_situation",
        "General special situation detection pattern",
        ["Stored metadata indicates a special situation but no precise playbook rule matched"],
        ["Confirm official source", "Confirm situation type", "Map required resources", "Compare checklist gaps"],
        ["Pattern confidence is limited until filing and playbook are confirmed"],
        "low",
    )


def _matched_patterns(summary: HistoricalAnalogueCaseSummary, workspace: dict) -> list[MatchedPattern]:
    pattern_id, title, reasons, manual_checks, risk_notes, confidence = _pattern_rule(summary)
    if _required_resources(workspace):
        reasons.append("Required resources are already mapped in the methodology workspace")
    if _checklist(workspace):
        reasons.append("Checklist concepts are available for manual comparison")
    return [
        MatchedPattern(
            pattern_id=pattern_id,
            title=title,
            similarity_reason=f"{summary.filing_type or 'Unknown filing'} / {summary.situation_type or 'unknown situation'} maps to this processed playbook pattern.",
            applies_because=reasons,
            manual_checks=manual_checks,
            risk_notes=risk_notes,
            confidence=confidence,  # type: ignore[arg-type]
        )
    ]


def _course_links(patterns: list[MatchedPattern]) -> list[CourseMethodologyLink]:
    links: list[CourseMethodologyLink] = []
    for pattern in patterns:
        if pattern.pattern_id == "self_tender_sc_to_i":
            links.append(CourseMethodologyLink(
                label="Tender offer playbook",
                playbook="tender_offer.md",
                section="Offer Terms",
                safe_summary="Compare offer documents, expiration, proration, source of funds, and required official evidence.",
            ))
        elif pattern.pattern_id == "acquisition_tender_sc_to_t":
            links.append(CourseMethodologyLink(
                label="Merger-arbitrage tender pattern",
                playbook="tender_offer.md",
                section="Tender Conditions",
                safe_summary="Compare bidder/target context, offer conditions, transaction documents, timing, and withdrawal mechanics.",
            ))
        elif pattern.pattern_id == "spin_off_form_10":
            links.append(CourseMethodologyLink(
                label="Spin-off playbook",
                playbook="spin_off.md",
                section="Separation Mechanics",
                safe_summary="Compare parent/spin entity, distribution terms, capital structure, pro forma financials, and filing status.",
            ))
        elif pattern.pattern_id == "liquidation_dissolution_8k":
            links.append(CourseMethodologyLink(
                label="Liquidation pattern",
                playbook="liquidation.md",
                section="Distribution Evidence",
                safe_summary="Compare approvals, asset/liability evidence, expected distributions, and timing disclosures.",
            ))
        else:
            links.append(CourseMethodologyLink(
                label="General special situation checklist",
                playbook="global_checklist.md",
                section="Source Traceability",
                safe_summary="Confirm official source, situation type, required resources, checklist coverage, and manual review flags.",
            ))
    return links


def _comparison_checklist(workspace: dict) -> list[AnalogueComparisonChecklistItem]:
    rows: list[AnalogueComparisonChecklistItem] = []
    for resource in _required_resources(workspace):
        status = _status(resource)
        if status in MISSING_STATUSES or status == "candidate_found":
            rows.append(AnalogueComparisonChecklistItem(
                label=f"Compare required resource: {_title(resource, 'Untitled resource')}",
                status=status,
                why_it_matters="Analogies are weak until the same kind of source evidence is available for this case.",
                related_required_resource_ids=[_resource_id(resource)] if _resource_id(resource) else [],
            ))
    for item in _checklist(workspace):
        status = _status(item)
        if status in MISSING_STATUSES or status == "candidate_found":
            rows.append(AnalogueComparisonChecklistItem(
                label=f"Compare checklist concept: {_title(item, 'Untitled checklist item')}",
                status=status,
                why_it_matters="Checklist gaps show what must be manually compared before relying on the analogy.",
                related_check_ids=[_check_id(item)] if _check_id(item) else [],
            ))
    if not rows:
        rows.append(AnalogueComparisonChecklistItem(
            label="Confirm source traceability before using analogues",
            status="manual_review_required",
            why_it_matters="Every analogy should be supported by official source links and mapped evidence.",
        ))
    return rows[:12]


def _historical_reconstruction_workspace(hc: HistoricalCase) -> dict:
    reconstruction = _clean_dict(hc.reconstruction)
    return _clean_dict(reconstruction.get("methodology_workspace") or reconstruction.get("methodology_workspace_snapshot"))


def _historical_playbook(hc: HistoricalCase) -> str | None:
    reconstruction = _clean_dict(hc.reconstruction)
    return _text(reconstruction.get("playbook_used") or reconstruction.get("selected_playbook") or _playbook_from_workspace(_historical_reconstruction_workspace(hc)))


def _historical_filing_type(hc: HistoricalCase) -> str | None:
    reconstruction = _clean_dict(hc.reconstruction)
    return _text(reconstruction.get("filing_type") or reconstruction.get("detected_form_type"))


def _historical_methodology_status(hc: HistoricalCase) -> str | None:
    reconstruction = _clean_dict(hc.reconstruction)
    return _text(reconstruction.get("methodology_status") or reconstruction.get("playbook_status") or hc.status)


def _score_historical_case(
    summary: HistoricalAnalogueCaseSummary,
    workspace: dict,
    hc: HistoricalCase,
) -> tuple[int, list[str], list[str]]:
    score = 0
    reasons: list[str] = []
    differences: list[str] = []
    if _norm(hc.situation_type) == _norm(summary.situation_type):
        score += 35
        reasons.append("Same situation type")
    else:
        differences.append("Different situation type")

    filing = _historical_filing_type(hc)
    if filing and _norm(filing) == _norm(summary.filing_type):
        score += 20
        reasons.append("Same filing type")
    elif filing or summary.filing_type:
        differences.append("Filing type differs or is missing")

    playbook = _historical_playbook(hc)
    if playbook and _norm(playbook) == _norm(summary.selected_playbook):
        score += 20
        reasons.append("Same playbook label")
    elif playbook or summary.selected_playbook:
        differences.append("Playbook label differs or is missing")

    hc_workspace = _historical_reconstruction_workspace(hc)
    if _resource_tokens(workspace) & _resource_tokens(hc_workspace):
        score += 10
        reasons.append("Overlapping required resource concepts")
    if _checklist_tokens(workspace) & _checklist_tokens(hc_workspace):
        score += 10
        reasons.append("Overlapping checklist concepts")

    status = _historical_methodology_status(hc)
    if status and _norm(status) == _norm(summary.methodology_status):
        score += 5
        reasons.append("Similar methodology status")

    if not reasons:
        reasons.append("Loaded as a historical workspace for manual comparison")
    if not differences:
        differences.append("Differences must still be confirmed manually")
    return min(score, 100), reasons, differences


def _historical_matches(
    summary: HistoricalAnalogueCaseSummary,
    workspace: dict,
    historical_cases: list[HistoricalCase],
) -> list[HistoricalCaseMatch]:
    rows: list[HistoricalCaseMatch] = []
    for hc in historical_cases:
        score, reasons, differences = _score_historical_case(summary, workspace, hc)
        if score <= 0:
            continue
        rows.append(HistoricalCaseMatch(
            historical_case_id=str(hc.id),
            title=hc.company_name,
            situation_type=hc.situation_type,
            similarity_score=score,
            similarity_reasons=reasons,
            key_differences=differences,
            manual_comparison_steps=[
                "Compare official filing/source trail.",
                "Compare required resource coverage.",
                "Compare checklist gaps and manual review flags.",
                "Document why the analogy applies and where it breaks.",
            ],
        ))
    return sorted(rows, key=lambda row: row.similarity_score, reverse=True)[:8]


def build_situation_historical_analogues(
    situation: SpecialSituation,
    historical_cases: list[HistoricalCase] | None = None,
) -> HistoricalAnaloguesPackage:
    workspace = _workspace_from_situation(situation)
    summary = _summary_for_situation(situation)
    patterns = _matched_patterns(summary, workspace)
    return HistoricalAnaloguesPackage(
        case_id=str(situation.id),
        case_type="special_situation",
        case_summary=summary,
        matched_patterns=patterns,
        historical_case_matches=_historical_matches(summary, workspace, historical_cases or []),
        course_methodology_links=_course_links(patterns),
        comparison_checklist=_comparison_checklist(workspace),
        warnings=WARNINGS,
        guardrails=GUARDRAILS,
    )


def build_research_case_historical_analogues(
    rc: ResearchCase,
    historical_cases: list[HistoricalCase] | None = None,
    source_situation: SpecialSituation | None = None,
) -> HistoricalAnaloguesPackage:
    workspace = _workspace_from_case(rc)
    summary = _summary_for_case(rc, source_situation)
    patterns = _matched_patterns(summary, workspace)
    return HistoricalAnaloguesPackage(
        case_id=str(rc.id),
        case_type="research_case",
        case_summary=summary,
        matched_patterns=patterns,
        historical_case_matches=_historical_matches(summary, workspace, historical_cases or []),
        course_methodology_links=_course_links(patterns),
        comparison_checklist=_comparison_checklist(workspace),
        warnings=WARNINGS,
        guardrails=GUARDRAILS,
    )
