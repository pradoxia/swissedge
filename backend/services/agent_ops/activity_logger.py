import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.agent_ops import AgentActivity, AgentLearningProposal, AgentResult

logger = logging.getLogger(__name__)


async def log_agent_activity(
    db: AsyncSession,
    *,
    agent_id: uuid.UUID | None = None,
    room_id: uuid.UUID | None = None,
    activity_type: str,
    title: str,
    summary: str | None = None,
    severity: str = "info",
    status: str = "completed",
    related_entity_type: str | None = None,
    related_entity_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> uuid.UUID | None:
    try:
        async with db.begin_nested():
            activity = AgentActivity(
                agent_id=agent_id,
                room_id=room_id,
                activity_type=activity_type,
                title=title,
                summary=summary,
                severity=severity,
                status=status,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                metadata_json=metadata,
            )
            db.add(activity)
            await db.flush()
            return activity.id
    except Exception as exc:
        logger.warning("Agent Ops activity logging failed: %s", exc)
        return None


async def log_agent_result(
    db: AsyncSession,
    *,
    activity_id: uuid.UUID,
    result_type: str,
    summary: str | None = None,
    status: str = "success",
    metrics: dict[str, Any] | None = None,
) -> uuid.UUID | None:
    try:
        async with db.begin_nested():
            result = AgentResult(
                activity_id=activity_id,
                result_type=result_type,
                summary=summary,
                status=status,
                metrics=metrics,
            )
            db.add(result)
            await db.flush()
            return result.id
    except Exception as exc:
        logger.warning("Agent Ops result logging failed: %s", exc)
        return None


async def create_learning_proposal(
    db: AsyncSession,
    *,
    title: str,
    problem_statement: str,
    proposed_change: str,
    expected_benefit: str | None = None,
    risk_level: str = "medium",
    source_diagnostic_id: uuid.UUID | None = None,
    agent_id: uuid.UUID | None = None,
    room_id: uuid.UUID | None = None,
) -> uuid.UUID | None:
    try:
        async with db.begin_nested():
            proposal = AgentLearningProposal(
                source_diagnostic_id=source_diagnostic_id,
                agent_id=agent_id,
                room_id=room_id,
                title=title,
                problem_statement=problem_statement,
                proposed_change=proposed_change,
                expected_benefit=expected_benefit,
                risk_level=risk_level,
                status="proposed",
            )
            db.add(proposal)
            await db.flush()
            return proposal.id
    except Exception as exc:
        logger.warning("Agent Ops learning proposal creation failed: %s", exc)
        return None
