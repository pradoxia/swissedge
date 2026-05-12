# Sprint ZA — Agent Rooms 2.0: Gamified Agent Operations

Date: 2026-05-12

## Goal

Expand Agent Ops from a high-level overview into navigable operational room detail pages.

## Implemented

- Added room detail route:
  - `/agent-ops/rooms/[id]`
- Updated `/agent-ops` overview:
  - room cards are clickable.
  - room cards show agent, activity, diagnostic, and proposal counts from already-loaded Agent Ops rows.
- Added room detail UI:
  - room header and guardrail status.
  - agent cards with deterministic CSS avatar placeholders.
  - selected-agent detail panel.
  - recent logs grouped by selected agent.
  - diagnostics/problems section.
  - related ResearchCase/SpecialSituation links when Agent Ops rows include related entity metadata.
  - conceptual agent interaction map.
  - derived operational indicators: Coverage XP, Signal XP, Learning XP, Reliability, Evidence Quality, Noise Penalty, and Review Discipline.

## Data Sources

Sprint ZA uses existing read-only Agent Ops endpoints:

- `GET /api/agent-ops/rooms`
- `GET /api/agent-ops/agents?room_key=...`
- `GET /api/agent-ops/activity?room_key=...`
- `GET /api/agent-ops/diagnostics?room_key=...`
- `GET /api/agent-ops/proposals?room_key=...`

No new backend endpoints were added.

## Profile Editing

Profile display-name and avatar editing is deferred.

Reason: there is no existing safe AgentProfile PATCH endpoint. Sprint ZA avoids introducing new backend mutations and keeps the room experience read-only.

The room detail page includes the note:

`Editable names and avatars planned for a future safe profile customization sprint.`

## Avatar Strategy

Agent avatars are deterministic CSS placeholders:

- initials from the agent display name.
- stable color selection derived from the agent key.
- no image fetching.
- no uploads.
- no binary assets.
- no external URLs.

## Operational Indicators

Metrics are derived in the frontend from rows already returned by Agent Ops:

- Coverage XP: activity count times 10.
- Signal XP: successful/completed activity count times 10.
- Learning XP: diagnostics plus reviewed proposal count times 10.
- Reliability: deterministic score adjusted by warning/error diagnostics and success activity.
- Evidence Quality: derived from evidence-related activity and successful activity.
- Noise Penalty: warning/error/critical diagnostics times 10.
- Review Discipline: manual-review/guardrail activity and reviewed proposals.

These are clearly labeled as read-only operational indicators. They are not persisted and are not performance guarantees.

## Guardrails

- Frontend-only Agent Ops UI change.
- No DB migration.
- No new backend writes.
- No scanner integration.
- No evaluator integration.
- No evaluator v2 global activation.
- No live AI.
- No cron changes.
- No `/api/investment/scan`.
- No automatic ResearchCase creation.
- No automatic evaluation.
- No automatic publishing.
- No recommendations.
- No Marketplace/Sales changes.
- Manual review remains mandatory.

## Validation

Commands run:

```powershell
npm run build
git diff --check
```

Result:

- Frontend build passed and includes `/agent-ops/rooms/[id]`.
- Diff check passed with line-ending warnings only.
