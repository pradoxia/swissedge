import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_filing():
    """Sample filing input for testing."""
    return {
        "company": "Test Corp",
        "ticker": "TEST",
        "filing_type": "SC TO-T",
        "date": "2026-04-29",
        "url": "https://sec.gov/test",
        "summary": "Test acquisition tender offer",
        "situation_type": None,
        "cik": "0001234567",
        "accession_number": "0001234567-26-000001"
    }


@pytest.fixture
def mock_v1_situation():
    """Mock situation with v1 evaluation."""
    from backend.models.investment import SpecialSituation
    from datetime import datetime, timezone
    import uuid

    sit = SpecialSituation(
        id=uuid.uuid4(),
        situation_type="merger",
        company_name="V1 Test Corp",
        ticker="V1T",
        filing_type="8-K",
        filing_url="https://test.com/v1",
        detected_at=datetime.now(timezone.utc),
        status="detected",
        evaluation={
            "checklist_results": [],
            "strengths": ["test"],
            "weaknesses": [],
            "risks": [],
            "confidence": "MEDIUM",
            "recommendation": "WATCHLIST",
            "summary": "V1 evaluation"
        }
    )
    return sit


@pytest.fixture
def mock_v2_situation():
    """Mock situation with v2 evaluation."""
    from backend.models.investment import SpecialSituation
    from datetime import datetime, timezone
    import uuid

    sit = SpecialSituation(
        id=uuid.uuid4(),
        situation_type="merger_arbitrage",
        company_name="V2 Test Corp",
        ticker="V2T",
        filing_type="SC TO-T",
        filing_url="https://test.com/v2",
        detected_at=datetime.now(timezone.utc),
        status="detected",
        evaluation={
            "evaluator_version": "v2",
            "situation_type": "merger_arbitrage",
            "subtype": "acquisition_tender_offer",
            "playbook_status": "evaluator_ready",
            "evaluator_confidence": "FULL",
            "recommendation": "DEEP_RESEARCH",
            "routing_decision": {
                "selected_playbook": "merger_arbitrage.md",
                "detection_confidence": "HIGH"
            },
            "human_review_required": [],
            "risk_flags": [{"flag": "test"}],
            "prohibited_inferences_detected": [],
            "missing_documents": [],
            "disclaimer": "Test disclaimer"
        }
    )
    return sit


@pytest.mark.asyncio
async def test_evaluate_v2_endpoint_exists():
    """Test that /evaluate-v2 endpoint exists."""
    response = client.post("/api/investment/evaluate-v2", json={
        "company": "Test",
        "filing_type": "8-K",
        "date": "2026-04-29",
        "url": "https://test.com",
        "summary": "Test"
    })
    # Should not be 404
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_evaluate_v2_uses_v2_evaluator(sample_filing):
    """Test that evaluate-v2 endpoint uses v2 evaluator."""
    mock_result = {
        "situation_type": "merger_arbitrage",
        "evaluator_version": "v2",
        "recommendation": "DEEP_RESEARCH",
        "disclaimer": "Este análisis es educativo. No es asesoramiento financiero."
    }
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 100, "output_tokens": 50}

    with patch("backend.api.investment.router.evaluate_situation", new_callable=AsyncMock) as mock_eval:
        with patch("backend.api.investment.router.run_logger.start_run", new_callable=AsyncMock) as mock_start:
            with patch("backend.api.investment.router.run_logger.finish_run", new_callable=AsyncMock):
                with patch("backend.api.investment.router.run_logger.log_ai_usage", new_callable=AsyncMock):
                    mock_eval.return_value = (mock_result, mock_usage)
                    mock_start.return_value = "test-run-id"

                    response = client.post("/api/investment/evaluate-v2", json=sample_filing)

                    assert response.status_code == 200
                    data = response.json()
                    assert data["evaluator_version"] == "v2"
                    assert data["result"]["situation_type"] == "merger_arbitrage"
                    assert "daily_limit" in data


@pytest.mark.asyncio
async def test_evaluate_v2_daily_limit_enforcement(sample_filing):
    """Test that daily limit is enforced."""
    # Reset counter
    from backend.api.investment.router import _v2_daily_counter
    _v2_daily_counter["date"] = None
    _v2_daily_counter["count"] = 0

    mock_result = {"situation_type": "test", "evaluator_version": "v2"}
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 100, "output_tokens": 50}

    with patch("backend.api.investment.router.evaluate_situation", new_callable=AsyncMock) as mock_eval:
        with patch("backend.api.investment.router.run_logger.start_run", new_callable=AsyncMock):
            with patch("backend.api.investment.router.run_logger.finish_run", new_callable=AsyncMock):
                with patch("backend.api.investment.router.run_logger.log_ai_usage", new_callable=AsyncMock):
                    mock_eval.return_value = (mock_result, mock_usage)

                    # Make 10 successful requests
                    for i in range(10):
                        response = client.post("/api/investment/evaluate-v2", json=sample_filing)
                        assert response.status_code == 200
                        data = response.json()
                        assert data["daily_limit"]["used"] == i + 1

                    # 11th request should be rejected
                    response = client.post("/api/investment/evaluate-v2", json=sample_filing)
                    assert response.status_code == 429
                    assert "limit reached" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_evaluate_v2_does_not_affect_scan_endpoint(sample_filing):
    """Test that v2 endpoint does not change default v1 behavior in scan."""
    import os
    from backend.api.investment.router import _v2_daily_counter

    # Reset counter
    _v2_daily_counter["date"] = None
    _v2_daily_counter["count"] = 0

    # Ensure EVALUATOR_VERSION is not set globally
    original = os.environ.get("EVALUATOR_VERSION")
    if "EVALUATOR_VERSION" in os.environ:
        del os.environ["EVALUATOR_VERSION"]

    try:
        mock_result = {"situation_type": "test", "evaluator_version": "v2"}
        mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 100, "output_tokens": 50}

        with patch("backend.api.investment.router.evaluate_situation", new_callable=AsyncMock) as mock_eval:
            with patch("backend.api.investment.router.run_logger.start_run", new_callable=AsyncMock):
                with patch("backend.api.investment.router.run_logger.finish_run", new_callable=AsyncMock):
                    with patch("backend.api.investment.router.run_logger.log_ai_usage", new_callable=AsyncMock):
                        mock_eval.return_value = (mock_result, mock_usage)

                        # Call v2 endpoint
                        response = client.post("/api/investment/evaluate-v2", json=sample_filing)
                        assert response.status_code == 200

                        # Verify EVALUATOR_VERSION is not set globally after v2 call
                        assert os.environ.get("EVALUATOR_VERSION") is None

    finally:
        if original is not None:
            os.environ["EVALUATOR_VERSION"] = original


