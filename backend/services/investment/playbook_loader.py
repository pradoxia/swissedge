import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PLAYBOOKS_DIR = Path(__file__).parent.parent.parent.parent / "course_index" / "playbooks"
_EVALUATION_SCHEMA_PATH = _PLAYBOOKS_DIR / "evaluation_schema.json"


def load_evaluation_schema() -> dict:
    """Load and validate evaluation_schema.json."""
    if not _EVALUATION_SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"evaluation_schema.json not found at {_EVALUATION_SCHEMA_PATH}. "
            "Run scripts/ingest_course.py to generate global artifacts."
        )

    with _EVALUATION_SCHEMA_PATH.open(encoding="utf-8") as f:
        schema = json.load(f)

    required_keys = ["schema_version", "enumerations", "situation_rules", "sample_empty_output"]
    missing = [k for k in required_keys if k not in schema]
    if missing:
        logger.warning(f"evaluation_schema.json missing keys: {missing}")

    return schema


def get_situation_rules(situation_type: str) -> dict:
    """Get situation-specific rules from evaluation_schema.json."""
    schema = load_evaluation_schema()
    return schema.get("situation_rules", {}).get(situation_type, {})


def get_allowed_checks(situation_type: str) -> list:
    """Get allowed evaluator checks for a situation type."""
    rules = get_situation_rules(situation_type)
    return rules.get("allowed_checks", [])


def get_prohibited_checks(situation_type: str) -> list:
    """Get prohibited evaluator checks for a situation type."""
    rules = get_situation_rules(situation_type)
    return rules.get("prohibited_checks", [])


def get_default_playbook_status(situation_type: str) -> str | None:
    """Get default playbook status for a situation type."""
    rules = get_situation_rules(situation_type)
    return rules.get("default_playbook_status")


def get_default_recommendation_if_detection_only(situation_type: str) -> str | None:
    """Get default recommendation for detection-only playbooks."""
    rules = get_situation_rules(situation_type)
    return rules.get("default_recommendation_if_detection_only")


def load_artifact_text(name: str) -> str:
    """Load a global artifact markdown file by name.

    Args:
        name: One of: taxonomy, source_map, risk_patterns, global_checklist

    Returns:
        Full text content of the artifact file.

    Raises:
        FileNotFoundError: If artifact file does not exist.
        ValueError: If name is not a recognized artifact.
    """
    allowed = {"taxonomy", "source_map", "risk_patterns", "global_checklist"}
    if name not in allowed:
        raise ValueError(f"Unknown artifact '{name}'. Allowed: {allowed}")

    path = _PLAYBOOKS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"Artifact {name}.md not found at {path}. "
            "Run scripts/ingest_course.py to generate global artifacts."
        )

    return path.read_text(encoding="utf-8")
