import asyncio
import logging
import re
from datetime import datetime, timezone

import httpx

from backend.services.marketplace.adapters.base import Listing, MarketplaceAdapter, PriceComparison
from backend.services.marketplace.price_engine import calculate_price_comparison

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.tutti.ch/de/q"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "de-CH,de;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}
_RATE_LIMIT_SECONDS = 5
_last_request: datetime | None = None


async def _rate_limit():
    global _last_request
    if _last_request is not None:
        elapsed = (datetime.now(timezone.utc) - _last_request).total_seconds()
        if elapsed < _RATE_LIMIT_SECONDS:
            await asyncio.sleep(_RATE_LIMIT_SECONDS - elapsed)
    _last_request = datetime.now(timezone.utc)


def _parse_price(text: str) -> float | None:
    """Extract numeric price from strings like 'CHF 350.–' or '350'."""
    cleaned = re.sub(r"[^\d.,]", "", text).replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_listings_from_html(html: str, marketplace: str = "tutti.ch") -> list[Listing]:
    """
    Minimal HTML parser for Tutti.ch search results.
    Tutti renders listings as JSON-LD and data attributes — we parse those.
    Falls back to regex if structure changes.
    """
    listings: list[Listing] = []

    # Try to extract from JSON-LD script blocks
    json_ld_pattern = re.compile(r'"name"\s*:\s*"([^"]+)".*?"price"\s*:\s*"?([\d.,]+)"?', re.DOTALL)
    url_pattern = re.compile(r'"url"\s*:\s*"(https://www\.tutti\.ch[^"]+)"')

    for match in json_ld_pattern.finditer(html):
        title = match.group(1)
        price = _parse_price(match.group(2))
        if price is None:
            continue
        url_match = url_pattern.search(html, match.start())
        url = url_match.group(1) if url_match else _SEARCH_URL
        listings.append(Listing(title=title, price=price, currency="CHF", url=url, marketplace=marketplace))

    return listings


class TuttiAdapter(MarketplaceAdapter):
    """
    Phase 1 adapter for Tutti.ch.
    search() and get_price() use HTTP scraping.
    create_listing() returns formatted copy-paste text only (no browser automation yet).
    """

    async def search(self, query: str, limit: int = 20, **filters) -> list[Listing]:
        await _rate_limit()
        params = {"q": query, "sort": "newest"}
        try:
            async with httpx.AsyncClient(
                headers=_HEADERS, follow_redirects=True, timeout=15
            ) as http:
                # Warm up the session cookie first
                await http.get("https://www.tutti.ch/de", timeout=10)
                response = await http.get(_SEARCH_URL, params=params)
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (403, 429):
                logger.warning("Tutti.ch blocked request (HTTP %s) — returning empty results", e.response.status_code)
                return []
            logger.warning("Tutti.ch returned %s for query '%s'", e.response.status_code, query)
            raise
        except httpx.RequestError as e:
            logger.error("Tutti.ch request failed: %s", e)
            raise

        listings = _parse_listings_from_html(response.text)
        return listings[:limit]

    async def get_price(self, query: str) -> PriceComparison:
        listings = await self.search(query, limit=50)
        return calculate_price_comparison(listings, currency="CHF")

    async def create_listing(self, item: dict) -> dict:
        """
        Phase 1: return formatted copy-paste text for Tutti.ch.
        item keys: title, description_de, price, condition, category
        """
        title = item.get("title", "")
        description = item.get("description_de", "")
        price = item.get("price", 0)
        condition = item.get("condition", "Gut")
        category = item.get("category", "")

        text = (
            f"**{title}**\n\n"
            f"{description}\n\n"
            f"Zustand: {condition}\n"
            f"Preis: CHF {price:.0f}\n"
        )
        if category:
            text += f"Kategorie: {category}\n"

        text += "\nBitte kontaktieren Sie mich für weitere Informationen."

        return {
            "status": "draft",
            "marketplace": "tutti.ch",
            "copy_paste_text": text,
            "listing_url": None,
            "note": "Phase 1: copy this text to https://www.tutti.ch/de/aufgeben",
        }

    async def get_listing_status(self, listing_id: str) -> str:
        return "unknown"

    async def health_check(self) -> dict:
        try:
            async with httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=10) as http:
                resp = await http.get("https://www.tutti.ch/de", timeout=10)
                if resp.status_code in (200, 301, 302):
                    return {"status": "ok", "message": "Tutti.ch reachable (scraping may be rate-limited)"}
                if resp.status_code in (403, 429):
                    return {"status": "warning", "message": f"Tutti.ch returned {resp.status_code} — anti-bot active, search returns empty results"}
                return {"status": "warning", "message": f"Tutti.ch returned HTTP {resp.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Tutti.ch unreachable: {e}"}
