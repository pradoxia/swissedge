---
document_id: RUNBOOK
title: Operations Runbook
version: 0.4.8
status: active
owner: Dani
last_updated: 2026-06-10
source_of_truth: true
review_cycle: manual
---

# SwissEdge Operations Runbook

Date: 2026-06-10

## Daily Review

- Open Mission Control: `/`
- Open Agent Ops: `/agent-ops`
- Open Radar Status: `/investment/radar-status`
- Open Situations: `/investment/situations`
- Open Research Inbox: `/investment/research-inbox`
- Review Intelligence KPIs: `/investment/intelligence`

## Guarded Actions

Do not run guarded actions unless explicitly approved:

- Trigger `/api/investment/scan`.
- Change or install cron.
- Enable live AI globally.
- Run migrations.
- Publish externally.
- Mutate governance data.
- Acquire SEC document body text outside the manual SEC-only acquisition flow.

## Runtime Validation

Use the frontend and read-only APIs first:

- `GET /api/health/full`
- `GET /api/investment/detection-runs/status`
- `GET /api/observability/agents`
- `GET /api/observability/mission-control`
- `GET /api/agent-ops/rooms`

## Manual SEC Document Body Acquisition

M1 adds manual SEC body acquisition for `ResearchDocument` rows created from SEC document candidates.

Operational rules:

- Body text acquisition is manual only.
- Body text acquisition is SEC-only and uses the existing SEC URL validation boundary.
- Body text acquisition must not crawl arbitrary external links.
- Body text acquisition must not trigger scans, cron, live AI, evaluator v2, brief generation, promotion, rejection, publishing, or evidence verification.
- Body text is stored on `ResearchDocument` only after URL validation passes.
- Production migration for `research_documents.body_text*` fields requires Dani approval before deployment.
- Full document body text must not be logged.

Safe statuses:

- `requested`
- `acquired`
- `skipped_invalid_url`
- `skipped_too_large`
- `failed_fetch`
- `failed_parse`
- `failed_persist`

Manual endpoints:

- `POST /api/investment/research-cases/{research_case_id}/sec-document-acquisition` acquires SEC metadata candidates and attempts body text for newly stored `ResearchDocument` rows.
- `POST /api/investment/research-documents/{document_id}/body-text-acquisition` retries body acquisition for one existing `ResearchDocument`.

## AI Client Hardening

M2-pre prepares AI infrastructure for gated Analyze Case preview work, but does not enable live AI.

Operational rules:

- `ai_live_enabled` defaults to `false`.
- Live AI provider calls require explicit Dani approval and environment configuration.
- Structured AI output must fail explicitly when JSON parsing or schema validation fails.
- Retries are limited to safe transient failures such as timeout, 429, or 5xx.
- Daily budget caps are conservative and block calls when configured limits are reached.
- AI output must not be persisted or shown as investment analysis unless a later approved sprint explicitly gates and scopes that behavior.

M2A adds the backend preview contract at `POST /api/investment/research-cases/{research_case_id}/analyze-preview`.

Operational rules:

- The endpoint is manual only.
- If live AI is disabled, the endpoint returns a controlled unavailable response.
- If required document body text is missing, the endpoint returns `blocked_missing_documents` and does not call an AI provider.
- Preview output is not persisted and must not mutate ResearchCase status, readiness, decisions, documents, sources, tasks, or publication state.
- Analyze Case preview does not activate evaluator v2, scanner changes, cron, auto-promotion, auto-discard, auto-publish, or investment directive language.

M2B adds observability for every manual Analyze Case preview attempt.

Operational rules:

- Disabled, blocked, budget-exceeded, parse-error, validation-error, and successful preview attempts must create a safe run record.
- Run summaries must include metadata and outcome status only, never prompt text or full document body text.
- AI usage is logged only when a provider call actually occurs and usage metadata exists.
- Daily budget checks use logged `AiUsage.estimated_cost` as an operational estimate, not billing-grade cost accounting.

## Scheduled SEC EDGAR Detection

Scheduled detection is documented in `docs/operations/SCHEDULED_DETECTION.md`.

Operational rules:

- The manual endpoint `POST /api/investment/scan` and the scheduled wrapper both use the shared scan orchestrator.
- Scheduled detection is disabled unless `SWISSEDGE_SCHEDULED_SCAN_ENABLED=true` or the wrapper is called with `--enable`.
- The intended cron schedule is Monday-Friday at 08:00, 14:00, and 20:00 Europe/Zurich.
- Every attempt must create or update a `DetectionRun` when the database is reachable.
- Missing `SEC_USER_AGENT` must be reported as `failed_config_error` without printing the value.
- Scheduled detection may create metadata-only `SpecialSituation` triage records after deduplication.
- Scheduled detection must not create `ResearchCase` records, promote, discard, publish, run live AI, or emit investment recommendations.

