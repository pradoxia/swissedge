# Sprint X-B — ResearchCase Evaluation Preparation / Deep Research Assist

Date: 2026-05-11

## Goal

Prepare promoted ResearchCases for safe, manual evaluation readiness review.

This sprint does not evaluate a case. It gives Dani a deterministic preparation report that shows whether the ResearchCase has enough mapped evidence for a later human-reviewed evaluation step.

## What Was Implemented

- Added read-only backend endpoint:
  - `GET /api/investment/research-cases/{id}/evaluation-prep`
- Added deterministic preparation builder from existing metadata:
  - ResearchCase metadata.
  - `ResearchCase.brief.methodology_workspace_snapshot`.
  - Required resources.
  - Methodology checklist items.
  - ResearchCase documents and sources metadata.
- Added frontend panel on:
  - `/investment/research/[id]`
- The panel shows:
  - readiness level and score.
  - blocking reasons.
  - warnings.
  - missing required resources.
  - checklist gaps.
  - source quality notes.
  - suggested next manual actions.
  - guardrail labels.

## Readiness Levels

- `not_ready`: no methodology snapshot exists, no required resources/checklist exist, or most required resources are missing.
- `needs_more_evidence`: some candidates or evidence exist, but required resources or checklist coverage are still incomplete.
- `ready_for_manual_evaluation`: conservative metadata threshold is met, but the case still requires human review.

## Storage / Persistence

No new persistence was added.

The endpoint derives the package from existing ResearchCase data and returns it read-only. It does not write to the database and does not update status/readiness fields.

## Guardrails Confirmed

- Preparation only.
- No live AI.
- No evaluator v2 global enablement.
- No automatic evaluation.
- No recommendation generation.
- No buy/sell/hold language.
- No public draft creation.
- No publishing.
- No crawling.
- No PDF download.
- No SEC document body fetching.
- No external source calls.
- No `/api/investment/scan`.
- No cron change.
- No automatic ResearchCase creation.

## Limitations

- The readiness package depends on the promoted ResearchCase snapshot. Legacy ResearchCases without `methodology_workspace_snapshot` will show `not_ready`.
- Source quality is metadata-only. It does not inspect linked pages, filings, PDFs, or article bodies.
- Checklist `verified` remains human-controlled. The builder never marks anything verified.
- The score is a conservative deterministic aid, not an investment conclusion.

## Claude Review Recommendation

GO if Claude confirms:

- Endpoint remains read-only.
- No live AI/external calls are introduced.
- Readiness labels do not imply evaluation or recommendation.
- Frontend copy clearly states preparation only.
- Tests cover missing snapshot, missing resources, candidate resources, evidence-found resources, checklist gaps, and forbidden recommendation language.
