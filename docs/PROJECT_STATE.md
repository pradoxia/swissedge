# SwissEdge — Project State

## 1. Project Name and Purpose

**SwissEdge** is a modular AI platform running 24/7 on a private VPS, with two operational domains:

- **Marketplace Assistant** — generates Hochdeutsch listings for Swiss second-hand platforms (Tutti.ch), handles pricing, approval flow and safety checks.
- **Special Situations Investment Radar** — scans SEC EDGAR for corporate events (spin-offs, mergers, tender offers, proxy fights), evaluates them against an investment course methodology. **Reframed (2026-05-01) as a private investment research desk**: identifies, investigates, documents, learns from, and will eventually publish structured research on special situations.
- **Telegram / OpenClaw control layer** — OpenClaw (Node.js) receives Telegram messages from Dani, routes commands to FastAPI, formats and returns results.
- **FastAPI backend** — source of truth for all business logic, observability, DB writes and AI calls.

---

## 2. Last Updated

2026-05-13 (Sprint AJ local — Official Source Finder & SEC Filing Locator Workbench)

---

## 3. Current Phase

**Current active track — Investment Platform V2 + Agent Ops / Fontana foundation.**

Current sprint state:
- Sprints A-O: Investment Platform V2 and Agent Ops foundation completed as previously documented. Agent Ops backend foundation and `/agent-ops` UI are deployed; logger isolation exists; scanner/evaluator integration remains not approved.
- Sprint Q: SEC EDGAR Detection Core completed and production-validated. It detects P1 official SEC signals (`SC TO-T`, `SC TO-I`, `Form 10`, and 8-K liquidation/dissolution metadata signals), enforces lookback locally, deduplicates repeated findings, and creates/updates minimal `SpecialSituation` detection records. Detected does not mean evaluated.
- Sprint Q.1: historical false detections from the pre-Hotfix-2 date-filter bug were cleaned through a manual, confirmation-gated CLI.
- Sprint R: scheduled SEC EDGAR intake is active through cron after Dani manual approval. It runs the manual detection path with a 168-hour lookback and keeps the one-request-per-five-seconds SEC throttle.
- Sprint S: SpecialSituation methodology workspace completed. P1 SpecialSituations have fixed checklist and required-resource snapshots under `evaluation.methodology_workspace`.
- Sprint T: Resource Scout v1 completed. It stores manual resource candidates and search suggestions; it does not browse the web, crawl, download PDFs, fetch document bodies, or verify evidence.
- Sprint U: Kanban actions and evidence mapping completed. Workflow movement and resource evidence mapping are manual; `evidence_found` does not mean verified, evaluated, or recommended.
- Sprint V: manual SpecialSituation -> ResearchCase promotion completed and production-validated after hotfix. Promotion is idempotent and stores `research_case_id` in `evaluation.methodology_workspace`.
- Sprint W: milestone closeout and GitHub sync preparation. Current active flow is `SEC EDGAR cron -> SpecialSituation -> Kanban -> checklist/resources -> evidence mapping -> manual ResearchCase promotion`.
- Sprint X-A: Compact Kanban Overview implemented for `/investment/situations`. The page now defaults to a compact responsive Kanban overview with phase counts, top cases per phase, preserved filters, and a detailed board toggle. Frontend-only; no backend, migration, cron, scanner, live AI, evaluator, ResearchCase automation, publishing, or Marketplace/Sales changes.
- Sprint X-B: ResearchCase Evaluation Preparation / Deep Research Assist implemented locally. `GET /api/investment/research-cases/{id}/evaluation-prep` returns a deterministic metadata-only preparation package from the ResearchCase brief snapshot, metadata, tasks, documents, and sources. `/investment/research/[id]` now includes an Evaluation Preparation panel with readiness level, missing required resources, checklist gaps, source quality notes, and manual next actions. This is preparation only: no live AI, no evaluator v2 global enablement, no automatic evaluation, no recommendations, no publishing, no crawling/PDF/document body fetching, no `/scan`, and no cron change.
- Sprint Y: Evidence Links & Research Traceability implemented locally. New read-only endpoints `GET /api/investment/situations/{id}/evidence-links` and `GET /api/investment/research-cases/{id}/evidence-links` normalize stored source metadata into traceability packages. `/investment/situations/[id]` and `/investment/research/[id]` show original SEC source links, resource candidate links, required-resource/checklist support links, ResearchCase source/document links, and metadata-only guardrails. It does not fetch document bodies, crawl, download PDFs, evaluate, verify evidence automatically, recommend, publish, call `/scan`, change cron, or enable evaluator v2 globally.
- Sprint Z: Intelligence Scoring Foundation implemented locally. `GET /api/investment/research-cases/{id}/intelligence-score` returns a deterministic 0-100 IA Score derived from existing ResearchCase metadata, Evaluation Preparation, and Evidence Links. The score uses Detection (40), Structuring (40), and Risk Discipline (20) components with grades `APPROVABLE`, `USEFUL_INCOMPLETE`, and `REVIEW_PIPELINE`. `/investment/research/[id]` includes an Intelligence Score card that states `APPROVABLE` means structurally approvable for manual review only, not investment approval. No DB writes, migration, live AI, external calls, evaluator activation, automatic evaluation, ResearchCase auto-creation, publishing, crawling, PDF download, document body fetching, cron change, or `/scan`.
- Sprint ZA: Agent Rooms 2.0 implemented locally as a frontend-only Agent Ops expansion. `/agent-ops/rooms/[id]` opens room detail pages with room metrics, agents, deterministic avatar placeholders, selected-agent logs, diagnostics, related ResearchCase/SpecialSituation links when present, conceptual interaction maps, and derived read-only operational indicators. `/agent-ops` room cards now show compact counts and link to room details. Profile name/avatar editing is deferred because no safe AgentProfile PATCH endpoint exists. No backend endpoints, DB migration, scanner/evaluator integration, live AI, cron changes, automation, publishing, recommendations, or Marketplace/Sales changes.
- Sprint AB: Missing Evidence Hunter & Case Documentation Guide implemented locally. New deterministic read-only guide builder and endpoints organize existing SpecialSituation and ResearchCase metadata into documentation quality, source trail, manual verification steps, missing required resources, checklist gaps, stored search suggestions, Missing Evidence Hunter next manual actions, quick links, and a derived activity timeline. `/investment/situations/[id]` and `/investment/research/[id]` show the guide near the top; Kanban cards show derived documentation status; Agent Ops shows Missing Evidence Hunter as an observer/manual research plan. No cron, scheduler execution, browsing, document fetching, PDF download, SEC document body fetching, live AI, automatic evaluation, automatic ResearchCase creation, automatic promotion, publishing, public draft creation, recommendations, Marketplace/Sales changes, or DB migration.
- Sprint AC: Case Activity Log & Research Timeline implemented locally. New deterministic read-only timeline builder and endpoints normalize stored SpecialSituation and ResearchCase metadata into event rows with event type, origin, agent/process, status, related entity, safe links, and metadata-only flags. `/investment/situations/[id]` shows a Case Activity Log; `/investment/research/[id]` shows a Research Timeline / Case Activity Log; Kanban cards show compact latest activity/attention markers without N+1 calls; Agent Ops shows case-row relevance by agent. Timelines are derived/current-state views, not persisted audit logs yet. No cron, scheduler execution, live AI, scanner/evaluator call, crawling, document fetching, automatic evaluation, automatic ResearchCase creation, automatic promotion, publishing, Marketplace/Sales changes, DB migration, or deploy.
- Sprint AD: Agent Rooms Real Ops + Case Research Agent implemented locally. `/agent-ops` and `/agent-ops/rooms/[id]` now present richer operational rooms, stronger agent identities, mission/watch/output metadata, conceptual interaction maps, scheduler posture display only, Missing Evidence Hunter as the case research agent, case-row relevance, related-case links when logs provide IDs, problems by agent, and frontend-derived XP/reliability/evidence-quality indicators. Rename/avatar editing remains deferred; no safe profile customization endpoint was added. No backend mutation, DB migration, cron, scheduler execution, live AI, scanner/evaluator runtime connection, publishing, recommendations, Marketplace/Sales changes, or deploy.
- Sprint AE: Batch Hardening, Deployment Readiness & UX Consistency implemented locally. The required Sprint AC fix was applied: SpecialSituation activity timeline now loads outside the main blocking page load and fails locally only. SpecialSituation evidence links also load as a non-blocking secondary panel. ResearchCase Evaluation Preparation and Evidence Links loaders are separated so secondary panel failures remain local. Kanban warning styling and Missing Evidence Hunter badge visibility were tightened. Deployment readiness and deep smoke-test checklist were documented. No backend mutation, DB migration, cron, scheduler execution, live AI, scanner/evaluator runtime connection, publishing, recommendations, Marketplace/Sales changes, or deploy.
- Sprint AH: Intelligence KPI Dashboard & Fontana Diagnostic Report v1 implemented locally. New deterministic read-only endpoints `GET /api/investment/intelligence/kpis` and `GET /api/investment/intelligence/fontana-report` aggregate stored SpecialSituation, ResearchCase, methodology workspace, Evidence Links, Documentation Guide, Activity Timeline inputs, Intelligence Score, and Agent Ops data where available. New `/investment/intelligence` dashboard shows preparation quality, documentation quality, evidence coverage, manual review workload, bottlenecks, lowest scoring cases, missing evidence cases, and manual next actions. Mission Control links to the dashboard, and Agent Ops now shows a deterministic Fontana observer report. No AI, evaluator, scanner, `/scan`, cron, scheduler execution, automatic evaluation, automatic ResearchCase creation, automatic promotion, crawling, PDF download, SEC body fetch, external HTTP, investment recommendations, publishing, Marketplace/Sales changes, DB migration, or deploy.
- Sprint AI: Research Command Center, Batch QA Polish & Deployment Verification UI implemented locally. Mission Control now shows the active workflow from SEC EDGAR detection through SpecialSituation, Kanban, Missing Evidence Hunter, ResearchCase, Evaluation Preparation, Evidence Links, Intelligence Score, Intelligence KPIs, and Fontana. A static manual Deployment Verification Checklist lists backend endpoints and frontend routes Dani should check after deployment. Cross-links were tightened across Mission Control, SpecialSituation detail, ResearchCase detail, Intelligence KPIs, and Agent Ops. Agent Ops room detail secondary panels now fail locally if one room endpoint is temporarily unavailable. Frontend/docs only: no backend endpoint, migration, deployment, AI, evaluator, scanner, `/scan`, cron change, scheduler execution, automatic evaluation, automatic ResearchCase creation, automatic promotion, crawling, document fetch, investment recommendations, publishing, or Marketplace/Sales changes.
- Sprint AJ: Official Source Finder & SEC Filing Locator Workbench implemented locally. New deterministic read-only endpoints `GET /api/investment/situations/{id}/official-source-finder` and `GET /api/investment/research-cases/{id}/official-source-finder` build manual official-source packages from stored SEC metadata, methodology workspace resources/checklists, resource candidates, search suggestions, ResearchCase snapshots, and Evidence Links. Situation and ResearchCase detail pages now show an Official Source Finder panel with SEC metadata, stored filing links, missing official document targets, locator steps, and copyable manual queries. Kanban cards show compact source-finder indicators from already-loaded JSON only. Agent Ops documents the Official Source Finder as manual/observer-only. No web search, SEC fetch, PDF download, crawl, link verification, AI, evaluator, scanner, `/scan`, cron change, scheduler execution, automatic evaluation, automatic ResearchCase creation, automatic promotion, publishing, recommendations, Marketplace/Sales changes, DB migration, or deploy.

