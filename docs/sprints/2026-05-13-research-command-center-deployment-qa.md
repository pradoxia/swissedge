# Sprint AI - Research Command Center, Batch QA Polish & Deployment Verification UI

Date: 2026-05-13

## Summary

Sprint AI adds a read-only Research Command Center on Mission Control and a static Deployment Verification Checklist for Dani's post-deployment QA flow.

The Command Center explains the active workflow:

`SEC EDGAR -> SpecialSituation -> Kanban -> Missing Evidence Hunter -> ResearchCase -> Evaluation Preparation -> Evidence Links -> Intelligence Score -> Intelligence KPIs -> Fontana`

It also adds compact quick links across Kanban, Research Inbox, ResearchCases, Intelligence KPIs, Agent Ops, Radar Status, and Sources.

## UX Changes

- Mission Control now has a prominent Research Command Center section.
- Mission Control now has a manual Deployment Verification Checklist.
- Intelligence KPIs links back to Kanban, ResearchCases, Agent Ops, and Fontana.
- Agent Ops top navigation links to Intelligence KPIs.
- SpecialSituation detail quick links include Intelligence KPIs.
- ResearchCase detail header links to Kanban and Intelligence KPIs.
- Agent Ops room detail secondary panels now fail locally if activity/diagnostics/proposals/agents are temporarily unavailable.

## Guardrails

This sprint is read-only and does not trigger deployments.

It does not:

- call AI
- call evaluator v2
- call `/scan`
- change cron
- run a scheduler
- evaluate cases
- recommend investments
- publish or create public drafts
- crawl the web
- download PDFs
- fetch SEC document bodies
- create or promote ResearchCases automatically
- change Marketplace/Sales behavior
- add a migration
- deploy

Manual review remains required.

## Validation

Required validation before handoff:

- `npm run build`
- `git diff --check`
- secret hygiene check on current diff
- confirm `.claude/` remains untracked

Backend tests are not required for Sprint AI because the sprint is frontend/docs only.
