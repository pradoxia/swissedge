# SwissEdge — Compact Session Handoff

> Full canonical state: `docs/PROJECT_STATE.md`
> Architecture decisions: `docs/decisions.md`
> Last updated: 2026-05-13 (Sprint AJ local — Official Source Finder & SEC Filing Locator Workbench)

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

**Investment Platform V2 deployed notes:** Sprint A scanner funnel diagnostics implemented and deployed. Sprint B Research Inbox read-only implemented and deployed. Sprint B.1 Research Inbox UI polish implemented and deployed. Sprint C V2 ResearchCase metadata implemented and deployed; Alembic revision `d4e5f6a7b8c9` applied. Sprint E manual create-from-situation bridge initializes V2 metadata for SEC/evaluation-linked ResearchCases locally and pending deploy. Sprint F created `swissedge-ai-context` as an AI-safe documentation layer. Sprint F: AI-Safe Context Architecture - `swissedge-ai-context` project layer created, with AI-safe context structure being completed through Sprint F.1. No runtime code changes. Sprint G created Agent Ops + Fontana architecture docs; no runtime behavior changed. Sprint G/G.1: Agent Ops + Fontana architecture docs completed, including data model, API, UI, metrics, routing audits, and ADRs. Documentation only; no runtime changes. Sprint H Agent Ops backend foundation is deployed; Alembic revision `e5f6a7b8c9d0` was applied; API smoke tests passed with 6 rooms, 6 agents, and empty activity/diagnostics/proposals lists. Sprint I `/agent-ops` Mission Control UI is deployed and smoke-tested. It is read-only except proposal status review and does not connect Agent Ops to scanner/evaluator. No source-driven intake, scan behavior, cron, global v2, live AI, publishing, or Marketplace/Sales changes in any of these sprints.

## Recent completed / local work

