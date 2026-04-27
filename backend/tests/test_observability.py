"""
Observability layer tests.
All DB-touching tests use a mock AsyncSession so no live DB is required.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.observability.run_logger import (
    estimate_cost,
    estimate_tokens,
    start_run,
    finish_run,
    fail_run,
    log_ai_usage,
)
from backend.models.observability import AgentRun, AiUsage


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_db():
    """Return a minimal mock AsyncSession that records db.add() calls."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    # Simulate execute().scalars().first() returning None by default
    execute_result = MagicMock()
    execute_result.scalars.return_value.first.return_value = None
    db.execute = AsyncMock(return_value=execute_result)
    return db


# ── Test 1: agent_run record is created for scan ──────────────────────────────

@pytest.mark.asyncio
async def test_agent_run_created_for_scan():
    db = _mock_db()
    run_id = await start_run(
        db,
        agent_name="investment_scanner",
        agent_type="fastapi",
        runtime="fastapi",
        trigger_source="api_call",
        task_name="scan_situations",
        input_summary="Scanning last 6h",
    )
    # db.add should have been called with an AgentRun
    assert db.add.called
    added = db.add.call_args[0][0]
    assert isinstance(added, AgentRun)
    assert added.agent_name == "investment_scanner"
    assert added.status == "started"
    # run_id is the .id of the added object (set by default= uuid.uuid4)
    assert added.id is not None


# ── Test 2: agent_run record is created for listing generation ────────────────

@pytest.mark.asyncio
async def test_agent_run_created_for_listing():
    db = _mock_db()
    run_id = await start_run(
        db,
        agent_name="marketplace_lister",
        agent_type="fastapi",
        runtime="fastapi",
        task_name="generate_listing",
        input_summary="iPhone 14 Pro Gut",
        human_approval_required=True,
    )
    added = db.add.call_args[0][0]
    assert isinstance(added, AgentRun)
    assert added.agent_name == "marketplace_lister"
    assert added.human_approval_required is True


# ── Test 3: ai_usage is logged when AI client is called ──────────────────────

@pytest.mark.asyncio
async def test_ai_usage_logged_when_ai_client_called():
    db = _mock_db()
    run_id = uuid.uuid4()
    await log_ai_usage(
        db,
        run_id=run_id,
        agent_name="investment_evaluator",
        provider="openai",
        model="gpt-4o-mini",
        prompt_name="situation_evaluator",
        input_tokens=1200,
        output_tokens=400,
    )
    assert db.add.called
    added = db.add.call_args[0][0]
    assert isinstance(added, AiUsage)
    assert added.model == "gpt-4o-mini"
    assert added.input_tokens == 1200
    assert added.output_tokens == 400
    assert added.total_tokens == 1600
    # Cost should be non-zero for gpt-4o-mini
    assert added.estimated_cost is not None
    assert float(added.estimated_cost) > 0


# ── Test 4: failed run logs error_message ────────────────────────────────────

@pytest.mark.asyncio
async def test_failed_run_logs_error():
    db = _mock_db()
    # Simulate an existing AgentRun returned from DB
    mock_run = AgentRun(
        id=uuid.uuid4(),
        agent_name="investment_scanner",
        agent_type="fastapi",
        runtime="fastapi",
        trigger_source="api_call",
        status="started",
        started_at=datetime.now(timezone.utc),
    )
    db.execute.return_value.scalars.return_value.first.return_value = mock_run

    await fail_run(db, mock_run.id, "SEC EDGAR returned 429 Too Many Requests")

    assert mock_run.status == "failed"
    assert "429" in mock_run.error_message
    assert mock_run.outcome_score == 0
    assert mock_run.finished_at is not None


# ── Test 5: observability summary returns cost data ──────────────────────────

@pytest.mark.asyncio
async def test_observability_summary_returns_costs():
    """
    Calls GET /api/observability/summary via FastAPI test client.
    Uses a mocked DB session so no live PostgreSQL is needed.
    """
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.db.database import get_db

    async def mock_get_db():
        db = _mock_db()
        # summary endpoint executes several scalar queries; return 0 for all
        db.execute.return_value.scalar.return_value = 0
        db.execute.return_value.scalars.return_value.all.return_value = []
        db.execute.return_value.all.return_value = []
        yield db

    app.dependency_overrides[get_db] = mock_get_db
    try:
        client = TestClient(app)
        response = client.get("/api/observability/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_runs" in data
        assert "total_ai_cost_usd" in data
        assert "generated_at" in data
    finally:
        app.dependency_overrides.pop(get_db, None)


# ── Test 6: claude-session endpoint can be logged ────────────────────────────

@pytest.mark.asyncio
async def test_claude_session_can_be_logged():
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.db.database import get_db

    async def mock_get_db():
        db = _mock_db()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        yield db

    app.dependency_overrides[get_db] = mock_get_db
    try:
        client = TestClient(app)
        response = client.post(
            "/api/observability/claude-session",
            json={
                "task_name": "test_session",
                "input_summary": "Testing claude session logging",
                "output_summary": "Session logged successfully",
                "input_tokens": 5000,
                "output_tokens": 1500,
                "outcome": "Test passed",
                "outcome_score": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["status"] == "logged"
    finally:
        app.dependency_overrides.pop(get_db, None)


# ── Unit tests for helpers ────────────────────────────────────────────────────

def test_estimate_cost_gpt4o_mini():
    cost = estimate_cost("gpt-4o-mini", input_tokens=1_000_000, output_tokens=1_000_000)
    assert cost == pytest.approx(0.75, rel=0.01)


def test_estimate_tokens():
    text = "a" * 400
    assert estimate_tokens(text) == 100
