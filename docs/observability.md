# SwissEdge — Observability Design
> How the system tracks what every agent does, at what cost, with what outcome.
> Last updated: 2026-04-27.

---

## Principles

1. **Every important action creates an `agent_runs` record.** "Important" means: any AI call, any scan, any listing generation, any heartbeat, any engineering session.
2. **Every AI call creates an `ai_usage` record.** If the provider returns real token counts, store them. Otherwise estimate from character count and mark as `estimated`.
3. **No secrets in logs.** No API keys, passwords, or tokens in any observability field.
4. **No raw private data.** Store summaries, not full prompts with sensitive personal content. Filenames and company names are fine; personal user messages should be paraphrased.
5. **Observability must not break business logic.** All logging is wrapped in try/except. A DB write failure must not cause a scan or listing to fail.
6. **Investment sources are editable.** The scanner reads active sources from the `investment_sources` DB table. No hardcoding. Every scan logs which sources were checked and how many results each returned.

---

## Data model

### agent_runs table
The central observability ledger. One row per significant agent action.

```
id UUID                          — primary key
agent_name string                — e.g. "investment_scanner", "marketplace_lister"
agent_type string                — "fastapi_service", "cron", "openclaw", "claude_code"
module string                    — e.g. "api.investment.router"
runtime string                   — "fastapi", "openclaw", "cron", "claude_code"
trigger_source string            — "api_call", "cron", "telegram", "manual"
task_name string                 — human-readable task identifier
input_summary text               — brief description of inputs (no secrets, no raw PII)
output_summary text              — brief description of outputs or result
status string                    — "started" | "completed" | "failed"
started_at timestamptz           — when the run began
finished_at timestamptz          — when it ended (null if still running or failed mid-way)
duration_ms integer              — wall-clock milliseconds
model_used string                — e.g. "gpt-4o-mini" (null if no AI)
input_tokens integer             — null if no AI
output_tokens integer            — null if no AI
estimated_cost numeric(12,6)     — USD, null if no AI
files_touched JSONB              — list of files changed (claude_code runs)
api_calls_made JSONB             — list of external API calls and their outcomes
database_records_created JSONB   — {table: count} of new DB rows
error_message text               — exception message on failure
human_approval_required bool     — true if action needs Dani's sign-off
human_approved bool              — null = pending, true = approved, false = rejected
final_outcome text               — one-line outcome description
outcome_score integer            — 1 = success, 0 = failure, null = not yet assessed
created_at timestamptz
updated_at timestamptz
```

### ai_usage table
One row per AI API call. Links back to an agent_run.

```
id UUID
run_id UUID FK → agent_runs (nullable — can log orphan AI calls)
agent_name string
provider string                  — "openai" | "anthropic"
model string
prompt_name string               — name of the prompt template used (e.g. "situation_evaluator")
input_tokens integer
output_tokens integer
total_tokens integer
estimated_cost numeric(12,6)     — USD
created_at timestamptz
```

---

## Token estimation

When the AI provider response includes `usage.prompt_tokens` / `usage.completion_tokens` (OpenAI) or `usage.input_tokens` / `usage.output_tokens` (Anthropic), use real values.

When real values are unavailable, estimate:
- Input tokens ≈ `len(prompt_text) / 4`
- Output tokens ≈ `len(response_text) / 4`
- Mark `output_summary` with `[token counts: estimated]`

---

## Cost estimation (model pricing as of 2026-04)

| Model | Input $/1M | Output $/1M |
|-------|-----------|------------|
| gpt-4o-mini | 0.150 | 0.600 |
| gpt-4o | 2.500 | 10.000 |
| claude-haiku-4-5 | 0.800 | 4.000 |
| claude-sonnet-4-6 | 3.000 | 15.000 |

Update this table when pricing changes. The `estimate_cost()` function reads from this dict.

---

## How each agent type is logged

### FastAPI agents (investment_scanner, marketplace_lister, etc.)
- `start_run()` called at the top of the endpoint handler
- `finish_run()` or `fail_run()` called at the end (in try/finally)
- AI calls within the handler call `log_ai_usage()` with real or estimated tokens
- Both calls use the same DB session as the business logic

### OpenClaw agents (telegram_router, openclaw_operator)
- Every FastAPI endpoint that OpenClaw calls already creates an `agent_runs` record
- `trigger_source = "telegram"` distinguishes these from API calls
- OpenClaw should pass `X-Trigger-Source: telegram` header where possible (future enhancement)
- OpenClaw must not bypass FastAPI for business logic

### Cron agents (scan, follow-up, heartbeat)
- The `heartbeat` endpoint receives the `task_name` and records a minimal agent_run
- Scan runs already go through `POST /api/investment/scan` — same instrumentation as FastAPI agents
- `trigger_source = "cron"` for all cron-triggered calls

### Claude Code sessions (claude_engineer)
- Sessions are logged manually via `POST /api/observability/claude-session`
- The engineering log in `docs/engineering-log.md` is the primary record
- Token data may be partial — see `docs/claude-code-usage.md`

---

## Investment source observability

Every scan (`POST /api/investment/scan`) must log to `agent_runs`:
- `api_calls_made`: list of `{source_name, source_url, filings_returned, errors}`
- `database_records_created`: `{"special_situations": N}`
- `output_summary`: "Scanned N sources. M filings found. K new situations created."

Sources must be read from the `investment_sources` DB table. A source with `active=false` is skipped. A source with a missing adapter logs a warning (not an error) and continues.

---

## What is NOT stored

- Raw prompt text containing personal user messages
- API keys, passwords, bot tokens
- Full HTML/JSON responses from external APIs (store counts and summaries only)
- Credit card or payment information

---

## Querying the observability data

Use the observability API (see `backend/api/observability/router.py`):

```
GET /api/observability/runs          — paginated run list
GET /api/observability/runs/{id}     — single run detail
GET /api/observability/summary       — system status + costs + top agents
GET /api/observability/costs         — cost breakdown by agent and model
GET /api/observability/agents        — agent registry with stats
POST /api/observability/claude-session — log a Claude Code engineering session
```

---

## Future dashboard

The observability API is designed to feed a private dashboard (not yet built) that shows:
- Agent activity timeline
- Cost per day/week/agent
- Failed runs with error messages
- Pending human approvals
- Investment source health
- OpenClaw command history
