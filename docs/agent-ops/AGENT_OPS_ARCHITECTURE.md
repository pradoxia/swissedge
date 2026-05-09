# SwissEdge Agent Ops & Learning Layer Architecture

## 1. Purpose

Agent Ops exists to make SwissEdge explainable, observable, and capable of learning safely over time.

It provides:

- Observability across source intake, scanner diagnostics, ResearchCase workflow, evidence quality, routing, and publication safety.
- Diagnostics that explain where pipelines are succeeding, failing, noisy, stale, or misleading.
- Learning proposals that capture improvement ideas without applying them automatically.
- Activity tracking for rooms, agents, runs, diagnostics, and outcomes.
- Routing audits for deterministic methodology decisions.
- Room and agent visibility for Mission Control.
- Long-term system learning without autonomous production mutation.
- Operational intelligence for Dani, Codex, Claude, and future agents.

## 2. Strategic Principle

Agent Ops is not autonomy first. It is observability first.

Initial implementation should:

- Observe.
- Log.
- Diagnose.
- Propose.
- Visualize.

Initial implementation must not:

- Make autonomous production changes.
- Deploy autonomously.
- Change evaluator behavior autonomously.
- Modify routing rules autonomously.
- Trigger scans autonomously.
- Change source registry behavior autonomously.

## 3. Relationship to Investment Platform V2

Agent Ops supports Investment Platform V2 by making the source-driven ResearchCase pipeline auditable.

It should help explain:

- Which `investment_sources` are active, missing connectors, stale, or producing no cases.
- Whether SEC EDGAR diagnostics show raw hits, parsed filings, classified candidates, skips, duplicates, and created records.
- Whether ResearchCases are created with V2 metadata, tasks, sources, evidence level, official-source status, and methodology status.
- Whether Research Inbox buckets reflect backend reality.
- Whether Internal Audit findings are recurring.
- Whether future source-driven intake is reliable before any autonomy is introduced.

Agent Ops should remain additive. It must not become a hidden control plane for scanner, cron, evaluator, source registry, or publishing behavior.

## 4. Room Model

Rooms are conceptual operating areas:

- Radar Room: detection, scanner health, SEC EDGAR coverage, source funnel diagnostics.
- Evidence Lab: filings, documents, snippets, source provenance, official-source status, evidence quality.
- Research Desk: ResearchCases, Research Inbox, briefs, tasks, enrichment, readiness.
- Quality Court: false positives, stale cases, methodology gaps, official-source gaps, duplicates, guardrail violations.
- Playbook Workshop: playbook gaps, routing improvements, methodology status, source map, risk patterns, checklist improvements.
- Agent Ops: rooms, agents, activity feed, diagnostics, scoreboards, learning proposals, Fontana reports.

## 5. Agent Model

Initial agents:

- Edgar Scout.
- Form Parser.
- Router Analyst.
- Case Builder.
- Quality Sentinel.
- Playbook Scribe.
- Fontana.

Operational agents are initially observational or manually triggered. Fontana is different: it is a governance agent that observes the whole system conceptually and maintains strategic continuity. Fontana does not execute production changes.

## 6. Learning Loop

The learning loop is:

`activity -> result -> diagnostic event -> learning proposal -> human approval -> Codex implementation -> Claude review -> manual deploy`

Learning proposals are recommendations. They can suggest a routing rule improvement, source addition, UI clarity fix, diagnostic metric, task template, or playbook checklist update. They must not auto-apply.

## 7. Fail-Safe Logging

Agent Ops logging must never break scanner, evaluator, ResearchCase, source intake, or publishing flows.

Logging should be best-effort and fail-safe:

- Primary workflow succeeds even if Agent Ops logging fails.
- Logging errors are isolated and observable.
- Agent Ops never blocks critical user-facing flows unless an explicit future hard safety gate is approved.

## 8. Guardrails

Permanent guardrails:

- No `/api/investment/scan` trigger unless explicitly approved.
- No cron changes unless explicitly approved.
- No evaluator v2 global enablement.
- No live AI unless explicitly authorized.
- No deploy or service restart.
- No autonomous production changes.
- No autonomous routing modifications.
- No autonomous source registry modifications.
- No automatic publication.
- No buy/sell/hold recommendation language.
- No secrets, credentials, private infrastructure details, raw `.env`, private URLs, IPs, Tailscale details, VPS details, or DB dumps.
- No raw course transcripts, audio, video, or copyrighted raw course text.
- Human-in-the-loop always.

## 9. Implementation Phases

- Phase 1: docs.
- Phase 2: backend foundation.
- Phase 3: Mission Control UI.
- Phase 4: fail-safe logger integration.
- Phase 5: controlled learning proposals.
- Phase 6: Fontana reports.

## 10. Non-Goals

This sprint does not change runtime behavior. It does not implement backend tables, services, APIs, frontend UI, migrations, scanner changes, cron changes, evaluator changes, source registry wiring, live AI calls, deployment, or autonomous behavior.

## 11. Implementation Specs

Detailed implementation planning documents:

- `docs/agent-ops/DATA_MODEL.md`
- `docs/agent-ops/API_SPEC.md`
- `docs/agent-ops/UI_SPEC.md`
- `docs/agent-ops/METRICS.md`
- `docs/agent-ops/FONTANA_CTO.md`
- `docs/agent-ops/ROUTING_AUDITS.md`
- `docs/ADR/0002-agent-ops-learning-layer.md`
- `docs/ADR/0003-fontana-cto-project-governor.md`
