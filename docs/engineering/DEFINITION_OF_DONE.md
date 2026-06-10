---
document_id: DEFINITION_OF_DONE
title: Definition Of Done
version: 0.1.0
status: active
owner: Dani
last_updated: 2026-06-08
source_of_truth: true
review_cycle: manual
---

# SwissEdge Definition Of Done

Date: 2026-06-08

## Product Done

- Scope matches the approved prompt.
- User-facing behavior is understandable and safe.
- Empty/partial/mock/unknown states are explicit.
- Guardrails are preserved.

## Backend Done

- Endpoints match documented contracts.
- Data mutations are explicit and approved.
- Errors are safe and useful.
- Agent/run logging is present for agent or AI execution.
- Tests or focused verification cover risky behavior.

## Frontend Done

- Routes render expected states.
- UI distinguishes real, derived, static, partial, empty, and unknown data.
- Navigation matches routing decisions.
- No text implies unsupported automation or investment advice.
- Screenshots can be provided for Claude when UX is part of the task.

## Documentation Done

- Official source-of-truth docs are updated when decisions change.
- Duplicative/outdated docs are linked or archived.
- New docs identify source, scope, and status.
- No secrets or private infrastructure details are included.

## Tests And Verification Done

- Run the smallest meaningful check for the change.
- If tests/build cannot run, document why.
- Claude Code verification is used for material implementation changes.

## Guardrail Done

- No scanner/cron/live-AI changes unless approved.
- No auto-trading, auto-publishing, auto-discard, auto-promotion, or auto-verification.
- No buy/sell language.
- No governance data mutation unless approved.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.1.0 | 2026-06-08 | Codex | Initial official version. |
