# Course Documentation Map

The Course Documentation Map is compact structured metadata that connects a situation type to the documentation workflow SwissEdge should use.

It supports Playbook Workshop, Research Desk, Documentation Agent, Quality Court, and Fontana without copying private or long course text into the codebase.

## What It Contains

For each supported situation type, the map defines:

- relevant course chapter references
- applicable playbooks
- checklist items
- required documents
- required information
- blocking conditions
- guardrails

Supported situation types:

- `merger_arbitrage`
- `tender_offer`
- `spin_off`
- `bankruptcy`
- `liquidation`
- `rights_offering`
- `proxy_fight`
- `unknown`

Unknown or unsupported values fall back to the `unknown` map.

## Course Privacy

The map intentionally stores only concise metadata:

- chapter IDs
- short chapter titles
- relevance labels
- short reasons
- checklist labels
- required document categories
- required information categories

It does not store private course passages, long excerpts, proprietary examples, or full methodology text.

## How It Is Used

### Playbook Workshop

Uses the map to select:

- relevant chapters
- applicable playbooks
- checklist items
- required documents
- required information

### Research Desk

Uses the map to compare current evidence and document package state against what the course requires.

### Documentation Agent

Future Documentation Agent v1 can use the map to produce deterministic documentation reports and next manual actions.

### Quality Court

Quality Court can use the map to identify missing critical evidence or weak documentation before Dani relies on the case package.

### Fontana

Fontana can combine this map with the Skill Registry to identify missing capabilities by situation type and propose product or technical improvements.

## API

Read-only endpoint:

```text
GET /api/investment/course-documentation-map/{situation_type}
```

This endpoint does not mutate data, run detection, call live AI, create ResearchCases, or verify documents.

## Guardrails

- The map is documentation metadata, not an investment recommendation.
- Required documents are not automatically verified.
- Found or suggested documents remain separate from verified documents.
- Dani remains the final decision maker.
