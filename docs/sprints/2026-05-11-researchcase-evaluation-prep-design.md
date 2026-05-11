# ResearchCase Evaluation Preparation / Deep Research Assist Design

Date: 2026-05-11

## Goal

Prepare promoted ResearchCases for deeper human-reviewed analysis without activating automatic evaluation.

The output of this phase should be a safe evaluation preparation package. It should organize what SwissEdge already knows, identify missing evidence, and make the next human research steps obvious.

## Non-Goals

- Do not call live AI.
- Do not run evaluator v2.
- Do not enable evaluator v2 globally.
- Do not create investment recommendations.
- Do not publish.
- Do not create public drafts.
- Do not crawl the web.
- Do not download PDFs.
- Do not fetch document or article bodies.
- Do not auto-promote SpecialSituations.
- Do not auto-create ResearchCases from detection.

## Inputs

For a promoted ResearchCase, the preparation package should read:

- Imported SpecialSituation metadata.
- SEC detection metadata.
- Filing type, filing date, filing URL, accession number, and selected playbook.
- Methodology checklist snapshot.
- Required resources.
- Resource candidates.
- Search suggestions.
- Evidence-found mappings.
- Current workflow status.
- Initial promotion tasks and notes.

## Evaluation Readiness Package

Recommended package structure:

```json
{
  "research_case_id": "...",
  "source_special_situation_id": "...",
  "readiness_status": "needs_more_work",
  "metadata_summary": {},
  "checklist_summary": {},
  "required_resources_summary": {},
  "resource_candidates_summary": {},
  "evidence_found_mappings": [],
  "missing_evidence_report": [],
  "source_quality_overview": [],
  "suggested_next_tasks": [],
  "guardrails": []
}
```

The package is read-only at first. It should not overwrite ResearchCase content or SpecialSituation workspace data.

## Readiness Checks

Initial deterministic checks can include:

- Official SEC filing candidate exists.
- Required resources marked `missing`.
- Required resources marked `candidate_found`.
- Required resources marked `evidence_found`.
- Checklist items still `not_started` or `needs_evidence`.
- Checklist items marked `evidence_found`.
- Checklist items marked `verified`.
- Human review required count.
- Missing source types by methodology template.
- Whether any candidate resource has been rejected.

`verified` must remain human-controlled. Sprint U evidence mapping may set `evidence_found`, but this is not equivalent to verification.

## Missing Evidence Report

The missing evidence report should identify:

- Required resource title.
- Expected source.
- Related checklist items.
- Current status.
- Suggested manual next action.

This report should use existing metadata and resource mappings only. It should not fetch, crawl, or infer external content.

## Source Quality Overview

The source quality overview should classify already stored candidates by metadata only:

- official SEC filing
- company investor relations
- press release
- transaction page
- offer document
- PDF link metadata
- news link metadata
- other

No article text, PDF content, or SEC document body should be fetched in this phase.

## Recommended Future Workflow

1. ResearchCase.
2. Evaluation readiness check.
3. Missing evidence report.
4. Manual evaluation preview.
5. Human review.
6. Optional evaluator v2 preview only when explicitly authorized.

## Possible Future Endpoints

Future low-risk backend additions could include:

- `GET /api/investment/research-cases/{id}/evaluation-readiness`
- `GET /api/investment/research-cases/{id}/missing-evidence`

Both should be read-only initially.

## Guardrails

- No live AI.
- No evaluator v2 global enablement.
- No automatic recommendation.
- No buy/sell/hold language.
- No automatic publication.
- No web crawling.
- No PDF download.
- No document body fetching.
- No automatic ResearchCase creation from detection.
- No automatic SpecialSituation promotion.