Current strategic direction:
- ResearchCase is the primary durable work object.
- Research Inbox is the main operating queue for existing and future preliminary ResearchCases.
- Agent Ops is observability-first, not autonomy-first.
- Fontana is documented as CTO / Project Governor concept only; no runtime implementation yet.
- SEC EDGAR source-driven detection is operational and scheduled. ResearchCase evaluation remains manual/preparatory.
- Public Site / Brand Experience / User Documentation remains paused.

Standing guardrails:
- No `/api/investment/scan` unless explicitly approved.
- No cron changes unless explicitly approved.
- No evaluator v2 global enablement.
- No live AI unless explicitly approved.
- No deploy or migrations unless Dani explicitly executes/approves.
- No automatic ResearchCase creation from scanner yet.
- No Marketplace/Sales changes unless explicitly scoped.
- No public-site implementation while paused.
- No secrets, private infrastructure details, raw `.env`, DB dumps, raw course transcripts, or copyrighted raw course text in docs.

## Strategic Consolidation — AI Context + Agent Ops + Fontana

AI-Safe Context Architecture is now represented by `swissedge-ai-context/`, a curated context layer for assistants. It contains safe project state, roadmap, decisions, glossary, Agent Ops notes, AI-safe playbook/evaluator placeholders, and publication guardrails. It must not contain secrets, private infrastructure details, raw course materials, or copyrighted raw course text.

Agent Ops & Learning Layer is documented and partially implemented. The docs in `docs/agent-ops/` define rooms, agents, metrics, data model, API, UI, Fontana CTO, and routing audits. Sprint H backend foundation is documented deployed with additive migration `e5f6a7b8c9d0` applied, read-only endpoints, proposal status review, and a fail-safe logger skeleton. Sprint I `/agent-ops` UI is documented deployed. Sprint ZA adds local navigable room detail pages without backend changes. Sprint K logger isolation exists locally, but scanner/evaluator integration remains not approved. Sprint N/O add only narrow observer activity logging for proposal review and manual ResearchCase creation.

Fontana is documented as SwissEdge CTO / Project Governor. Sprint AH adds a deterministic Fontana Diagnostic Report endpoint and Agent Ops panel. Fontana remains an observer/advisor/documenter concept only. It can surface reports, ADR candidates, and improvements, but cannot deploy, modify production, trigger scans, change cron, enable evaluator v2, call AI, or auto-apply proposals.

Current status: Investment Platform V2 and Agent Ops are the active tracks. SEC EDGAR source-driven detection is operational through the approved cron wrapper. `SpecialSituation` is the detection object; manual Kanban/resource/evidence work prepares cases for manual ResearchCase promotion. `investment_sources` still does not control scanner execution. `/agent-ops` UI is documented deployed and smoke-tested; Sprint ZA room details are local. Scoreboard persistence, profile customization, and Fontana runtime remain deferred.

Next steps: Claude review of the Sprint AB/AC/AD/AE batch, then Dani manual deploy only if approved. Any future manual evaluation preview or evaluator v2 preview remains a separate explicit-approval gate without live AI/global evaluator activation by default.

**Previous deployed baseline — Investment Research Platform Phase 5 COMPLETE AND DEPLOYED — validated by Dani (2026-05-03).**

Phase 5 summary:
- **5A — Public Article Draft from ResearchCase:** `POST /api/investment/research-cases/{id}/public-draft` creates a private `PublicArticleDraft` from ResearchCase brief/tasks/documents/sources metadata. No AI, no external calls, no URL fetching, no private notes, no internal IDs, no operational metadata in public output.
- **5B — Editorial Review Workflow:** `GET /api/investment/public-drafts`, `GET/PATCH /api/investment/public-drafts/{id}` support private editing and status workflow: `draft -> in_review -> approved -> archived`. Direct `draft -> approved` is blocked. Approval is blocked if title/body/disclaimer are missing or buy/sell/internal metadata is detected. `published` is not exposed as an allowed workflow state.
- **5C — Markdown/Substack Export:** `GET /api/investment/public-drafts/{id}/markdown` returns Markdown for manual copy/export. No Substack API integration and no public posting.
- **5D — Publishing Checklist + Manual Approval Gate:** `/investment/public-drafts/[id]` shows checklist, backend validation warnings, disclaimer, and "PRIVATE DRAFT - NOT PUBLISHED" guardrail. ResearchCase detail has a Public Draft panel; `/investment/public-drafts` lists drafts.
- Dani smoke test validated: draft creation from ResearchCase, draft detail, private/not-published labels, editing, `draft -> in_review -> approved`, direct `draft -> approved` block, approval blocks for missing disclaimer and buy/sell language, clean approval, and Markdown/Substack-ready copy/export.
- No auto-publish; no Substack API; no external posting; no migration; no scanner/cron/v2 changes; no buy/sell language allowed.

**Phase 1 COMPLETE AND DEPLOYED. Phase 2 COMPLETE AND DEPLOYED. Phase 3 COMPLETE AND DEPLOYED — validated by Dani. Phase 4 COMPLETE AND DEPLOYED — validated by Dani. Phase 5 COMPLETE AND DEPLOYED — validated by Dani. Public Site / Brand Experience / User Documentation is paused. Next implementation should continue Agent Ops deployment validation or SEC source-driven intake only after explicit approval.**

---

**Investment Research Platform — Phase 4 COMPLETE AND DEPLOYED — validated by Dani (2026-05-02).**

Phase 4 summary:
- **4A** — Source Intelligence Approval Queue is live: `POST /research-cases/{id}/source-intelligence-suggestions` (save), `GET /source-intelligence-suggestions` (list with filters), `PATCH /source-intelligence-suggestions/{id}` (approve/reject). Status transitions: `proposed → approved | rejected`. Only `proposed` suggestions can be reviewed (409 on others). No apply endpoint. No `investment_sources` write. Full `run_logger` on save; no AI call on save/review.
- **4B** — Historical Case manual workspace is live: `POST/GET /api/investment/historical-cases`, `GET/PATCH /api/investment/historical-cases/{id}`. Status lifecycle: `seed → reconstructed → lessons_extracted → source_intel_applied`. Fields: `company_name`, `situation_type`, `event_date_approx`, `seed_notes`, `course_chapter_ref`, `reconstruction`. No migration (table in `c3d4e5f6a7b8`).
- **4C** — Historical Case Source Intelligence Preview: `POST /historical-cases/{id}/source-intelligence-preview` (`saved_to_db: false`, no URL fetching, no crawling, uses seed_notes + reconstruction only, skips AI if no notes); `POST /historical-cases/{id}/source-intelligence-suggestions` (save proposals). Full `run_logger` on preview endpoint.
- Frontend: `/investment/historical-cases` (list/create), `/investment/historical-cases/[id]` (detail + notes + preview + approve/reject), `/investment/source-intelligence` (approval queue page); ResearchCase source intelligence panel updated with "Save proposals to queue" + inline approve/reject for saved proposals.
- Tests: 31/31 Phase 4 tests pass; no live AI called; no migration needed.
- npm run build: 0 errors, 0 TypeScript errors. 3 new routes visible in build output.
- Dani manual smoke test validated: Source Intelligence queue loads; proposals can be reviewed; approve/reject works; no apply-to-`investment_sources` button is present; historical cases route loads; minimal historical case creation works; historical case detail opens; notes/status edits persist.
- Deployment validation confirmed: no migration needed; no scanner/cron/v2 changes; no publishing; no buy/sell language.
- Phase 4D — Apply Approved Proposals to Case Sources is deferred. No `investment_sources` writes exist. No scanner registry writes exist. No automatic apply exists.

**Phase 3 COMPLETE AND DEPLOYED — validated by Dani. Phase 4 COMPLETE AND DEPLOYED — validated by Dani. Phase 5 COMPLETE AND DEPLOYED — validated by Dani.**

Phase 5 guardrails:
- No auto-publish.
- No Substack API integration yet.
- No public posting.
- No buy/sell language.
- Educational content only.
- Manual approval required.
- Public drafts must not expose private notes, internal IDs, VPS details, or operational metadata.
- AI may help draft, but output must be reviewed manually.

---

