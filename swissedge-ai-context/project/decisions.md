# SwissEdge Decisions

## DEC-001 — AI-Safe Context Architecture

- Status: accepted.
- Context: Assistants need continuity without secrets, private infrastructure, or huge conversations.
- Decision: create `swissedge-ai-context` as curated AI-safe documentation.
- Consequences: prompts can reference a stable safe layer; runtime details remain private.
- Guardrails: no `.env`, keys, tokens, IPs, private URLs, logs with secrets, or raw course material.

## DEC-002 — ResearchCase as Primary Work Object

- Status: accepted.
- Context: The old scanner-first model centered `SpecialSituation`, while real research happens in `ResearchCase`.
- Decision: Investment Platform V2 centers `ResearchCase` instead of `SpecialSituation`.
- Consequences: Research Inbox becomes the main queue; `SpecialSituation` remains useful as a legacy/evaluation signal source.
- Guardrails: no automatic ResearchCase creation from scanners until explicitly approved.

## DEC-003 — Agent Ops Before Autonomy

- Status: accepted.
- Context: Autonomous behavior is risky without observability and review.
- Decision: build diagnostics, reports, and learning proposals before autonomous agent behavior.
- Consequences: agents start as observational or manually triggered.
- Guardrails: no auto-apply, no auto-deploy, no auto-publish, no cron changes.

## DEC-004 — Fontana CTO / Project Governor

- Status: accepted.
- Context: SwissEdge needs project continuity, architectural memory, and governance across iterations.
- Decision: introduce Fontana as observer/advisor/documenter, not autonomous executor.
- Consequences: Fontana can produce reports, identify risks, propose improvements, and maintain roadmap/ADRs.
- Guardrails: Fontana cannot deploy, modify production, change cron, trigger scans, or merge code.

## DEC-005 — No Autonomous Production Changes

- Status: accepted.
- Context: SwissEdge contains private workflows and production-sensitive behavior.
- Decision: all production changes require Dani approval and manual deployment.
- Consequences: Codex prepares, Claude reviews if needed, Dani approves and deploys.
- Guardrails: no background production mutation by any assistant or agent.
