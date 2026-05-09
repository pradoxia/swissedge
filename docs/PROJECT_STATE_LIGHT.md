# SwissEdge — Compact Session Handoff

> Full canonical state: `docs/PROJECT_STATE.md`
> Architecture decisions: `docs/decisions.md`
> Last updated: 2026-05-03 (Phase 5 COMPLETE AND DEPLOYED — PublicArticleDraft from ResearchCase, private editorial review workflow, Markdown/Substack-ready export, publishing checklist/manual approval gate; validated by Dani)

---

## 1. Project Purpose

SwissEdge is a modular AI platform with two domains:
- **Investment Research Desk** — detects, investigates, documents, and eventually publishes structured research on special situations (SEC EDGAR + future sources).
- **Marketplace Assistant** — generates Hochdeutsch listings for Swiss second-hand platforms. **Status: PAUSED/PRESERVED** — all code and DB tables live; no changes until explicitly scoped.

---

## 2. Investment Research Platform — Phase Status

| Phase | Description | Status |
|---|---|---|
| 1A | DB tables (7 models, Alembic migration `c3d4e5f6a7b8`) | DEPLOYED — tables live, 16 FK constraints verified |
| 1B | ResearchCase API (CRUD endpoints + Pydantic schemas) | DEPLOYED |
| 1C | Frontend `/investment/research` list + detail pages | DEPLOYED |
| 1D | Evaluation Detail → ResearchCase panel | DEPLOYED |
| 1E | Research Workspace: manual Tasks/Documents/Sources add-edit | DEPLOYED |
| 1F | Research Brief Skeleton — manual 14-section editor | DEPLOYED |
| 1G | Research Workspace Polish — header, workflow strip, section hints, empty states | DEPLOYED |
| 1H | Deploy + Smoke Test | DEPLOYED — validated by Dani |
| 2A | AI Research Brief Preview — manual trigger, preview panel, section-select apply | DEPLOYED |
| 2B | Apply + Save Confirmation — explicit apply-selected, merge with existing brief | DEPLOYED |
| 2C | Metadata-only UX notice — document/source URLs metadata-only warning in preview panel | DEPLOYED |
| 2D | Research Quality Checklist — AI checklist + suggested status/readiness, assistive only | DEPLOYED |
| 2E | AI Status / Readiness Assist — apply buttons for suggested status + readiness | DEPLOYED |
| 3A | Document/Source UI Enrichment — doc_type selector, signal_quality editor, metadata-only labels, snippet field, notes field for tags | DEPLOYED |
| 3B | Manual Snippet Capture — paste text into document summary field, save on explicit button, copyright warning | DEPLOYED |
| 3C | AI Document Analysis Preview — POST /api/investment/research-documents/{id}/analysis-preview, saved_to_db: false | DEPLOYED |
| 3D | Source Intelligence Preview — POST /api/investment/research-cases/{id}/source-intelligence-preview, saved_to_db: false, proposals only | COMPLETE AND DEPLOYED — validated by Dani |
| 3E | Source Intelligence Approval — design doc prepared, now implemented as Phase 4A | IMPLEMENTED AS 4A |
| 4 | Source Intelligence + Historical Cases — approval queue, approve/reject proposal workflow, historical cases manual workspace, historical case source intelligence preview/proposals | COMPLETE AND DEPLOYED — validated by Dani |
| 4A | Source Intelligence Approval Queue — save proposals, approve/reject per suggestion, no apply to investment_sources | COMPLETE AND DEPLOYED — validated by Dani |
| 4B | Historical Case Workspace — manual create/list/get/patch, status lifecycle, seed notes, reconstruction | COMPLETE AND DEPLOYED — validated by Dani |
| 4C | Historical Case Source Intelligence Preview — POST /api/investment/historical-cases/{id}/source-intelligence-preview, saved_to_db: false | COMPLETE AND DEPLOYED — validated by Dani |
| 4D | Apply Approved Proposals to Case Sources | DEFERRED — do not implement now |
| 5 | Publishing / Substack Workflow | COMPLETE AND DEPLOYED — validated by Dani |
| 5A | Public Article Draft from ResearchCase | COMPLETE AND DEPLOYED — validated by Dani |
| 5B | Editorial Review Workflow | COMPLETE AND DEPLOYED — validated by Dani |
| 5C | Markdown/Substack Export | COMPLETE AND DEPLOYED — validated by Dani |
| 5D | Publishing Checklist + Manual Approval Gate | COMPLETE AND DEPLOYED — validated by Dani |
| 6 | Public Site / Brand Experience / User Documentation | PAUSED |
| 6A | Public Site Concept to Visual Prototype | PAUSED |

