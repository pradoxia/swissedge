# SwissEdge Investment Platform V2 Architecture

Date: 2026-05-09

Status: architecture and cleanup planning only. No implementation is approved by this document.

## 1. Purpose

SwissEdge Investment is shifting from a scanner-first model to a source-driven ResearchCase pipeline because the current flow loses too much operational meaning before research begins.

The current model is:

`SEC scanner -> SpecialSituation -> Evaluations queue -> manual ResearchCase`

That works as an early MVP, but it has three structural weaknesses:

- Discovery is centered on one hardcoded scanner path rather than on the `investment_sources` registry.
- Relevant signals become `SpecialSituation` rows first, while the durable research object, `ResearchCase`, is created manually later.
- Empty or low-yield scans are difficult to diagnose because source coverage, intake, classification, evaluation, and UI visibility are not tracked as one funnel.

The V2 goal is:

`investment_sources -> connector / intake method -> preliminary ResearchCase -> initial course-grounded evaluation -> Research Inbox -> iterative enrichment -> deep research / archive / public draft`

This makes `ResearchCase` the primary unit of work from the beginning. A source does not merely generate a passive signal; it creates a traceable research candidate with origin, evidence, methodology status, verification tasks, and disclaimer.

## 2. Current State

`investment_sources` exists as a DB model and API surface. It supports fields such as name, URL, source type, active flag, priority, check frequency, access method, query template, last checked, last success, and last error. The frontend `/investment/sources` page can list and toggle sources. Current gap: the production scanner does not yet use this table for scan decisions.

SEC EDGAR scanner exists. The current scan endpoint uses a hardcoded `SECEdgarAdapter` and queries the SEC full-text endpoint for a fixed list of forms. It writes `SpecialSituation` records after classification and evaluation. Current gap: it is not source-registry driven, has limited funnel metrics, and creates situations rather than preliminary ResearchCases.

`SpecialSituation` and the Evaluations queue exist. They are operational as the current candidate queue. They hold company, ticker, filing type, filing URL, status, evaluation JSON, source URLs, notes, and history. Current gap: this is a signal/evaluation queue, not a research inbox.

`ResearchCase` workspace exists and is deployed. A ResearchCase can be created manually from a `SpecialSituation`; it has status, brief, readiness label, notes, disclaimer, tasks, documents, and sources. Current gap: there is no source-driven automatic or semi-automatic preliminary ResearchCase intake.

AI Brief Preview exists. It is manual, preview-only, and applies selected sections into the ResearchCase brief. It uses stored case metadata, tasks, documents, and sources. It does not fetch URLs.

Quality Assist exists. It is manual, preview-only, and suggests status/readiness from stored case data. It hard-blocks automated movement toward public publication behavior and keeps output assistive.

Document Intelligence exists. It analyzes pasted snippets stored on `ResearchDocument`, not external URLs. It is preview-only and does not automatically create tasks.

Source Intelligence exists. It scores case-level `ResearchSource` rows and creates proposed `SourceIntelligenceSuggestion` records. It has an approval queue, but no apply-to-source-registry behavior yet.

`PublicArticleDraft` exists. It is a private editorial artifact created from a ResearchCase and manually reviewed. It is not a publishing system. No public posting or Substack integration is active.

Radar Status exists. It is a read-only frontend view over observability, source registry, and cron schedule. Current gap: it can imply source registry health is scanner health, even though the scanner is not yet driven by source registry rows.

## 3. Target Architecture

Target flow:

```text
investment_sources
  -> connector / intake method
  -> source intake event or equivalent trace record
  -> preliminary ResearchCase
  -> initial course-grounded evaluation
  -> Research Inbox
  -> iterative enrichment
  -> deep research / archive / public draft
```

The V2 pipeline should behave as follows:

