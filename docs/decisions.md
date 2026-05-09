# SwissEdge — Architecture Decision Log

## D001 — FastAPI is the source of truth

**Decision:** All business logic, DB writes, AI calls, and validation live in the FastAPI backend. No other component (OpenClaw, Telegram, scripts) duplicates or shadows this logic.

**Why:** Single source of truth prevents drift. OpenClaw is ephemeral; FastAPI + PostgreSQL are durable.

**Consequence:** Every new feature is an endpoint first. OpenClaw/Telegram are callers, not owners.

---

## D002 — OpenClaw is an operator, not business logic

**Decision:** OpenClaw routes Telegram messages to FastAPI endpoints and formats responses. It does not evaluate investments, generate listings, or query the DB directly.

**Why:** OpenClaw is a Node.js general-purpose tool maintained separately. Putting logic there creates a hard-to-audit, hard-to-test black box.

**Consequence:** OpenClaw commands are thin wrappers: receive text → call FastAPI → return response.

---

## D003 — Claude Code is engineer, not architect

**Decision:** Claude Code implements exactly what is specified. If a spec is ambiguous, it asks Dani. It does not make architecture decisions unilaterally.

**Prompt Objection Check:** Before implementing anything non-trivial, confirm the spec is unambiguous. If it is, proceed. If not, surface the ambiguity in one question.

**Why:** Unilateral AI decisions on a production system are unsafe and hard to audit.

---

## D004 — Observability before autonomy

**Decision:** No agent can be promoted to "active" status unless its runs are fully logged in `agent_runs` and AI usage is logged in `ai_usage` (where applicable).

**Why:** You cannot trust what you cannot measure. Costs and failure rates must be visible before automation is widened.

**Consequence:** Every new FastAPI endpoint that calls AI or an external API must call `run_logger.start_run()` / `finish_run()` / `fail_run()`. Observability calls are wrapped in try/except — a DB failure must never break business logic.

---

## D005 — Human approval for risky actions

**Decision:** Private Telegram research alerts sent only to Dani, clearly marked as educational/research, may be automated. Everything else with external or irreversible impact requires explicit human confirmation before execution: listing publish, public publication, external content sharing, personal data sharing, accepting offers, arranging meetings or pickups, VPS deploys, database migrations, destructive DB operations, security or secret changes, and git push to main.

**Why:** The blast radius of an automated mistake in production is high. Trust is earned incrementally.

**Consequence:** Phase 1 marketplace = draft-only. Claude Code never runs deploy commands without an explicit "deploy" or "apply" instruction in the current session.

---

## D006 — No secrets in Git or docs

**Decision:** Credentials, tokens, IPs, Tailscale addresses, and raw `.env` content are never committed to the repository or written into documentation.

**Why:** The GitHub repo may become public or be shared later, so it must be treated as public-safe. A leaked token is a permanent incident until rotated.

**Consequence:** Docs use `[PLACEHOLDER]` for credential references. Scripts with secrets live in `scripts/vps_config.py` (local only, git-ignored).

---

## D007 — Course material is private

**Decision:** Raw course transcripts, audio, and video are never committed to Git. The `course/` and `Curso de Arte de Invertir/` directories are git-ignored.

**Why:** The course is copyrighted material. Publishing it would violate IP rights.

**Consequence:** `course_index/` is git-ignored by default. Raw transcripts, audio, video and all generated course derivatives stay on the VPS only. Only sanitized, non-copyrighted methodology schemas, generic checklists and high-level summaries may be committed after explicit review.

---

## D008 — PostgreSQL is runtime source of truth for investment sources

**Decision:** The list of active investment sources (SEC EDGAR queries, news feeds, etc.) is stored in the `investment_sources` DB table. It is never hardcoded in Python.

**Why:** Sources need to be added/removed without code deploys. Dani can manage them via Telegram commands or the API.

**Consequence:** The scanner reads from DB at runtime. New sources are added via `POST /api/investment/sources`.

---

## D009 — Marketplace automation starts with drafts

**Decision:** Phase 1 listing generation produces a draft for human review. Auto-publish is not enabled. The progressive trust score system (score < 10 → always draft) is the gating mechanism for Phase 2.

**Why:** A wrong price or misleading listing on Tutti.ch damages reputation. Safety must come before speed.

**Consequence:** The publish step is always manual in Phase 1. The safety module (`safety.py`) validates all outgoing messages for PII regardless of trust score.

---

## D010 — Investment outputs are research, not financial advice

**Decision:** Every investment evaluation output must include: uncertainty level, risk list, source links, course chapter references, and the legal disclaimer "Este análisis es educativo. No es asesoramiento financiero."

**Why:** Legal and ethical requirement. The platform is a research tool, not a licensed advisor.

**Consequence:** The disclaimer is appended at the FastAPI layer, not optionally by the caller. Evaluator prompts explicitly frame output as educational analysis.

---

## D011 — Mission Control is the primary operational control layer

**Decision:** The Telegram interface (`mission control`, `agentes`, `agente <name>`, `cron`, `costes`, `errores`) is the primary way Dani monitors the platform in production. The observability API is the source; Telegram is the window.

