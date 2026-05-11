import uuid

import pytest

from backend.models.investment import SpecialSituation
from backend.api.investment.router import _serialize
from backend.services.investment.methodology_workspace import WORKSPACE_KEY, attach_methodology_workspace_to_evidence
from backend.services.investment.resource_scout import (
    add_manual_resource_candidate,
    run_resource_scout,
    scout_special_situation,
    update_resource_candidate_review,
    update_workflow_status,
)


def _evaluation(filing_type="SC TO-T", situation_type="merger_arbitrage", subtype="acquisition_tender_offer"):
    evidence = {
        "source": "sec_edgar",
        "detected_only": True,
        "sec_detection": {
            "accession_number": "0001140361-26-019536",
            "cik": "0001829280",
            "filing_url": "https://www.sec.gov/Archives/edgar/data/1829280/000114036126019536/filing.htm",
            "filing_date": "2026-05-08",
            "detected_form_type": filing_type,
            "situation_type": situation_type,
            "subtype": subtype,
            "selected_playbook": "merger_arbitrage.md",
        },
    }
    return attach_methodology_workspace_to_evidence(evidence)


def _situation(**kwargs):
    return SpecialSituation(
        id=kwargs.get("id", uuid.uuid4()),
        situation_type=kwargs.get("situation_type", "merger_arbitrage"),
        company_name=kwargs.get("company_name", "Forian Inc."),
        ticker=kwargs.get("ticker", "FORA"),
        filing_type=kwargs.get("filing_type", "SC TO-T"),
        filing_url=kwargs.get("filing_url", "https://www.sec.gov/Archives/edgar/data/1829280/000114036126019536/filing.htm"),
        status=kwargs.get("status", "detected"),
        evaluation=kwargs.get("evaluation", _evaluation()),
    )


def test_resource_scout_creates_sec_filing_candidate_and_queries():
    sit = _situation()
    summary = scout_special_situation(sit, apply=True)
    workspace = sit.evaluation[WORKSPACE_KEY]

    assert summary["candidates_created"] >= 1
    assert any(c["source_type"] == "sec_filing" for c in workspace["resource_candidates"])
    assert any("investor relations" in q for q in summary["search_queries_suggested"])


def test_resource_scout_does_not_duplicate_existing_candidates():
    sit = _situation()
    first = scout_special_situation(sit, apply=True)
    second = scout_special_situation(sit, apply=True)

    assert first["candidates_created"] >= 1
    assert second["candidates_created"] == 0
    assert second["candidates_existing"] >= 1


def test_second_dry_run_after_apply_reports_existing_candidates():
    sit = _situation()
    scout_special_situation(sit, apply=True)
    dry_run = scout_special_situation(sit, apply=False)

    assert dry_run["candidates_created"] == 0
    assert dry_run["candidates_existing"] >= 1
    assert dry_run["required_resources_updated"] == 0


def test_resource_scout_updates_required_resource_status_only_to_candidate_found():
    sit = _situation()
    scout_special_situation(sit, apply=True)
    workspace = sit.evaluation[WORKSPACE_KEY]
    resource = next(item for item in workspace["required_resources"] if item["resource_id"] == "ma_sc_to_t")

    assert resource["status"] == "candidate_found"
    assert all(item["status"] != "verified" for item in workspace["checklist"])


def test_resource_scout_apply_reassigns_evaluation_json_for_jsonb_tracking():
    sit = _situation()
    original_evaluation = sit.evaluation

    scout_special_situation(sit, apply=True)

    assert sit.evaluation is not original_evaluation
    assert "resource_candidates" in sit.evaluation[WORKSPACE_KEY]
    assert "search_suggestions" in sit.evaluation[WORKSPACE_KEY]


def test_api_serialization_includes_resource_candidates_and_search_suggestions():
    sit = _situation()
    scout_special_situation(sit, apply=True)

    payload = _serialize(sit)

    workspace = payload["methodology_workspace"]
    assert workspace["resource_candidates"]
    assert workspace["search_suggestions"]
    assert any(item["status"] == "candidate_found" for item in workspace["required_resources"])


def test_resource_scout_dry_run_does_not_write():
    sit = _situation()
    summary = scout_special_situation(sit, apply=False)

    assert summary["candidates_created"] >= 1
    assert "resource_candidates" not in sit.evaluation[WORKSPACE_KEY]


class FakeScalars:
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items

    def first(self):
        return self.items[0] if self.items else None


class FakeResult:
    def __init__(self, items):
        self.items = items

    def scalars(self):
        return FakeScalars(self.items)


class FakeDb:
    def __init__(self, items):
        self.items = items
        self.flush_count = 0

    async def execute(self, _query):
        return FakeResult(self.items)

    async def flush(self):
        self.flush_count += 1


@pytest.mark.asyncio
async def test_run_resource_scout_apply_writes_only_targeted_situation():
    targeted = _situation(id=uuid.uuid4())
    other = _situation(id=uuid.uuid4(), company_name="Other Corp")
    db = FakeDb([targeted, other])

    summary = await run_resource_scout(db, situation_id=str(targeted.id), apply=True)

    assert summary["count"] == 1
    assert "resource_candidates" in targeted.evaluation[WORKSPACE_KEY]
    assert "resource_candidates" not in other.evaluation[WORKSPACE_KEY]
    assert db.flush_count == 1


