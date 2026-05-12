# Intelligence Scoring

Date: 2026-05-12

## Purpose

The Intelligence Score measures the current quality, safety, and usefulness of a ResearchCase preparation package.

It is deterministic and read-only. It does not evaluate the investment, make recommendations, create ResearchCases, publish drafts, fetch documents, crawl URLs, call AI, or write to the database.

## Endpoint

`GET /api/investment/research-cases/{id}/intelligence-score`

The endpoint loads the ResearchCase and returns a derived package from:

- ResearchCase metadata.
- Promotion brief snapshot.
- Evaluation Preparation package.
- Evidence Links / Research Traceability package.
- Tasks, documents, and sources already stored on the ResearchCase.

## Score Breakdown

Total: 100 points.

- Detection Score: 0-40
  - Intake lineage.
  - Official source metadata.
  - Detection summary completeness.
  - SEC/source traceability links.
- Structuring Score: 0-40
  - Evaluation Preparation readiness.
  - Required-resource coverage.
  - `candidate_found` resources receive partial coverage credit only.
  - Checklist evidence mapping.
  - Brief section coverage.
  - Presence of tasks, documents, and sources.
- Risk Discipline Score: 0-20
  - Financial-advice disclaimer.
  - No directive investment language in stored metadata.
  - Visible human-review requirements.
  - Not marked published.
  - Preparation warnings surfaced for manual review.

## Grades

- `APPROVABLE` (90-100): Structurally approvable for manual review only.
- `USEFUL_INCOMPLETE` (70-89): Useful preparation package, but incomplete.
- `REVIEW_PIPELINE` (<70): Pipeline review recommended before relying on the package.

Important: `APPROVABLE` does not mean investment approval. It means the ResearchCase preparation package is structurally approvable for manual review.

## Guardrails

- Manual review remains mandatory.
- No DB writes.
- No autosave.
- No live AI.
- No external HTTP calls.
- No SEC document body fetching.
- No PDF downloads.
- No crawling.
- No automatic evaluation.
- No ResearchCase auto-creation.
- No trading decisions.
- No public draft creation or publishing.

## Known Limits

- The score is only as good as the stored ResearchCase metadata and snapshots.
- Metadata-only links are scored for traceability, not verified factual content.
- `verified` remains human-controlled; the score never marks evidence as verified.
- The score is a preparation-quality signal, not an investment conclusion.
