from __future__ import annotations

from copy import deepcopy
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.investment import SpecialSituation


TEMPLATE_VERSION = "v0.1"
WORKSPACE_KEY = "methodology_workspace"
ALLOWED_INITIAL_STATUSES = {"not_started", "needs_evidence"}
ALLOWED_WORKFLOW_STATUSES = {
    "new_detection",
    "triage_needed",
    "needs_resources",
    "checklist_in_progress",
    "ready_for_research_case",
    "promoted_to_research_case",
    "watchlist",
    "ignored",
}
ALLOWED_CHECKLIST_STATUSES = {
    "not_started",
    "needs_evidence",
    "evidence_found",
    "in_progress",
    "verified",
    "unknown",
    "not_applicable",
    "human_review_required",
}
ALLOWED_REQUIRED_RESOURCE_STATUSES = {
    "missing",
    "candidate_found",
    "evidence_found",
    "rejected",
    "not_applicable",
}


def _check(
    check_id: str,
    section: str,
    title: str,
    description: str,
    required_evidence_types: list[str],
    status: str = "not_started",
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "section": section,
        "title": title,
        "description": description,
        "required_evidence_types": required_evidence_types,
        "status": status,
        "human_review_required": True,
        "notes": None,
        "evidence_refs": [],
    }


def _resource(
    resource_id: str,
    title: str,
    description: str,
    source_type: str,
    required_or_optional: str,
    expected_source: str,
    related_check_ids: list[str],
) -> dict[str, Any]:
    return {
        "resource_id": resource_id,
        "title": title,
        "description": description,
        "source_type": source_type,
        "required_or_optional": required_or_optional,
        "expected_source": expected_source,
        "related_check_ids": related_check_ids,
        "status": "missing",
    }


