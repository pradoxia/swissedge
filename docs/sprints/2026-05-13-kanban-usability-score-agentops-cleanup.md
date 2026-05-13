# Sprint AK - Kanban Usability, Score Guidance & Agent Ops Cleanup

Date: 2026-05-13

## Summary

Sprint AK improves the daily research workflow without adding automation.

Implemented locally:
- Kanban `Hide empty phases` now works in the default Pipeline board and Compact Overview.
- Kanban cards are simplified for scanning, with advanced source/documentation details behind a small Details toggle.
- Filters now cover search text, filing type, special situation type, and workflow phase.
- Pipeline board has visible horizontal guidance, a visible scrollbar, and `Scroll left` / `Scroll right` buttons.
- Manual query copy uses `navigator.clipboard.writeText`, scoped copied feedback, and a manual-select failure message.
- Intelligence Score now explains how Detection, Structuring, and Risk Discipline scores improve through manual documentation work.
- Agent Ops replaces the large Scheduler/Frequency panel with Agent Workload & Next Manual Actions.
- Long agent names, room keys, badges, and labels wrap safely inside cards.

## Guardrails

- Frontend/docs usability pass only.
- No backend automation.
- No live AI.
- No evaluator activation.
- No scanner or `/api/investment/scan`.
- No cron or scheduler execution.
- No automatic evaluation, ResearchCase creation, promotion, source verification, publishing, public draft creation, crawling, PDF download, or SEC document body fetching.
- No investment recommendation or buy/sell/hold language.
- No deployment was performed.

## Manual Validation Notes

- Hide Empty Phases ON hides empty columns after filters are applied.
- Hide Empty Phases OFF shows all workflow phases.
- Search, filing type, special situation type, and workflow phase filters affect cards and counts.
- Kanban cards remain skimmable by default.
- Horizontal board navigation is visible and scroll buttons only move the board.
- Copy query shows `Copied` or `Copy failed - select manually`.
- Intelligence Score explains how to improve preparation quality without auto-fix buttons.
- Agent Ops shows useful workload/next manual actions and keeps scheduler info compact.
- Long labels no longer overflow card boundaries.
