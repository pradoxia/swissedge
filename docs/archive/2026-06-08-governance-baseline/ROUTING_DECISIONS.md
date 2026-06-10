Archived: superseded by docs/ux/SCREENSHOT_MAP.md and docs/architecture/SYSTEM_ARCHITECTURE.md

# SwissEdge Routing Decisions

Date: 2026-06-08

## Current Decisions

| Decision | Current route | Rationale |
| --- | --- | --- |
| Governance lives in Agent Ops for now | `/agent-ops` | Agent Ops already contains Executive Office, Fontana, Dani Weber, proposals, activity, diagnostics, and rooms. |
| No dedicated governance route yet | none | The repo audit found no `/governance` route. Adding one is out of scope until governance data contracts are clearer. |
| Mission Control links to governance but does not duplicate it | `/` | Mission Control is the executive hub and navigation surface, not backend truth. |
| Campus remains visual/ops overview | `/campus` | Campus is useful for UX and spatial navigation but is not operational source of truth. |
| SpecialSituation list remains primary triage list | `/investment/situations` | `SpecialSituation` is the current detection/triage object. |
| Situation detail remains main triage/workbench route | `/investment/situations/[id]` | The route contains documentation, evidence, Study Guide, completion, source finder, acquisition, and timeline panels. |
| ResearchCase list remains durable research list | `/investment/research` | `ResearchCase` is the deeper durable research object after manual promotion or intake. |
| ResearchCase detail remains durable research workbench | `/investment/research/[id]` | It owns research tasks, documents, sources, evidence, score, operational view, and publication prep. |
| Legacy evaluations remains accessible but de-emphasized | `/investment/evaluations`, `/investment/evaluations/[id]` | Useful for older/manual evaluator flows, but not the main product model. |
| Watchlist remains accessible but de-emphasized | `/investment/watchlist` | Watchlist is a workflow/state, not a separate primary entity. |

## Route Boundaries

- Do not create `/governance` until a sprint explicitly scopes it.
- Do not move governance out of `/agent-ops` until product routing is approved.
- Do not duplicate complex governance panels on Mission Control; link to Agent Ops instead.
- Do not make Campus the source of operational truth.
- Do not remove legacy routes during governance stabilization.

## Claude Screenshot Implication

For governance UX work, Claude should receive:

- `http://localhost:3000/`
- `http://localhost:3000/agent-ops`
- `http://localhost:3000/campus`

If Claude asks for `/governance`, provide `/agent-ops` and explain that no dedicated governance route exists yet.
