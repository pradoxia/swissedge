import pytest
from unittest.mock import AsyncMock, patch
from backend.services.investment.evaluator import _evaluate_situation_v2
from backend.services.investment.sources.base import Filing


@pytest.fixture
def sample_filing():
    """Sample filing for testing."""
    return Filing(
        company="Test Corp",
        ticker="TEST",
        filing_type="SC TO-I",
        date="2024-07-03",
        url="https://test.com/filing",
        summary="Test tender offer",
        situation_type="tender_offer",
    )


@pytest.mark.asyncio
async def test_v2_handles_json_with_preamble(sample_filing):
    """Test that v2 evaluator handles AI output with preamble text before JSON."""
    malformed_output = '''Here is the evaluation:

{
  "situation_type": "tender_offer",
  "evaluator_confidence": "PARTIAL",
  "recommendation": "WATCHLIST"
}'''

    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 100, "output_tokens": 50}

    with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = (malformed_output, mock_usage)

        result, usage = await _evaluate_situation_v2(sample_filing)

        assert result["situation_type"] == "tender_offer"
        assert result["recommendation"] == "WATCHLIST"


@pytest.mark.asyncio
async def test_v2_handles_json_with_trailing_text(sample_filing):
    """Test that v2 evaluator handles AI output with trailing text after JSON."""
    malformed_output = '''{
  "situation_type": "tender_offer",
  "evaluator_confidence": "PARTIAL",
  "recommendation": "WATCHLIST"
}

Let me know if you need any clarification.'''

    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 100, "output_tokens": 50}

    with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = (malformed_output, mock_usage)

        result, usage = await _evaluate_situation_v2(sample_filing)

        assert result["situation_type"] == "tender_offer"
        assert result["recommendation"] == "WATCHLIST"


@pytest.mark.asyncio
async def test_v2_handles_markdown_code_blocks(sample_filing):
    """Test that v2 evaluator handles markdown code blocks."""
    malformed_output = '''```json
{
  "situation_type": "tender_offer",
  "evaluator_confidence": "PARTIAL",
  "recommendation": "WATCHLIST"
}
```'''

    mock_usage = {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 100, "output_tokens": 50}

    with patch("backend.services.investment.evaluator.complete_with_usage", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = (malformed_output, mock_usage)

        result, usage = await _evaluate_situation_v2(sample_filing)

        assert result["situation_type"] == "tender_offer"
        assert result["recommendation"] == "WATCHLIST"
