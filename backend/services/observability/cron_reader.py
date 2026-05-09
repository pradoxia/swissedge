"""
Cron file reader for SwissEdge mission control.
Reads system and user crontabs, redacts secrets.
Falls back to `sudo crontab -l` for root's crontab if the spool file
is not readable by the FastAPI process user.
"""
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

_REDACT_ASSIGN = re.compile(
    r'((?:--)?(?:token|password|passwd|secret|api[_-]?key|apikey|auth|bearer)[\s=:])(\S+)',
    re.IGNORECASE,
)
_REDACT_TELEGRAM_TOKEN = re.compile(r'\b\d{8,10}:[A-Za-z0-9_-]{35,}\b')
_REDACT_LONG_HEX = re.compile(r'\b[0-9a-fA-F]{40,}\b')
_REDACT_ENV_VAR = re.compile(
    r'(\b(?:TOKEN|SECRET|PASSWORD|API_KEY|APIKEY|AUTH_TOKEN|BOT_TOKEN)\s*=\s*)(\S+)',
    re.IGNORECASE,
)


def redact_secrets(command: str) -> str:
    command = _REDACT_ASSIGN.sub(r'\1[REDACTED]', command)
    command = _REDACT_ENV_VAR.sub(r'\1[REDACTED]', command)
    command = _REDACT_TELEGRAM_TOKEN.sub('[REDACTED]', command)
    command = _REDACT_LONG_HEX.sub('[REDACTED]', command)
    return command


def _is_valid_cron(schedule: str) -> bool:
    try:
        from croniter import croniter  # available via apscheduler dep
        return croniter.is_valid(schedule)
    except Exception:
        return False


def _parse_lines(lines: list[str], source: str, is_system: bool = False) -> list[dict[str, Any]]:
    """Parse crontab lines into entry dicts."""
    entries = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*=', line):
            continue

        parts = line.split()
        min_parts = 7 if is_system else 6
        if len(parts) < min_parts:
            continue

        schedule = " ".join(parts[:5])
        if not _is_valid_cron(schedule):
            continue

        if is_system:
            user = parts[5]
            raw_command = " ".join(parts[6:])
        else:
            user = None
            raw_command = " ".join(parts[5:])

        entries.append({
            "schedule": schedule,
            "user": user,
            "command": redact_secrets(raw_command),
            "source": source,
        })
    return entries


def _parse_cron_file(path: str) -> list[dict[str, Any]]:
    """Parse a single crontab file. Handles both system (6-field) and user (5-field) formats."""
    is_system = path == "/etc/crontab"
    try:
        content = Path(path).read_text(encoding="utf-8")
        return _parse_lines(content.splitlines(), source=path, is_system=is_system)
    except (FileNotFoundError, PermissionError, OSError):
        return []


def _parse_sudo_crontab(user: str = "root") -> list[dict[str, Any]]:
    """
    Read a user's crontab via `sudo crontab -u <user> -l`.
    Returns [] silently if sudo is unavailable, times out, or access is denied.
    Secrets are redacted from the output.
    """
    try:
        result = subprocess.run(
            ["sudo", "crontab", "-u", user, "-l"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []
        lines = result.stdout.splitlines()
        return _parse_lines(lines, source=f"sudo crontab -u {user}", is_system=False)
    except Exception:
        return []


def get_upcoming(days: int = 3) -> dict[str, Any]:
    """
    Return upcoming cron executions over the next `days` days.
    Uses Europe/Zurich timezone. Secrets are redacted from command lines.
    """
    cron_paths = [
        "/etc/crontab",
        "/var/spool/cron/crontabs/root",
        "/var/spool/cron/crontabs/swdeploy",
    ]

    try:
        from croniter import croniter
        croniter_available = True
    except ImportError:
        croniter_available = False

    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Zurich")
    except Exception:
        tz = None

    now_naive = datetime.now()
    end_naive = now_naive + timedelta(days=days)

    now_display = datetime.now(tz).isoformat() if tz else now_naive.isoformat()
    end_display = (datetime.now(tz) + timedelta(days=days)).isoformat() if tz else end_naive.isoformat()

    sources_checked = list(cron_paths)

    if not croniter_available:
        return {
            "timezone": "Europe/Zurich",
            "window_days": days,
            "window_start": now_display,
            "window_end": end_display,
            "count": 0,
            "entries": [],
            "sources_checked": sources_checked,
            "note": "croniter library not available — cannot compute next runs.",
        }

    all_cron_entries: list[dict[str, Any]] = []

    # Read spool files first
    for path in cron_paths:
        parsed = _parse_cron_file(path)
        all_cron_entries.extend(parsed)

    # If root spool file yielded nothing (likely PermissionError), fall back to sudo
    root_spool_entries = [e for e in all_cron_entries if e["source"] == "/var/spool/cron/crontabs/root"]
    if not root_spool_entries:
        sudo_entries = _parse_sudo_crontab("root")
        if sudo_entries:
            all_cron_entries.extend(sudo_entries)
            sources_checked.append("sudo crontab -u root")

    upcoming: list[dict[str, Any]] = []
    for entry in all_cron_entries:
        try:
            cron = croniter(entry["schedule"], now_naive)
            while True:
                next_dt = cron.get_next(datetime)
                if next_dt > end_naive:
                    break
                if tz:
                    next_display = next_dt.replace(tzinfo=tz).isoformat()
                else:
                    next_display = next_dt.isoformat()
                upcoming.append({
                    "scheduled_at": next_display,
                    "schedule": entry["schedule"],
                    "user": entry.get("user"),
                    "command": entry["command"],
                    "source": entry["source"],
                })
        except Exception:
            continue

    upcoming.sort(key=lambda x: x["scheduled_at"])

    note = "Secrets redacted from command lines." if all_cron_entries else (
        "No cron entries found — cron files may not be accessible in this environment."
    )

    return {
        "timezone": "Europe/Zurich",
        "window_days": days,
        "window_start": now_display,
        "window_end": end_display,
        "count": len(upcoming),
        "entries": upcoming,
        "sources_checked": sources_checked,
        "note": note,
    }


def format_upcoming_text(data: dict[str, Any]) -> str:
    lines = [
        "SWISSEDGE — CRON SCHEDULE",
        f"Timezone : {data['timezone']}",
        f"Window   : {data['window_start']} → {data['window_end']}",
        f"Days     : {data['window_days']}",
        "=" * 60,
    ]

    entries = data.get("entries", [])
    if not entries:
        lines.append(f"\n{data.get('note', 'No entries found.')}")
    else:
        for e in entries:
            user_part = f" [{e['user']}]" if e.get("user") else ""
            lines.append(f"\n{e['scheduled_at']}{user_part}")
            lines.append(f"  schedule : {e['schedule']}")
            lines.append(f"  command  : {e['command']}")
            lines.append(f"  source   : {e['source']}")

    if entries:
        lines.append(f"\n{data.get('note', '')}")

    return "\n".join(lines)
