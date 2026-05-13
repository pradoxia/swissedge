# Sprint AM - Case Completion Workbench & Manual Review Workflow

Date: 2026-05-13

## Summary

Sprint AM adds a deterministic, read-only Case Completion Workbench for SpecialSituations and ResearchCases.

Implemented locally:
- Backend service `backend/services/investment/case_completion.py`.
- Read-only endpoints:
  - `GET /api/investment/situations/{id}/completion-workbench`
  - `GET /api/investment/research-cases/{id}/completion-workbench`
- Shared frontend component `CaseCompletionWorkbench`.
- SpecialSituation and ResearchCase detail pages show:
  - completion level
  - completion score
  - blocking items
  - next manual actions
  - what each action improves
  - score improvement plan
  - section status links
  - guardrails
- Kanban cards show compact completion status from already-loaded JSON only.
- Intelligence Score card links to the completion plan.
- Agent Ops documents Case Completion Coach as manual/observer-only.

## Guardrails

- Deterministic/read-only.
- No automatic completion.
- No database writes.
- No live AI.
- No evaluator activation.
- No scanner or `/api/investment/scan`.
- No cron or scheduler execution.
- No automatic evaluation, ResearchCase creation, promotion, source verification, publishing, public draft creation, crawling, PDF download, SEC document body fetching, or external HTTP calls.
- No investment action language.
- Manual review remains required.

## Manual Use

The workbench helps Dani answer:
- What should I do next?
- Which required resources are blocking completion?
- Which candidate sources need review?
- Which checklist items need evidence?
- Which actions improve documentation quality, evidence coverage, and Intelligence Score?
- What must remain manual before relying on the case?

## Validation Notes

Targeted backend tests cover missing resources, candidate review actions, checklist mapping actions, ResearchCase score plans, completion score improvement, promoted case state, no investment action language, and no network client imports.
