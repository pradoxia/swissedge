# SwissEdge Sprint Q Closeout — SEC EDGAR Detection Core

## Summary

Sprint Q implemented the first production-safe SEC EDGAR detection core as a manual path.

Detected means SwissEdge found an official SEC signal, classified it preliminarily with deterministic rules, stored minimal evidence, avoided duplicates, and made it visible for human review as a `SpecialSituation`.

This sprint does not evaluate detected filings, does not create ResearchCases, does not schedule execution, and does not trigger `/api/investment/scan`.

## Existing Scanner State Found

- Existing `POST /api/investment/scan` fetches SEC filings and then calls `evaluate_situation`, which can call live AI.
- Existing `SECEdgarAdapter` already used the SEC full-text search endpoint and returned diagnostics.
- Existing dedupe in `/scan` was filing-URL based only.
- Existing adapter form coverage included forms beyond Sprint Q P1 scope.
- Existing rate limit was approximately 10 requests/second; Sprint Q requires a more conservative one-request-every-5-seconds path.

## What Changed

- Added `backend/services/investment/sec_detection.py`.
- Added `backend/cli/sec_edgar_detect.py`.
- Updated `backend/services/investment/sources/sec_edgar.py` for:
  - P1 form coverage only by default: `SC TO-T`, `SC TO-I`, `Form 10`, `8-K`.
  - Conservative throttle: one request every 5 seconds.
  - Backoff handling for 429, 403, 5xx, and network errors.
  - Correct accession-number parsing from SEC hit metadata.
  - 8-K liquidation/dissolution-only classification in the adapter.
- Updated deterministic routing to recognize `liquidation` and `dissolution` language for 8-K voluntary liquidation detection.
- Documented that manual deployment must include the new service, CLI entrypoint, and updated SEC adapter. No migration is required.

## Supported P1 Signals

- `SC TO-T` -> `merger_arbitrage` / `acquisition_tender_offer`
- `SC TO-I` -> `tender_offer` / `self_tender`
- `Form 10` -> `spin_off` / `standard_spin_off`
- `8-K` with clear liquidation/dissolution language -> `bankruptcy` / `voluntary_liquidation`

Unsupported forms are skipped in the Sprint Q detection core.

## 8-K Limitation

Sprint Q 8-K liquidation/dissolution detection is metadata-dependent. It uses SEC search result metadata fields, not full document body fetching. Therefore recall for liquidation 8-Ks may be incomplete.

This is intentional for Sprint Q to avoid extra document downloads and keep SEC requests conservative. A future sprint may add controlled document-body retrieval only if needed and rate-limited.

## Deduplication

The manual detection core checks for existing `SpecialSituation` records by:

1. Filing URL.
2. Accession number stored in minimal SEC detection evidence.
3. Fallback company name + filing type.

Duplicate candidates are counted in the run summary and are not repeatedly reprocessed.

## Persistence

Sprint Q writes only minimal `SpecialSituation` records:

- `status="detected"`
- official SEC filing metadata
- deterministic detection result
- accession number and CIK when available
- educational/non-advice disclaimer

No ResearchCase is automatically created.

## Manual Run

Dry run:

```bash
python -m backend.cli.sec_edgar_detect --hours-back 36 --dry-run
```

Write detected candidates:

```bash
python -m backend.cli.sec_edgar_detect --hours-back 36
```

Do not schedule this command yet.

## Run Summary

Every run returns JSON with:

- started/completed timestamps
- lookback window
- filings fetched
- filings inspected
- candidates detected
- duplicates skipped
- unsupported forms skipped
- `SpecialSituation` records created
- `SpecialSituation` records updated
- errors
- rate-limit/backoff events
- dry-run flag
- query start/end date
- filings skipped outside the local lookback window
- filings skipped because filing date metadata was missing
- oldest/newest filing date seen in returned SEC metadata
- per-form fetched counts

## Tests Added

- `SC TO-T` classification.
- `SC TO-I` classification.
- `Form 10` classification.
- `8-K` liquidation/dissolution classification.
- Unsupported form skip.
- Duplicate accession skip.
- No ResearchCase auto-creation.
- Rate-limit/backoff summary event extraction.

