# CLAUDE.md — SwissEdge Platform

## Project Identity

**SwissEdge** is a modular AI platform with two domains:
1. **Marketplace Assistant** — Sell and find deals on Swiss second-hand marketplaces via Telegram
2. **Special Situations Radar** — Detect, evaluate and publish investment special situations

## Architecture Overview

```
OpenClaw (Contabo VPS) ← operational brain 24/7
├── Telegram bot (receives messages, routes to backend)
├── Cron jobs (scheduled searches, health checks)
└── Calls FastAPI endpoints for heavy lifting

FastAPI Backend (same Contabo VPS) ← muscle
├── /api/marketplace/* — listing generation, price comparison
├── /api/investment/* — SEC/EDGAR search, evaluation, course reference
├── /api/health/* — system diagnostics
└── PostgreSQL database

Vercel ← public showcase
└── Next.js research journal

Claude Code ← builder + doctor
├── Builds all code
└── Runs /doctor to diagnose OpenClaw failures
```

## Tech Stack

| Component       | Technology                          |
|----------------|-------------------------------------|
| Backend         | Python 3.12 + FastAPI               |
| Database        | PostgreSQL 16                       |
| Task scheduler  | APScheduler (phase 1), Celery (phase 2+) |
| Telegram        | python-telegram-bot                 |
| Web frontend    | Next.js 14 + Tailwind               |
| Deploy backend  | Docker Compose on Contabo VPS       |
| Deploy frontend | Vercel                              |
| Orchestrator    | OpenClaw (existing, on same VPS)    |
| Dev environment | Windows 11 + WSL2 Ubuntu            |

## Project Structure

```
swissedge/
├── CLAUDE.md                    # ← you are here
├── README.md
├── docker-compose.yml           # PostgreSQL + Redis
├── .env.example
├── backend/
│   ├── main.py                  # FastAPI app entry
│   ├── config.py                # Settings from env
│   ├── api/
│   │   ├── marketplace/         # Marketplace endpoints
│   │   ├── investment/          # Investment endpoints
│   │   └── health/              # Health check endpoints
│   ├── services/
│   │   ├── marketplace/
│   │   │   ├── adapters/        # MarketplaceAdapter interface
│   │   │   │   ├── base.py      # Abstract adapter
│   │   │   │   ├── tutti.py     # Tutti.ch (browser automation)
│   │   │   │   ├── ricardo.py   # Ricardo.ch (API, phase 2)
│   │   │   │   ├── amazon.py    # Amazon PA-API
│   │   │   │   └── digitec.py   # Digitec (scraping)
│   │   │   ├── price_engine.py  # Price comparison logic
│   │   │   ├── listing_gen.py   # Description generator (Hochdeutsch)
│   │   │   └── inventory.py     # Personal inventory management
│   │   ├── investment/
│   │   │   ├── sources/         # Source adapters (SEC, news, etc.)
│   │   │   │   ├── base.py      # Abstract source
│   │   │   │   ├── sec_edgar.py # SEC EDGAR API
│   │   │   │   └── news.py      # News feeds (phase 2+)
│   │   │   ├── evaluator.py     # Evaluates situations vs course methodology
│   │   │   ├── course_index.py  # Course reference system
│   │   │   └── publisher.py     # Publishes to web
│   │   └── telegram/
│   │       ├── bot.py           # Bot handlers
│   │       ├── commands.py      # Command definitions
│   │       └── safety.py        # Safety rules (no phone, no address, etc.)
│   ├── models/                  # SQLAlchemy models
│   ├── db/                      # Database migrations (Alembic)
│   └── tests/
├── course/                      # Investment course data (git-ignored)
│   ├── 01_chapter_name/
│   │   └── transcript.txt
│   └── ...
├── course_index/                # Generated from course (committed)
│   ├── chapter_01_summary.md
│   ├── chapter_01_playbook.md
│   ├── chapter_01_checklist.md
│   ├── chapter_01_timestamps.json
│   └── master_index.json        # Maps situation types → chapters
├── web/                         # Next.js frontend
│   └── ...
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   ├── product-requirements.md
│   ├── open-questions.md
│   └── health-check-spec.md
├── config/
│   ├── sources.yaml             # Editable list of investment sources
│   ├── marketplaces.yaml        # Marketplace configuration
│   └── safety_rules.yaml        # Bot safety rules
└── scripts/
    ├── ingest_course.py         # One-time course processing
    └── doctor.py                # System health diagnostics
```

## Key Design Decisions

### Marketplace Adapter Pattern
Every marketplace implements `MarketplaceAdapter` with:
- `search(query) → List[Listing]`
- `get_price(query) → PriceComparison`
- `create_listing(item) → Draft | PublishedListing`
- `get_listing_status(id) → Status`

