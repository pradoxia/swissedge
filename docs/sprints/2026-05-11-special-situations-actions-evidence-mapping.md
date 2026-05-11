# SwissEdge Sprint U Closeout - Kanban Actions + Evidence Mapping

## Summary

Sprint U makes SEC-detected `SpecialSituation` workspaces actionable without changing the detection or evaluation boundaries.

Users can now move a situation through a manual Kanban workflow, add and review resource candidates, link resources to required resources and checklist items, and mark linked material as `evidence_found`.

## Backend

No migration is required. Sprint U stores workflow/action state inside:

```text
SpecialSituation.evaluation.methodology_workspace
```

Added narrow mutation endpoints:

```text
PATCH /api/investment/situations/{id}/workflow-status
POST /api/investment/situations/{id}/resources
PATCH /api/investment/situations/{id}/resources/{resource_candidate_id}
```

Workflow statuses:

- `new_detection`
- `triage_needed`
- `needs_resources`
- `checklist_in_progress`
- `ready_for_research_case`
- `watchlist`
- `ignored`

Resource review statuses:

- `candidate_found`
- `evidence_found`
- `rejected`
- `human_review_required`

When a resource candidate is marked `evidence_found`, linked required resources can move to `evidence_found`, and linked checklist items can move to `evidence_found`. Sprint U never marks checklist items `verified` automatically.

## Progress Recalculation

`methodology_workspace.progress` now counts:

- `total_checks`
- `evidence_found`
- `verified_checks`
- `missing_required_resources`
- `candidate_resources`
- `human_review_required_count`

## Frontend

`/investment/situations` now groups cards by `methodology_workspace.workflow_status` first, with fallback to the existing situation status. Cards show detected-only/source labels, checklist/resource progress, and a simple manual "Move to" control.

`/investment/situations/[id]` now supports:

- manual workflow movement
- candidate resource review
- linking candidates to required resources and checklist items
- marking candidates as `evidence_found`
- rejecting candidates without deleting them
- manual resource add with related-resource/checklist selectors
- copy/open actions for search suggestions

The UI keeps Resource Scout manual and does not imply autonomous discovery, evaluation, or ResearchCase promotion.

## Guardrails Confirmed

- No cron modification.
- No `/api/investment/scan`.
- No live AI.
- No evaluator v2 global enablement.
- No ResearchCase auto-creation.
- No public drafts or publishing.
- No buy/sell/hold recommendation language.
- No broad web crawling.
- No X/Twitter scraping or API.
- No PDF download.
- No SEC document or article body fetching.
- No full copyrighted article text storage.
- No Marketplace/Sales changes.
- No Alembic migration.
- No auto-deploy.

## Deployment Notes

Backend and frontend deploy are required after review GO. No Alembic step is needed.

Manual verification after deploy:

1. Open `/investment/situations`.
2. Move one SEC-detected situation to `needs_resources`.
3. Open `/investment/situations/{id}`.
4. Add a manual HTTP/HTTPS resource candidate.
5. Link it to one required resource and one checklist item.
6. Mark it `evidence_found`.
7. Confirm the required resource and checklist item move to `evidence_found`, not `verified`.
8. Reject a separate candidate and confirm it remains visible.

Resource Scout remains manual-only.
