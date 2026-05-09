# Phase 3E — Source Intelligence Approval

> Status: DESIGN ONLY — not yet implemented  
> Prereq: Phase 3D deployed and smoke-tested by Dani

---

## Goal

Allow an analyst to review AI-generated source intelligence proposals (from the Phase 3D preview endpoint) and explicitly approve or reject each suggestion. Approved suggestions can optionally be applied to the research case's source registry — but never automatically. No write to `investment_sources` (the global scanner table) at any point.

---

## Hard Boundary

- **No auto-apply.** Every write to the DB requires a deliberate analyst action.
- **`investment_sources` table is never mutated** by any Phase 3E endpoint.
- **No URL fetching or crawling** — all data flows from stored metadata only.
- **`saved_to_db: false`** on preview responses remains unchanged.
- **No buy/sell language** in any stored or returned field.
- No Marketplace/Sales changes.
- No cron changes.
- No scanner trigger.

---

## Data Strategy

### New table: `SourceIntelligenceSuggestion`

The `SourceIntelligenceSuggestion` model already exists in `backend/models/source_intelligence.py`. Phase 3E activates persistence for it.

**Key columns (from existing model):**

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `research_case_id` | UUID FK → `research_cases.id` | |
| `run_id` | UUID FK → `agent_runs.id` nullable | links to observability run |
| `action` | str | `"add"` / `"update_priority"` / `"deactivate"` |
| `source_name` | str | |
| `source_type` | str | nullable |
| `reason` | str | |
| `evidence_from_case` | str | nullable |
| `confidence` | str | `"high"` / `"medium"` / `"low"` |
| `manual_review_required` | bool | always `True` at creation |
| `status` | str | lifecycle field — see below |
| `reviewed_at` | datetime nullable | set on approve/reject |
| `applied_at` | datetime nullable | set on apply |
| `created_at` | datetime | |

**Alembic migration required:** a new migration adding the `source_intelligence_suggestions` table (if not already present from Phase 1A migration). Verify with `alembic current` before implementing.

---

## Suggestion Lifecycle

```
proposed → reviewed → approved  → (optionally) applied
                   ↘ rejected
```

| Status | Meaning |
|---|---|
| `proposed` | AI-generated, not yet reviewed |
| `approved` | Analyst confirmed it is valid — not yet written to case sources |
| `rejected` | Analyst dismissed it |
| `applied` | Analyst applied it — a new `ResearchSource` row was created in the case |

Transitions:
- `proposed → approved` or `proposed → rejected` via PATCH
- `approved → applied` via dedicated POST (apply action)
- `rejected` is terminal — cannot be re-approved (analyst must re-run preview)
- `applied` is terminal

---

## Manual Approval Workflow

1. Analyst opens Research Workspace for a case.
2. Analyst triggers "Source Intelligence Preview" (Phase 3D, unchanged).
3. Preview panel renders proposals as ephemeral cards.
4. Analyst clicks **Save proposals** — POSTs the preview payload; backend persists all suggestions as `proposed`.
5. Analyst reviews saved proposals in a Proposals tab or side panel.
6. For each proposal, analyst clicks **Approve** or **Reject**.
7. For approved proposals, analyst can click **Apply to Case** — creates a `ResearchSource` row on the case.
8. Applied source appears in the case's source list; suggestion status moves to `applied`.

---

## UI Concept

**Research Workspace (`/investment/research/[id]`):**

- New **"Source Proposals"** tab or section below the existing source list.
- Each row: source name, source type, action, confidence badge, reason text, approve / reject buttons (shown when status is `proposed`), apply button (shown when status is `approved`), status label.
- "Save proposals" button appears in the Source Intelligence Preview panel after a successful preview (same panel as Phase 3D).
- No auto-apply on save. No bulk apply.
- Rejected proposals are shown with a muted style and no action buttons.

---

## API Concept

### Save proposals (new)

```
POST /api/investment/research-cases/{id}/source-intelligence-suggestions
```

