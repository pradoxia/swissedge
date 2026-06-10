# Feature Status Matrix

Date: 2026-06-08

| Feature area | Current status | Existing files | Missing files | Dependencies | Safe to reuse? | Recommended next action |
| --- | --- | --- | --- | --- | --- | --- |
| SpecialSituation detection | partial | `backend/api/investment/router.py`, `backend/services/investment/sec_detection.py`, `backend/services/investment/sources/sec_edgar.py`, `backend/cli/sec_edgar_detect.py`, `backend/models/investment.py` | Source-registry-driven scanner wiring | SEC user agent, Postgres, `SpecialSituation`, `DetectionRun` | Yes, with guardrails | Preserve current path; document/fix scanner-source mismatch before governance changes. |
| Investment situations list | implemented | `frontend/app/investment/situations/page.tsx`, `frontend/lib/api.ts`, `GET /api/investment/situations` | None obvious | `special_situations` rows | Yes | Reuse as primary screenshot/list surface. |
| Situation detail | implemented | `frontend/app/investment/situations/[id]/page.tsx`, related panels | Real sample ID unknown | Situation row plus derived service endpoints | Yes | Use for UX work once a real ID is supplied or queried. |
| Study Guide | partial | `EducationStudyGuidePanel.tsx`, `studyGuideMapping.ts`, `course_index.py`, `course_documentation_map.py`, `docs/COURSE_DOCUMENTATION_MAP.md` | Complete mapping for every situation type/chapter unknown | Processed course index and sanitized maps | Yes | Reuse UI; audit mapping completeness before expanding. |
| Course index / chapter mapping | partial | `backend/services/investment/course_index.py`, `course_documentation_map.py`, `course_index/`, `docs/COURSE_DOCUMENTATION_MAP.md` | Unknown completeness of source references | Sanitized course metadata | Yes | Validate missing chapter/source metadata only. |
| Evidence Lab | designed/partial | `docs/agent-ops/ROOMS.md`, evidence panels/services, `DocumentationExtractionField` | Dedicated Evidence Lab route/persisted room outputs | Situation/ResearchCase evidence/document services | Reuse pieces | Keep as concept plus panels; do not invent new room persistence yet. |
| Playbook Workshop | designed/partial | `docs/agent-ops/ROOMS.md`, `course_documentation_map.py`, `studyGuideMapping.ts` | Dedicated route/persisted playbook-workshop outputs | Course maps, playbooks | Reuse pieces | Treat as designed room; improve maps before UI expansion. |
| Research Desk | designed/partial | `docs/agent-ops/ROOMS.md`, ResearchCase pages/services | Dedicated room route/persisted room outputs | ResearchCase tables | Yes | Reuse ResearchCase list/detail as current real implementation. |
| Quality Court | designed/partial | `docs/agent-ops/ROOMS.md`, `case_completion.py`, `intelligence_score.py`, Agent Ops diagnostics | Dedicated quality decisions/reviews | Completion/workbench data | Reuse pieces | Keep read-only until governance decisions are modeled. |
| Agent Ops rooms | partial | `frontend/app/agent-ops/page.tsx`, `rooms/[id]/page.tsx`, `backend/api/agent_ops/router.py`, `AgentRoom` | Room-specific persisted outputs, score snapshot | Agent Ops DB/config | Yes | Reuse for governance baseline; avoid profile mutation until endpoint exists. |
| Agent cards | partial | `AgentStatusBadge.tsx`, `AgentSafetyCard.tsx`, `AgentConfigPanel.tsx`, `campus-config.ts` | Safe profile edit endpoint | Agent registry/Agent Ops config | Yes | Reuse card design; mark static/config-derived fields. |
| Agent activity/logs | partial | `AgentActivity`, `AgentRun`, `run_logger.py`, Agent Ops/observability routes | Comprehensive logs for every configured agent | Run logging integration | Yes | Reuse run/activity schema; do not assume all agents have runs. |
| Campus | partial | `frontend/app/campus/**`, `frontend/public/campus/**` | Campus DB model | Observability, cron, static config/assets | Yes | Use for UX screenshots; clarify static-vs-live data. |
| Mission Control | partial | `frontend/app/page.tsx`, `backend/api/observability/router.py` | Unified backend-driven Mission Control data contract | Static frontend arrays + observability APIs | Yes | Reuse as hub; avoid treating hardcoded statuses as source of truth. |
| Observability agents | partial | `backend/services/observability/agent_registry.py`, `backend/api/observability/router.py`, `frontend/app/agents/**` | Runtime coverage for all conceptual agents | `agent_runs`, `ai_usage` | Yes | Reuse registry/runs; flag stale/no-run agents. |
| Fontana report | partial | `FontanaReportPanel.tsx`, `fontana_report.py`, `agent_ops/governance.py`, Fontana docs | Persisted report table and approval workflow | Agent Ops, runs, detection/course data | Yes | Reuse deterministic read-only report; no autonomous actions. |
| Dani Weber metrics | partial | `DaniWeberReportPanel.tsx`, `dani_weber_metrics.py`, `executive_review.py`, `agent_ops/governance.py` | Persisted COO decision model | Situations, ResearchCases, extraction fields | Yes | Reuse metrics for process governance only. |
| Governance panels | partial | `frontend/app/agent-ops/page.tsx`, `FontanaReportPanel.tsx`, `DaniWeberReportPanel.tsx`, Executive Review service | Dedicated `/governance` route, persisted decisions/reports | Existing reports/proposals | Yes | Keep inside Agent Ops/Mission Control until product model is decided. |
| Scanner / detection runs | partial | `DetectionRun`, detection run services/routes, Radar Status page | Source-registry-driven scan, richer funnel diagnostics | SEC adapter, cron wrapper, DB | Yes | Reuse logs; do not change cron or scan behavior yet. |
| Intelligence scoring | implemented/partial | `intelligence_score.py`, `IntelligenceScoreCard.tsx`, tests | Unknown calibration/ground truth | Situation/ResearchCase evidence/doc data | Yes | Reuse as preparation-quality score, not investment advice. |
| Sprint log / product docs | implemented | `docs/sprints/**`, `docs/PROJECT_STATE*.md`, `docs/product/**`, `docs/investment/**` | Single current source of truth before this audit | Human-maintained docs | Yes | Use these new `docs/context/*` files as coordination baseline. |

## What Should Not Be Touched Yet

- `/api/investment/scan` behavior, SEC scanner coverage, cron schedules, or deployment scripts.
- Source registry semantics beyond documenting current mismatch.
- Live AI/evaluator defaults.
- Public publishing automation.
- Agent autonomy or governance write paths beyond existing proposal review.
- Marketplace/Sales surfaces unless separately scoped.

