# Investment Research Platform — Technical Overview

> Internal reference document. Not for external distribution.
> Last updated: 2026-05-02 — covers Phase 1A through 4C (all COMPLETE AND DEPLOYED).
> Source files read: `backend/api/investment/research_cases.py`, `backend/services/investment/research_cases.py`, `frontend/app/investment/research/page.tsx`, `frontend/app/investment/research/[id]/page.tsx`, `frontend/app/investment/source-intelligence/page.tsx`, `frontend/app/investment/historical-cases/page.tsx`, `frontend/app/investment/historical-cases/[id]/page.tsx`, `frontend/lib/api.ts`.

---

## 1. Main Purpose

The Investment Research Platform is the active domain of SwissEdge. It detects, investigates, documents, and structures research on **special situations** — corporate events such as spinoffs, mergers, and tender offers — sourced initially from SEC EDGAR filings.

The platform is a **structured analyst workspace**, not a trading or recommendations engine. Every AI-generated output carries the disclaimer:

> *Este análisis es educativo. No es asesoramiento financiero.*

The platform is organized around two primary case types:

- **ResearchCase** — a live, ongoing investigation linked to a detected situation or created manually.
- **HistoricalCase** — a manually reconstructed past case study used for pattern recognition and source intelligence training.

A third object, **SourceIntelligenceSuggestion**, forms a shared approval queue that spans both case types.

---

## 2. Main Frontend Routes

| Route | Component | Description |
|---|---|---|
| `/investment/research` | `ResearchCasesPage` | List of all ResearchCases; status and readiness filters; create-from-situation panel |
| `/investment/research/[id]` | `ResearchDetailPage` | Full research workspace: brief, notes, tasks, documents, sources, AI panels |
| `/investment/source-intelligence` | `SourceIntelligenceQueuePage` | Global approval queue for all SourceIntelligenceSuggestions across both case types |
| `/investment/historical-cases` | `HistoricalCasesPage` | List of all HistoricalCases; status filter; inline create form |
| `/investment/historical-cases/[id]` | `HistoricalCaseDetailPage` | Historical case workspace: notes, status, Source Intelligence Preview, saved proposals |
| `/investment/evaluations` | (separate domain) | Upstream evaluation queue — entry point to create a ResearchCase from a detected situation |
| `/investment/watchlist` | (separate domain) | Watchlist with status filter |
| `/investment/radar-status` | (separate domain) | Scanner observability, read-only |
| `/investment/sources` | (separate domain) | Source registry and toggles |

### Research Detail Page Sub-Panels (`/investment/research/[id]`)

The detail page is the most complex route. It contains the following independent sub-panels, each rendered inline:

- **BriefEditor** — collapsible 14-section structured brief editor; shows "X/14 SECTIONS FILLED" progress indicator.
- **AiPreviewPanel** — AI brief generation preview; section-by-section compare with apply-selected workflow; displays context used, model name, and token counts.
- **QualityAssistPanel** — 9-item AI quality checklist with suggested status and readiness; explicit apply buttons.
- **DocumentCard** (per document) — inline metadata editing, snippet paste editor, per-document AI analysis.
- **SourceCard** (per source) — signal quality dropdown and notes editor.
- **SourceIntelligencePanel** — generate preview, view suggestions and source scores, save proposals to queue, inline approve/reject.

---

## 3. Main Backend Endpoint Groups

All endpoints live under the prefix `/api/investment/` and are registered via a FastAPI `APIRouter` in `backend/api/investment/research_cases.py`.

### ResearchCase CRUD

| Method | Path | Description |
|---|---|---|
| `POST` | `/research-cases/from-situation/{situation_id}` | Create ResearchCase linked to an upstream Situation |
| `POST` | `/research-cases` | Create ResearchCase manually (no linked situation) |
| `GET` | `/research-cases` | List all ResearchCases (filters: status, readiness) |
| `GET` | `/research-cases/{id}` | Get single ResearchCase with eager-loaded relations |
| `PATCH` | `/research-cases/{id}` | Update status, readiness, notes, brief sections |