1. `InvestmentSource` describes an operational source, such as SEC EDGAR, an RSS feed, an email alert, a newsletter, an X account, a manual Telegram input, or a future API.
2. A connector or intake method reads from the source according to its approved method. Some methods are automated, some are manual, and some are metadata-only.
3. Each relevant input creates a traceable source intake event. This can be a new table later or an equivalent logged event in the first implementation.
4. The intake event creates or updates a preliminary `ResearchCase`.
5. The initial evaluation runs against processed course methodology artifacts, never raw course transcripts.
6. The case enters a Research Inbox with status, source origin, evidence level, methodology status, official-source status, tasks, documents, duplicate state, and follow-up needs.
7. The case is enriched through official source verification, document snippets, tasks, source intelligence, quality assist, and manual notes.
8. Later, a mature case can move to deep research, archive, or private public-draft preparation.

## 4. Core Entities

| Entity | Role in V2 | Current state |
|---|---|---|
| `InvestmentSource` | Operational registry row for every source SwissEdge may intake from. | Exists, needs extension. |
| Source connector / intake method | Code or manual workflow that reads from a source and normalizes events. | Partially exists for SEC EDGAR as `SECEdgarAdapter`; needs registry wiring and method abstraction. |
| Source intake event | Trace record for one source input: raw metadata, source ID, intake method, classification, duplicate decision, and case creation result. | New. Can start as logged diagnostics before a table. |
| `ResearchCase` | Primary durable research object, created as early as possible from relevant source input. | Exists, needs intake metadata and inbox fields. |
| `ResearchTask` | Verification and enrichment tasks for Dani or agents. | Exists, reusable. |
| `ResearchDocument` | Case/historical document metadata and manually pasted snippets. | Exists, reusable; may need official-source status fields later. |
| `ResearchSource` | Case-level source reference and usefulness notes. | Exists, reusable; already links optionally to `investment_sources`. |
| `PublicArticleDraft` | Private editorial output after research is documented and manually approved. | Exists, keep later in pipeline. |
| `HistoricalCase` | Past case study and source learning object. | Exists, useful for feedback loop, not initial V2 intake path. |

## 5. InvestmentSource V2

Target source registry fields:

| Field | Purpose | Current status |
|---|---|---|
| `source_type` | Broad type: `sec_edgar`, `x_account`, `newsletter`, `email_alert`, `rss`, `website`, `company_ir`, `manual_telegram`, `api`, `other`. | Exists, needs stricter vocabulary. |
| `intake_method` | How SwissEdge receives inputs: `poll_api`, `manual_paste`, `email_forward`, `rss_poll`, `telegram_manual`, `browser_review`, `future_connector`. | New. |
| `connector_key` | Stable adapter key, for example `sec_edgar_efts`, `manual_telegram`, `rss_generic`. | New. |
| `status` | Operational status: `active`, `paused`, `manual_only`, `needs_connector`, `broken`, `retired`. | New; current `active` boolean can map into this. |
| `priority` | Scheduling and inbox priority. | Exists. |
| `reliability` | Operator-level trust score: `official`, `high`, `medium`, `low`, `experimental`. | New. |
| `auto_create_research_case` | Whether relevant inputs may create preliminary ResearchCases automatically. | New. |
| `requires_manual_review` | Whether source outputs must be reviewed before case creation or enrichment. | New. |
| `last_intake_at` | Last successful source intake attempt. | New; current `last_checked` partially overlaps. |
| `last_case_created_at` | Last time this source produced a ResearchCase. | New. |
| `cases_created_count` | Count of ResearchCases created from this source. | New. |
| `last_error` | Last connector/intake error. | Exists. |

No migration is implemented in this sprint.

## 6. Preliminary ResearchCase Lifecycle

Target lifecycle:

- `detected`: A relevant source input was detected and a preliminary case exists.
- `initial_evaluated`: Initial course-grounded evaluation is attached.
- `needs_official_source`: The case originated from a non-official source and needs primary documents.
- `needs_enrichment`: The case has enough signal to investigate but lacks tasks, documents, sources, or methodology depth.
- `ready_for_deep_research`: The case has official evidence, methodology reference, and clear next tasks.
- `documented`: The research brief is complete enough for durable internal use.
- `archived` / `discarded`: The case is no longer active. `discarded` is conceptually distinct from archive but can map to archive until a new status is added.

Mapping to current valid ResearchCase statuses:

