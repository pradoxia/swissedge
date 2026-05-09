# SwissEdge — AI-Safe Project State

This is the long-form AI-safe project state. It intentionally excludes secrets, infrastructure identifiers, private URLs, IPs, credentials, raw `.env` content, production logs, and raw course materials.

## Current Strategic Direction

SwissEdge is evolving into a private investment research operating system centered on source-driven ResearchCases and safe multi-agent operations.

Active strategic layers:

- Investment Platform V2.
- AI-Safe Context Architecture.
- Agent Ops & Learning Layer.
- Fontana CTO / Project Governor.

Paused tracks:

- Public site.
- Public publishing automation.
- Marketplace/Sales runtime changes.

## Investment Platform V2

Current operating model:

`investment_sources -> connector/intake -> preliminary ResearchCase -> initial course-grounded evaluation -> Research Inbox -> enrichment -> deep research / archive / public draft`

Current reality:

- ResearchCase is the primary durable work object.
- Research Inbox exists as a read-only operating queue.
- V2 metadata exists on ResearchCase.
- Manual Evaluation/SpecialSituation to ResearchCase bridge initializes V2 metadata for SEC/evaluation-linked cases.
- SEC source-driven automatic ResearchCase intake is future work.
- Scanner behavior is not changed by this context layer.

## Guardrails

- No global evaluator v2.
- No cron changes unless explicitly approved.
- No `/api/investment/scan` unless explicitly approved.
- No live AI unless explicitly approved.
- No auto deploy.
- No auto publish.
- No secrets in AI context.
- No raw course materials in AI context.

## Continuity Note

Use `PROJECT_STATE_LIGHT.md` for compact handoff and this file for safer strategic context. Runtime details remain in the private core repo and require human review before being summarized here.
