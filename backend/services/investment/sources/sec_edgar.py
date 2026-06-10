import asyncio
import logging
import re
from datetime import datetime, time, timedelta, timezone

import httpx

from backend.config import get_settings
from backend.services.investment.sources.base import Filing, InvestmentSource

logger = logging.getLogger(__name__)

# SEC EDGAR full-text search API
_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
_BROWSE_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
_RATE_LIMIT_SECONDS = 5.0
_BACKOFF_SECONDS = 60.0
_DEFAULT_QUERY_LIMIT = 20

# Map filing types to situation types
_FILING_TYPE_MAP: dict[str, str] = {
    "Form 10": "spin_off",
    "SC TO-T": "merger_arbitrage",
    "SC TO-I": "tender_offer",
    "8-K": None,  # needs content analysis to classify
}

# Legacy mapping used by older scanner/search_by_type paths. Sprint Q manual SEC
# detection uses the P1-only search_recent_with_diagnostics path; do not expand
# Sprint Q scope through this mapping.
_SITUATION_FILING_TYPES: dict[str, list[str]] = {
    "spin_off": ["Form 10", "8-K"],
    "tender_offer": ["SC TO-T", "SC TO-I", "SC 13E-3", "8-K"],
    "merger": ["8-K", "DEF 14A"],
    "proxy_fight": ["DEF 14A", "DEFC14A", "DEFA14A"],
    "ipo": ["S-1", "F-1"],
}

_LIQUIDATION_KEYWORDS = [
    "plan of liquidation",
    "plan of dissolution",
    "liquidation",
    "dissolution",
]


def _classify_8k(summary: str) -> str | None:
    lower = summary.lower()
    if any(k in lower for k in _LIQUIDATION_KEYWORDS):
        return "bankruptcy"
    return None


async def _rate_limit():
    await asyncio.sleep(_RATE_LIMIT_SECONDS)


def _build_headers() -> dict:
    settings = get_settings()
    user_agent = settings.sec_user_agent or "SwissEdge/1.0 (contact@example.com)"
    return {
        "User-Agent": user_agent,
        "Accept": "application/json",
    }


def _first(value) -> str | None:
    if isinstance(value, list) and value:
        return str(value[0])
    if isinstance(value, str):
        return value
    return None


def _root_form(src: dict) -> str:
    root_form = _first(src.get("root_forms"))
    return root_form or src.get("file_type") or src.get("form") or ""


def _accession_from_hit(hit: dict, src: dict) -> str:
    accession = src.get("accession_no") or src.get("adsh") or src.get("accession_number")
    if accession:
        return str(accession)
    hit_id = hit.get("_id")
    if isinstance(hit_id, str):
        return hit_id.split(":", 1)[0]
    return ""


def _parse_display_name(value: str) -> tuple[str, str | None, str | None]:
    cik_match = re.search(r"\(CIK\s+(\d+)\)", value)
    ticker_match = re.search(r"\(([A-Z][A-Z0-9.\-]{0,9})\)\s+\(CIK\s+\d+\)", value)
    company = re.sub(r"\s+\([A-Z][A-Z0-9.\-]{0,9}\)\s+\(CIK\s+\d+\)", "", value)
    company = re.sub(r"\s+\(CIK\s+\d+\)", "", company).strip()
    return company or value, ticker_match.group(1) if ticker_match else None, cik_match.group(1) if cik_match else None


def _display_company(src: dict) -> tuple[str, str | None, str | None]:
    display_names = src.get("display_names") or []
    if display_names:
        first_display = display_names[0]
        if isinstance(first_display, dict):
            return (
                first_display.get("name") or src.get("entity_name") or "Unknown",
                first_display.get("ticker"),
                str(first_display.get("cik")) if first_display.get("cik") else None,
            )
        if isinstance(first_display, str):
            return _parse_display_name(first_display)
    return src.get("entity_name") or "Unknown", None, None


def _parse_filing_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        try:
            return datetime.combine(datetime.strptime(raw[:10], "%Y-%m-%d").date(), time.min, tzinfo=timezone.utc)
        except ValueError:
            return None


