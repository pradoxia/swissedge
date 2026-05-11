# Sprint Y — Evidence Links & Research Traceability

Date: 2026-05-11

## Goal

Make source/evidence provenance visible before any evaluation happens.

SwissEdge can now show where stored metadata came from across the SEC EDGAR to ResearchCase workflow:

- original SEC filing/source links.
- resource candidate links.
- required-resource support links.
- checklist evidence links.
- ResearchCase source/document links.
- metadata-only labels and guardrails.

## Backend

Added deterministic metadata-only normalizer:

- `backend/services/investment/evidence_links.py`

Added read-only endpoints:

- `GET /api/investment/situations/{id}/evidence-links`
- `GET /api/investment/research-cases/{id}/evidence-links`

Also added a compact `evidence_links_summary` to:

- `GET /api/investment/research-cases/{id}/evaluation-prep`

## Frontend

Added shared traceability UI:

- `frontend/app/components/EvidenceLinksPanel.tsx`

Updated:

- `/investment/situations/[id]`
- `/investment/research/[id]`

The panels show metadata-only source links, origins, statuses, required-resource IDs, checklist IDs, SEC metadata, and guardrails.

## Guardrails

- Metadata-only.
- No document body fetching.
- No crawling.
- No PDF downloads.
- No external HTTP calls.
- No automatic evaluation.
- No automatic verification.
- No recommendations.
- No publishing.
- No public draft creation.
- No `/api/investment/scan`.
- No cron change.
- No evaluator v2 global enablement.
- No live AI.
- No ResearchCase auto-creation.

## Product Language

- Source link means where the metadata/evidence came from.
- Candidate source does not mean verified.
- Evidence found does not mean verified.
- Research traceability does not mean evaluation.
- No investment recommendation is generated.

## Known Limitations

- The normalizer only uses URLs already stored in DB/JSON.
- If SEC metadata exists without a stored filing URL, SwissEdge shows a metadata-only note instead of inventing a URL.
- Duplicate URLs are grouped by origin/source type so the same URL can still appear distinctly as a promotion snapshot source and a ResearchCase source.
- Search suggestions remain suggestions; they are not fetched or converted into web results.
