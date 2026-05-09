import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.api.investment.research_cases import router
from backend.models.publishing import PublicArticleDraft
from backend.services.investment import research_cases as svc


class _ScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return self._rows


class _ExecuteResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _ScalarResult(self._rows)


class FakeSession:
    def __init__(self, research_case=None, drafts=None):
        self.research_case = research_case
        self.drafts = drafts or []
        self.added = []

    async def execute(self, _stmt):
        if self.research_case is not None:
            rc = self.research_case
            self.research_case = None
            return _ExecuteResult([rc])
        return _ExecuteResult(self.drafts)

    def add(self, obj):
        self.added.append(obj)
        if isinstance(obj, PublicArticleDraft):
            if obj.id is None:
                obj.id = uuid.uuid4()
            if obj.created_at is None:
                obj.created_at = datetime.now(timezone.utc)
            self.drafts.append(obj)

    async def flush(self):
        pass

    async def refresh(self, obj):
        if isinstance(obj, PublicArticleDraft):
            if obj.id is None:
                obj.id = uuid.uuid4()
            if obj.created_at is None:
                obj.created_at = datetime.now(timezone.utc)


def _research_case():
    return SimpleNamespace(
        id=uuid.uuid4(),
        situation_id=None,
        status="documented",
        investment_readiness="candidate",
        disclaimer=svc._DISCLAIMER,
        brief={
            "executive_summary": "Example public summary",
            "situation_type": "Spin-off",
            "why_interesting": "The case has structural complexity and requires further research.",
            "risk_analysis": "Execution risk remains.",
            "missing_information": "Confirm distribution timing.",
            "public_summary_draft": "A concise educational note for public review.",
        },
        tasks=[
            SimpleNamespace(description="Confirm board approval timing", status="open"),
            SimpleNamespace(description="Private note should not use task notes", status="done"),
        ],
        documents=[
            SimpleNamespace(title="Public filing", doc_type="sec_filing", url="https://example.com/filing"),
        ],
        sources=[
            SimpleNamespace(source_name="Company investor relations", source_url="https://example.com/ir"),
        ],
    )


def _draft(**overrides):
    data = {
        "id": uuid.uuid4(),
        "research_case_id": uuid.uuid4(),
        "status": "draft",
        "title": "Public research note",
        "content": f"Educational body.\n\n{svc._DISCLAIMER}",
        "readiness_label": "candidate",
        "disclaimer": svc._DISCLAIMER,
        "disclaimer_present": True,
        "buy_sell_language_check": True,
        "tags": {"values": []},
        "created_at": datetime.now(timezone.utc),
        "approved_at": None,
        "published_at": None,
    }
    data.update(overrides)
    return PublicArticleDraft(**data)


@pytest.mark.asyncio
async def test_create_public_draft_from_research_case():
    db = FakeSession(research_case=_research_case())
    draft = await svc.create_public_article_draft(db, uuid.uuid4())

    assert draft.status == "draft"
    assert draft.readiness_label == "candidate"
    assert svc._DISCLAIMER in draft.content
    assert "Private note" not in draft.content
    assert "research_case_id" not in draft.content


@pytest.mark.asyncio
async def test_list_get_update_public_draft():
    draft = _draft()
    db = FakeSession(drafts=[draft])

    rows = await svc.list_public_article_drafts(db)
    assert rows == [draft]

    fetched = await svc.get_public_article_draft(db, draft.id)
    assert fetched.id == draft.id

    updated = await svc.update_public_article_draft(
        db,
        draft.id,
        svc.PublicArticleDraftUpdate(title="Edited title", status="in_review"),
    )
    assert updated.title == "Edited title"
    assert updated.status == "in_review"


@pytest.mark.asyncio
async def test_validation_blocks_approval_when_disclaimer_missing():
    draft = _draft(status="in_review", content="Educational body without disclaimer", disclaimer_present=False)
    db = FakeSession(drafts=[draft])

    with pytest.raises(HTTPException) as exc:
        await svc.update_public_article_draft(
            db,
            draft.id,
            svc.PublicArticleDraftUpdate(status="approved"),
        )

    assert exc.value.status_code == 422
    assert "validation_warnings" in exc.value.detail


