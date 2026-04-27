# Health Check Specification — Doctor System

## Purpose

The Doctor system lets Claude Code diagnose what's working and what's broken in the SwissEdge platform. It also enables OpenClaw to self-monitor and alert via Telegram when something fails.

## Two Modes of Operation

### Mode 1: Claude Code Doctor (on-demand)
```
You open Claude Code → say "revisa el sistema" → Claude runs doctor.py → reads report → tells you what's broken and how to fix it
```

### Mode 2: OpenClaw Self-Monitor (automated)
```
OpenClaw cron (every 12 hours) → calls GET /api/health/full → if any component is "error" → sends Telegram alert to you
```

## Components Checked

### Infrastructure
| Component | Check Method | Healthy | Warning | Error |
|-----------|-------------|---------|---------|-------|
| PostgreSQL | SELECT 1 | Connected | Slow (>2s) | Cannot connect |
| Redis | PING | PONG received | Slow (>1s) | Cannot connect |
| Disk space | df -h | >20% free | 10-20% free | <10% free |
| Backend API | GET /health/ping | 200 OK | Slow (>5s) | No response |

### Marketplace Adapters
| Component | Check Method | Healthy | Warning | Error |
|-----------|-------------|---------|---------|-------|
| Tutti.ch | Search "test" | Results returned | Slow or partial | 403/timeout/blocked |
| Ricardo.ch | API ping (phase 2) | Auth valid | Auth expiring | Auth failed |
| Amazon PA-API | Test query | Results returned | Rate limited | Auth expired |
| Digitec | Search "test" | Results returned | Slow | Blocked |

### Investment Sources
| Component | Check Method | Healthy | Warning | Error |
|-----------|-------------|---------|---------|-------|
| SEC EDGAR | Search recent filings | Results returned | Slow | Timeout/error |
| Course index | Load master_index.json | Valid, all chapters | Partial | Missing/corrupt |

### Operational
| Component | Check Method | Healthy | Warning | Error |
|-----------|-------------|---------|---------|-------|
| Telegram bot | Check webhook status | Webhook active | — | Webhook missing |
| OpenClaw scan cron | Last run timestamp | Within expected interval | 1.5x interval | >2x interval |
| OpenClaw follow-up cron | Last run timestamp | Within expected interval | 1.5x interval | >2x interval |
| OpenClaw health cron | Last run timestamp | Within expected interval | 1.5x interval | >2x interval |

## Health Check API Response

```json
{
  "status": "degraded",
  "timestamp": "2026-04-26T12:00:00Z",
  "uptime_seconds": 86400,
  "components": [
    {
      "name": "postgresql",
      "category": "infrastructure",
      "status": "ok",
      "message": "Connected. 1,234 inventory items, 56 situations tracked.",
      "response_time_ms": 12,
      "last_checked": "2026-04-26T12:00:00Z"
    },
    {
      "name": "tutti_scraper",
      "category": "marketplace",
      "status": "error",
      "message": "HTTP 403 Forbidden on search request.",
      "last_success": "2026-04-23T10:00:00Z",
      "last_error": "2026-04-26T11:55:00Z",
      "error_count_24h": 8
    },
    {
      "name": "sec_edgar",
      "category": "investment",
      "status": "ok",
      "message": "Last query returned 14 filings. Avg response: 340ms.",
      "last_checked": "2026-04-26T10:00:00Z"
    },
    {
      "name": "openclaw_cron_scan_situations",
      "category": "operational",
      "status": "warning",
      "message": "Last execution was 26 hours ago. Expected interval: 6 hours.",
      "last_run": "2026-04-25T10:00:00Z",
      "expected_interval_hours": 6
    },
    {
      "name": "course_index",
      "category": "investment",
      "status": "ok",
      "message": "master_index.json valid. 20 chapters indexed. 8 situation types mapped.",
      "last_checked": "2026-04-26T12:00:00Z"
    }
  ],
  "recommendations": [
    "🔴 Tutti.ch scraper has been failing for 3 days. Options: (1) rotate User-Agent, (2) use Apify as fallback, (3) switch to manual mode for listings.",
    "🟡 OpenClaw cron 'scan_situations' appears stalled. Check OpenClaw dashboard → Tasks → scan_situations. May need manual restart.",
    "🟢 SEC EDGAR and course index are healthy. Investment radar is operational."
  ],
  "summary": {
    "total_components": 8,
    "ok": 5,
    "warning": 1,
    "error": 2
  }
}
```

## OpenClaw Cron Tracking

For OpenClaw cron monitoring to work, each OpenClaw scheduled task must call a "heartbeat" endpoint after execution:

```
POST /api/health/heartbeat
{
  "task_name": "scan_special_situations",
  "status": "completed",
  "items_processed": 14,
  "errors": 0
}
```

This writes to the health_checks table. The doctor checks last heartbeat timestamps against expected intervals.

### OpenClaw Cron Configuration

Configure these in OpenClaw:

| Task Name | Schedule | Endpoint to Call | On Success |
|-----------|----------|-----------------|------------|
| scan_special_situations | Every 6 hours | POST /api/investment/scan | POST /api/health/heartbeat |
| follow_up_watchlist | Daily 09:00 | POST /api/investment/follow-up | POST /api/health/heartbeat |
| check_watched_prices | Every 12 hours | POST /api/marketplace/check-watched | POST /api/health/heartbeat |
| system_health | Every 12 hours | GET /api/health/full | If error → send Telegram alert |

## doctor.py Script

```python
#!/usr/bin/env python3
"""SwissEdge Doctor — System Health Diagnostics"""

import sys
import httpx
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8000"

def main():
    try:
        response = httpx.get(f"{BACKEND_URL}/api/health/full", timeout=30)
        report = response.json()
    except Exception as e:
        print(f"❌ CRITICAL: Cannot reach backend at {BACKEND_URL}")
        print(f"   Error: {e}")
        print(f"   Is the backend running? Try: docker-compose ps")
        sys.exit(2)
    
    print(f"\n{'='*60}")
    print(f"  SwissEdge Health Report")
    print(f"  {report['timestamp']}")
    print(f"{'='*60}\n")
    
    status_icons = {"ok": "✅", "warning": "⚠️", "error": "❌"}
    
    for component in report["components"]:
        icon = status_icons.get(component["status"], "❓")
        print(f"  {icon} {component['name']}: {component['message']}")
    
    print(f"\n{'─'*60}")
    print(f"  Summary: {report['summary']['ok']} ok, "
          f"{report['summary']['warning']} warnings, "
          f"{report['summary']['error']} errors")
    print(f"  Overall: {report['status'].upper()}")
    print(f"{'─'*60}\n")
    
    if report["recommendations"]:
        print("  Recommendations:")
        for rec in report["recommendations"]:
            print(f"  {rec}")
        print()
    
    # Exit code for Claude Code to interpret
    if report["status"] == "healthy":
        sys.exit(0)
    elif report["status"] == "degraded":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()
```

## What Claude Code Does With the Report

When the user says "revisa el sistema" in Claude Code:

1. Claude runs `python scripts/doctor.py`
2. Reads the output
3. For each error/warning:
   - Explains the component's purpose in the system
   - Diagnoses likely cause based on error message
   - Proposes specific fix (command to run, file to edit, config to change)
4. For OpenClaw issues specifically:
   - Checks if the issue is in OpenClaw config or in the backend endpoint
   - Suggests whether to fix in OpenClaw dashboard or in code
   - Can modify backend code if the endpoint itself is broken
5. Prioritizes: fix errors first, then warnings
6. After fixes: re-runs doctor.py to verify
