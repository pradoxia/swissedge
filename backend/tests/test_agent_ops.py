import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.db.database import get_db
from backend.main import app
from backend.models.agent_ops import (
    AgentActivity,
    AgentDiagnosticEvent,
    AgentLearningProposal,
    AgentProfile,
    AgentRoom,
)
from backend.services.agent_ops import activity_logger
from backend.services.agent_ops.service import (
    DEFAULT_AGENTS,
    DEFAULT_ROOMS,
    ensure_default_rooms_and_agents,
    update_proposal_status,
)


def _now():
    return datetime.now(timezone.utc)


def _result_scalars(items, first=None):
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    result.scalars.return_value.first.return_value = first if first is not None else (items[0] if items else None)
    return result


def _mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _override_db(db_mock):
    async def _fake():
        yield db_mock
    app.dependency_overrides[get_db] = _fake


def _clear_db_override():
    app.dependency_overrides.pop(get_db, None)


def test_agent_ops_models_import_and_tables():
    assert AgentRoom.__tablename__ == "agent_rooms"
    assert AgentProfile.__tablename__ == "agent_profiles"
    assert AgentActivity.__tablename__ == "agent_activities"
    assert AgentDiagnosticEvent.__tablename__ == "agent_diagnostic_events"
    assert AgentLearningProposal.__tablename__ == "agent_learning_proposals"
    assert "metadata" in AgentActivity.__table__.c


@pytest.mark.anyio
async def test_default_rooms_seed_idempotently_when_missing():
    db = _mock_db()
    db.execute = AsyncMock(side_effect=[
        _result_scalars([]),
        _result_scalars([]),
    ])

    await ensure_default_rooms_and_agents(db)

    added = [call.args[0] for call in db.add.call_args_list]
    assert len([item for item in added if isinstance(item, AgentRoom)]) == len(DEFAULT_ROOMS)
    assert db.flush.await_count == 2


@pytest.mark.anyio
async def test_default_agents_seed_idempotently_when_existing():
    rooms = [
        AgentRoom(id=uuid.uuid4(), key=data["key"], name=data["name"], status="active", display_order=data["display_order"])
        for data in DEFAULT_ROOMS
    ]
    agents = [
        AgentProfile(
            id=uuid.uuid4(),
            key=data["key"],
            name=data["name"],
            room_id=rooms[0].id,
            status="planned",
            implementation_status="documented",
            autonomy_level="observer",
        )
        for data in DEFAULT_AGENTS
    ]
    db = _mock_db()
    db.execute = AsyncMock(side_effect=[
        _result_scalars(rooms),
        _result_scalars(agents),
    ])

    await ensure_default_rooms_and_agents(db)

    db.add.assert_not_called()


def test_get_rooms_returns_six_rooms(monkeypatch):
    rooms = [
        AgentRoom(id=uuid.uuid4(), key=data["key"], name=data["name"], status="active", display_order=data["display_order"])
        for data in DEFAULT_ROOMS
    ]
    monkeypatch.setattr("backend.api.agent_ops.router.ensure_default_rooms_and_agents", AsyncMock())
    monkeypatch.setattr("backend.api.agent_ops.router.list_rooms", AsyncMock(return_value=rooms))
    db = _mock_db()
    _override_db(db)
    try:
        response = TestClient(app).get("/api/agent-ops/rooms")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 6
        assert {room["key"] for room in data["rooms"]} == {room["key"] for room in DEFAULT_ROOMS}
    finally:
        _clear_db_override()


def test_get_agents_returns_initial_agents(monkeypatch):
    room = AgentRoom(id=uuid.uuid4(), key="radar_room", name="Radar Room", status="active", display_order=10)
    agents = [
        AgentProfile(
            id=uuid.uuid4(),
            key=data["key"],
            name=data["name"],
            room_id=room.id,
            room=room,
            role=data["role"],
            status="planned",
            implementation_status="documented",
            autonomy_level="observer",
            guardrails=data["guardrails"],
        )
        for data in DEFAULT_AGENTS
    ]
    monkeypatch.setattr("backend.api.agent_ops.router.ensure_default_rooms_and_agents", AsyncMock())
    monkeypatch.setattr("backend.api.agent_ops.router.list_agents", AsyncMock(return_value=agents))
    db = _mock_db()
    _override_db(db)
    try:
        response = TestClient(app).get("/api/agent-ops/agents")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 6
        assert {agent["key"] for agent in data["agents"]} == {agent["key"] for agent in DEFAULT_AGENTS}
    finally:
        _clear_db_override()


