#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
CRON_LOG_DIR="$REPO_ROOT/state/logs"
CRON_LOG="$CRON_LOG_DIR/local_daily.log"
USER_BIN_DIR="$HOME/.npm-global/bin"
mkdir -p "$CRON_LOG_DIR"

JOB="0 7 * * * cd '$REPO_ROOT' && PATH='$USER_BIN_DIR:/usr/local/bin:/usr/bin:/bin' '$PYTHON_BIN' '$REPO_ROOT/scripts/run_local_daily.py' >> '$CRON_LOG' 2>&1"

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT
crontab -l 2>/dev/null | grep -v "scripts/run_local_daily.py" > "$TMP_FILE" || true
printf '%s\n' "$JOB" >> "$TMP_FILE"
crontab "$TMP_FILE"

echo "Installed cron job:"
echo "$JOB"
echo "Logs: $CRON_LOG"
