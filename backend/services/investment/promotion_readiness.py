from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from backend.models.investment import SpecialSituation
from backend.services.investment.document_package import DocumentPackage
from backend.services.investment.evidence_links import SituationEvidenceLinksPackage


ReadinessLevel = Literal["not_ready", "needs_documentation", "ready_for_manual_promotion"]


class PromotionReadinessPackage(BaseModel):
    situation_id: str
    readiness_level: ReadinessLevel
    readiness_score: int
    blocking_reasons: list[str]
    missing_required_documents: list[str]
    supporting_evidence: list[dict]
    suggested_manual_actions: list[str]
    warnings: list[str]
    recommended_next_step: str
    guardrails: list[str]


GUARDRAILS = [
    "Promotion Readiness is read-only and deterministic.",
    "Ready for manual promotion does not mean investment approval.",
    "SwissEdge does not auto-promote SpecialSituations to ResearchCases.",
    "Suggested or found documents are not automatically verified.",
    "Dani remains the final decision maker.",
]


def build_promotion_readiness_package(
    situation: SpecialSituation,
    *,
    document_package: DocumentPackage,
    evidence_links: SituationEvidenceLinksPackage,
) -> PromotionReadinessPackage:
    missing_required = [
        item.label
        for item in document_package.documents
        if item.priority == "required" and item.status in {"missing", "needs_manual_check"}
    ]
    evidence = _supporting_evidence(evidence_links)
    identifiers = _identifier_count(situation, evidence_links)
    blocking = _blocking_reasons(situation, missing_required, evidence, identifiers)
    score = _score(
        missing_required_count=len(missing_required),
        evidence_count=len(evidence),
        identifier_count=identifiers,
        document_readiness=document_package.readiness_level,
    )
    level = _readiness_level(
        blocking_reasons=blocking,
        missing_required_count=len(missing_required),
        evidence_count=len(evidence),
        identifier_count=identifiers,
    )
    actions = _manual_actions(missing_required, evidence, identifiers, document_package.manual_next_actions)
    warnings = _warnings(document_package, level)

    return PromotionReadinessPackage(
        situation_id=str(situation.id),
        readiness_level=level,
        readiness_score=score,
        blocking_reasons=blocking,
        missing_required_documents=missing_required,
        supporting_evidence=evidence[:6],
        suggested_manual_actions=actions,
        warnings=warnings,
        recommended_next_step=_recommended_next_step(level, actions),
        guardrails=GUARDRAILS,
    )


def _identifier_count(situation: SpecialSituation, evidence_links: SituationEvidenceLinksPackage) -> int:
    detection = evidence_links.sec_detection if isinstance(evidence_links.sec_detection, dict) else {}
    values = [
        situation.filing_url,
        situation.filing_type,
        detection.get("filing_url"),
        detection.get("accession_number"),
        detection.get("cik"),
        detection.get("detected_form_type") or detection.get("filing_type"),
    ]
    return len({str(value).strip() for value in values if isinstance(value, str) and value.strip()})


def _supporting_evidence(evidence_links: SituationEvidenceLinksPackage) -> list[dict]:
    rows = []
    for link in evidence_links.links:
        rows.append({
            "label": link.label,
            "url": link.url,
            "source_type": link.source_type,
            "origin": link.origin,
            "status": link.status,
            "filing_type": link.filing_type,
            "accession_number": link.accession_number,
            "metadata_only": link.metadata_only,
            "verified": False,
            "notes": link.notes,
        })
    return rows


def _blocking_reasons(
    situation: SpecialSituation,
    missing_required: list[str],
    evidence: list[dict],
    identifiers: int,
) -> list[str]:
    reasons = []
    if not situation.situation_type:
        reasons.append("Situation type is missing.")
    if not situation.company_name:
        reasons.append("Company name is missing.")
    if identifiers < 2:
        reasons.append("SEC filing identifiers are incomplete.")
    if not evidence:
        reasons.append("No supporting evidence links are available.")
    if missing_required:
        reasons.append("Required documents are still missing or need manual check.")
    return reasons


def _score(
    *,
    missing_required_count: int,
    evidence_count: int,
    identifier_count: int,
    document_readiness: str,
) -> int:
    score = 20
    score += min(identifier_count, 5) * 8
    score += min(evidence_count, 4) * 8
    if document_readiness == "ready_for_manual_evaluation":
        score += 30
    elif document_readiness == "mostly_ready":
        score += 20
    elif document_readiness == "useful_incomplete":
        score += 10
    score -= min(missing_required_count, 5) * 12
    return max(0, min(100, score))


def _readiness_level(
    *,
    blocking_reasons: list[str],
    missing_required_count: int,
    evidence_count: int,
    identifier_count: int,
) -> ReadinessLevel:
    hard_blockers = {
        "Situation type is missing.",
        "Company name is missing.",
        "SEC filing identifiers are incomplete.",
        "No supporting evidence links are available.",
    }
    if any(reason in hard_blockers for reason in blocking_reasons) or evidence_count == 0 or identifier_count < 2:
        return "not_ready"
    if missing_required_count > 0:
        return "needs_documentation"
    return "ready_for_manual_promotion"


def _manual_actions(
    missing_required: list[str],
    evidence: list[dict],
    identifiers: int,
    document_actions: list[str],
) -> list[str]:
    actions = []
    if identifiers < 2:
        actions.append("Confirm SEC filing URL, form type, CIK, and accession metadata.")
    if not evidence:
        actions.append("Add at least one source or SEC evidence link before considering promotion.")
    for label in missing_required[:4]:
        actions.append(f"Find or manually confirm required document: {label}.")
    actions.extend(document_actions[:4])
    if not actions:
        actions.append("Dani should manually review the evidence package and decide whether to promote.")
    return list(dict.fromkeys(actions))[:8]


def _warnings(document_package: DocumentPackage, level: ReadinessLevel) -> list[str]:
    warnings = [
        "This is a promotion-readiness view, not an investment recommendation.",
        "Ready for manual promotion does not mean investment approval.",
    ]
    if level == "ready_for_manual_promotion":
        warnings.append("Ready for manual promotion only means the ResearchCase creation decision can be reviewed by Dani.")
    if document_package.suggested_links:
        warnings.append("Suggested links are not verified documents.")
    warnings.extend(document_package.warnings[:3])
    return list(dict.fromkeys(warnings))


def _recommended_next_step(level: ReadinessLevel, actions: list[str]) -> str:
    if level == "ready_for_manual_promotion":
        return "Dani manual decision: review evidence and decide whether to create a ResearchCase."
    if actions:
        return actions[0]
    return "Continue manual documentation before promotion."
