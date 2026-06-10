Archived: superseded by docs/product/ROADMAP.md

# SwissEdge Next Sprint Plan

Date: 2026-06-08

## Sprint 1 Candidate

### Name

Governance Surface Stabilization

### Goal

Make the current governance surface in `/agent-ops` clear, safe, read-only, and visually understandable without adding a new route, persistence layer, scanner behavior, cron behavior, or live-AI behavior.

### Why Now

The repo audit established that `/agent-ops` is the current governance surface and no `/governance` route exists. Fontana, Dani Weber, and Executive Review already have deterministic read-only endpoint data and UI surfaces, but the governance model needs to be visually obvious and guardrail-safe before deeper governance or implementation work begins.

### Scope

- Keep governance in `/agent-ops`.
- Make Executive Office visually clear.
- Make Fontana and Dani Weber panels clearly read-only.
- Ensure guardrail notes are always visible.
- Ensure stuck cases link to case detail when IDs exist.
- Ensure reports use existing endpoint data.
- Ensure safe empty states for missing/stale data.
- Ensure Mission Control clearly links to Agent Ops.
- Update documentation references to this governance baseline where explicitly needed.

### Out Of Scope

- Do not add persistence yet.
- Do not create `/governance`.
- Do not touch scanner behavior.
- Do not touch cron behavior.
- Do not trigger `/api/investment/scan`.
- Do not activate live AI.
- Do not add autonomous governance actions.
- Do not create investment recommendations.
- Do not auto-publish, auto-discard, auto-promote, or auto-verify evidence.
- Do not refactor unrelated Agent Ops, investment, marketplace, or public-site code.

### Files Likely Involved

- `frontend/app/agent-ops/page.tsx`
- `frontend/app/components/FontanaReportPanel.tsx`
- `frontend/app/components/DaniWeberReportPanel.tsx`
- `frontend/app/page.tsx`
- `frontend/lib/api.ts` only if existing types are insufficient
- `docs/governance/*`

Backend files should not be changed unless verification proves an existing endpoint contract is broken.

### Risks

- Static/derived governance UI could be mistaken for authoritative persisted decisions.
- Fontana/Dani wording could accidentally imply investment advice.
- Empty states could look like system failure rather than missing data.
- Mission Control could duplicate governance instead of linking to it.
- Stuck-case links may be unavailable when IDs are missing.

### Acceptance Criteria

- `/agent-ops` clearly shows Executive Office.
- Fontana and Dani Weber panels render from existing endpoints.
- Fontana and Dani Weber panels are clearly read-only/diagnostic.
- Guardrail notes are always visible.
- No investment recommendation language appears.
- No buy/sell language appears in governance agent outputs.
- Empty states are safe and explicit.
- Stuck cases link to case detail when IDs exist.
- Mission Control links clearly to Agent Ops.
- No `/governance` route is created.
- No scanner, cron, live-AI, migration, publication, or autonomous action behavior changes.
- Documentation references this governance baseline.

### Claude Screenshots Required

Minimum:

- `http://localhost:3000/`
- `http://localhost:3000/agent-ops`
- `http://localhost:3000/campus`
- `http://localhost:3000/investment/situations`
- `http://localhost:3000/investment/radar-status`
- `http://localhost:3000/investment/intelligence`

If available:

- `http://localhost:3000/investment/situations/<REAL_SITUATION_ID>`
- `http://localhost:3000/investment/research/<REAL_RESEARCH_CASE_ID>`
- `http://localhost:3000/agent-ops/rooms/executive_office`

Label each screenshot as real, partial, mock, empty, or unknown.

### Codex Implementation Tasks

- Inspect `/agent-ops` and Mission Control current UI.
- Implement only scoped visual/read-only clarity changes.
- Keep existing endpoint usage.
- Preserve current route structure.
- Ensure guardrail text is visible.
- Make safe empty states explicit.
- Verify no scanner/cron/live-AI/publication behavior changed.
- Run a scoped build or lint check if feasible.

### Claude Code Verification Tasks

- Review diff for out-of-scope changes.
- Verify no `/governance` route was created.
- Verify `/agent-ops` still uses existing endpoints.
- Verify guardrails are visible.
- Verify no investment recommendation or buy/sell language.
- Verify empty states are explicit.
- Verify Mission Control links to Agent Ops.
- Verify scanner, cron, live AI, migrations, APIs, and routes were not changed.

## Recommended Sprint 1 Decision

Proceed with "Governance Surface Stabilization" before adding governance persistence, a dedicated route, or new authority models.
