import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.investment import router as investment_router
from backend.db.database import get_db
from backend.cli import sec_edgar_detect
from backend.models.investment import DetectionRun
from backend.services.investment.detection_run_service import (
    DetectionRunService,
    build_detection_run_status,
    counters_from_summary,
    serialize_detection_run,
)


def test_sec_edgar_cli_defaults_to_dry_run(monkeypatch):
    monkeypatch.setattr("sys.argv", ["sec_edgar_detect"])

    args = sec_edgar_detect._parse_args()

    assert args.dry_run is True


def test_sec_edgar_cli_live_create_requires_explicit_flag(monkeypatch):
    monkeypatch.setattr("sys.argv", ["sec_edgar_detect", "--live-create"])

    args = sec_edgar_detect._parse_args()

    assert args.dry_run is False


def test_sec_edgar_cli_rejects_conflicting_mode_flags(monkeypatch):
    monkeypatch.setattr("sys.argv", ["sec_edgar_detect", "--dry-run", "--live-create"])

    with pytest.raises(SystemExit):
        sec_edgar_detect._parse_args()


class FakeSession:
    def __init__(self):
        self.rows = {}
        self.added = []
        self.commits = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def add(self, item):
        self.added.append(item)
        self.rows[item.id] = item

    async def get(self, model, item_id):
        return self.rows.get(item_id)

    async def commit(self):
        self.commits += 1


class FakeSessionFactory:
    def __init__(self, session):
        self.session = session

    def __call__(self):
        return self.session


def test_detection_run_summary_counter_mapping():
    summary = {
        "started_at": "2026-05-16T10:00:00+00:00",
        "completed_at": "2026-05-16T10:00:03+00:00",
        "filings_fetched": 3,
        "raw_hits": 122,
        "candidates_detected": 2,
        "unsupported_forms_skipped": 1,
        "duplicates_skipped": 1,
        "special_situations_created": 1,
        "errors": ["one"],
        "form_counts": {"SC TO-T": 2, "8-K": 1},
    }

    counters = counters_from_summary(summary)

    assert counters["raw_hits"] == 122
    assert counters["parsed_filings"] == 3
    assert counters["classified_filings"] == 2
    assert counters["unclassified_filings"] == 1
    assert counters["duplicates_skipped"] == 1
    assert counters["special_situations_created"] == 1
    assert counters["errors_count"] == 1
    assert counters["runtime_seconds"] == 3
    assert counters["forms_checked_json"] == ["SC TO-T", "8-K"]


def test_detection_run_raw_hits_falls_back_to_per_form_raw_totals():
    summary = {
        "filings_fetched": 0,
        "per_form_summary": {
            "8-K": {"raw": 100, "parsed": 0, "classified": 0},
            "SC TO-I": {"raw": 21, "parsed": 0, "classified": 0},
            "SC TO-T": {"raw": 1, "parsed": 0, "classified": 0},
            "Form 10": {"raw": 0, "parsed": 0, "classified": 0},
        },
        "errors": [],
    }

    counters = counters_from_summary(summary)

    assert counters["raw_hits"] == 122
    assert counters["per_form_summary_json"]["8-K"]["raw"] == 100


@pytest.mark.asyncio
async def test_detection_run_service_start_and_mark_success():
    session = FakeSession()
    service = DetectionRunService(FakeSessionFactory(session))

    run_id = await service.start_run(hours_back=48, dry_run=True, forms_checked=["SC TO-T"])
    await service.mark_success(run_id, summary={"raw_hits": 122, "filings_fetched": 1, "candidates_detected": 1})

    run = session.rows[run_id]
    assert run.status == "success"
    assert run.hours_back == 48
    assert run.dry_run is True
    assert run.raw_hits == 122
    assert run.parsed_filings == 1
    assert run.classified_filings == 1
    assert run.finished_at is not None


@pytest.mark.asyncio
async def test_detection_run_service_fails_safe():
    class BrokenFactory:
        def __call__(self):
            raise RuntimeError("logging unavailable")

    service = DetectionRunService(BrokenFactory())

    assert await service.start_run(hours_back=48) is None
    await service.mark_failed(uuid.uuid4(), "boom")


