Archived: superseded by docs/README.md and docs/product/PRD.md

# SwissEdge Project Source Of Truth

Date: 2026-06-08

Source baseline:

- `docs/context/REPO_AUDIT.md`
- `docs/context/ROUTE_AND_ENDPOINT_MAP.md`
- `docs/context/FEATURE_STATUS_MATRIX.md`
- `docs/context/SCREENSHOT_MAP.md`
- `docs/context/SAMPLE_SCREENSHOT_URLS.md`
- `docs/context/OPEN_ARCHITECTURE_QUESTIONS.md`

## What SwissEdge Is

SwissEdge is a private investment research operating system. Its current implementation centers on detecting special situations, organizing them into manual research workflows, maintaining evidence and documentation discipline, and exposing operational/governance visibility through Mission Control, Agent Ops, observability, and the Campus UX layer.

SwissEdge is not an autonomous investment decision system. It must not make investment recommendations, publish automatically, discard cases automatically, or bypass Dani approval.

## Current Product Operating Model

The current operating model is:

`SEC EDGAR / detection metadata -> SpecialSituation triage -> evidence and documentation workbench -> manual promotion -> ResearchCase durable research object -> intelligence/readiness/governance review`

Key decisions:

- `SpecialSituation` remains the triage object.
- `ResearchCase` remains the deeper durable research object.
- Watchlist is a workflow/state label, not a separate primary entity.
- `/agent-ops` is the current governance surface.
- There is no dedicated `/governance` route for now.
- Mission Control `/` is an executive hub, not backend truth.
- Campus `/campus` is a visual/UX layer, not operational source of truth.

## Source Of Truth By Area

| Area | Current source of truth | Real | Partial | Static/visual | Must not be treated as source of truth |
| --- | --- | --- | --- | --- | --- |
| Investment situations | `special_situations` via `backend/models/investment.py`, `backend/api/investment/router.py`, `/investment/situations` | Situation rows, status, filing metadata, evaluation JSON | Derived workbench panels and methodology workspace JSON | Kanban visual grouping | Static labels or empty UI states |
| Research cases | `research_cases` and child tables via `backend/models/investment_research.py`, `backend/api/investment/research_cases.py` | ResearchCase, tasks, documents, sources, historical cases | Preview/AI-assisted reports and derived readiness | Research list/detail layout | Legacy situation state as durable research truth |
| Detection runs | `detection_runs`, detection run services, Radar Status | Run counters, status, stored summaries | Funnel diagnosis and empty-run explanation | Radar UI summaries | Source Registry active count as scanner behavior |
| Agent Ops | Agent Ops models plus `backend/api/agent_ops/router.py` and `backend/services/agent_ops/*` | Rooms/profiles/activity/diagnostics/proposals where persisted | Config-derived governance/agent catalog | Room cards, avatars, display labels | Visual room layout as proof of runtime execution |
| Observability | `agent_runs`, `ai_usage`, `backend/api/observability/router.py` | Stored runs and usage | Agent registry coverage for conceptual agents | Agent roster presentation | Missing/stale run panels as proof that an agent does not exist |
| Mission Control | `frontend/app/page.tsx` | Navigation hub and explicit links | Static checklist/status labels | Executive dashboard layout | Backend/runtime truth |
| Campus | `frontend/app/campus/**`, `frontend/public/campus/**`, observability calls | Linked live run/agent data when endpoints respond | Static room/agent configuration | Campus map, buildings, avatars | Operational source of truth |
| Governance agents | Fontana/Dani services and Agent Ops governance panels | Deterministic read-only reports from existing endpoints | No persisted report model yet | Office/panel presentation | Autonomous authority or approval state |
| Study Guide | `EducationStudyGuidePanel.tsx`, `studyGuideMapping.ts`, `course_documentation_map.py`, processed course index | Sanitized mapping metadata where present | Placeholder/gap states for incomplete mappings | Panel layout | Raw course text or complete methodology proof |

## What Is Real

- `SpecialSituation`, `ResearchCase`, `DetectionRun`, `AgentRun`, Agent Ops models.
- Situation list/detail and ResearchCase list/detail routes.
- Agent Ops route and existing Agent Ops endpoints.
- Observability endpoints and run/usage tables.
- Deterministic Fontana, Dani Weber, and Executive Review endpoint data.
- Study Guide mapping infrastructure and sanitized course metadata surfaces.

## What Is Partial

- Source Registry is real as a UI/API/model, but it is not scanner source of truth until `/scan` is wired to `investment_sources`.
- Governance panels are read-only and derived; no dedicated persisted governance report/decision model exists.
- Campus combines real endpoint data with static UX configuration/assets.
- Agent Ops includes real models and APIs, but many agents are observer/config entries rather than independently executing runtime agents.
- Study Guide can show safe placeholders where mapping is incomplete.
- Case activity timelines are derived views, not persisted audit logs.

## What Is Static Or Visual

- Mission Control module statuses and deployment checklist in `frontend/app/page.tsx`.
- Campus map, room assets, and configured agent/building metadata.
- Some Agent Ops cards, avatars, and derived labels.
- Public site prototype/static article data.

## What Must Not Be Treated As Source Of Truth

- Mission Control hardcoded status labels.
- Campus visual configuration.
- Source Registry toggles as scanner behavior.
- Placeholder/gap text as completed methodology.
- Legacy `/investment/evaluations` or `/investment/watchlist` as the primary product model.
- Test fixture companies, IDs, or mocked AI outputs as real data.
- Any screenshot with empty/mock/partial data unless explicitly labeled.
