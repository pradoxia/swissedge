"""W1 tests — automatic SEC document acquisition + evidence mapping.

All network access is faked. No live SEC calls, no AI, no DB.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.models.investment import SpecialSituation
from backend.services.investment.auto_acquisition import (
    auto_acquire_for_created_situations,
    auto_acquire_situation_documents,
    _resource_title_variants,
)
from backend.services.investment.methodology_workspace import (
    WORKSPACE_KEY,
    attach_methodology_workspace_to_evidence,
)

FILING_URL = "https://www.sec.gov/Archives/edgar/data/1320017/000114036126024731/"

INDEX_HTML = """
<html><body><table>
<a href="/Archives/edgar/data/1320017/000114036126024731/sctot.htm">SC TO-T</a>
<a href="/Archives/edgar/data/1320017/000114036126024731/ex99a1a_offer.htm">EX-99.(a)(1)(A)</a>
<a href="/Archives/edgar/data/1320017/000114036126024731/ex2-1_merger.htm">EX-2.1</a>
<a href="/Archives/edgar/data/1320017/000114036126024731/ex99a5_press.htm">EX-99.(a)(5)</a>
<a href="/Archives/edgar/data/1320017/000114036126024731/form.xml">XML</a>
<a href="/Archives/edgar/data/1320017/000114036126024731/0001140361-26-024731-index.htm">Index</a>
<a href="https://evil.example.com/doc.htm">offsite</a>
</table></body></html>
"""

BODIES = {
    "sctot.htm": b"<html><body>SCHEDULE TO Tender Offer Statement SC TO-T filing under Section 14(d)(1)</body></html>",
    "ex99a1a_offer.htm": b"<html><body>OFFER TO PURCHASE for cash all outstanding shares of common stock</body></html>",
    "ex2-1_merger.htm": b"<html><body>AGREEMENT AND PLAN OF MERGER. This Merger Agreement defines closing conditions.</body></html>",
    "ex99a5_press.htm": b"<html><body>PRESS RELEASE: Target company announces tender offer commencement</body></html>",
}


async def fake_index_fetch(url: str) -> str:
    return INDEX_HTML


async def fake_body_fetch(url: str) -> tuple[bytes, str | None]:
    filename = url.rsplit("/", 1)[-1]
    if filename not in BODIES:
        raise RuntimeError(f"unexpected fetch: {url}")
    return BODIES[filename], "text/html"


def _make_situation(filing_url: str = FILING_URL) -> SpecialSituation:
    evidence = attach_methodology_workspace_to_evidence({
        "detected_only": True,
        "source": "sec_edgar",
        "sec_detection": {
            "situation_type": "merger_arbitrage",
            "subtype": "acquisition_tender_offer",
            "detected_form_type": "SC TO-T",
            "filing_url": filing_url,
            "cik": "1320017",
            "accession_number": "0001140361-26-024731",
            "filing_date": "2026-06-10",
        },
    })
    situation = SpecialSituation(
        situation_type="merger_arbitrage",
        company_name="Lisata Therapeutics, Inc.",
        ticker="LSTA",
        filing_type="SC TO-T",
        filing_url=filing_url,
        status="detected",
        evaluation=evidence,
        source_urls=[filing_url],
    )
    situation.id = uuid.uuid4()
    return situation


def _make_db(existing_urls: list[str] | None = None) -> AsyncMock:
    db = AsyncMock()
    result = MagicMock()
    result.all.return_value = [(url,) for url in (existing_urls or [])]
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


def _workspace(situation: SpecialSituation) -> dict:
    return situation.evaluation[WORKSPACE_KEY]


def _resource(workspace: dict, resource_id: str) -> dict:
    return next(r for r in workspace["required_resources"] if r["resource_id"] == resource_id)


def _check(workspace: dict, check_id: str) -> dict:
    return next(c for c in workspace["checklist"] if c["check_id"] == check_id)


class TestTitleVariants:
    def test_basic_title(self):
        assert "offer to purchase" in _resource_title_variants("Offer to Purchase")

    def test_slash_splits(self):
        variants = _resource_title_variants("Plan of liquidation / dissolution")
        assert "plan of liquidation" in variants
        assert "dissolution" in variants

    def test_stopwords_removed(self):
        variants = _resource_title_variants("SC 14D9 if available")
        assert any("14d9" in v or "14d 9" in v for v in variants)


@pytest.mark.asyncio
async def test_acquires_documents_and_maps_evidence_found():
    situation = _make_situation()
    db = _make_db()

    summary = await auto_acquire_situation_documents(
        db, situation, index_fetcher=fake_index_fetch, body_fetcher=fake_body_fetch
    )

    # 4 fetchable candidates (xml + index + offsite excluded)
    assert summary["documents_considered"] == 4
    assert summary["documents_acquired"] == 4
    assert summary["documents_failed"] == 0

    workspace = _workspace(situation)
    assert _resource(workspace, "ma_sc_to_t")["status"] == "evidence_found"
    assert _resource(workspace, "ma_offer_purchase")["status"] == "evidence_found"
    assert _resource(workspace, "ma_merger_agreement")["status"] == "evidence_found"

    refs = _resource(workspace, "ma_offer_purchase")["evidence_refs"]
    assert refs and refs[0]["verified"] is False
    assert refs[0]["human_review_required"] is True
    assert refs[0]["source"] == "auto_acquisition"

    # Related checks upgraded, never verified
    assert _check(workspace, "ma_offer_terms")["status"] == "evidence_found"
    assert _check(workspace, "ma_agreement")["status"] == "evidence_found"

    # Deal-term resources (offer price etc.) must NOT be auto-marked
    assert _resource(workspace, "ma_offer_price")["status"] == "missing"

    audit = workspace["auto_acquisition"]
    assert audit["verified"] is False
    assert audit["human_review_required"] is True


@pytest.mark.asyncio
async def test_non_sec_filing_url_is_skipped_entirely():
    situation = _make_situation(filing_url="https://example.com/not-sec")
    db = _make_db()
    fetch = AsyncMock()

    summary = await auto_acquire_situation_documents(
        db, situation, index_fetcher=fetch, body_fetcher=fetch
    )

    fetch.assert_not_called()
    assert summary["documents_acquired"] == 0
    assert any("skipped" in w.lower() for w in summary["warnings"])


@pytest.mark.asyncio
async def test_single_body_failure_does_not_break_batch():
    situation = _make_situation()
    db = _make_db()

    async def flaky_body_fetch(url: str) -> tuple[bytes, str | None]:
        if "merger" in url:
            raise RuntimeError("boom")
        return await fake_body_fetch(url)

    summary = await auto_acquire_situation_documents(
        db, situation, index_fetcher=fake_index_fetch, body_fetcher=flaky_body_fetch
    )

    assert summary["documents_acquired"] == 3
    assert summary["documents_failed"] == 1
    workspace = _workspace(situation)
    assert _resource(workspace, "ma_offer_purchase")["status"] == "evidence_found"
    assert _resource(workspace, "ma_merger_agreement")["status"] == "missing"


@pytest.mark.asyncio
async def test_existing_documents_are_not_refetched():
    situation = _make_situation()
    existing = f"{FILING_URL}ex99a1a_offer.htm"
    db = _make_db(existing_urls=[existing])

    summary = await auto_acquire_situation_documents(
        db, situation, index_fetcher=fake_index_fetch, body_fetcher=fake_body_fetch
    )

    assert summary["documents_acquired"] == 3  # offer doc skipped as existing


@pytest.mark.asyncio
async def test_created_situations_hook_is_capped_and_fail_safe():
    situations = {str(uuid.uuid4()): _make_situation() for _ in range(6)}
    entries = [{"id": key} for key in situations]

    db = _make_db()

    async def fake_get(model, situation_id):
        return situations.get(str(situation_id))

    db.get = AsyncMock(side_effect=fake_get)

    overall = await auto_acquire_for_created_situations(
        db, entries, index_fetcher=fake_index_fetch, body_fetcher=fake_body_fetch
    )

    assert overall["situations_processed"] == 5  # cap
    assert any("capped" in w for w in overall["warnings"])
    assert overall["documents_acquired"] == 20  # 4 docs x 5 situations


@pytest.mark.asyncio
async def test_hook_survives_per_situation_exception():
    good = _make_situation()
    entries = [{"id": str(uuid.uuid4())}, {"id": str(good.id)}]
    db = _make_db()

    async def get_side_effect(model, situation_id):
        if situation_id == good.id:
            return good
        raise RuntimeError("db hiccup")

    db.get = AsyncMock(side_effect=get_side_effect)

    overall = await auto_acquire_for_created_situations(
        db, entries, index_fetcher=fake_index_fetch, body_fetcher=fake_body_fetch
    )

    assert overall["situations_processed"] == 1
    assert any("failed safely" in w for w in overall["warnings"])
