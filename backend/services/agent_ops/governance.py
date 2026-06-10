import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.investment import DetectionRun, DocumentationExtractionField, SpecialSituation
from backend.models.investment_research import ResearchCase
from backend.models.observability import AgentRun
from backend.services.investment.course_documentation_map import COURSE_DOCUMENTATION_MAPS, get_course_documentation_map
from backend.services.observability import cron_reader
from backend.services.observability.run_logger import finish_run, start_run


BASE_GUARDRAILS = [
    "No investment recommendations.",
    "No trading-direction language.",
    "No automatic evidence verification.",
    "No automatic case promotion, discard, publication, or watchlist decisions.",
    "No live AI execution.",
    "No cron changes.",
]

FORBIDDEN_ACTIONS = [
    "auto_verify_evidence",
    "auto_promote_case",
    "auto_discard_case",
    "auto_publish",
    "make_investment_recommendation",
    "trigger_scan",
    "change_cron",
    "enable_live_ai",
]


@dataclass(frozen=True)
class RoomConfig:
    room_key: str
    room_label: str
    description: str
    display_order: int


@dataclass(frozen=True)
class AgentConfig:
    agent_key: str
    display_name: str
    backend_agent_name: str
    room_key: str
    role_title: str
    role_description: str
    enabled: bool
    schedule_enabled: bool
    schedule_cron: str | None
    schedule_label: str
    run_mode: str
    allowed_actions: list[str]
    forbidden_actions: list[str]
    safety_level: str
    data_sources: list[str]
    output_types: list[str]
    command_matchers: list[str]


ROOMS = [
    RoomConfig(
        room_key="detection_room",
        room_label="Detection Room",
        description="SEC detection, source monitoring, scanner health, and candidate intake.",
        display_order=10,
    ),
    RoomConfig(
        room_key="evidence_lab",
        room_label="Evidence Lab",
        description="Filing parsing, document metadata, provenance, and draft extraction review.",
        display_order=20,
    ),
    RoomConfig(
        room_key="playbook_workshop",
        room_label="Playbook Workshop",
        description="Course references, study guides, documentation maps, and methodology gaps.",
        display_order=30,
    ),
    RoomConfig(
        room_key="research_desk",
        room_label="Research Desk",
        description="SpecialSituation and ResearchCase organization for manual research flow.",
        display_order=40,
    ),
    RoomConfig(
        room_key="quality_court",
        room_label="Quality Court",
        description="Safety, completeness, duplicates, readiness wording, and manual review gaps.",
        display_order=50,
    ),
    RoomConfig(
        room_key="executive_office",
        room_label="Executive Office",
        description="Read-only governance diagnostics for Fontana and Dani Weber.",
        display_order=60,
    ),
]

ROOM_BY_KEY = {room.room_key: room for room in ROOMS}


