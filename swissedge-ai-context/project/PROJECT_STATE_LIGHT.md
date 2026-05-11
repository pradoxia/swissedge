# SwissEdge — AI-Safe Project State Light

## Current Strategic Direction

SwissEdge is moving toward:

- Investment Platform V2.
- AI-Safe Context Architecture.
- Agent Ops & Learning Layer.
- Fontana CTO / Project Governor.

## Investment Platform V2 Progress

- Sprint A: scanner funnel diagnostics and truthful Radar Status.
- Sprint B: Research Inbox read-only.
- Sprint B.1: Research Inbox UI polish.
- Sprint C: V2 ResearchCase metadata.
- Sprint C.1: deploy script and deployment notes cleanup.
- Sprint D: V2 metadata detail panel and Internal Audit read-only.
- Sprint E: manual Evaluation/SpecialSituation to V2 ResearchCase bridge.
- Sprint F: AI-safe context folder and documentation layer.
- Sprint G: Agent Ops + Fontana architecture docs (docs/agent-ops/, swissedge-ai-context/agent-ops/).
- Sprint G.1: Agent Ops implementation specs completed (DATA_MODEL, API_SPEC, METRICS, UI_SPEC, FONTANA_CTO, ROUTING_AUDITS, ADRs).
- Sprint H: Agent Ops backend foundation deployed — six additive tables, read-only API, proposal PATCH, fail-safe logger skeleton. Revision `e5f6a7b8c9d0` is documented as applied in 2026-05-10 closeout docs.
- Sprint H.1: Deploy script guard — Agent Ops migration and module allowlist verified/applied before manual deploy.
- Sprint I: `/agent-ops` Mission Control UI deployed and smoke-tested. Read-only except proposal status review.
- Sprint J: Agent Ops PATCH behavior and fail-safe logger tests hardened locally.
- Sprint K: Agent Ops logger isolation implemented locally with nested transactions/SAVEPOINTs; scanner/evaluator integration remains not approved.
- Sprint L: `/agent-ops` UI hygiene improved locally.
- Sprint M: Agent Ops deployed-state verification documented.
- Sprint N: proposal review logging implemented as narrow Agent Ops observer activity; reviewer-note-only PATCH does not create activity.
- Sprint O: manual Evaluation/SpecialSituation -> ResearchCase creation logging implemented as narrow Agent Ops observer activity.
- Sprint Q: SEC EDGAR Detection Core implemented and production manual validation completed. It creates or updates minimal `SpecialSituation` detections for P1 official SEC signals only (`SC TO-T`, `SC TO-I`, `Form 10`, and 8-K liquidation/dissolution metadata signals). `SpecialSituation` is the initial detection object. Detected does not mean evaluated. It does not call AI, create ResearchCases, trigger `/scan`, enable evaluator v2 globally, publish, or use external sources.
- Sprint Q.1: manual cleanup CLI added for historical false SEC detections from the pre-Hotfix-2 validation bug. It is dry-run by default and delete requires explicit confirmation.
- Sprint R: scheduled SEC EDGAR intake is enabled through cron after Dani manual approval. Initial frequency is twice daily at 07:00/19:00 UTC with a 168-hour lookback. Rate limit remains one SEC request every five seconds and dedupe prevents repeated `SpecialSituation` creation. No live AI, no `/scan`, no evaluator v2 global enablement, no ResearchCase auto-creation, no public publishing, no document body fetching, and no external sources.
- Sprint S: SpecialSituation methodology workspace foundation implemented locally. New SEC detections attach `evaluation.methodology_workspace` snapshots with fixed checklist and required-resource templates for P1 signals. Existing SEC detections can be backfilled manually. Frontend route `/investment/situations/[id]` displays detection summary, methodology checklist, required resources, progress, and planned next actions. Templates are based on processed artifacts and marked `requires_course_review=true`. No live AI, no web crawling, no PDF download, no document body fetching, no automatic verification, no ResearchCase auto-creation, no public publishing, no cron change, and no `/scan`.
- Sprint T: Resource Scout v1 implemented locally as a manual CLI and safe manual resource endpoint. It stores `resource_candidates` and `search_suggestions` inside `evaluation.methodology_workspace`, creates candidates from existing SEC metadata, updates clearly mapped required resources to `candidate_found`, and never marks checklist items verified. No broad web discovery, no crawling, no PDF download, no SEC document body fetching, no article text storage, no cron/autonomous scouting, no live AI, no ResearchCase auto-creation, no public publishing, and no `/scan`.
- Sprint U: Kanban Actions + Evidence Mapping implemented locally. Workflow status is stored in `evaluation.methodology_workspace.workflow_status`; manual resource review can link candidates to required resources/checklist items and mark linked material `evidence_found`. `evidence_found` does not mean verified, evaluated, or recommended. No cron modification, `/scan`, live AI, evaluator v2 global enablement, ResearchCase auto-creation, web crawling, PDF download, document body fetching, public publishing, or Marketplace/Sales changes.
- Sprint V: manual SpecialSituation -> ResearchCase promotion implemented and production-validated after hotfix. Endpoint `POST /api/investment/situations/{id}/promote-to-research-case` creates an idempotent ResearchCase for deeper research, stores `research_case_id` in `evaluation.methodology_workspace`, snapshots detection/workspace context into `ResearchCase.brief`, and creates conservative initial tasks/sources. Promotion is manual only and does not evaluate, recommend, publish, create public drafts, call live AI, enable evaluator v2 globally, crawl, download PDFs, fetch document bodies, modify cron, or call `/scan`.
- Sprint W: SEC EDGAR to ResearchCase milestone closeout and GitHub sync preparation. Current active flow is `SEC EDGAR cron -> SpecialSituation -> Kanban -> checklist/resources -> evidence mapping -> manual ResearchCase promotion`. Next recommended phase is ResearchCase Evaluation Preparation / Deep Research Assist, without automatic evaluation.
- Sprint X-A: Compact Kanban Overview implemented for `/investment/situations`. The page now defaults to a compact responsive Kanban overview with phase counts, top cases per phase, preserved filters, and a detailed board toggle. Frontend-only; no backend, migration, cron, scanner, live AI, evaluator, ResearchCase automation, publishing, or Marketplace/Sales changes.
- Sprint X-B: ResearchCase Evaluation Preparation / Deep Research Assist implemented locally. New read-only endpoint `GET /api/investment/research-cases/{id}/evaluation-prep` returns a deterministic metadata-only readiness package. Frontend `/investment/research/[id]` shows readiness level, missing required resources, checklist gaps, source quality notes, and manual next actions. This is preparation only: no live AI, no evaluator v2 global enablement, no automatic evaluation, no recommendations, no publishing, no crawling/PDF/document body fetching, no `/scan`, and no cron change.

