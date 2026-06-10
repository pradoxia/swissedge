# SwissEdge Repo Audit

Date: 2026-06-08

Scope: repo inspection only. No app behavior, routes, APIs, migrations, scheduler state, or runtime data were changed. This audit includes uncommitted local files visible in the working tree.

Status vocabulary:

- implemented: code path, route, API, or model exists.
- partially implemented: visible UI/service exists but depends on manual steps, derived data, metadata-only data, unverified data, or incomplete backend integration.
- designed but not implemented: documentation/spec exists without matching executable surface.
- missing: expected surface not found.
- unknown: cannot verify from repository inspection alone.

## Current Frontend Routes

Primary private frontend is Next.js App Router under `frontend/app`.

| Route | Page/component file | Purpose | Status |
| --- | --- | --- | --- |
| `/` | `frontend/app/page.tsx` | Mission Control hub with hardcoded module/status metadata and links. | partial |
| `/campus` | `frontend/app/campus/page.tsx`, `frontend/app/campus/CampusView.tsx`, `frontend/app/campus/campus-config.ts` | Visual Operations Campus using real observability calls plus configured campus rooms/agents/assets. | partial |
| `/agent-ops` | `frontend/app/agent-ops/page.tsx` | Agent Ops dashboard: rooms, agents, activity, diagnostics, proposals, Fontana, Dani Weber, Executive Review. | partial |
| `/agent-ops/calendar` | `frontend/app/agent-ops/calendar/page.tsx` | Cron/upcoming execution calendar. | partial |
| `/agent-ops/rooms/[id]` | `frontend/app/agent-ops/rooms/[id]/page.tsx` | Room detail page using Agent Ops APIs. | partial |
| `/agents` | `frontend/app/agents/page.tsx` | Observability agent roster. | implemented |
| `/agents/[agent_name]` | `frontend/app/agents/[agent_name]/page.tsx` | Observability agent detail. | implemented |
| `/investment/situations` | `frontend/app/investment/situations/page.tsx` | SpecialSituation Kanban/list. | implemented |
| `/investment/situations/[id]` | `frontend/app/investment/situations/[id]/page.tsx` | Situation detail/workbench with Study Guide, evidence, source finder, document package, SEC acquisition, activity timeline. | implemented |
| `/investment/research` | `frontend/app/investment/research/page.tsx` | ResearchCase list and linked situations. | implemented |
| `/investment/research/[id]` | `frontend/app/investment/research/[id]/page.tsx` | ResearchCase detail/workbench. | implemented |
| `/investment/research-inbox` | `frontend/app/investment/research-inbox/page.tsx` | V2 research inbox over ResearchCases and situations. | partial |
| `/investment/radar-status` | `frontend/app/investment/radar-status/page.tsx` | Read-only scanner/source/cron status. | partial |
| `/investment/intelligence` | `frontend/app/investment/intelligence/page.tsx` | Intelligence KPI dashboard. | implemented |
| `/investment/sources` | `frontend/app/investment/sources/page.tsx` | Source registry UI. Scanner does not yet use registry rows. | partial |
| `/investment/internal-audit` | `frontend/app/investment/internal-audit/page.tsx` | Internal data quality audit. | partial |
| `/investment/evaluations` | `frontend/app/investment/evaluations/page.tsx` | Legacy evaluations queue over SpecialSituations. | partial/legacy |
| `/investment/evaluations/[id]` | `frontend/app/investment/evaluations/[id]/page.tsx` | Legacy evaluation detail and manual v2 preview. | partial/legacy |
| `/investment/watchlist` | `frontend/app/investment/watchlist/page.tsx` | Older watchlist view over situations. | partial/legacy |
| `/investment/source-intelligence` | `frontend/app/investment/source-intelligence/page.tsx` | Source intelligence suggestion queue. | partial |
| `/investment/historical-cases` | `frontend/app/investment/historical-cases/page.tsx` | Historical case list/create. | implemented |
| `/investment/historical-cases/[id]` | `frontend/app/investment/historical-cases/[id]/page.tsx` | Historical case detail/source-intelligence context. | implemented |
| `/investment/public-drafts` | `frontend/app/investment/public-drafts/page.tsx` | Public article draft list. | implemented |
| `/investment/public-drafts/[id]` | `frontend/app/investment/public-drafts/[id]/page.tsx` | Draft detail/markdown. | implemented |
| `/marketplace`, `/marketplace/buying`, `/marketplace/sales`, `/marketplace/sales/items`, `/marketplace/sales/items/[id]` | `frontend/app/marketplace/**/page.tsx` | Marketplace/sales surfaces. Not central to governance baseline. | implemented/paused |