AGENTS = [
    AgentConfig(
        agent_key="edgar_scout",
        display_name="Edgar Scout",
        backend_agent_name="investment_scanner",
        room_key="detection_room",
        role_title="SEC Detection Observer",
        role_description="Monitors SEC detection runs, scanner health, and candidate creation gates.",
        enabled=True,
        schedule_enabled=True,
        schedule_cron=None,
        schedule_label="Cron-managed SEC detection cadence when configured.",
        run_mode="scheduled_live_gated",
        allowed_actions=["read_sec_metadata", "record_detection_runs", "create_candidates_when_live_gates_pass"],
        forbidden_actions=FORBIDDEN_ACTIONS,
        safety_level="high",
        data_sources=["SEC EDGAR", "detection_runs", "special_situations"],
        output_types=["DetectionRun", "candidate SpecialSituation", "scanner diagnostics"],
        command_matchers=["investment_scanner", "sec_edgar", "scan"],
    ),
    AgentConfig(
        agent_key="form_parser",
        display_name="Form Parser",
        backend_agent_name="investment_classifier",
        room_key="evidence_lab",
        role_title="Filing Classification Observer",
        role_description="Classifies filing metadata and reports candidate-only/manual-review reasons.",
        enabled=True,
        schedule_enabled=False,
        schedule_cron=None,
        schedule_label="Manual or called by detection flow.",
        run_mode="manual_only",
        allowed_actions=["classify_filing_metadata", "mark_candidate_only", "report_human_review_required"],
        forbidden_actions=FORBIDDEN_ACTIONS,
        safety_level="high",
        data_sources=["SEC filing metadata", "detection classifier rules"],
        output_types=["classification report", "candidate-only reason"],
        command_matchers=["investment_classifier", "classifier", "classification"],
    ),
    AgentConfig(
        agent_key="router_analyst",
        display_name="Router Analyst",
        backend_agent_name="methodology_router",
        room_key="detection_room",
        role_title="Methodology Routing Observer",
        role_description="Explains deterministic routing between situation types and playbooks.",
        enabled=True,
        schedule_enabled=False,
        schedule_cron=None,
        schedule_label="Manual only.",
        run_mode="manual_only",
        allowed_actions=["read_routing_metadata", "report_missing_routes"],
        forbidden_actions=FORBIDDEN_ACTIONS,
        safety_level="high",
        data_sources=["course documentation map", "situation metadata"],
        output_types=["routing diagnostic"],
        command_matchers=["router", "methodology"],
    ),
    AgentConfig(
        agent_key="playbook_scribe",
        display_name="Playbook Scribe",
        backend_agent_name="course_reference_agent",
        room_key="playbook_workshop",
        role_title="Course Reference Steward",
        role_description="Surfaces missing or weak course reference metadata without exposing course text.",
        enabled=True,
        schedule_enabled=False,
        schedule_cron=None,
        schedule_label="Manual only.",
        run_mode="manual_only",
        allowed_actions=["read_course_metadata", "report_missing_course_references"],
        forbidden_actions=FORBIDDEN_ACTIONS + ["expose_private_course_text"],
        safety_level="high",
        data_sources=["course_documentation_map", "knowledge_base metadata"],
        output_types=["course reference diagnostic", "study guide gap"],
        command_matchers=["course_reference_agent", "course", "playbook"],
    ),
    AgentConfig(
        agent_key="case_builder",
        display_name="Case Builder",
        backend_agent_name="investment_evaluator",
        room_key="research_desk",
        role_title="Research Case Organizer",
        role_description="Organizes research-case metadata only under manual/gated flows.",
        enabled=True,
        schedule_enabled=False,
        schedule_cron=None,
        schedule_label="Manual/gated only.",
        run_mode="manual_only",
        allowed_actions=["read_case_metadata", "summarize_workflow_status"],
        forbidden_actions=FORBIDDEN_ACTIONS + ["change_evaluator_v2_global_behavior"],
        safety_level="critical",
        data_sources=["special_situations", "research_cases"],
        output_types=["case organization summary"],
        command_matchers=["investment_evaluator", "case_builder"],
    ),
    AgentConfig(
        agent_key="quality_sentinel",
        display_name="Quality Sentinel",
        backend_agent_name="quality_sentinel",
        room_key="quality_court",
        role_title="Workflow Safety Reviewer",
        role_description="Reports safety, completeness, evidence, and wording gaps for human review.",
        enabled=True,
        schedule_enabled=False,
        schedule_cron=None,
        schedule_label="Manual only.",
        run_mode="diagnostic_only",
        allowed_actions=["read_workflow_metadata", "report_quality_gaps"],
        forbidden_actions=FORBIDDEN_ACTIONS,
        safety_level="critical",
        data_sources=["special_situations", "documentation_extraction_fields", "agent_runs"],
        output_types=["quality diagnostic"],
        command_matchers=["quality_sentinel", "quality"],
    ),
    AgentConfig(
        agent_key="fontana",
        display_name="Fontana",
        backend_agent_name="fontana_governance",
        room_key="executive_office",
        role_title="CTO / System Governor",
        role_description="Read-only technical governance agent for system health and implementation risks.",
        enabled=True,
        schedule_enabled=False,
        schedule_cron=None,
        schedule_label="Manual preview now; schedule metadata only until cron is approved.",
        run_mode="diagnostic_only",
        allowed_actions=["read_system_metadata", "create_governance_preview_log", "report_engineering_findings"],
        forbidden_actions=FORBIDDEN_ACTIONS + ["apply_fixes"],
        safety_level="critical",
        data_sources=["agent_runs", "detection_runs", "course_documentation_map", "documentation_extraction_fields"],
        output_types=["Fontana governance report"],
        command_matchers=["fontana", "fontana_governance"],
    ),
    AgentConfig(
        agent_key="dani_weber",
        display_name="Dani Weber",
        backend_agent_name="dani_weber_governance",
        room_key="executive_office",
        role_title="COO / Operations Governor",
        role_description="Read-only operations governance agent for workflow bottlenecks and manual workload.",
        enabled=True,
        schedule_enabled=False,
        schedule_cron=None,
        schedule_label="Manual preview now; schedule metadata only until cron is approved.",
        run_mode="diagnostic_only",
        allowed_actions=["read_operations_metadata", "create_governance_preview_log", "report_manual_workflow_findings"],
        forbidden_actions=FORBIDDEN_ACTIONS,
        safety_level="critical",
        data_sources=["special_situations", "research_cases", "documentation_extraction_fields", "agent_runs"],
        output_types=["Dani Weber operations report"],
        command_matchers=["dani_weber", "weber", "operations_governance"],
    ),
]

