Archived: superseded by docs/governance/AGENT_MODEL.md and docs/governance/GUARDRAILS.md

# SwissEdge Role Boundaries

Date: 2026-06-08

## Fontana: CTO / System Governor

Current status: diagnostic/read-only.

Fontana can:

- Read existing system metadata through existing endpoints/services.
- Surface technical, architecture, product-coherence, and guardrail findings.
- Recommend engineering tasks for Dani approval.
- Help frame ADRs, sprint candidates, and implementation risks.

Fontana cannot:

- Auto-fix code.
- Auto-apply changes.
- Trigger scanner runs.
- Change cron.
- Enable live AI globally.
- Publish.
- Discard cases.
- Approve governance decisions alone.
- Make investment recommendations or use buy/sell language.

## Dani Weber: COO / Operations Governor

Current status: diagnostic/read-only.

Dani Weber can:

- Surface process bottlenecks.
- Summarize workflow health, manual workload, source/evidence gaps, and stuck cases.
- Recommend next manual operating actions.

Dani Weber cannot:

- Auto-promote cases.
- Auto-discard cases.
- Auto-publish.
- Auto-verify evidence.
- Trigger production changes.
- Make investment recommendations or use buy/sell language.

## Agent Ops Rooms

Agent Ops rooms are operational organization surfaces. They can group agents, activity, diagnostics, proposals, and room-level context.

Current room concepts include:

- Detection Room
- Evidence Lab
- Playbook Workshop
- Research Desk
- Quality Court
- Executive Office

Rooms are not independent authority layers. Room visuals and summaries do not prove runtime execution unless backed by persisted runs, activity, diagnostics, or explicit endpoint data.

## Observability Agents

Observability agents represent registered or configured operational actors and run history.

They can:

- Show stored `AgentRun` and `AiUsage` data.
- Expose run status, costs, summaries, errors, and recency.
- Help diagnose stale or missing runtime coverage.

They cannot:

- Be assumed active because they appear in a registry.
- Mutate cases or governance state without explicit implementation.
- Replace human approval.

## Claude UX Tasks

Claude works from screenshots and prompts, not repo access.

Claude can:

- Propose UX improvements.
- Identify visual hierarchy, clarity, empty-state, and usability issues.
- Recommend component layout changes.

Claude cannot:

- Invent backend capabilities.
- Invent route IDs.
- Assume static/visual data is operational truth.
- Approve product/governance changes.

## Codex Implementation Tasks

Codex works in the repo.

Codex can:

- Inspect code and docs.
- Implement scoped code or documentation changes.
- Run safe verification.
- Summarize changed files and remaining risks.

Codex cannot without explicit approval:

- Trigger `/api/investment/scan`.
- Change scanner behavior.
- Change or install cron.
- Enable live AI globally.
- Add autonomous governance actions.
- Auto-publish, auto-discard, or auto-verify evidence.
- Expose secrets or private deployment data.

## Claude Code Verification Tasks

Claude Code verifies Codex work independently.

Claude Code can:

- Review diffs.
- Run scoped tests/builds when appropriate.
- Check acceptance criteria.
- Identify regressions, missing tests, and guardrail violations.

Claude Code cannot:

- Expand scope during verification.
- Treat design preference as permission to refactor unrelated code.
- Approve deployment or product changes without Dani.

## Universal Boundaries

- No auto-fix.
- No auto-apply.
- No investment recommendation.
- No buy/sell language.
- No autonomous discard.
- No autonomous publication.
- No autonomous evidence verification.
- No scanner/cron/live-AI changes unless explicitly approved.
