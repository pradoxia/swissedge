# Detection Runs

DetectionRun records are the operational log for SEC EDGAR detection. They answer a simple question: did the detector run, what did it see, and did it stay inside the safety guardrails?

DetectionRun visibility is read-only. Viewing it does not execute detection, call `/api/investment/scan`, call live AI, create ResearchCases, auto-promote, or auto-discard anything.

## What A DetectionRun Is

A `DetectionRun` is one stored record for one SEC EDGAR detection attempt.

It captures:

- when the run started and ended
- whether it was dry-run or live-create
- how many filings were fetched, parsed, classified, skipped, or created
- which SEC forms were checked
- any errors or partial failures
- per-form funnel metrics when available

It is a system-health and audit object, not an investment object.

## When It Is Created

A DetectionRun is created when the SEC EDGAR detection CLI runs:

```bash
python -m backend.cli.sec_edgar_detect --hours-back 48
```

By default, the CLI runs in dry-run mode.

The safe runner script also creates DetectionRun records when enabled:

```bash
scripts/run_sec_edgar_detection.sh
```

The read-only API endpoints do not create DetectionRuns.

## Run Modes

### Manual Dry-Run

Manual dry-run means Dani or an operator intentionally runs detection from the shell in safe mode.

Expected behavior:

- SEC filings may be fetched and classified.
- DetectionRun row is written.
- `SpecialSituation` rows are not created.
- No ResearchCase is created.
- No evaluator or live AI runs.

### Cron Dry-Run

Cron dry-run means a scheduled shell runner executes the same safe workflow.

Expected behavior is the same as manual dry-run, except the trigger is scheduled. Cron should remain dry-run until Dani approves another mode.

### Live-Create

Live-create means detection may create `SpecialSituation` rows for strong, non-duplicate classified filings.

Live-create requires explicit approval and explicit configuration. It still must not create ResearchCases, run live AI, auto-promote, auto-discard, or mark documents verified.

Direct CLI live-create requires:

```bash
python -m backend.cli.sec_edgar_detect --hours-back 48 --live-create
```

## Important Fields

### `raw_hits`

Number of raw SEC hits returned before SwissEdge parsing and filtering.

High raw hits with low classification can be normal during busy filing windows.

### `parsed_filings`

Number of filings that were parsed into the detector’s internal filing shape.

If raw hits are high and parsed filings are zero, inspect detector parsing and SEC response shape.

### `classified_filings`

Number of filings classified as potentially relevant special situations.

Strong forms such as `SC TO-T`, `SC TO-I`, and Form 10 should classify more directly than weak 8-K signals.

### `unclassified_filings`

Number of parsed filings that were not strong enough to classify.

For 8-K, unclassified output is often healthy. It means the detector avoided noisy promotion.

### `duplicates_skipped`

Number of classified filings skipped because SwissEdge already had a matching stored record.

This is expected once detection has been running for a while.

### `special_situations_created`

Number of `SpecialSituation` rows created.

In dry-run mode this should be `0`.

### `errors_count`

Number of errors observed during the detection run.

Non-zero errors should be reviewed, but a partial run may still produce useful metrics.

### `runtime_seconds`

Approximate runtime from start to finish.

Sudden increases may suggest SEC latency, network issues, or detector slowdown.

### `per_form_summary`

Per-form funnel detail when available.

Expected keys may include:

- `raw`
- `parsed`
- `classified`
- `unclassified`
- `duplicates`
- `created`
- `errors`

Use this to see whether one form type, such as 8-K, is creating noise or errors.

## Status Meanings

### `no_runs`

No DetectionRun rows exist yet.

This is normal before the first manual or scheduled dry-run.

### `healthy`

Recent runs exist and the latest run completed without failure signals.

Healthy does not mean the filings are investment-worthy. It only means detection visibility is functioning.

### `warning`

Something needs operator attention.

Common causes:

- latest run failed
- latest run is still running
- recent errors exist
- partial run completed with errors

### `stale`

No recent run has happened within the expected freshness window.

Check whether the runner is disabled, cron is inactive, or logs show execution errors.

### `failed`

The individual DetectionRun failed.

Look at `error_message`, backend logs, and runner logs.

## How To Read Radar Status

Radar Status gives a compact operational view:

- latest run status
- dry-run or live-create mode
- hours back
- raw hits
- classified filings
- created SpecialSituations
- duplicates skipped
- errors
- runtime
- forms checked
- latest successful run

Read it as a system dashboard, not as an investment dashboard.

## Normal Output

Normal dry-run output often looks like:

- latest status is `healthy`
- mode is `dry-run`
- `special_situations_created` is `0`
- errors are `0`
- 8-K has many unclassified filings
- strong forms classify when relevant
- runtime is stable

## Warning Signs

Investigate when:

- status is `no_runs` after a run should have happened
- status is `stale`
- latest run is `failed`
- latest run stays `running` for too long
- dry-run creates SpecialSituations
- `errors_count` is repeatedly non-zero
- `parsed_filings` drops to zero while `raw_hits` is non-zero
- 8-K classification becomes unusually aggressive
- Radar Status cannot load detection status

## Guardrails

- DetectionRun APIs are read-only.
- Do not call `POST /api/investment/scan` for this workflow.
- Dry-run must not create `SpecialSituation` rows.
- Detection does not create `ResearchCase` rows automatically.
- Detection does not call live AI or evaluator v2 globally.
- Detection does not mark evidence or documents verified.