@pytest.mark.asyncio
async def test_validation_blocks_approval_when_buy_sell_language_appears():
    draft = _draft(status="in_review", content=f"This says buy now.\n\n{svc._DISCLAIMER}", buy_sell_language_check=False)
    db = FakeSession(drafts=[draft])

    with pytest.raises(HTTPException) as exc:
        await svc.update_public_article_draft(
            db,
            draft.id,
            svc.PublicArticleDraftUpdate(status="approved"),
        )

    assert exc.value.status_code == 422
    assert "Buy/sell recommendation language detected." in exc.value.detail["validation_warnings"]


@pytest.mark.asyncio
async def test_draft_cannot_be_approved_directly():
    draft = _draft(status="draft")
    db = FakeSession(drafts=[draft])

    with pytest.raises(HTTPException) as exc:
        await svc.update_public_article_draft(
            db,
            draft.id,
            svc.PublicArticleDraftUpdate(status="approved"),
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == "Draft must be moved to in_review before approval."


@pytest.mark.asyncio
async def test_draft_can_move_to_in_review():
    draft = _draft(status="draft")
    db = FakeSession(drafts=[draft])

    updated = await svc.update_public_article_draft(
        db,
        draft.id,
        svc.PublicArticleDraftUpdate(status="in_review"),
    )

    assert updated.status == "in_review"


@pytest.mark.asyncio
async def test_in_review_can_be_approved():
    draft = _draft(status="in_review")
    db = FakeSession(drafts=[draft])

    updated = await svc.update_public_article_draft(
        db,
        draft.id,
        svc.PublicArticleDraftUpdate(status="approved"),
    )

    assert updated.status == "approved"
    assert updated.approved_at is not None


@pytest.mark.asyncio
async def test_supported_statuses_can_archive_but_archived_cannot_reopen():
    for current_status in ("draft", "in_review", "approved"):
        draft = _draft(status=current_status)
        db = FakeSession(drafts=[draft])

        updated = await svc.update_public_article_draft(
            db,
            draft.id,
            svc.PublicArticleDraftUpdate(status="archived"),
        )

        assert updated.status == "archived"

    archived = _draft(status="archived")
    db = FakeSession(drafts=[archived])

    with pytest.raises(HTTPException) as exc:
        await svc.update_public_article_draft(
            db,
            archived.id,
            svc.PublicArticleDraftUpdate(status="in_review"),
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == "Archived drafts cannot transition back to another status."


def test_buy_sell_patterns_defined_before_phase5_helper_use():
    assert isinstance(svc._BUY_SELL_PATTERNS, list)
    assert svc._contains_buy_sell_language("buy now")


def test_markdown_export_excludes_private_internal_fields():
    draft = _draft(title="Clean title", content=f"Clean public body.\n\n{svc._DISCLAIMER}")
    markdown = svc.render_public_article_markdown(draft)

    assert markdown.startswith("# Clean title")
    assert svc._DISCLAIMER in markdown
    assert "research_case_id" not in markdown
    assert "run_id" not in markdown
    assert "/api/" not in markdown


def test_no_publish_endpoint_exists():
    paths = {route.path for route in router.routes}
    assert "/public-drafts/{draft_id}/publish" not in paths
    assert all("substack" not in path.lower() for path in paths)


def test_no_scanner_cron_or_v2_phase5_endpoint_exists():
    paths = {route.path for route in router.routes}
    assert all("/scan" not in path for path in paths)
    assert all("cron" not in path.lower() for path in paths)
    assert all("evaluate-v2" not in path for path in paths)


@pytest.mark.asyncio
async def test_get_public_draft_404():
    db = FakeSession(drafts=[])

    with pytest.raises(HTTPException) as exc:
        await svc.get_public_article_draft(db, uuid.uuid4())

    assert exc.value.status_code == 404
