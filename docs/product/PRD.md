---
document_id: PRD
title: Product Requirements Document
version: 0.3.1
status: active
owner: Dani
last_updated: 2026-06-09
source_of_truth: true
review_cycle: manual
---

# SwissEdge Product Requirements Document

Date: 2026-06-09

## 1. Document Control

| Field | Value |
| --- | --- |
| document_id | PRD |
| title | Product Requirements Document |
| version | 0.3.1 |
| status | active |
| owner | Dani |
| last_updated | 2026-06-09 |
| source_of_truth | true |
| review_cycle | manual |

## 2. Executive Summary

SwissEdge is a private, human-reviewed investment research operating system for special situations. The MVP is complete when the central research loop works end-to-end: SEC EDGAR filing detection, Research Inbox triage, manually approved document acquisition, AI-assisted preview analysis, a completed 14-section brief, and a recorded human decision.

SwissEdge is not an auto-trading product, autonomous investment adviser, or publishing automation system.

## 3. Product Vision

SwissEdge should become Dani's trusted operating system for special situation research: a source-driven, evidence-first workspace where filings become decided cases through a safe, repeatable research loop.

Long term, SwissEdge may support LLM-assisted reasoning and richer agent workflows, but the product foundation must remain deterministic, observable, and safe.

The MVP v3 loop is:

`Detect -> Triage -> Acquire Documents -> Analyze Preview -> Brief -> Human Decision`

The North Star Metric is: at least 3 cases decided per week with no more than 2 hours of Dani time per case, sustained for 2 consecutive weeks.

## 4. Problem Statement

Special situation research is operationally fragile:

- Official signals arrive through filings and source feeds with uneven metadata.
- Important transaction documents and evidence can be buried in noisy or incomplete source material.
- Research can stall when missing documents, weak classification, unclear workflow state, or missing decision records are not visible.
- AI assistance can create risk if it invents facts, collapses unknown states into guidance, or uses investment recommendation language.
- Dani needs a small number of trusted operating surfaces rather than scattered dashboards and ambiguous status pages.

SwissEdge solves this by organizing signals, evidence, workflow state, governance diagnostics, and AI collaboration context around explicit human review.

## 5. Target Users / Personas

| User / Persona | Role | Product Need |
| --- | --- | --- |
| Dani | Product Owner, operator, repository owner, final approver | Review signals, inspect evidence, approve product decisions, validate screenshots, and decide next actions. |
| ChatGPT | Product Architect / PM / Governance Designer | Define product behavior, architecture decisions, sprint prompts, guardrails, and review Codex/Claude outputs. |
| Claude | UX Engineer without repository access | Work from screenshots, URLs, official docs, and task briefs without inventing backend behavior or product rules. |
| Codex | Implementation Engineer with repository access | Implement approved tasks, update docs, respect guardrails, and report verification. |
| Claude Code | Verification Engineer with repository access | Verify builds, tests, wiring, guardrails, regression risk, and compliance with `CLAUDE.md`. |
| Future internal agents | Fontana, Dani Weber, Edgar Scout, Form Parser, Router Analyst, Case Builder, Quality Sentinel, Playbook Scribe | Provide documented personas, deterministic diagnostics where implemented, and future prompt foundations under explicit approval. |

## 6. Goals

- Detect special situation signals from official sources.
- Convert raw signals into structured `SpecialSituation` triage objects.
- Organize evidence, provenance, missing documents, and documentation state.
- Support manual promotion from `SpecialSituation` to `ResearchCase`.
- Provide supporting governance and observability through Agent Ops.
- Keep Fontana, Dani Weber, and Executive Review read-only and diagnostic-only; they are useful support surfaces, not MVP completion criteria.
- Keep Study Guide guidance tied to real mapped chapter references.
- Keep human approval mandatory for promotion, conclusions, publishing, and operational changes.
- Complete the MVP v3 research loop from filing detection to recorded human decision.
- Track the North Star Metric for decided cases and Dani time per case.
- Generate context packs as internal collaboration aids without making them product acceptance criteria or replacing official docs.

