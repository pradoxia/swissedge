# SwissEdge Engineering Workflow

## Roles

| Role | Tool | Responsibility |
|---|---|---|
| Architect / Product Owner | ChatGPT | Roadmap, sprint scope, guardrails, acceptance criteria |
| Engineer / Implementer | Codex | Implement scoped work, tests, build, final implementation report |
| Reviewer / Auditor | Claude Code | Review diff only, GO/NO-GO, detect scope/safety risks |
| Tester / Approver | Dani | Manual deploy, smoke test, priority decisions |

## Sprint Lifecycle

PLANNED → IMPLEMENTING → READY_FOR_REVIEW → REVIEW_GO → DEPLOYED → VALIDATED → CLOSED

## Core Rules

- Codex implements.
- Claude reviews.
- ChatGPT plans.
- Dani deploys and validates.
- No agent deploys without Dani.
- No migrations without explicit approval.
- No scanner, cron, v2 global, publishing, or Marketplace/Sales changes unless explicitly scoped.

## Investment Guardrails

- Educational research only.
- No financial advice.
- No buy/sell recommendation language.
- Use readiness labels only:
  - monitor
  - not_actionable
  - needs_more_work
  - candidate
- Always include: "Este análisis es educativo. No es asesoramiento financiero."

## Token Saving Rules

- Use docs/PROJECT_STATE_LIGHT.md first.
- Read docs/PROJECT_STATE.md only when explicitly needed.
- Read only listed files.
- One sprint = one fresh session.
- Claude reviews only changed files/diff.
- Avoid broad repo scans.

## Repo / VPS Drift

If VPS behavior differs from repo:
1. Stop.
2. Report drift.
3. Do not overwrite production behavior blindly.
4. Bring repo back in sync deliberately.
5. Dani approves deploy.

## State Updates

- PROJECT_STATE_LIGHT.md: compact active status.
- PROJECT_STATE.md: full canonical history.
- decisions.md: only real architecture decisions.
