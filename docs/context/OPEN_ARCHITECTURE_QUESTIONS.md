# Open Architecture Questions

Date: 2026-06-08

## Product Model

- Should `SpecialSituation` remain the visible triage object long-term, or should `ResearchCase` become the primary operating object after source-driven intake? Current split is in `backend/models/investment.py` and `backend/models/investment_research.py`.
- Should Mission Control statuses in `frontend/app/page.tsx` stay as curated product labels, or be sourced from a backend status contract?
- Should `/investment/evaluations` and `/investment/watchlist` remain accessible legacy/advanced surfaces, or be hidden behind a lower-priority navigation model?
- What is the exact governance boundary between Dani Weber process authority, Fontana technical governance, and Agent Ops proposals?

## Data Model

- Should Fontana and Dani Weber reports be persisted as first-class tables, or remain derived views plus optional `AgentRun` preview logs? Current code: `backend/services/agent_ops/governance.py`, `backend/services/investment/fontana_report.py`, `backend/services/investment/dani_weber_metrics.py`.
- Should governance decisions be modeled separately from `AgentLearningProposal`? Current proposal model is `backend/models/agent_ops.py`.
- Should `InvestmentSource` gain/require `connector_key` and stricter source-type vocabulary before scanner rewiring? Current model: `backend/models/investment.py`.
- Should `CaseActivityTimeline` become a persisted audit log, or stay a derived/current-state package? Current service: `backend/services/investment/case_activity.py`.
- Should documentation extraction statuses include `verified`? `backend/services/agent_ops/governance.py` counts `DocumentationExtractionField.status == "verified"`, while model default/review values need validation against actual UI/API vocabulary.

## Frontend Routing

- Is a dedicated `/governance` route desired, or should governance remain inside `/` Mission Control and `/agent-ops` Executive Office? No `/governance` page exists under `frontend/app`.
- Should `/campus` be a primary work surface or a visual navigation/ops overview? It currently mixes static config/assets with observability data in `frontend/app/campus`.
- Which detail route should Claude optimize first: `/investment/situations/[id]` or `/investment/research/[id]`?
- Should legacy `/investment/evaluations/[id]` stay available for v2 preview and old workflows?

## Backend / API

- When should `/api/investment/scan` switch from hardcoded `SECEdgarAdapter` to active `investment_sources` rows? Current mismatch is documented in `docs/investment/RADAR_RELIABILITY_AUDIT.md` and visible in `backend/api/investment/router.py`.
- Should scanner write preliminary `ResearchCase` records directly, or continue writing `SpecialSituation` until manual promotion?
- Should `POST /api/agent-ops/governance/*/run-preview` write only `AgentRun`, or also persist report snapshots?
- Should Agent Ops config endpoints read DB `AgentRoom`/`AgentProfile` rows, static `governance.py` config, or both?
- Which preview endpoints are allowed to call AI locally, and how should UX mark them? Examples are in `backend/api/investment/research_cases.py` and `backend/api/investment/router.py`.

## Agents / Governance

- What is the approval lifecycle for improvement proposals before Codex/Claude implementation? Existing PATCH only updates Agent Ops proposal status/reviewer note in `backend/api/agent_ops/router.py`.
- Should Fontana be allowed to create proposal records automatically, or only generate read-only report items?
- Should Dani Weber metrics create actionable workflow tasks, or remain dashboard-only?
- Which agents are real runtime agents versus configured observer/persona entries? Current catalog is in `backend/services/agent_ops/governance.py` and `backend/services/observability/agent_registry.py`.

## Observability

- Is `cron_reader` expected to read local developer crons, production crons, or a generated deployment schedule? Current routes: `backend/api/observability/router.py`.
- Should `DetectionRun` and `AgentRun` be joined in a common operations timeline?
- What is the required retention policy for `AgentRun`, `AiUsage`, `AgentActivity`, and diagnostics?
- How should empty scanner runs explain whether zero results came from SEC errors, no raw hits, unclassified hits, duplicates, or filters?

## UX / Claude Work

- Claude needs real IDs for `/investment/situations/[id]` and `/investment/research/[id]`. No real committed IDs were found.
- Which viewport set should be canonical for screenshots: desktop only, or desktop plus mobile for every key route?
- Should Claude treat placeholder/static sections as design targets or as areas to preserve until backend contracts are settled?
- Should Study Guide screenshots use a `tender_offer`/`SC TO-I` case specifically, or any mapped situation type?

## Security / Guardrails

- Keep `.env`, private deployment targets, server paths, and secrets out of AI-safe docs. Existing docs already warn about older deploy scripts containing private targets.
- Do not trigger `/api/investment/scan`, live AI previews, cron installation, publication, or document fetching during UX/governance work.
- Governance surfaces must not imply investment advice or auto-approval. This is reinforced in `backend/services/agent_ops/governance.py` guardrails.
- Public-site content should remain manually approved/static until publication workflow is explicitly implemented.

## Technical Debt

- Scanner source-registry mismatch: `InvestmentSource` UI/API is real but not used by `/scan`.
- Mission Control hardcoded statuses can drift from backend truth.
- Agent Ops has both persisted models and code-defined config; source of truth needs clarification.
- Campus is visually rich but static/config-derived in important places.
- No dedicated governance persistence model.
- No verified sample screenshot IDs.
- Legacy/advanced investment routes may confuse current product model.
- Older scripts under `scripts/` include production/deployment/cron behavior and should be handled carefully.

## Reusable Now

- `SpecialSituation`, `ResearchCase`, `DetectionRun`, `AgentRun`, Agent Ops models.
- Situation list/detail, ResearchCase list/detail, Agent Ops, Campus, Mission Control, Radar Status, Intelligence KPIs.
- Read-only Fontana/Dani/Executive Review services and panels.
- Course/Study Guide metadata surfaces, with caveat that mappings need audit.
- Existing sprint/product docs as historical context, with these `docs/context/*` files as the new baseline.

## Should Not Be Touched Yet

- Scanner behavior, cron, source-registry scanner wiring, live AI defaults, evaluator global behavior, publication automation, marketplace/sales, deployment scripts, and governance write models.

## Recommended 3-Step Next Plan

1. Validate runtime truth: start local backend/frontend, collect real IDs from `/api/investment/situations` and `/api/investment/research-cases`, then update `SAMPLE_SCREENSHOT_URLS.md`.
2. Decide source of truth: choose whether governance/Mission Control data remains derived/static or gets explicit backend contracts and persistence.
3. Scope one narrow governance sprint: likely source-registry/scanner mismatch documentation or read-only governance report persistence, with no scanner/cron/live-AI behavior changes.