## 7. Non-Goals

SwissEdge must not be:

- An auto-trading system.
- An autonomous investment adviser.
- An auto-publishing system.
- An auto-discarding system.
- A replacement for Dani's decision-making.
- A source of buy/sell language in agent outputs.
- A system that treats AI output as final investment advice.
- A system that presents fake, placeholder, unknown, or unmapped data as real guidance.
- A system that changes scanner, cron, publishing, or production behavior without explicit approval.

## 8. Core Concepts and Entities

| Entity | Definition | Purpose | MVP Status | Relationships |
| --- | --- | --- | --- | --- |
| `SpecialSituation` | Triage object created from a detected signal. | Hold raw opportunity context before deeper research. | In MVP. | May be promoted manually to `ResearchCase`; linked to evidence, Study Guide, source data, and activity. |
| `ResearchCase` | Durable deeper research object. | Preserve structured research, documentation, evidence, and readiness. | In MVP. | Can originate from `SpecialSituation`; owns deeper research workflow and documentation state. |
| Watchlist | State/status, not a primary entity. | Mark workflow visibility or tracking posture. | In MVP as status concept. | Applies to cases or situations; does not replace `SpecialSituation` or `ResearchCase`. |
| `DetectionRun` | Record or status of detection/scanner activity. | Explain scan health, timing, and source diagnostics. | In MVP for visibility. | Related to source intake and detected situations; scanner behavior changes require approval. |
| `DecisionRecord` | Planned persisted record of a human decision. | Capture CANDIDATE, WATCHLIST, or REJECT with reason, author, and date. | Planned for MVP v3. | Related to a `SpecialSituation` or `ResearchCase`; requires approved model/migration work before implementation. |
| `AgentRun` | Execution-history concept for agents. | Record when agents run, what they checked, and status. | Partially present / evolving. | Related to observability and future agent history. |
| `AgentActivity` | Activity feed item or diagnostic entry. | Surface agent/process context and issues. | In MVP through Agent Ops surfaces. | Related to rooms, agents, cases, diagnostics, and proposals. |
| Evidence Packet | Group of evidence, links, provenance, and missing evidence state. | Help Dani judge whether a case is sufficiently supported. | In MVP as evidence/documentation visibility. | Related to situations, research cases, document packages, and source registry. |
| Document Package | Organized set of required, candidate, draft, missing, or reviewed documents. | Make documentation completeness and gaps visible. | In MVP. | Feeds promotion readiness and research workflow. |
| SEC Document Body Text | Planned acquired text body for selected SEC documents. | Provide source material for human review and gated AI previews. | Planned for MVP v3; not yet claimed implemented here. | Requires explicit Dani approval if it changes metadata-only acquisition assumptions or needs persistence changes. |
| Study Guide | Course/playbook mapping surface with chapter references. | Connect cases to learning and methodology only when mappings are real. | In MVP with guardrails. | Requires real chapter references; gaps stay separate from course coverage. |
| Source Registry | Catalog of sources and source metadata. | Track source provenance and reliability. | In MVP as visibility; scanner rewiring is future. | Related to evidence, detection, and scanner-source alignment risk. |
| Fontana | CTO / System Governor persona and deterministic diagnostic panel. | Summarize technical/product coherence, risks, guardrails, and sprint options. | In MVP as read-only diagnostics. | Linked to Agent Ops and `docs/agents/FONTANA.md`; not a live LLM agent. |
| Dani Weber | COO / Operations Governor persona and deterministic diagnostic panel. | Summarize funnel, bottlenecks, documentation blockers, and operational improvement opportunities. | In MVP as read-only diagnostics. | Linked to Agent Ops and `docs/agents/DANI_WEBER.md`; not a live LLM agent. |

