# Promotion Readiness

Promotion Readiness helps Dani decide whether a detected `SpecialSituation` is ready for manual promotion into a durable `ResearchCase`.

It is read-only, deterministic, and advisory for workflow readiness only. It does not approve an investment.

## What It Uses

Promotion Readiness uses available metadata from:

- the SpecialSituation
- Document Package
- evidence links
- SEC acquisition metadata when available
- filing URL
- accession number
- form type
- situation type

It does not mutate the database.

It does not create a ResearchCase.

It does not call live AI, evaluator v2, or `/api/investment/scan`.

## Readiness Levels

### `not_ready`

The situation is missing basic support needed for a manual promotion decision.

Common causes:

- no supporting evidence links
- incomplete SEC identifiers
- unclear situation type
- missing company context

Operator action: fix the basic source trail before considering promotion.

### `needs_documentation`

The situation has enough source context to be understandable, but required documents are still missing or need manual check.

Operator action: use Document Package missing items and manual actions to complete the documentation trail.

### `ready_for_manual_promotion`

The situation appears documented enough for Dani to decide whether to create a ResearchCase.

Important: `ready_for_manual_promotion` does not mean investment approval. It only means the manual promotion decision can be reviewed.

## Readiness Score

The score is a compact 0-100 operational signal.

It considers:

- SEC/source identifiers
- supporting evidence links
- required document coverage
- document package readiness

Use the score for triage, not as a decision rule.

## Blocking Reasons

Blocking reasons explain why a situation is not ready.

Examples:

- SEC filing identifiers are incomplete.
- No supporting evidence links are available.
- Required documents are still missing or need manual check.

Resolve blockers before manual promotion.

## Missing Required Documents

This list comes from the Document Package.

Use it as the first documentation work queue. Missing required documents should be searched or manually confirmed before promotion unless Dani intentionally overrides the gap.

## Supporting Evidence

Supporting evidence shows the top stored metadata links that explain why SwissEdge can trace the detection.

Important:

- metadata-only links are not legal verification
- suggested links are not evidence until manually reviewed
- supporting evidence helps trace the case, not approve it

## Recommended Next Action

The recommended next action is the next practical operator step.

Examples:

- confirm SEC filing identifiers
- find a missing required document
- manually review the evidence package
- decide whether to create a ResearchCase

Follow it as a checklist hint, not as automation.

## Manual Promotion

Dani may manually create a ResearchCase when:

- the source trail is understandable
- required documents are found or consciously accepted as missing
- the situation is worth durable research tracking
- the case needs tasks, documents, sources, operational view, or deeper review

Promotion should remain manual.

## Guardrails

- Promotion Readiness is read-only.
- It does not create ResearchCases.
- It does not update SpecialSituations.
- It does not call live AI or evaluator v2.
- It does not call `/api/investment/scan`.
- It does not auto-discard detections.
- `ready_for_manual_promotion` does not mean investment approval.
- Dani remains the final decision maker.
