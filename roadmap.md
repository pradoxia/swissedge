# Roadmap — SwissEdge Platform

## Phase 0 — Setup (1 week)

### Goal: Development environment ready, project skeleton created

- [ ] Install WSL2 Ubuntu on Windows 11
- [ ] Install Claude Code CLI
- [ ] Install Docker Desktop (WSL2 backend)
- [ ] Create monorepo with project structure from CLAUDE.md
- [ ] Create docker-compose.yml (PostgreSQL + Redis)
- [ ] Create FastAPI skeleton with health endpoint
- [ ] Create Telegram bot skeleton (or configure existing OpenClaw bot)
- [ ] Create .env.example with all required variables
- [ ] Create all docs/ files
- [ ] Install recommended Claude Code skills (see docs/skills-to-install.md)
- [ ] Verify OpenClaw can call a test FastAPI endpoint on same VPS

### Success criteria
- `docker-compose up` starts PostgreSQL and Redis
- `GET /api/health/ping` returns 200
- OpenClaw can call the ping endpoint
- Claude Code can run `/doctor` and see the health report

---

## Phase 1 — MVP (3-4 weeks)

### 1A: Course Ingestion (week 1)

- [ ] Create `scripts/ingest_course.py`
- [ ] Process all 20 chapters: transcript → summary + playbook + checklist + timestamps
- [ ] Generate `master_index.json` mapping situation types to chapters
- [ ] Verify: given a situation type, system returns correct chapter + timestamp
- [ ] Store processed files in `course_index/` and commit to git

### 1B: Telegram Bot — Sell Item (weeks 2-3)

- [ ] Implement photo analysis endpoint (`POST /api/marketplace/analyze-photo`)
- [ ] Implement Hochdeutsch description generator
- [ ] Implement TuttiAdapter.search() for price comparison (scraping)
- [ ] Implement price engine (average, range, percentile)
- [ ] Wire OpenClaw: receive photo → call backend → send draft to user
- [ ] Phase 1 output: formatted text + photos ready for copy-paste to Tutti.ch
- [ ] Test with 10 real items

### 1C: SEC/EDGAR Search Prototype (weeks 3-4)

- [ ] Implement SEC EDGAR source adapter (full-text search API)
- [ ] Filter filings by type: 8-K, S-1, Form 10, SC TO, DEF 14A
- [ ] Basic classification: map filing to situation type
- [ ] Match situation type to course chapter via master_index.json
- [ ] Manual test: run search, verify results make sense
- [ ] Create basic evaluation using course checklists

### 1D: Private Dashboard (week 4)

- [ ] Simple admin page (can be just a CLI tool or basic web page)
- [ ] View inventory items and their status
- [ ] View detected special situations
- [ ] View health check results
- [ ] View upcoming follow-up dates

### Success criteria
- Send photo to Telegram → receive publishable draft in 30 seconds
- Price comparison works for at least Tutti.ch
- SEC search returns relevant spin-offs and mergers
- Each situation links to correct course chapter

---

## Phase 2 — Automation (4-6 weeks)

### 2A: Scheduled Investment Radar

- [ ] Configure OpenClaw cron: scan 4x daily
- [ ] Automatic evaluation with course methodology
- [ ] Strength/weakness scoring
- [ ] Telegram alerts for new situations
- [ ] Follow-up agenda: schedule reminders for situations on watchlist
- [ ] Status tracking: detected → analyzing → watchlist → active → closed

### 2B: Price Monitoring

- [ ] Implement "watch this item" feature
- [ ] OpenClaw cron: check watched items 2x daily
- [ ] Alert when price drops below threshold
- [ ] Add Amazon DE adapter for price comparison
- [ ] Add Digitec adapter for price comparison

### 2C: Ricardo.ch Integration (if partnership key available)

- [ ] Apply for Ricardo.ch partnership credentials
- [ ] Implement RicardoAdapter using their API
- [ ] Add Ricardo as listing target in Telegram flow

### 2D: Doctor System

- [ ] Implement full health check endpoint
- [ ] Check: database, each scraper, each API, cron jobs, Telegram webhook
- [ ] Track OpenClaw task execution times
- [ ] Detect stale cron jobs (last run too long ago)
- [ ] Auto-alert via Telegram when component fails
- [ ] Claude Code `/doctor` reads health report and suggests fixes

### Success criteria
- System runs autonomously for 1 week with minimal intervention
- Investment radar finds real situations daily
- Price monitoring sends useful alerts
- Doctor detects and reports failures within 1 hour

---

## Phase 3 — Public Web & Community (4-6 weeks)

### 3A: Research Journal Website

- [ ] Next.js project with Tailwind
- [ ] Public page listing special situations
- [ ] Each situation has: type, date, thesis, checklist, risks, sources, status, disclaimer
- [ ] Filter by type, status, date
- [ ] SEO optimized for investment research keywords
- [ ] Deploy to Vercel

### 3B: Newsletter & External Presence

- [ ] Set up Substack newsletter
- [ ] Automate: when situation status changes to "watchlist", generate newsletter draft
- [ ] Create Seeking Alpha author profile
- [ ] Publish first 3-5 analyses on Seeking Alpha (manual, AI-assisted writing)
- [ ] LinkedIn posts for selected situations

### 3C: Historical Situations Database

- [ ] Search for past special situations (last 2-3 years)
- [ ] Evaluate what the returns would have been
- [ ] Track record page on website
- [ ] Find blogs/people who wrote about those situations
- [ ] Build initial contact list in investor_contacts table

### Success criteria
- Website live with 10+ published situations
- Newsletter has first subscribers
- At least 1 Seeking Alpha article published
- 20+ historical situations analyzed with hypothetical returns

---

## Phase 4 — Expansion (ongoing)

### 4A: More Marketplaces
- [ ] Facebook Marketplace
- [ ] Anibis.ch
- [ ] eBay
- [ ] Progressive auto-publish based on trust score

### 4B: More Investment Sources
- [ ] News feeds (PR Newswire, Business Wire)
- [ ] Specialized blogs discovered in phase 3C
- [ ] European regulatory filings (BaFin, SIX Exchange)
- [ ] RSS/Atom feed aggregator

### 4C: Community Features
- [ ] Commenting on situations (website)
- [ ] Contact management and outreach
- [ ] Collaboration with other researchers

### 4D: Advanced Architecture
- [ ] Migrate APScheduler → Celery + Redis for task queue
- [ ] Add pgvector for semantic search across sources
- [ ] Multi-language support (EN/DE/FR for Swiss audience)
- [ ] Mobile-friendly Telegram mini-app

---

## Token Budget Guidelines

| Activity | Estimated tokens/month | Notes |
|---|---|---|
| OpenClaw Telegram routing | 5,000-15,000 | Simple HTTP calls, minimal reasoning |
| OpenClaw cron jobs | 2,000-5,000 | 4x daily scan = ~120 calls/month |
| Description generation | 10,000-30,000 | Depends on items sold |
| SEC analysis | 15,000-40,000 | Depends on situations found |
| Claude Code sessions | Variable | Only when building/debugging |
| **Total operational** | **~30,000-90,000/month** | After build phase |

The key savings come from:
1. Caching scraping results (no repeated calls)
2. Pre-processed course index (no re-reading transcripts)
3. Prompts in files (consistent, no wasted tokens on prompt engineering each time)
4. FastAPI does computation, OpenClaw just routes
