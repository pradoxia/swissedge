from __future__ import annotations

from copy import deepcopy
from typing import Any


SUPPORTED_SITUATION_TYPES = [
    "merger_arbitrage",
    "tender_offer",
    "spin_off",
    "bankruptcy",
    "liquidation",
    "rights_offering",
    "proxy_fight",
    "unknown",
]

ALIASES = {
    "acquisition_tender_offer": "merger_arbitrage",
    "issuer_tender": "tender_offer",
    "dissolution": "liquidation",
}

GUARDRAILS = [
    "Course Documentation Map is compact metadata, not private course text.",
    "The map supports manual documentation and review; it is not an investment recommendation.",
    "Required documents and information are not automatically verified.",
    "Dani remains the final decision maker.",
]


def _chapter(chapter_id: str, title: str, relevance: str, reason: str) -> dict[str, str]:
    return {"chapter_id": chapter_id, "title": title, "relevance": relevance, "reason": reason}


def _doc(key: str, label: str, importance: str, source_hint: str, why: str, search: str) -> dict[str, str]:
    return {
        "document_key": key,
        "label": label,
        "importance": importance,
        "source_hint": source_hint,
        "why_it_matters": why,
        "search_guidance": search,
    }


def _info(key: str, label: str, importance: str, why: str, docs: list[str], skills: list[str]) -> dict[str, Any]:
    return {
        "info_key": key,
        "label": label,
        "importance": importance,
        "why_it_matters": why,
        "source_document_keys": docs,
        "required_skill_keys": skills,
    }


def _check(key: str, label: str, importance: str, why: str, docs: list[str], skills: list[str]) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "importance": importance,
        "why_it_matters": why,
        "required_document_keys": docs,
        "required_skill_keys": skills,
    }


COMMON_SEC_DOC = _doc(
    "sec_filing_detail",
    "SEC filing detail page",
    "high",
    "SEC",
    "Anchors the case to an official accession and filing history.",
    "Open the official SEC accession detail page and confirm form, date, CIK, and accession.",
)

