# SwissEdge Agent Ops Data Model Spec

This document defines the proposed Agent Ops data model for a future backend implementation. It is documentation only. No migration is implemented in this sprint.

## 1. Principles

- All tables are additive.
- No table changes scanner, evaluator, ResearchCase, source registry, cron, publishing, or deployment behavior.
- Agent Ops logging must be fail-safe and best-effort.
- Learning proposals do not auto-apply.
- Metadata and evidence fields must not store secrets, credentials, private infrastructure details, raw `.env`, DB dumps, raw course content, or copyrighted raw text.

Sprint H implementation note: core Agent Ops tables were implemented for rooms, profiles, activity, results, diagnostic events, and learning proposals. `agent_score_snapshot` remains deferred for a later scoreboard sprint.

## 2. `agent_room`

### Purpose

Stores the conceptual operating areas used by Agent Ops and Mission Control.

### Proposed Fields

| Field | Type | Required | Default | Notes |
|---|---|---:|---|---|
| `id` | UUID/string | yes | generated | Primary key. |
| `key` | string | yes | none | Unique stable key, for example `radar_room`. |
| `name` | string | yes | none | Human-readable room name. |
| `description` | text | no | null | Safe operational description. |
| `status` | string | yes | `planned` | `active`, `planned`, `paused`, `retired`. |
| `display_order` | int | yes | `100` | Mission Control ordering. |
| `created_at` | datetime | yes | now | Creation timestamp. |
| `updated_at` | datetime | yes | now | Last update timestamp. |

### Relationships

- One room has many `agent_profile` rows.
- One room may have many activities, diagnostics, proposals, and score snapshots.

### Indexes

- Unique index on `key`.
- Index on `status`.
- Index on `display_order`.

### Retention Considerations

Rooms are durable reference records. Do not delete first; retire with `status='retired'`.

### Safety Notes

Descriptions must remain operational and sanitized. Do not include production infrastructure details.

## 3. `agent_profile`

### Purpose

Defines documented or implemented agents and their room membership.

### Proposed Fields

| Field | Type | Required | Default | Notes |
|---|---|---:|---|---|
| `id` | UUID/string | yes | generated | Primary key. |
| `key` | string | yes | none | Unique stable key, for example `edgar_scout`. |
| `name` | string | yes | none | Human-readable agent name. |
| `room_id` | FK `agent_room` | yes | none | Primary room. |
| `role` | text | no | null | Agent role summary. |
| `status` | string | yes | `planned` | `planned`, `active`, `paused`, `retired`. |
| `implementation_status` | string | yes | `documented` | `documented`, `planned`, `partial`, `implemented`. |
| `autonomy_level` | string | yes | `observer` | `observer`, `manual`, `assistive`, `automated`, `prohibited`. |
| `guardrails` | text/json | no | null | Sanitized guardrail list. |
| `created_at` | datetime | yes | now | Creation timestamp. |
| `updated_at` | datetime | yes | now | Last update timestamp. |

### Relationships

- Belongs to one `agent_room`.
- May have many activities, diagnostics, proposals, and score snapshots.

### Indexes

- Unique index on `key`.
- Index on `room_id`.
- Index on `status`.
- Index on `implementation_status`.

### Retention Considerations

Retire agents rather than deleting them so reports remain explainable.

### Safety Notes

`autonomy_level='automated'` is prohibited until Dani explicitly approves an automation scope. Guardrails must not contain secrets.

## 4. `agent_activity`

### Purpose

Records observable actions, checks, summaries, or manual agent-related events.

### Proposed Fields

| Field | Type | Required | Default | Notes |
|---|---|---:|---|---|
| `id` | UUID/string | yes | generated | Primary key. |
| `agent_id` | FK `agent_profile` | no | null | Optional actor. |
| `room_id` | FK `agent_room` | no | null | Optional room. |
| `activity_type` | string | yes | none | Example: `scanner_funnel_review`, `routing_audit`, `fontana_report`. |
| `title` | string | yes | none | Short safe title. |
| `summary` | text | no | null | Sanitized summary. |
| `severity` | string | yes | `info` | `info`, `success`, `warning`, `error`, `skipped`. |
| `status` | string | yes | `completed` | `started`, `completed`, `failed`, `skipped`. |
| `related_entity_type` | string | no | null | Example: `research_case`, `investment_source`, `special_situation`. |
| `related_entity_id` | string | no | null | String reference to avoid tight coupling. |
| `metadata` | json | no | null | Sanitized structured context. |
| `created_at` | datetime | yes | now | Event timestamp. |

### Relationships

- May belong to an agent and/or room.
- Has many `agent_result` rows.

### Indexes

- Index on `created_at`.
- Index on `agent_id`.
- Index on `room_id`.
- Index on `severity`.
- Index on `status`.
- Composite index on `related_entity_type`, `related_entity_id`.

### Retention Considerations

Keep recent activity for Mission Control. Older activity can be summarized later, but deletion policy should be explicit.

### Safety Notes

Never store raw payloads that may contain secrets, raw course text, private URLs, or production logs. Store summaries and safe counts.

## 5. `agent_result`

### Purpose

Stores the outcome of an activity.

### Proposed Fields

