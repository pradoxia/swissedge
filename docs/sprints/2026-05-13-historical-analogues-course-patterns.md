# Sprint AL - Historical Analogues & Course Pattern Mapping

Date: 2026-05-13

## Summary

Sprint AL adds a deterministic, read-only Historical Analogues & Course Patterns layer for SpecialSituations and ResearchCases.

Implemented locally:
- Backend service `backend/services/investment/historical_analogues.py`.
- Read-only endpoints:
  - `GET /api/investment/situations/{id}/historical-analogues`
  - `GET /api/investment/research-cases/{id}/historical-analogues`
- Case detail panels showing:
  - matched methodology patterns
  - similar HistoricalCase rows
  - why the case is similar
  - key differences
  - manual comparison checklist
  - processed course/playbook pattern summaries
  - warnings and guardrails
- Kanban cards show compact deterministic pattern labels from already-loaded metadata.
- Intelligence KPIs links historical comparison to low-quality/manual-work cases.
- Agent Ops documents Pattern Analyst as manual/observer-only.

## Method

The matcher uses deterministic metadata only:
- filing type
- situation type
- selected playbook / playbook used
- methodology status
- required resource labels/source types
- checklist labels/sections
- stored HistoricalCase reconstruction metadata when present

No semantic AI matching, no external lookup, and no raw course material access was added.

## Guardrails

- No raw course materials.
- No raw transcripts.
- No copyrighted course excerpts.
- No live AI.
- No evaluator call or activation.
- No scanner or `/api/investment/scan` call.
- No cron or scheduler change.
- No automatic evaluation, ResearchCase creation, promotion, source verification, publishing, or public draft creation.
- No crawling, PDF download, SEC document body fetching, or external HTTP calls.
- No valuation or investment action language.
- Manual review remains required.

## Validation Notes

Targeted backend tests cover:
- SC TO-I self-tender mapping.
- SC TO-T tender/merger-arb mapping.
- Form 10 spin-off mapping.
- 8-K liquidation mapping.
- ResearchCase promoted snapshot mapping.
- HistoricalCase similarity scoring.
- No investment action language in package output.
- No network clients imported by the service.

Frontend build should confirm the new shared panel and case-detail loaders compile.
