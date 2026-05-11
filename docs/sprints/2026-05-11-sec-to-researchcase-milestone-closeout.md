# SEC EDGAR to ResearchCase Milestone Closeout

Date: 2026-05-11

## What Was Built

SwissEdge now has an operational SEC EDGAR detection-to-research workflow:

1. SEC EDGAR scheduled intake detects P1 special situation signals.
2. Detection creates or updates `SpecialSituation` records.
3. The SpecialSituation Kanban board supports manual workflow movement.
4. Methodology workspaces attach fixed checklist and required-resource snapshots.
5. Resource Scout v1 stores manual resource candidates and search suggestions.
6. Evidence mapping links candidate resources to required resources and checklist items.
7. Dani can manually promote a ready SpecialSituation into an idempotent ResearchCase.

Detected does not mean evaluated. Candidate resources do not mean verified. Evidence found does not mean investment conclusion. ResearchCase promotion does not publish or recommend anything.

## Production Validation Summary

- SEC EDGAR manual detection was validated in production.
- Scheduled SEC EDGAR intake is active through Dani-approved cron.
- SEC lookback/date filtering works.
- Deduplication prevents repeated SpecialSituation creation.
- Historical false detections from the pre-Hotfix-2 validation bug were cleaned through a manual cleanup tool.
- Methodology workspace, Resource Scout, Kanban actions, evidence mapping, and manual ResearchCase promotion were validated through the current production workflow.
- Sprint V hotfix shortened the promotion `brief_version` to `ss_promo_v1`, fitting the existing ResearchCase schema without migration.
- Duplicate promotion is prevented and existing ResearchCases are returned idempotently.

## Current Active Flow

`SEC EDGAR cron -> SpecialSituation -> Kanban -> checklist/resources -> evidence mapping -> manual ResearchCase promotion`

## What Is Still Manual

- Resource Scout v1 is manual.
- Resource review is manual.
- Evidence mapping is manual.
- Kanban workflow movement is manual.
- ResearchCase promotion is manual.
- Evaluation readiness review is manual.
- Any public publication remains manual and separate.

## What Is Not Implemented

- No automatic ResearchCase creation from SEC detection.
- No automatic evaluation.
- No evaluator v2 global enablement.
- No live AI evaluation.
- No buy/sell/hold recommendation generation.
- No public auto-publication.
- No web crawling.
- No PDF download.
- No SEC document body fetching.
- No full Resource Scout web discovery.
- No automatic promotion.
- No ResearchCase evaluation automation yet.

## Guardrails Confirmed

- No `/api/investment/scan` dependency for SEC EDGAR scheduled intake.
- No live AI calls were added for this milestone.
- No evaluator v2 global enablement.
- No automatic ResearchCase creation from detection.
- No public draft creation from detection or promotion.
- No publishing.
- No Marketplace/Sales changes.
- No raw course materials, secrets, private infrastructure details, DB dumps, or production logs should be committed.

## Known Issues / Debt

- The backend deploy script still contains a pre-existing hardcoded deployment target. Do not copy the value into AI-safe docs. Handle this in a separate infrastructure hygiene sprint.
- Existing frontend lint debt remains outside the SEC-to-ResearchCase work.
- Resource Scout v1 does not yet browse the web; it stores known candidates, manual resources, and search suggestions.
- 8-K liquidation/dissolution detection remains metadata-dependent and may miss filings whose liquidation language appears only in document bodies.
- ResearchCase evaluation automation is not implemented.
- Promotion is manual only; no automatic promotion exists.
- No public publication flow is connected to SEC detection or ResearchCase promotion.

## Next Recommended Sprint

ResearchCase Evaluation Preparation / Deep Research Assist.

The next phase should prepare safe ResearchCase readiness packages, missing evidence reports, source quality summaries, and manual evaluation preview design. It should not activate live AI, evaluator v2, automatic recommendations, automatic publication, crawling, PDF downloads, or document body fetching without a separate explicit approval.