def _items_from_src(src: dict) -> list[str]:
    """Extract 8-K item codes (e.g. '1.03', '3.01') from an EFTS hit when present.

    EFTS exposes item codes for 8-K filings in the `items` field. Defensive:
    returns [] when the field is missing or has an unexpected shape.
    """
    raw = src.get("items")
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    codes: list[str] = []
    for value in raw:
        match = re.search(r"(\d{1,2}\.\d{2})", str(value))
        if match:
            codes.append(match.group(1))
    return codes


def _parse_hit(hit: dict) -> Filing | None:
    try:
        src = hit.get("_source", {})
        filing_type = _root_form(src)
        company, ticker, display_cik = _display_company(src)
        date_filed = src.get("file_date") or src.get("filed_at") or src.get("filed") or src.get("period_ending") or ""
        accession = _accession_from_hit(hit, src)
        cik = str(src.get("entity_id") or src.get("cik") or display_cik or "")
        entity_name = src.get("entity_name") or company

        # Build filing URL
        accession_clean = accession.replace("-", "") if accession else ""
        file_name = src.get("file_name") or src.get("file") or ""
        if cik and accession_clean and file_name:
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{file_name}"
        elif cik and accession_clean:
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/"
        else:
            url = f"{_SEARCH_URL}?q={accession}" if accession else _SEARCH_URL

        headline = src.get("file_description") or src.get("file_name") or src.get("summary") or ""
        item_codes = _items_from_src(src)
        items_suffix = f" Items: {', '.join(item_codes)}." if item_codes else ""
        summary = f"{filing_type} filed by {entity_name or company} on {date_filed}. {headline}{items_suffix}".strip()

        situation_type = _FILING_TYPE_MAP.get(filing_type)
        if situation_type is None and filing_type.upper().startswith("8-K"):
            situation_type = _classify_8k(summary)

        return Filing(
            company=entity_name or company,
            ticker=ticker,
            filing_type=filing_type,
            date=date_filed,
            url=url,
            summary=summary,
            situation_type=situation_type,
            cik=cik,
            accession_number=accession,
        )
    except Exception as e:
        logger.debug("Failed to parse SEC hit: %s", e)
        return None


def _filter_filings_by_lookback(
    filings: list[Filing],
    *,
    start_datetime: datetime,
    end_datetime: datetime,
) -> tuple[list[Filing], dict]:
    included: list[Filing] = []
    outside_lookback_skipped = 0
    missing_filing_date_skipped = 0
    seen_dates: list[datetime] = []

    for filing in filings:
        filing_datetime = _parse_filing_datetime(filing.date)
        if filing_datetime is None:
            missing_filing_date_skipped += 1
            continue
        seen_dates.append(filing_datetime)
        if filing_datetime < start_datetime or filing_datetime > end_datetime:
            outside_lookback_skipped += 1
            continue
        included.append(filing)

    return included, {
        "outside_lookback_skipped": outside_lookback_skipped,
        "missing_filing_date_skipped": missing_filing_date_skipped,
        "oldest_filing_date_seen": min(seen_dates).date().isoformat() if seen_dates else None,
        "newest_filing_date_seen": max(seen_dates).date().isoformat() if seen_dates else None,
    }


