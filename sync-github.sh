#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYNC_DIR="$ROOT_DIR/.github-sync"
LOCK_DIR="$SYNC_DIR/lock"
INTERVAL_SECONDS=300
MODE="once"
COMMIT_MESSAGE=""

usage() {
  cat <<'EOF'
Usage:
  ./sync-github.sh [commit message]
  ./sync-github.sh --watch [seconds]

Examples:
  ./sync-github.sh
  ./sync-github.sh "Add migration tests"
  ./sync-github.sh --watch 300

Watch mode keeps the terminal open and syncs every five minutes by default.
Press Control+C to stop it.
EOF
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

if [ "${1:-}" = "--watch" ]; then
  MODE="watch"
  INTERVAL_SECONDS="${2:-300}"
  if ! [[ "$INTERVAL_SECONDS" =~ ^[0-9]+$ ]] || [ "$INTERVAL_SECONDS" -lt 30 ]; then
    echo "Watch interval must be an integer of at least 30 seconds."
    exit 1
  fi
elif [ "$#" -gt 0 ]; then
  COMMIT_MESSAGE="$*"
fi

mkdir -p "$SYNC_DIR"

acquire_lock() {
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "Another GitHub sync is already running."
    exit 1
  fi
  trap 'rm -rf "$LOCK_DIR"' EXIT INT TERM
}

check_repository() {
  git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null
  if ! git -C "$ROOT_DIR" remote get-url origin >/dev/null 2>&1; then
    echo "Git remote 'origin' is not configured."
    exit 1
  fi
}

scan_staged_secrets() {
  local staged_diff
  staged_diff="$(git -C "$ROOT_DIR" diff --cached --no-ext-diff --unified=0 -- . \
    ':(exclude)*.lock' ':(exclude)sync-github.sh')"

  if printf '%s' "$staged_diff" | grep -E \
    '^\+.*(sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{20,}|LLM_API_KEY=[^[:space:]]+|OPENAI_API_KEY=[^[:space:]]+)' \
    >/dev/null; then
    echo "Sync blocked: staged changes appear to contain an API key or database credential."
    echo "Remove the secret from tracked files, then run the sync again."
    exit 1
  fi

  if printf '%s' "$staged_diff" \
    | grep -E '^\+.*postgresql(\+asyncpg)?://[^[:space:]]+:[^@[:space:]]+@' \
    | grep -Ev '@(localhost|127\.0\.0\.1):' \
    >/dev/null; then
    echo "Sync blocked: staged changes appear to contain a remote database credential."
    echo "Remove the credential from tracked files, then run the sync again."
    exit 1
  fi
}

sync_once() {
  cd "$ROOT_DIR"
  local branch
  branch="$(git branch --show-current)"
  if [ -z "$branch" ]; then
    echo "Sync blocked: detached HEAD is not supported."
    return 1
  fi

  git add -A || return 1

  if git diff --cached --quiet; then
    echo "No local changes to sync."
  else
    scan_staged_secrets
    local message="$COMMIT_MESSAGE"
    if [ -z "$message" ]; then
      message="Sync local changes $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    git commit -m "$message" || return 1
  fi

  git pull --rebase origin "$branch" || return 1
  git push origin "$branch" || return 1
  echo "GitHub sync completed at $(date '+%Y-%m-%d %H:%M:%S')."
}

acquire_lock
check_repository

if [ "$MODE" = "once" ]; then
  sync_once
  exit 0
fi

echo "Automatic GitHub sync is running every ${INTERVAL_SECONDS}s."
echo "Press Control+C to stop."
while true; do
  if ! sync_once; then
    echo "Sync failed. The next attempt will run in ${INTERVAL_SECONDS}s."
  fi
  sleep "$INTERVAL_SECONDS"
done