@pytest.mark.asyncio
async def test_evaluate_v2_fallback_detection(sample_filing):
    """Test that fallback to v1 is detected and reported."""
    from backend.api.investment.router import _v2_daily_counter

    # Reset counter
    _v2_daily_counter["date"] = None
    _v2_daily_counter["count"] = 0

    mock_result = {
        "situation_type": "test",
        "_fallback_to_v1": True,
        "evaluator_version": "v1"
    }
    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 100, "output_tokens": 50}

    with patch("backend.api.investment.router.evaluate_situation", new_callable=AsyncMock) as mock_eval:
        with patch("backend.api.investment.router.run_logger.start_run", new_callable=AsyncMock):
            with patch("backend.api.investment.router.run_logger.finish_run", new_callable=AsyncMock):
                with patch("backend.api.investment.router.run_logger.log_ai_usage", new_callable=AsyncMock):
                    mock_eval.return_value = (mock_result, mock_usage)

                    response = client.post("/api/investment/evaluate-v2", json=sample_filing)

                    assert response.status_code == 200
                    data = response.json()
                    assert data["fallback_occurred"] is True
                    assert data["evaluator_version"] == "v1"


def test_extract_v2_fields_from_v1_evaluation():
    """Test that v1 evaluations gracefully return defaults for v2 fields."""
    from backend.api.investment.router import _extract_v2_fields

    v1_eval = {
        "checklist_results": [],
        "strengths": ["test"],
        "weaknesses": [],
        "risks": [],
        "confidence": "MEDIUM",
        "recommendation": "WATCHLIST"
    }

    result = _extract_v2_fields(v1_eval)

    assert result["evaluator_version"] == "v1"
    assert result["v2_situation_type"] is None
    assert result["selected_playbook"] is None
    assert result["playbook_status"] is None
    assert result["human_review_required_count"] == 0
    assert result["risk_flags_count"] == 0
    assert result["prohibited_inferences_count"] == 0


def test_extract_v2_fields_from_v2_evaluation():
    """Test that v2 evaluations correctly extract dashboard fields."""
    from backend.api.investment.router import _extract_v2_fields

    v2_eval = {
        "evaluator_version": "v2",
        "situation_type": "merger_arbitrage",
        "subtype": "acquisition_tender_offer",
        "playbook_status": "evaluator_ready",
        "evaluator_confidence": "FULL",
        "recommendation": "DEEP_RESEARCH",
        "routing_decision": {
            "selected_playbook": "merger_arbitrage.md"
        },
        "human_review_required": [{"item": "test1"}, {"item": "test2"}],
        "risk_flags": [{"flag": "test"}],
        "prohibited_inferences_detected": [],
        "missing_documents": []
    }

    result = _extract_v2_fields(v2_eval)

    assert result["evaluator_version"] == "v2"
    assert result["v2_situation_type"] == "merger_arbitrage"
    assert result["v2_subtype"] == "acquisition_tender_offer"
    assert result["selected_playbook"] == "merger_arbitrage.md"
    assert result["playbook_status"] == "evaluator_ready"
    assert result["recommendation"] == "DEEP_RESEARCH"
    assert result["evaluator_confidence"] == "FULL"
    assert result["human_review_required_count"] == 2
    assert result["risk_flags_count"] == 1
    assert result["prohibited_inferences_count"] == 0
    assert result["missing_documents_count"] == 0


def test_situations_list_includes_v2_fields(mock_v1_situation, mock_v2_situation):
    """Test that /situations endpoint includes v2 dashboard fields."""
    from backend.api.investment.router import _serialize

    v1_serialized = _serialize(mock_v1_situation)
    v2_serialized = _serialize(mock_v2_situation)

    # V1 should have defaults
    assert v1_serialized["evaluator_version"] == "v1"
    assert v1_serialized["selected_playbook"] is None

    # V2 should have extracted fields
    assert v2_serialized["evaluator_version"] == "v2"
    assert v2_serialized["v2_situation_type"] == "merger_arbitrage"
    assert v2_serialized["selected_playbook"] == "merger_arbitrage.md"
    assert v2_serialized["playbook_status"] == "evaluator_ready"
    assert v2_serialized["recommendation"] == "DEEP_RESEARCH"
    assert v2_serialized["human_review_required_count"] == 0
    assert v2_serialized["risk_flags_count"] == 1

