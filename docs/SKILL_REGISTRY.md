# Skill Registry

The Skill Registry defines the capabilities SwissEdge needs across Agent Rooms.

It keeps the UI simple by supporting a few visible agents and many internal skills.

## Recommended Model

- Few visible agents.
- Many internal skills.
- Skills grouped by capability.
- Skills can be required by situation type.
- Fontana can report implemented and missing skills.

Visible agents should represent ownership. Internal skills should represent reusable capabilities.

## Skill Groups

Current groups:

- Course Intelligence
- SEC Evidence
- Document Intelligence
- Transaction Terms
- Situation-Specific Skills
- Documentation Quality
- Quality / Guardrails

## Skill Fields

Each skill includes:

- `skill_key`
- `label`
- `group`
- `description`
- `implemented`
- `required_for_situation_types`
- `outputs`
- `dependencies`

`implemented` is conservative. Conceptual skills are marked `false` until SwissEdge has deterministic support.

## Examples

Course Intelligence:

- Course Chapter Mapper
- Playbook Matcher
- Checklist Builder
- Course Question Mapper

SEC Evidence:

- SEC Filing Locator
- SEC Exhibit Index Reader
- SEC Document Classifier
- Related Filing Finder

Document Intelligence:

- Found Document Matcher
- Missing Document Detector
- Document Importance Assigner
- Source Confidence Assessor

Transaction Terms:

- Consideration Extractor
- Timeline Extractor
- Condition Extractor
- Risk Factor Extractor

Situation-Specific Skills:

- Tender Offer Terms Skill
- Schedule 14D-9 Finder
- Form 10 Analyzer
- Liquidation Plan Analyzer
- Rights Offering Terms Skill
- Proxy Materials Analyzer

Documentation Quality and Guardrails:

- Readiness Scorer
- Next Best Action Generator
- Guardrail Checker
- Misclassification Detector

## How Fontana Uses It

Fontana can use the Skill Registry to answer:

- which skills a situation type requires
- which required skills are implemented
- which required skills are missing
- which missing skills block a room
- which missing skills should become future sprint candidates

This should produce product, process, and technical improvement proposals only. It should not produce investment recommendations.

## API

Read-only endpoint:

```text
GET /api/investment/skill-requirements/{situation_type}
```

This endpoint does not mutate data, run detection, call live AI, create ResearchCases, or verify documents.

## Guardrails

- Skills describe capabilities; they do not run agents.
- Missing skills are system gaps, not investment conclusions.
- Implemented skills are deterministic only.
- Dani remains the final decision maker.
