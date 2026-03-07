#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UV_BIN="${UV_BIN:-$(command -v uv || true)}"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
CRON_LOG_DIR="$REPO_ROOT/state/logs"
CRON_LOG="$CRON_LOG_DIR/local_daily.log"
USER_BIN_DIR="$HOME/.npm-global/bin"
LOCAL_BIN_DIR="$HOME/.local/bin"
mkdir -p "$CRON_LOG_DIR"

if [ -n "$UV_BIN" ]; then
  RUN_CMD="'$UV_BIN' run --with-requirements '$REPO_ROOT/requirements.txt' python '$REPO_ROOT/scripts/run_local_daily.py'"
else
  RUN_CMD="'$PYTHON_BIN' '$REPO_ROOT/scripts/run_local_daily.py'"
fi

JOB="0 7 * * * cd '$REPO_ROOT' && PATH='$USER_BIN_DIR:$LOCAL_BIN_DIR:/usr/local/bin:/usr/bin:/bin' $RUN_CMD >> '$CRON_LOG' 2>&1"

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT
crontab -l 2>/dev/null | grep -v "scripts/run_local_daily.py" > "$TMP_FILE" || true
printf '%s\n' "$JOB" >> "$TMP_FILE"
crontab "$TMP_FILE"

echo "Installed cron job:"
echo "$JOB"
echo "Logs: $CRON_LOG"