| V2 lifecycle | Current status mapping | Notes |
|---|---|---|
| `detected` | `detected` | Already valid. |
| `initial_evaluated` | `brief_generated` or `under_investigation` | Depends on whether an initial brief exists. |
| `needs_official_source` | `under_investigation` + task/readiness metadata | Needs new explicit field later. |
| `needs_enrichment` | `under_investigation` | Already valid but too broad. |
| `ready_for_deep_research` | `under_investigation` + `investment_readiness="candidate"` | Needs explicit inbox bucket later. |
| `documented` | `documented` | Already valid. |
| `archived` | `archived` | Already valid. |
| `discarded` | `archived` + reason metadata | New status later if needed. |

Current readiness labels remain:

- `monitor`
- `not_actionable`
- `needs_more_work`
- `candidate`

## 7. Course-Grounded Methodology Requirement

Every analytical output must include or be traceable to this methodology contract:

- `situation_type`
- `playbook_used`
- `checklist_used`
- `methodology_status`
- `course_reference`
- `evidence_level`
- `missing_information`
- `risks`
- `next_steps`
- `human_review_required`
- `disclaimer`

Agents must use processed artifacts only:

- `course_index/master_index.json`
- `course_index/playbooks/*.md`
- `course_index/playbooks/taxonomy.md`
- `course_index/playbooks/source_map.md`
- `course_index/playbooks/risk_patterns.md`
- `course_index/playbooks/global_checklist.md`
- `course_index/playbooks/evaluation_schema.json`

Agents must never read or quote raw course transcripts, audio, video, or copyrighted course text. The processed artifacts define routing, checklist, source category, risk, and evaluation schema boundaries. If a situation lacks sufficient methodology support, the output must say that it is detection-only or needs human review.

All investment outputs must include:

`Este análisis es educativo. No es asesoramiento financiero.`

## 8. Agent Network V2

| Agent | Purpose | Inputs | Outputs | Required skills | Existing support | Priority |
|---|---|---|---|---|---|---|
| Source Registry Manager | Maintain source metadata and operational status. | `InvestmentSource` rows, source suggestions. | Updated source registry, warnings. | CRUD, validation, source taxonomy. | Partially exists through `/investment/sources`. | Now |
| Source Intake Agent | Normalize source inputs into intake events. | Source connector results or manual input. | Source intake events, duplicate checks. | Connector orchestration, observability. | New. | Now |
| SEC EDGAR Intake Agent | First production source-driven intake path. | SEC source rows, EDGAR connector output. | Preliminary ResearchCases from SEC filings. | SEC metadata parsing, filing classification. | Partially exists as scanner + adapter. | Now |
| External Signal Agent | Handle non-official source signals without over-trusting them. | X account summaries, newsletters, RSS, email, manual notes. | Preliminary cases or tasks requiring official source verification. | Signal normalization, provenance, caution. | New. | Later |
| ResearchCase Creator Agent | Create minimal ResearchCases from intake events. | Intake event, source metadata, classification. | ResearchCase, tasks, documents, sources. | Idempotency, dedupe, metadata mapping. | Partially exists from `SpecialSituation`. | Now |
| Course Methodology Agent | Attach course-grounded methodology context. | Situation type, source evidence. | Playbook/checklist/status contract. | `course_index` loading and routing. | Partially exists through loaders/routing. | Now |
| Initial Evaluation Agent | Produce initial structured evaluation without pretending final certainty. | Preliminary case, methodology contract. | Initial evaluation, risks, missing info, tasks. | Prompting, schema validation, no directive language. | Partially exists as v1/v2 evaluator. | Now |
| Research Inbox Agent | Organize preliminary cases into actionable buckets. | ResearchCases and intake metadata. | Inbox rows, filters, counts. | UI/API aggregation. | New, but list pages exist. | Now |
| Official Source Verification Agent | Ensure external signals are tied back to primary documents. | Non-official case, source hints. | Verification tasks and source status. | Provenance, official-source policy. | New. | Later |
| Market Monitoring Agent | Follow active cases for market-data changes. | Active ResearchCases, market data snapshots. | Change alerts, stale-data warnings. | Market data ingestion, event detection. | New. | Later |
| Deep Research Agent | Expand mature cases into full research briefs. | Ready cases, documents, tasks, sources. | Deep brief sections and task suggestions. | Course methodology, document intelligence. | Partially exists as AI Brief Preview. | Later |
| Document Intelligence Agent | Analyze pasted document snippets. | ResearchDocument summaries/snippets. | Preview analysis, risks, missing info. | Snippet analysis, copyright caution. | Exists. | Later |
| Source Intelligence Agent | Learn useful sources from active and historical cases. | ResearchSources, HistoricalCases. | Source suggestions and source scores. | Source quality analysis. | Exists as preview and queue. | Later |
| Quality Review Agent | Check case completeness and readiness. | ResearchCase data. | Checklist, suggested status/readiness. | QA, schema validation. | Exists. | Later |
| Duplicate & Merge Agent | Detect duplicate cases across sources. | Intake events, ResearchCases, filings. | Duplicate warnings, merge suggestions. | Entity matching, idempotency. | New. | Now |
| Timeline & Follow-up Agent | Maintain next checks and stale-case warnings. | ResearchCase status, tasks, market events. | Follow-up tasks and alerts. | Scheduling, status rules. | Partially exists as watchlist follow-up. | Later |
| Telegram Interaction Agent | Allow Dani to submit/manual triage cases. | Telegram messages, links, notes. | Manual intake events or case updates. | Intent routing, safety. | OpenClaw exists as operator; not V2-specific. | Later |
| Internal Methodology & Operations Auditor | Detect drift, misleading UI, stale data, missing methodology. | DB state, routes, source registry, UI assumptions. | Audit reports and warnings. | Static/runtime audit, architecture rules. | New; audit docs exist manually. | Now |
| Public Draft Agent | Convert documented cases into private editorial drafts. | Documented ResearchCase. | PublicArticleDraft. | Editorial transformation, compliance checks. | Exists. | Later |

