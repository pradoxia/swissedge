# SwissEdge Architecture Overview

## System Layers

- Core/private runtime: backend, frontend, database models, migrations, deployment scripts, private configuration, and operational infrastructure.
- AI-safe context: curated documentation for AI assistants. It excludes secrets, private infrastructure, raw course materials, and production-sensitive logs.
- Public site: future public-facing research experience. This track is paused.

## Investment Platform V2

Investment Platform V2 centers `ResearchCase` as the primary durable work object.

Research Inbox is the main work queue. It shows ResearchCases with source origin, intake method, evidence level, official-source status, methodology status, readiness, tasks, documents, sources, duplicate state, and follow-up needs.

`investment_sources` will become the operational source registry. It is intended to describe SEC EDGAR, newsletters, email alerts, RSS feeds, websites, company IR pages, manual inputs, and future APIs.

Scanner diagnostics exist. SEC source-driven intake is future work. Source-driven intake is not fully active yet.

## Agent Ops Direction

Agent Ops will organize work into rooms, agents, diagnostics, learning proposals, and Fontana CTO reports.

Future concepts:

- Rooms for Radar, Evidence Lab, Research Desk, Quality Court, Playbook Workshop, and Agent Ops.
- Agents with observable responsibilities and strict guardrails.
- Diagnostics for funnel health, routing, evidence quality, stale cases, duplicates, and methodology gaps.
- Learning proposals that recommend changes but never auto-apply.
- A future `/agent-ops` Mission Control route.

## Safety

SwissEdge uses human review as the production boundary. AI may observe, analyze, draft, propose, and prepare code or documents. Dani approves and deploys manually. No assistant may autonomously change production, cron, evaluator defaults, scans, publishing, or infrastructure.