Public site routes exist separately under `public-site/app`: `/`, `/research`, `/research/meridian-group-separation`, `/methodology`.

## Current Backend API Endpoints

FastAPI routers are registered in `backend/main.py`:

- `/api/health`: `backend/api/health/router.py`
- `/api/marketplace`: `backend/api/marketplace/router.py`
- `/api/marketplace/sales`: `backend/api/marketplace/sales_items.py`
- `/api/investment`: `backend/api/investment/router.py`
- `/api/investment`: `backend/api/investment/research_cases.py`
- `/api/observability`: `backend/api/observability/router.py`
- `/api/agent-ops`: `backend/api/agent_ops/router.py`

Investment endpoints include:

- Detection/scanner/status: `GET /intelligence/kpis`, `GET /detection-runs/latest`, `GET /detection-runs/status`, `GET /detection-runs/readiness`, `GET /detection-runs`, `GET /detection-runs/{run_id}`, `POST /scan`.
- Executive/governance: `GET /intelligence/fontana-report`, `GET /executive/dani-weber-metrics`, `GET /executive/review`.
- Evaluation: `POST /evaluate-v2`.
- Situations: `GET /situations`, `GET/PATCH /situations/{id}`, evidence/documentation/source/acquisition/activity/promotion endpoints, resource and workflow-status PATCH/POST endpoints.
- Knowledge/course: `GET /knowledge`, `GET /knowledge/{key}`, `GET /course-index`, `GET /course-documentation-map/{situation_type}`, `GET /skill-requirements/{situation_type}`.
- Sources: `GET/POST /sources`, `PATCH/DELETE /sources/{id}`, `POST /sources/{id}/test`.
- ResearchCases: create/list/detail/update plus tasks, documents, sources, evidence, intelligence score, documentation guide, source finder, historical analogues, completion workbench, operational view, SEC acquisition, timelines, AI preview endpoints, source-intelligence suggestions, historical cases, and public drafts.
- Agent Ops: `GET /rooms`, `GET /rooms/{room_key}`, `GET /agents`, `GET /agents/{agent_key}`, governance preview/latest endpoints, execution calendar, activity, diagnostics, proposals, proposal PATCH.
- Observability: runs, summary, costs, agent registry/details/text, mission control, cron upcoming, Claude session logging.

## Database Models / Entities

Investment and situations:

- `backend/models/investment.py`
  - `SpecialSituation`: initial detection/triage object. Stores type, company, ticker, filing metadata, status, evaluation JSON, methodology workspace-like JSON, notes, follow-up/published flags.
  - `SituationHistory`: status transitions.
  - `InvestmentSource`: source registry metadata and toggle fields. Partially operational because `/scan` still uses hardcoded `SECEdgarAdapter`.
  - `DetectionRun`: scanner/detection funnel counters and summaries.
  - `DocumentationExtractionField`: draft/reviewed extraction fields tied to `SpecialSituation`.
  - `InvestorContact`: contact metadata.

Research and publication:

- `backend/models/investment_research.py`
  - `ResearchCase`, `ResearchTask`, `ResearchDocument`, `ResearchSource`, `HistoricalCase`.
- `backend/models/source_intelligence.py`
  - `SourceIntelligenceSuggestion`.
- `backend/models/publishing.py`
  - `PublicArticleDraft`.

Agents, observability, governance:

- `backend/models/agent_ops.py`
  - `AgentRoom`, `AgentProfile`, `AgentActivity`, `AgentResult`, `AgentDiagnosticEvent`, `AgentLearningProposal`.
- `backend/models/observability.py`
  - `AgentRun`, `AiUsage`.

Campus and mission control:

- No separate DB model found. Campus and mission-control surfaces are derived from observability, Agent Ops config, cron reader, static frontend config, and existing investment tables.

Governance:

- No persisted `GovernanceDecision`, `FontanaReport`, or `DaniWeberReport` model found. Fontana/Dani reports are generated read-only from services and can log preview runs in `agent_runs`.

## Existing Components By Area

Investment situations:

- `frontend/app/investment/situations/page.tsx`
- `frontend/app/investment/situations/[id]/page.tsx`
- `frontend/app/components/CaseCompletionWorkbench.tsx`
- `frontend/app/components/CaseActivityTimeline.tsx`
- `frontend/app/components/EvidenceLinksPanel.tsx`
- `frontend/app/components/SECTransparencyPanel.tsx`
- `frontend/app/components/SecDocumentAcquisitionPanel.tsx`
- `frontend/app/components/OfficialSourceFinderPanel.tsx`
- `frontend/app/components/DocumentPackagePanel.tsx`
- `frontend/app/components/DocumentationAgentPanel.tsx`
- `frontend/app/components/DocumentationTasksPanel.tsx`
- `frontend/app/components/HistoricalAnaloguesPanel.tsx`
- `frontend/app/components/IntelligenceScoreCard.tsx`

