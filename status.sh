#!/usr/bin/env bash
set -euo pipefail

check_url() {
  local name="$1"
  local url="$2"

  if curl -fsS "$url" >/dev/null 2>&1; then
    echo "$name: running"
  else
    echo "$name: stopped"
  fi
}

check_url "Frontend" "http://localhost:3000"
check_url "Backend" "http://127.0.0.1:8000/health"
