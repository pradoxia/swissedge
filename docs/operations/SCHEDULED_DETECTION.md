---
document_id: SCHEDULED_DETECTION
title: Scheduled Detection
version: 0.1.0
status: active
owner: Dani
last_updated: 2026-06-09
source_of_truth: true
review_cycle: manual
---

# SwissEdge Scheduled Detection

Date: 2026-06-09

## Purpose

This document defines the Sprint 2 scheduled SEC EDGAR detection flow. The flow is controlled, observable, and limited to creating `SpecialSituation` triage records from official SEC EDGAR metadata.

## Architecture

Sprint 2 uses option C:

- Shared internal service: `backend/services/investment/scan_orchestrator.py`.
- Manual trigger: `POST /api/investment/scan` calls the orchestrator with `trigger_type=manual`.
- Scheduled trigger: `scripts/run_special_situation_scan.py` calls the orchestrator with `trigger_type=scheduled`.
- Source: `sec_edgar` only.
- Scheduler: VPS cron first. OpenClaw is not the core scheduler in this sprint.

## Manual Scan Flow

1. Dani or an approved operator calls `POST /api/investment/scan`.
2. The endpoint calls `run_special_situation_scan(..., source="sec_edgar", trigger_type="manual")`.
3. The orchestrator starts a `DetectionRun`.
4. The SEC EDGAR detector fetches and classifies supported forms.
5. Deduplication runs before any `SpecialSituation` creation.
6. New eligible situations are stored as triage candidates only.
7. The `DetectionRun` is marked with a logical status and counters.
8. The endpoint returns the scan summary.

## Scheduled Scan Flow

1. VPS cron calls `scripts/run_special_situation_scan.py`.
2. The wrapper loads local environment values without printing secrets.
3. The wrapper obtains a lock file to avoid overlapping runs.
4. The wrapper calls the orchestrator with `trigger_type=scheduled`.
5. The orchestrator records every run, including zero-result and failed scans.
6. The wrapper prints a compact JSON summary and exits with a useful code.

Exit codes:

- `0`: `success_with_results` or `success_empty`.
- `1`: failed status.
- `2`: `partial_success`.

## Cron Schedule

Approved intended schedule:

- Monday to Friday.
- 08:00, 14:00, 20:00 Europe/Zurich time.

If the VPS timezone is Europe/Zurich:

```cron
# REQUIRES Dani approval before activating
0 8,14,20 * * 1-5 cd /path/to/swissedge && /path/to/venv/bin/python scripts/run_special_situation_scan.py --source sec_edgar --trigger scheduled --live-create >> logs/special_situation_scan.log 2>&1
```

Use safe local paths only. Do not put secrets in the crontab.

If the VPS timezone is UTC, confirm daylight-saving implications before installing the cron. Prefer setting the server timezone to Europe/Zurich or using a systemd timer with timezone support.

## Activation And Disable

The wrapper is disabled unless one of these is true:

- `SWISSEDGE_SCHEDULED_SCAN_ENABLED=true` is present in the local environment.
- The wrapper is called with `--enable`.

To disable scheduled detection:

- Remove or comment the cron entry, or
- Set `SWISSEDGE_SCHEDULED_SCAN_ENABLED=false`.

Do not disable by editing application code.

## DetectionRun Statuses

Logical statuses:

- `success_with_results`: scan completed and created at least one new `SpecialSituation`.
- `success_empty`: scan completed but created no new situations.
- `partial_success`: scan produced usable data but also warnings/errors.
- `failed_source_error`: SEC EDGAR fetch/source failure prevented useful results.
- `failed_config_error`: required configuration, such as `SEC_USER_AGENT`, is missing.
- `failed_database_error`: database write/update failed.
- `failed_unknown`: unexpected failure.

Each `DetectionRun` stores counters and metadata in existing fields and `summary_json`; no Sprint 2 migration is required.

## Deduplication Strategy

Before creating a `SpecialSituation`, the detector checks strongest available identifiers:

- Filing URL.
- Accession number in `evaluation.sec_detection`.
- Company plus filing type as a fallback.
- Batch-level duplicate keys for repeated filings in the same scan.

Duplicate-only runs must still produce a `DetectionRun` with `duplicates_skipped` and no fabricated results.

## Allowed Scheduled Action

The scheduled scan may create new `SpecialSituation` records with metadata-only SEC EDGAR evidence and manual-review status.

## Forbidden Scheduled Actions

The scheduled scan must not:

- Create `ResearchCase` records.
- Promote cases.
- Discard cases.
- Publish content.
- Run live AI.
- Call Claude, OpenAI, Anthropic, or MCP.
- Create investment recommendations.
- Use buy/sell language.
- Deploy or mutate production settings.

## Observability

Status is visible through:

- `/investment/radar-status`.
- `/agent-ops`.
- `GET /api/investment/detection-runs/status`.
- `GET /api/investment/detection-runs/latest`.
- `GET /api/investment/detection-runs`.

Mission Control may link or summarize scanner status but is not the source of truth.

## Troubleshooting

Missing `SEC_USER_AGENT`:

- Expected status: `failed_config_error`.
- Fix: configure a safe SEC user agent in the runtime environment.
- Do not print the value in logs.

Database errors:

- Expected status may be `failed_database_error`, or the run may fail before it can be recorded if the database is unreachable.
- Check Postgres connectivity, migrations, and `DATABASE_URL`.

SEC HTTP errors or rate limits:

- Check warnings, `rate_limit_backoff_events`, and source diagnostics.
- Do not retry aggressively.

Duplicate-only runs:

- Expected status: usually `success_empty`.
- Check `duplicates_skipped`.
- No new `SpecialSituation` should be created.

Zero-result runs:

- Expected status: `success_empty`.
- Confirm forms checked and raw hits.

Cron not running:

- Confirm crontab entry, server timezone, executable paths, virtualenv path, and log path.
- Confirm `SWISSEDGE_SCHEDULED_SCAN_ENABLED=true`.

Venv/env loading issue:

- Confirm the cron command runs from the repository root.
- Confirm the virtualenv path exists.
- Confirm `.env` is readable by the cron user.

## Verification Without Real Production Scan

Safe checks:

```bash
python scripts/run_special_situation_scan.py --help
python -m py_compile backend/services/investment/scan_orchestrator.py scripts/run_special_situation_scan.py
```

Do not run the wrapper in live-create mode against production unless Dani explicitly approves cron activation.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.1.0 | 2026-06-09 | Codex | Initial scheduled SEC EDGAR detection operations guide. |
