---
document_id: SCREENSHOT_MAP
title: Screenshot Map
version: 0.2.1
status: active
owner: Dani
last_updated: 2026-06-08
source_of_truth: true
review_cycle: manual
---

# SwissEdge Screenshot Map

Date: 2026-06-08

Base local URL: `http://localhost:3000`

## Rules

- Never invent IDs.
- Mark data as real, partial, mock, empty, visual, static, or unknown.
- Desktop screenshots first.
- Mobile screenshots are optional unless the task is responsive UX.
- For proposed routes, do not screenshot until implemented.

## Routes For Claude UX Work

| Page name | Route / URL | Status | Purpose | What Claude should inspect | Relevant components | Screenshot priority |
| --- | --- | --- | --- | --- | --- | --- |
| Mission Control | `http://localhost:3000/` | implemented | Executive hub and navigation | Hierarchy, links to Agent Ops/governance, status labels, checklist clarity | `frontend/app/page.tsx` | High |
| Investment root | `http://localhost:3000/investment` | proposed | Future investment section hub | Not available yet; proposed route decision only | none | Low |
| Situations list | `http://localhost:3000/investment/situations` | implemented | Main `SpecialSituation` triage list | Kanban/list clarity, filters, card metadata, empty states | `frontend/app/investment/situations/page.tsx` | High |
| Situation workbench | `http://localhost:3000/investment/situations/<REAL_SITUATION_ID>` | implemented, needs real ID | Main triage/detail route | Header, workbench, Study Guide, evidence, source finder, SEC acquisition, activity timeline | `frontend/app/investment/situations/[id]/page.tsx`, shared panels | High |
| Investment governance | `http://localhost:3000/investment/governance` | proposed | Canonical future investment governance route | Proposed route; do not capture until implemented | none | High after implementation |
| Agent Ops | `http://localhost:3000/agent-ops` | implemented | Current governance surface and Agent Ops dashboard | Executive Office, Fontana, Dani Weber, rooms, activity, diagnostics, proposals | `frontend/app/agent-ops/page.tsx` | High |
| Agent Ops rooms | `http://localhost:3000/agent-ops/rooms` | proposed | Future room index route | Proposed route; current room links are from `/agent-ops` | none | Medium after implementation |
| Agent Ops room detail | `http://localhost:3000/agent-ops/rooms/<ROOM_SLUG>` | implemented, uses room slug | Room-level details | Room header, agent cards, logs, diagnostics, proposals | `frontend/app/agent-ops/rooms/[id]/page.tsx` | Medium |
| Campus | `http://localhost:3000/campus` | implemented | Visual/ops overview | Campus map, room navigation, live/static data distinction | `frontend/app/campus/**` | Medium |
| Observability | `http://localhost:3000/observability` | proposed | Future observability hub | Proposed route; current observability pages are `/agents`, `/investment/radar-status`, `/agent-ops/calendar` | none | Medium after implementation |
| Mission Control alias | `http://localhost:3000/mission-control` | proposed | Future alias if desired | Proposed route; current Mission Control is `/` | none | Low |
| Research cases | `http://localhost:3000/investment/research` | implemented | Durable research list | List clarity, linked situations, empty states | `frontend/app/investment/research/page.tsx` | Medium |
| Research case detail | `http://localhost:3000/investment/research/<REAL_RESEARCH_CASE_ID>` | implemented, needs real ID | Durable research workbench | Evidence, tasks, sources, readiness, publication prep | `frontend/app/investment/research/[id]/page.tsx` | Medium |
| Radar status | `http://localhost:3000/investment/radar-status` | implemented | Detection/scanner status | Scanner status, source-registry warning, cron/upcoming, latest run | `frontend/app/investment/radar-status/page.tsx` | High |
| Intelligence KPIs | `http://localhost:3000/investment/intelligence` | implemented | Quality/readiness KPIs | KPI hierarchy, missing evidence, manual workload, Fontana links | `frontend/app/investment/intelligence/page.tsx` | Medium |

## Obtaining IDs

- `SpecialSituation`: open `/investment/situations`, click a real card, or call `GET http://localhost:8000/api/investment/situations`.
- `ResearchCase`: open `/investment/research`, click a real row, or call `GET http://localhost:8000/api/investment/research-cases`.
- Room slug: use `detection_room`, `evidence_lab`, `playbook_workshop`, `research_desk`, `quality_court`, or `executive_office`.

## Sprint 1 Governance Screenshots

For Claude UX review, capture:

- `http://localhost:3000/agent-ops`
- `http://localhost:3000/`
- Fontana panel close-up.
- Dani Weber panel close-up.
- Executive Review section.
- Proposals section if present.

Mark endpoint failures, empty states, and partial data explicitly in the handoff.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.2.1 | 2026-06-08 | Codex | Sprint 1 UX polish: governance copy, labels and empty-state clarity for /agent-ops. |
| 0.2.0 | 2026-06-08 | Codex | Added Sprint 1 governance screenshot requirements. |
| 0.1.0 | 2026-06-08 | Codex | Initial official version. |
