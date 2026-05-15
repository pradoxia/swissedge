# Sprint AU - SEC Acquisition Deployment QA

Date: 2026-05-15

## Purpose

Provide a manual deployment QA and smoke-test path for SEC EDGAR Document Acquisition v1. This sprint documents verification steps and polishes Mission Control QA guidance; it does not change acquisition behavior.

## Pre-Deploy Checklist

- Confirm local changes have passed validation.
- Confirm no files are staged unless Dani explicitly asks.
- Confirm no deployment has already been run.
- Confirm the private backend deploy script copies the SEC acquisition service file:
  - `backend/services/investment/sec_document_acquisition.py`
- Confirm the frontend build includes the SEC acquisition panel on:
  - `/investment/situations/[id]`
  - `/investment/research/[id]`
  - `/`
- Confirm `.claude/` remains untracked and private deployment files are not committed.

## Local Validation Commands

```powershell
$env:DEBUG='false'
python -m pytest backend/tests/test_sec_document_acquisition.py -v
```

```powershell
Set-Location frontend
npm run build
Set-Location ..
```

```powershell
git diff --check
git status --short
git diff --cached --name-only
```

## Backend Endpoints To Verify

- `GET /api/investment/situations/{id}/sec-document-acquisition-preview`
- `POST /api/investment/situations/{id}/sec-document-acquisition`
- `GET /api/investment/research-cases/{id}/sec-document-acquisition-preview`
- `POST /api/investment/research-cases/{id}/sec-document-acquisition`

## Manual Curl Examples

Use placeholders only. Do not paste private hostnames, IPs, credentials, tokens, `.env` values, or infrastructure details into sprint docs.

```bash
curl "<BASE_URL>/api/investment/situations/<SITUATION_ID>/sec-document-acquisition-preview"
```

```bash
curl -X POST "<BASE_URL>/api/investment/situations/<SITUATION_ID>/sec-document-acquisition"
```

```bash
curl "<BASE_URL>/api/investment/research-cases/<RESEARCH_CASE_ID>/sec-document-acquisition-preview"
```

```bash
curl -X POST "<BASE_URL>/api/investment/research-cases/<RESEARCH_CASE_ID>/sec-document-acquisition"
```

## Expected Safe Behavior

- Preview loads from stored metadata without writes.
- POST runs only after a manual user action.
- Only official SEC URLs are accepted for acquisition.
- Evidence remains unverified until manual review.
- Checklist and resource statuses are not auto-completed.
- ResearchCases are not auto-promoted.
- No evaluator, AI, scanner, `/api/investment/scan`, scheduler, or cron behavior runs.
- Acquired SEC documents are official source candidates, not verified evidence.

## Failure Modes

- `ModuleNotFoundError` can occur after deploy if the private deploy script misses `backend/services/investment/sec_document_acquisition.py`.
- SEC URL is missing, malformed, or non-SEC.
- No documents are discovered from available identifiers.
- Frontend state appears stale after acquisition; reload the case page and verify stored metadata.
- SEC fetch times out; keep behavior conservative and retry manually later.

## Rollback Notes

- Revert frontend panel usage or endpoint calls if the UI path needs to be withdrawn.
- No migration rollback is expected.
- No cron rollback is expected.
- No evaluator, scanner, AI, or scheduler rollback is expected because this sprint does not enable any of them.

## No-Migration Statement

SEC EDGAR Document Acquisition v1 uses existing storage:

- `SpecialSituation.evaluation` JSONB for methodology workspace/resource candidate metadata.
- Existing `ResearchDocument` and `ResearchSource` tables for ResearchCase document/source metadata.

No new database table or migration is required.
