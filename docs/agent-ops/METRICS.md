# SwissEdge Agent Ops Metrics Spec

Agent Ops metrics must be operationally useful. They are not decorative gamification and should not create incentives to generate noisy activity.

## 1. Coverage XP

### Purpose

Measures how much of a room, source, route, or case universe is covered by observable diagnostics.

### What Increases It

- Source has connector status tracked.
- Scanner funnel has raw/parsed/classified/skipped/created counts.
- ResearchCases have V2 metadata, tasks, sources, and evidence status.
- Routing decisions include audit reasons.

### What Decreases It

- Missing diagnostics.
- Unknown source status.
- Cases with null metadata.
- Routes with no explainability.

### Example Formula

`coverage_xp = completed_coverage_checks * 10 - missing_required_checks * 5`

### What Good Looks Like

High coverage with few unknown fields and clear operational explanations.

### What Bad Looks Like

Many active sources or cases but no diagnostics explaining current status.

### Caveats

Coverage does not equal correctness.

### Mission Control Placement

Room cards, source detail, ResearchCase health, and routing audit summaries.

## 2. Signal XP

### Purpose

Measures useful signal production relative to noise.

### What Increases It

- Candidate becomes a useful ResearchCase.
- Diagnostic finding leads to accepted improvement.
- Source produces official or trusted evidence.

### What Decreases It

- False positives.
- Duplicates.
- Unclassified candidates.
- Low-quality external signals.

### Example Formula

`signal_xp = useful_cases * 20 + accepted_findings * 10 - false_positives * 10 - duplicates * 3`

### What Good Looks Like

Sources and agents produce fewer but more actionable findings.

### What Bad Looks Like

High volume with low conversion to useful research.

### Caveats

Early source exploration may have lower signal while still being useful.

### Mission Control Placement

Source-level and room-level score panels.

## 3. Learning XP

### Purpose

Measures whether the system produces actionable, human-reviewed improvements.

### What Increases It

- Learning proposals are created from diagnostics.
- Proposals are accepted after review.
- Accepted proposals are implemented.
- Repeated issues decline after implementation.

### What Decreases It

- Repeated issues with no proposal.
- Many rejected proposals due to poor evidence.
- Accepted proposals never implemented.

### Example Formula

`learning_xp = accepted_proposals * 20 + implemented_proposals * 30 - stale_accepted_proposals * 10`

### What Good Looks Like

Clear proposal flow from diagnostic to reviewed improvement.

### What Bad Looks Like

Large unreviewed backlog or repeated issues without learning.

### Caveats

Learning XP should not reward proposal spam.

### Mission Control Placement

Learning Proposals tab and Agent Ops summary.

## 4. Reliability Score

### Purpose

Summarizes whether a source, room, route, or agent behaves predictably and explainably.

### What Increases It

- Consistent successful diagnostics.
- Low error rate.
- Clear skip reasons.
- Stable source behavior.

### What Decreases It

- Failed logging.
- Missing funnel counts.
- Unexplained empty results.
- Repeated stale cases.

### Example Formula

`reliability_score = max(0, 100 - error_rate_points - unknown_status_points - stale_points - unexplained_empty_points)`

### What Good Looks Like

Operators can answer what happened and why.

### What Bad Looks Like

UI appears healthy while backend reality is unknown or misleading.

### Caveats

Reliability should be computed conservatively when data is sparse.

### Mission Control Placement

Room, agent, and source cards.

## 5. Evidence Quality

### Purpose

Measures whether cases and diagnostics rely on official, trusted, and documented evidence.

### What Increases It

- Official primary source attached.
- Official-source status reviewed.
- Documents and sources have useful metadata.
- Missing evidence is explicitly tracked.

### What Decreases It

- External unverified evidence.
- Metadata-only records with no verification task.
- Missing official source for external cases.

### Example Formula

`evidence_quality_score = official_primary_cases * 100 / total_cases_with_evidence_status`

Adjust with penalties for missing tasks, missing sources, or stale verification.

### What Good Looks Like

Cases can be traced to official or trusted evidence.

### What Bad Looks Like

Cases depend on unverified external summaries.

### Caveats

Some early inbox cases can legitimately start as unknown; the metric should show that as incomplete, not failed.

### Mission Control Placement

Evidence Lab and Research Desk views.

## 6. Noise Penalty

### Purpose

Highlights sources, routes, or agents that generate repeated low-quality work.

### What Increases It

- False positives.
- Duplicates.
- Repeated unclassified candidates.
- Out-of-scope cases.
- Misleading UI/status claims.

### What Decreases It

- Accepted deduplication improvements.
- Improved routing rules.
- Better source configuration.

### Example Formula

`noise_penalty = false_positives * 5 + duplicates * 2 + out_of_scope_cases * 5 + misleading_status_findings * 10`

### What Good Looks Like

Low or declining penalty after improvements.

### What Bad Looks Like

High activity but high waste.

### Caveats

Penalty should be interpreted with source maturity and exploration status.

### Mission Control Placement

Quality Court, Radar Room, and Scoreboard.

## 7. Metric Scopes

### Source Level

- Coverage: connector status, last intake, funnel counts.
- Signal: useful cases produced.
- Reliability: errors, stale runs, unexplained empties.
- Evidence Quality: official source availability.
- Noise Penalty: false positives and duplicates.

### Agent Level

- Activity count.
- Diagnostic usefulness.
- Proposal acceptance rate.
- Error/skipped rate.
- Guardrail compliance.

### Room Level

- Aggregated diagnostics.
- Open proposal count.
- Reliability by operating area.
- Staleness and unresolved warnings.

### Case Level

- V2 metadata completeness.
- Evidence level.
- Official-source status.
- Task/document/source count.
- Stale follow-up status.

### Routing Level

- Route explainability.
- Methodology status distribution.
- False-positive/false-negative tracking.
- Weak-pattern count.
- Proposal history for rule changes.