**Phase 3D — Source Intelligence Preview — detail record:**
- **New endpoint:** `POST /api/investment/research-cases/{id}/source-intelligence-preview`
- **Service function** (`backend/services/investment/research_cases.py`): `generate_source_intelligence_preview()` — loads `ResearchCase` with tasks/documents/sources; if no sources → immediate return with warning (no AI call); loads optional linked `SpecialSituation`; builds prompt from all stored metadata; calls `complete_with_usage()` with system prompt from `backend/prompts/source_intelligence_preview.txt` (2000 max_tokens); parses JSON into `source_scores` and `suggestions`; validates `action` values (add/update_priority/deactivate); validates `confidence` (high/medium/low); forces `manual_review_required: True` on all suggestions; applies `_strip_buy_sell` across all text fields; returns `{saved_to_db: false, research_case_id, source_scores, suggestions, warnings, disclaimer, usage}`. Never writes to `investment_sources`. No URL fetching.
- **Backend router** (`backend/api/investment/research_cases.py`): full `run_logger` instrumentation (start_run/finish_run/fail_run/log_ai_usage); agent_name=`source_intelligence_previewer`; same isolation pattern as Phase 2A/3C.
- **Prompt file** (`backend/prompts/source_intelligence_preview.txt`): system prompt for source scoring and suggestions. No buy/sell language allowed.
- **Frontend API** (`frontend/lib/api.ts`): `SourceScoreItem`, `SourceIntelligenceSuggestion`, `SourceIntelligencePreviewResult` interfaces; `generateSourceIntelligencePreview(caseId)` function.
- **Frontend UI** (`frontend/app/investment/research/[id]/page.tsx`): `SourceIntelligencePanel` component — "Generate source intelligence preview" button (indigo); manual trigger only; "PROPOSALS ONLY — NOT APPLIED" banner; metadata-only warning; source scores grid; suggestions list with action/confidence labels; disclaimer; DISCARD button. No apply button (investment_sources writes deferred). Sources section: improved "SIGNAL QUALITY" label; "WHY THIS SOURCE WAS USEFUL" notes label; metadata-only warning notice. `SourceIntelligencePanel` embedded at bottom of Sources section.
- **Tests** (`backend/tests/test_research_cases_phase3d_source_intelligence.py`): 14 tests — 10 `TestSourceIntelligencePreviewService`, 4 `TestSourceIntelligencePreviewEndpoint` — all passing.
- **19/19 Phase 3C tests still pass.**
- **npm run build: 0 errors, 0 TypeScript errors**
- No DB migrations; no scanner/cron/v2 global changes; no Marketplace/Sales changes; no secrets; no buy/sell language; no writes to `investment_sources`.

**Phase 3 COMPLETE AND DEPLOYED — validated by Dani. Phase 4 COMPLETE AND DEPLOYED — validated by Dani. Phase 5 COMPLETE AND DEPLOYED — validated by Dani. Phase 4D apply-to-case-sources is deferred; no `investment_sources` writes, scanner registry writes, or automatic apply exist.**

**Investment Research Platform — Phase 3A+3B+3C Document/Source UI Enrichment + Snippet Capture + AI Document Analysis Preview (2026-05-02) — COMPLETE AND DEPLOYED — validated by Dani:**
- **3A — Document/Source UI Enrichment:** `doc_type` selector (8 options), `signal_quality` editor (low/medium/high), metadata-only label on URLs, `snippet` field mapped to `doc.summary`, `notes` field mapped to `src.notes` (tags). No migration — uses existing columns. Frontend: new field rows in document and source cards.
- **3B — Manual Snippet Capture:** Paste text into document summary field; save on explicit "SAVE SNIPPET" button; copyright warning displayed; no URL fetching.
- **3C — AI Document Analysis Preview:** `POST /api/investment/research-documents/{id}/analysis-preview`; calls `generate_document_analysis_preview()`; guard: `_MIN_SNIPPET_LENGTH = 50` — short/None snippet skips AI entirely and returns warning; full `run_logger` instrumentation; `saved_to_db: False`; no DB write; no URL fetching; no automatic task creation; `_strip_buy_sell()` on all string/list output fields; JSON parse fallback to `_analysis_defaults()` + warning; 7-key analysis output: `summary, key_points, risks, timeline_items, missing_information, suggested_research_tasks, source_usefulness`.
- **Backend PATCH endpoints:** `PATCH /research-cases/{id}/documents/{doc_id}` → `patch_document()`; `PATCH /research-cases/{id}/sources/{src_id}` → `patch_source()`; `patch_source` validates `signal_quality` against `VALID_SIGNAL_QUALITY` (400 on invalid).
- **Tests** (`backend/tests/test_research_cases_phase3_document_intelligence.py`): 19 tests — 4 `TestPatchDocument`, 4 `TestPatchSource`, 8 `TestDocumentAnalysisPreviewService`, 3 `TestDocumentAnalysisPreviewEndpoint` — all passing.
- **npm run build: 0 errors, 0 TypeScript errors**
- No DB migrations; no scanner/cron/v2 global changes; no Marketplace/Sales changes; no secrets; no buy/sell language

**Phase 3A+3B+3C COMPLETE AND DEPLOYED. Next recommended sprint: Phase 3D — Source Usefulness Scoring + Source Intelligence Suggestions**

**Investment Research Platform — Phase 2D/2E Research Quality Checklist + Status Assist (2026-05-02) — COMPLETE AND DEPLOYED — validated by Dani:**
- **Backend service** (`backend/services/investment/research_cases.py`): `generate_quality_preview()` function — loads `ResearchCase` with tasks/documents/sources + optional linked `SpecialSituation`; assembles quality-review prompt with brief completeness breakdown, open task count, document and source counts; calls `complete_with_usage()` with `_QUALITY_SYSTEM` (1200 max_tokens); parses JSON response into `{quality_checklist, suggested_status, suggested_readiness, rationale}`; validates `suggested_status` against `VALID_STATUSES` and `suggested_readiness` against `VALID_READINESS` with graceful defaults on invalid values; returns `{saved_to_db: false, quality_checklist, suggested_status, suggested_readiness, rationale, warnings, disclaimer, usage}`; no DB write; no URL fetching
- **`published` hard-block:** `_parse_quality_json` hard-blocks `suggested_status: published` — downgraded to `documented` (if `brief_completeness` checklist item is true) or `under_investigation` (otherwise); warning appended: "published status cannot be suggested by AI; manual editorial approval is required." `published` status requires explicit manual action only.
- **Backend router** (`backend/api/investment/research_cases.py`): `POST /research-cases/{id}/quality-preview` endpoint; full `run_logger` instrumentation (start_run/finish_run/fail_run/log_ai_usage); agent_name=`research_quality_reviewer`; same isolation pattern as Phase 2A brief preview
- **Frontend API** (`frontend/lib/api.ts`): `QualityChecklist` interface (9 boolean fields), `QualityPreviewResult` interface, `generateQualityPreview(id)` function
- **Frontend UI** (`frontend/app/investment/research/[id]/page.tsx`): `QualityAssistPanel` component — "✓ RUN QUALITY CHECK" button (teal); teal "ASSISTIVE PREVIEW — NOT SAVED" banner; metadata-only UX warning in both panels; quality checklist grid (✓/✗ per item); suggested status + readiness display; rationale text; "APPLY SUGGESTED STATUS", "APPLY SUGGESTED READINESS", "APPLY BOTH", "DISCARD" buttons; all apply via existing `saveField()`/PATCH mechanism; no autosave; no useEffect trigger
- **UX metadata warning** added to both `AiPreviewPanel` and `QualityAssistPanel`: "Attached document/source URLs are used as metadata only. SwissEdge does not fetch or read linked URLs in this preview."
- **Tests** (`backend/tests/test_research_cases_phase2d.py`): 15 tests (13 unit, 2 integration) — all passing; covers saved_to_db=false, no-DB-write, valid status/readiness values, all checklist keys present and boolean, disclaimer present, malformed JSON defaults, invalid status default, invalid readiness default, published hard-block (both branches: brief_complete→documented / brief_incomplete→under_investigation), 404, no linked situation
- **Phase 2A tests still passing** (`backend/tests/test_research_cases_phase2a.py`): 7/7
- **Total: 22/22 tests passing**
- **npm run build: 0 errors, 0 TypeScript errors**
- No DB migrations; no scanner/cron/v2 global changes; no Marketplace/Sales changes; no secrets; no buy/sell language

**Phase 2 COMPLETE AND DEPLOYED. Phase 3A+3B+3C COMPLETE AND DEPLOYED. Next recommended sprint: Phase 3D — Source Usefulness Scoring + Source Intelligence Suggestions**

**Investment Research Platform — Phase 2A AI Research Brief Preview (2026-05-02) — COMPLETE:**
- **Backend service** (`backend/services/investment/research_cases.py`): `generate_brief_preview()` function — loads `ResearchCase` with tasks/documents/sources, optionally loads linked `SpecialSituation`, assembles source-aware prompt, calls `complete_with_usage()`, parses JSON response into 14-section dict; returns `{saved_to_db, preview, source_context_used, warnings, disclaimer, usage}`; no DB write; no URL fetching
- **Backend router** (`backend/api/investment/research_cases.py`): `POST /research-cases/{id}/generate-brief-preview` endpoint; `run_logger.start_run()` / `finish_run()` / `fail_run()` + `log_ai_usage()` fully wired; raises `HTTPException` if service raises; all exceptions propagate correctly after logging
- **Frontend API** (`frontend/lib/api.ts`): `BriefPreviewSections` interface, `BriefPreviewResult` interface, `generateBriefPreview(id)` function
- **Frontend UI** (`frontend/app/investment/research/[id]/page.tsx`): `AiPreviewPanel` component — "⚡ GENERATE AI BRIEF" button (violet); preview-only banner with context/model/token stats; warnings block (orange); disclaimer line; section-by-section comparison grid (AI preview vs current); per-section checkbox selection; SELECT ALL / NONE controls; "APPLY N SECTIONS" button merges into `rc.brief` via existing PATCH; DISCARD resets; no autosave
- **Tests** (`backend/tests/test_research_cases_phase2a.py`): 7 tests (5 unit, 2 integration) — all passing
- No DB migrations; no scanner/cron/v2 global changes

**Investment Research Platform — Phase 1 COMPLETE (2026-05-02):**
- All phases 1A–1H deployed and validated by Dani
- 1A: DB tables live (7 models, migration `c3d4e5f6a7b8`, 16 FK constraints)
- 1B: ResearchCase API — CRUD endpoints, Pydantic schemas, 409 idempotency, readiness enum enforcement
- 1C: Frontend list + detail pages (`/investment/research`, `/investment/research/[id]`)
- 1D: Evaluation Detail → ResearchCase panel (create from situation, 409 recovery, 8 UI states)
- 1E: Research Workspace — Tasks/Documents/Sources inline add-edit
- 1F: Research Brief Skeleton — manual 14-section textarea editor, SAVE button, fill counter
- 1G: Workspace Polish — header, workflow strip, section hints, empty states, done/cancelled task styling
- 1H: Deploy + smoke test — all endpoints and routes live, validated

