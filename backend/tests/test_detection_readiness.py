import uuid
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.investment import router as investment_router
from backend.db.database import get_db
from backend.models.investment import DetectionRun
from backend.services.investment.detection_readiness import build_detection_readiness


def _run(
    *,
    status: str = "success",
    dry_run: bool = True,
    raw_hits: int = 122,
    classified_filings: int = 1,
    errors_count: int = 0,
    special_situations_created: int = 0,
    summary_json: dict | None = None,
) -> DetectionRun:
    summary = summary_json or {
        "raw_hits": raw_hits,
        "classified_filings": classified_filings,
        "candidates_detected": classified_filings,
        "errors": ["detection failed"] if errors_count else [],
        "per_form_summary": {
            "SC TO-T": {"raw": raw_hits, "parsed": classified_filings, "classified": classified_filings},
        },
    }
    return DetectionRun(
        id=uuid.uuid4(),
        source="sec_edgar",
        started_at=datetime.now(timezone.utc),
        status=status,
        dry_run=dry_run,
        raw_hits=raw_hits,
        parsed_filings=classified_filings,
        classified_filings=classified_filings,
        unclassified_filings=max(raw_hits - classified_filings, 0),
        duplicates_skipped=0,
        special_situations_created=special_situations_created,
        errors_count=errors_count,
        summary_json=summary,
        created_at=datetime.now(timezone.utc),
    )


def test_detection_readiness_no_runs_is_not_ready():
    package = build_detection_readiness([])

    assert package.readiness_level == "not_ready"
    assert package.latest_run is None
    assert package.blockers == ["No DetectionRun records exist yet."]


def test_detection_readiness_failed_latest_run_is_not_ready():
    package = build_detection_readiness([_run(status="failed", errors_count=1)])

    assert package.readiness_level == "not_ready"
    assert "Latest DetectionRun failed." in package.blockers


def test_detection_readiness_single_healthy_dry_run_observes_more():
    package = build_detection_readiness([_run()])

    assert package.readiness_level == "observe_more"
    assert "Latest DetectionRun completed successfully with zero errors." in package.reasons
    assert package.latest_run["dry_run"] is True


def test_detection_readiness_multiple_healthy_dry_runs_ready_for_limited_live_create():
    package = build_detection_readiness([_run(), _run(raw_hits=5, classified_filings=1)])

    assert package.readiness_level == "ready_for_limited_live_create"
    assert "Multiple recent dry-runs are healthy." in package.reasons


def test_detection_readiness_raw_hits_without_classified_candidates_warns_only():
    package = build_detection_readiness([_run(raw_hits=122, classified_filings=0)])

    assert package.readiness_level == "observe_more"
    assert package.blockers == []
    assert any("raw SEC hits" in warning for warning in package.warnings)


def test_detection_readiness_backoff_events_observe_more():
    package = build_detection_readiness([
        _run(
            raw_hits=0,
            classified_filings=0,
            summary_json={
                "raw_hits": 0,
                "parsed_filings": 0,
                "classified_filings": 0,
                "rate_limit_backoff_events": [
                    {"filing_type": "SC TO-T", "status_code": 500, "backoff_seconds": 60},
                ],
            },
        ),
        _run(raw_hits=5, classified_filings=1),
    ])

    assert package.readiness_level == "observe_more"
    assert package.blockers == []
    assert package.recommended_next_step == "Keep dry-run enabled and observe the next scheduled run."


def test_detection_readiness_backoff_warning_includes_sec_details():
    package = build_detection_readiness([
        _run(
            summary_json={
                "rate_limit_backoff_events": [
                    {"filing_type": "SC TO-T", "status_code": 500, "backoff_seconds": 60},
                ],
            },
        )
    ])

    warning_text = " ".join(package.warnings)
    assert "SEC backoff events occurred during the latest run." in warning_text
    assert "SC TO-T" in warning_text
    assert "500" in warning_text
    assert "60" in warning_text


def test_detection_readiness_backoff_with_null_filing_dates_does_not_crash():
    package = build_detection_readiness([
        _run(
            summary_json={
                "newest_filing_date": None,
                "oldest_filing_date": None,
                "rate_limit_backoff_events": [
                    {"filing_type": "SC TO-T", "status_code": 500, "backoff_seconds": 60},
                ],
            },
        )
    ])

    assert package.readiness_level == "observe_more"
    assert package.blockers == []


def test_detection_readiness_suggested_scope_is_conservative():
    package = build_detection_readiness([_run(), _run()])
    scope = package.suggested_live_create_scope

    assert {"SC TO-T", "SC TO-I", "Form 10"}.issubset(set(scope.allowed_forms))
    assert "8-K" in scope.conservative_forms
    assert any("8-K should remain conservative" in note for note in scope.notes)


def test_detection_readiness_route_hits_static_endpoint(monkeypatch):
    async def fake_latest_runs(db, limit=10):
        return []

    async def override_get_db():
        yield object()

    app = FastAPI()
    app.include_router(investment_router.router, prefix="/api/investment")
    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(investment_router, "get_latest_runs", fake_latest_runs)

    response = TestClient(app).get("/api/investment/detection-runs/readiness")

    assert response.status_code == 200
    assert response.json()["readiness_level"] == "not_ready"
    assert response.json()["guardrails"]["no_scan_trigger"] is True


@pytest.mark.asyncio
async def test_detection_readiness_endpoint_is_read_only(monkeypatch):
    async def fake_latest_runs(db, limit=10):
        return [_run(), _run(raw_hits=3, classified_filings=1)]

    class FakeDb:
        def __init__(self):
            self.added = []
            self.commits = 0

        def add(self, item):
            self.added.append(item)

        async def commit(self):
            self.commits += 1

    db = FakeDb()
    monkeypatch.setattr(investment_router, "get_latest_runs", fake_latest_runs)

    package = await investment_router.get_detection_runs_readiness(db=db)

    assert package.readiness_level == "ready_for_limited_live_create"
    assert db.added == []
    assert db.commits == 0
    assert package.guardrails["no_scan_trigger"] is True
