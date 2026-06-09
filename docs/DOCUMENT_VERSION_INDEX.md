---
document_id: DOCUMENT_VERSION_INDEX
title: Document Version Index
version: 0.5.0
status: active
owner: Dani
last_updated: 2026-06-09
source_of_truth: true
review_cycle: manual
---

# SwissEdge Document Version Index

This index lists the official SwissEdge documents, versions, ownership, source-of-truth status, and purpose. Official docs should keep metadata frontmatter and changelogs current.

| Document | Path | Version | Status | Owner | Source of truth | Last updated | Purpose |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SwissEdge Documentation Index | `docs/README.md` | 0.1.4 | active | Dani | true | 2026-06-09 | Top-level documentation map and source-of-truth guide, including MVP v3 direction, scheduled detection operations, and proposal/reference hierarchy. |
| Product Requirements Document | `docs/product/PRD.md` | 0.3.0 | active | Dani | true | 2026-06-09 | Official product requirements and MVP v3 direction: end-to-end research loop, North Star Metric, human approval rules, support surfaces, acceptance criteria, risks, and related docs. |
| MVP Scope | `docs/product/MVP_SCOPE.md` | 0.4.0 | active | Dani | true | 2026-06-09 | MVP v3 in-scope, out-of-MVP, post-MVP, scheduled detection boundary, approval gates, and supporting governance boundaries. |
| Product Roadmap | `docs/product/ROADMAP.md` | 0.5.0 | active | Dani | true | 2026-06-09 | MVP v3 M1-M6 sprint sequence, implemented scheduled detection status, superseded governance-first candidates, and post-MVP roadmap. |
| MVP v3 Proposal | `docs/product/MVP_V3_PROPOSAL.md` | 0.3.0 | superseded_reference | Dani | false | 2026-06-09 | Historical proposal/reference absorbed into official docs; not source of truth when conflicts exist. |
| Operating Model | `docs/governance/OPERATING_MODEL.md` | 0.1.0 | active | Dani | true | 2026-06-08 | Collaboration model, roles, handoffs, decisions, and approvals. |
| AI Collaboration Model | `docs/governance/AI_COLLABORATION_MODEL.md` | 0.1.1 | active | Dani | true | 2026-06-08 | AI roles, workflow, handoffs, context packs, screenshot protocol, and failure mode. |
| Agent Model | `docs/governance/AGENT_MODEL.md` | 0.1.1 | active | Dani | true | 2026-06-08 | High-level room and agent index pointing to per-agent docs. |
| Guardrails | `docs/governance/GUARDRAILS.md` | 0.3.0 | active | Dani | true | 2026-06-09 | Non-negotiable product, production, governance, security, UX, MVP v3 approval gates, and Agent Ops governance limits. |
| System Architecture | `docs/architecture/SYSTEM_ARCHITECTURE.md` | 0.2.0 | active | Dani | true | 2026-06-09 | Current frontend, backend, endpoint, scheduled detection, and system-boundary architecture. |
| Data Model | `docs/architecture/DATA_MODEL.md` | 0.1.0 | active | Dani | true | 2026-06-08 | Current and deferred domain/entity model. |
| Agent Implementation Model | `docs/architecture/AGENT_IMPLEMENTATION_MODEL.md` | 0.1.0 | active | Dani | true | 2026-06-08 | Current deterministic agent implementation model and future LLM-assisted agent path. |
| Sprint Handoff Template | `docs/engineering/SPRINT_HANDOFF_TEMPLATE.md` | 0.1.0 | active | Dani | true | 2026-06-08 | Standard implementation and verification handoff format. |
| Definition Of Done | `docs/engineering/DEFINITION_OF_DONE.md` | 0.1.0 | active | Dani | true | 2026-06-08 | Completion criteria for product, backend, frontend, docs, tests, and guardrails. |
| API Specification | `docs/engineering/API_SPECIFICATION.md` | 0.1.0 | active | Dani | true | 2026-06-08 | High-level official API map. |
| Operations Runbook | `docs/operations/RUNBOOK.md` | 0.2.0 | active | Dani | true | 2026-06-09 | Safe daily operations, scheduled detection checks, and guarded action rules. |
| Observability | `docs/operations/OBSERVABILITY.md` | 0.2.0 | active | Dani | true | 2026-06-08 | Logging, diagnostics, health, activity, execution-history, and Agent Ops governance requirements. |
| Scheduled Detection | `docs/operations/SCHEDULED_DETECTION.md` | 0.1.0 | active | Dani | true | 2026-06-09 | Controlled SEC EDGAR scheduled detection flow, cron activation, statuses, deduplication, observability, and guardrails. |
| Screenshot Map | `docs/ux/SCREENSHOT_MAP.md` | 0.2.1 | active | Dani | true | 2026-06-08 | Routes and screenshot protocol for Claude UX work, including Sprint 1 governance screenshots. |
| Agent Documentation Index | `docs/agents/README.md` | 0.1.1 | active | Dani | true | 2026-06-08 | Index of official per-agent docs, shared guardrails, and current non-LLM runtime status. |
| Fontana Agent | `docs/agents/FONTANA.md` | 0.2.0 | active | Dani | true | 2026-06-08 | CTO / System Governor agent definition and Sprint 1 UI representation. |
| Dani Weber Agent | `docs/agents/DANI_WEBER.md` | 0.2.0 | active | Dani | true | 2026-06-08 | COO / Operations Governor agent definition and Sprint 1 UI representation. |
| Edgar Scout Agent | `docs/agents/EDGAR_SCOUT.md` | 0.1.0 | active | Dani | true | 2026-06-08 | SEC / source signal scout agent definition. |
| Form Parser Agent | `docs/agents/FORM_PARSER.md` | 0.1.0 | active | Dani | true | 2026-06-08 | Filing and document parser agent definition. |
| Router Analyst Agent | `docs/agents/ROUTER_ANALYST.md` | 0.1.0 | active | Dani | true | 2026-06-08 | Situation classifier agent definition. |
| Case Builder Agent | `docs/agents/CASE_BUILDER.md` | 0.1.0 | active | Dani | true | 2026-06-08 | ResearchCase builder agent definition. |
| Quality Sentinel Agent | `docs/agents/QUALITY_SENTINEL.md` | 0.1.0 | active | Dani | true | 2026-06-08 | Quality and guardrail reviewer agent definition. |
| Playbook Scribe Agent | `docs/agents/PLAYBOOK_SCRIBE.md` | 0.1.0 | active | Dani | true | 2026-06-08 | Course and Study Guide mapping agent definition. |
| Claude Code Repository Instructions | `CLAUDE.md` | 0.1.0 | active | Dani | true | 2026-06-08 | Claude Code verification role, guardrails, workflow, and reporting format. |

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.5.0 | 2026-06-09 | Codex | Updated source-of-truth docs for adopted MVP v3 direction and marked MVP_V3_PROPOSAL as superseded reference, not source of truth. |
| 0.4.0 | 2026-06-09 | Codex | Added Scheduled Detection official document and updated Sprint 2 roadmap, architecture, runbook, MVP scope, and docs index versions. |
| 0.3.1 | 2026-06-09 | Codex | Updated PRD version and purpose after full Product Requirements Document rewrite. |
| 0.3.0 | 2026-06-08 | Codex | Added Agent Implementation Model and updated agent/roadmap document versions for the LLM-assisted governance agent future path. |
| 0.2.1 | 2026-06-08 | Codex | Sprint 1 UX polish: governance copy, labels and empty-state clarity for /agent-ops. |
| 0.2.0 | 2026-06-08 | Codex | Updated versions for Sprint 1 governance surface stabilization docs. |
| 0.1.1 | 2026-06-08 | Codex | Added AI Collaboration Model to the official document index. |
| 0.1.0 | 2026-06-08 | Codex | Initial official document version index. |
