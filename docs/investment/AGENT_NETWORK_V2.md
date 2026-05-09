# SwissEdge Investment Agent Network V2

Date: 2026-05-09

Status: future agent network definition. Do not implement these agents from this document alone.

## Network Principles

- FastAPI remains the source of truth for business logic, DB writes, validation, and AI calls.
- `investment_sources` is the operational source registry.
- `ResearchCase` is the primary durable work object.
- Every analytical agent must use processed course methodology artifacts, never raw course materials.
- Every investment output must include the required educational disclaimer.
- Agents may create tasks, warnings, previews, and draft research artifacts only within approved workflows.
- No agent publishes, changes cron, deploys, restarts services, triggers scans, globally enables v2, uses X API, scrapes X.com, crawls URLs, or issues directive recommendation language without explicit future approval.

## Source Registry Manager

- Goal: Keep `investment_sources` accurate, operational, and auditable.
- Trigger: Manual UI/API changes, approved source-intelligence suggestions, auditor warnings.
- Inputs: Source metadata, approved suggestions, source health.
- Outputs: Source registry rows, status warnings, configuration gaps.
- Data touched: `investment_sources`, later source audit records.
- Course methodology dependency: Uses `source_map` categories to classify source purpose, but does not analyze opportunities.
- Guardrails: Does not run connectors or create cases by itself.
- First implementation priority: Now.
- Existing state: Partially exists through source CRUD and UI.
- Future enhancements: Source quality score, connector readiness, source lineage.

## Source Intake Agent

- Goal: Normalize raw source inputs into traceable intake events.
- Trigger: Approved connector run or manual intake.
- Inputs: Source row, connector output, manual note, or imported alert.
- Outputs: Source intake event, normalized candidate metadata.
- Data touched: Future source intake event table or structured observability payload.
- Course methodology dependency: Calls Course Methodology Agent for situation taxonomy only after normalization.
- Guardrails: Does not fetch unapproved URLs; does not create final conclusions.
- First implementation priority: Now.
- Existing state: New.
- Future enhancements: Multi-source batching, replay, dead-letter queue.

## SEC EDGAR Intake Agent

- Goal: Make SEC EDGAR the first source-driven intake path.
- Trigger: Approved scan/intake execution; future scheduled source intake.
- Inputs: SEC EDGAR `InvestmentSource` row, form coverage config, SEC connector output.
- Outputs: Intake events and preliminary ResearchCases.
- Data touched: `investment_sources`, `ResearchCase`, `ResearchDocument`, `ResearchSource`, observability.
- Course methodology dependency: Uses routing engine and evaluation schema to classify forms and methodology status.
- Guardrails: No scan trigger in this planning sprint; respect SEC rate limits; log funnel metrics.
- First implementation priority: Now.
- Existing state: Partially exists as hardcoded scanner and `SECEdgarAdapter`.
- Future enhancements: Pagination, per-form diagnostics, amendment tracking.

## External Signal Agent

- Goal: Intake non-official signals safely and require official-source verification.
- Trigger: Manual paste, email alert, RSS item, approved future connector.
- Inputs: External signal metadata, source row.
- Outputs: Preliminary ResearchCase or verification task.
- Data touched: ResearchCase, ResearchTask, ResearchSource, future intake event.
- Course methodology dependency: Uses taxonomy and source map to guess situation type cautiously.
- Guardrails: No X scraping, no X API, no URL crawling, no treating external signals as official evidence.
- First implementation priority: Later.
- Existing state: New.
- Future enhancements: Email forwarding, RSS polling, manual Telegram intake.

## ResearchCase Creator Agent

- Goal: Create minimal preliminary ResearchCases from intake events.
- Trigger: Intake event classified as relevant.
- Inputs: Intake event, source metadata, duplicate check result.
- Outputs: ResearchCase, origin source, initial tasks, disclaimer.
- Data touched: `research_cases`, `research_tasks`, `research_sources`, `research_documents`.
- Course methodology dependency: Stores methodology status from Course Methodology Agent.
- Guardrails: Idempotent; no duplicate creation when canonical case exists.
- First implementation priority: Now.
- Existing state: Partially exists as create-from-situation.
- Future enhancements: Merge suggestions and canonical case selection.

## Course Methodology Agent

