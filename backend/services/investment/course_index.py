import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_INDEX_DIR = Path(__file__).parent.parent.parent.parent / "course_index"
_MASTER_INDEX_PATH = _INDEX_DIR / "master_index.json"


def load_master_index() -> dict:
    """Load the master index mapping situation types to chapters."""
    if not _MASTER_INDEX_PATH.exists():
        logger.warning("master_index.json not found. Run scripts/ingest_course.py first.")
        return {}
    with _MASTER_INDEX_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def get_chapter_for_situation(situation_type: str) -> dict:
    """Return primary chapter number and timestamp for a situation type."""
    index = load_master_index()
    entry = index.get(situation_type)
    if not entry:
        return {"chapter": None, "timestamp": None}
    return {
        "chapter": entry.get("primary"),
        "chapters": entry.get("chapters", []),
        "timestamp": entry.get("timestamp"),
    }


def get_checklist_for_situation(situation_type: str) -> list[str]:
    """Load checklist items for the primary chapter of a situation type."""
    info = get_chapter_for_situation(situation_type)
    chapter = info.get("chapter")
    if chapter is None:
        return []
    path = _INDEX_DIR / f"chapter_{chapter:02d}_checklist.md"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [l.lstrip("- ").strip() for l in lines if l.strip().startswith("-")]


def get_playbook_for_situation(situation_type: str) -> list[str]:
    """Load playbook steps for the primary chapter of a situation type."""
    info = get_chapter_for_situation(situation_type)
    chapter = info.get("chapter")
    if chapter is None:
        return []
    path = _INDEX_DIR / f"chapter_{chapter:02d}_playbook.md"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


def get_summary_for_situation(situation_type: str) -> str:
    """Load the chapter summary for a situation type."""
    info = get_chapter_for_situation(situation_type)
    chapter = info.get("chapter")
    if chapter is None:
        return ""
    path = _INDEX_DIR / f"chapter_{chapter:02d}_summary.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