@pytest.mark.asyncio
async def test_detection_run_read_api_serializes_run():
    run = DetectionRun(
        id=uuid.uuid4(),
        source="sec_edgar",
        started_at=datetime.now(timezone.utc),
        status="success",
        dry_run=True,
        hours_back=48,
        raw_hits=4,
        parsed_filings=3,
        classified_filings=2,
        unclassified_filings=1,
        duplicates_skipped=1,
        special_situations_created=1,
        errors_count=0,
        created_at=datetime.now(timezone.utc),
    )

    class FakeDb:
        async def get(self, model, item_id):
            return run if item_id == run.id else None

    data = await investment_router.get_detection_run(str(run.id), db=FakeDb())

    assert data["id"] == str(run.id)
    assert data["source"] == "sec_edgar"
    assert data["status"] == "success"
    assert data["dry_run"] is True
    assert data["unclassified_filings"] == 1


def _detection_runs_client(fake_db):
    app = FastAPI()
    app.include_router(investment_router.router, prefix="/api/investment")

    async def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.mark.asyncio
async def test_latest_detection_run_api_empty_state(monkeypatch):
    async def fake_latest_runs(db, limit=1):
        return []

    monkeypatch.setattr(investment_router, "get_latest_runs", fake_latest_runs)

    data = await investment_router.get_latest_detection_run(db=object())

    assert data == {"run": None}


def test_latest_detection_run_route_hits_static_endpoint(monkeypatch):
    async def fake_latest_runs(db, limit=1):
        return []

    monkeypatch.setattr(investment_router, "get_latest_runs", fake_latest_runs)

    response = _detection_runs_client(object()).get("/api/investment/detection-runs/latest")

    assert response.status_code == 200
    assert response.json() == {"run": None}


@pytest.mark.asyncio
async def test_detection_run_status_api_is_read_only(monkeypatch):
    run = DetectionRun(
        id=uuid.uuid4(),
        source="sec_edgar",
        started_at=datetime.now(timezone.utc),
        status="success",
        dry_run=True,
        hours_back=48,
        raw_hits=4,
        parsed_filings=3,
        classified_filings=2,
        unclassified_filings=1,
        errors_count=0,
        created_at=datetime.now(timezone.utc),
    )

    async def fake_latest_runs(db, limit=20):
        return [run]

    monkeypatch.setattr(investment_router, "get_latest_runs", fake_latest_runs)
    data = await investment_router.get_detection_runs_status(db=object())

    assert data["status"] == "healthy"
    assert data["latest_run"]["id"] == str(run.id)
    assert data["cron_safe_defaults"] == {
        "enabled_default": False,
        "dry_run_default": True,
        "hours_back_default": 48,
    }
    assert data["guardrails"]["no_scan_trigger"] is True


def test_detection_run_status_route_hits_static_endpoint(monkeypatch):
    async def fake_latest_runs(db, limit=20):
        return []

    monkeypatch.setattr(investment_router, "get_latest_runs", fake_latest_runs)

    response = _detection_runs_client(object()).get("/api/investment/detection-runs/status")

    assert response.status_code == 200
    assert response.json()["status"] == "no_runs"


def test_detection_run_invalid_uuid_returns_clean_404():
    class FakeDb:
        async def get(self, model, item_id):
            raise AssertionError("invalid UUID should not query the database")

    response = _detection_runs_client(FakeDb()).get("/api/investment/detection-runs/not-a-uuid")

    assert response.status_code == 404
    assert response.json()["detail"] == "Detection run not found"


@pytest.mark.asyncio
async def test_sec_edgar_cli_marks_detection_run_success(monkeypatch):
    logger = AsyncMock()
    logger.start_run.return_value = uuid.uuid4()
    monkeypatch.setattr(sec_edgar_detect, "_parse_args", lambda: type("Args", (), {"hours_back": 48, "dry_run": True})())
    monkeypatch.setattr(sec_edgar_detect, "DetectionRunService", lambda: logger)

    fake_db = AsyncMock()
    fake_context = AsyncMock()
    fake_context.__aenter__.return_value = fake_db
    fake_context.__aexit__.return_value = False

    with patch.object(sec_edgar_detect, "AsyncSessionLocal", return_value=fake_context):
        with patch.object(sec_edgar_detect, "run_sec_edgar_detection", new=AsyncMock(return_value={"errors": [], "filings_fetched": 1})):
            await sec_edgar_detect._main()

    logger.start_run.assert_awaited_once()
    logger.mark_success.assert_awaited_once()
    logger.mark_failed.assert_not_called()


