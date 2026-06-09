from types import SimpleNamespace
import uuid

import pytest

from backend.api.investment import router as investment_router
from backend.models.investment import DetectionRun
from backend.services.investment import scan_orchestrator
from backend.services.investment.scan_orchestrator import run_special_situation_scan


class FakeDb:
    def __init__(self):
        self.added = []
        self.commits = 0
        self.rollbacks = 0
        self.flushes = 0

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        self.flushes += 1
        for item in self.added:
            if isinstance(item, DetectionRun) and item.id is None:
                item.id = uuid.uuid4()

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


@pytest.mark.asyncio
async def test_orchestrator_records_scheduled_success_with_results(monkeypatch):
    db = FakeDb()

    async def fake_detection(_db, **kwargs):
        assert kwargs["trigger_type"] == "scheduled"
        assert kwargs["dry_run"] is False
        return {
            "started_at": "2026-06-09T08:00:00+00:00",
            "completed_at": "2026-06-09T08:00:03+00:00",
            "filings_fetched": 2,
            "raw_hits": 2,
            "classified_filings": 1,
            "unclassified_filings": 1,
            "duplicates_skipped": 1,
            "special_situations_created": 1,
            "created_situations": [{"id": "s1"}],
            "errors": [],
            "per_form_summary": {"SC TO-T": {"raw": 2, "created": 1}},
        }

    monkeypatch.setattr(scan_orchestrator, "run_sec_edgar_detection", fake_detection)
    monkeypatch.setattr(scan_orchestrator, "get_settings", lambda: SimpleNamespace(sec_user_agent="SwissEdge test"))

    summary = await run_special_situation_scan(db, trigger_type="scheduled", dry_run=False)

    run = next(item for item in db.added if isinstance(item, DetectionRun))
    assert summary["status"] == "success_with_results"
    assert summary["trigger_type"] == "scheduled"
    assert summary["new_special_situations_created"] == 1
    assert run.status == "success_with_results"
    assert run.special_situations_created == 1
    assert run.summary_json["guardrails"]["no_research_case_creation"] is True


@pytest.mark.asyncio
async def test_orchestrator_records_missing_sec_user_agent_without_calling_source(monkeypatch):
    db = FakeDb()

    async def fail_detection(*args, **kwargs):
        raise AssertionError("source should not be called when SEC_USER_AGENT is missing")

    monkeypatch.setattr(scan_orchestrator, "run_sec_edgar_detection", fail_detection)
    monkeypatch.setattr(scan_orchestrator, "get_settings", lambda: SimpleNamespace(sec_user_agent=""))

    summary = await run_special_situation_scan(db, trigger_type="scheduled")

    run = next(item for item in db.added if isinstance(item, DetectionRun))
    assert summary["status"] == "failed_config_error"
    assert summary["errors"] == ["Missing SEC_USER_AGENT"]
    assert run.status == "failed_config_error"
    assert run.error_message == "Missing SEC_USER_AGENT"


@pytest.mark.asyncio
async def test_manual_scan_endpoint_delegates_to_orchestrator(monkeypatch):
    calls = []

    async def fake_orchestrator(db, **kwargs):
        calls.append(kwargs)
        return {
            "run_id": "run-1",
            "source": "sec_edgar",
            "trigger_type": "manual",
            "status": "success_empty",
            "parsed_filings": 0,
            "new_special_situations_created": 0,
            "duplicates_skipped": 0,
            "created_situations": [],
            "warnings": [],
            "errors": [],
        }

    monkeypatch.setattr(investment_router, "run_special_situation_scan", fake_orchestrator)

    response = await investment_router.scan_situations(hours_back=6, db=object())

    assert calls == [{
        "source": "sec_edgar",
        "trigger_type": "manual",
        "hours_back": 6,
        "dry_run": False,
    }]
    assert response["new_situations"] == 0
    assert response["detection_run"]["trigger_type"] == "manual"
