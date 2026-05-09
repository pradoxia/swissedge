# SwissEdge — Investment Research Platform Redesign

**Status:** Design document — documentation only. No implementation, migration, endpoint, or cron changes.
**Author:** SwissEdge design sprint (2026-05-01)
**Prerequisite reading:** `PROJECT_STATE.md`, `docs/decisions.md`, `CLAUDE.md`

---

## 1. Product Purpose

SwissEdge Investment is a **private investment research desk** for special situations. It is not a stock screener, robo-advisor, or trading signal generator.

Its job is to:

1. **Identify** corporate special situations appearing in public filings and news.
2. **Investigate** each situation using public sources: SEC filings, company websites, investor relations materials, press releases, analyst commentary, board/management history, and course-derived methodology.
3. **Explain** the situation in structured form: what it is, why it may be interesting, what the course methodology prescribes, what is missing, what manual follow-up Dani should do.
4. **Study historical cases**: reconstruct past situations that SwissEdge could have detected, identify the entry window, what sources were available, and extract lessons.
5. **Improve source intelligence** continuously: active case experience and historical case study feed back into the `investment_sources` registry.
6. **Publish** selected research as structured, manually approved public educational content — separate from private Mission Control, written for a community audience, using status labels only (never buy/sell language).

All outputs are educational. The disclaimer `"Este análisis es educativo. No es asesoramiento financiero."` is appended at the FastAPI layer on every investment output.

---

## 2. Current State Summary

| Component | Status |
|---|---|
| SEC EDGAR scanner | ✅ Operational — cron, EFTS query fixed |
| `special_situations` table | ✅ Live — populated by scanner |
| v1 evaluator | ✅ Production default — course-methodology prompt |
| v2 evaluator | Manual-preview only — validated, not in cron |
| `investment_sources` table | ✅ 7 sources (4 active, 3 inactive); enable/disable UI live |
| Source enable/disable | ⚠ UI live but scanner still hardcoded to SECEdgarAdapter (Sprint 17 gap) |
| Evaluations queue / detail / watchlist | ✅ Operational |
| Radar Status (read-only) | ✅ Operational |
| Course extraction | ✅ Complete — 22 chapters, 132 files, 7 playbooks, global artifacts |
| ResearchCase model | ❌ Not yet designed or implemented |
| Historical case infrastructure | ❌ Not yet designed or implemented |
| Source intelligence feedback loop | ❌ Not yet designed or implemented |
| Publishing pipeline | ❌ Not yet designed or implemented |

**Gap being addressed by this document:** The platform can detect and evaluate; it cannot yet investigate, document, study history, or publish.

---

## 3. Strategic Product Definition

### What changes

| Before | After |
|---|---|
| Scanner finds filing → evaluator scores it → Dani reviews | Scanner finds filing → research agent builds structured brief → Dani investigates → documented case |
| Evaluations are self-contained, no history | Active cases feed historical case archive; historical cases improve source intelligence |
| No publishing path | Research desk can produce public educational articles — manually gated |
| Sources are static DB rows | Sources are live entities that gain/lose weight based on what they surface |

### What does NOT change

- v1 evaluator remains production default. No cron change.
- v2 remains manual-preview only. No global enable.
- Scanner cron is unchanged. No `/api/investment/scan` calls from this system.
- All publishing requires explicit manual approval — no auto-publish ever.
- FastAPI is source of truth (D001). OpenClaw is an operator only (D002).
- Observability wraps every AI call (D004).
- No secrets, IPs, or raw course material in any file (D006, D007).

### Investment recommendation guardrail

Public-facing output uses **status labels only**:

| Label | Meaning |
|---|---|
| `monitor` | Situation is active; not enough clarity to act |
| `not actionable` | Situation does not meet course criteria |
| `needs more work` | Interesting but incomplete; more research required |
| `candidate for further research` | Meets initial criteria; warrants deep investigation |

No direct buy/sell language in any output, private or public.

---

## 4. Core User Workflow

