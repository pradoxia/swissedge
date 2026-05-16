import uuid
from datetime import datetime, timezone

import pytest

from backend.api.investment import router as situation_api
from backend.models.investment import SpecialSituation
from backend.services.investment.document_package import build_situation_document_package
from backend.services.investment.evidence_links import build_situation_evidence_links
from backend.services.investment.promotion_readiness import build_promotion_readiness_package
from backend.services.investment.sec_document_acquisition import build_situation_sec_document_acquisition_preview


SEC_URL = "https://www.sec.gov/Archives/edgar/data/1/0001-index.htm"


def _situation(
    *,
    filing_url: str | None = SEC_URL,
    source_urls: list[str] | None = None,
    situation_type: str | None = "merger_arbitrage",
) -> SpecialSituation:
    sec_detection = {
        "situation_type": situation_type,
        "detected_form_type": "SC TO-T",
        "filing_url": filing_url,
        "accession_number": "0001" if filing_url else None,
        "cik": "1" if filing_url else None,
    }
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type=situation_type,
        company_name="Example Corp",
        ticker="EXM",
        filing_type="SC TO-T" if filing_url else None,
        filing_url=filing_url,
        detected_at=datetime.now(timezone.utc),
        status="detected",
        evaluation={"sec_detection": sec_detection},
        source_urls=source_urls if source_urls is not None else ([filing_url] if filing_url else []),
    )


def _readiness(sit: SpecialSituation):
    evidence = build_situation_evidence_links(sit)
    sec_preview = build_situation_sec_document_acquisition_preview(sit)
    documents = build_situation_document_package(sit, evidence_links=evidence, sec_preview=sec_preview)
    return build_promotion_readiness_package(sit, document_package=documents, evidence_links=evidence)


def test_promotion_readiness_not_ready_without_sec_context():
    package = _readiness(_situation(filing_url=None, source_urls=[]))

    assert package.readiness_level == "not_ready"
    assert "SEC filing identifiers are incomplete." in package.blocking_reasons
    assert "No supporting evidence links are available." in package.blocking_reasons
    assert package.readiness_score < 50


def test_promotion_readiness_needs_documentation_with_missing_required_docs():
    package = _readiness(_situation())

    assert package.readiness_level == "needs_documentation"
    assert package.missing_required_documents
    assert "Required documents are still missing or need manual check." in package.blocking_reasons
    assert package.recommended_next_step.startswith("Find or manually confirm")


def test_promotion_readiness_ready_for_manual_promotion_when_required_docs_present():
    sit = _situation(source_urls=[
        SEC_URL,
        "https://www.sec.gov/Archives/edgar/data/1/offer to purchase.htm",
        "https://www.sec.gov/Archives/edgar/data/1/schedule 14d-9.htm",
        "https://www.sec.gov/Archives/edgar/data/1/merger agreement.htm",
    ])

    package = _readiness(sit)

    assert package.readiness_level == "ready_for_manual_promotion"
    assert package.missing_required_documents == []
    assert package.blocking_reasons == []
    assert package.readiness_score >= 80
    assert "does not mean investment approval" in " ".join(package.warnings)


@pytest.mark.asyncio
async def test_promotion_readiness_endpoint_is_read_only_and_does_not_mutate():
    sit = _situation()

    class Result:
        def scalars(self):
            return self

        def first(self):
            return sit

    class FakeDb:
        def __init__(self):
            self.added = []
            self.commits = 0

        async def execute(self, query):
            return Result()

        def add(self, item):
            self.added.append(item)

        async def commit(self):
            self.commits += 1

    db = FakeDb()
    before = {
        "status": sit.status,
        "evaluation": sit.evaluation.copy(),
        "source_urls": list(sit.source_urls),
    }

    package = await situation_api.get_situation_promotion_readiness(str(sit.id), db=db)

    assert package.situation_id == str(sit.id)
    assert db.added == []
    assert db.commits == 0
    assert sit.status == before["status"]
    assert sit.evaluation == before["evaluation"]
    assert sit.source_urls == before["source_urls"]
