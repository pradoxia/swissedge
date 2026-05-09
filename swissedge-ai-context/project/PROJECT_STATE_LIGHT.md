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
- Sprint H: Agent Ops backend foundation — six additive tables, read-only API, proposal PATCH, fail-safe logger skeleton. Revision e5f6a7b8c9d0. Pending deploy.
- Sprint H.1: Deploy script guard — Agent Ops migration and modules added to deploy allowlist. No runtime code changed.

## Current Operating Model

`investment_sources -> connector/intake -> preliminary ResearchCase -> initial course-grounded evaluation -> Research Inbox -> enrichment -> deep research / archive / public draft`

The current system is in transition. Source-driven intake is not fully active yet, and SEC scanner behavior is not automatically creating ResearchCases.

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

- Sprint I: `/agent-ops` Mission Control UI (read-only, proposal status review).
- Later: Fontana CTO report generation.
- Later: SEC source-driven ResearchCase intake.
- Later: Fail-safe logger wired into scanner/evaluator flows (requires session isolation fix first).
