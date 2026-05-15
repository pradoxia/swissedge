# Sprint AN+AO — Product Surface Simplification + SEC EDGAR Document Acquisition v1

Date: 2026-05-15

## Source of Truth

This sprint follows `docs/product/SWISSEDGE_PRODUCT_OPERATING_MODEL.md`.

Current operating flow:

Detect -> Triage -> Document -> Evidence Review -> Promote -> Evaluate -> Candidate / Watchlist / Reject.

## Product Surface Classification

### Core Surfaces

- Mission Control
- Kanban — Special Situations
- SpecialSituation detail
- Research Cases
- ResearchCase detail
- Intelligence KPIs

These surfaces support the daily SEC-driven research workflow: detected signals, triage, documentation, manual promotion, evidence review, and operational view labels.

### Supporting Surfaces

- Sources
- Agent Ops / Executive Office
- Dani Weber Office — COO
- Fontana Office — CTO
- Historical Cases / Analogues
- Publishing Drafts, manual only
- Radar Status

These surfaces support governance, source posture, deterministic audit, historical context, and manual editorial preparation.

### Advanced / Legacy Surfaces

- Evaluations Queue
- Evaluation detail pages
- Investment Watchlist
- Source Intelligence
- Agent Roster
- Evaluator v2 manual preview

These remain available, but they are not the primary investment workflow. Evaluator v2 remains manual-preview only and is not globally enabled.

### Paused Surfaces

- Marketplace / Sales
- Public-site implementation

These are preserved and de-emphasized from the investment workflow. No Marketplace/Sales functional changes or public-site implementation were made.

## Rationale

The product surface should make the active workflow obvious without deleting older capability. `SpecialSituation` is a detected signal and triage object. `ResearchCase` is the durable deep research object. `Watchlist` is a ResearchCase state/view label, not a separate entity. Candidate / Watchlist / Reject are operational labels for human review, not investment advice.

## SEC EDGAR Document Acquisition v1

Manual SEC acquisition adds read-only previews and manually triggered SEC-only metadata acquisition for SpecialSituations and ResearchCases.

Endpoints:

- `GET /api/investment/situations/{id}/sec-document-acquisition-preview`
- `POST /api/investment/situations/{id}/sec-document-acquisition`
- `GET /api/investment/research-cases/{id}/sec-document-acquisition-preview`
- `POST /api/investment/research-cases/{id}/sec-document-acquisition`

The POST endpoints may write metadata candidates only:

- SpecialSituation: appends official SEC metadata candidates to `methodology_workspace.resource_candidates`.
- ResearchCase: creates `ResearchDocument` and `ResearchSource` metadata rows.

Evidence remains unverified until manual review. The acquisition does not complete checklist items, mark sources verified, promote ResearchCases, evaluate, publish, run AI, run the scanner, or change cron/scheduler behavior.

## Deployment Note

Because Sprint AO adds `backend/services/investment/sec_document_acquisition.py`, Dani must update the private local `scripts/deploy_backend_files.ps1` allowlist before backend deployment. That script is private/gitignored and was not edited.