```
[Scanner cron] → new SpecialSituation row
        ↓
[Dani opens Evaluations Queue]
        ↓
[Selects situation → Detail Page]
        ↓
[Requests Research Brief (manual)]
        ↓ (situation_research_agent runs, ~1 AI call)
[ResearchCase created, status: brief_generated]
        ↓
[Dani reviews brief, marks tasks, adds notes]
        ↓
[ResearchCase: under_investigation]
        ↓
[Dani concludes investigation]
        ↓
[ResearchCase: documented]
        ↓
[Optional: Dani requests PublicArticleDraft]
        ↓ (publisher_agent runs)
[Dani reviews draft → approves → published]
        ↓
[Source Intelligence Agent proposes new/updated sources]
        ↓ (Dani reviews → approved sources added to investment_sources)
```

Historical path:
```
[Dani identifies past case to study]
        ↓
[HistoricalCase seeded manually or from completed ResearchCase]
        ↓ (historical_case_agent runs)
[Timeline reconstructed, entry window identified, lessons extracted]
        ↓
[Source Intelligence Agent proposes sources based on lessons]
```

---

## 5. Agent Network

All agents are FastAPI-registered logical agents. All AI calls use `complete_with_usage()` and log to `agent_runs` / `ai_usage`. All observability calls are wrapped in try/except (D004).

### 5.1 `investment_scanner`

**Already exists.** No changes in this sprint.

- Polls SEC EDGAR via cron (every 6h)
- Creates `SpecialSituation` rows
- Sprint 17 gap: reads hardcoded SECEdgarAdapter, not `investment_sources` DB table

**Future:** Wire scanner to read from `investment_sources` table so enable/disable toggles take effect.

---

### 5.2 `situation_research_agent` _(new)_

**Trigger:** Manual only — Dani clicks "Generate Research Brief" on a detail page.

**Input:** `SpecialSituation` row + course methodology playbook (from `course_index/`) + available documents

**Processing:**
1. Load situation context (filing type, company, existing evaluation)
2. Route to correct playbook via `routing_engine` (already exists)
3. Compose research prompt from playbook + situation + available public metadata
4. Execute AI call → produce structured research brief (14 sections — see §6)
5. Create `ResearchCase` row, status `brief_generated`
6. Create initial `ResearchTask` rows from "Missing Information" section

**Output:** `ResearchCase` with `brief` JSON, status `brief_generated`

**Observability:** `run_logger.start_run("situation_research_agent")` / `finish_run()` / `fail_run()`

**Guardrails:**
- One brief per `SpecialSituation` per day (rate limit — same pattern as v2 10/day cap)
- `save_to_db: false` flag for dry-run/preview mode
- Disclaimer appended at FastAPI layer

---

### 5.3 `historical_case_agent` _(new)_

**Trigger:** Manual only — Dani initiates a historical case study.

**Input:** Seed data for a known past special situation (company, event type, approximate date range, course chapter reference)

**Processing:**
1. Load seed data
2. Compose reconstruction prompt from methodology + seed
3. Execute AI call → produce timeline, entry window, sources used, lessons
4. Create `HistoricalCase` row, status `reconstructed`
5. Extract source intelligence signals → create `SourceIntelligenceSuggestion` records (for review)
6. Mark `lessons_extracted`

**Output:** `HistoricalCase` with structured reconstruction; source intelligence suggestions

**Observability:** Full `run_logger` wrapping

**Guardrails:**
- Manual trigger only
- No live data fetching — works from publicly available information and course methodology
- Does not reference raw course transcripts

---

### 5.4 `source_intelligence_agent` _(new)_

**Trigger:** Manual only — triggered after a ResearchCase is documented or a HistoricalCase is lessons-extracted.

**Input:** Completed `ResearchCase` or `HistoricalCase`; current `investment_sources` table state

**Processing:**
1. Analyse which sources contributed useful signal
2. Identify sources missing from current `investment_sources` table
3. Score existing sources based on case contribution
4. Produce `SourceIntelligenceSuggestion` list for Dani review

**Output:** Proposed additions/modifications to `investment_sources` — never auto-applied

**Observability:** Full `run_logger` wrapping

**Guardrails:**
- Proposals require explicit Dani approval before `POST /api/investment/sources` is called
- No auto-write to `investment_sources`

---

### 5.5 `publisher_agent` _(new)_

**Trigger:** Manual only — Dani requests a public article draft from a documented `ResearchCase`.

**Input:** `ResearchCase` (status `documented`), section 14 (Public Summary Draft) from research brief

**Processing:**
1. Extract the research brief's section 14 as base content
2. Compose editorial prompt — rewrite for public audience; educational tone; status labels only
3. Execute AI call → produce `PublicArticleDraft`
4. Create `PublicArticleDraft` row, status `draft`

