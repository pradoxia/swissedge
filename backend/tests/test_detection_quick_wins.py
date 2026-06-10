"""Tests for the detection quick-wins sprint.

Covers: 8-K item-code classification, Form 25 / SC 13E3 normalization and
routing, odd-lot keyword detection, amendment-normalized dedupe keys, and the
competition lens derived from SEC public float.
"""

from backend.services.investment.routing_engine import (
    build_routing_decision,
    detect_form_type,
    detect_situation_type,
    extract_8k_item_codes,
)
from backend.services.investment.sec_company_facts import (
    SMALL_COMPANY_PUBLIC_FLOAT_USD,
    build_competition_lens,
)
from backend.services.investment.sec_detection import (
    _is_batch_duplicate,
    _normalize_form,
    build_sec_classification_report,
)
from backend.services.investment.sources.base import Filing
from backend.services.investment.sources.sec_edgar import SECEdgarAdapter, _items_from_src


def _filing(filing_type: str, summary: str = "", **kwargs) -> Filing:
    return Filing(
        company=kwargs.get("company", "Test Corp"),
        ticker=kwargs.get("ticker", "TST"),
        filing_type=filing_type,
        date=kwargs.get("date", "2026-06-09"),
        url=kwargs.get("url", "https://www.sec.gov/Archives/edgar/data/1/000000000126000001/doc.htm"),
        summary=summary,
        cik=kwargs.get("cik", "0000000001"),
        accession_number=kwargs.get("accession_number", "0000000001-26-000001"),
    )


class TestItemCodeExtraction:
    def test_extracts_codes_from_summary(self):
        assert extract_8k_item_codes("8-K filed by X on 2026-06-09. Items: 1.03, 9.01.") == ["1.03", "9.01"]

    def test_no_items_returns_empty(self):
        assert extract_8k_item_codes("8-K filed by X.") == []
        assert extract_8k_item_codes(None) == []

    def test_items_from_efts_src(self):
        assert _items_from_src({"items": ["1.03", "9.01"]}) == ["1.03", "9.01"]
        assert _items_from_src({"items": "item 3.01"}) == ["3.01"]
        assert _items_from_src({}) == []
        assert _items_from_src({"items": 42}) == []


class TestItemCodeClassification:
    def test_item_1_03_is_high_confidence_bankruptcy(self):
        decision = detect_situation_type(_filing("8-K", "8-K filed. Items: 1.03."))
        assert decision["situation_type"] == "bankruptcy"
        assert decision["detection_confidence"] == "HIGH"
        assert decision["reason_code"] == "item_1_03_bankruptcy"

    def test_item_3_01_is_delisting(self):
        decision = detect_situation_type(_filing("8-K", "8-K filed. Items: 3.01."))
        assert decision["situation_type"] == "delisting"
        assert decision["reason_code"] == "item_3_01_delisting"

    def test_item_5_01_is_change_of_control(self):
        decision = detect_situation_type(_filing("8-K", "8-K filed. Items: 5.01."))
        assert decision["situation_type"] == "merger"
        assert decision["subtype"] == "change_of_control"

    def test_item_takes_precedence_over_weak_keywords(self):
        decision = detect_situation_type(_filing("8-K", "restructuring update. Items: 1.03."))
        assert decision["reason_code"] == "item_1_03_bankruptcy"


class TestNewForms:
    def test_sc_13e3_normalizes_and_routes_going_private(self):
        assert detect_form_type(_filing("SC 13E3")) == "13E-3"
        decision = detect_situation_type(_filing("SC 13E3"))
        assert decision["subtype"] == "going_private"
        assert decision["detection_confidence"] == "HIGH"

    def test_form_25_normalizes_and_routes_delisting(self):
        assert detect_form_type(_filing("25-NSE")) == "Form 25"
        decision = detect_situation_type(_filing("25-NSE"))
        assert decision["situation_type"] == "delisting"
        routing = build_routing_decision(_filing("25-NSE"))
        assert routing["playbook_status"] == "detection_only"

    def test_new_forms_are_queried_by_adapter(self):
        assert "SC 13E3" in SECEdgarAdapter.FILING_TYPES
        assert "25-NSE" in SECEdgarAdapter.FILING_TYPES


class TestOddLot:
    def test_odd_lot_keyword_detected(self):
        decision = detect_situation_type(_filing("8-K", "tender offer with odd lot provision"))
        assert decision["subtype"] == "odd_lot_provision"
        assert decision["reason_code"] == "odd_lot_keyword"

    def test_sweeps_configured(self):
        phrases = [phrase for phrase, _forms in SECEdgarAdapter.FULL_TEXT_SWEEPS]
        assert "odd lot" in phrases
        assert "plan of liquidation" in phrases


class TestAmendmentDedupe:
    def test_normalize_form_strips_amendment_suffix(self):
        assert _normalize_form("SC TO-T/A") == "SC TO-T"
        assert _normalize_form("SC TO-T") == "SC TO-T"
        assert _normalize_form(None) == ""

    def test_amendment_is_batch_duplicate_of_parent(self):
        seen: set[str] = set()
        original = _filing("SC TO-T", url="https://www.sec.gov/a", accession_number="acc-1")
        amendment = _filing("SC TO-T/A", url="https://www.sec.gov/b", accession_number="acc-2")
        assert _is_batch_duplicate(original, seen) is False
        assert _is_batch_duplicate(amendment, seen) is True


class TestCandidateOnlyEligibility:
    def test_defm14a_is_candidate_not_strict_creation(self):
        report = build_sec_classification_report(_filing("DEFM14A"))
        assert report["creation_eligible"] is False
        assert report["ignored_reason"] == "outside_strict_creation_allowlist"
        assert report["detected_situation_type"] == "merger"

    def test_sc_14d9_medium_confidence_is_candidate(self):
        report = build_sec_classification_report(_filing("SC 14D9"))
        assert report["creation_eligible"] is False
        assert report["ignored_reason"] == "classification_confidence_not_high"

    def test_strict_allowlist_unchanged(self):
        report = build_sec_classification_report(_filing("SC TO-I"))
        assert report["creation_eligible"] is True


class TestCompetitionLens:
    def test_small_float_flags_low_competition(self):
        lens = build_competition_lens({"public_float_usd": 50_000_000, "as_of": "2026-01-31"})
        assert lens["small_company_flag"] is True
        assert lens["threshold_usd"] == SMALL_COMPANY_PUBLIC_FLOAT_USD
        assert "Not investment advice" in lens["disclaimer"]

    def test_large_float_not_flagged(self):
        lens = build_competition_lens({"public_float_usd": 5_000_000_000})
        assert lens["small_company_flag"] is False

    def test_unknown_stays_unknown(self):
        lens = build_competition_lens(None)
        assert lens["small_company_flag"] is None
        assert lens["status"] == "unknown"
