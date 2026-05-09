# SwissEdge Research Inbox Specification

Date: 2026-05-09

Status: future implementation specification. No implementation is included in this sprint.

Implementation Sprint B note (2026-05-09): first read-only frontend route `/investment/research-inbox` implemented locally. It uses existing `GET /api/investment/research-cases` plus existing situations data for linked-evaluation labels. No backend endpoint, DB migration, source-driven intake, scanner trigger, live AI call, cron change, or mutating inbox action was added.

## 1. Purpose

The Research Inbox is the main operating queue for Investment Platform V2. It shows preliminary ResearchCases created from source intake, not just evaluated scanner rows.

Its job is to help Dani answer:

- What new cases entered the research desk?
- Where did each case come from?
- Is the evidence official or external/unverified?
- Which methodology applies?
- What is missing before deep research?
- Which cases are duplicates, stale, or ready to investigate?

## 2. Difference from Evaluations Queue

The current Evaluations Queue is based on `SpecialSituation` rows. It is useful for scanner output, but it is not the durable research work queue.

Research Inbox differences:

| Evaluations Queue | Research Inbox |
|---|---|
| Centers `SpecialSituation`. | Centers `ResearchCase`. |
| Shows evaluated signals. | Shows source-originated research candidates. |
| Mostly SEC scanner oriented. | Source-registry oriented. |
| Statuses are detection workflow statuses. | Buckets are research-workflow and evidence statuses. |
| ResearchCase is created manually later. | Preliminary ResearchCase is created early. |
| Limited source provenance. | Source origin and intake method are first-class. |

The Evaluations Queue should remain during migration as a legacy/signal view.

## 3. ResearchCase Intake Buckets

Initial buckets:

- New intake: preliminary case created, not yet reviewed.
- Initial evaluated: initial methodology/evaluation attached.
- Needs official source: originated from an external or manual source and lacks primary evidence.
- Needs enrichment: needs tasks, documents, source notes, or methodology details.
- Ready for deep research: evidence and methodology are sufficient for deeper work.
- Monitoring: case is active but waiting for future event/date/filing.
- Documented: research brief is sufficiently complete.
- Archived/discarded: no longer active, with reason.

## 4. Required Case Metadata

Minimum metadata for a V2 inbox row:

- `research_case_id`
- `case_title` or generated display title
- `company_name` if known
- `ticker` if known
- `situation_type_guess`
- `source_origin_name`
- `investment_source_id`
- `source_type`
- `intake_method`
- `connector_key`
- `intake_event_id` or diagnostic trace ID
- `evidence_level`
- `official_source_status`
- `methodology_status`
- `playbook_used`
- `checklist_used`
- `course_reference`
- `investment_readiness`
- `open_task_count`
- `document_count`
- `source_count`
- `duplicate_status`
- `last_intake_at`
- `updated_at`
- `next_follow_up_at`
- `disclaimer_present`

## 5. Columns

Recommended first table columns:

- Case
- Company / ticker
- Situation type
- Source
- Intake method
- Evidence
- Official source
- Methodology
- Readiness
- Tasks
- Docs
- Sources
- Duplicate
- Updated
- Next follow-up
- Actions

Column behavior:

- Case links to `/investment/research/[id]`.
- Source links to `/investment/sources` filtered by source when available.
- Evidence and methodology should be compact badges.
- Tasks/docs/sources should show counts and warnings.
- Duplicate status should show `unique`, `possible_duplicate`, or `merged`.

## 6. Filters

Required filters:

- Bucket
- Source type
- Source name
- Intake method
- Situation type
- Evidence level
- Official-source status
- Methodology status
- Readiness
- Duplicate status
- Has open tasks
- Has no documents
- Has no sources
- Age/staleness

Useful future filters:

- SEC form type
- Connector key
- Playbook
- Reliability
- Follow-up date
- Created by source vs manual

## 7. Actions

First implementation actions:

- Open ResearchCase.
- Mark reviewed.
- Add verification task.
- Add document metadata.
- Add source reference.
- Mark needs official source.
- Mark ready for deep research.
- Archive/discard with reason.

Later actions:

- Run initial evaluation preview.
- Run quality preview.
- Run source intelligence preview.
- Resolve duplicate/merge.
- Create private public draft after documented state.

No action should trigger publication, external posting, scanner changes, cron changes, or v2 global enablement.

## 8. Detail View Additions

