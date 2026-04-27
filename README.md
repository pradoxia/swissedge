# SwissEdge Platform

Modular AI platform with two domains:

1. **Marketplace Assistant** — Sell and find deals on Swiss second-hand marketplaces via Telegram
2. **Special Situations Radar** — Detect, evaluate and publish investment special situations

## Quick Start

### Prerequisites
- Docker Desktop with WSL2 backend
- Python 3.12+

### Setup

```bash
# Copy environment variables
cp .env.example .env
# Edit .env with your credentials

# Start infrastructure
docker-compose up -d

# Install Python dependencies
pip install -r requirements.txt

# Start the backend
uvicorn backend.main:app --reload

# Verify it's running
curl http://localhost:8000/api/health/ping
```

### Health Check

```bash
python scripts/doctor.py
```

## Project Structure

```
swissedge/
├── backend/          # FastAPI backend (muscle)
│   ├── api/          # HTTP endpoints
│   ├── services/     # Business logic
│   ├── models/       # SQLAlchemy models
│   └── prompts/      # AI prompt templates
├── course_index/     # Pre-processed course data (committed)
├── course/           # Raw course transcripts (git-ignored)
├── config/           # YAML configuration files
├── scripts/          # Utility scripts (ingest_course, doctor)
├── web/              # Next.js research journal (Vercel)
└── deploy/           # VPS deployment scripts
```

## Docs

- [Architecture](architecture.md)
- [Product Requirements](product-requirements.md)
- [Roadmap](roadmap.md)
- [Build Sessions](claude-code-sessions.md)
- [Open Questions](open-questions.md)

## Architecture

OpenClaw (Contabo VPS) acts as the brain: handles Telegram routing and cron scheduling.
FastAPI backend (same VPS) acts as the muscle: handles all computation, database, and AI calls.
Vercel hosts the public Next.js research journal.
