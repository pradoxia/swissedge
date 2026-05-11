#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${SWISSEDGE_APP_DIR:-/opt/swissedge}"
LOCK_FILE="${SWISSEDGE_SEC_EDGAR_LOCK:-/tmp/swissedge_sec_edgar_detection.lock}"
HOURS_BACK="${SWISSEDGE_SEC_EDGAR_HOURS_BACK:-168}"

log() {
  printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"
}

run_detection() {
  cd "$APP_DIR"

  if [ ! -f ".venv/bin/activate" ]; then
    log "ERROR: missing virtualenv at $APP_DIR/.venv"
    return 1
  fi

  if [ ! -f ".env" ]; then
    log "ERROR: missing environment file at $APP_DIR/.env"
    return 1
  fi

  # Export environment variables for the CLI without printing secret values.
  set -a
  # shellcheck disable=SC1091
  . "$APP_DIR/.env"
  set +a

  # shellcheck disable=SC1091
  . "$APP_DIR/.venv/bin/activate"

  log "SEC EDGAR detection started hours_back=$HOURS_BACK"
  python -m backend.cli.sec_edgar_detect --hours-back "$HOURS_BACK"
  log "SEC EDGAR detection completed"
}

if command -v flock >/dev/null 2>&1; then
  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    log "SEC EDGAR detection already running; skipping overlapping run"
    exit 0
  fi
  run_detection
else
  LOCK_DIR="${LOCK_FILE}.d"
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    log "SEC EDGAR detection already running; skipping overlapping run"
    exit 0
  fi
  trap 'rmdir "$LOCK_DIR"' EXIT
  run_detection
fi
