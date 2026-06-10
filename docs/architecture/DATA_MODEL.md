---
document_id: DATA_MODEL
title: Data Model
version: 0.2.3
status: active
owner: Dani
last_updated: 2026-06-10
source_of_truth: true
review_cycle: manual
---

# SwissEdge Data Model

Date: 2026-06-10

## Existing Core Entities

### SpecialSituation

Implemented in `backend/models/investment.py`.

Purpose: detection and triage object for special situation candidates.

Key fields: `id`, `situation_type`, `company_name`, `ticker`, `filing_type`, `filing_url`, `detected_at`, `status`, `evaluation`, `notes`, `created_at`, `updated_at`.

### ResearchCase

Implemented in `backend/models/investment_research.py`.

Purpose: durable deeper research object after manual promotion or intake.

Key fields: `id`, `situation_id`, `status`, `brief`, `notes`, `investment_readiness`, source/intake metadata, evidence/methodology fields, `created_at`, `updated_at`.

Child entities: `ResearchTask`, `ResearchDocument`, `ResearchSource`.

### ResearchDocument

Implemented in `backend/models/investment_research.py`.

Purpose: document metadata and, after M1, manually acquired SEC document body text for later human review and gated analysis.

Key metadata fields: `id`, `research_case_id`, `historical_case_id`, `doc_type`, `url`, `title`, `retrieved_at`, `summary`, `added_by`, `created_at`.

M1 body text fields:

- `body_text`: nullable full extracted SEC body text.
- `body_text_excerpt`: nullable safe excerpt for UI/status display.
- `body_text_sha256`: nullable SHA-256 hash of stored body text.
- `body_text_acquired_at`: nullable acquisition timestamp.
- `body_text_status`: nullable safe status such as `requested`, `acquired`, `skipped_invalid_url`, `skipped_too_large`, `failed_fetch`, `failed_parse`, or `failed_persist`.
- `body_text_error`: nullable safe error message; must not contain full document text.
- `body_text_size_bytes`: nullable response size metadata.

Boundary: M1 body text acquisition is SEC-only, manual, and does not verify evidence, promote/reject cases, publish, activate live AI, or run scans/cron.

### PriceSnapshot

Implemented in `backend/models/investment.py`.

Purpose: cached market price metadata from a future approved price provider or from M4B manual Research Inbox entry. Provider selection is pending, and no production price refresh cron is installed.

Key fields: `id`, `ticker`, `provider`, `latest_close_price`, `close_date`, `currency`, `market_cap`, `average_daily_volume`, `fetched_at`, `safe_metadata`, `created_at`, `updated_at`.

### CasePriceContext

Implemented in `backend/models/investment.py`.

Purpose: cached workflow/prioritization context for a `SpecialSituation` or `ResearchCase`.

Key fields: `id`, `special_situation_id`, `research_case_id`, `ticker`, `offer_price`, `offer_price_source`, `price_snapshot_id`, `latest_close_price`, `latest_close_date`, `estimated_spread_pct`, `spread_status`, `status_reason`, `created_at`, `updated_at`.

Safe statuses: `available`, `missing_offer_price`, `missing_market_price`, `stale_price`, `not_applicable`.

Boundary: price context is not investment advice, does not verify candidate-only situations, and must not auto-promote, reject, discard, archive, publish, analyze, or decide cases. M4B uses the existing M4A tables and adds no migration; production M4A migration still requires Dani approval.

### DecisionRecord

Implemented in `backend/models/investment.py`.

Purpose: auditable manual human decision record for a `SpecialSituation` or `ResearchCase`.

Key fields: `id`, `special_situation_id`, `research_case_id`, `outcome`, `reason`, `author`, `source_surface`, `safe_metadata`, `created_at`, `updated_at`.

Allowed outcomes: `CANDIDATE`, `WATCHLIST`, `REJECT`, `NEED_MORE_EVIDENCE`.

Boundary: exactly one target is required. Every record requires reason and author. Decision records are workflow/audit context only and must not auto-promote, reject, discard, archive, publish, analyze, decide, verify evidence, acquire documents, or hide queue items. Migration file created but not applied; production migration requires Dani approval.

### AgentRoom

Equivalent implemented as `AgentRoom` in `backend/models/agent_ops.py`.