## 9. MVP Scope

MVP v3 must include:

- SEC EDGAR filing detection as a code-ready scheduled detection flow; operational cron activation still requires Dani approval.
- Research Inbox or equivalent triage queue for new `SpecialSituation` and open `ResearchCase` work.
- Manual SEC document body acquisition for selected case documents.
- AI-assisted preview-only analysis and brief generation after explicit approval.
- Human approval section-by-section before any AI output is persisted.
- 14-section brief completion.
- Human decision logging: CANDIDATE, WATCHLIST, or REJECT with reason and author.
- North Star metrics for decided cases per week and Dani time per case.
- Mission Control `/`.
- `SpecialSituation` list `/investment/situations`.
- `SpecialSituation` detail `/investment/situations/[id]`.
- `ResearchCase` list `/investment/research`.
- `ResearchCase` detail `/investment/research/[id]`.
- Study Guide with real mapped chapter references only.
- Evidence and documentation visibility.
- Manual promotion readiness.
- Clear empty, error, partial, and unknown states.
- Supporting Agent Ops / Governance `/agent-ops`.

MVP must not include:

- Dedicated `/governance` route.
- `/investment/governance` as a current or canonical MVP route.
- Live LLM agents.
- MCP.
- Obsidian vault.
- Scanner-source registry rewiring.
- Cron changes.
- Operational cron activation without Dani approval.
- Live AI activation without Dani approval.
- Auto-fix.
- Auto-publish.
- Auto-discard.
- Investment recommendation automation.
- Persistent governance report tables unless explicitly approved.
- Fontana, Dani Weber, Executive Review, Agent Rooms 2.0, Intelligence KPIs, or context packs as MVP acceptance criteria.

`/investment/governance` may be considered only as a future route if explicitly approved in a later sprint.

## 10. User Journeys

### 10.1 Dani Reviews Detected SpecialSituations

- Entry point: `/investment/situations` or Mission Control `/`.
- Steps: open list, scan statuses, identify promising or blocked situations, open a detail page.
- Expected result: Dani understands which signals need review and which are blocked or incomplete.
- Failure/empty states: list shows explicit empty or unavailable state; no fake situations are shown as real.

### 10.2 Dani Opens a SpecialSituation Workbench

- Entry point: `/investment/situations/[id]`.
- Steps: review summary, filing/source context, evidence, documentation state, Study Guide, and activity.
- Expected result: Dani can decide what research step is needed next.
- Failure/empty states: missing IDs, unavailable evidence, unknown mappings, or backend errors are shown explicitly.

### 10.3 Dani Checks Evidence and Missing Documents

- Entry point: situation or research detail workbench.
- Steps: inspect evidence links, document package, source finder, and missing-document indicators.
- Expected result: Dani sees what exists, what is candidate-only, what is missing, and what remains manual.
- Failure/empty states: candidate metadata is not presented as verified evidence.

### 10.4 Dani Checks Study Guide References

- Entry point: Study Guide panel on case detail.
- Steps: review mapped chapter references, gaps, and methodology notes.
- Expected result: course guidance appears only when a real chapter reference exists.
- Failure/empty states: unmapped cases show `No chapter reference mapped yet`; unknown cases do not default to issuer tender topics.

### 10.5 Dani Decides Whether to Promote to ResearchCase

- Entry point: SpecialSituation detail.
- Steps: review readiness, evidence, documentation blockers, and manual next actions.
- Expected result: Dani decides whether to promote, defer, or gather more evidence.
- Failure/empty states: missing evidence or unknown readiness blocks are visible; promotion is not autonomous.

### 10.6 Dani Completes The MVP v3 Research Loop

- Entry point: Research Inbox or the current triage/research workbench until the inbox is implemented.
- Steps: review a detected filing, triage the situation, manually acquire SEC document text when approved, request preview-only AI assistance when approved, complete the 14-section brief, and record CANDIDATE, WATCHLIST, or REJECT with reason.
- Expected result: a real case reaches a documented human decision inside SwissEdge.
- Failure/empty states: missing document bodies, unavailable AI preview, or undecided status remain explicit and do not become implied recommendations.

