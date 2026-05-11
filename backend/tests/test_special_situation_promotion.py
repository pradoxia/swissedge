import inspect
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from backend.models.investment import SpecialSituation
from backend.models.investment_research import ResearchCase, ResearchSource, ResearchTask
from backend.services.investment.methodology_workspace import WORKSPACE_KEY, attach_methodology_workspace_to_evidence
from backend.services.investment.research_cases import (
    PromoteSpecialSituationPayload,
    promote_special_situation_to_research_case,
)


def _evaluation():
    evidence = {
        "source": "sec_edgar",
        "detected_only": True,
        "sec_detection": {
            "accession_number": "0001140361-26-019536",
            "cik": "0001829280",
            "filing_url": "https://www.sec.gov/Archives/edgar/data/1829280/000114036126019536/filing.htm",
            "filing_date": "2026-05-08",
            "detected_form_type": "SC TO-T",
            "situation_type": "merger_arbitrage",
            "subtype": "acquisition_tender_offer",
            "selected_playbook": "merger_arbitrage.md",
            "playbook_status": "evaluator_ready",
            "detection_confidence": "HIGH",
        },
    }
    updated = attach_methodology_workspace_to_evidence(evidence)
    workspace = updated[WORKSPACE_KEY]
    workspace["workflow_status"] = "ready_for_research_case"
    workspace["resource_candidates"] = [{
        "resource_candidate_id": "candidate-1",
        "title": "Offer document",
        "url": "https://example.com/offer",
        "source_type": "offer_document",
        "status": "evidence_found",
        "related_resource_ids": ["ma_offer_purchase"],
        "related_check_ids": ["ma_offer_terms"],
    }]
    workspace["search_suggestions"] = [{
        "suggestion_id": "suggestion-1",
        "query": "\"Forian Inc.\" offer to purchase",
        "suggestion_type": "offer_document",
    }]
    return updated


def _situation(evaluation=None):
    return SpecialSituation(
        id=uuid.uuid4(),
        situation_type="merger_arbitrage",
        company_name="Forian Inc.",
        ticker="FORA",
        filing_type="SC TO-T",
        filing_url="https://www.sec.gov/Archives/edgar/data/1829280/000114036126019536/filing.htm",
        detected_at=datetime(2026, 5, 8, tzinfo=timezone.utc),
        status="detected",
        evaluation=evaluation if evaluation is not None else _evaluation(),
        source_urls=["https://www.sec.gov/Archives/edgar/data/1829280/000114036126019536/filing.htm"],
    )


def _result_first(item):
    result = MagicMock()
    result.scalars.return_value.first.return_value = item
    return result


class PromotionDb:
    def __init__(self, situation, existing=None):
        self.situation = situation
        self.existing = existing
        self.calls = 0
        self.added = []
        self.flush_count = 0
        self.add = MagicMock(side_effect=self.added.append)
        self.refresh = AsyncMock()

    async def execute(self, _query):
        self.calls += 1
        if self.calls == 1:
            return _result_first(self.situation)
        if self.calls == 2:
            return _result_first(self.existing)
        research_cases = [item for item in self.added if isinstance(item, ResearchCase)]
        return _result_first(self.existing or (research_cases[0] if research_cases else None))

    async def flush(self):
        self.flush_count += 1
        for item in self.added:
            if getattr(item, "id", None) is None:
                item.id = uuid.uuid4()
            if isinstance(item, ResearchCase):
                item.tasks = [task for task in self.added if isinstance(task, ResearchTask)]
                item.sources = [source for source in self.added if isinstance(source, ResearchSource)]
                item.documents = []


