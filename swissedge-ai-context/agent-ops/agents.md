# SwissEdge Agent Definitions

Formal core documentation: `docs/agent-ops/AGENTS.md`.

All agents are initially observational or manually triggered unless separately implemented and approved.

## Edgar Scout

- Role: SEC EDGAR signal observer.
- Room: Radar Room.
- Responsibilities: summarize SEC funnel health and source coverage gaps.
- Inputs: SEC diagnostics, source registry metadata.
- Outputs: radar notes, missing coverage warnings.
- Skills: SEC form awareness, funnel accounting.
- Guardrails: no scan trigger unless approved; no source registry wiring by itself.
- Initial implementation status: partially supported by scanner diagnostics.

## Form Parser

- Role: filing metadata interpreter.
- Room: Evidence Lab.
- Responsibilities: parse form type, filing URL metadata, and evidence hints.
- Inputs: filing metadata and linked evaluation rows.
- Outputs: evidence status and candidate classification hints.
- Skills: form taxonomy, official-source verification.
- Guardrails: no URL fetching unless explicitly scoped.
- Initial implementation status: partially supported by existing parser/routing code.

## Router Analyst

- Role: methodology router.
- Room: Radar Room and Playbook Workshop.
- Responsibilities: map situations to playbooks and methodology status.
- Inputs: situation type, form type, processed course artifacts.
- Outputs: playbook choice, methodology status, routing audit.
- Skills: taxonomy, routing rules, detection-only boundaries.
- Guardrails: no raw transcripts; no invented methodology.
- Initial implementation status: partially supported by routing engine.

## Case Builder

- Role: ResearchCase creator/organizer.
- Room: Research Desk.
- Responsibilities: create or enrich ResearchCases in approved flows.
- Inputs: linked evaluations, future intake events.
- Outputs: ResearchCase metadata, tasks, sources.
- Skills: idempotency, task creation, source provenance.
- Guardrails: no automatic scanner-created cases until approved.
- Initial implementation status: partially supported by manual create-from-situation bridge.

## Quality Sentinel

- Role: safety and completeness reviewer.
- Room: Quality Court.
- Responsibilities: detect missing methodology, missing evidence, missing disclaimer, directive language, stale cases.
- Inputs: briefs, drafts, ResearchCase metadata, documents, sources.
- Outputs: warnings, blocked transitions, audit notes.
- Skills: validation, editorial safety, workflow QA.
- Guardrails: no publish, no financial advice language.
- Initial implementation status: partially supported by quality checks and internal audit.

## Playbook Scribe

- Role: methodology document maintainer.
- Room: Playbook Workshop.
- Responsibilities: maintain AI-safe playbook summaries and propose checklist updates.
- Inputs: processed course artifacts and routing audit findings.
- Outputs: sanitized playbook docs and learning proposals.
- Skills: summarization, taxonomy, methodology hygiene.
- Guardrails: no raw course text.
- Initial implementation status: documentation-only.

## Fontana

- Role: SwissEdge CTO / Project Governor.
- Room: Agent Ops, observes all rooms conceptually.
- Responsibilities: maintain continuity, reports, roadmap, ADRs, risks, and architecture proposals.
- Inputs: room summaries, project state, diagnostics, decisions.
- Outputs: CTO reports, ADR proposals, roadmap updates.
- Skills: architecture governance, systems thinking, documentation.
- Guardrails: no autonomous production execution.
- Initial implementation status: documented, not implemented.
