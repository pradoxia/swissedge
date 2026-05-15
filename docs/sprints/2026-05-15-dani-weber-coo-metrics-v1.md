# Sprint AV - Dani Weber COO Metrics v1

Date: 2026-05-15

## Purpose

Create a deterministic COO metrics layer for Dani Weber focused on process and funnel bottlenecks in the SwissEdge Investment Platform.

## Role Boundary

Dani Weber is COO / Process Governor. The metrics layer focuses on:

- detection coverage
- promotion rate
- documentation quality
- noise reduction
- process bottlenecks

Dani Weber does not make investment decisions, review individual cases as the primary workflow, auto-apply improvements, or trigger production changes.

## Backend

Added a read-only endpoint:

- `GET /api/investment/executive/dani-weber-metrics`

The endpoint reads existing deterministic metadata only:

- `SpecialSituation` rows
- `evaluation.methodology_workspace.workflow_status`
- `evaluation.methodology_workspace.required_resources`
- `evaluation.methodology_workspace.resource_candidates`
- `evaluation.methodology_workspace.checklist`
- linked `ResearchCase` IDs where present
- `ResearchCase` status metadata

No DB writes, migration, external fetch, AI call, evaluator call, scanner call, scheduler, or cron behavior was added.

## Output

The metrics package includes:

- total SpecialSituation count
- workflow phase distribution
- situation type distribution
- promotion rate to ResearchCase
- documentation blockers
- missing resource frequency
- candidate source coverage
- cases stuck by phase
- low-priority/noise count
- top bottlenecks
- recommended process improvements
- guardrails

Process improvements are proposal-shaped objects with `requires_dani_approval: true` and `auto_apply: false`.

## Frontend

Agent Ops / Executive Office now shows a compact Dani Weber COO metrics snapshot:

- signal count
- promotion rate
- missing required resources
- noise rows
- top COO bottleneck

Executive Review can reference the top COO bottleneck. The UI remains read-only and proposal-only.

## Guardrails

- No autonomous execution.
- No live AI.
- No evaluator or evaluator v2 global change.
- No `/api/investment/scan` call.
- No cron or scheduler changes.
- No automatic ResearchCase creation or promotion.
- No source/evidence auto-verification.
- No checklist/resource auto-completion.
- No investment recommendation language.
- Candidate / Watchlist / Reject remain operational workflow labels, not investment advice.

## What Remains Manual

Dani manually approves process improvements, implementation sprints, deploys, source changes, detection-rule changes, and any proposal status changes.
