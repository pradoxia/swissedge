import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from backend.config import get_settings
from backend.services.investment.sources.base import Filing, InvestmentSource

logger = logging.getLogger(__name__)

# SEC EDGAR full-text search API
_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
_BROWSE_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
_RATE_LIMIT_SECONDS = 0.11  # ~10 req/s max per SEC policy
_DEFAULT_QUERY_LIMIT = 20

# Map filing types to situation types
_FILING_TYPE_MAP: dict[str, str] = {
    "Form 10": "spin_off",
    "SC TO-T": "tender_offer",
    "SC TO-I": "tender_offer",
    "SC 13E-3": "tender_offer",
    "DEF 14A": "proxy_fight",
    "DEFC14A": "proxy_fight",
    "S-1": "ipo",
    "F-1": "ipo",
    "8-K": None,  # needs content analysis to classify
}

_SITUATION_FILING_TYPES: dict[str, list[str]] = {
    "spin_off": ["Form 10", "8-K"],
    "tender_offer": ["SC TO-T", "SC TO-I", "SC 13E-3", "8-K"],
    "merger": ["8-K", "DEF 14A"],
    "proxy_fight": ["DEF 14A", "DEFC14A", "DEFA14A"],
    "ipo": ["S-1", "F-1"],
}

_SPIN_OFF_KEYWORDS = ["spin-off", "spinoff", "separation", "carve-out", "form 10"]
_MERGER_KEYWORDS = ["merger", "acquisition", "acquires", "definitive agreement", "business combination"]


def _classify_8k(summary: str) -> str | None:
    lower = summary.lower()
    if any(k in lower for k in _SPIN_OFF_KEYWORDS):
        return "spin_off"
    if any(k in lower for k in _MERGER_KEYWORDS):
        return "merger"
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


def _parse_hit(hit: dict) -> Filing | None:
    try:
        src = hit.get("_source", {})
        filing_type = src.get("file_type", "")
        company = src.get("display_names", [{}])[0].get("name", "Unknown") if src.get("display_names") else "Unknown"
        ticker = src.get("display_names", [{}])[0].get("ticker") if src.get("display_names") else None
        date_filed = src.get("file_date", "")
        accession = src.get("period_of_report") or src.get("accession_no", "")
        cik = src.get("entity_id", "")
        entity_name = src.get("entity_name", company)

        # Build filing URL
        accession_clean = accession.replace("-", "") if accession else ""
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/" if cik and accession_clean else ""

        summary = f"{filing_type} filed by {entity_name or company} on {date_filed}"

        situation_type = _FILING_TYPE_MAP.get(filing_type)
        if situation_type is None and filing_type == "8-K":
            situation_type = _classify_8k(src.get("period_of_report", "") + summary)

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


class SECEdgarAdapter(InvestmentSource):
    """
    Source adapter for SEC EDGAR full-text search API.
    Respects SEC rate limits: max 10 requests/second.
    Requires SEC_USER_AGENT env var with your email.
    """

    FILING_TYPES = ["8-K", "S-1", "F-1", "SC TO-T", "SC TO-I", "Form 10", "DEF 14A", "DEFC14A"]

    async def search_recent(self, hours_back: int = 6) -> list[Filing]:
        filings, _diagnostics = await self.search_recent_with_diagnostics(hours_back=hours_back)
        return filings

    async def search_recent_with_diagnostics(self, hours_back: int = 6) -> tuple[list[Filing], dict]:
        since = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        date_str = since.strftime("%Y-%m-%d")

        all_filings: list[Filing] = []
        by_form: dict[str, dict] = {}
        for filing_type in self.FILING_TYPES:
            await _rate_limit()
            filings, diagnostics = await self._query_with_diagnostics(
                filing_type=filing_type,
                date_from=date_str,
            )
            all_filings.extend(filings)
            by_form[filing_type] = diagnostics

        total_raw_hits = sum(int(d.get("raw_hits", 0)) for d in by_form.values())
        total_limited_hits = sum(int(d.get("limited_hits", 0)) for d in by_form.values())
        total_parsed_filings = sum(int(d.get("parsed_filings", 0)) for d in by_form.values())

        return all_filings, {
            "adapter_name": "SECEdgarAdapter",
            "source": "sec_edgar",
            "endpoint": _SEARCH_URL,
            "source_registry_used": False,
            "hours_back": hours_back,
            "date_from": date_str,
            "forms_searched": self.FILING_TYPES,
            "query_limit_per_form": _DEFAULT_QUERY_LIMIT,
            "raw_hits_total": total_raw_hits,
            "limited_hits_total": total_limited_hits,
            "parsed_filings_total": total_parsed_filings,
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
        limit: int = _DEFAULT_QUERY_LIMIT,
    ) -> tuple[list[Filing], dict]:
        params: dict = {
            "q": f'"{filing_type}"',
            "forms": filing_type,
        }
        if date_from:
            params["dateRange"] = "custom"
            params["startdt"] = date_from

        try:
            async with httpx.AsyncClient(headers=_build_headers(), timeout=20) as client:
                response = await client.get(_SEARCH_URL, params=params)
                if response.status_code == 429:
                    logger.warning("SEC EDGAR rate limited. Sleeping 60s.")
                    await asyncio.sleep(60)
                    return [], {
                        "filing_type": filing_type,
                        "query": params,
                        "raw_hits": 0,
                        "limited_hits": 0,
                        "parsed_filings": 0,
                        "parse_failures": 0,
                        "classified_filings": 0,
                        "unclassified_filings": 0,
                        "rate_limited": True,
                    }
                response.raise_for_status()
                data = response.json()
        except httpx.RequestError as e:
            logger.error("SEC EDGAR request failed: %s", e)
            raise

        hits = data.get("hits", {}).get("hits", [])
        filings = [f for hit in hits[:limit] if (f := _parse_hit(hit)) is not None]
        logger.info("SEC EDGAR: %d filings for type '%s'", len(filings), filing_type)
        classified = [f for f in filings if f.situation_type]
        return filings, {
            "filing_type": filing_type,
            "query": params,
            "raw_hits": len(hits),
            "limited_hits": len(hits[:limit]),
            "parsed_filings": len(filings),
            "parse_failures": max(0, len(hits[:limit]) - len(filings)),
            "classified_filings": len(classified),
            "unclassified_filings": len(filings) - len(classified),
        }