- Goal: Attach processed methodology context to each case.
- Trigger: New preliminary case or initial evaluation.
- Inputs: Situation type guess, filing/source metadata.
- Outputs: Playbook used, checklist used, methodology status, course reference.
- Data touched: ResearchCase metadata later; no raw course data.
- Course methodology dependency: Directly uses `master_index`, playbooks, taxonomy, source map, risk patterns, global checklist, and evaluation schema.
- Guardrails: Never uses raw transcripts/audio/video; marks detection-only/out-of-scope clearly.
- First implementation priority: Now.
- Existing state: Partially exists through `playbook_loader`, `course_index`, and `routing_engine`.
- Future enhancements: Artifact health checks and methodology versioning.

## Initial Evaluation Agent

- Goal: Produce an initial, schema-bound, course-grounded assessment for inbox triage.
- Trigger: Preliminary ResearchCase creation or manual rerun.
- Inputs: Case metadata, source evidence, methodology contract.
- Outputs: Initial evaluation, missing information, risks, human-review items, tasks.
- Data touched: ResearchCase brief/evaluation metadata, tasks, observability.
- Course methodology dependency: Mandatory.
- Guardrails: Preview or controlled save only; no global v2 enablement; no directive recommendation language.
- First implementation priority: Now.
- Existing state: Partially exists as v1/v2 evaluator and quality/brief previews.
- Future enhancements: Shadow compare v1/v2, no-AI deterministic precheck.

## Research Inbox Agent

- Goal: Organize preliminary ResearchCases into work buckets.
- Trigger: User opens inbox or scheduled read-only summary.
- Inputs: ResearchCases, tasks, documents, sources, intake metadata.
- Outputs: Inbox rows, bucket counts, warnings.
- Data touched: Read-only initially.
- Course methodology dependency: Displays methodology status and missing methodology warnings.
- Guardrails: First version should be read-only or minimal status/task actions.
- First implementation priority: Now.
- Existing state: New, but research list page is reusable.
- Future enhancements: Saved views, triage metrics.

## Official Source Verification Agent

- Goal: Ensure external signals are grounded in official evidence.
- Trigger: External-source ResearchCase enters inbox.
- Inputs: Source origin, case metadata, source reliability.
- Outputs: Verification tasks and official-source status.
- Data touched: ResearchTask, ResearchDocument metadata, ResearchCase metadata later.
- Course methodology dependency: Uses source_map to know likely official source classes.
- Guardrails: Does not crawl URLs; creates tasks rather than claiming evidence.
- First implementation priority: Later.
- Existing state: New.
- Future enhancements: Official-source checklist by situation type.

## Market Monitoring Agent

- Goal: Follow active ResearchCases with market-data observations.
- Trigger: Future scheduled monitoring or manual refresh.
- Inputs: Active cases, approved market data providers, watch fields.
- Outputs: Observations, change alerts, follow-up tasks.
- Data touched: Future market snapshot records, ResearchTask, observability.
- Course methodology dependency: Uses risk patterns and playbook-specific monitoring needs.
- Guardrails: Never issues directive recommendation language; no provider implementation now.
- First implementation priority: Later.
- Existing state: New.
- Future enhancements: Tiingo, FMP, Alpha Vantage, Polygon/Massive, EODHD, Nasdaq Data Link evaluation.

## Deep Research Agent

- Goal: Expand ready cases into full research briefs.
- Trigger: Manual action from a ready case.
- Inputs: Case, verified documents, snippets, sources, tasks, methodology contract.
- Outputs: Structured research brief preview.
- Data touched: ResearchCase brief after manual apply.
- Course methodology dependency: Mandatory.
- Guardrails: Preview-first, manual apply, no URL fetching unless separately approved.
- First implementation priority: Later.
- Existing state: Partially exists as AI Brief Preview.
- Future enhancements: Multi-document synthesis with citations to stored snippets.

## Document Intelligence Agent

- Goal: Analyze manually supplied document snippets.
- Trigger: Manual preview on a ResearchDocument.
- Inputs: Stored snippet/summary and document metadata.
- Outputs: Summary, key points, risks, timeline items, missing information, suggested tasks.
- Data touched: Preview result only today.
- Course methodology dependency: Should align output with playbook and checklist in future.
- Guardrails: No URL fetching; copyright caution; no auto task creation unless approved.
- First implementation priority: Later.
- Existing state: Exists.
- Future enhancements: Task proposal queue.

## Source Intelligence Agent