Add to ResearchCase detail:

- Intake origin panel.
- Source registry link.
- Intake method and connector key.
- Evidence level.
- Official-source status.
- Methodology status.
- Playbook/checklist/course reference summary.
- Duplicate warning panel.
- Staleness/follow-up panel.
- Initial evaluation panel separate from full brief.
- Official source verification checklist.

These should be additive and not remove existing tasks, documents, sources, brief, quality assist, document intelligence, source intelligence, or public draft panels.

## 9. Duplicate / Merge Handling

Duplicate states:

- `unique`
- `possible_duplicate`
- `merged`
- `ignored_duplicate`

Duplicate signals:

- Same filing URL.
- Same accession number.
- Same company and situation type within a short time window.
- Same external URL.
- Same source-origin event.
- Same manually supplied title/URL.

First implementation:

- Detect possible duplicates and show warnings.
- Do not auto-merge.
- Allow Dani to open both cases.

Later implementation:

- Merge tasks, documents, and sources into a canonical ResearchCase.
- Preserve intake event history.
- Mark duplicates as merged rather than deleting.

## 10. Official Source Verification Workflow

Official-source statuses:

- `official_attached`
- `official_needed`
- `official_not_applicable`
- `official_pending_review`
- `official_missing`

Rules:

- SEC filings are official primary evidence for SEC-sourced cases.
- Company IR, regulator, court, exchange, and official press release sources may qualify depending on situation type.
- X accounts, newsletters, news, emails, and manual Telegram notes are external signals, not official proof.
- External-source cases should automatically receive a task to attach or identify official evidence.

## 11. Course Methodology Indicators

Methodology statuses:

- `evaluator_ready`
- `partial`
- `routing_detection_only`
- `detection_only`
- `out_of_scope`
- `unknown`

Indicators:

- Playbook used.
- Checklist used.
- Course reference available.
- Missing methodology.
- Human review required.
- Prohibited inference guard status.

The inbox must make it obvious when a case is detection-only or out of scope.

## 12. Source Quality Indicators

Source quality signals:

- Source reliability: `official`, `high`, `medium`, `low`, `experimental`.
- Case signal quality: `high`, `medium`, `low`, `no_signal`.
- Intake method confidence.
- Last successful intake.
- Source error status.
- Historical usefulness from Source Intelligence.

Source quality should inform triage priority, not produce final recommendations.

## 13. Empty States

Research Inbox empty states:

- No ResearchCases: "No research cases yet. Create one from a source intake or existing evaluation."
- No new intake: "No new intake items. Check Radar Status for source health."
- No official-source cases: "No cases with official evidence attached."
- Filtered empty: "No cases match these filters. Clear filters or check archived/discarded."
- Source-driven intake unavailable: "Source-driven intake is not wired yet. Current ResearchCases may still come from evaluations."

## 14. Acceptance Criteria for First Implementation

First implementation should be read-only or minimally mutating.

Acceptance criteria:

- `/investment/research-inbox` exists.
- It lists existing ResearchCases without breaking `/investment/research`.
- It clearly labels cases with missing V2 metadata as `legacy/manual`.
- It shows bucket, readiness, task count, document count, source count, updated date, and situation link when present.
- It does not claim that source-driven intake is active until it is.
- It links to ResearchCase detail.
- It has filters for status/readiness/source availability.
- It includes empty states.
- It requires no DB migration if implemented before V2 metadata fields.
- It triggers no scan, no live AI, no cron, no deploy behavior, and no publishing.

## 15. Implementation Note: Sprint C V2 Metadata Contract

Sprint C adds the additive V2 ResearchCase metadata contract and prepares nullable metadata fields for the Research Inbox.

The Inbox should now prefer real metadata when present:

- `source_origin_name`
- `investment_source_id`
- `intake_method`
- `connector_key`
- `intake_event_id`
- `evidence_level`
- `official_source_status`
- `methodology_status`
- `playbook_used`
- `checklist_used`
- `course_reference`
- `duplicate_status`
- `next_follow_up_at`
- `discarded_reason`

Legacy cases with null V2 metadata remain valid and should continue to display as legacy/manual or unknown using the fallback rules in `docs/investment/V2_RESEARCHCASE_METADATA_CONTRACT.md`.

Sprint C does not wire source-driven intake, trigger scans, create ResearchCases automatically, change cron, enable evaluator v2 globally, or add external automation.
