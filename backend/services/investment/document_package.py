from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment.evidence_links import (
    ResearchCaseEvidenceLinksPackage,
    SituationEvidenceLinksPackage,
)
from backend.services.investment.sec_document_acquisition import SecDocumentAcquisitionPackage


Priority = Literal["required", "recommended", "optional"]
SourceHint = Literal["SEC", "company_ir", "court", "manual", "other"]
DocumentStatus = Literal["found", "suggested", "missing", "needs_manual_check", "not_applicable"]
ReadinessLevel = Literal["not_ready", "useful_incomplete", "mostly_ready", "ready_for_manual_evaluation"]


class DocumentTemplateItem(BaseModel):
    document_key: str
    label: str
    priority: Priority
    source_hint: SourceHint
    description: str


class DocumentPackageItem(DocumentTemplateItem):
    status: DocumentStatus
    matched_links: list[dict] = []
    suggested_links: list[dict] = []
    notes: str | None = None
    verified: bool = False


class DocumentPackageSummary(BaseModel):
    readiness_level: ReadinessLevel
    required_found: int
    required_missing: int
    recommended_found: int
    recommended_missing: int
    suggested_links_count: int
    manual_actions_count: int


class DocumentPackage(BaseModel):
    case_id: str
    case_type: Literal["special_situation", "research_case"]
    situation_type: str | None
    readiness_level: ReadinessLevel
    summary: DocumentPackageSummary
    documents: list[DocumentPackageItem]
    suggested_links: list[dict]
    manual_next_actions: list[str]
    warnings: list[str]
    guardrails: list[str]


@dataclass(frozen=True)
class TemplateRow:
    key: str
    label: str
    priority: Priority
    source_hint: SourceHint
    description: str


TEMPLATES: dict[str, list[TemplateRow]] = {
    "merger_arbitrage": [
        TemplateRow("sc_to_t", "SC TO-T", "required", "SEC", "Third-party tender offer statement."),
        TemplateRow("offer_to_purchase", "Offer to Purchase", "required", "SEC", "Offer terms and procedural details."),
        TemplateRow("letter_of_transmittal", "Letter of Transmittal", "recommended", "SEC", "Tender submission mechanics."),
        TemplateRow("schedule_14d_9", "Schedule 14D-9", "required", "SEC", "Target board recommendation and position."),
        TemplateRow("merger_agreement", "Merger Agreement", "required", "SEC", "Transaction terms, conditions, and termination rights."),
        TemplateRow("press_release", "Press Release", "recommended", "company_ir", "Company announcement for event context."),
        TemplateRow("company_ir_page", "Company IR page", "recommended", "company_ir", "Company investor relations transaction page."),
        TemplateRow("sec_filing_detail", "SEC filing detail page", "required", "SEC", "Official SEC accession detail page."),
        TemplateRow("key_exhibits", "Key exhibits", "recommended", "SEC", "Relevant exhibits attached to the filing."),
    ],
    "tender_offer": [
        TemplateRow("sc_to_i", "SC TO-I", "required", "SEC", "Issuer tender offer statement."),
        TemplateRow("offer_to_purchase", "Offer to Purchase", "required", "SEC", "Offer terms and procedural details."),
        TemplateRow("letter_of_transmittal", "Letter of Transmittal", "recommended", "SEC", "Tender submission mechanics."),
        TemplateRow("issuer_tender_statement", "Issuer tender offer statement", "required", "SEC", "Issuer filing package and amendments."),
        TemplateRow("press_release", "Press Release", "recommended", "company_ir", "Company announcement for event context."),
        TemplateRow("sec_filing_detail", "SEC filing detail page", "required", "SEC", "Official SEC accession detail page."),
        TemplateRow("key_exhibits", "Key exhibits", "recommended", "SEC", "Relevant exhibits attached to the filing."),
    ],
    "spin_off": [
        TemplateRow("form_10", "Form 10", "required", "SEC", "Registration statement for the separated company."),
        TemplateRow("information_statement", "Information Statement", "required", "SEC", "Distribution, business, and risk information."),
        TemplateRow("parent_press_release", "Parent company press release", "recommended", "company_ir", "Parent announcement for transaction context."),
        TemplateRow("investor_presentation", "Investor presentation", "recommended", "company_ir", "Management presentation for separation rationale."),
        TemplateRow("pro_forma_financials", "Pro forma financials", "required", "SEC", "Standalone financial view for manual analysis."),
        TemplateRow("separation_agreement", "Separation agreement", "recommended", "SEC", "Agreement governing the separation."),
        TemplateRow("tax_matters_agreement", "Tax Matters Agreement", "recommended", "SEC", "Tax responsibilities and constraints."),
        TemplateRow("transition_services_agreement", "Transition Services Agreement", "optional", "SEC", "Post-separation service dependencies."),
        TemplateRow("sec_filing_detail", "SEC filing detail page", "required", "SEC", "Official SEC accession detail page."),
    ],
    "bankruptcy": [
        TemplateRow("8k_liquidation", "8-K liquidation/dissolution", "required", "SEC", "Official event disclosure."),
        TemplateRow("plan_of_liquidation", "Plan of Liquidation", "required", "SEC", "Liquidation mechanics and expected distributions."),
        TemplateRow("proxy_statement", "Proxy statement if shareholder approval needed", "recommended", "SEC", "Shareholder vote materials when applicable."),
        TemplateRow("court_filings", "Court filings if bankruptcy", "recommended", "court", "Court docket or bankruptcy documents."),
        TemplateRow("press_release", "Press release", "recommended", "company_ir", "Company announcement for event context."),
        TemplateRow("asset_sale_agreements", "Asset sale agreements if applicable", "optional", "SEC", "Asset sale terms and proceeds context."),
        TemplateRow("estimated_distribution_documents", "Estimated distribution documents", "recommended", "SEC", "Company estimate of distributions, if disclosed."),
        TemplateRow("sec_filing_detail", "SEC filing detail page", "required", "SEC", "Official SEC accession detail page."),
    ],
}