**Output:** `PublicArticleDraft` — never published without explicit manual approval

**Observability:** Full `run_logger` wrapping

**Guardrails:**
- `published = false` at creation; never flipped by automation
- All buy/sell language stripped — replaced with status labels
- Disclaimer `"Este análisis es educativo. No es asesoramiento financiero."` included
- Manual approval required before status is set to `approved` → `published`

---

## 6. Research Brief Output Format (14 Sections)

The brief is stored as JSON in `ResearchCase.brief`. The FastAPI response serialises it for the frontend. All 14 sections are present; empty sections contain `null` or `[]`, not omitted.

```json
{
  "situation_id": "<uuid>",
  "generated_at": "<ISO timestamp>",
  "model_used": "<model id>",
  "playbook_version": "<routing type + version>",
  "disclaimer": "Este análisis es educativo. No es asesoramiento financiero.",
  "sections": {
    "1_executive_summary": { ... },
    "2_situation_type": { ... },
    "3_why_interesting": { ... },
    "4_course_methodology": { ... },
    "5_company_context": { ... },
    "6_board_management": { ... },
    "7_key_documents": { ... },
    "8_timeline": { ... },
    "9_risk_analysis": { ... },
    "10_verify_before_investing": { ... },
    "11_missing_information": { ... },
    "12_source_intelligence": { ... },
    "13_investment_readiness": { ... },
    "14_public_summary_draft": { ... }
  }
}
```

### Section Definitions

| # | Section | Content |
|---|---|---|
| 1 | **Executive Summary** | 3–5 sentence overview: what happened, what type, why notable, current status |
| 2 | **Situation Type** | Routing type (spin_off / merger_arbitrage / tender_offer / bankruptcy / proxy_fight / rights_offering / merger); confidence; filing type |
| 3 | **Why It May Be Interesting** | Thesis bullets: what the potential opportunity is; why the situation may be mispriced or overlooked; which course criteria it meets preliminarily |
| 4 | **Course Methodology Reference** | Primary playbook chapter(s); key checklist items from that chapter; what the playbook prescribes as next steps; `"Timestamp not available"` if no real timestamp found |
| 5 | **Company Context** | Name, ticker, sector, market cap range (if available), business description, recent financial condition signals |
| 6 | **Board / Management** | Key decision-makers identified in filing; any notable changes (new CEO, activist board seats, etc.) |
| 7 | **Key Documents** | List of SEC filing URLs; any other public documents referenced; document summaries |
| 8 | **Timeline** | Chronological list of known events: filing dates, announcement dates, regulatory deadlines, expected close (if stated) |
| 9 | **Risk Analysis** | Risk list: execution risk, regulatory risk, financing risk, management risk, market risk, course-specific risks for this situation type |
| 10 | **What To Verify Before Investing** | Checklist of open questions that require research before any investment decision; sourced from playbook checklist |
| 11 | **Missing Information / Manual Tasks for Dani** | Specific research actions Dani must perform: check company IR page, read proxy materials, verify ownership structure, find comparable transactions — each becomes a `ResearchTask` row |
| 12 | **Source Intelligence** | Which sources were useful in building this brief; which sources yielded no signal; new sources to consider; output feeds `source_intelligence_agent` |
| 13 | **Investment Readiness** | One of: `monitor` / `not actionable` / `needs more work` / `candidate for further research`; rationale; confidence level |
| 14 | **Public Summary Draft** | Editorial paragraph suitable for public publication; educational only; no buy/sell language; status label only; pending manual editorial review before use |

---

## 7. ResearchCase Lifecycle

```
detected
    │
    ▼  [situation_research_agent runs — manual trigger]
brief_generated
    │
    ▼  [Dani opens brief, starts working tasks]
under_investigation
    │
    ▼  [Dani marks all tasks resolved or deferred]
documented
    │
    ├──▶ archived   [no publishing interest]
    │
    └──▶ [publisher_agent runs — manual trigger]
         PublicArticleDraft: draft → approved → published
```

**Lifecycle rules:**
- Status advances forward only (no back-transitions, except `documented → archived`).
- `brief_generated` may not be skipped.
- A ResearchCase remains `under_investigation` as long as open `ResearchTask` rows exist with status `open`.
- `archived` and `published` are terminal states.
- Deleting a ResearchCase requires explicit action (not auto-cleaned).