TEMPLATES: dict[str, dict[str, Any]] = {
    "merger_arbitrage_acquisition_tender": {
        "template_key": "merger_arbitrage_acquisition_tender",
        "matches": {"situation_type": "merger_arbitrage", "subtype": "acquisition_tender_offer", "filing_type": "SC TO-T"},
        "checklist": [
            _check("ma_offer_terms", "Deal Terms", "Confirm offer terms", "Capture offer price, consideration type, expiration date, and tender mechanics from official materials.", ["SC TO-T", "Offer to Purchase"], "needs_evidence"),
            _check("ma_agreement", "Deal Terms", "Review transaction agreement", "Identify key closing conditions, termination rights, and any break fee or tender thresholds.", ["Merger Agreement", "SC TO-T exhibits"], "needs_evidence"),
            _check("ma_financing", "Financing", "Check financing terms", "Determine whether financing is committed, conditional, or otherwise a closing risk.", ["Financing disclosure", "Offer to Purchase"]),
            _check("ma_regulatory", "Regulatory", "Map approvals", "List required regulatory approvals and any HSR or antitrust disclosures.", ["Offer to Purchase", "Press release", "Amendments"]),
            _check("ma_target_response", "Process", "Find target response", "Locate target board recommendation or SC 14D-9 when available.", ["SC 14D-9", "Target press release"]),
            _check("ma_updates", "Monitoring", "Track amendments", "Check for amendments that change price, expiration, conditions, or risk factors.", ["Amendments"]),
        ],
        "required_resources": [
            _resource("ma_sc_to_t", "SC TO-T filing", "Initial third-party tender offer filing.", "sec_filing", "required", "SEC EDGAR", ["ma_offer_terms"]),
            _resource("ma_offer_purchase", "Offer to Purchase", "Primary tender offer document.", "sec_exhibit", "required", "SEC EDGAR exhibit", ["ma_offer_terms", "ma_regulatory"]),
            _resource("ma_merger_agreement", "Merger Agreement", "Transaction agreement and closing conditions.", "sec_exhibit", "required", "SEC EDGAR exhibit", ["ma_agreement"]),
            _resource("ma_target_release", "Target company press release", "Target announcement or response.", "press_release", "required", "Target investor relations", ["ma_target_response"]),
            _resource("ma_acquirer_release", "Acquirer press release", "Acquirer announcement and strategic rationale.", "press_release", "optional", "Acquirer investor relations", ["ma_agreement"]),
            _resource("ma_sc_14d9", "SC 14D9 if available", "Target board recommendation filing.", "sec_filing", "optional", "SEC EDGAR", ["ma_target_response"]),
            _resource("ma_expiration", "Expiration date", "Current tender offer expiration.", "deal_term", "required", "Offer materials", ["ma_offer_terms"]),
            _resource("ma_offer_price", "Offer price", "Current offer price and consideration type.", "deal_term", "required", "Offer materials", ["ma_offer_terms"]),
            _resource("ma_financing_terms", "Financing terms", "Committed financing and funding conditions.", "deal_term", "required", "Offer materials", ["ma_financing"]),
            _resource("ma_regulatory_approvals", "Regulatory approvals", "Required approvals and timing constraints.", "regulatory", "required", "Offer materials", ["ma_regulatory"]),
            _resource("ma_amendments", "Amendments", "Later SEC amendments to offer terms.", "sec_filing", "optional", "SEC EDGAR", ["ma_updates"]),
            _resource("ma_market_price", "Current market price", "Future market-data input; not integrated in Sprint S.", "market_data", "optional", "Market data provider later", ["ma_offer_terms"]),
        ],
    },
    "tender_offer_self_tender": {
        "template_key": "tender_offer_self_tender",
        "matches": {"situation_type": "tender_offer", "subtype": "self_tender", "filing_type": "SC TO-I"},
        "checklist": [
            _check("st_terms", "Offer Terms", "Confirm self-tender terms", "Capture price, range or fixed price, size, expiration, and tender mechanics.", ["SC TO-I", "Offer to Purchase"], "needs_evidence"),
            _check("st_proration", "Offer Terms", "Review proration and priority", "Identify proration rules, odd-lot priority, and conditions for oversubscription.", ["Offer to Purchase", "Letter of Transmittal"]),
            _check("st_funds", "Financing", "Check source of funds", "Verify cash, debt, or other financing sources supporting the tender.", ["SC TO-I", "Offer to Purchase"]),
            _check("st_balance_sheet", "Financial Context", "Review liquidity context", "Collect recent balance sheet or liquidity context for human review.", ["10-Q", "10-K", "Earnings release"]),
            _check("st_updates", "Monitoring", "Track amendments", "Check for amendments to range, size, expiration, proration, or conditions.", ["Amendments"]),
        ],
        "required_resources": [
            _resource("st_sc_to_i", "SC TO-I filing", "Issuer tender offer filing.", "sec_filing", "required", "SEC EDGAR", ["st_terms"]),
            _resource("st_offer_purchase", "Offer to Purchase", "Primary self-tender terms document.", "sec_exhibit", "required", "SEC EDGAR exhibit", ["st_terms", "st_proration"]),
            _resource("st_letter_transmittal", "Letter of Transmittal", "Tender submission mechanics.", "sec_exhibit", "required", "SEC EDGAR exhibit", ["st_proration"]),
            _resource("st_dutch_range", "Dutch auction range if applicable", "Pricing range and clearing-price mechanics.", "deal_term", "optional", "Offer materials", ["st_terms"]),
            _resource("st_odd_lot", "Odd-lot priority", "Any odd-lot holder priority terms.", "deal_term", "optional", "Offer materials", ["st_proration"]),
            _resource("st_proration_terms", "Proration terms", "Oversubscription and allocation rules.", "deal_term", "required", "Offer materials", ["st_proration"]),
            _resource("st_expiration", "Expiration date", "Current tender expiration.", "deal_term", "required", "Offer materials", ["st_terms"]),
            _resource("st_source_funds", "Source of funds", "Funding source disclosure.", "financial_disclosure", "required", "SC TO-I", ["st_funds"]),
            _resource("st_liquidity", "Recent balance sheet / liquidity", "Recent liquidity context for review.", "financial_statement", "required", "SEC filings", ["st_balance_sheet"]),
            _resource("st_ir_page", "Company IR page", "Issuer investor relations page.", "company_site", "optional", "Company IR", ["st_updates"]),
            _resource("st_press_release", "Press release", "Issuer announcement.", "press_release", "required", "Company IR", ["st_terms"]),
            _resource("st_amendments", "Amendments", "Later SEC amendments.", "sec_filing", "optional", "SEC EDGAR", ["st_updates"]),
        ],
    },
    "spin_off_standard": {
        "template_key": "spin_off_standard",
        "matches": {"situation_type": "spin_off", "subtype": "standard_spin_off", "filing_type": "Form 10"},
        "checklist": [
            _check("so_business", "Business", "Understand SpinCo business", "Summarize business, segment profile, customers, and standalone strategy.", ["Form 10", "Information Statement"], "needs_evidence"),
            _check("so_financials", "Financials", "Review pro forma financials", "Collect pro forma statements, leverage, debt allocation, and capital structure.", ["Form 10", "Pro forma financials"]),
            _check("so_distribution", "Transaction Mechanics", "Confirm distribution mechanics", "Identify distribution ratio, record date, expected timing, and parent holders affected.", ["Information Statement", "Press release"]),
            _check("so_tax", "Tax", "Check tax treatment", "Capture stated tax treatment and any conditions or tax opinion dependencies.", ["Information Statement", "Form 10"]),
            _check("so_management", "Governance", "Review management incentives", "Collect management, board, compensation, and incentive disclosures.", ["Form 10"]),
            _check("so_updates", "Monitoring", "Track amendments", "Check Form 10 amendments for changed financials, timing, or transaction terms.", ["Form 10 amendments"]),
        ],
        "required_resources": [
            _resource("so_form_10", "Form 10", "SpinCo registration statement.", "sec_filing", "required", "SEC EDGAR", ["so_business", "so_financials"]),
            _resource("so_form_10_amendments", "Form 10 amendments", "Later amendments to registration statement.", "sec_filing", "optional", "SEC EDGAR", ["so_updates"]),
            _resource("so_info_statement", "Information statement", "Distribution and shareholder information.", "sec_exhibit", "required", "SEC EDGAR", ["so_distribution", "so_tax"]),
            _resource("so_parent_release", "Parent company press release", "Parent announcement and timing.", "press_release", "required", "Parent IR", ["so_distribution"]),
            _resource("so_description", "Spin company description", "Business overview.", "business_profile", "required", "Form 10", ["so_business"]),
            _resource("so_pro_forma", "Pro forma financials", "Standalone financial statements.", "financial_statement", "required", "Form 10", ["so_financials"]),
            _resource("so_debt", "Debt allocation", "Debt and capital structure allocation.", "financial_disclosure", "required", "Form 10", ["so_financials"]),
            _resource("so_incentives", "Management incentives", "Management and incentive disclosures.", "governance", "required", "Form 10", ["so_management"]),
            _resource("so_tax_treatment", "Tax treatment", "Expected tax treatment.", "tax_disclosure", "required", "Information Statement", ["so_tax"]),
            _resource("so_distribution_ratio", "Distribution ratio", "Shares distributed per parent share.", "deal_term", "required", "Information Statement", ["so_distribution"]),
            _resource("so_timing", "Expected timing", "Record date, distribution date, and milestones.", "deal_term", "required", "Press release / Information Statement", ["so_distribution"]),
        ],
    },
    "liquidation_or_dissolution_voluntary": {
        "template_key": "liquidation_or_dissolution_voluntary",
        "matches": {"situation_type": "bankruptcy", "subtype": "voluntary_liquidation", "filing_type": "8-K"},
        "checklist": [
            _check("liq_plan", "Plan", "Collect liquidation or dissolution plan", "Locate the governing plan and summarize process, approvals, and scope.", ["8-K", "Plan of Liquidation"], "needs_evidence"),
            _check("liq_approvals", "Approvals", "Confirm approval requirements", "Identify board approval, shareholder approval requirements, and key conditions.", ["8-K", "Proxy materials"]),
            _check("liq_assets", "Assets", "Review asset sale plan", "Collect asset sale process and expected proceeds disclosures.", ["8-K", "Press release", "Plan"]),
            _check("liq_liabilities", "Claims", "Review liabilities and claims", "Identify known liabilities, claims, reserves, and contingencies.", ["8-K", "Financial statements"]),
            _check("liq_distributions", "Distributions", "Capture estimated distributions", "Record stated distribution estimates, timing, uncertainty, and assumptions.", ["8-K", "Plan", "Press release"]),
            _check("liq_updates", "Monitoring", "Track amendments and updates", "Monitor later filings for revised timing, proceeds, claims, or distributions.", ["Amendments", "8-K updates"]),
        ],
        "required_resources": [
            _resource("liq_8k", "8-K filing", "Current report announcing liquidation or dissolution.", "sec_filing", "required", "SEC EDGAR", ["liq_plan"]),
            _resource("liq_plan_doc", "Plan of liquidation / dissolution", "Governing plan document.", "sec_exhibit", "required", "SEC EDGAR exhibit", ["liq_plan", "liq_distributions"]),
            _resource("liq_board", "Board approval", "Board approval disclosure.", "governance", "required", "8-K", ["liq_approvals"]),
            _resource("liq_shareholder", "Shareholder approval requirement", "Whether shareholder approval is required and timing.", "governance", "required", "8-K / proxy materials", ["liq_approvals"]),
            _resource("liq_est_distributions", "Estimated distributions", "Management estimate of cash distributions.", "deal_term", "required", "Plan / 8-K", ["liq_distributions"]),
            _resource("liq_asset_sale", "Asset sale plan", "Asset sale process and expected proceeds.", "transaction_document", "required", "Plan / 8-K", ["liq_assets"]),
            _resource("liq_claims", "Liabilities and claims", "Known claims, reserves, and contingencies.", "financial_disclosure", "required", "SEC filings", ["liq_liabilities"]),
            _resource("liq_timeline", "Timeline", "Milestones and expected wind-down timing.", "deal_term", "required", "Plan / 8-K", ["liq_distributions"]),
            _resource("liq_press_release", "Press release", "Company announcement.", "press_release", "optional", "Company IR", ["liq_plan"]),
            _resource("liq_amendments", "Later amendments", "Later updates to plan, timing, claims, or distributions.", "sec_filing", "optional", "SEC EDGAR", ["liq_updates"]),
        ],
    },
}


