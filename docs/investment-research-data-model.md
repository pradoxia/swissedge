# SwissEdge — Investment Research Platform: Phase 1 Data Model

**Status:** Technical design — documentation only. No implementation, migration, endpoint, or cron changes.
**Sprint:** Data Model Design (2026-05-01)
**Prerequisite reading:** `docs/investment-research-platform-redesign.md`, `docs/decisions.md`
**Existing models inspected:** `backend/models/investment.py`, `backend/models/observability.py`

---

## 0. Canonical Location Note

All references to `PROJECT_STATE.md` in this document mean `docs/PROJECT_STATE.md`. There is no root-level copy. The canonical file lives at `docs/PROJECT_STATE.md`.

---

## 1. Existing Model Reference

Before defining new models, the key existing fields that new models relate to:

### `special_situations` (existing, read-only from research perspective)

| Field | Type | Relevant to research? |
|---|---|---|
| `id` | UUID PK | FK target for `ResearchCase`, `HistoricalCase` |
| `situation_type` | String(100) | Used for playbook routing in brief generation |
| `company_name` | Text | Surfaced in brief §5 |
| `ticker` | String(20) | Surfaced in brief §5 |
| `filing_type` | String(50) | Surfaced in brief §2 |
| `filing_url` | Text | Surfaced in brief §7 (public URL only) |
| `detected_at` | DateTime | Timeline anchor in brief §8 |
| `status` | String(50) | Lifecycle state (`detected`, `reviewing`, `watchlist`, `ignored`, `archived`) |
| `evaluation` | JSONB | v1/v2 evaluator output — input to brief generation |
| `course_chapter` | Integer | Course reference — input to brief §4 |
| `notes` | Text | Dani's existing notes |

**Design rule:** `ResearchCase` is linked to `SpecialSituation` via FK. Research cases augment situations — they do not replace or duplicate `special_situations` rows. A `SpecialSituation` can have zero or one `ResearchCase` (one-to-one for Phase 1; revisit if multiple brief iterations are needed in Phase 2).

### `investment_sources` (existing)

| Field | Type | Relevant to source intelligence? |
|---|---|---|
| `id` | UUID PK | FK target for `SourceIntelligenceSuggestion.suggested_source_id` |
| `name` | Text | Surfaced in brief §12 |
| `url` | Text | Surfaced in brief §12 |
| `source_type` | String(50) | Category |
| `active` | Boolean | Enable/disable toggle |
| `priority` | Integer | Used to rank sources |
| `last_success` | DateTime | Freshness indicator |
| `last_error` | Text | Health indicator |

**Design rule:** `source_intelligence_agent` never writes to `investment_sources` directly. It produces `SourceIntelligenceSuggestion` rows. Only after explicit Dani approval does the normal `POST /api/investment/sources` path execute.

### `agent_runs` (existing)

| Field | Type | How new agents use it |
|---|---|---|
| `id` | UUID PK | FK target for `run_id` on all new models |
| `agent_name` | String(100) | `situation_research_agent`, `historical_case_agent`, etc. |
| `status` | String(20) | `started` / `finished` / `failed` |
| `estimated_cost` | Numeric | Tracked per AI call |
| `input_tokens` / `output_tokens` | Integer | Per-call token counts |
| `human_approval_required` | Boolean | Set `true` for all publishing actions |

**Design rule:** Every new agent call creates an `agent_runs` row via `run_logger.start_run()`. The `run_id` FK on new models links back to the triggering run. This is non-negotiable (D004).

### `ai_usage` (existing)

| Field | Type | How new agents use it |
|---|---|---|
| `run_id` | UUID FK → `agent_runs.id` | Links AI usage to the run that triggered it |
| `agent_name` | String(100) | One row per AI call per agent |
| `model` | String(100) | Model used |
| `input_tokens` / `output_tokens` / `estimated_cost` | — | Cost tracking |

**Design rule:** Every `complete_with_usage()` call logs to `ai_usage`. No exceptions.

---

## 2. New Models

---

### 2.1 `ResearchCase`

**Table name:** `research_cases`

**Purpose:** Central research artifact for a detected `SpecialSituation`. Holds the structured 14-section research brief, lifecycle status, observability link, and Dani's working notes. One ResearchCase per SpecialSituation (Phase 1).

**Relationship to existing entities:**
- `situation_id` → `special_situations.id` (required FK, cascade-on-delete: `SET NULL` — research case is preserved even if the situation is archived/deleted, to avoid losing research work)
- `run_id` → `agent_runs.id` (FK, `ondelete=SET NULL` — observability link; nullable to allow manual creation without an AI run)