Safe checks:

```bash
python scripts/run_special_situation_scan.py --help
python -m py_compile backend/services/investment/scan_orchestrator.py scripts/run_special_situation_scan.py
```

## Research Inbox

M3A adds a minimal manual Research Inbox foundation.

Operational rules:

- `GET /api/investment/research-inbox` is read-only and combines detected `SpecialSituation` rows with open `ResearchCase` rows.
- Candidate-only items must remain labeled as candidate-only and unverified.
- The inbox may link to existing manual promotion and detail routes, but must not auto-promote, reject, discard, archive, publish, run AI, or make decisions.
- M3B adds manual `DecisionRecord` creation from Research Inbox for `CANDIDATE`, `WATCHLIST`, `REJECT`, and `NEED_MORE_EVIDENCE`.
- Every decision requires reason and author.
- Decisions are human-recorded workflow/audit context only; `NEED_MORE_EVIDENCE` is workflow context, not a recommendation.
- Decision recording does not auto-promote, reject, discard, archive, publish, analyze, decide, verify evidence, acquire documents, or hide queue items.
- Migration file created but not applied; production migration requires Dani approval.
- No cron, scanner, deploy, live AI, evaluator v2, or provider LLM behavior changes are included.

M4C adds manual curated source intake from Research Inbox.

Operational rules:

- Curated intake creates `SpecialSituation` triage candidates only.
- Curated intake is candidate-only and unverified.
- Curated intake records source attribution for later per-source yield metrics, deferred to M6.
- Curated intake does not scrape, crawl, poll RSS, fetch URL bodies, promote, reject, discard, archive, publish, analyze, create ResearchCases, create DecisionRecords, create price context, acquire documents, or trigger scanners.
- M4C uses existing `SpecialSituation` fields and `evaluation` metadata; no migration is required.
- No production deployment, VPS change, production migration, source scraping cron, price cron, SEC cron, scanner change, live AI, or provider integration is approved in M4C.

## ResearchCase Workbench

M5 consolidates `/investment/research/{id}` into a daily case workbench.

Operational rules:

- The workbench is organized as Documents, Analysis / Brief, and Decision.
- It reuses existing manual controls for document metadata, SEC-only body text acquisition, preview-only analysis, brief editing, decision recording, and manual price context.
- Analyze Preview remains gated, preview-only, observable, and not persisted by the workbench.
- Decision and price context actions remain human-triggered and reason/source based.
- The workbench must not change scanner behavior, cron, migrations, production state, live AI settings, provider settings, publishing state, or case workflow automatically.

## Price Context

M4A adds local price/spread context foundations for triage prioritization only. M4B adds manual Research Inbox price-context editing.

Operational rules:

- `estimated_spread_pct` is workflow context, not investment advice or a case decision.
- Price refresh is decoupled from SEC detection cron.
- No production price refresh cron is installed in M4A.
- No SEC cron or scanner behavior changed in M4A.
- The price context migration file is a local code artifact only; it has not been applied.
- Production migration requires Dani approval.
- Price context must not auto-promote, reject, discard, publish, analyze, or decide any case.
- Manual price context may record ticker, offer price, offer price source, latest close, currency, status, and status reason.
- Manual price context does not call a market-data provider, live AI, evaluator v2, scanner, SEC cron, or price cron.
- M4B uses existing M4A tables; no new migration is required.
- No production deployment, VPS change, production migration, provider integration, or price cron is approved in M4B.

## Incident Notes

For scanner, cron, live AI, or production incidents:

- Record what happened.
- Record what was checked.
- Record affected routes/endpoints.
- Record whether data was mutated.
- Do not apply fixes without Dani approval.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.4.8 | 2026-06-11 | Codex | Added M5 ResearchCase workbench operating rules and no-automation boundary. |
| 0.4.7 | 2026-06-10 | Codex | Added M4C manual curated source intake rules and no-scraping/no-automation boundary. |
| 0.4.6 | 2026-06-10 | Codex | Added M4B manual price context activation rules and no-provider/no-cron boundary. |
| 0.4.5 | 2026-06-10 | Codex | Added M3B manual DecisionRecord operating rules and production migration approval boundary. |
| 0.4.0 | 2026-06-10 | Codex | Added M2-pre AI client hardening note: live AI remains disabled by default, structured output failures are explicit, retries are bounded, and budget caps are conservative. |
| 0.3.0 | 2026-06-10 | Codex | Added M1 manual SEC document body acquisition operating rules, safe statuses, endpoints, and production migration approval note. |
| 0.2.0 | 2026-06-09 | Codex | Added scheduled SEC EDGAR detection operating rules and safe validation commands. |
| 0.1.0 | 2026-06-08 | Codex | Initial official version. |