**Phase 1 COMPLETE AND DEPLOYED. Phase 2 COMPLETE AND DEPLOYED. Phase 3 COMPLETE AND DEPLOYED — validated by Dani. Phase 4 COMPLETE AND DEPLOYED — validated by Dani. Phase 5 COMPLETE AND DEPLOYED — validated by Dani. Next active track: Investment Platform V2 — Source-Driven ResearchCase Pipeline. Public Site / Brand Experience / User Documentation is paused.**

**Investment Platform V2 deployed notes:** Sprint A scanner funnel diagnostics implemented and deployed. Sprint B Research Inbox read-only implemented and deployed. Sprint B.1 Research Inbox UI polish implemented and deployed. Sprint C V2 ResearchCase metadata implemented and deployed; Alembic revision `d4e5f6a7b8c9` applied. Sprint E manual create-from-situation bridge initializes V2 metadata for SEC/evaluation-linked ResearchCases locally and pending deploy. Sprint F created `swissedge-ai-context` as an AI-safe documentation layer. Sprint F: AI-Safe Context Architecture - `swissedge-ai-context` project layer created, with AI-safe context structure being completed through Sprint F.1. No runtime code changes. Sprint G created Agent Ops + Fontana architecture docs; no runtime behavior changed. Sprint G/G.1: Agent Ops + Fontana architecture docs completed, including data model, API, UI, metrics, routing audits, and ADRs. Documentation only; no runtime changes. Sprint H Agent Ops backend foundation implemented locally/pending deploy: tables, read-only API, proposal PATCH, fail-safe logger skeleton. No scanner/evaluator integration yet. Sprint H.1 fixes backend deploy allowlist for Agent Ops migration and modules. No runtime code changed. Sprint I adds initial `/agent-ops` Mission Control UI locally/pending deploy. It is read-only except proposal status review and does not connect Agent Ops to scanner/evaluator. No source-driven intake, scan behavior, cron, global v2, live AI, publishing, or Marketplace/Sales changes in any of these sprints.

**Phase 3 summary (all validated by Dani):**
- 3A: Document/Source UI enrichment live (doc_type, signal_quality, metadata-only labels, snippet, notes)
- 3B: Manual document snippet capture live (explicit save, copyright warning, no URL fetching)
- 3C: AI document analysis preview live (`saved_to_db: false`, no URL fetching, no auto task creation)
- 3D: Source intelligence preview live (`saved_to_db: false`, proposals-only, no `investment_sources` writes, no auto-apply, no URL fetching/crawling)

**Phase 4A+4B+4C deployed notes (2026-05-02):**
- 4A: SourceIntelligenceSuggestion approval queue is live — `POST /research-cases/{id}/source-intelligence-suggestions`, `GET /source-intelligence-suggestions`, `PATCH /source-intelligence-suggestions/{id}` (approve/reject only); no apply endpoint; no `investment_sources` write
- 4B: HistoricalCase manual workspace is live — `POST/GET/GET/{id}/PATCH /api/investment/historical-cases`; status lifecycle: seed → reconstructed → lessons_extracted → source_intel_applied; no migration (table already live)
- 4C: Historical Case Source Intelligence Preview — `POST /historical-cases/{id}/source-intelligence-preview`; `saved_to_db: false`; uses stored notes/reconstruction only; no URL fetching; save-proposals endpoint also added for historical cases
- Frontend: `/investment/historical-cases`, `/investment/historical-cases/[id]`, `/investment/source-intelligence` (approval queue)
- ResearchCase source intelligence panel updated: "Save proposals to queue" button + saved proposals list with approve/reject inline
- Dani smoke test validated: Source Intelligence queue loads; proposals can be reviewed; approve/reject works; no apply-to-`investment_sources` button is present; historical cases route loads; minimal historical case creation works; detail opens; notes/status edits persist.
- 31/31 tests passed before deploy; npm run build 0 errors before deploy; no live AI called in tests; no migration needed; no scanner/cron/v2 changes; no publishing; no buy/sell language.
- Phase 4D apply-to-case-sources is deferred. No `investment_sources` writes exist. No scanner registry writes exist. No automatic apply exists.

