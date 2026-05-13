# Sprint AB — Missing Evidence Hunter & Case Documentation Guide

## Summary

Sprint AB adds deterministic Case Documentation Guides for SpecialSituations and ResearchCases. The guides organize existing stored metadata into an actionable manual research plan for Dani.

## Implemented

- Added read-only Case Documentation Guide builder in `backend/services/investment/case_documentation.py`.
- Added `GET /api/investment/situations/{id}/documentation-guide`.
- Added `GET /api/investment/research-cases/{id}/documentation-guide`.
- Added Case Documentation Guide sections near the top of:
  - `/investment/situations/[id]`
  - `/investment/research/[id]`
- Added Kanban documentation badges derived from already-loaded situation metadata.
- Added visual Agent Ops identity for `Missing Evidence Hunter`.
- Added targeted backend tests for the deterministic guide builder.

## What The Guide Shows

- Where the case came from.
- SEC metadata and stored filing link when available.
- Manual verification steps.
- Missing required resources.
- Missing checklist evidence.
- Stored search suggestions and copyable queries.
- Missing Evidence Hunter observer panel.
- Current manual research plan.
- Derived activity timeline.
- Documentation quality score.

## Guardrails

- No cron changes.
- No scheduler execution.
- No browsing.
- No document fetching.
- No PDF download.
- No SEC document body fetching.
- No live AI calls.
- No automatic evaluation.
- No automatic ResearchCase creation.
- No automatic promotion.
- No publishing or public draft creation.
- No investment instruction language.
- No Marketplace/Sales changes.
- No DB migration.

## Notes

Documentation quality is documentation completeness only. It is not the Intelligence Score and not an investment evaluation.

The Missing Evidence Hunter is observer/manual only in this sprint. Frequent missing-evidence checks are planned only for a future approved sprint.
