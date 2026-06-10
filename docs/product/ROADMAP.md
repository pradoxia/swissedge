---
document_id: ROADMAP
title: Product Roadmap
version: 0.5.4
status: active
owner: Dani
last_updated: 2026-06-10
source_of_truth: true
review_cycle: manual
---

# SwissEdge Roadmap

Date: 2026-06-10

## Current Direction: MVP v3 Research Loop

The approved MVP direction is now the end-to-end research loop:

`Detect -> Triage -> Acquire Documents -> Analyze Preview -> Brief -> Human Decision`

MVP validation is measured by the North Star Metric: at least 3 cases decided per week with no more than 2 hours of Dani time per case, sustained for 2 consecutive weeks.

Governance surfaces remain useful, but Fontana, Dani Weber, Executive Review, Agent Rooms 2.0, Intelligence KPIs, and context packs are no longer MVP completion criteria.

## Phase 0: Baseline And Governance

- Repo audit and route/API inventory.
- Official documentation structure.
- Guardrails and AI workflow.
- Agent model and observability requirements.
- Screenshot protocol for UX handoffs.

## Phase 1: Governance Surface Stabilization

- Keep governance visible in `/agent-ops`.
- Clarify Executive Office, Fontana, and Dani Weber as read-only.
- Keep guardrail notes always visible.
- Link stuck cases to detail pages when IDs exist.
- Use existing endpoint data and safe empty states.
- Do not add persistence or new routes yet.

Status: implemented as Sprint 1 governance surface stabilization. `/agent-ops` is the current operational governance center for SwissEdge MVP. No new `/governance` route exists.

## Phase 2: Agent Registry And Logs

- Align observability registry with official agent model.
- Add or document missing agent skills, findings, and recommendations.
- Ensure every agent has profile/card requirements.
- Ensure no silent runs.

## Phase 3: Investment Governance Route

- Decide whether `/investment/governance` becomes canonical in the app.
- If approved, implement as read-only and endpoint-driven.
- Link from Mission Control, Campus, and Agent Ops.

## Phase 4: Source And Scanner Reliability

- Resolve Source Registry versus scanner source-of-truth mismatch.
- Improve empty-scan explanations and per-form/source diagnostics.
- Keep scanner/cron changes explicitly approved.

Status: Sprint 2 scheduled SEC EDGAR detection activation is implemented as a controlled cron-safe flow. Manual and scheduled triggers share the scan orchestrator, `DetectionRun` logging is the operational source of truth, and scheduled creation is limited to metadata-only `SpecialSituation` triage candidates. Full source-registry-driven scanner execution remains deferred.

## Implemented Sprint - Scheduled SEC EDGAR Detection Activation

### Goal

Activate controlled scheduled SEC EDGAR detection while keeping scanner behavior observable, deduplicated, and human-reviewed.

### Implemented Scope

- Shared scan orchestrator for manual and scheduled SEC EDGAR scans.
- `POST /api/investment/scan` delegates to the orchestrator with `trigger_type=manual`.
- Cron-safe wrapper `scripts/run_special_situation_scan.py` delegates with `trigger_type=scheduled`.
- `DetectionRun` records logical statuses, counters, trigger type, warnings, errors, dry-run mode, and source metadata.
- SEC EDGAR deduplication prevents duplicate `SpecialSituation` creation.
- `/investment/radar-status` and `/agent-ops` expose scanner status from read-only APIs.

### Guardrails

- No `ResearchCase` creation.
- No promotion, discard, or publishing.
- No live AI, Claude, OpenAI, Anthropic, or MCP.
- No investment recommendations or buy/sell language.
- Cron activation still requires explicit operational approval.

## Phase 5: Governance Persistence

- Decide whether Fontana/Dani reports become persisted report snapshots.
- Add `AgentFinding` and `AgentRecommendation` support if approved.
- Keep recommendations approval-required and non-autonomous.

Current SwissEdge agents are documented personas and deterministic/read-only governance workers. They are not yet live Claude/LLM agents.

## Next MVP v3 Sprints

These sprints supersede the previous governance-first candidate sprint list. They are planned work and do not imply current runtime behavior.

### M1 - SEC Document Acquisition v2: Document Body Text

Status: implemented locally in Sprint M1. Production migration still requires Dani approval.

- Manually triggered SEC body text acquisition for selected `ResearchDocument` rows.
- Acquisition remains bounded to SEC-hosted URLs accepted by the existing SEC URL validation logic.
- Nullable DB fields persist body text, excerpt, hash, acquired timestamp, status, safe error, and size metadata.
- Existing ResearchCase SEC acquisition can store body text for newly acquired SEC document candidates.
- No cron, scanner behavior, promotion, discard, publishing, evaluator v2, brief generation, or live AI activation.

### M2 - Gated AI Analysis / Analyze Case

- Add one explicitly approved manual "Analyze Case" flow.
- Generate preview-only analysis, 14-section brief draft, and quality checklist.
- Require human section-by-section approval before any AI output is persisted.
- Do not enable live AI globally and do not treat AI output as advice.

### M3 - Research Inbox + One-Click Human Decision

- Add a single triage queue for new `SpecialSituation` records and open `ResearchCase` work.
- Status: M3A implements the minimal unified Research Inbox queue and manual next-action links. M3B adds manual `DecisionRecord` persistence for `CANDIDATE`, `WATCHLIST`, `REJECT`, and `NEED_MORE_EVIDENCE`; every decision requires reason and author, remains human-recorded workflow context, and does not auto-promote, reject, discard, archive, publish, analyze, or decide.

