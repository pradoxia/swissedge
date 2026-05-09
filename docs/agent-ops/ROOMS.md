# SwissEdge Agent Ops Rooms

## Radar Room

### Purpose

Monitor SEC EDGAR, scan coverage, forms, rate limits, and scanner funnel diagnostics.

### Agents

- Edgar Scout.
- Form Parser.
- Router Analyst.
- Quality Sentinel.

### Inputs

- Scanner funnel diagnostics.
- SEC form coverage configuration.
- Source registry status.
- Radar Status summaries.
- Error and rate-limit diagnostics.

### Outputs

- Source coverage warnings.
- Empty-scan explanations.
- SEC reliability notes.
- Candidate funnel reports.

### Example Activities

- Explain why a scan created zero opportunities.
- Compare searched forms against routing coverage.
- Flag SEC adapter rate-limit handling issues.

### Diagnostics

- Raw hits by form.
- Parsed filings by form.
- Classified candidates.
- Skipped unclassified filings.
- Duplicate count.
- Created situations/cases.
- Rate-limit events.

### Metrics

- Coverage XP.
- Signal XP.
- Reliability Score.
- Noise Penalty.

### Future Mission Control View

Scanner/source health board with funnel counts, form coverage, recent errors, and source registry mismatch warnings.

### Guardrails

- No scan trigger.
- No cron change.
- No source registry wiring.
- No automatic ResearchCase creation.

## Evidence Lab

### Purpose

Track filing parsing, document metadata, snippets, official-source status, and evidence quality.

### Agents

- Form Parser.
- Quality Sentinel.
- Playbook Scribe.

### Inputs

- ResearchDocuments.
- ResearchSources.
- Filing metadata.
- User-provided snippets.
- Official-source status fields.

### Outputs

- Evidence quality labels.
- Missing official-source warnings.
- Document completeness diagnostics.
- Verification task proposals.

### Example Activities

- Identify cases without official evidence.
- Flag metadata-only URLs that need snippets.
- Detect weak source provenance.

### Diagnostics

- Missing official source.
- Missing documents.
- Snippet unavailable.
- Evidence level unknown.
- Source quality low.

### Metrics

- Evidence Quality.
- Source-level Reliability Score.
- Case-level missing evidence count.

### Future Mission Control View

Evidence completeness matrix by case, source type, and official-source status.

### Guardrails

- No URL crawling.
- No raw copyrighted text.
- No claims beyond stored metadata/snippets.

## Research Desk

### Purpose

Operate ResearchCases, Research Inbox, briefs, tasks, and enrichment.

### Agents

- Case Builder.
- Router Analyst.
- Quality Sentinel.

### Inputs

- ResearchCases.
- V2 metadata.
- Tasks.
- Documents.
- Sources.
- Briefs.
- Linked evaluations.

### Outputs

- Inbox buckets.
- Follow-up tasks.
- Readiness labels.
- Enrichment warnings.

### Example Activities

- Show cases needing enrichment.
- Identify cases ready for deep research.
- Flag stale or taskless ResearchCases.

### Diagnostics

- No open tasks.
- No documents.
- No sources.
- Missing V2 metadata.
- Stale updated date.

### Metrics

- Case-level completeness.
- Research Desk throughput.
- Stale case count.

### Future Mission Control View

Research Inbox operations view with bucket counts, warnings, and follow-up focus.

### Guardrails

- No automatic status mutation.
- No live AI unless manually requested.
- No publication action.

## Quality Court

### Purpose

Detect false positives, missing methodology, missing official sources, stale cases, duplicate cases, and guardrail violations.

### Agents

- Quality Sentinel.
- Fontana.

### Inputs

- ResearchCase metadata.
- Briefs.
- PublicArticleDrafts.
- Internal Audit findings.
- Diagnostic events.

### Outputs

- Validation warnings.
- Blocked transition reasons.
- Learning proposals.
- Safety reports.

### Example Activities

- Flag missing disclaimer.
- Detect prohibited recommendation language.
- Identify duplicate cases.
- Explain false positives.

### Diagnostics

- Missing methodology.
- Missing official source.
- Duplicate status possible.
- Out-of-scope methodology.
- Stale case.
- Publication safety issue.

### Metrics

- Reliability Score.
- Noise Penalty.
- False-positive rate.
- Guardrail violation count.

### Future Mission Control View

Quality dashboard with blocked issues, recurring risks, and safety scorecards.

### Guardrails

- No auto-publish.
- No auto-approval.
- No directive investment language.

## Playbook Workshop

### Purpose

Maintain playbook gaps, routing improvements, methodology status, `source_map`, `risk_patterns`, and checklist improvements.

### Agents

- Playbook Scribe.
- Router Analyst.
- Fontana.

### Inputs

- Processed course artifacts.
- Routing audit findings.
- False-positive/false-negative patterns.
- Learning proposals.

### Outputs

- Playbook improvement proposals.
- Routing rule proposals.
- Checklist update proposals.
- Methodology gap notes.

### Example Activities

- Identify a situation type that routes poorly.
- Propose a checklist item.
- Mark a playbook as detection-only.

### Diagnostics

- Unknown situation type.
- Weak route pattern.
- Missing checklist.
- Methodology out of scope.

### Metrics

- Routing-level precision proxy.
- Methodology coverage.
- Learning XP.

### Future Mission Control View

Methodology health view with routing gaps, proposal queue, and playbook status.

### Guardrails

- No raw course text.
- No autonomous routing changes.
- No methodology invention.

## Agent Ops

### Purpose

Coordinate rooms, agents, activity feed, scoreboards, learning proposals, and Fontana reports.

### Agents

- Fontana.
- Quality Sentinel.
- Future Operations Auditor.

### Inputs

- Room summaries.
- Agent activity.
- Diagnostic events.
- Learning proposals.
- ADRs.
- Roadmap.

### Outputs

- Activity feed.
- Scoreboards.
- CTO reports.
- ADR proposals.
- Prioritized next steps.

### Example Activities

- Generate a Fontana report.
- Review accepted/rejected proposals.
- Monitor recurring operational patterns.

### Diagnostics

- Missing observability.
- Stale docs.
- Inconsistent UI claims.
- Repeated failures.

### Metrics

- Agent-level Reliability Score.
- Room-level health.
- Learning proposal acceptance rate.

### Future Mission Control View

`/agent-ops` with tabs for rooms, agents, activity, diagnostics, proposals, scoreboards, and Fontana reports.

### Guardrails

- No autonomous execution.
- No production mutation.
- Human approval required for implementation.