**Investment Research Platform — Phase 1G Research Workspace Polish (2026-05-02) — COMPLETE AND DEPLOYED:**
- **Frontend UI only** (`frontend/app/investment/research/[id]/page.tsx`): no backend changes, no migration, no API changes
- **Workspace header:** "RESEARCH WORKSPACE" label, `CASE {id[:8]}` cyan title, situation link, status badge, readiness badge, `updated_at` timestamp
- **Workflow strip:** `WORKFLOW_STEPS` constant (`detected → brief_generated → under_investigation → documented → archived → published`); current step highlighted in cyan, past steps dimmed, future steps near-invisible; `findIndex()` for past/current/future logic
- **Section order:** Overview/Status → Research Brief → Tasks/Missing Info → Key Documents → Useful Sources → Disclaimer/Guardrails
- **`Section` component:** added optional `hint` prop — subdued monospace helper text below section title; used in Brief, Tasks, Documents, Sources sections
- **Empty states:** distinct per section — "No tasks yet. Add one below.", "No documents attached yet.", "No sources recorded yet."
- **Task display:** done/cancelled tasks shown with `line-through` and `text-gray-600`; status regex fix (`replace(/_/g, ' ')` not `replace('_', ' ')`)
- **Disclaimer panel:** merged disclaimer + guardrail notice into single amber-tinted bottom panel
- **npm run build passes: 0 errors, 0 TypeScript errors; all routes built**
- No DB migrations; no backend changes; no scanner/cron/v2/AI/crawling/publishing changes; no Marketplace/Sales changes
- **Next recommended task:** Deploy Phase 1B + 1C + 1D + 1E + 1F + 1G together — run `scripts/deploy_backend_files.ps1` then `scripts/deploy_frontend.ps1`; no new migration needed

**Investment Research Platform — Phase 1F Research Brief Skeleton (2026-05-02) — COMPLETE AND DEPLOYED:**
- **Frontend UI** (`frontend/app/investment/research/[id]/page.tsx`): replaced read-only `BriefSection` with `BriefEditor` component — collapsible 14-section textarea form; initialized from `rc.brief` on load; explicit "SAVE BRIEF" button (no autosave); inline success/error message; section fill counter (X/14 SECTIONS FILLED)
- **14 sections:** Executive Summary, Situation Type, Why It May Be Interesting, Course Methodology Reference, Company Context, Board/Management, Key Documents, Timeline, Risk Analysis, What To Verify Before Investing, Missing Information/Manual Tasks for Dani, Source Intelligence, Investment Readiness, Public Summary Draft
- **Save path:** `BriefEditor.onSave(draft)` → `saveField({ brief: draft }, 'Brief saved')` → existing `PATCH /api/investment/research-cases/{id}` → `ResearchCase.brief` JSONB column — no backend changes, no migration
- **npm run build passes: 0 errors, 0 TypeScript errors; all routes built**
- No DB migrations; no backend changes; no scanner/cron/v2/AI/crawling/publishing changes; no Marketplace/Sales changes
- **Next recommended task:** Deploy Phase 1B + 1C + 1D + 1E + 1F together — run `scripts/deploy_backend_files.ps1` then `scripts/deploy_frontend.ps1`; no new migration needed

**Investment Research Platform — Phase 1E Research Workspace (2026-05-02) — COMPLETE AND DEPLOYED:**
- **Backend service layer** (`backend/services/investment/research_cases.py`): added `VALID_TASK_STATUSES`, `VALID_SIGNAL_QUALITY` constants; `ResearchTaskCreate`, `ResearchTaskUpdate`, `ResearchDocumentCreate`, `ResearchSourceCreate` Pydantic schemas; service functions: `create_task`, `list_tasks`, `update_task`, `create_document`, `list_documents`, `create_source`, `list_sources`
- **Backend router** (`backend/api/investment/research_cases.py`): 6 new endpoints: `GET/POST /research-cases/{id}/tasks`, `PATCH /research-tasks/{task_id}`, `GET/POST /research-cases/{id}/documents`, `GET/POST /research-cases/{id}/sources`
- **Backend tests** (`backend/tests/test_research_cases_phase1e.py`): schema, service, and endpoint tests covering happy path + error paths for all three child types
- **Frontend API** (`frontend/lib/api.ts`): `addResearchTask`, `updateResearchTask`, `addResearchDocument`, `addResearchSource` functions
- **Frontend UI** (`frontend/app/investment/research/[id]/page.tsx`): Tasks section: inline add form (description + priority), status dropdown (PATCH on change); Documents section: inline add form (url + title + doc_type); Sources section: inline add form (name + url + signal_quality); all use `load()` to refresh after mutation; no alert(); inline error messages
- **npm run build passes: 0 errors, 0 TypeScript errors; all routes built**
- No DB migrations; no scanner/cron/v2/AI/crawling/publishing changes; no Marketplace/Sales changes
- **Next recommended task:** Deploy Phase 1B + 1C + 1D + 1E together; smoke test all research endpoints and UI
- `frontend/app/investment/evaluations/[id]/page.tsx`: Research Case panel added below Decision Card, before v2 Preview panel
- Panel states: `loading` (spinner text), `case_exists` (status badge + readiness badge + updated_at + "Open Research Case" link), `no_case` ("No research case yet" + "Create Research Case" button), `create_in_progress` (button disabled + "Creating…"), `create_success` (router.push to `/investment/research/{id}`), `duplicate_409` (silent recovery GET → redirect if found, else inline message with link to research list), `backend_error` (inline message + retry), `research_api_unavailable` (inline error; rest of page unaffected)
- Disclaimer always shown in panel: "Este análisis es educativo. No es asesoramiento financiero."
- 409 recovery: catches `err.message.includes('409')`, calls `fetchResearchCases({ situation_id })`, redirects if case found, shows inline link to `/investment/research` if not
- No `alert()` in any branch; all feedback is inline within the panel
- `frontend/lib/api.ts`: no changes (all API functions already present from Phase 1C)
- **npm run build passes: 0 errors, 0 TypeScript errors; all routes built**
- No backend changes; no scanner/cron/v2/AI/crawling/publishing changes; no Marketplace/Sales files modified; no DB migrations
- **Next recommended task:** Deploy Phase 1B + 1C + 1D together — run `scripts/deploy_backend_files.ps1` then `scripts/deploy_frontend.ps1`; smoke test `GET /api/investment/research-cases` and `/investment/research`

**Investment Research Platform — Phase 1D Design (2026-05-02) — COMPLETE (documentation only):**
- `docs/investment-research-phase-1d-evaluation-link.md` created: full design note for Evaluation Detail → ResearchCase panel
- Covers: goal, current state, user journey, 8 UI states, API contract (3 endpoints), duplicate/409 handling, routing behavior, guardrails, acceptance criteria, test plan, open questions, future follow-up tasks
- No code changes; no backend; no frontend; no deploy; no migrations
- **Next recommended task:** Implement Phase 1D — add ResearchCase panel to `/investment/evaluations/[id]`; requires Phase 1B + 1C deployed first

**Investment Research Platform — Phase 1C Frontend (2026-05-02) — COMPLETE AND DEPLOYED:**
- `frontend/app/investment/research/page.tsx`: list page — status/readiness filters; create-from-situation panel (explicit user action only); task/document/source counts per row
- `frontend/app/investment/research/[id]/page.tsx`: detail page — inline status/readiness editors (PATCH on save); notes editor; brief viewer (collapsible); task/document/source sections; disclaimer always shown
- `frontend/lib/api.ts`: `ResearchCase`, `ResearchTask`, `ResearchDocument`, `ResearchSource`, `ResearchCasesResponse` interfaces; `fetchResearchCases`, `fetchResearchCase`, `createResearchCaseFromSituation`, `updateResearchCase` functions
- `frontend/app/page.tsx`: Research Cases card added to Investment Operations section (status: MANUAL)
- `frontend/app/investment/evaluations/page.tsx`: RESEARCH nav link added to header
- **npm run build passes: 0 errors, 0 TypeScript errors; 16 routes built**
- No backend changes; no scanner/cron/v2/AI/crawling/publishing changes; no Marketplace/Sales files modified

**Investment Research Platform — Phase 1B Service Layer (2026-05-01) — COMPLETE AND DEPLOYED:**
- **ORM gap fixed:** `HistoricalCase.sources` + `ResearchSource.historical_case` with `back_populates="sources"` — no migration needed (ORM-only)
- **Pydantic schemas:** `ResearchCaseRead`, `ResearchCaseCreate`, `ResearchCaseUpdate`, `ResearchTaskRead`, `ResearchDocumentRead`, `ResearchSourceRead` in `backend/services/investment/research_cases.py`
- **Service layer:** `create_research_case_from_situation` (idempotent — 409 on duplicate), `get_research_case`, `list_research_cases`, `update_research_case` — all in same file; readiness and status enum enforcement at service layer
- **API endpoints** in `backend/api/investment/research_cases.py`, registered in `main.py` under `/api/investment`:
  - `POST /research-cases/from-situation/{situation_id}` — creates `ResearchCase` linked to existing `SpecialSituation`; 409 if already exists
  - `GET /research-cases` — filterable by `status`, `investment_readiness`, `situation_id`
  - `GET /research-cases/{id}` — full detail with tasks/documents/sources
  - `PATCH /research-cases/{id}` — update status/readiness/notes/brief fields
- **Disclaimer** always present in `ResearchCaseRead`; never stripped or overrideable via API
- **Readiness labels enforced:** `monitor|not_actionable|needs_more_work|candidate` only — API returns 400 for anything else
- **No AI call; no external fetch; no scanner change; no cron change; no v2 change; no frontend; no deploy**
- **79/79 tests pass** (41 Phase 1B + 38 Phase 1A); `scripts/deploy_backend_files.ps1` allowlist updated

