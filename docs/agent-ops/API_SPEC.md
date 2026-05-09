# SwissEdge Agent Ops API Spec

This document defines the initial Agent Ops API. It is documentation only. The implementation must follow the same private Mission Control auth/access model as the rest of the private app.

## 1. API Principles

- GET endpoints are read-only.
- PATCH proposals only changes proposal review state and reviewer notes.
- No endpoint triggers scans.
- No endpoint changes cron.
- No endpoint enables evaluator v2.
- No endpoint deploys.
- No endpoint applies learning proposals automatically.
- Responses must not include secrets, credentials, private infrastructure details, raw logs, raw course text, or copyrighted raw content.

## 2. `GET /api/agent-ops/rooms`

### Purpose

Return Agent Ops room definitions and summary metrics.

### Query Params

- `status`: optional filter, for example `active`, `planned`, `paused`, `retired`.
- `include_metrics`: optional boolean, default `true`.

### Response Shape

```json
{
  "rooms": [
    {
      "id": "room-id",
      "key": "radar_room",
      "name": "Radar Room",
      "description": "Detection and scanner diagnostics.",
      "status": "active",
      "display_order": 10,
      "metrics": {
        "activity_count_7d": 0,
        "warning_count_7d": 0,
        "open_proposals": 0
      }
    }
  ]
}
```

### Error Cases

- `401/403`: not authorized.
- `500`: unexpected server error.

### Guardrails

Read-only. Must not trigger diagnostics generation as a side effect.

### Mutation Behavior

None.

## 3. `GET /api/agent-ops/agents`

### Purpose

Return Agent Ops agent profiles and implementation status.

### Query Params

- `room_key`: optional room filter.
- `status`: optional agent status filter.
- `implementation_status`: optional implementation status filter.

### Response Shape

```json
{
  "agents": [
    {
      "id": "agent-id",
      "key": "edgar_scout",
      "name": "Edgar Scout",
      "room_key": "radar_room",
      "role": "SEC EDGAR signal and scanner health observer.",
      "status": "planned",
      "implementation_status": "documented",
      "autonomy_level": "observer",
      "guardrails": ["no scan trigger", "no cron change"]
    }
  ]
}
```

### Error Cases

- `401/403`: not authorized.
- `500`: unexpected server error.

### Guardrails

Read-only. Agent status display must not imply autonomy.

### Mutation Behavior

None.

## 4. `GET /api/agent-ops/activity`

### Purpose

Return activity feed records for rooms, agents, and related entities.

### Query Params

- `room_key`: optional.
- `agent_key`: optional.
- `severity`: optional.
- `status`: optional.
- `related_entity_type`: optional.
- `related_entity_id`: optional.
- `limit`: optional, default `50`, max to be defined by implementation.
- `cursor`: optional pagination cursor.

### Response Shape

```json
{
  "items": [
    {
      "id": "activity-id",
      "room_key": "radar_room",
      "agent_key": "edgar_scout",
      "activity_type": "scanner_funnel_review",
      "title": "SEC scan produced no created cases",
      "summary": "Zero created cases; duplicate and unclassified counts need review.",
      "severity": "warning",
      "status": "completed",
      "related_entity_type": null,
      "related_entity_id": null,
      "created_at": "2026-05-09T00:00:00Z"
    }
  ],
  "next_cursor": null
}
```

### Error Cases

- `400`: invalid filter.
- `401/403`: not authorized.
- `500`: unexpected server error.

### Guardrails

Read-only. Must not run new activities.

### Mutation Behavior

None.

## 5. `GET /api/agent-ops/diagnostics`

### Purpose

Return diagnostic events for reliability, quality, routing, source, and evidence issues.

### Query Params

- `room_key`: optional.
- `agent_key`: optional.
- `severity`: optional.
- `diagnostic_type`: optional.
- `related_entity_type`: optional.
- `related_entity_id`: optional.
- `limit`: optional, default `50`.
- `cursor`: optional.

### Response Shape

```json
{
  "items": [
    {
      "id": "diagnostic-id",
      "room_key": "quality_court",
      "agent_key": "quality_sentinel",
      "severity": "warning",
      "diagnostic_type": "missing_methodology",
      "title": "ResearchCase missing methodology status",
      "description": "Case has no V2 methodology metadata.",
      "evidence": {
        "case_id": "case-id"
      },
      "related_entity_type": "research_case",
      "related_entity_id": "case-id",
      "created_at": "2026-05-09T00:00:00Z"
    }
  ],
  "next_cursor": null
}
```

### Error Cases

- `400`: invalid filter.
- `401/403`: not authorized.
- `500`: unexpected server error.

### Guardrails

Read-only. Evidence payloads must be sanitized.

### Mutation Behavior

None.

## 6. `GET /api/agent-ops/proposals`

### Purpose

Return learning proposals awaiting or recording human review.

### Query Params

- `status`: optional.
- `risk_level`: optional.
- `room_key`: optional.
- `agent_key`: optional.
- `limit`: optional, default `50`.
- `cursor`: optional.

### Response Shape

```json
{
  "items": [
    {
      "id": "proposal-id",
      "title": "Add scanner duplicate count to Radar Status",
      "problem_statement": "Empty scans are hard to interpret.",
      "proposed_change": "Display duplicate count from scanner funnel diagnostics.",
      "expected_benefit": "Improves operational clarity.",
      "risk_level": "low",
      "status": "proposed",
      "reviewer_note": null,
      "reviewed_by": null,
      "reviewed_at": null,
      "created_at": "2026-05-09T00:00:00Z",
      "updated_at": "2026-05-09T00:00:00Z"
    }
  ],
  "next_cursor": null
}
```

### Error Cases

- `400`: invalid filter.
- `401/403`: not authorized.
- `500`: unexpected server error.

### Guardrails

Read-only. Listing proposals must not apply them.

### Mutation Behavior

None.

## 7. `PATCH /api/agent-ops/proposals/{id}`

### Purpose

Update proposal review status and reviewer note only.

### Request Body

```json
{
  "status": "accepted",
  "reviewer_note": "Approved for a future Codex sprint."
}
```

### Allowed Updates

- Update `status`.
- Add or replace `reviewer_note`.
- Set `reviewed_at` server-side when review status changes.
- Set `reviewed_by` if the private auth model exposes the current user safely.

### Allowed Status Transitions

- `proposed -> accepted`
- `proposed -> rejected`
- `proposed -> deferred`
- `accepted -> implemented`
- `deferred -> proposed`
- `deferred -> rejected`
- any non-archived status -> `archived`

### Not Allowed

- Auto-apply proposal.
- Run code.
- Deploy.
- Change scanner.
- Change evaluator.
- Change cron.
- Call live AI.
- Modify source registry behavior.

### Response Shape

```json
{
  "proposal": {
    "id": "proposal-id",
    "status": "accepted",
    "reviewer_note": "Approved for a future Codex sprint.",
    "reviewed_by": "private-user",
    "reviewed_at": "2026-05-09T00:00:00Z",
    "updated_at": "2026-05-09T00:00:00Z"
  }
}
```

### Error Cases

- `400`: invalid status or invalid transition.
- `401/403`: not authorized.
- `404`: proposal not found.
- `409`: proposal already archived or transition conflict.
- `500`: unexpected server error.

### Guardrails

This endpoint is the only initial mutating Agent Ops endpoint. It must mutate review metadata only.

### Mutation Behavior

Human review metadata only. No operational side effects.
