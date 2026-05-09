import pytest
from unittest.mock import AsyncMock, patch
from backend.services.investment.sources.base import Filing
from backend.services.investment.evaluator import (
    evaluate_situation,
    _get_evaluator_version,
    _normalize_v2_result,
    _check_prohibited_inferences,
)


def test_get_evaluator_version_default():
    """Test that default evaluator version is v1."""
    with patch.dict("os.environ", {}, clear=True):
        assert _get_evaluator_version() == "v1"


def test_get_evaluator_version_v2():
    """Test that EVALUATOR_VERSION=v2 is recognized."""
    with patch.dict("os.environ", {"EVALUATOR_VERSION": "v2"}):
        assert _get_evaluator_version() == "v2"


def test_get_evaluator_version_case_insensitive():
    """Test that EVALUATOR_VERSION is case-insensitive."""
    with patch.dict("os.environ", {"EVALUATOR_VERSION": "V2"}):
        assert _get_evaluator_version() == "v2"


@pytest.mark.asyncio
async def test_v2_normalizes_missing_fields():
    """Test that v2 normalizes missing arrays/objects to required schema."""
    filing = Filing(
        company="Test Corp",
        ticker="TST",
        filing_type="8-K",
        date="2026-04-29",
        url="https://sec.gov/test",
        summary="Test filing",
    )

    # Minimal valid JSON response
    mock_response = '''{
        "situation_type": "merger",
        "recommendation": "WATCHLIST",
        "summary": "Test summary"
    }'''
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 100, "output_tokens": 50}

    with patch.dict("os.environ", {"EVALUATOR_VERSION": "v2"}):
        with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = (mock_response, mock_usage)

            result, usage = await evaluate_situation(filing)

            # Verify all required fields exist
            assert "situation_type" in result
            assert "subtype" in result
            assert "playbook_status" in result
            assert "evaluator_confidence" in result
            assert "recommendation" in result
            assert "routing_decision" in result
            assert "evidence_sources" in result
            assert "checklist_results" in result
            assert "risk_flags" in result
            assert "human_review_required" in result
            assert "prohibited_inferences_detected" in result
            assert "missing_documents" in result
            assert "latest_amendment_check" in result
            assert "scope_notes" in result
            assert "disclaimer" in result

            # Verify arrays are lists
            assert isinstance(result["evidence_sources"], list)
            assert isinstance(result["checklist_results"], list)
            assert isinstance(result["risk_flags"], list)
            assert isinstance(result["human_review_required"], list)
            assert isinstance(result["prohibited_inferences_detected"], list)
            assert isinstance(result["missing_documents"], list)

            # Verify objects are dicts
            assert isinstance(result["routing_decision"], dict)
            assert isinstance(result["latest_amendment_check"], dict)

            # Verify exact disclaimer
            assert result["disclaimer"] == "Este análisis es educativo. No es asesoramiento financiero."


@pytest.mark.asyncio
async def test_v2_sc_to_i_routes_to_tender_offer():
    """Test that SC TO-I filing routes to tender_offer playbook."""
    filing = Filing(
        company="Company Inc",
        ticker="CO",
        filing_type="SC TO-I",
        date="2026-04-29",
        url="https://sec.gov/test",
        summary="Self-tender offer at $50 per share",
    )

    mock_response = '''{
        "situation_type": "tender_offer",
        "subtype": "self_tender",
        "playbook_status": "partial",
        "evaluator_confidence": "PARTIAL",
        "recommendation": "HUMAN_REVIEW_REQUIRED",
        "summary": "Self-tender detected, hold-vs-tender decision requires human review",
        "routing_decision": {
            "detected_form_type": "SC TO-I",
            "selected_playbook": "tender_offer.md",
            "detection_confidence": "HIGH"
        },
        "human_review_required": [
            {
                "item": "hold_vs_tender_decision",
                "reason": "requires intrinsic value estimate",
                "required_human_input": "valuation model",
                "related_playbook": "tender_offer.md",
                "blocking_for_recommendation": true
            }
        ],
        "disclaimer": "Este análisis es educativo. No es asesoramiento financiero."
    }'''
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 200, "output_tokens": 100}

    with patch.dict("os.environ", {"EVALUATOR_VERSION": "v2"}):
        with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = (mock_response, mock_usage)

            result, usage = await evaluate_situation(filing)

            # Verify routing
            assert result["situation_type"] == "tender_offer"
            assert result["subtype"] == "self_tender"
            assert result["routing_decision"]["selected_playbook"] == "tender_offer.md"
            assert result["playbook_status"] == "partial"

            # Verify hold-vs-tender is flagged for human review
            assert len(result["human_review_required"]) > 0
            assert any("hold_vs_tender" in item.get("item", "").lower() for item in result["human_review_required"])


