# ADR-0002 - Agent Ops & Learning Layer

## Status

Accepted

## Context

SwissEdge is becoming a source-driven ResearchCase platform. Before adding autonomy, the system needs observability, diagnostics, routing audits, activity tracking, and human-reviewed learning proposals.

## Decision

Define Agent Ops as an observability-first layer with rooms, agents, activities, diagnostics, metrics, proposals, routing audits, and future Mission Control UI.

Agent Ops starts as documentation and later additive backend tables/APIs. It must not change scanner, evaluator, source registry, cron, publishing, or deployment behavior by default.

## Consequences

- Sprint H backend foundation can implement known schema/API basics instead of inventing them.
- Operators can distinguish observations from actions.
- Learning proposals become explicit and reviewable.
- Fail-safe logging becomes a core implementation requirement.

## Guardrails

- No autonomous scans.
- No cron changes.
- No evaluator v2 global enablement.
- No autonomous source changes.
- No autonomous routing changes.
- No autonomous deploys.
- No live AI unless explicitly authorized.
- No proposal auto-apply.
- No secrets or raw course content in metadata/evidence fields.

## Alternatives Considered

- Build autonomous agents first: rejected as unsafe without diagnostics and approval workflows.
- Keep diagnostics only in ad hoc logs: rejected because long-term learning and UI visibility require structured records.

## Related Documents

- `docs/agent-ops/AGENT_OPS_ARCHITECTURE.md`
- `docs/agent-ops/DATA_MODEL.md`
- `docs/agent-ops/API_SPEC.md`
- `docs/agent-ops/METRICS.md`
- `docs/agent-ops/UI_SPEC.md`
- `docs/agent-ops/ROUTING_AUDITS.md`

## Date

2026-05-09
