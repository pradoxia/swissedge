import uuid
from datetime import datetime, timezone

import pytest

from backend.api.investment import research_cases as research_api
from backend.api.investment import router as situation_api
from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase, ResearchDocument, ResearchSource
from backend.services.investment.documentation_agent import (
    build_research_case_documentation_report,
    build_special_situation_documentation_report,
)
from backend.services.investment.methodology_workspace import WORKSPACE_KEY


SEC_URL = "https://www.sec.gov/Archives/edgar/data/1/0001-index.htm"


def _situation(
    source_urls: list[str] | None = None,
    *,
    situation_type: str = "merger_arbitrage",
    filing_type: str = "SC TO-T",
    workspace: dict | None = None,
) -> SpecialSituation:
    evaluation = {
        "sec_detection": {
            "situation_type": situation_type,
            "detected_form_type": filing_type,
            "filing_url": SEC_URL,
            "accession_number": "0001",
            "cik": "1",
        }
    }
    if workspace is not None:
        evaluation[WORKSPACE_KEY] = workspace
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type=situation_type,
        company_name="Example Corp",
        ticker="EXM",
        filing_type=filing_type,
        filing_url=SEC_URL,
        detected_at=datetime.now(timezone.utc),
        status="detected",
        evaluation=evaluation,
        source_urls=source_urls if source_urls is not None else [SEC_URL],
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
                "company_name": "Example Corp",
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


class Result:
    def __init__(self, value):
        self.value = value

    def scalars(self):
        return self

    def first(self):
        return self.value


class FakeDb:
    def __init__(self, *values):
        self.values = list(values)
        self.added = []
        self.commits = 0

    async def execute(self, query):
        return Result(self.values.pop(0))

    def add(self, item):
        self.added.append(item)

    async def commit(self):
        self.commits += 1


@pytest.mark.asyncio
async def test_special_situation_documentation_agent_report_is_metadata_based():
    sit = _situation()

    report = await build_special_situation_documentation_report(str(sit.id), FakeDb(sit))

    assert report.subject_type == "special_situation"
    assert report.subject_id == str(sit.id)
    assert report.case_type == "merger_arbitrage"
    assert report.documentation_status in {"useful_incomplete", "mostly_documented", "ready_for_manual_review"}
    assert report.course_chapters
    assert "merger_arbitrage" in report.applicable_playbooks
    assert report.checklist
    assert report.documents_found
    assert report.documents_missing
    assert report.critical_missing_documents
    assert report.required_information
    assert report.required_skills
    assert report.implemented_skills
    assert report.missing_skills
    assert report.manual_actions
    assert report.suggested_searches
    assert report.next_best_action
    assert report.guardrails["read_only"] is True
    assert report.guardrails["no_live_ai"] is True
    assert report.guardrails["no_auto_promotion"] is True
    assert any("deterministic metadata" in warning for warning in report.warnings)


@pytest.mark.asyncio
async def test_research_case_documentation_agent_report_uses_existing_documents():
    rc = _research_case()

    report = await build_research_case_documentation_report(str(rc.id), FakeDb(rc))

    found_keys = {item["document_key"] for item in report.documents_found}
    assert report.subject_type == "research_case"
    assert report.subject_id == str(rc.id)
    assert report.case_type == "merger_arbitrage"
    assert "offer_to_purchase" in found_keys
    assert any(item["label"] == "Press Release" for item in report.documents_found)
    assert report.documentation_status in {"useful_incomplete", "mostly_documented", "ready_for_manual_review"}
    assert report.guardrails["metadata_only"] is True
    assert report.guardrails["no_auto_verification"] is True


@pytest.mark.asyncio
async def test_documentation_agent_endpoints_are_read_only():
    sit = _situation()
    rc = _research_case()
    sit_db = FakeDb(sit)
    rc_db = FakeDb(rc)

    sit_report = await situation_api.get_situation_documentation_agent_report(str(sit.id), db=sit_db)
    rc_report = await research_api.get_case_documentation_agent_report(str(rc.id), db=rc_db)

    assert sit_report.subject_type == "special_situation"
    assert rc_report.subject_type == "research_case"
    assert sit_db.added == []
    assert sit_db.commits == 0
    assert rc_db.added == []
    assert rc_db.commits == 0
    assert "post" not in situation_api.get_situation_documentation_agent_report.__name__
    assert "post" not in research_api.get_case_documentation_agent_report.__name__


