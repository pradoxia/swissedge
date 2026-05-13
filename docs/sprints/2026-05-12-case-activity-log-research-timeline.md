# Sprint AC — Case Activity Log & Research Timeline

## Summary

Sprint AC adds a deterministic, read-only Case Activity Log / Research Timeline layer for SpecialSituations and ResearchCases.

The timeline is derived from existing stored metadata only. It is useful for explaining what has happened, where the information came from, which observer agent/process is associated with each item, and which documentation gaps still need manual attention.

## Implemented

- Added `backend/services/investment/case_activity.py`.
- Added normalized timeline package models and deterministic builders:
  - `build_situation_activity_timeline`
  - `build_research_case_activity_timeline`
- Added read-only endpoints:
  - `GET /api/investment/situations/{id}/activity-timeline`
  - `GET /api/investment/research-cases/{id}/activity-timeline`
- Added shared frontend timeline component:
  - `frontend/app/components/CaseActivityTimeline.tsx`
- Added Case Activity Log to SpecialSituation detail.
- Added Research Timeline / Case Activity Log to ResearchCase detail.
- Added compact latest-activity / attention line to Kanban cards without N+1 calls.
- Improved Agent Ops visual relevance:
  - agent cards show case-row counts
  - Missing Evidence Hunter / Quality Sentinel / Fontana panels summarize related loaded rows
  - room detail pages show case timeline relevance by selected agent
- Added backend tests for the activity builder.

## Timeline Sources

Timeline events are derived from:

- SpecialSituation detection, created, and updated timestamps.
- Stored SEC detection metadata.
- Methodology workspace presence.
- Required resources and checklist status.
- Resource candidates and stored search suggestions.
- Manual ResearchCase link/promotion metadata.
- ResearchCase created/updated timestamps.
- ResearchCase tasks, sources, and documents.
- Evidence Links availability.
- Evaluation Preparation availability.
- Intelligence Score availability.
- Case Documentation Guide summary.
- Existing Agent Ops rows when safely related to the case.

## Important Caveat

These timelines are not persisted audit logs yet.

They are current-state derived views. If old records have no timestamp, the UI groups them under `Current state - timestamp unavailable`.

Future approved sprint work may add persisted event logs, but Sprint AC does not add that storage layer.

## Guardrails Confirmed

- No cron changes.
- No scheduler execution.
- No live AI.
- No evaluator call.
- No scanner call.
- No `/api/investment/scan` call.
- No external HTTP calls.
- No crawling.
- No PDF download.
- No SEC document body fetching.
- No automatic evaluation.
- No automatic ResearchCase creation.
- No automatic promotion.
- No publishing.
- No public draft creation.
- No investment recommendation workflow.
- No buy/sell/hold output.
- No Marketplace/Sales changes.
- No DB migration.
- No auto-deploy.

## Validation

- Targeted backend tests: `python -m pytest backend\tests\test_case_activity.py backend\tests\test_case_documentation.py`
- Frontend build: `npm run build`
- Diff hygiene: `git diff --check`
- Secret hygiene: current diff scanned before review handoff
- `.claude/` remains untracked/uncommitted

## Review Posture

Sprint AC should be reviewed by ClaudeCode before Sprint AD starts.

Do not deploy after this sprint.