- Goal: Learn which sources are useful from active and historical cases.
- Trigger: Manual preview/save suggestions.
- Inputs: ResearchSource rows, historical case notes, reconstruction.
- Outputs: Source scores and source suggestions.
- Data touched: `source_intelligence_suggestions`.
- Course methodology dependency: Should use source_map and situation type.
- Guardrails: Suggestions require manual approval; no automatic apply to `investment_sources`.
- First implementation priority: Later.
- Existing state: Exists.
- Future enhancements: Apply-approved workflow after Phase 4D approval.

## Quality Review Agent

- Goal: Check completeness and workflow readiness.
- Trigger: Manual quality preview.
- Inputs: ResearchCase, tasks, documents, sources, brief.
- Outputs: Checklist, suggested status/readiness, warnings.
- Data touched: Preview only; manual apply for status/readiness.
- Course methodology dependency: Should verify methodology fields in V2.
- Guardrails: Cannot auto-publish or bypass manual approval.
- First implementation priority: Later.
- Existing state: Exists.
- Future enhancements: Inbox batch warnings.

## Duplicate & Merge Agent

- Goal: Detect duplicate cases from multiple sources.
- Trigger: Intake event, inbox view, or manual check.
- Inputs: Company, ticker, filing URL, accession, source URLs, situation type, dates.
- Outputs: Duplicate warnings and merge suggestions.
- Data touched: Future duplicate table or case metadata; no deletion.
- Course methodology dependency: Minimal; situation type helps matching.
- Guardrails: No auto-merge in first version.
- First implementation priority: Now.
- Existing state: New, with simple duplicate-by-filing URL in scanner.
- Future enhancements: Canonical case merge UI.

## Timeline & Follow-up Agent

- Goal: Keep case deadlines and stale states visible.
- Trigger: Manual or future scheduled follow-up.
- Inputs: Case status, tasks, follow-up dates, documents.
- Outputs: Follow-up warnings and tasks.
- Data touched: ResearchTask, future timeline records.
- Course methodology dependency: Uses playbook-specific event/deadline expectations.
- Guardrails: No cron changes now.
- First implementation priority: Later.
- Existing state: Partially exists as watchlist follow-up.
- Future enhancements: Deadline calendar and stale-case dashboard.

## Telegram Interaction Agent

- Goal: Let Dani submit and triage research inputs from Telegram.
- Trigger: Manual Telegram message.
- Inputs: Text, links, source hints, case commands.
- Outputs: Manual intake event, task, note, or status change through FastAPI.
- Data touched: FastAPI-managed DB records only.
- Course methodology dependency: Calls backend agents; does not own analysis.
- Guardrails: OpenClaw/Telegram remains operator, not business logic.
- First implementation priority: Later.
- Existing state: OpenClaw exists as an operator; V2 manual intake does not yet exist.
- Future enhancements: Guided intake forms and case lookup.

## Internal Methodology & Operations Auditor

- Goal: Detect architecture drift, missing methodology, misleading UI, stale cases, and broken source operations.
- Trigger: Manual audit run or future read-only dashboard.
- Inputs: Source registry, ResearchCases, observability, route behavior, UI claims, methodology fields.
- Outputs: Audit report, warnings, suggested fixes.
- Data touched: Read-only initially.
- Course methodology dependency: Checks methodology artifacts and contract presence.
- Guardrails: Does not mutate data in first implementation.
- First implementation priority: Now.
- Existing state: New; current manual audit documents are inputs.
- Future enhancements: Dashboard and recurring reports after approval.

Sprint D implementation note: Sprint D implements the first read-only frontend audit page at `/investment/internal-audit` using existing `fetchResearchCases()`, `fetchSources()`, and `fetchAgent()` APIs. It computes 10 audit checks client-side (missing V2 metadata, methodology, official source status, no tasks/docs/sources, candidate cases without methodology, archived without reason, source registry not wired, scanner diagnostics). It does not mutate data, trigger scans, call AI, or alter sources.

## Public Draft Agent

- Goal: Convert documented ResearchCases into private editorial drafts.
- Trigger: Manual action from a documented case.
- Inputs: ResearchCase brief, tasks, documents, source metadata.
- Outputs: PublicArticleDraft.
- Data touched: `public_article_drafts`.
- Course methodology dependency: Ensures educational framing and readiness label.
- Guardrails: Manual review only; no public posting; no Substack API.
- First implementation priority: Later.
- Existing state: Exists.
- Future enhancements: Better article template, still manual publishing only.
