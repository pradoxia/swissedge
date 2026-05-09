import json
from pathlib import Path
from backend.services.investment.sources.base import Filing
from backend.services.investment.routing_engine import build_routing_decision


def load_shadow_fixtures():
    """Load shadow test fixtures from JSON file."""
    fixtures_path = Path(__file__).parent / "fixtures" / "evaluator_v2_shadow_cases.json"
    with fixtures_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data["test_cases"]


def test_fixtures_load():
    """Test that shadow fixtures load correctly."""
    fixtures = load_shadow_fixtures()
    assert len(fixtures) == 5
    assert all("id" in f for f in fixtures)
    assert all("filing" in f for f in fixtures)
    assert all("expected_routing" in f for f in fixtures)
    assert all("expected_behavior" in f for f in fixtures)


def test_cash_merger_acquisition_tender_routing():
    """Test routing for cash merger via acquisition tender (SC TO-T)."""
    fixtures = load_shadow_fixtures()
    case = next(f for f in fixtures if f["id"] == "cash_merger_acquisition_tender")

    filing = Filing(**case["filing"])
    routing = build_routing_decision(filing)

    assert routing["situation_type"] == case["expected_routing"]["situation_type"]
    assert routing["subtype"] == case["expected_routing"]["subtype"]
    assert routing["selected_playbook"] == case["expected_routing"]["selected_playbook"]
    assert routing["playbook_status"] == case["expected_routing"]["playbook_status"]
    assert routing["detection_confidence"] == case["expected_routing"]["detection_confidence"]


def test_self_tender_fixed_price_routing():
    """Test routing for self-tender offer (SC TO-I)."""
    fixtures = load_shadow_fixtures()
    case = next(f for f in fixtures if f["id"] == "self_tender_fixed_price")

    filing = Filing(**case["filing"])
    routing = build_routing_decision(filing)

    assert routing["situation_type"] == case["expected_routing"]["situation_type"]
    assert routing["subtype"] == case["expected_routing"]["subtype"]
    assert routing["selected_playbook"] == case["expected_routing"]["selected_playbook"]
    assert routing["playbook_status"] == case["expected_routing"]["playbook_status"]
    assert routing["detection_confidence"] == case["expected_routing"]["detection_confidence"]


def test_standard_spin_off_routing():
    """Test routing for standard spin-off (Form 10)."""
    fixtures = load_shadow_fixtures()
    case = next(f for f in fixtures if f["id"] == "standard_spin_off")

    filing = Filing(**case["filing"])
    routing = build_routing_decision(filing)

    assert routing["situation_type"] == case["expected_routing"]["situation_type"]
    assert routing["subtype"] == case["expected_routing"]["subtype"]
    assert routing["selected_playbook"] == case["expected_routing"]["selected_playbook"]
    assert routing["playbook_status"] == case["expected_routing"]["playbook_status"]
    assert routing["detection_confidence"] == case["expected_routing"]["detection_confidence"]


def test_voluntary_liquidation_routing():
    """Test routing for voluntary liquidation (8-K dissolution)."""
    fixtures = load_shadow_fixtures()
    case = next(f for f in fixtures if f["id"] == "voluntary_liquidation")

    filing = Filing(**case["filing"])
    routing = build_routing_decision(filing)

    assert routing["situation_type"] == case["expected_routing"]["situation_type"]
    assert routing["subtype"] == case["expected_routing"]["subtype"]
    assert routing["selected_playbook"] == case["expected_routing"]["selected_playbook"]
    assert routing["playbook_status"] == case["expected_routing"]["playbook_status"]
    assert routing["detection_confidence"] == case["expected_routing"]["detection_confidence"]


def test_activist_proxy_fight_routing():
    """Test routing for activist proxy fight (SC 13D)."""
    fixtures = load_shadow_fixtures()
    case = next(f for f in fixtures if f["id"] == "activist_proxy_fight")

    filing = Filing(**case["filing"])
    routing = build_routing_decision(filing)

    assert routing["situation_type"] == case["expected_routing"]["situation_type"]
    assert routing["subtype"] == case["expected_routing"]["subtype"]
    assert routing["selected_playbook"] == case["expected_routing"]["selected_playbook"]
    assert routing["playbook_status"] == case["expected_routing"]["playbook_status"]
    assert routing["detection_confidence"] == case["expected_routing"]["detection_confidence"]