@pytest.mark.asyncio
async def test_v2_sc_to_t_routes_to_merger_arbitrage():
    """Test that SC TO-T filing routes to merger_arbitrage playbook."""
    filing = Filing(
        company="Target Corp",
        ticker="TGT",
        filing_type="SC TO-T",
        date="2026-04-29",
        url="https://sec.gov/test",
        summary="Tender offer by Acquirer Inc at $100 per share",
    )

    mock_response = '''{
        "situation_type": "merger_arbitrage",
        "subtype": "acquisition_tender_offer",
        "playbook_status": "evaluator_ready",
        "evaluator_confidence": "FULL",
        "recommendation": "DEEP_RESEARCH",
        "summary": "Acquisition tender offer detected, spread analysis possible",
        "routing_decision": {
            "detected_form_type": "SC TO-T",
            "selected_playbook": "merger_arbitrage.md",
            "detection_confidence": "HIGH"
        },
        "disclaimer": "Este análisis es educativo. No es asesoramiento financiero."
    }'''
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 200, "output_tokens": 100}

    with patch.dict("os.environ", {"EVALUATOR_VERSION": "v2"}):
        with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = (mock_response, mock_usage)

            result, usage = await evaluate_situation(filing)

            # Verify routing
            assert result["situation_type"] == "merger_arbitrage"
            assert result["subtype"] == "acquisition_tender_offer"
            assert result["routing_decision"]["selected_playbook"] == "merger_arbitrage.md"
            assert result["playbook_status"] == "evaluator_ready"
            assert result["recommendation"] == "DEEP_RESEARCH"


@pytest.mark.asyncio
async def test_v2_form_10_spin_off_partial_status():
    """Test that Form 10 spin-off has partial status with human review items."""
    filing = Filing(
        company="SpinCo",
        ticker=None,
        filing_type="Form 10",
        date="2026-04-29",
        url="https://sec.gov/test",
        summary="Spinco registration statement for separation from Parent Corp",
    )

    mock_response = '''{
        "situation_type": "spin_off",
        "subtype": "standard_spin_off",
        "playbook_status": "partial",
        "evaluator_confidence": "PARTIAL",
        "recommendation": "HUMAN_REVIEW_REQUIRED",
        "summary": "Spin-off detected, sum-of-parts valuation and institutional mandate analysis require human review",
        "routing_decision": {
            "detected_form_type": "Form 10",
            "selected_playbook": "spin_off.md",
            "detection_confidence": "HIGH"
        },
        "human_review_required": [
            {
                "item": "sum_of_parts_valuation",
                "reason": "requires peer comparable data not in filings",
                "required_human_input": "valuation model",
                "related_playbook": "spin_off.md",
                "blocking_for_recommendation": true
            },
            {
                "item": "institutional_mandate_inference",
                "reason": "can only observe fund category from 13F, cannot infer mandate",
                "required_human_input": "judgment",
                "related_playbook": "spin_off.md",
                "blocking_for_recommendation": false
            }
        ],
        "disclaimer": "Este análisis es educativo. No es asesoramiento financiero."
    }'''
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 200, "output_tokens": 150}

    with patch.dict("os.environ", {"EVALUATOR_VERSION": "v2"}):
        with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = (mock_response, mock_usage)

            result, usage = await evaluate_situation(filing)

            # Verify partial status
            assert result["situation_type"] == "spin_off"
            assert result["playbook_status"] == "partial"
            assert result["evaluator_confidence"] == "PARTIAL"

            # Verify human review items
            assert len(result["human_review_required"]) >= 2
            items = [item.get("item", "") for item in result["human_review_required"]]
            assert any("sum_of_parts" in item.lower() for item in items)
            assert any("mandate" in item.lower() for item in items)