New marketplaces = new adapter file, nothing else changes.

### OpenClaw as Brain, FastAPI as Muscle
- OpenClaw handles: Telegram routing, cron scheduling, simple decisions
- FastAPI handles: scraping, AI generation, database, evaluation
- This minimizes token consumption: OpenClaw makes HTTP calls, not complex reasoning

### Progressive Trust for Listings
Each item type accumulates a confidence score based on user approvals:
- Score < 10 → always show draft for approval
- Score >= 10 → suggest auto-publish (user can override)
- Safety rules ALWAYS apply regardless of trust score

### Investment Disclaimers
EVERY investment output MUST include:
- Uncertainty level
- List of risks
- Source links
- Course chapter references
- Legal disclaimer: "This is not financial advice"

### Course Reference System
The course is processed ONCE into structured files:
- `summary.md` — what the chapter covers
- `playbook.md` — step-by-step methodology
- `checklist.md` — evaluation checklist
- `timestamps.json` — searchable timestamp index
- `master_index.json` — maps situation types to chapters

DO NOT re-read raw transcripts in normal operation. Always use the processed index.

## Coding Conventions

- Python: use type hints everywhere, Pydantic for models
- Async by default for all I/O operations
- Config in YAML files, not hardcoded
- All prompts stored in `backend/prompts/` as .txt files, never inline
- German text generation: Hochdeutsch, simple, natural, no Schweizerdeutsch
- Tests: pytest, minimum coverage for adapters and safety rules
- Git: conventional commits, feature branches

## Safety Rules (non-negotiable)

### Marketplace Bot
- NEVER share user's phone number or exact address
- NEVER accept offers without user approval
- NEVER arrange pickup/meeting without user confirmation
- NEVER publish without approval in phase 1
- Always use Hochdeutsch, clear and simple

### Investment Output
- NEVER present as personalized financial advice
- ALWAYS include disclaimer
- ALWAYS show uncertainty and risks
- ALWAYS cite sources
- ALWAYS reference course methodology

## Doctor System

The `/doctor` command in Claude Code runs `scripts/doctor.py` which:
1. Calls `GET /api/health/full` on the backend
2. Checks each component: database, scrapers, APIs, cron jobs, Telegram bot
3. Reports what works, what's broken, and suggests fixes
4. Identifies OpenClaw tasks that are failing and why

Run this at the start of every Claude Code session focused on debugging.

## Environment Variables

See `.env.example` for all required variables. Critical ones:
- `DATABASE_URL` — PostgreSQL connection
- `TELEGRAM_BOT_TOKEN` — Bot token (reuse existing OpenClaw bot or create new)
- `SEC_USER_AGENT` — Required by SEC EDGAR API (your email)
- `OPENAI_API_KEY` — For OpenClaw's ChatGPT calls
- `ANTHROPIC_API_KEY` — For Claude-powered analysis (optional, phase 2+)

---

## Claude Code Workflow Rules

These rules apply to every Claude Code session on this project.

1. **Append to the engineering log.** Every session must add an entry to `docs/engineering-log.md` using the fixed template. Do not skip fields. Do not abbreviate.

2. **Run `/doctor` before debugging.** If a session involves debugging a service issue, run `scripts/doctor.py` first to get the current health state before touching code.

3. **No deploy without explicit approval.** Never run `systemctl restart`, `docker compose up`, `alembic upgrade head`, or any VPS-mutating command unless Dani has explicitly said "deploy" or "apply" in the current session.

4. **All VPS operations use `swdeploy`.** Do not attempt root SSH. Use `swdeploy` + `sudo -S` for all privileged operations.

5. **Observability is non-negotiable.** Every new FastAPI endpoint that calls an AI service or external API must call `run_logger.start_run()` / `finish_run()` / `fail_run()`. Wrap all logger calls in try/except — observability must never break business logic.

6. **Do not hardcode investment sources.** The scanner reads sources from the `investment_sources` DB table. Add new sources via `POST /api/investment/sources` or `config/investment_sources.yaml` seed, never in code.

7. **Do not make architecture decisions.** Dani and the design documents are the architects. Implement exactly what is specified. If a spec is ambiguous, ask — do not decide.

8. **Every AI call must use `complete_with_usage()`.** The `complete()` wrapper is provided for convenience; internal callers should use `complete_with_usage()` and pass usage data to `run_logger.log_ai_usage()`.

9. **Do not store secrets in code or docs.** All credentials live in `scripts/vps_config.py` (local only, not committed) and in `.env` on the VPS. If a doc or comment needs to reference a credential, use `[PLACEHOLDER]`.

10. **Collect token cost at end of session.** Run `/cost` before closing the session, submit the result to `POST /api/observability/claude-session` once the backend is reachable, and record the cost in the engineering log.
