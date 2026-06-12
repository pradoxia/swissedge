"""W3 — Study Guide real chapter mapping served from course_index.

Builds situation-type -> course-chapter references using ONLY real processed
course data (``course_index/master_index.json`` + per-chapter summaries).

Guardrails:
- No invented mappings: types absent from master_index are returned as explicit
  gaps ("not mapped"), never as guidance.
- Chapter descriptions are excerpts of the real chapter summaries.
- Educational references only; never evidence, verification, or advice.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_INDEX_DIR = Path(__file__).resolve().parents[3] / "course_index"
_EXCERPT_CHARS = 260

# Situation types the product can detect today. Types missing from
# master_index.json are surfaced as explicit gaps, not guesses.
KNOWN_SITUATION_TYPES = [
    "merger_arbitrage",
    "merger",
    "tender_offer",
    "spin_off",
    "bankruptcy",
    "proxy_fight",
    "rights_offering",
    "delisting",
]

_GAP_NOTES = {
    "tender_offer": (
        "master_index.json does not map chapters for self-tenders yet. "
        "Pending Dani validation before any mapping is shown."
    ),
    "proxy_fight": "The processed course index does not map chapters for proxy fights.",
    "rights_offering": "The processed course index does not map chapters for rights offerings.",
    "delisting": "The processed course index does not map chapters for delistings.",
}


def _summary_excerpt(index_dir: Path, chapter: int) -> str | None:
    path = index_dir / f"chapter_{chapter:02d}_summary.md"
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    text = re.sub(r"\s+", " ", text)
    if len(text) <= _EXCERPT_CHARS:
        return text
    return text[:_EXCERPT_CHARS].rsplit(" ", 1)[0] + "…"


def _chapter_reference(
    index_dir: Path,
    chapter: int,
    *,
    situation_type: str,
    primary: bool,
    timestamp: str | None,
) -> dict[str, Any]:
    excerpt = _summary_excerpt(index_dir, chapter)
    summary_file = f"course_index/chapter_{chapter:02d}_summary.md"
    concept = "Primary course reference" if primary else "Related course chapter"
    if primary and timestamp:
        concept = f"Primary course reference (starts at {timestamp})"
    return {
        "chapter_number": chapter,
        "chapter_title": f"Chapter {chapter}",
        "concept_label": f"{concept} for {situation_type.replace('_', ' ')}",
        "description": excerpt or "Chapter summary file not found in course_index.",
        "file_path": summary_file if excerpt else None,
    }


def build_study_guide_map(index_dir: Path | None = None) -> dict[str, Any]:
    """Return the full situation-type -> mapping payload (shim-compatible shape)."""
    base = index_dir or _DEFAULT_INDEX_DIR
    master_path = base / "master_index.json"
    mappings: dict[str, Any] = {}
    master: dict[str, Any] = {}
    warnings: list[str] = []

    if master_path.exists():
        try:
            loaded = json.loads(master_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                master = loaded
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append(f"master_index.json could not be read: {exc}")
    else:
        warnings.append("master_index.json not found; all situation types reported as unmapped.")

    for situation_type in sorted(set(KNOWN_SITUATION_TYPES) | set(master.keys())):
        entry = master.get(situation_type)
        if isinstance(entry, dict) and entry.get("chapters"):
            chapters = [int(c) for c in entry.get("chapters") or [] if str(c).isdigit() or isinstance(c, int)]
            primary = entry.get("primary")
            primary = int(primary) if primary is not None else (chapters[0] if chapters else None)
            timestamp = entry.get("timestamp") if isinstance(entry.get("timestamp"), str) else None
            core = [
                _chapter_reference(base, c, situation_type=situation_type, primary=True, timestamp=timestamp)
                for c in chapters
                if c == primary
            ]
            supporting = [
                _chapter_reference(base, c, situation_type=situation_type, primary=False, timestamp=None)
                for c in chapters
                if c != primary
            ]
            mappings[situation_type] = {"core": core, "supporting": supporting, "gaps": []}
        else:
            mappings[situation_type] = {
                "core": [],
                "supporting": [],
                "gaps": [
                    {
                        "concept_label": situation_type.replace("_", " "),
                        "description": "No course chapters are mapped for this situation type in master_index.json.",
                        "closest_chapters": [],
                        "annotation_note": _GAP_NOTES.get(
                            situation_type,
                            "Unmapped situation type. Mapping requires real course coverage and Dani validation.",
                        ),
                    }
                ],
            }

    return {
        "source": "course_index/master_index.json",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "warnings": warnings,
        "guardrails": [
            "Mappings come only from the processed course index; nothing is invented.",
            "Educational references only — not evidence, verification, or investment advice.",
        ],
        "situation_types": mappings,
    }


def get_study_guide_for_type(situation_type: str, index_dir: Path | None = None) -> dict[str, Any]:
    payload = build_study_guide_map(index_dir)
    normalized = (situation_type or "").strip().lower()
    mapping = payload["situation_types"].get(normalized)
    return {
        "situation_type": normalized,
        "mapped": bool(mapping and mapping.get("core")),
        "mapping": mapping,
        "source": payload["source"],
        "warnings": payload["warnings"],
        "guardrails": payload["guardrails"],
    }