@pytest.mark.asyncio
async def test_v2_bankruptcy_nav_construction_flagged():
    """Test that NAV construction in bankruptcy is flagged as prohibited/human review."""
    filing = Filing(
        company="Liquidating Corp",
        ticker="LIQ",
        filing_type="8-K",
        date="2026-04-29",
        url="https://sec.gov/test",
        summary="Company announces plan of dissolution and liquidation",
    )

    mock_response = '''{
        "situation_type": "bankruptcy",
        "subtype": "voluntary_liquidation",
        "playbook_status": "partial",
        "evaluator_confidence": "PARTIAL",
        "recommendation": "HUMAN_REVIEW_REQUIRED",
        "summary": "Voluntary liquidation detected, NAV construction requires human review",
        "routing_decision": {
            "detected_form_type": "8-K",
            "selected_playbook": "bankruptcy.md",
            "detection_confidence": "HIGH"
        },
        "human_review_required": [
            {
                "item": "nav_construction",
                "reason": "requires asset realization factors not disclosed in filings",
                "required_human_input": "valuation model",
                "related_playbook": "bankruptcy.md",
                "blocking_for_recommendation": true
            }
        ],
        "disclaimer": "Este análisis es educativo. No es asesoramiento financiero."
    }'''
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 200, "output_tokens": 120}

    with patch.dict("os.environ", {"EVALUATOR_VERSION": "v2"}):
        with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = (mock_response, mock_usage)

            result, usage = await evaluate_situation(filing)

            # Verify NAV construction is flagged
            assert result["situation_type"] == "bankruptcy"
            assert result["playbook_status"] == "partial"
            items = [item.get("item", "").lower() for item in result["human_review_required"]]
            assert any("nav" in item for item in items)


@pytest.mark.asyncio
async def test_v2_detection_only_proxy_fight():
    """Test that proxy_fight returns DETECTION_ONLY recommendation."""
    filing = Filing(
        company="Target Inc",
        ticker="TGT",
        filing_type="SC 13D",
        date="2026-04-29",
        url="https://sec.gov/test",
        summary="Activist investor discloses 8% stake, seeks board seats",
    )

    mock_response = '''{
        "situation_type": "proxy_fight",
        "subtype": "activist_campaign",
        "playbook_status": "detection_only",
        "evaluator_confidence": "PARTIAL",
        "recommendation": "DETECTION_ONLY",
        "summary": "Activist campaign detected, no evaluation methodology available",
        "routing_decision": {
            "detected_form_type": "SC 13D",
            "selected_playbook": "proxy_fight.md",
            "detection_confidence": "HIGH"
        },
        "scope_notes": "Course provides no evaluation methodology for proxy fights beyond detection",
        "disclaimer": "Este análisis es educativo. No es asesoramiento financiero."
    }'''
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 150, "output_tokens": 80}

    with patch.dict("os.environ", {"EVALUATOR_VERSION": "v2"}):
        with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = (mock_response, mock_usage)

            result, usage = await evaluate_situation(filing)

            # Verify detection-only behavior
            assert result["situation_type"] == "proxy_fight"
            assert result["playbook_status"] == "detection_only"
            assert result["recommendation"] == "DETECTION_ONLY"


def test_prohibited_inference_guard_detects_nav():
    """Test that prohibited inference guard detects NAV construction attempt."""
    result = {
        "situation_type": "bankruptcy",
        "summary": "I estimate liquidation NAV at $15 per share based on asset realization",
        "recommendation": "DEEP_RESEARCH",
        "human_review_required": [],
        "prohibited_inferences_detected": [],
    }

    checked = _check_prohibited_inferences(result)

    # Verify NAV construction was detected
    assert len(checked["prohibited_inferences_detected"]) > 0
    assert any("nav" in item.lower() for item in checked["prohibited_inferences_detected"])
    # Verify recommendation escalated
    assert checked["recommendation"] == "HUMAN_REVIEW_REQUIRED"


def test_prohibited_inference_guard_allows_flagged_items():
    """Test that prohibited inference guard allows items already flagged for human review."""
    result = {
        "situation_type": "bankruptcy",
        "summary": "NAV construction requires human review",
        "recommendation": "HUMAN_REVIEW_REQUIRED",
        "human_review_required": [
            {"item": "nav_construction", "reason": "requires valuation model"}
        ],
        "prohibited_inferences_detected": [],
    }

    checked = _check_prohibited_inferences(result)

    # Verify no false positive (NAV mentioned but properly flagged)
    assert len(checked["prohibited_inferences_detected"]) == 0


def test_prohibited_inference_guard_detects_multiple():
    """Test that prohibited inference guard detects multiple prohibited inferences."""
    result = {
        "situation_type": "spin_off",
        "summary": "Sum-of-parts valuation suggests 30% upside. Institutional mandate analysis indicates forced selling.",
        "scope_notes": "Broker deadline is typically 2 days before expiration",
        "recommendation": "DEEP_RESEARCH",
        "human_review_required": [],
        "prohibited_inferences_detected": [],
    }

    checked = _check_prohibited_inferences(result)

    # Verify multiple detections
    assert len(checked["prohibited_inferences_detected"]) >= 2
    detected_lower = [item.lower() for item in checked["prohibited_inferences_detected"]]
    assert any("sum-of-parts" in item or "valuation" in item for item in detected_lower)
    assert any("mandate" in item or "broker" in item for item in detected_lower)
    assert checked["recommendation"] == "HUMAN_REVIEW_REQUIRED"
