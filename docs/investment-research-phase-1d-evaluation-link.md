# Phase 1D — Evaluation Detail → ResearchCase Link

**Status:** Design document — documentation only. No implementation, migration, endpoint, or cron changes.
**Sprint:** Phase 1D design (2026-05-02)
**Prerequisite reading:** `docs/PROJECT_STATE.md`, `docs/investment-research-platform-redesign.md`, `docs/investment-research-data-model.md`

---

## 1. Goal

Connect the existing Evaluation Detail page (`/investment/evaluations/[id]`) to the ResearchCase system by adding a Research Case panel. The panel allows Dani to:

- See whether a ResearchCase already exists for the situation.
- Create a new ResearchCase from the situation with one click.
- Navigate directly to the ResearchCase detail page.

This closes the loop between the detection/evaluation pipeline and the research desk. No new backend code is required — the Phase 1B API already supports all needed operations.

---

## 2. Current State

| Component | Status |
|---|---|
| `special_situations` table + evaluations queue/detail | ✅ Live on VPS |
| ResearchCase DB tables (Phase 1A) | ✅ Live on VPS — migration `c3d4e5f6a7b8` applied |
| ResearchCase service + API endpoints (Phase 1B) | ✅ Built — **not yet deployed** |
| Research list + detail pages (Phase 1C) | ✅ Built — **not yet deployed** |
| ResearchCase panel on Evaluation Detail | ❌ Not yet built — this is Phase 1D |

**Deploy note:** Phase 1B and 1C must be deployed before Phase 1D can be tested end-to-end. The Phase 1D frontend change depends on the Phase 1B endpoints being live.

---

## 3. User Journey

```
/investment/evaluations
  → [click row]
/investment/evaluations/[id]          ← Evaluation Detail (exists)
  → [Research Case panel — new in Phase 1D]
      → if no case: [Create Research Case] button
      → if case exists: [Open Research Case] button → link
/investment/research/[id]             ← ResearchCase Detail (Phase 1C)
```

Full path from list to research desk:

1. Dani opens Evaluation Detail for a situation.
2. Research Case panel loads below the Decision Card.
3. If no case exists: single "Create Research Case" button.
4. On click: POST `/api/investment/research-cases/from-situation/{situation_id}`.
5. On success: redirect to `/investment/research/{new_id}`.
6. On subsequent visits: panel shows "Open Research Case" button linking to `/investment/research/{case_id}`.

---

## 4. UI States

| State | Trigger | UI Behavior |
|---|---|---|
| **loading** | Panel mounts; GET in flight | Skeleton or "Loading research case…" text; button disabled |
| **no_case** | GET returns empty array or 404 | "No research case yet" text; "Create Research Case" button enabled |
| **case_exists** | GET returns a case row | Case status badge (monitor / not_actionable / needs_more_work / candidate) + readiness badge; "Open Research Case" button → `href=/investment/research/{id}` |
| **create_in_progress** | POST in flight | Button shows spinner; disabled; no other UI change |
| **create_success** | POST returns 201 | Router pushes to `/investment/research/{id}` |
| **duplicate_409** | POST returns 409 | Do not show error alert; silently fetch existing case via `GET /api/investment/research-cases?situation_id={id}`; if found, redirect to it; if fetch fails, show inline message: "A research case already exists — [view it]" |
| **backend_error** | POST or GET returns 5xx | Inline message below panel: "Could not load research case. Try again." Retry button shown. No `alert()`. |
| **research_api_unavailable** | Network error or 503 | Inline message: "Research case service unavailable." Panel does not block rest of page. |

---

## 5. API Contract

All endpoints are already implemented in Phase 1B. Phase 1D consumes them from the frontend only.

### 5.1 Check for existing case

```
GET /api/investment/research-cases?situation_id={situation_id}
```

- Returns `{ items: ResearchCase[], total: number }`.
- If `total === 0` → no case exists → show create button.
- If `total >= 1` → case exists → show open button using `items[0].id`.
- Called on panel mount.

### 5.2 Create case from situation

```
POST /api/investment/research-cases/from-situation/{situation_id}
```

- Returns `ResearchCase` (201) on success.
- Returns 409 if a case already exists for this situation.
- Returns 404 if the situation does not exist.
- No request body required.

### 5.3 Fetch full case detail (optional pre-load)

```
GET /api/investment/research-cases/{id}
```

- Returns full `ResearchCase` with tasks, documents, sources.
- Used if the panel needs to show more than status/readiness badges.
- For Phase 1D the panel is intentionally minimal; full detail is on the research page.

---

## 6. Duplicate Handling

A 409 from `POST /api/investment/research-cases/from-situation/{situation_id}` is **not a fatal error**. The 409 means the case already exists (idempotency guard in Phase 1B service layer).

Recovery sequence:

1. POST returns 409.
2. Frontend calls `GET /api/investment/research-cases?situation_id={id}`.
3. If GET succeeds and returns a case → redirect to `/investment/research/{id}` silently.
4. If GET also fails → show inline message: "A research case already exists — [view it]" with a link to `/investment/research` (list page).

**No `alert()` in any branch.** All feedback is inline within the panel.

---

## 7. Routing Behavior

