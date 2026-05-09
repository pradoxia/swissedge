# Investment Research Platform — Phase 3: Source and Document Intelligence

> Design sprint completed: 2026-05-02
> Status: DESIGN COMPLETE — implementation pending Dani approval
> Prerequisite: Phase 2 COMPLETE AND DEPLOYED

---

## 1. Purpose

Phase 3 adds structured intelligence enrichment to the two supporting entities already present in every ResearchCase: `ResearchDocument` and `ResearchSource`. The goal is to make the Research Workspace meaningfully richer without crossing the Phase 3 hard boundary (no URL fetching, no scanner changes, no publishing).

Three capabilities:

1. **Document summarisation** — AI reads title + URL (metadata only) + analyst notes to produce a structured summary of what the document likely contains and why it is relevant to the case.
2. **Source signal enrichment** — tag sources with sector, jurisdiction, and source type to enable filtering and quality signals across the workspace.
3. **Research Brief export** — render a completed brief as structured HTML for offline review and archiving.

A fourth capability — brief versioning — is included as sub-sprint 3E and is implementation-ready but lower priority.

---

## 2. Hard Boundary (Phase 3)

The following are **explicitly out of scope** for all Phase 3 sub-sprints:

| Boundary | Rule |
|---|---|
| URL crawling / content fetching | No fetching of document or source URLs. Metadata-only. |
| Scanner trigger | No `/scan` invocation, no cron changes |
| v2 evaluator global promotion | v2 remains manual-preview only |
| Publishing | No `status: published` transitions — manual editorial only |
| Buy/sell language | Forbidden in all AI output |
| Marketplace/Sales domain | Paused/preserved — no changes |
| Auto-apply to `investment_sources` | `SourceIntelligenceSuggestion` proposals only — never auto-applied |
| Live AI calls during implementation | All AI endpoints mocked during development |

---

## 3. Sub-Sprints

### 3A — Document and Source UI Enrichment (metadata-first, no AI)

**Scope:** Extend the Research Workspace UI for `ResearchDocument` and `ResearchSource` to capture the enrichment metadata fields already present in the data model.

**ResearchDocument additions:**
- `doc_type` selector: `sec_filing` / `press_release` / `ir_page` / `presentation` / `news` / `other`
- `relevance_score` slider or numeric input (1–10)
- `ai_summary` display-only panel (populated by 3B)

**ResearchSource additions:**
- `signal_quality` selector: `high` / `medium` / `low` / `no_signal`
- Sector tag input (free text, stored in existing `metadata` JSON field)
- Jurisdiction tag input (free text, stored in existing `metadata` JSON field)
- Source type tag input (free text, stored in existing `metadata` JSON field)

**Backend:**
- `PATCH /api/investment/research-cases/{id}/documents/{doc_id}` — already live (Phase 1E); verify `doc_type` and `relevance_score` fields are accepted
- `PATCH /api/investment/research-cases/{id}/sources/{source_id}` — verify `signal_quality` and `metadata` JSON merge are accepted

**Acceptance criteria:**
- Analyst can set `doc_type` on any document and `signal_quality` on any source from the workspace
- Values persist on save
- No AI calls in 3A

---

### 3B — Document AI Summary (manual trigger, metadata-only)

**Scope:** Add a "Generate Summary" button per document in the workspace. On click, POST to a new endpoint that calls the AI with document metadata (title, URL as string, doc_type, analyst notes) and returns a structured summary. No URL fetching.

**New endpoint:**
```
POST /api/investment/research-cases/{id}/documents/{doc_id}/generate-summary
```

**Request:** no body — context assembled server-side from stored document fields.

**Response:**
```json
{
  "document_id": "uuid",
  "ai_summary": "string",
  "relevance_rationale": "string",
  "suggested_relevance_score": 1-10,
  "warnings": ["string"],
  "saved_to_db": false,
  "disclaimer": "Este análisis es educativo. No es asesoramiento financiero.",
  "usage": { "provider": "...", "model": "...", "input_tokens": 0, "output_tokens": 0 }
}
```

**AI rules (see section 7):**
- Prompt includes: case context, document title, URL (as metadata string only — "DO NOT fetch this URL"), doc_type, analyst notes
- AI must not infer content from URL path beyond what is stated
- No buy/sell language in summary
- `saved_to_db: false` always — analyst applies manually via a separate "Apply Summary" button

**Apply flow:**
- "Apply Summary" button PATCHes `ai_summary` and optionally `relevance_score` to the document
- Analyst can edit the summary before applying

**Observability:** `run_logger.start_run()` / `finish_run()` / `fail_run()` required. Wrap all logger calls in try/except.

**Tests (mocked):**
- Returns `saved_to_db: false`
- No DB write on generate
- Returns disclaimer
- Malformed AI JSON returns safe defaults with warning
- 404 on unknown case or document

