from datetime import datetime, timezone

import pytest

from backend.models.investment import SpecialSituation
from backend.services.investment import sec_false_detection_cleanup
from backend.services.investment.sec_false_detection_cleanup import (
    DELETE_CONFIRMATION,
    is_false_sec_detection_candidate,
    run_false_detection_cleanup,
)


def _situation(
    *,
    status: str = "detected",
    source: str = "sec_edgar",
    detected_only: bool = True,
    filing_date: str | None = "2007-05-10",
    detected_at: datetime = datetime(2026, 5, 11, 11, 36, tzinfo=timezone.utc),
) -> SpecialSituation:
    evaluation = {
        "source": source,
        "detected_only": detected_only,
        "sec_detection": {
            "filing_date": filing_date,
            "accession_number": "0001193125-07-123456",
        },
    }
    return SpecialSituation(
        situation_type="merger_arbitrage",
        company_name="Historical Corp",
        ticker="HIST",
        filing_type="SC TO-T",
        filing_url="https://www.sec.gov/Archives/old",
        status=status,
        detected_at=detected_at,
        evaluation=evaluation,
    )


def test_matches_historical_false_sec_detection_record():
    assert is_false_sec_detection_candidate(_situation()) is True


def test_does_not_match_good_may_2026_record():
    assert is_false_sec_detection_candidate(_situation(filing_date="2026-05-04")) is False
    assert is_false_sec_detection_candidate(_situation(filing_date="2026-05-08")) is False


@pytest.mark.parametrize("situation", [
    _situation(status="watchlist"),
    _situation(source="manual"),
    _situation(detected_only=False),
])
def test_does_not_match_watchlist_v2_or_manual_records(situation):
    assert is_false_sec_detection_candidate(situation) is False


def test_does_not_match_record_without_sec_detection():
    situation = _situation()
    situation.evaluation = {"source": "sec_edgar", "detected_only": True}
    assert is_false_sec_detection_candidate(situation) is False


class FakeDb:
    def __init__(self):
        self.deleted = []

    async def delete(self, item):
        self.deleted.append(item)


@pytest.mark.asyncio
async def test_dry_run_does_not_delete(monkeypatch):
    match = _situation()
    db = FakeDb()

    async def fake_find_false_sec_detections(_db):
        return [match]

    monkeypatch.setattr(sec_false_detection_cleanup, "find_false_sec_detections", fake_find_false_sec_detections)
    summary = await run_false_detection_cleanup(db)

    assert summary["dry_run"] is True
    assert summary["matched_count"] == 1
    assert summary["deleted_count"] == 0
    assert db.deleted == []


@pytest.mark.asyncio
async def test_delete_requires_explicit_confirmation(monkeypatch):
    match = _situation()
    db = FakeDb()

    async def fake_find_false_sec_detections(_db):
        return [match]

    monkeypatch.setattr(sec_false_detection_cleanup, "find_false_sec_detections", fake_find_false_sec_detections)
    summary = await run_false_detection_cleanup(db, delete=True, confirm="WRONG")

    assert summary["matched_count"] == 1
    assert summary["deleted_count"] == 0
    assert "error" in summary
    assert db.deleted == []


@pytest.mark.asyncio
async def test_delete_with_confirmation_deletes_only_matches(monkeypatch):
    match = _situation()
    db = FakeDb()

    async def fake_find_false_sec_detections(_db):
        return [match]

    monkeypatch.setattr(sec_false_detection_cleanup, "find_false_sec_detections", fake_find_false_sec_detections)
    summary = await run_false_detection_cleanup(db, delete=True, confirm=DELETE_CONFIRMATION)

    assert summary["matched_count"] == 1
    assert summary["deleted_count"] == 1
    assert db.deleted == [match]