| Event | Behavior |
|---|---|
| Create success (201) | `router.push('/investment/research/{new_id}')` |
| Existing case button click | `<Link href="/investment/research/{case_id}">` — standard Next.js link; no JS navigation |
| 409 recovery (case found) | `router.push('/investment/research/{recovered_id}')` |
| 409 recovery (case not found) | Inline message with `<Link href="/investment/research">` |
| Backend error | Stay on current page; show retry option |

---

## 8. Guardrails

The following must not be touched during Phase 1D implementation:

| Area | Status |
|---|---|
| `/api/investment/scan` | ❌ Must not be called |
| Scanner / cron | ❌ No changes |
| Evaluator v1 / v2 | ❌ No changes |
| Live AI calls | ❌ None — panel is pure CRUD |
| External fetches / source crawling | ❌ None |
| Public publishing | ❌ Not applicable to this phase |
| Marketplace / Sales | ❌ No changes |
| DB migrations | ❌ None required; all tables live from Phase 1A |
| Deploy | ❌ Claude does not deploy; Dani runs scripts manually |
| Backend code (Phase 1D) | ❌ No new backend files or endpoint changes |

---

## 9. Acceptance Criteria

**AC-1 — Panel renders on Evaluation Detail**
- Research Case panel is visible on `/investment/evaluations/[id]` for any situation.

**AC-2 — No-case state**
- When no ResearchCase exists for the situation, panel shows "No research case yet" and a "Create Research Case" button.

**AC-3 — Create flow**
- Clicking "Create Research Case" POSTs to `/api/investment/research-cases/from-situation/{situation_id}`.
- On 201: navigates to `/investment/research/{new_id}`.
- Button is disabled and shows loading state while POST is in flight.

**AC-4 — Existing case state**
- When a ResearchCase exists, panel shows status and readiness badges and an "Open Research Case" link.
- Link navigates to `/investment/research/{case_id}`.

**AC-5 — 409 duplicate handling**
- POST returning 409 does not show an error alert.
- Frontend attempts recovery GET; if successful, navigates to existing case.
- If recovery GET also fails, shows inline message with link to research list.

**AC-6 — Backend error handling**
- 5xx responses and network errors show inline messages inside the panel.
- No `alert()` in any error branch.
- Rest of Evaluation Detail page continues to render normally.

**AC-7 — No prohibited side effects**
- No call to `/api/investment/scan`.
- No changes to evaluator, scanner, cron, Marketplace, or Sales code.
- No new DB migrations.

**AC-8 — TypeScript build passes**
- `npm run build` passes with 0 errors after Phase 1D changes.

---

## 10. Test Plan

### Manual tests (developer, pre-deploy)

1. Open an evaluation detail for a situation with no ResearchCase → verify "no case" state.
2. Click "Create Research Case" → verify 201 response → verify redirect to `/investment/research/{id}`.
3. Return to the same evaluation detail → verify "case exists" state shows correct badges and "Open" link.
4. Click "Open Research Case" → verify navigation to `/investment/research/{id}`.
5. Force a 409 (trigger create twice rapidly, or create manually before clicking) → verify silent recovery and redirect.
6. Kill backend (or use network throttle) → verify panel shows inline error, rest of page unaffected.
7. Verify no `alert()` appears in any scenario.

### Automated tests (Phase 1D test file)

- Mock `GET /api/investment/research-cases?situation_id=X` returning empty array → assert create button rendered.
- Mock `GET` returning one case → assert open link rendered with correct href.
- Mock `POST` returning 201 → assert router.push called with correct path.
- Mock `POST` returning 409 → mock recovery `GET` returning case → assert router.push called.
- Mock `POST` returning 409 → mock recovery `GET` returning empty → assert inline message rendered, no alert.
- Mock `GET` returning 5xx → assert inline error message rendered, no alert.

---

## 11. Open Questions

| # | Question | Impact |
|---|---|---|
| OQ-1 | Should the panel show any ResearchCase fields beyond status and readiness badges? (e.g. brief title, last updated date) | Low — easy to add fields if needed; Phase 1D keeps it minimal |
| OQ-2 | Should the Evaluation Detail page also receive a backlink from the ResearchCase detail page? | Low — currently research detail has no back-to-evaluation link; Phase 1D does not address this |
| OQ-3 | What happens if a situation has been archived? Should "Create Research Case" still be allowed? | Low — Phase 1B API does not block by status; UI can show panel regardless; revisit if needed |
| OQ-4 | Phase 1B is not yet deployed. Should Phase 1D implementation be blocked until 1B is live, or developed against mocked API? | Planning — recommended: implement against mock; deploy 1B and 1C together with 1D |

---

## 12. Future Follow-Up Tasks

| Task | Phase |
|---|---|
| Add back-link from ResearchCase detail → Evaluation Detail | Phase 1E or standalone |
| Show ResearchCase summary card on Evaluation queue row (inline badge) | Phase 1E |
| Add Research Case count / readiness to Mission Control home | Phase 2 |
| Connect `situation_research_agent` to create brief content on case creation | Phase 2 |
| Historical case intake from ResearchCase | Phase 3 |
| Source intelligence feedback loop | Phase 3 |
| Publishing pipeline | Phase 4 |