ALIASES = {
    "acquisition_tender_offer": "merger_arbitrage",
    "liquidation": "bankruptcy",
    "dissolution": "bankruptcy",
}

GUARDRAILS = [
    "Document Package is deterministic metadata support.",
    "Found or suggested documents are not automatically verified.",
    "Ready for manual evaluation does not mean investment approval.",
    "Dani remains the final decision maker.",
]


def build_situation_document_package(
    situation: SpecialSituation,
    *,
    evidence_links: SituationEvidenceLinksPackage,
    sec_preview: SecDocumentAcquisitionPackage | None = None,
) -> DocumentPackage:
    situation_type = _situation_type_for_situation(situation)
    return _build_package(
        case_id=str(situation.id),
        case_type="special_situation",
        situation_type=situation_type,
        evidence_links=evidence_links.links,
        sec_preview=sec_preview,
    )


def build_research_case_document_package(
    rc: ResearchCase,
    *,
    evidence_links: ResearchCaseEvidenceLinksPackage,
    sec_preview: SecDocumentAcquisitionPackage | None = None,
    source_situation: SpecialSituation | None = None,
) -> DocumentPackage:
    situation_type = _situation_type_for_case(rc, source_situation)
    return _build_package(
        case_id=str(rc.id),
        case_type="research_case",
        situation_type=situation_type,
        evidence_links=evidence_links.links,
        sec_preview=sec_preview,
    )


def _build_package(
    *,
    case_id: str,
    case_type: Literal["special_situation", "research_case"],
    situation_type: str | None,
    evidence_links: list,
    sec_preview: SecDocumentAcquisitionPackage | None,
) -> DocumentPackage:
    template = _template_for(situation_type)
    suggested_pool = _suggested_links(sec_preview)
    items = [
        _match_item(row, evidence_links=evidence_links, suggested_pool=suggested_pool)
        for row in template
    ]
    summary = _summary(items)
    return DocumentPackage(
        case_id=case_id,
        case_type=case_type,
        situation_type=situation_type,
        readiness_level=summary.readiness_level,
        summary=summary,
        documents=items,
        suggested_links=suggested_pool[:10],
        manual_next_actions=_manual_actions(items),
        warnings=_warnings(items, situation_type),
        guardrails=GUARDRAILS,
    )


def _template_for(situation_type: str | None) -> list[TemplateRow]:
    key = ALIASES.get((situation_type or "").lower(), (situation_type or "").lower())
    return TEMPLATES.get(key) or TEMPLATES["merger_arbitrage"]


def _situation_type_for_situation(situation: SpecialSituation) -> str | None:
    evidence = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    detection = evidence.get("sec_detection") if isinstance(evidence.get("sec_detection"), dict) else {}
    return detection.get("situation_type") or situation.situation_type


def _situation_type_for_case(rc: ResearchCase, source_situation: SpecialSituation | None) -> str | None:
    brief = rc.brief if isinstance(rc.brief, dict) else {}
    detection = brief.get("detection_summary") if isinstance(brief.get("detection_summary"), dict) else {}
    return detection.get("situation_type") or (source_situation.situation_type if source_situation else None)


