"""
Observability layer tests.
All DB-touching tests use a mock AsyncSession so no live DB is required.
Pure async helpers use pytest-anyio (anyio plugin, available via anyio>=4.0).
TestClient-based endpoint tests are sync (TestClient handles ASGI synchronously).
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.services.observability.run_logger import (
    estimate_daily_ai_spend_usd,
    estimate_cost,
    estimate_tokens,
    start_run,
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
    execute_result = MagicMock()
    execute_result.scalars.return_value.first.return_value = None
    db.execute = AsyncMock(return_value=execute_result)
    return db


def _mock_db_empty():
    """Mock DB that returns empty results for all queries (no runs in DB)."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    execute_result = MagicMock()
    execute_result.all.return_value = []
    execute_result.scalars.return_value.all.return_value = []
    execute_result.scalars.return_value.first.return_value = None
    execute_result.scalar.return_value = 0
    execute_result.first.return_value = None
    db.execute = AsyncMock(return_value=execute_result)
    return db


# ── Test 1: agent_run record is created for scan ──────────────────────────────

@pytest.mark.anyio
async def test_agent_run_created_for_scan():
    db = _mock_db()
    await start_run(
        db,
        agent_name="investment_scanner",
        agent_type="fastapi",
        runtime="fastapi",
        trigger_source="api_call",
        task_name="scan_situations",
        input_summary="Scanning last 6h",
    )
    assert db.add.called
    added = db.add.call_args[0][0]
    assert isinstance(added, AgentRun)
    assert added.agent_name == "investment_scanner"
    assert added.status == "started"
    # id is set by SQLAlchemy at flush time; mock flush is a no-op so we don't assert it here


# ── Test 2: agent_run record is created for listing generation ────────────────

@pytest.mark.anyio
async def test_agent_run_created_for_listing():
    db = _mock_db()
    await start_run(
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

@pytest.mark.anyio
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
    assert added.estimated_cost is not None
    assert float(added.estimated_cost) > 0


@pytest.mark.anyio
async def test_daily_ai_spend_estimate_uses_logged_usage():
    db = _mock_db()
    result = MagicMock()
    result.scalar.return_value = 1.25
    db.execute = AsyncMock(return_value=result)

    spend = await estimate_daily_ai_spend_usd(db)

    assert spend == 1.25
    db.execute.assert_awaited_once()


# ── Test 4: failed run logs error_message ────────────────────────────────────

@pytest.mark.anyio
async def test_failed_run_logs_error():
    db = _mock_db()
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

def test_observability_summary_returns_costs():
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.db.database import get_db

    def mock_get_db():
        db = _mock_db_empty()
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

def test_claude_session_can_be_logged():
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.db.database import get_db

    def mock_get_db():
        db = _mock_db_empty()
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


# ── Mission Control & Agent Registry Tests ────────────────────────────────────

def test_agents_endpoint_returns_registered_agents_without_runs():
    """GET /agents must return all 16 registered agents even with no DB runs."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.db.database import get_db
    from backend.services.observability.agent_registry import REGISTRY

    def mock_get_db():
        yield _mock_db_empty()

    app.dependency_overrides[get_db] = mock_get_db
    try:
        client = TestClient(app)
        response = client.get("/api/observability/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == len(REGISTRY)
        returned_names = {a["agent_name"] for a in data["agents"]}
        assert returned_names == set(REGISTRY.keys())
        for agent in data["agents"]:
            assert agent["total_runs"] == 0
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_mission_control_returns_all_agents():
    """GET /mission-control must return all 16 registered agents."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.db.database import get_db
    from backend.services.observability.agent_registry import REGISTRY

    def mock_get_db():
        yield _mock_db_empty()

    app.dependency_overrides[get_db] = mock_get_db
    try:
        client = TestClient(app)
        response = client.get("/api/observability/mission-control")
        assert response.status_code == 200
        data = response.json()
        assert data["total_agents"] == len(REGISTRY)
        returned_names = {a["agent_name"] for a in data["agents"]}
        assert returned_names == set(REGISTRY.keys())
        assert "generated_at" in data
        assert "total_cost_usd" in data
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_mission_control_text_returns_plain_text():
    """GET /mission-control/text must return text/plain with agent names."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.db.database import get_db

    def mock_get_db():
        yield _mock_db_empty()

    app.dependency_overrides[get_db] = mock_get_db
    try:
        client = TestClient(app)
        response = client.get("/api/observability/mission-control/text")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        body = response.text
        assert "AGENT MISSION CONTROL" in body
        assert "marketplace_lister" in body
        assert "investment_scanner" in body
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_agent_detail_returns_instructions_and_recent_runs():
    """GET /agents/{agent_name} must return registry fields + recent_runs + stats."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.db.database import get_db

    def mock_get_db():
        yield _mock_db_empty()

    app.dependency_overrides[get_db] = mock_get_db
    try:
        client = TestClient(app)
        response = client.get("/api/observability/agents/marketplace_lister")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_name"] == "marketplace_lister"
        assert "instructions" in data
        assert "permissions" in data
        assert "human_approval_rules" in data
        assert "warnings" in data
        assert "recommended_next_action" in data
        assert "stats" in data
        assert "recent_runs" in data
        assert "recent_ai_usage" in data
        assert data["stats"]["total_runs"] == 0
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_agent_detail_text_returns_plain_text():
    """GET /agents/{agent_name}/text must return text/plain with key fields."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.db.database import get_db

    def mock_get_db():
        yield _mock_db_empty()

    app.dependency_overrides[get_db] = mock_get_db
    try:
        client = TestClient(app)
        response = client.get("/api/observability/agents/investment_scanner/text")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        body = response.text
        assert "investment_scanner" in body
        assert "INSTRUCTIONS" in body
        assert "PERMISSIONS" in body
        assert "STATS" in body
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_unknown_agent_returns_404():
    """GET /agents/{agent_name} must return 404 for unregistered agents."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.db.database import get_db

    def mock_get_db():
        yield _mock_db_empty()

    app.dependency_overrides[get_db] = mock_get_db
    try:
        client = TestClient(app)
        response = client.get("/api/observability/agents/nonexistent_agent_xyz")
        assert response.status_code == 404
        assert "not registered" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_cron_upcoming_returns_next_3_days():
    """GET /cron/upcoming returns correct structure (no real cron files needed)."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/observability/cron/upcoming?days=3")
    assert response.status_code == 200
    data = response.json()
    assert data["window_days"] == 3
    assert data["timezone"] == "Europe/Zurich"
    assert "entries" in data
    assert "count" in data
    assert "window_start" in data
    assert "window_end" in data
    assert "sources_checked" in data
    assert isinstance(data["entries"], list)


def test_cron_upcoming_text_returns_plain_text():
    """GET /cron/upcoming/text returns text/plain with header."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/observability/cron/upcoming/text?days=3")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    assert "CRON SCHEDULE" in body
    assert "Europe/Zurich" in body


