Archived: superseded by docs/governance/OPERATING_MODEL.md

# SwissEdge AI Workflow

Date: 2026-06-08

This document defines how Dani, ChatGPT, Claude, Codex, and Claude Code collaborate around SwissEdge.

## Roles

| Role | Responsibility | Inputs | Outputs |
| --- | --- | --- | --- |
| Dani | Product owner and final approval authority | Repo access, screenshots, runtime validation, product intent | Approval decisions, screenshots, real IDs, priority calls, final acceptance |
| ChatGPT | Product architect, PM, governance designer | `docs/context/*`, `docs/governance/*`, Dani direction, Claude/Codex findings | Product decisions, architecture framing, implementation prompts, governance updates |
| Claude | UX engineer without repo access | Screenshots, exact URLs, route notes, task prompt, constraints | UX critique, visual redesign guidance, component-level recommendations |
| Codex | Implementation engineer with repo access | ChatGPT implementation prompt, repo state, governance docs, Claude UX notes | Code/docs changes, verification notes, implementation summary |
| Claude Code | Verification engineer with repo access | Codex diff, acceptance criteria, governance docs, route/API maps | Independent review, bug/risk findings, pass/fail verification |

## Handoff Flow

1. Dani and ChatGPT define the product/governance decision.
2. Dani captures screenshots using `docs/governance/SCREENSHOT_PROTOCOL.md`.
3. ChatGPT turns the decision and screenshots into a Claude UX prompt when UX work is needed.
4. Claude returns UX recommendations based on screenshots and constraints.
5. ChatGPT turns the approved UX/product decision into a Codex implementation prompt.
6. Codex implements only the scoped change, respecting `docs/governance/GUARDRAILS.md`.
7. Claude Code verifies the diff against acceptance criteria.
8. Dani reviews runtime behavior and gives final approval.
9. Decisions and material changes are recorded in docs.

## Screenshots For Claude

Claude does not have repo access. Claude must receive:

- Exact local route URL.
- Screenshot image.
- Whether data is real, partial, mock, empty, or unknown.
- Any real ID context needed for dynamic routes.
- The intended UX task and explicit non-goals.

Use `docs/governance/SCREENSHOT_PROTOCOL.md` as the capture protocol. Never invent IDs for Claude.

## Implementation Prompts For Codex

ChatGPT prompts to Codex should include:

- Goal.
- Exact files or route surfaces likely involved.
- Acceptance criteria.
- Out-of-scope list.
- Guardrails.
- Any Claude UX notes being implemented.
- Verification expectations.

Codex should:

- Inspect before editing.
- Keep changes surgical.
- Avoid scanner, cron, live AI, publication, and autonomous governance changes unless explicitly approved.
- Update documentation when requested.

## Claude Code Verification

Claude Code should verify:

- The implementation matches the prompt.
- No out-of-scope files or behaviors were changed.
- Guardrails remain visible and enforceable.
- Routes and APIs still match current source-of-truth docs.
- Empty states are safe and explicit.
- No investment recommendation, buy/sell wording, auto-discard, auto-publish, scanner, cron, or live-AI change slipped in.

Claude Code should lead with findings, ordered by severity.

## Recording Decisions

Record material decisions in the smallest appropriate place:

- Governance/product baseline: `docs/governance/*`
- Repo-state inventory: `docs/context/*`
- Architecture decisions: `docs/ADR/*`
- Sprint execution notes: `docs/sprints/*`
- Current product state: `docs/PROJECT_STATE.md` or `docs/PROJECT_STATE_LIGHT.md` when explicitly scoped

Do not bury source-of-truth changes only in chat.
