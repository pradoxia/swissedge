# Investment Research Tech Debt Review

Date: 2026-05-02
Scope: Technical debt scout only. No implementation, tests, build, deploy, or repo scan.

Files reviewed:
- `docs/PROJECT_STATE_LIGHT.md`
- `frontend/app/investment/research/[id]/page.tsx`
- `frontend/lib/api.ts`
- `backend/services/investment/research_cases.py`
- `backend/api/investment/research_cases.py`

## Executive Summary

The Investment Research Platform is functional and phase-complete through 4A/4B/4C, but the implementation has accumulated feature-driven concentration in a few files:

- `frontend/app/investment/research/[id]/page.tsx` is about 1,685 lines and owns page orchestration, major panels, cards, forms, preview workflows, persistence feedback, and display constants.
- `frontend/lib/api.ts` is about 935 lines and mixes several product areas plus all Investment Research API types and fetch wrappers.
- `backend/services/investment/research_cases.py` is about 1,461 lines and mixes schemas, CRUD services, prompt builders, AI parsers, preview generators, source intelligence queue services, and historical case services.
- `backend/api/investment/research_cases.py` is about 503 lines and has repeated run logging boilerplate across AI preview endpoints.

The largest opportunity is not a rewrite. It is a sequence of small extractions that preserve behavior while making Phase 4D safer to implement.

## Top 10 Recommended Improvements

1. Extract frontend research detail components from `page.tsx`.
   Suggested first split: `BriefEditor`, `AiPreviewPanel`, `QualityAssistPanel`, `DocumentCard`, `SourceCard`, `SourceIntelligencePanel`, and `Section`.

2. Introduce shared frontend preview UI primitives.
   Current panels repeat loading state, error state, preview-only banners, warnings, disclaimers, discard controls, and "metadata only" copy.

3. Centralize metadata-only and saved-to-db false banners.
   The same policy appears in brief preview, quality assist, document analysis, source intelligence, document empty states, and source sections.

4. Extract document/source card editors.
   `DocumentCard` and `SourceCard` both combine display, edit state, save state, field validation, async API calls, and action messaging. They should become focused components with smaller hooks.

5. Split `frontend/lib/api.ts` by domain.
   A low-risk structure would be `investmentResearchApi`, `investmentSituationsApi`, `observabilityApi`, and `salesApi`, while keeping a compatibility re-export if needed.

6. Split backend service concerns.
   `research_cases.py` should gradually move into modules for CRUD, AI previews, source intelligence suggestions, and historical cases.

7. Add a common backend AI preview helper.
   Repeated pattern: load context, build prompt, call `complete_with_usage`, parse JSON, force `saved_to_db: false`, append warnings/disclaimer/usage, strip buy/sell language.

8. Add a common router run-logger wrapper for manual preview endpoints.
   `preview_document_analysis`, `preview_brief`, `preview_quality`, `preview_source_intelligence`, and `preview_hist_source_intelligence` repeat start/finish/log/fail/commit behavior.

9. Normalize source intelligence suggestion mapping.
   Research case and historical case save functions both map `source_name`/`proposed_name`, `source_type`/`proposed_source_type`, `reason`/`rationale`, default action, and status.

10. Improve test coverage around cross-case ownership and Phase 4D preconditions.
   Before adding apply behavior, tests should cover suggestion ownership, status transitions, rejected/proposed/apply disallowed cases, no `investment_sources` writes, and no scanner registry writes.

## Frontend Findings

### Large Components

`frontend/app/investment/research/[id]/page.tsx` currently contains the full research detail page and several substantial child components:

- `AiPreviewPanel`
- `QualityAssistPanel`
- `DocumentCard`
- `SourceCard`
- `SourceIntelligencePanel`
- `ResearchDetailPage`

The page-level component also owns many independent UI states: loading/error, status editing, readiness editing, notes editing, task add form, document add form, source add form, save states, and global action messages.

Recommended extraction order:

1. Move pure display helpers/constants first: `Section`, status colors, readiness colors, task/source color maps.
2. Move `BriefEditor`.
3. Move preview panels one at a time.
4. Move `DocumentCard` and `SourceCard`.
5. Move add forms for tasks/documents/sources after cards are stable.

### Repeated UI Patterns

Repeated patterns found:

- Preview lifecycle: `running/generating`, `result/preview`, `error`, `discard`.
- Apply/save lifecycle: `applying/saving`, success/error message, timeout clear.
- Preview-only banners: "PREVIEW ONLY - NOT SAVED", "ASSISTIVE PREVIEW - NOT SAVED", "PROPOSALS ONLY - NOT APPLIED".
- Metadata-only URL warning.
- Warnings blocks with orange styling.
- Disclaimer display.
- Inline card edit forms.
- Source/document empty states.

Low-risk shared components:

- `PreviewPolicyBanner`
- `MetadataOnlyNotice`
- `PreviewWarnings`
- `PreviewDisclaimer`
- `InlineActionMessage`
- `Section`
- `FieldRow` or small labeled field helpers