def select_methodology_template(
    *,
    situation_type: str | None,
    subtype: str | None,
    filing_type: str | None,
) -> dict[str, Any] | None:
    normalized_form = (filing_type or "").upper()
    for template in TEMPLATES.values():
        match = template["matches"]
        if situation_type != match["situation_type"]:
            continue
        if subtype != match["subtype"]:
            continue
        if match["filing_type"].upper() not in normalized_form:
            continue
        return template
    return None


def build_methodology_workspace(
    *,
    situation_type: str | None,
    subtype: str | None,
    filing_type: str | None,
) -> dict[str, Any] | None:
    template = select_methodology_template(
        situation_type=situation_type,
        subtype=subtype,
        filing_type=filing_type,
    )
    if not template:
        return None

    checklist = deepcopy(template["checklist"])
    required_resources = deepcopy(template["required_resources"])
    progress = calculate_workspace_progress({
        "checklist": checklist,
        "required_resources": required_resources,
    })

    return {
        "template_key": template["template_key"],
        "template_version": TEMPLATE_VERSION,
        "source": "processed_course_artifacts",
        "requires_course_review": True,
        "checklist": checklist,
        "required_resources": required_resources,
        "progress": progress,
    }


def recalculate_methodology_progress(workspace: dict[str, Any]) -> dict[str, int]:
    checklist = workspace.get("checklist") if isinstance(workspace.get("checklist"), list) else []
    resources = workspace.get("required_resources") if isinstance(workspace.get("required_resources"), list) else []
    candidates = workspace.get("resource_candidates") if isinstance(workspace.get("resource_candidates"), list) else []
    return {
        "total_checks": len(checklist),
        "verified_checks": sum(1 for item in checklist if item.get("status") == "verified"),
        "evidence_found": sum(1 for item in checklist if item.get("status") == "evidence_found"),
        "missing_required_resources": sum(
            1
            for item in resources
            if item.get("required_or_optional") == "required" and item.get("status") == "missing"
        ),
        "candidate_resources": sum(1 for item in candidates if item.get("status") == "candidate_found"),
        "human_review_required_count": sum(1 for item in checklist if item.get("human_review_required") is True),
    }


