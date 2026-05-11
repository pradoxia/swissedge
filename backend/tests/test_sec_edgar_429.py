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
import httpx
from datetime import datetime, timezone

from backend.services.investment.sources.sec_edgar import SECEdgarAdapter, _parse_hit


def _make_mock_response(status_code: int) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    return resp


def _make_ok_response(data: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=data)
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


@pytest.mark.asyncio
async def test_query_with_diagnostics_request_error_returns_backoff_diagnostics():
    """Network errors should return safe diagnostics instead of raising."""
    adapter = SECEdgarAdapter()

    with patch("backend.services.investment.sources.sec_edgar.asyncio.sleep", new_callable=AsyncMock):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.RequestError("network down"))
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            filings, diagnostics = await adapter._query_with_diagnostics(
                filing_type="SC TO-T",
                date_from="2026-05-01",
            )

    assert filings == []
    assert diagnostics["backoff"] is True
    assert diagnostics["rate_limited"] is False
    assert diagnostics["backoff_error"] == "RequestError"
    assert diagnostics["parsed_filings"] == 0


def test_parse_search_index_hit_with_root_forms_and_string_display_names():
    filing = _parse_hit({
        "_id": "0001140361-26-019536:ny20069883x7_sctota.htm",
        "_source": {
            "root_forms": ["SC TO-T"],
            "display_names": [
                "Forian Inc. (FORA) (CIK 0001829280)",
                "2025 Acquisition Company, LLC (CIK 0002083167)",
            ],
            "file_date": "2026-05-08",
            "file_name": "ny20069883x7_sctota.htm",
        },
    })

    assert filing is not None
    assert filing.filing_type == "SC TO-T"
    assert filing.company == "Forian Inc."
    assert filing.ticker == "FORA"
    assert filing.cik == "0001829280"
    assert filing.accession_number == "0001140361-26-019536"


@pytest.mark.asyncio
async def test_query_with_diagnostics_counts_real_shaped_search_index_hit():
    adapter = SECEdgarAdapter()
    data = {
        "hits": {
            "total": {"value": 6},
            "hits": [{
                "_id": "0001140361-26-019536:ny20069883x7_sctota.htm",
                "_source": {
                    "root_forms": ["SC TO-T"],
                    "display_names": [
                        "Forian Inc. (FORA) (CIK 0001829280)",
                        "2025 Acquisition Company, LLC (CIK 0002083167)",
                    ],
                    "file_date": "2026-05-08",
                    "file_name": "ny20069883x7_sctota.htm",
                },
            }],
        },
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=_make_ok_response(data))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        filings, diagnostics = await adapter._query_with_diagnostics(
            filing_type="SC TO-T",
            date_from="2026-05-04",
        )

    assert len(filings) == 1
    assert filings[0].filing_type == "SC TO-T"
    assert diagnostics["raw_hits"] == 1
    assert diagnostics["parsed_filings"] == 1
    assert diagnostics["classified_filings"] == 1


@pytest.mark.asyncio
async def test_query_with_diagnostics_includes_hit_inside_lookback():
    adapter = SECEdgarAdapter()
    data = {
        "hits": {
            "hits": [{
                "_id": "0001140361-26-019536:ny20069883x7_sctota.htm",
                "_source": {
                    "root_forms": ["SC TO-T"],
                    "display_names": ["Forian Inc. (FORA) (CIK 0001829280)"],
                    "file_date": "2026-05-10",
                    "file_name": "ny20069883x7_sctota.htm",
                },
            }],
        },
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=_make_ok_response(data))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        filings, diagnostics = await adapter._query_with_diagnostics(
            filing_type="SC TO-T",
            date_from="2026-05-09",
            date_to="2026-05-11",
            start_datetime=datetime(2026, 5, 9, tzinfo=timezone.utc),
            end_datetime=datetime(2026, 5, 11, 23, 59, 59, tzinfo=timezone.utc),
        )

    assert len(filings) == 1
    assert filings[0].filing_type == "SC TO-T"
    assert diagnostics["outside_lookback_skipped"] == 0
    assert diagnostics["missing_filing_date_skipped"] == 0
    assert diagnostics["query_start_date"] == "2026-05-09"
    assert diagnostics["query_end_date"] == "2026-05-11"
    params = mock_client.get.call_args.kwargs["params"]
    assert params["keys"] == "SC TO-T"
    assert params["forms"] == "SC TO-T"
    assert params["dateRange"] == "custom"
    assert params["startdt"] == "2026-05-09"
    assert params["enddt"] == "2026-05-11"
    assert params["from"] == 0


@pytest.mark.asyncio
async def test_query_with_diagnostics_skips_hit_outside_lookback():
    adapter = SECEdgarAdapter()
    data = {
        "hits": {
            "hits": [{
                "_id": "0001193125-07-123456:old_sctot.htm",
                "_source": {
                    "root_forms": ["SC TO-T"],
                    "display_names": ["Old Deal Corp. (OLD) (CIK 0000000002)"],
                    "file_date": "2007-05-10",
                    "file_name": "old_sctot.htm",
                },
            }],
        },
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=_make_ok_response(data))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        filings, diagnostics = await adapter._query_with_diagnostics(
            filing_type="SC TO-T",
            date_from="2026-05-09",
            date_to="2026-05-11",
            start_datetime=datetime(2026, 5, 9, tzinfo=timezone.utc),
            end_datetime=datetime(2026, 5, 11, 23, 59, 59, tzinfo=timezone.utc),
        )

    assert filings == []
    assert diagnostics["parsed_filings"] == 0
    assert diagnostics["outside_lookback_skipped"] == 1
    assert diagnostics["oldest_filing_date_seen"] == "2007-05-10"
    assert diagnostics["newest_filing_date_seen"] == "2007-05-10"


@pytest.mark.asyncio
async def test_query_with_diagnostics_skips_hit_missing_filing_date():
    adapter = SECEdgarAdapter()
    data = {
        "hits": {
            "hits": [{
                "_id": "0001140361-26-019536:ny20069883x7_sctota.htm",
                "_source": {
                    "root_forms": ["SC TO-T"],
                    "display_names": ["No Date Corp. (NODT) (CIK 0000000003)"],
                    "file_name": "ny20069883x7_sctota.htm",
                },
            }],
        },
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=_make_ok_response(data))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        filings, diagnostics = await adapter._query_with_diagnostics(
            filing_type="SC TO-T",
            date_from="2026-05-09",
            date_to="2026-05-11",
            start_datetime=datetime(2026, 5, 9, tzinfo=timezone.utc),
            end_datetime=datetime(2026, 5, 11, 23, 59, 59, tzinfo=timezone.utc),
        )

    assert filings == []
    assert diagnostics["parsed_filings"] == 0
    assert diagnostics["missing_filing_date_skipped"] == 1


def test_parse_search_index_8k_liquidation_metadata_hit():
    filing = _parse_hit({
        "_id": "0000000000-26-000111:liquidation_8k.htm",
        "_source": {
            "root_forms": ["8-K"],
            "display_names": ["Liquidating Corp. (LIQ) (CIK 0000000001)"],
            "filed_at": "2026-05-09",
            "file_name": "liquidation_8k.htm",
            "file_description": "Current report announcing plan of liquidation",
        },
    })

    assert filing is not None
    assert filing.filing_type == "8-K"
    assert filing.situation_type == "bankruptcy"
    assert filing.date == "2026-05-09"