Body: array of suggestion objects from the preview payload (analyst selects which to save, or saves all).  
Returns: array of created `SourceIntelligenceSuggestion` records with `status: "proposed"`.  
No AI call. No `investment_sources` write.

### List proposals

```
GET /api/investment/research-cases/{id}/source-intelligence-suggestions
```

Returns all proposals for the case, ordered by `created_at desc`.

### Review a proposal (approve / reject)

```
PATCH /api/investment/research-cases/{id}/source-intelligence-suggestions/{suggestion_id}
```

Body: `{ "status": "approved" | "rejected" }`  
Sets `reviewed_at`. Returns updated suggestion.  
Rejects if current status is not `proposed`.  
Rejects if `status` value is not `approved` or `rejected`.

### Apply an approved proposal

```
POST /api/investment/research-cases/{id}/source-intelligence-suggestions/{suggestion_id}/apply
```

No body.  
Pre-condition checks (returns 409 if any fail):
- Suggestion status must be `approved`.
- `action` must be `"add"` (only `add` is supported in Phase 3E; `update_priority` and `deactivate` are reserved).
- `source_name` must not be blank.

If checks pass:
1. Creates a new `ResearchSource` row on the case with `source_name`, `source_type` (if present), `notes` = suggestion `reason`.
2. Sets suggestion `status = "applied"`, `applied_at = now()`.
3. Returns `{ "applied": true, "source_id": "<new source uuid>" }`.

No write to `investment_sources`.

---

## Safety Checks Before Apply

| Check | Failure response |
|---|---|
| Suggestion status ≠ `approved` | 409 — must approve before applying |
| Action ≠ `"add"` | 409 — only `add` action supported for apply in Phase 3E |
| `source_name` blank | 422 — source name required |
| Research case not found | 404 |

---

## Acceptance Criteria

1. `POST .../source-intelligence-suggestions` persists proposals with `status: "proposed"` and `manual_review_required: True`. No AI call on this endpoint.
2. `GET .../source-intelligence-suggestions` returns all proposals for the case.
3. `PATCH .../source-intelligence-suggestions/{id}` with `{ "status": "approved" }` transitions from `proposed` only; sets `reviewed_at`.
4. `PATCH` with `{ "status": "rejected" }` transitions from `proposed` only; sets `reviewed_at`. Rejected proposals cannot be re-approved.
5. `POST .../apply` creates a `ResearchSource` row; sets suggestion to `applied`; `investment_sources` remains untouched.
6. `POST .../apply` on a non-approved suggestion returns 409.
7. `POST .../apply` on an already-applied suggestion returns 409.
8. Buy/sell language check on `source_name` and `notes` at apply time — returns 422 if found.
9. All endpoints use `run_logger.start_run()` / `finish_run()` / `fail_run()`.
10. No auto-apply anywhere — no suggestion is ever applied without an explicit `POST .../apply`.
11. Tests: unit + integration for all lifecycle transitions, safety checks, and the no-auto-apply guardrail. Target ≥ 12 new tests.

---

## Open Questions

1. **Migration status:** Does the `source_intelligence_suggestions` table already exist from the Phase 1A migration (`c3d4e5f6a7b8`)? Run `alembic current` and check the migration file before implementing to avoid a double-migration.
2. **Apply scope for Phase 3E:** Only `action = "add"` is supported. `update_priority` and `deactivate` require more complex logic (finding the existing source by name/type, mutating it). Defer to Phase 3F or later.
3. **Bulk approve/apply:** Not in scope. Single-item operations only.
4. **Expiry:** Proposals currently have no TTL. If the analyst re-runs the preview, new proposals are appended (not deduped). A future sprint could add dedup by `(research_case_id, source_name, action)`.
5. **Frontend "Save proposals" UX:** Does analyst save all proposals from the preview, or select individually? Recommendation: save all by default; analyst then rejects unwanted ones. Simpler than a multi-select step.