**Why:** Dani is mobile-first. A dashboard frontend is lower priority than a working Telegram control layer.

**Consequence:** All observability endpoints have both JSON and `/text` variants. Text variants are optimized for Telegram: plain text, no Markdown formatting that triggers escaping bugs, truncated at 4000 chars.

---

## D012 — Token efficiency protocol

**Decision:** Claude Code sessions start by reading only `PROJECT_STATE.md`, `docs/decisions.md`, `CLAUDE.md`, and files directly relevant to the task. Full repo scans are prohibited.

**Why:** Unnecessary reads consume context and cost tokens. The handover files exist precisely to eliminate cold-start scanning.

**Consequence:** The session startup instruction in PROJECT_STATE.md §15 is the canonical entry point. Every session ends with `/cost` submission to `POST /api/observability/claude-session`.

---

## D013 — GitHub contains code, not operations

**Decision:** The GitHub repo contains source code, tests, and non-secret documentation. It does not contain: deployment scripts with credentials, VPS configuration, operational state files, session logs, or cost logs.

**Why:** The repo may become public or be shared later. Operational details (IPs, service names, token patterns) narrow the attack surface if kept off GitHub.

**Consequence:** Git-ignored files are listed in PROJECT_STATE.md §12. SWISSEDGE.md (OpenClaw instruction file) lives on VPS only.

---

## D014 — Course Methodology Extraction required before serious investment automation

**Decision:** The investment evaluator must not be promoted to trusted-output status until the "El Arte de Invertir" course has been processed into structured playbooks and checklists in `course_index/`, and the evaluator prompt has been rebuilt using those playbooks.

**Why:** The current evaluator uses a generic prompt. Its output is plausible but not grounded in the actual methodology Dani paid to learn. Trusting shallow output for real investment decisions is worse than having no evaluator.

**Consequence:** Course Methodology Extraction is complete (2026-04-28). The evaluator upgrade is still blocked by two further prerequisites: (1) Timestamp Repair Sprint — real audio timestamps for LF-split chapters; (2) Global Methodology Synthesis — cross-chapter taxonomy, global playbooks, and evaluation_schema.json. Do not upgrade the evaluator until both are done. `foundational_analysis` chapters (14, 15, 17, 22) are excluded from routing and must not feed situation-specific playbooks. `course_index/` remains private/gitignored at all times.

---

## D016 — Investment platform is a research desk, not a signal generator

**Decision:** SwissEdge Investment is defined as a private research desk for special situations. Its purpose is to identify, investigate, document, study historical cases, improve source intelligence, and produce manually approved educational content. It is not a trading signal generator, stock screener, or automated buy/sell recommendation engine.

**Why:** The v1/v2 evaluator pipeline produces plausible structured output but does not yet constitute a full research workflow. Dani needs a system that supports the full lifecycle: detection → deep investigation → documentation → historical learning → source improvement → optional publication. Framing the platform as a "scanner + evaluator" was too narrow and led to a dead-end architecture where each evaluation was self-contained with no persistent research value.

**Consequence:** Six new data models are introduced (`ResearchCase`, `ResearchTask`, `ResearchDocument`, `ResearchSource`, `HistoricalCase`, `PublicArticleDraft`). A seventh model (`SourceIntelligenceSuggestion`) was added during data model design. Four new agents are defined (`situation_research_agent`, `historical_case_agent`, `source_intelligence_agent`, `publisher_agent`). The v1 evaluator remains production default; the new research agents are layered on top — they do not replace the evaluator. All investment output continues to include the mandatory disclaimer. All publishing requires explicit manual approval. Full spec in `docs/investment-research-platform-redesign.md` and `docs/investment-research-data-model.md`.

---

## D015 — Every sprint updates handover state

**Decision:** At the end of every Claude Code sprint, `PROJECT_STATE.md` must be updated to reflect current phase, production status, known issues and next tasks. `docs/decisions.md` must be updated only if an architecture decision changed.

**Why:** Stale handover files cause hallucinations, wasted context reads and cold-start confusion in future sessions. The files exist to make sessions restartable without re-scanning the repo.

**Consequence:** No sprint is closed without a PROJECT_STATE.md update. Confirm no secrets were introduced before closing.

---

## D017 — buy_sell_language_check gates PublicArticleDraft approval

**Decision:** A `PublicArticleDraft` cannot advance from `draft` to `approved` unless `buy_sell_language_check = true`. This flag is set by the `publisher_agent` prompt response and validated at the API layer before any status transition. If `false`, the API returns the detected phrases so Dani can correct the draft.

**Why:** The no-buy/sell-language requirement (D010, D016) must be mechanically enforced — a prompt instruction alone is insufficient since LLMs can slip buy/sell phrasing. A database flag makes the check auditable and reversible.

**Consequence:** `publisher_agent` must perform a language check pass and include a `buy_sell_language_check` boolean in its output. The FastAPI PATCH endpoint for `PublicArticleDraft` must assert this flag before allowing the `approved` transition. The check is also applied at `ResearchCase.brief` write time as a soft warning (log only — does not block brief generation).
