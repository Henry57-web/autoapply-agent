#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$ROOT_DIR/.runtime"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_LOG="$RUNTIME_DIR/backend.log"
FRONTEND_LOG="$RUNTIME_DIR/frontend.log"
BACKEND_PID=""
FRONTEND_PID=""

mkdir -p "$RUNTIME_DIR"

cleanup() {
  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    pkill -P "$FRONTEND_PID" >/dev/null 2>&1 || true
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
  rm -f "$RUNTIME_DIR/frontend.pid" "$RUNTIME_DIR/backend.pid"
}

trap cleanup EXIT INT TERM

if [ ! -f "$BACKEND_DIR/.env" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  echo "Created backend/.env. Add your DATABASE_URL and LLM_API_KEY, then run ./start.sh again."
  exit 1
fi

if [ ! -f "$FRONTEND_DIR/.env.local" ]; then
  cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env.local"
fi

PYTHON="$BACKEND_DIR/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  echo "Creating Python environment..."
  python3 -m venv "$BACKEND_DIR/.venv"
fi

if ! "$PYTHON" -c "import alembic, fastapi, sqlalchemy, uvicorn" >/dev/null 2>&1; then
  echo "Installing backend dependencies..."
  "$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
fi

echo "Applying database migrations..."
(
  cd "$BACKEND_DIR"
  "$PYTHON" -m alembic upgrade head
)

if [ -x "$ROOT_DIR/.tools/node/bin/npm" ]; then
  export PATH="$ROOT_DIR/.tools/node/bin:$PATH"
elif ! command -v npm >/dev/null 2>&1; then
  echo "Node.js is required. Install it from https://nodejs.org and run ./start.sh again."
  exit 1
fi

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm install)
fi

if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "Backend is already running."
else
  echo "Starting backend..."
  (
    cd "$BACKEND_DIR"
    "$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
  ) >"$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!
  echo "$BACKEND_PID" >"$RUNTIME_DIR/backend.pid"
fi

if curl -fsS http://localhost:3000 >/dev/null 2>&1; then
  echo "Frontend is already running."
else
  echo "Starting frontend..."
  (
    cd "$FRONTEND_DIR"
    npm run dev
  ) >"$FRONTEND_LOG" 2>&1 &
  FRONTEND_PID=$!
  echo "$FRONTEND_PID" >"$RUNTIME_DIR/frontend.pid"
fi

ready=false
for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1 &&
    curl -fsS http://localhost:3000 >/dev/null 2>&1; then
    ready=true
    echo
    echo "AutoApply Agent is ready."
    echo "Open: http://localhost:3000"
    echo "API docs: http://127.0.0.1:8000/docs"
    echo
    echo "Keep this terminal open. Press Control+C to stop both services."
    break
  fi
  sleep 1
done

if [ "$ready" != true ]; then
  echo
  echo "Startup did not finish within 30 seconds."
  echo "Backend log: $BACKEND_LOG"
  echo "Frontend log: $FRONTEND_LOG"
  exit 1
fi

while true; do
  if [ -n "$BACKEND_PID" ] && ! kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    echo "Backend stopped unexpectedly. Check $BACKEND_LOG"
    exit 1
  fi
  if [ -n "$FRONTEND_PID" ] && ! kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    echo "Frontend stopped unexpectedly. Check $FRONTEND_LOG"
    exit 1
  fi
  sleep 2
done