@pytest.mark.asyncio
async def test_promote_creates_research_case_from_special_situation():
    sit = _situation()
    db = PromotionDb(sit)

    rc, created = await promote_special_situation_to_research_case(
        db,
        sit.id,
        PromoteSpecialSituationPayload(notes="Manual promotion"),
    )

    assert created is True
    assert isinstance(rc, ResearchCase)
    assert rc.status == "under_investigation"
    assert rc.investment_readiness == "needs_more_work"
    assert rc.intake_method == "special_situation_promotion"
    assert rc.brief["detected_not_evaluated"] is True
    assert rc.brief["detection_summary"]["accession_number"] == "0001140361-26-019536"
    assert rc.brief["methodology_workspace_snapshot"]["resource_candidates"]
    assert sit.evaluation[WORKSPACE_KEY]["research_case_id"] == str(rc.id)
    assert sit.evaluation[WORKSPACE_KEY]["workflow_status"] == "promoted_to_research_case"
    assert len([item for item in db.added if isinstance(item, ResearchTask)]) == 7
    assert any(isinstance(item, ResearchSource) for item in db.added)


@pytest.mark.asyncio
async def test_second_promote_returns_existing_without_duplicate():
    sit = _situation()
    existing = ResearchCase(id=uuid.uuid4(), situation_id=sit.id, status="under_investigation", disclaimer="Este análisis es educativo. No es asesoramiento financiero.")
    existing.tasks = []
    existing.sources = []
    existing.documents = []
    db = PromotionDb(sit, existing=existing)

    rc, created = await promote_special_situation_to_research_case(db, sit.id)

    assert created is False
    assert rc is existing
    assert sit.evaluation[WORKSPACE_KEY]["research_case_id"] == str(existing.id)
    assert not any(isinstance(item, ResearchCase) for item in db.added)


@pytest.mark.asyncio
async def test_promote_uses_existing_workspace_link():
    linked_id = uuid.uuid4()
    evaluation = _evaluation()
    evaluation[WORKSPACE_KEY]["research_case_id"] = str(linked_id)
    sit = _situation(evaluation=evaluation)
    existing = ResearchCase(id=linked_id, situation_id=sit.id, status="under_investigation", disclaimer="Este análisis es educativo. No es asesoramiento financiero.")
    existing.tasks = []
    existing.sources = []
    existing.documents = []
    db = PromotionDb(sit, existing=existing)

    rc, created = await promote_special_situation_to_research_case(db, sit.id)

    assert created is False
    assert rc is existing
    assert not any(isinstance(item, ResearchCase) for item in db.added)


@pytest.mark.asyncio
async def test_promote_requires_methodology_workspace():
    sit = _situation(evaluation={"source": "sec_edgar", "detected_only": True})
    db = PromotionDb(sit)

    with pytest.raises(HTTPException) as exc_info:
        await promote_special_situation_to_research_case(db, sit.id)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_promote_rejects_invalid_status_and_missing_situation():
    sit = _situation()
    with pytest.raises(HTTPException) as exc_info:
        await promote_special_situation_to_research_case(
            PromotionDb(sit),
            sit.id,
            PromoteSpecialSituationPayload(initial_status="published_now"),
        )
    assert exc_info.value.status_code == 400

    missing = PromotionDb(None)
    with pytest.raises(HTTPException) as missing_exc:
        await promote_special_situation_to_research_case(missing, uuid.uuid4())
    assert missing_exc.value.status_code == 404


def test_promotion_does_not_call_ai_or_create_public_draft():
    import backend.services.investment.research_cases as svc

    src = inspect.getsource(svc.promote_special_situation_to_research_case)
    assert "complete_with_usage" not in src
    assert "PublicArticleDraft" not in src
    assert "create_public_article_draft" not in src


@pytest.mark.asyncio
async def test_promotion_values_fit_research_case_column_limits():
    sit = _situation()
    db = PromotionDb(sit)

    rc, created = await promote_special_situation_to_research_case(db, sit.id)

    assert created is True
    constrained_fields = [
        "status",
        "brief_version",
        "playbook_version",
        "model_used",
        "investment_readiness",
        "intake_method",
        "connector_key",
        "evidence_level",
        "official_source_status",
        "methodology_status",
        "playbook_used",
        "checklist_used",
        "duplicate_status",
    ]
    for field in constrained_fields:
        value = getattr(rc, field)
        column_type = ResearchCase.__table__.c[field].type
        length = getattr(column_type, "length", None)
        if value is not None and length is not None:
            assert len(value) <= length, f"{field}={value!r} exceeds VARCHAR({length})"
    assert rc.brief_version == "ss_promo_v1"