def test_get_activity_empty(monkeypatch):
    monkeypatch.setattr("backend.api.agent_ops.router.list_activity", AsyncMock(return_value=[]))
    _override_db(_mock_db())
    try:
        response = TestClient(app).get("/api/agent-ops/activity")
        assert response.status_code == 200
        assert response.json() == {"count": 0, "items": []}
    finally:
        _clear_db_override()


def test_get_diagnostics_empty(monkeypatch):
    monkeypatch.setattr("backend.api.agent_ops.router.list_diagnostics", AsyncMock(return_value=[]))
    _override_db(_mock_db())
    try:
        response = TestClient(app).get("/api/agent-ops/diagnostics")
        assert response.status_code == 200
        assert response.json() == {"count": 0, "items": []}
    finally:
        _clear_db_override()


def test_get_proposals_empty(monkeypatch):
    monkeypatch.setattr("backend.api.agent_ops.router.list_proposals", AsyncMock(return_value=[]))
    _override_db(_mock_db())
    try:
        response = TestClient(app).get("/api/agent-ops/proposals")
        assert response.status_code == 200
        assert response.json() == {"count": 0, "items": []}
    finally:
        _clear_db_override()


@pytest.mark.anyio
async def test_patch_proposal_valid_transition_works():
    proposal = AgentLearningProposal(
        id=uuid.uuid4(),
        title="Improve diagnostic metric",
        problem_statement="Missing metric.",
        proposed_change="Add safe metric.",
        risk_level="low",
        status="proposed",
        created_at=_now(),
        updated_at=_now(),
    )
    db = _mock_db()
    db.execute = AsyncMock(return_value=_result_scalars([proposal], first=proposal))

    updated = await update_proposal_status(db, str(proposal.id), "accepted", "Approved.")

    assert updated.status == "accepted"
    assert updated.reviewer_note == "Approved."
    assert updated.reviewed_at is not None
    assert updated.proposed_change == "Add safe metric."


@pytest.mark.anyio
async def test_patch_proposal_invalid_transition_fails():
    proposal = AgentLearningProposal(
        id=uuid.uuid4(),
        title="Improve diagnostic metric",
        problem_statement="Missing metric.",
        proposed_change="Add safe metric.",
        status="implemented",
        created_at=_now(),
        updated_at=_now(),
    )
    db = _mock_db()
    db.execute = AsyncMock(return_value=_result_scalars([proposal], first=proposal))

    with pytest.raises(Exception) as exc:
        await update_proposal_status(db, str(proposal.id), "accepted")

    assert getattr(exc.value, "status_code", None) == 409


def test_patch_endpoint_does_not_auto_apply(monkeypatch):
    proposal = AgentLearningProposal(
        id=uuid.uuid4(),
        title="Improve routing",
        problem_statement="Weak route.",
        proposed_change="Change routing in a future Codex sprint.",
        status="accepted",
        reviewer_note="Approved.",
        reviewed_at=_now(),
        created_at=_now(),
        updated_at=_now(),
    )
    mock_update = AsyncMock(return_value=proposal)
    monkeypatch.setattr("backend.api.agent_ops.router.update_proposal_status", mock_update)
    db = _mock_db()
    _override_db(db)
    try:
        response = TestClient(app).patch(
            f"/api/agent-ops/proposals/{proposal.id}",
            json={"status": "accepted", "reviewer_note": "Approved."},
        )
        assert response.status_code == 200
        data = response.json()["proposal"]
        assert data["status"] == "accepted"
        assert data["proposed_change"] == "Change routing in a future Codex sprint."
        mock_update.assert_awaited_once()
    finally:
        _clear_db_override()


@pytest.mark.anyio
async def test_fail_safe_logger_catches_db_errors():
    db = _mock_db()
    db.add.side_effect = RuntimeError("db unavailable")

    result = await activity_logger.log_agent_activity(
        db,
        activity_type="test",
        title="Should not raise",
    )

    assert result is None
