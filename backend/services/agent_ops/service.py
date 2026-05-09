import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.agent_ops import (
    AgentActivity,
    AgentDiagnosticEvent,
    AgentLearningProposal,
    AgentProfile,
    AgentRoom,
)


ALLOWED_PROPOSAL_STATUSES = {
    "proposed",
    "accepted",
    "rejected",
    "deferred",
    "implemented",
    "archived",
}

ALLOWED_TRANSITIONS = {
    "proposed": {"accepted", "rejected", "deferred", "archived"},
    "accepted": {"implemented", "archived"},
    "rejected": {"archived"},
    "deferred": {"proposed", "rejected", "archived"},
    "implemented": {"archived"},
    "archived": set(),
}

DEFAULT_ROOMS = [
    {
        "key": "radar_room",
        "name": "Radar Room",
        "description": "Detection, scanner health, SEC EDGAR coverage, and source funnel diagnostics.",
        "status": "active",
        "display_order": 10,
    },
    {
        "key": "evidence_lab",
        "name": "Evidence Lab",
        "description": "Filing parsing, document metadata, source provenance, and evidence quality.",
        "status": "active",
        "display_order": 20,
    },
    {
        "key": "research_desk",
        "name": "Research Desk",
        "description": "ResearchCases, Research Inbox, tasks, briefs, enrichment, and readiness.",
        "status": "active",
        "display_order": 30,
    },
    {
        "key": "quality_court",
        "name": "Quality Court",
        "description": "False positives, missing methodology, official-source gaps, duplicates, and guardrails.",
        "status": "active",
        "display_order": 40,
    },
    {
        "key": "playbook_workshop",
        "name": "Playbook Workshop",
        "description": "Playbook gaps, routing improvements, methodology status, and checklist proposals.",
        "status": "active",
        "display_order": 50,
    },
    {
        "key": "agent_ops",
        "name": "Agent Ops",
        "description": "Rooms, agents, activity feed, diagnostics, learning proposals, and future reports.",
        "status": "active",
        "display_order": 60,
    },
]

DEFAULT_AGENTS = [
    {
        "key": "edgar_scout",
        "name": "Edgar Scout",
        "room_key": "radar_room",
        "role": "SEC EDGAR signal and scanner health observer.",
        "guardrails": ["no scan trigger", "no cron change", "no source registry wiring"],
    },
    {
        "key": "form_parser",
        "name": "Form Parser",
        "room_key": "evidence_lab",
        "role": "Filing metadata interpreter and evidence-status helper.",
        "guardrails": ["no URL fetching unless approved", "no raw filing storage"],
    },
    {
        "key": "router_analyst",
        "name": "Router Analyst",
        "room_key": "radar_room",
        "role": "Deterministic methodology routing observer.",
        "guardrails": ["no autonomous rule changes", "no evaluator v2 global changes"],
    },
    {
        "key": "case_builder",
        "name": "Case Builder",
        "room_key": "research_desk",
        "role": "ResearchCase organizer for approved manual or future intake flows.",
        "guardrails": ["no automatic scanner-to-ResearchCase creation", "no source registry writes"],
    },
    {
        "key": "quality_sentinel",
        "name": "Quality Sentinel",
        "room_key": "quality_court",
        "role": "Safety, completeness, and workflow reviewer.",
        "guardrails": ["no publishing", "no recommendation language", "no automatic approval"],
    },
    {
        "key": "playbook_scribe",
        "name": "Playbook Scribe",
        "room_key": "playbook_workshop",
        "role": "AI-safe methodology document maintainer.",
        "guardrails": ["no raw course transcripts", "no copyrighted raw course text"],
    },
]


async def ensure_default_rooms_and_agents(db: AsyncSession) -> None:
    result = await db.execute(select(AgentRoom))
    existing_rooms = {room.key: room for room in result.scalars().all()}

    for data in DEFAULT_ROOMS:
        if data["key"] not in existing_rooms:
            room = AgentRoom(id=uuid.uuid4(), **data)
            db.add(room)
            existing_rooms[room.key] = room

    await db.flush()

    result = await db.execute(select(AgentProfile))
    existing_agents = {agent.key: agent for agent in result.scalars().all()}

    for data in DEFAULT_AGENTS:
        if data["key"] in existing_agents:
            continue
        room = existing_rooms[data["room_key"]]
        agent = AgentProfile(
            id=uuid.uuid4(),
            key=data["key"],
            name=data["name"],
            room_id=room.id,
            role=data["role"],
            status="planned",
            implementation_status="documented",
            autonomy_level="observer",
            guardrails=data["guardrails"],
        )
        db.add(agent)

    await db.flush()


