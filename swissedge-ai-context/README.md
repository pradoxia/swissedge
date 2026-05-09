# SwissEdge AI-Safe Context

## Purpose

This folder is the curated, safe context layer for AI assistants working on SwissEdge. It is designed for ChatGPT, Claude, Codex, future GPTs, and future internal agents that need project continuity without access to secrets, private infrastructure, huge conversation history, or raw copyrighted course material.

## Three-Layer Model

- `swissedge-core`: the real runtime/private system, including backend, frontend, database models, deployment scripts, private infrastructure, and operational secrets. This layer is not safe to share broadly with AI assistants.
- `swissedge-ai-context`: the AI-safe documentation and continuity layer. It contains sanitized architecture, state, roadmap, decisions, glossary, evaluator summaries, agent ops definitions, and publication rules.
- `swissedge-public`: the future public-facing research site. This track is paused until explicitly resumed.

## What This Folder Is For

- Context continuity across ChatGPT, Claude, Codex, and future GPTs.
- Safer prompts with curated project facts.
- Reducing dependence on giant conversations.
- Shared knowledge between assistants without leaking runtime details.
- Documentation-first architecture.
- Sprint continuity.
- Decision tracking.
- Future Agent Ops and Fontana CTO reporting.

## Project State Files

The `project/PROJECT_STATE_LIGHT.md` in this AI-safe context layer is a curated AI-safe summary. It is not a direct copy of `docs/PROJECT_STATE_LIGHT.md`. The two files may intentionally differ. Update the AI-safe summary when preparing context for AI sessions; update the main docs state when recording implementation state.

## What Must Never Be Included

- `.env` files.
- API keys.
- Tokens.
- Credentials.
- DB dumps.
- Private IPs.
- Private URLs.
- Tailscale details.
- VPS details.
- Production secrets.
- Raw production logs with sensitive data.
- Raw course transcripts.
- Raw audio/video.
- Copyrighted raw course text.

## Human-in-the-Loop Rule

AI can propose. Codex can prepare changes. Claude can review. Dani approves. Dani deploys manually.

No assistant or future agent may autonomously deploy, change production, modify cron, trigger scans, enable evaluator v2 globally, publish content, or apply infrastructure changes without explicit human approval.
