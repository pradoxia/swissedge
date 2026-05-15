from __future__ import annotations

import inspect
import json
import uuid

import pytest

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.services.investment import sec_document_acquisition as module
from backend.services.investment.methodology_workspace import WORKSPACE_KEY
from backend.services.investment.sec_document_acquisition import (
    acquire_sec_documents_from_preview,
    apply_research_case_sec_acquisition_metadata,
    apply_situation_sec_acquisition_metadata,
    build_research_case_sec_document_acquisition_preview,
    build_situation_sec_document_acquisition_preview,
)

SEC_URL = "https://www.sec.gov/Archives/edgar/data/1829280/000114036126019536/formsc-to.htm"


def _workspace(*, missing: bool = True) -> dict:
    return {
        "template_key": "tender_offer",
        "required_resources": [
            {
                "resource_id": "offer_document",
                "title": "Offer document",
                "source_type": "offer_document",
                "status": "missing" if missing else "evidence_found",
            }
        ],
        "resource_candidates": [],
        "checklist": [
            {"check_id": "offer_terms", "title": "Offer terms", "status": "needs_evidence"},
        ],
    }


def _situation(*, filing_url: str | None = SEC_URL) -> SpecialSituation:
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type="tender_offer",
        company_name="Forian Inc.",
        ticker="FORA",
        filing_type="SC TO-I",
        filing_url=filing_url,
        evaluation={
            "sec_detection": {
                "filing_url": filing_url,
                "cik": "0001829280",
                "accession_number": "0001140361-26-019536",
                "filing_type": "SC TO-I",
                "filing_date": "2026-05-13",
                "company_name": "Forian Inc.",
                "ticker": "FORA",
            },
            WORKSPACE_KEY: _workspace(),
        },
    )


def _case(*, filing_url: str | None = SEC_URL) -> ResearchCase:
    rc = ResearchCase(
        id=uuid.uuid4(),
        status="under_investigation",
        brief={
            "title": "Forian Inc. SC TO-I",
            "detection_summary": {
                "filing_url": filing_url,
                "cik": "0001829280",
                "accession_number": "0001140361-26-019536",
                "filing_type": "SC TO-I",
                "filing_date": "2026-05-13",
                "company_name": "Forian Inc.",
                "ticker": "FORA",
            },
            "methodology_workspace_snapshot": _workspace(),
        },
    )
    rc.documents = []
    rc.sources = []
    rc.tasks = []
    return rc


def _text(value) -> str:
    return json.dumps(value.model_dump() if hasattr(value, "model_dump") else value).lower()


def test_preview_with_complete_sec_metadata():
    package = build_situation_sec_document_acquisition_preview(_situation())

    assert package.available_identifiers.cik == "0001829280"
    assert package.available_identifiers.accession_number == "0001140361-26-019536"
    assert package.missing_identifiers == []
    assert package.official_links
    assert package.official_links[0].verified is False
    assert package.official_links[0].human_review_required is True


def test_preview_with_missing_metadata():
    situation = _situation(filing_url=None)
    situation.evaluation["sec_detection"].pop("cik")

    package = build_situation_sec_document_acquisition_preview(situation)

    assert "filing_url" in package.missing_identifiers
    assert "cik" in package.missing_identifiers
    assert package.official_links == []
    assert package.copyable_queries


@pytest.mark.asyncio
async def test_post_acquisition_safely_handles_non_sec_url():
    preview = build_situation_sec_document_acquisition_preview(_situation(filing_url="https://example.com/filing.htm"))
    called = False

    async def fetcher(url: str) -> str:
        nonlocal called
        called = True
        return ""

    package = await acquire_sec_documents_from_preview(preview, fetcher=fetcher)

    assert called is False
    assert package.acquired_documents == []
    assert any("no official sec.gov" in warning.lower() for warning in package.warnings)


@pytest.mark.asyncio
async def test_post_creates_metadata_candidates_not_verified_evidence():
    html = '<html><body><a href="/Archives/edgar/data/1829280/000114036126019536/ex-99.htm">exhibit</a></body></html>'
    preview = build_situation_sec_document_acquisition_preview(_situation())

    async def fetcher(url: str) -> str:
        assert url == SEC_URL
        return html

    package = await acquire_sec_documents_from_preview(preview, fetcher=fetcher)

    assert package.acquired_documents
    assert all(doc.verified is False for doc in package.acquired_documents)
    assert all(doc.human_review_required is True for doc in package.acquired_documents)
    assert "body" not in _text(package)


@pytest.mark.asyncio
async def test_situation_storage_does_not_complete_checklist_or_verify():
    situation = _situation()
    preview = build_situation_sec_document_acquisition_preview(situation)

    async def fetcher(url: str) -> str:
        return '<a href="/Archives/edgar/data/1829280/000114036126019536/offer.htm">offer</a>'

    package = await acquire_sec_documents_from_preview(preview, fetcher=fetcher)
    stored = apply_situation_sec_acquisition_metadata(situation, package)
    workspace = situation.evaluation[WORKSPACE_KEY]

    assert stored
    assert workspace["checklist"][0]["status"] == "needs_evidence"
    assert workspace["required_resources"][0]["status"] == "missing"
    assert stored[0]["status"] == "candidate_found"
    assert stored[0]["verified"] is False


@pytest.mark.asyncio
async def test_research_case_storage_creates_documents_and_sources_only():
    rc = _case()
    preview = build_research_case_sec_document_acquisition_preview(rc)

    async def fetcher(url: str) -> str:
        return '<a href="/Archives/edgar/data/1829280/000114036126019536/offer.htm">offer</a>'

    package = await acquire_sec_documents_from_preview(preview, fetcher=fetcher)
    stored = apply_research_case_sec_acquisition_metadata(rc, package)

    assert len(stored) == 2
    assert rc.situation_id is None
    assert all("Human review required" in (getattr(item, "summary", None) or getattr(item, "notes", "")) for item in stored)
    assert all(record["verified"] is False for record in package.stored_records)


def test_no_investment_action_language():
    package = build_situation_sec_document_acquisition_preview(_situation())
    text = _text(package)

    assert "buy" not in text
    assert "sell" not in text
    assert "hold" not in text
    assert "recommendation" not in text


def test_no_scan_ai_evaluator_or_scheduler_behavior_in_service():
    source = inspect.getsource(module)
    banned = ["evaluate_situation", "run_v2", "/api/investment/scan", "scheduler", "cron", "openai", "anthropic"]
    assert not any(token in source.lower() for token in banned)


def test_network_client_is_restricted_to_sec_acquisition_service():
    source = inspect.getsource(module)

    assert "httpx.AsyncClient" in source
    assert "SEC_HOSTS" in source
    assert "_is_sec_url" in source
