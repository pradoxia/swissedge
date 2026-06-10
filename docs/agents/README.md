---
document_id: AGENTS_README
title: Agent Documentation Index
version: 0.1.1
status: active
owner: Dani
last_updated: 2026-06-08
source_of_truth: true
review_cycle: manual
---

# SwissEdge Agents

This folder contains the official per-agent documentation for SwissEdge. `docs/governance/AGENT_MODEL.md` is the high-level index; these files hold the maintainable agent definitions.

Current SwissEdge agents are documented personas and deterministic/read-only governance workers. They are not yet live Claude/LLM agents. The implementation distinction is defined in `docs/architecture/AGENT_IMPLEMENTATION_MODEL.md`.

## Official Agent Docs

| Agent | Slug | Room | Document |
| --- | --- | --- | --- |
| Fontana | `fontana` | Executive Office | `docs/agents/FONTANA.md` |
| Dani Weber | `weber` | Executive Office | `docs/agents/DANI_WEBER.md` |
| Edgar Scout | `edgar-scout` | Detection Room | `docs/agents/EDGAR_SCOUT.md` |
| Form Parser | `form-parser` | Evidence Lab | `docs/agents/FORM_PARSER.md` |
| Router Analyst | `router-analyst` | Detection Room | `docs/agents/ROUTER_ANALYST.md` |
| Case Builder | `case-builder` | Research Desk | `docs/agents/CASE_BUILDER.md` |
| Quality Sentinel | `quality-sentinel` | Quality Court | `docs/agents/QUALITY_SENTINEL.md` |
| Playbook Scribe | `playbook-scribe` | Playbook Workshop | `docs/agents/PLAYBOOK_SCRIBE.md` |

## Shared Guardrails

- Agents must not silently run without logging.
- Diagnostic governance agents remain read-only until explicitly approved otherwise.
- No agent may make investment recommendations as final user advice.
- No agent may use buy/sell language in product output.
- Human approval is required for promotion, publishing, verification, scanner changes, cron changes, and governance mutation.

## Changelog

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 0.1.1 | 2026-06-08 | Codex | Clarified that current agents are personas and deterministic/read-only governance workers, not live Claude/LLM agents. |
| 0.1.0 | 2026-06-08 | Codex | Initial per-agent documentation index. |