## Current Status Summary

- Investment Platform V2 is the active product track.
- AI-Safe Context folder structure is complete; all 25 expected context files exist.
- Playbook and evaluator files in AI-safe context are placeholders and need future sanitization before implementation use.
- Agent Ops + Fontana documentation is complete enough to guide backend/UI work.
- Agent Ops backend foundation and `/agent-ops` UI are documented deployed and smoke-tested.
- Agent Ops migration `e5f6a7b8c9d0` is documented as applied in the 2026-05-10 closeout docs.
- Agent Ops activity may contain narrow observer events from proposal review and manual ResearchCase creation if Sprint N/O are deployed; diagnostics/proposals may still be empty unless manually created.
- SEC EDGAR manual detection is validated and scheduled SEC EDGAR intake is enabled through cron. Sprint S/T/U/V methodology, resource, Kanban, evidence-mapping, and manual ResearchCase promotion features are complete and production-validated through manual promotion. EDGAR is operational.
- Resource Scout v1 is manual only. It stores candidates/search suggestions but does not browse the web, crawl, download PDFs, or verify evidence.
- ResearchCase promotion is manual only. Detection does not auto-create ResearchCases, and promotion does not evaluate, recommend, publish, or create public drafts.
- `investment_sources` still does not control scanner execution.

## Current Operating Model

`SEC EDGAR cron -> SpecialSituation -> Kanban -> checklist/resources -> evidence mapping -> manual ResearchCase promotion -> ResearchCase deep research`

The current system has an operational SEC-driven detection path. Evaluation remains manual/preparatory: source-driven detection creates `SpecialSituation` records, and ResearchCase promotion is a separate manual action.

## Current Guardrails

- No global v2 evaluator.
- No cron change.
- No `/scan` unless explicitly approved.
- No live AI unless explicitly approved.
- No auto deploy.
- No auto publish.
- No secrets in AI context.
- No raw course materials.

## Next Strategic Sprints

- Sprint W/X-B GitHub sync after final review: commit/push only when Dani chooses to run it.
- Claude review of Sprint X-B ResearchCase Evaluation Preparation.
- Later: controlled official-source discovery, SEC intake observability, external manual intake, Fontana CTO reports, market monitoring.