| Field | Type | Required | Default | Notes |
|---|---|---:|---|---|
| `id` | UUID/string | yes | generated | Primary key. |
| `activity_id` | FK `agent_activity` | yes | none | Parent activity. |
| `result_type` | string | yes | none | Example: `diagnostic_summary`, `proposal_created`, `report_generated`. |
| `summary` | text | no | null | Sanitized result summary. |
| `status` | string | yes | `success` | `success`, `warning`, `error`, `skipped`. |
| `metrics` | json | no | null | Safe aggregate metrics only. |
| `created_at` | datetime | yes | now | Result timestamp. |

### Relationships

- Belongs to one `agent_activity`.

### Indexes

- Index on `activity_id`.
- Index on `status`.
- Index on `created_at`.

### Retention Considerations

Retain with parent activity. Large result details should be avoided.

### Safety Notes

Metrics must be aggregate and sanitized.

## 6. `agent_diagnostic_event`

### Purpose

Records a specific issue, warning, reliability finding, or quality signal.

### Proposed Fields

| Field | Type | Required | Default | Notes |
|---|---|---:|---|---|
| `id` | UUID/string | yes | generated | Primary key. |
| `agent_id` | FK `agent_profile` | no | null | Optional diagnosing agent. |
| `room_id` | FK `agent_room` | no | null | Optional room. |
| `severity` | string | yes | `info` | `info`, `success`, `warning`, `error`, `skipped`. |
| `diagnostic_type` | string | yes | none | Example: `missing_methodology`, `source_no_connector`, `routing_weak_pattern`. |
| `title` | string | yes | none | Short finding title. |
| `description` | text | no | null | Sanitized detail. |
| `evidence` | json | no | null | Safe counts, IDs, or labels only. |
| `related_entity_type` | string | no | null | Optional entity type. |
| `related_entity_id` | string | no | null | Optional entity id. |
| `created_at` | datetime | yes | now | Diagnostic timestamp. |

### Relationships

- May create or support `agent_learning_proposal`.

### Indexes

- Index on `created_at`.
- Index on `diagnostic_type`.
- Index on `severity`.
- Composite index on `related_entity_type`, `related_entity_id`.

### Retention Considerations

Diagnostics should remain available for trend analysis. Summarization can be added later.

### Safety Notes

Evidence JSON must not contain full documents, raw logs, secrets, or raw course text.

## 7. `agent_learning_proposal`

### Purpose

Stores improvement recommendations that require human approval before implementation.

### Proposed Fields

| Field | Type | Required | Default | Notes |
|---|---|---:|---|---|
| `id` | UUID/string | yes | generated | Primary key. |
| `source_diagnostic_id` | FK `agent_diagnostic_event` | no | null | Origin diagnostic. |
| `agent_id` | FK `agent_profile` | no | null | Proposing agent. |
| `room_id` | FK `agent_room` | no | null | Related room. |
| `title` | string | yes | none | Short proposal title. |
| `problem_statement` | text | yes | none | What is wrong or incomplete. |
| `proposed_change` | text | yes | none | Proposed implementation or doc change. |
| `expected_benefit` | text | no | null | Why it helps. |
| `risk_level` | string | yes | `medium` | `low`, `medium`, `high`. |
| `status` | string | yes | `proposed` | `proposed`, `accepted`, `rejected`, `deferred`, `implemented`, `archived`. |
| `reviewer_note` | text | no | null | Human review note. |
| `reviewed_by` | string | no | null | Reviewer identity if available. |
| `reviewed_at` | datetime | no | null | Review timestamp. |
| `created_at` | datetime | yes | now | Creation timestamp. |
| `updated_at` | datetime | yes | now | Last update timestamp. |

### Relationships

- May originate from one diagnostic.
- May belong to one agent and/or room.

### Indexes

- Index on `status`.
- Index on `risk_level`.
- Index on `created_at`.
- Index on `room_id`.
- Index on `agent_id`.

### Retention Considerations

Keep rejected and archived proposals for institutional memory.

### Safety Notes

Proposal acceptance never applies the change automatically. Implementation remains Dani approval -> Codex work -> optional Claude review -> manual deploy.

## 8. `agent_score_snapshot` Optional/Future

### Purpose

Stores periodic score snapshots for rooms or agents. This is optional and should come after activity and diagnostics are stable.

### Proposed Fields

| Field | Type | Required | Default | Notes |
|---|---|---:|---|---|
| `id` | UUID/string | yes | generated | Primary key. |
| `agent_id` | FK `agent_profile` | no | null | Agent score scope. |
| `room_id` | FK `agent_room` | no | null | Room score scope. |
| `coverage_xp` | int | yes | `0` | Coverage progress metric. |
| `signal_xp` | int | yes | `0` | Useful signal metric. |
| `learning_xp` | int | yes | `0` | Proposal/learning metric. |
| `reliability_score` | float | no | null | 0-100 score. |
| `evidence_quality_score` | float | no | null | 0-100 score. |
| `noise_penalty` | int | yes | `0` | Penalty points for noise or recurring false positives. |
| `period_start` | datetime | yes | none | Scoring window start. |
| `period_end` | datetime | yes | none | Scoring window end. |
| `created_at` | datetime | yes | now | Snapshot timestamp. |

### Relationships

- Applies to either an agent, a room, or both.

### Indexes

- Index on `period_start`, `period_end`.
- Index on `agent_id`.
- Index on `room_id`.

### Retention Considerations

Keep snapshots for trend views. Downsample later if needed.

### Safety Notes

Scores must be explainable and operationally useful, not decorative gamification.
