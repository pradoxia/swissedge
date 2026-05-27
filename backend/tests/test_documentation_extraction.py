import uuid
from io import BytesIO
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException, UploadFile

from backend.models.investment import DocumentationExtractionField, SpecialSituation
from backend.services.investment import documentation_sources
from backend.services.investment.documentation_extraction import (
    extract_draft_fields,
    read_and_store_draft_fields,
    review_extraction_field,
)
from backend.services.investment.documentation_sources import (
    add_link_documentation_source,
    add_uploaded_document_source,
    list_documentation_sources,
)
from backend.services.investment.methodology_workspace import WORKSPACE_KEY


def _situation() -> SpecialSituation:
    candidate_id = "candidate-offer"
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type="tender_offer",
        company_name="Example Tender",
        ticker="EXM",
        filing_type="SC TO-I",
        filing_url="https://www.sec.gov/Archives/example/index.htm",
        detected_at=datetime.now(timezone.utc),
        status="detected",
        evaluation={
            "sec_detection": {"situation_type": "tender_offer", "detected_form_type": "SC TO-I"},
            WORKSPACE_KEY: {
                "resource_candidates": [
                    {
                        "resource_candidate_id": candidate_id,
                        "title": "Offer to Purchase candidate",
                        "url": "https://example.com/offer.htm",
                        "source_type": "sec_filing",
                        "status": "candidate_found",
                        "related_resource_ids": ["offer_to_purchase"],
                        "related_check_ids": ["extract_tender_terms"],
                    }
                ]
            },
        },
    )


def _empty_situation() -> SpecialSituation:
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type="tender_offer",
        company_name="Example Tender",
        ticker="EXM",
        filing_type="SC TO-I",
        filing_url="https://www.sec.gov/Archives/example/index.htm",
        detected_at=datetime.now(timezone.utc),
        status="detected",
        evaluation={
            "sec_detection": {"situation_type": "tender_offer", "detected_form_type": "SC TO-I"},
            WORKSPACE_KEY: {
                "required_resources": [{"resource_id": "offer_to_purchase", "status": "missing"}],
                "resource_candidates": [],
            },
        },
    )


class Result:
    def __init__(self, value):
        self.value = value

    def scalars(self):
        return self

    def first(self):
        return self.value[0] if isinstance(self.value, list) and self.value else self.value

    def all(self):
        return self.value if isinstance(self.value, list) else [self.value]


class FakeDb:
    def __init__(self, *values):
        self.values = list(values)
        self.added = []
        self.flush_count = 0

    async def execute(self, query):
        return Result(self.values.pop(0))

    def add(self, row):
        self.added.append(row)

    async def flush(self):
        self.flush_count += 1
        for row in self.added:
            if row.id is None:
                row.id = uuid.uuid4()


def test_tender_offer_extractor_finds_draft_fields():
    fields = extract_draft_fields(
        "The offer price is $10.50 per share. Withdrawal rights may be exercised before expiration. "
        "Odd-lot holders will not be subject to proration.",
        situation_type="tender_offer",
        document_key="offer_to_purchase",
    )

    keys = {field.field_key for field in fields}
    assert "offer_price" in keys
    assert "withdrawal_rights" in keys
    assert all(field.confidence < 1 for field in fields)


def test_source_link_creates_unverified_mapped_document():
    sit = _empty_situation()

    candidate = add_link_documentation_source(
        sit,
        url="https://example.com/offer.htm",
        document_key="offer_to_purchase",
        title="Offer to Purchase",
        source_type="source_link",
        related_required_resource_ids=["offer_to_purchase"],
        related_checklist_item_ids=["extract_tender_terms"],
    )
    grouped = list_documentation_sources(sit)

    assert candidate["verified"] is False
    assert candidate["status"] == "source_link_pending_review"
    assert candidate["resource_candidate_id"] in {
        item["resource_candidate_id"]
        for item in grouped["sources_by_document_key"]["offer_to_purchase"]
    }
    assert grouped["source_counts_by_document_key"]["offer_to_purchase"] == 1
    assert grouped["latest_source_by_document_key"]["offer_to_purchase"]["verified"] is False


