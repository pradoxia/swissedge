import pytest
from backend.services.investment.sources.base import Filing
from backend.services.investment.routing_engine import (
    detect_form_type,
    detect_situation_type,
    route_playbook,
    check_scope,
    build_routing_decision,
)


def test_detect_form_type_sc_to_t():
    filing = Filing(
        company="Target Corp",
        ticker="TGT",
        filing_type="SC TO-T",
        date="2026-04-29",
        url="https://sec.gov/...",
        summary="Tender offer by Acquirer Inc",
    )
    assert detect_form_type(filing) == "SC TO-T"


def test_detect_form_type_sc_to_i():
    filing = Filing(
        company="Company Inc",
        ticker="CO",
        filing_type="SC TO-I",
        date="2026-04-29",
        url="https://sec.gov/...",
        summary="Self-tender offer",
    )
    assert detect_form_type(filing) == "SC TO-I"


def test_detect_form_type_form_10():
    filing = Filing(
        company="SpinCo",
        ticker=None,
        filing_type="Form 10",
        date="2026-04-29",
        url="https://sec.gov/...",
        summary="Spinco registration",
    )
    assert detect_form_type(filing) == "Form 10"


def test_detect_situation_type_sc_to_t():
    filing = Filing(
        company="Target Corp",
        ticker="TGT",
        filing_type="SC TO-T",
        date="2026-04-29",
        url="https://sec.gov/...",
        summary="Tender offer by Acquirer Inc",
    )
    result = detect_situation_type(filing)
    assert result["situation_type"] == "merger_arbitrage"
    assert result["subtype"] == "acquisition_tender_offer"
    assert result["detection_confidence"] == "HIGH"


def test_detect_situation_type_sc_to_i():
    filing = Filing(
        company="Company Inc",
        ticker="CO",
        filing_type="SC TO-I",
        date="2026-04-29",
        url="https://sec.gov/...",
        summary="Self-tender offer",
    )
    result = detect_situation_type(filing)
    assert result["situation_type"] == "tender_offer"
    assert result["subtype"] == "self_tender"
    assert result["detection_confidence"] == "HIGH"


def test_detect_situation_type_form_10():
    filing = Filing(
        company="SpinCo",
        ticker=None,
        filing_type="Form 10",
        date="2026-04-29",
        url="https://sec.gov/...",
        summary="Spinco registration statement",
    )
    result = detect_situation_type(filing)
    assert result["situation_type"] == "spin_off"
    assert result["subtype"] == "standard_spin_off"
    assert result["detection_confidence"] == "HIGH"


def test_detect_situation_type_plan_of_dissolution():
    filing = Filing(
        company="Liquidating Corp",
        ticker="LIQ",
        filing_type="8-K",
        date="2026-04-29",
        url="https://sec.gov/...",
        summary="Company announces plan of dissolution and liquidation",
    )
    result = detect_situation_type(filing)
    assert result["situation_type"] == "bankruptcy"
    assert result["subtype"] == "voluntary_liquidation"
    assert result["detection_confidence"] == "HIGH"


def test_detect_situation_type_unknown():
    filing = Filing(
        company="Unknown Corp",
        ticker="UNK",
        filing_type="10-Q",
        date="2026-04-29",
        url="https://sec.gov/...",
        summary="Quarterly report",
    )
    result = detect_situation_type(filing)
    assert result["situation_type"] == "unknown"
    assert result["detection_confidence"] == "LOW"


def test_route_playbook_merger_arbitrage():
    result = route_playbook("merger_arbitrage", "acquisition_tender_offer", "SC TO-T")
    assert result["selected_playbook"] == "merger_arbitrage.md"
    assert result["routed_to"] is None


def test_route_playbook_tender_offer():
    result = route_playbook("tender_offer", "self_tender", "SC TO-I")
    assert result["selected_playbook"] == "tender_offer.md"
    assert result["routed_to"] is None


def test_route_playbook_spin_off():
    result = route_playbook("spin_off", "standard_spin_off", "Form 10")
    assert result["selected_playbook"] == "spin_off.md"
    assert result["routed_to"] is None


def test_route_playbook_bankruptcy():
    result = route_playbook("bankruptcy", "voluntary_liquidation", "8-K")
    assert result["selected_playbook"] == "bankruptcy.md"
    assert result["routed_to"] is None


def test_route_playbook_merger_gateway():
    result = route_playbook("merger", "definitive_merger_proxy", "DEFM14A")
    assert result["selected_playbook"] == "merger.md"
    assert result["routed_to"] == "merger_arbitrage.md"


def test_check_scope_merger_arbitrage():
    result = check_scope("merger_arbitrage", "acquisition_tender_offer")
    assert result["playbook_status"] == "evaluator_ready"
    assert result["out_of_scope_reason"] is None


def test_check_scope_spin_off():
    result = check_scope("spin_off", "standard_spin_off")
    assert result["playbook_status"] == "partial"


def test_check_scope_proxy_fight():
    result = check_scope("proxy_fight", "activist_campaign")
    assert result["playbook_status"] == "detection_only"


def test_check_scope_unknown():
    result = check_scope("unknown", None)
    assert result["playbook_status"] == "out_of_scope"


def test_build_routing_decision_sc_to_t():
    filing = Filing(
        company="Target Corp",
        ticker="TGT",
        filing_type="SC TO-T",
        date="2026-04-29",
        url="https://sec.gov/...",
        summary="Tender offer by Acquirer Inc",
    )
    result = build_routing_decision(filing)
    assert result["detected_form_type"] == "SC TO-T"
    assert result["situation_type"] == "merger_arbitrage"
    assert result["selected_playbook"] == "merger_arbitrage.md"
    assert result["playbook_status"] == "evaluator_ready"
    assert result["detection_confidence"] == "HIGH"


def test_build_routing_decision_sc_to_i():
    filing = Filing(
        company="Company Inc",
        ticker="CO",
        filing_type="SC TO-I",
        date="2026-04-29",
        url="https://sec.gov/...",
        summary="Self-tender offer",
    )
    result = build_routing_decision(filing)
    assert result["detected_form_type"] == "SC TO-I"
    assert result["situation_type"] == "tender_offer"
    assert result["selected_playbook"] == "tender_offer.md"
    assert result["playbook_status"] == "partial"