### Tasks, Documents, Sources (sub-resources of ResearchCase)

| Method | Path | Description |
|---|---|---|
| `POST` | `/research-cases/{id}/tasks` | Add a ResearchTask |
| `PATCH` | `/research-cases/{id}/tasks/{task_id}` | Update task status, title, notes |
| `POST` | `/research-cases/{id}/documents` | Add a ResearchDocument |
| `PATCH` | `/research-cases/{id}/documents/{doc_id}` | Update doc title, doc_type, snippet, notes, signal_quality |
| `POST` | `/research-cases/{id}/sources` | Add a ResearchSource |
| `PATCH` | `/research-cases/{id}/sources/{src_id}` | Update source signal_quality, notes |

### AI Preview Endpoints (ResearchCase)

| Method | Path | Description |
|---|---|---|
| `POST` | `/research-cases/{id}/generate-brief-preview` | AI brief generation preview; `saved_to_db: false` |
| `POST` | `/research-cases/{id}/quality-preview` | AI quality checklist + suggested status/readiness; `saved_to_db: false` |
| `POST` | `/research-documents/{id}/analysis-preview` | Per-document AI analysis; `saved_to_db: false` |
| `POST` | `/research-cases/{id}/source-intelligence-preview` | AI source intelligence proposals; `saved_to_db: false` |

### Source Intelligence Suggestion Queue (Phase 4A)

| Method | Path | Description |
|---|---|---|
| `POST` | `/research-cases/{id}/source-intelligence-suggestions` | Save proposals from a ResearchCase preview to the queue |
| `GET` | `/source-intelligence-suggestions` | List all suggestions (filters: status, action, research_case_id, historical_case_id) |
| `PATCH` | `/source-intelligence-suggestions/{id}` | Approve or reject a single suggestion (status only) |

### Historical Cases (Phase 4B)

| Method | Path | Description |
|---|---|---|
| `POST` | `/historical-cases` | Create a HistoricalCase |
| `GET` | `/historical-cases` | List all HistoricalCases (filter: status) |
| `GET` | `/historical-cases/{id}` | Get single HistoricalCase |
| `PATCH` | `/historical-cases/{id}` | Update status, seed_notes, reconstruction |

### Historical Case Source Intelligence (Phase 4C)

| Method | Path | Description |
|---|---|---|
| `POST` | `/historical-cases/{id}/source-intelligence-preview` | AI source intelligence proposals for a historical case; `saved_to_db: false` |
| `POST` | `/historical-cases/{id}/source-intelligence-suggestions` | Save proposals from a HistoricalCase preview to the shared queue |

### Observability

Every AI endpoint (`generate-brief-preview`, `quality-preview`, `analysis-preview`, `source-intelligence-preview`, and their historical-case equivalents) is wrapped with:

```python
run_id = run_logger.start_run(...)
try:
    ...
    run_logger.finish_run(run_id, ...)
except Exception:
    run_logger.fail_run(run_id, ...)
    raise
```

Token usage is recorded via `log_ai_usage()` for every AI call.

---

## 4. Core Data Objects

### ResearchCase

The central object representing an ongoing investigation.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `situation_id` | UUID (nullable) | FK to upstream `investment_situations` table; null for manually created cases |
| `company_name` | string | |
| `situation_type` | string | e.g. spinoff, merger, tender_offer |
| `status` | enum | `under_investigation`, `documented`, `watching`, `archived` |
| `investment_readiness` | enum | `monitor`, `not_actionable`, `needs_more_work`, `candidate` |
| `notes` | text | Free-form analyst notes |
| `brief` | JSONB | 14-key structured brief; keys match `_BRIEF_SECTIONS` |
| `tasks` | relation | List of `ResearchTask` objects |
| `documents` | relation | List of `ResearchDocument` objects |
| `sources` | relation | List of `ResearchSource` objects |
| `created_at` / `updated_at` | datetime | |