### 10.7 Dani Reviews Agent Ops Governance

- Entry point: `/agent-ops`.
- Steps: inspect Executive Office, Fontana, Dani Weber, Executive Review, proposals, rooms, agents, activity, diagnostics, and guardrails.
- Expected result: Dani understands governance posture and can approve or defer future work; this supports the MVP but does not complete it.
- Failure/empty states: unavailable panels show diagnostic-only empty states; no panel implies live AI or autonomous execution.

### 10.8 Dani Uses Context Packs for AI Collaboration

- Entry point: `scripts/context_delivery/build_context_pack.py all` and generated `entrega/*` folders.
- Steps: generate packs, attach the relevant pack to ChatGPT, Claude, Codex, or Claude Code.
- Expected result: each AI receives current official context without secrets or archived docs.
- Failure/empty states: context pack manifests show missing docs; missing required docs must be fixed before relying on the pack.

## 11. Functional Requirements by Surface

### 11.1 Mission Control `/`

- Purpose: executive navigation hub and high-level product entry point.
- Required content: links to core investment surfaces, Agent Ops, and key operational areas.
- Must link to `/agent-ops`.
- Must not be treated as backend source of truth.
- Must distinguish current, supporting, paused, legacy, and future surfaces where relevant.

### 11.2 Agent Ops `/agent-ops`

- Purpose: supporting governance surface.
- Must include Executive Office, Fontana, Dani Weber, Executive Review, proposals, rooms, agents, activity, diagnostics, and guardrail visibility.
- Fontana must be CTO / System Governor and diagnostic-only.
- Dani Weber must be COO / Operations Governor and diagnostic-only.
- Executive Review must combine COO and CTO findings without making investment recommendations.
- Proposals may be reviewed as status/notes only; implementation requires a separate approved sprint.
- Must not trigger scanner, cron, deploy, evaluator rollout, live AI, autonomous execution, publish, discard, or production mutation.

### 11.3 SpecialSituation List `/investment/situations`

- Purpose: show detected or stored triage candidates.
- Required fields: title/company context when available, situation type, status, source/form context, dates, readiness or blocker indicators, and link to detail.
- Must show status clearly.
- Empty state must say when no situations are available rather than fabricating examples.

### 11.4 SpecialSituation Detail `/investment/situations/[id]`

- Required sections: overview, filing/source context, evidence, documentation guide, Study Guide, source finder, document package, promotion readiness, and activity timeline.
- Evidence must distinguish verified, candidate, draft, missing, rejected, and unknown states.
- Documentation guide must show missing requirements and manual next actions.
- Study Guide must follow the mapping rule in section 11.6.
- Promotion readiness must remain human-reviewed.
- Activity timeline must not imply hidden autonomous execution.

### 11.5 ResearchCase List and Detail

- Purpose: durable research workspace for cases that move beyond triage.
- Relationship to `SpecialSituation`: a ResearchCase may be created from a manually promoted SpecialSituation.
- List must show available research cases, status/readiness where available, and detail links.
- Detail must support deeper evidence, documentation, source intelligence, research notes, and readiness review.
- Research workflow must not produce final investment advice or buy/sell recommendations.
- MVP v3 research workflow must support, after separately approved implementation, document acquisition status, preview-only analysis, 14-section brief progress, and human decision state.

### 11.6 Study Guide

- Study Priority cards must require a real `chapter_id` or chapter reference.
- The UI must not show default issuer tender study topics for unmapped or unknown cases.
- If no chapter reference is mapped, the UI must show an explicit empty state such as `No chapter reference mapped yet`.
- Methodology gaps must remain separate from course coverage.
- Unknown mapping must be treated as unknown, not as useful guidance.

