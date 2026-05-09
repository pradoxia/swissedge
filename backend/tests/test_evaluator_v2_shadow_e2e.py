import pytest
from unittest.mock import AsyncMock, patch
import json
from pathlib import Path
from backend.services.investment.sources.base import Filing
from backend.services.investment.evaluator import evaluate_situation


def load_shadow_fixtures():
    """Load shadow test fixtures from JSON file."""
    fixtures_path = Path(__file__).parent / "fixtures" / "evaluator_v2_shadow_cases.json"
    with fixtures_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data["test_cases"]


def _build_mock_v2_response(case):
    """Build a mock v2 response matching evaluation_schema.json for a test case."""
    return json.dumps({
        "situation_type": case["expected_routing"]["situation_type"],
        "subtype": case["expected_routing"]["subtype"],
        "playbook_status": case["expected_routing"]["playbook_status"],
        "evaluator_confidence": case["expected_behavior"]["evaluator_confidence"],
        "recommendation": case["expected_behavior"]["recommendation_class"],
        "summary": f"Test evaluation for {case['filing']['company']}",
        "routing_decision": {
            "detected_form_type": case["filing"]["filing_type"],
            "detected_signal": "test fixture",
            "selected_playbook": case["expected_routing"]["selected_playbook"],
            "routed_from": None,
            "routed_to": None,
            "routing_reason": "test routing",
            "out_of_scope_reason": None,
            "detection_confidence": case["expected_routing"]["detection_confidence"]
        },
        "evidence_sources": [{
            "source_type": "SEC_EDGAR_filing",
            "document_name": case["filing"]["filing_type"],
            "filing_type": case["filing"]["filing_type"],
            "filing_date": case["filing"]["date"],
            "accession_or_identifier": None,
            "source_confidence": "HIGH",
            "used_for": "primary filing",
            "limitations": None
        }],
        "checklist_results": [],
        "risk_flags": [],
        "human_review_required": [
            {"item": item, "reason": "test", "required_human_input": "test", "related_playbook": case["expected_routing"]["selected_playbook"], "blocking_for_recommendation": True}
            for item in case["expected_behavior"].get("human_review_items", [])
        ] if case["expected_behavior"]["human_review_expected"] else [],
        "prohibited_inferences_detected": [],
        "missing_documents": [],
        "latest_amendment_check": {
            "checked": False,
            "latest_document_date": None,
            "latest_document_type": None,
            "amendment_found": False,
            "stale_data_risk": "UNKNOWN"
        },
        "scope_notes": "",
        "disclaimer": "Este análisis es educativo. No es asesoramiento financiero."
    })


@pytest.mark.asyncio
async def test_e2e_cash_merger_acquisition_tender():
    """End-to-end test: cash merger via acquisition tender (SC TO-T)."""
    fixtures = load_shadow_fixtures()
    case = next(f for f in fixtures if f["id"] == "cash_merger_acquisition_tender")

    filing = Filing(**case["filing"])
    mock_response = _build_mock_v2_response(case)
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 200, "output_tokens": 150}

    with patch.dict("os.environ", {"EVALUATOR_VERSION": "v2"}):
        with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = (mock_response, mock_usage)

            result, usage = await evaluate_situation(filing)

            # Verify schema fields
            assert "situation_type" in result
            assert "routing_decision" in result
            assert "evidence_sources" in result
            assert "checklist_results" in result
            assert "risk_flags" in result
            assert "human_review_required" in result
            assert "prohibited_inferences_detected" in result
            assert "disclaimer" in result

            # Verify routing
            assert result["situation_type"] == "merger_arbitrage"
            assert result["routing_decision"]["selected_playbook"] == "merger_arbitrage.md"
            assert result["playbook_status"] == "evaluator_ready"

            # Verify disclaimer
            assert result["disclaimer"] == "Este análisis es educativo. No es asesoramiento financiero."

            # Verify no prohibited inferences
            assert len(result["prohibited_inferences_detected"]) == 0


@pytest.mark.asyncio
async def test_e2e_self_tender_partial_status():
    """End-to-end test: self-tender with partial status and human review."""
    fixtures = load_shadow_fixtures()
    case = next(f for f in fixtures if f["id"] == "self_tender_fixed_price")

    filing = Filing(**case["filing"])
    mock_response = _build_mock_v2_response(case)
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 200, "output_tokens": 150}

    with patch.dict("os.environ", {"EVALUATOR_VERSION": "v2"}):
        with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = (mock_response, mock_usage)

            result, usage = await evaluate_situation(filing)

            # Verify routing
            assert result["situation_type"] == "tender_offer"
            assert result["routing_decision"]["selected_playbook"] == "tender_offer.md"
            assert result["playbook_status"] == "partial"

            # Verify human review items present
            assert len(result["human_review_required"]) > 0
            items = [item["item"] for item in result["human_review_required"]]
            assert any("hold_vs_tender" in item.lower() for item in items)

            # Verify disclaimer
            assert result["disclaimer"] == "Este análisis es educativo. No es asesoramiento financiero."


@pytest.mark.asyncio
async def test_e2e_spin_off_human_review_flags():
    """End-to-end test: spin-off with sum-of-parts and mandate flagged."""
    fixtures = load_shadow_fixtures()
    case = next(f for f in fixtures if f["id"] == "standard_spin_off")

    filing = Filing(**case["filing"])
    mock_response = _build_mock_v2_response(case)
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 200, "output_tokens": 150}

    with patch.dict("os.environ", {"EVALUATOR_VERSION": "v2"}):
        with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = (mock_response, mock_usage)

            result, usage = await evaluate_situation(filing)

            # Verify routing
            assert result["situation_type"] == "spin_off"
            assert result["playbook_status"] == "partial"

            # Verify human review items
            assert len(result["human_review_required"]) >= 2
            items = [item["item"].lower() for item in result["human_review_required"]]
            assert any("sum_of_parts" in item or "valuation" in item for item in items)
            assert any("mandate" in item for item in items)


@pytest.mark.asyncio
async def test_e2e_voluntary_liquidation_nav_flagged():
    """End-to-end test: voluntary liquidation with NAV construction flagged."""
    fixtures = load_shadow_fixtures()
    case = next(f for f in fixtures if f["id"] == "voluntary_liquidation")

    filing = Filing(**case["filing"])
    mock_response = _build_mock_v2_response(case)
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 200, "output_tokens": 150}

    with patch.dict("os.environ", {"EVALUATOR_VERSION": "v2"}):
        with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = (mock_response, mock_usage)

            result, usage = await evaluate_situation(filing)

            # Verify routing
            assert result["situation_type"] == "bankruptcy"
            assert result["playbook_status"] == "partial"

            # Verify NAV construction flagged
            items = [item["item"].lower() for item in result["human_review_required"]]
            assert any("nav" in item for item in items)


@pytest.mark.asyncio
async def test_e2e_detection_only_proxy_fight():
    """End-to-end test: proxy fight returns DETECTION_ONLY."""
    fixtures = load_shadow_fixtures()
    case = next(f for f in fixtures if f["id"] == "activist_proxy_fight")

    filing = Filing(**case["filing"])
    mock_response = _build_mock_v2_response(case)
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 150, "output_tokens": 100}

    with patch.dict("os.environ", {"EVALUATOR_VERSION": "v2"}):
        with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = (mock_response, mock_usage)

            result, usage = await evaluate_situation(filing)

            # Verify detection-only behavior
            assert result["situation_type"] == "proxy_fight"
            assert result["playbook_status"] == "detection_only"
            assert result["recommendation"] == "DETECTION_ONLY"
