# SwissEdge Sprint UI Polish — Mission Control Frontend

**Date:** 2026-05-11
**Type:** Frontend-only polish (no backend changes)
**Scope:** 7 investment list pages + 1 shared component file

---

## Summary

Rewrote all dark/neon-themed investment list pages to match the existing design system defined in `frontend/app/globals.css`. Created a shared component library (`frontend/app/components/ui.tsx`) used by all rewritten pages and the existing `radar-status` page.

The old theme (`bg-gray-900`, `text-cyan-400`, `glow-*`, `scan-line`, `glass-panel`, gradient headers) is now removed from all list pages. The new theme uses the existing CSS variables: warm neutral palette (`--bg-page: #f5f4f1`), DM Sans + DM Mono typography, and the `.card`, `.data-table`, `.status-badge--*`, `.btn`, `.filter-btn`, `.page-container` system.

---

## Routes Touched

| Route | Status |
|---|---|
| `/investment/evaluations` | Rewritten |
| `/investment/research` | Rewritten |
| `/investment/watchlist` | Rewritten |
| `/investment/public-drafts` | Rewritten |
| `/investment/source-intelligence` | Rewritten |
| `/investment/historical-cases` | Rewritten |
| `/investment/research-inbox` | Rewritten |
| `/investment/sources` | Already on design system — no changes |
| `/investment/radar-status` | Already on design system — no changes |
| `/investment/evaluations/[id]` | Out of scope — detail pages deferred |
| `/investment/research/[id]` | Out of scope — detail pages deferred |
| `/investment/historical-cases/[id]` | Out of scope — detail pages deferred |
| `/investment/public-drafts/[id]` | Out of scope — detail pages deferred |

---

## Components Created

`frontend/app/components/ui.tsx`

| Export | Purpose |
|---|---|
| `PageHeader` | Title + subtitle + back nav + badge slot + actions slot |
| `SectionCard` | Card wrapper with optional section title header |
| `StatusBadge` | Maps status strings to design system badge classes via `BADGE_MAP` |
| `EmptyState` | Icon + title + description; used on all list pages |
| `LoadingState` | Spinner + label; replaces all inline loading patterns |
| `ErrorBanner` | Muted red error display; replaces all inline error patterns |
| `InfoBanner` | variant: `info` / `warning` / `guardrail`; used for disclaimers and system notices |
| `MetricRow` | Row of `metric-pill` items for summary strips |

`BADGE_MAP` covers: workflow statuses, research case statuses, readiness levels, playbook statuses, evaluator versions, agent ops states, historical case statuses, source intel statuses, public draft statuses. Falls back to `status-badge--readonly` for unknown values.

---

## Design Principles Applied

1. **Warm neutral palette** — `--bg-page: #f5f4f1`, `--text-primary: #1a1917`, `--border-default: #e0ddd6`. No dark backgrounds.
2. **Typography discipline** — DM Sans for readable prose, DM Mono for IDs/dates/metadata/labels. No uppercase screaming headers.
3. **No glow, no neon, no gradients** — removed `glow-cyan`, `glow-green`, `glow-red`, `bg-gradient-to-r`, `text-transparent`, `bg-clip-text`, `scan-line`.
4. **Neutral badge system** — all statuses use `status-badge--{active,preview,manual,readonly,partial}`. No green/red trading connotations.
5. **BUY/SELL colors eliminated** — `watchlist/page.tsx` previously used `bg-green-500/20 text-green-400 border-green-400 glow-green` for BUY/STRONG_BUY and `bg-red-500/20 text-red-400 border-red-400 glow-red` for AVOID/SELL. All replaced with `status-badge--readonly` (neutral).
6. **Consistent shell** — all pages use `PageHeader`, `LoadingState`, `ErrorBanner`, `EmptyState` from ui.tsx.
7. **Guardrail banners visible** — research, public-drafts, source-intelligence, historical-cases all show `InfoBanner variant="guardrail"` disclaimers on every load.
8. **Tables scroll horizontally** — all `data-table` instances wrapped in `overflowX: auto` divs.
9. **Null safety throughout** — all nullable fields (company name, ticker, dates, recommendations) guarded before render.

---

## Build Result

```
✓ Compiled successfully
✓ TypeScript: no errors
✓ 24 routes generated (static + dynamic)
✓ Duplicate key fixed in BADGE_MAP (removed 4 redundant quoted aliases: 'manual', 'preview', 'active', 'partial')
```

All 24 routes pass. Build is clean.

---

## Explicit Guardrail Confirmation

| Guardrail | Status |
|---|---|
| No backend files modified | ✓ Confirmed |
| No API endpoint paths changed | ✓ Confirmed |
| No API contracts changed (same fetch calls, same params) | ✓ Confirmed |
| No cron or scheduler logic | ✓ Confirmed |
| No `/api/investment/scan` trigger | ✓ Confirmed |
| No evaluator v2 enablement | ✓ Confirmed |
| No live AI call added | ✓ Confirmed |
| No auto-publish logic | ✓ Confirmed |
| No SEC detection logic changed | ✓ Confirmed |
| No ResearchCase auto-creation | ✓ Confirmed |
| No Agent Ops control plane changes | ✓ Confirmed |
| No secrets, IPs, Tailscale addresses added | ✓ Confirmed |
| No buy/sell recommendation colors | ✓ Confirmed |
| All output framed as educational research | ✓ Confirmed |

---

## Known Deferred Items

1. **Detail pages** — `evaluations/[id]`, `research/[id]`, `historical-cases/[id]`, `public-drafts/[id]` still use the old dark theme (`bg-gray-950`, `text-cyan-400`, etc.). Deferred to a separate sprint. Do not deploy the frontend as a "complete polish" — advise Dani these exist.
2. **`ErrorBanner` inside create panel grid** — `research/page.tsx` renders `ErrorBanner` (which has `marginBottom: 24px`) inside a flex grid. Causes slightly oversized vertical gap. Minor cosmetic issue, not a blocker.
3. **`research-inbox` badge colors** — retains Tailwind light color classes (`border-slate-200`, `border-sky-200`, `border-amber-200`, etc.) for the inbox-specific bucket/evidence/methodology badges. These are informational semantic colors, not buy/sell. Acceptable for this sprint.
