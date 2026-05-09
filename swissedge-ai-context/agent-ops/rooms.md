# SwissEdge Agent Ops Rooms

Formal core documentation: `docs/agent-ops/ROOMS.md`.

## Radar Room

### Purpose

Monitor source and scanner health, especially SEC EDGAR coverage and scanner funnel clarity.

### Agents

Edgar Scout, Form Parser, Router Analyst, Quality Sentinel.

### Inputs

Scanner diagnostics, source registry summaries, SEC form coverage, observed candidate counts, and empty-run summaries.

### Outputs

Funnel status, empty-scan explanations, coverage warnings, reliability notes, and learning proposals.

### Diagnostics

Raw hits, parsed candidates, classified candidates, skipped unclassified, duplicates, evaluated count, created cases, errors, and rate-limit concerns.

### Guardrails

No autonomous scans, cron changes, source registry wiring, evaluator changes, or production actions.

## Evidence Lab

### Purpose

Organize documents, sources, snippets, metadata, official-source verification, and evidence quality.

### Agents

Form Parser, Quality Sentinel, Playbook Scribe.

### Inputs

ResearchDocuments, ResearchSources, linked filings, user snippets, source metadata, and official-source status.

### Outputs

Evidence quality notes, official-source status, missing evidence tasks, and documentation readiness warnings.

### Diagnostics

Missing official source, weak evidence, metadata-only evidence, stale links, missing snippets, and source-quality gaps.

### Guardrails

No URL fetching, crawling, external API use, raw copyrighted text storage, or publication actions unless explicitly approved.

## Research Desk

### Purpose

Coordinate ResearchCase workflow from Research Inbox triage through enrichment, monitoring, deep research, documentation, or archive.

### Agents

Case Builder, Router Analyst, Quality Sentinel.

### Inputs

ResearchCases, tasks, documents, sources, V2 metadata, readiness labels, and linked situations.

### Outputs

Triage buckets, follow-up tasks, readiness labels, enrichment requirements, and case workflow summaries.

### Diagnostics

Stale ResearchCases, no tasks, no docs, no sources, missing V2 metadata, unclear readiness, and blocked follow-ups.

### Guardrails

No automatic case creation, status mutation, live AI call, or publishing action unless separately approved.

## Quality Court

### Purpose

Enforce methodology, disclaimer, evidence, and safety constraints across research outputs.

### Agents

Quality Sentinel, Fontana.

### Inputs

Briefs, previews, public drafts, methodology metadata, disclaimers, and diagnostic events.

### Outputs

Validation warnings, readiness concerns, publishing blocks, methodology gaps, and safety findings.

### Diagnostics

Missing disclaimer, buy/sell/hold language, missing methodology, unsupported claims, missing official sources, and stale review status.

### Guardrails

No public publishing, recommendation language, raw course text, or private metadata in public-facing material.

## Playbook Workshop

### Purpose

Maintain course-grounded methodology summaries, routing concepts, taxonomy, source maps, risk patterns, and checklist proposals.

### Agents

Playbook Scribe, Router Analyst, Fontana.

### Inputs

Sanitized course artifacts, routing audits, learning proposals, evaluator summaries, and human-approved methodology notes.

### Outputs

Playbook updates, checklist proposals, taxonomy improvements, and routing clarification notes.

### Diagnostics

Out-of-scope patterns, routing ambiguity, weak checklist coverage, missing course references, and stale methodology summaries.

### Guardrails

No raw course transcripts, copyrighted raw text, autonomous routing changes, or evaluator v2 global changes.

## Agent Ops

### Purpose

Coordinate room definitions, agent definitions, activity feed concepts, diagnostics, learning proposals, scoreboards, and Fontana reports.

### Agents

Fontana, Quality Sentinel, future Operations Auditor.

### Inputs

Room summaries, diagnostics, task history, decisions, ADRs, roadmap notes, and learning proposals.

### Outputs

Reports, ADR proposals, roadmap updates, agent health summaries, and next-sprint recommendations.

### Diagnostics

Stale docs, inconsistent UI claims, missing observability, recurring failures, missing proposal outcomes, and unsafe automation requests.

### Guardrails

No autonomous production changes, deployments, cron changes, scans, source mutations, or evaluator changes.