## Backend Findings

### Large Or Mixed Service Areas

`backend/services/investment/research_cases.py` currently includes:

- Pydantic read/create/update schemas.
- Research case CRUD.
- Task/document/source CRUD.
- Brief preview prompt, parser, generator.
- Quality preview prompt, parser, generator.
- Document analysis preview prompt, parser, generator.
- Source intelligence preview prompt, parser, generator.
- Source intelligence suggestion queue services.
- Historical case schemas and services.
- Historical case source intelligence preview.

Suggested split:

- `research_case_models.py` or `schemas.py`
- `research_case_crud.py`
- `research_child_items.py`
- `research_ai_previews.py`
- `source_intelligence.py`
- `historical_cases.py`

This should be done incrementally with import re-exports if existing router imports need stability.

### Repeated AI Preview Pattern

The AI preview functions repeat a useful but now copy-heavy pattern:

- Build context prompt.
- Call `complete_with_usage`.
- Parse JSON with defensive defaults.
- Return `saved_to_db: False`.
- Include `warnings`, `disclaimer`, and `usage`.
- Strip or reject buy/sell language.
- Avoid URL fetching.

Suggested helper shape:

- `run_ai_json_preview(prompt, system, max_tokens, parser, default_payload)`
- `preview_response(payload, warnings, usage, id_fields)`
- shared `contains_buy_sell_language` and recursive sanitizer for strings/lists/dicts

Keep this helper boring and explicit. Do not make it too generic until at least two preview paths are migrated safely.

### Router Instrumentation Duplication

`backend/api/investment/research_cases.py` repeats run logger behavior across manual preview endpoints:

- `start_run`
- service call
- `finish_run`
- optional `log_ai_usage`
- `db.commit`
- `fail_run` on exception

Suggested helper:

- `run_logged_preview(db, agent_name, task_name, input_summary, prompt_name, operation, output_summary_fn)`

This would reduce endpoint boilerplate while preserving observability.

## Test Gaps

Known from reviewed files and state:

- Frontend component-level tests are not evident from reviewed files. The preview panels and card editors are good candidates for future tests after extraction.
- API client error handling is repeated and could use tests after introducing a shared `requestJson` helper.
- Backend apply behavior for Phase 4D does not exist yet and should get focused tests before/with implementation.
- Source intelligence suggestion filtering should test combined filters and invalid UUID behavior at the router layer.
- Ownership checks should be strengthened for document/source patch endpoints because route includes `research_case_id`, but service patch functions operate by child id.
- Historical case source intelligence should test buy/sell stripping through the shared source-intel parser path.
- Run logger failure behavior should have at least one endpoint test or helper-level unit test if extracted.

## Low-Risk Quick Wins

1. Extract `MetadataOnlyNotice` and use it in preview panels and source/document sections.
2. Extract `PreviewWarnings`.
3. Extract `PreviewDisclaimer`.
4. Extract `InlineActionMessage`.
5. Move `Section` into a local shared component file.
6. Add a tiny frontend `parseApiError(response)` helper in `frontend/lib/api.ts`.
7. Introduce constants for repeated preview banner text.
8. Add shared backend suggestion mapping helper for research and historical saves.
9. Add shared backend `validate_enum(value, allowed, field_name)` helper.
10. Add tests for Phase 4D guardrails before implementing apply.

## Risky Changes That Should Wait

- Full frontend page rewrite or routing restructure.
- Moving all API client functions at once.
- Splitting the entire backend service module in one PR.
- Generalizing all AI preview parsing into one complex abstraction immediately.
- Changing prompt wording while refactoring.
- Changing run logger semantics before Phase 4D.
- Refactoring source intelligence and implementing apply in the same broad change.
- Touching `investment_sources` or scanner registry as part of cleanup.

## Suggested Next Engineering Cleanup Sprint

Sprint name: Investment Research Cleanup 1 - Preview UI and API Helper Extraction

Goal:
Reduce frontend duplication before Phase 4D without changing behavior.

Scope:
- Extract `MetadataOnlyNotice`, `PreviewWarnings`, `PreviewDisclaimer`, and `InlineActionMessage`.
- Extract `Section`.
- Add `parseApiError(response)` or `requestJson` helper for Investment Research API calls.
- Keep all endpoint URLs, copy, payloads, and behavior unchanged.

Acceptance criteria:
- Research case detail page renders the same workflows.
- AI brief preview, quality assist, document analysis preview, source intelligence preview, and proposal review still use the same API calls.
- Metadata-only and preview-only messages remain visible.
- No deploy, scanner, cron, v2, publishing, or `investment_sources` behavior changes.

Recommended follow-up sprint:
Investment Research Cleanup 2 - Backend AI Preview Helper

Scope:
- Extract run logger wrapper or AI preview helper, but not both in the same sprint unless the first extraction is very small.
- Add focused tests for unchanged behavior.

