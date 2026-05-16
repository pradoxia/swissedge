import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from backend.api.investment import research_cases as research_api
from backend.api.investment import router as situation_api
from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase, ResearchDocument, ResearchSource
from backend.services.investment.document_package import (
    build_research_case_document_package,
    build_situation_document_package,
)
from backend.services.investment.evidence_links import (
    build_research_case_evidence_links,
    build_situation_evidence_links,
)
from backend.services.investment.sec_document_acquisition import (
    build_research_case_sec_document_acquisition_preview,
    build_situation_sec_document_acquisition_preview,
)


SEC_URL = "https://www.sec.gov/Archives/edgar/data/1/0001-index.htm"


def _situation(situation_type: str = "merger_arbitrage") -> SpecialSituation:
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type=situation_type,
        company_name="Example Corp",
        ticker="EXM",
        filing_type="SC TO-T",
        filing_url=SEC_URL,
        detected_at=datetime.now(timezone.utc),
        status="detected",
        evaluation={
            "sec_detection": {
                "situation_type": situation_type,
                "detected_form_type": "SC TO-T",
                "filing_url": SEC_URL,
                "accession_number": "0001",
                "cik": "1",
            }
        },
        source_urls=[SEC_URL],
    )


def _research_case() -> ResearchCase:
    rc = ResearchCase(
        id=uuid.uuid4(),
        status="under_investigation",
        brief={
            "title": "Example Corp SC TO-T",
            "detection_summary": {
                "situation_type": "merger_arbitrage",
                "filing_type": "SC TO-T",
                "filing_url": SEC_URL,
                "accession_number": "0001",
            },
        },
    )
    rc.documents = [
        ResearchDocument(
            research_case_id=rc.id,
            doc_type="offer_to_purchase",
            title="Offer to Purchase",
            url="https://www.sec.gov/Archives/edgar/data/1/offer.htm",
        )
    ]
    rc.sources = [
        ResearchSource(
            research_case_id=rc.id,
            source_name="Company press release",
            source_url="https://example.com/press-release",
            signal_quality="medium",
        )
    ]
    return rc


def test_situation_document_package_marks_sec_filing_found_not_verified():
    sit = _situation()
    evidence = build_situation_evidence_links(sit)
    sec_preview = build_situation_sec_document_acquisition_preview(sit)

    package = build_situation_document_package(sit, evidence_links=evidence, sec_preview=sec_preview)

    sc_to_t = next(item for item in package.documents if item.document_key == "sc_to_t")
    assert sc_to_t.status in {"found", "suggested"}
    assert sc_to_t.verified is False
    assert package.summary.required_missing >= 1
    assert "Ready for manual evaluation does not mean investment approval." in package.guardrails


def test_research_case_document_package_matches_documents_and_sources():
    rc = _research_case()
    evidence = build_research_case_evidence_links(rc)
    sec_preview = build_research_case_sec_document_acquisition_preview(rc)

    package = build_research_case_document_package(rc, evidence_links=evidence, sec_preview=sec_preview)

    offer = next(item for item in package.documents if item.document_key == "offer_to_purchase")
    press = next(item for item in package.documents if item.document_key == "press_release")
    assert offer.status == "found"
    assert press.status == "found"
    assert package.readiness_level in {"useful_incomplete", "mostly_ready", "ready_for_manual_evaluation"}


@pytest.mark.asyncio
async def test_situation_document_package_api(monkeypatch):
    sit = _situation()

    class Result:
        def scalars(self):
            return self
        def first(self):
            return sit

    class FakeDb:
        async def execute(self, query):
            return Result()

    package = await situation_api.get_situation_document_package(str(sit.id), db=FakeDb())

    assert package.case_id == str(sit.id)
    assert package.case_type == "special_situation"


@pytest.mark.asyncio
async def test_research_case_document_package_api():
    rc = _research_case()

    class Result:
        def __init__(self, value):
            self.value = value
        def scalars(self):
            return self
        def first(self):
            return self.value

    class FakeDb:
        async def execute(self, query):
            return Result(rc)

    package = await research_api.get_case_document_package(str(rc.id), db=FakeDb())

    assert package.case_id == str(rc.id)
    assert package.case_type == "research_case"


def test_document_package_api_functions_are_read_only():
    assert "post" not in situation_api.get_situation_document_package.__name__
    assert "post" not in research_api.get_case_document_package.__name__
