"""
Regression test: SEC EDGAR 429 rate-limit handling in _query_with_diagnostics.

Before the fix, a 429 response caused _query_with_diagnostics() to return []
(a bare list) instead of tuple[list[Filing], dict], which crashed the caller
with ValueError: not enough values to unpack.

After the fix, a 429 returns ([], {<diagnostics with rate_limited:True>}),
allowing search_recent_with_diagnostics() to continue across remaining forms.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.investment.sources.sec_edgar import SECEdgarAdapter


def _make_mock_response(status_code: int) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    return resp


@pytest.mark.asyncio
async def test_query_with_diagnostics_429_returns_tuple():
    """_query_with_diagnostics must return (list, dict) on 429, not bare []."""
    adapter = SECEdgarAdapter()

    mock_response = _make_mock_response(429)

    with patch("backend.services.investment.sources.sec_edgar.asyncio.sleep", new_callable=AsyncMock):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            filings, diagnostics = await adapter._query_with_diagnostics(
                filing_type="8-K",
                date_from="2026-05-01",
            )

    assert filings == [], "Expected empty filings list on 429"
    assert isinstance(diagnostics, dict), "Expected diagnostics dict on 429"
    assert diagnostics.get("rate_limited") is True
    assert diagnostics.get("raw_hits") == 0
    assert diagnostics.get("parsed_filings") == 0
    assert diagnostics.get("filing_type") == "8-K"


@pytest.mark.asyncio
async def test_search_recent_with_diagnostics_survives_429():
    """search_recent_with_diagnostics must not raise when one form returns 429."""
    adapter = SECEdgarAdapter()

    mock_429 = _make_mock_response(429)
    ok_data = {"hits": {"hits": []}}
    mock_ok = MagicMock()
    mock_ok.status_code = 200
    mock_ok.raise_for_status = MagicMock()
    mock_ok.json = MagicMock(return_value=ok_data)

    call_count = 0

    async def side_effect_get(url, params=None):
        nonlocal call_count
        call_count += 1
        # First form gets 429, all others return 200 with empty hits
        return mock_429 if call_count == 1 else mock_ok

    with patch("backend.services.investment.sources.sec_edgar.asyncio.sleep", new_callable=AsyncMock):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = side_effect_get
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            # Must not raise
            filings, diagnostics = await adapter.search_recent_with_diagnostics(hours_back=6)

    assert filings == [], "Expected no filings when all forms return empty or 429"
    assert "by_form" in diagnostics

    # The rate-limited form must appear in by_form with rate_limited marker
    first_form = SECEdgarAdapter.FILING_TYPES[0]
    assert first_form in diagnostics["by_form"]
    assert diagnostics["by_form"][first_form].get("rate_limited") is True

    # All other forms must also be present
    for form in SECEdgarAdapter.FILING_TYPES[1:]:
        assert form in diagnostics["by_form"], f"Missing by_form entry for {form}"
