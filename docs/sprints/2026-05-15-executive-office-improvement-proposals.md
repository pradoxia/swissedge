# Sprint AP — Executive Office & Improvement Proposals v1

Date: 2026-05-15

## Purpose

Sprint AP creates the first practical Executive Office layer for SwissEdge. It is deterministic, proposal-only, and approval-based. It does not execute changes autonomously.

The Executive Office gives Dani one place to review process findings, technical interpretation, and improvement proposals before deciding what becomes a future sprint.

## Dani Weber Office — COO

Dani Weber is the COO and human approval authority. The COO focus is process flow, bottlenecks, promotion rate, documentation quality, noise reduction, and source/skill/process improvements.

COO decisions remain manual:

- promote a SpecialSituation to a ResearchCase
- approve or reject proposal status
- approve future implementation work
- approve deployment, cron changes, scanner changes, evaluator changes, and publication gates

## Fontana Office — CTO

Fontana is the CTO-layer deterministic audit surface. Fontana focuses on technology, architecture, product coherence, technical debt, guardrails, and sprint recommendations.

Fontana does not write records, trigger agents, call AI, deploy, change cron, run scanner endpoints, or approve work.

## Bidirectional Feedback Loop

Executive Review combines COO and CTO findings:

- COO finding category
- CTO interpretation
- joint product/process next step
- approval required
- related product area
- guardrail note

This is a review loop, not an execution loop.

## Proposal Types

Improvement Proposals v1 supports these proposal types:

- `ADD_SOURCE`
- `IMPROVE_AGENT_SKILL`
- `IMPROVE_DETECTION_RULE`
- `IMPROVE_DOCUMENTATION_WORKFLOW`
- `SIMPLIFY_UI_SURFACE`
- `ADD_KPI`
- `FIX_BOTTLENECK`
- `DEFER_FEATURE`
- `HIDE_LEGACY_SURFACE`
- `CREATE_SPRINT`

## Approval Model

Proposals are represented as deterministic UI objects and, where available, existing Agent Ops proposal rows. Existing Agent Ops proposal review remains the only write behavior used by this sprint: status and reviewer note updates only.

Proposal status does not apply the proposal. Implementation requires Dani approval in a future scoped sprint.

## Guardrails

- No live AI.
- No `/api/investment/scan`.
- No evaluator v2 global change.
- No scanner/evaluator runtime change.
- No cron or scheduler change.
- No autonomous production change.
- No ResearchCase creation, promotion, evaluation, verification, publication, or discard.
- No source/evidence auto-verification.
- No checklist/resource auto-completion.
- No Marketplace/Sales functional change.
- No public-site implementation.
- No deploy, staging, or commit.
- No secrets, `.env`, credentials, private infrastructure details, DB dumps, raw course transcripts, course audio/video, raw `course_index` content, or copyrighted course text.

## What Remains Manual

- Dani reviews proposals and decides whether to approve, reject, or defer.
- Future implementation requires an explicit sprint.
- Deployment remains manual.
- Evidence review remains manual.
- Publication remains manual.

## Implementation Notes

- Mission Control shows a compact Executive Office section with Dani Weber Office, Fontana Office, Executive Review, and Pending Improvement Proposals.
- Agent Ops shows deterministic Executive Office cards, Executive Review summaries, and Improvement Proposals v1.
- No backend endpoints, services, database migrations, or new write paths were added for AP.