### M4 - Price Connector + Estimated Spread Context

Status: M4A implements the local model/service foundation for cached price context and neutral `estimated_spread_pct` display in Research Inbox. Price/spread context is workflow prioritization context only, not advice or a decision signal. Provider selection, production migration, and production price refresh cron remain pending Dani approval.

### M4 - Consolidated Workbench

- Consolidate active case work into Documentos / Analisis-Brief / Decision sections.
- Reuse existing read-only endpoints where possible.
- Reduce panel sprawl without changing backend behavior outside the approved sprint scope.

### M5 - North Star Metrics + MVP Validation

- Show decided cases per week, Dani time per case, and funnel movement from detection to decision.
- Validate at least 3 cases decided per week with no more than 2 hours of Dani time per case for 2 consecutive weeks.
- Keep metrics descriptive; no trading alerts or investment recommendations.

### M6 - Hardening Buffer

- Reserve time for parsing failures, retry behavior, UI polish, documentation cleanup, and real-case edge cases found in M1-M5.
- Keep scope bounded to hardening the MVP v3 loop.

## Post-MVP

- Eval harness / golden set for classification, analysis, and prompt/model regression testing.
- Real LLM pipeline agents after the gated preview workflow is validated.
- More sources after the SEC loop is reliable.
- Publishing workflow after the manual approval model is complete.
- Fontana/Dani Weber LLM-assisted governance after the research loop is producing decided cases.
- Obsidian Knowledge Vault as a navigation layer if still useful.
- Canonical `/investment/governance` route only if approved later.

## Future Sprint - Obsidian Knowledge Vault v1

### Goal

Create an Obsidian-compatible knowledge vault for SwissEdge so Dani can visually navigate the product, architecture, agents, rooms, concepts, sprints, decisions, guardrails, and context packs.

### Purpose

The vault is a navigation and knowledge layer. It must not replace official source-of-truth documentation.

Official source of truth remains:

- `docs/product/PRD.md`
- `docs/product/MVP_SCOPE.md`
- `docs/product/ROADMAP.md`
- `docs/governance/GUARDRAILS.md`
- `docs/governance/OPERATING_MODEL.md`
- `docs/architecture/SYSTEM_ARCHITECTURE.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/agents/*.md`
- `docs/operations/OBSERVABILITY.md`
- `docs/ux/SCREENSHOT_MAP.md`

### Scope

- Create `obsidian/SwissEdge/`.
- Add start page and map notes.
- Add agent notes.
- Add room notes.
- Add concept notes.
- Add sprint and decision notes.
- Add templates.
- Link to official docs.
- Add script to refresh generated vault indexes.
- Keep the vault read-only/manual-first.
- No MCP integration yet.
- No write automation yet.

### Out Of Scope

- Runtime changes.
- Backend changes.
- Frontend changes.
- Scanner changes.
- Cron changes.
- Live AI.
- MCP.
- Autonomous documentation mutation.
- Replacing official docs with vault notes.

### Acceptance Criteria

- Obsidian vault exists as a navigable knowledge layer.
- Official docs are linked, not duplicated.
- Source-of-truth hierarchy remains clear.
- No runtime behavior changes.
- No secrets copied.
- No archived docs copied unless explicitly configured.
- Vault helps Dani, ChatGPT, Claude, Codex, and Claude Code understand SwissEdge faster.

## Future Sprint - LLM-Assisted Governance Agents

### Goal

Introduce optional Claude-assisted reasoning for Fontana and Dani Weber using their agent documents as system prompts and read-only backend context.

### Scope

- Use existing deterministic endpoints as data providers.
- Build a prompt/context layer from `docs/agents/FONTANA.md` and `docs/agents/DANI_WEBER.md`.
- Generate LLM-assisted findings and recommendations.
- Store or display reports safely.
- Keep deterministic fallback.
- Keep human approval mandatory.

### Out Of Scope

- Tooling with write permissions.
- Auto-fix.
- Auto-apply.
- Auto-discard.
- Auto-publish.
- Investment recommendations.
- Buy/sell language.
- Scanner/cron changes.

## Superseded Candidate Sprints

The earlier candidate list prioritized governance stabilization, observability registry work, agent profile cards, source-registry scanner alignment, Obsidian, and LLM-assisted governance. Those items remain valid supporting or post-MVP work, but they are superseded as the next product sequence by M1-M6 above.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.5.4 | 2026-06-10 | Codex | Documented M3B manual DecisionRecord foundation and no-autonomous-decision boundary. |
| 0.5.1 | 2026-06-10 | Codex | Marked M1 SEC Document Acquisition v2 as implemented locally and documented production migration approval boundary. |
| 0.5.0 | 2026-06-09 | Codex | Adopted MVP v3 roadmap with M1-M6 research-loop sprints, North Star validation, and post-MVP governance/agent/source/publishing work. |
| 0.4.0 | 2026-06-09 | Codex | Marked Scheduled SEC EDGAR Detection Activation as implemented and documented remaining scanner reliability guardrails. |
| 0.3.0 | 2026-06-08 | Codex | Added LLM-Assisted Governance Agents as a future sprint candidate and clarified current agents are not live Claude/LLM agents. |
| 0.2.1 | 2026-06-08 | Codex | Sprint 1 UX polish: governance copy, labels and empty-state clarity for /agent-ops. |
| 0.2.0 | 2026-06-08 | Codex | Marked Sprint 1 governance surface stabilization as implemented for `/agent-ops`. |
| 0.1.0 | 2026-06-08 | Codex | Initial official version; includes Obsidian Knowledge Vault v1 as a future sprint candidate. |