@pytest.mark.asyncio
async def test_sc_to_i_found_maps_to_issuer_tender_statement_package():
    sit = _situation(situation_type="tender_offer", filing_type="SC TO-I")

    report = await build_special_situation_documentation_report(str(sit.id), FakeDb(sit))

    found_by_key = {item["document_key"]: item for item in report.documents_found}
    critical_missing_keys = {item["document_key"] for item in report.critical_missing_documents}
    assert "sc_to_i" in found_by_key
    assert "issuer_tender_statement" in found_by_key
    assert found_by_key["issuer_tender_statement"]["status"] == "found_metadata"
    assert found_by_key["issuer_tender_statement"]["verified"] is False
    assert "issuer_tender_statement" not in critical_missing_keys


@pytest.mark.asyncio
async def test_suggested_offer_to_purchase_does_not_make_tender_terms_ready():
    sit = _situation(
        situation_type="tender_offer",
        filing_type="SC TO-I",
        workspace={
            "required_resources": [
                {
                    "resource_id": "offer_to_purchase",
                    "title": "Offer to Purchase",
                    "source_type": "SEC exhibits",
                    "status": "missing",
                }
            ]
        },
    )

    report = await build_special_situation_documentation_report(str(sit.id), FakeDb(sit))

    offer = next(item for item in report.documents_missing if item["document_key"] == "offer_to_purchase")
    extract_terms = next(item for item in report.checklist if item["key"] == "extract_tender_terms")
    assert offer["status"] == "needs_manual_check"
    assert extract_terms["status"] == "needs_manual_check"
    assert extract_terms["verified"] is False
    assert report.documentation_status != "ready_for_manual_review"


@pytest.mark.asyncio
async def test_next_best_action_uses_existing_sec_filing_url_first():
    sit = _situation(situation_type="tender_offer", filing_type="SC TO-I")

    report = await build_special_situation_documentation_report(str(sit.id), FakeDb(sit))

    assert report.next_best_action == (
        "Open the existing SEC filing/detail directory first and inspect exhibits for Offer to Purchase, "
        "Letter of Transmittal, and amendments."
    )
    assert report.manual_actions[0] == report.next_best_action
    assert SEC_URL in report.manual_actions[1]


@pytest.mark.asyncio
async def test_manual_actions_are_deduplicated():
    sit = _situation(situation_type="tender_offer", filing_type="SC TO-I")

    report = await build_special_situation_documentation_report(str(sit.id), FakeDb(sit))

    assert len(report.manual_actions) == len(set(report.manual_actions))


@pytest.mark.asyncio
async def test_documentation_agent_never_marks_documents_verified():
    sit = _situation(situation_type="tender_offer", filing_type="SC TO-I")

    report = await build_special_situation_documentation_report(str(sit.id), FakeDb(sit))

    assert all(item["verified"] is False for item in report.documents_found)
    assert all(item["verified"] is False for item in report.documents_missing)
    assert all(item["verified"] is False for item in report.critical_missing_documents)
    assert all(item["verified"] is False for item in report.checklist)


@pytest.mark.asyncio
async def test_ready_for_manual_review_requires_no_critical_needs_manual_docs():
    sit = _situation(
        source_urls=[
            SEC_URL,
            "https://www.sec.gov/Archives/edgar/data/1/offer-to-purchase.htm",
            "https://www.sec.gov/Archives/edgar/data/1/letter-of-transmittal.htm",
            "https://www.sec.gov/Archives/edgar/data/1/press-release.htm",
        ],
        situation_type="tender_offer",
        filing_type="SC TO-I",
        workspace={
            "required_resources": [
                {
                    "resource_id": "offer_to_purchase",
                    "title": "Offer to Purchase",
                    "source_type": "SEC exhibits",
                    "status": "missing",
                }
            ]
        },
    )

    report = await build_special_situation_documentation_report(str(sit.id), FakeDb(sit))

    assert report.documentation_status != "ready_for_manual_review"
    assert any(item["document_key"] == "offer_to_purchase" for item in report.documents_missing)
