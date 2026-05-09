# SwissEdge Routing Audits Spec

## 1. Purpose

Routing audits make deterministic routing explainable. They show why a candidate matched a playbook, why alternatives were rejected, what evidence supported the route, and whether human review is required.

## 2. Candidate Routes

A routing audit should record:

- Candidate route name.
- Situation type.
- Filing type or source signal type.
- Matched patterns.
- Confidence or score if available.
- Rejection reason for non-selected routes.

## 3. Scoring Reasons

Scoring reasons should be human-readable and safe:

- Form type matched playbook.
- Keyword or metadata pattern matched.
- Official source status supports route.
- Evidence is incomplete.
- Route is detection-only.
- Route is out of scope.

Do not store raw filings, raw course text, or private source payloads.

## 4. Routing Evidence

Evidence should include safe labels and references:

- Form type.
- Source type.
- Filing URL presence boolean or sanitized URL reference when already stored.
- Situation type.
- V2 metadata fields.
- Relevant safe snippets only if user-provided or already sanitized.

## 5. Playbook Version

Each audit should include:

- `playbook_key`.
- `playbook_version` or artifact version if available.
- `checklist_key` if used.
- `methodology_status`.

If versioning is not implemented yet, use `unknown` and flag it as a diagnostic gap.

## 6. Methodology Status

Allowed values should align with the V2 metadata contract:

- `unknown`
- `evaluator_ready`
- `partial`
- `routing_detection_only`
- `detection_only`
- `out_of_scope`
- `human_review_required`

## 7. Safety Flags

Examples:

- `needs_official_source`
- `missing_methodology`
- `detection_only`
- `out_of_scope`
- `possible_duplicate`
- `human_review_required`
- `no_recommendation_language`

## 8. Human Review Labels

Human review labels should explain why a route needs review:

- Ambiguous form or signal.
- Missing official source.
- Weak methodology coverage.
- Conflicting evidence.
- Possible duplicate.
- High noise source.

## 9. False Positive Tracking

A false positive record should capture:

- Original route.
- Why it was wrong.
- Which pattern was too broad.
- Whether a learning proposal was created.
- Human reviewer note if available.

## 10. False Negative Tracking

A false negative record should capture:

- Missed case or route.
- Source or form that should have matched.
- Missing pattern, parser gap, or source coverage gap.
- Whether a learning proposal was created.

## 11. Weak Pattern Detection

Weak patterns include:

- Repeated matches with no useful ResearchCase.
- Frequent detection-only outcomes.
- Form types routed too broadly.
- Metadata-only signals that lack official evidence.
- External sources with high duplicate or low reliability rates.

## 12. Learning Proposal Triggers

Create a learning proposal when:

- A route produces repeated false positives.
- A known situation type is missed.
- A playbook lacks required checklist coverage.
- UI labels misrepresent route status.
- Evidence quality is consistently too low.

Learning proposals must not auto-apply.

## 13. Example Routing Audit Record

```json
{
  "candidate_id": "candidate-or-case-id",
  "selected_route": "merger_arbitrage",
  "candidate_routes": [
    {
      "route": "merger_arbitrage",
      "score": 85,
      "reasons": ["official filing present", "transaction terms detected"]
    },
    {
      "route": "generic_merger",
      "score": 55,
      "reasons": ["merger signal present", "less specific than selected route"]
    }
  ],
  "routing_evidence": {
    "form_type": "DEFM14A",
    "source_type": "sec_edgar",
    "official_source_status": "official_attached"
  },
  "playbook_key": "merger_arbitrage",
  "playbook_version": "unknown",
  "methodology_status": "evaluator_ready",
  "safety_flags": ["human_review_required"],
  "human_review_label": "Confirm deal terms and conditions before deep research."
}
```

## 14. Governance

No autonomous routing changes are allowed. All routing rule changes require:

1. Learning proposal.
2. Dani approval.
3. Codex implementation.
4. Claude review if needed.
5. Dani manual deployment.