### 11.7 Context Packs

- Purpose: provide AI-specific official context bundles for collaboration.
- Generated folders:
  - `entrega/chatgpt`: product, governance, architecture, agent, and sprint context.
  - `entrega/codex`: implementation context.
  - `entrega/claude`: UX and screenshot-based task context.
  - `entrega/claude-code`: verification context.
- Context packs are navigation and handoff aids only.
- Official source of truth remains the documents listed in `docs/DOCUMENT_VERSION_INDEX.md`.
- Packs must not include secrets, `.env`, private paths, or archived docs unless explicitly configured.

## 12. Functional Requirements by Agent

Current agents are documented personas and deterministic/read-only governance workers where implemented. They are not yet live Claude/LLM agents.

| Agent | Doc | Requirement |
| --- | --- | --- |
| Fontana | `docs/agents/FONTANA.md` | CTO / System Governor; read-only diagnostics; no production authority. |
| Dani Weber | `docs/agents/DANI_WEBER.md` | COO / Operations Governor; read-only process/funnel diagnostics; no autonomous decisions. |
| Edgar Scout | `docs/agents/EDGAR_SCOUT.md` | Official-source signal scout persona; future or limited diagnostic role only unless approved. |
| Form Parser | `docs/agents/FORM_PARSER.md` | Filing/document parser persona; must not invent filing content. |
| Router Analyst | `docs/agents/ROUTER_ANALYST.md` | Situation classifier persona; routing output must remain reviewable. |
| Case Builder | `docs/agents/CASE_BUILDER.md` | ResearchCase builder persona; promotion remains manual. |
| Quality Sentinel | `docs/agents/QUALITY_SENTINEL.md` | Quality and guardrail reviewer persona; must surface risks and unknowns. |
| Playbook Scribe | `docs/agents/PLAYBOOK_SCRIBE.md` | Course and Study Guide mapping persona; must require real chapter references. |

Agent implementation boundaries are defined in `docs/architecture/AGENT_IMPLEMENTATION_MODEL.md`.

## 13. Business Rules / Product Rules

- `SpecialSituation` remains the triage object.
- `ResearchCase` remains the durable deeper research object.
- Watchlist is state/status, not a primary entity.
- Governance is read-only and diagnostic-only for MVP.
- Governance surfaces remain useful support tools, but they are not MVP completion criteria.
- Human approval is required for promotion, conclusions, document-body acquisition where it changes prior assumptions, AI preview execution, AI output persistence, publishing, and implementation of proposals.
- No fake data may be presented as real.
- No unknown mappings may pretend to be useful guidance.
- Candidate evidence is not verified evidence.
- Agent output must not include buy/sell language.
- AI output is assistive context, not final investment advice.
- Scanner, cron, live AI, publishing, and production changes require explicit approval.
- Every CANDIDATE, WATCHLIST, or REJECT decision must include a reason and author once the decision log is implemented.

## 14. Guardrails

`docs/governance/GUARDRAILS.md` is the authoritative guardrail document. Top-level PRD guardrails:

- No auto-trading.
- No investment recommendation language as final advice.
- No buy/sell instructions.
- No auto-publish.
- No auto-discard.
- No autonomous promotion.
- No auto-promotion.
- No autonomous evidence verification.
- No scanner changes without explicit approval.
- No cron changes without explicit approval.
- No cron activation without explicit approval.
- No live AI changes without explicit approval.
- No live AI activation without explicit approval.
- No migrations without explicit approval.
- No auto-persisting AI output without explicit approval.
- No fake data presented as real.
- No secrets exposed in docs, context packs, logs, or UI.
- Missing context must be marked UNKNOWN rather than invented.

## 15. Non-Functional Requirements

