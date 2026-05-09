# ADR-0001 - AI-Safe Context Architecture

## Status

Accepted

## Context

SwissEdge needs continuity across ChatGPT, Claude, Codex, and future assistants without exposing secrets, private infrastructure details, raw production logs, raw course materials, or huge conversation history.

## Decision

Create `swissedge-ai-context` as a curated AI-safe documentation layer. It contains sanitized project state, architecture summaries, playbook placeholders, evaluator placeholders, Agent Ops concepts, Fontana notes, and publication guardrails.

## Consequences

- AI sessions can start from a stable safe context.
- Runtime code and private infrastructure remain separate.
- The AI-safe context can intentionally differ from main implementation state docs.
- Sanitization discipline becomes part of project operations.

## Guardrails

- No `.env` files.
- No API keys, tokens, credentials, DB dumps, private IPs, private URLs, Tailscale details, or VPS details.
- No raw production logs with sensitive data.
- No raw course transcripts, audio, video, or copyrighted raw course text.
- No autonomous production changes.

## Alternatives Considered

- Use only the main repo docs: rejected because they may contain implementation detail not suitable for broad AI context.
- Use long chat transcripts as memory: rejected because they are brittle and hard to sanitize.

## Related Documents

- `swissedge-ai-context/README.md`
- `swissedge-ai-context/project/PROJECT_STATE_LIGHT.md`
- `docs/PROJECT_STATE_LIGHT.md`

## Date

2026-05-09
