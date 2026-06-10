# Route And Endpoint Map

Date: 2026-06-08

## Frontend Routes

| Route | Page/component file | Purpose | Data source/API used | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `/` | `frontend/app/page.tsx` | Mission Control hub | Hardcoded frontend arrays; links only | partial | Static deployment checklist and module metadata. |
| `/campus` | `frontend/app/campus/page.tsx`, `frontend/app/campus/CampusView.tsx` | Operations Campus | `fetchAgents`, `fetchCronUpcoming`, `fetchMissionControl`, `fetchAgent`; static `campus-config.ts` | partial | Visual/static config plus real observability. |
| `/agent-ops` | `frontend/app/agent-ops/page.tsx` | Agent Ops / Executive Office | Agent Ops APIs, `fetchFontanaReport`, `fetchDaniWeberMetrics`, `fetchExecutiveReview` | partial | Read-only except proposal status/reviewer-note patch. |
| `/agent-ops/calendar` | `frontend/app/agent-ops/calendar/page.tsx` | Execution calendar | `fetchCronUpcoming` | partial | Reads parsed cron/upcoming data. |
| `/agent-ops/rooms/[id]` | `frontend/app/agent-ops/rooms/[id]/page.tsx` | Room detail | `fetchAgentOpsRooms/Agents/Activity/Diagnostics/Proposals` | partial | Requires room key such as `detection_room`. |
| `/agents` | `frontend/app/agents/page.tsx` | Observability agent roster | `fetchAgents` | real | Uses `/api/observability/agents`. |
| `/agents/[agent_name]` | `frontend/app/agents/[agent_name]/page.tsx` | Agent detail | `fetchAgent` | real | Requires observability agent registry name. |
| `/investment/situations` | `frontend/app/investment/situations/page.tsx` | SpecialSituation Kanban/list | `fetchSituations`, `updateSituationWorkflowStatus` | real | Uses persisted `special_situations`; cards also render derived JSON. |
| `/investment/situations/[id]` | `frontend/app/investment/situations/[id]/page.tsx` | Situation detail | Situation, evidence, docs, guide, source finder, SEC preview, completion, promotion, timeline APIs | real | Needs real `SpecialSituation.id`. |
| `/investment/research` | `frontend/app/investment/research/page.tsx` | ResearchCase list | `fetchResearchCases`, `fetchSituations` | real | Links promoted/durable cases. |
| `/investment/research/[id]` | `frontend/app/investment/research/[id]/page.tsx` | ResearchCase detail | ResearchCase detail/workbench APIs | real | Needs real `ResearchCase.id`. |
| `/investment/research-inbox` | `frontend/app/investment/research-inbox/page.tsx` | V2 inbox | `fetchResearchCases`, `fetchSituations` | partial | Current docs call this read-only first pass. |
| `/investment/radar-status` | `frontend/app/investment/radar-status/page.tsx` | Scanner/source/cron status | `fetchAgent('investment_scanner')`, `fetchSources`, `fetchCronUpcoming`, detection run APIs | partial | Source registry can mislead because scanner ignores active source rows. |
| `/investment/intelligence` | `frontend/app/investment/intelligence/page.tsx` | Intelligence KPIs | `fetchIntelligenceKpis` | real | Read-only aggregate. |
| `/investment/sources` | `frontend/app/investment/sources/page.tsx` | Source registry | `fetchSources`, `toggleSourceActive` | partial | UI/API real; scanner integration missing. |
| `/investment/internal-audit` | `frontend/app/investment/internal-audit/page.tsx` | Internal audit | `fetchResearchCases`, `fetchSources`, `fetchAgent('investment_scanner')` | partial | Derived/read-only audit surface. |
| `/investment/evaluations` | `frontend/app/investment/evaluations/page.tsx` | Legacy evaluations queue | `fetchSituations`, archive/status APIs | partial | Legacy/advanced surface. |
| `/investment/evaluations/[id]` | `frontend/app/investment/evaluations/[id]/page.tsx` | Legacy evaluation detail | `fetchSituation`, v2 preview, research case promotion/list APIs | partial | Manual v2 preview is explicitly non-persistent when configured. |
| `/investment/watchlist` | `frontend/app/investment/watchlist/page.tsx` | Old watchlist | `fetchSituations`, `updateSituationStatus` | partial/legacy | Operational label over situations. |
| `/investment/source-intelligence` | `frontend/app/investment/source-intelligence/page.tsx` | Source suggestion queue | `fetchSourceIntelligenceSuggestions`, review API | partial | Approval queue does not automatically apply source changes. |
| `/investment/historical-cases` | `frontend/app/investment/historical-cases/page.tsx` | Historical cases | `fetchHistoricalCases`, create API | real | Manual workspace. |
| `/investment/historical-cases/[id]` | `frontend/app/investment/historical-cases/[id]/page.tsx` | Historical case detail | `fetchHistoricalCase`, source-intelligence APIs | real | Needs real historical case ID. |
| `/investment/public-drafts` | `frontend/app/investment/public-drafts/page.tsx` | Draft list | `fetchPublicDrafts` | real | Manual publication workflow. |
| `/investment/public-drafts/[id]` | `frontend/app/investment/public-drafts/[id]/page.tsx` | Draft detail | `fetchPublicDraft`, `fetchPublicDraftMarkdown` | real | Needs real draft ID. |

