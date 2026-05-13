# Sprint AH — Intelligence KPI Dashboard & Fontana Diagnostic Report v1

Date: 2026-05-13

## Summary

Sprint AH adds a read-only Intelligence KPI layer and deterministic Fontana Diagnostic Report v1.

The new platform-level KPI view measures stored preparation state across SpecialSituations, ResearchCases, methodology workspaces, Evidence Links, Documentation Guides, Activity Timeline inputs, Intelligence Score outputs, and Agent Ops tables when available.

## Backend

Added deterministic services:

- `backend/services/investment/intelligence_kpis.py`
- `backend/services/investment/fontana_report.py`

Added read-only endpoints:

- `GET /api/investment/intelligence/kpis`
- `GET /api/investment/intelligence/fontana-report`

The endpoints aggregate existing stored data only. They do not write to the database and do not mutate ORM objects.

## Frontend

Added:

- `/investment/intelligence`
- Mission Control card: `Intelligence KPIs`
- Agent Ops Fontana Diagnostic Report panel

The dashboard uses safe language: preparation quality, documentation quality, manual review readiness, evidence coverage, manual workload, and bottlenecks.

## Guardrails

- Read-only.
- No AI called.
- No evaluator called.
- No scanner called.
- No `/api/investment/scan`.
- No cron changes.
- No scheduler execution.
- No automatic evaluation.
- No automatic ResearchCase creation.
- No automatic promotion.
- No crawling.
- No PDF download.
- No SEC document body fetching.
- No external HTTP calls.
- No investment recommendations.
- No buy/sell/hold language.
- No publishing or public draft creation.
- Manual review remains required.
- No DB migration.
- No deployment performed.

## Tests

Added:

- `backend/tests/test_intelligence_kpis.py`

Coverage includes empty datasets, case counts, Intelligence grade counts, safe documentation aggregation, evidence status counts, Agent Ops indicators, deterministic Fontana findings, language guardrails, network-client import guardrails, and read-only GET endpoint patterns.

## Deployment

Do not deploy after this sprint. ClaudeCode must review before deployment.
