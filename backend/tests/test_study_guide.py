"""W3 tests — Study Guide real chapter mapping from course_index."""

from __future__ import annotations

import json
from pathlib import Path

from backend.services.investment.study_guide import (
    build_study_guide_map,
    get_study_guide_for_type,
)


def _make_index(tmp_path: Path) -> Path:
    (tmp_path / "master_index.json").write_text(json.dumps({
        "merger_arbitrage": {"chapters": [5, 6, 7], "primary": 5, "timestamp": "10:00"},
        "spin_off": {"chapters": [3], "primary": 3, "timestamp": "02:15"},
    }), encoding="utf-8")
    (tmp_path / "chapter_05_summary.md").write_text(
        "Chapter 5 covers the merger arbitrage process in depth. " * 10, encoding="utf-8"
    )
    (tmp_path / "chapter_06_summary.md").write_text("Chapter 6 deal documents.", encoding="utf-8")
    # chapter 7 summary intentionally missing
    (tmp_path / "chapter_03_summary.md").write_text("Chapter 3 spin-off mechanics.", encoding="utf-8")
    return tmp_path


def test_mapped_type_returns_real_chapters(tmp_path):
    payload = build_study_guide_map(_make_index(tmp_path))
    ma = payload["situation_types"]["merger_arbitrage"]

    assert [c["chapter_number"] for c in ma["core"]] == [5]
    assert sorted(c["chapter_number"] for c in ma["supporting"]) == [6, 7]
    assert ma["gaps"] == []

    primary = ma["core"][0]
    assert primary["chapter_title"] == "Chapter 5"
    assert "10:00" in primary["concept_label"]
    assert "merger arbitrage process" in primary["description"]
    assert primary["file_path"] == "course_index/chapter_05_summary.md"


def test_missing_summary_file_is_explicit_not_invented(tmp_path):
    payload = build_study_guide_map(_make_index(tmp_path))
    ma = payload["situation_types"]["merger_arbitrage"]
    ch7 = next(c for c in ma["supporting"] if c["chapter_number"] == 7)
    assert ch7["file_path"] is None
    assert "not found" in ch7["description"]


def test_unmapped_type_is_gap_never_guidance(tmp_path):
    payload = build_study_guide_map(_make_index(tmp_path))
    tender = payload["situation_types"]["tender_offer"]
    assert tender["core"] == []
    assert tender["supporting"] == []
    assert len(tender["gaps"]) == 1
    assert "Dani validation" in tender["gaps"][0]["annotation_note"]


def test_missing_master_index_reports_warning(tmp_path):
    payload = build_study_guide_map(tmp_path)  # empty dir
    assert any("not found" in w for w in payload["warnings"])
    assert payload["situation_types"]["merger_arbitrage"]["core"] == []


def test_get_for_type_normalizes_and_flags_mapped(tmp_path):
    index = _make_index(tmp_path)
    mapped = get_study_guide_for_type("  Merger_Arbitrage ", index)
    assert mapped["mapped"] is True
    assert mapped["situation_type"] == "merger_arbitrage"

    unmapped = get_study_guide_for_type("delisting", index)
    assert unmapped["mapped"] is False
    assert unmapped["mapping"]["gaps"]


def test_guardrails_always_present(tmp_path):
    payload = build_study_guide_map(_make_index(tmp_path))
    assert any("nothing is invented" in g for g in payload["guardrails"])
    assert any("not evidence" in g for g in payload["guardrails"])