## 9. SEC EDGAR Priority Path

SEC EDGAR should become the first fully operational source-driven intake:

```text
SEC EDGAR InvestmentSource
  -> SEC connector
  -> source intake event
  -> preliminary ResearchCase
  -> initial course-grounded evaluation
  -> Research Inbox
```

Required behavior:

- SEC EDGAR exists as an `InvestmentSource` row with `source_type="sec_edgar"` and a connector key.
- The intake job reads active/eligible SEC sources from `investment_sources`.
- The SEC connector records per-form funnel metrics.
- Each relevant filing creates or updates a preliminary ResearchCase directly.
- The ResearchCase records source origin, filing metadata, evidence level, methodology status, official-source status, and verification tasks.
- Duplicates are detected before creating a new case.

Current known gap:

- The scanner is currently not fully driven by `investment_sources`; it directly instantiates `SECEdgarAdapter`.

## 10. External Source Path

External sources are handled generically. Catalyst Bulletin / DealintCB is one example, not the center of the architecture.

Source categories:

- Catalyst Bulletin / DealintCB
- Other X accounts
- Newsletters
- Email alerts
- RSS feeds
- Manual Telegram input
- Websites
- Company IR pages
- Future APIs

Generic external-source flow:

```text
external InvestmentSource
  -> approved intake method
  -> external signal event
  -> duplicate check
  -> preliminary ResearchCase or verification task
  -> official source verification
  -> initial course-grounded evaluation
```

Rules:

- No X scraping or X API use until explicitly approved.
- No URL crawling in this architecture sprint.
- External signals should not be treated as official evidence.
- External-sourced cases should usually start with `needs_official_source`.
- The first task should identify or attach official company, SEC, court, or regulator evidence where applicable.

## 11. Research Inbox

Purpose:

The Research Inbox is the main manual queue for preliminary ResearchCases. It replaces the Evaluations queue as the primary work surface for new opportunities.

Buckets:

- New intake
- Initial evaluated
- Needs official source
- Needs enrichment
- Ready for deep research
- Monitoring
- Archived/discarded

Columns:

- Case
- Source origin
- Intake method
- Situation type guess
- Evidence level
- Official-source status
- Methodology status
- Readiness
- Open tasks
- Documents
- Sources
- Duplicate status
- Last updated
- Next follow-up

Actions:

- Open case
- Mark needs official source
- Add verification task
- Attach document metadata
- Add source reference
- Run initial evaluation preview
- Mark ready for deep research
- Archive/discard with reason
- Create public draft only after documented state and manual approval

Filters:

- Source type
- Source name
- Intake method
- Situation type
- Evidence level
- Official-source status
- Methodology status
- Readiness
- Open-task count
- Duplicate status
- Age/staleness

## 12. Market Monitoring Future Path

The Market Monitoring Agent is future work. It should:

- Follow active ResearchCases.
- Retrieve price, volume, and fundamental snapshots from approved providers.
- Detect material changes such as price movement, spread changes, volume spikes, deadline proximity, amendment filings, or stale data.
- Create observations and tasks, not final investment instructions.
- Never issue directive recommendation language.

Possible providers to evaluate later:

- Tiingo
- FMP
- Alpha Vantage
- Polygon/Massive
- EODHD
- Nasdaq Data Link

No provider implementation is approved in this sprint.

## 13. Internal Auditor Requirements

The Internal Methodology & Operations Auditor must check:

- Sources with no connector.
- Active sources not producing cases.
- ResearchCases without methodology reference.
- External cases without official-source tasks.
- Cases without tasks/documents/sources.
- Scanner not wired to source registry.
- UI claims not matching backend reality.
- Missing disclaimers.
- Directive recommendation language violations.
- Stale cases.
- Duplicate cases.
- Missing observability.
- Source registry rows with broken status, stale `last_intake_at`, or repeated errors.
- ResearchCases whose status/readiness combination is inconsistent.

The auditor should first produce read-only reports. It should not mutate cases or sources without a separate approval workflow.

## 14. Migration Strategy

Safe migration stages:

1. No deletion first. Preserve `SpecialSituation`, Evaluations queue, current ResearchCase workflow, and public drafts.
2. Add metadata first. Extend source and case contracts on paper, then with additive DB fields only after approval.
3. Add inbox next. Build a read-only Research Inbox over existing ResearchCases before changing intake.
4. Wire SEC EDGAR next. Make SEC the first source-driven path from `investment_sources` to preliminary ResearchCase.
5. Add external intake after SEC is reliable. Start with manual or email/RSS style ingestion, not scraping.
6. Add market monitoring later. Keep it observational and task-generating.
7. Add auditor dashboard. Surface architecture drift, missing metadata, stale cases, and misleading UI claims.

## 15. Non-Goals

This architecture sprint does not:

- Implement new agents.
- Trigger scans.
- Change cron.
- Enable evaluator v2 globally.
- Run live AI.
- Run DB migrations.
- Deploy or restart services.
- Modify Marketplace/Sales.
- Modify public-site work.
- Scrape X.com or use the X API.
- Use Substack API.
- Fetch or crawl URLs.
- Add secrets, infrastructure details, raw `.env`, credentials, raw course transcripts, or copyrighted course text.
- Auto-publish anything.

## 16. Open Questions

- Should preliminary ResearchCases keep `SpecialSituation` as an optional legacy link, or should `SpecialSituation` become a derived/compatibility view over source intake events?
- Should source intake events be a new table immediately, or can Sprint 1 start with structured `agent_runs` diagnostics plus ResearchCase metadata?
- What is the minimal `InvestmentSource` V2 field set for the first migration?
- Which current ResearchCase statuses should remain user-visible once Research Inbox buckets exist?
- Should `discarded` become a real ResearchCase status or remain `archived` plus reason metadata?
- What exact evidence-level vocabulary should be used: `official_primary`, `official_secondary`, `trusted_external`, `unverified_external`, `manual_note`?
- What source reliability labels should Dani see in the UI?
- Which SEC forms should be included in the first source-driven SEC intake release?
- Should v2 evaluator be used only as shadow evaluation for SEC-created ResearchCases, or should a new initial-evaluation service be built from the same schema?
- What are the first non-SEC external sources that Dani wants to model after SEC is reliable?