- Sprint A: Scanner funnel diagnostics + truthful Radar Status.
- Sprint B: Research Inbox read-only.
- Sprint B.1: Research Inbox UI polish.
- Sprint C: V2 ResearchCase metadata + migration.
- Sprint C.1: deploy script and deployment notes cleanup.
- Sprint D: V2 metadata detail panel + Internal Audit read-only.
- Sprint E: Manual Evaluation/SpecialSituation -> V2 ResearchCase bridge.
- Sprint F/F.1: AI-Safe Context Architecture completed.
- Sprint G/G.1: Agent Ops + Fontana architecture docs completed.
- Sprint H: Agent Ops backend foundation deployed; migration `e5f6a7b8c9d0` applied; API smoke tests passed.
- Sprint I: `/agent-ops` Mission Control UI deployed and smoke-tested.
- Sprint J: Agent Ops backend PATCH behavior and logger fail-safe tests hardened locally; no scanner/evaluator integration.
- Sprint K: Agent Ops logger failures isolated from caller transactions with nested transactions/SAVEPOINTs before future runtime wiring; scanner/evaluator integration remains not approved.
- Sprint L: Agent Ops UI hygiene improved locally with refresh button, safer guardrails rendering, and friendlier activity/diagnostic labels. Frontend-only.
- Sprint M: Agent Ops backend/frontend verification closeout documented. Backend and `/agent-ops` UI are treated as deployed and smoke-tested; local endpoint verification was unavailable because no backend was listening locally.
- Sprint N: Agent Ops proposal status review now logs safe Agent Ops activity with the fail-safe logger. Reviewer-note-only PATCH does not create activity. No scanner/evaluator, SEC EDGAR, ResearchCase, cron, source registry, or investment runtime integration was added.
- Sprint O: Manual Evaluation/SpecialSituation -> ResearchCase creation now logs safe Agent Ops activity as a runtime observer. No scanner/evaluator, SEC EDGAR intake, cron, source registry, live AI, or automatic ResearchCase creation behavior was added.
- Sprint Q: SEC EDGAR Detection Core implemented and production manual validation completed. It detects P1 official SEC signals (`SC TO-T`, `SC TO-I`, `Form 10`, and 8-K liquidation/dissolution metadata signals), enforces lookback locally, deduplicates repeated findings, creates/updates minimal `SpecialSituation` detection records, and returns a run summary. `SpecialSituation` is the initial detection object. Detected does not mean evaluated. No `/scan` production call, live AI, evaluator v2 global enablement, public drafts, ResearchCase auto-creation, Marketplace/Sales, or external sources.
- Sprint Q.1: manual cleanup tool added for historical false SEC detections from the pre-Hotfix-2 validation bug. Cleanup is dry-run by default and delete requires explicit confirmation.
- Sprint R: scheduled SEC EDGAR intake is enabled through cron after Dani manual approval. It uses `scripts/run_sec_edgar_detection.sh` for twice-daily runs at 07:00/19:00 UTC with `python -m backend.cli.sec_edgar_detect --hours-back 168`. Rate limit remains one request every five seconds and dedupe prevents repeated creation. No `/scan`, live AI, evaluator v2 global enablement, ResearchCase auto-creation, public publishing, document body fetching, or external sources.
- Sprint S: SpecialSituation methodology workspace foundation implemented locally. New SEC detections attach `evaluation.methodology_workspace` snapshots with fixed checklist and required-resource templates for P1 signals. Existing SEC detections can be backfilled manually with `python -m backend.cli.special_situation_attach_methodology --dry-run` then `--apply`. Frontend route `/investment/situations/[id]` displays detection summary, checklist, resources, progress, and planned next actions. Templates are based on processed artifacts and marked `requires_course_review=true`. No live AI, web crawling, PDF download, document body fetching, automatic verification, ResearchCase auto-creation, public publishing, cron change, or `/scan`.
- Sprint T: Resource Scout v1 implemented locally as a manual CLI and safe manual resource endpoint. It stores `resource_candidates` and `search_suggestions` inside `evaluation.methodology_workspace`, creates candidates from existing SEC metadata, updates clearly mapped required resources to `candidate_found`, and never marks checklist items verified. No broad web discovery, crawling, PDF download, SEC document body fetching, article text storage, cron/autonomous scouting, live AI, ResearchCase auto-creation, public publishing, or `/scan`.
- Sprint U: Kanban Actions + Evidence Mapping implemented locally. Workflow status is stored in `evaluation.methodology_workspace.workflow_status`; manual resource review can link candidates to required resources/checklist items and mark linked material `evidence_found`. `evidence_found` does not mean verified, evaluated, or recommended. No cron modification, `/scan`, live AI, evaluator v2 global enablement, ResearchCase auto-creation, web crawling, PDF download, document body fetching, public publishing, or Marketplace/Sales changes.
- Sprint AH: Intelligence KPI Dashboard & Fontana Diagnostic Report v1 implemented locally. New read-only endpoints `GET /api/investment/intelligence/kpis` and `GET /api/investment/intelligence/fontana-report` aggregate stored SpecialSituation, ResearchCase, methodology workspace, Evidence Links, Documentation Guide, Intelligence Score, and Agent Ops data into platform KPIs and deterministic Fontana findings. New `/investment/intelligence` dashboard shows preparation quality, documentation quality, evidence coverage, manual review workload, bottlenecks, and manual next actions. Mission Control links to Intelligence KPIs, and Agent Ops shows the deterministic Fontana report. No AI, evaluator, scanner, `/scan`, cron, scheduler execution, automatic evaluation, automatic ResearchCase creation, automatic promotion, crawling, PDF download, SEC body fetch, external HTTP, investment recommendations, publishing, Marketplace/Sales changes, DB migration, or deploy.
- Sprint AI: Research Command Center, Batch QA Polish & Deployment Verification UI implemented locally. Mission Control now shows the active workflow from SEC EDGAR detection through SpecialSituation, Kanban, Missing Evidence Hunter, ResearchCase, Evaluation Preparation, Evidence Links, Intelligence Score, Intelligence KPIs, and Fontana. A static manual Deployment Verification Checklist lists backend endpoints and frontend routes Dani should check after deployment. Cross-links were tightened across Mission Control, SpecialSituation detail, ResearchCase detail, Intelligence KPIs, and Agent Ops. Agent Ops room detail secondary panels now fail locally if one room endpoint is temporarily unavailable. Frontend/docs only: no backend endpoint, migration, deployment, AI, evaluator, scanner, `/scan`, cron change, scheduler execution, automatic evaluation, automatic ResearchCase creation, automatic promotion, crawling, document fetch, investment recommendations, publishing, or Marketplace/Sales changes.
- Sprint AJ: Official Source Finder & SEC Filing Locator Workbench implemented locally. New read-only endpoints `GET /api/investment/situations/{id}/official-source-finder` and `GET /api/investment/research-cases/{id}/official-source-finder` build manual official-source packages from stored SEC metadata, methodology workspace resources/checklists, resource candidates, search suggestions, ResearchCase snapshots, and Evidence Links. Situation and ResearchCase detail pages now show an Official Source Finder panel with SEC metadata, stored filing links, missing official document targets, locator steps, and copyable manual queries. Kanban cards show compact source-finder indicators from already-loaded JSON only. Agent Ops documents the Official Source Finder as manual/observer-only. No web search, SEC fetch, PDF download, crawl, link verification, AI, evaluator, scanner, `/scan`, cron change, scheduler execution, automatic evaluation, automatic ResearchCase creation, automatic promotion, publishing, recommendations, Marketplace/Sales changes, DB migration, or deploy.
- Sprint V: manual SpecialSituation -> ResearchCase promotion implemented and production-validated after hotfix. Endpoint `POST /api/investment/situations/{id}/promote-to-research-case` creates an idempotent ResearchCase for deeper research, stores `research_case_id` in `evaluation.methodology_workspace`, snapshots detection/workspace context into `ResearchCase.brief`, and creates conservative initial tasks/sources. Promotion is manual only and does not evaluate, recommend, publish, create public drafts, call live AI, enable evaluator v2 globally, crawl, download PDFs, fetch document bodies, modify cron, or call `/scan`.
- Sprint W: SEC EDGAR to ResearchCase milestone closeout and GitHub sync preparation. Current active flow is `SEC EDGAR cron -> SpecialSituation -> Kanban -> checklist/resources -> evidence mapping -> manual ResearchCase promotion`. Next recommended phase is ResearchCase Evaluation Preparation / Deep Research Assist, without automatic evaluation.
- Sprint X-A: Compact Kanban Overview implemented for `/investment/situations`. The page now defaults to a compact responsive Kanban overview with phase counts, top cases per phase, preserved filters, and a detailed board toggle. Frontend-only; no backend, migration, cron, scanner, live AI, evaluator, ResearchCase automation, publishing, or Marketplace/Sales changes.
- Sprint X-B: ResearchCase Evaluation Preparation / Deep Research Assist implemented locally. New read-only endpoint `GET /api/investment/research-cases/{id}/evaluation-prep` returns a deterministic metadata-only readiness package for promoted ResearchCases. Frontend `/investment/research/[id]` shows an Evaluation Preparation panel with readiness level, missing required resources, checklist gaps, source quality notes, and next manual actions. Preparation only: no live AI, no evaluator v2 global enablement, no automatic evaluation, no recommendations, no publishing, no crawling/PDF/document body fetching, no `/scan`, and no cron change.
- Sprint Y: Evidence Links & Research Traceability implemented locally. New read-only traceability endpoints show original SEC source links, resource candidate links, required-resource/checklist support links, ResearchCase source/document links, and metadata-only guardrails in `/investment/situations/[id]` and `/investment/research/[id]`. It does not fetch document bodies, crawl, download PDFs, evaluate, verify evidence automatically, recommend, publish, call `/scan`, change cron, or enable evaluator v2 globally.
- Sprint Z: Intelligence Scoring Foundation implemented locally. New read-only endpoint `GET /api/investment/research-cases/{id}/intelligence-score` returns a deterministic 0-100 IA Score with Detection (40), Structuring (40), and Risk Discipline (20) components. `/investment/research/[id]` now shows an Intelligence Score card integrated with Evaluation Preparation and Evidence Links. `APPROVABLE` means structurally approvable for manual review only, not investment approval. No DB writes, migration, live AI, external calls, evaluator activation, automatic evaluation, ResearchCase auto-creation, publishing, crawling, PDF download, document body fetching, cron change, or `/scan`.
- Sprint ZA: Agent Rooms 2.0 implemented locally as a frontend-only Agent Ops expansion. `/agent-ops/rooms/[id]` opens navigable room detail pages with room metrics, agents, deterministic avatars, selected-agent logs, diagnostics, related ResearchCase/SpecialSituation links when present, conceptual interaction maps, and derived read-only operational indicators. `/agent-ops` room cards now link to room details. Profile name/avatar editing is deferred because no safe AgentProfile PATCH endpoint exists. No backend endpoints, DB migration, scanner/evaluator integration, live AI, cron changes, automation, publishing, recommendations, or Marketplace/Sales changes.
- Sprint AB: Missing Evidence Hunter & Case Documentation Guide implemented locally. New read-only endpoints `GET /api/investment/situations/{id}/documentation-guide` and `GET /api/investment/research-cases/{id}/documentation-guide` return deterministic documentation packages from existing SEC metadata, methodology workspace snapshots, required resources, resource candidates, search suggestions, Evidence Links, Evaluation Preparation, Intelligence Score, and ResearchCase sources/documents/tasks. `/investment/situations/[id]` and `/investment/research/[id]` now show Case Documentation Guide sections near the top; Kanban cards show derived documentation status; Agent Ops shows Missing Evidence Hunter as observer/manual. No cron, scheduler execution, browsing, document fetching, live AI, automatic evaluation, automatic promotion, ResearchCase auto-creation, publishing, public draft creation, recommendations, Marketplace/Sales changes, or DB migration.
- Sprint AC: Case Activity Log & Research Timeline implemented locally. New read-only endpoints `GET /api/investment/situations/{id}/activity-timeline` and `GET /api/investment/research-cases/{id}/activity-timeline` return deterministic current-state timelines from stored SEC/workspace/resource/search/research/Agent Ops metadata. `/investment/situations/[id]` and `/investment/research/[id]` now show derived case activity timelines; Kanban cards show latest activity/attention markers without N+1 calls; Agent Ops shows case-row relevance by agent. These are not persisted audit logs yet. No cron, scheduler execution, live AI, scanner/evaluator call, crawling, document fetching, automatic evaluation, automatic ResearchCase creation, publishing, Marketplace/Sales changes, DB migration, or deploy.
- Sprint AD: Agent Rooms Real Ops + Case Research Agent implemented locally. `/agent-ops` and `/agent-ops/rooms/[id]` now show stronger agent identities, room missions, conceptual interaction maps, scheduler posture display only, Missing Evidence Hunter as the case research agent, case-row relevance, related-case links where logs provide IDs, problems by agent, and frontend-derived XP/reliability/evidence-quality indicators. Rename/avatar editing remains deferred because no safe profile customization endpoint was added. No backend mutation, DB migration, cron, scheduler execution, live AI, scanner/evaluator runtime connection, publishing, recommendations, Marketplace/Sales changes, or deploy.
- Sprint AE: Batch hardening and deployment readiness implemented locally. SpecialSituation activity timeline and evidence links now load as non-blocking secondary panels, matching the documentation-guide fix. ResearchCase Evidence Links and Evaluation Preparation loaders are separated so secondary panel failures stay local. Kanban styling avoids warning color for `Missing: 0` and gates Missing Evidence Hunter badge to cases with documentation/workspace context. Batch deployment readiness and deep smoke-test checklist are documented. No backend mutation, DB migration, cron, scheduler execution, live AI, scanner/evaluator runtime connection, publishing, recommendations, Marketplace/Sales changes, or deploy.

