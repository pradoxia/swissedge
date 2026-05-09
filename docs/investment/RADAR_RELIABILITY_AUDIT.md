# SwissEdge Investment Radar Reliability Audit

Date: 2026-05-08

Scope: private Investment Radar reliability only. No scan was triggered, no live AI call was made, and no production operation was changed.

## 1. Executive Summary

Status: partially operational, but currently unreliable as a discovery system.

The implemented radar can run a SEC EDGAR scan, parse filings into `Filing` objects, evaluate classified filings with the production evaluator, and create `special_situations` rows visible in the Evaluations queue. The pipeline is therefore not blocked end to end.

The main reliability problem is earlier in the funnel: coverage is narrow and observability is too coarse. The scanner uses one hardcoded adapter, `SECEdgarAdapter`, not the `investment_sources` table. It searches a fixed list of SEC forms and drops unclassified filings silently. Empty scans are recorded as successful runs, but the current logs do not preserve enough funnel counts to explain why zero rows were created.

Most likely answer for Dani: the radar is running, but it may be finding few opportunities because the scan is limited to one source, fixed SEC form queries, metadata-only classification, a short default time window, per-form result limits, duplicate filtering, and silent drops for filings whose `situation_type` is missing.

## 2. Current Detection Pipeline

Actual implemented path:

1. Trigger: `POST /api/investment/scan`, implemented in `backend/api/investment/router.py`.
2. Run logging starts with `agent_name="investment_scanner"` and input summary `Scanning SEC EDGAR for filings in last {hours_back}h`.
3. The endpoint calls `_sec.search_recent(hours_back=hours_back)`, where `_sec = SECEdgarAdapter()`.
4. `SECEdgarAdapter.search_recent()` loops over a hardcoded `FILING_TYPES` list.
5. For each form, `_query()` calls the SEC EDGAR full-text search endpoint.
6. Each SEC hit is parsed by `_parse_hit()` into a `Filing`.
7. `_parse_hit()` assigns `situation_type` from a static map. For `8-K`, it tries keyword classification from the generated summary and `period_of_report`.
8. The scan endpoint loops over parsed filings and immediately skips any filing with no `situation_type`.
9. The scan endpoint checks for an existing `SpecialSituation` with the same `filing_url` and skips duplicates.
10. Remaining filings are passed to `evaluate_situation()`.
11. Production evaluator version is selected by `EVALUATOR_VERSION`, defaulting to `v1`.
12. A `SpecialSituation` row is inserted with `status="detected"`, the filing metadata, evaluation JSON, and source URL.
13. `GET /api/investment/situations` returns rows for the Evaluations UI.
14. `/investment/evaluations` loads situations and shows the queue.
15. `/investment/evaluations/[id]` can create a `ResearchCase` through `POST /api/investment/research-cases/from-situation/{situation_id}`.

Key code evidence:

- `backend/api/investment/router.py`: scanner endpoint starts at line 304; calls `_sec.search_recent()` at line 322; skips missing `situation_type` at line 340; deduplicates by `filing_url` at lines 343-346; evaluates at line 351; creates `SpecialSituation` at lines 368-378; returns `scanned_filings` and `new_situations` at lines 398-401.
- `backend/services/investment/sources/sec_edgar.py`: SEC adapter, form list, query building, hit parsing.
- `backend/services/investment/evaluator.py`: evaluator defaults to v1 through `os.getenv("EVALUATOR_VERSION", "v1")` at line 28.
- `backend/services/investment/research_cases.py`: ResearchCase creation from a situation at lines 265-303.

## 3. Current Scanner Coverage

Source adapter:

- Only `SECEdgarAdapter` is used by the scan endpoint.
- It is instantiated directly as `_sec = SECEdgarAdapter()` in `backend/api/investment/router.py`.
- No active source query is made against `investment_sources` during `/scan`.

SEC endpoint:

- `https://efts.sec.gov/LATEST/search-index`
- Defined as `_SEARCH_URL` in `backend/services/investment/sources/sec_edgar.py`.

Forms searched by `search_recent()`:

- `8-K`
- `S-1`
- `F-1`
- `SC TO-T`
- `SC TO-I`
- `Form 10`
- `DEF 14A`
- `DEFC14A`

Query shape:

- `_query()` sends `q` as the quoted filing type, for example `"8-K"`.
- It also sends `forms` equal to the filing type.
- If a time window is provided, it sends `dateRange=custom` and `startdt=<YYYY-MM-DD>`.

