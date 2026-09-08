#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$REPO_ROOT/.cache/dailypaper/bin:$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"
VENV="$REPO_ROOT/.cache/dailypaper/venv"
LOG_DIR="$REPO_ROOT/state/logs"
MODE="${1:-install}"

if [[ $# -gt 1 ]]; then
  echo 'Usage: bash scripts/install_local_cron.sh [--status|--logs|--check]' >&2
  exit 2
fi
case "$MODE" in
  --logs)
    if [[ -f "$LOG_DIR/local_daily.log" ]]; then
      tail -n 80 "$LOG_DIR/local_daily.log"
    else
      echo 'No DailyPaper log yet.'
    fi
    exit 0 ;;
  --status)
    if [[ ! -x "$VENV/bin/python" ]]; then
      echo 'DailyPaper dependencies are not installed. Run bash scripts/install_local_cron.sh' >&2
      exit 1
    fi
    exec "$VENV/bin/python" "$REPO_ROOT/scripts/local_schedule.py" status --repo-root "$REPO_ROOT" ;;
  install|--check) ;;
  *) echo 'Usage: bash scripts/install_local_cron.sh [--status|--logs|--check]' >&2; exit 2 ;;
esac

mkdir -p "$REPO_ROOT/.cache/dailypaper" "$LOG_DIR"
for executable in python3 git flock; do
  command -v "$executable" >/dev/null || { echo "Missing prerequisite: $executable" >&2; exit 1; }
done
exec 9> "$REPO_ROOT/.cache/dailypaper/install.lock"
flock -n 9 || { echo 'Another DailyPaper setup is running.' >&2; exit 75; }

if [[ "$MODE" == install ]]; then
  command -v crontab >/dev/null || { echo 'Install and enable Cronie before scheduling DailyPaper.' >&2; exit 1; }
  command -v npm >/dev/null || { echo 'Install Node.js/npm to install or update Codex.' >&2; exit 1; }
  LATEST_VERSION="$(npm view @openai/codex@latest version)"
  [[ "$LATEST_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+([-.][a-zA-Z0-9.-]+)?$ ]] || { echo 'Cannot verify the current Codex release.' >&2; exit 1; }
  INSTALLED_VERSION=""
  if command -v codex >/dev/null; then
    INSTALLED_VERSION="$(codex --version)"
    INSTALLED_VERSION="${INSTALLED_VERSION##* }"
  fi
  if [[ "$INSTALLED_VERSION" == "$LATEST_VERSION" ]]; then
    echo "Codex $LATEST_VERSION is current."
  else
    # Versioned user-owned dependencies avoid replacing a running binary on NFS.
    # This changes neither the account's credentials nor its permission settings.
    CODEX_DIR="$REPO_ROOT/.cache/dailypaper/codex/$LATEST_VERSION"
    npm install --prefix "$CODEX_DIR" --no-save --package-lock=false "@openai/codex@$LATEST_VERSION"
    [[ "$("$CODEX_DIR/node_modules/.bin/codex" --version)" == "codex-cli $LATEST_VERSION" ]] || { echo 'Installed Codex version did not verify.' >&2; exit 1; }
    mkdir -p "$REPO_ROOT/.cache/dailypaper/bin"
    ln -sfn "$CODEX_DIR/node_modules/.bin/codex" "$REPO_ROOT/.cache/dailypaper/bin/codex.next"
    mv -Tf "$REPO_ROOT/.cache/dailypaper/bin/codex.next" "$REPO_ROOT/.cache/dailypaper/bin/codex"
    hash -r
    [[ "$(codex --version)" == "codex-cli $LATEST_VERSION" ]] || { echo 'Installed Codex version did not verify.' >&2; exit 1; }
  fi
  if command -v uv >/dev/null; then
    uv venv --allow-existing "$VENV"
    uv pip install --python "$VENV/bin/python" --upgrade -r "$REPO_ROOT/requirements.txt"
  else
    python3 -m venv "$VENV"
    "$VENV/bin/python" -m pip install --upgrade pip
    "$VENV/bin/python" -m pip install --upgrade -r "$REPO_ROOT/requirements.txt"
  fi
fi

if [[ ! -x "$VENV/bin/python" ]]; then
  echo 'Run bash scripts/install_local_cron.sh to install dependencies first.' >&2
  exit 1
fi
# Same runner and model/tool preflight as production. Authentication and approval
# settings are inherited; no report is generated and no recommendation is reserved.
"$VENV/bin/python" "$REPO_ROOT/scripts/run_local_daily.py" --repo-root "$REPO_ROOT" --check-runtime 2>&1 | tee -a "$LOG_DIR/local_daily.log"
if [[ "$MODE" == --check ]]; then
  exit 0
fi

# Keep only executable directories in the cron PATH; never embed environment secrets.
CRON_PATH="$VENV/bin"
for executable in codex node git; do
  executable_path="$(command -v "$executable")"
  CRON_PATH="$CRON_PATH:$(dirname "$executable_path")"
done
CRON_PATH="$CRON_PATH:/usr/local/bin:/usr/bin:/bin"
"$VENV/bin/python" "$REPO_ROOT/scripts/local_schedule.py" install --repo-root "$REPO_ROOT" --python "$VENV/bin/python" --path "$CRON_PATH"
echo 'Status: bash scripts/install_local_cron.sh --status'
echo 'Logs:   bash scripts/install_local_cron.sh --logs'
