# SwissEdge V2 ResearchCase Metadata Contract

Date: 2026-05-09

Scope: additive ResearchCase metadata for Investment Platform V2. This contract does not implement SEC intake, source registry wiring, live AI, cron changes, automatic ResearchCase creation, or external source automation.

## 1. Purpose

SwissEdge is moving from a scanner-first flow into a source-driven ResearchCase pipeline:

`investment_sources -> connector / intake method -> preliminary ResearchCase -> initial course-grounded evaluation -> Research Inbox -> iterative enrichment`

The Research Inbox needs a small, durable metadata layer before SEC source-driven intake can be wired safely. These fields let the app distinguish legacy/manual cases from source-created cases, show whether official evidence exists, track methodology readiness, and prepare for duplicate handling and follow-up scheduling without changing current runtime behavior.

The metadata is intentionally additive. Existing ResearchCases remain valid with null metadata and must continue to load through the current research workspace and create-from-situation flow.

## 2. Field List

| Field | Type | Nullable | Enum values | Default | Purpose | Inbox | Set now / future |
|---|---|---:|---|---|---|---|---|
| `source_origin_name` | text | yes | none | null | Human-readable source origin, such as `SEC EDGAR`, `Manual`, or `Legacy Evaluation`. | Yes | Future intake agents; manual edit later. |
| `investment_source_id` | UUID FK to `investment_sources.id` | yes | none | null | Optional link to the operational source registry. | Yes, later as a source link/filter. | Future source-driven intake. |
| `intake_method` | string | yes | see section 3 | null | How the case entered the system. | Yes | Future intake agents; null means legacy. |
| `connector_key` | string | yes | none | null | Stable connector identifier, such as `sec_edgar_efts` or `rss_generic`. | Yes, secondary metadata. | Future connectors. |
| `intake_event_id` | string | yes | none | null | Future trace pointer to a source intake event. No intake event table is required yet. | Later | Future intake tracing. |
| `evidence_level` | string | yes | see section 3 | null | Current strength of source evidence. | Yes | Future intake/evaluation agents; fallback for legacy cases. |
| `official_source_status` | string | yes | see section 3 | null | Whether an official source is missing, needed, pending review, attached, or not applicable. | Yes | Future verification agents; fallback for legacy cases. |
| `methodology_status` | string | yes | see section 3 | null | Whether the case is grounded in the course methodology enough for evaluation. | Yes | Future methodology/evaluation agents. |
| `playbook_used` | string | yes | none | null | Identifier/name of the playbook used. Must not store raw course text. | Yes, secondary metadata. | Future methodology agent. |
| `checklist_used` | string | yes | none | null | Identifier/name of the checklist used. Must not store raw course text. | Yes, secondary metadata. | Future methodology agent. |
| `course_reference` | text | yes | none | null | Pointer to course artifact IDs, file names, sections, or structured references. Must not store raw transcripts or copyrighted course text. | Yes, secondary metadata. | Future methodology agent. |
| `duplicate_status` | string | yes | see section 3 | null | Duplicate/merge state for inbox triage. | Yes | Future duplicate and merge agent. |
| `next_follow_up_at` | datetime | yes | none | null | Next planned review/follow-up timestamp. | Yes | Future timeline/follow-up agent; manual edit later. |
| `discarded_reason` | text | yes | none | null | Human-readable reason when a case is discarded or archived. | Yes for archived/discarded views. | Future human or auditor workflows. |

All enum fields are stored as conservative string values for now. Runtime validation can be tightened later once manual editing and intake agents are designed.

## 3. Recommended Enums

`evidence_level`:

- `unknown`
- `external_unverified`
- `trusted_external`
- `official_secondary`
- `official_primary`
- `mixed`

`official_source_status`:

- `unknown`
- `official_missing`
- `official_needed`
- `official_pending_review`
- `official_attached`
- `official_not_applicable`

`methodology_status`:

- `unknown`
- `evaluator_ready`
- `partial`
- `routing_detection_only`
- `detection_only`
- `out_of_scope`
- `human_review_required`

`duplicate_status`:

- `unique`
- `possible_duplicate`
- `merged`
- `ignored_duplicate`
- `unknown`

`intake_method`:

- `legacy_manual`
- `evaluation_linked`
- `sec_edgar`
- `manual_paste`
- `telegram_manual`
- `email_forward`
- `rss_poll`
- `webhook`
- `api`
- `unknown`

## 4. Legacy Mapping

Existing ResearchCases should display safely:

- `source_origin_name = null` -> `legacy/manual`, unless linked sources or linked situation data can provide a better label.
- `intake_method = null` -> `legacy/manual` in the UI and `legacy_manual` in future normalized exports.
- Linked situation with `filing_url` or `filing_type` -> evidence can be shown as likely official filing fallback.
- Linked SEC URL or SEC filing document -> official source can be shown as likely official fallback.
- Missing `methodology_status`, `playbook_used`, `checklist_used`, and `course_reference` -> legacy/missing methodology.
- Missing `official_source_status` -> unknown.
- Missing `duplicate_status` -> no duplicate badge, treated as unknown by future audit logic.

Null means "not recorded yet", not "false" and not "not applicable".

## 5. Migration Strategy

Migration strategy is additive only:

- Add nullable columns to `research_cases`.
- Add a nullable foreign key from `research_cases.investment_source_id` to `investment_sources.id`.
- Add indexes for future inbox filters.
- Do not alter existing status or readiness enums.
- Do not backfill existing rows in the migration.
- Do not delete or rewrite existing ResearchCases.
- Do not require any field for legacy cases.

Existing ResearchCases must remain valid after the migration. Source-driven intake can populate these fields in later sprints.

## 6. API Contract

`ResearchCaseRead` should expose all V2 metadata fields as nullable values.

Current Sprint C behavior:

- Read schemas expose the metadata.
- Create-from-situation remains unchanged and leaves V2 metadata null.
- PATCH remains limited to the existing editable fields: status, notes, readiness, brief metadata, and model metadata.
- V2 metadata is read-only for now because the UI does not yet have an approved manual edit workflow.

Future PATCH support should be added only after manual editing rules, enum validation, audit history, and source registry semantics are approved.

## 7. UI Contract

Research Inbox should prefer real V2 metadata when present and use legacy fallback labels when fields are null:

- Source origin column: `source_origin_name`, else linked `ResearchSource`, else linked evaluation/filing, else `legacy/manual`.
- Intake method column: `intake_method`, else `legacy/manual`.
- Evidence column: `evidence_level`, else `official_filing` fallback for linked filings/documents, else `unknown`.
- Official source column: `official_source_status`, else `likely_official` for SEC links/documents, else `unknown`.
- Methodology column: `methodology_status`, else `partial` if playbook/checklist/course reference exists, else `legacy` for older brief/playbook version markers, else `missing`.
- Duplicate status: show a small badge only when `duplicate_status` is present.
- Follow-up: show `next_follow_up_at` when present.
- Legacy/missing V2 metadata: true only when no V2 metadata fields are populated.

The UI must not imply that source-driven intake or SEC-to-ResearchCase automation is active until those paths are actually wired.

## 8. Non-Goals

- No SEC source-driven intake.
- No scanner behavior changes.
- No `investment_sources` wiring into `/scan`.
- No automatic ResearchCase creation.
- No cron changes.
- No global evaluator v2 enablement.
- No live AI calls.
- No Catalyst, Gmail, RSS, X, webhook, or external automation.
- No market monitoring.
- No raw course transcripts or copyrighted course text stored in metadata.
- No secrets, credentials, IPs, hostnames, Tailscale details, VPS details, or raw `.env` content.

## 9. Implementation Note: Sprint E Manual Evaluation Bridge

Sprint E initializes V2 metadata in the existing manual create-from-situation flow:

`SpecialSituation / Evaluation -> manual Create ResearchCase`

When a linked `SpecialSituation` contains SEC filing metadata, the new `ResearchCase` is created with:

- `source_origin_name = "SEC EDGAR"`
- `intake_method = "evaluation_linked"`
- `connector_key = "sec_edgar_efts"`
- `evidence_level = "official_primary"`
- `official_source_status = "official_attached"`
- `duplicate_status = "unique"`

The service also attempts deterministic methodology enrichment from existing routing/playbook utilities:

- `methodology_status`
- `playbook_used`
- `checklist_used`
- `course_reference`

If methodology derivation fails, case creation still succeeds with safe `unknown`/null values.

For non-SEC linked evaluations, the case is still created with safe bridge metadata:

- `source_origin_name = "Legacy Evaluation"`
- `intake_method = "evaluation_linked"`
- `connector_key = "legacy_evaluation"`
- `evidence_level = "unknown"`
- `official_source_status = "unknown"`

Sprint E also adds initial verification/enrichment tasks and a metadata-only `ResearchSource` during manual ResearchCase creation. It does not fetch URLs.

This is not automatic scanner intake. Scanner behavior, cron, source registry wiring, evaluator defaults, live AI behavior, external automation, and deployment remain unchanged.