## Current blockers / warnings

- Agent Ops logger isolation exists from Sprint K, but scanner/evaluator integration is still not approved.
- Agent Ops activity may contain narrow observer events from proposal review and manual ResearchCase creation if Sprint N/O are deployed; diagnostics/proposals may still be empty unless manually created.
- Agent Ops Scoreboard and Fontana reports remain placeholders.
- SEC EDGAR manual detection is validated and scheduled SEC EDGAR intake is enabled through cron. Sprint S/T/U/V methodology, resource, Kanban, evidence-mapping, and manual ResearchCase promotion features are complete and production-validated through manual promotion. EDGAR is operational.
- Resource Scout v1 is manual only. It stores candidates/search suggestions but does not browse the web, crawl, download PDFs, or verify evidence.
- ResearchCase promotion is manual only. Detection does not auto-create ResearchCases, and promotion does not evaluate, recommend, publish, or create public drafts.
- `investment_sources` still does not control scanner execution.
- Evaluator v2 remains not globally enabled.
- Cron must not be changed without approval.
- `/scan` must not be called unless explicitly requested.
- Browser DevTools may show a CSP `unsafe-eval` warning; this is known low-priority and CSP must not be relaxed unless functionality is actually broken.

## Next recommended sprints

1. Sprint X-B/Y/Z/ZA/AB/AC/AD/AE GitHub sync after final review: commit/push only when Dani chooses to run it.
2. Claude review of Sprint AB/AC/AD/AE batch before deployment.
3. Optional controlled official-source discovery only after explicit approval; Resource Scout remains manual until then.
4. Fontana report runtime after explicit approval.
5. Market monitoring after source-driven intake stabilizes.

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
| `/agent-ops` | Agent Ops Mission Control UI + Research Agent Network + room links + case-row relevance + derived XP indicators | DEPLOYED + Sprint AD local |
| `/agent-ops/rooms/[id]` | Agent Ops room detail with room posture, agent missions, interaction maps, logs, diagnostics, related objects, case timeline relevance, and derived operational indicators | Sprint AD local |
| `/investment/evaluations` | Evaluation queue | DEPLOYED |
| `/investment/evaluations/[id]` | Evaluation detail + Research Case panel | DEPLOYED |
| `/investment/research-inbox` | Research Inbox read-only — existing ResearchCases with V2 metadata when present and legacy/manual fallback labels | DEPLOYED per Sprint B/B.1 summaries — verify manually if needed |
| `/investment/research` | Research Cases list | DEPLOYED |
| `/investment/research/[id]` | Research Case detail + workspace + Case Documentation Guide + Research Timeline + Evaluation Prep + Evidence Links + Intelligence Score + AI Brief Preview + Quality Assist + Source Intelligence Panel (save/approve/reject) | DEPLOYED + Sprint AC local |
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
| Case Documentation Guides | `GET /api/investment/situations/{id}/documentation-guide`, `GET /api/investment/research-cases/{id}/documentation-guide` | Local — Sprint AB read-only |
| Case Activity Timelines | `GET /api/investment/situations/{id}/activity-timeline`, `GET /api/investment/research-cases/{id}/activity-timeline` | Local — Sprint AC read-only |
| Research Brief Preview | `POST /api/investment/research-cases/{id}/generate-brief-preview` | Live |
| Intelligence Score | `GET /api/investment/research-cases/{id}/intelligence-score` | Local — Sprint Z read-only |
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

