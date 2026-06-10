---
document_id: OPERATING_MODEL
title: Operating Model
version: 0.1.0
status: active
owner: Dani
last_updated: 2026-06-08
source_of_truth: true
review_cycle: manual
---

# SwissEdge Operating Model

Date: 2026-06-08

## Collaboration Model

SwissEdge uses a human-led AI workflow. Dani owns product decisions and final approval. AI assistants support architecture, UX, implementation, and verification inside strict guardrails.

## Roles

| Role | Responsibility | Inputs | Outputs |
| --- | --- | --- | --- |
| Dani | Product owner and final approval authority | Repo state, runtime app, screenshots, user intent | Approval, priorities, real IDs, screenshots, acceptance |
| ChatGPT | Product architect, PM, governance designer | Official docs, repo audits, Dani direction, Claude/Codex findings | Product decisions, scoped prompts, governance docs |
| Claude | UX engineer without repo access | Screenshots, route notes, constraints, prompts | UX critique and design recommendations |
| Codex | Implementation engineer with repo access | Scoped implementation prompt, repo files, official docs | Code/docs changes, verification notes, implementation report |
| Claude Code | Verification engineer with repo access | Codex diff, acceptance criteria, official docs | Independent review, risk findings, pass/fail verification |

## Handoff Rules

- ChatGPT defines scope before implementation.
- Dani provides screenshots for Claude using `docs/ux/SCREENSHOT_MAP.md`.
- Claude gives UX recommendations from screenshots only.
- Codex implements scoped changes in repo.
- Claude Code verifies against acceptance criteria and guardrails.
- Dani gives final approval.

## Decision Recording

- Product definition: `docs/product/PRD.md`
- MVP boundaries: `docs/product/MVP_SCOPE.md`
- Roadmap: `docs/product/ROADMAP.md`
- Guardrails: `docs/governance/GUARDRAILS.md`
- Agent model: `docs/governance/AGENT_MODEL.md`
- Architecture: `docs/architecture/SYSTEM_ARCHITECTURE.md`
- Data model: `docs/architecture/DATA_MODEL.md`
- Observability: `docs/operations/OBSERVABILITY.md`
- UX screenshots: `docs/ux/SCREENSHOT_MAP.md`

## Approval Rules

Explicit Dani approval is required for:

- Scanner behavior changes.
- Cron changes or cron installation.
- Live AI global rollout.
- Migrations.
- Publishing.
- Governance data mutation.
- Autonomous agent behavior.
- Any production-changing action.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.1.0 | 2026-06-08 | Codex | Initial official version. |
