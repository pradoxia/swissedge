# SwissEdge Sprint — Special Situations Kanban Board UI

## Summary

Implemented a Kanban pipeline view for all `SpecialSituation` records at `/investment/situations`.
This is a read-only UI sprint — no backend changes, no migrations, no cron changes, no new API endpoints.

## New Route

`/investment/situations` — Kanban board (7 columns, horizontal scroll)

## Files Changed

- `frontend/app/investment/situations/page.tsx` — **created** (Kanban board)
- `frontend/app/investment/situations/[id]/page.tsx` — **updated** back link from `/investment/evaluations` → `/investment/situations`

## Kanban Columns

| Column key              | Label                | Status values mapped               |
|-------------------------|----------------------|------------------------------------|
| `detected`              | New Detections       | `detected`                         |
| `triage_needed`         | Needs Triage         | `triage_needed` + unknown statuses |
| `needs_resources`       | Needs Resources      | `needs_resources`                  |
| `checklist_in_progress` | Checklist In Progress| `checklist_in_progress`            |
| `ready_for_research_case` | Ready for Research | `ready_for_research_case`          |
| `watchlist`             | Watchlist            | `watchlist`                        |
| `ignored`               | Ignored              | `ignored`, `archived`              |

Sprint S `triage_needed`, `needs_resources`, `checklist_in_progress`, `ready_for_research_case` statuses are wired up and ready — columns appear empty until those statuses exist in the database.

## Column Resolution Logic

1. If `evaluation.methodology_workspace.workflow_status` is present (Sprint S), use it.
2. Otherwise fall back to `SpecialSituation.status`.
3. If status matches no known column, fall through to `triage_needed` (safe catch-all).

## Card Content

Each Kanban card shows:
- Company name (truncated at 36 chars)
- Ticker (if present)
- Filing type badge + SEC situation type badge (if present)
- `workspace` badge if methodology workspace is attached
- Filing date (from `evaluation.sec_detection.filing_date`, fallback to `detected_at`)
- SEC filing URL link (opens in new tab, does not navigate away from board)

Clicking the card navigates to `/investment/situations/[id]` (methodology workspace detail page).

## Filters

All filters are client-side, applied after `fetchSituations()` returns all records.

- Text search: matches `company_name` or `ticker`
- Situation type dropdown: populated from live data
- Filing type dropdown: populated from live data
- "Clear filters" button appears when any filter is active

## Metrics

MetricRow above the board shows (from full unfiltered list):
- Total
- New Detections (status = `detected`)
- Watchlist (status = `watchlist`)
- Ready for Research (status = `ready_for_research_case`)
- Missing Resources (status = `needs_resources`)
- SEC-only (where `evaluation.detected_only = true`)

## Build Verification

```
✓ Compiled successfully in 1719ms
✓ TypeScript: clean — 0 errors
✓ Routes: 26 total, /investment/situations (static) and /investment/situations/[id] (dynamic) confirmed
```

## Guardrails Confirmed

- No backend changes.
- No Alembic migration.
- No cron change.
- No live AI.
- No `/api/investment/scan`.
- No evaluator v2 global enablement.
- No ResearchCase auto-creation.
- No public publishing.
- No buy/sell language.
- Read-only board — status movement not implemented (no `updateSituationStatus` calls).
- InfoBanner: "Detected does not mean evaluated."
- Footer: "detected does not mean evaluated — no publishing without manual approval"

## Design

- Follows design system: `page-container--wide`, `card`, `status-badge--*`, `btn--*`, `MetricRow`, `PageHeader`, `InfoBanner`, `StatusBadge`, `ErrorBanner`, `LoadingState`.
- No dark theme, no neon colors, no buy/sell connotations.
- Horizontal scroll for columns — each column 272px wide.
- Empty columns show a dashed placeholder ("Empty"), not a full EmptyState component.
