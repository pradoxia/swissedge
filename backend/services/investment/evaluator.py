import json
import logging
import os
from pathlib import Path

from backend.services.ai_client import complete_with_usage
from backend.services.investment.sources.base import Filing
from backend.services.investment.course_index import (
    get_chapter_for_situation,
    get_checklist_for_situation,
    get_playbook_for_situation,
)

logger = logging.getLogger(__name__)

_PROMPT_V1_PATH = Path(__file__).parent.parent.parent / "prompts" / "situation_evaluator.txt"
_PROMPT_V2_PATH = Path(__file__).parent.parent.parent / "prompts" / "situation_evaluator_v2.txt"
_DISCLAIMER = (
    "\n\n⚠️ DISCLAIMER: This analysis is for informational and educational purposes only. "
    "It is NOT personalized financial advice. Always do your own research before "
    "making investment decisions. Past special situations do not guarantee future results."
)
_DISCLAIMER_V2 = "Este análisis es educativo. No es asesoramiento financiero."


def _get_evaluator_version() -> str:
    """Get evaluator version from environment variable. Default is v1."""
    return os.getenv("EVALUATOR_VERSION", "v1").lower()


def _load_prompt_v1() -> str:
    return _PROMPT_V1_PATH.read_text(encoding="utf-8")


def _load_prompt_v2() -> str:
    return _PROMPT_V2_PATH.read_text(encoding="utf-8")


async def evaluate_situation(filing: Filing) -> tuple[dict, dict]:
    """
    Evaluate a filing using the course methodology.
    Returns (evaluation_dict, usage_dict).
    usage_dict keys: provider, model, input_tokens, output_tokens.
    evaluation_dict always includes a disclaimer.
    """
    version = _get_evaluator_version()

    if version == "v2":
        try:
            return await _evaluate_situation_v2(filing)
        except Exception as e:
            logger.warning(f"Evaluator v2 failed for {filing.company}, falling back to v1: {e}")
            # Fall back to v1

    return await _evaluate_situation_v1(filing)


async def _evaluate_situation_v1(filing: Filing) -> tuple[dict, dict]:
    """Original v1 evaluator logic."""
    situation_type = filing.situation_type or "unknown"
    chapter_info = get_chapter_for_situation(situation_type)
    checklist = get_checklist_for_situation(situation_type)
    playbook = get_playbook_for_situation(situation_type)

    checklist_text = "\n".join(f"- {item}" for item in checklist) if checklist else "No checklist available."
    playbook_text = "\n".join(playbook) if playbook else "No playbook available."

    template = _load_prompt_v1()
    prompt = template.format(
        situation_type=situation_type,
        company_name=filing.company,
        filing_type=filing.filing_type,
        filing_summary=filing.summary,
        checklist=checklist_text,
        playbook=playbook_text,
    )

    usage: dict = {}
    try:
        raw, usage = await complete_with_usage(prompt)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
    except json.JSONDecodeError:
        logger.warning("Evaluator returned non-JSON for %s", filing.company)
        result = {
            "checklist_results": [],
            "strengths": [],
            "weaknesses": [],
            "risks": ["Could not parse AI evaluation"],
            "confidence": "LOW",
            "recommendation": "PASS",
            "summary": filing.summary,
        }
    except Exception as e:
        logger.error("Evaluation failed for %s: %s", filing.company, e)
        raise

    result["course_chapter"] = chapter_info.get("chapter")
    result["course_timestamp"] = chapter_info.get("timestamp")
    result["source_urls"] = [filing.url] if filing.url else []
    result["disclaimer"] = _DISCLAIMER.strip()

    return result, usage