def test_cron_output_redacts_secrets():
    """redact_secrets() must remove tokens, passwords, and long hex strings."""
    from backend.services.observability.cron_reader import redact_secrets

    # Telegram bot token format
    cmd = "python bot.py --token=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"
    result = redact_secrets(cmd)
    assert "1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ" not in result
    assert "[REDACTED]" in result

    # --password= flag
    cmd2 = "pg_dump --password=mysecretpassword mydb"
    result2 = redact_secrets(cmd2)
    assert "mysecretpassword" not in result2
    assert "[REDACTED]" in result2

    # Long hex API key (40+ chars)
    cmd3 = "curl -H 'X-Key: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2' https://api.example.com"
    result3 = redact_secrets(cmd3)
    assert "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2" not in result3
    assert "[REDACTED]" in result3

    # Safe strings must pass through unchanged
    cmd4 = "curl http://localhost:8000/api/health/ping"
    result4 = redact_secrets(cmd4)
    assert result4 == cmd4


def test_agent_card_includes_last_run_when_available():
    """GET /agents must show last_run timestamp when agent has runs in DB."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.db.database import get_db

    last_run_ts = datetime(2026, 4, 28, 10, 0, 0, tzinfo=timezone.utc)

    def mock_get_db():
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        counts_result = MagicMock()
        counts_result.all.return_value = [
            ("marketplace_lister", "completed", 4),
            ("marketplace_lister", "failed", 1),
        ]
        last_run_result = MagicMock()
        last_run_result.all.return_value = [
            ("marketplace_lister", last_run_ts),
        ]
        db.execute = AsyncMock(side_effect=[counts_result, last_run_result])
        yield db

    app.dependency_overrides[get_db] = mock_get_db
    try:
        client = TestClient(app)
        response = client.get("/api/observability/agents")
        assert response.status_code == 200
        data = response.json()
        lister = next(a for a in data["agents"] if a["agent_name"] == "marketplace_lister")
        assert lister["total_runs"] == 5
        assert lister["failed_runs"] == 1
        assert lister["last_run"] is not None
        assert "2026-04-28" in lister["last_run"]
    finally:
        app.dependency_overrides.pop(get_db, None)