Current fields: `id`, `key`, `name`, `description`, `status`, `display_order`, `created_at`, `updated_at`.

Proposed alignment: treat `key` as `slug`; add/document `purpose`, `is_active`, and stable room ordering if needed.

### AgentProfile

Equivalent implemented as `AgentProfile` in `backend/models/agent_ops.py`.

Current fields: `id`, `key`, `name`, `room_id`, `role`, `status`, `implementation_status`, `autonomy_level`, `guardrails`, `created_at`, `updated_at`.

Proposed alignment: treat `key` as `slug`; add/document `display_name`, `description`, `run_mode`, `cadence_cron`, `next_run_at`, `last_run_at`, `permissions`, `forbidden_actions`, and `endpoint` if persistence is approved.

### AgentSkill

Not implemented as a dedicated table.

Proposed fields: `id`, `agent_slug` or `agent_id`, `skill_label`, `description`, `proficiency_level`, `is_editable`, `created_at`, `updated_at`.

Current safe implementation: document skills in `docs/agents/` and code registries. Do not add a migration until an approved implementation sprint.

### AgentActivity

Implemented in `backend/models/agent_ops.py`.

Current fields: `id`, `agent_id`, `room_id`, `activity_type`, `title`, `summary`, `severity`, `status`, `related_entity_type`, `related_entity_id`, `metadata_json`, `created_at`.

Proposed alignment: `summary` covers description; retain `metadata_json`.

### AgentRun

Implemented in `backend/models/observability.py`.

Current fields: `id`, `agent_name`, `agent_type`, `module`, `runtime`, `trigger_source`, `task_name`, `input_summary`, `output_summary`, `status`, `started_at`, `finished_at`, token/cost fields, touched/called/created JSON, error/outcome fields, approval flags, timestamps.

Proposed alignment: `agent_name` can map to `agent_slug`; `finished_at` covers completed time; `trigger_source` covers trigger type.

### AgentFinding

Not implemented as a dedicated table.

Proposed fields: `id`, `agent_slug` or `agent_id`, `run_id`, `severity`, `title`, `description`, `area`, `owner_hint`, `related_entity_type`, `related_entity_id`, `created_at`.

Current safe implementation: findings are returned as report payloads and may be summarized in `AgentActivity` or `AgentRun` output.

### AgentRecommendation

Partially represented by `AgentLearningProposal` in `backend/models/agent_ops.py`.

Proposed fields: `id`, `agent_slug` or `agent_id`, `run_id`, `order`, `title`, `description`, `owner`, `status`, `requires_approval`, `created_at`, `updated_at`.

Current reuse: use `AgentLearningProposal` for approval-required proposals; do not duplicate until persistence model is approved.

### DocumentPackage

Implemented as service/Pydantic package, not a primary DB table. See `backend/services/investment/document_package.py` and frontend panels.

Purpose: derived package of required/found/suggested/missing documents.

### EvidencePacket

Implemented as derived evidence link packages rather than a primary DB table. See `backend/services/investment/evidence_links.py`.

Purpose: provenance, official links, candidate links, metadata-only warnings, and checklist/resource links.

### StudyGuideMapping

Implemented as static/frontend/backend mapping metadata rather than a DB table.

Files: `frontend/app/components/studyGuideMapping.ts`, `backend/services/investment/course_documentation_map.py`, `docs/COURSE_DOCUMENTATION_MAP.md`.

## Deferred Schema Work

Future safe schema candidates:

- `AgentSkill`
- `AgentFinding`
- `AgentRecommendation` alignment or extension of `AgentLearningProposal`
- Persisted governance report snapshots
- Explicit `purpose`/`is_active` fields for rooms
- Persistent cadence/endpoint fields for agent profiles

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.2.3 | 2026-06-10 | Codex | Documented M4B manual price context activation using existing M4A tables. |
| 0.2.2 | 2026-06-10 | Codex | Documented M3B `DecisionRecord` model and no-side-effect decision boundary. |
| 0.2.0 | 2026-06-10 | Codex | Documented M1 nullable `ResearchDocument` body text fields, status vocabulary, and SEC-only manual acquisition boundary. |
| 0.1.0 | 2026-06-08 | Codex | Initial official version with agent-doc reference alignment. |
