# Sprint AE — Batch Deployment Readiness

## Purpose

Sprint AE hardens the HOTFIX-AA / AB / AC / AD batch before one deep verification deployment.

No deployment is performed by this sprint.

## Batch Features Included

- Mission Control card and navigation improvements.
- Kanban — Special Situations as the central pipeline board.
- SpecialSituation quick actions and documentation/status indicators.
- Case Documentation Guide for SpecialSituations and ResearchCases.
- Missing Evidence Hunter as a manual observer / case research agent.
- Documentation Quality scoring.
- How to Find This Case and manual verification steps.
- Evidence Links / Research Traceability.
- Evaluation Preparation.
- Intelligence Score.
- Case Activity Log / Research Timeline.
- Agent Ops room and agent identity upgrades.
- Agent Ops scheduler posture display only.
- Derived operational indicators and XP-style metrics.

## High-Level Areas Touched

- Investment SpecialSituation detail page.
- Investment ResearchCase detail page.
- SpecialSituation Kanban board.
- Mission Control home.
- Agent Ops overview.
- Agent Ops room detail.
- Frontend API client types/functions.
- Read-only backend builder services.
- Read-only backend endpoints.
- Sprint and project state documentation.

## Backend Endpoints Added In Batch

- `GET /api/investment/situations/{id}/documentation-guide`
- `GET /api/investment/research-cases/{id}/documentation-guide`
- `GET /api/investment/situations/{id}/activity-timeline`
- `GET /api/investment/research-cases/{id}/activity-timeline`

Existing deploy-context endpoints to verify:

- `GET /api/investment/situations/{id}/evidence-links`
- `GET /api/investment/research-cases/{id}/evidence-links`
- `GET /api/investment/research-cases/{id}/evaluation-prep`
- `GET /api/investment/research-cases/{id}/intelligence-score`

## Backend Files To Include In Deploy Script

- `backend/services/investment/evidence_links.py`
- `backend/services/investment/intelligence_score.py`
- `backend/services/investment/case_documentation.py`
- `backend/services/investment/case_activity.py`
- `backend/api/investment/router.py`
- `backend/api/investment/research_cases.py`

## Migration Status

No migration expected.

The batch adds deterministic read-only services/endpoints and frontend UX changes. It does not add tables or columns.

## Frontend Routes To Verify

- `/`
- `/investment/situations`
- `/investment/situations/{id}`
- `/investment/research/{id}`
- `/agent-ops`
- `/agent-ops/rooms/{id}`

## Deep Smoke Test Checklist

1. Mission Control loads and shows `Kanban — Special Situations`.
2. `/investment/situations` loads as a horizontal pipeline board by default.
3. Kanban cards show Open case, SEC link when stored, ResearchCase link when promoted, docs status, missing count, and latest activity.
4. `Missing: 0` is not styled as a warning.
5. SpecialSituation detail loads when documentation-guide endpoint is unavailable.
6. SpecialSituation detail loads when activity-timeline endpoint is unavailable.
7. SpecialSituation Quick Links remain visible even without methodology workspace.
8. SpecialSituation Case Documentation Guide shows local error only when unavailable.
9. SpecialSituation Case Activity Log shows local error only when unavailable.
10. ResearchCase detail core page loads even if Evaluation Prep, Evidence Links, Intelligence Score, Documentation Guide, or Activity Timeline fail.
11. ResearchCase detail shows Kanban breadcrumb.
12. ResearchCase detail shows Documentation Guide, Intelligence Score, Evaluation Prep, Evidence Links, and Research Timeline near the top.
13. Agent Ops overview loads.
14. Missing Evidence Hunter is visible and marked manual / observer-only.
15. Agent Ops scheduler posture says disabled/manual/future approved sprint.
16. Agent Ops room detail opens.
17. Agent interaction maps state they are conceptual only.
18. Agent logs show real loaded rows only; empty states do not invent activity.
19. Related case links appear only where loaded rows provide related entity IDs.
20. No page shows a deploy, scan, evaluator activation, publishing, or scheduler execution control.

## Rollback Notes

Rollback is expected to be file-level frontend/backend revert only. No database rollback is expected because no migration is included.

If a read-only endpoint fails after deployment, core case pages should remain usable because secondary panels are non-blocking and show local panel errors.

## Guardrails Confirmed

- No live AI.
- No evaluator v2 global activation.
- No `/api/investment/scan` call.
- No cron changes.
- No scheduler execution.
- No automatic evaluation.
- No ResearchCase auto-creation.
- No automatic promotion.
- No publishing.
- No public draft creation.
- No investment recommendations.
- No buy/sell/hold language.
- No crawling.
- No PDF download.
- No SEC document body fetching.
- No external HTTP calls.
- No Marketplace/Sales changes.
- No secrets, hostnames, credentials, environment values, infrastructure details, production logs, or raw course materials.
- No auto-deploy.