async def list_rooms(db: AsyncSession, *, status: str | None = None) -> list[AgentRoom]:
    q = select(AgentRoom).order_by(AgentRoom.display_order, AgentRoom.name)
    if status:
        q = q.where(AgentRoom.status == status)
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_agents(
    db: AsyncSession,
    *,
    room_key: str | None = None,
    status: str | None = None,
    implementation_status: str | None = None,
) -> list[AgentProfile]:
    q = select(AgentProfile).join(AgentRoom).options(selectinload(AgentProfile.room)).order_by(AgentProfile.name)
    if room_key:
        q = q.where(AgentRoom.key == room_key)
    if status:
        q = q.where(AgentProfile.status == status)
    if implementation_status:
        q = q.where(AgentProfile.implementation_status == implementation_status)
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_activity(db: AsyncSession, filters: dict[str, Any]) -> list[AgentActivity]:
    limit = _safe_limit(filters.get("limit"))
    q = (
        select(AgentActivity)
        .options(selectinload(AgentActivity.agent), selectinload(AgentActivity.room))
        .order_by(desc(AgentActivity.created_at))
        .limit(limit)
    )
    if filters.get("room_key"):
        q = q.join(AgentRoom, AgentActivity.room_id == AgentRoom.id).where(AgentRoom.key == filters["room_key"])
    if filters.get("agent_key"):
        q = q.join(AgentProfile, AgentActivity.agent_id == AgentProfile.id).where(AgentProfile.key == filters["agent_key"])
    if filters.get("severity"):
        q = q.where(AgentActivity.severity == filters["severity"])
    if filters.get("status"):
        q = q.where(AgentActivity.status == filters["status"])
    if filters.get("related_entity_type"):
        q = q.where(AgentActivity.related_entity_type == filters["related_entity_type"])
    if filters.get("related_entity_id"):
        q = q.where(AgentActivity.related_entity_id == filters["related_entity_id"])
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_diagnostics(db: AsyncSession, filters: dict[str, Any]) -> list[AgentDiagnosticEvent]:
    limit = _safe_limit(filters.get("limit"))
    q = (
        select(AgentDiagnosticEvent)
        .options(selectinload(AgentDiagnosticEvent.agent), selectinload(AgentDiagnosticEvent.room))
        .order_by(desc(AgentDiagnosticEvent.created_at))
        .limit(limit)
    )
    if filters.get("room_key"):
        q = q.join(AgentRoom, AgentDiagnosticEvent.room_id == AgentRoom.id).where(AgentRoom.key == filters["room_key"])
    if filters.get("agent_key"):
        q = q.join(AgentProfile, AgentDiagnosticEvent.agent_id == AgentProfile.id).where(AgentProfile.key == filters["agent_key"])
    if filters.get("severity"):
        q = q.where(AgentDiagnosticEvent.severity == filters["severity"])
    if filters.get("diagnostic_type"):
        q = q.where(AgentDiagnosticEvent.diagnostic_type == filters["diagnostic_type"])
    if filters.get("related_entity_type"):
        q = q.where(AgentDiagnosticEvent.related_entity_type == filters["related_entity_type"])
    if filters.get("related_entity_id"):
        q = q.where(AgentDiagnosticEvent.related_entity_id == filters["related_entity_id"])
    result = await db.execute(q)
    return list(result.scalars().all())


async def list_proposals(db: AsyncSession, filters: dict[str, Any]) -> list[AgentLearningProposal]:
    limit = _safe_limit(filters.get("limit"))
    q = (
        select(AgentLearningProposal)
        .options(selectinload(AgentLearningProposal.agent), selectinload(AgentLearningProposal.room))
        .order_by(desc(AgentLearningProposal.created_at))
        .limit(limit)
    )
    if filters.get("room_key"):
        q = q.join(AgentRoom, AgentLearningProposal.room_id == AgentRoom.id).where(AgentRoom.key == filters["room_key"])
    if filters.get("agent_key"):
        q = q.join(AgentProfile, AgentLearningProposal.agent_id == AgentProfile.id).where(AgentProfile.key == filters["agent_key"])
    if filters.get("status"):
        q = q.where(AgentLearningProposal.status == filters["status"])
    if filters.get("risk_level"):
        q = q.where(AgentLearningProposal.risk_level == filters["risk_level"])
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_proposal_status(
    db: AsyncSession,
    proposal_id: str,
    status: str,
    reviewer_note: str | None = None,
) -> AgentLearningProposal:
    if status not in ALLOWED_PROPOSAL_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid proposal status")

    try:
        pid = uuid.UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid proposal id")

    result = await db.execute(select(AgentLearningProposal).where(AgentLearningProposal.id == pid))
    proposal = result.scalars().first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if status != proposal.status and status not in ALLOWED_TRANSITIONS.get(proposal.status, set()):
        raise HTTPException(status_code=409, detail="Invalid proposal status transition")

    if status != proposal.status:
        proposal.status = status
        proposal.reviewed_at = datetime.now(timezone.utc)
    if reviewer_note is not None:
        proposal.reviewer_note = reviewer_note
    proposal.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return proposal


def _safe_limit(value: Any) -> int:
    try:
        return min(max(int(value or 50), 1), 200)
    except (TypeError, ValueError):
        return 50