---

## 8. HistoricalCase Lifecycle

```
seed
    │  [agent triggered manually by Dani]
    ▼
reconstructed
    │  [Dani reviews reconstruction, confirms accuracy]
    ▼
lessons_extracted
    │  [source_intelligence_agent runs — proposes sources]
    ▼
source_intel_applied
```

**Lifecycle rules:**
- Seeds may be created from: Dani manually, or from a `documented` ResearchCase that is retrospectively eligible for historical study.
- `reconstructed` requires an AI call; all others are status transitions.
- `lessons_extracted` triggers a source intelligence suggestion workflow — not auto-applied.
- `source_intel_applied` means proposed sources were reviewed and acted on (approved or explicitly rejected).

---

## 9. Source Intelligence Lifecycle

```
Active case learning:
  ResearchCase (documented)
      ↓
  source_intelligence_agent analyses which sources contributed
      ↓
  SourceIntelligenceSuggestion rows created (status: proposed)
      ↓
  Dani reviews each suggestion
      ↓
  Approved → POST /api/investment/sources (Dani runs or approves)
  Rejected → suggestion marked rejected

Historical case learning:
  HistoricalCase (lessons_extracted)
      ↓
  source_intelligence_agent analyses historical source landscape
      ↓
  Same suggestion → review → approved/rejected flow
```

**Rules:**
- `source_intelligence_agent` never writes directly to `investment_sources`.
- All writes to `investment_sources` go through `POST /api/investment/sources` with explicit approval.
- Proposals include: source type, URL or description, rationale, case reference, suggested priority.
- Proposals expire (status `expired`) after 30 days if not acted on.

---

## 10. Publishing Workflow

```
ResearchCase (documented)
    │
    ▼  [Dani requests article draft — manual]
publisher_agent runs
    │
    ▼
PublicArticleDraft (status: draft)
    │
    ▼  [Dani reviews draft in Mission Control]
Editorial review
    │
    ├──▶ rejected → draft archived
    │
    └──▶ approved → status: approved
                     │
                     ▼  [Dani initiates publish — manual]
                     published (external publication step — outside platform scope for now)
```

**Publishing guardrails (non-negotiable):**
- `published = false` at creation; never flipped by automation.
- No direct buy/sell language. All investment readiness expressed as status labels.
- Disclaimer `"Este análisis es educativo. No es asesoramiento financiero."` present in every draft.
- Source attribution must not expose: private credentials, internal system details, Tailscale addresses, VPS service names.
- Public content scope for Phase 1: educational analysis only. No portfolio recommendations.

---

## 11. Draft Data Model

These are design-time specifications. **No migration or implementation in this sprint.**

All models are SQLAlchemy / Pydantic, following existing conventions in `backend/models/`.

---

### `ResearchCase`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `situation_id` | UUID FK → `special_situations.id` | Required |
| `status` | Enum | `detected` / `brief_generated` / `under_investigation` / `documented` / `archived` / `published` |
| `brief` | JSONB | Full 14-section research brief |
| `playbook_version` | str | Routing type + version used |
| `model_used` | str | AI model that generated brief |
| `run_id` | UUID FK → `agent_runs.id` | Observability link |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |
| `notes` | Text | Dani's free-form notes |

---

### `ResearchDocument`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `research_case_id` | UUID FK → `research_cases.id` | Required |
| `doc_type` | str | `sec_filing` / `press_release` / `ir_page` / `presentation` / `news` / `other` |
| `url` | str | Public URL only — no private links |
| `title` | str | |
| `retrieved_at` | DateTime | |
| `summary` | Text | AI-generated or manual summary |

---

### `ResearchSource`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `research_case_id` | UUID FK → `research_cases.id` | |
| `historical_case_id` | UUID FK → `historical_cases.id` | Nullable — one or the other |
| `source_name` | str | Human-readable label |
| `source_url` | str | Nullable |
| `signal_quality` | Enum | `high` / `medium` / `low` / `no_signal` |
| `notes` | Text | What signal this source yielded |

_These are ephemeral records per research session. They feed `source_intelligence_agent`. They are not the same as `investment_sources` DB rows._

---