Valid `status` values: `under_investigation`, `documented`, `watching`, `archived`.
Valid `investment_readiness` values: `monitor`, `not_actionable`, `needs_more_work`, `candidate`.
API returns `400` for any value outside these sets.

#### Brief Sections (14 keys)

`situation_summary`, `key_actors`, `timeline`, `financial_overview`, `legal_regulatory`, `risks`, `catalysts`, `comparable_situations`, `source_analysis`, `information_gaps`, `preliminary_thesis`, `monitoring_plan`, `open_questions`, `research_status_note`

### ResearchTask

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `research_case_id` | UUID | FK to ResearchCase |
| `title` | string | |
| `status` | enum | `pending`, `in_progress`, `done`, `blocked` |
| `notes` | text (nullable) | |
| `created_at` | datetime | |

### ResearchDocument

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `research_case_id` | UUID | FK to ResearchCase |
| `title` | string | |
| `url` | string (nullable) | Metadata-only — never fetched or crawled |
| `doc_type` | string (nullable) | e.g. `sec_filing`, `press_release`, `news_article`, `analyst_report`, `court_filing`, `regulatory_filing`, `other` |
| `summary` | text (nullable) | Used as the document snippet for AI analysis |
| `signal_quality` | enum (nullable) | `high`, `medium`, `low`, `noise` |
| `notes` | text (nullable) | Analyst notes / tags |
| `metadata_only` | bool | True if document has URL but no fetched content |
| `created_at` | datetime | |

Minimum snippet length for AI document analysis: **50 characters** (`_MIN_SNIPPET_LENGTH = 50`).

### ResearchSource

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `research_case_id` | UUID | FK to ResearchCase |
| `name` | string | |
| `url` | string (nullable) | Metadata-only — never fetched |
| `source_type` | string (nullable) | |
| `signal_quality` | enum (nullable) | `high`, `medium`, `low`, `noise` |
| `notes` | text (nullable) | |
| `created_at` | datetime | |

### HistoricalCase

Manually reconstructed past case studies. No link to live scanner or upstream evaluation.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `company_name` | string | |
| `situation_type` | string | |
| `event_date_approx` | string (nullable) | Free-form e.g. "2016-Q4" |
| `seed_notes` | text (nullable) | Initial reconstruction notes |
| `course_chapter_ref` | string (nullable) | Reference to course material chapter |
| `reconstruction` | JSONB (nullable) | Structured reconstruction data (deferred editor — Phase 4E) |
| `status` | enum | `seed`, `reconstructed`, `lessons_extracted`, `source_intel_applied` |
| `linked_situation_id` | UUID (nullable) | Optional FK to a live situation |
| `disclaimer` | string | Always `"Este análisis es educativo. No es asesoramiento financiero."` |
| `created_at` / `updated_at` | datetime | |

Valid `status` values: `seed`, `reconstructed`, `lessons_extracted`, `source_intel_applied`.

### SourceIntelligenceSuggestion

Shared approval queue object. Spans both ResearchCase and HistoricalCase origins.

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `research_case_id` | UUID (nullable) | Set when originated from a ResearchCase |
| `historical_case_id` | UUID (nullable) | Set when originated from a HistoricalCase |
| `action` | enum | `add`, `update_priority`, `deactivate` |
| `proposed_name` | string | Suggested source name |
| `proposed_source_type` | string (nullable) | |
| `rationale` | text (nullable) | AI-generated reasoning |
| `status` | enum | `proposed`, `approved`, `rejected` |
| `created_at` / `reviewed_at` | datetime | `reviewed_at` set on approve/reject |

Valid `status` values: `proposed`, `approved`, `rejected`.
The `PATCH` endpoint accepts only `approved` or `rejected` — `proposed` cannot be re-set via API.

---

## 5. User Workflows