Situation detail page:

- `frontend/app/investment/situations/[id]/page.tsx`
- `frontend/app/investment/situations/[id]/situation.module.css`

Study Guide:

- `frontend/app/components/EducationStudyGuidePanel.tsx`
- `frontend/app/components/studyGuideMapping.ts`
- `backend/services/investment/course_index.py`
- `backend/services/investment/course_documentation_map.py`
- `docs/COURSE_DOCUMENTATION_MAP.md`

Agent Ops:

- `frontend/app/agent-ops/page.tsx`
- `frontend/app/agent-ops/rooms/[id]/page.tsx`
- `frontend/app/agent-ops/calendar/page.tsx`
- `frontend/app/components/AgentStatusBadge.tsx`
- `frontend/app/components/AgentSafetyCard.tsx`
- `frontend/app/components/AgentRunHistory.tsx`
- `frontend/app/components/AgentRunDetailDrawer.tsx`
- `frontend/app/components/AgentExecutionEventCard.tsx`
- `frontend/app/components/AgentExecutionCalendar.tsx`
- `frontend/app/components/AgentConfigPanel.tsx`
- `frontend/app/components/AgentCalendarFilters.tsx`
- `backend/api/agent_ops/router.py`
- `backend/services/agent_ops/service.py`
- `backend/services/agent_ops/governance.py`

Campus:

- `frontend/app/campus/page.tsx`
- `frontend/app/campus/CampusView.tsx`
- `frontend/app/campus/campus-config.ts`
- `frontend/public/campus/**`

Mission Control:

- `frontend/app/page.tsx`
- `frontend/app/home.module.css`
- `backend/api/observability/router.py` (`/mission-control`)

Fontana:

- `frontend/app/components/FontanaReportPanel.tsx`
- `frontend/app/agent-ops/page.tsx`
- `backend/services/investment/fontana_report.py`
- `backend/services/agent_ops/governance.py`
- `docs/ADR/0003-fontana-cto-project-governor.md`
- `docs/agent-ops/FONTANA_CTO.md`

Dani Weber:

- `frontend/app/components/DaniWeberReportPanel.tsx`
- `frontend/app/agent-ops/page.tsx`
- `backend/services/investment/dani_weber_metrics.py`
- `backend/services/investment/executive_review.py`
- `backend/services/agent_ops/governance.py`
- `docs/sprints/2026-05-15-dani-weber-coo-metrics-v1.md`
- `docs/sprints/2026-05-15-executive-review-v1.md`

Observability:

- `frontend/app/agents/page.tsx`
- `frontend/app/agents/[agent_name]/page.tsx`
- `frontend/app/investment/radar-status/page.tsx`
- `backend/api/observability/router.py`
- `backend/services/observability/run_logger.py`
- `backend/services/observability/agent_registry.py`
- `backend/services/observability/cron_reader.py`

## Existing Services / Jobs / Cron / Scheduled Tasks

Implemented services:

- SEC detection: `backend/services/investment/sec_detection.py`, `backend/services/investment/sources/sec_edgar.py`, `backend/cli/sec_edgar_detect.py`.
- Scanner API: `POST /api/investment/scan` in `backend/api/investment/router.py`; uses hardcoded `_sec = SECEdgarAdapter(...)`.
- Detection runs: `backend/services/investment/detection_run_service.py`, `backend/services/investment/detection_readiness.py`.
- Case/research services: `backend/services/investment/research_cases.py`, `evidence_links.py`, `document_package.py`, `documentation_agent.py`, `documentation_extraction.py`, `case_completion.py`, `case_activity.py`, `official_source_finder.py`, `historical_analogues.py`, `intelligence_score.py`, `intelligence_kpis.py`, `fontana_report.py`, `dani_weber_metrics.py`, `executive_review.py`.
- Agent Ops services: `backend/services/agent_ops/service.py`, `backend/services/agent_ops/activity_logger.py`, `backend/services/agent_ops/governance.py`.
- Observability: `backend/services/observability/run_logger.py`, `cron_reader.py`, `agent_registry.py`.

Scheduled-task artifacts:

- `scripts/run_sec_edgar_detection.sh`: cron-friendly wrapper for `python -m backend.cli.sec_edgar_detect`.
- `scripts/examples/sec_edgar_cron.example`: example cron/systemd timer concept.
- `docs/investment/DEPLOYMENT_NOTES.md`: documents manual cron enablement and warns no automatic cron install.
- Older VPS/OpenClaw scripts can install or inspect crons and may call `/api/investment/scan`: `scripts/setup_openclaw_integration.py`, `scripts/deploy_telegram_notifier.py`, `scripts/trigger_action.py`, `scripts/final_status_check.py`.
- `deploy/systemd/swissedge-telegram-bot.service`: Telegram bot service file.

