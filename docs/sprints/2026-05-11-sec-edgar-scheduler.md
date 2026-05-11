# SwissEdge Sprint R Closeout — Scheduled SEC EDGAR Intake

## Summary

Sprint R prepares scheduled SEC EDGAR detection using the validated Sprint Q manual detection service.

Detected does not mean evaluated. The scheduler only runs deterministic SEC detection and creates or updates minimal `SpecialSituation` records for human review.

## Scheduler Mechanism

Chosen mechanism: Linux cron template plus a production wrapper script.

Wrapper:

```bash
/opt/swissedge/scripts/run_sec_edgar_detection.sh
```

The wrapper:

- changes directory to `/opt/swissedge`
- activates `.venv`
- loads `/opt/swissedge/.env` without printing values
- runs `python -m backend.cli.sec_edgar_detect --hours-back 168`
- logs start/end timestamps to stdout
- exits non-zero on command failure
- prevents overlapping runs with `flock`, falling back to a lock directory if `flock` is unavailable

## Manual Enablement

After backend deployment and Claude GO, Dani can enable cron manually.

Prepare permissions and log directory:

```bash
cd /opt/swissedge
sudo chmod +x scripts/run_sec_edgar_detection.sh
sudo mkdir -p logs
```

Cron template:

```cron
0 7,19 * * * /opt/swissedge/scripts/run_sec_edgar_detection.sh >> /opt/swissedge/logs/sec_edgar_detection.log 2>&1
```

This runs twice daily at 07:00 UTC and 19:00 UTC with a 168-hour lookback.

## Logs

Recommended log path:

```bash
/opt/swissedge/logs/sec_edgar_detection.log
```

The log contains:

- wrapper start timestamp
- JSON summary from the SEC detection CLI
- wrapper completion timestamp
- failure status if the CLI exits non-zero

The wrapper does not print secrets and does not fetch SEC document bodies.

## Guardrails Confirmed

- No cron entry was installed automatically.
- No `/api/investment/scan` call.
- No live AI.
- No evaluator v2 global enablement.
- No ResearchCase auto-creation.
- No public drafts or publishing.
- No external/non-SEC sources.
- No document body fetching.
- No Alembic migration.
- No Marketplace/Sales changes.

## Deployment Notes

`scripts/deploy_backend_files.ps1` now includes `scripts/run_sec_edgar_detection.sh` in the backend file allowlist and backup loop.

No migration is required.

## Validation After Enablement

After Dani enables cron manually, inspect the latest log:

```bash
tail -n 120 /opt/swissedge/logs/sec_edgar_detection.log
```

Expected behavior:

- each run emits a JSON summary
- repeated findings are deduplicated
- `errors` remains empty
- no evaluator, ResearchCase creation, publishing, or `/scan` behavior appears
