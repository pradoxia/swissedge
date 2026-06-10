"""Best-effort SEC company-facts enrichment (official source only).

Fetches `dei:EntityPublicFloat` from the SEC XBRL company-concept API to give
detected situations a size/competition context without a market-data provider.

Guardrails:
- Official SEC host only (data.sec.gov), proper User-Agent, conservative throttle.
- Best-effort: any failure returns None and never breaks a detection run.
- Output is descriptive market context, not a recommendation of any kind.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)

_COMPANY_CONCEPT_URL = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/dei/EntityPublicFloat.json"
_THROTTLE_SECONDS = 1.0
_TIMEOUT_SECONDS = 10
# Explainable, conservative threshold for the low-institutional-competition flag.
SMALL_COMPANY_PUBLIC_FLOAT_USD = 300_000_000


def _build_headers() -> dict:
    settings = get_settings()
    user_agent = settings.sec_user_agent or "SwissEdge/1.0 (contact@example.com)"
    return {"User-Agent": user_agent, "Accept": "application/json"}


def _latest_float_entry(data: dict) -> dict | None:
    units = data.get("units") or {}
    usd_entries = units.get("USD") or []
    if not isinstance(usd_entries, list) or not usd_entries:
        return None
    dated = [e for e in usd_entries if isinstance(e, dict) and e.get("end") and e.get("val") is not None]
    if not dated:
        return None
    return max(dated, key=lambda e: str(e.get("end")))


async def fetch_public_float(cik: str | None) -> dict[str, Any] | None:
    """Fetch latest reported public float for a CIK. Returns None on any failure."""
    if not cik or not str(cik).strip().isdigit():
        return None
    padded_cik = str(cik).strip().zfill(10)
    url = _COMPANY_CONCEPT_URL.format(cik=padded_cik)
    try:
        await asyncio.sleep(_THROTTLE_SECONDS)
        async with httpx.AsyncClient(headers=_build_headers(), timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return None
            data = response.json()
    except Exception as exc:  # best-effort by design
        logger.debug("SEC company facts fetch failed for CIK %s: %s", cik, exc)
        return None

    entry = _latest_float_entry(data)
    if entry is None:
        return None

    try:
        float_usd = float(entry["val"])
    except (TypeError, ValueError):
        return None

    return {
        "public_float_usd": float_usd,
        "as_of": entry.get("end"),
        "source": "sec_companyfacts",
        "source_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def build_competition_lens(public_float: dict[str, Any] | None) -> dict[str, Any]:
    """Derive an explainable low-institutional-competition flag from public float.

    This is a prioritization filter only — explicitly NOT an investment
    recommendation. Unknown data stays unknown.
    """
    if not public_float or public_float.get("public_float_usd") is None:
        return {
            "small_company_flag": None,
            "status": "unknown",
            "explanation": "Public float not available from SEC company facts; competition context unknown.",
            "disclaimer": "Prioritization context only. Not investment advice.",
        }
    float_usd = float(public_float["public_float_usd"])
    is_small = float_usd < SMALL_COMPANY_PUBLIC_FLOAT_USD
    return {
        "small_company_flag": is_small,
        "status": "derived",
        "public_float_usd": float_usd,
        "threshold_usd": SMALL_COMPANY_PUBLIC_FLOAT_USD,
        "as_of": public_float.get("as_of"),
        "explanation": (
            f"Public float ${float_usd:,.0f} is {'below' if is_small else 'at or above'} the "
            f"${SMALL_COMPANY_PUBLIC_FLOAT_USD:,.0f} threshold used as a proxy for low institutional competition. "
            "Float can be stale (reported in 10-K cover data) and is a size proxy, not a tradability judgment."
        ),
        "disclaimer": "Prioritization context only. Not investment advice.",
    }