## Backend Endpoints

| Method + path | Handler/controller file | Purpose | Data source/service used | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `GET /` | `backend/main.py` | Root status | Static response | real | Basic backend landing. |
| `GET /api/health/ping` | `backend/api/health/router.py` | Health ping | DB dependency optional checks | real | |
| `GET /api/health/full` | `backend/api/health/router.py` | Full health | DB/health services | real | |
| `POST /api/health/heartbeat` | `backend/api/health/router.py` | Cron heartbeat | `HealthCheck` model | real | Used by older cron scripts. |
| `POST /api/investment/scan` | `backend/api/investment/router.py` | SEC scan into SpecialSituations | `SECEdgarAdapter`, evaluator, `SpecialSituation`, run logging | partial | Does not use `investment_sources`; do not call casually. |
| `GET /api/investment/detection-runs*` | `backend/api/investment/router.py` | Detection run status/list/detail/readiness | `DetectionRun`, detection readiness service | real | Read-only. |
| `GET /api/investment/situations` | `backend/api/investment/router.py` | List situations | `SpecialSituation` | real | |
| `GET /api/investment/situations/{id}` | `backend/api/investment/router.py` | Situation detail | `SpecialSituation`, linked ResearchCase lookup | real | |
| `PATCH /api/investment/situations/{id}` | `backend/api/investment/router.py` | Update status/notes/etc. | `SpecialSituation`, `SituationHistory` | real | Mutating. |
| `GET /api/investment/situations/{id}/evidence-links` | `backend/api/investment/router.py` | Evidence link package | `evidence_links.py` | real | Derived/read-only. |
| `GET /api/investment/situations/{id}/documentation-guide` | `backend/api/investment/router.py` | Documentation guide | `case_documentation.py` | real | Derived/read-only. |
| `GET /api/investment/situations/{id}/document-package` | `backend/api/investment/router.py` | Document package | `document_package.py` | real | Derived/read-only. |
| `GET /api/investment/situations/{id}/documentation-agent-report` | `backend/api/investment/router.py` | Documentation agent report | `documentation_agent.py` | real | Derived/read-only. |
| `GET/POST /api/investment/situations/{id}/documentation-sources*` | `backend/api/investment/router.py` | Link/upload documentation source metadata | `documentation_sources.py` | partial | Upload/link metadata; not broad web crawling. |
| `GET/PATCH/POST /api/investment/documentation-extractions*` | `backend/api/investment/router.py` | Draft extraction/review | `DocumentationExtractionField`, extraction services | partial | Review workflow exists, evidence still manual. |
| `GET /api/investment/situations/{id}/promotion-readiness` | `backend/api/investment/router.py` | Promotion readiness | `promotion_readiness.py` | real | Read-only. |
| `POST /api/investment/situations/{id}/promote-to-research-case` | `backend/api/investment/router.py` | Manual promotion | `research_cases.py` service | real | Mutating/manual. |
| `GET /api/investment/situations/{id}/official-source-finder` | `backend/api/investment/router.py` | Official source locator package | `official_source_finder.py` | real | Manual locator; no browsing. |
| `GET /api/investment/situations/{id}/historical-analogues` | `backend/api/investment/router.py` | Pattern/historical context | `historical_analogues.py` | real | Read-only. |
| `GET /api/investment/situations/{id}/completion-workbench` | `backend/api/investment/router.py` | Manual completion plan | `case_completion.py` | real | Read-only. |
| `GET/POST /api/investment/situations/{id}/sec-document-acquisition*` | `backend/api/investment/router.py` | SEC metadata acquisition preview/apply | `sec_document_acquisition.py` | partial | POST mutates metadata/candidates only. |
| `GET /api/investment/situations/{id}/activity-timeline` | `backend/api/investment/router.py` | Derived timeline | `case_activity.py` | partial | Not persisted audit log. |
| `GET /api/investment/course-index` | `backend/api/investment/router.py` | Course index | `course_index.py` | partial | Depends on processed course index. |
| `GET /api/investment/course-documentation-map/{type}` | `backend/api/investment/router.py` | Situation type mapping | `course_documentation_map.py` | partial | Some mappings can be sparse. |
| `GET /api/investment/sources` etc. | `backend/api/investment/router.py` | Source registry CRUD/test | `InvestmentSource`, `SECEdgarAdapter` for test | partial | CRUD real; scanner wiring missing. |
| `GET /api/investment/intelligence/kpis` | `backend/api/investment/router.py` | KPI package | `intelligence_kpis.py` | real | Read-only aggregate. |
| `GET /api/investment/intelligence/fontana-report` | `backend/api/investment/router.py` | Fontana diagnostic report | `fontana_report.py` | real | Derived/read-only. |
| `GET /api/investment/executive/dani-weber-metrics` | `backend/api/investment/router.py` | COO metrics | `dani_weber_metrics.py` | real | Derived/read-only. |
| `GET /api/investment/executive/review` | `backend/api/investment/router.py` | Executive Review | `executive_review.py` | real | Derived/read-only. |
| `POST /api/investment/evaluate-v2` | `backend/api/investment/router.py` | Manual v2 evaluation preview/persistence path | evaluator service, run logger | partial | Daily counter, manual-only boundaries in docs. |
| `GET/POST/PATCH /api/investment/research-cases*` | `backend/api/investment/research_cases.py` | ResearchCase workflows | `ResearchCase`, tasks/docs/sources, services | real | Some preview endpoints call AI when invoked. |
| `GET/POST/PATCH /api/investment/historical-cases*` | `backend/api/investment/research_cases.py` | Historical cases | `HistoricalCase`, source intelligence | real | |
| `GET/PATCH /api/investment/public-drafts*` | `backend/api/investment/research_cases.py` | Public drafts | `PublicArticleDraft` | real | Manual publishing workflow; no auto-publish found. |
| `GET /api/agent-ops/rooms*` | `backend/api/agent_ops/router.py` | Agent Ops rooms | DB rooms or governance config/service | real/partial | Room config also exists in service code. |
| `GET /api/agent-ops/agents*` | `backend/api/agent_ops/router.py` | Agent configs/profiles | Agent Ops models/services | real/partial | Many are observer configs. |
| `GET/POST /api/agent-ops/governance/fontana/*` | `backend/api/agent_ops/router.py` | Fontana report/preview | `agent_ops/governance.py`, `agent_runs` | partial | Preview logs run; no report table. |
| `GET/POST /api/agent-ops/governance/dani-weber/*` | `backend/api/agent_ops/router.py` | Dani Weber report/preview | `agent_ops/governance.py`, `agent_runs` | partial | Preview logs run; no report table. |
| `GET /api/agent-ops/execution-calendar` | `backend/api/agent_ops/router.py` | Past/upcoming events | `agent_runs`, `cron_reader` | partial | Derived. |
| `GET /api/agent-ops/activity` | `backend/api/agent_ops/router.py` | Activity feed | `AgentActivity` | real | |
| `GET /api/agent-ops/diagnostics` | `backend/api/agent_ops/router.py` | Diagnostics | `AgentDiagnosticEvent` | real | |
| `GET/PATCH /api/agent-ops/proposals*` | `backend/api/agent_ops/router.py` | Learning proposals/review | `AgentLearningProposal` | real | Only explicit Agent Ops mutation found. |
| `GET /api/observability/runs*` | `backend/api/observability/router.py` | Run list/detail | `AgentRun`, `AiUsage` | real | |
| `GET /api/observability/summary`, `/costs` | `backend/api/observability/router.py` | Aggregates | `AgentRun`, `AiUsage` | real | |
| `GET /api/observability/agents*` | `backend/api/observability/router.py` | Agent registry/detail/text | `agent_registry.py`, `AgentRun` | partial | Registry is code-defined. |
| `GET /api/observability/mission-control*` | `backend/api/observability/router.py` | Mission-control summary | Agent registry + runs | partial | Not the homepage data source. |
| `GET /api/observability/cron/upcoming*` | `backend/api/observability/router.py` | Parsed cron schedule | `cron_reader.py` | partial/unknown | Depends on environment cron visibility. |
| `POST /api/observability/claude-session` | `backend/api/observability/router.py` | Log Claude session | `AgentRun` | real | Mutating run log. |