Do not touch yet:

- Scanner cron, `/api/investment/scan`, deployment scripts, OpenClaw cron scripts, and live SEC/AI paths without a separately scoped sprint and approval.

## Mock / Hardcoded / Placeholder / Partial Implementations

- Mission Control module/status cards and deployment checklist are hardcoded in `frontend/app/page.tsx`.
- Campus uses static config/assets in `frontend/app/campus/campus-config.ts` and `frontend/public/campus/**`, combined with observability calls.
- Source registry UI is real, but scanner source selection is hardcoded to `SECEdgarAdapter`; documented in `docs/investment/RADAR_RELIABILITY_AUDIT.md`.
- `backend/services/agent_ops/governance.py` defines governance room/agent catalog in code; governance reports are generated, not persisted as report entities.
- Study Guide has local mapping/placeholder behavior in `frontend/app/components/studyGuideMapping.ts` and `EducationStudyGuidePanel.tsx`.
- Agent Ops room detail pages include derived indicators and configured avatars/assets; profile editing is deferred because no safe `AgentProfile` PATCH endpoint was found.
- Public site uses static data in `public-site/data/article.ts`.
- Tests contain many mocked AI/DB/SEC cases; these are not real sample IDs.

## Current Documentation Files

Product/architecture:

- `README.md`, `architecture.md`, `product-requirements.md`, `roadmap.md`, `open-questions.md`
- `docs/PROJECT_STATE.md`, `docs/PROJECT_STATE_LIGHT.md`
- `docs/product/SWISSEDGE_PRODUCT_OPERATING_MODEL.md`
- `docs/investment/INVESTMENT_PLATFORM_V2_ARCHITECTURE.md`
- `docs/investment/CLEANUP_AND_REUSE_PLAN.md`
- `docs/technical/INVESTMENT_RESEARCH_TECHNICAL_OVERVIEW.md`
- `docs/technical/INVESTMENT_RESEARCH_TECH_DEBT_REVIEW.md`

Agents/governance/observability:

- `docs/agents.md`, `docs/observability.md`
- `docs/agent-ops/*.md`
- `docs/ADR/0001-ai-safe-context-architecture.md`
- `docs/ADR/0002-agent-ops-learning-layer.md`
- `docs/ADR/0003-fontana-cto-project-governor.md`
- `swissedge-ai-context/**`

Investment/sprint logs:

- `docs/investment/*.md`
- `docs/sprints/*.md`
- `docs/DETECTION_RUNS.md`
- `docs/intelligence_scoring.md`
- `docs/COURSE_DOCUMENTATION_MAP.md`
- `docs/workflow/*.md`

## Known Broken / Missing / Unknown Pieces

Implemented and reusable:

- SpecialSituation scanner/detection model and API.
- Situation list/detail, ResearchCase list/detail, evidence/document/source support surfaces.
- DetectionRun and AgentRun observability.
- Agent Ops rooms/agents/activity/diagnostics/proposals API and UI.
- Fontana/Dani deterministic read-only reports.
- Course documentation and Study Guide metadata surfaces.

Partially implemented:

- Source registry: UI and API exist, but scanner does not consume `investment_sources`.
- Scanner funnel: creates situations, but empty-scan diagnosis and per-form health remain limited.
- Governance: reports are deterministic/read-only and mostly derived; report persistence and approval workflow are not modeled.
- Agent Ops activity/logs: models and APIs exist, but many agents are observer/config entries without real execution logs.
- Campus: visually implemented, but depends on derived/static config and observability availability.
- Study Guide: visible, but mappings can be placeholders when no course chapters are mapped.
- SEC document acquisition: manual metadata/candidate flow exists; evidence remains unverified by design.

Designed but not implemented:

- Source-driven ResearchCase intake replacing scanner-first flow.
- Persistent governance decisions/reports beyond Agent Ops proposals and run logs.
- Agent score snapshots/scoreboard.
- Full Evidence Lab / Playbook Workshop / Research Desk / Quality Court as independent operational rooms with persisted outputs.

Missing:

- Safe `AgentProfile` PATCH/customization endpoint.
- Dedicated `/governance` frontend route found none.
- DB model for persisted Fontana/Dani reports.
- Verified real sample IDs committed to repo for screenshot URLs.

Unknown:

- Live database contents and deployed route health.
- Whether local uncommitted files are deployed.
- Whether cron is currently installed in the target environment.
- Whether current migrations are applied locally or in production.
