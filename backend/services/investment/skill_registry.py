from __future__ import annotations

from copy import deepcopy
from typing import Any

from backend.services.investment.course_documentation_map import normalize_situation_type


SKILL_GROUPS = [
    "Course Intelligence",
    "SEC Evidence",
    "Document Intelligence",
    "Transaction Terms",
    "Situation-Specific Skills",
    "Documentation Quality",
    "Quality / Guardrails",
]


def _skill(
    skill_key: str,
    label: str,
    group: str,
    description: str,
    implemented: bool,
    required_for: list[str],
    outputs: list[str],
    dependencies: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "skill_key": skill_key,
        "label": label,
        "group": group,
        "description": description,
        "implemented": implemented,
        "required_for_situation_types": required_for,
        "outputs": outputs,
        "dependencies": dependencies or [],
    }


SKILLS = [
    _skill("course_chapter_mapper", "Course Chapter Mapper", "Course Intelligence", "Maps situation types to compact course chapter references.", True, ["all"], ["course_chapters"]),
    _skill("playbook_matcher", "Playbook Matcher", "Course Intelligence", "Selects the relevant playbook for a situation type.", True, ["all"], ["applicable_playbooks"]),
    _skill("checklist_builder", "Checklist Builder", "Course Intelligence", "Builds deterministic checklist items from course metadata.", True, ["all"], ["checklist_items"]),
    _skill("course_question_mapper", "Course Question Mapper", "Course Intelligence", "Maps playbooks to safe course questions without long course text.", False, ["all"], ["course_questions"], ["course_chapter_mapper"]),
    _skill("sec_filing_locator", "SEC Filing Locator", "SEC Evidence", "Locates official SEC filing references from stored metadata.", True, ["all"], ["sec_links"]),
    _skill("sec_exhibit_index_reader", "SEC Exhibit Index Reader", "SEC Evidence", "Reads exhibit indexes and identifies likely source documents.", False, ["merger_arbitrage", "tender_offer", "spin_off", "rights_offering"], ["exhibit_targets"], ["sec_filing_locator"]),
    _skill("sec_document_classifier", "SEC Document Classifier", "SEC Evidence", "Classifies SEC document metadata into known document types.", True, ["all"], ["document_classification"]),
    _skill("related_filing_finder", "Related Filing Finder", "SEC Evidence", "Finds related filings across accession history or amendments.", False, ["all"], ["related_filings"], ["sec_filing_locator"]),
    _skill("found_document_matcher", "Found Document Matcher", "Document Intelligence", "Matches stored evidence links to expected document keys.", True, ["all"], ["found_documents"]),
    _skill("missing_document_detector", "Missing Document Detector", "Document Intelligence", "Identifies required and recommended documents not found in metadata.", True, ["all"], ["missing_documents"], ["found_document_matcher"]),
    _skill("document_importance_assigner", "Document Importance Assigner", "Document Intelligence", "Assigns critical/high/medium/low importance to expected documents.", True, ["all"], ["document_importance"]),
    _skill("source_confidence_assessor", "Source Confidence Assessor", "Document Intelligence", "Assesses source provenance and confidence for manual review.", False, ["all"], ["source_confidence"]),
    _skill("consideration_extractor", "Consideration Extractor", "Transaction Terms", "Extracts consideration terms from official documents when deterministic.", False, ["merger_arbitrage"], ["consideration_terms"], ["sec_exhibit_index_reader"]),
    _skill("timeline_extractor", "Timeline Extractor", "Transaction Terms", "Extracts key dates when deterministic source data is available.", False, ["merger_arbitrage", "tender_offer", "spin_off", "bankruptcy", "liquidation", "proxy_fight"], ["timeline_items"]),
    _skill("condition_extractor", "Condition Extractor", "Transaction Terms", "Extracts closing, approval, or process conditions when deterministic.", False, ["merger_arbitrage", "spin_off", "bankruptcy", "liquidation"], ["condition_items"]),
    _skill("risk_factor_extractor", "Risk Factor Extractor", "Transaction Terms", "Extracts explicit risk factors from source documents.", False, ["all"], ["risk_factors"]),
    _skill("tender_offer_terms_skill", "Tender Offer Terms Skill", "Situation-Specific Skills", "Maps tender offer size, price, proration, expiration, and withdrawal terms.", False, ["tender_offer"], ["tender_terms"], ["sec_exhibit_index_reader"]),
    _skill("schedule_14d9_finder", "Schedule 14D-9 Finder", "Situation-Specific Skills", "Identifies target board response materials.", False, ["merger_arbitrage"], ["target_response_documents"], ["sec_filing_locator"]),
    _skill("form_10_analyzer", "Form 10 Analyzer", "Situation-Specific Skills", "Analyzes Form 10 metadata and required spin-off sections.", False, ["spin_off"], ["spin_off_sections"], ["sec_document_classifier"]),
    _skill("liquidation_plan_analyzer", "Liquidation Plan Analyzer", "Situation-Specific Skills", "Maps liquidation, bankruptcy, or restructuring plan terms.", False, ["bankruptcy", "liquidation"], ["plan_terms"], ["sec_document_classifier"]),
    _skill("rights_offering_terms_skill", "Rights Offering Terms Skill", "Situation-Specific Skills", "Maps subscription rights, oversubscription, and offer timing.", False, ["rights_offering"], ["rights_terms"], ["sec_document_classifier"]),
    _skill("proxy_materials_analyzer", "Proxy Materials Analyzer", "Situation-Specific Skills", "Maps proxy materials, vote items, slates, and solicitation context.", False, ["proxy_fight"], ["proxy_terms"], ["sec_document_classifier"]),
    _skill("readiness_scorer", "Readiness Scorer", "Documentation Quality", "Scores documentation readiness for manual review or promotion.", True, ["all"], ["readiness_score"], ["missing_document_detector"]),
    _skill("next_best_action_generator", "Next Best Action Generator", "Documentation Quality", "Generates deterministic next manual actions.", True, ["all"], ["manual_actions"], ["missing_document_detector"]),
    _skill("guardrail_checker", "Guardrail Checker", "Quality / Guardrails", "Checks that outputs remain metadata-only and avoid recommendation language.", True, ["all"], ["guardrail_status"]),
    _skill("misclassification_detector", "Misclassification Detector", "Quality / Guardrails", "Flags possible mismatch between form, situation type, and playbook.", False, ["all"], ["classification_warnings"], ["playbook_matcher"]),
]


