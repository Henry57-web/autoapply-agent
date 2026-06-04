#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$ROOT_DIR/.runtime"

stop_process() {
  local name="$1"
  local pid_file="$RUNTIME_DIR/$2.pid"

  if [ ! -f "$pid_file" ]; then
    echo "$name was not started by ./start.sh."
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" >/dev/null 2>&1; then
    pkill -P "$pid" >/dev/null 2>&1 || true
    kill "$pid"
    echo "Stopped $name."
  else
    echo "$name is not running."
  fi
  rm -f "$pid_file"
}

stop_process "Frontend" "frontend"
stop_process "Backend" "backend"
