---
document_id: API_SPECIFICATION
title: API Specification
version: 0.1.3
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

- `GET /api/investment/research-inbox`
- `POST /api/investment/research-inbox/decision`
- `POST /api/investment/research-inbox/price-context`
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

`GET /api/investment/research-inbox` may include optional `price_context` per item with neutral fields such as `ticker`, `offer_price`, `latest_close_price`, `latest_close_date`, `estimated_spread_pct`, `spread_status`, and `updated_at`. This is workflow prioritization context only and must not be used as advice or an automated decision.

`GET /api/investment/research-inbox` may include optional `latest_decision` per item with `id`, `target_type`, `target_id`, `outcome`, `reason`, `author`, `source_surface`, and `created_at`.

`POST /api/investment/research-inbox/decision` records one manual decision. Request fields: `target_type` (`special_situation` or `research_case`), `target_id`, `outcome` (`CANDIDATE`, `WATCHLIST`, `REJECT`, or `NEED_MORE_EVIDENCE`), `reason`, and `author`. Reason and author are required. The endpoint creates only a `DecisionRecord`; it must not promote, reject, discard, archive, publish, analyze, verify evidence, acquire documents, or hide queue items.

`POST /api/investment/research-inbox/price-context` manually creates or updates cached price context. Request fields: `target_type`, `target_id`, optional `ticker`, `offer_price`, `offer_price_source`, `latest_close_price`, `latest_close_date`, optional `currency`, optional manual `spread_status`, and `status_reason`. If valid offer and latest close prices are present, `estimated_spread_pct` is recalculated with Decimal math. The endpoint does not call market-data providers, live AI, evaluator v2, scanner, cron, or external data sources, and it must not mutate case status or create decisions.

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
| 0.1.3 | 2026-06-10 | Codex | Added M4B manual Research Inbox price-context endpoint. |
| 0.1.2 | 2026-06-10 | Codex | Added M3B Research Inbox decision recording endpoint and latest_decision response note. |
| 0.1.1 | 2026-06-10 | Codex | Added Research Inbox and optional price context response note for M4A. |
| 0.1.0 | 2026-06-08 | Codex | Initial official version. |