def get_skill_registry() -> dict[str, Any]:
    return {"groups": deepcopy(SKILL_GROUPS), "skills": deepcopy(SKILLS)}


def _applies_to(skill: dict[str, Any], situation_type: str) -> bool:
    required_for = skill.get("required_for_situation_types") or []
    return "all" in required_for or situation_type in required_for


def get_skills_for_situation_type(situation_type: str | None) -> list[dict[str, Any]]:
    key = normalize_situation_type(situation_type)
    return deepcopy([skill for skill in SKILLS if _applies_to(skill, key)])


def get_missing_skills_for_situation_type(situation_type: str | None) -> list[dict[str, Any]]:
    return [skill for skill in get_skills_for_situation_type(situation_type) if not skill["implemented"]]


def get_skill_requirements_map(situation_type: str | None) -> dict[str, Any]:
    key = normalize_situation_type(situation_type)
    skills = get_skills_for_situation_type(key)
    implemented = [skill for skill in skills if skill["implemented"]]
    missing = [skill for skill in skills if not skill["implemented"]]
    return {
        "situation_type": key,
        "required_skills": skills,
        "implemented_skills": implemented,
        "missing_skills": missing,
        "summary": {
            "required_count": len(skills),
            "implemented_count": len(implemented),
            "missing_count": len(missing),
        },
        "guardrails": [
            "Skill Registry describes capabilities; it does not run agents.",
            "Missing skills are product and process gaps, not investment conclusions.",
            "Implemented=true is conservative and only reflects existing deterministic support.",
        ],
    }