Time window:

- Scan endpoint default: `hours_back=6`.
- SEC adapter converts this to a calendar date string: `datetime.now(timezone.utc) - timedelta(hours=hours_back)`, then `YYYY-MM-DD`.
- This means a 6 hour scan is implemented as a start date, not an exact timestamp window.

Limits:

- `_query()` default `limit=20`.
- `search_recent()` queries 8 form types, so the theoretical maximum returned to the scanner is 160 parsed filings before downstream skips.
- There is no pagination.

Classification:

- Direct filing map:
  - `Form 10` -> `spin_off`
  - `SC TO-T`, `SC TO-I`, `SC 13E-3` -> `tender_offer`
  - `DEF 14A`, `DEFC14A` -> `proxy_fight`
  - `S-1`, `F-1` -> `ipo`
  - `8-K` -> requires keyword classification
- `8-K` keyword classification currently checks only the generated summary plus `period_of_report`, not the full filing text. This is probably too weak for many corporate events.

Important mismatch with v2 routing:

- The v2 routing engine recognizes more form types and patterns, including `SC 13D`, `DFAN14A`, `S-3`, `F-3`, `DEFM14A`, `PREM14A`, `S-4`, and `13E-3`.
- The production scanner does not search several of those forms, so v2 cannot help with candidates that are never fetched.

## 4. Funnel Visibility

What is currently logged:

- Scan started through `run_logger.start_run()`.
- SEC source call summary with source name, endpoint URL, total parsed filings returned, and errors if the whole SEC call fails.
- Final output summary: `Scanned 1 source. N filings found. M new situations created.`
- Created DB records count: `{"special_situations": M}`.
- AI usage for each evaluated filing, if evaluation succeeds.
- Full run details are available through observability endpoints, and Radar Status reads `fetchAgent('investment_scanner')`.

What is not logged clearly:

- Raw SEC hits per form before parsing.
- Parsed filings per form.
- Classified vs unclassified filings.
- Skipped filings because `situation_type` is missing.
- Skipped duplicates by `filing_url`.
- Evaluation failures per filing. These are stored in the row's evaluation JSON if the row is still created, but not summarized in the scanner funnel.
- Per-form SEC errors if one form fails while others could continue. Current `_query()` raises on request errors, and `/scan` fails the whole scan.
- Whether zero new situations means no raw hits, no classified hits, all duplicates, or evaluator/DB problems.

Radar Status currently shows:

- Agent status, run counts, failed run count.
- Last run output summary.
- Last success/failure.
- Recent scanner runs.
- Source registry summary.
- Cron calendar.

Radar Status does not currently show:

- Raw hits by form.
- Candidate funnel counts.
- Skip reasons.
- Duplicate count.
- A warning that Source Registry active/inactive toggles do not control `/scan`.

Recommended diagnostics fields:

- `raw_hits_by_form`
- `parsed_filings_by_form`
- `classified_candidates_by_type`
- `skipped_unclassified_count`
- `skipped_duplicate_count`
- `evaluated_count`
- `evaluation_error_count`
- `created_count`
- `source_registry_used: false`
- `adapter_name: SECEdgarAdapter`
- `forms_searched`
- `hours_back`
- `query_limit_per_form`

## 5. Why It May Find No Opportunities

Ranked likely causes:

1. Scanner coverage is too narrow. It uses only SEC EDGAR and only a hardcoded form list.
2. `investment_sources` is not wired into the scanner, so source expansion in the UI does not expand real discovery.
3. Several forms recognized by the v2 routing engine are not searched by the production scanner.
4. `8-K` classification is probably too weak because it does not inspect filing text or item descriptions; it mostly sees a generic summary.
5. Unclassified filings are silently skipped in `/scan`.
6. Duplicate filtering by `filing_url` may make scans look empty after earlier runs.
7. Per-form limit is 20 and there is no pagination.
8. Default scan window is six hours, converted to a start date. This may be operationally acceptable, but it is not a precise rolling six-hour window.
9. SEC API request failures fail the scan, but partial source/form health is not captured.
10. v1 evaluator is production default and less structured than v2, so even created candidates may be less useful. However, v1 is not the primary reason opportunities are not detected, because detection happens before evaluation.

## 6. Confirmed Gaps

Confirmed gaps:

- Scanner does not use `investment_sources`.
- Sources UI toggle does not affect scans.
- v2 evaluator is not globally active.
- Source universe is incomplete.
- Scanner may be too narrow.
- Empty scan reasons may not be visible enough.

Additional confirmed gaps:

- Observability agent registry currently claims the scanner reads active sources from the DB, but the scan code uses a hardcoded `_sec` adapter.
- Registry text says inactive sources are skipped by `investment_scanner`; current code has no such branch.
- Source Registry Summary on Radar Status can be misleading because it displays active source counts next to scanner runs even though those counts do not control scanning.
- There is no scanner funnel test proving raw SEC hits become visible UI rows.
- `SECEdgarAdapter._query()` logs filings returned per form to Python logs, but those per-form counts are not persisted to `agent_runs`.

Severity:

- High: scanner not wired to `investment_sources`.
- High: insufficient funnel metrics for empty scans.
- Medium: production form coverage narrower than v2 routing coverage.
- Medium: 8-K classifier likely under-detects because it uses metadata summary only.
- Medium: source registry and agent registry can mislead operators.
- Low: Evaluations page can hide rows only when manual filters are active; default page requests archived rows too.

## 7. Frontend Visibility Check

Evaluations page:

- `/investment/evaluations` calls `fetchSituations()` with `include_archived: true`.
- Default quick status filter is empty, so all statuses returned by the backend are visible.
- Additional evaluator/playbook/recommendation filters default to empty.
- The page does not appear to hide active rows by default.
- It can show an empty queue if a user has selected a quick status filter or v2-specific filter that excludes v1 rows.
- v1 rows have `evaluator_version="v1"` from serializer defaults and usually lack v2-specific `playbook_status`, `selected_playbook`, and v2 recommendation fields.

Backend list behavior:

- `GET /api/investment/situations` excludes archived rows by default unless `include_archived=true`.
- The Evaluations page explicitly passes `include_archived=true`, so archived rows are included there.
- Backend filtering by v2 fields happens after loading rows and serializing JSON.
- There is no pagination on `GET /situations`, so the current UI is not losing rows due to page size.

Radar Status page:

- It is read-only and does not trigger scans.
- It reads `investment_scanner` observability, source registry, and cron schedule.
- It may imply source registry health is scanner health, which is not currently true.

Evaluation detail page:

- It exposes a manual v2 preview button with confirmation and states that it makes a live AI call and does not save to DB.
- ResearchCase creation is manual from a situation detail page.

## 8. Backend/Data Check

Main tables involved:

- `special_situations`: created by `/api/investment/scan`; displayed by Evaluations queue.
- `situation_history`: written when a situation status is patched.
- `investment_sources`: displayed and managed by source registry, but not used by `/scan`.
- `research_cases`: created manually from a `special_situations` row.
- `agent_runs`: stores scan run status and summary.
- `ai_usage`: stores evaluator token usage when evaluation succeeds.

Main endpoints:

- `POST /api/investment/scan`: scan trigger. Do not call without explicit approval.
- `GET /api/investment/situations?include_archived=true`: read all visible evaluations.
- `GET /api/investment/situations/{id}`: read one evaluation.
- `POST /api/investment/research-cases/from-situation/{situation_id}`: manual ResearchCase creation.
- `GET /api/investment/research-cases?situation_id={id}`: check whether a situation has a ResearchCase.
- `GET /api/investment/sources`: read source registry.
- `GET /api/observability/agents/investment_scanner`: inspect scanner runs.
- `GET /api/observability/runs?agent_name=investment_scanner`: inspect raw run records.
- `GET /api/observability/cron/upcoming?days=3`: inspect upcoming scheduled scan entries.

Manual read-only checks Dani can run through the app/API:

- Check latest `investment_scanner` run output summary.
- Check latest `api_calls_made` payload for `filings_returned`.
- Check `database_records_created.special_situations`.
- Query situations with `include_archived=true`.
- Compare source registry active count against the audit finding that active toggles do not yet affect scan behavior.

No secrets, hostnames, IPs, or infrastructure details are needed for these checks.

## 9. Test Coverage

Existing relevant tests:

- `backend/tests/test_investment_api.py`: v2 endpoint behavior, v2 daily limit, v2 does not persist global `EVALUATOR_VERSION`, serializer extraction of v2 fields.
- `backend/tests/test_evaluator.py`: evaluator version default, v2 normalization, routing/evaluation behavior with mocked AI, prohibited inference guard.
- `backend/tests/test_evaluator_v2_shadow_e2e.py`: mocked v2 end-to-end evaluation for fixture cases.
- `backend/tests/test_evaluator_shadow_fixtures.py`: deterministic v2 routing fixture tests.
- `backend/tests/test_observability.py`: agent run logging, observability endpoints, cron upcoming shape, secret redaction.
- ResearchCase tests cover later workspace behavior, not the scanner funnel itself.

Missing tests:

- Unit tests for `SECEdgarAdapter._parse_hit()` against representative SEC EFTS hit shapes.
- Unit tests for `SECEdgarAdapter._query()` parameter construction.
- Scanner endpoint test with mocked SEC filings proving scan -> evaluate -> `SpecialSituation`.
- Scanner endpoint test proving unclassified filings are counted and reported.
- Scanner endpoint test proving duplicates are counted and reported.
- Scanner endpoint test proving source registry toggles currently do not affect `/scan`, or future tests proving they do once wired.
- UI tests for Evaluations filters and empty-state interpretation.
- Radar Status test showing funnel metrics once diagnostics are added.

## 10. Recommended Next Sprints

Sprint A: read-only diagnostics and funnel metrics

- Add scanner funnel summary to `agent_runs.api_calls_made` or a dedicated diagnostics payload.
- Persist per-form raw hits, parsed filings, classified candidates, skipped unclassified, skipped duplicates, evaluated, evaluation errors, created.
- Update Radar Status to display these metrics.
- Add a clear banner: Source Registry toggles are read-only for now and do not control scanner behavior.

Sprint B: scanner query coverage hardening

- Review form coverage against v2 routing.
- Add missing forms in read-only/shadow mode first: `SC 13D`, `DFAN14A`, `DEFM14A`, `PREM14A`, `S-4`, `S-3`, `F-3`, and `SC 14D-9` if relevant.
- Add per-form limits and pagination policy.
- Improve `8-K` classification using available SEC metadata without crawling full documents unless explicitly approved.

Sprint C: wire `investment_sources` into scanner

- Replace hardcoded `_sec.search_recent()` with DB-driven active source selection.
- Keep `SECEdgarAdapter` as the first supported adapter.
- Respect `active`, `check_frequency_hours`, `priority`, and adapter type.
- Update agent registry text only after the code behavior is true.

Sprint D: limited v2 shadow mode for new candidates

- Do not enable v2 globally.
- For newly created candidates, optionally run v2 shadow evaluation under a daily cap and store shadow output separately or in a clearly marked preview field.
- Compare v1/v2 routing and usefulness metrics.

Sprint E: opportunity triage dashboard

- Add a private triage page showing newly detected, duplicate, unclassified, and needs-review candidates.
- Include source, form, detected signal, confidence, and reason for inclusion or exclusion.

Sprint F: historical/source intelligence feedback loop

- Use approved historical/source intelligence suggestions to propose source registry changes.
- Keep apply-to-source-registry manual until Phase 4D-style apply rules are approved.

## 11. Safe Immediate Fixes Applied

No code fixes were applied.

Only this audit document was added. The directory `docs/investment/` was created because it did not exist.

Reason: the findings point to coverage and diagnostics work rather than a tiny safe bug fix. Changing scanner behavior, query coverage, source registry wiring, or evaluator versioning would exceed this controlled audit sprint.

## 12. Risks / Non-Goals

Confirmed non-goals respected:

- No scan triggered.
- No cron changed.
- No v2 globally enabled.
- No `EVALUATOR_VERSION` default changed.
- No DB migration.
- No deploy.
- No service restart.
- No live AI call.
- No Marketplace/Sales changes.
- No public-site changes.
- No publishing, Substack, or public article workflow changes.
- No secrets, IPs, hostnames, credentials, Tailscale details, raw `.env` content, or VPS details added.
- No raw course transcript, audio, video, or course_index content added.

Operational risk if unchanged:

- Dani may see a healthy Radar Status page and active sources, while actual scans are still limited to one hardcoded SEC adapter.
- Empty scans remain ambiguous.
- Good opportunities can be missed before evaluation because they were never fetched or were silently skipped as unclassified.

GO / NO-GO for next implementation:

- GO for Sprint A: read-only diagnostics and funnel metrics.
- NO-GO for source registry wiring, broader SEC coverage, or v2 shadow mode until Sprint A exposes the current funnel clearly and tests are added.
