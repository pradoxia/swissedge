import re
import yaml
from pathlib import Path

_RULES_PATH = Path("config/safety_rules.yaml")

_PHONE_PATTERN = re.compile(r"\b(\+?\d[\d\s\-().]{7,}\d)\b")
_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_IBAN_PATTERN = re.compile(r"\b[A-Z]{2}\d{2}[\d\s]{10,30}\b")
_ADDRESS_PATTERN = re.compile(
    r"\b(strasse|gasse|weg|platz|allee|avenue|rue|via|strada|chemin)\b",
    re.IGNORECASE,
)


def _load_rules() -> dict:
    if _RULES_PATH.exists():
        return yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))
    return {}


def validate_outgoing_message(text: str) -> tuple[bool, list[str]]:
    """
    Check that an outgoing Telegram message does not violate safety rules.
    Returns (is_safe, list_of_violations).
    """
    violations: list[str] = []

    if _PHONE_PATTERN.search(text):
        violations.append("Message contains a phone number. Remove before sending.")

    if _EMAIL_PATTERN.search(text):
        violations.append("Message contains an email address. Remove before sending.")

    if _IBAN_PATTERN.search(text):
        violations.append("Message contains what looks like a bank account (IBAN). Remove before sending.")

    if _ADDRESS_PATTERN.search(text):
        violations.append("Message may contain a street address. Review before sending.")

    return len(violations) == 0, violations


def check_action_requires_approval(action: str) -> bool:
    """
    Return True if this action requires explicit user approval before execution.
    """
    rules = _load_rules()
    never_without_approval = rules.get("telegram_bot", {}).get("never_without_approval", [])
    return action in never_without_approval


def get_auto_responses() -> dict[str, str]:
    """Return the dict of actions that can be auto-responded without approval."""
    rules = _load_rules()
    auto = rules.get("telegram_bot", {}).get("auto_respond_allowed", [])
    result = {}
    for item in auto:
        if isinstance(item, dict):
            result.update(item)
    return result


def get_investment_disclaimer() -> str:
    rules = _load_rules()
    return rules.get("investment", {}).get(
        "mandatory_disclaimer",
        "⚠️ This is not financial advice. Always do your own research.",
    )
