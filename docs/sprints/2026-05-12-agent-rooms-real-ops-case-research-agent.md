# Sprint AD — Agent Rooms Real Ops + Case Research Agent

## Summary

Sprint AD upgrades Agent Ops into a stronger read-only operational control-room experience.

It makes rooms and agents feel more real and useful without adding autonomous execution. Agent identities now include mission, input signals, output artifacts, scheduler posture, current mode, future mode, related case counts, problem counts, and derived operational indicators.

## Implemented

- Upgraded `/agent-ops` overview:
  - room cards now show operational score, current mode, scheduler posture, and future-approval posture
  - added a stronger Research Agent Network panel
  - added deterministic identity metadata for key research agents
  - added XP indicators derived from loaded Agent Ops rows
  - highlighted Missing Evidence Hunter as the case research agent
- Upgraded `/agent-ops/rooms/[id]`:
  - room header now shows current mode, scheduler posture, and guardrail status
  - interaction map uses richer room chains
  - agent roster cards show mission, watches, outputs, mode, scheduler posture, case rows, diagnostics, and XP
  - selected agent detail shows mission, input signals, output artifacts, scheduler posture, latest logs, related cases, diagnostics, and next manual actions where derivable
- Kept rename/avatar editing deferred:
  - no safe profile customization endpoint is added in this sprint
  - UI clearly states editing is planned for a future safe sprint

## Agent Identities

Sprint AD strengthens frontend identity metadata for:

- Edgar Scout
- Router Analyst
- Resource Scout
- Evidence Mapper
- Missing Evidence Hunter
- Quality Sentinel
- Intelligence Scorer
- Playbook Scribe
- Fontana

## Missing Evidence Hunter

Missing Evidence Hunter is now treated visually as the case research agent.

It watches:

- missing required resources
- missing checklist evidence
- candidate-only resources
- rejected/noisy sources
- cases with no SEC filing URL
- low documentation quality
- low Intelligence Score

It outputs:

- missing evidence list
- manual search plan
- documentation gaps
- suggested next manual actions

Current mode remains manual / observer-only.

## Guardrails Confirmed

- No cron changes.
- No scheduler execution.
- No live AI.
- No scanner call.
- No evaluator call.
- No `/api/investment/scan` call.
- No backend mutation added.
- No DB migration.
- No automatic evaluation.
- No automatic ResearchCase creation.
- No automatic promotion.
- No publishing.
- No public draft creation.
- No crawling.
- No PDF download.
- No SEC document body fetching.
- No external HTTP calls.
- No Marketplace/Sales changes.
- No auto-deploy.

## Notes

Derived operational indicators are read-only and frontend-derived. They are not persisted metrics and should not be interpreted as performance guarantees.

Case linkage becomes richer only when more observer logs include `related_entity_type` and `related_entity_id`.

## Review Posture

Sprint AD is the third sprint in the AB/AC/AD batch.

Do not deploy after this sprint. The batch requires ClaudeCode review and Dani deployment approval.