COURSE_DOCUMENTATION_MAPS: dict[str, dict[str, Any]] = {
    "merger_arbitrage": {
        "situation_type": "merger_arbitrage",
        "display_name": "Merger arbitrage / acquisition tender",
        "relevant_course_chapters": [
            _chapter("event_driven_mergers", "Merger arbitrage process", "primary", "Defines transaction mechanics, spread, timing, and closing risks."),
            _chapter("deal_documents", "Deal document review", "primary", "Identifies the documents needed to understand offer terms and board recommendation."),
            _chapter("risk_controls", "Risk and downside controls", "secondary", "Frames conditions, financing, termination, and regulatory risk."),
        ],
        "applicable_playbooks": ["merger_arbitrage", "acquisition_tender"],
        "required_documents": [
            _doc("sc_to_t", "SC TO-T", "critical", "SEC", "Official third-party tender offer statement.", "Search SEC filings for SC TO-T and amendments."),
            _doc("offer_to_purchase", "Offer to Purchase", "critical", "SEC exhibits", "Defines offer price, timing, conditions, and procedures.", "Review filing exhibits and tender offer documents."),
            _doc("schedule_14d_9", "Schedule 14D-9", "critical", "SEC", "Shows target board position and recommendation.", "Search target company SEC filings for Schedule 14D-9."),
            _doc("merger_agreement", "Merger Agreement", "critical", "SEC exhibits", "Defines legal conditions, termination rights, and consideration.", "Check 8-K or tender offer exhibits for the transaction agreement."),
            _doc("press_release", "Press Release", "medium", "company_ir", "Provides announcement context and timing.", "Check company IR transaction news."),
            COMMON_SEC_DOC,
        ],
        "required_information": [
            _info("consideration", "Consideration and offer price", "critical", "Needed to understand economics.", ["offer_to_purchase", "merger_agreement"], ["consideration_extractor"]),
            _info("timeline", "Offer and closing timeline", "high", "Needed to assess process and key dates.", ["offer_to_purchase"], ["timeline_extractor"]),
            _info("conditions", "Closing and tender conditions", "critical", "Needed to identify deal break risk.", ["offer_to_purchase", "merger_agreement"], ["condition_extractor"]),
            _info("board_recommendation", "Target board recommendation", "high", "Needed to confirm target response.", ["schedule_14d_9"], ["schedule_14d9_finder"]),
        ],
        "checklist_items": [
            _check("confirm_offer_docs", "Confirm official tender documents", "critical", "The case cannot be reviewed without official offer terms.", ["sc_to_t", "offer_to_purchase"], ["sec_filing_locator", "sec_document_classifier"]),
            _check("confirm_target_response", "Confirm target board response", "critical", "Board recommendation can change risk and timing.", ["schedule_14d_9"], ["schedule_14d9_finder"]),
            _check("review_conditions", "Review closing conditions", "critical", "Conditions define the main break points.", ["merger_agreement", "offer_to_purchase"], ["condition_extractor"]),
        ],
        "blocking_conditions": [
            "Offer to Purchase is missing.",
            "Schedule 14D-9 is missing or not yet reviewed.",
            "Merger Agreement is missing.",
            "Consideration or closing conditions cannot be identified from official documents.",
        ],
        "notes": GUARDRAILS,
    },
    "tender_offer": {
        "situation_type": "tender_offer",
        "display_name": "Issuer tender offer",
        "relevant_course_chapters": [
            _chapter("issuer_tenders", "Issuer tender offers", "primary", "Defines issuer offer mechanics, proration, and participation considerations."),
            _chapter("capital_returns", "Capital return events", "secondary", "Provides context for buybacks, tender offers, and capital allocation."),
        ],
        "applicable_playbooks": ["issuer_tender_offer"],
        "required_documents": [
            _doc("sc_to_i", "SC TO-I", "critical", "SEC", "Official issuer tender offer statement.", "Search SEC filings for SC TO-I and amendments."),
            _doc("offer_to_purchase", "Offer to Purchase", "critical", "SEC exhibits", "Defines offer price, size, timing, and conditions.", "Review issuer tender offer exhibits."),
            _doc("letter_of_transmittal", "Letter of Transmittal", "high", "SEC exhibits", "Defines participation mechanics.", "Check tender offer exhibit index."),
            _doc("press_release", "Press Release", "medium", "company_ir", "Provides announcement context.", "Check company IR and SEC 8-K exhibits."),
            COMMON_SEC_DOC,
        ],
        "required_information": [
            _info("offer_size", "Offer size and price range", "critical", "Defines economics and scale.", ["offer_to_purchase"], ["tender_offer_terms_skill"]),
            _info("proration", "Proration and priority terms", "high", "Affects expected execution.", ["offer_to_purchase", "letter_of_transmittal"], ["tender_offer_terms_skill"]),
            _info("expiration", "Expiration and withdrawal timing", "high", "Needed for event calendar.", ["offer_to_purchase"], ["timeline_extractor"]),
        ],
        "checklist_items": [
            _check("confirm_issuer_offer", "Confirm issuer tender statement", "critical", "The official issuer filing anchors the case.", ["sc_to_i"], ["sec_filing_locator"]),
            _check("extract_tender_terms", "Extract tender terms", "critical", "Offer size, price, and timing drive the review.", ["offer_to_purchase"], ["tender_offer_terms_skill"]),
            _check("confirm_participation_mechanics", "Confirm participation mechanics", "high", "Submission mechanics affect feasibility.", ["letter_of_transmittal"], ["sec_exhibit_index_reader"]),
        ],
        "blocking_conditions": [
            "SC TO-I is missing.",
            "Offer to Purchase is missing.",
            "Offer size or expiration date cannot be identified.",
        ],
        "notes": GUARDRAILS,
    },
    "spin_off": {
        "situation_type": "spin_off",
        "display_name": "Spin-off",
        "relevant_course_chapters": [
            _chapter("spin_offs", "Spin-off analysis", "primary", "Defines separation mechanics and standalone company review."),
            _chapter("pro_forma_financials", "Pro forma financial review", "primary", "Frames standalone financial context."),
            _chapter("tax_and_separation", "Tax and separation agreements", "secondary", "Highlights structural dependencies."),
        ],
        "applicable_playbooks": ["spin_off"],
        "required_documents": [
            _doc("form_10", "Form 10", "critical", "SEC", "Primary registration statement for the separated company.", "Search SEC filings for Form 10 or 10-12B."),
            _doc("information_statement", "Information Statement", "critical", "SEC exhibits", "Explains distribution, business, risks, and governance.", "Review Form 10 exhibits and amendments."),
            _doc("pro_forma_financials", "Pro forma financials", "critical", "SEC", "Shows standalone financial profile.", "Review Form 10 financial sections and exhibits."),
            _doc("separation_agreement", "Separation agreement", "high", "SEC exhibits", "Defines post-separation obligations.", "Check exhibit index for separation agreement."),
            _doc("tax_matters_agreement", "Tax Matters Agreement", "high", "SEC exhibits", "Defines tax constraints and responsibilities.", "Check exhibit index for tax matters agreement."),
            COMMON_SEC_DOC,
        ],
        "required_information": [
            _info("distribution_terms", "Distribution terms", "critical", "Needed to understand timing and share distribution.", ["information_statement"], ["timeline_extractor"]),
            _info("standalone_financials", "Standalone financial profile", "critical", "Needed for review of the separated business.", ["pro_forma_financials"], ["form_10_analyzer"]),
            _info("separation_dependencies", "Separation dependencies", "high", "Needed to assess execution and transition risks.", ["separation_agreement"], ["condition_extractor"]),
        ],
        "checklist_items": [
            _check("confirm_form_10", "Confirm Form 10 package", "critical", "The Form 10 is the core spin-off source.", ["form_10"], ["sec_filing_locator", "form_10_analyzer"]),
            _check("review_financials", "Review pro forma financials", "critical", "Standalone economics depend on pro forma information.", ["pro_forma_financials"], ["form_10_analyzer"]),
            _check("review_separation_docs", "Review separation agreements", "high", "Separation terms affect operational risk.", ["separation_agreement", "tax_matters_agreement"], ["sec_exhibit_index_reader"]),
        ],
        "blocking_conditions": [
            "Form 10 is missing.",
            "Information Statement is missing.",
            "Pro forma financials are missing.",
        ],
        "notes": GUARDRAILS,
    },
    "bankruptcy": {
        "situation_type": "bankruptcy",
        "display_name": "Bankruptcy / restructuring",
        "relevant_course_chapters": [
            _chapter("distressed_events", "Distressed and bankruptcy events", "primary", "Defines restructuring context and court-source dependency."),
            _chapter("claims_and_recovery", "Claims and recovery framework", "secondary", "Frames distributions and recovery uncertainty."),
        ],
        "applicable_playbooks": ["bankruptcy", "distressed_restructuring"],
        "required_documents": [
            _doc("8k_bankruptcy", "8-K bankruptcy disclosure", "critical", "SEC", "Official disclosure of bankruptcy or restructuring event.", "Search company SEC filings for 8-K event disclosure."),
            _doc("court_filings", "Court filings", "critical", "court", "Court docket is often the primary source of process details.", "Review official court docket or approved docket provider manually."),
            _doc("restructuring_plan", "Restructuring or reorganization plan", "high", "court", "Defines proposed treatment and recovery structure.", "Search court filings and SEC exhibits."),
            _doc("press_release", "Press release", "medium", "company_ir", "Provides announcement context.", "Check company IR or 8-K exhibit."),
            COMMON_SEC_DOC,
        ],
        "required_information": [
            _info("case_status", "Case status and forum", "critical", "Needed to understand legal process.", ["court_filings", "8k_bankruptcy"], ["liquidation_plan_analyzer"]),
            _info("recovery_terms", "Recovery or treatment terms", "high", "Needed for manual recovery review.", ["restructuring_plan"], ["condition_extractor"]),
            _info("timeline", "Court and process timeline", "high", "Needed for catalyst tracking.", ["court_filings"], ["timeline_extractor"]),
        ],
        "checklist_items": [
            _check("confirm_court_source", "Confirm court source", "critical", "Bankruptcy review depends on court records.", ["court_filings"], ["source_confidence_assessor"]),
            _check("review_plan_terms", "Review restructuring plan terms", "high", "Plan terms drive recovery analysis.", ["restructuring_plan"], ["liquidation_plan_analyzer"]),
        ],
        "blocking_conditions": [
            "Court source is missing.",
            "Bankruptcy or restructuring disclosure is missing.",
            "Plan or process status cannot be identified.",
        ],
        "notes": GUARDRAILS,
    },
    "liquidation": {
        "situation_type": "liquidation",
        "display_name": "Liquidation / dissolution",
        "relevant_course_chapters": [
            _chapter("liquidations", "Liquidation and dissolution events", "primary", "Defines plan, asset sale, and distribution review."),
            _chapter("asset_value_realization", "Asset value realization", "secondary", "Frames distribution estimates and execution risk."),
        ],
        "applicable_playbooks": ["liquidation", "dissolution"],
        "required_documents": [
            _doc("8k_liquidation", "8-K liquidation/dissolution", "critical", "SEC", "Official event disclosure.", "Search SEC filings for liquidation or dissolution 8-K."),
            _doc("plan_of_liquidation", "Plan of Liquidation", "critical", "SEC exhibits", "Defines mechanics, approvals, and distributions.", "Check 8-K, proxy, and exhibit index."),
            _doc("proxy_statement", "Proxy statement if approval needed", "high", "SEC", "Shows shareholder vote details when required.", "Search DEF 14A or related proxy filings."),
            _doc("estimated_distribution_documents", "Estimated distribution documents", "critical", "SEC", "Supports manual estimate of distributions.", "Search SEC filings and company liquidation updates."),
            COMMON_SEC_DOC,
        ],
        "required_information": [
            _info("distribution_estimate", "Estimated distribution range", "critical", "Needed for manual liquidation review.", ["plan_of_liquidation", "estimated_distribution_documents"], ["liquidation_plan_analyzer"]),
            _info("approval_status", "Approval and vote status", "high", "Needed to understand whether liquidation can proceed.", ["proxy_statement", "plan_of_liquidation"], ["condition_extractor"]),
            _info("asset_sale_status", "Asset sale status", "medium", "Needed if proceeds depend on sales.", ["plan_of_liquidation"], ["timeline_extractor"]),
        ],
        "checklist_items": [
            _check("confirm_plan", "Confirm plan of liquidation", "critical", "The plan defines the process and potential distributions.", ["plan_of_liquidation"], ["liquidation_plan_analyzer"]),
            _check("confirm_distribution_docs", "Confirm distribution support", "critical", "Distribution estimates must come from source documents.", ["estimated_distribution_documents"], ["source_confidence_assessor"]),
        ],
        "blocking_conditions": [
            "Plan of Liquidation is missing.",
            "Estimated distribution support is missing.",
            "Approval status is unclear.",
        ],
        "notes": GUARDRAILS,
    },
    "rights_offering": {
        "situation_type": "rights_offering",
        "display_name": "Rights offering",
        "relevant_course_chapters": [
            _chapter("rights_offerings", "Rights offerings", "primary", "Defines subscription mechanics, oversubscription, and dilution."),
            _chapter("capital_structure", "Capital structure events", "secondary", "Frames dilution and financing context."),
        ],
        "applicable_playbooks": ["rights_offering"],
        "required_documents": [
            _doc("rights_offering_prospectus", "Rights offering prospectus", "critical", "SEC", "Defines subscription terms and eligibility.", "Search SEC filings for prospectus or registration statement."),
            _doc("subscription_rights_agreement", "Subscription rights agreement", "high", "SEC exhibits", "Defines mechanics and rights terms.", "Check registration statement exhibits."),
            _doc("press_release", "Press release", "medium", "company_ir", "Provides announcement context.", "Check company IR and 8-K exhibits."),
            COMMON_SEC_DOC,
        ],
        "required_information": [
            _info("subscription_terms", "Subscription terms", "critical", "Needed to understand participation mechanics.", ["rights_offering_prospectus"], ["rights_offering_terms_skill"]),
            _info("oversubscription", "Oversubscription rights", "high", "Can materially affect expected allocation.", ["rights_offering_prospectus", "subscription_rights_agreement"], ["rights_offering_terms_skill"]),
        ],
        "checklist_items": [
            _check("confirm_prospectus", "Confirm rights offering prospectus", "critical", "The prospectus is the primary source.", ["rights_offering_prospectus"], ["sec_filing_locator"]),
            _check("extract_rights_terms", "Extract rights terms", "critical", "Terms define economics and participation.", ["rights_offering_prospectus"], ["rights_offering_terms_skill"]),
        ],
        "blocking_conditions": [
            "Rights offering prospectus is missing.",
            "Subscription terms are unclear.",
        ],
        "notes": GUARDRAILS,
    },
    "proxy_fight": {
        "situation_type": "proxy_fight",
        "display_name": "Proxy fight / activist contest",
        "relevant_course_chapters": [
            _chapter("proxy_contests", "Proxy contests", "primary", "Defines voting materials, activist thesis, and board response."),
            _chapter("governance_events", "Governance events", "secondary", "Frames governance and voting implications."),
        ],
        "applicable_playbooks": ["proxy_fight", "activist_campaign"],
        "required_documents": [
            _doc("proxy_statement", "Proxy statement", "critical", "SEC", "Official voting and meeting material.", "Search DEF 14A and contested solicitation filings."),
            _doc("activist_proxy_materials", "Activist proxy materials", "critical", "SEC", "Shows dissident slate, proposal, or thesis.", "Search DFAN14A, PREC14A, DEFC14A, and related filings."),
            _doc("company_response", "Company response materials", "high", "company_ir", "Shows board response and counterarguments.", "Check company IR and SEC solicitation materials."),
            COMMON_SEC_DOC,
        ],
        "required_information": [
            _info("vote_items", "Voting items and slate", "critical", "Needed to understand the contest.", ["proxy_statement", "activist_proxy_materials"], ["proxy_materials_analyzer"]),
            _info("timeline", "Meeting and vote timeline", "high", "Needed for catalyst tracking.", ["proxy_statement"], ["timeline_extractor"]),
        ],
        "checklist_items": [
            _check("confirm_proxy_materials", "Confirm proxy materials", "critical", "Proxy contest review needs both sides where possible.", ["proxy_statement", "activist_proxy_materials"], ["proxy_materials_analyzer"]),
            _check("review_vote_timeline", "Review vote timeline", "high", "Timing defines next actions.", ["proxy_statement"], ["timeline_extractor"]),
        ],
        "blocking_conditions": [
            "Proxy statement is missing.",
            "Activist materials are missing.",
            "Voting items are unclear.",
        ],
        "notes": GUARDRAILS,
    },
    "unknown": {
        "situation_type": "unknown",
        "display_name": "Unknown / needs classification",
        "relevant_course_chapters": [
            _chapter("classification", "Situation classification", "primary", "Used when the situation type is not yet reliable."),
        ],
        "applicable_playbooks": ["manual_triage"],
        "required_documents": [
            COMMON_SEC_DOC,
            _doc("source_disclosure", "Source disclosure", "critical", "manual", "A primary source is needed before mapping the case.", "Open the original source and identify form, date, and event type."),
        ],
        "required_information": [
            _info("classification_basis", "Classification basis", "critical", "Needed before selecting a playbook.", ["source_disclosure", "sec_filing_detail"], ["playbook_matcher", "misclassification_detector"]),
        ],
        "checklist_items": [
            _check("classify_situation", "Classify situation type", "critical", "The case cannot move through the course map without a playbook.", ["source_disclosure"], ["playbook_matcher", "course_chapter_mapper"]),
        ],
        "blocking_conditions": [
            "Situation type is unknown.",
            "Primary source disclosure is missing.",
        ],
        "notes": GUARDRAILS,
    },
}


def normalize_situation_type(situation_type: str | None) -> str:
    key = (situation_type or "unknown").strip().lower()
    key = ALIASES.get(key, key)
    return key if key in COURSE_DOCUMENTATION_MAPS else "unknown"


def get_course_documentation_map(situation_type: str | None) -> dict[str, Any]:
    return deepcopy(COURSE_DOCUMENTATION_MAPS[normalize_situation_type(situation_type)])


def get_relevant_course_chapters(situation_type: str | None) -> list[dict[str, str]]:
    return get_course_documentation_map(situation_type)["relevant_course_chapters"]


def get_required_documents(situation_type: str | None) -> list[dict[str, str]]:
    return get_course_documentation_map(situation_type)["required_documents"]


def get_required_information(situation_type: str | None) -> list[dict[str, Any]]:
    return get_course_documentation_map(situation_type)["required_information"]


def get_course_checklist(situation_type: str | None) -> list[dict[str, Any]]:
    return get_course_documentation_map(situation_type)["checklist_items"]
