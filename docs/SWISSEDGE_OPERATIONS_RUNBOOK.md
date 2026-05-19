# SwissEdge Operations Runbook

This runbook helps Dani operate the current SEC detection and documentation workflow safely.

The current workflow is:

1. SEC EDGAR detection runs in dry-run mode.
2. DetectionRun records show operational health.
3. Radar Status displays latest detection status.
4. SpecialSituations are reviewed manually.
5. Document Package shows expected and missing documents.
6. Promotion Readiness shows whether manual ResearchCase promotion is ready to review.
7. Dani decides manually whether to create a ResearchCase.

## Daily Check Routine

1. Open Radar Status.
2. Confirm detection status is healthy or understand the warning.
3. Confirm latest run mode is dry-run unless Dani explicitly approved otherwise.
4. Check raw hits, classified filings, duplicates, errors, and runtime.
5. Review any new or noteworthy SpecialSituations.
6. For each interesting SpecialSituation, check Document Package.
7. Check Promotion Readiness.
8. Promote manually only when the source trail is clear enough for durable research.

## Check Cron Dry-Run Logs

Use the deployment environment’s normal log location. The runner should print:

- start timestamp
- enabled or disabled state
- dry-run mode
- hours back
- command result
- end timestamp

Expected dry-run behavior:

- a DetectionRun is written
- `special_situations_created` remains `0`
- no ResearchCase is created
- no evaluator or live AI runs

If logs are empty, check whether cron is installed, enabled, and pointing at the correct generic project directory.

## Check DetectionRun Status

Use the read-only endpoint:

```bash
curl "$API_BASE_URL/api/investment/detection-runs/status"
```

Good signs:

- `status` is `healthy`
- `latest_run` exists
- `dry_run` is `true`
- `errors_count` is `0`
- `special_situations_created` is `0` during dry-run

Warning signs:

- `status` is `no_runs`
- `status` is `stale`
- latest run is `failed`
- latest run remains `running` too long
- errors repeat across runs
- dry-run creates SpecialSituations

## Use Radar Status

Radar Status is the fastest operational check.

Look at:

- latest run timestamp
- status
- mode: disabled, dry-run, or live-create
- hours back
- raw hits
- classified filings
- created SpecialSituations
- duplicates skipped
- errors
- runtime
- forms checked
- latest successful run

If no runs exist, run one manual dry-run after deployment is confirmed.

## Review A New SpecialSituation

Open the SpecialSituation detail page and check:

- company and ticker
- filing type
- situation type
- SEC filing link
- evidence links
- Document Package
- Promotion Readiness
- activity timeline
- manual search suggestions

Do not treat detection as evaluation. Detection only means SwissEdge found a possible event.

## Use Document Package

Start with required documents.

Checklist:

- Are required documents found?
- Are any required documents only suggested?
- Are missing items important enough to block promotion?
- Do manual actions point to SEC, company IR, court, or other sources?
- Are any suggested links still unreviewed?

Remember:

- found does not mean legally verified
- suggested does not mean evidence
- readiness does not mean investment approval

## Use Promotion Readiness

Promotion Readiness answers: is this SpecialSituation ready for Dani to decide whether to create a ResearchCase?

Review:

- readiness level
- score
- blocking reasons
- missing required documents
- supporting evidence
- recommended next manual action

Interpretation:

- `not_ready`: fix source trail first
- `needs_documentation`: complete missing documents first
- `ready_for_manual_promotion`: Dani can review whether to create a ResearchCase

## When To Manually Create A ResearchCase

Create a ResearchCase manually when:

- the situation deserves durable tracking
- the source trail is understandable
- required documents are found or consciously accepted as missing
- Dani wants tasks, documents, source tracking, operational view, or deeper review

Do not create a ResearchCase just because detection found something.

## Check ResearchCase Detail

After manual promotion, review:

- origin and source context
- evidence links
- Document Package
- Operational View
- tasks
- documents
- sources
- activity timeline
- any missing required documents

ResearchCase detail is for structured research operations. It is not automatic approval.

## What Not To Do

- Do not call `POST /api/investment/scan`.
- Do not enable live AI.
- Do not globally activate evaluator v2.
- Do not auto-promote SpecialSituations to ResearchCases.
- Do not auto-discard detections.
- Do not mark documents verified automatically.
- Do not treat DetectionRun health as investment quality.
- Do not treat Document Package readiness as approval.
- Do not treat Promotion Readiness as approval.

## Guardrails

- SEC detection starts safe in dry-run mode.
- DetectionRun APIs are read-only.
- Radar Status is read-only.
- Document Package is deterministic metadata support.
- Promotion Readiness is deterministic workflow support.
- Manual ResearchCase promotion remains Dani’s decision.

## Troubleshooting

### Backend Down

Symptoms:

- UI cannot load API data
- curl returns connection failure
- service status is not active

Actions:

1. Check backend service status using the deployment environment’s normal service command.
2. Review backend logs.
3. Confirm latest deployed files are compatible.
4. Restart backend only after checking logs.

### `detection_status` Returns `000`

`000` usually means curl could not connect.

Actions:

1. Confirm backend service is active.
2. Confirm the API base URL is correct.
3. Check whether the backend process is listening.
4. Check firewall or proxy only if local service checks pass.

### `no_runs`

No DetectionRun rows exist.

Actions:

1. Confirm migration was applied.
2. Run one manual dry-run.
3. Refresh Radar Status.
4. If still `no_runs`, inspect CLI output and backend logs.

### Failed Run

Actions:

1. Open latest DetectionRun detail.
2. Read `error_message`.
3. Check `per_form_summary`.
4. Inspect runner logs.
5. Re-run manually in dry-run mode only after understanding the failure.

### Migration Missing

Symptoms:

- detection endpoints fail
- logs mention missing `detection_runs` table or columns

Actions:

1. Confirm migration file exists in the deployed backend.
2. Run the project’s normal Alembic upgrade workflow.
3. Restart backend.
4. Re-check detection status endpoint.

### Import Error After Deploy

Example symptom:

- router imports a class or service that does not exist on the deployed filesystem

Actions:

1. Confirm the deployed file contains the expected class or function.
2. Confirm all related service files were deployed together.
3. Restart backend.
4. Re-check a stable endpoint and the detection status endpoint.

### Cron Not Writing Logs

Actions:

1. Confirm cron entry points to the generic project directory.
2. Confirm the runner script is executable in the deployment environment.
3. Confirm required environment variables are set for the cron context.
4. Confirm `SWISSEDGE_SEC_EDGAR_ENABLED` is intentionally set.
5. Run the same command manually in dry-run mode.
6. Check whether DetectionRun rows are written.

## Safe Manual Dry-Run

Generic example:

```bash
export SWISSEDGE_SEC_EDGAR_ENABLED=true
export SWISSEDGE_SEC_EDGAR_DRY_RUN=true
export SWISSEDGE_SEC_EDGAR_HOURS_BACK=48
scripts/run_sec_edgar_detection.sh
```

Direct CLI dry-run:

```bash
python -m backend.cli.sec_edgar_detect --hours-back 48
```

Do not use live-create until Dani approves.