**Investment Research Platform — Phase 1A Persistence Foundation (2026-05-01) — COMPLETE AND DEPLOYED:**
- `backend/models/investment_research.py`: `ResearchCase`, `ResearchTask`, `ResearchDocument`, `ResearchSource`, `HistoricalCase`
- `backend/models/source_intelligence.py`: `SourceIntelligenceSuggestion`
- `backend/models/publishing.py`: `PublicArticleDraft`
- All FK ondelete rules applied (SET NULL / RESTRICT / CASCADE per data model spec); disclaimer defaults embedded; `buy_sell_language_check` field on `PublicArticleDraft` enforced non-nullable
- `backend/db/migrations/versions/c3d4e5f6a7b8_add_investment_research_tables.py`: 7 tables in FK-dependency order with full index set
- `backend/db/migrations/env.py`: new model modules added to import list
- `backend/tests/test_investment_research_models.py`: 38 unit tests — all pass; no live DB required
- **Migration applied on VPS — alembic head: `c3d4e5f6a7b8`; all 7 tables confirmed live; all 16 FK constraints verified; health check 200 OK**
- **Known ORM gap:** `ResearchSource` has no `back_populates` from `HistoricalCase` — no runtime impact yet (no endpoints), fix in Phase 1B before `historical_case_agent` endpoint
- No endpoints; no frontend; no cron; no scanner change; no v2 change

**Investment Research Platform — Data Model Design Sprint (2026-05-01) — COMPLETE:**
- `docs/investment-research-data-model.md` created: 7 models fully specified (`ResearchCase`, `ResearchTask`, `ResearchDocument`, `ResearchSource`, `HistoricalCase`, `PublicArticleDraft`, `SourceIntelligenceSuggestion`)
- Each model: purpose, lifecycle/status values, full field table (type / required / manual-vs-generated / private-vs-publishable), FK relationships to existing tables, suggested indexes, validation rules, open questions
- Cross-model relationship diagram included; Alembic migration order specified; SQLAlchemy file placement recommended
- Disclaimer enforcement documented: which fields require canonical string, how `buy_sell_language_check` gates approval
- `SourceIntelligenceSuggestion` model added (was implicit in redesign doc, now fully specified)
- Canonical PROJECT_STATE confirmed at `docs/PROJECT_STATE.md` — no root-level copy exists
- No implementation; no migration; no endpoint; no cron change; no v2 change; no deploy

**Investment Research Platform — Design Sprint (2026-05-01) — COMPLETE:**
- `docs/investment-research-platform-redesign.md` created: full product definition, 5-agent network, 14-section research brief format, ResearchCase/HistoricalCase/PublicArticleDraft lifecycles, source intelligence lifecycle, publishing workflow, draft data models (6 models), API/UI implications, safety guardrails, phased roadmap (5 phases), 10 open questions
- No implementation; no migration; no endpoint; no cron change; no v2 change; no deploy
- v1 evaluator: still production default; v2: still manual-preview only; scanner: unchanged
- Investment Research Platform is now the active primary track

**Marketplace Sales Automation (Sprints 28–34) — VALIDATED IN PRODUCTION:**
- `SalesItem` model + `SalesPlatformListing` model with Alembic migration `b2c3d4e5f6a7` — 3 DB tables live on VPS: `sales_items`, `sales_item_photos`, `sales_platform_listings`
- Sales Items API confirmed live: `POST /sales/items`, `GET /sales/items`, `GET /sales/items/{id}`, `PATCH /sales/items/{id}`, `POST /sales/items/{id}/generate-platform-drafts`, `POST /sales/telegram-intake`
- Auto-creates 4 `SalesPlatformListing` rows per item on creation (Ricardo.ch, Tutti.ch, Anibis.ch, Facebook CH)
- `POST /sales/telegram-intake` single-call endpoint: creates SalesItem + 4 platform listings, returns `{item_id, item_url, reply_es}` (no listing generation on intake)
- Frontend: `/marketplace/sales/items` list page + `/marketplace/sales/items/[id]` detail page with 6 platform tabs (Overview + 4 platform draft tabs) — deployed and accessible
- Deterministic Python bot plan complete: `deploy/systemd/swissedge-telegram-bot.service` + `docs/swissedge-telegram-bot-deploy.md` created
- **Telegram/OpenClaw intake not reliable for DB writes** — OpenClaw (GPT-based) not dependable for structured `telegram-intake` calls; deterministic Python bot or direct API preferred for sales intake
- **Deploy archive optimized (2026-05-01):** `scripts/deploy_frontend.ps1` now excludes `./node_modules` and `./.next` from tar — archive reduced from ~260 MB to < 1 MB

**Mission Control frontend fully operational — production readiness complete. All dashboard routes deployed and validated on VPS (Tailscale-only access).**

Investment evaluator v2 manual live shadow test complete — GO decision received. V2 validated on 2 real SEC filings with 4 live AI calls; routing, schema compliance, and prohibited inference guard all functioning correctly; v1 remains production default pending limited production testing approval.

**Infrastructure & Observability Hardening (2026-04-30) — DEPLOYED AND VALIDATED:**
- SEC EDGAR EFTS query fixed: removed 3 spurious Elasticsearch DSL params (`_source`, `hits.hits.total.value`, `hits.hits._source.file_date`) that caused 500 errors; `dateRange`/`startdt` now only sent when an explicit date window is requested — `backend/services/investment/sources/sec_edgar.py`
- `backend/services/investment/sources/sec_edgar.py` added to `scripts/deploy_backend_files.ps1` allowlist
- Cron visibility fixed: `cron_reader.py` now falls back to `sudo crontab -u root -l` when the root spool file is not readable (PermissionError); root investment scan cron entries are now visible in `GET /api/observability/cron/upcoming`; `cron_reader.py` added to deploy allowlist
- `croniter==3.0.3` added to `requirements.txt` (was present as APScheduler transitive dep; now explicitly pinned)
- Radar Status page crash-proofed (React error #31): all API state typed as `unknown`, `safeText()`/`safeArr()` helpers guard every render; `database_records_created` dict no longer rendered as raw object
- Radar Status cron display polished: investment scan entries show "SEC EDGAR scan" label + `friendlySchedule()` human-readable frequency; other SwissEdge jobs show friendly labels (watchlist follow-up, marketplace check, health check); raw cron expressions hidden; capped at 3 scan + 4 other entries
- Deploy script backup retention fixed (PowerShell escaping): bash `$vars` and `$()` now backtick-escaped inside double-quoted here-strings; frontend keeps 2 most recent `frontend_backup_*`, backend keeps 5 most recent `backup_*`
- /opt/swissedge disk usage reduced to ~1 GB after old backup cleanup
- No `/scan` triggered; v1 remains default; v2 remains manual-preview only

**Hotfix — Radar Status cron response shape (2026-04-30) — DEPLOYED AND VALIDATED:**
- `/investment/radar-status` crashed in production: `CronEntry`/`CronUpcomingResponse` TypeScript interfaces did not match real backend response shape
- Backend returns `{ window_days, entries: [{ scheduled_at, schedule, command, source, user }] }`; frontend had declared `{ days_ahead, entries: [{ next_run, next_run_iso }] }`
- Fixed: `frontend/lib/api.ts` interfaces corrected; page references updated (`days_ahead` → `window_days`, `entry.next_run` → `entry.scheduled_at`)
- No backend changes; no scanner changes; no cron changes; no DB mutation; read-only guarantee preserved
- TypeScript build passed; deployed via `scripts/deploy_frontend.ps1` — validated by Dani

**Sprint 13 — Mission Control Home Polish (2026-04-30) — DEPLOYED AND VALIDATED:**
- Flat 7-card list replaced with three labeled sections: Investment Operations, Platform Observability, Future Modules
- `SectionLabel` + `ModuleGrid` + `statusBarWidth` helper extracted; status labels READ-ONLY and PREVIEW added
- Safety strip: "CRON V2: DISABLED" in red (previously ambiguous "NO CRON V2")
- Evaluator v2 card: status PREVIEW, links to `/investment/evaluations` (access via detail page — no dedicated route)
- Radar Status card on home: status READ-ONLY, links to `/investment/radar-status`
- No backend calls; pure static page; no route changes
- TypeScript build passed; deployed via `scripts/deploy_frontend.ps1` — validated by Dani

**Sprint 12 — Scanner Observability / Radar Status (2026-04-30) — DEPLOYED AND VALIDATED:**
- `/investment/radar-status` route added — read-only scanner observability page; does not trigger scans
- Shows: last scanner run details, last success, last failure, recent runs table, next scheduled scans (cron), source registry summary
- Data from three existing read-only endpoints: `GET /api/observability/agents/investment_scanner`, `GET /api/investment/sources`, `GET /api/observability/cron/upcoming?days=3`
- Each section has independent error/empty state; page renders even if one endpoint fails
- `CronEntry`, `CronUpcomingResponse`, `fetchCronUpcoming()` added to `frontend/lib/api.ts`; RADAR STATUS nav link added to evaluations page
- No POST calls; no scan trigger; no cron mutation; footer label confirms read-only
- TypeScript build passed; deployed via `scripts/deploy_frontend.ps1` — validated by Dani (cron interface corrected by hotfix)

**Sprint 11 — Course References for Source Categories (2026-04-30) — DEPLOYED AND VALIDATED:**
- `/investment/sources` page now has three grouped sections: A) Operational (active DB rows), B) Placeholder (inactive DB rows), C) Future Methodology (static frontend array from source_map.md analysis)
- Summary cards at top of page show counts for each section
- Placeholder items (3 inactive DB sources) show a `▸ COURSE REF` button inline in the Name cell; clicking expands a violet panel with Playbook / Primary Chapter / Supporting Chapters / Why It Matters
- Future Methodology items (8 static categories) show a `▸ COURSE REF` button per row; click expands the same panel format
- Course references are chapter-level only (e.g., "Ch. 10", "Ch. 7") — no video timestamps; "Timestamp not available" displayed honestly
- Static mapping `PLACEHOLDER_COURSE_REFS` keyed by exact DB source name; `FUTURE_SOURCES` array contains `courseRefs[]` per category
- Enable/Disable toggle preserved for Operational and Placeholder sections; Future Methodology items are display-only
- No new dependencies; frontend-only diff in `frontend/app/investment/sources/page.tsx`
- TypeScript build passed; deployed via `scripts/deploy_frontend.ps1` — validated by Dani