@pytest.mark.asyncio
async def test_upload_source_creates_unverified_mapped_document_without_extraction(tmp_path, monkeypatch):
    monkeypatch.setattr(documentation_sources, "UPLOAD_ROOT", tmp_path)
    sit = _empty_situation()

    candidate = await add_uploaded_document_source(
        sit,
        file=UploadFile(filename="offer.txt", file=BytesIO(b"Offer price is $10.50 per share.")),
        document_key="offer_to_purchase",
        title="Offer to Purchase",
        related_required_resource_ids=["offer_to_purchase"],
        related_checklist_item_ids=["extract_tender_terms"],
    )

    assert candidate["verified"] is False
    assert candidate["status"] == "uploaded_pending_review"
    assert candidate["stored_path"]
    assert candidate["resource_candidate_id"] in [
        item["resource_candidate_id"]
        for item in sit.evaluation[WORKSPACE_KEY]["resource_candidates"]
    ]


@pytest.mark.asyncio
async def test_manual_read_stores_draft_fields_without_verification():
    sit = _situation()

    async def fetcher(url: str) -> str:
        assert url == "https://example.com/offer.htm"
        return "Offer price is $10.50 per share. The offer expires June 30, 2026."

    rows = await read_and_store_draft_fields(
        FakeDb(sit, []),
        sit.id,
        candidate_source_id="candidate-offer",
        document_key="offer_to_purchase",
        fetcher=fetcher,
    )

    assert rows
    assert all(row.status == "draft" for row in rows)
    assert all(row.reviewed_at is None for row in rows)
    assert all(row.document_key == "offer_to_purchase" for row in rows)


@pytest.mark.asyncio
async def test_manual_read_uploaded_text_source_stores_expected_tender_offer_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(documentation_sources, "UPLOAD_ROOT", tmp_path)
    sit = _empty_situation()
    candidate = await add_uploaded_document_source(
        sit,
        file=UploadFile(filename="offer.txt", file=BytesIO(b"Offer price is $10.50 per share. Source of funds will be cash on hand.")),
        document_key="offer_to_purchase",
        title="Offer to Purchase",
    )

    rows = await read_and_store_draft_fields(
        FakeDb(sit, []),
        sit.id,
        candidate_source_id=candidate["resource_candidate_id"],
        document_key="offer_to_purchase",
    )

    assert {row.field_key for row in rows} >= {"offer_price", "source_of_funds"}
    assert all(row.status == "draft" for row in rows)
    assert candidate["verified"] is False
    assert candidate["status"] == "draft_extracted"


@pytest.mark.asyncio
async def test_url_only_extract_requires_manual_endpoint_call():
    sit = _situation()
    assert not sit.evaluation[WORKSPACE_KEY].get("documentation_extractions")


@pytest.mark.asyncio
async def test_pdf_upload_returns_reader_warning(tmp_path, monkeypatch):
    monkeypatch.setattr(documentation_sources, "UPLOAD_ROOT", tmp_path)
    sit = _empty_situation()
    candidate = await add_uploaded_document_source(
        sit,
        file=UploadFile(filename="offer.pdf", file=BytesIO(b"%PDF fake")),
        document_key="offer_to_purchase",
        title="Offer PDF",
    )

    with pytest.raises(HTTPException) as exc:
        await read_and_store_draft_fields(
            FakeDb(sit),
            sit.id,
            candidate_source_id=candidate["resource_candidate_id"],
            document_key="offer_to_purchase",
        )

    assert "Upload a text/HTML version or add the SEC exhibit link if readable" in exc.value.detail
    assert candidate["verified"] is False


@pytest.mark.asyncio
async def test_manual_read_requires_candidate_document_mapping():
    sit = _situation()

    with pytest.raises(Exception):
        await read_and_store_draft_fields(
            FakeDb(sit),
            sit.id,
            candidate_source_id="candidate-offer",
            document_key="letter_of_transmittal",
            fetcher=lambda url: None,
        )


@pytest.mark.asyncio
async def test_review_field_accept_edit_reject_only_changes_extraction_row():
    row = DocumentationExtractionField(
        id=uuid.uuid4(),
        situation_id=uuid.uuid4(),
        candidate_source_id="candidate-offer",
        document_key="offer_to_purchase",
        field_key="offer_price",
        field_label="Offer price",
        extracted_value="$10.50 per share",
        status="draft",
    )

    updated = await review_extraction_field(
        FakeDb([row]),
        row.id,
        status="edited",
        extracted_value="$10.50",
        reviewed_by="Dani",
    )

    assert updated.status == "edited"
    assert updated.extracted_value == "$10.50"
    assert updated.reviewed_by == "Dani"
    assert updated.reviewed_at is not None