async def _evaluate_situation_v2(filing: Filing) -> tuple[dict, dict]:
    """New v2 evaluator with routing engine and evaluation schema."""
    from backend.services.investment.routing_engine import build_routing_decision
    from backend.services.investment.playbook_loader import (
        load_evaluation_schema,
        get_allowed_checks,
        get_prohibited_checks,
        get_situation_rules,
    )

    # Build routing decision
    routing_decision = build_routing_decision(filing)
    situation_type = routing_decision["situation_type"]
    subtype = routing_decision.get("subtype")
    playbook_status = routing_decision["playbook_status"]
    selected_playbook = routing_decision.get("selected_playbook", "unknown")

    # Load evaluation schema
    schema = load_evaluation_schema()

    # Get situation-specific rules
    allowed_checks = get_allowed_checks(situation_type)
    prohibited_checks = get_prohibited_checks(situation_type)
    situation_rules = get_situation_rules(situation_type)
    human_review_triggers = situation_rules.get("human_review_triggers", [])

    # Build playbook context (minimal for now)
    playbook_context = f"Playbook: {selected_playbook}\nStatus: {playbook_status}"

    # Build evidence sources
    evidence_sources = f"Primary filing: {filing.filing_type} dated {filing.date}"

    # Build risk patterns (minimal for now)
    relevant_risk_patterns = "See risk_patterns.md for full risk library"

    # Format routing decision for prompt
    routing_text = json.dumps(routing_decision, indent=2)

    # Build prompt
    template = _load_prompt_v2()
    prompt = template.format(
        company_name=filing.company,
        ticker=filing.ticker or "N/A",
        filing_type=filing.filing_type,
        filing_date=filing.date,
        filing_url=filing.url or "N/A",
        filing_summary=filing.summary,
        routing_decision=routing_text,
        situation_type=situation_type,
        subtype=subtype or "N/A",
        playbook_status=playbook_status,
        selected_playbook=selected_playbook,
        detection_confidence=routing_decision.get("detection_confidence", "UNKNOWN"),
        allowed_checks="\n".join(f"- {c}" for c in allowed_checks) if allowed_checks else "None specified",
        prohibited_checks="\n".join(f"- {c}" for c in prohibited_checks) if prohibited_checks else "None specified",
        human_review_triggers="\n".join(f"- {t}" for t in human_review_triggers) if human_review_triggers else "None specified",
        relevant_risk_patterns=relevant_risk_patterns,
        playbook_context=playbook_context,
        evidence_sources=evidence_sources,
    )

    # Call AI
    usage: dict = {}
    raw, usage = await complete_with_usage(prompt)
    raw = raw.strip()

    # Parse JSON response - handle markdown code blocks and extra text
    if raw.startswith("```"):
        # Extract content between code fences
        parts = raw.split("```")
        if len(parts) >= 2:
            raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]

    # Find JSON object boundaries if there's extra text
    raw = raw.strip()
    if not raw.startswith("{"):
        # Look for first { to handle preamble text
        start = raw.find("{")
        if start != -1:
            raw = raw[start:]

    if not raw.endswith("}"):
        # Look for last } to handle trailing text
        end = raw.rfind("}")
        if end != -1:
            raw = raw[:end + 1]

    result = json.loads(raw.strip())

    # Normalize schema
    result = _normalize_v2_result(result, filing, routing_decision)

    # Prohibited inference guard
    result = _check_prohibited_inferences(result)

    return result, usage


def _normalize_v2_result(result: dict, filing: Filing, routing_decision: dict) -> dict:
    """Ensure v2 result has all required schema fields."""
    normalized = {
        "situation_type": result.get("situation_type", routing_decision["situation_type"]),
        "subtype": result.get("subtype", routing_decision.get("subtype")),
        "playbook_status": result.get("playbook_status", routing_decision["playbook_status"]),
        "evaluator_confidence": result.get("evaluator_confidence", "INSUFFICIENT"),
        "recommendation": result.get("recommendation", "HUMAN_REVIEW_REQUIRED"),
        "summary": result.get("summary", filing.summary),
        "routing_decision": result.get("routing_decision", routing_decision),
        "evidence_sources": result.get("evidence_sources", []),
        "checklist_results": result.get("checklist_results", []),
        "risk_flags": result.get("risk_flags", []),
        "human_review_required": result.get("human_review_required", []),
        "prohibited_inferences_detected": result.get("prohibited_inferences_detected", []),
        "missing_documents": result.get("missing_documents", []),
        "latest_amendment_check": result.get("latest_amendment_check", {
            "checked": False,
            "latest_document_date": None,
            "latest_document_type": None,
            "amendment_found": False,
            "stale_data_risk": "UNKNOWN"
        }),
        "scope_notes": result.get("scope_notes", ""),
        "disclaimer": result.get("disclaimer", _DISCLAIMER_V2),
    }

    # Ensure disclaimer is exactly correct
    if normalized["disclaimer"] != _DISCLAIMER_V2:
        normalized["disclaimer"] = _DISCLAIMER_V2

    return normalized


def _check_prohibited_inferences(result: dict) -> dict:
    """Check for prohibited inferences in the result and flag them."""
    # Phrases that indicate the evaluator is PROVIDING a prohibited value (not just mentioning it)
    fabrication_indicators = [
        ("i estimate", "nav"),
        ("i calculate", "nav"),
        ("liquidation nav at", None),
        ("nav of", None),
        ("sum-of-parts", "suggests"),
        ("sum-of-parts", "indicates"),
        ("valuation suggests", None),
        ("institutional mandate", "analysis indicates"),
        ("institutional mandate", "suggests"),
        ("broker deadline is", None),
        ("tax treatment", "is"),
        ("court will", None),
        ("cfius will", None),
        ("cvr probability", "is"),
        ("clearing price", "will be"),
        ("shareholders will vote", None),
        ("participation rate", "will be"),
    ]

    summary_lower = result.get("summary", "").lower()
    scope_notes_lower = result.get("scope_notes", "").lower()
    combined_text = summary_lower + " " + scope_notes_lower

    detected = []
    for indicator in fabrication_indicators:
        if isinstance(indicator, tuple):
            phrase1, phrase2 = indicator
            if phrase2:
                # Both phrases must be present
                if phrase1 in combined_text and phrase2 in combined_text:
                    detected.append(f"{phrase1.replace(' ', '_')}_fabrication")
            else:
                # Single phrase is enough
                if phrase1 in combined_text:
                    detected.append(f"{phrase1.replace(' ', '_')}_fabrication")

    if detected:
        result["prohibited_inferences_detected"] = list(set(
            result.get("prohibited_inferences_detected", []) + detected
        ))

        # Escalate recommendation if not already terminal
        if result["recommendation"] not in ("OUT_OF_SCOPE", "DETECTION_ONLY"):
            result["recommendation"] = "HUMAN_REVIEW_REQUIRED"

    return result