**Sprint 10 — Source Categories UI (2026-04-30) — DEPLOYED AND VALIDATED:**
- Inline action feedback added to detail page (Mark Reviewing / Add to Watchlist / Ignore / Archive / Save Notes) — no `alert()`, uses `actionMessage` state + `setTimeout` clear; `✓`/`⚠` inline in nav row
- v2 preview panel hardened: "PREVIEW ONLY — NOT SAVED TO DB" subtitle label; button text "Run v2 preview (preview only)"; 429 handling with explicit message; daily limit turns red when `remaining === 0`
- `/investment/sources` page added — table with Name/Type/Market/Priority/Freq/Last Checked/Last Error/Status columns; Enable/Disable toggle using `PATCH /api/investment/sources/{id}`; scanner disclaimer footer
- `frontend/lib/api.ts` extended: `InvestmentSource` interface (13 fields), `fetchSources()`, `toggleSourceActive()`
- Sources card added to Mission Control home (`/`) with `status: ACTIVE`, `href: /investment/sources`
- SOURCES nav link added to evaluations queue (`/investment/evaluations`)
- Discovery Source and Source Detail fields added to Decision Card on detail page — inferred from `filing_url` (sec.gov → SEC EDGAR) and `filing_type` presence; pure frontend, no backend changes
- `scripts/seed_investment_sources.py` created — idempotent, API-based (stdlib urllib only), DRY_RUN support; reads `config/investment_sources.yaml`; 7 sources
- `scripts/deploy_backend_files.ps1` fixed — PowerShell `$(dirname $file)` expansion bug in SSH here-string resolved; `seed_investment_sources.py` and `config/investment_sources.yaml` added to deploy allowlist
- `investment_sources` DB table seeded: 7 sources (4 active, 3 inactive); `/investment/sources` page shows all entries; Enable/Disable toggle validated
- Deployed via `scripts/deploy_frontend.ps1` and `scripts/deploy_backend_files.ps1` — validated by Dani, no production issues found

**Frontend batch — Queue UX, Decision Card, Watchlist, v2 Preview (2026-04-30) — DEPLOYED AND VALIDATED:**
- Queue UX simplified: workflow pills are now the sole filter; "Show test/demo" and "Show archived" checkboxes removed; always loads all rows
- Decision Card added to detail page — compact summary grid (company, ticker, filing type, workflow/evaluator/playbook/recommendation badges, confidence, conditional HR/risk counts, filing URL)
- Rendering hotfix: `(situation.status ?? 'unknown').toUpperCase()` — was crashing with null status on old DB rows, stalling detail page at "Rendering..."
- Workflow action buttons (Mark Reviewing / Add to Watchlist / Ignore / Archive) wired and verified
- Human Notes section added to detail page; uses existing `PATCH /api/investment/situations/{id}` with `{ notes }` body; `saveNotes()` added to `lib/api.ts`
- `/investment/watchlist` route added — green-themed, filters `status === 'watchlist'` client-side; accessible via WATCHLIST → link from queue nav
- Manual v2 preview button added to detail page; calls `POST /api/investment/evaluate-v2` with `save_to_db: false` hardcoded — zero persistence risk
- v1 remains default evaluator; v2 remains manual-preview only — no cron changes, no scan calls, no live AI during implementation, no backend changes
- TypeScript build passed; deployed via `scripts/deploy_frontend.ps1` — validated

**Sprint 2 — Investment Evaluations quick filters (2026-04-30):**
- Added workflow status quick filter pills (All / Detected / Reviewing / Watchlist / Ignored / Archived) above the evaluations table
- Each pill shows a live count from the current dataset
- Active pill is visually highlighted (cyan glow)
- Removed the dead "Status" dropdown from Filter Parameters (it was never sent to the backend — dead state)
- Quick filter is now the single workflow status filter; Evaluator Version / Playbook Status / Recommendation dropdowns remain unchanged
- Quick filters respect existing Show test/demo data and Show archived toggles
- No backend changes required; frontend-only diff in `frontend/app/investment/evaluations/page.tsx`
- Pending deploy: `scripts/deploy_frontend.ps1`

Next.js frontend scaffolded in `frontend/` with dark sci-fi Mission Control theme. All 5 routes operational: home (`/`), agent roster (`/agents`), agent detail (`/agents/[agent_name]`), investment evaluations queue (`/investment/evaluations`), evaluation detail (`/investment/evaluations/[id]`). TypeScript build passed. Smoke test passed. Frontend API interface fixed (agent `status` → `current_status`). Frontend not yet deployed; local usage validated with real backend data.

All 16 logical agents are registered. Mission Control is live. `scripts/ingest_course.py` rewritten with two-stage extraction, verbatim-leak detector, `--chapters` list flag, `--max-cost` guard, and disk-read early exit for idempotency. All 22 chapters extracted → 132 files in `course_index/`. Zero verbatim-leak warnings. Total extraction cost: ~$0.14. `master_index.json` rebuilt deterministically (7 routing types). Chapters 14, 15, 17, 22 classified as `foundational_analysis` (excluded from routing). Timestamp repair complete — all 22 chapters have `timestamp_quality: real_sentence_timestamp`.

Global Methodology Synthesis produced 7 routing-type playbooks + `_synthesis_rules.md` in `course_index/playbooks/`. All five analytical playbooks have been quality-reviewed and fixed to v1.1 (merger_arbitrage.md, merger.md, spin_off.md, tender_offer.md, bankruptcy.md). Two playbooks (proxy_fight.md, rights_offering.md) are detection-only — the course provides insufficient methodology for deep evaluation and require no further review sprint. Playbook quality review phase is complete.

Global cross-chapter artifacts complete (2026-04-29): taxonomy.md v1.0, source_map.md v1.0, risk_patterns.md v1.0, global_checklist.md v1.0, evaluation_schema.json v1.0. evaluation_schema.json validation passed.

**Investment evaluator v2 implementation complete (2026-04-29):**
- Evaluator v2 Phase 1: `backend/services/investment/playbook_loader.py` and `backend/services/investment/routing_engine.py` created; 30/30 tests passed
- Evaluator v2 Phase 2: `backend/prompts/situation_evaluator_v2.txt` created with evaluation_schema.json-compliant structure
- Evaluator v2 Phase 3: `backend/services/investment/evaluator.py` upgraded with EVALUATOR_VERSION feature flag; v1 remains default
- Evaluator v2 Phase 4: Controlled v2 test suite added (12 tests); 42/42 total tests passed; all tests use mocks (no live AI/SEC calls)
- Evaluator v2 Phase 5: Shadow testing fixtures created (5 synthetic cases); mocked E2E tests added; 23/23 evaluator tests passed
- Evaluator v2 Phase 6: Manual live shadow test complete (2026-04-29); 4 live AI calls on 2 real SEC filings (SC TO-I, SC TO-T); GO decision received
- V2 features: routing_engine for situation detection, evaluation_schema.json output, prohibited inference guard, safe v1 fallback
- V2 status: **VALIDATED WITH LIVE AI RESPONSES** — routing, schema compliance, and prohibited inference guard all functioning correctly
- V2 production status: **READY FOR LIMITED PRODUCTION TESTING** — requires explicit approval before enabling in cron or globally

---

## 4. Production Status

- FastAPI backend: **running** on private VPS
- OpenClaw (Node.js): **running** on private VPS
- PostgreSQL: **running** (used for agent_runs, ai_usage, investment_sources, special_situations)
- Redis: running (available, used by APScheduler)
- **Next.js frontend**: **deployed on VPS** as systemd service `swissedge-frontend`; running on port 3001; accessible via Tailscale only (no public exposure)
- **Deployment**: Manual deployment scripts available in `scripts/` directory:
  - `deploy_frontend.ps1` — packages frontend/, uploads via scp, deploys to /opt/swissedge/frontend (1 scp + 1 ssh)
  - `deploy_backend_files.ps1` — packages backend files, uploads via scp, deploys to /opt/swissedge (1 scp + 1 ssh)
  - SSH key auth configured; no password prompts required
  - Claude cannot deploy directly; Dani runs scripts manually from repo root
- GitHub repo: https://github.com/pradoxia/swissedge
- VPS access: via private network; privileged operations use a non-root deploy user with sudo

---

## 5. Verified Live Endpoints

All tested and returning correct responses on VPS:

| Endpoint | Status |
|---|---|
| GET `/api/health/ping` | ✅ |
| GET `/api/observability/summary` | ✅ |
| GET `/api/observability/agents` | ✅ returns all 16 registered agents |
| GET `/api/observability/runs` | ✅ |
| GET `/api/observability/mission-control` | ✅ |
| GET `/api/observability/mission-control/text` | ✅ plain text |
| GET `/api/observability/agents/{agent_name}` | ✅ full card + recent runs |
| GET `/api/observability/agents/{agent_name}/text` | ✅ plain text |
| GET `/api/observability/cron/upcoming?days=3` | ✅ Europe/Zurich tz |
| GET `/api/observability/cron/upcoming/text?days=3` | ✅ plain text |
| POST `/api/marketplace/generate-listing` | ✅ ai_usage logged |
| POST `/api/marketplace/get-price` | ✅ |
| POST `/api/marketplace/search` | ✅ (Tutti anti-bot active) |
| POST `/api/investment/scan` | ✅ SEC EDGAR |
| GET `/api/investment/situations` | ✅ |
| GET `/api/investment/sources` | ✅ returns 7 sources (4 active, 3 inactive) |
| GET `/api/marketplace/sales/items` | ✅ |
| GET `/api/marketplace/sales/items/{id}` | ✅ |
| POST `/api/marketplace/sales/items` | ✅ |
| PATCH `/api/marketplace/sales/items/{id}` | ✅ |
| POST `/api/marketplace/sales/items/{id}/generate-platform-drafts` | ✅ |
| POST `/api/marketplace/sales/telegram-intake` | ✅ |

---

## 6. Database / Observability State

- `agent_runs` table: exists, populated
- `ai_usage` table: exists; populated for `marketplace_lister` (bug fixed session 2026-04-28) and `investment_evaluator`
- `investment_sources` table: exists; **populated — 7 sources (4 active, 3 inactive)** seeded via `scripts/seed_investment_sources.py` from `config/investment_sources.yaml`
- `special_situations` table: exists
- `sales_items` table: **live on VPS — validated in production**
- `sales_item_photos` table: **live on VPS — validated in production**
- `sales_platform_listings` table: **live on VPS — validated in production**
- `research_cases`, `research_tasks`, `research_documents`, `research_sources`, `historical_cases`, `source_intelligence_suggestions`, `public_article_drafts`: **live on VPS — migration c3d4e5f6a7b8 applied; all 16 FK constraints verified**
- 16 logical agents registered in `backend/services/observability/agent_registry.py`
- `marketplace_lister` now logs ai_usage correctly (was bug: used `complete()` instead of `complete_with_usage()`)
- Claude Code sessions can be logged via `POST /api/observability/claude-session`
- Costs and tokens tracked where provider usage is available; falls back to character-based estimate when not
- `run_logger.py` wraps all observability calls in try/except — a DB failure never breaks business logic