### `ResearchTask`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `research_case_id` | UUID FK → `research_cases.id` | Required |
| `description` | Text | Generated from brief section 11 |
| `status` | Enum | `open` / `done` / `deferred` / `cancelled` |
| `created_at` | DateTime | |
| `resolved_at` | DateTime | Nullable |
| `notes` | Text | Dani's resolution notes |

---

### `HistoricalCase`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `company_name` | str | |
| `situation_type` | str | Routing type |
| `event_date_approx` | Date | Approximate date of the event |
| `seed_notes` | Text | Dani's seed description |
| `reconstruction` | JSONB | Agent-produced reconstruction (timeline, entry window, lessons) |
| `status` | Enum | `seed` / `reconstructed` / `lessons_extracted` / `source_intel_applied` |
| `linked_situation_id` | UUID FK → `special_situations.id` | Nullable — if active case was later studied |
| `run_id` | UUID FK → `agent_runs.id` | |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

---

### `PublicArticleDraft`

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `research_case_id` | UUID FK → `research_cases.id` | Required |
| `status` | Enum | `draft` / `approved` / `published` / `archived` |
| `content` | Text | Full article draft |
| `readiness_label` | Enum | `monitor` / `not_actionable` / `needs_more_work` / `candidate` |
| `disclaimer_present` | bool | Must be `true` — validation enforced at API layer |
| `buy_sell_language_check` | bool | Automated flag; `true` = no buy/sell language detected |
| `created_at` | DateTime | |
| `approved_at` | DateTime | Nullable |
| `published_at` | DateTime | Nullable |
| `run_id` | UUID FK → `agent_runs.id` | |

---

## 12. API / UI Implications (High Level)