## Not Implemented

- No cron/scheduler.
- No production `/api/investment/scan` trigger.
- No live AI/evaluator call.
- No evaluator v2 global enablement.
- No ResearchCase auto-promotion.
- No public draft creation.
- No external/non-SEC sources.
- No Agent Ops control plane.
- No Fontana runtime.

## Known Pre-Existing Issue

- `scripts/deploy_backend_files.ps1` contains a hardcoded private deployment target. This predates Sprint Q and was not refactored in this cleanup. Handle it separately in an infrastructure hygiene sprint; do not copy the value into AI-safe context docs.

## Hotfix — SEC Search-Index Parser

Dani's VPS dry run initially returned `filings_fetched=0`, while a manual SEC `search-index` query returned hits. The parser was updated to support SEC search-index hits that expose form types through `_source.root_forms`, accession/document identifiers through `_id`, string-based `_source.display_names`, and alternate filing date fields.

This hotfix keeps Sprint Q scope unchanged: P1 forms only, no document-body fetching, no cron, no `/api/investment/scan`, no live AI, and no ResearchCase auto-creation.

## Hotfix 2 — Lookback Enforcement

Dani's second VPS validation showed that `--hours-back 36` and `--hours-back 168` returned identical counts, and SEC results included historical filings from prior years. Sprint Q now sends SEC search-index date parameters with `dateRange=custom`, `startdt`, `enddt`, `forms`, `from`, and `size`, and also applies a local post-filter before detection.

The parser now treats `_source.file_date`, `_source.filed_at`, and `_source.filed` as filing-date fields, with `_source.period_ending` only as a fallback when no filing date exists. Parsed hits with missing filing dates are skipped by default. Parsed hits before the requested start datetime or after the requested end datetime are skipped as outside the lookback window.

The run summary now reports `query_start_date`, `query_end_date`, `outside_lookback_skipped`, `missing_filing_date_skipped`, `oldest_filing_date_seen`, `newest_filing_date_seen`, and `form_counts`.

Dani's first live VPS validation may have created historical `SpecialSituation` records because of the date-filter bug. Do not delete those records as part of this sprint; review and clean them separately after inspection.

Manual validation after deployment:

```bash
python -m backend.cli.sec_edgar_detect --hours-back 36 --dry-run
python -m backend.cli.sec_edgar_detect --hours-back 168 --dry-run
```

Expected result: counts may differ, very old filings should not be included as candidates, `outside_lookback_skipped` may be greater than zero if SEC returns old results, and `errors` should remain empty.

## Sprint Q.1 — Historical False Detection Cleanup

Sprint Q.1 adds a manual cleanup CLI for historical false `SpecialSituation` records created during validation before Hotfix 2 enforced local lookback filtering. The tool is not automatic and does not run on import, startup, cron, or deploy.

Dry-run first:

```bash
python -m backend.cli.sec_edgar_cleanup_false_detections --dry-run
```

Dry-run is also the default if no mode flag is provided:

```bash
python -m backend.cli.sec_edgar_cleanup_false_detections
```

Delete requires both flags:

```bash
python -m backend.cli.sec_edgar_cleanup_false_detections --delete --confirm DELETE_FALSE_SEC_DETECTIONS
```

The cleanup matches only records satisfying all criteria:

- `SpecialSituation.status = "detected"`
- `evaluation.source = "sec_edgar"`
- `evaluation.detected_only = true`
- `evaluation.sec_detection.filing_date < "2026-05-04"`
- `detected_at` between `2026-05-11T11:30:00Z` and `2026-05-11T11:45:00Z`

The cleanup must not touch manually created situations, evaluated examples, watchlist records, records without `evaluation.sec_detection`, or the validated good run dated `2026-05-04` through `2026-05-08`.

## Sprint R Candidate

Scheduler/read-only observability design for SEC EDGAR detection after Dani validates manual Sprint Q dry runs with correct lookback behavior and Claude gives GO.
