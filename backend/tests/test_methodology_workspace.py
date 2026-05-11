import pytest

from backend.models.investment import SpecialSituation
from backend.services.investment import methodology_workspace
from backend.services.investment.methodology_workspace import (
    WORKSPACE_KEY,
    attach_methodology_workspace_backfill,
    attach_methodology_workspace_to_evidence,
    build_methodology_workspace,
    select_methodology_template,
)
from backend.services.investment.sec_detection import _build_minimal_evidence
from backend.services.investment.sources.base import Filing


@pytest.mark.parametrize(
    ("situation_type", "subtype", "filing_type", "template_key"),
    [
        ("merger_arbitrage", "acquisition_tender_offer", "SC TO-T", "merger_arbitrage_acquisition_tender"),
        ("tender_offer", "self_tender", "SC TO-I", "tender_offer_self_tender"),
        ("spin_off", "standard_spin_off", "Form 10", "spin_off_standard"),
        ("bankruptcy", "voluntary_liquidation", "8-K", "liquidation_or_dissolution_voluntary"),
    ],
)
def test_selects_expected_template(situation_type, subtype, filing_type, template_key):
    template = select_methodology_template(
        situation_type=situation_type,
        subtype=subtype,
        filing_type=filing_type,
    )

    assert template is not None
    assert template["template_key"] == template_key


def test_default_checklist_statuses_are_not_verified():
    workspace = build_methodology_workspace(
        situation_type="merger_arbitrage",
        subtype="acquisition_tender_offer",
        filing_type="SC TO-T",
    )

    assert workspace is not None
    statuses = {item["status"] for item in workspace["checklist"]}
    assert statuses <= {"not_started", "needs_evidence"}
    assert "verified" not in statuses
    assert workspace["progress"]["verified_checks"] == 0


def test_required_resources_generated():
    workspace = build_methodology_workspace(
        situation_type="tender_offer",
        subtype="self_tender",
        filing_type="SC TO-I",
    )

    assert workspace is not None
    resources = workspace["required_resources"]
    assert len(resources) >= 5
    assert all(item["status"] == "missing" for item in resources)
    assert any(item["required_or_optional"] == "required" for item in resources)


def test_attach_workspace_to_new_sec_detection_evidence():
    filing = Filing(
        company="Example Corp",
        ticker="EXM",
        filing_type="SC TO-T",
        date="2026-05-11",
        url="https://www.sec.gov/Archives/example",
        summary="Tender offer",
        cik="0000000001",
        accession_number="0001",
    )
    decision = {
        "detected_form_type": "SC TO-T",
        "detected_signal": "Form type: SC TO-T",
        "detection_confidence": "HIGH",
        "situation_type": "merger_arbitrage",
        "subtype": "acquisition_tender_offer",
        "selected_playbook": "merger_arbitrage.md",
        "playbook_status": "evaluator_ready",
    }

    evidence = _build_minimal_evidence(filing, decision)

    assert evidence[WORKSPACE_KEY]["template_key"] == "merger_arbitrage_acquisition_tender"
    assert evidence[WORKSPACE_KEY]["requires_course_review"] is True


def _situation(*, status="detected", source="sec_edgar", detected_only=True, with_workspace=False) -> SpecialSituation:
    evaluation = {
        "source": source,
        "detected_only": detected_only,
        "sec_detection": {
            "detected_form_type": "SC TO-I",
            "situation_type": "tender_offer",
            "subtype": "self_tender",
        },
    }
    if with_workspace:
        evaluation[WORKSPACE_KEY] = {"template_key": "existing"}
    return SpecialSituation(
        situation_type="tender_offer",
        company_name="Issuer Corp",
        ticker="ISS",
        filing_type="SC TO-I",
        filing_url="https://www.sec.gov/Archives/example",
        status=status,
        evaluation=evaluation,
    )


class FakeScalars:
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items


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
async def test_backfill_dry_run_does_not_write():
    item = _situation()
    db = FakeDb([item])

    summary = await attach_methodology_workspace_backfill(db)

    assert summary["dry_run"] is True
    assert summary["matched_count"] == 1
    assert summary["updated_count"] == 0
    assert WORKSPACE_KEY not in item.evaluation
    assert db.flush_count == 0


@pytest.mark.asyncio
async def test_backfill_apply_writes_only_matched_records():
    matched = _situation()
    watchlist = _situation(status="watchlist")
    manual = _situation(source="manual")
    existing = _situation(with_workspace=True)
    db = FakeDb([matched, watchlist, manual, existing])

    summary = await attach_methodology_workspace_backfill(db, apply=True)

    assert summary["matched_count"] == 1
    assert summary["updated_count"] == 1
    assert matched.evaluation[WORKSPACE_KEY]["template_key"] == "tender_offer_self_tender"
    assert WORKSPACE_KEY not in watchlist.evaluation
    assert WORKSPACE_KEY not in manual.evaluation
    assert existing.evaluation[WORKSPACE_KEY]["template_key"] == "existing"
    assert db.flush_count == 1


def test_attach_helper_leaves_unknown_templates_unchanged():
    evidence = {
        "source": "sec_edgar",
        "detected_only": True,
        "sec_detection": {
            "detected_form_type": "10-Q",
            "situation_type": "unknown",
            "subtype": None,
        },
    }

    assert attach_methodology_workspace_to_evidence(evidence) == evidence
