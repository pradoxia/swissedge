from types import SimpleNamespace

import pytest

from backend.models.investment import SpecialSituation
from backend.services.investment import sec_detection
from backend.services.investment.sec_detection import classify_sec_p1_candidate, run_sec_edgar_detection
from backend.services.investment.sources.base import Filing


def _filing(filing_type: str, summary: str = "Official filing", accession: str = "0001") -> Filing:
    return Filing(
        company="Example Corp",
        ticker="EXM",
        filing_type=filing_type,
        date="2026-05-11",
        url=f"https://www.sec.gov/Archives/example/{accession}",
        summary=summary,
        cik="0000000001",
        accession_number=accession,
    )


def test_sc_to_t_classification():
    result = classify_sec_p1_candidate(_filing("SC TO-T", "Third-party acquisition tender offer"))
    assert result is not None
    assert result["situation_type"] == "merger_arbitrage"
    assert result["subtype"] == "acquisition_tender_offer"


def test_sc_to_i_classification():
    result = classify_sec_p1_candidate(_filing("SC TO-I", "Issuer self-tender offer"))
    assert result is not None
    assert result["situation_type"] == "tender_offer"
    assert result["subtype"] == "self_tender"


def test_form_10_classification():
    result = classify_sec_p1_candidate(_filing("Form 10", "SpinCo registration statement"))
    assert result is not None
    assert result["situation_type"] == "spin_off"
    assert result["subtype"] == "standard_spin_off"


@pytest.mark.parametrize("phrase", [
    "plan of liquidation",
    "plan of dissolution",
    "liquidation",
    "dissolution",
])
def test_8k_liquidation_dissolution_classification(phrase):
    result = classify_sec_p1_candidate(_filing("8-K", f"Company approved a {phrase}"))
    assert result is not None
    assert result["situation_type"] == "bankruptcy"
    assert result["subtype"] == "voluntary_liquidation"


def test_unsupported_form_skipped():
    assert classify_sec_p1_candidate(_filing("10-Q", "Quarterly report")) is None
    assert classify_sec_p1_candidate(_filing("DEF 14A", "Proxy statement")) is None


class FakeDb:
    def __init__(self):
        self.added = []
        self.flush_count = 0

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        self.flush_count += 1


class FakeAdapter:
    def __init__(self, filings, diagnostics=None):
        self.filings = filings
        self.diagnostics = diagnostics or {"by_form": {}}

    async def search_recent_with_diagnostics(self, hours_back: int):
        return self.filings, self.diagnostics


@pytest.mark.asyncio
async def test_duplicate_accession_skipped(monkeypatch):
    db = FakeDb()
    existing = SimpleNamespace(evaluation={"sec_detection": {"accession_number": "0001"}})

    async def fake_find_existing(_db, _filing):
        return existing

    monkeypatch.setattr(sec_detection, "_find_existing_situation", fake_find_existing)
    summary = await run_sec_edgar_detection(db, adapter=FakeAdapter([_filing("SC TO-T")]))

    assert summary["candidates_detected"] == 1
    assert summary["duplicates_skipped"] == 1
    assert summary["special_situations_created"] == 0
    assert db.added == []


@pytest.mark.asyncio
async def test_creates_special_situation_without_research_case(monkeypatch):
    db = FakeDb()

    async def fake_find_existing(_db, _filing):
        return None

    monkeypatch.setattr(sec_detection, "_find_existing_situation", fake_find_existing)
    summary = await run_sec_edgar_detection(db, adapter=FakeAdapter([_filing("Form 10")]))

    assert summary["special_situations_created"] == 1
    assert len(db.added) == 1
    assert isinstance(db.added[0], SpecialSituation)
    assert db.added[0].status == "detected"
    assert db.added[0].evaluation["detected_only"] is True


@pytest.mark.asyncio
async def test_backoff_events_in_summary(monkeypatch):
    db = FakeDb()

    async def fake_find_existing(_db, _filing):
        return None

    diagnostics = {
        "by_form": {
            "SC TO-T": {
                "rate_limited": True,
                "backoff": True,
                "backoff_status_code": 429,
                "backoff_seconds": 60.0,
            }
        }
    }
    monkeypatch.setattr(sec_detection, "_find_existing_situation", fake_find_existing)
    summary = await run_sec_edgar_detection(db, adapter=FakeAdapter([], diagnostics))

    assert summary["rate_limit_backoff_events"] == [{
        "filing_type": "SC TO-T",
        "rate_limited": True,
        "status_code": 429,
        "error": None,
        "backoff_seconds": 60.0,
    }]