class SECEdgarAdapter(InvestmentSource):
    """
    Source adapter for SEC EDGAR full-text search API.
    Respects a conservative Sprint Q throttle: one request every 5 seconds.
    Requires SEC_USER_AGENT env var with your email.
    """

    FILING_TYPES = [
        "SC TO-T",
        "SC TO-I",
        "Form 10",
        "8-K",
        "SC 14D9",
        "DEFM14A",
        "PREM14A",
        "DFAN14A",
        "S-4",
        "SC 13E3",
        "25-NSE",
    ]

    # Targeted full-text sweeps: high-value phrases that form filters miss.
    # Each tuple is (quoted phrase, optional forms filter or None for all forms).
    FULL_TEXT_SWEEPS: list[tuple[str, str | None]] = [
        ("odd lot", None),
        ("plan of liquidation", "8-K"),
        ("dutch auction", None),
    ]

    async def search_recent(self, hours_back: int = 6) -> list[Filing]:
        filings, _diagnostics = await self.search_recent_with_diagnostics(hours_back=hours_back)
        return filings

    async def search_recent_with_diagnostics(self, hours_back: int = 6) -> tuple[list[Filing], dict]:
        end_datetime = datetime.now(timezone.utc)
        start_datetime = end_datetime - timedelta(hours=hours_back)
        start_date_str = start_datetime.strftime("%Y-%m-%d")
        end_date_str = end_datetime.strftime("%Y-%m-%d")

        all_filings: list[Filing] = []
        by_form: dict[str, dict] = {}
        for filing_type in self.FILING_TYPES:
            await _rate_limit()
            filings, diagnostics = await self._query_with_diagnostics(
                filing_type=filing_type,
                date_from=start_date_str,
                date_to=end_date_str,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
            )
            all_filings.extend(filings)
            by_form[filing_type] = diagnostics

        # Full-text sweeps: catch high-value phrases the form filters miss.
        # Results join the same parse/lookback/dedupe pipeline downstream.
        seen_accessions = {f.accession_number for f in all_filings if f.accession_number}
        for phrase, forms_filter in self.FULL_TEXT_SWEEPS:
            await _rate_limit()
            sweep_filings, sweep_diagnostics = await self._query_with_diagnostics(
                filing_type=forms_filter or "",
                date_from=start_date_str,
                date_to=end_date_str,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                full_text_query=phrase,
            )
            sweep_diagnostics["full_text_query"] = phrase
            new_filings = []
            for filing in sweep_filings:
                if filing.accession_number and filing.accession_number in seen_accessions:
                    continue
                if filing.accession_number:
                    seen_accessions.add(filing.accession_number)
                filing.summary = f"{filing.summary} [full-text sweep: {phrase}]"
                new_filings.append(filing)
            all_filings.extend(new_filings)
            sweep_diagnostics["sweep_new_filings"] = len(new_filings)
            by_form[f'sweep:"{phrase}"'] = sweep_diagnostics

        total_raw_hits = sum(int(d.get("raw_hits", 0)) for d in by_form.values())
        total_limited_hits = sum(int(d.get("limited_hits", 0)) for d in by_form.values())
        total_parsed_filings = sum(int(d.get("parsed_filings", 0)) for d in by_form.values())
        total_outside_lookback_skipped = sum(int(d.get("outside_lookback_skipped", 0)) for d in by_form.values())
        total_missing_filing_date_skipped = sum(int(d.get("missing_filing_date_skipped", 0)) for d in by_form.values())
        seen_dates = [
            value
            for d in by_form.values()
            for value in [d.get("oldest_filing_date_seen"), d.get("newest_filing_date_seen")]
            if value
        ]

        return all_filings, {
            "adapter_name": "SECEdgarAdapter",
            "source": "sec_edgar",
            "endpoint": _SEARCH_URL,
            "source_registry_used": False,
            "hours_back": hours_back,
            "date_from": start_date_str,
            "date_to": end_date_str,
            "query_start_date": start_date_str,
            "query_end_date": end_date_str,
            "forms_searched": self.FILING_TYPES,
            "query_limit_per_form": _DEFAULT_QUERY_LIMIT,
            "raw_hits_total": total_raw_hits,
            "limited_hits_total": total_limited_hits,
            "parsed_filings_total": total_parsed_filings,
            "outside_lookback_skipped": total_outside_lookback_skipped,
            "missing_filing_date_skipped": total_missing_filing_date_skipped,
            "oldest_filing_date_seen": min(seen_dates) if seen_dates else None,
            "newest_filing_date_seen": max(seen_dates) if seen_dates else None,
            "form_counts": {form: int(data.get("parsed_filings", 0)) for form, data in by_form.items()},
            "by_form": by_form,
        }

    async def search_by_type(self, situation_type: str) -> list[Filing]:
        filing_types = _SITUATION_FILING_TYPES.get(situation_type, ["8-K"])
        all_filings: list[Filing] = []
        for filing_type in filing_types:
            await _rate_limit()
            filings = await self._query(filing_type=filing_type)
            all_filings.extend(filings)
        return all_filings

    async def _query(self, filing_type: str, date_from: str | None = None, limit: int = _DEFAULT_QUERY_LIMIT) -> list[Filing]:
        filings, _diagnostics = await self._query_with_diagnostics(
            filing_type=filing_type,
            date_from=date_from,
            limit=limit,
        )
        return filings

    async def _query_with_diagnostics(
        self,
        filing_type: str,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = _DEFAULT_QUERY_LIMIT,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
        full_text_query: str | None = None,
    ) -> tuple[list[Filing], dict]:
        # Note: the legacy `keys` param sent the form name as a full-text term,
        # which is redundant with `forms` and can distort ranking. `q` is now
        # only used for explicit full-text sweeps (quoted phrase).
        params: dict = {
            "from": 0,
            "size": limit,
        }
        if filing_type:
            params["forms"] = filing_type
        if full_text_query:
            params["q"] = f'"{full_text_query}"'
        if date_from:
            params["dateRange"] = "custom"
            params["startdt"] = date_from
        if date_to:
            params["enddt"] = date_to

        query_start_date = date_from
        query_end_date = date_to

        try:
            async with httpx.AsyncClient(headers=_build_headers(), timeout=20) as client:
                response = await client.get(_SEARCH_URL, params=params)
                if response.status_code in {403, 429} or response.status_code >= 500:
                    logger.warning("SEC EDGAR backoff for status %s. Sleeping %ss.", response.status_code, _BACKOFF_SECONDS)
                    await asyncio.sleep(_BACKOFF_SECONDS)
                    return [], {
                        "filing_type": filing_type,
                        "query": params,
                        "raw_hits": 0,
                        "limited_hits": 0,
                        "parsed_filings": 0,
                        "parse_failures": 0,
                        "classified_filings": 0,
                        "unclassified_filings": 0,
                        "outside_lookback_skipped": 0,
                        "missing_filing_date_skipped": 0,
                        "query_start_date": query_start_date,
                        "query_end_date": query_end_date,
                        "oldest_filing_date_seen": None,
                        "newest_filing_date_seen": None,
                        "rate_limited": response.status_code == 429,
                        "backoff": True,
                        "backoff_status_code": response.status_code,
                        "backoff_seconds": _BACKOFF_SECONDS,
                    }
                response.raise_for_status()
                data = response.json()
        except httpx.RequestError as e:
            logger.error("SEC EDGAR request failed: %s", e)
            await asyncio.sleep(_BACKOFF_SECONDS)
            return [], {
                "filing_type": filing_type,
                "query": params,
                "raw_hits": 0,
                "limited_hits": 0,
                "parsed_filings": 0,
                "parse_failures": 0,
                "classified_filings": 0,
                "unclassified_filings": 0,
                "outside_lookback_skipped": 0,
                "missing_filing_date_skipped": 0,
                "query_start_date": query_start_date,
                "query_end_date": query_end_date,
                "oldest_filing_date_seen": None,
                "newest_filing_date_seen": None,
                "rate_limited": False,
                "backoff": True,
                "backoff_error": type(e).__name__,
                "backoff_seconds": _BACKOFF_SECONDS,
            }

        hits = data.get("hits", {}).get("hits", [])
        parsed_filings = [f for hit in hits[:limit] if (f := _parse_hit(hit)) is not None]
        if start_datetime is not None and end_datetime is not None:
            filings, filter_diagnostics = _filter_filings_by_lookback(
                parsed_filings,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
            )
        else:
            filings = parsed_filings
            filter_diagnostics = {
                "outside_lookback_skipped": 0,
                "missing_filing_date_skipped": 0,
                "oldest_filing_date_seen": None,
                "newest_filing_date_seen": None,
            }
        logger.info("SEC EDGAR: %d filings for type '%s'", len(filings), filing_type)
        classified = [f for f in filings if f.situation_type]
        return filings, {
            "filing_type": filing_type,
            "query": params,
            "raw_hits": len(hits),
            "limited_hits": len(hits[:limit]),
            "parsed_filings": len(filings),
            "parse_failures": max(0, len(hits[:limit]) - len(parsed_filings)),
            "classified_filings": len(classified),
            "unclassified_filings": len(filings) - len(classified),
            "outside_lookback_skipped": filter_diagnostics["outside_lookback_skipped"],
            "missing_filing_date_skipped": filter_diagnostics["missing_filing_date_skipped"],
            "query_start_date": query_start_date,
            "query_end_date": query_end_date,
            "oldest_filing_date_seen": filter_diagnostics["oldest_filing_date_seen"],
            "newest_filing_date_seen": filter_diagnostics["newest_filing_date_seen"],
        }