- Safety: all automation must be bounded by explicit guardrails and human approval.
- Observability: important runs, diagnostics, health states, and agent activity must be visible.
- Traceability: evidence, sources, decisions, and mappings must be inspectable.
- Maintainability: official docs must keep metadata and changelogs current.
- Explainability: UI should explain what is known, unknown, missing, candidate-only, or read-only.
- Explicit empty states: absence of data must be visible and honest.
- Documentation versioning: official docs are tracked in `docs/DOCUMENT_VERSION_INDEX.md`.
- Human approval: conclusions, promotion, publishing, and operational changes require Dani approval.
- Local-first validation: implementation should be verified locally before deployment.

## 16. Acceptance Criteria for MVP

- SEC EDGAR scheduled detection is code-ready and observable through `DetectionRun`; operational cron activation remains blocked until Dani approves it.
- Dani can triage detected filings through the Research Inbox or equivalent MVP v3 triage workflow.
- Dani can acquire selected SEC document body text under explicit manual action once M1 is implemented and approved.
- Dani can request AI-assisted analysis and 14-section brief previews only after explicit approval; preview output is not final advice.
- Dani can approve, apply, or discard preview sections before persistence.
- Dani can complete the 14-section brief for a real case.
- Dani can record a human decision of CANDIDATE, WATCHLIST, or REJECT with reason and author.
- North Star metrics show decided cases per week and Dani time per case.
- No forbidden automation exists in MVP behavior.
- Governance surfaces, Fontana, Dani Weber, Executive Review, Agent Rooms, Intelligence KPIs, and context packs may support the workflow but do not count as MVP completion criteria.

## 17. Out of Scope / Future Roadmap

- Obsidian Knowledge Vault.
- LLM-assisted Governance Agents.
- MCP read-only integration.
- Scanner-source registry alignment.
- Governance report persistence.
- Deeper ResearchCase workflow.
- Agent Rooms 2.0.
- Intelligence KPIs as a standalone MVP surface.
- Context packs as product acceptance criteria.
- Agent timeline unification.
- Canonical `/investment/governance` route only if approved later.
- Expanded source connectors beyond current approved scope.
- External publishing workflow after manual approval model is complete.

### 17.1 Curated Human Source Registry (planned intake)

Future curated-intake feature: ideas seen in these sources enter the same triage
loop as SEC detections via manual intake (`origin=curated`, with source
attribution). Selection criteria: historical quality of published cases and fit
with the low-institutional-competition strategy. Performance per source must be
measured (cases reaching CANDIDATE) and low-signal sources pruned periodically.

| # | Source | URL | Tier | Description |
| --- | --- | --- | --- | --- |
| 1 | Special Situation Investments | specialsituationinvestments.com | Daily | Tender offers, liquidations, odd lots, going-privates with spread math. Publishes closed-idea track record with returns. Closest match to SwissEdge's target universe. |
| 2 | InsideArbitrage | insidearbitrage.com | Daily | Systematic event-driven coverage: "Merger Arbitrage Mondays" (15+ years uninterrupted), spin-offs, buybacks, tender offers, reverse splits, insider transactions. |
| 3 | Odd Lot Special Situations Newsletter | oddlotspecialsituations.com | Daily | Specialized in odd-lot tenders and reverse splits — structurally closed to institutions; one of the best risk-adjusted niches for individual investors. |
| 4 | Yet Another Value Blog (Andrew Walker) | yetanothervalueblog.com | Weekly | High-quality event-driven write-ups and podcast interviews with special situations managers. Reference for thesis structure. |
| 5 | Clark Street Value | clarkstreetvalue.blogspot.com | Weekly | Micro/nano-cap event-driven: liquidations, REITs in sales processes, asset sales. Historically excellent; reduced posting frequency but active. |
| 6 | Exploring with Alluvial Capital (Dave Waters) | alluvial.substack.com | Weekly | Nano-caps, OTC and forgotten market corners — where institutional competition is absent. |
| 7 | PETITION | petition.substack.com | Weekly | Distressed investing, restructuring and b