---

## 7. Registered Logical Agents (16)

| Agent | Status | Runtime |
|---|---|---|
| claude_engineer | active | claude_code |
| openclaw_operator | active | openclaw |
| telegram_router | active | openclaw |
| system_doctor | active | fastapi+cron |
| security_auditor | active | claude_code |
| marketplace_lister | partial | fastapi |
| marketplace_pricer | active | fastapi |
| marketplace_searcher | pending | fastapi |
| marketplace_safety_guard | partial | fastapi+openclaw |
| investment_scanner | active | fastapi+cron |
| investment_classifier | active | fastapi |
| investment_evaluator | active | fastapi |
| course_reference_agent | partial | fastapi |
| source_registry_manager | active | fastapi |
| publisher_agent | partial | fastapi |
| contact_discovery_agent | future | future |

**partial** = implemented but known limitation or incomplete wiring.
**pending** = endpoint exists but agent tracking not fully separated yet.
**future** = not yet implemented.

---

## 8. Telegram / OpenClaw Status

- **OpenClaw** is the active Telegram handler (Node.js), running on the private VPS
- OpenClaw instruction file was updated 2026-04-28 with 6 new Mission Control commands
- OpenClaw should now support:

| Command | Action |
|---|---|
| `mission control` / `control` | GET /api/observability/mission-control/text |
| `agentes` | GET /api/observability/agents → formatted Spanish list |
| `agente <agent_name>` | GET /api/observability/agents/{agent_name}/text |
| `cron` | GET /api/observability/cron/upcoming/text?days=3 |
| `costes` | GET /api/observability/summary → Spanish summary |
| `errores` | GET /api/observability/runs?status=failed → Spanish list |

- Existing commands also supported: `estado`, `scan`, `situaciones`, `watchlist`, `precio`, `buscar`, `logs`, `ayuda`
- **Sales intake via OpenClaw** (`quiero vender <item>`): maps to `POST /api/marketplace/sales/telegram-intake`; returns `reply_es` which OpenClaw sends verbatim — do not call `generate-listing` on sales trigger; patch documented in `docs/openclaw-sales-intake-patch.md`; **requires VPS edit of `/root/.openclaw/workspace/SWISSEDGE.md` and openclaw restart**
- **Deterministic Python bot** (`backend/services/telegram/bot.py`): fully updated with sales handlers, `telegram-intake` calls, `active_item_id` tracking; `deploy/systemd/swissedge-telegram-bot.service` created; full deploy guide at `docs/swissedge-telegram-bot-deploy.md`; **not active — pending deploy decision**
- Two Telegram polling sources cannot run simultaneously; if Python bot is deployed, OpenClaw Telegram polling must be disabled first (see `docs/swissedge-telegram-bot-deploy.md` Step 1)

---

## 9. Marketplace Status

> **Status as of 2026-05-01: PAUSED** — Marketplace Sales is validated in production (3 DB tables live, all Sales API endpoints confirmed, frontend routes operational). Further Sales development (photo storage, bot deploy, pricing agent) is paused while Investment Research Platform design sprint runs. Telegram/OpenClaw is not reliable for DB writes — structured intake must go through deterministic Python bot or direct API. Resume when Investment design sprint is complete.

**Sales-first orientation** — buying features (price comparison, search) are operational but deferred; selling workflow is the primary focus.

### Selling (Sales Automation — implemented, pending deploy)
- **Sales Items API** fully built: POST /items, GET /items, GET /items/{id}, PATCH /items/{id}, POST /telegram-intake, POST /items/{id}/generate-platform-drafts
- **`POST /telegram-intake`**: single-call deterministic endpoint — creates SalesItem + 4 platform listing rows, returns Spanish reply; no AI on intake
- **Status machine**: `needs_info → ready_to_list → listed → sold / archived`; auto-promotion when all required fields present
- **Platform coverage**: Ricardo.ch, Tutti.ch, Anibis.ch, Facebook Marketplace CH (4 rows auto-created per item)
- **Frontend**: `/marketplace/sales/items` (list) + `/marketplace/sales/items/[id]` (detail with 6 tabs); deployed but awaiting Alembic migration on VPS
- **Generate platform drafts**: `POST /items/{id}/generate-platform-drafts` calls listing AI once, writes Hochdeutsch text to all 4 platform rows
- **No auto-publish** — all listings require explicit human approval before any platform action

### Selling pipeline — 10-item roadmap (in priority order)
1. Photo storage endpoint (`POST /sales/items/{id}/photos`)
2. Trash lifecycle (soft-delete for items and photos)
3. **Deploy deterministic bot** (`swissedge-telegram-bot.service`) — or apply OpenClaw SWISSEDGE.md patch as interim
4. Photo attach: accept Telegram photo in Python bot → upload to backend → link to item
5. Follow-up answers: bot PATCH fields when Dani answers intake questions
6. Comparable research: fetch Ricardo/Tutti listings for price context
7. Pricing agent: suggest CHF price based on comparables
8. Platform draft generation trigger from Telegram (after all fields collected)
9. Buyer question relay (Telegram → Dani confirmation → buyer reply)
10. Ricardo.ch API integration (Phase 2 adapter)

### Buying (deferred)
- `POST /api/marketplace/generate-listing` — works; generates Hochdeutsch listing; logs agent_runs + ai_usage
- Price comparison (`get-price`) — works; uses Tutti.ch HTTP scraper
- **Tutti.ch scraper currently blocked by 403 / anti-bot** — listing generation works but live price search may return empty
- Automatic publishing is **not enabled** — all listings require human approval before publish

---

## 10. Investment Research Platform

### Strategic Definition (2026-05-01)

SwissEdge Investment is **not only a scanner**. It is a **private investment research desk** for identifying, investigating, documenting, learning from, and eventually publishing structured research on special situations.

**Core vision:**
1. **Identify** special situations appearing in the market (SEC EDGAR + future sources)
2. **Investigate** each situation deeply using public sources: company website, investor relations pages, press releases, SEC filings, presentations, investor meeting materials, public news, management/board information, historical market context
3. **Explain** the situation: what it is, why it may be interesting, what must be checked, what risks matter, what the course methodology says, what information is missing, what manual actions Dani must take
4. **Study historical cases**: whether SwissEdge could have participated, when the opportunity was visible, what the entry window was, who was discussing it, what sources were useful, what lessons should improve future source discovery
5. **Improve source intelligence** over time using historical and active case learnings
6. **Publish** findings as structured public educational/community content — separate from private Mission Control — with manual review before publication

**Investment recommendation guardrail (public-facing):**
Avoid direct buy/sell language in public output. Use status labels only: `monitor` / `not actionable` / `needs more work` / `candidate for further research`

---

### Current System State (preserved)

- Investment Evaluations queue: ✅ operational
- Evaluation detail pages: ✅ operational
- Watchlist: ✅ operational
- Human notes: ✅ operational
- Sources page: ✅ operational (7 sources: 4 active, 3 inactive)
- Radar Status: ✅ operational (read-only)
- SEC EDGAR scanner: ✅ operational (EFTS query fixed 2026-04-30)
- v1 evaluator: ✅ **production default**
- v2 evaluator: manual-preview only — validated, not yet in cron
- Scanner does **not** yet read from `investment_sources` DB table — hardcoded to `SECEdgarAdapter` (Sprint 17 gap)
- Source attribution is **inferred** from `filing_url`/`filing_type`, not stored as FK
- Course extraction: complete (22 chapters, 132 files, `course_index/playbooks/`)
- Global artifacts: taxonomy.md, source_map.md, risk_patterns.md, global_checklist.md, evaluation_schema.json — all v1.0, complete
- All 7 playbooks quality-reviewed; merger_arbitrage.md and merger.md evaluator-ready; spin_off, tender_offer, bankruptcy PARTIAL; proxy_fight and rights_offering detection-only

---

### Investment Source Strategy

Current `investment_sources` DB table holds 7 entries (SEC EDGAR + scaffolded placeholders). This is **incomplete**. The full source universe must be deep-mined from `course_index/` and includes:

- Company IR pages
- Press releases and 8-K/6-K filings
- Investor presentations and proxy materials
- Financial news sources and newsletters
- Public expert blogs, activist/proxy sources
- Court and bankruptcy dockets
- X/Twitter accounts (public, methodology-relevant)
- Other course-identified source categories (see `source_map.md`)

Sources enable/disable toggle is operational in the UI but has no effect on scans yet (Sprint 17 gap).

---

### Investment Research Platform Redesign — Next Strategic Block

**Step 1 — Design sprint (documentation first, no code):**
1. Create `docs/investment-research-platform-redesign.md` covering:
   - Full product definition
   - Agent network (scanner, researcher, historian, source intelligence, publisher)
   - Research brief output format (14-section template — see below)
   - ResearchCase lifecycle: `detected → brief_generated → under_investigation → documented → archived / published`
   - HistoricalCase lifecycle: `seed → reconstructed → lessons_extracted → source_intel_applied`
   - Source intelligence lifecycle: how active and historical cases feed back into `investment_sources`
   - Publishing workflow: private research → editorial review → public article draft → published

2. **Course Deep Mining sprint:**
   - Extract all sources mentioned in the course (people, newsletters, blogs, accounts, websites, documents, court sources, activist sources, public databases)
   - Extract historical case examples and situations discussed in the course
   - Extract analysis patterns and research workflows
   - Output: seed data for `investment_sources` + `historical_cases` tables

**Step 2 — Data model design:**
- `ResearchCase` — linked to `SpecialSituation`; holds structured research brief
- `ResearchDocument` — individual source documents attached to a case (filing, press release, presentation)
- `ResearchSource` — ephemeral source reference used during a specific research session
- `ResearchTask` — manual action item generated by the research agent for Dani
- `HistoricalCase` — past special situation reconstructed for learning
- `PublicArticleDraft` — editorial output from a documented case; not published without explicit approval

