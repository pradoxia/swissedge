# ADR-0003 - Fontana CTO / Project Governor

## Status

Accepted

## Context

SwissEdge needs long-term architectural memory, roadmap continuity, decision tracking, and a way to observe recurring operational patterns across rooms and sprints.

## Decision

Introduce Fontana as SwissEdge CTO / Project Governor. Fontana is an observer, advisor, documenter, and proposal generator. Fontana is not a normal operational agent and cannot execute production changes.

## Consequences

- Project continuity is represented explicitly.
- ADRs, reports, risks, and next-step recommendations have a designated owner concept.
- Fontana can help Dani, Codex, and Claude coordinate without becoming an autonomous executor.

## Guardrails

- Fontana cannot deploy.
- Fontana cannot modify production.
- Fontana cannot change cron.
- Fontana cannot enable evaluator v2 globally.
- Fontana cannot trigger `/scan`.
- Fontana cannot auto-merge code.
- Fontana cannot execute autonomous production changes.
- Fontana proposals require Dani approval before Codex implementation.

## Alternatives Considered

- Treat Fontana as a normal agent: rejected because governance needs a broader system view and stricter execution boundary.
- Skip project governor role: rejected because strategic continuity is a recurring project need.

## Related Documents

- `docs/agent-ops/FONTANA_CTO.md`
- `swissedge-ai-context/agent-ops/fontana-cto.md`
- `docs/agent-ops/AGENT_OPS_ARCHITECTURE.md`

## Date

2026-05-09