**New API endpoints needed (Phase 2 implementation, not this sprint):**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/investment/research-cases` | Create ResearchCase (trigger `situation_research_agent`) |
| `GET` | `/api/investment/research-cases` | List all ResearchCases |
| `GET` | `/api/investment/research-cases/{id}` | Get single ResearchCase with full brief |
| `PATCH` | `/api/investment/research-cases/{id}` | Update status, notes |
| `GET` | `/api/investment/research-cases/{id}/tasks` | List ResearchTasks |
| `PATCH` | `/api/investment/research-tasks/{id}` | Update task status/notes |
| `POST` | `/api/investment/historical-cases` | Seed a HistoricalCase |
| `POST` | `/api/investment/historical-cases/{id}/reconstruct` | Trigger `historical_case_agent` |
| `GET` | `/api/investment/historical-cases` | List HistoricalCases |
| `POST` | `/api/investment/source-intelligence/analyse` | Trigger `source_intelligence_agent` on a case |
| `GET` | `/api/investment/source-intelligence/suggestions` | List pending suggestions |
| `PATCH` | `/api/investment/source-intelligence/suggestions/{id}` | Approve or reject suggestion |
| `POST` | `/api/investment/public-drafts` | Trigger `publisher_agent` on a documented ResearchCase |
| `GET` | `/api/investment/public-drafts` | List PublicArticleDrafts |
| `PATCH` | `/api/investment/public-drafts/{id}` | Update status (approve / archive) |

**UI pages needed (Phase 2, not this sprint):**

- `/investment/research-cases` — list view, filter by status
- `/investment/research-cases/[id]` — detail: full brief, task list, documents, notes
- `/investment/historical-cases` — list + seed form
- `/investment/historical-cases/[id]` — reconstruction view
- `/investment/source-intelligence` — suggestion review queue
- `/investment/public-drafts` — editorial review queue

**Existing pages unchanged:** Evaluations Queue, Evaluation Detail, Watchlist, Sources, Radar Status.

---

## 13. Safety and Compliance Guardrails

All of the following apply to every component of the Investment Research Platform and are non-negotiable.

| Guardrail | Where enforced |
|---|---|
| `"Este análisis es educativo. No es asesoramiento financiero."` | FastAPI response layer — appended automatically |
| Status labels only in public output (`monitor` / `not actionable` / `needs more work` / `candidate`) | `publisher_agent` prompt + `buy_sell_language_check` flag |
| No buy/sell language in any output, private or public | Evaluator + publisher prompts |
| No auto-publish | `published = false` at creation; never flipped by automation |
| No auto-write to `investment_sources` | `source_intelligence_agent` produces proposals only |
| All publishing requires explicit manual approval | `PublicArticleDraft.status` gating — API checks `approved_at` before allowing `published_at` |
| No secrets, IPs, tokens, or VPS details in any content or document | Structural rule (D006) |
| No raw course content in any DB field or API response | Structural rule (D007) — `course_index/` is gitignored; prompts reference playbooks only |
| Observability wraps every AI call | `run_logger.start_run()` / `finish_run()` / `fail_run()` — never breaks business logic |
| Rate limiting on agent triggers | Pattern: daily caps per situation (same as v2 10/day pattern) |

---

## 14. Phased Implementation Roadmap

### Phase 1 — Foundation (next sprint block)

1. **Sprint 17 prerequisite:** Wire scanner to read `investment_sources` DB table — makes enable/disable toggles operational. (Already identified as Sprint 17 gap in `PROJECT_STATE.md`.)
2. **Data model implementation:** Create `ResearchCase`, `ResearchTask`, `ResearchDocument`, `ResearchSource`, `HistoricalCase`, `PublicArticleDraft` SQLAlchemy models + Pydantic schemas.
3. **Alembic migration:** One migration for all new tables. Run on VPS after Dani approval.
4. **`situation_research_agent` v1:** Implement endpoint `POST /api/investment/research-cases`. Reuse `routing_engine` + v2 evaluator prompt as base. Output structured JSON brief. Full observability.
5. **Research Case detail page:** `/investment/research-cases/[id]` — read-only view of brief + task list. Connect from existing Evaluation Detail page.

### Phase 2 — Investigation workflow

6. **Task management:** ResearchTask CRUD; mark done/deferred from UI.
7. **Research Case list page:** `/investment/research-cases` — filter by status.
8. **Document attachment:** Allow Dani to attach public URLs to a case as `ResearchDocument` rows.
9. **Notes save:** `PATCH /api/investment/research-cases/{id}` with `notes` field.

### Phase 3 — Historical learning

10. **`historical_case_agent` v1:** Seed form, reconstruction endpoint, lessons extraction.
11. **Historical Case list + detail pages.**
12. **`source_intelligence_agent` v1:** Analysis endpoint; suggestions list and review UI.

### Phase 4 — Publishing

13. **`publisher_agent` v1:** Article draft generation; editorial review queue.
14. **PublicArticleDraft approval workflow in UI.**
15. **External publication mechanism** (TBD — blog, Substack, GitHub Pages, or other — architecture decision deferred).

### Phase 5 — Source depth

16. **Course Deep Mining sprint:** Extract all sources, people, newsletters, blogs, accounts, documents, and court sources mentioned in the course. Seed data for `investment_sources` + `HistoricalCase` tables. (No raw transcripts committed.)
17. **Source coverage expansion:** New source adapters beyond SEC EDGAR; aligned with `source_map.md`.

---

## 15. Open Questions

| # | Question | Impact | Owner |
|---|---|---|---|
| OQ1 | What is the target publishing platform? (Substack, GitHub Pages, own blog, other) | Affects `publisher_agent` output format and `PublicArticleDraft` structure | Dani |
| OQ2 | Should `ResearchCase` replace or augment the existing `special_situations` detail page? Or be a separate route? | Affects frontend routing design | Dani |
| OQ3 | Should `situation_research_agent` reuse the v2 evaluator prompt as a base, or have its own dedicated prompt? | Affects prompt design sprint | Design |
| OQ4 | What is the rate limit for `situation_research_agent`? (v2 uses 10/day) | Affects cost and API design | Dani |
| OQ5 | Should `HistoricalCase` seeds come only from Dani manually, or can they be bootstrapped from completed `ResearchCase` rows automatically? | Affects `historical_case_agent` trigger design | Dani |
| OQ6 | Is the 14-section brief the correct granularity, or should some sections be collapsible/optional based on situation type? | Affects prompt design and frontend rendering | Dani |
| OQ7 | Should `PublicArticleDraft` include a title and tags for SEO purposes? | Affects `PublicArticleDraft` model | Dani |
| OQ8 | Which historical cases should be seeded first? (Course mentions specific examples — extract in Course Deep Mining sprint) | Affects Phase 3 kickoff | Dani |
| OQ9 | Should `source_intelligence_agent` run automatically after a case is documented, or always require a manual trigger? | Affects automation vs. control tradeoff | Dani |
| OQ10 | What happens to a `ResearchCase` if the underlying `SpecialSituation` is archived or ignored in the evaluations queue? | Affects lifecycle and orphan cleanup | Design |