def calculate_workspace_progress(workspace: dict[str, Any]) -> dict[str, int]:
    return recalculate_methodology_progress(workspace)


def attach_methodology_workspace_to_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    if WORKSPACE_KEY in evidence:
        return evidence

    sec_detection = evidence.get("sec_detection") if isinstance(evidence.get("sec_detection"), dict) else {}
    workspace = build_methodology_workspace(
        situation_type=sec_detection.get("situation_type") or evidence.get("situation_type"),
        subtype=sec_detection.get("subtype") or evidence.get("subtype"),
        filing_type=sec_detection.get("detected_form_type") or evidence.get("filing_type"),
    )
    if not workspace:
        return evidence

    updated = deepcopy(evidence)
    updated[WORKSPACE_KEY] = workspace
    return updated


def situation_matches_backfill_target(situation: SpecialSituation) -> bool:
    if situation.status != "detected":
        return False
    evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
    if evaluation.get("source") != "sec_edgar":
        return False
    if evaluation.get("detected_only") is not True:
        return False
    if WORKSPACE_KEY in evaluation:
        return False
    return isinstance(evaluation.get("sec_detection"), dict)


async def attach_methodology_workspace_backfill(
    db: AsyncSession,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    result = await db.execute(select(SpecialSituation).where(SpecialSituation.status == "detected"))
    candidates = [item for item in result.scalars().all() if situation_matches_backfill_target(item)]

    matched: list[dict[str, Any]] = []
    updated_count = 0
    for situation in candidates:
        evaluation = situation.evaluation if isinstance(situation.evaluation, dict) else {}
        updated = attach_methodology_workspace_to_evidence(evaluation)
        workspace = updated.get(WORKSPACE_KEY)
        if not workspace:
            continue
        matched.append({
            "id": str(situation.id),
            "company_name": situation.company_name,
            "filing_type": situation.filing_type,
            "template_key": workspace["template_key"],
        })
        if apply:
            situation.evaluation = updated
            updated_count += 1

    if apply and updated_count:
        await db.flush()

    return {
        "dry_run": not apply,
        "matched_count": len(matched),
        "updated_count": updated_count,
        "matches": matched,
    }
