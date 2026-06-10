# Screenshot Map

Date: 2026-06-08

Base local frontend URL: `http://localhost:3000`

Claude should receive real local URLs only. Dynamic detail routes require real IDs from a running backend/database. Do not invent IDs.

| Route path | Local dev URL | Page/component file | Purpose | Required data/state | Needs real ID? | How to obtain ID | Recommended screenshots | Notes for Claude |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/investment/situations` | `http://localhost:3000/investment/situations` | `frontend/app/investment/situations/page.tsx` | Investment situations list/Kanban | Backend running; `GET /api/investment/situations` reachable | No | Not needed | Full page at desktop and mobile; filters; one populated column/card if data exists | This is the primary real situation list surface. |
| `/investment/situations/[id]` | `http://localhost:3000/investment/situations/<SITUATION_ID>` | `frontend/app/investment/situations/[id]/page.tsx` | Situation detail page | A real `SpecialSituation.id`; supporting derived endpoints | Yes | Open `/investment/situations`, click a card, or call `GET /api/investment/situations` and copy an `id` | Header/workbench; Study Guide panel; Evidence/Document Package; Official Source Finder; SEC Acquisition; Activity Timeline | Use a real ID only. If no data exists, mark unavailable. |
| Situation detail with Study Guide | `http://localhost:3000/investment/situations/<SITUATION_ID>` | `EducationStudyGuidePanel.tsx` inside situation detail | Study Guide section | Situation with `situation_type`, `filing_type`, or mapped guide data | Yes | Prefer a tender_offer/SC TO-I situation from list/API | Screenshot the Study Guide panel expanded and any placeholder/gap state | Study Guide can show safe placeholder/gap text when mapping is incomplete. |
| `/agent-ops` | `http://localhost:3000/agent-ops` | `frontend/app/agent-ops/page.tsx` | Agent Ops and Executive Office | Agent Ops, Fontana, Dani Weber, Executive Review endpoints reachable | No | Not needed | Top overview; rooms; activity/diagnostics/proposals; Fontana panel; Dani Weber panel | Read-only governance surface except proposal review controls. |
| `/agent-ops/rooms/[id]` | `http://localhost:3000/agent-ops/rooms/detection_room` | `frontend/app/agent-ops/rooms/[id]/page.tsx` | Agent room detail | Room key and Agent Ops APIs | Uses key | Known keys in `backend/services/agent_ops/governance.py`: `detection_room`, `evidence_lab`, `playbook_workshop`, `research_desk`, `quality_court`, `executive_office` | Room header, agent cards, activity/diagnostics/proposals | Use `executive_office` for Fontana/Dani governance context. |
| `/agent-ops/calendar` | `http://localhost:3000/agent-ops/calendar` | `frontend/app/agent-ops/calendar/page.tsx` | Execution calendar | Cron reader endpoint data | No | Not needed | Calendar/list view and empty/error state | Environment-dependent; may be empty locally. |
| `/campus` | `http://localhost:3000/campus` | `frontend/app/campus/page.tsx`, `CampusView.tsx` | Visual Operations Campus | Static assets plus observability APIs | No | Not needed | Full campus first viewport; selected building/agent overlay; mobile view | Distinguish visual config/assets from live run data. |
| `/` | `http://localhost:3000/` | `frontend/app/page.tsx` | Mission Control hub | No backend required for static content | No | Not needed | First viewport; Investment Operations; Executive Office; Platform Observability; Deployment Verification Checklist | Statuses/checklist are hardcoded frontend metadata. |
| Governance page | UNKNOWN | None found | Dedicated governance page | Unknown | Unknown | No `/governance` route found in `frontend/app` | Use `/agent-ops` and `/` Executive Office sections instead | Do not ask Claude to capture `/governance` unless a route is added later. |
| Fontana on Agent Ops | `http://localhost:3000/agent-ops` | `FontanaReportPanel.tsx`, `frontend/app/agent-ops/page.tsx` | CTO/governance report | Fontana report endpoints | No | Not needed | Fontana Office card/report section; Executive Review if visible | Fontana is deterministic/read-only; no autonomous execution. |
| Fontana on Mission Control | `http://localhost:3000/` | `frontend/app/page.tsx` | Executive Office link/card | Static homepage data | No | Not needed | Executive Office section | Homepage card links to `/agent-ops`. |
| Dani Weber on Agent Ops | `http://localhost:3000/agent-ops` | `DaniWeberReportPanel.tsx`, `frontend/app/agent-ops/page.tsx` | COO/process metrics | Dani Weber metrics endpoints | No | Not needed | Dani Weber Office card/report section | Metrics are process/governance, not investment decisions. |
| Dani Weber on Mission Control | `http://localhost:3000/` | `frontend/app/page.tsx` | Executive Office link/card | Static homepage data | No | Not needed | Executive Office section | Homepage card links to `/agent-ops`. |
| `/investment/intelligence` | `http://localhost:3000/investment/intelligence` | `frontend/app/investment/intelligence/page.tsx` | Intelligence KPI dashboard | KPI endpoint reachable | No | Not needed | KPI overview, bottlenecks, missing evidence cases | Useful for Fontana/intelligence context. |
| `/investment/radar-status` | `http://localhost:3000/investment/radar-status` | `frontend/app/investment/radar-status/page.tsx` | Scanner/detection status | Observability, sources, cron, detection run endpoints | No | Not needed | Scanner status, source registry summary, cron/upcoming, latest detection | Add note that sources UI does not control scanner yet. |
| `/investment/research` | `http://localhost:3000/investment/research` | `frontend/app/investment/research/page.tsx` | ResearchCase list | ResearchCase and situation APIs | No | Not needed | List/table and linked situation controls | Durable research object list. |
| `/investment/research/[id]` | `http://localhost:3000/investment/research/<RESEARCH_CASE_ID>` | `frontend/app/investment/research/[id]/page.tsx` | ResearchCase detail | A real `ResearchCase.id` | Yes | Open `/investment/research`, click a case, or call `GET /api/investment/research-cases` | Header/workbench, Evidence, Study/Documentation sections, SEC acquisition | Use only real IDs. |

## Minimum URL Set For Claude UX Work

- Situations list: `http://localhost:3000/investment/situations`
- Situation detail: `http://localhost:3000/investment/situations/<REAL_SITUATION_ID>`
- Study Guide: same situation detail URL, with Study Guide visible
- Agent Ops: `http://localhost:3000/agent-ops`
- Campus: `http://localhost:3000/campus`
- Mission Control: `http://localhost:3000/`
- Governance: use `http://localhost:3000/agent-ops` and the Executive Office section; dedicated route is unknown/missing.

