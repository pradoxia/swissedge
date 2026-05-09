# SwissEdge Telegram Sales Bot — Deployment Guide

**Purpose:** Replace OpenClaw as the Telegram handler with a deterministic Python bot that reliably calls the Sales Items API.

**When to run this:** After `scripts/deploy_backend_files.ps1` has been run and the backend is updated with `POST /api/marketplace/sales/telegram-intake`.

---

## Architecture after this deploy

```
Dani (Telegram)
    │
    ▼
swissedge-telegram-bot.service   ← NEW: Python long-polling bot (deterministic)
    │  POST /api/marketplace/sales/telegram-intake
    │  POST /api/marketplace/generate-listing
    │  GET  /api/investment/situations
    │  ... (all existing commands)
    ▼
FastAPI :8000                     ← unchanged
    │
    ▼
PostgreSQL                        ← SalesItem rows created here
```

OpenClaw continues to run but with Telegram polling **disabled** — it keeps its Mission Control HTTP gateway active for other tools.

---

## Prerequisites

1. Backend deployed with `POST /api/marketplace/sales/telegram-intake` (Sprint 34 backend).
2. `python-telegram-bot` installed in VPS venv — verify:
   ```bash
   /opt/swissedge/.venv/bin/pip show python-telegram-bot
   ```
   If missing: `/opt/swissedge/.venv/bin/pip install python-telegram-bot`
3. `TELEGRAM_BOT_TOKEN` set in `/opt/swissedge/.env` — verify (value, not name):
   ```bash
   grep TELEGRAM_BOT_TOKEN /opt/swissedge/.env
   ```

---

## Step 1 — Disable OpenClaw Telegram polling

Two Telegram bots cannot both poll the same token simultaneously. OpenClaw must release it first.

**Option A — Disable Telegram in openclaw.json (preferred):**
```bash
ssh swdeploy@100.73.109.52
sudo nano /root/.openclaw/openclaw.json
# Find the telegram section and set enabled: false  OR  remove the bot token from it
# Save and exit

sudo systemctl restart openclaw
# Wait 5 seconds for OpenClaw to release the long-poll connection
sleep 5
```

**Option B — Stop OpenClaw entirely (use only if Option A is not available):**
```bash
sudo systemctl stop openclaw
# OR if pm2:
pm2 stop openclaw
```

> **Rollback note:** Keep OpenClaw's token config somewhere safe before editing. You will need it to re-enable OpenClaw Telegram if rolling back.

---

## Step 2 — Copy service file to VPS

From your local machine (Windows, repo root):
```powershell
scp deploy\systemd\swissedge-telegram-bot.service swdeploy@100.73.109.52:/tmp/swissedge-telegram-bot.service
```

Then on VPS:
```bash
ssh swdeploy@100.73.109.52
sudo mv /tmp/swissedge-telegram-bot.service /etc/systemd/system/swissedge-telegram-bot.service
sudo systemctl daemon-reload
```

---

## Step 3 — Start the bot service

```bash
sudo systemctl enable swissedge-telegram-bot
sudo systemctl start swissedge-telegram-bot
sleep 3
sudo systemctl status swissedge-telegram-bot --no-pager
```

Expected output: `Active: active (running)` with no Python import errors.

If there is an import error, check:
```bash
sudo journalctl -u swissedge-telegram-bot -n 30 --no-pager
```

---

## Step 4 — Smoke test

Send to Telegram bot:

| Message | Expected response |
|---------|------------------|
| `/start` | Welcome message |
| `Vende esta taza` | Spanish intake reply + link to `/marketplace/sales/items/{id}` |
| Product photo (no caption) | "📸 He recibido la foto." + same intake reply |
| `/situations` | Investment situations list |
| `/doctor` | System health report |

**Verify in browser:** Open `http://100.73.109.52:3001/marketplace/sales/items` — new item should appear with `status: needs_info`.

---

## Rollback

If anything goes wrong:

```bash
# Stop the Python bot
sudo systemctl stop swissedge-telegram-bot
sudo systemctl disable swissedge-telegram-bot

# Re-enable OpenClaw Telegram (reverse Step 1)
# Option A reversal: re-add token to /root/.openclaw/openclaw.json, then:
sudo systemctl restart openclaw
# Option B reversal:
sudo systemctl start openclaw
# or: pm2 start openclaw
```

---

## Service file reference

File: `deploy/systemd/swissedge-telegram-bot.service`

Key settings:
- Runs as `root` (required to read `/opt/swissedge/.venv` and `/opt/swissedge/.env`)
- `EnvironmentFile=/opt/swissedge/.env` — picks up `TELEGRAM_BOT_TOKEN` automatically, no token in service file
- `WorkingDirectory=/opt/swissedge` — required for relative imports (`backend.*`)
- `Restart=on-failure` + `RestartSec=10` — auto-recovers after crash
- `After=swissedge.service` — waits for FastAPI to be up before polling starts

---

## Env vars required

All already present in `/opt/swissedge/.env`:

| Variable | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot polling token — **never commit this** |
| `DATABASE_URL` | Not directly used by bot but required by shared `config.py` import |
| `OPENAI_API_KEY` | Not used by bot directly |

The bot itself only needs `TELEGRAM_BOT_TOKEN`. The other variables are loaded because `get_settings()` reads the full `.env`.

---

## What NOT to do

- Do not paste `TELEGRAM_BOT_TOKEN` into any file in this repo
- Do not run both OpenClaw Telegram polling and this bot simultaneously — Telegram will deliver messages to only one, causing missed messages and 409 conflicts
- Do not add `--webhook` unless a public HTTPS URL is available (it is not — VPS is Tailscale-only)
- Do not set `AUTO_PUBLISH=true` anywhere — no such config exists and publishing is permanently disabled