**Lifecycle / status values:**

| Status | Who sets it | Meaning |
|---|---|---|
| `detected` | Auto — created when SpecialSituation row exists and Dani requests a brief | Situation known; brief not yet generated |
| `brief_generated` | `situation_research_agent` on completion | Brief produced; not yet reviewed |
| `under_investigation` | Dani manually (or auto when a ResearchTask is opened) | Dani is actively working the case |
| `documented` | Dani manually — after all open tasks resolved/deferred | Investigation complete |
| `archived` | Dani manually | No publishing interest; terminal |
| `published` | Set only after a linked `PublicArticleDraft` reaches `published` | Terminal — at least one article published |

**Status transition rules:**
- Forward-only, except `documented → archived`
- `brief_generated` cannot be skipped
- `documented → published` only via `PublicArticleDraft` approval path; not a direct PATCH

**Fields:**

| Column | Type | Required | Manual/Generated | Private/Publishable | Notes |
|---|---|---|---|---|---|
| `id` | UUID PK | — | Generated | Private | `default=uuid.uuid4` |
| `situation_id` | UUID FK → `special_situations.id` | Yes | Generated | Private | `nullable=True` with `SET NULL` on delete |
| `status` | String(50) | Yes | Both | Private | Default: `detected` |
| `brief` | JSONB | No | Generated | Both | Full 14-section JSON; `null` until agent runs. Section 14 contains publishable draft text. |
| `brief_version` | String(20) | No | Generated | Private | e.g. `v1.0` — allows future brief re-generation without losing prior |
| `playbook_version` | String(100) | No | Generated | Private | Routing type + playbook version used (e.g. `spin_off:v1.1`) |
| `model_used` | String(100) | No | Generated | Private | AI model that generated brief |
| `run_id` | UUID FK → `agent_runs.id` | No | Generated | Private | `ondelete=SET NULL`; nullable |
| `notes` | Text | No | Manual | Private | Dani's free-form working notes |
| `disclaimer` | Text | Yes | Generated | Both | Must equal `"Este análisis es educativo. No es asesoramiento financiero."` — validated at API layer |
| `investment_readiness` | String(50) | No | Generated | Both | One of: `monitor` / `not_actionable` / `needs_more_work` / `candidate` — mirrors brief §13; stored denormalised for fast filtering |
| `created_at` | DateTime(tz) | — | Generated | Private | `default=_now` |
| `updated_at` | DateTime(tz) | — | Generated | Private | `onupdate=_now` |

**Relationships (SQLAlchemy):**
- `situation` → `SpecialSituation` (many-to-one)
- `tasks` → `List[ResearchTask]` (one-to-many, `cascade="all, delete-orphan"`)
- `documents` → `List[ResearchDocument]` (one-to-many, `cascade="all, delete-orphan"`)
- `sources` → `List[ResearchSource]` (one-to-many, `cascade="all, delete-orphan"`)
- `public_drafts` → `List[PublicArticleDraft]` (one-to-many)

**Suggested indexes:**
- `idx_research_cases_situation_id` on `situation_id` — most common join
- `idx_research_cases_status` on `status` — list page filtering
- `idx_research_cases_investment_readiness` on `investment_readiness` — filter by readiness label

**Validation rules:**
- `disclaimer` must equal the exact canonical string at write time (API-layer check, not DB constraint)
- `investment_readiness` must be one of the four allowed labels if present; reject any buy/sell language
- `status` must be a member of the valid enum; reject unknown values
- `brief` must be valid JSON if present; structure validated against brief schema on write
- `situation_id` must reference an existing `special_situations.id`; 404 if not found

**How research cases are created from detected SpecialSituation rows:**
1. Dani opens Evaluation Detail page for a `SpecialSituation`
2. Clicks "Generate Research Brief" — calls `POST /api/investment/research-cases` with `{ situation_id, save_to_db: true }`
3. FastAPI creates an `agent_runs` row, runs `situation_research_agent`
4. Agent loads `SpecialSituation`, routes to playbook via `routing_engine`, calls AI, receives 14-section JSON
5. FastAPI creates `ResearchCase` row (status `brief_generated`), creates `ResearchTask` rows from brief §11
6. Returns `ResearchCase` + tasks to frontend

**Disclaimer placement:** The `disclaimer` field stores the canonical string. The brief JSON `sections.1_executive_summary` must also embed it. FastAPI asserts both on write.

