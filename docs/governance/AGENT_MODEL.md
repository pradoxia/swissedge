---
document_id: AGENT_MODEL
title: Agent Model
version: 0.1.1
status: active
owner: Dani
last_updated: 2026-06-08
source_of_truth: true
review_cycle: manual
---

# SwissEdge Agent Model

Date: 2026-06-08

This document is the high-level agent model index. Detailed per-agent definitions live in `docs/agents/`.

Current SwissEdge agents are documented personas and deterministic/read-only governance workers. They are not yet live Claude/LLM agents. See `docs/architecture/AGENT_IMPLEMENTATION_MODEL.md` for the implementation model and future LLM-assisted path.

## Room Model

| Room | Purpose |
| --- | --- |
| Detection Room | Detect raw special situation signals and create `SpecialSituation` candidates. |
| Evidence Lab | Collect official evidence, SEC filings, company IR links, transaction documents, exhibits, and provenance. |
| Playbook Workshop | Map cases against the Arte de Invertir course, chapter references, checklists, concepts, and gaps. |
| Research Desk | Build structured research documentation from evidence and playbook requirements. |
| Quality Court | Review evidence quality, consistency, missing fields, hallucination risk, and guardrail compliance. |
| Executive Office | System governance, process governance, diagnostics, bottlenecks, and improvement proposals. |

## Official Agents

| Agent | Slug | Room | Detailed doc |
| --- | --- | --- | --- |
| Fontana | `fontana` | Executive Office | `docs/agents/FONTANA.md` |
| Dani Weber | `weber` | Executive Office | `docs/agents/DANI_WEBER.md` |
| Edgar Scout | `edgar-scout` | Detection Room | `docs/agents/EDGAR_SCOUT.md` |
| Form Parser | `form-parser` | Evidence Lab | `docs/agents/FORM_PARSER.md` |
| Router Analyst | `router-analyst` | Detection Room | `docs/agents/ROUTER_ANALYST.md` |
| Case Builder | `case-builder` | Research Desk | `docs/agents/CASE_BUILDER.md` |
| Quality Sentinel | `quality-sentinel` | Quality Court | `docs/agents/QUALITY_SENTINEL.md` |
| Playbook Scribe | `playbook-scribe` | Playbook Workshop | `docs/agents/PLAYBOOK_SCRIBE.md` |

## Current Runtime Status

Agent documents define personas, missions, skills, permissions, and guardrails. Current runtime agent surfaces derive structured reports from backend services and database state. No current endpoint uses Claude, live LLM reasoning, or agent documents as active system prompts.

## Universal Agent Requirements

Every agent must have:

- Name and slug.
- Room/department.
- Role and purpose.
- Responsibilities and skills.
- Inputs and outputs.
- Permissions and forbidden actions.
- Run mode.
- Scheduled execution cadence, even if not active yet.
- Next-run strategy.
- Related endpoints.
- UI visibility requirements.
- Detailed execution log.
- Activity feed summary.

No agent should silently run without logging.

## Logging Requirements

Every run must eventually record:

- Agent slug/name.
- Room.
- Start and end time.
- Status.
- Run mode.
- Trigger type.
- Endpoint called.
- Scope checked.
- Entities read/touched.
- Findings.
- Recommendations.
- Errors.
- Whether human approval is required.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.1.1 | 2026-06-08 | Codex | Clarified current agent runtime status and linked the Agent Implementation Model. |
| 0.1.0 | 2026-06-08 | Codex | Initial official version. |