**Next recommended sprint:** Claude review of Sprint X-B/Y/Z/ZA, then Dani-approved manual deploy/smoke test if accepted.

V2 sprint history:
- Sprint A: scanner funnel diagnostics, UI truthfulness, SEC EDGAR 429 fix.
- Sprint B: `/investment/research-inbox` read-only page over existing ResearchCases; legacy/V2 fallback labels.
- Sprint B.1: Research Inbox UI polish.
- Sprint C: V2 ResearchCase metadata additive migration (`d4e5f6a7b8c9`); 14 nullable fields on `research_cases`; frontend inbox prefers real V2 metadata with legacy fallback.
- Sprint C.1: deploy script updated to include Sprint C migration file; deployment notes added.
- Sprint D: ResearchCase detail V2 metadata read-only panel added; `/investment/internal-audit` read-only page created; Internal Audit card added to Mission Control; nav link added to Research Inbox.
- Sprint E: existing manual `SpecialSituation` / Evaluation -> Create ResearchCase flow initializes V2 metadata, initial verification tasks, and a metadata-only source for SEC/evaluation-linked cases.
- Sprint F: `swissedge-ai-context` AI-safe documentation layer created.
- Sprint G: `docs/agent-ops` architecture docs and `docs/ADR` decision records created for Agent Ops + Fontana.
- Sprint H: Agent Ops backend foundation deployed; migration `e5f6a7b8c9d0` applied per 2026-05-10 closeout docs.
- Sprint I: `/agent-ops` Mission Control UI deployed and smoke-tested per 2026-05-10 closeout docs.
- Sprint J: proposal PATCH behavior and fail-safe logger tests hardened locally.
- Sprint K: logger writes isolated with nested transactions/SAVEPOINTs locally; scanner/evaluator integration remains not approved.
- Sprint L: `/agent-ops` UI hygiene improved locally.
- Sprint M: Agent Ops deployed-state verification documented.
- Sprint N: proposal review creates narrow observer activity when deployed; reviewer-note-only PATCH does not create activity.
- Sprint O: manual Evaluation/SpecialSituation -> ResearchCase bridge creates narrow observer activity when deployed.
- Sprint Q: manual SEC EDGAR Detection Core implemented and production manual validation completed; creates minimal `SpecialSituation` detections for P1 signals only (`SC TO-T`, `SC TO-I`, `Form 10`, 8-K liquidation/dissolution metadata signals). Detected does not mean evaluated; no evaluator call and no ResearchCase creation.
- Sprint Q.1: manual cleanup tool for historical false detections from the pre-Hotfix-2 validation bug.
- Sprint R: scheduler wrapper deployed and cron enabled manually for twice-daily SEC EDGAR detection with 168-hour lookback.
- Sprint S: methodology checklist/resource snapshots attach to SEC-detected `SpecialSituation` records.
- Sprint T: Resource Scout v1 stores official SEC candidates, manual URL candidates, and search suggestions in the methodology workspace. Automated web discovery remains future work.
- Sprint U: manual Kanban movement, resource review, manual resource add, resource-to-checklist linking, and `evidence_found` progress updates. Verification remains human-controlled and ResearchCase promotion remains future work.
- Sprint V: manual idempotent promotion from SpecialSituation to ResearchCase with detection/workspace snapshot, initial verification tasks, metadata-only sources, and `research_case_id` stored in the methodology workspace.

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