def test_detection_run_serializer_shape():
    run = DetectionRun(
        id=uuid.uuid4(),
        source="sec_edgar",
        started_at=datetime.now(timezone.utc),
        status="running",
        dry_run=True,
        hours_back=48,
        created_at=datetime.now(timezone.utc),
    )

    data = serialize_detection_run(run)

    assert data["raw_hits"] == 0
    assert data["parsed_filings"] == 0
    assert data["unclassified_filings"] == 0
    assert data["forms_checked_json"] is None


def test_detection_run_serializer_falls_back_to_summary_raw_hits():
    run = DetectionRun(
        id=uuid.uuid4(),
        source="sec_edgar",
        started_at=datetime.now(timezone.utc),
        status="success",
        dry_run=True,
        raw_hits=0,
        parsed_filings=0,
        classified_filings=0,
        unclassified_filings=0,
        errors_count=0,
        summary_json={
            "raw_hits": 122,
            "parsed_filings": 3,
            "classified_filings": 1,
            "unclassified_filings": 2,
            "outside_lookback_skipped": 5,
            "missing_filing_date_skipped": 2,
            "unsupported_forms_skipped": 7,
            "candidates_detected": 1,
            "per_form_summary": {
                "8-K": {"raw": 100, "parsed": 0, "classified": 0},
            },
            "errors": [],
        },
        created_at=datetime.now(timezone.utc),
    )

    data = serialize_detection_run(run)

    assert data["raw_hits"] == 122
    assert data["parsed_filings"] == 3
    assert data["classified_filings"] == 1
    assert data["unclassified_filings"] == 2
    assert data["outside_lookback_skipped"] == 5
    assert data["missing_filing_date_skipped"] == 2
    assert data["unsupported_forms_skipped"] == 7
    assert data["candidates_detected"] == 1
    assert data["per_form_summary"]["8-K"]["raw"] == 100


def test_detection_run_status_latest_run_uses_summary_raw_hits_fallback():
    run = DetectionRun(
        id=uuid.uuid4(),
        source="sec_edgar",
        started_at=datetime.now(timezone.utc),
        status="success",
        dry_run=True,
        raw_hits=0,
        summary_json={
            "per_form_summary": {
                "8-K": {"raw": 100},
                "SC TO-I": {"raw": 21},
                "SC TO-T": {"raw": 1},
            },
            "errors": [],
        },
        errors_count=0,
        created_at=datetime.now(timezone.utc),
    )

    status = build_detection_run_status([run])

    assert status["status"] == "healthy"
    assert status["latest_run"]["raw_hits"] == 122


def test_detection_run_status_no_runs_and_failed_run():
    assert build_detection_run_status([])["status"] == "no_runs"

    failed = DetectionRun(
        id=uuid.uuid4(),
        source="sec_edgar",
        started_at=datetime.now(timezone.utc),
        status="failed",
        dry_run=True,
        errors_count=1,
        created_at=datetime.now(timezone.utc),
    )

    status = build_detection_run_status([failed])
    assert status["status"] == "warning"
    assert status["latest_failed_run"]["id"] == str(failed.id)
    assert status["recent_errors_count"] == 1


def test_detection_run_status_handles_running_dry_run_and_live_create():
    running = DetectionRun(
        id=uuid.uuid4(),
        source="sec_edgar",
        started_at=datetime.now(timezone.utc),
        status="running",
        dry_run=True,
        hours_back=48,
        created_at=datetime.now(timezone.utc),
    )
    live_success = DetectionRun(
        id=uuid.uuid4(),
        source="sec_edgar",
        started_at=datetime.now(timezone.utc),
        status="success",
        dry_run=False,
        hours_back=48,
        created_at=datetime.now(timezone.utc),
    )

    running_status = build_detection_run_status([running])
    live_status = build_detection_run_status([live_success])

    assert running_status["status"] == "warning"
    assert running_status["latest_run"]["dry_run"] is True
    assert running_status["latest_successful_run"] is None
    assert running_status["latest_failed_run"] is None
    assert live_status["status"] == "healthy"
    assert live_status["latest_run"]["dry_run"] is False


def test_sec_edgar_runner_keeps_safe_defaults_and_validation():
    script = Path("scripts/run_sec_edgar_detection.sh").read_text()

    assert 'SWISSEDGE_SEC_EDGAR_ENABLED:-false' in script
    assert 'SWISSEDGE_SEC_EDGAR_DRY_RUN:-true' in script
    assert 'SWISSEDGE_SEC_EDGAR_HOURS_BACK:-48' in script
    assert 'is_positive_integer "$HOURS_BACK"' in script
    assert 'is_bool "$DRY_RUN"' in script
    assert "crontab" not in script
    assert "systemctl" not in script
