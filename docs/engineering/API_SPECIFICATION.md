---
document_id: API_SPECIFICATION
title: API Specification
version: 0.1.0
status: active
owner: Dani
last_updated: 2026-06-08
source_of_truth: true
review_cycle: manual
---

# SwissEdge API Specification

Date: 2026-06-08

This is the official high-level API map. Detailed route inventory is maintained in `docs/context/ROUTE_AND_ENDPOINT_MAP.md`.

## Health

- `GET /api/health/ping`
- `GET /api/health/full`
- `POST /api/health/heartbeat`

## Investment Situations

- `GET /api/investment/situations`
- `GET /api/investment/situations/{id}`
- `PATCH /api/investment/situations/{id}`
- `GET /api/investment/situations/{id}/evidence-links`
- `GET /api/investment/situations/{id}/documentation-guide`
- `GET /api/investment/situations/{id}/document-package`
- `GET /api/investment/situations/{id}/documentation-agent-report`
- `GET /api/investment/situations/{id}/official-source-finder`
- `GET /api/investment/situations/{id}/historical-analogues`
- `GET /api/investment/situations/{id}/completion-workbench`
- `GET /api/investment/situations/{id}/activity-timeline`
- `POST /api/investment/situations/{id}/promote-to-research-case`

## Detection And Scanner

- `GET /api/investment/detection-runs/latest`
- `GET /api/investment/detection-runs/status`
- `GET /api/investment/detection-runs/readiness`
- `GET /api/investment/detection-runs`
- `GET /api/investment/detection-runs/{run_id}`
- `POST /api/investment/scan`

Guardrail: do not trigger `POST /api/investment/scan` unless explicitly approved.

## Governance And Intelligence

- `GET /api/investment/intelligence/kpis`
- `GET /api/investment/intelligence/fontana-report`
- `GET /api/investment/executive/dani-weber-metrics`
- `GET /api/investment/executive/review`

## Agent Ops

- `GET /api/agent-ops/rooms`
- `GET /api/agent-ops/rooms/{room_key}`
- `GET /api/agent-ops/agents`
- `GET /api/agent-ops/agents/{agent_key}`
- `GET /api/agent-ops/activity`
- `GET /api/agent-ops/diagnostics`
- `GET /api/agent-ops/proposals`
- `PATCH /api/agent-ops/proposals/{proposal_id}`
- `GET /api/agent-ops/governance/fontana/latest`
- `POST /api/agent-ops/governance/fontana/run-preview`
- `GET /api/agent-ops/governance/dani-weber/latest`
- `POST /api/agent-ops/governance/dani-weber/run-preview`
- `GET /api/agent-ops/execution-calendar`

## Observability

- `GET /api/observability/runs`
- `GET /api/observability/runs/{run_id}`
- `GET /api/observability/summary`
- `GET /api/observability/costs`
- `GET /api/observability/agents`
- `GET /api/observability/agents/{agent_name}`
- `GET /api/observability/mission-control`
- `GET /api/observability/cron/upcoming`

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.1.0 | 2026-06-08 | Codex | Initial official version. |