### 5.1 Evaluation → ResearchCase

1. Analyst reviews upstream evaluation at `/investment/evaluations/[id]`.
2. Clicks "Create Research Case" in the Evaluation Detail panel.
3. Frontend calls `POST /api/investment/research-cases/from-situation/{situation_id}`.
4. Redirected to `/investment/research/[id]` with the new case pre-populated.

Alternatively, a ResearchCase can be created directly from the Research Cases list (`POST /api/investment/research-cases` with no `situation_id`).

### 5.2 Research Workspace — Tasks, Documents, Sources

All three are manually managed. No automatic creation from scanner or AI.

- **Add task**: Enter title → POST `/research-cases/{id}/tasks` → task appears inline.
- **Update task status**: Click status badge → inline dropdown → PATCH.
- **Add document**: Enter title + optional URL → POST. URL is stored as metadata only.
- **Edit document**: Inline `doc_type` selector, `signal_quality` dropdown, notes field, snippet textarea — each saved explicitly via PATCH.
- **Add source**: Enter name + optional URL → POST. URL is metadata only.
- **Edit source**: `signal_quality` dropdown, notes textarea — saved via explicit PATCH.

### 5.3 Research Brief — Manual Editing

The `BriefEditor` panel surfaces all 14 sections as independent text areas. Each section is edited and saved independently via `PATCH /research-cases/{id}` with the updated `brief` JSONB payload. Progress indicator shows "X/14 SECTIONS FILLED" (non-empty sections count).

### 5.4 AI Brief Preview

1. Analyst opens `AiPreviewPanel` in the research workspace.
2. Clicks "GENERATE AI BRIEF PREVIEW".
3. Frontend calls `POST /research-cases/{id}/generate-brief-preview`.
4. Panel displays side-by-side: current saved section vs. AI-suggested section.
5. Analyst selects individual sections via checkboxes.
6. Clicks "APPLY SELECTED SECTIONS" → selected sections merged into brief via PATCH.
7. Analyst clicks "SAVE BRIEF" to persist.

Context used, model name, and token counts are displayed in the panel footer. A "URL METADATA ONLY" notice appears if any document/source URLs are present (they were not fetched).

### 5.5 Quality Assist

1. Analyst opens `QualityAssistPanel`.
2. Clicks "RUN QUALITY ANALYSIS".
3. Frontend calls `POST /research-cases/{id}/quality-preview`.
4. Panel displays 9-item checklist (each `true`/`false`) plus suggested status and readiness.
5. Analyst can click "APPLY SUGGESTED STATUS", "APPLY SUGGESTED READINESS", or "APPLY BOTH" — each triggers a PATCH.

The panel banner reads "ASSISTIVE PREVIEW — NOT SAVED". The AI suggestion is never auto-applied.

### 5.6 Document Analysis Preview

1. Analyst pastes a text snippet (≥50 chars) into the document's summary field and saves it via PATCH.
2. Clicks "ANALYSE DOCUMENT" button on the `DocumentCard`.
3. Frontend calls `POST /research-documents/{doc_id}/analysis-preview`.
4. Panel displays: `summary`, `key_points`, `risks`, `timeline_items`, `suggested_research_tasks`, `source_usefulness`.
5. Analyst reviews and applies information manually to the brief or tasks.

Footer reads: "NOT SAVED — apply changes manually". No auto-task creation. No URL fetching.

### 5.7 Source Intelligence Preview (ResearchCase)

1. Analyst opens `SourceIntelligencePanel` on the research workspace.
2. Clicks "GENERATE SOURCE INTELLIGENCE PREVIEW".
3. Frontend calls `POST /research-cases/{id}/source-intelligence-preview`.
4. Panel displays:
   - **Source scores**: usefulness assessment for each existing source (signal_quality, usefulness_reason, suggested_follow_up).
   - **Suggestions**: list of proposed source actions (add/update_priority/deactivate) with confidence and reasoning.