def _match_item(row: TemplateRow, *, evidence_links: list, suggested_pool: list[dict]) -> DocumentPackageItem:
    matched = [link for link in evidence_links if _matches_link(row, link)]
    found_links = [
        link
        for link in matched
        if str(getattr(link, "status", "") or "") not in {"candidate_found", "manual_review_required"}
    ]
    candidate_links = [
        link
        for link in matched
        if str(getattr(link, "status", "") or "") in {"candidate_found", "manual_review_required"}
    ]
    found = [link.model_dump() for link in found_links]
    candidates = [link.model_dump() for link in candidate_links]
    suggested = [link for link in suggested_pool if _matches(row, _dict_text(link))]
    if found:
        status: DocumentStatus = "found"
        notes = "Stored metadata has a matching link. Manual review still required."
    elif candidates:
        status = "needs_manual_check"
        notes = "Candidate source added — needs review. It is not verified evidence."
    elif suggested:
        status = "suggested"
        notes = "A candidate link may match this document. It is not verified."
    elif row.source_hint in {"court", "manual", "company_ir"}:
        status = "needs_manual_check"
        notes = "Requires manual source review outside stored SEC metadata."
    else:
        status = "missing"
        notes = "No matching stored or suggested metadata is available."
    return DocumentPackageItem(
        document_key=row.key,
        label=row.label,
        priority=row.priority,
        source_hint=row.source_hint,
        description=row.description,
        status=status,
        matched_links=(found + candidates)[:4],
        suggested_links=suggested[:4],
        notes=notes,
        verified=False,
    )


def _matches(row: TemplateRow, text: str) -> bool:
    text = text.lower()
    tokens = [row.key.replace("_", " "), row.label.lower()]
    if row.key == "sc_to_t":
        tokens.extend(["sc to-t", "sc to t", "schedule to"])
    if row.key == "sc_to_i":
        tokens.extend(["sc to-i", "sc to i", "schedule to"])
    if row.key == "issuer_tender_statement":
        tokens.extend(["sc to-i", "sc to i", "schedule to", "issuer tender"])
    if row.key == "sec_filing_detail":
        tokens.extend(["sec filing", "accession", "stored sec filing"])
    if row.key == "key_exhibits":
        tokens.extend(["exhibit", "ex-"])
    if row.key == "form_10":
        tokens.extend(["form 10", "10-12b"])
    return any(token and token in text for token in tokens)


def _matches_link(row: TemplateRow, link) -> bool:
    linked_resources = getattr(link, "linked_required_resource_ids", []) or []
    if row.key in linked_resources:
        return True
    return _matches(row, _link_text(link))


def _link_text(link) -> str:
    return " ".join(str(getattr(link, attr, "") or "") for attr in ("label", "url", "source_type", "filing_type", "notes"))


def _dict_text(item: dict) -> str:
    return " ".join(str(value or "") for value in item.values())


def _suggested_links(sec_preview: SecDocumentAcquisitionPackage | None) -> list[dict]:
    if not sec_preview:
        return []
    links = [doc.model_dump() for doc in sec_preview.official_links]
    links.extend(target.model_dump() for target in sec_preview.likely_document_targets)
    return links


def _summary(items: list[DocumentPackageItem]) -> DocumentPackageSummary:
    required = [item for item in items if item.priority == "required"]
    recommended = [item for item in items if item.priority == "recommended"]
    required_found = len([item for item in required if item.status in {"found", "suggested"}])
    recommended_found = len([item for item in recommended if item.status in {"found", "suggested"}])
    required_missing = len([item for item in required if item.status in {"missing", "needs_manual_check"}])
    recommended_missing = len([item for item in recommended if item.status in {"missing", "needs_manual_check"}])
    suggested_links_count = sum(len(item.suggested_links) for item in items)
    manual_actions_count = len([item for item in items if item.status in {"missing", "needs_manual_check", "suggested"}])
    if required_missing == 0 and recommended_missing <= 1:
        readiness: ReadinessLevel = "ready_for_manual_evaluation"
    elif required_missing <= 1:
        readiness = "mostly_ready"
    elif required_found > 0 or recommended_found > 0:
        readiness = "useful_incomplete"
    else:
        readiness = "not_ready"
    return DocumentPackageSummary(
        readiness_level=readiness,
        required_found=required_found,
        required_missing=required_missing,
        recommended_found=recommended_found,
        recommended_missing=recommended_missing,
        suggested_links_count=suggested_links_count,
        manual_actions_count=manual_actions_count,
    )


def _manual_actions(items: list[DocumentPackageItem]) -> list[str]:
    actions = []
    for item in items:
        if item.status == "suggested":
            actions.append(f"Review suggested link for {item.label}; do not mark verified until Dani confirms it.")
        elif item.status in {"missing", "needs_manual_check"} and item.priority in {"required", "recommended"}:
            actions.append(f"Find or confirm {item.label} from {item.source_hint}.")
    return actions[:8]


def _warnings(items: list[DocumentPackageItem], situation_type: str | None) -> list[str]:
    warnings = []
    if not situation_type:
        warnings.append("Situation type is unclear; default merger-arbitrage template was used.")
    missing_required = [item.label for item in items if item.priority == "required" and item.status in {"missing", "needs_manual_check"}]
    if missing_required:
        warnings.append(f"Missing required documents: {', '.join(missing_required[:5])}.")
    if any(item.status == "suggested" for item in items):
        warnings.append("Suggested links require manual review and are not verified evidence.")
    return warnings
