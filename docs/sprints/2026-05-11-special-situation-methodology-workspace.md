# SwissEdge Sprint S Closeout — SpecialSituation Methodology Workspace

## Summary

Sprint S adds methodology workspace snapshots to SEC-detected `SpecialSituation` records.

Detected does not mean evaluated. Checklist attached does not mean verified. Resource listed does not mean evidence accepted. Final verification remains human-reviewed.

## What Changed

- Added fixed methodology checklist templates for Sprint Q P1 signals.
- Added fixed required-resource templates for each supported situation type.
- New SEC detections store a snapshot under `evaluation.methodology_workspace`.
- Added a manual backfill CLI for existing SEC-detected `SpecialSituation` records that do not yet have a workspace.
- Added a read-only SpecialSituation methodology route: `/investment/situations/[id]`.
- Added a methodology workspace link from the evaluations queue.

## Templates

Sprint S templates cover:

- `merger_arbitrage` / `acquisition_tender_offer` / `SC TO-T`
- `tender_offer` / `self_tender` / `SC TO-I`
- `spin_off` / `standard_spin_off` / `Form 10`
- `liquidation_or_dissolution` / `voluntary_liquidation` / `8-K` liquidation/dissolution, stored against the existing `bankruptcy` / `voluntary_liquidation` routing output

Templates are concise, practical, and based on processed methodology artifacts and existing routing/playbook mappings. They are marked `requires_course_review=true`.

## Storage

No migration is required.

The workspace is stored in the existing `SpecialSituation.evaluation` JSONB field:

```json
{
  "methodology_workspace": {
    "template_key": "...",
    "template_version": "v0.1",
    "source": "processed_course_artifacts",
    "requires_course_review": true,
    "checklist": [],
    "required_resources": [],
    "progress": {}
  }
}
```

Checklist items start only as `not_started` or `needs_evidence`. Sprint S never marks an item as verified.

Required resources start with `status="missing"`.

## Backfill

Dry-run, default:

```bash
python -m backend.cli.special_situation_attach_methodology --dry-run
```

Apply:

```bash
python -m backend.cli.special_situation_attach_methodology --apply
```

Backfill targets only:

- `SpecialSituation.status = "detected"`
- `evaluation.source = "sec_edgar"`
- `evaluation.detected_only = true`
- existing `evaluation.sec_detection`
- missing `evaluation.methodology_workspace`

Backfill does not touch watchlist records, manual records, v2 evaluated examples, or ResearchCases.

## UI

New read-only route:

```text
/investment/situations/[id]
```

Sections:

- Detection Summary
- Progress Summary
- Methodology Checklist
- Required Resources
- Next Actions placeholders

Future actions are shown as disabled/planned. Resource Scout is not active in Sprint S.

## Guardrails Confirmed

- No live AI.
- No web crawling.
- No PDF download.
- No SEC document body fetching.
- No automatic verification.
- No ResearchCase auto-creation.
- No public publishing.
- No `/api/investment/scan`.
- No cron modification.
- No external sources.
- No Alembic migration.
- No Marketplace/Sales changes.

## Future Sprint T

Resource Scout should be designed separately. It may collect URLs/resources later, but Sprint S only defines the workspace and missing-resource placeholders.