**Step 3 — Agent design:**
- **Situation Research Agent** — given a `SpecialSituation`, generate a structured research brief; include company context, board/management, documents, timeline, risks, missing info, source intelligence
- **Historical Case Study Agent** — reconstruct past special situations; identify timing, sources, entry window, lessons
- **Source Intelligence Agent** — identify useful sources from historical and active cases; suggest additions to `investment_sources`
- **Publishing Pipeline** — convert private research into public educational/community content; manual review gate before any publication

**Research brief target output (14 sections):**
1. Executive Summary
2. Situation Type
3. Why It May Be Interesting
4. Course Methodology Reference
5. Company Context
6. Board / Management
7. Key Documents
8. Timeline
9. Risk Analysis
10. What To Verify Before Investing
11. Missing Information / Manual Tasks for Dani
12. Source Intelligence (sources that yielded useful signal)
13. Investment Readiness (monitor / not actionable / needs more work / candidate)
14. Public Summary Draft (editorial; not published without approval)

---

### Investment Outputs Guardrail (non-negotiable)

- Every investment output includes: "Este análisis es educativo. No es asesoramiento financiero."
- Public-facing material uses status labels only — never direct buy/sell language
- All publishing requires explicit manual approval — no auto-publish
- Source attribution must not expose private credentials or internal system details

---

## 11. Cron Status

- System cron jobs exist on VPS for: SEC investment scan (every 6h), watchlist follow-up (daily 09:00), health checks
- `GET /api/observability/cron/upcoming/text?days=3` reads system crontab and user crontabs; shows next 3-day schedule in Europe/Zurich timezone
- Secrets are redacted from cron command lines in the output
- OpenClaw crons are **not the source of truth** for SwissEdge scheduling — system crontab is
- `cron_reader.py` falls back to `sudo crontab -u root -l` when the root spool file is not readable; root cron entries (including investment scan) are now visible in the cron endpoint
- `croniter==3.0.3` explicitly pinned in `requirements.txt`; installed on VPS

---

## 12. Git / Repository Status

- GitHub: https://github.com/pradoxia/swissedge
- Branch: `main`
- Last commit: observability foundation (`feat: initial SwissEdge platform observability foundation`)
- **Intentionally excluded from Git** (via .gitignore or manual exclusion):
  - `.env` — all environment secrets
  - `scripts/` — VPS config, deployment scripts, private credentials
  - `course/` — raw course transcripts (private/copyrighted)
  - `Curso de Arte de Invertir/` — course audio/video/materials
  - `course_index/` — git-ignored; only sanitized, non-copyrighted methodology schemas, generic checklists and high-level summaries may be committed after explicit review
  - `SYSTEM.md` — operational state file
  - `claude-code-sessions.md` — session log with possible operational details
  - `docs/engineering-log.md` — engineering session log
  - `docs/claude-code-usage.md` — session cost log
  - `docs/openclaw-observability.md` — operational observability notes
  - `swissedge-documentation.pptx` — generated documentation with possible operational details
  - `/root/.openclaw/workspace/SWISSEDGE.md` — lives on VPS only

---

## 13. Known Issues

| Issue | Severity | Notes |
|---|---|---|
| No authentication layer yet | Medium | Frontend protected by Tailscale network isolation only; add basic auth before any public exposure consideration |
| Frontend uses port 3001 | Low | Port 3000 was occupied on VPS; systemd service configured for 3001 |
| Scanner ignores `investment_sources` DB table | Medium | `SECEdgarAdapter` is hardcoded in scanner; sources UI (enable/disable) has no effect on actual scans yet |
| Discovery source is inferred, not stored | Low | `filing_url` and `filing_type` used for inference; no DB field for source_id on special_situations |
| Duplicate/test evaluation rows exist | Low | Manual testing created duplicate evaluations; add cleanup or hide-test-data strategy later |
| Limited v2 evaluation sample size | Low | Four evaluations tested (SC TO-I, SC TO-T, Form 10, 8-K liquidation); covers main situation types but limited volume |
| Disclaimer encoding in PowerShell output | Low | "Este análisis..." appears as "Este anÃ¡lisis..." in curl output; check if visible in browser UI |
| Tutti.ch scraper blocked (403) | Medium | Listing generation still works via AI; price search may be empty |
| timestamp_refs are proportional, not word-matched | Low | Navigation is reliable; exact word-match lookup requires future word-alignment sprint |
| proxy_fight.md / rights_offering.md detection-only | Medium | Course does not provide evaluation methodology for these types; do not attempt deep evaluation |
| ch08 contains pedagogical/broker/mindset content | Low | Must not pollute filing-evaluable investment criteria when building global playbooks |
| Standalone Telegram bot not active | Medium | `swissedge-telegram-bot.service` created and ready; deploy guide at `docs/swissedge-telegram-bot-deploy.md`; requires OpenClaw Telegram polling disabled first to avoid 409 conflicts |
| Sales Alembic migration not run on VPS | ~~High~~ | **Resolved** — migration `b2c3d4e5f6a7` confirmed run; 3 tables live in production |
| OpenClaw not reliable for Sales intake DB writes | High | OpenClaw (GPT-based) fails to consistently call `telegram-intake` correctly; use deterministic Python bot (`swissedge-telegram-bot.service`) or direct API; intake via OpenClaw not recommended |
| OpenClaw token/cost usage not tracked in FastAPI | Medium | OpenClaw's own AI calls are not in agent_runs/ai_usage yet |
| `marketplace_searcher` logged under `marketplace_pricer` | Low | Naming mismatch; needs agent_name split when confirmed |
| `course_reference_agent` returns empty if course_index missing | Medium | course_index must exist on VPS — deploy not done yet |
| Course source references are chapter-level only | Low | `source_map.md` contains no video names or minute timestamps; PLACEHOLDER_COURSE_REFS and FUTURE_SOURCES in sources page.tsx show "Timestamp not available" — enrich only if Dani requests |
| `ResearchSource ↔ HistoricalCase` ORM relationship missing | ~~Low~~ | **Resolved in Phase 1B** — `HistoricalCase.sources` + `ResearchSource.historical_case` added with `back_populates`; no migration needed |

---

## 14. Next Recommended Tasks (in order)

### Investment Research Platform — Phase 6A Public Site Concept to Visual Prototype (active — primary track)
1. Define the public SwissEdge brand experience and first-viewport concept.
2. Prototype the public site direction without exposing private research notes, internal IDs, operational metadata, or unpublished draft content.
3. Keep publishing manual-only; Phase 5 remains a private editorial workflow.

Phase 5 deployed guardrails remain active:
- No auto-publish.
- No Substack API integration yet.
- No public posting.
- No buy/sell language.
- Educational content only.
- Manual approval required.
- Public drafts must not expose private notes, internal IDs, VPS details, or operational metadata.
- AI may help draft, but output must be reviewed manually.

### Deferred Investment Items
1. **Phase 4D — Apply Approved Proposals to Case Sources** — deferred; do not implement now.
2. Apply approved source suggestions to `investment_sources`.
3. Scanner source registry wiring.

### Recommended Follow-up
1. Phase 6B — Screenshot-backed User Guide.
2. Phase 6C — Public Research Article Template Polish.
3. Phase 6D — Substack Manual Publishing Workflow.
4. Investment Research Cleanup 1 — Preview UI and API Helper Extraction.

### Sales Roadmap (paused — resume after Investment design sprint)
6. **Deploy deterministic Python bot** — follow `docs/swissedge-telegram-bot-deploy.md`; disable OpenClaw Telegram → scp service file → enable + start `swissedge-telegram-bot.service` → smoke test
7. **Photo storage endpoint** — `POST /sales/items/{id}/photos` to accept base64 or URL, store in `sales_item_photos`
8. **Photo attach in bot** — accept Telegram photo → upload to backend → link to active item
9. **Follow-up answer collection** — bot PATCH fields as Dani responds to intake questions
10. **Pricing agent** — comparable research from Ricardo/Tutti + CHF price suggestion

### Deferred
- **Basic auth** — before any public exposure; HTTP Basic Auth or NextAuth.js
- **Tutti.ch proxy** — if Dani requests live price search; add `SCRAPERAPI_KEY` to `.env`
- **Ricardo.ch adapter** — Phase 2; requires API agreement

---

## 15. How to Start a New Session

Paste this at the start of every session:

> Read `PROJECT_STATE.md`, `docs/decisions.md`, `CLAUDE.md`, and only files directly relevant to the task. Summarize current state in 10 lines. Do not scan the whole repo.

---

## 16. Session Closing Rule

At the end of every sprint:
1. Update `PROJECT_STATE.md` — current phase, production status, known issues, next tasks.
2. Update `docs/decisions.md` only if an architecture decision changed.
3. Confirm no secrets, IPs, service names or credentials were introduced into either file.

Next sessions start by reading `PROJECT_STATE.md`, `docs/decisions.md`, `CLAUDE.md`, and only task-relevant files. Do not scan the whole repo.

---

## 17. Do-Not-Do List

- Do not commit secrets, tokens, passwords, IPs or raw .env content
- Do not commit course transcripts, audio or video
- Do not expose private IPs, Tailscale addresses or VPS credentials
- Do not automate listing publishing without explicit human approval
- Do not treat OpenClaw as business logic — it is an operator that calls FastAPI
- Do not build the frontend before backend control and observability are stable
- Do not change investment logic without a course methodology review
- Do not integrate course outputs into investment_evaluator until Timestamp Repair, Global Methodology Synthesis, and evaluator upgrade are all complete
- Do not commit course_index/
- Do not treat foundational_analysis as a routing type
- Do not treat timestamp_refs as exact word-match positions — they are proportionally distributed; use for chapter navigation only
- Do not run VPS-mutating commands (restart, migrate, deploy) without explicit "deploy" or "apply" instruction
- Do not publish investment research publicly without explicit manual approval — no auto-publish at any stage
- Do not use direct buy/sell language in public-facing investment output — use status labels (monitor / not actionable / needs more work / candidate)
- Do not make architecture decisions — implement approved specs, ask if ambiguous
- Do not add features beyond what the current task requires
