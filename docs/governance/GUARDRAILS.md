---
document_id: GUARDRAILS
title: Guardrails
version: 0.3.0
status: active
owner: Dani
last_updated: 2026-06-08
source_of_truth: true
review_cycle: manual
---

# SwissEdge Guardrails

Date: 2026-06-09

These are non-negotiable limits for SwissEdge product, engineering, governance, and agent work.

## Investment Guardrails

- No auto-trading.
- No investment recommendations as final user advice.
- No buy/sell language in agent outputs.
- No valuation conclusion from governance agents.
- Human review is required for candidate promotion and conclusions.
- Evidence must remain clearly marked until manually verified.

## Production Guardrails

- No autonomous production changes.
- Do not trigger `/api/investment/scan` unless explicitly approved.
- Do not change cron without approval.
- Do not install cron without approval.
- Do not operationally activate scheduled detection cron without Dani approval.
- Do not enable evaluator v2 globally without explicit approval.
- Do not make evaluator v2 the default manual flow without explicit Dani approval.
- Do not enable live AI globally without explicit approval.
- Do not activate live AI for case analysis without explicit Dani approval.
- Do not run migrations without explicit approval.
- Do not add or run a DB migration for `body_text`, decision logs, price snapshots, or related MVP v3 model changes without explicit Dani approval.
- Do not change scanner behavior unless explicitly scoped and approved.
- Do not download SEC document bodies if that changes prior metadata-only assumptions unless Dani explicitly approves the change.
- Do not persist AI output unless Dani explicitly approves the persistence behavior.

## Governance Guardrails

- Fontana is diagnostic-only/read-only for now.
- Dani Weber is diagnostic-only/read-only for now.
- `/agent-ops` is the current MVP governance surface.
- Guardrail notes must remain visible on governance panels.
- Executive Review is a read-only governance summary, not an investment recommendation, case approval, or rejection.
- Governance proposals require human approval before implementation.
- No data mutation from governance agents.
- No auto-fix.
- No auto-apply.
- No auto-promotion.
- No auto-discard.
- No auto-publishing.
- No autonomous recommendations becoming tasks without approval.
- Fontana, Dani Weber, Executive Review, Agent Rooms, Intelligence KPIs, and context packs are supporting tools, not MVP completion criteria.

## Security Guardrails

- Do not expose secrets.
- Do not expose `.env`.
- Do not expose deployment targets.
- Do not expose server paths.
- Do not expose private credentials.
- Do not copy private infrastructure details into AI-safe docs.

## Source-Of-Truth Guardrails

- Do not treat static frontend status labels as backend truth.
- Do not treat Mission Control as backend truth.
- Do not treat Campus visual config as operational truth.
- Do not treat Source Registry as scanner source of truth until scanner wiring is fixed.
- Do not treat mocked tests, fixture IDs, or example companies as real data.
- Do not treat derived timelines as persisted audit logs.

## UX Guardrails

- Never invent IDs.
- Mark empty, mock, partial, visual, static, and unknown data clearly.
- Desktop screenshots first.
- Claude works from screenshots and prompts, not repo access.
- Study Guide mapping rule: the UI must not show default issuer tender study topics for unmapped or unknown cases. Study Priority cards require real chapter references. If no chapter reference is mapped, the UI must show an explicit empty state such as `No chapter reference mapped yet`.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.3.0 | 2026-06-09 | Codex | Added MVP v3 approval gates for SEC document body acquisition, migrations, live AI, evaluator defaulting, AI output persistence, and governance-as-support boundaries. |
| 0.2.0 | 2026-06-08 | Codex | Added Sprint 1 governance surface guardrails for `/agent-ops`. |
| 0.1.0 | 2026-06-08 | Codex | Initial official version; documents the Study Guide chapter-reference guardrail. |
