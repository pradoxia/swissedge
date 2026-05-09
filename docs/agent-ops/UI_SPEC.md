# SwissEdge Agent Ops UI Spec

Future route: `/agent-ops`

This is the Mission Control surface for Agent Ops and Fontana. It should feel like a serious operations center: calm, institutional, readable, and consistent with the improved Research Inbox direction. Avoid cyberpunk styling, childish gamification, crypto/trading hype, and decorative noise.

## 1. Global UI Guardrails

- Read-only by default.
- Mutating controls limited initially to learning proposal review.
- No scan trigger.
- No cron controls.
- No evaluator v2 global control.
- No deploy control.
- No live AI trigger unless a future sprint explicitly adds a manual, confirmed action.
- Show warnings when data is incomplete or observational only.

## 2. Rooms Tab

### Purpose

Show room health and operational scope.

### Data Needed

Rooms, room status, agent count, diagnostics count, open proposals, and summary metrics.

### Components

- Room summary cards.
- Room detail table.
- Health badges.
- Guardrail note per room.

### Empty States

- No rooms documented yet.
- No diagnostics recorded yet.

### Warning States

- Room documented but no agents.
- Room active but no recent activity.

### Read-Only vs Mutating

Read-only.

### Future Enhancements

Room drill-down with trends and related cases/sources.

## 3. Agents Tab

### Purpose

Show agent definitions, implementation status, autonomy level, and guardrails.

### Data Needed

Agent profiles, room membership, implementation status, autonomy level, guardrails, recent activity.

### Components

- Agent table.
- Status filters.
- Autonomy badges.
- Guardrail panel.

### Empty States

- No agents documented.

### Warning States

- Agent marked active without implementation mapping.
- Agent autonomy level unclear.

### Read-Only vs Mutating

Read-only.

### Future Enhancements

Agent profile detail view and activity history.

## 4. Activity Feed Tab

### Purpose

Show chronological operational activity across rooms and agents.

### Data Needed

Agent activity records, result summaries, severity, status, related entity references.

### Components

- Filterable activity list.
- Severity/status chips.
- Related entity links where safe.

### Empty States

- No activity recorded yet.

### Warning States

- Recent failed activities.
- Repeated skipped diagnostics.

### Read-Only vs Mutating

Read-only.

### Future Enhancements

Saved filters and activity export for internal review.

## 5. Diagnostics Tab

### Purpose

Show reliability, evidence, source, routing, methodology, and workflow diagnostics.

### Data Needed

Diagnostic events, severity, diagnostic type, related entity references, safe evidence payloads.

### Components

- Diagnostic table.
- Severity filters.
- Diagnostic type filters.
- Entity links.

### Empty States

- No diagnostics recorded yet.

### Warning States

- High severity diagnostics.
- Missing evidence or methodology.
- Scanner/source mismatch.

### Read-Only vs Mutating

Read-only.

### Future Enhancements

Create learning proposal from diagnostic after explicit approval.

## 6. Routing Audits Tab

### Purpose

Explain deterministic routing decisions and identify weak patterns.

### Data Needed

Candidate routes, chosen route, scoring reasons, evidence, playbook version, methodology status, safety flags, false positive/negative labels.

### Components

- Routing audit list.
- Candidate route comparison.
- Methodology status badges.
- Weak-pattern warnings.

### Empty States

- No routing audits recorded.

### Warning States

- Detection-only route shown as evaluator-ready.
- Missing playbook version.
- Repeated false positives or false negatives.

### Read-Only vs Mutating

Read-only.

### Future Enhancements

Proposal creation for routing improvement.

## 7. Learning Proposals Tab

### Purpose

Review human-supervised improvement proposals.

### Data Needed

Proposal records, status, risk level, problem statement, proposed change, expected benefit, reviewer note.

### Components

- Proposal table.
- Status filters.
- Proposal detail drawer.
- Review controls for allowed status transitions.

### Empty States

- No proposals yet.

### Warning States

- High-risk proposal.
- Accepted proposal not implemented.
- Stale deferred proposal.

### Read-Only vs Mutating

Only this tab has initial mutation: proposal status/reviewer note updates. It must not apply proposals.

### Future Enhancements

Link accepted proposals to Codex sprint docs or ADRs.

## 8. Scoreboard Tab

### Purpose

Show operational metrics without turning them into vanity gamification.

### Data Needed

Coverage XP, Signal XP, Learning XP, Reliability Score, Evidence Quality, Noise Penalty by source, agent, room, case, and route.

### Components

- Compact score cards.
- Trend table.
- Caveat notes.
- Drill-down links.

### Empty States

- No score snapshots yet.

### Warning States

- High noise penalty.
- Reliability score unknown due to missing data.

### Read-Only vs Mutating

Read-only.

### Future Enhancements

Time window comparison and explanation tooltips.

## 9. Fontana Reports Tab

### Purpose

Display Fontana CTO reports and strategic continuity notes.

### Data Needed

Report title, created date, current state, recently completed, active risks, architecture concerns, diagnostics, proposed improvements, next steps, deferred decisions, and things not to touch yet.

### Components

- Report list.
- Report reader.
- Risk/next-step summary.

### Empty States

- No Fontana reports generated yet.

### Warning States

- Report stale.
- Active risks unresolved.

### Read-Only vs Mutating

Read-only initially.

### Future Enhancements

Manual report generation after explicit approval; ADR proposal links.
