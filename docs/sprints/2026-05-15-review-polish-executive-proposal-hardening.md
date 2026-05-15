# Sprint AT - Review Polish & Executive Proposal Hardening

Date: 2026-05-15

## Purpose

Apply ClaudeCode's non-blocking review polish for Sprints AN+AO+AP and harden the Executive Office proposal mapping without changing backend behavior.

## Changes

- SpecialSituation SEC document acquisition refreshes the situation data after a successful manual acquisition so workspace resource candidates are visible without a page reload.
- Mission Control deployment verification now includes the four SEC document acquisition smoke-check endpoints:
  - `GET /api/investment/situations/{id}/sec-document-acquisition-preview`
  - `POST /api/investment/situations/{id}/sec-document-acquisition`
  - `GET /api/investment/research-cases/{id}/sec-document-acquisition-preview`
  - `POST /api/investment/research-cases/{id}/sec-document-acquisition`
- SEC acquisition tests now include `anthropic` in the banned-token guardrail check.
- Agent Ops maps existing proposals into ImprovementProposalV1 with deterministic keyword inference instead of index alternation.

## Guardrails

- No backend endpoints, backend services, or DB migrations were added.
- No proposal is auto-applied, persisted with new fields, or converted into a Codex task.
- No autonomous execution, scheduler, cron, scanner, evaluator, live AI, deployment, staging, or commit was performed.
- SEC acquisition remains manual-trigger only. Evidence remains unverified until manual review.

## Manual Boundary

Dani still approves implementation, deployment, proposal acceptance, and any future sprint creation. Candidate / Watchlist / Reject remain operational workflow labels, not investment advice.
