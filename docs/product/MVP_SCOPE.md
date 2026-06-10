---
document_id: MVP_SCOPE
title: MVP Scope
version: 0.5.0
status: active
owner: Dani
last_updated: 2026-06-10
source_of_truth: true
review_cycle: manual
---

# SwissEdge MVP Scope

Date: 2026-06-10

## MVP Goal

The MVP is a private, human-reviewed research operating system that can run the central special situations research loop end-to-end:

`Detect -> Triage -> Acquire Documents -> Analyze Preview -> Brief -> Human Decision`

MVP v3 is complete when at least 3 cases are decided per week with no more than 2 hours of Dani time per case, sustained for 2 consecutive weeks.

Post-validation operating target: 2 decided cases per day in study mode — each
decision references the applied course chapters (Study Guide), so processing
cases IS studying the course. Fast, well-reasoned rejections count as decided
cases; the goal is building judgment through repetitions.

## Strategic Focus

SwissEdge prioritizes situations where institutional competition is structurally
low: micro/nano-caps, low liquidity, odd-lot tenders, small liquidations. The
detection layer surfaces this explicitly through the Competition Lens
(SEC public float, derived `small_company_flag`) and odd-lot detection. The
lens is a prioritization filter with visible criteria — never a recommendation.

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
- Price connector: daily-close data per ticker via a swappable `PriceProvider`
  (provider decision pending), spread vs offer price for tenders, market cap,
  and average daily volume — prioritization context only.
- Competition Lens v0 (implemented 2026-06-09): SEC public float
  (`dei:EntityPublicFloat`) per created situation with explainable
  `small_company_flag` (< $300M threshold).
- Curated human source intake: minimal manual form (URL, source, ticker, type)
  creating a `SpecialSituation` with `origin=curated` and source attribution,
  entering the same triage loop; per-source CANDIDATE yield is measured. The
  9-source registry lives in PRD §17.1.

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

Scheduled SEC EDGAR detection is in MVP as a controlled, metadata-only triage flow:

- Sources are limited to official SEC hosts (`efts.sec.gov` for search,
  `data.sec.gov` for company facts enrichment).
- Manual scan and scheduled scan share the same orchestrator.
- The intended schedule is Monday-Friday at 08:00, 14:00, and 20:00 Europe/Zurich.
- Cron was operationally activated by Dani on 2026-06-09.
- Scheduled runs record `DetectionRun` status, counters, warnings, errors, source, trigger type, and dry-run mode.
- Created records are `SpecialSituation` triage candidates only and require human review. This includes (since the 2026-06-09 detection quick-wins sprint, Dani-approved): strict-allowlist creations (SC TO-T/I, Form 10) and `candidate_only` creations for medium/high-confidence classified filings (DEFM14A, PREM14A, S-4, SC 14D9, 13E-3, Form 25), 8-K item-code signals (1.03, 3.01, 5.01), and full-text sweep hits ("odd lot", "plan of liquidation", "dutch auction").
- Best-effort market context enrichment (public float, max 10 lookups/run) is descriptive only.
- No scheduled flow may create `ResearchCase` records, promote, discard, publish, run live AI, or produce investment recommendations.

## MVP v3 Implementation Status and Boundaries

| Sprint | Scope | Status (2026-06-10) |
| --- | --- | --- |
| M0 (quick wins) | 8-K items, candidate-only persistence, new forms, EFTS fix, sweeps, Competition Lens v0 | Implemented; 76/76 tests; deploy pending |
| M1 | SEC document body acquisition (text) under explicit manual action | In progress (Codex): `body_text` migration + schema exist locally; F1 promotion bug fixed 2026-06-10; F2 test/schema fixes pending |
| M2 | Gated AI analysis: one "Analyze case" flow unifying document analysis, brief preview, quality preview (preview-only, apply per section) | Not started; underlying services exist (Phase 2A/2D/3C, evaluator v2 shadow-GO); requires explicit live-AI approval |
| M3 | Research Inbox as single queue + one-click decision with persisted `DecisionRecord` (decision, reason, author, date) | Partial: inbox route exists; decision persistence not implemented (migration approval required) |
| M4 (reordered 2026-06-10, was M5) | Price connector + Competition Lens v1 (spread vs offer, market cap, ADV) + curated source intake | Not started; provider decision pending (ChatGPT); Competition Lens v0 shipped in M0. Prioritized ahead of workbench consolidation by Dani: spread math turns detections into actionable numbers and is independent of M2/M3. |
| M5 (reordered, was M4) | Consolidated workbench (Documents / Analysis-Brief / Decision) for ResearchCase detail | Partial: SpecialSituation detail done (Sprint 3A); ResearchCase detail pending |
| M6 | North Star metrics page (cases/week, time per case, funnel, per-origin yield) | Not started |
| M7 | Hardening buffer | Not started |

These items define MVP v3 direction. This document does not claim anything is implemented beyond the status column above.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.5.1 | 2026-06-10 | Claude (Cowork) | Reordered sprints per Dani: price connector (now M4) prioritized ahead of ResearchCase workbench consolidation (now M5). |
| 0.5.0 | 2026-06-10 | Claude (Cowork) | Merged MVP_V3_PROPOSAL v0.2.0: study-mode 2/day target, strategic low-competition focus, price connector + curated intake in scope, detection boundary updated for quick wins + activated cron, sprint table with implementation status. Approved by Dani. |
| 0.4.0 | 2026-06-09 | Codex | Adopted MVP v3 scope: end-to-end research loop, North Star Metric, planned document acquisition/AI preview/decision logging, and governance demoted from completion criteria to supporting visibility. |
| 0.3.0 | 2026-06-09 | Codex | Added controlled scheduled SEC EDGAR detection as an MVP triage capability with explicit guardrails. |
| 0.2.0 | 2026-06-08 | Codex | Added MVP governance surface definition for `/agent-ops`. |
| 0.1.0 | 2026-06-08 | Codex | Initial official version. |
