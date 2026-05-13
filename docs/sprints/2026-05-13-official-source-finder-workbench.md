# Sprint AJ - Official Source Finder & SEC Filing Locator Workbench

Date: 2026-05-13

## Summary

Sprint AJ adds a deterministic Official Source Finder for SpecialSituations and ResearchCases.

The workbench helps Dani manually locate official case evidence from stored metadata:

- original SEC filing URL when already stored
- CIK, accession number, filing type, filing date, company, ticker, and playbook context
- official links already stored as metadata
- missing required resources and checklist evidence
- manual locator steps
- copyable manual search queries

## Backend

New read-only service:

- `backend/services/investment/official_source_finder.py`

New GET-only endpoints:

- `GET /api/investment/situations/{id}/official-source-finder`
- `GET /api/investment/research-cases/{id}/official-source-finder`

The service uses existing stored SpecialSituation, ResearchCase, methodology workspace, resource candidate, search suggestion, and Evidence Links metadata. It does not write to the database.

## Frontend

New shared panel:

- `frontend/app/components/OfficialSourceFinderPanel.tsx`

Integrated into:

- `/investment/situations/{id}`
- `/investment/research/{id}`
- `/investment/situations` Kanban cards, using already-loaded JSON only
- `/investment/intelligence`
- `/agent-ops`
- `/agent-ops/rooms/{id}`

## Guardrails

This sprint is manual and deterministic.

It does not:

- run web searches
- fetch SEC documents
- download PDFs
- crawl websites
- verify links automatically
- call AI
- call evaluator v2
- call scanner or `/scan`
- change cron
- run schedulers
- create or promote ResearchCases automatically
- evaluate cases
- recommend investments
- publish or create public drafts
- change Marketplace/Sales behavior
- add a migration
- deploy

Candidate sources and `evidence_found` rows remain unverified until human review.

## Validation

Required validation before handoff:

- targeted backend tests for Official Source Finder
- `npm run build` in `frontend/`
- `git diff --check`
- secret hygiene check on current diff
- confirm `.claude/` remains untracked