5. Banner reads: "PROPOSALS ONLY — NOT APPLIED".
6. Analyst clicks "SAVE X PROPOSAL(S)" → calls `POST /research-cases/{id}/source-intelligence-suggestions`.
7. Saved proposals appear in inline list with Approve/Reject buttons.

### 5.8 Source Intelligence Approval Queue

Accessible at `/investment/source-intelligence`. Aggregates all proposals across ResearchCases and HistoricalCases.

- **Filter** by status (proposed/approved/rejected) and action (add/update_priority/deactivate).
- **Pending Review** section: Approve or Reject each proposal individually.
- **Reviewed** section: read-only list of decided proposals.
- Each proposal links back to its originating ResearchCase or HistoricalCase.
- **No apply action exists**. Approval is a decision record only.

### 5.9 Historical Cases — Create and Manage

1. Navigate to `/investment/historical-cases`.
2. Click "+ NEW HISTORICAL CASE" → inline form requires `company_name` and `situation_type`; optional `event_date_approx` and `seed_notes`.
3. POST creates the case at `seed` status.
4. Open the case detail at `/investment/historical-cases/[id]`.
5. Edit notes via inline textarea → explicit SAVE button → PATCH.
6. Advance status via inline dropdown → explicit SAVE button → PATCH.

### 5.10 Historical Case Source Intelligence Preview

Same flow as ResearchCase Source Intelligence Preview (§5.7), but scoped to a HistoricalCase:

1. Click "GENERATE SOURCE INTELLIGENCE PREVIEW" on the detail page.
2. Frontend calls `POST /historical-cases/{id}/source-intelligence-preview`.
3. View suggestions → save proposals → inline approve/reject.

Proposals saved from a HistoricalCase set `historical_case_id` on the `SourceIntelligenceSuggestion` row (not `research_case_id`).

---

## 6. What Is Manual-Only

These actions require explicit analyst input and have no automated or AI-triggered equivalent:

- Creating a ResearchCase (either from a Situation or from scratch).
- Adding, editing, or deleting ResearchTasks.
- Adding, editing, or deleting ResearchDocuments (including URL entry and snippet paste).
- Adding, editing, or deleting ResearchSources.
- Editing any brief section (14 sections edited individually).
- Updating ResearchCase `status` and `investment_readiness`.
- Advancing a HistoricalCase `status` through its lifecycle.
- Editing HistoricalCase `seed_notes` and `reconstruction`.
- Approving or rejecting any SourceIntelligenceSuggestion.
- Creating a HistoricalCase.

---

## 7. What Is Preview-Only

These AI endpoints return a result object with `saved_to_db: false`. Nothing is persisted automatically. The analyst must explicitly apply or save results through a separate UI action.

| Preview Endpoint | What Is Returned | Explicit Apply Action |
|---|---|---|
| `generate-brief-preview` | 14 suggested brief sections | Checkbox-select + "APPLY SELECTED SECTIONS" button |
| `quality-preview` | 9-item checklist + suggested status/readiness | "APPLY SUGGESTED STATUS / READINESS / BOTH" buttons |
| `analysis-preview` (document) | Summary, key points, risks, timeline, task suggestions | Manual copy/paste or manual task creation by analyst |
| `source-intelligence-preview` | Source scores + add/update/deactivate proposals | "SAVE X PROPOSAL(S)" button → then Approve/Reject in queue |
| `historical-case source-intelligence-preview` | Same as above, scoped to HistoricalCase | Same save + approve/reject flow |

---

## 8. What Is Never Automatic

The following actions are architecturally excluded from any automatic trigger path. They require explicit human initiation at every step:

- **URL fetching / crawling** — Document and source URLs are stored as metadata only. No backend code reads the URL contents. Applies to all document analysis, source intelligence, and brief preview flows.
- **Applying AI proposals to `investment_sources`** — The global source registry is never written to by any current endpoint. The Phase 4D apply endpoint does not yet exist.
- **Task creation from AI output** — The document analysis preview may suggest research tasks, but no endpoint auto-creates them.
- **Brief section auto-save** — The brief preview panel never writes to the database without an explicit "APPLY SELECTED SECTIONS" action followed by a separate "SAVE BRIEF" action.
- **Status promotion** — AI Quality Assist may suggest a status change; it is never applied without an analyst click. The `published` status is hard-blocked from AI suggestion entirely (see §9).
- **Scanner trigger** — The `/api/investment/scan` endpoint is never called from the research platform frontend.
- **Cron changes** — No research platform action modifies any scheduled task.

---

## 9. Safety Guardrails

### Published Status Hard-Block

The Quality Assist parser enforces a hard rule: if the AI returns `suggested_status: "published"`, the value is silently downgraded:

- To `documented` if `brief_completeness` is `true`
- To `under_investigation` otherwise

A warning is appended to the response. The `published` status requires manual editorial approval only and cannot be set via the Quality Assist apply action.

### Buy/Sell Language Filter

A `_BUY_SELL_PATTERNS` regex set is applied to all AI-generated text fields (brief sections, quality suggestions, document analysis output, source intelligence proposals) before they are returned in any preview response. Any match causes the output to be flagged and the affected field is sanitized or the request is rejected with a warning.

At suggestion apply time (Phase 4D, not yet implemented), `proposed_name` and `rationale` will also be checked — a match returns `422`.

### Only `approved` Suggestions Can Be Applied (Phase 4D)

When the Phase 4D apply endpoint is implemented, it will enforce: only suggestions with `status = "approved"` can be applied. Applying a `proposed` or `rejected` suggestion will return `409`.

### Input Validation

- `investment_readiness` values outside `{monitor, not_actionable, needs_more_work, candidate}` → `400`.
- `status` values outside the valid set for each object type → `400`.
- Document analysis requested when snippet is shorter than 50 characters → rejected with validation error.
- `PATCH /source-intelligence-suggestions/{id}` accepts only `approved` or `rejected` — `proposed` is not a valid target state.

### Disclaimer Enforcement

Every AI response includes the disclaimer: *"Este análisis es educativo. No es asesoramiento financiero."* This is hardcoded server-side as `_DISCLAIMER` and returned in every preview result. The frontend renders it in every AI panel footer and at the bottom of every list and detail page.

### URL Metadata-Only Notice

When a ResearchCase has documents or sources with URLs, the AI Brief Preview panel and Document Analysis Preview panel display an explicit notice: "URL METADATA ONLY — document/source URLs were not fetched."

---

## 10. Current Limitations and Deferred Features

### Not Yet Implemented

| Feature | Phase | Notes |
|---|---|---|
| Apply approved proposals to `ResearchSource` | **4D** | `POST /source-intelligence-suggestions/{id}/apply`; creates `ResearchSource` row; sets `status = applied`; `applied_at = now()` |
| Historical Case reconstruction editor | **4E** | Structured JSONB fields for the `reconstruction` column; currently free-text notes only |
| Cross-case lessons linking | **4F** | HistoricalCase lessons → linked to source intelligence queue for cross-case learning |
| Brief export and versioning | Deferred | No export (PDF, Markdown, etc.) currently exists |
| Publishing pipeline | Deferred | `published` status exists in the enum but the path to reach it is editorial-manual only |
| Apply proposals to `investment_sources` | Deferred (4D+) | The global source registry is never written by any current endpoint |
| Document URL fetching | Explicitly excluded | Metadata-only by design; no planned implementation |

### Known Architectural Gaps