@pytest.mark.asyncio
async def test_batch_limit_is_capped():
    db = FakeDb([_situation(id=uuid.uuid4()) for _ in range(30)])

    summary = await run_resource_scout(db, limit=100, apply=False)

    assert summary["limit"] == 25


def test_manual_resource_add_validates_url():
    sit = _situation()
    with pytest.raises(ValueError):
        add_manual_resource_candidate(
            sit,
            title="Bad URL",
            url="ftp://example.com/file.pdf",
            source_type="pdf_link",
        )


def test_manual_resource_add_updates_workspace_without_fetching():
    sit = _situation()
    result = add_manual_resource_candidate(
        sit,
        title="Investor relations page",
        url="https://example.com/investors",
        source_type="company_ir",
        related_resource_ids=["ma_target_release"],
    )

    assert result["created"] is True
    assert sit.evaluation[WORKSPACE_KEY]["resource_candidates"][0]["url"] == "https://example.com/investors"


def test_manual_resource_add_can_generate_title_from_domain():
    sit = _situation()
    result = add_manual_resource_candidate(
        sit,
        title=None,
        url="https://example.com/investors",
        source_type="company_ir",
    )

    assert result["created"] is True
    assert result["candidate"]["title"] == "example.com"


def test_workflow_status_update_valid_status_preserves_existing_evaluation():
    sit = _situation()
    original_sec_detection = dict(sit.evaluation["sec_detection"])

    workspace = update_workflow_status(sit, "needs_resources")

    assert workspace["workflow_status"] == "needs_resources"
    assert sit.evaluation["sec_detection"] == original_sec_detection
    assert sit.evaluation[WORKSPACE_KEY]["progress"]["total_checks"] > 0


def test_workflow_status_update_rejects_invalid_status():
    sit = _situation()

    with pytest.raises(ValueError):
        update_workflow_status(sit, "evaluated")


def test_resource_review_evidence_found_updates_links_without_verifying():
    sit = _situation()
    add_manual_resource_candidate(
        sit,
        title="Offer to Purchase",
        url="https://example.com/offer.pdf",
        source_type="offer_document",
        related_resource_ids=["ma_offer_purchase"],
        related_check_ids=["ma_offer_terms"],
    )
    candidate = sit.evaluation[WORKSPACE_KEY]["resource_candidates"][0]

    result = update_resource_candidate_review(
        sit,
        resource_candidate_id=candidate["resource_candidate_id"],
        status="evidence_found",
    )
    workspace = result["workspace"]
    required = next(item for item in workspace["required_resources"] if item["resource_id"] == "ma_offer_purchase")
    check = next(item for item in workspace["checklist"] if item["check_id"] == "ma_offer_terms")

    assert result["candidate"]["status"] == "evidence_found"
    assert required["status"] == "evidence_found"
    assert check["status"] == "evidence_found"
    assert check["status"] != "verified"
    assert workspace["progress"]["evidence_found"] >= 1


def test_resource_review_rejects_candidate_without_deleting():
    sit = _situation()
    add_manual_resource_candidate(
        sit,
        title="Bad link",
        url="https://example.com/bad",
        source_type="other",
    )
    candidate_id = sit.evaluation[WORKSPACE_KEY]["resource_candidates"][0]["resource_candidate_id"]

    update_resource_candidate_review(
        sit,
        resource_candidate_id=candidate_id,
        status="rejected",
        notes="Wrong company.",
    )

    candidate = sit.evaluation[WORKSPACE_KEY]["resource_candidates"][0]
    assert candidate["status"] == "rejected"
    assert candidate["notes"] == "Wrong company."
    assert len(sit.evaluation[WORKSPACE_KEY]["resource_candidates"]) == 1


def test_resource_review_rejects_verified_status_and_missing_workspace():
    sit = _situation()
    add_manual_resource_candidate(
        sit,
        title="Link",
        url="https://example.com/link",
        source_type="other",
    )
    candidate_id = sit.evaluation[WORKSPACE_KEY]["resource_candidates"][0]["resource_candidate_id"]

    with pytest.raises(ValueError):
        update_resource_candidate_review(sit, resource_candidate_id=candidate_id, status="verified")

    unsupported = _situation(evaluation={"source": "manual"})
    with pytest.raises(ValueError):
        update_workflow_status(unsupported, "needs_resources")


def test_resource_review_can_relink_candidate_and_recalculate_candidate_count():
    sit = _situation()
    add_manual_resource_candidate(
        sit,
        title="Investor relations",
        url="https://example.com/ir",
        source_type="company_ir",
    )
    candidate_id = sit.evaluation[WORKSPACE_KEY]["resource_candidates"][0]["resource_candidate_id"]

    update_resource_candidate_review(
        sit,
        resource_candidate_id=candidate_id,
        status="candidate_found",
        related_resource_ids=["ma_target_release"],
        related_check_ids=["ma_target_response"],
    )

    workspace = sit.evaluation[WORKSPACE_KEY]
    candidate = workspace["resource_candidates"][0]
    assert candidate["related_resource_ids"] == ["ma_target_release"]
    assert candidate["related_check_ids"] == ["ma_target_response"]
    assert workspace["progress"]["candidate_resources"] == 1


def test_watchlist_manual_record_not_changed_by_unsupported_workspace():
    sit = _situation(status="watchlist", evaluation={"source": "manual"})
    summary = scout_special_situation(sit, apply=True)

    assert summary["errors"] == ["methodology_workspace_missing_or_unsupported"]
    assert sit.evaluation == {"source": "manual"}