**Open questions:**
- OQ-RC1: Should there be exactly one ResearchCase per SpecialSituation, or allow multiple iterations (e.g. re-run brief after new filings)? Phase 1 assumes one; Phase 2 may need `version` + soft-archive of prior brief.
- OQ-RC2: If `situation_id` is `SET NULL` on delete, should the ResearchCase still be visible in the list? Or auto-archived?
- OQ-RC3: Should `investment_readiness` be writable by Dani (override the agent's label), or agent-only?

---

### 2.2 `ResearchDocument`

**Table name:** `research_documents`

**Purpose:** Individual public-URL documents attached to a research case. Captures filing URLs, press releases, IR pages, and presentations that Dani or the agent used during investigation. Documents are evidence — not generated content.

**Relationship to existing entities:**
- `research_case_id` → `research_cases.id` (required FK, `cascade="all, delete-orphan"`)

**Fields:**

| Column | Type | Required | Manual/Generated | Private/Publishable | Notes |
|---|---|---|---|---|---|
| `id` | UUID PK | — | Generated | Private | |
| `research_case_id` | UUID FK → `research_cases.id` | Yes | Generated | Private | |
| `doc_type` | String(50) | Yes | Both | Private | Enum: `sec_filing` / `press_release` / `ir_page` / `presentation` / `news` / `other` |
| `url` | Text | Yes | Both | Publishable | Public URL only — never a private link, VPS path, or credential-bearing URL |
| `title` | Text | No | Both | Publishable | Document title or descriptive label |
| `retrieved_at` | DateTime(tz) | No | Generated | Private | When the document was first accessed/linked |
| `summary` | Text | No | Both | Both | AI-generated or Dani-written summary of document content |
| `added_by` | String(50) | No | Generated | Private | `agent` or `dani` — who attached this document |
| `created_at` | DateTime(tz) | — | Generated | Private | `default=_now` |

**Suggested indexes:**
- `idx_research_documents_case_id` on `research_case_id`
- `idx_research_documents_doc_type` on `doc_type` — filter by type on detail page

**Validation rules:**
- `url` must be an HTTP/HTTPS URL; no file paths, no internal addresses, no Tailscale URLs
- `doc_type` must be one of the allowed enum values
- `summary` must not contain buy/sell language; soft-check at API layer (log warning, do not hard-reject)
- Duplicate `url` within the same `research_case_id` should be prevented or warned; not a hard DB constraint but an API-layer check

**Open questions:**
- OQ-RD1: Should documents be shared across cases (if the same SEC filing appears in two research cases), or is per-case duplication acceptable? Phase 1: per-case duplication is fine. Phase 2 could deduplicate by URL.
- OQ-RD2: Should the API auto-fetch and summarise a URL when attached, or is summary always manual/agent-provided?

---

### 2.3 `ResearchSource`

**Table name:** `research_sources`

**Purpose:** Ephemeral signal-quality record for a specific source as experienced during a research session. These are per-case observations, not the global `investment_sources` registry. They feed the `source_intelligence_agent` to propose additions to the registry. A `ResearchSource` row says "in the context of this case, this source yielded X quality signal."

**Relationship to existing entities:**
- `research_case_id` → `research_cases.id` (nullable FK — source can be attached to either a ResearchCase or a HistoricalCase)
- `historical_case_id` → `historical_cases.id` (nullable FK — must have exactly one of the two set)
- `investment_source_id` → `investment_sources.id` (nullable FK — set if this source is already in the registry; null if it is a newly discovered source not yet in the registry)

**Fields:**

| Column | Type | Required | Manual/Generated | Private/Publishable | Notes |
|---|---|---|---|---|---|
| `id` | UUID PK | — | Generated | Private | |
| `research_case_id` | UUID FK → `research_cases.id` | No* | Both | Private | *Exactly one of `research_case_id` or `historical_case_id` must be set |
| `historical_case_id` | UUID FK → `historical_cases.id` | No* | Both | Private | |
| `investment_source_id` | UUID FK → `investment_sources.id` | No | Both | Private | `ondelete=SET NULL`; null = newly discovered source |
| `source_name` | Text | Yes | Both | Publishable | Human-readable label (e.g. "SEC EDGAR EFTS", "Company IR page") |
| `source_url` | Text | No | Both | Publishable | Public URL; same validation as `ResearchDocument.url` |
| `signal_quality` | String(20) | Yes | Both | Private | Enum: `high` / `medium` / `low` / `no_signal` |
| `notes` | Text | No | Both | Private | What signal this source yielded; not buy/sell language |
| `created_at` | DateTime(tz) | — | Generated | Private | |

**Suggested indexes:**
- `idx_research_sources_case_id` on `research_case_id`
- `idx_research_sources_historical_case_id` on `historical_case_id`
- `idx_research_sources_investment_source_id` on `investment_source_id` — correlate with registry
- `idx_research_sources_signal_quality` on `signal_quality` — filter high-signal sources

**Validation rules:**
- Exactly one of `research_case_id` or `historical_case_id` must be non-null (API-layer check)
- `signal_quality` must be one of the four allowed values
- `source_url` if present must be HTTP/HTTPS; same rules as `ResearchDocument.url`
- `notes` must not expose internal credentials, IPs, or service names

**How this feeds source intelligence:**
After a `ResearchCase` reaches `documented`, `source_intelligence_agent` reads all `ResearchSource` rows for that case, groups by `signal_quality`, and proposes: add `high`-signal sources that are not in `investment_sources`; deprioritise `no_signal` sources already in the registry.

**Open questions:**
- OQ-RS1: DB constraint for the "exactly one of two FKs" rule — PostgreSQL `CHECK` constraint or API-only? Recommendation: API-layer check in Phase 1; add DB constraint in Phase 2.
- OQ-RS2: Should `ResearchSource` rows survive `ResearchCase` deletion? Recommendation: `CASCADE DELETE` — they are meaningful only in context of their case.

---

### 2.4 `ResearchTask`

**Table name:** `research_tasks`

**Purpose:** A discrete, actionable research step that Dani must complete before a case can be marked `documented`. Tasks are generated from brief §11 ("Missing Information / Manual Tasks for Dani") and can also be added manually. A `ResearchCase` cannot advance to `documented` while any task is `open`.

**Relationship to existing entities:**
- `research_case_id` → `research_cases.id` (required FK, `cascade="all, delete-orphan"`)

**Fields:**

| Column | Type | Required | Manual/Generated | Private/Publishable | Notes |
|---|---|---|---|---|---|
| `id` | UUID PK | — | Generated | Private | |
| `research_case_id` | UUID FK → `research_cases.id` | Yes | Generated | Private | |
| `description` | Text | Yes | Both | Private | Task description; generated from brief §11 or Dani-written |
| `status` | String(20) | Yes | Both | Private | Enum: `open` / `done` / `deferred` / `cancelled` |
| `priority` | Integer | No | Both | Private | 1 (highest) – 5 (lowest); default 3 |
| `source` | String(20) | No | Generated | Private | `agent` (auto-created from brief) or `manual` (Dani-added) |
| `notes` | Text | No | Manual | Private | Dani's resolution notes, findings, or reasons for deferral |
| `created_at` | DateTime(tz) | — | Generated | Private | |
| `resolved_at` | DateTime(tz) | No | Generated | Private | Set when status changes to `done`, `deferred`, or `cancelled` |

**Suggested indexes:**
- `idx_research_tasks_case_id` on `research_case_id`
- `idx_research_tasks_status` on `status` — count open tasks per case efficiently

**Validation rules:**
- `status` must be one of the four allowed values
- `priority` must be integer 1–5 if provided
- Transition to `documented` on the parent `ResearchCase` is blocked unless zero `open` tasks remain (API-layer check)
- `description` must not be empty

**Open questions:**
- OQ-RT1: Should tasks be orderable (drag-to-reorder)? Phase 1: ordered by `priority` then `created_at` is sufficient.
- OQ-RT2: Should completing the last `open` task auto-advance `ResearchCase` to `documented`? Or always require explicit Dani action? Recommendation: explicit action — avoids surprising status changes.

---

### 2.5 `HistoricalCase`

**Table name:** `historical_cases`

**Purpose:** A past corporate special situation reconstructed for learning purposes. Captures what the situation was, when it was visible, what the entry window was, and lessons extracted. Feeds source intelligence. Can be seeded from Dani's knowledge of past situations or elevated from a completed `ResearchCase`.

**Relationship to existing entities:**
- `linked_situation_id` → `special_situations.id` (nullable FK, `ondelete=SET NULL`) — set if this historical case corresponds to a `SpecialSituation` row that was later studied; null for cases pre-dating the scanner or sourced from Dani's memory
- `run_id` → `agent_runs.id` (nullable FK, `ondelete=SET NULL`) — the reconstruction run

**Lifecycle / status values:**

| Status | Who sets it | Meaning |
|---|---|---|
| `seed` | Dani manually | Basic facts entered; reconstruction not yet run |
| `reconstructed` | `historical_case_agent` on completion | Agent has produced timeline, entry window, and lessons |
| `lessons_extracted` | Dani manually (confirms reconstruction accuracy) | Dani confirms the reconstruction; lessons are valid |
| `source_intel_applied` | `source_intelligence_agent` post-review | Source suggestions from this case were reviewed and acted on |

**Fields:**

| Column | Type | Required | Manual/Generated | Private/Publishable | Notes |
|---|---|---|---|---|---|
| `id` | UUID PK | — | Generated | Private | |
| `company_name` | Text | Yes | Manual | Publishable | Name of the company involved |
| `situation_type` | String(100) | Yes | Manual | Publishable | Routing type (e.g. `spin_off`, `tender_offer`) |
| `event_date_approx` | Date | No | Manual | Publishable | Approximate date the situation became public |
| `seed_notes` | Text | No | Manual | Private | Dani's initial description and context |
| `course_chapter_ref` | Integer | No | Manual | Private | Primary course chapter that covers this situation type |
| `reconstruction` | JSONB | No | Generated | Both | Agent-produced: `{ timeline: [...], entry_window: {...}, sources_used: [...], lessons: [...], what_we_missed: str }` |
| `status` | String(50) | Yes | Both | Private | Default: `seed` |
| `linked_situation_id` | UUID FK → `special_situations.id` | No | Manual | Private | Nullable; `ondelete=SET NULL` |
| `run_id` | UUID FK → `agent_runs.id` | No | Generated | Private | Nullable; `ondelete=SET NULL` |
| `disclaimer` | Text | Yes | Generated | Both | Must equal canonical disclaimer string if any published content is derived from this case |
| `created_at` | DateTime(tz) | — | Generated | Private | |
| `updated_at` | DateTime(tz) | — | Generated | Private | |

**Relationships (SQLAlchemy):**
- `linked_situation` → `SpecialSituation` (many-to-one, optional)
- `sources` → `List[ResearchSource]` (one-to-many, `cascade="all, delete-orphan"`)

**Suggested indexes:**
- `idx_historical_cases_status` on `status`
- `idx_historical_cases_situation_type` on `situation_type` — group by type for pattern analysis
- `idx_historical_cases_linked_situation_id` on `linked_situation_id`

**Validation rules:**
- `situation_type` must be one of the 7 routing types defined in `course_index/playbooks/`
- `reconstruction` JSONB must conform to the defined structure: `timeline`, `entry_window`, `sources_used`, `lessons`, `what_we_missed` — validated at API layer on write
- `status` must be a member of the valid enum; forward-only transitions enforced at API layer
- `disclaimer` must equal canonical string if `reconstruction` is present

**How historical cases feed source intelligence:**
After `lessons_extracted`, `source_intelligence_agent` reads `reconstruction.sources_used`, compares against `investment_sources`, and proposes additions. It also reads `reconstruction.lessons` for source-related insights. Output: `SourceIntelligenceSuggestion` rows.

**Open questions:**
- OQ-HC1: Should HistoricalCase have its own `ResearchDocument` table, or reuse the same `research_documents` table? Recommendation: reuse `research_documents` by adding a nullable `historical_case_id` FK column — avoids table proliferation.
- OQ-HC2: Who can advance status from `lessons_extracted` to `source_intel_applied`? Recommendation: only after Dani explicitly approves or rejects all linked `SourceIntelligenceSuggestion` rows.

---

### 2.6 `PublicArticleDraft`

**Purpose:** An editorially prepared article suitable for external publication, derived from a `documented` `ResearchCase`. Never published automatically — requires explicit Dani approval at every step.

**Table name:** `public_article_drafts`

**Relationship to existing entities:**
- `research_case_id` → `research_cases.id` (required FK; `ondelete=RESTRICT` — cannot delete a ResearchCase while a draft exists)
- `run_id` → `agent_runs.id` (nullable FK, `ondelete=SET NULL`) — the `publisher_agent` run that generated the draft

**Lifecycle / status values:**

| Status | Who sets it | Meaning |
|---|---|---|
| `draft` | `publisher_agent` | AI-generated draft; not yet reviewed |
| `approved` | Dani manually — explicit PATCH | Draft reviewed and approved for publication |
| `published` | Dani manually — explicit PATCH after `approved` | Article marked as externally published (the actual publishing step is external to the platform in Phase 1) |
| `archived` | Dani manually | Draft rejected or superseded; terminal |

**Status transition rules:**
- `draft → approved` only; no skipping directly to `published`
- `approved → published` only; cannot revert to `draft`
- `approved → archived` allowed (rejected after approval)
- `published` is terminal; no further transitions
- `agent_runs.human_approval_required` is set `true` for any run that generates a draft — audit trail

**Fields:**

| Column | Type | Required | Manual/Generated | Private/Publishable | Notes |
|---|---|---|---|---|---|
| `id` | UUID PK | — | Generated | Private | |
| `research_case_id` | UUID FK → `research_cases.id` | Yes | Generated | Private | `ondelete=RESTRICT` |
| `status` | String(20) | Yes | Both | Private | Default: `draft` |
| `title` | Text | No | Both | Publishable | Article title; generated by agent or Dani-edited |
| `content` | Text | Yes | Generated | Publishable | Full article text; no buy/sell language; educational only |
| `readiness_label` | String(50) | Yes | Generated | Publishable | One of: `monitor` / `not_actionable` / `needs_more_work` / `candidate` |
| `disclaimer` | Text | Yes | Generated | Publishable | Must equal `"Este análisis es educativo. No es asesoramiento financiero."` — enforced at API layer |
| `disclaimer_present` | Boolean | Yes | Generated | Private | `true` = disclaimer confirmed present in `content`; validated on write |
| `buy_sell_language_check` | Boolean | Yes | Generated | Private | `true` = no buy/sell language detected in `content`; validated on write; `false` blocks `approved` transition |
| `tags` | JSONB | No | Both | Publishable | Array of string tags; for SEO/categorisation (Phase 2) |
| `run_id` | UUID FK → `agent_runs.id` | No | Generated | Private | `ondelete=SET NULL` |
| `created_at` | DateTime(tz) | — | Generated | Private | |
| `approved_at` | DateTime(tz) | No | Generated | Private | Set when status transitions to `approved` |
| `published_at` | DateTime(tz) | No | Generated | Private | Set when status transitions to `published` |

**Suggested indexes:**
- `idx_public_article_drafts_case_id` on `research_case_id`
- `idx_public_article_drafts_status` on `status` — editorial queue filtering
- `idx_public_article_drafts_readiness_label` on `readiness_label`

**Validation rules (API-layer enforcement):**
- `disclaimer` must equal canonical string on every write
- `disclaimer_present` must be `true` before status can advance to `approved`
- `buy_sell_language_check` must be `true` before status can advance to `approved` — if `false`, surface the detected phrases to Dani
- `readiness_label` must be one of the four valid labels; reject anything else
- `content` must be non-empty
- `published_at` may only be set if `approved_at` is already set
- `approved_at` may only be set if `status` is transitioning to `approved`

**How public article drafts are created (never automatically):**
1. `ResearchCase` must be in `documented` status
2. Dani explicitly requests a draft via `POST /api/investment/public-drafts` with `{ research_case_id }`
3. `publisher_agent` runs — reads brief §14 (Public Summary Draft), rewrites for public audience
4. Agent checks for buy/sell language, validates disclaimer presence
5. Creates `PublicArticleDraft` row, status `draft`, `buy_sell_language_check` set
6. `agent_runs.human_approval_required = true` is set on the triggering run
7. No `published = true` or `published_at` at creation — ever

**Open questions:**
- OQ-PAD1: Should `content` be Markdown or HTML? Recommendation: Markdown — easier to review and portable across publishing platforms.
- OQ-PAD2: One draft per ResearchCase, or allow multiple drafts (e.g. retry after revision)? Phase 1: allow multiple drafts per case; UI shows list sorted by `created_at`; only one can be `approved` at a time (enforce at API layer).
- OQ-PAD3: External publishing mechanism (Substack, GitHub Pages, own blog) is deferred — see OQ1 in `investment-research-platform-redesign.md`. Phase 1 only sets `published_at`; the actual external publication is Dani's manual action outside the platform.

---

### 2.7 `SourceIntelligenceSuggestion` _(not in original redesign doc — added here)_

**Table name:** `source_intelligence_suggestions`

**Purpose:** A proposal from `source_intelligence_agent` to add or modify a row in `investment_sources`. Never auto-applied. Dani reviews and approves or rejects each suggestion.

**Note:** The redesign doc described this entity conceptually but did not name it as a model. It is named and specified here for completeness. This is new relative to the redesign doc.

**Relationship to existing entities:**
- `research_case_id` → `research_cases.id` (nullable FK — the active case that generated this suggestion)
- `historical_case_id` → `historical_cases.id` (nullable FK — the historical case that generated this suggestion)
- `existing_source_id` → `investment_sources.id` (nullable FK, `ondelete=SET NULL`) — set if this suggestion modifies an existing source; null if it proposes a new one
- `run_id` → `agent_runs.id` (nullable FK, `ondelete=SET NULL`)

**Fields:**

| Column | Type | Required | Manual/Generated | Private/Publishable | Notes |
|---|---|---|---|---|---|
| `id` | UUID PK | — | Generated | Private | |
| `research_case_id` | UUID FK | No | Generated | Private | One of `research_case_id` or `historical_case_id` |
| `historical_case_id` | UUID FK | No | Generated | Private | |
| `existing_source_id` | UUID FK → `investment_sources.id` | No | Generated | Private | Null = new source proposal |
| `action` | String(20) | Yes | Generated | Private | `add` / `update_priority` / `deactivate` |
| `proposed_name` | Text | No | Generated | Private | For `add` action |
| `proposed_url` | Text | No | Generated | Private | For `add` action; must be HTTP/HTTPS |
| `proposed_source_type` | String(50) | No | Generated | Private | For `add` action |
| `proposed_priority` | Integer | No | Generated | Private | For `add` or `update_priority` actions |
| `rationale` | Text | Yes | Generated | Private | Agent's explanation for the suggestion |
| `status` | String(20) | Yes | Both | Private | `proposed` / `approved` / `rejected` / `expired` |
| `run_id` | UUID FK → `agent_runs.id` | No | Generated | Private | |
| `created_at` | DateTime(tz) | — | Generated | Private | |
| `reviewed_at` | DateTime(tz) | No | Generated | Private | Set when Dani approves or rejects |
| `expires_at` | DateTime(tz) | No | Generated | Private | Default: `created_at + 30 days`; auto-expired by a nightly job (Phase 2) |

**Suggested indexes:**
- `idx_si_suggestions_status` on `status` — review queue
- `idx_si_suggestions_research_case_id` on `research_case_id`
- `idx_si_suggestions_historical_case_id` on `historical_case_id`

**Validation rules:**
- `action` must be one of `add` / `update_priority` / `deactivate`
- For `add` action: `proposed_name` and `proposed_url` must be present
- `proposed_url` must be HTTP/HTTPS
- `approved` status may only be set if `rationale` is present
- Approval triggers a separate API call to `POST /api/investment/sources` — not auto-executed by PATCH on this model

---

## 3. Cross-Model Relationship Summary

```
special_situations (existing)
    │
    ├── 1:1 ──► research_cases
    │               │
    │               ├── 1:N ──► research_tasks
    │               ├── 1:N ──► research_documents
    │               ├── 1:N ──► research_sources
    │               ├── 1:N ──► public_article_drafts
    │               └── 1:N ──► source_intelligence_suggestions
    │
    └── 0:1 ──► historical_cases (linked_situation_id, nullable)
                    │
                    ├── 1:N ──► research_sources
                    └── 1:N ──► source_intelligence_suggestions

investment_sources (existing)
    │
    └── 0:N ──► source_intelligence_suggestions (existing_source_id, nullable)
                └── approved suggestions → POST /api/investment/sources

agent_runs (existing)
    │
    ├── 0:1 ──► research_cases (run_id)
    ├── 0:1 ──► historical_cases (run_id)
    ├── 0:1 ──► public_article_drafts (run_id)
    └── 0:1 ──► source_intelligence_suggestions (run_id)

ai_usage (existing)
    └── N:1 ──► agent_runs (run_id)
```

---

## 4. Disclaimer and Buy/Sell Language Enforcement

### Which fields must contain the disclaimer

| Model | Field | Enforcement |
|---|---|---|
| `ResearchCase` | `disclaimer` | Required; API validates exact string on write |
| `ResearchCase` | `brief.sections.1_executive_summary` | Embedded in JSON; validated at brief-parse time |
| `HistoricalCase` | `disclaimer` | Required if `reconstruction` is present |
| `PublicArticleDraft` | `disclaimer` | Required; API validates exact string on write |
| `PublicArticleDraft` | `disclaimer_present` | Boolean flag; must be `true` before `approved` transition |
| `PublicArticleDraft` | `content` | Disclaimer text must appear verbatim in the content body |

**Canonical disclaimer string:** `"Este análisis es educativo. No es asesoramiento financiero."`

This string is defined as a constant at the FastAPI service layer — not hardcoded per-prompt. Both the prompt template and the API-layer validator reference the same constant.

### Buy/sell language enforcement

| Layer | Mechanism |
|---|---|
| Agent prompts | Prompt explicitly instructs: do not use buy/sell language; use status labels only |
| `PublicArticleDraft.buy_sell_language_check` | Boolean flag set by agent; `false` if detected phrases found |
| API-layer check | Before `approved` transition: if `buy_sell_language_check = false`, reject transition and return detected phrases |
| Status labels | `readiness_label` on `PublicArticleDraft` and `investment_readiness` on `ResearchCase` enforce the four-value enum |

**Banned phrase examples** (for prompt and checker reference, not exhaustive):
- "buy", "sell", "invest", "purchase shares", "take a position", "go long", "go short"
- "recommend buying", "recommend selling", "strong buy", "target price"

**Allowed labels:**
- `monitor` — situation is active; not enough clarity to act
- `not_actionable` — does not meet course criteria
- `needs_more_work` — interesting but incomplete
- `candidate` — meets initial criteria; warrants deep investigation

---

## 5. Alembic Migration Notes (for Phase 1 implementation)

**Documentation only — do not run this sprint.**

All 7 new tables should be created in a single Alembic migration. Suggested migration ID pattern: `c3d4e5f6a7b8` (follow existing pattern in `alembic.ini`).

**Order of table creation** (to satisfy FK dependencies):
1. `research_cases` (depends on `special_situations`, `agent_runs`)
2. `research_tasks` (depends on `research_cases`)
3. `research_documents` (depends on `research_cases`)
4. `historical_cases` (depends on `special_situations`, `agent_runs`)
5. `research_sources` (depends on `research_cases`, `historical_cases`)
6. `source_intelligence_suggestions` (depends on `research_cases`, `historical_cases`, `investment_sources`, `agent_runs`)
7. `public_article_drafts` (depends on `research_cases`, `agent_runs`)

**Rollback safety:**
- All new tables are additive — no modifications to existing tables
- `ondelete=SET NULL` on FKs pointing to existing tables prevents migration from breaking existing data
- `ondelete=RESTRICT` on `public_article_drafts.research_case_id` requires draft cleanup before case deletion — intentional

---

## 6. SQLAlchemy Model File Placement

**Documentation only — do not create these files this sprint.**

Suggested placement within existing structure:

```
backend/models/
├── investment.py          (existing — SpecialSituation, InvestmentSource, SituationHistory, InvestorContact)
├── investment_research.py (new — ResearchCase, ResearchTask, ResearchDocument, ResearchSource)
├── historical_cases.py    (new — HistoricalCase)
├── source_intelligence.py (new — SourceIntelligenceSuggestion)
└── publishing.py          (new — PublicArticleDraft)
```

Alternative: add all new models to `investment.py` as a single file (acceptable for Phase 1 given file is already 86 lines and all models are investment-domain).

**Decision deferred to implementation sprint.** Either approach is valid; consistency with existing convention (one file per domain cluster) favours the split.

---

## 7. Open Questions Consolidated

| ID | Model | Question | Recommendation | Owner |
|---|---|---|---|---|
| OQ-RC1 | ResearchCase | One brief per situation or allow multiple iterations? | One in Phase 1; versioned in Phase 2 | Design |
| OQ-RC2 | ResearchCase | ResearchCase visible in list if situation_id becomes null? | Auto-archive on null | Design |
| OQ-RC3 | ResearchCase | Is `investment_readiness` writable by Dani? | Yes — Dani can override | Dani |
| OQ-RD1 | ResearchDocument | Shared documents across cases or per-case duplication? | Per-case duplication in Phase 1 | Design |
| OQ-RD2 | ResearchDocument | Auto-fetch+summarise on URL attach? | Manual/agent in Phase 1 | Design |
| OQ-RS1 | ResearchSource | DB constraint for exactly-one-FK rule? | API-layer Phase 1; DB constraint Phase 2 | Design |
| OQ-RS2 | ResearchSource | Survive ResearchCase deletion? | CASCADE DELETE | Design |
| OQ-RT1 | ResearchTask | Drag-to-reorder needed? | Priority + created_at ordering sufficient in Phase 1 | Dani |
| OQ-RT2 | ResearchTask | Auto-advance case to `documented` when last task done? | No — explicit Dani action required | Dani |
| OQ-HC1 | HistoricalCase | Separate `research_documents` for historical cases? | Reuse table with nullable `historical_case_id` FK | Design |
| OQ-HC2 | HistoricalCase | Who advances to `source_intel_applied`? | Only after all linked suggestions reviewed | Design |
| OQ-PAD1 | PublicArticleDraft | Markdown or HTML for `content`? | Markdown | Design |
| OQ-PAD2 | PublicArticleDraft | Multiple drafts per ResearchCase? | Yes; one `approved` at a time enforced at API layer | Design |
| OQ-PAD3 | PublicArticleDraft | External publishing mechanism? | Deferred — see OQ1 in redesign doc | Dani |