---

### 3C — Source Intelligence Suggestions (read-only proposals)

**Scope:** Add a "Analyse Source" button per source in the workspace. On click, POST to a new endpoint that calls the AI with source metadata (name, URL as string, signal_quality, metadata tags) to produce structured enrichment suggestions. Suggestions are proposals only — never auto-applied.

**New endpoint:**
```
POST /api/investment/research-cases/{id}/sources/{source_id}/analyse-source
```

**Response:**
```json
{
  "source_id": "uuid",
  "suggested_signal_quality": "high|medium|low|no_signal",
  "suggested_sector": "string",
  "suggested_jurisdiction": "string",
  "suggested_source_type": "string",
  "rationale": "string",
  "warnings": ["string"],
  "saved_to_db": false,
  "disclaimer": "Este análisis es educativo. No es asesoramiento financiero.",
  "usage": { "provider": "...", "model": "...", "input_tokens": 0, "output_tokens": 0 }
}
```

**Guardrail:** `SourceIntelligenceSuggestion` records are proposals only. The `investment_sources` table is never mutated by this endpoint.

**Apply flow:** "Apply" button PATCHes `signal_quality` and metadata JSON fields on the source record only.

**Observability:** same `run_logger` pattern as 3B.

**Tests (mocked):** same pattern as 3B — saved_to_db false, no DB write, disclaimer, malformed JSON safe defaults, 404.

---

### 3D — Research Brief Export (HTML render)

**Scope:** Add an "Export Brief" button on the Research Case detail page. On click, GET a new endpoint that renders the current `brief` JSON as structured HTML and returns it as a downloadable file.

**New endpoint:**
```
GET /api/investment/research-cases/{id}/export-brief
```

**Response:** `Content-Type: text/html`, `Content-Disposition: attachment; filename="brief_{ticker}_{date}.html"`

**Render rules:**
- All 14 brief sections rendered with section headings
- Disclaimer appended at the bottom
- No buy/sell language check: if the brief contains "buy", "sell", "short", "long position" as investment directives, the export is blocked with a 422 and a warning message
- No AI call — pure server-side render from stored `brief` JSON
- Empty brief fields rendered as "(not completed)"

**Frontend:** download triggered by `<a href=... download>` or `window.open`.

**No observability required** — no AI or external API call.

**Tests:**
- Returns 200 with `text/html` content type for case with brief
- Returns 422 if brief contains prohibited buy/sell directive language
- Returns 404 for unknown case
- Disclaimer present in rendered HTML

---

### 3E — Brief Versioning (track versions, allow rollback)

**Scope:** On every "Apply" to `ResearchCase.brief`, save the prior version to a `ResearchBriefVersion` table before overwriting. Add a version history panel to the Research Workspace with a "Restore" button.

**New model: `ResearchBriefVersion`**
```
id: UUID PK
research_case_id: UUID FK → research_cases.id
brief_version: int
brief: JSONB
model_used: str nullable
created_at: timestamptz
```

**New Alembic migration** required.

**New endpoints:**
```
GET  /api/investment/research-cases/{id}/brief-versions          → list versions
POST /api/investment/research-cases/{id}/brief-versions/{v}/restore → restore version
```

**Restore flow:** copies `brief` from `ResearchBriefVersion` back to `ResearchCase.brief`, increments `brief_version` on the live record.

**No AI call** — pure data operation.

**Tests:**
- Version saved on brief apply
- Restore returns 200 and updates `ResearchCase.brief`
- List returns ordered version history

---

## 4. Data Implications

| Entity | Change | Sprint |
|---|---|---|
| `ResearchDocument` | No schema change — `doc_type`, `relevance_score`, `ai_summary` already in model | 3A/3B |
| `ResearchSource` | No schema change — `signal_quality`, `metadata` already in model | 3A/3C |
| `SourceIntelligenceSuggestion` | No schema change — exists for proposal storage | 3C |
| `ResearchBriefVersion` | New table via Alembic migration | 3E |
| `ResearchCase.brief_version` | Already in model — increment on each apply | 3E |

Sub-sprints 3A through 3D require **no new Alembic migration**. Only 3E adds a new table.

---

## 5. UI Implications

**Research Workspace (`/investment/research/[id]`):**

| Component | Change | Sprint |
|---|---|---|
| Document row | Add `doc_type` selector + `relevance_score` input + "Generate Summary" button + summary display panel | 3A/3B |
| Source row | Add `signal_quality` selector + sector/jurisdiction/source type tag inputs + "Analyse Source" button + suggestions display | 3A/3C |
| Brief section | Add "Export Brief" button in header action row | 3D |
| Brief section | Add version history panel + "Restore" button | 3E |

