# SwissEdge Sprint T Closeout — Resource Scout + Evidence Workspace v1

## Summary

Sprint T adds Resource Scout v1 for `SpecialSituation` methodology workspaces.

Resource Scout finds and stores resource candidates. It does not verify evidence, does not evaluate the investment case, and does not create ResearchCases.

## Discovery Scope

No broad automated web discovery is implemented in Sprint T. There is no web search API integration, no crawling, no PDF download, and no SEC document body fetching.

Resource Scout v1 creates value through:

- SEC filing candidate from existing `sec_detection.filing_url`
- SEC archive directory candidate when CIK and accession are available
- deterministic search query suggestions for company IR, press releases, offer documents, transaction pages, amendments, and situation-specific documents
- manual resource candidate entry through a safe backend endpoint

## Storage

No migration is required.

Resource candidates and search suggestions are stored inside:

```text
SpecialSituation.evaluation.methodology_workspace
```

New fields:

- `resource_candidates`
- `search_suggestions`

Required resources move from `missing` to `candidate_found` when a candidate clearly maps to a template resource. Checklist items are never marked verified automatically.

## CLI

Single situation dry-run:

```bash
python -m backend.cli.resource_scout_special_situation --situation-id <id> --dry-run
```

Single situation apply:

```bash
python -m backend.cli.resource_scout_special_situation --situation-id <id> --apply
```

Limited batch dry-run:

```bash
python -m backend.cli.resource_scout_special_situation --limit 5 --dry-run
```

Limited batch apply:

```bash
python -m backend.cli.resource_scout_special_situation --limit 5 --apply
```

Batch runs are bounded. The CLI caps batch limit at 25.

## API

Added:

```text
POST /api/investment/situations/{id}/resources
```

Allowed fields:

- `title`
- `url`
- `source_type`
- `notes`
- `related_resource_ids`
- `related_check_ids`

The endpoint validates that URLs are absolute `http` or `https` URLs. It does not fetch the URL body.

## Frontend

`/investment/situations/[id]` now shows:

- Required Resources
- Found / Candidate Resources
- Search Suggestions
- Manual Add Resource form
- Resource Scout CLI availability notice

The UI does not imply verification, evaluation, scheduled resource scouting, or active autonomous agents.

## Guardrails Confirmed

- No cron modification.
- No `/api/investment/scan`.
- No live AI.
- No evaluator v2 global enablement.
- No ResearchCase auto-creation.
- No public drafts or publishing.
- No buy/sell/hold language.
- No web crawling.
- No X/Twitter scraping or API.
- No PDF content download.
- No SEC document body fetching.
- No full copyrighted article text storage.
- No autonomous scheduled resource scouting.
- No Marketplace/Sales changes.
- No Alembic migration.

## Hotfix — JSONB Persistence

Dani's first VPS apply run reported candidates created, but a follow-up dry-run still reported those same candidates as new and the API response did not show `resource_candidates` or `search_suggestions`.

Root cause: Resource Scout mutated nested `evaluation.methodology_workspace` JSON in place, which PostgreSQL JSONB / SQLAlchemy does not reliably track as a changed column.

Fix:

- Resource Scout now works on a deep copy of `SpecialSituation.evaluation`.
- Apply mode mutates the copied JSON.
- The full copied JSON is reassigned to `situation.evaluation`.
- `flag_modified(situation, "evaluation")` is called before flush/commit.
- API serialization already exposes the full `methodology_workspace`, including `resource_candidates`, `search_suggestions`, and updated required resource statuses.

Validation expectation after deploy:

```bash
python -m backend.cli.resource_scout_special_situation --situation-id <id> --apply
python -m backend.cli.resource_scout_special_situation --situation-id <id> --dry-run
```

The second command should report `candidates_created: 0`, `candidates_existing > 0`, and `required_resources_updated: 0` when no new candidate remains.

## Future Compatibility

Resource Scout v1 creates a structured place for deeper agents to work later. Future versions can add controlled official-source discovery, PDF metadata handling, or human-reviewed evidence acceptance without changing the core workspace shape.
