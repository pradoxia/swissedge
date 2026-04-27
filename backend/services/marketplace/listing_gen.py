import json
import logging
from pathlib import Path

from backend.services.ai_client import complete

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / "listing_generator.txt"


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


async def generate_listing(
    item_description: str,
    brand: str = "",
    condition: str = "Gut",
    category: str = "",
    price: float = 0,
) -> dict:
    """
    Generate a Hochdeutsch listing title and description.
    Returns dict with keys: title, description, category_suggestion.
    """
    template = _load_prompt()
    prompt = (
        template
        .replace("{item_description}", item_description)
        .replace("{brand}", brand or "unbekannt")
        .replace("{condition}", condition)
        .replace("{category}", category or "Diverses")
        .replace("{price}", f"{price:.0f}" if price else "wird noch festgelegt")
    )

    try:
        raw = await complete(prompt)
        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
    except json.JSONDecodeError:
        logger.warning("AI response was not valid JSON, returning raw text")
        result = {
            "title": item_description[:60],
            "description": item_description,
            "category_suggestion": category or "Diverses",
        }
    except Exception as e:
        logger.error("Listing generation failed: %s", e)
        raise

    return result