AGENT_BY_KEY = {agent.agent_key: agent for agent in AGENTS}
AGENT_BY_BACKEND = {agent.backend_agent_name: agent for agent in AGENTS}


async def list_agent_configs(db: AsyncSession, *, room_key: str | None = None) -> list[dict[str, Any]]:
    runs_by_agent = await _recent_runs_by_agent(db)
    upcoming_by_agent = _upcoming_by_agent(days=7)
    agents = [agent for agent in AGENTS if room_key is None or agent.room_key == room_key]
    return [_serialize_agent_config(agent, runs_by_agent, upcoming_by_agent) for agent in agents]


async def get_agent_config(db: AsyncSession, agent_key: str) -> dict[str, Any]:
    agent = AGENT_BY_KEY.get(agent_key)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    runs_by_agent = await _recent_runs_by_agent(db, agent_names=[agent.backend_agent_name])
    upcoming_by_agent = _upcoming_by_agent(days=7)
    return _serialize_agent_config(agent, runs_by_agent, upcoming_by_agent)


async def list_room_configs(db: AsyncSession) -> list[dict[str, Any]]:
    agents = await list_agent_configs(db)
    agents_by_room: dict[str, list[dict[str, Any]]] = {}
    for agent in agents:
        agents_by_room.setdefault(agent["room_key"], []).append(agent)
    return [_serialize_room(room, agents_by_room.get(room.room_key, [])) for room in ROOMS]


async def get_room_config(db: AsyncSession, room_key: str) -> dict[str, Any]:
    room = ROOM_BY_KEY.get(room_key)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    agents = await list_agent_configs(db, room_key=room_key)
    return _serialize_room(room, agents)


