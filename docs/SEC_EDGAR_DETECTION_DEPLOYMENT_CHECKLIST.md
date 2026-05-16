# SEC EDGAR Detection Deployment Checklist

This checklist prepares SwissEdge SEC EDGAR DetectionRun logging, document packages, and Radar Status visibility for a safe dry-run validation. It does not activate production cron.

## Safety Rules

- Do not call `POST /api/investment/scan`.
- Do not enable live AI or evaluator v2 globally.
- Do not auto-promote `SpecialSituation` records to `ResearchCase`.
- Do not auto-discard detections.
- Do not mark documents or evidence as verified automatically.
- Keep `SWISSEDGE_SEC_EDGAR_ENABLED=false` until Dani approves scheduled execution.
- Keep first scheduled validations in dry-run mode.

## Deployment Order

1. Deploy backend files.
2. Run Alembic migration.
3. Restart the backend service.
4. Deploy frontend files.
5. Verify DetectionRun read-only endpoints.
6. Run one SEC EDGAR dry-run manually.
7. Check Radar Status.
8. Check backend and runner logs.
9. Only later consider enabling cron, after Dani approves.

## Migration

Run the migration in the deployed backend environment using the project’s normal Alembic workflow:

```bash
alembic upgrade head
```

Expected table:

- `detection_runs`

Expected new columns include:

- `raw_hits`
- `parsed_filings`
- `classified_filings`
- `unclassified_filings`
- `duplicates_skipped`
- `special_situations_created`
- `errors_count`
- `forms_checked_json`
- `per_form_summary_json`
- `summary_json`

## Manual Dry-Run

Use placeholders and the deployed environment’s normal shell/session setup. Do not paste secrets or private paths into commands.

```bash
export SWISSEDGE_APP_DIR=/path/to/swissedge
export SWISSEDGE_SEC_EDGAR_ENABLED=true
export SWISSEDGE_SEC_EDGAR_DRY_RUN=true
export SWISSEDGE_SEC_EDGAR_HOURS_BACK=48
scripts/run_sec_edgar_detection.sh
```

Direct CLI usage is also dry-run by default:

```bash
python -m backend.cli.sec_edgar_detect --hours-back 48
```

Live-create mode requires the explicit `--live-create` CLI flag, and should not be used until Dani approves.

Expected behavior:

- The run logs a `DetectionRun`.
- Dry-run does not create `SpecialSituation` rows.
- No `ResearchCase` is auto-created.
- No evaluator or live AI runs.
- 8-K detection remains conservative; weak 8-K signals stay unclassified/review-only.

Do not set `SWISSEDGE_SEC_EDGAR_DRY_RUN=false` or use `--live-create` until Dani approves live-create mode.

## Endpoint Smoke Tests

Use the deployed API base URL placeholder:

```bash
curl "$API_BASE_URL/api/investment/detection-runs/status"
curl "$API_BASE_URL/api/investment/detection-runs/latest"
curl "$API_BASE_URL/api/investment/detection-runs"
```

Expected:

- All endpoints return HTTP 200.
- Endpoints are read-only and do not execute detection.
- Empty state returns cleanly when no detection runs exist.
- Failed latest run returns a warning status, not a 500.
- Running latest run returns a warning status, not a 500.
- Dry-run and live-create runs are visible through `dry_run`.

## UI Smoke Tests

Open the frontend using the normal deployed frontend URL placeholder.

- Radar Status page loads.
- Radar Status shows SEC detection status.
- Radar Status shows a no-runs warning if no `DetectionRun` rows exist.
- Radar Status shows a failed-run warning if the latest run failed.
- Radar Status shows latest successful run when available.
- Radar Status mode language is clear:
  - `disabled` when no run exists and cron defaults are disabled
  - `dry-run` when the latest run was dry-run
  - `live-create` when the latest run was live-create
- SpecialSituation detail page loads Document Package panel.
- ResearchCase detail page loads Document Package panel.
- ResearchCase Operational View includes document readiness fields:
  - `documentation_readiness`
  - `missing_required_count`
  - `missing_recommended_count`
  - `top_missing_documents`
  - `manual_actions_count`

## Guardrail Smoke Tests

Confirm manually:

- No cron entry was added or edited.
- No systemd timer was added or enabled.
- No production deploy command triggered a scan.
- No request was made to `POST /api/investment/scan`.
- No live AI call was made.
- Evaluator v2 was not globally activated.
- No `SpecialSituation` was auto-promoted to `ResearchCase`.
- No detection was auto-discarded.
- No document or evidence item was auto-verified as final truth.

## Cron Consideration Later

Only after Dani approves, a disabled-by-default scheduling example can be adapted from:

```text
scripts/examples/sec_edgar_cron.example
```

Before enabling any schedule:

- confirm migrations are applied
- confirm dry-run writes `DetectionRun` rows
- confirm Radar Status renders cleanly
- confirm logs are readable
- confirm Dani approves live-create or continued dry-run scheduling