No new routes required. All changes are within the existing Research Case detail page.

---

## 6. AI Rules (applies to all AI endpoints in Phase 3)

1. Every new AI endpoint uses `complete_with_usage()` — not `complete()`.
2. Every new AI endpoint wraps `run_logger.start_run()` / `finish_run()` / `fail_run()` in try/except.
3. All prompts stored in `backend/prompts/` as `.txt` files — never inline.
4. URL fields are passed to the AI prompt as metadata strings only. The prompt must explicitly instruct the AI: "DO NOT attempt to fetch or access this URL. Treat it as a label only."
5. AI output must never contain buy/sell directives. Parser must check for and strip/warn on any such language.
6. All AI responses return `saved_to_db: false`. Analyst applies changes explicitly.
7. Disclaimer `"Este análisis es educativo. No es asesoramiento financiero."` must be returned in every AI endpoint response.
8. Malformed AI JSON must return safe defaults with a warning — never a 500.

---

## 7. Safety / Legal / Copyright

- **No URL fetching.** Document and source URLs are metadata only. No HTTP requests to third-party URLs from any Phase 3 endpoint.
- **No SEC/EDGAR content reproduction.** AI summaries are analyst-facing internal notes, not published output.
- **No buy/sell language.** All AI summaries and source analyses are investment-neutral. Any directive language triggers a warning and is stripped before response.
- **Disclaimer on all AI output.** All AI-generated content carries the standard platform disclaimer.
- **No `published` status.** Phase 3 adds no new paths to `status: published`.
- **`SourceIntelligenceSuggestion` — proposals only.** The `investment_sources` registry is never mutated by Phase 3 endpoints.

---

## 8. Acceptance Criteria

| Sub-sprint | Criterion |
|---|---|
| 3A | `doc_type` and `signal_quality` persist on save from workspace UI |
| 3A | Sector, jurisdiction, source type tags persist in `metadata` JSON |
| 3B | "Generate Summary" returns `saved_to_db: false` |
| 3B | No DB write on generate — only on explicit "Apply Summary" |
| 3B | Disclaimer present in every generate-summary response |
| 3B | Malformed AI JSON returns safe defaults with warning, not 500 |
| 3C | "Analyse Source" returns `saved_to_db: false` |
| 3C | `investment_sources` table unmodified by analyse-source endpoint |
| 3D | Export returns valid HTML with all 14 sections and disclaimer |
| 3D | Export blocked with 422 if brief contains buy/sell directive language |
| 3E | Prior brief saved to `ResearchBriefVersion` on every apply |
| 3E | Restore updates `ResearchCase.brief` and increments `brief_version` |
| All | All new AI endpoints emit `run_logger` events |
| All | All tests run with mocked AI — no live AI calls during CI |

---

## 9. Open Questions

1. **Document summary prompt scope:** Should the AI summary prompt include the full case `brief` as context (to allow relevance reasoning against what is already written), or only the document metadata and analyst notes? Including the brief improves relevance reasoning but increases token cost per call.

2. **`doc_type` vs free-text type:** The current enum (`sec_filing`, `press_release`, `ir_page`, `presentation`, `news`, `other`) may be too narrow for some situations (e.g., court filings, regulatory orders). Should a free-text override field be added alongside the enum, or should the enum be extended?

3. **Brief export format:** HTML is proposed for offline review. Should PDF export (via headless browser or a library like WeasyPrint) be added in 3D or scoped to a later phase? PDF is higher fidelity for archiving but adds a dependency.

4. **Source intelligence suggestions persistence:** `SourceIntelligenceSuggestion` records are written on each "Analyse Source" call. Should they be deduplicated (one per source, overwritten on re-run) or append-only (full history)? Append-only is simpler but will grow unbounded.

5. **Brief versioning trigger:** 3E proposes saving a version on every "Apply" to `brief`. If the analyst applies multiple times in quick succession, version count grows rapidly. Should a minimum time gap (e.g., 5 minutes) or a minimum diff threshold be enforced before creating a new version?

---

## 10. Next Recommended Sprint

**Phase 3A — Document and Source UI Enrichment** is the lowest-risk entry point: no AI calls, no new DB migrations, and directly improves analyst workflow. Recommended first sprint.

Sequence:
1. **3A** — UI enrichment (metadata fields, no AI) — 1 sprint
2. **3B** — Document AI summary (manual trigger, mocked in tests) — 1 sprint
3. **3C** — Source intelligence suggestions (manual trigger, mocked in tests) — 1 sprint
4. **3D** — Brief HTML export (no AI) — 1 sprint
5. **3E** — Brief versioning (new migration required) — 1 sprint, last due to migration risk

Phase 3A can begin immediately after Dani approves this design.
