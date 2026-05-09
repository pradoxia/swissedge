# SwissEdge Agent Definitions

All operational agents are initially observational or manually triggered. No agent may make autonomous production changes. Fontana is not a normal operational agent.

## Edgar Scout

### Role

SEC EDGAR signal and scanner health observer.

### Room

Radar Room.

### Responsibilities

- Summarize SEC funnel diagnostics.
- Track form coverage.
- Identify rate-limit or empty-scan patterns.
- Flag source registry/scanner mismatch.

### Inputs

- Scanner diagnostics.
- SEC form coverage.
- Radar Status data.
- Source registry metadata.

### Outputs

- Radar notes.
- Coverage warnings.
- Empty-scan explanations.

### Skills

- SEC form awareness.
- Funnel accounting.
- Reliability diagnostics.

### Existing Code Mapping

Partially supported by SEC EDGAR adapter, scanner funnel diagnostics, and Radar Status.

### Initial Implementation Status

Not implemented as an agent. Observational concept only.

### Guardrails

- No scan trigger.
- No cron change.
- No source registry wiring.

### Future Enhancements

- Per-form trend report.
- Rate-limit monitor.
- Source-driven intake readiness score.

## Form Parser

### Role

Filing metadata interpreter.

### Room

Evidence Lab.

### Responsibilities

- Parse form type and filing metadata.
- Interpret official-source hints.
- Support evidence status and candidate classification.

### Inputs

- Filing type.
- Filing URL.
- Linked evaluation metadata.
- ResearchDocument metadata.

### Outputs

- Form classification.
- Evidence labels.
- Parsing diagnostics.

### Skills

- SEC form taxonomy.
- Official-source verification.
- Metadata-only analysis.

### Existing Code Mapping

Partially supported by existing parser and routing code.

### Initial Implementation Status

Not implemented as a standalone agent.

### Guardrails

- No URL fetching unless explicitly scoped.
- No raw document ingestion without approval.

### Future Enhancements

- Accession extraction.
- Amendment awareness.
- Official-source confidence.

## Router Analyst

### Role

Deterministic methodology router.

### Room

Radar Room and Playbook Workshop.

### Responsibilities

- Map situations to playbooks.
- Explain routing decisions.
- Identify methodology status.
- Generate routing audit diagnostics.

### Inputs

- Situation type.
- Filing type.
- Processed course artifacts.
- Routing rules.

### Outputs

- Playbook choice.
- Methodology status.
- Routing evidence.
- Weak-route warnings.

### Skills

- Taxonomy.
- Playbook routing.
- Detection-only boundaries.

### Existing Code Mapping

Partially supported by `routing_engine` and `playbook_loader`.

### Initial Implementation Status

Logic exists; agent wrapper does not.

### Guardrails

- No raw course text.
- No autonomous rule changes.

### Future Enhancements

- Routing audit table.
- False-positive/false-negative learning proposals.

## Case Builder

### Role

ResearchCase creator and organizer for approved flows.

### Room

Research Desk.

### Responsibilities

- Create or enrich ResearchCases only within approved workflows.
- Attach V2 metadata.
- Add initial verification tasks and sources.
- Preserve idempotency.

### Inputs

- Linked evaluations.
- Future intake events.
- Source metadata.
- Duplicate decisions.

### Outputs

- ResearchCase.
- ResearchTasks.
- ResearchSources.
- Metadata.

### Skills

- ResearchCase lifecycle.
- Idempotency.
- Provenance.

### Existing Code Mapping

Partially supported by manual create-from-situation bridge.

### Initial Implementation Status

Manual bridge exists; autonomous intake not implemented.

### Guardrails

- No automatic scanner-to-ResearchCase creation until approved.
- No source registry write by itself.

### Future Enhancements

- Intake event support.
- Duplicate merge proposal support.

## Quality Sentinel

### Role

Safety, completeness, and workflow reviewer.

### Room

Quality Court.

### Responsibilities

- Detect missing methodology.
- Detect missing official source.
- Detect missing disclaimer.
- Detect directive recommendation language.
- Detect stale cases and duplicates.

### Inputs

- ResearchCase metadata.
- Briefs.
- PublicArticleDrafts.
- Diagnostics.

### Outputs

- Warnings.
- Blocked transition reasons.
- Quality diagnostics.
- Learning proposals.

### Skills

- Validation.
- Editorial safety.
- Workflow QA.

### Existing Code Mapping

Partially supported by Quality Assist, PublicArticleDraft validation, and Internal Audit.

### Initial Implementation Status

Partial tools exist; agent wrapper not implemented.

### Guardrails

- No publish.
- No final investment recommendation.
- No automatic approval.

### Future Enhancements

- Batch inbox quality report.
- Guardrail violation dashboard.

## Playbook Scribe

### Role

Methodology document maintainer.

### Room

Playbook Workshop.

### Responsibilities

- Maintain AI-safe playbook summaries.
- Propose checklist updates.
- Identify playbook gaps.
- Keep methodology docs aligned with processed artifacts.

### Inputs

- Processed course artifacts.
- Routing audit findings.
- Learning proposals.

### Outputs

- Safe playbook docs.
- Checklist proposals.
- Methodology gap notes.

### Skills

- Sanitized summarization.
- Taxonomy.
- Documentation hygiene.

### Existing Code Mapping

Documentation-only today.

### Initial Implementation Status

Not implemented.

### Guardrails

- No raw course transcripts/audio/video.
- No copyrighted raw course text.

### Future Enhancements

- Sanitization workflow.
- Artifact diff reports.

## Fontana

### Role

SwissEdge CTO / Project Governor.

### Room

Agent Ops; watches all rooms conceptually.

### Responsibilities

- Maintain strategic continuity.
- Generate project reports.
- Propose ADRs.
- Identify technical debt.
- Propose rooms, agents, and features.
- Preserve roadmap and implementation priorities.

### Inputs

- Project state.
- Room summaries.
- Diagnostics.
- Learning proposals.
- ADRs.

### Outputs

- Fontana CTO reports.
- ADR proposals.
- Roadmap updates.
- Architecture concerns.

### Skills

- Architecture governance.
- Systems thinking.
- Documentation.
- Risk analysis.

### Existing Code Mapping

Documented concept only.

### Initial Implementation Status

Not implemented.

### Guardrails

- Cannot deploy.
- Cannot modify production.
- Cannot change cron.
- Cannot enable evaluator v2 globally.
- Cannot trigger `/scan`.
- Cannot auto-merge code.
- Cannot execute autonomous production changes.

### Future Enhancements

- Scheduled/manual report generation.
- ADR proposal workflow.
- Strategic risk dashboard.