async def build_fontana_report(db: AsyncSession, *, run_mode: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    runs_by_agent = await _recent_runs_by_agent(db)
    detection = await _latest_detection_run(db)
    draft_count = await _count_draft_extractions(db)
    course_gaps = _course_reference_gaps()

    findings: list[dict[str, Any]] = []
    stale_agents = []
    for agent in AGENTS:
        runs = runs_by_agent.get(agent.backend_agent_name, [])
        last_run = runs[0] if runs else None
        stale = _is_stale(last_run.started_at if last_run else None, now, agent)
        if stale:
            stale_agents.append({
                "agent_key": agent.agent_key,
                "backend_agent_name": agent.backend_agent_name,
                "last_run_at": _dt(last_run.started_at) if last_run else None,
                "reason": "No recent run is recorded for this observable agent.",
            })

    if stale_agents:
        findings.append(_finding(
            "FONTANA_STALE_AGENT_RUNS",
            "medium",
            "Agent Ops",
            "Some observable agents have no recent run metadata.",
            "Campus and execution calendar may show empty or stale operational panels.",
            f"{len(stale_agents)} stale or never-run agent configs.",
            "Wire real run logging or scheduled preview logging for these agents.",
            "Codex",
        ))

    if detection and detection.status == "failed":
        findings.append(_finding(
            "FONTANA_DETECTION_FAILED",
            "high",
            "SEC Detection",
            "Latest SEC detection run failed.",
            detection.error_message or "The latest DetectionRun has failed status.",
            f"detection_run:{detection.id}",
            "Inspect SEC detection logs and keep live-create gates closed until resolved.",
            "Codex",
        ))

    if course_gaps:
        findings.append(_finding(
            "FONTANA_COURSE_REFERENCE_GAPS",
            "medium",
            "Study Guide",
            "Some course documentation map entries lack concrete source references.",
            "Study Guide cards may be less actionable without chapter/source metadata.",
            ", ".join(course_gaps[:5]),
            "Add chapter/source metadata to remaining course map entries.",
            "Dani",
        ))

    if draft_count:
        findings.append(_finding(
            "FONTANA_DRAFT_EXTRACTIONS_PRESENT",
            "low",
            "Documentation Workflow",
            "Draft extraction fields exist and must stay visibly unverified.",
            "Draft data is useful only when the UI keeps it distinct from verified evidence.",
            f"documentation_extraction_fields:draft_count={draft_count}",
            "Keep Accept/Edit/Reject review separate from extraction.",
            "Claude",
        ))

    severity_counts = _severity_counts(findings)
    system_health = "critical" if severity_counts["critical"] else "warning" if findings else "healthy"
    report_id = f"fontana-{now.strftime('%Y%m%d%H%M%S')}"
    return {
        "report_id": report_id,
        "agent_key": "fontana",
        "generated_at": now.isoformat(),
        "run_mode": run_mode,
        "system_health": system_health,
        "severity_counts": severity_counts,
        "scope_reviewed": [
            "agent configuration catalog",
            "agent_runs recency",
            "SEC detection latest run",
            "Study Guide course metadata",
            "documentation draft extraction status",
        ],
        "findings": findings,
        "stale_agents": stale_agents,
        "failed_endpoints": [],
        "data_inconsistencies": [],
        "deployment_warnings": [],
        "recommended_engineering_tasks": [finding["recommended_engineering_task"] for finding in findings],
        "guardrails": BASE_GUARDRAILS,
    }


async def run_fontana_preview(db: AsyncSession) -> dict[str, Any]:
    run_id = await start_run(
        db,
        agent_name="fontana_governance",
        agent_type="governance",
        module="backend.services.agent_ops.governance",
        runtime="fastapi",
        trigger_source="manual_preview",
        task_name="fontana_governance_preview",
        input_summary="Read-only Fontana governance preview.",
        human_approval_required=False,
    )
    report = await build_fontana_report(db, run_mode="manual")
    await finish_run(
        db,
        run_id,
        output_summary=f"{len(report['findings'])} findings; health={report['system_health']}",
        final_outcome="Read-only governance preview generated. No investment data mutated.",
        database_records_created={"governance_report_snapshots": 0},
    )
    await db.commit()
    report["linked_run_id"] = str(run_id) if run_id else None
    return report


async def build_dani_weber_report(db: AsyncSession, *, run_mode: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    situations = await _recent_situations(db)
    research_cases = await _recent_research_cases(db)
    draft_count = await _count_draft_extractions(db)
    verified_count = await _count_verified_extractions(db)
    case_funnel = _build_case_funnel(situations, research_cases)
    priority_cases = _priority_cases(situations)
    bottleneck_rooms = _bottleneck_rooms(case_funnel, draft_count, verified_count)
    operating_health = "stalled" if not situations and not research_cases else "bottlenecked" if bottleneck_rooms else "flowing"
    cases_touched_24h = await _cases_touched_24h(db)
    report_id = f"dani-weber-{now.strftime('%Y%m%d%H%M%S')}"

    operational_findings = []
    if priority_cases:
        operational_findings.append({
            "severity": "medium",
            "affected_area": "Manual Review Queue",
            "title": "Cases need manual workflow attention.",
            "description": "These cases are prioritized by missing resources, draft evidence state, or stale workflow metadata.",
        })
    if draft_count and not verified_count:
        operational_findings.append({
            "severity": "medium",
            "affected_area": "Evidence Lab",
            "title": "Draft fields exist without verified extraction fields.",
            "description": "Draft extraction is present; manual review remains the next operational step.",
        })

    return {
        "report_id": report_id,
        "agent_key": "dani_weber",
        "generated_at": now.isoformat(),
        "run_mode": run_mode,
        "operating_health": operating_health,
        "case_funnel": case_funnel,
        "cases_touched_24h": cases_touched_24h,
        "stuck_cases": priority_cases,
        "bottleneck_rooms": bottleneck_rooms,
        "manual_actions_count": len(priority_cases) + draft_count,
        "priority_cases": priority_cases,
        "operational_findings": operational_findings,
        "recommended_next_actions": [
            "Review candidate sources before treating them as evidence.",
            "Review draft extraction fields with Accept/Edit/Reject workflow when implemented.",
            "Keep promotion and verification manual.",
        ],
        "guardrails": BASE_GUARDRAILS,
    }


async def run_dani_weber_preview(db: AsyncSession) -> dict[str, Any]:
    run_id = await start_run(
        db,
        agent_name="dani_weber_governance",
        agent_type="governance",
        module="backend.services.agent_ops.governance",
        runtime="fastapi",
        trigger_source="manual_preview",
        task_name="dani_weber_governance_preview",
        input_summary="Read-only Dani Weber operations preview.",
        human_approval_required=False,
    )
    report = await build_dani_weber_report(db, run_mode="manual")
    await finish_run(
        db,
        run_id,
        output_summary=f"{len(report['priority_cases'])} priority cases; health={report['operating_health']}",
        final_outcome="Read-only operations preview generated. No investment decisions mutated.",
        database_records_created={"governance_report_snapshots": 0},
    )
    await db.commit()
    report["linked_run_id"] = str(run_id) if run_id else None
    return report


async def build_execution_calendar(
    db: AsyncSession,
    *,
    days: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    start, end = _calendar_window(now, days=days, from_date=from_date, to_date=to_date)
    past_events = await _past_run_events(db, start, end)
    upcoming_events = _upcoming_events(start, end)
    events = sorted(past_events + upcoming_events, key=lambda item: item["start_time"])
    return {
        "generated_at": now.isoformat(),
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "count": len(events),
        "events": events,
    }


async def _recent_runs_by_agent(
    db: AsyncSession,
    *,
    agent_names: list[str] | None = None,
) -> dict[str, list[AgentRun]]:
    q = select(AgentRun).order_by(desc(AgentRun.started_at)).limit(500)
    if agent_names:
        q = q.where(AgentRun.agent_name.in_(agent_names))
    result = await db.execute(q)
    grouped: dict[str, list[AgentRun]] = {}
    for run in result.scalars().all():
        grouped.setdefault(run.agent_name, []).append(run)
    return {name: runs[:10] for name, runs in grouped.items()}


def _serialize_agent_config(
    agent: AgentConfig,
    runs_by_agent: dict[str, list[AgentRun]],
    upcoming_by_agent: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    room = ROOM_BY_KEY[agent.room_key]
    runs = runs_by_agent.get(agent.backend_agent_name, [])
    last_run = runs[0] if runs else None
    upcoming = upcoming_by_agent.get(agent.agent_key, {})
    schedule_cron = upcoming.get("schedule") or agent.schedule_cron
    return {
        "agent_key": agent.agent_key,
        "key": agent.agent_key,
        "display_name": agent.display_name,
        "name": agent.display_name,
        "backend_agent_name": agent.backend_agent_name,
        "room_key": agent.room_key,
        "room_label": room.room_label,
        "role_title": agent.role_title,
        "role_description": agent.role_description,
        "enabled": agent.enabled,
        "schedule_enabled": bool(agent.schedule_enabled or schedule_cron),
        "schedule_cron": schedule_cron,
        "schedule_label": agent.schedule_label,
        "next_run_at": upcoming.get("scheduled_at"),
        "run_mode": agent.run_mode,
        "allowed_actions": agent.allowed_actions,
        "forbidden_actions": agent.forbidden_actions,
        "safety_level": agent.safety_level,
        "data_sources": agent.data_sources,
        "output_types": agent.output_types,
        "last_run_at": _dt(last_run.started_at) if last_run else None,
        "last_run_status": last_run.status if last_run else None,
        "last_10_runs": [_serialize_run_summary(run) for run in runs],
    }


def _serialize_room(room: RoomConfig, agents: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "room_key": room.room_key,
        "key": room.room_key,
        "room_label": room.room_label,
        "name": room.room_label,
        "description": room.description,
        "display_order": room.display_order,
        "agent_keys": [agent["agent_key"] for agent in agents],
        "agents": agents,
    }


def _serialize_run_summary(run: AgentRun) -> dict[str, Any]:
    return {
        "run_id": str(run.id),
        "status": run.status,
        "started_at": _dt(run.started_at),
        "finished_at": _dt(run.finished_at),
        "duration_ms": run.duration_ms,
        "trigger_source": run.trigger_source,
        "task_name": run.task_name,
        "output_summary": run.output_summary,
        "error_message": run.error_message,
        "database_records_created": run.database_records_created,
    }


def _upcoming_by_agent(days: int) -> dict[str, dict[str, Any]]:
    try:
        entries = cron_reader.get_upcoming(days=days).get("entries", [])
    except Exception:
        entries = []
    grouped: dict[str, dict[str, Any]] = {}
    for entry in entries:
        agent = _agent_from_command(entry.get("command") or "")
        if not agent or agent.agent_key in grouped:
            continue
        grouped[agent.agent_key] = entry
    return grouped


def _agent_from_command(command: str) -> AgentConfig | None:
    command_lower = command.lower()
    for agent in AGENTS:
        if any(matcher.lower() in command_lower for matcher in agent.command_matchers):
            return agent
    return None


async def _latest_detection_run(db: AsyncSession) -> DetectionRun | None:
    result = await db.execute(select(DetectionRun).order_by(desc(DetectionRun.started_at)).limit(1))
    return result.scalars().first()


async def _count_draft_extractions(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(DocumentationExtractionField).where(DocumentationExtractionField.status == "draft")
    )
    return int(result.scalar() or 0)


async def _count_verified_extractions(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).select_from(DocumentationExtractionField).where(DocumentationExtractionField.status == "verified")
    )
    return int(result.scalar() or 0)


async def _recent_situations(db: AsyncSession) -> list[SpecialSituation]:
    result = await db.execute(select(SpecialSituation).order_by(desc(SpecialSituation.detected_at)).limit(200))
    return list(result.scalars().all())


async def _recent_research_cases(db: AsyncSession) -> list[ResearchCase]:
    result = await db.execute(select(ResearchCase).order_by(desc(ResearchCase.created_at)).limit(200))
    return list(result.scalars().all())


async def _cases_touched_24h(db: AsyncSession) -> int:
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    result = await db.execute(select(AgentRun).where(AgentRun.started_at >= since).limit(200))
    count = 0
    for run in result.scalars().all():
        records = run.database_records_created or {}
        for key in ("special_situations", "research_cases", "documentation_extraction_fields"):
            value = records.get(key)
            if isinstance(value, int):
                count += value
    return count


def _course_reference_gaps() -> list[str]:
    gaps = []
    for situation_type in COURSE_DOCUMENTATION_MAPS:
        item = get_course_documentation_map(situation_type)
        for chapter in item.get("relevant_course_chapters", []):
            if not isinstance(chapter, dict):
                gaps.append(f"{situation_type}:legacy_chapter_value")
                continue
            if not chapter.get("chapter_id") or not chapter.get("source_file"):
                gaps.append(f"{situation_type}:{chapter.get('title') or chapter.get('chapter_id') or 'unknown'}")
    return gaps


def _build_case_funnel(situations: list[SpecialSituation], research_cases: list[ResearchCase]) -> dict[str, int]:
    funnel = {
        "new_detection": 0,
        "needs_resources": 0,
        "checklist_in_progress": 0,
        "ready_for_research": 0,
        "promoted": 0,
        "watchlist": 0,
        "archived": 0,
    }
    for situation in situations:
        status = (situation.status or "").lower()
        evaluation = situation.evaluation or {}
        if status in {"archived", "discarded"}:
            funnel["archived"] += 1
        elif status in {"watchlist", "monitoring"}:
            funnel["watchlist"] += 1
        elif status in {"promoted", "research"}:
            funnel["promoted"] += 1
        elif evaluation.get("documentation_status") == "needs_resources":
            funnel["needs_resources"] += 1
        elif evaluation.get("workflow_status") == "checklist_in_progress":
            funnel["checklist_in_progress"] += 1
        else:
            funnel["new_detection"] += 1
    for case in research_cases:
        if (case.status or "").lower() in {"ready", "ready_for_research"}:
            funnel["ready_for_research"] += 1
    return funnel


def _priority_cases(situations: list[SpecialSituation]) -> list[dict[str, Any]]:
    priority = []
    now = datetime.now(timezone.utc)
    for situation in situations[:50]:
        evaluation = situation.evaluation or {}
        reason = None
        next_action = None
        if evaluation.get("documentation_status") == "needs_resources":
            reason = "Needs documentation resources."
            next_action = "Add or review candidate source manually."
        elif evaluation.get("candidate_sources_count", 0):
            reason = "Candidate sources exist and need human evidence review."
            next_action = "Review candidate sources before marking evidence verified."
        elif _is_stale(situation.detected_at, now, None):
            reason = "Detected case has no recent workflow movement in the visible metadata."
            next_action = "Review current workflow phase and required documents."
        if reason:
            priority.append({
                "case_id": str(situation.id),
                "company_name": situation.company_name,
                "situation_type": situation.situation_type,
                "reason": reason,
                "next_action": next_action,
            })
        if len(priority) >= 10:
            break
    return priority


def _bottleneck_rooms(case_funnel: dict[str, int], draft_count: int, verified_count: int) -> list[dict[str, Any]]:
    bottlenecks = []
    if case_funnel["needs_resources"]:
        bottlenecks.append({
            "room_key": "research_desk",
            "room_label": "Research Desk",
            "reason": "Cases are waiting for resources.",
            "count": case_funnel["needs_resources"],
        })
    if draft_count and not verified_count:
        bottlenecks.append({
            "room_key": "evidence_lab",
            "room_label": "Evidence Lab",
            "reason": "Draft extraction fields need manual review.",
            "count": draft_count,
        })
    return bottlenecks


async def _past_run_events(db: AsyncSession, start: datetime, end: datetime) -> list[dict[str, Any]]:
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.started_at >= start, AgentRun.started_at <= end)
        .order_by(desc(AgentRun.started_at))
        .limit(500)
    )
    events = []
    for run in result.scalars().all():
        agent = AGENT_BY_BACKEND.get(run.agent_name) or _agent_from_command(" ".join([run.agent_name, run.task_name or ""]))
        if not agent:
            continue
        events.append(_calendar_event_from_run(run, agent))
    return events


def _upcoming_events(start: datetime, end: datetime) -> list[dict[str, Any]]:
    days = max(1, min(30, (end - start).days + 1))
    try:
        entries = cron_reader.get_upcoming(days=days).get("entries", [])
    except Exception:
        entries = []
    events = []
    for entry in entries:
        scheduled_at = _parse_dt(entry.get("scheduled_at"))
        if not scheduled_at or scheduled_at < start or scheduled_at > end:
            continue
        agent = _agent_from_command(entry.get("command") or "")
        if not agent:
            continue
        events.append(_calendar_event_from_cron(entry, scheduled_at, agent))
    return events


def _calendar_event_from_run(run: AgentRun, agent: AgentConfig) -> dict[str, Any]:
    records = run.database_records_created or {}
    warnings_count = 1 if run.status in {"warning", "partial"} else 0
    errors_count = 1 if run.status == "failed" or run.error_message else 0
    status = _calendar_status(run.status)
    return {
        "event_id": f"run-{run.id}",
        "agent_key": agent.agent_key,
        "agent_display_name": agent.display_name,
        "backend_agent_name": agent.backend_agent_name,
        "room_key": agent.room_key,
        "room_label": ROOM_BY_KEY[agent.room_key].room_label,
        "title": run.task_name or f"{agent.display_name} run",
        "start_time": _dt(run.started_at),
        "end_time": _dt(run.finished_at),
        "expected_duration": None,
        "status": status,
        "run_type": "scheduled" if run.trigger_source in {"cron", "scheduled"} else "manual",
        "mode": _mode_for_agent(agent),
        "last_run_status": run.status,
        "cases_touched": _cases_touched(records),
        "records_created": records,
        "warnings_count": warnings_count,
        "errors_count": errors_count,
        "allowed_actions": agent.allowed_actions,
        "forbidden_actions": agent.forbidden_actions,
        "linked_run_id": str(run.id),
        "cron_expression": None,
        "command_summary": run.input_summary,
        "output_summary": run.output_summary,
        "guardrail_summary": "; ".join(BASE_GUARDRAILS),
    }


def _calendar_event_from_cron(entry: dict[str, Any], scheduled_at: datetime, agent: AgentConfig) -> dict[str, Any]:
    return {
        "event_id": f"upcoming-{agent.agent_key}-{scheduled_at.isoformat()}",
        "agent_key": agent.agent_key,
        "agent_display_name": agent.display_name,
        "backend_agent_name": agent.backend_agent_name,
        "room_key": agent.room_key,
        "room_label": ROOM_BY_KEY[agent.room_key].room_label,
        "title": f"Scheduled {agent.display_name}",
        "start_time": scheduled_at.isoformat(),
        "end_time": None,
        "expected_duration": "unknown",
        "status": "upcoming",
        "run_type": "scheduled",
        "mode": _mode_for_agent(agent),
        "last_run_status": None,
        "cases_touched": 0,
        "records_created": {},
        "warnings_count": 0,
        "errors_count": 0,
        "allowed_actions": agent.allowed_actions,
        "forbidden_actions": agent.forbidden_actions,
        "linked_run_id": None,
        "cron_expression": entry.get("schedule"),
        "command_summary": entry.get("command"),
        "output_summary": None,
        "guardrail_summary": "; ".join(BASE_GUARDRAILS),
    }


def _calendar_window(
    now: datetime,
    *,
    days: int | None,
    from_date: str | None,
    to_date: str | None,
) -> tuple[datetime, datetime]:
    if from_date or to_date:
        start = _parse_date_start(from_date) if from_date else now - timedelta(days=1)
        end = _parse_date_end(to_date) if to_date else now + timedelta(days=1)
    else:
        window_days = max(1, min(int(days or 1), 30))
        start = now - timedelta(days=window_days)
        end = now + timedelta(days=window_days)
    return start, end


def _parse_date_start(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(value)
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _parse_date_end(value: str | None) -> datetime:
    start = _parse_date_start(value)
    if "T" not in value:
        return start + timedelta(days=1) - timedelta(microseconds=1)
    return start


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _calendar_status(status: str) -> str:
    mapping = {
        "started": "running",
        "running": "running",
        "completed": "success",
        "success": "success",
        "failed": "failed",
        "warning": "warning",
        "partial": "warning",
        "skipped": "skipped",
    }
    return mapping.get(status, "warning")


def _mode_for_agent(agent: AgentConfig) -> str:
    if agent.run_mode == "scheduled_dry_run":
        return "dry_run"
    if agent.run_mode == "scheduled_live_gated":
        return "live_gated"
    if agent.run_mode == "diagnostic_only":
        return "diagnostic_only"
    return "read_only"


def _cases_touched(records: dict[str, Any]) -> int:
    total = 0
    for key in ("special_situations", "research_cases"):
        value = records.get(key)
        if isinstance(value, int):
            total += value
    return total


def _is_stale(value: datetime | None, now: datetime, agent: AgentConfig | None) -> bool:
    if value is None:
        return True
    value = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    threshold = timedelta(days=2) if agent and agent.schedule_enabled else timedelta(days=14)
    return now - value > threshold


def _severity_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for finding in findings:
        severity = finding.get("severity")
        if severity in counts:
            counts[severity] += 1
    return counts


def _finding(
    finding_id: str,
    severity: str,
    affected_area: str,
    title: str,
    description: str,
    evidence_reference: str,
    recommended_engineering_task: str,
    owner_hint: str,
) -> dict[str, Any]:
    return {
        "finding_id": finding_id,
        "severity": severity,
        "affected_area": affected_area,
        "title": title,
        "description": description,
        "evidence_reference": evidence_reference,
        "recommended_engineering_task": recommended_engineering_task,
        "owner_hint": owner_hint,
    }


def _dt(value: datetime | None) -> str | None:
    return value.isoformat() if value else None