**Phase 5A+5B+5C+5D deployed notes (2026-05-03):**
- 5A: `POST /api/investment/research-cases/{id}/public-draft` creates a private `PublicArticleDraft` from ResearchCase brief/tasks/documents/sources metadata; no AI; no external calls; no private notes or internal IDs in public output.
- 5B: `GET/PATCH /api/investment/public-drafts/{id}` supports private editorial review and status workflow: `draft -> in_review -> approved -> archived`; direct `draft -> approved` is blocked; approval is blocked if title/body/disclaimer are missing or buy/sell/internal metadata is detected.
- 5C: `GET /api/investment/public-drafts/{id}/markdown` returns Substack-ready Markdown for manual copy/export only; no Substack API integration and no public posting.
- 5D: Frontend public draft detail includes publishing checklist, manual approval gate, backend validation warnings, disclaimer, and "PRIVATE DRAFT - NOT PUBLISHED" labels.
- Frontend: `/investment/public-drafts`, `/investment/public-drafts/[id]`, and ResearchCase detail Public Draft panel.
- Dani smoke test validated: Public Draft can be created from ResearchCase; draft detail opens; private/not-published labels are visible; draft can be edited; `draft -> in_review -> approved` works; direct `draft -> approved` is blocked; approval blocks missing disclaimer and buy/sell language; clean approval works; Markdown/Substack-ready copy/export works.
- No auto-publish; no Substack API; no external posting; no migration; no scanner/cron/v2 changes; no buy/sell language allowed.

**Quality Assist guardrail:** `suggested_status: published` is hard-blocked by the parser. If AI returns `published`, it is downgraded to `documented` (when `brief_completeness` is true) or `under_investigation` (otherwise), and a warning is appended. `published` status requires manual editorial approval only.

---

## 3. Current Frontend Routes

| Route | Description | Status |
|---|---|---|
| `/` | Mission Control home | DEPLOYED |
| `/investment/evaluations` | Evaluation queue | DEPLOYED |
| `/investment/evaluations/[id]` | Evaluation detail + Research Case panel | DEPLOYED |
| `/investment/research-inbox` | Research Inbox read-only — existing ResearchCases with V2 metadata when present and legacy/manual fallback labels | IMPLEMENTED LOCALLY — pending deploy |
| `/investment/research` | Research Cases list | DEPLOYED |
| `/investment/research/[id]` | Research Case detail + workspace + AI Brief Preview + Quality Assist + Source Intelligence Panel (save/approve/reject) | DEPLOYED |
| `/investment/watchlist` | Watchlist (status filter) | DEPLOYED |
| `/investment/radar-status` | Scanner observability (read-only) | DEPLOYED |
| `/investment/sources` | Source registry + toggles | DEPLOYED |
| `/investment/historical-cases` | Historical Cases list + create | DEPLOYED — validated by Dani |
| `/investment/historical-cases/[id]` | Historical Case detail + notes + Source Intelligence Preview + approval | DEPLOYED — validated by Dani |
| `/investment/source-intelligence` | Source Intelligence Approval Queue (all cases) | DEPLOYED — validated by Dani |
| `/investment/public-drafts` | Public Article Draft editorial queue | DEPLOYED — validated by Dani |
| `/investment/public-drafts/[id]` | Public draft editor, Markdown export, publishing checklist | DEPLOYED — validated by Dani |
| `/agents`, `/agents/[name]` | Agent roster + detail | DEPLOYED |
| `/marketplace/sales/items` | Sales list | DEPLOYED (paused domain) |
| `/marketplace/sales/items/[id]` | Sales detail | DEPLOYED (paused domain) |

---

## 4. Backend Endpoint Groups

| Group | Prefix | State |
|---|---|---|
| Health | `/api/health` | Live |
| Observability | `/api/observability` | Live |
| Investment Situations | `/api/investment/situations`, `/api/investment/sources`, `/api/investment/scan`, `/api/investment/evaluate-v2` | Live |
| Research Cases | `/api/investment/research-cases`, `/api/investment/research-tasks` | Live |
| Research Brief Preview | `POST /api/investment/research-cases/{id}/generate-brief-preview` | Live |
| Research Quality Preview | `POST /api/investment/research-cases/{id}/quality-preview` | Live |
| Document Analysis Preview | `POST /api/investment/research-documents/{id}/analysis-preview` | Live |
| Document/Source PATCH | `PATCH /api/investment/research-cases/{id}/documents/{doc_id}`, `PATCH .../sources/{src_id}` | Live |
| Source Intelligence Preview | `POST /api/investment/research-cases/{id}/source-intelligence-preview` | Live |
| Source Intelligence Suggestions (4A) | `POST /research-cases/{id}/source-intelligence-suggestions`, `GET /source-intelligence-suggestions`, `PATCH /source-intelligence-suggestions/{id}` | Live — validated by Dani |
| Historical Cases (4B) | `POST/GET /api/investment/historical-cases`, `GET/PATCH /api/investment/historical-cases/{id}` | Live — validated by Dani |
| Historical Case Source Intelligence (4C) | `POST /api/investment/historical-cases/{id}/source-intelligence-preview`, `POST /api/investment/historical-cases/{id}/source-intelligence-suggestions` | Live — validated by Dani |
| Public Article Drafts (5A-5D) | `POST /research-cases/{id}/public-draft`, `GET/PATCH /public-drafts`, `GET /public-drafts/{id}/markdown` | Live — validated by Dani |
| Marketplace | `/api/marketplace` | Live (paused domain) |
| Sales | `/api/marketplace/sales` | Live (paused domain) |