- **`reconstruction` field** on HistoricalCase is JSONB but has no structured editor; the frontend shows seed_notes only. The `reconstruction` column is writable via PATCH but the UI for it is deferred to Phase 4E.
- **`course_chapter_ref`** on HistoricalCase is displayed read-only; no UI to edit it currently exists in the frontend.
- **`linked_situation_id`** on HistoricalCase is stored but not surfaced as a link in the frontend.
- **Source scores** (`SourceScoreItem` objects) from the Source Intelligence Preview are displayed inline in the preview panel but are not persisted to any table. Only the `suggestions` array is saveable to the queue.
- **`suggested_research_tasks`** from Document Analysis Preview are shown as display text only; no one-click "create task from suggestion" action exists.
- **Bulk approve/reject** is not available in the Source Intelligence Queue; each proposal must be reviewed individually.

### Operational Constraints

- The `/api/investment/scan` endpoint is excluded from all research platform flows.
- Evaluator v2 is manual-preview only; v1 is the production default.
- The Marketplace/Sales domain is preserved but paused; no changes are scoped.
- No Alembic migration is included in Phase 4B/4C (historical_cases table was already deployed).

---

## Final Report

### Changed Files

None. This is a documentation-only file.

### Sections Created

| # | Section Title | Status |
|---|---|---|
| 1 | Main Purpose | Complete |
| 2 | Main Frontend Routes | Complete — includes sub-panel breakdown for `/investment/research/[id]` |
| 3 | Main Backend Endpoint Groups | Complete — all endpoint groups from Phase 1A through 4C |
| 4 | Core Data Objects | Complete — ResearchCase (with 14 brief keys), ResearchTask, ResearchDocument, ResearchSource, HistoricalCase, SourceIntelligenceSuggestion |
| 5 | User Workflows | Complete — 10 discrete workflows documented |
| 6 | What Is Manual-Only | Complete |
| 7 | What Is Preview-Only | Complete — table with all 5 preview endpoints and their apply actions |
| 8 | What Is Never Automatic | Complete |
| 9 | Safety Guardrails | Complete — published block, buy/sell filter, input validation, disclaimer enforcement, URL metadata notice |
| 10 | Current Limitations and Deferred Features | Complete — Phase 4D/4E/4F, known gaps, operational constraints |

### Gaps Found

1. **`course_chapter_ref` editing** — no frontend editor exists; displayed read-only.
2. **`reconstruction` JSONB editor** — deferred to Phase 4E; current frontend only shows `seed_notes`.
3. **`linked_situation_id` on HistoricalCase** — stored in DB but not surfaced as a navigable link in the frontend.
4. **Source scores not persisted** — `SourceScoreItem` results are preview-only with no save path; only `suggestions` can be queued.
5. **Bulk operations on approval queue** — no bulk approve/reject endpoint or UI.
6. **`suggested_research_tasks` from document analysis** — display-only; no one-click create-task action.
7. **Phase 4D apply endpoint** — not yet implemented; the approved-proposal-to-ResearchSource write path is the most significant missing link in the current architecture.

### Recommended Next Documentation Files

| File | Purpose |
|---|---|
| `docs/technical/API_REFERENCE.md` | Full endpoint-by-endpoint reference with request/response schemas, error codes, and example payloads — suitable for integration testing or onboarding |
| `docs/technical/DATA_MODEL.md` | Entity-relationship diagram (text form) and full field-level schema for all 7 DB models including FK constraints and Alembic migration IDs |
| `docs/technical/AI_ENDPOINTS.md` | Prompt structure, context assembly logic, token budget, model used, and `run_logger` observability pattern for each of the 5 AI preview endpoints |
| `docs/technical/GUARDRAILS.md` | Exhaustive guardrail catalogue: buy/sell filter regex, published status block, metadata-only URL policy, `investment_readiness` validation, suggestion apply guard |
| `docs/user/RESEARCH_WORKFLOW_GUIDE.md` | User-facing step-by-step guide to the research case workflow (evaluation → brief → quality assist → source intelligence → approval) |
| `docs/user/HISTORICAL_CASES_GUIDE.md` | User-facing guide to the historical cases workspace (create → reconstruct → source intelligence → lessons) |
