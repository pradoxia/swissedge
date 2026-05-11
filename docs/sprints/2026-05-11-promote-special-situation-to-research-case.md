# SwissEdge Sprint V Closeout - Promote SpecialSituation to ResearchCase

## Summary

Sprint V adds a manual promotion path from a `SpecialSituation` methodology workspace into a `ResearchCase`.

Promotion is manual only. It creates a deeper research workspace; it does not evaluate, recommend, publish, create public drafts, call live AI, or trigger `/api/investment/scan`.

## Endpoint

Added:

```text
POST /api/investment/situations/{id}/promote-to-research-case
```

Optional request body:

```json
{
  "title": "Optional title",
  "initial_status": "under_investigation",
  "notes": "Optional notes"
}
```

The endpoint accepts only narrow promotion fields. It does not accept arbitrary ResearchCase JSON or arbitrary evaluation overwrite.

## Idempotency

Duplicate ResearchCases are prevented in two layers:

1. `SpecialSituation.evaluation.methodology_workspace.research_case_id`
2. Existing `ResearchCase.situation_id`

If a ResearchCase already exists, the endpoint returns it with `created=false`.

## Mapping

The promoted `ResearchCase` receives safe structured context from:

- `SpecialSituation` detection metadata
- SEC accession / filing date / playbook fields when present
- `methodology_workspace.checklist`
- `methodology_workspace.required_resources`
- `methodology_workspace.resource_candidates`
- `methodology_workspace.search_suggestions`
- `methodology_workspace.progress`
- `methodology_workspace.workflow_status`

The context is stored in `ResearchCase.brief` as a snapshot with `detected_not_evaluated=true`.

Initial conservative tasks are created for verification, document collection, date checks, resource review, checklist review, and deciding whether deeper evaluation is warranted.

Resource candidates are copied to `ResearchSource` rows as metadata-only sources. URLs are not fetched.

After promotion, the SpecialSituation workspace stores:

- `research_case_id`
- `workflow_status = promoted_to_research_case`

## Frontend

`/investment/situations/[id]` now shows a manual `Promote to ResearchCase` action when a methodology workspace exists and no ResearchCase is linked.

Before promoting, the UI warns:

```text
This will create a ResearchCase for deeper analysis. It will not evaluate, recommend, or publish.
```

After success, the UI links to `/investment/research/{id}` and disables duplicate promotion.

`/investment/situations` now shows a promoted badge and a Promoted Kanban column.

## Guardrails Confirmed

- No cron modification.
- No `/api/investment/scan`.
- No live AI.
- No evaluator v2 global enablement.
- No automatic ResearchCase creation from detection.
- No automatic promotion.
- No public draft creation.
- No publishing.
- No buy/sell/hold recommendation language.
- No web crawling.
- No PDF download.
- No document/article body fetching.
- No Marketplace/Sales changes.
- No Alembic migration.
- No auto-deploy.

## Manual Verification

1. Open `/investment/situations/{id}` for a SEC-detected situation with methodology workspace.
2. Click `Promote to ResearchCase`.
3. Confirm the warning.
4. Verify the success state links to `/investment/research/{research_case_id}`.
5. Click promote again or reload the page and verify no duplicate ResearchCase is created.
6. Open the ResearchCase and confirm status is `under_investigation`, readiness is `needs_more_work`, and brief contains detection/workspace snapshot context.

## Hotfix - brief_version length

Production validation initially failed during promotion with:

```text
value too long for type character varying(20)
```

Root cause: Sprint V used `brief_version = "special_situation_promotion_v1"`, which exceeded the existing `research_cases.brief_version` `VARCHAR(20)` column.

Fix:

- Shortened promotion brief version to `ss_promo_v1`.
- Added defensive tests that promotion-created constrained string fields fit their model column lengths.
- No Alembic migration is needed.
