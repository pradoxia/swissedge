import json
import logging
from pathlib import Path

from backend.services.ai_client import complete_with_usage
from backend.services.investment.sources.base import Filing
from backend.services.investment.course_index import (
    get_chapter_for_situation,
    get_checklist_for_situation,
    get_playbook_for_situation,
)

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "situation_evaluator.txt"
_DISCLAIMER = (
    "\n\n⚠️ DISCLAIMER: This analysis is for informational and educational purposes only. "
    "It is NOT personalized financial advice. Always do your own research before "
    "making investment decisions. Past special situations do not guarantee future results."
)


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


async def evaluate_situation(filing: Filing) -> tuple[dict, dict]:
    """
    Evaluate a filing using the course methodology.
    Returns (evaluation_dict, usage_dict).
    usage_dict keys: provider, model, input_tokens, output_tokens.
    evaluation_dict always includes a disclaimer.
    """
    situation_type = filing.situation_type or "unknown"
    chapter_info = get_chapter_for_situation(situation_type)
    checklist = get_checklist_for_situation(situation_type)
    playbook = get_playbook_for_situation(situation_type)

    checklist_text = "\n".join(f"- {item}" for item in checklist) if checklist else "No checklist available."
    playbook_text = "\n".join(playbook) if playbook else "No playbook available."

    template = _load_prompt()
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
