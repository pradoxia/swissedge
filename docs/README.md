---
document_id: DOCS_README
title: SwissEdge Documentation Index
version: 0.1.4
status: active
owner: Dani
last_updated: 2026-06-09
source_of_truth: true
review_cycle: manual
---

# SwissEdge Documentation

Date: 2026-06-09

This directory now has an official reference structure. Use these documents first for product, governance, architecture, engineering, operations, and UX decisions.

The current product direction is MVP v3: the official MVP is the end-to-end research loop from SEC EDGAR filing detection to triage, approved document acquisition, approved AI preview, 14-section brief, and recorded human decision.

## Official Reference Set

### Product

- `docs/product/PRD.md`: what SwissEdge is, what problem it solves, core workflows, users, principles, and non-goals.
- `docs/product/MVP_SCOPE.md`: MVP v3 research-loop scope, out-of-MVP, post-MVP, and future research boundaries.
- `docs/product/ROADMAP.md`: MVP v3 M1-M6 sprint sequence, implemented scheduled detection status, and post-MVP candidates.
- `docs/product/MVP_V3_PROPOSAL.md`: superseded/reference proposal that has been absorbed into the official product docs; not source of truth.

### Governance

- `docs/governance/OPERATING_MODEL.md`: how Dani, ChatGPT, Claude, Codex, and Claude Code collaborate.
- `docs/governance/AI_COLLABORATION_MODEL.md`: AI collaboration workflow, handoffs, context packs, and failure mode.
- `docs/governance/GUARDRAILS.md`: non-negotiable product, production, security, governance, and UX limits.
- `docs/governance/AGENT_MODEL.md`: high-level room and agent index.
- `docs/agents/`: per-agent definitions, permissions, schedules, observability, and failure modes.

### Architecture

- `docs/architecture/SYSTEM_ARCHITECTURE.md`: current frontend/backend/module architecture and system boundaries.
- `docs/architecture/DATA_MODEL.md`: current and proposed domain/entity model.
- `docs/architecture/AGENT_IMPLEMENTATION_MODEL.md`: distinction between agent personas, deterministic governance workers, future LLM-assisted agents, and future Claude-powered agents.

### Engineering

- `docs/engineering/SPRINT_HANDOFF_TEMPLATE.md`: standard future implementation/verification prompt format.
- `docs/engineering/DEFINITION_OF_DONE.md`: done criteria for product, backend, frontend, docs, tests, and guardrails.
- `docs/engineering/API_SPECIFICATION.md`: high-level official API map.

### Operations

- `docs/operations/RUNBOOK.md`: safe daily operations and guarded actions.
- `docs/operations/OBSERVABILITY.md`: logs, metrics, agent activity, health states, execution history, and diagnostics.
- `docs/operations/SCHEDULED_DETECTION.md`: controlled SEC EDGAR scheduled detection, cron activation, statuses, deduplication, and operational guardrails.

### UX

- `docs/ux/SCREENSHOT_MAP.md`: routes Dani should screenshot for Claude UX work.

## Documentation Versioning

- `docs/DOCUMENT_VERSION_INDEX.md`: official document inventory, versions, status, ownership, source-of-truth flag, and purpose.
- Official docs include metadata frontmatter and a changelog.
- Version changes use semantic versioning: major for breaking product/architecture/governance changes, minor for new sections or workflows, and patch for wording or clarifications.

## Context Packs And AI Handoffs

- `scripts/context_delivery/README.md`: how to generate context packs for ChatGPT, Codex, Claude, and Claude Code.
- `CLAUDE.md`: root-level Claude Code instructions for verification work inside the repo.
- Context packs write to `entrega/` and are navigation/context bundles only; they must not include secrets, `.env`, private paths, or archived docs unless explicitly configured.

## Supporting Context

- `docs/context/*`: repo audit, route/endpoint map, feature status matrix, screenshot map, sample URL status, and open architecture questions.
- `docs/ADR/*`: architecture decision records.
- `docs/sprints/*`: historical sprint notes.
- `docs/archive/*`: superseded or conflicting documents retained for reference.

## Source-Of-Truth Rule

If a statement conflicts with the official reference set, prefer the official reference set unless a newer approved sprint explicitly updates it.

Proposal documents are reference material only unless their decisions have been absorbed into the official reference set and version index.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.1.4 | 2026-06-09 | Codex | Updated docs map for MVP v3 direction and clarified MVP_V3_PROPOSAL as superseded/reference material. |
| 0.1.3 | 2026-06-09 | Codex | Added Scheduled Detection operations reference. |
| 0.1.2 | 2026-06-08 | Codex | Added Agent Implementation Model reference. |
| 0.1.1 | 2026-06-08 | Codex | Added AI Collaboration Model reference. |
| 0.1.0 | 2026-06-08 | Codex | Initial official version with versioning and context-pack links. |