---

## 5. Readiness Labels

Only these four values are valid for `investment_readiness` on `ResearchCase`:

- `monitor`
- `not_actionable`
- `needs_more_work`
- `candidate`

API returns 400 for any other value.

---

## 6. Hard Guardrails

**Never do these without explicit instruction from Dani:**

- `/scan` endpoint — no scanner trigger
- Cron changes — no new or modified cron entries
- v2 evaluator globally — v1 is production default; v2 is manual-preview only
- Live AI calls during implementation
- Deploy (`scripts/deploy_backend_files.ps1`, `scripts/deploy_frontend.ps1`)
- DB migrations (`alembic upgrade`)
- Service restarts
- Marketplace/Sales changes — domain is paused/preserved
- Secrets, IPs, VPS hostnames, Tailscale addresses in any file
- Raw course material or `course_index/` content
- Buy/sell language in any investment output

---

## 7. Claude Working Rules

1. Read `PROJECT_STATE_LIGHT.md` first (this file).
2. Read `docs/PROJECT_STATE.md` only if task requires deep context not covered here.
3. Read only files directly relevant to the task — no full repo scan.
4. One-pass implementation: implement exactly what is specified.
5. Update `docs/PROJECT_STATE.md` once at end of sprint — not during.
6. Update `docs/decisions.md` only if an architecture decision changed.
7. Confirm no secrets introduced before closing any sprint.
8. Every new AI/external API endpoint must use `run_logger.start_run()` / `finish_run()` / `fail_run()` wrapped in try/except.

---

## 8. Next Recommended Sprint

**Investment Platform V2 — Source-Driven ResearchCase Pipeline** is the next active track.

V2 focus:
- Make `investment_sources` the operational source registry.
- Move from scanner-created `SpecialSituation` rows toward source-driven preliminary ResearchCases.
- Define the Research Inbox as the main manual queue.
- Make SEC EDGAR the first fully operational source-driven intake path.
- Keep analytical output grounded in processed course methodology artifacts.
- Preserve current private research and publishing workflows while Public Site work remains paused.

**Next recommended sprint:** Agent Ops backend foundation after review.

V2 sprint history (all deployed except Sprint D which is local/pending):
- Sprint A: scanner funnel diagnostics, UI truthfulness, SEC EDGAR 429 fix.
- Sprint B: `/investment/research-inbox` read-only page over existing ResearchCases; legacy/V2 fallback labels.
- Sprint B.1: Research Inbox UI polish.
- Sprint C: V2 ResearchCase metadata additive migration (`d4e5f6a7b8c9`); 14 nullable fields on `research_cases`; frontend inbox prefers real V2 metadata with legacy fallback.
- Sprint C.1: deploy script updated to include Sprint C migration file; deployment notes added.
- Sprint D: ResearchCase detail V2 metadata read-only panel added; `/investment/internal-audit` read-only page created; Internal Audit card added to Mission Control; nav link added to Research Inbox. Local — pending deploy.
- Sprint E: existing manual `SpecialSituation` / Evaluation -> Create ResearchCase flow initializes V2 metadata, initial verification tasks, and a metadata-only source for SEC/evaluation-linked cases. Local — pending deploy.
- Sprint F: `swissedge-ai-context` AI-safe documentation layer created. Local — pending deploy/review.
- Sprint G: `docs/agent-ops` architecture docs and `docs/ADR` decision records created for Agent Ops + Fontana. Local — pending deploy/review.

**Deferred / future cleanup:**
- Phase 4D — Apply Approved Proposals to Case Sources.
- Apply approved source suggestions to `investment_sources`.
- Scanner source registry wiring.

**Guardrails (hard — do not override without explicit instruction from Dani):**
- No auto-publish.
- No Substack API integration yet.
- No public posting.
- No buy/sell language in any output.
- Educational content only.
- Manual approval required.
- Public drafts must not expose private notes, internal IDs, VPS details, or operational metadata.
- No scanner trigger, no cron changes, no v2 evaluator global promotion.
- No URL fetching or crawling — document/source URLs remain metadata-only unless explicitly scoped.
- No Alembic migration without explicit approval.
- No Marketplace/Sales changes — domain is paused/preserved.
