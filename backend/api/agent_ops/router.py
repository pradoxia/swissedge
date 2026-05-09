from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.agent_ops import AgentActivity, AgentDiagnosticEvent, AgentLearningProposal, AgentProfile, AgentRoom
from backend.services.agent_ops.service import (
    ensure_default_rooms_and_agents,
    list_activity,
    list_agents,
    list_diagnostics,
    list_proposals,
    list_rooms,
    update_proposal_status,
)

router = APIRouter()


class ProposalPatch(BaseModel):
    status: str
    reviewer_note: str | None = None


@router.get("/rooms")
async def get_rooms(
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    await ensure_default_rooms_and_agents(db)
    await db.commit()
    rooms = await list_rooms(db, status=status)
    return {"count": len(rooms), "rooms": [_serialize_room(room) for room in rooms]}


@router.get("/agents")
async def get_agents(
    room_key: str | None = Query(default=None),
    status: str | None = Query(default=None),
    implementation_status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    await ensure_default_rooms_and_agents(db)
    await db.commit()
    agents = await list_agents(
        db,
        room_key=room_key,
        status=status,
        implementation_status=implementation_status,
    )
    return {"count": len(agents), "agents": [_serialize_agent(agent) for agent in agents]}


@router.get("/activity")
async def get_activity(
    room_key: str | None = Query(default=None),
    agent_key: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    related_entity_type: str | None = Query(default=None),
    related_entity_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    items = await list_activity(db, {
        "room_key": room_key,
        "agent_key": agent_key,
        "severity": severity,
        "status": status,
        "related_entity_type": related_entity_type,
        "related_entity_id": related_entity_id,
        "limit": limit,
    })
    return {"count": len(items), "items": [_serialize_activity(item) for item in items]}


@router.get("/diagnostics")
async def get_diagnostics(
    room_key: str | None = Query(default=None),
    agent_key: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    diagnostic_type: str | None = Query(default=None),
    related_entity_type: str | None = Query(default=None),
    related_entity_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    items = await list_diagnostics(db, {
        "room_key": room_key,
        "agent_key": agent_key,
        "severity": severity,
        "diagnostic_type": diagnostic_type,
        "related_entity_type": related_entity_type,
        "related_entity_id": related_entity_id,
        "limit": limit,
    })
    return {"count": len(items), "items": [_serialize_diagnostic(item) for item in items]}


@router.get("/proposals")
async def get_proposals(
    status: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    room_key: str | None = Query(default=None),
    agent_key: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    items = await list_proposals(db, {
        "status": status,
        "risk_level": risk_level,
        "room_key": room_key,
        "agent_key": agent_key,
        "limit": limit,
    })
    return {"count": len(items), "items": [_serialize_proposal(item) for item in items]}


@router.patch("/proposals/{proposal_id}")
async def patch_proposal(
    proposal_id: str,
    payload: ProposalPatch,
    db: AsyncSession = Depends(get_db),
):
    proposal = await update_proposal_status(
        db,
        proposal_id=proposal_id,
        status=payload.status,
        reviewer_note=payload.reviewer_note,
    )
    await db.commit()
    await db.refresh(proposal)
    return {"proposal": _serialize_proposal(proposal)}


def _dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _room_key(obj: Any) -> str | None:
    room = getattr(obj, "room", None)
    return getattr(room, "key", None)


def _agent_key(obj: Any) -> str | None:
    agent = getattr(obj, "agent", None)
    return getattr(agent, "key", None)


def _serialize_room(room: AgentRoom) -> dict[str, Any]:
    return {
        "id": str(room.id),
        "key": room.key,
        "name": room.name,
        "description": room.description,
        "status": room.status,
        "display_order": room.display_order,
        "created_at": _dt(room.created_at),
        "updated_at": _dt(room.updated_at),
    }


def _serialize_agent(agent: AgentProfile) -> dict[str, Any]:
    return {
        "id": str(agent.id),
        "key": agent.key,
        "name": agent.name,
        "room_id": str(agent.room_id),
        "room_key": _room_key(agent),
        "role": agent.role,
        "status": agent.status,
        "implementation_status": agent.implementation_status,
        "autonomy_level": agent.autonomy_level,
        "guardrails": agent.guardrails,
        "created_at": _dt(agent.created_at),
        "updated_at": _dt(agent.updated_at),
    }


def _serialize_activity(activity: AgentActivity) -> dict[str, Any]:
    return {
        "id": str(activity.id),
        "agent_id": str(activity.agent_id) if activity.agent_id else None,
        "agent_key": _agent_key(activity),
        "room_id": str(activity.room_id) if activity.room_id else None,
        "room_key": _room_key(activity),
        "activity_type": activity.activity_type,
        "title": activity.title,
        "summary": activity.summary,
        "severity": activity.severity,
        "status": activity.status,
        "related_entity_type": activity.related_entity_type,
        "related_entity_id": activity.related_entity_id,
        "metadata": activity.metadata_json,
        "created_at": _dt(activity.created_at),
    }


def _serialize_diagnostic(event: AgentDiagnosticEvent) -> dict[str, Any]:
    return {
        "id": str(event.id),
        "agent_id": str(event.agent_id) if event.agent_id else None,
        "agent_key": _agent_key(event),
        "room_id": str(event.room_id) if event.room_id else None,
        "room_key": _room_key(event),
        "severity": event.severity,
        "diagnostic_type": event.diagnostic_type,
        "title": event.title,
        "description": event.description,
        "evidence": event.evidence,
        "related_entity_type": event.related_entity_type,
        "related_entity_id": event.related_entity_id,
        "created_at": _dt(event.created_at),
    }


def _serialize_proposal(proposal: AgentLearningProposal) -> dict[str, Any]:
    return {
        "id": str(proposal.id),
        "source_diagnostic_id": str(proposal.source_diagnostic_id) if proposal.source_diagnostic_id else None,
        "agent_id": str(proposal.agent_id) if proposal.agent_id else None,
        "agent_key": _agent_key(proposal),
        "room_id": str(proposal.room_id) if proposal.room_id else None,
        "room_key": _room_key(proposal),
        "title": proposal.title,
        "problem_statement": proposal.problem_statement,
        "proposed_change": proposal.proposed_change,
        "expected_benefit": proposal.expected_benefit,
        "risk_level": proposal.risk_level,
        "status": proposal.status,
        "reviewer_note": proposal.reviewer_note,
        "reviewed_by": proposal.reviewed_by,
        "reviewed_at": _dt(proposal.reviewed_at),
        "created_at": _dt(proposal.created_at),
        "updated_at": _dt(proposal.updated_at),
    }
