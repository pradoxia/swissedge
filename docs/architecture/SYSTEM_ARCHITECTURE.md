---
document_id: SYSTEM_ARCHITECTURE
title: System Architecture
version: 0.2.0
status: active
owner: Dani
last_updated: 2026-06-09
source_of_truth: true
review_cycle: manual
---

# SwissEdge System Architecture

Date: 2026-06-09

## Current Application Shape

SwissEdge is a multi-surface private application:

- Frontend: Next.js App Router in `frontend/app`.
- Backend: FastAPI in `backend`.
- Database: PostgreSQL via SQLAlchemy async models and Alembic migrations.
- Public site prototype: separate Next.js app in `public-site`.
- Documentation/context: `docs`, `swissedge-ai-context`, and processed course/index assets.

## Frontend Modules

- Mission Control: `frontend/app/page.tsx`
- Agent Ops: `frontend/app/agent-ops/**`
- Campus: `frontend/app/campus/**`
- Situations: `frontend/app/investment/situations/**`
- Research cases: `frontend/app/investment/research/**`
- Radar status: `frontend/app/investment/radar-status/page.tsx`
- Intelligence KPIs: `frontend/app/investment/intelligence/page.tsx`
- Sources: `frontend/app/investment/sources/page.tsx`
- Historical cases and public drafts: `frontend/app/investment/historical-cases/**`, `frontend/app/investment/public-drafts/**`

## Backend Routers

Registered in `backend/main.py`:

- `/api/health`: health and heartbeat.
- `/api/marketplace`: marketplace utility endpoints.
- `/api/marketplace/sales`: sales item persistence.
- `/api/investment`: situations, scanner, intelligence, sources, knowledge, course maps.
- `/api/investment`: research cases, historical cases, public drafts.
- `/api/observability`: runs, usage, agents, mission control, cron.
- `/api/agent-ops`: rooms, agents, activity, diagnostics, proposals, governance previews.

## Core System Boundaries

- Mission Control is an executive hub and link surface, not backend truth.
- Campus is a visual/UX layer, not operational truth.
- Agent Ops is the current governance surface.
- Proposed canonical investment governance route is `/investment/governance`, but it is not implemented yet.
- Source Registry exists, but scanner behavior is not source-registry truth until wiring is fixed.
- Governance agents are read-only/diagnostic until explicitly approved otherwise.

## Existing Endpoint Families

- Situations: `/api/investment/situations*`
- ResearchCases: `/api/investment/research-cases*`
- Detection runs: `/api/investment/detection-runs*`
- Intelligence: `/api/investment/intelligence/*`
- Executive metrics: `/api/investment/executive/*`
- Agent Ops: `/api/agent-ops/*`
- Observability: `/api/observability/*`

## Read-Only Governance Foundation

Fontana and Dani Weber currently draw from deterministic services and existing endpoint data:

- `GET /api/investment/intelligence/fontana-report`
- `GET /api/investment/executive/dani-weber-metrics`
- `GET /api/investment/executive/review`
- `GET /api/agent-ops/governance/fontana/latest`
- `GET /api/agent-ops/governance/dani-weber/latest`

These must remain diagnostic/read-only until a future approved sprint adds persistence or authority.

## Scheduled Detection Flow

Sprint 2 introduces controlled SEC EDGAR scheduled detection without changing the product authority model.

- Shared orchestrator: `backend/services/investment/scan_orchestrator.py`.
- Manual trigger: `POST /api/investment/scan` calls the orchestrator with `trigger_type=manual`.
- Scheduled trigger: `scripts/run_special_situation_scan.py` calls the orchestrator with `trigger_type=scheduled`.
- Source: `sec_edgar` only.
- Scheduler: VPS cron first; OpenClaw is not the core scheduler for this sprint.
- Observability: every reachable run records a `DetectionRun` with status, counters, warnings, errors, and source metadata.
- Deduplication: filing URL, accession number, company plus form type, and batch keys are checked before creating a `SpecialSituation`.

Allowed scheduled mutation is limited to metadata-only `SpecialSituation` triage creation after deduplication and with manual review required.

Forbidden scheduled behavior:

- No `ResearchCase` creation.
- No promotion or discard.
- No publishing.
- No live AI, Claude, OpenAI, Anthropic, or MCP calls.
- No investment recommendation or buy/sell language.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.2.0 | 2026-06-09 | Codex | Added Sprint 2 scheduled SEC EDGAR detection architecture and guardrails. |
| 0.1.0 | 2026-06-08 | Codex | Initial official version. |
