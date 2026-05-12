# Sprint Z — Intelligence Scoring Foundation & Research Quality Layer

Date: 2026-05-12

## Goal

Add a deterministic, read-only IA Score for ResearchCases to measure the quality, safety, and usefulness of the current preparation state.

## Implemented

- Added backend scoring service:
  - `backend/services/investment/intelligence_score.py`
- Added read-only endpoint:
  - `GET /api/investment/research-cases/{id}/intelligence-score`
- Added frontend API types and fetch helper:
  - `fetchResearchCaseIntelligenceScore(id)`
- Added ResearchCase UI card:
  - `frontend/app/components/IntelligenceScoreCard.tsx`
  - Integrated into `/investment/research/[id]`
- Added documentation:
  - `docs/intelligence_scoring.md`
- Added backend tests:
  - complete case scores `APPROVABLE`.
  - incomplete case scores `REVIEW_PIPELINE`.
  - directive investment language lowers risk discipline.
  - output avoids buy/sell/hold language.
  - service imports no network clients.
  - endpoint returns the score package through GET.

## Score Model

- Detection Score: 0-40.
- Structuring Score: 0-40.
- Risk Discipline Score: 0-20.

Grades:

- `APPROVABLE`: 90-100.
- `USEFUL_INCOMPLETE`: 70-89.
- `REVIEW_PIPELINE`: below 70.

`APPROVABLE` is explicitly labeled as structural approval for manual review only. It is not investment approval.

## Safety

This sprint is read-only and deterministic:

- No DB writes.
- No migration.
- No cron changes.
- No `/api/investment/scan`.
- No live AI.
- No external HTTP calls.
- No evaluator v2 activation.
- No automatic evaluation.
- No ResearchCase auto-creation.
- No trading decisions or investment recommendations.
- No publishing or public draft creation.
- No crawling, PDF download, or SEC document body fetching.

## Verification

Commands run:

```powershell
$env:DEBUG='false'; python -m pytest backend/tests/test_intelligence_score.py backend/tests/test_evaluation_prep.py backend/tests/test_evidence_links.py
npm run build
```

Results:

- Backend targeted tests: 20 passed.
- Frontend build: passed.
