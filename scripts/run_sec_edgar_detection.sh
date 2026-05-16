#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${SWISSEDGE_APP_DIR:-/opt/swissedge}"
LOCK_FILE="${SWISSEDGE_SEC_EDGAR_LOCK:-/tmp/swissedge_sec_edgar_detection.lock}"
HOURS_BACK="${SWISSEDGE_SEC_EDGAR_HOURS_BACK:-48}"
DRY_RUN="${SWISSEDGE_SEC_EDGAR_DRY_RUN:-true}"
ENABLED="${SWISSEDGE_SEC_EDGAR_ENABLED:-false}"

log() {
  printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"
}

is_positive_integer() {
  case "$1" in
    ''|*[!0-9]*) return 1 ;;
    *) [ "$1" -gt 0 ] ;;
  esac
}

is_bool() {
  [ "$1" = "true" ] || [ "$1" = "false" ]
}

run_detection() {
  cd "$APP_DIR"

  if [ -f ".env" ]; then
    # Export environment variables for the CLI without printing secret values.
    set -a
    # shellcheck disable=SC1091
    . "$APP_DIR/.env"
    set +a
    HOURS_BACK="${SWISSEDGE_SEC_EDGAR_HOURS_BACK:-$HOURS_BACK}"
    DRY_RUN="${SWISSEDGE_SEC_EDGAR_DRY_RUN:-$DRY_RUN}"
    ENABLED="${SWISSEDGE_SEC_EDGAR_ENABLED:-$ENABLED}"
  fi

  if [ "$ENABLED" != "true" ]; then
    log "SEC EDGAR detection disabled; set SWISSEDGE_SEC_EDGAR_ENABLED=true to run"
    return 0
  fi

  if ! is_positive_integer "$HOURS_BACK"; then
    log "ERROR: SWISSEDGE_SEC_EDGAR_HOURS_BACK must be a positive integer; got '$HOURS_BACK'"
    return 1
  fi

  if ! is_bool "$DRY_RUN"; then
    log "ERROR: SWISSEDGE_SEC_EDGAR_DRY_RUN must be true or false; got '$DRY_RUN'"
    return 1
  fi

  if [ ! -f ".venv/bin/activate" ]; then
    log "ERROR: missing virtualenv at $APP_DIR/.venv"
    return 1
  fi

  if [ ! -f ".env" ]; then
    log "ERROR: missing environment file at $APP_DIR/.env"
    return 1
  fi

  # shellcheck disable=SC1091
  . "$APP_DIR/.venv/bin/activate"

  args=(python -m backend.cli.sec_edgar_detect --hours-back "$HOURS_BACK")
  if [ "$DRY_RUN" = "true" ]; then
    args+=(--dry-run)
  fi

  if [ "$DRY_RUN" = "true" ]; then
    mode="dry-run"
  else
    mode="live-create"
  fi

  log "SEC EDGAR detection started mode=$mode hours_back=$HOURS_BACK lock=$LOCK_FILE"
  "${args[@]}"
  log "SEC EDGAR detection completed mode=$mode hours_back=$HOURS_BACK"
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
