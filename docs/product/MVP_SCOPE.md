---
document_id: MVP_SCOPE
title: MVP Scope
version: 0.4.0
status: active
owner: Dani
last_updated: 2026-06-09
source_of_truth: true
review_cycle: manual
---

# SwissEdge MVP Scope

Date: 2026-06-09

## MVP Goal

The MVP is a private, human-reviewed research operating system that can run the central special situations research loop end-to-end:

`Detect -> Triage -> Acquire Documents -> Analyze Preview -> Brief -> Human Decision`

MVP v3 is complete when at least 3 cases are decided per week with no more than 2 hours of Dani time per case, sustained for 2 consecutive weeks.

## In MVP

- `SpecialSituation` detection and triage workflow.
- SEC EDGAR scheduled detection code-readiness using a shared orchestrator and `DetectionRun` logging; operational cron activation still requires Dani approval.
- Research Inbox or equivalent triage queue for detected situations and open research work.
- SEC document body acquisition under explicit manual action.
- AI-assisted preview-only analysis and brief generation after explicit approval.
- Human approval section-by-section before AI output is persisted.
- 14-section brief completion workflow.
- Decision logging with decision, reason, author, and date.
- North Star metrics: decided cases per week and Dani time per case.
- `ResearchCase` durable research workflow.
- Manual promotion from `SpecialSituation` to `ResearchCase`.
- Situation list and detail workbench.
- ResearchCase list and detail workbench.
- Evidence/document package visibility.
- Study Guide and playbook mapping surfaces.
- Radar/detection run status.
- Agent Ops governance surface as supporting visibility.
- Fontana and Dani Weber read-only diagnostic panels as supporting visibility.
- Observability agent registry and execution history as supporting visibility.
- Screenshot protocol for Claude UX work.
- Guardrails for scanner, cron, live AI, publishing, and investment language.

## Supporting Governance Surface

- `/agent-ops` is the current operational governance center for the MVP.
- Fontana is displayed as CTO / System Governor.
- Dani Weber is displayed as COO / Operations Governor.
- Both panels are read-only and `diagnostic_only`.
- Executive Review is a read-only governance summary, not an investment recommendation or case decision.
- Governance proposals require human approval before implementation.
- No canonical `/governance` route is implemented yet.
- Fontana, Dani Weber, Executive Review, Agent Rooms 2.0, Intelligence KPIs, and context packs are not MVP completion criteria.

## Explicitly Out Of MVP

- Auto-trading.
- Investment recommendations as final user advice.
- Buy/sell instructions.
- Auto-publishing.
- Autonomous case promotion.
- Autonomous discard.
- Autonomous evidence verification.
- Governance-agent data mutation.
- Cron changes without explicit approval.
- Evaluator v2 global rollout without explicit approval.
- Dedicated production-grade `/investment/governance` implementation unless scoped separately.
- Full source-registry-driven scanner rewrite.
- Scheduler activation without Dani approval.
- Live AI activation without Dani approval.
- SEC document body persistence or `body_text` migration without explicit approval.
- Decision log model/migration changes without explicit approval.
- Any persistence of AI output without explicit approval.
- Fontana/Dani Weber as acceptance criteria for MVP completion.
- Executive Review as acceptance criteria for MVP completion.
- Agent Rooms 2.0.
- Intelligence KPIs as a standalone MVP surface.
- Context packs as product acceptance criteria.

## Post-MVP

- Canonical `/investment/governance` route if approved.
- Persisted governance report snapshots.
- Agent findings and recommendations as first-class entities.
- Source-registry-driven scanner execution.
- Richer scanner funnel diagnostics.
- Agent profile pages/cards with complete skills, permissions, next run, and logs.
- More complete Evidence Lab, Playbook Workshop, Research Desk, and Quality Court room outputs.
- Formal governance decision log.
- Eval harness / golden set for classification and analysis regression testing.
- Real LLM pipeline agents after the gated preview workflow is validated.
- Fontana/Dani Weber LLM-assisted governance after the research loop proves value.

## Future / Later Research

- Additional source connectors beyond SEC EDGAR.
- External public publishing workflow after manual approval model is complete.
- Market monitoring beyond official filings.
- Contact discovery and outreach support.
- Deeper course/playbook mapping and methodology gap workflows.
- Automated scheduling only after explicit safety review.

## Scheduled Detection Boundary

Scheduled SEC EDGAR detection is in MVP only as a controlled, metadata-only triage flow:

- Source is limited to `sec_edgar`.
- Manual scan and scheduled scan share the same orchestrator.
- The intended schedule is Monday-Friday at 08:00, 14:00, and 20:00 Europe/Zurich.
- Scheduled runs record `DetectionRun` status, counters, warnings, errors, source, trigger type, and dry-run mode.
- Created records are `SpecialSituation` triage candidates only and require human review.
- No scheduled flow may create `ResearchCase` records, promote, discard, publish, run live AI, or produce investment recommendations.
- Cron is code-ready but not operationally activated until Dani approves it.

## MVP v3 Planned Implementation Boundaries

- M1 SEC document acquisition v2 adds document body text after explicit approval.
- M2 gated AI analysis adds preview-only analysis and brief generation after explicit approval.
- M3 Research Inbox and one-click human decision adds the queue and decision log after explicit approval for any required model or migration changes.
- M4 consolidated workbench simplifies the active research surface.
- M5 North Star metrics validates throughput and Dani time per case.
- M6 hardening absorbs parsing, retry, UX, and documentation issues found in real cases.

These items define MVP v3 direction. This document does not claim they are already implemented unless the current runtime already supports them.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.4.0 | 2026-06-09 | Codex | Adopted MVP v3 scope: end-to-end research loop, North Star Metric, planned document acquisition/AI preview/decision logging, and governance demoted from completion criteria to supporting visibility. |
| 0.3.0 | 2026-06-09 | Codex | Added controlled scheduled SEC EDGAR detection as an MVP triage capability with explicit guardrails. |
| 0.2.0 | 2026-06-08 | Codex | Added MVP governance surface definition for `/agent-ops`. |
| 0.1.0 | 2026-06-08 | Codex | Initial official version. |
