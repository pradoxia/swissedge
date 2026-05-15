# Sprint AX - ResearchCase Operational View v1

## Purpose

Sprint AX adds deterministic Operational View preparation for ResearchCases. The view translates stored product metadata into a workflow label for manual review:

- Candidate
- Watchlist
- Reject
- Insufficient Information

This is a SwissEdge product workflow surface only. It is not investment advice, does not imply any private action, and does not write private decisions back into the product.

## Endpoint

- `GET /api/investment/research-cases/{id}/operational-view`

The endpoint is read-only and deterministic. It reads ResearchCase metadata, evaluation preparation, intelligence score, evidence links, completion workbench data, SEC acquisition metadata, and historical analogue context.

## Rules

Candidate requires adequate stored documentation, enough source coverage, no critical missing official resources, adequate completion and intelligence scores, clean risk-discipline checks, and either SEC metadata or historical analogue support.

Watchlist is used when the case has a useful workflow signal but still needs event, document, timing, spread, vote, regulatory, approval, or catalyst clarity.

Reject is used when stored metadata indicates weak evidence, unsupported situation context, stale or expired events, excessive noise, or archived/not-actionable workflow state.

Insufficient Information is used when stored metadata is not enough to choose a workflow label safely.

## Frontend

ResearchCase detail pages now show a compact Operational View card with:

- workflow label
- confidence
- rationale
- blockers
- what would change the view
- next manual actions
- guardrail reminder

The card does not apply any status change automatically.

## Guardrails

- No live AI
- No evaluator
- No `/api/investment/scan`
- No cron or scheduler
- No DB writes
- No auto-promotion
- No source or evidence auto-verification
- No checklist/resource auto-completion
- No public publishing
- Dani makes the final manual decision

## Deploy Note

Because this sprint adds `backend/services/investment/operational_view.py`, Dani must update the private backend deploy allowlist locally before deploying the backend.
