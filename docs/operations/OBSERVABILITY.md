---
document_id: OBSERVABILITY
title: Observability
version: 0.2.0
status: active
owner: Dani
last_updated: 2026-06-08
source_of_truth: true
review_cycle: manual
---

# SwissEdge Observability

Date: 2026-06-08

## Purpose

Observability explains what SwissEdge agents and workflows did, when they did it, what they checked, what they found, and what still requires human approval.

No agent should silently run without logging.

## Existing Structures

- `AgentRun`: stored execution history in `backend/models/observability.py`.
- `AiUsage`: model/token/cost usage in `backend/models/observability.py`.
- `AgentActivity`: short readable activity feed in `backend/models/agent_ops.py`.
- `AgentDiagnosticEvent`: diagnostic events in `backend/models/agent_ops.py`.
- `AgentLearningProposal`: approval-required improvement proposals in `backend/models/agent_ops.py`.
- `DetectionRun`: scanner/detection history in `backend/models/investment.py`.

## Required Agent Profile/Card Fields

Canonical per-agent definitions live in `docs/agents/`.

Every agent should eventually show:

- Name
- Role
- Room
- Skills
- Current status
- Last run
- Next run
- Run mode
- Endpoint
- Permissions and guardrails

## Required Detailed Log Fields

Every execution should eventually log:

- Agent slug/name
- Start time
- End time
- Status
- Run mode
- Trigger type
- Endpoint called
- What was checked
- What was found
- Related entity type and ID
- Errors
- Recommendations created
- Whether human approval is required

## Activity Feed Requirements

Activity feed entries should be short and readable:

- What happened.
- Which agent/room did it.
- Which case/entity it relates to.
- Severity.
- Status.
- Manual next action if any.

The feed must be useful for Dani to understand actual agent work. It must not imply actions that did not happen.

## Health States

Use clear states:

- healthy
- warning
- degraded
- failed
- stale
- unknown

Empty data must be labeled as empty or unavailable, not silently treated as healthy.

## Mission Control

Mission Control is an executive hub and summary surface. It can display observability summaries but is not backend truth.

Mission Control should link clearly to `/agent-ops`, the current MVP governance surface, without duplicating full governance panels.

## Agent Ops Governance Surface

- `/agent-ops` is the operational governance center for MVP.
- Fontana and Dani Weber are read-only and `diagnostic_only`.
- Executive Review is a read-only governance summary.
- Governance proposals are human-reviewed and approval-required.
- Guardrail notes must remain visible.
- Empty, loading, error, and partial-data states must be explicit and must not show fake data.

## Execution History

Execution history should be sourced from:

- `AgentRun` for agent and AI execution.
- `DetectionRun` for scanner/detection execution.
- `AgentActivity` for readable Agent Ops activity.

## Diagnostics

Diagnostics should state:

- Area affected.
- Severity.
- Evidence/reference.
- Owner hint.
- Recommended next action.
- Whether approval is required.

## Current Gaps

- Not all conceptual agents have persisted runs.
- `AgentSkill`, `AgentFinding`, and `AgentRecommendation` are not dedicated tables yet.
- Source Registry is not scanner source of truth until scanner wiring is fixed.
- Campus visuals are not operational truth.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.2.0 | 2026-06-08 | Codex | Added Sprint 1 Agent Ops governance observability requirements. |
| 0.1.0 | 2026-06-08 | Codex | Initial official version with per-agent documentation reference. |
